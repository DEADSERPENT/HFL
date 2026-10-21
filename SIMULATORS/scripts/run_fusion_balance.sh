#!/usr/bin/env bash
# Two-stage titrated balance test (PREREGISTRATION_FUSION_BALANCE.md §7,
# as amended by F-A1 2026-10-19).
#
# LEVER CHANGE — F-A1. The registered lever was --feat_b_scale. It is
# INFORMATION-PRESERVING: modality B is z-scored and its encoder is linear in
# the first layer, so multiplying one feature by alpha is undone by a 1/alpha
# weight. Measured on the one calibration point that completed before the
# 2026-09-21 crash: alpha=0.15 left arm b at 0.8214 against 0.8221 intact — the
# lever moved B by 0.0007 when it was asked to move it by ~0.115. Titration is
# therefore done with --feat_b_noise, which mixes the feature with fixed-seed
# Gaussian noise (x -> a*x + sqrt(1-a^2)*eps) and so destroys information
# rather than rescaling it. a=1 is intact, a=0 is pure noise.
#
# Stage 2a calibrates modality B's strength; stage 2b is the registered test.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source /home/mit/DEADSERPENT/HFL/hfl_env/bin/activate
COMMON="--dataset eicu --eval_every 250 --val_cap 40000 --max_steps 8000"
OUT=results/phase5
IDX=4                      # APACHE — modality B's dominant channel

echo "===== STAGE 2a — calibration: arm b only, 2 seeds, noise lever ====="
for A in 0.20 0.40 0.60 0.80; do
  python -u scripts/modality_ablation.py $COMMON --seeds 42 43 \
    --arms b --feat_b_noise "$IDX:$A" --out "$OUT/fusbal_calib_n$A.json"
done

echo "===== picking ALPHA* nearest the A arm ====="
python - <<'PY'
import json, glob, re
import numpy as np
# Target: arm A's AUROC on the current partitions, read from the matched
# control artefact — never hardcoded.
target = json.load(open("results/phase5/ablation_eicu_matched.json"))
a = float(np.mean([r["auroc"] for r in target["runs"]["a"]]))
best, ba = None, None
for f in sorted(glob.glob("results/phase5/fusbal_calib_n*.json")):
    al = float(re.search(r"_n([0-9.]+)\.json", f).group(1))
    d = json.load(open(f))
    b = float(np.mean([r["auroc"] for r in d["runs"]["b"]]))
    print(f"  alpha={al}  B={b:.4f}  |B-A|={abs(b - a):.4f}", flush=True)
    if best is None or abs(b - a) < best:
        best, ba = abs(b - a), al
print(f"  A arm = {a:.4f} -> ALPHA* = {ba}  (|B-A| = {best:.4f})", flush=True)
if best > 0.04:
    print("  [warn] ALPHA* does not bring B within 0.04 of A. The grid does "
          "not bracket the target; widen it before reading stage 2b as a "
          "balanced comparison.", flush=True)
open("results/phase5/fusbal_alpha.txt", "w").write(str(ba))
PY

ALPHA=$(cat results/phase5/fusbal_alpha.txt)
echo "===== STAGE 2b — registered test at ALPHA*=$ALPHA, 5 seeds, all arms ====="
python -u scripts/modality_ablation.py $COMMON --seeds 42 43 44 45 46 \
  --feat_b_noise "$IDX:$ALPHA" --out "$OUT/fusbal_test_n$ALPHA.json"
echo "===== done ====="
