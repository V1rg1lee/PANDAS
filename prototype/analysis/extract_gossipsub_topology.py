#!/usr/bin/env python3
"""Extract topology-oriented CSVs from libp2p GossipSub JSON traces.

The libp2p-pubsub JSON tracer emits one JSON object per line. For topology
comparison, the most useful events are:

- addPeer / removePeer: peers known by the pubsub router;
- graft / prune: peers added to or removed from the mesh for a topic;
- sendRPC / recvRPC: message/control traffic between peers.

This script produces compact CSV files that are easier to compare with a
simulator than the raw trace stream.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    topic: str


def main() -> None:
    args = parse_args()
    trace_dir = Path(args.trace_dir)
    out_dir = Path(args.out_dir)

    if not trace_dir.is_dir():
        raise SystemExit(f"trace directory does not exist: {trace_dir}")
    if args.nodes_file and not Path(args.nodes_file).is_file():
        raise SystemExit(f"nodes file does not exist: {args.nodes_file}")
    if str(out_dir) == "/topology":
        raise SystemExit(
            "refusing to write to /topology. Your shell variable EXP is probably empty; "
            "run `echo \"$EXP\"` and re-define EXP/RESULTS/NODES before extracting."
        )
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise SystemExit(
            f"cannot create output directory {out_dir}: permission denied. "
            "Check that EXP is set to your experiment directory."
        ) from exc

    traces = sorted(trace_dir.glob(args.trace_glob))
    if not traces:
        raise SystemExit(f"no trace files matched {trace_dir / args.trace_glob}")

    peer_alias = trace_peer_aliases(traces)
    node_count_from_file = count_nodes(Path(args.nodes_file)) if args.nodes_file else None

    mesh_events: list[dict[str, Any]] = []
    peer_events: list[dict[str, Any]] = []
    rpc_events: list[dict[str, Any]] = []
    event_counts: Counter[str] = Counter()

    mesh_edges: set[Edge] = set()
    max_mesh_edges: set[Edge] = set()

    for trace_file in traces:
        for event in iter_trace_events(trace_file):
            event_type = classify_event(event)
            event_counts[event_type] += 1

            timestamp = event.get("timestamp", "")
            local_peer = event.get("peerID", "")

            if "addPeer" in event:
                peer_id = event["addPeer"].get("peerID", "")
                peer_events.append(row(timestamp, local_peer, peer_id, "addPeer", peer_alias))

            if "removePeer" in event:
                peer_id = event["removePeer"].get("peerID", "")
                peer_events.append(row(timestamp, local_peer, peer_id, "removePeer", peer_alias))

            if "graft" in event:
                peer_id = event["graft"].get("peerID", "")
                topic = event["graft"].get("topic", "")
                edge = Edge(local_peer, peer_id, topic)
                mesh_edges.add(edge)
                max_mesh_edges.add(edge)
                mesh_events.append(row(timestamp, local_peer, peer_id, "graft", peer_alias, topic))

            if "prune" in event:
                peer_id = event["prune"].get("peerID", "")
                topic = event["prune"].get("topic", "")
                edge = Edge(local_peer, peer_id, topic)
                mesh_edges.discard(edge)
                mesh_events.append(row(timestamp, local_peer, peer_id, "prune", peer_alias, topic))

            rpc_events.extend(extract_rpc_events(event, peer_alias))

    write_rows(out_dir / "mesh_events.csv", mesh_events, [
        "timestamp",
        "event",
        "topic",
        "source_peer",
        "source_alias",
        "target_peer",
        "target_alias",
    ])
    write_rows(out_dir / "peer_events.csv", peer_events, [
        "timestamp",
        "event",
        "topic",
        "source_peer",
        "source_alias",
        "target_peer",
        "target_alias",
    ])
    write_rows(out_dir / "rpc_events.csv", rpc_events, [
        "timestamp",
        "event",
        "topic",
        "source_peer",
        "source_alias",
        "target_peer",
        "target_alias",
        "message_count",
        "ihave_count",
        "iwant_count",
        "graft_count",
        "prune_count",
    ])

    final_edges = sorted(mesh_edges, key=lambda e: (e.topic, e.source, e.target))
    all_seen_edges = sorted(max_mesh_edges, key=lambda e: (e.topic, e.source, e.target))
    all_peers = set(peer_alias.keys())
    all_peers.update(peer for edge in [*final_edges, *all_seen_edges] for peer in [edge.source, edge.target])

    final_undirected_edges = directed_to_undirected(final_edges)
    seen_undirected_edges = directed_to_undirected(all_seen_edges)

    write_edge_rows(out_dir / "mesh_final_edges.csv", final_edges, peer_alias)
    write_edge_rows(out_dir / "mesh_seen_edges.csv", all_seen_edges, peer_alias)
    write_undirected_edge_rows(out_dir / "mesh_final_edges_undirected.csv", final_undirected_edges, peer_alias)
    write_undirected_edge_rows(out_dir / "mesh_seen_edges_undirected.csv", seen_undirected_edges, peer_alias)

    final_degrees = degree_rows(final_edges, peer_alias, all_peers)
    seen_degrees = degree_rows(all_seen_edges, peer_alias, all_peers)
    final_undirected_degrees = undirected_degree_rows(final_undirected_edges, peer_alias, all_peers)
    seen_undirected_degrees = undirected_degree_rows(seen_undirected_edges, peer_alias, all_peers)
    write_rows(out_dir / "mesh_final_degrees.csv", final_degrees, ["peer", "alias", "out_degree", "in_degree", "total_degree"])
    write_rows(out_dir / "mesh_seen_degrees.csv", seen_degrees, ["peer", "alias", "out_degree", "in_degree", "total_degree"])
    write_rows(out_dir / "mesh_final_degrees_undirected.csv", final_undirected_degrees, ["peer", "alias", "degree"])
    write_rows(out_dir / "mesh_seen_degrees_undirected.csv", seen_undirected_degrees, ["peer", "alias", "degree"])

    graph_stats = [
        topology_stats("final_directed", final_edges, all_peers, directed=True),
        topology_stats("seen_directed", all_seen_edges, all_peers, directed=True),
        topology_stats("final_undirected", final_undirected_edges, all_peers, directed=False),
        topology_stats("seen_undirected", seen_undirected_edges, all_peers, directed=False),
    ]
    write_rows(out_dir / "graph_stats.csv", graph_stats, [
        "name",
        "directed",
        "node_count",
        "edge_count",
        "density",
        "min_degree",
        "avg_degree",
        "max_degree",
        "component_count",
        "largest_component_size",
    ])

    summary = {
        "trace_files": [str(path) for path in traces],
        "event_counts": dict(sorted(event_counts.items())),
        "mesh_final_edge_count": len(final_edges),
        "mesh_final_undirected_edge_count": len(final_undirected_edges),
        "mesh_seen_edge_count": len(all_seen_edges),
        "mesh_seen_undirected_edge_count": len(seen_undirected_edges),
        "node_count_from_traces": len(peer_alias),
        "node_count_from_nodes_file": node_count_from_file,
        "graph_stats": graph_stats,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print(f"wrote topology extraction to {out_dir}")
    print(json.dumps(summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_dir", help="directory containing *.trace files")
    parser.add_argument("--nodes-file", help="optional nodes.csv for peer aliases")
    parser.add_argument("--out-dir", default="topology_out", help="output directory")
    parser.add_argument("--trace-glob", default="*.trace", help="trace filename glob")
    return parser.parse_args()


def iter_trace_events(path: Path) -> Any:
    with path.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def classify_event(event: dict[str, Any]) -> str:
    for key in [
        "publishMessage",
        "rejectMessage",
        "duplicateMessage",
        "deliverMessage",
        "addPeer",
        "removePeer",
        "recvRPC",
        "sendRPC",
        "dropRPC",
        "join",
        "leave",
        "graft",
        "prune",
    ]:
        if key in event:
            return key
    return f"type_{event.get('type', 'unknown')}"


def count_nodes(path: Path) -> int:
    with path.open() as handle:
        return sum(1 for record in csv.reader(handle) if len(record) == 6)


def trace_peer_aliases(paths: list[Path]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for path in paths:
        for event in iter_trace_events(path):
            peer_id = event.get("peerID")
            if peer_id:
                aliases[peer_id] = path.stem
            break
    return aliases


def row(
    timestamp: Any,
    source_peer: str,
    target_peer: str,
    event: str,
    aliases: dict[str, str],
    topic: str = "",
) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "event": event,
        "topic": topic,
        "source_peer": source_peer,
        "source_alias": aliases.get(source_peer, ""),
        "target_peer": target_peer,
        "target_alias": aliases.get(target_peer, ""),
    }


def extract_rpc_events(event: dict[str, Any], aliases: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    timestamp = event.get("timestamp", "")
    local_peer = event.get("peerID", "")

    if "sendRPC" in event:
        rpc = event["sendRPC"]
        source_peer = local_peer
        target_peer = rpc.get("sendTo", "")
        event_name = "sendRPC"
    elif "recvRPC" in event:
        rpc = event["recvRPC"]
        source_peer = rpc.get("receivedFrom", "")
        target_peer = local_peer
        event_name = "recvRPC"
    else:
        return rows

    meta = rpc.get("meta", {})
    messages = meta.get("messages", [])
    control = meta.get("control", {})
    ihave = control.get("ihave", [])
    iwant = control.get("iwant", [])
    graft = control.get("graft", [])
    prune = control.get("prune", [])
    topics = sorted({
        item.get("topic", "")
        for item in [*messages, *ihave, *graft, *prune]
        if item.get("topic", "")
    })
    topic = ";".join(topics)

    rows.append({
        "timestamp": timestamp,
        "event": event_name,
        "topic": topic,
        "source_peer": source_peer,
        "source_alias": aliases.get(source_peer, ""),
        "target_peer": target_peer,
        "target_alias": aliases.get(target_peer, ""),
        "message_count": len(messages),
        "ihave_count": count_control_messages(ihave),
        "iwant_count": count_control_messages(iwant),
        "graft_count": len(graft),
        "prune_count": len(prune),
    })
    return rows


def count_control_messages(items: list[dict[str, Any]]) -> int:
    total = 0
    for item in items:
        total += len(item.get("messageIDs", []))
    return total


def write_edge_rows(path: Path, edges: list[Edge], aliases: dict[str, str]) -> None:
    rows = [
        {
            "topic": edge.topic,
            "source_peer": edge.source,
            "source_alias": aliases.get(edge.source, ""),
            "target_peer": edge.target,
            "target_alias": aliases.get(edge.target, ""),
        }
        for edge in edges
    ]
    write_rows(path, rows, ["topic", "source_peer", "source_alias", "target_peer", "target_alias"])


def write_undirected_edge_rows(path: Path, edges: list[Edge], aliases: dict[str, str]) -> None:
    rows = [
        {
            "topic": edge.topic,
            "peer_a": edge.source,
            "alias_a": aliases.get(edge.source, ""),
            "peer_b": edge.target,
            "alias_b": aliases.get(edge.target, ""),
        }
        for edge in edges
    ]
    write_rows(path, rows, ["topic", "peer_a", "alias_a", "peer_b", "alias_b"])


def directed_to_undirected(edges: list[Edge]) -> list[Edge]:
    undirected = {
        Edge(min(edge.source, edge.target), max(edge.source, edge.target), edge.topic)
        for edge in edges
        if edge.source != edge.target
    }
    return sorted(undirected, key=lambda e: (e.topic, e.source, e.target))


def degree_rows(edges: list[Edge], aliases: dict[str, str], peers: set[str]) -> list[dict[str, Any]]:
    out_degree: Counter[str] = Counter()
    in_degree: Counter[str] = Counter()
    for edge in edges:
        out_degree[edge.source] += 1
        in_degree[edge.target] += 1

    return [
        {
            "peer": peer,
            "alias": aliases.get(peer, ""),
            "out_degree": out_degree[peer],
            "in_degree": in_degree[peer],
            "total_degree": out_degree[peer] + in_degree[peer],
        }
        for peer in sorted(peers)
    ]


def undirected_degree_rows(edges: list[Edge], aliases: dict[str, str], peers: set[str]) -> list[dict[str, Any]]:
    degree: Counter[str] = Counter()
    for edge in edges:
        degree[edge.source] += 1
        degree[edge.target] += 1

    return [
        {
            "peer": peer,
            "alias": aliases.get(peer, ""),
            "degree": degree[peer],
        }
        for peer in sorted(peers)
    ]


def topology_stats(name: str, edges: list[Edge], peers: set[str], directed: bool) -> dict[str, Any]:
    node_count = len(peers)
    edge_count = len(edges)
    if node_count <= 1:
        density = 0.0
    elif directed:
        density = edge_count / (node_count * (node_count - 1))
    else:
        density = edge_count / (node_count * (node_count - 1) / 2)

    if directed:
        degree_values = [
            sum(1 for edge in edges if edge.source == peer) + sum(1 for edge in edges if edge.target == peer)
            for peer in peers
        ]
    else:
        degree_counter: Counter[str] = Counter()
        for edge in edges:
            degree_counter[edge.source] += 1
            degree_counter[edge.target] += 1
        degree_values = [degree_counter[peer] for peer in peers]

    components = connected_components(peers, directed_to_undirected(edges) if directed else edges)
    largest_component_size = max((len(component) for component in components), default=0)

    return {
        "name": name,
        "directed": int(directed),
        "node_count": node_count,
        "edge_count": edge_count,
        "density": f"{density:.6f}",
        "min_degree": min(degree_values, default=0),
        "avg_degree": f"{(sum(degree_values) / node_count) if node_count else 0:.6f}",
        "max_degree": max(degree_values, default=0),
        "component_count": len(components),
        "largest_component_size": largest_component_size,
    }


def connected_components(peers: set[str], undirected_edges: list[Edge]) -> list[set[str]]:
    adjacency: dict[str, set[str]] = {peer: set() for peer in peers}
    for edge in undirected_edges:
        adjacency.setdefault(edge.source, set()).add(edge.target)
        adjacency.setdefault(edge.target, set()).add(edge.source)

    seen: set[str] = set()
    components: list[set[str]] = []
    for peer in sorted(adjacency):
        if peer in seen:
            continue
        stack = [peer]
        component: set[str] = set()
        seen.add(peer)
        while stack:
            current = stack.pop()
            component.add(current)
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
