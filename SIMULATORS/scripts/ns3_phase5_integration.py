"""
NS-3 Phase 5 Integration — Re-run network simulation with Phase 5 payload sizes.
Uses actual uplink bytes from HFL-MM-HC training run to update NS-3 results.
Reads: results/phase5/hfl_mm_hc_results.csv  (produced by hfl_trainer.py)
Reads: results/ns3/ns3_results.csv            (Phase 4 NS-3 baseline)
Writes: results/ns3/ns3_phase5_results.csv    (updated with Phase 5 payloads)
"""

import os
import csv
import json
import math
import argparse
from datetime import datetime


# ── Topology, resolved from the DATASET REGISTRY ───────────────────────────
# These MUST match the configuration hfl_trainer.py actually ran, or every
# derived QoS figure describes a different experiment. They have been wrong
# twice: originally 20 devices / 3 edges / 12.8 MB (never trained), then
# hardcoded to a 6-device topology after the datasets changed.
# They are now DERIVED, so they cannot drift again.
#
#   wear    : 22 clients, 2 edges, 3,925,875 params (15.70 MB fp32)
#   vitaldb :  9 clients, 2 edges, 1,864,227 params ( 7.46 MB fp32)


def resolve_topology(dataset: str, tau_e: int = 5) -> dict:
    """Read client/edge counts from the dataset's partition_meta.json and the
    parameter count from the model that dataset actually builds."""
    import sys
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for sub in ("data/loaders", "model/architecture", "model/utils"):
        sys.path.insert(0, os.path.join(_root, sub))
    from datasets import get_spec
    from hfl_mm_model import build_hfl_mm_hc

    sp = get_spec(dataset)
    meta = json.load(open(os.path.join(_root, sp.partition_dir,
                                       "partition_meta.json")))
    kw = {"n_channels_a": sp.n_channels_a}
    if sp.modality_b != "image":
        kw.update(modality_b="features", feat_b_dim=sp.feat_b_dim)
    n_params = build_hfl_mm_hc(n_classes=sp.n_classes, **kw).n_total
    n_dev, n_edge = meta["n_devices"], meta["n_edges"]
    return {
        "dataset": dataset, "n_devices": n_dev, "n_edges": n_edge,
        "tau_e": tau_e,
        # every device uploads once per edge round
        "uploads_per_round": n_dev * tau_e,
        "model_bytes_fp32": n_params * 4, "n_params": n_params,
    }


# Filled in by main() from --dataset; module-level defaults keep the
# theoretical fallback path importable.
N_DEVICES   = 9
N_EDGES     = 2
TAU_E       = 5
UPLOADS_PER_ROUND = N_DEVICES * TAU_E
MODEL_SIZE_BYTES_FP32 = 1_864_227 * 4
TOPK_RATIO  = 0.20                     # 20% sparsification
QUANT_BITS  = 8                        # 8-bit quantization
# Per uploaded tensor: 20% of elements as int32 index + uint8 value = 5 B per
# 0.2 elements = 1 B/element vs 4 B/element FP32 → 4× on what is actually sent.
COMPRESSION_RATIO = 4.0
UPDATE_BYTES_DEVICE = int(MODEL_SIZE_BYTES_FP32 / COMPRESSION_RATIO)
UPDATE_BYTES_EDGE   = int(MODEL_SIZE_BYTES_FP32 * 0.5)

# Phase 4 validated QoS results (from Phase 4 NS-3 simulation)
PHASE4_COMM_REDUCTION = 0.764   # 76.4%
PHASE4_ENERGY_SAVING  = 0.749   # 74.9%
PHASE4_RELIABILITY    = 0.9905  # 99.05%


def load_hfl_results(csv_path: str) -> list[dict]:
    if not os.path.exists(csv_path):
        return []
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def compute_comm_stats(hfl_rows: list[dict]) -> dict:
    """Derive communication metrics from training log."""
    if not hfl_rows:
        # Use theoretical values from Phase 5 plan
        uplink_bytes_per_round = UPLOADS_PER_ROUND * UPDATE_BYTES_DEVICE
        downlink_bytes_per_round = N_DEVICES * MODEL_SIZE_BYTES_FP32
        # Baseline (no compression) = every upload carries the full FP32 model.
        # Must use UPLOADS_PER_ROUND, not N_DEVICES: the measured uplink_bytes
        # the `else` branch compares against covers all 30 uploads in a global
        # round, so a 6-upload baseline would understate the reduction 5×.
        baseline_bytes_per_round = UPLOADS_PER_ROUND * MODEL_SIZE_BYTES_FP32
        comm_reduction = 1.0 - (uplink_bytes_per_round / baseline_bytes_per_round)
        return {
            "source": "theoretical",
            "uplink_bytes_per_round": uplink_bytes_per_round,
            "downlink_bytes_per_round": downlink_bytes_per_round,
            "baseline_bytes_per_round": baseline_bytes_per_round,
            "comm_reduction_pct": round(comm_reduction * 100, 2),
        }

    # Parse actual uplink bytes from training log
    uplink_vals = []
    for row in hfl_rows:
        if "uplink_bytes" in row and row["uplink_bytes"]:
            try:
                uplink_vals.append(int(float(row["uplink_bytes"])))
            except ValueError:
                pass

    if uplink_vals:
        avg_uplink = sum(uplink_vals) / len(uplink_vals)
        baseline   = UPLOADS_PER_ROUND * MODEL_SIZE_BYTES_FP32
        comm_reduction = 1.0 - (avg_uplink / baseline)
    else:
        avg_uplink     = UPLOADS_PER_ROUND * UPDATE_BYTES_DEVICE
        baseline       = UPLOADS_PER_ROUND * MODEL_SIZE_BYTES_FP32
        comm_reduction = 1.0 - (avg_uplink / baseline)

    return {
        "source": "measured",
        "uplink_bytes_per_round": int(avg_uplink),
        "downlink_bytes_per_round": N_DEVICES * MODEL_SIZE_BYTES_FP32,
        "baseline_bytes_per_round": int(baseline),
        "comm_reduction_pct": round(comm_reduction * 100, 2),
    }


def simulate_ns3_metrics(comm_stats: dict, n_rounds: int = 20) -> dict:
    """
    Compute NS-3-equivalent network metrics from compression parameters.
    Phase 4 ran actual NS-3; Phase 5 updates the payload sizes and
    re-derives throughput, delay, and reliability analytically.
    """
    uplink_per_round  = comm_stats["uplink_bytes_per_round"]
    downlink_per_round = comm_stats["downlink_bytes_per_round"]

    # LTE 4G uplink throughput: ~5 Mbps per device (IoT setting)
    lte_uplink_mbps   = 5.0
    lte_downlink_mbps = 20.0

    # Transmission time per round (all devices upload in parallel to edge)
    # Bottleneck: slowest device in cluster (~N_DEVICES/N_EDGES per edge)
    devices_per_edge  = N_DEVICES / N_EDGES
    uplink_time_s     = (uplink_per_round * 8) / (lte_uplink_mbps * 1e6)
    downlink_time_s   = (downlink_per_round * 8) / (lte_downlink_mbps * 1e6)
    round_comm_time_s = uplink_time_s + downlink_time_s

    # Reliability: packet loss model (LTE ~0.1% per transmission)
    # Two hops: device→edge + edge→cloud.
    #
    # `update_reliability` is a PER-UPDATE quantity — the objective is phrased
    # "Update reliability > 99%", and Phase 4 measured it per-round in NS-3
    # (99.053% mean over the HFL_Proposed rows). It was previously computed as
    # hop_success ** n_rounds, i.e. the probability that ALL rounds succeed,
    # which is a different quantity and degenerate as a target: it decays with
    # round count (96.08% at 20 rounds, 81.86% at 100), so any system fails it
    # for a long enough run. The whole-run figure is still reported, under its
    # own name, because it is genuinely informative — just not this objective.
    packet_loss_rate  = 0.001
    hop_success       = (1 - packet_loss_rate) ** 2
    reliability       = hop_success                # per update, 2 hops
    run_reliability   = hop_success ** n_rounds    # all n_rounds succeed

    # Energy: proportional to bytes transmitted (simplified linear model)
    # 1 MB uplink ≈ 0.5 J (LTE IoT, measured in similar deployments).
    # Both sides must cover the same set of uploads. Previously the baseline
    # was one model per device while `uplink_per_round` already aggregated the
    # whole round, so the ratio collapsed to 1.0 and energy saving reported a
    # flat 0.0% FAIL regardless of how good the compression was.
    energy_per_mb = 0.5  # Joules
    uplink_mb     = uplink_per_round / 1e6
    baseline_mb   = (UPLOADS_PER_ROUND * MODEL_SIZE_BYTES_FP32) / 1e6
    energy_compressed = uplink_mb   * energy_per_mb * n_rounds
    energy_baseline   = baseline_mb * energy_per_mb * n_rounds
    energy_saving_pct = (1 - energy_compressed / energy_baseline) * 100

    # Throughput utilization
    theoretical_capacity_mbps = lte_uplink_mbps * N_DEVICES
    actual_throughput_mbps    = (uplink_mb * 8 * N_DEVICES) / round_comm_time_s

    return {
        "round_uplink_time_s":        round(uplink_time_s, 3),
        "round_downlink_time_s":      round(downlink_time_s, 3),
        "round_comm_time_total_s":    round(round_comm_time_s, 3),
        "comm_reduction_pct":         comm_stats["comm_reduction_pct"],
        "energy_saving_pct":          round(energy_saving_pct, 2),
        "update_reliability_pct":     round(reliability * 100, 4),
        "run_reliability_all_rounds_pct": round(run_reliability * 100, 4),
        "throughput_mbps":            round(actual_throughput_mbps, 3),
        "capacity_mbps":              theoretical_capacity_mbps,
        "uplink_bytes_per_device":    uplink_per_round // N_DEVICES,
        "total_uplink_bytes_all_rounds": uplink_per_round * n_rounds,
    }


def check_qos_targets(ns3: dict) -> list[dict]:
    targets = [
        {"objective": "O1 Comm reduction ≥ 50%",
         "value": ns3["comm_reduction_pct"],
         "threshold": 50.0,
         "unit": "%",
         "pass": ns3["comm_reduction_pct"] >= 50.0},
        {"objective": "O4 Energy saving ≥ 20%",
         "value": ns3["energy_saving_pct"],
         "threshold": 20.0,
         "unit": "%",
         "pass": ns3["energy_saving_pct"] >= 20.0},
        {"objective": "Update reliability > 99%",
         "value": ns3["update_reliability_pct"],
         "threshold": 99.0,
         "unit": "%",
         "pass": ns3["update_reliability_pct"] > 99.0},
    ]
    return targets


def write_results(ns3: dict, comm: dict, qos: list[dict], output_csv: str) -> None:
    os.makedirs(os.path.dirname(output_csv) if os.path.dirname(output_csv) else ".", exist_ok=True)
    rows = []

    # Network metrics
    for k, v in ns3.items():
        rows.append({"metric": k, "value": v, "source": "phase5_ns3_integration"})
    for k, v in comm.items():
        rows.append({"metric": f"comm_{k}", "value": v, "source": "phase5_compression"})

    # QoS pass/fail
    for q in qos:
        rows.append({
            "metric": q["objective"],
            "value": f"{q['value']}{q['unit']}",
            "source": f"{'PASS' if q['pass'] else 'FAIL'}",
        })

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "source"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[SAVED] NS-3 Phase 5 results → {output_csv}")


def main():
    global N_DEVICES, N_EDGES, TAU_E, UPLOADS_PER_ROUND, MODEL_SIZE_BYTES_FP32
    parser = argparse.ArgumentParser(description="NS-3 Phase 5 network metric integration")
    parser.add_argument("--dataset", default="vitaldb",
                        choices=["wear", "vitaldb"],
                        help="Topology and model size are derived from this.")
    parser.add_argument("--hfl_results", default="results/phase5/hfl_mm_hc_results.csv")
    parser.add_argument("--n_rounds", type=int, default=20)
    parser.add_argument("--output", default="results/ns3/ns3_phase5_results.csv")
    args = parser.parse_args()

    # Derive the topology from the dataset rather than trusting constants.
    topo = resolve_topology(args.dataset, TAU_E)
    N_DEVICES = topo["n_devices"]
    N_EDGES   = topo["n_edges"]
    UPLOADS_PER_ROUND = topo["uploads_per_round"]
    MODEL_SIZE_BYTES_FP32 = topo["model_bytes_fp32"]
    globals().update(UPDATE_BYTES_DEVICE=int(MODEL_SIZE_BYTES_FP32 / COMPRESSION_RATIO),
                     UPDATE_BYTES_EDGE=int(MODEL_SIZE_BYTES_FP32 * 0.5))

    print("=" * 60)
    print("  NS-3 Phase 5 Network Integration")
    print(f"  dataset: {args.dataset}  |  {topo['n_params']:,} params "
          f"({MODEL_SIZE_BYTES_FP32/1e6:.2f} MB fp32)")
    print(f"  Topology: {N_DEVICES} devices → {N_EDGES} edges → 1 cloud")
    print(f"  Compression: TopK({int(TOPK_RATIO*100)}%) + INT{QUANT_BITS} = {COMPRESSION_RATIO}× total")
    print("=" * 60)

    hfl_rows = load_hfl_results(args.hfl_results)
    if hfl_rows:
        print(f"[INFO] Loaded {len(hfl_rows)} training rounds from {args.hfl_results}")
    else:
        print(f"[INFO] HFL results not found — using theoretical payload estimates.")

    comm  = compute_comm_stats(hfl_rows)
    ns3   = simulate_ns3_metrics(comm, n_rounds=args.n_rounds)
    qos   = check_qos_targets(ns3)

    print(f"\n  Uplink per round (all devices): {comm['uplink_bytes_per_round']/1e6:.2f} MB")
    print(f"  Comm reduction:                 {ns3['comm_reduction_pct']:.1f}%")
    print(f"  Energy saving:                  {ns3['energy_saving_pct']:.1f}%")
    print(f"  Update reliability:             {ns3['update_reliability_pct']:.3f}%")
    print(f"  Round comm time:                {ns3['round_comm_time_total_s']:.3f} s")

    print("\n  QoS VALIDATION (O1, O4, Reliability):")
    all_pass = True
    for q in qos:
        icon = "✓" if q["pass"] else "✗"
        print(f"    [{icon}] {q['objective']}: {q['value']}{q['unit']}")
        if not q["pass"]:
            all_pass = False

    write_results(ns3, comm, qos, args.output)

    if all_pass:
        print("\n  [PASS] All Phase 4 QoS targets maintained in Phase 5.")
    else:
        print("\n  [WARN] Some QoS targets not met — review compression settings.")


if __name__ == "__main__":
    main()
