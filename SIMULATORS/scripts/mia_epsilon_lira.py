#!/usr/bin/env python
"""
mia_epsilon_lira.py — LiRA record-vs-patient attack across a privacy budget sweep.

WHY THIS EXISTS
---------------
The patient-MIA hypothesis (N-A) was tested at eps=1 and refuted: the paired
record-minus-patient gap was +0.0325 with a CI covering zero on all four attack
variants, against a predicted ~0.20.

The diagnostic that came with that null is the reason for this script. On the
patient arm LiRA ADDED NOTHING over a plain loss threshold (-0.0071). That is
what a defence with no signal left to recover looks like — and at eps=1
(sigma=11.33) the RECORD arm is nearly as quiet. Both arms sit so close to
chance that a real difference between them has no room to appear.

So the hypothesis may not be wrong; it may have been tested where nothing is
visible. Loosening the budget leaves membership signal in both arms, and the
record-vs-patient difference — if it exists — has space to show. This script
runs the same audit at eps in {4, 8, 16} and reports the gap AS A CURVE IN
EPSILON rather than as one number.

WHAT IT DOES
------------
For each epsilon, for each arm in {sample, patient}:
  1. targets — reuse the checkpoint if present, otherwise train it. The recipe
     is READ FROM AN EXISTING mia_sweep run_metadata.json and only epsilon,
     seed, arm and output paths are substituted, so a target trained here is
     recipe-identical to the eps=4/8 targets already on disk. Nothing about the
     training configuration is hardcoded in this file.
  2. attack — hand the arm to scripts/lira_attack.py, which derives each
     shadow's recipe from its own target's metadata and skips shadows already
     completed (so an interrupted run resumes).
Then it pools every epsilon into one CSV and prints the paired
record-minus-patient gap per epsilon, which is the actual research question.

PRE-REGISTERED READING — fix this before looking at the output
--------------------------------------------------------------
  * The positive control stands at 0.6277 (head-only, no DP). Any arm whose
    best attack exceeds it is leaking more than a model known to memorise.
  * A gap is only reportable if its CI excludes zero. Three seeds is few;
    expect wide intervals and do not read an interval that covers zero as
    support merely because the sign is right.
  * MONOTONICITY IS THE CLAIM. A single significant epsilon is weak evidence.
    The gap growing as the budget loosens is the prediction; that pattern is
    what would revive N-A, and its absence across all three is what would
    close it for good.
  * Report TPR at 0.1 % FPR alongside AUC. Mean AUC hides the confident-
    identification tail, and that tail is the clinical disclosure.

This does NOT resurrect the eps=1 claim either way. At eps=1 the effect is
refuted and stays refuted; a positive finding here would say the vulnerability
is real but only at budgets looser than the one the system actually ships.

Usage
-----
    python scripts/mia_epsilon_lira.py --dataset vitaldb \
        --epsilons 4.0 8.0 16.0 --seeds 42 43 44 --n_shadows 16

    # see the plan and the cost without running anything
    python scripts/mia_epsilon_lira.py --plan_only
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SIM = _HERE.parent
sys.path.insert(0, str(_SIM / "data" / "loaders"))

from datasets import REGISTRY, get_spec  # noqa: E402

ARMS = ("sample", "patient")

# Per-shadow wall-clock measured during the eps=1 LiRA run, used only to print
# a cost estimate. Loosening epsilon does not change the step count, so these
# carry over.
_MIN_PER_SHADOW = {"sample": 11.0, "patient": 38.0}


def _eps_tag(eps: float) -> str:
    """mia_sweep names checkpoints with a one-decimal tag: eps4.0, eps16.0."""
    return f"eps{eps:.1f}"


def _find_recipe(sweep_dir: Path) -> list[str]:
    """Recover the training argv from an existing mia_sweep run.

    Reading the recipe rather than restating it is what keeps a newly trained
    eps=16 target comparable to the eps=4/8 targets already on disk. If this
    file carried its own copy of the hyperparameters they could drift from the
    runs they are supposed to match, and nothing would flag it.
    """
    metas = sorted(sweep_dir.glob("run_metadata_*.json"))
    if not metas:
        raise SystemExit(
            f"[FATAL] no run_metadata_*.json under {sweep_dir}.\n"
            f"        The training recipe is read from a previous mia_sweep "
            f"run; without one there is nothing to copy and the targets would "
            f"not be comparable. Run the eps=4/8 sweep first.")
    argv = json.load(open(metas[0]))["argv"]
    if not argv or "hfl_trainer.py" not in argv[0]:
        raise SystemExit(f"[FATAL] {metas[0]} does not look like a trainer run.")
    return list(argv)


def _subst(argv: list[str], *, eps: float, seed: int, arm: str,
           ckpt: Path, out_csv: Path) -> list[str]:
    """Return the recipe with only budget, seed, arm and paths replaced."""
    out, i = [], 0
    swap = {"--epsilon": f"{eps}", "--seed": str(seed), "--dp_unit": arm,
            "--save_checkpoint": str(ckpt), "--output": str(out_csv)}
    while i < len(argv):
        tok = argv[i]
        if tok in swap:
            out += [tok, swap.pop(tok)]
            i += 2
            continue
        out.append(tok)
        i += 1
    for flag, val in swap.items():           # flags absent from the source run
        out += [flag, val]
    return out


def _run(cmd: list[str], *, cwd: Path, dry: bool) -> None:
    printable = " ".join(str(c) for c in cmd)
    print(f"    $ {printable}", flush=True)
    if dry:
        return
    r = subprocess.run([sys.executable, "-u", *cmd], cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(f"[FATAL] command failed ({r.returncode}): {printable}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--epsilons", type=float, nargs="+", default=[4.0, 8.0, 16.0],
                    help="budgets to audit. eps=1 is deliberately absent: it is "
                         "already answered and refuted")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
    ap.add_argument("--n_shadows", type=int, default=16)
    ap.add_argument("--split_seed", type=int, default=7,
                    help="must match the eps=1 run (7) or the eps arms are not "
                         "comparable to the result they are being contrasted with")
    ap.add_argument("--sweep_dir", default=None,
                    help="default: results/phase5/mia_sweep/<dataset>")
    ap.add_argument("--out_root", default=None,
                    help="default: results/phase5/lira_eps/<dataset>")
    ap.add_argument("--plan_only", action="store_true",
                    help="print what would run, and the cost, then stop")
    ap.add_argument("--skip_train", action="store_true",
                    help="fail instead of training a missing target")
    a = ap.parse_args()

    get_spec(a.dataset)                       # validates the dataset name

    sweep_dir = Path(a.sweep_dir) if a.sweep_dir else \
        _SIM / "results" / "phase5" / "mia_sweep" / a.dataset
    if not sweep_dir.is_absolute():
        sweep_dir = _SIM / sweep_dir
    out_root = Path(a.out_root) if a.out_root else \
        _SIM / "results" / "phase5" / "lira_eps" / a.dataset
    if not out_root.is_absolute():
        out_root = _SIM / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    recipe = _find_recipe(sweep_dir)

    # ── plan ────────────────────────────────────────────────────────────────
    missing, present, shadow_min = [], 0, 0.0
    for eps in a.epsilons:
        for arm in a.arms:
            shadow_min += a.n_shadows * _MIN_PER_SHADOW[arm]
            for seed in a.seeds:
                ck = sweep_dir / f"ckpt_{arm}_{_eps_tag(eps)}_seed{seed}.pt"
                (present := present + 1) if ck.exists() else missing.append(ck)

    print("=" * 74)
    print(f"  LiRA epsilon sweep — {a.dataset}")
    print("=" * 74)
    print(f"  budgets        : {', '.join(str(e) for e in a.epsilons)}")
    print(f"  arms           : {', '.join(a.arms)}")
    print(f"  seeds          : {', '.join(str(s) for s in a.seeds)}")
    print(f"  shadows / arm  : {a.n_shadows}")
    print(f"  targets present: {present}")
    print(f"  targets to train: {len(missing)}")
    for m in missing:
        print(f"      - {m.name}")
    print(f"\n  estimated shadow time: {shadow_min/60:.1f} h"
          f"  (+ target training)")
    print(f"  resumable: completed shadows are skipped on re-run\n")
    if a.plan_only:
        return
    if missing and a.skip_train:
        raise SystemExit("[FATAL] --skip_train set but targets are missing.")

    # ── targets ─────────────────────────────────────────────────────────────
    for eps in a.epsilons:
        for arm in a.arms:
            for seed in a.seeds:
                tag = _eps_tag(eps)
                ck = sweep_dir / f"ckpt_{arm}_{tag}_seed{seed}.pt"
                if ck.exists():
                    continue
                print(f"[train] {arm} {tag} seed{seed}")
                _run(_subst(recipe, eps=eps, seed=seed, arm=arm, ckpt=ck,
                            out_csv=sweep_dir / f"{arm}_{tag}_seed{seed}.csv"),
                     cwd=_SIM, dry=False)

    # ── attacks ─────────────────────────────────────────────────────────────
    for eps in a.epsilons:
        tag = _eps_tag(eps)
        for arm in a.arms:
            odir = out_root / tag
            odir.mkdir(parents=True, exist_ok=True)
            print(f"\n[attack] {arm} @ {tag}")
            _run(["scripts/lira_attack.py",
                  "--dataset", a.dataset,
                  "--arms", arm,
                  "--seeds", *[str(s) for s in a.seeds],
                  "--target_dir", str(sweep_dir),
                  "--ckpt_pattern", "ckpt_{arm}_" + tag + "_seed{seed}.pt",
                  "--out_dir", str(odir),
                  "--n_shadows", str(a.n_shadows),
                  "--split_seed", str(a.split_seed)],
                 cwd=_SIM, dry=False)

    # ── pool ────────────────────────────────────────────────────────────────
    pooled, fields = [], None
    for eps in a.epsilons:
        tag = _eps_tag(eps)
        for arm in a.arms:
            f = out_root / tag / f"lira_{a.dataset}_{arm}.csv"
            if not f.exists():
                print(f"[warn] missing {f} — arm omitted from the pooled table")
                continue
            for row in csv.DictReader(open(f)):
                row["epsilon"] = eps
                fields = fields or ["epsilon", *row]
                pooled.append(row)

    if not pooled:
        raise SystemExit("[FATAL] no per-arm CSVs found; nothing to pool.")

    pooled_csv = out_root / f"lira_eps_sweep_{a.dataset}.csv"
    with open(pooled_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(pooled)

    print("\n" + "=" * 74)
    print("  POOLED — paired record-minus-patient gap by budget")
    print("=" * 74)
    print("  Read the CURVE, not any single row. Monotone growth in epsilon is")
    print("  the prediction; a lone significant point is not.")
    print(f"\n  written: {pooled_csv.relative_to(_SIM)}")
    print(f"\n  Now run the paired statistics:")
    print(f"    python scripts/run_statistics.py --input "
          f"{pooled_csv.relative_to(_SIM)} --group epsilon --paired arm")
    print("\n  Compare every arm against the standing positive control, 0.6277.")


if __name__ == "__main__":
    main()
