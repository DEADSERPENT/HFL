"""
component_ablation.py — Phase 6 deliverable D6.2 (Phase 6.txt §6.3).

The proposed system claims five components. This removes one at a time and
measures what breaks, which is the only way to show none of them is redundant:

  C1  two-tier hierarchical aggregation
  C2  differential privacy (eps <= 1)
  C3  gradient sparsification (top-20 %)
  C4  8-bit quantization
  C5  multimodal late fusion

  ┌──────┬────┬────┬────┬────┬────┬────────────────────────────────┐
  │ A0   │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ full system                    │
  │ A1   │ ✗  │ ✓  │ ✓  │ ✓  │ ✓  │ flat tier                      │
  │ A2   │ ✓  │ ✗  │ ✓  │ ✓  │ ✓  │ no DP                          │
  │ A3   │ ✓  │ ✓  │ ✗  │ ✓  │ ✓  │ dense updates                  │
  │ A4   │ ✓  │ ✓  │ ✓  │ ✗  │ ✓  │ float32 updates                │
  │ A5   │ ✓  │ ✓  │ ✓  │ ✓  │ ✗  │ single modality                │
  ├──────┴────┴────┴────┴────┴────┼────────────────────────────────┤
  │ A6   A0 + ASWA aggregation    │ INCLUSION arm, not an ablation │
  └───────────────────────────────┴────────────────────────────────┘

Every arm is one hfl_trainer invocation with the same seed, rounds, data and
partitions — only the flag under test changes. Nothing is re-implemented here,
so an ablation arm cannot drift from the system it is ablating.

Two arms need explanation.

A1 (flat) is expressed as --n_edges 1 --tau_e 1. With a single edge that
aggregates every round, the edge tier collapses into the cloud tier and the
topology is behaviourally flat. It is an approximation of a true single-tier
implementation, and it is labelled as such in the output rather than presented
as an independent flat-FL implementation.

A2 (no DP) uses --no_dp, NOT a large --epsilon. A loose budget still clips
per-sample gradients, so it measures "what does a weak guarantee cost", not
"what does privacy cost at all" — and it would understate C2's true cost.

A5 (no fusion) is not run here. Retraining a genuinely unimodal system is what
scripts/modality_ablation.py already does, with its own encoder-width controls;
this script reads that result instead of producing a second, differently-built
answer to the same question.

A6 (ASWA) is an INCLUSION arm and is labelled as one, because the trainer
defaults to --agg_mode fedavg: A0 does not contain ASWA, so there is nothing to
remove. ASWA is a surviving component of the scrapped PHANTOM-FL design that
has never been measured, which is the only reason it is still listed as a
limitation. Running it as an inclusion arm retires that limitation whichever
way the number falls — it either becomes a measured contribution, or it is
deleted with evidence rather than dropped in silence.

The sign convention therefore INVERTS for A6. For an ablation arm a drop
against A0 means the component contributes; for an inclusion arm a RISE means
it contributes. Reporting both under one rule would invert the conclusion.
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
from datasets import get_spec, REGISTRY                      # noqa: E402


# Smallest AUROC difference this design can resolve. Each arm is one seed, so
# this is a floor on interpretation, not a significance test — see the verdict
# block in main(). Justified against the five-seed comparisons in phase5, where
# seed spread on this task is of this order.
NOISE_FLOOR = 0.01

# component → the flag that REMOVES it
ARMS = {
    "A0": dict(label="full system", removes=None, flags=[]),
    "A1": dict(label="no C1 — flat tier", removes="C1",
               flags=["--n_edges", "1", "--tau_e", "1"]),
    "A2": dict(label="no C2 — no DP", removes="C2", flags=["--no_dp"]),
    "A3": dict(label="no C3 — dense (no top-k)", removes="C3",
               flags=["--sparsity", "1.0"]),
    "A4": dict(label="no C4 — float32 (no quant)", removes="C4",
               flags=["--quant_bits", "32"]),
    "A5": dict(label="no C5 — unimodal", removes="C5", flags=None),  # external
    # Inclusion arm: 'adds' rather than 'removes', which flips how its delta
    # against A0 is read. See the module docstring.
    "A6": dict(label="+ ASWA aggregation", removes=None, adds="C6",
               flags=["--agg_mode", "aswa"]),
}


def read_last_row(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else {}


def read_arm_metrics(csv_path):
    """Test metrics for one arm, plus the run's cost columns.

    The trainer writes VALIDATION metrics per round into the CSV and the TEST
    metrics — computed once on the checkpoint validation selected, which is
    usually not the last round — into a `<output>_final.json` sidecar beside it.
    Reading `test_*` out of the CSV therefore returns nothing at all, which is
    exactly what this script used to do: every arm came back empty and the
    comparison table printed a column of dashes.

    Uplink is summed over rounds from `uplink_bytes` and converted here; there
    is no `uplink_mb` column and never was.
    """
    out = {}
    sidecar = Path(os.path.splitext(csv_path)[0] + "_final.json")
    if sidecar.exists():
        d = json.loads(sidecar.read_text())
        t = d.get("test", {})
        out.update(
            test_accuracy=t.get("accuracy"),
            test_macro_auc=t.get("macro_auc"),
            test_auprc=t.get("auprc"),
            test_case_auc=t.get("case_auc"),
            epsilon_spent=d.get("epsilon_spent"),
            selected_round=d.get("selected_round"),
            best_val=d.get("best_val"),
            uplink_mb=(round(d["uplink_bytes_total"] / 1e6, 3)
                       if d.get("uplink_bytes_total") else None),
        )
        return out

    # No sidecar: the run predates it. The trainer has always stored the same
    # test metrics inside the checkpoint, so a completed older run is fully
    # recoverable and does not need to be repeated. This costs a torch.load of
    # the weights, which is why it is the fallback and not the primary path.
    ckpt = csv_path.parent / f"ckpt_{csv_path.stem.replace('ablation_', '')}.pt"
    rows = list(csv.DictReader(open(csv_path))) if os.path.exists(csv_path) else []
    if ckpt.exists():
        try:
            import torch
            d = torch.load(ckpt, map_location="cpu", weights_only=False)
            t = d.get("test_metrics") or {}
            if t:
                out.update(
                    test_accuracy=t.get("accuracy"),
                    test_macro_auc=t.get("macro_auc"),
                    test_auprc=t.get("auprc"),
                    test_case_auc=t.get("case_auc"),
                    epsilon_spent=(rows[-1].get("epsilon_spent") if rows else None),
                    uplink_mb=round(sum(int(r.get("uplink_bytes") or 0)
                                        for r in rows) / 1e6, 3) or None,
                    source=f"{ckpt.name} (pre-sidecar run)",
                )
                return out
        except Exception as e:
            print(f"  [warn] could not read {ckpt.name}: {e}")

    # Neither artefact: the run did not finish. Report the validation figures
    # under their own names rather than silently passing them off as test
    # metrics, and let the summary mark the arm incomplete.
    if rows:
        last = rows[-1]
        out.update(
            val_macro_auc=last.get("val_macro_auc"),
            val_auprc=last.get("val_auprc"),
            epsilon_spent=last.get("epsilon_spent"),
            uplink_mb=round(sum(int(r.get("uplink_bytes") or 0)
                                for r in rows) / 1e6, 3),
            incomplete="no _final.json or checkpoint — test metrics unavailable",
        )
    return out



def _train_one(a, arm, cfg, seed, csv_path, out_dir, enc, log_dir, results):
    """Train one (arm, seed) and record its metrics.

    NO --local_epochs: hfl_trainer.py does not define that flag (it fixes one
    local epoch per FL call, hardcoded into its own DP accounting). Passing it
    made argparse reject the command, so every arm that trains was failing
    silently behind a printed usage message.
    """
    argv = [sys.executable, str(_SIM / "model" / "training" / "hfl_trainer.py"),
            "--dataset", a.dataset, "--rounds", str(a.rounds),
            "--batch_size", str(a.batch_size), "--seed", str(seed),
            "--epsilon", str(a.epsilon),
            "--epsilon_conf", str(a.epsilon_conf),
            "--freeze_encoders", "--pretrained_encoders", enc,
            "--save_checkpoint", str(out_dir / f"ckpt_{arm}_seed{seed}.pt"),
            "--output", str(csv_path)] + cfg["flags"]

    print("\n" + "=" * 78)
    print(f"  \u25b6 {arm} seed {seed} — {cfg['label']}")
    print("=" * 78)
    print("  $ " + " ".join(argv), flush=True)
    if a.dry_run:
        return

    t0 = time.time()
    # PYTHONUNBUFFERED: the child block-buffers its stdout when it is a pipe
    # rather than a terminal, so without this the arm log stays empty until the
    # process exits. On a multi-hour run that makes a live job
    # indistinguishable from a hung one.
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    with open(log_dir / f"{arm}_seed{seed}.log", "w") as lf:
        proc = subprocess.Popen(argv, cwd=str(_SIM), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1,
                                env=env)
        for line in proc.stdout:
            sys.stdout.write(line)
            lf.write(line)
            sys.stdout.flush()
            lf.flush()
        proc.wait()
    if proc.returncode != 0:
        print(f"  \u2717 {arm} seed {seed} FAILED (exit {proc.returncode})")
        return
    row = read_arm_metrics(csv_path)
    row.update(arm=arm, seed=seed, label=cfg["label"],
               removes=cfg["removes"] or "\u2014", adds=cfg.get("adds") or "",
               seconds=round(time.time() - t0, 1))
    results.append(row)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--arms", nargs="*", default=list(ARMS),
                   help="subset of A0..A6 (A6 is an inclusion arm)")
    ap.add_argument("--rounds", type=int, default=10)
    # No --local_epochs. hfl_trainer.py has no such flag: it fixes one local
    # epoch per FL call because its DP accounting depends on that. Accepting the
    # option here would let a caller believe they had set something.
    # 64 matches the published system. Batch size is not a free knob under DP:
    # it sets the sampling rate q = B/N, which drives the RDP accounting, so at
    # 16 the same --epsilon 0.80 budget was spending 0.7987 instead of the
    # paper's 0.7705 and A0 scored 0.8463 against the reported 0.8429. The
    # ablation has to characterise the system the paper describes.
    ap.add_argument("--batch_size", type=int, default=64)
    # Defaults are the operating point the paper reports, so the ablation sits
    # at the same budget as every other published number: --epsilon 0.80 is the
    # TRAINING target (the run spends 0.7705 of it) and --epsilon_conf 0.20 is
    # charged for the conformal quantile release, composing to 0.9705 <= 1.
    # Earlier arms ran at 1.0/0.5, composing to 1.498 — a different point, which
    # would have made the ablation incomparable with the rest of the study.
    ap.add_argument("--epsilon", type=float, default=0.80)
    ap.add_argument("--epsilon_conf", type=float, default=0.20)
    # Multiple seeds, because a single run cannot resolve any delta smaller
    # than the seed spread (~0.01 AUROC here) and most component effects are
    # smaller than that. With one seed this table could only ever support
    # communication claims.
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--pretrained_encoders", default=None)
    ap.add_argument("--output_dir", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    spec = get_spec(a.dataset)
    out_dir = Path(a.output_dir or _SIM / "results" / "phase6" / a.dataset)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir = out_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    enc = a.pretrained_encoders or str(
        _SIM / "checkpoints" / f"pretrained_encoders_{a.dataset}.pt")

    unknown = [x for x in a.arms if x not in ARMS]
    if unknown:
        raise SystemExit(f"unknown arm(s) {unknown}; available {list(ARMS)}")
    if not os.path.exists(enc) and not a.dry_run:
        raise SystemExit(
            f"[ablation][FATAL] pretrained encoders missing:\n  {enc}\n"
            f"Every arm uses the head-only recipe, so all of them would freeze "
            f"RANDOM encoders and the whole table would be meaningless.\n"
            f"Run: python model/training/pretrain_encoders.py --dataset {a.dataset}")

    print("=" * 78)
    print(f"COMPONENT ABLATION — {a.dataset.upper()}   (Phase 6, D6.2)")
    print("=" * 78)
    print(spec)
    print(f"  arms   : {a.arms}")
    print(f"  rounds : {a.rounds}   seeds: {a.seeds}")
    print(f"  budget : train eps<={a.epsilon} + conformal {a.epsilon_conf} "
          f"= {a.epsilon + a.epsilon_conf:.2f} composed")
    print(f"  output : {out_dir}")

    results = []
    for arm in a.arms:
        cfg = ARMS[arm]
        csv_path = out_dir / f"ablation_{arm}.csv"

        if arm == "A5":
            src = _SIM / "results" / "phase5" / f"ablation_{a.dataset}.json"
            if not src.exists():
                print(f"\n  ⊘ A5 skipped — {src.name} not found. "
                      f"Run: python scripts/modality_ablation.py "
                      f"--dataset {a.dataset}")
                continue
            d = json.loads(src.read_text())
            # Best single modality = the system with fusion removed.
            best = max(("a", "b"),
                       key=lambda m: sum(r["auroc"] for r in d["runs"][m]))
            rs = d["runs"][best]
            row = {"arm": "A5", "label": cfg["label"], "removes": "C5",
                   "test_macro_auc": sum(r["auroc"] for r in rs) / len(rs),
                   "test_auprc": sum(r["auprc"] for r in rs) / len(rs),
                   "test_accuracy": sum(r["acc"] for r in rs) / len(rs),
                   "source": f"modality_ablation.json (arm '{best}')"}
            results.append(row)
            with open(csv_path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(row)); w.writeheader(); w.writerow(row)
            print(f"\n  ⊙ A5 taken from {src.name} (unimodal arm '{best}')")
            continue

        for seed in a.seeds:
            csv_path = out_dir / f"ablation_{arm}_seed{seed}.csv"
            # Runs made before this script took seeds are named without one.
            # Adopt them as the first seed rather than discarding hours of
            # equivalent compute.
            legacy = out_dir / f"ablation_{arm}.csv"
            if seed == a.seeds[0] and legacy.exists() and not csv_path.exists():
                for suf in ("", "_final.json"):
                    src = (out_dir / f"ablation_{arm}{suf}" if suf
                           else legacy)
                    dst = (out_dir / f"ablation_{arm}_seed{seed}{suf}" if suf
                           else csv_path)
                    if src.exists():
                        src.rename(dst)
                ck = out_dir / f"ckpt_{arm}.pt"
                if ck.exists():
                    ck.rename(out_dir / f"ckpt_{arm}_seed{seed}.pt")
                print(f"\n  ⊙ adopted pre-seed run of {arm} as seed {seed}")

            if csv_path.exists() and not a.force:
                print(f"\n  ⊙ {arm} seed {seed} cached — {csv_path.name}")
                row = read_arm_metrics(csv_path)
                row.update(arm=arm, seed=seed, label=cfg["label"],
                           removes=cfg["removes"] or "—", adds=cfg.get("adds") or "")
                results.append(row)
                continue
            _train_one(a, arm, cfg, seed, csv_path, out_dir, enc, log_dir, results)
        continue

    if a.dry_run:
        return 0

    # ── combined table ──────────────────────────────────────────────
    combined = out_dir / "ablation.csv"
    fields = ["arm", "label", "removes", "adds", "test_accuracy",
              "test_macro_auc", "test_auprc", "test_case_auc", "epsilon_spent",
              "uplink_mb", "selected_round", "best_val", "seconds", "source",
              "incomplete"]
    with open(combined, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k, "") for k in fields})

    print("\n" + "=" * 78)
    print(f"ABLATION SUMMARY — {a.dataset}")
    print("=" * 78)
    def fnum(r, k):
        try:
            return float(r.get(k, ""))
        except (TypeError, ValueError):
            return None

    # Group by arm; each arm now holds one row per seed.
    by_arm = {}
    for r in results:
        by_arm.setdefault(r.get("arm"), []).append(r)

    try:
        sys.path.insert(0, str(_SIM / "scripts"))
        from run_statistics import mean_ci, paired_test      # noqa: E402
    except Exception:
        mean_ci = paired_test = None

    hdr = (f"{'arm':<5}{'removes':<9}{'label':<26}{'n':>3}"
           f"{'AUROC':>18}{'AUPRC':>18}")
    print(hdr); print("-" * len(hdr))
    for arm in [x for x in ARMS if x in by_arm]:
        rows = by_arm[arm]
        au = [fnum(r, "test_macro_auc") for r in rows]
        ap_ = [fnum(r, "test_auprc") for r in rows]
        au = [v for v in au if v is not None]
        ap_ = [v for v in ap_ if v is not None]
        def fmt(vals):
            if not vals:
                return f"{'—':>18}"
            if mean_ci and len(vals) > 1:
                m, h, _ = mean_ci(vals)
                return f"{m:>11.4f}±{h:<6.4f}"
            return f"{vals[0]:>18.4f}"
        print(f"{arm:<5}{rows[0].get('removes','—'):<9}"
              f"{str(rows[0].get('label',''))[:25]:<26}{len(au):>3}"
              f"{fmt(au)}{fmt(ap_)}")

    missing = [arm for arm, rows in by_arm.items()
               if not any(fnum(r, "test_macro_auc") is not None for r in rows)]
    if missing:
        print(f"\n  \u26a0 no test metrics for {missing} — did not complete. "
              f"Re-run with --force before reading the comparison below.")

    a0_rows = by_arm.get("A0", [])
    if a0_rows and paired_test:
        print("\n  effect of each component (paired against A0 by seed):")
        base = {r["seed"]: fnum(r, "test_macro_auc") for r in a0_rows
                if fnum(r, "test_macro_auc") is not None}
        for arm in [x for x in ARMS if x in by_arm and x not in ("A0", "A5")]:
            rows = by_arm[arm]
            pairs = [(base[r["seed"]], fnum(r, "test_macro_auc"))
                     for r in rows if r.get("seed") in base
                     and fnum(r, "test_macro_auc") is not None]
            if not pairs:
                continue
            b = [x for x, _ in pairs]
            v = [y for _, y in pairs]
            tag = f"+{rows[0]['adds']}" if rows[0].get("adds") else rows[0]["removes"]
            if len(pairs) < 2:
                d = v[0] - b[0]
                note = (f"   \u2190 n=1, unresolvable" if abs(d) < NOISE_FLOOR
                        else f"   \u2190 n=1, needs seeds to confirm")
                print(f"    {tag:<4} {str(rows[0].get('label',''))[:32]:<34}"
                      f"\u0394AUROC {d:+.4f}{note}")
                continue
            t = paired_test(b, v)          # reports v vs b
            d, lo, hi = t["mean_diff"], t["ci_low"], t["ci_high"]
            # An interval spanning zero is unresolved regardless of the point
            # estimate. The sign convention inverts for an INCLUSION arm: for
            # an ablation a drop means the component helps; for A6 a rise does.
            if not t["significant"]:
                verdict = "   \u2190 interval spans zero — unresolved"
            elif rows[0].get("adds"):
                verdict = ("   \u2190 contributes" if d > 0 else
                           "   \u2190 no contribution — drop it")
            else:
                verdict = ("   \u2190 component contributes" if d < 0 else
                           "   \u2190 removing it did not hurt")
            print(f"    {tag:<4} {str(rows[0].get('label',''))[:32]:<34}"
                  f"\u0394AUROC {d:+.4f} [{lo:+.4f},{hi:+.4f}] n={t['n']}"
                  + verdict)
        print(f"\n  Intervals are Student-t over seeds {a.seeds}. A delta whose "
              f"interval covers zero is not a finding, whatever its sign.")

    # C5 reported from its own experiment, where the comparison is internally
    # controlled, rather than as a difference against a system it does not share
    # an operating point with.
    src = _SIM / "results" / "phase5" / f"ablation_{a.dataset}.json"
    if src.exists():
        d = json.loads(src.read_text())
        v = d.get("verdict", {})
        print(f"\n  C5 (fusion) — measured separately, centralised and "
              f"non-private, {len(d.get('seeds', []))} seeds:")
        print(f"    fusion vs best single modality: "
              f"ΔAUROC {d.get('fusion_gain_auroc', float('nan')):+.4f}  "
              f"ΔAUPRC {d.get('fusion_gain_auprc', float('nan')):+.4f}")
        if v.get("gain_over_sd") is not None:
            print(f"    {v['gain_over_sd']:.1f}x the seed standard deviation")
        print(f"    NOT differenced against A0: that arm carries no DP and no "
              f"federation, so the gap would not be attributable to fusion.")
    print("\n" + "=" * 78)
    print(f"Combined table: {combined}")
    print("NOTE: A1 approximates a flat tier via --n_edges 1 --tau_e 1; "
          "it is not a separate single-tier implementation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
