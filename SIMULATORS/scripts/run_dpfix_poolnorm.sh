#!/usr/bin/env bash
#==============================================================================
# run_dpfix_poolnorm.sh — eICU stage F with PUBLIC standardization constants.
#
# Theorem 1 holds with the standardization constants fixed. The preprocessor
# fits them on the training individuals, so they are an unprotected release
# about the protected cohort. This stage re-standardizes eICU with constants
# fitted on the disjoint public pool (make_poolnorm_data.py), re-pretrains the
# encoders on that pool in the new units, and repeats stage F (same recipe,
# mechanism and seeds). Everything the private head sees is then either
# public or covered by the guarantee.
#
#   bash SIMULATORS/scripts/run_dpfix_poolnorm.sh [dataset]   (default eicu)
# Waits for every other dpfix stage. Resumable (finished runs are skipped).
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
DS=${1:-eicu}; TAG=_poolnorm
SEEDS=(42 43 44 45 46)
PPB=64; EPS_TRAIN=0.9; EPS_CONF=0.1
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

read -r DATA PDIR < <(python - "$DS" <<'EOF'
import sys; sys.path.insert(0, "data/loaders")
from datasets import get_spec
s = get_spec(sys.argv[1]); print(s.data_dir + "_poolnorm", s.partition_dir)
EOF
)
PUB="$PDIR/public_indices.npy"
ENC="$SIM/checkpoints/pretrained_encoders_${DS}${TAG}.pt"
MARK="$SIM/results/phase5/.dpfix/G_${DS}${TAG}.done"
[[ -f "$MARK" ]] && { echo "[$(stamp)] $DS$TAG done"; exit 0; }
[[ -f "$PUB" ]] || { echo "[FAIL] missing $PUB"; exit 1; }

echo "[$(stamp)] waiting for the other dpfix stages ..."
while pgrep -f "run_dpfix_(stage[A-Z0-9]*|lira)\.sh" >/dev/null; do sleep 300; done

# 1 ── public-constant data (CPU; aborts if the remap would not be exact)
if [[ ! -f "$DATA/meta/norm_stats_pool.json" ]]; then
  python -u scripts/make_poolnorm_data.py "$DS" || { echo "[FAIL] make_poolnorm_data"; exit 1; }
fi

# 2 ── encoders on the public pool, in the new units (same settings as before)
if [[ ! -f "$ENC" ]]; then
  echo "[$(stamp)] pretraining encoders on the public pool"
  python -u model/training/pretrain_encoders.py --dataset "$DS" --data_dir "$DATA" \
    --public_data "$PUB" --epochs 30 --batch_size 64 --eval_every 250 \
    --output "$ENC" || { echo "[FAIL] pretrain_encoders"; exit 1; }
fi

# 3 ── stage F: the headline recipe with the new data and encoders
RECIPE=$(python - "$DS" "$ENC" <<'EOF'
import glob, json, re, sys
ds, enc = sys.argv[1], sys.argv[2]
best = None
for f in glob.glob("results/phase5/run_metadata_*.json"):
    d = json.load(open(f)); a = d.get("argv")
    a = a if isinstance(a, str) else " ".join(map(str, a or []))
    if re.search(rf"--output\s+\S*proposed_{ds}\.csv", a) and "--dp_unit" not in a \
            and (best is None or d["timestamp"] > best[0]):
        best = (d["timestamp"], a)
toks = best[1].split()[1:]
drop = {"--seed", "--output", "--save_checkpoint", "--epsilon", "--epsilon_conf",
        "--pretrained_encoders", "--data_dir"}
out, i = [], 0
while i < len(toks):
    if toks[i] in drop:
        i += 2
        continue
    out.append(toks[i]); i += 1
print(" ".join(out + ["--pretrained_encoders", enc]))
EOF
)
[[ -z "$RECIPE" ]] && { echo "[FAIL] no recipe for $DS"; exit 1; }
echo "[$(stamp)] recipe: $RECIPE --data_dir $DATA"
O="$SIM/results/phase5/o2b_system/${DS}${TAG}"
for sd in "${SEEDS[@]}"; do
  for arm in dp nodp; do
    R="$O/${arm}_s$sd"; mkdir -p "$R"
    [[ -f "$R/run_test.json" ]] && continue
    EXTRA=(--dp_unit patient --patients_per_batch $PPB --sigma_mode per_client
           --accountant prv --epsilon $EPS_TRAIN --epsilon_conf $EPS_CONF)
    [[ $arm == nodp ]] && EXTRA+=(--no_dp)
    echo "[$(stamp)] $DS$TAG $arm seed $sd"
    # shellcheck disable=SC2086
    python -u model/training/hfl_trainer.py $RECIPE --data_dir "$DATA" "${EXTRA[@]}" \
      --seed $sd --save_checkpoint "$R/ckpt.pt" --output "$R/run.csv" --no_monitor \
      > "$R/train.log" 2>&1 || echo "[FAIL] $DS$TAG $arm seed $sd (see $R/train.log)"
    grep -E "Final Test|TOTAL reportable" "$R/train.log"
  done
done
python -u scripts/o2b_system_collect.py "$DS" --tag "$TAG"
python -u scripts/o2b_paired_summary.py "${DS}${TAG}" --root "$SIM/results/phase5/o2b_system"
mkdir -p "$(dirname "$MARK")"; touch "$MARK"
echo "[$(stamp)] STAGE G ($DS$TAG) DONE"
