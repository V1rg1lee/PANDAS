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

## Topology Analysis

After a run, reconstruct common snapshots from the real GossipSub traces and
compute statistical topology metrics with:

```sh
python3 analysis/topology_pipeline.py pipeline-traces \
  "$RESULTS" \
  --out-dir "$EXP/topology_pipeline" \
  --heartbeat-ms 1000 \
  --topic gossipsub-smoke
```

This writes:

- `snapshots/snapshots.csv`: common directed snapshot format usable for real traces and simulator outputs;
- `snapshots/trace_events.csv`: observed GossipSub control/message/RPC events from real traces;
- `snapshots/edge_lifetimes.csv`: exact GRAFT-to-PRUNE lifetimes when PRUNE is observed;
- `metrics/node_degree_timeseries.csv`: per-node in/out/total directed degree per heartbeat;
- `metrics/degree_timeseries.csv`: degree distribution summary per heartbeat;
- `metrics/churn_timeseries.csv`: added/removed edges, churn, and Jaccard stability;
- `metrics/control_timeseries.csv`: one row per heartbeat bucket with GRAFT/PRUNE/IHAVE/IWANT/publish/delivery/RPC counters;
- `metrics/global_graph_timeseries.csv`: density, components, clustering, reciprocity, path metrics when feasible;
- `metrics/edge_lifetimes_from_snapshots.csv`: reconstructed edge lifetimes from snapshot changes;
- `metrics/convergence_metrics.json`: heuristic stabilization indicators;
- `metrics/methodology.md`: exact vs inferred metrics and assumptions.

Simulator snapshots can be analyzed with the same metric stage:

```sh
python3 analysis/topology_pipeline.py analyze-snapshots \
  simulator_snapshots.csv \
  --out-dir simulator_metrics
```

Optional plots:

```sh
python3 analysis/plot_topology_metrics.py "$EXP/topology_pipeline/metrics"
```
