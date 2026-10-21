#!/usr/bin/env python3
"""
Multi-seed B4 / B7 / B6 — intervals on the paper's headline privacy result.

The epsilon sweep behind the "pretrained initialisation, not head-only DP"
finding is single-seed at every point, which the manuscript's Limitations
already concedes: the claim it supports is "the monotonicity of the trend
rather than any individual value". This adds seeds so each point carries an
interval.

This is NOT the move refused for objective O2b. There, a pass/fail threshold
sat inside the confidence interval and extending seeds would have been a search
for the favourable side of it. Here no threshold is involved: the effect is
already reported as monotone, and more seeds upgrade "trend only" to "resolved",
which is exactly the stated limitation.

    B4 = recipe 'full'      full-model DP, RANDOM init      (prior art)
    B7 = recipe 'full_pre'  full-model DP, PRETRAINED init  (isolates init)
    B6 = recipe 'head'      head-only DP,  PRETRAINED init  (proposed)

--resume keys on (epsilon, recipe, seed), so the existing seed-42 rows are
reused and only the new seeds are trained.
"""
import argparse, json, subprocess, sys
from pathlib import Path

_SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import get_spec, REGISTRY          # noqa: E402

# wear's full-model DP OOMs at batch 64 without this; resolved per dataset
# rather than hardcoded at the call site.
PHYS_BATCH = {"wear": 16}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["vitaldb", "wear"],
                    choices=sorted(REGISTRY))
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--epsilons", nargs="+",
                    default=["0.5", "1.0", "2.0", "4.0", "8.0", "inf"])
    ap.add_argument("--recipes", nargs="+", default=["full", "full_pre", "head"])
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--batch_size", type=int, default=64)
    a = ap.parse_args()

    for ds in a.datasets:
        spec = get_spec(ds)
        enc = _SIM / "checkpoints" / f"pretrained_encoders_{ds}.pt"
        if not enc.exists():
            print(f"[skip] {ds}: no {enc.name}", flush=True)
            continue
        # select_on matches the published sweep for this corpus.
        sel = "auprc" if ds == "vitaldb" else "auc"
        cmd = [sys.executable, "-u",
               str(_SIM / "model" / "training" / "epsilon_sweep.py"),
               "--dataset", ds,
               "--epsilons", *a.epsilons,
               "--recipes", *a.recipes,
               "--seeds", *[str(s) for s in a.seeds],
               "--rounds", str(a.rounds),
               "--batch_size", str(a.batch_size),
               "--select_on", sel,
               "--pretrained_encoders", str(enc),
               "--resume"]
        if ds in PHYS_BATCH:
            cmd += ["--max_physical_batch_size", str(PHYS_BATCH[ds])]
        print("\n" + "=" * 74)
        print(f"  B4/B7/B6 multi-seed — {ds}   seeds={a.seeds}")
        print("=" * 74)
        print("  $ " + " ".join(cmd[2:]), flush=True)
        r = subprocess.run(cmd, cwd=_SIM)
        if r.returncode != 0:
            print(f"[FAILED] {ds} exit {r.returncode}", flush=True)

    print("\n[done] re-run scripts/collect_phase5_results.py to refresh "
          "downstream tables.", flush=True)


if __name__ == "__main__":
    main()
