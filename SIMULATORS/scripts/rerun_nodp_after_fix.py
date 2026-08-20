"""
rerun_nodp_after_fix.py — repair every run affected by the --no_dp early-stop bug.

THE BUG
-------
hfl_trainer stopped on `cumulative_eps >= args.epsilon`. Under --no_dp the
accountant reports eps = inf, and `inf >= 0.8` is true on round 1, so every
non-private run trained for 1 round of 10 and then reported itself finished.

Nothing crashed and nothing was logged as failed, so the artefacts looked
complete. The consequence reached the paper: the MIA positive control -- the
configuration described as "non-private training of the same head", the thing
that makes the null on the private arms admissible -- was a 1-round model. A
model trained a tenth as long memorises less, so the control understated the
leakage an adversary can reach, and the comparison against the private arms
confounded DP with training duration.

WHAT THIS DOES
--------------
1. Re-trains every mia_factorial run that passed --no_dp, using that run's OWN
   recorded argv, so nothing drifts except the fixed early-stop condition.
2. Asserts each re-run actually logged its full round count. The bug's whole
   character was silent truncation, so a repair that does not verify the round
   count would be able to fail the same way.
3. Clears the head_nodp shadow set and re-runs LiRA, because a shadow must be
   trained the way its target was: 1-round shadows calibrated against a
   re-trained 10-round target would misfit every per-example Gaussian.
4. Reports the new control AUC against the published 0.6277.

Prior artefacts are archived, never deleted: they are valid measurements of a
1-round model, and the paper's revision history should be able to point at them.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

_SIM = Path(__file__).resolve().parent.parent
PUBLISHED_CONTROL_AUC = 0.6277          # results.tex, MIA table
PUBLISHED_CONTROL_ATTACK = "lira_offline"   # the variant that figure refers to


def recorded_nodp_runs(factorial_dir: Path):
    """Every (argv, output, checkpoint) that actually passed --no_dp.

    Read from run_metadata rather than reconstructed, so the re-run differs
    from the original in exactly one thing: the trainer fix.
    """
    out = []
    for f in sorted(factorial_dir.glob("run_metadata_*.json")):
        try:
            argv = json.load(open(f)).get("argv") or []
        except Exception:
            continue
        if "--no_dp" not in argv:
            continue
        g = lambda k: (argv[argv.index(k) + 1] if k in argv else None)
        out.append({"meta": f.name, "argv": argv,
                    "output": g("--output"), "ckpt": g("--save_checkpoint"),
                    "rounds": int(g("--rounds") or 0)})
    # One entry per checkpoint, newest metadata wins.
    dedup = {}
    for r in out:
        dedup[r["ckpt"]] = r
    return list(dedup.values())


def rounds_logged(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0
    with open(csv_path) as f:
        return max(0, sum(1 for _ in f) - 1)


def archive(paths, dest: Path, note: str):
    dest.mkdir(parents=True, exist_ok=True)
    moved = 0
    for p in paths:
        p = Path(p)
        if p.exists():
            shutil.move(str(p), str(dest / p.name))
            moved += 1
    (dest / "README.txt").write_text(note)
    return moved


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb")
    ap.add_argument("--factorial_dir", default=None)
    ap.add_argument("--lira_dir", default=None)
    ap.add_argument("--arm", default="head_nodp", help="LiRA arm to rebuild")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--n_shadows", type=int, default=16)
    ap.add_argument("--ckpt_pattern", default="ckpt_{arm}_seed{seed}.pt")
    ap.add_argument("--wait_for", default="component_ablation.py",
                    help="don't contend for the GPU with this process; "
                         "empty string to start immediately")
    ap.add_argument("--skip_lira", action="store_true")
    ap.add_argument("--dry_run", action="store_true")
    a = ap.parse_args()

    fac = Path(a.factorial_dir or _SIM / "results" / "phase5" / "mia_factorial" / a.dataset)
    lira = Path(a.lira_dir or _SIM / "results" / "phase5" / "lira" / a.dataset)
    stamp = time.strftime("%Y%m%d_%H%M%S")

    runs = recorded_nodp_runs(fac)
    print("=" * 78)
    print(f"RE-RUN OF --no_dp ARTEFACTS AFTER THE EARLY-STOP FIX  ({a.dataset})")
    print("=" * 78)
    if not runs:
        raise SystemExit(f"no --no_dp runs recorded in {fac}")
    print(f"  affected runs : {len(runs)}")
    for r in runs:
        got = rounds_logged(_SIM / r["output"]) if r["output"] else 0
        print(f"    {Path(r['ckpt']).name:<32} asked {r['rounds']:>2}  ran {got:>2}")

    if a.dry_run:
        print("\n  (dry run — nothing re-trained)")
        return 0

    # ── 1. archive, then re-train each with its own recipe ──────────────
    old = [_SIM / r["output"] for r in runs if r["output"]] + \
          [_SIM / r["ckpt"] for r in runs if r["ckpt"]]
    n = archive(old, fac / f"archive_1round_{stamp}",
                "Runs truncated to 1 round by the --no_dp early-stop bug "
                "(inf >= epsilon). Valid measurements of a 1-round model; "
                "superseded by full-length re-runs. See "
                "scripts/rerun_nodp_after_fix.py\n")
    print(f"\n  archived {n} prior artefact(s)")

    if a.wait_for:
        while subprocess.run(["pgrep", "-f", a.wait_for],
                             capture_output=True).returncode == 0:
            print(f"  waiting for {a.wait_for} to finish (GPU in use)…", flush=True)
            time.sleep(60)

    failures = []
    for i, r in enumerate(runs, 1):
        print("\n" + "=" * 78)
        print(f"  [{i}/{len(runs)}] {Path(r['ckpt']).name}")
        print("=" * 78, flush=True)
        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        rc = subprocess.run([sys.executable, *r["argv"]], cwd=str(_SIM), env=env)
        got = rounds_logged(_SIM / r["output"])
        # The bug was silent truncation. A repair that does not check the round
        # count could reproduce it and still look successful.
        if rc.returncode != 0 or got != r["rounds"]:
            failures.append((Path(r["ckpt"]).name, r["rounds"], got, rc.returncode))
            print(f"  ✗ expected {r['rounds']} rounds, logged {got}")
        else:
            print(f"  ✓ {got}/{r['rounds']} rounds")

    if failures:
        print("\n  FAILED:")
        for name, want, got, rc in failures:
            print(f"    {name}: asked {want}, logged {got}, exit {rc}")
        raise SystemExit("re-run incomplete — not rebuilding LiRA on bad targets")

    if a.skip_lira:
        print("\n  targets rebuilt; LiRA skipped by request")
        return 0

    # ── 2. shadows must match their target, so rebuild them ─────────────
    sdir = lira / "shadows" / a.arm
    if sdir.exists():
        moved = shutil.move(str(sdir), str(lira / "shadows" /
                                           f"{a.arm}_1round_{stamp}"))
        print(f"\n  archived 1-round shadow set -> {Path(moved).name}")
    for csv in lira.glob(f"lira_{a.dataset}_{a.arm}.csv"):
        shutil.move(str(csv), str(lira / f"{csv.stem}_1round_{stamp}.csv"))

    print("\n" + "=" * 78)
    print(f"  REBUILDING LiRA — arm {a.arm}, {a.n_shadows} shadows")
    print("=" * 78, flush=True)
    cmd = [sys.executable, str(_SIM / "scripts" / "lira_attack.py"),
           "--dataset", a.dataset, "--arms", a.arm,
           "--target_dir", str(fac), "--ckpt_pattern", a.ckpt_pattern,
           "--seeds", *[str(s) for s in a.seeds],
           "--n_shadows", str(a.n_shadows)]
    print("  $ " + " ".join(cmd[1:]), flush=True)
    rc = subprocess.run(cmd, cwd=str(_SIM),
                        env={**os.environ, "PYTHONUNBUFFERED": "1"})
    if rc.returncode != 0:
        raise SystemExit(f"LiRA rebuild failed (exit {rc.returncode})")

    # ── 3. report against what the paper currently claims ───────────────
    res = lira / f"lira_{a.dataset}_{a.arm}.csv"
    if res.exists():
        import csv as _csv
        rows = list(_csv.DictReader(open(res)))
        best = {}
        for row in rows:
            best.setdefault(row["attack"], []).append(float(row["attack_auc"]))
        print("\n" + "=" * 78)
        print(f"  NEW CONTROL ({a.arm}, full-length training)")
        print("=" * 78)
        for atk, vals in best.items():
            m = sum(vals) / len(vals)
            print(f"    {atk:<16} AUC {m:.4f}   (n={len(vals)})")
        # Compare against the SAME attack variant the paper reports. An
        # earlier version preferred lira_online_gv and differenced it against
        # the published lira_offline figure, reporting a 0.0233 "fall" that was
        # entirely the gap between two attacks rather than any change in the
        # model. Comparing whichever variant happens to exist is how a
        # measurement error gets published as a finding.
        lr = best.get(PUBLISHED_CONTROL_ATTACK)
        if lr:
            m = sum(lr) / len(lr)
            d = m - PUBLISHED_CONTROL_AUC
            print(f"\n    published control ({PUBLISHED_CONTROL_ATTACK}) was "
                  f"{PUBLISHED_CONTROL_AUC:.4f}; now {m:.4f} ({d:+.4f})")
            print("    Interpretation: the control exists to prove the attack "
                  "can detect leakage. It must stay clearly above the private "
                  "arms; whether it rises or falls with training length is a "
                  "property of the model, not a pass/fail criterion.")
        else:
            print(f"\n    [warn] {PUBLISHED_CONTROL_ATTACK} not in results; "
                  f"cannot compare against the published figure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
