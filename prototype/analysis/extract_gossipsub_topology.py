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
    out_dir.mkdir(parents=True, exist_ok=True)

    traces = sorted(trace_dir.glob(args.trace_glob))
    if not traces:
        raise SystemExit(f"no trace files matched {trace_dir / args.trace_glob}")

    peer_alias = trace_peer_aliases(traces)
    if args.nodes_file:
        peer_alias.update(load_peer_aliases(Path(args.nodes_file)))

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
    write_edge_rows(out_dir / "mesh_final_edges.csv", final_edges, peer_alias)
    write_edge_rows(out_dir / "mesh_seen_edges.csv", all_seen_edges, peer_alias)

    final_degrees = degree_rows(final_edges, peer_alias)
    seen_degrees = degree_rows(all_seen_edges, peer_alias)
    write_rows(out_dir / "mesh_final_degrees.csv", final_degrees, ["peer", "alias", "out_degree", "in_degree", "total_degree"])
    write_rows(out_dir / "mesh_seen_degrees.csv", seen_degrees, ["peer", "alias", "out_degree", "in_degree", "total_degree"])

    summary = {
        "trace_files": [str(path) for path in traces],
        "event_counts": dict(sorted(event_counts.items())),
        "mesh_final_edge_count": len(final_edges),
        "mesh_seen_edge_count": len(all_seen_edges),
        "peer_alias_count": len(peer_alias),
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


def load_peer_aliases(path: Path) -> dict[str, str]:
    aliases: dict[str, str] = {}
    with path.open() as handle:
        reader = csv.reader(handle)
        for record in reader:
            if len(record) != 6:
                continue
            nick, _tcp_port, _udp_port, ip, multiaddr, _role = record
            peer_id = multiaddr.rsplit("/p2p/", 1)[-1]
            aliases[peer_id] = f"{nick}-{ip}"
    return aliases


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


def degree_rows(edges: list[Edge], aliases: dict[str, str]) -> list[dict[str, Any]]:
    out_degree: Counter[str] = Counter()
    in_degree: Counter[str] = Counter()
    peers = set()
    for edge in edges:
        out_degree[edge.source] += 1
        in_degree[edge.target] += 1
        peers.add(edge.source)
        peers.add(edge.target)

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


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
