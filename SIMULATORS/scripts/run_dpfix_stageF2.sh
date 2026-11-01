#!/usr/bin/env bash
#==============================================================================
# run_dpfix_stageF2.sh — stage F on VitalDB with the DISJOINT encoders.
#
# Theorem 1 needs encoders pretrained on a population disjoint from every
# client (assumption A2). The VitalDB headline uses the oracle encoders
# (pretrained on pooled client data), so its budget does not describe the
# system end to end. eICU already uses disjoint encoders. This repeats the
# stage-F O2b on VitalDB with pretrained_encoders_vitaldb_public.pt so the
# paper has a headline the theorem covers. Same mechanism and seeds as F.
#
#   bash SIMULATORS/scripts/run_dpfix_stageF2.sh
# Waits for stages B-E. Resumable (finished runs are skipped).
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
DS=vitaldb; TAG=_disjoint
ENC="$SIM/checkpoints/pretrained_encoders_${DS}_public.pt"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }
[[ -f "$ENC" ]] || { echo "[FAIL] missing $ENC"; exit 1; }

echo "[$(stamp)] waiting for stages B-E ..."
while pgrep -f "run_dpfix_stage(A|F|BE)\.sh" >/dev/null; do sleep 300; done

MARK="$SIM/results/phase5/.dpfix/F2_${DS}.done"
[[ -f "$MARK" ]] && { echo "[$(stamp)] F2 done"; exit 0; }
O="$SIM/results/phase5/o2b_system/${DS}${TAG}"
for sd in 42 43 44 45 46; do
  for arm in dp nodp; do
    R="$O/${arm}_s$sd"; mkdir -p "$R"
    [[ -f "$R/run_test.json" ]] && continue
    EXTRA=(--dp_unit patient --patients_per_batch 64 --sigma_mode per_client
           --accountant prv --epsilon 0.9 --epsilon_conf 0.1)
    [[ $arm == nodp ]] && EXTRA+=(--no_dp)
    echo "[$(stamp)] $DS$TAG $arm seed $sd"
    python -u model/training/hfl_trainer.py --dataset $DS --rounds 10 --tau_e 5 \
      --batch_size 64 --freeze_encoders --pretrained_encoders "$ENC" "${EXTRA[@]}" \
      --seed $sd --save_checkpoint "$R/ckpt.pt" --output "$R/run.csv" --no_monitor \
      > "$R/train.log" 2>&1 || echo "[FAIL] $DS$TAG $arm seed $sd (see $R/train.log)"
    grep -E "Final Test|TOTAL reportable" "$R/train.log"
  done
done
python -u scripts/o2b_system_collect.py "$DS" --tag "$TAG"
python -u scripts/o2b_paired_summary.py "${DS}${TAG}" --root "$SIM/results/phase5/o2b_system"
touch "$MARK"
echo "[$(stamp)] STAGE F2 DONE"
