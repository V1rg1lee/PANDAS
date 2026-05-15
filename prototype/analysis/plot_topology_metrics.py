#!/usr/bin/env python3
"""Optional plots for topology pipeline outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics_dir")
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required for plots: python3 -m pip install matplotlib") from exc

    metrics_dir = Path(args.metrics_dir)
    if not metrics_dir.is_dir():
        raise SystemExit(f"metrics directory does not exist: {metrics_dir}")

    out_dir = Path(args.out_dir) if args.out_dir else metrics_dir / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    plot_degree_distribution(plt, metrics_dir, out_dir)
    plot_degree_timeseries(plt, metrics_dir, out_dir)
    plot_churn_timeseries(plt, metrics_dir, out_dir)
    plot_control_timeseries(plt, metrics_dir, out_dir)
    plot_edge_lifetimes(plt, metrics_dir, out_dir)
    plot_global_timeseries(plt, metrics_dir, out_dir)
    print(f"wrote plots to {out_dir}")


def plot_degree_distribution(plt: Any, metrics_dir: Path, out_dir: Path) -> None:
    rows = read_csv(metrics_dir / "union_degree_distribution.csv")
    if not rows:
        return
    degrees = [int(row["degree"]) for row in rows]
    counts = [int(row["count"]) for row in rows]
    plt.figure()
    plt.bar(degrees, counts)
    plt.xlabel("Directed out-degree")
    plt.ylabel("Node count")
    plt.title("Union mesh degree distribution")
    save(plt, out_dir / "degree_distribution.png")


def plot_degree_timeseries(plt: Any, metrics_dir: Path, out_dir: Path) -> None:
    rows = read_csv(metrics_dir / "degree_timeseries.csv")
    if not rows:
        return
    x = [int(row["heartbeat_index"]) for row in rows]
    plt.figure()
    plt.plot(x, [float(row["mean_degree"]) for row in rows], label="mean")
    plt.plot(x, [float(row["median_degree"]) for row in rows], label="median")
    plt.fill_between(
        x,
        [float(row["q25_degree"]) for row in rows],
        [float(row["q75_degree"]) for row in rows],
        alpha=0.25,
        label="q25-q75",
    )
    plt.xlabel("Heartbeat")
    plt.ylabel("Directed out-degree")
    plt.title("Mesh degree over time")
    plt.legend()
    save(plt, out_dir / "degree_timeseries.png")


def plot_churn_timeseries(plt: Any, metrics_dir: Path, out_dir: Path) -> None:
    rows = read_csv(metrics_dir / "churn_timeseries.csv")
    if not rows:
        return
    x = [int(row["heartbeat_index"]) for row in rows]
    plt.figure()
    plt.plot(x, [float(row["edge_churn_rate"]) for row in rows], label="churn")
    plt.plot(x, [float(row["jaccard_similarity"]) for row in rows], label="jaccard")
    plt.xlabel("Heartbeat")
    plt.ylabel("Ratio")
    plt.title("Mesh stability over time")
    plt.legend()
    save(plt, out_dir / "churn_timeseries.png")


def plot_control_timeseries(plt: Any, metrics_dir: Path, out_dir: Path) -> None:
    rows = read_csv(metrics_dir / "control_timeseries.csv")
    if not rows:
        return
    x = [int(row["heartbeat_index"]) for row in rows]
    plt.figure()
    for key in ["graft_count", "prune_count", "rpc_graft_count", "rpc_prune_count", "ihave_count", "iwant_count"]:
        if key in rows[0]:
            plt.plot(x, [int(row[key]) for row in rows], label=key.replace("_count", ""))
    plt.xlabel("Heartbeat")
    plt.ylabel("Count")
    plt.title("GossipSub control events")
    plt.legend()
    save(plt, out_dir / "control_timeseries.png")


def plot_edge_lifetimes(plt: Any, metrics_dir: Path, out_dir: Path) -> None:
    rows = read_csv(metrics_dir / "edge_lifetimes_from_snapshots.csv")
    lifetimes = [int(row["lifetime_ms"]) for row in rows if row.get("lifetime_ms")]
    if not lifetimes:
        return
    plt.figure()
    plt.hist(lifetimes, bins=min(30, max(1, len(set(lifetimes)))))
    plt.xlabel("Lifetime (ms)")
    plt.ylabel("Edge count")
    plt.title("Directed edge lifetime distribution")
    save(plt, out_dir / "edge_lifetimes.png")


def plot_global_timeseries(plt: Any, metrics_dir: Path, out_dir: Path) -> None:
    rows = read_csv(metrics_dir / "global_graph_timeseries.csv")
    if not rows:
        return
    x = [int(row["heartbeat_index"]) for row in rows]
    plt.figure()
    plt.plot(x, [int(row["component_count"]) for row in rows], label="components")
    plt.plot(x, [int(row["largest_component_size"]) for row in rows], label="largest component")
    plt.xlabel("Heartbeat")
    plt.ylabel("Count")
    plt.title("Connectivity over time")
    plt.legend()
    save(plt, out_dir / "connectivity_timeseries.png")

    plt.figure()
    plt.plot(x, [float(row["average_clustering_coefficient"]) for row in rows], label="clustering")
    plt.plot(x, [float(row["reciprocal_edge_ratio"]) for row in rows], label="reciprocity")
    plt.xlabel("Heartbeat")
    plt.ylabel("Ratio")
    plt.title("Structure over time")
    plt.legend()
    save(plt, out_dir / "structure_timeseries.png")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as handle:
        return list(csv.DictReader(handle))


def save(plt: Any, path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


if __name__ == "__main__":
    main()
