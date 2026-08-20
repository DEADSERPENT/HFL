"""
epsilon_sweep.py — the privacy–utility curve (deliverable D5.12).

This is the central experiment of the thesis: how does utility move as the
privacy budget tightens, and does the head-only recipe change the shape of that
curve? For each eps it runs BOTH private recipes on identical data:

    full   : DP-SGD over the whole model         (the B4 recipe / prior art)
    head   : frozen pretrained encoders + DP-SGD on the fusion head only
             (the proposed recipe)

plus one eps=inf reference (no DP) so the curve has an anchor for "what does
privacy cost at all". The interesting result is not either curve alone but the
GAP between them as eps shrinks: if head-only DP is the contribution, that gap
must widen as the budget tightens.

Implementation note — this file deliberately contains no training loop. It
delegates to baselines.run_dp_fedavg / run_fedavg so that the sweep, the
baselines and the proposed model are scored by the same code on the same
partitions. The previous version had its own loop that (a) re-sliced the raw
dataset with range(0, 0.7n), bypassing the partition files and their leakage
controls, (b) hardcoded n_devices=10 "for sweep speed" instead of the real
topology, (c) never used a val split, so it reported the last round rather than
the selected one, and (d) called roc_auc_score(multi_class="ovr") on a binary
task, whose exception branch returned auc=0.0. Any curve it produced compared
the sweep against itself, not against the rest of the pipeline.
"""

import os
import sys
import csv
import json
import time
import argparse
from pathlib import Path

import numpy as np

_MODEL_ROOT = Path(__file__).parent.parent
for _sub in ("privacy", "architecture", "training", "deploy", "utils"):
    sys.path.insert(0, str(_MODEL_ROOT / _sub))
sys.path.insert(0, str(_MODEL_ROOT.parent / "data" / "loaders"))

from device_utils import get_device, optimize_gpu, set_seed          # noqa: E402
from datasets import get_spec                                        # noqa: E402
from baselines import (build_loaders, compute_class_weight,          # noqa: E402
                       run_dp_fedavg, run_fedavg, _save_csv)


def _parse_eps(tokens):
    """Accept 'inf' anywhere in the list; keep it last so the reference row
    is written after the private points."""
    out = []
    for t in tokens:
        out.append(float("inf") if str(t).lower() in ("inf", "none", "nodp")
                   else float(t))
    return sorted(out, key=lambda e: (e == float("inf"), e))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True,
                    choices=["wear", "vitaldb"])
    ap.add_argument("--data_dir", default=None)
    ap.add_argument("--partition_dir", default=None)
    ap.add_argument("--output_dir", default=None,
                    help="default: results/phase5/epsilon_sweep/<dataset>")
    ap.add_argument("--epsilons", nargs="+", default=["0.5", "1.0", "2.0", "4.0", "8.0", "inf"])
    ap.add_argument("--recipes", nargs="+", default=["full", "head"],
                    choices=["full", "head"],
                    help="which private recipes to sweep")
    ap.add_argument("--pretrained_encoders", default=None,
                    help="required for the 'head' recipe; default resolves to "
                         "checkpoints/pretrained_encoders_<dataset>.pt")
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--local_epochs", type=int, default=1)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--delta", type=float, default=1e-5)
    ap.add_argument("--max_grad_norm", type=float, default=1.0)
    ap.add_argument("--max_physical_batch_size", type=int, default=0,
                    help="0 = no micro-batching. The full-model recipe holds a "
                         "per-sample gradient for EVERY parameter, so on the "
                         "larger model it OOMs at batch 64 and the whole sweep "
                         "dies. Splitting keeps the LOGICAL batch — and the "
                         "privacy accounting — unchanged.")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--class_weight", choices=["none", "balanced", "auto"], default="auto")
    ap.add_argument("--select_on", choices=["auc", "auprc", "auto"], default="auto")
    ap.add_argument("--resume", action="store_true",
                    help="skip (eps, recipe, seed) combinations already in the CSV")
    args = ap.parse_args()

    spec = get_spec(args.dataset)
    if args.data_dir or args.partition_dir:
        import dataclasses
        spec = dataclasses.replace(
            spec, data_dir=args.data_dir or spec.data_dir,
            partition_dir=args.partition_dir or spec.partition_dir)

    _sim = Path(_MODEL_ROOT).parent
    out_dir = args.output_dir or str(_sim / "results" / "phase5" /
                                     "epsilon_sweep" / args.dataset)
    os.makedirs(out_dir, exist_ok=True)
    if args.select_on == "auto":
        args.select_on = "auprc" if spec.n_classes == 2 else "auc"
    use_cw = (args.class_weight == "balanced" or
              (args.class_weight == "auto" and spec.n_classes == 2))
    ckpt = args.pretrained_encoders or str(
        _sim / "checkpoints" / f"pretrained_encoders_{args.dataset}.pt")

    if "head" in args.recipes and not os.path.exists(ckpt):
        raise SystemExit(
            f"[sweep][FATAL] the 'head' recipe needs pretrained encoders and none "
            f"were found at:\n  {ckpt}\n"
            f"Run:  python model/training/pretrain_encoders.py --dataset {args.dataset}\n"
            f"Freezing RANDOM encoders would measure nothing, so this is fatal "
            f"rather than a warning.")

    epsilons = _parse_eps(args.epsilons)
    device = get_device()
    optimize_gpu()
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)

    print("=" * 74)
    print(f"EPSILON SWEEP — {args.dataset.upper()}")
    print("=" * 74)
    print(spec)
    print(f"  epsilons : {['inf' if e == float('inf') else e for e in epsilons]}")
    print(f"  recipes  : {args.recipes}   seeds: {args.seeds}   rounds: {args.rounds}")
    print(f"  select_on: {args.select_on}   class_weight: {use_cw}")
    print(f"  output   : {out_dir}")

    full_ds, n_dev, device_loaders, pooled, order, group_test = build_loaders(
        spec, args.batch_size, device)
    cw = compute_class_weight(full_ds, order["train"], spec.n_classes) if use_cw else None

    from hfl_mm_model import (build_hfl_mm_hc, freeze_encoders,   # noqa: E402
                              load_pretrained_encoders)
    _kw = {"n_channels_a": spec.n_channels_a}
    if spec.modality_b != "image":
        _kw.update(modality_b="features", feat_b_dim=spec.feat_b_dim)

    def model_full():
        return build_hfl_mm_hc(n_classes=spec.n_classes, **_kw)

    def model_head():
        m = build_hfl_mm_hc(n_classes=spec.n_classes, **_kw)
        load_pretrained_encoders(m, ckpt)
        return freeze_encoders(m)

    csv_path = os.path.join(out_dir, "epsilon_sweep.csv")
    done = set()
    rows = []
    if args.resume and os.path.exists(csv_path):
        with open(csv_path) as f:
            for r in csv.DictReader(f):
                rows.append(r)
                done.add((r["epsilon"], r["recipe"], r["seed"]))
        print(f"  resume   : {len(done)} combinations already recorded")

    fields = ["dataset", "epsilon", "recipe", "seed", "rounds", "accuracy",
              "macro_auc", "auprc", "case_auc", "case_auprc", "sigma",
              "epsilon_spent", "dp_params", "total_params", "time_s"]

    def flush():
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)

    common = dict(device=device, class_weight=cw, select_on=args.select_on,
                  group_ids=group_test)

    for seed in args.seeds:
        for eps in epsilons:
            elab = "inf" if eps == float("inf") else f"{eps:g}"
            # eps=inf is the no-DP reference, and it must be run ONCE PER
            # RECIPE — not once overall.
            #
            # The reference exists to answer "what does privacy cost?", which
            # is a PAIRED question: same architecture, same initialisation,
            # DP on versus off. A single reference built from the full model
            # with random init is not comparable to the head arm, which starts
            # from pretrained encoders. Measured on VitalDB the mismatch made
            # the no-DP reference (0.8149) score BELOW every head-only point
            # (0.8457-0.8506) — i.e. "privacy improves accuracy", which is not
            # a finding, it is a broken comparator. Objective 2 subtracts from
            # this reference, so the whole accuracy-loss claim inherits it.
            recipes = args.recipes if eps == float("inf") else args.recipes
            for rec in recipes:
                key = (elab, rec, str(seed))
                if key in done:
                    print(f"\n[skip] eps={elab} recipe={rec} seed={seed} (already done)")
                    continue
                print("\n" + "=" * 74)
                print(f"  eps={elab}  recipe={rec}  seed={seed}")
                print("=" * 74)
                set_seed(seed)
                t0 = time.time()

                if eps == float("inf"):
                    # Same model factory the private arm of this recipe uses,
                    # so the only difference is DP on/off.
                    _mf = model_head if rec == "head" else model_full
                    r = run_fedavg(_mf, device_loaders, pooled,
                                   rounds=args.rounds, local_epochs=args.local_epochs,
                                   lr=args.lr, **common)
                    r.update(sigma="", epsilon_spent="", dp_trained_params="",
                             total_params="")
                else:
                    r = run_dp_fedavg(
                        model_head if rec == "head" else model_full,
                        device_loaders, pooled, rounds=args.rounds,
                        local_epochs=args.local_epochs, lr=args.lr, epsilon=eps,
                        delta=args.delta, max_grad_norm=args.max_grad_norm,
                        head_only=(rec == "head"),
                        max_physical_batch_size=args.max_physical_batch_size,
                        label=f"eps{elab}-{rec}", **common)

                rows.append({
                    "dataset": args.dataset, "epsilon": elab, "recipe": rec,
                    "seed": seed, "rounds": args.rounds,
                    "accuracy": r.get("test_accuracy"),
                    "macro_auc": r.get("test_macro_auc"),
                    "auprc": r.get("test_auprc"),
                    "case_auc": r.get("test_case_auc", ""),
                    "case_auprc": r.get("test_case_auprc", ""),
                    "sigma": r.get("sigma", ""),
                    "epsilon_spent": r.get("epsilon_spent", ""),
                    "dp_params": r.get("dp_trained_params", ""),
                    "total_params": r.get("total_params", ""),
                    "time_s": round(time.time() - t0, 1),
                })
                flush()          # written after every point — a crash mid-sweep
                                 # must not lose the hours already spent

    # ── curve summary ────────────────────────────────────────────────
    print("\n" + "=" * 74)
    print(f"PRIVACY–UTILITY CURVE — {args.dataset}")
    print("=" * 74)
    key = "auprc" if args.select_on == "auprc" else "macro_auc"

    def mean_at(elab, rec):
        v = [float(r[key]) for r in rows
             if r["epsilon"] == elab and r["recipe"] == rec and r.get(key)
             not in ("", None) and not np.isnan(float(r[key]))]
        return float(np.mean(v)) if v else float("nan")

    hdr = f"{'eps':>6}" + "".join(f"{r:>12}" for r in args.recipes) + f"{'gap':>10}"
    print(hdr); print("-" * len(hdr))
    for eps in epsilons:
        elab = "inf" if eps == float("inf") else f"{eps:g}"
        if eps == float("inf"):
            vals = [mean_at(elab, r) for r in args.recipes]
            line = f"{elab:>6}" + "".join(f"{v:>12.4f}" for v in vals)
            print(line + "   (no-DP reference, per recipe)")
            continue
        vals = [mean_at(elab, r) for r in args.recipes]
        line = f"{elab:>6}" + "".join(f"{v:>12.4f}" for v in vals)
        if len(vals) == 2 and not any(np.isnan(vals)):
            line += f"{vals[1] - vals[0]:>+10.4f}"
        print(line)
    print(f"\n(metric = {key}; 'gap' = head-only minus full-model)")
    print(f"CSV: {csv_path}")

    with open(os.path.join(out_dir, "sweep_meta.json"), "w") as f:
        json.dump({"dataset": args.dataset, "epsilons": [
            "inf" if e == float("inf") else e for e in epsilons],
            "recipes": args.recipes, "seeds": args.seeds,
            "rounds": args.rounds, "select_on": args.select_on,
            "class_weight": use_cw, "pretrained_encoders": ckpt,
            "n_devices": n_dev, "metric": key}, f, indent=2)


if __name__ == "__main__":
    main()
