# Minimal GossipSub Prototype

This directory contains a standalone libp2p GossipSub executable.

The old application protocol has been removed. The executable exposes only the
flags used by the GossipSub runner.

## Build

```sh
go build -o libp2p-das .
```

## Runtime Inputs

The binary expects:

- `-key`: a libp2p private key file;
- `-node`: a CSV file with rows shaped as:

```csv
nick,tcp_port,udp_port,ip,multiaddr,role
```

The runner uses `nick`, `tcp_port`, `ip`, and `multiaddr`. The `udp_port` and
`role` columns are kept as explicit metadata in the static topology file.

## Useful Flags

- `-gossipTopic`: topic to join.
- `-gossipInterval`: seconds between publishes.
- `-gossipMessageBytes`: payload size per publish.
- `-duration`: run duration in seconds.
- `-log`: directory where `.trace` files are written.

## Grid5000

Use:

```sh
Launching_scripts/grid5000_smoke_test_gossipsub.md
```

## Trace Analysis

After a run, extract mesh and traffic CSVs from the GossipSub traces with:

```sh
python3 analysis/extract_gossipsub_topology.py \
  "$RESULTS" \
  --nodes-file "$NODES" \
  --out-dir "$EXP/topology"
```

The extractor writes:

- `mesh_events.csv`: ordered `graft`/`prune` events;
- `mesh_final_edges.csv`: final directed mesh edges;
- `mesh_seen_edges.csv`: all directed mesh edges ever observed;
- `mesh_final_edges_undirected.csv` and `mesh_seen_edges_undirected.csv`;
- `mesh_final_degrees.csv` and `mesh_seen_degrees.csv`;
- `mesh_final_degrees_undirected.csv` and `mesh_seen_degrees_undirected.csv`;
- `graph_stats.csv`: node/edge counts, density, degree min/avg/max, components;
- `peer_events.csv`: pubsub peer add/remove events;
- `rpc_events.csv`: send/recv RPC counters;
- `summary.json`: compact run summary.
