#!/usr/bin/env bash
#==============================================================================
# run_o2b_multiseed.sh — Objective O2b at the protocol vitaldb and wear used:
# head recipe, eps=1 vs eps=inf, 30 rounds, paired by seed, written to
# results/phase5/o2b_multiseed/<ds>/ (the path check_objectives.py prefers).
#
#   bash SIMULATORS/scripts/run_o2b_multiseed.sh [dataset] [seed ...]
#        default: eicu 42 43 44 45 46
#
#   DP_UNIT=patient bash ...   private arm at the PATIENT level (patient_dp);
#   default sample (Opacus, record level), the unit of every pre-2026-10-22 run.
#
# Waits for any running trainer / pipeline (never two GPU jobs), is resumable
# (--resume skips finished (eps, recipe, seed) rows), and rescores the
# objectives after every seed so partial evidence is always on disk.
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
DS="${1:-eicu}"; shift || true
SEEDS=("$@"); [ ${#SEEDS[@]} -gt 0 ] || SEEDS=(42 43 44 45 46)
OUT="$SIM/results/phase5/o2b_multiseed/$DS"; mkdir -p "$OUT"
ENC="$SIM/checkpoints/pretrained_encoders_${DS}.pt"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

gpu_busy() { pgrep -f "hfl_trainer\.py|epsilon_sweep\.py|run_pipeline\.py|lira_attack\.py" >/dev/null 2>&1; }
echo "[$(stamp)] waiting for the GPU to be free ..."
while gpu_busy; do sleep 60; done

# Registry data_dir / partition_dir are relative to SIMULATORS/.
cd "$SIM"
for sd in "${SEEDS[@]}"; do
  echo; echo "=== $DS seed $sd  ($(stamp)) ==="
  python -u "$SIM/model/training/epsilon_sweep.py" --dataset "$DS" \
    --epsilons 1.0 inf --recipes head --seeds "$sd" --rounds 30 \
    --local_epochs 1 --batch_size 64 --max_physical_batch_size 0 \
    --pretrained_encoders "$ENC" --output_dir "$OUT" --resume \
    --dp_unit "${DP_UNIT:-sample}" \
    || echo "[FAIL] seed $sd"
  python -u "$SIM/scripts/check_objectives.py" --dataset "$DS" \
    --results_dir "$SIM/results/phase5" \
    --output "$SIM/results/phase5/objectives_${DS}.json" | grep -E "O2b|PASS|FAIL"
done
echo "[$(stamp)] DONE"
