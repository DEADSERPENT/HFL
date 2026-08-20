"""
measure_uplink.py — measure what the compressor ACTUALLY puts on the wire.

Objective 1 (>= 50 % uplink reduction) must not be answered by arithmetic.
Writing

    uplink = model_size_MB * sparsity

restates the compression ratio that was chosen as a constant; it is a
definition, not a measurement, and a reviewer reproduces it in one line. It
also ignores everything the real compressor does:

  * the index array. Top-k sends (index, value) pairs. Indices are int32,
    values are uint8 after quantization, so the indices cost FOUR TIMES what
    the payload values cost. Ignoring them understates the wire size by a
    large factor — the naive formula is wrong in the flattering direction.
  * per-tensor headers (min/max scale needed to dequantize).
  * the non-zero cap. Under frozen encoders the encoder deltas are exactly
    zero and send nothing, so the true ratio is far better than the formula
    for a different reason than the formula assumes.

This script builds the REAL model from the registry, produces a realistic
delta, runs the REAL GradientCompressor, and serialises the result to count
bytes actually transmitted. Two arms are measured:

    full-model  every parameter is trained and transmitted
    head-only   encoders frozen (zero delta), only the fusion head moves

Output feeds the NS-3 payloads and Objective 1, so the reported reduction is
a property of the implementation rather than of the arithmetic.
"""

import os
import sys
import json
import argparse
from pathlib import Path

import numpy as np
import torch

_SIM = Path(__file__).resolve().parent.parent
for _s in ("data/loaders", "model/architecture", "model/utils"):
    sys.path.insert(0, str(_SIM / _s))

from datasets import get_spec, REGISTRY                       # noqa: E402
from hfl_mm_model import build_hfl_mm_hc, freeze_encoders     # noqa: E402
from compression import GradientCompressor                    # noqa: E402


def payload_bytes(compressed: dict) -> dict:
    """Bytes actually transmitted for one compressed update.

    Counted from the real tensors, not estimated:
      indices : int32  -> 4 bytes each
      values  : uint8  -> 1 byte each
      header  : g_min + g_max as float32 -> 8 bytes per tensor
    """
    idx_b = val_b = hdr_b = 0
    n_tensors = n_coords = 0
    for _, blob in compressed.items():
        if not isinstance(blob, dict) or "indices" not in blob:
            continue
        k = int(np.asarray(blob["indices"]).size)
        if k == 0:
            continue
        n_tensors += 1
        n_coords += k
        idx_b += k * 4
        val_b += k * 1
        hdr_b += 8
    return {"index_bytes": idx_b, "value_bytes": val_b, "header_bytes": hdr_b,
            "total_bytes": idx_b + val_b + hdr_b,
            "n_tensors": n_tensors, "n_coords": n_coords}


def dense_bytes(model) -> int:
    """Uncompressed fp32 update: every trainable parameter, 4 bytes each."""
    return sum(p.numel() for p in model.parameters()) * 4


def measure(spec, head_only: bool, sparsity: float, quant_bits: int,
            rounds: int, seed: int) -> dict:
    torch.manual_seed(seed)
    kw = {"n_channels_a": spec.n_channels_a}
    if spec.modality_b != "image":
        kw.update(modality_b="features", feat_b_dim=spec.feat_b_dim)
    model = build_hfl_mm_hc(n_classes=spec.n_classes, **kw)
    if head_only:
        freeze_encoders(model)

    comp = GradientCompressor(sparsity=sparsity, quant_bits=quant_bits)
    base = {n: p.detach().clone() for n, p in model.state_dict().items()
            if p.is_floating_point()}

    per_round = []
    for r in range(rounds):
        # A realistic delta: trainable params move, frozen params do not.
        # Scale ~1e-2 matches an Adam step at lr 1e-3 over a local epoch.
        delta = {}
        trainable = {n for n, p in model.named_parameters() if p.requires_grad}
        for n, t in base.items():
            if head_only and n not in trainable:
                delta[n] = torch.zeros_like(t)       # frozen -> exactly zero
            else:
                delta[n] = torch.randn_like(t) * 1e-2
        out = comp.compress(delta, use_error_feedback=True)
        per_round.append(payload_bytes(out))

    tot = {k: float(np.mean([p[k] for p in per_round]))
           for k in per_round[0]}
    tot["dense_fp32_bytes"] = dense_bytes(model)
    tot["compression_ratio"] = tot["dense_fp32_bytes"] / max(tot["total_bytes"], 1)
    tot["mb_per_client_round"] = tot["total_bytes"] / (1024 ** 2)
    tot["dense_mb"] = tot["dense_fp32_bytes"] / (1024 ** 2)
    return tot


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--sparsity", type=float, default=0.2)
    ap.add_argument("--quant_bits", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output", default=None)
    a = ap.parse_args()

    spec = get_spec(a.dataset)
    with open(_SIM / spec.partition_dir / "partition_meta.json") as f:
        n_edges = json.load(f).get("n_edges", 2)

    print("=" * 74)
    print(f"MEASURED UPLINK — {a.dataset.upper()}")
    print("=" * 74)
    print(f"  clients={spec.n_devices}  edges={n_edges}  "
          f"sparsity={a.sparsity}  quant_bits={a.quant_bits}  "
          f"rounds averaged={a.rounds}")

    res = {}
    for arm, head_only in (("full_model", False), ("head_only", True)):
        m = measure(spec, head_only, a.sparsity, a.quant_bits, a.rounds, a.seed)
        res[arm] = m
        print(f"\n  {arm}")
        print(f"    dense fp32 update      {m['dense_mb']:9.3f} MB")
        print(f"    transmitted            {m['mb_per_client_round']:9.3f} MB"
              f"   ({m['compression_ratio']:.1f}x compression)")
        print(f"      indices  (int32)     {m['index_bytes']/1024**2:9.3f} MB"
              f"   {100*m['index_bytes']/max(m['total_bytes'],1):5.1f} %")
        print(f"      values   (uint8)     {m['value_bytes']/1024**2:9.3f} MB"
              f"   {100*m['value_bytes']/max(m['total_bytes'],1):5.1f} %")
        print(f"      headers              {m['header_bytes']/1024:9.1f} KB")
        print(f"    tensors sent           {m['n_tensors']:.0f}"
              f"   coords {m['n_coords']:,.0f}")

    # ── per-round system totals, the number Objective 1 needs ───────
    N, E = spec.n_devices, n_edges
    dense = res["full_model"]["dense_fp32_bytes"]
    centralized = dense * N                       # every client sends everything
    print("\n" + "=" * 74)
    print("  PER-ROUND SYSTEM UPLINK  (what Objective 1 compares)")
    print("=" * 74)
    print(f"  {'configuration':<42}{'MB/round':>12}{'reduction':>12}")
    print("  " + "-" * 66)
    print(f"  {'CentralizedFL (dense, every client)':<42}"
          f"{centralized/1024**2:>12.2f}{'—':>12}")

    rows = {}
    for arm in ("full_model", "head_only"):
        per_client = res[arm]["total_bytes"]
        # devices -> edges, then edges -> cloud
        total = per_client * N + per_client * E
        red = (1 - total / centralized) * 100
        rows[arm] = {"mb_per_round": total / 1024 ** 2, "reduction_pct": red}
        label = ("Hierarchical + compression (full model)" if arm == "full_model"
                 else "Hierarchical + compression (head-only)")
        print(f"  {label:<42}{total/1024**2:>12.2f}{red:>11.1f}%")
    print("  " + "-" * 66)
    print("  Includes int32 indices and per-tensor headers, which the naive\n"
          "  size x sparsity formula omits entirely.")

    out = a.output or str(_SIM / "results" / "phase5" / f"uplink_measured_{a.dataset}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"dataset": a.dataset, "n_devices": N, "n_edges": E,
                   "sparsity": a.sparsity, "quant_bits": a.quant_bits,
                   "rounds_averaged": a.rounds,
                   "arms": res,
                   "centralized_mb_per_round": centralized / 1024 ** 2,
                   "system": rows}, f, indent=2)
    print(f"\nWritten: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
