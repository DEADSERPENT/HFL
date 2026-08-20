"""
joint_eval.py — Phase 6 deliverable D6.1 (Phase 6.txt §6.2).

Assembles the five-system comparison table:

  S0  CentralizedFL   pooled data, no federation, no DP     → baseline B0
  S1  FlatFL_NoDP     FedAvg, single tier, no DP            → baseline B2
  S2  FL2DP           FedAvg + DP (eps=1), flat tier        → baseline B4
  S3  HED-FL          hierarchical, NO DP                   → run here
  S4  HFL-MM          proposed: 2-tier + DP + fusion        → proposed run

S0/S1/S2/S4 already exist as artifacts, so this script READS them rather than
retraining — re-running an arm under slightly different code is how two numbers
for the same system end up in one thesis. Only S3 has no existing artifact
(nothing else runs hierarchy without DP), so it is trained here via
hfl_trainer --no_dp.

Why S3 has to exist
-------------------
S4 differs from S2 in two ways at once: it adds the edge tier AND it changes
the DP recipe. S3 holds the topology of S4 while removing privacy entirely, so:

    S2 -> S3   what the hierarchy buys   (both non-comparable on privacy)
    S3 -> S4   what privacy costs        (same topology, DP on vs off)

Without S3 the table can report that S4 beats S2 but cannot say why, and the
hierarchy contribution stays unproven.

A note on the accuracy-loss column: it is computed against S0, per §6.2.2
("Accuracy loss vs. S0, <=2% at eps=1"), NOT against the best arm. S0 is the
no-privacy no-federation ceiling, which is what Objective 2 is written against.
"""

import os
import sys
import csv
import json
import time
import argparse
import subprocess
from pathlib import Path

_SIM = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import get_spec, REGISTRY                       # noqa: E402

SYSTEMS = [
    ("S0", "CentralizedFL", "pooled data, no FL, no DP"),
    ("S1", "FlatFL_NoDP", "FedAvg, single tier, no DP"),
    ("S2", "FL2DP", "FedAvg + DP, flat tier"),
    ("S3", "HED-FL", "hierarchical, no DP"),
    ("S4", "HFL-MM (PROPOSED)", "2-tier + head-only DP + fusion"),
]


def rows_of(path):
    if not Path(path).exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def last_row(path):
    r = rows_of(path)
    return r[-1] if r else {}


def num(d, *keys):
    for k in keys:
        if k in d and str(d[k]).strip() not in ("", "nan", "None"):
            try:
                return float(d[k])
            except ValueError:
                pass
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--local_epochs", type=int, default=1)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--epsilon", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--pretrained_encoders", default=None)
    ap.add_argument("--skip_s3", action="store_true",
                    help="do not train S3; report it as missing")
    ap.add_argument("--force_s3", action="store_true")
    ap.add_argument("--output_dir", default=None)
    a = ap.parse_args()

    ds = a.dataset
    spec = get_spec(ds)
    res = _SIM / "results" / "phase5"
    base = res / "baselines" / ds
    out_dir = Path(a.output_dir or _SIM / "results" / "phase6" / ds)
    out_dir.mkdir(parents=True, exist_ok=True)
    enc = a.pretrained_encoders or str(
        _SIM / "checkpoints" / f"pretrained_encoders_{ds}.pt")
    s3_csv = out_dir / f"s3_hedfl_{ds}.csv"

    print("=" * 84)
    print(f"JOINT EVALUATION — {ds.upper()}   (Phase 6, D6.1)")
    print("=" * 84)
    print(spec)

    # ── S3: the only arm with no existing artifact ──────────────────
    if not a.skip_s3 and (a.force_s3 or not s3_csv.exists()):
        if not os.path.exists(enc):
            print(f"\n[S3 SKIPPED] pretrained encoders missing: {enc}")
        else:
            argv = [sys.executable, str(_SIM / "model" / "training" / "hfl_trainer.py"),
                    "--dataset", ds, "--rounds", str(a.rounds),
                    "--local_epochs", str(a.local_epochs),
                    "--batch_size", str(a.batch_size), "--seed", str(a.seed),
                    "--no_dp",
                    "--freeze_encoders", "--pretrained_encoders", enc,
                    "--save_checkpoint", str(out_dir / f"ckpt_s3_{ds}.pt"),
                    "--output", str(s3_csv)]
            print("\n" + "=" * 84)
            print("  ▶ S3 HED-FL — hierarchical, NO differential privacy")
            print("=" * 84)
            print("  $ " + " ".join(argv))
            t0 = time.time()
            log = out_dir / "logs"; log.mkdir(exist_ok=True)
            with open(log / "s3_hedfl.log", "w") as lf:
                p = subprocess.Popen(argv, cwd=str(_SIM), stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in p.stdout:
                    sys.stdout.write(line); lf.write(line)
                p.wait()
            if p.returncode != 0:
                print(f"  ✗ S3 failed (exit {p.returncode}) — see {log/'s3_hedfl.log'}")
            else:
                print(f"  ✓ S3 done in {time.time()-t0:.0f}s")
    elif s3_csv.exists():
        print(f"\n  ⊙ S3 cached — {s3_csv.name}")

    # ── gather every system ─────────────────────────────────────────
    src = {
        "S0": base / "baseline_b0.csv",
        "S1": base / "baseline_b2.csv",
        "S2": base / "baseline_b4.csv",
        "S3": s3_csv,
        "S4": res / f"proposed_{ds}.csv",
    }
    ns3 = last_row(res / f"ns3_{ds}.csv")
    lat_path = res / f"latency_{ds}.json"
    lat = json.loads(lat_path.read_text()) if lat_path.exists() else {}

    def p95_ms(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if "p95" in k.lower():
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        pass
                r = p95_ms(v)
                if r is not None:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = p95_ms(v)
                if r is not None:
                    return r
        return None

    table = []
    for sid, name, desc in SYSTEMS:
        r = last_row(src[sid])
        table.append({
            "system": sid, "name": name, "description": desc,
            "source": str(src[sid].relative_to(_SIM)) if src[sid].exists() else "",
            "present": bool(r),
            "accuracy": num(r, "test_accuracy", "accuracy"),
            "macro_auc": num(r, "test_macro_auc", "macro_auc"),
            "auprc": num(r, "test_auprc", "auprc"),
            "case_auc": num(r, "test_case_auc", "case_auc"),
            "epsilon_spent": num(r, "epsilon_spent"),
            "uplink_mb": num(r, "uplink_mb", "total_uplink_mb", "uplink_total_mb"),
        })

    s0 = next((t for t in table if t["system"] == "S0"), None)
    ref_acc = s0["accuracy"] if s0 else None
    ref_up = s0["uplink_mb"] if s0 else None

    for t in table:
        # §6.2.2: accuracy loss is measured against S0, the no-privacy ceiling.
        t["acc_loss_vs_S0_pp"] = (
            (ref_acc - t["accuracy"]) * 100.0
            if (ref_acc is not None and t["accuracy"] is not None) else None)
        t["uplink_reduction_pct"] = (
            (1 - t["uplink_mb"] / ref_up) * 100.0
            if (ref_up and t["uplink_mb"] is not None) else None)
        # Latency and reliability are system-level QoS properties measured once
        # by ONNX/NS-3 on the deployed proposed model; they are not per-arm
        # training outputs, so they are attributed to S4 only rather than
        # copied across every row as if each arm had been benchmarked.
        t["p95_latency_ms"] = p95_ms(lat) if t["system"] == "S4" else None
        t["update_reliability_pct"] = (
            num(ns3, "update_reliability_pct", "reliability_pct")
            if t["system"] == "S4" else None)

    # ── write + print ───────────────────────────────────────────────
    out_csv = out_dir / "joint_eval.csv"
    fields = ["system", "name", "description", "present", "accuracy", "macro_auc",
              "auprc", "case_auc", "acc_loss_vs_S0_pp", "uplink_mb",
              "uplink_reduction_pct", "p95_latency_ms", "update_reliability_pct",
              "epsilon_spent", "source"]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for t in table:
            w.writerow({k: ("" if t.get(k) is None else t.get(k)) for k in fields})

    def g(v, fmt="{:.4f}"):
        return fmt.format(v) if isinstance(v, float) else "—"

    print("\n" + "=" * 84)
    print(f"JOINT EVALUATION TABLE — {ds}")
    print("=" * 84)
    hdr = (f"{'':<4}{'System':<20}{'acc':>9}{'AUROC':>9}{'AUPRC':>9}"
           f"{'ΔaccS0':>9}{'eps':>8}")
    print(hdr); print("-" * len(hdr))
    for t in table:
        if not t["present"]:
            print(f"{t['system']:<4}{t['name']:<20}{'— not run —':>44}")
            continue
        print(f"{t['system']:<4}{t['name']:<20}{g(t['accuracy']):>9}"
              f"{g(t['macro_auc']):>9}{g(t['auprc']):>9}"
              f"{g(t['acc_loss_vs_S0_pp'], '{:+.2f}'):>9}"
              f"{g(t['epsilon_spent'], '{:.2f}'):>8}")
    print("-" * len(hdr))

    missing = [t["system"] for t in table if not t["present"]]
    if missing:
        hint = {"S0": "baselines (B0)", "S1": "baselines (B2)",
                "S2": "baselines (B4)", "S3": "this script without --skip_s3",
                "S4": "the proposed run"}
        print("\n  not yet measured:")
        for m in missing:
            print(f"    {m} → run {hint[m]}")

    # ── the two contrasts the table exists to support ───────────────
    def get(sid, key):
        t = next((x for x in table if x["system"] == sid), {})
        return t.get(key)

    print("\n  CONTRASTS")
    for lhs, rhs, label in (("S2", "S3", "hierarchy (both vs flat, ignoring DP)"),
                            ("S3", "S4", "privacy cost at fixed topology")):
        a_, b_ = get(lhs, "macro_auc"), get(rhs, "macro_auc")
        if a_ is not None and b_ is not None:
            print(f"    {lhs} → {rhs}   ΔAUROC {b_ - a_:+.4f}   ({label})")
        else:
            print(f"    {lhs} → {rhs}   —   ({label}; needs both arms)")

    print(f"\nWritten: {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
