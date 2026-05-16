#!/usr/bin/env python3
"""Topology analysis pipeline for real and simulated GossipSub meshes.

The common snapshot format is:

    timestamp,heartbeat_index,node_id,peer_id,topic,mesh_size,snapshot_kind

Rows with ``snapshot_kind=heartbeat_marker`` mark a heartbeat/time bucket.
Rows with ``snapshot_kind=mesh_edge`` represent directed mesh edges.

This tool has three modes:

- ``traces-to-snapshots``: reconstruct snapshots from libp2p GossipSub traces.
- ``analyze-snapshots``: compute topology/time-series metrics from snapshots.
- ``pipeline-traces``: run both steps for real traces.

Real traces do not always expose exact heartbeat events. When they do not, this
tool uses fixed time buckets and labels the outputs as inferred.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SNAPSHOT_FIELDS = [
    "timestamp",
    "heartbeat_index",
    "node_id",
    "peer_id",
    "topic",
    "mesh_size",
    "snapshot_kind",
]


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    topic: str


@dataclass
class Snapshot:
    timestamp: int
    heartbeat_index: int
    edges: set[Edge]


@dataclass
class TraceEvent:
    timestamp_ns: int
    event_name: str
    local_peer: str
    remote_peer: str = ""
    topic: str = ""
    message_count: int = 0
    ihave_count: int = 0
    iwant_count: int = 0
    graft_count: int = 0
    prune_count: int = 0


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    traces_to_snapshots = subparsers.add_parser("traces-to-snapshots")
    traces_to_snapshots.add_argument("trace_dir")
    traces_to_snapshots.add_argument("--out-dir", required=True)
    traces_to_snapshots.add_argument("--trace-glob", default="*.trace")
    traces_to_snapshots.add_argument("--heartbeat-ms", type=int, default=1000)
    traces_to_snapshots.add_argument("--topic", default="")

    analyze_snapshots = subparsers.add_parser("analyze-snapshots")
    analyze_snapshots.add_argument("snapshots_csv")
    analyze_snapshots.add_argument("--out-dir", required=True)

    pipeline_traces = subparsers.add_parser("pipeline-traces")
    pipeline_traces.add_argument("trace_dir")
    pipeline_traces.add_argument("--out-dir", required=True)
    pipeline_traces.add_argument("--trace-glob", default="*.trace")
    pipeline_traces.add_argument("--heartbeat-ms", type=int, default=1000)
    pipeline_traces.add_argument("--topic", default="")

    args = parser.parse_args()

    if args.command == "traces-to-snapshots":
        traces_to_snapshots_command(args)
    elif args.command == "analyze-snapshots":
        analyze_snapshots_command(args)
    elif args.command == "pipeline-traces":
        out_dir = Path(args.out_dir)
        snapshot_dir = out_dir / "snapshots"
        analysis_dir = out_dir / "metrics"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshots_csv = snapshot_dir / "snapshots.csv"
        traces_to_snapshots_command(args, snapshots_csv=snapshots_csv)
        analyze_snapshots_file(snapshots_csv, analysis_dir)


def traces_to_snapshots_command(args: argparse.Namespace, snapshots_csv: Path | None = None) -> None:
    trace_dir = Path(args.trace_dir)
    if not trace_dir.is_dir():
        raise SystemExit(f"trace directory does not exist: {trace_dir}")
    if args.heartbeat_ms <= 0:
        raise SystemExit("--heartbeat-ms must be positive")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshots_csv = snapshots_csv or out_dir / "snapshots.csv"

    traces = sorted(trace_dir.glob(args.trace_glob))
    if not traces:
        raise SystemExit(f"no trace files matched {trace_dir / args.trace_glob}")

    alias_by_peer = aliases_from_trace_filenames(traces)
    events = list(iter_trace_events(traces, topic_filter=args.topic))
    if not events:
        raise SystemExit("no usable trace events found")

    first_ts = min(event.timestamp_ns for event in events)
    heartbeat_ns = args.heartbeat_ms * 1_000_000
    exact_heartbeats = any(event.event_name == "heartbeat" for event in events)
    methodology = "exact_heartbeat" if exact_heartbeats else "inferred_time_bucket"

    snapshots = reconstruct_snapshots(events, first_ts, heartbeat_ns)
    write_snapshots(snapshots_csv, snapshots, alias_by_peer)
    write_trace_nodes(snapshots_csv.parent / "nodes.csv", alias_by_peer)
    trace_events_path = snapshots_csv.parent / "trace_events.csv"
    edge_lifetimes_path = snapshots_csv.parent / "edge_lifetimes.csv"
    write_trace_events(trace_events_path, events, alias_by_peer, first_ts, heartbeat_ns)
    write_edge_lifetimes(edge_lifetimes_path, edge_lifetimes(events, first_ts), alias_by_peer)

    metadata = {
        "source": "real_gossipsub_trace",
        "methodology": methodology,
        "heartbeat_ms": args.heartbeat_ms,
        "trace_files": [str(path) for path in traces],
        "snapshot_count": len(snapshots),
        "event_count": len(events),
        "assumptions": [
            "Mesh state is reconstructed from observed graft/prune events.",
            "If no explicit heartbeat event is present, snapshots are emitted on fixed time buckets.",
            "Edges are directed: A->B and B->A are counted separately.",
        ],
    }
    (snapshots_csv.parent / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(f"wrote snapshots to {snapshots_csv}")


def analyze_snapshots_command(args: argparse.Namespace) -> None:
    analyze_snapshots_file(Path(args.snapshots_csv), Path(args.out_dir))


def analyze_snapshots_file(snapshots_csv: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshots = read_snapshots(snapshots_csv)
    if not snapshots:
        raise SystemExit(f"no snapshots found in {snapshots_csv}")

    all_nodes = nodes_from_snapshots(snapshots)
    all_nodes.update(read_trace_nodes(snapshots_csv.parent / "nodes.csv"))
    write_node_degree_timeseries(out_dir / "node_degree_timeseries.csv", snapshots, all_nodes)
    write_degree_timeseries(out_dir / "degree_timeseries.csv", snapshots, all_nodes)
    write_churn_timeseries(out_dir / "churn_timeseries.csv", snapshots)
    write_control_timeseries(out_dir / "control_timeseries.csv", snapshots_csv, snapshots)
    write_global_timeseries(out_dir / "global_graph_timeseries.csv", snapshots, all_nodes)

    union_edges = set().union(*(snapshot.edges for snapshot in snapshots))
    write_edges(out_dir / "union_directed_edges.csv", sorted_edges(union_edges))
    write_edges_undirected(out_dir / "union_undirected_edges.csv", directed_to_undirected(union_edges))
    write_degree_distribution(out_dir / "union_degree_distribution.csv", union_edges, all_nodes)
    write_edge_lifetimes_from_snapshots(out_dir / "edge_lifetimes_from_snapshots.csv", snapshots)
    write_convergence_metrics(out_dir / "convergence_metrics.json", snapshots, all_nodes)

    summary = summary_metrics(snapshots, all_nodes)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_methodology(out_dir / "methodology.md")
    print(f"wrote snapshot analysis to {out_dir}")


def iter_trace_events(paths: list[Path], topic_filter: str = "") -> Iterable[TraceEvent]:
    for path in paths:
        for raw in iter_json_lines(path):
            timestamp = int(raw.get("timestamp", 0))
            local_peer = raw.get("peerID", "")
            if "graft" in raw:
                topic = raw["graft"].get("topic", "")
                if topic_filter and topic != topic_filter:
                    continue
                yield TraceEvent(timestamp, "graft", local_peer, raw["graft"].get("peerID", ""), topic, graft_count=1)
            if "prune" in raw:
                topic = raw["prune"].get("topic", "")
                if topic_filter and topic != topic_filter:
                    continue
                yield TraceEvent(timestamp, "prune", local_peer, raw["prune"].get("peerID", ""), topic, prune_count=1)
            if "publishMessage" in raw:
                topic = raw["publishMessage"].get("topic", "")
                if topic_filter and topic != topic_filter:
                    continue
                yield TraceEvent(timestamp, "publish", local_peer, topic=topic, message_count=1)
            if "deliverMessage" in raw:
                topic = raw["deliverMessage"].get("topic", "")
                if topic_filter and topic != topic_filter:
                    continue
                yield TraceEvent(timestamp, "deliver", local_peer, raw["deliverMessage"].get("receivedFrom", ""), topic, message_count=1)
            if "sendRPC" in raw:
                yield rpc_trace_event(timestamp, "sendRPC", local_peer, raw["sendRPC"], topic_filter)
            if "recvRPC" in raw:
                rpc = raw["recvRPC"]
                received_from = rpc.get("receivedFrom", "")
                event = rpc_trace_event(timestamp, "recvRPC", received_from, rpc, topic_filter)
                event.remote_peer = local_peer
                yield event
            if "heartbeat" in raw:
                yield TraceEvent(timestamp, "heartbeat", local_peer)


def rpc_trace_event(timestamp: int, event_name: str, source_peer: str, rpc: dict[str, Any], topic_filter: str) -> TraceEvent:
    meta = rpc.get("meta", {})
    control = meta.get("control", {})
    messages = [msg for msg in meta.get("messages", []) if not topic_filter or msg.get("topic") == topic_filter]
    ihave = [item for item in control.get("ihave", []) if not topic_filter or item.get("topic") == topic_filter]
    iwant = control.get("iwant", [])
    graft = [item for item in control.get("graft", []) if not topic_filter or item.get("topic") == topic_filter]
    prune = [item for item in control.get("prune", []) if not topic_filter or item.get("topic") == topic_filter]
    topics = sorted({item.get("topic", "") for item in [*messages, *ihave, *graft, *prune] if item.get("topic", "")})
    remote = rpc.get("sendTo", "") if event_name == "sendRPC" else rpc.get("receivedFrom", "")
    return TraceEvent(
        timestamp_ns=timestamp,
        event_name=event_name,
        local_peer=source_peer,
        remote_peer=remote,
        topic=";".join(topics),
        message_count=len(messages),
        ihave_count=sum(len(item.get("messageIDs", [])) for item in ihave),
        iwant_count=sum(len(item.get("messageIDs", [])) for item in iwant),
        graft_count=len(graft),
        prune_count=len(prune),
    )


def reconstruct_snapshots(events: list[TraceEvent], first_ts: int, heartbeat_ns: int) -> list[Snapshot]:
    sorted_events = sorted(events, key=lambda event: event.timestamp_ns)
    last_bucket = max(bucket_index(event.timestamp_ns, first_ts, heartbeat_ns) for event in sorted_events)
    events_by_bucket: dict[int, list[TraceEvent]] = defaultdict(list)
    for event in sorted_events:
        events_by_bucket[bucket_index(event.timestamp_ns, first_ts, heartbeat_ns)].append(event)

    mesh: set[Edge] = set()
    snapshots: list[Snapshot] = []
    for bucket in range(last_bucket + 1):
        for event in events_by_bucket.get(bucket, []):
            if event.event_name == "graft" and event.remote_peer:
                mesh.add(Edge(event.local_peer, event.remote_peer, event.topic))
            elif event.event_name == "prune" and event.remote_peer:
                mesh.discard(Edge(event.local_peer, event.remote_peer, event.topic))
        snapshots.append(Snapshot(timestamp=bucket * heartbeat_ns // 1_000_000, heartbeat_index=bucket + 1, edges=set(mesh)))
    return snapshots


def read_snapshots(path: Path) -> list[Snapshot]:
    by_heartbeat: dict[int, Snapshot] = {}
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            heartbeat = int(row["heartbeat_index"])
            timestamp = int(row["timestamp"])
            snapshot = by_heartbeat.setdefault(heartbeat, Snapshot(timestamp, heartbeat, set()))
            if row["snapshot_kind"] == "mesh_edge":
                snapshot.edges.add(Edge(row["node_id"], row["peer_id"], row["topic"]))
    return [by_heartbeat[key] for key in sorted(by_heartbeat)]


def write_snapshots(path: Path, snapshots: list[Snapshot], aliases: dict[str, str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SNAPSHOT_FIELDS)
        writer.writeheader()
        for snapshot in snapshots:
            writer.writerow({
                "timestamp": snapshot.timestamp,
                "heartbeat_index": snapshot.heartbeat_index,
                "node_id": "",
                "peer_id": "",
                "topic": "",
                "mesh_size": len(snapshot.edges),
                "snapshot_kind": "heartbeat_marker",
            })
            for edge in sorted_edges(snapshot.edges):
                writer.writerow({
                    "timestamp": snapshot.timestamp,
                    "heartbeat_index": snapshot.heartbeat_index,
                    "node_id": aliases.get(edge.source, edge.source),
                    "peer_id": aliases.get(edge.target, edge.target),
                    "topic": edge.topic,
                    "mesh_size": out_degree(edge.source, snapshot.edges),
                    "snapshot_kind": "mesh_edge",
                })


def write_degree_timeseries(path: Path, snapshots: list[Snapshot], nodes: set[str]) -> None:
    fieldnames = [
        "timestamp",
        "heartbeat_index",
        "node_count",
        "edge_count",
        "mean_degree",
        "median_degree",
        "std_degree",
        "min_degree",
        "max_degree",
        "q10_degree",
        "q25_degree",
        "q75_degree",
        "q90_degree",
    ]
    rows = []
    for snapshot in snapshots:
        degrees = [out_degree(node, snapshot.edges) for node in sorted(nodes)]
        rows.append({
            "timestamp": snapshot.timestamp,
            "heartbeat_index": snapshot.heartbeat_index,
            "node_count": len(nodes),
            "edge_count": len(snapshot.edges),
            **distribution_stats(degrees, "degree"),
        })
    write_rows(path, rows, fieldnames)


def write_node_degree_timeseries(path: Path, snapshots: list[Snapshot], nodes: set[str]) -> None:
    rows = []
    for snapshot in snapshots:
        in_degrees = Counter(edge.target for edge in snapshot.edges)
        out_degrees = Counter(edge.source for edge in snapshot.edges)
        for node in sorted(nodes):
            rows.append({
                "timestamp": snapshot.timestamp,
                "heartbeat_index": snapshot.heartbeat_index,
                "node_id": node,
                "out_degree": out_degrees[node],
                "in_degree": in_degrees[node],
                "total_degree": out_degrees[node] + in_degrees[node],
            })
    write_rows(path, rows, ["timestamp", "heartbeat_index", "node_id", "out_degree", "in_degree", "total_degree"])


def write_churn_timeseries(path: Path, snapshots: list[Snapshot]) -> None:
    rows = []
    previous: set[Edge] = set()
    for snapshot in snapshots:
        added = snapshot.edges - previous
        removed = previous - snapshot.edges
        union = snapshot.edges | previous
        intersection = snapshot.edges & previous
        jaccard = len(intersection) / len(union) if union else 1.0
        churn_rate = (len(added) + len(removed)) / len(union) if union else 0.0
        rows.append({
            "timestamp": snapshot.timestamp,
            "heartbeat_index": snapshot.heartbeat_index,
            "edge_count": len(snapshot.edges),
            "added_edges": len(added),
            "removed_edges": len(removed),
            "edge_churn_rate": f"{churn_rate:.6f}",
            "jaccard_similarity": f"{jaccard:.6f}",
            "stable_edges": len(intersection),
        })
        previous = snapshot.edges
    write_rows(path, rows, [
        "timestamp",
        "heartbeat_index",
        "edge_count",
        "added_edges",
        "removed_edges",
        "edge_churn_rate",
        "jaccard_similarity",
        "stable_edges",
    ])


def write_control_timeseries(path: Path, snapshots_csv: Path, snapshots: list[Snapshot]) -> None:
    fieldnames = [
        "timestamp",
        "heartbeat_index",
        "heartbeat_count",
        "inferred_bucket_count",
        "graft_count",
        "prune_count",
        "rpc_graft_count",
        "rpc_prune_count",
        "ihave_count",
        "iwant_count",
        "publish_count",
        "deliver_count",
        "send_rpc_count",
        "recv_rpc_count",
    ]
    trace_events_path = snapshots_csv.parent / "trace_events.csv"
    if not trace_events_path.exists():
        rows = [empty_control_row(snapshot) for snapshot in snapshots]
        write_rows(path, rows, fieldnames)
        return

    counters: dict[int, Counter[str]] = defaultdict(Counter)
    with trace_events_path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            heartbeat = int(row["heartbeat_index"])
            event = row["event"]
            counters[heartbeat][event] += 1
            if event in {"sendRPC", "recvRPC"}:
                for key in ["graft_count", "prune_count", "ihave_count", "iwant_count"]:
                    counters[heartbeat][f"rpc_{key}"] += int(row.get(key, 0) or 0)

    rows = []
    for snapshot in snapshots:
        counter = counters[snapshot.heartbeat_index]
        rows.append({
            "timestamp": snapshot.timestamp,
            "heartbeat_index": snapshot.heartbeat_index,
            "heartbeat_count": counter["heartbeat"],
            "inferred_bucket_count": 0 if counter["heartbeat"] else 1,
            "graft_count": counter["graft"],
            "prune_count": counter["prune"],
            "rpc_graft_count": counter["rpc_graft_count"],
            "rpc_prune_count": counter["rpc_prune_count"],
            "ihave_count": counter["rpc_ihave_count"],
            "iwant_count": counter["rpc_iwant_count"],
            "publish_count": counter["publish"],
            "deliver_count": counter["deliver"],
            "send_rpc_count": counter["sendRPC"],
            "recv_rpc_count": counter["recvRPC"],
        })
    write_rows(path, rows, fieldnames)


def empty_control_row(snapshot: Snapshot) -> dict[str, Any]:
    return {
        "timestamp": snapshot.timestamp,
        "heartbeat_index": snapshot.heartbeat_index,
        "heartbeat_count": 0,
        "inferred_bucket_count": 1,
        "graft_count": 0,
        "prune_count": 0,
        "rpc_graft_count": 0,
        "rpc_prune_count": 0,
        "ihave_count": 0,
        "iwant_count": 0,
        "publish_count": 0,
        "deliver_count": 0,
        "send_rpc_count": 0,
        "recv_rpc_count": 0,
    }


def write_global_timeseries(path: Path, snapshots: list[Snapshot], nodes: set[str]) -> None:
    rows = []
    for snapshot in snapshots:
        undirected = directed_to_undirected(snapshot.edges)
        components = connected_components(nodes, undirected)
        clustering = average_clustering(nodes, undirected)
        rows.append({
            "timestamp": snapshot.timestamp,
            "heartbeat_index": snapshot.heartbeat_index,
            "directed_edge_count": len(snapshot.edges),
            "undirected_edge_count": len(undirected),
            "density_directed": f"{density(len(nodes), len(snapshot.edges), directed=True):.6f}",
            "density_undirected": f"{density(len(nodes), len(undirected), directed=False):.6f}",
            "component_count": len(components),
            "largest_component_size": max((len(component) for component in components), default=0),
            "average_clustering_coefficient": f"{clustering:.6f}",
            "reciprocal_edge_ratio": f"{reciprocal_edge_ratio(snapshot.edges):.6f}",
            "asymmetry_ratio": f"{1.0 - reciprocal_edge_ratio(snapshot.edges):.6f}",
            "avg_shortest_path_length": maybe_avg_shortest_path(nodes, undirected),
            "diameter": maybe_diameter(nodes, undirected),
        })
    write_rows(path, rows, [
        "timestamp",
        "heartbeat_index",
        "directed_edge_count",
        "undirected_edge_count",
        "density_directed",
        "density_undirected",
        "component_count",
        "largest_component_size",
        "average_clustering_coefficient",
        "reciprocal_edge_ratio",
        "asymmetry_ratio",
        "avg_shortest_path_length",
        "diameter",
    ])


def write_trace_events(path: Path, events: list[TraceEvent], aliases: dict[str, str], first_ts: int, heartbeat_ns: int) -> None:
    rows = []
    for event in sorted(events, key=lambda item: item.timestamp_ns):
        heartbeat = bucket_index(event.timestamp_ns, first_ts, heartbeat_ns) + 1
        rows.append({
            "timestamp": (event.timestamp_ns - first_ts) // 1_000_000,
            "heartbeat_index": heartbeat,
            "event": event.event_name,
            "topic": event.topic,
            "source_peer": aliases.get(event.local_peer, event.local_peer),
            "target_peer": aliases.get(event.remote_peer, event.remote_peer),
            "message_count": event.message_count,
            "ihave_count": event.ihave_count,
            "iwant_count": event.iwant_count,
            "graft_count": event.graft_count,
            "prune_count": event.prune_count,
        })
    write_rows(path, rows, [
        "timestamp",
        "heartbeat_index",
        "event",
        "topic",
        "source_peer",
        "target_peer",
        "message_count",
        "ihave_count",
        "iwant_count",
        "graft_count",
        "prune_count",
    ])


def edge_lifetimes(events: list[TraceEvent], first_ts: int) -> list[dict[str, Any]]:
    starts: dict[Edge, int] = {}
    lifetimes: list[dict[str, Any]] = []
    for event in sorted(events, key=lambda item: item.timestamp_ns):
        if event.event_name == "graft":
            starts[Edge(event.local_peer, event.remote_peer, event.topic)] = event.timestamp_ns
        elif event.event_name == "prune":
            edge = Edge(event.local_peer, event.remote_peer, event.topic)
            start = starts.pop(edge, None)
            if start is not None:
                lifetimes.append({
                    "source_peer": edge.source,
                    "target_peer": edge.target,
                    "topic": edge.topic,
                    "start_ms": (start - first_ts) // 1_000_000,
                    "end_ms": (event.timestamp_ns - first_ts) // 1_000_000,
                    "lifetime_ms": (event.timestamp_ns - start) // 1_000_000,
                    "status": "closed_by_prune",
                })
    for edge, start in starts.items():
        lifetimes.append({
            "source_peer": edge.source,
            "target_peer": edge.target,
            "topic": edge.topic,
            "start_ms": (start - first_ts) // 1_000_000,
            "end_ms": "",
            "lifetime_ms": "",
            "status": "still_present_at_trace_end",
        })
    return lifetimes


def write_edge_lifetimes(path: Path, rows: list[dict[str, Any]], aliases: dict[str, str]) -> None:
    aliased = []
    for row in rows:
        aliased.append({
            **row,
            "source_alias": aliases.get(row["source_peer"], row["source_peer"]),
            "target_alias": aliases.get(row["target_peer"], row["target_peer"]),
        })
    write_rows(path, aliased, [
        "source_peer",
        "source_alias",
        "target_peer",
        "target_alias",
        "topic",
        "start_ms",
        "end_ms",
        "lifetime_ms",
        "status",
    ])


def write_edge_lifetimes_from_snapshots(path: Path, snapshots: list[Snapshot]) -> None:
    starts: dict[Edge, int] = {}
    rows = []
    previous: set[Edge] = set()
    for snapshot in snapshots:
        for edge in snapshot.edges - previous:
            starts[edge] = snapshot.timestamp
        for edge in previous - snapshot.edges:
            start = starts.pop(edge, snapshot.timestamp)
            rows.append({
                "source_peer": edge.source,
                "target_peer": edge.target,
                "topic": edge.topic,
                "start_ms": start,
                "end_ms": snapshot.timestamp,
                "lifetime_ms": snapshot.timestamp - start,
                "status": "closed_by_snapshot_removal",
            })
        previous = snapshot.edges
    for edge, start in starts.items():
        rows.append({
            "source_peer": edge.source,
            "target_peer": edge.target,
            "topic": edge.topic,
            "start_ms": start,
            "end_ms": "",
            "lifetime_ms": "",
            "status": "still_present_at_last_snapshot",
        })
    write_rows(path, rows, ["source_peer", "target_peer", "topic", "start_ms", "end_ms", "lifetime_ms", "status"])


def write_convergence_metrics(path: Path, snapshots: list[Snapshot], nodes: set[str]) -> None:
    churn_rows = churn_metrics(snapshots)
    degree_means = []
    component_counts = []
    for snapshot in snapshots:
        degrees = [out_degree(node, snapshot.edges) for node in sorted(nodes)]
        degree_means.append(statistics.mean(degrees) if degrees else 0.0)
        component_counts.append(len(connected_components(nodes, directed_to_undirected(snapshot.edges))))

    payload = {
        "edge_churn_stabilization_heartbeat": first_stable_index(
            [row["edge_churn_rate"] for row in churn_rows], epsilon=0.05, window=3
        ),
        "mean_degree_stabilization_heartbeat": first_stable_index(degree_means, epsilon=0.5, window=3),
        "component_count_stabilization_heartbeat": first_stable_index(component_counts, epsilon=0.0, window=3),
        "stability_rule": "first heartbeat after which all following values remain within epsilon for a 3-sample moving window",
        "notes": [
            "These are heuristic convergence indicators, not protocol-defined convergence events.",
            "For short smoke tests, stabilization may be null because there are too few heartbeats.",
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def churn_metrics(snapshots: list[Snapshot]) -> list[dict[str, Any]]:
    rows = []
    previous: set[Edge] = set()
    for snapshot in snapshots:
        added = snapshot.edges - previous
        removed = previous - snapshot.edges
        union = snapshot.edges | previous
        intersection = snapshot.edges & previous
        rows.append({
            "heartbeat_index": snapshot.heartbeat_index,
            "edge_churn_rate": (len(added) + len(removed)) / len(union) if union else 0.0,
            "jaccard_similarity": len(intersection) / len(union) if union else 1.0,
        })
        previous = snapshot.edges
    return rows


def first_stable_index(values: list[float | int], epsilon: float, window: int) -> int | None:
    if len(values) < window:
        return None
    for index in range(len(values) - window + 1):
        tail = [float(value) for value in values[index:]]
        if max(tail) - min(tail) <= epsilon:
            return index + 1
    return None


def write_degree_distribution(path: Path, edges: set[Edge], nodes: set[str]) -> None:
    counts = Counter(out_degree(node, edges) for node in nodes)
    rows = [{"degree": degree, "count": count} for degree, count in sorted(counts.items())]
    write_rows(path, rows, ["degree", "count"])


def summary_metrics(snapshots: list[Snapshot], nodes: set[str]) -> dict[str, Any]:
    final = snapshots[-1]
    union_edges = set().union(*(snapshot.edges for snapshot in snapshots))
    final_undirected = directed_to_undirected(final.edges)
    union_undirected = directed_to_undirected(union_edges)
    union_components = connected_components(nodes, union_undirected)
    return {
        "node_count": len(nodes),
        "snapshot_count": len(snapshots),
        "final_directed_edge_count": len(final.edges),
        "final_undirected_edge_count": len(final_undirected),
        "union_directed_edge_count": len(union_edges),
        "union_undirected_edge_count": len(union_undirected),
        "final_density_directed": density(len(nodes), len(final.edges), True),
        "final_density_undirected": density(len(nodes), len(final_undirected), False),
        "final_reciprocal_edge_ratio": reciprocal_edge_ratio(final.edges),
        "union_reciprocal_edge_ratio": reciprocal_edge_ratio(union_edges),
        "union_component_count": len(union_components),
        "union_largest_component_size": max((len(component) for component in union_components), default=0),
        "union_average_clustering_coefficient": average_clustering(nodes, union_undirected),
        "union_avg_shortest_path_length": maybe_avg_shortest_path(nodes, union_undirected),
        "union_diameter": maybe_diameter(nodes, union_undirected),
    }


def nodes_from_snapshots(snapshots: list[Snapshot]) -> set[str]:
    nodes: set[str] = set()
    for snapshot in snapshots:
        for edge in snapshot.edges:
            nodes.add(edge.source)
            nodes.add(edge.target)
    return nodes


def write_trace_nodes(path: Path, aliases: dict[str, str]) -> None:
    rows = []
    for peer_id, alias in sorted(aliases.items(), key=lambda item: item[1]):
        rows.append({
            "peer_id": peer_id,
            "alias": alias,
            "role": role_from_alias(alias),
        })
    write_rows(path, rows, ["peer_id", "alias", "role"])


def read_trace_nodes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open() as handle:
        reader = csv.DictReader(handle)
        return {row["alias"] for row in reader if row.get("alias")}


def role_from_alias(alias: str) -> str:
    if alias.startswith("degraded"):
        return "degraded"
    return "node"


def out_degree(node: str, edges: set[Edge]) -> int:
    return sum(1 for edge in edges if edge.source == node)


def sorted_edges(edges: Iterable[Edge]) -> list[Edge]:
    return sorted(edges, key=lambda edge: (edge.topic, edge.source, edge.target))


def directed_to_undirected(edges: Iterable[Edge]) -> set[Edge]:
    return {
        Edge(min(edge.source, edge.target), max(edge.source, edge.target), edge.topic)
        for edge in edges
        if edge.source != edge.target
    }


def density(node_count: int, edge_count: int, directed: bool) -> float:
    if node_count <= 1:
        return 0.0
    max_edges = node_count * (node_count - 1)
    if not directed:
        max_edges /= 2
    return edge_count / max_edges if max_edges else 0.0


def distribution_stats(values: list[int], suffix: str) -> dict[str, Any]:
    if not values:
        return {
            f"mean_{suffix}": "0.000000",
            f"median_{suffix}": "0.000000",
            f"std_{suffix}": "0.000000",
            f"min_{suffix}": 0,
            f"max_{suffix}": 0,
            f"q10_{suffix}": "0.000000",
            f"q25_{suffix}": "0.000000",
            f"q75_{suffix}": "0.000000",
            f"q90_{suffix}": "0.000000",
        }
    return {
        f"mean_{suffix}": f"{statistics.mean(values):.6f}",
        f"median_{suffix}": f"{statistics.median(values):.6f}",
        f"std_{suffix}": f"{statistics.pstdev(values):.6f}",
        f"min_{suffix}": min(values),
        f"max_{suffix}": max(values),
        f"q10_{suffix}": f"{quantile(values, 0.10):.6f}",
        f"q25_{suffix}": f"{quantile(values, 0.25):.6f}",
        f"q75_{suffix}": f"{quantile(values, 0.75):.6f}",
        f"q90_{suffix}": f"{quantile(values, 0.90):.6f}",
    }


def quantile(values: list[int], q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[int(position)])
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def connected_components(nodes: set[str], undirected_edges: set[Edge]) -> list[set[str]]:
    adjacency = {node: set() for node in nodes}
    for edge in undirected_edges:
        adjacency.setdefault(edge.source, set()).add(edge.target)
        adjacency.setdefault(edge.target, set()).add(edge.source)
    seen: set[str] = set()
    components: list[set[str]] = []
    for node in sorted(adjacency):
        if node in seen:
            continue
        component: set[str] = set()
        stack = [node]
        seen.add(node)
        while stack:
            current = stack.pop()
            component.add(current)
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def average_clustering(nodes: set[str], undirected_edges: set[Edge]) -> float:
    adjacency = {node: set() for node in nodes}
    for edge in undirected_edges:
        adjacency[edge.source].add(edge.target)
        adjacency[edge.target].add(edge.source)
    coefficients = []
    for node in nodes:
        neighbors = list(adjacency[node])
        degree = len(neighbors)
        if degree < 2:
            coefficients.append(0.0)
            continue
        links = 0
        possible = degree * (degree - 1) / 2
        neighbor_set = set(neighbors)
        for i, left in enumerate(neighbors):
            for right in neighbors[i + 1:]:
                if right in adjacency[left]:
                    links += 1
        coefficients.append(links / possible)
    return statistics.mean(coefficients) if coefficients else 0.0


def reciprocal_edge_ratio(edges: set[Edge]) -> float:
    if not edges:
        return 0.0
    reciprocal = 0
    for edge in edges:
        if Edge(edge.target, edge.source, edge.topic) in edges:
            reciprocal += 1
    return reciprocal / len(edges)


def maybe_avg_shortest_path(nodes: set[str], undirected_edges: set[Edge]) -> str:
    distances = all_pairs_distances(nodes, undirected_edges)
    finite = [distance for distance in distances if distance > 0]
    if not finite:
        return ""
    return f"{statistics.mean(finite):.6f}"


def maybe_diameter(nodes: set[str], undirected_edges: set[Edge]) -> str:
    distances = all_pairs_distances(nodes, undirected_edges)
    finite = [distance for distance in distances if distance > 0]
    return str(max(finite)) if finite else ""


def all_pairs_distances(nodes: set[str], undirected_edges: set[Edge]) -> list[int]:
    if len(nodes) > 500:
        return []
    adjacency = {node: set() for node in nodes}
    for edge in undirected_edges:
        adjacency[edge.source].add(edge.target)
        adjacency[edge.target].add(edge.source)
    distances: list[int] = []
    for source in nodes:
        seen = {source}
        frontier = [(source, 0)]
        for current, distance in frontier:
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    next_distance = distance + 1
                    distances.append(next_distance)
                    frontier.append((neighbor, next_distance))
    return distances


def bucket_index(timestamp_ns: int, first_timestamp_ns: int, heartbeat_ns: int) -> int:
    return max(0, (timestamp_ns - first_timestamp_ns) // heartbeat_ns)


def iter_json_lines(path: Path) -> Iterable[dict[str, Any]]:
    with path.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def aliases_from_trace_filenames(paths: list[Path]) -> dict[str, str]:
    aliases = {}
    for path in paths:
        for event in iter_json_lines(path):
            peer_id = event.get("peerID")
            if peer_id:
                aliases[peer_id] = path.stem
            break
    return aliases


def write_edges(path: Path, edges: list[Edge]) -> None:
    rows = [{"source": edge.source, "target": edge.target, "topic": edge.topic} for edge in edges]
    write_rows(path, rows, ["source", "target", "topic"])


def write_edges_undirected(path: Path, edges: set[Edge]) -> None:
    rows = [{"node_a": edge.source, "node_b": edge.target, "topic": edge.topic} for edge in sorted_edges(edges)]
    write_rows(path, rows, ["node_a", "node_b", "topic"])


def write_methodology(path: Path) -> None:
    path.write_text("""# Methodology

Exact from real GossipSub traces:
- GRAFT and PRUNE events observed by the libp2p JSON tracer.
- Publish, delivery, duplicate, sendRPC, and recvRPC counters.
- Directed edge lifetimes when a GRAFT is followed by a PRUNE.

Reconstructed / inferred:
- Mesh snapshots are reconstructed by applying GRAFT/PRUNE events over time.
- If no explicit heartbeat event exists in the traces, heartbeat indexes are fixed-size time buckets.
- Edge lifetimes from snapshots are approximate when no PRUNE closes the edge.
- Convergence metrics are heuristic stability indicators.

Assumptions:
- Edges are directed.
- Local mesh degree is reported as directed out-degree; in-degree and total directed degree are also exported per node.
- Undirected views collapse A->B and B->A into one edge for structural statistics.
- Shortest-path metrics are skipped for graphs above 500 nodes to avoid expensive all-pairs computation.
- Shortest-path length is averaged over reachable node pairs only.
""")


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
