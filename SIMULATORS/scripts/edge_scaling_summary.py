"""edge_scaling_summary.py — update delivery and round latency against the number
of edge aggregators, from the packet-level edge-scaling runs.

Reads  results/ns3/ns3_results_<ds>.csv              (the dataset's own edge count)
       results/ns3/edge_scaling/ns3_<ds>_e<N>.csv     (run_edge_scaling.sh)
Writes results/ns3/edge_scaling/edge_scaling_<ds>.json and .csv

Only packet-level rows are used; an analytical row would carry a placeholder
reliability, not a measurement.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
import numpy as np

SIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NS3 = os.path.join(SIM, "results", "ns3")


def load(path):
    by = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(path)):
        if r.get("metric_source") != "packet-level":
            continue
        for c in ("reliability_pct", "L_total_ms", "L_comm_ms"):
            by[r["scenario"]][c].append(float(r[c]))
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--target", type=float, default=99.0,
                    help="O3b delivery target [%%]")
    a = ap.parse_args()
    out_dir = os.path.join(NS3, "edge_scaling")
    sys.path.insert(0, os.path.join(SIM, "scripts"))
    from ns3_phase5_integration import resolve_topology
    topo = resolve_topology(a.dataset)
    n_dev = topo["n_devices"]

    runs = {topo["n_edges"]: os.path.join(NS3, f"ns3_results_{a.dataset}.csv")}
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            m = re.fullmatch(rf"ns3_{re.escape(a.dataset)}_e(\d+)\.csv", f)
            if m:
                runs[int(m.group(1))] = os.path.join(out_dir, f)

    rows = []
    for e in sorted(runs):
        if not os.path.exists(runs[e]):
            continue
        for sc, v in sorted(load(runs[e]).items()):
            rel = np.array(v["reliability_pct"])
            rows.append(dict(
                n_edges=e, stations_per_edge=round(n_dev / e, 1), scenario=sc,
                n_rounds=len(rel), reliability_mean=round(rel.mean(), 3),
                reliability_min=round(rel.min(), 3),
                rounds_meeting_target=int((rel > a.target).sum()),
                latency_ms=round(float(np.mean(v["L_total_ms"])), 2),
                comm_ms=round(float(np.mean(v["L_comm_ms"])), 2),
                source=os.path.relpath(runs[e], SIM)))
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.join(out_dir, f"edge_scaling_{a.dataset}")
    with open(stem + ".csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    # smallest edge count at which the proposed configuration meets the target
    # on its MEAN and on its WORST round
    prop = [r for r in rows if r["scenario"] == "HFL_Proposed"]
    first = lambda key: next((r["n_edges"] for r in prop if r[key] > a.target), None)
    out = dict(dataset=a.dataset, n_devices=n_dev, target_pct=a.target,
               min_edges_mean_meets_target=first("reliability_mean"),
               min_edges_every_round_meets_target=first("reliability_min"),
               rows=rows)
    json.dump(out, open(stem + ".json", "w"), indent=2)

    print(f"{'edges':>5} {'sta/edge':>8} {'scenario':<14} {'rel mean':>8} {'rel min':>8}"
          f" {'ok':>5} {'lat ms':>7} {'comm ms':>8}")
    for r in rows:
        print(f"{r['n_edges']:>5} {r['stations_per_edge']:>8} {r['scenario']:<14}"
              f" {r['reliability_mean']:>8.2f} {r['reliability_min']:>8.2f}"
              f" {r['rounds_meeting_target']:>2}/{r['n_rounds']:<2}"
              f" {r['latency_ms']:>7.1f} {r['comm_ms']:>8.1f}")
    print(f"target {a.target} %: mean met from {out['min_edges_mean_meets_target']} edges,"
          f" every round from {out['min_edges_every_round_meets_target']} edges")
    print("wrote", stem + ".json")


if __name__ == "__main__":
    main()
