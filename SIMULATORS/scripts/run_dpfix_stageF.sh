#!/usr/bin/env bash
#==============================================================================
# run_dpfix_stageF.sh — improved patient-level operating point (2026-10-23),
# then hands over to stages B-E.
#
# Stage A showed the patient-level cost is set by the smallest clients: one
# sigma calibrated on the worst client (eICU: a 15-patient hospital, q = 1)
# is applied to every client. Here each client uses its own sigma_k
# (parallel composition: a patient is on one client only), the PRV accountant
# (tight upper bound, same mechanism), and a 0.9 / 0.1 training / conformal
# split. O2b is measured on the proposed system itself, private vs --no_dp,
# 5 paired seeds, with the test accuracy also reported at a threshold chosen
# on the validation cohort.
#
#   bash SIMULATORS/scripts/run_dpfix_stageF.sh
#
# Per dataset (vitaldb, eicu):
#   1. 5 seeds x {dp, nodp} -> results/phase5/o2b_system/<ds>/<arm>_s<seed>/
#   2. collect + paired summary
#   3. seed-42 private run becomes the headline proposed_<ds>.* (the
#      worst-client headline is moved to results/phase5/worst_client/)
#   4. rescore objectives
# Then exec run_dpfix_stageBE.sh (unchanged, worst-client calibration).
# Waits for stage A. Resumable: finished runs (run_test.json) are skipped.
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
SEEDS=(42 43 44 45 46)
PPB=64
EPS_TRAIN=0.9; EPS_CONF=0.1
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "[$(stamp)] waiting for stage A ..."
while pgrep -f run_dpfix_stageA.sh >/dev/null; do sleep 120; done

for DS in vitaldb eicu; do
  MARK="$SIM/results/phase5/.dpfix/F_${DS}.done"
  [[ -f "$MARK" ]] && { echo "[$(stamp)] $DS stage F done, skipping"; continue; }
  echo; echo "=== $DS stage F ($(stamp)) ==="
  # The headline recipe minus the per-run fields this stage sets itself.
  RECIPE=$(python - "$DS" <<'EOF'
import glob, json, re, sys
ds = sys.argv[1]
best = None
for f in glob.glob("results/phase5/run_metadata_*.json"):
    d = json.load(open(f)); a = d.get("argv")
    a = a if isinstance(a, str) else " ".join(map(str, a or []))
    if re.search(rf"--output\s+\S*proposed_{ds}\.csv", a) and "--dp_unit" not in a \
            and (best is None or d["timestamp"] > best[0]):
        best = (d["timestamp"], a)
toks = best[1].split()[1:]
drop = {"--seed", "--output", "--save_checkpoint", "--epsilon", "--epsilon_conf"}
out, i = [], 0
while i < len(toks):
    if toks[i] in drop:
        i += 2
        continue
    out.append(toks[i]); i += 1
print(" ".join(out))
EOF
)
  [[ -z "$RECIPE" ]] && { echo "[FAIL] no recipe for $DS"; continue; }
  echo "[$(stamp)] recipe: $RECIPE"
  O="$SIM/results/phase5/o2b_system/$DS"
  for sd in "${SEEDS[@]}"; do
    for arm in dp nodp; do
      R="$O/${arm}_s$sd"; mkdir -p "$R"
      [[ -f "$R/run_test.json" ]] && continue
      EXTRA=(--dp_unit patient --patients_per_batch $PPB --sigma_mode per_client
             --accountant prv --epsilon $EPS_TRAIN --epsilon_conf $EPS_CONF)
      [[ $arm == nodp ]] && EXTRA+=(--no_dp)
      echo "[$(stamp)] $DS $arm seed $sd"
      # shellcheck disable=SC2086
      python -u model/training/hfl_trainer.py $RECIPE "${EXTRA[@]}" --seed $sd \
        --save_checkpoint "$R/ckpt.pt" --output "$R/run.csv" --no_monitor \
        > "$R/train.log" 2>&1 || echo "[FAIL] $DS $arm seed $sd (see $R/train.log)"
      grep -E "Final Test|TOTAL reportable|per-client calibration" "$R/train.log"
    done
  done
  python -u scripts/o2b_system_collect.py "$DS"
  python -u scripts/o2b_paired_summary.py "$DS" --root "$SIM/results/phase5/o2b_system"

  # Headline = seed-42 private run. Keep the worst-client headline.
  P=results/phase5; W=$P/worst_client
  if [[ -f "$O/dp_s42/run_test.json" ]]; then
    mkdir -p "$W" checkpoints/worst_client
    for f in proposed_${DS}.csv proposed_${DS}_final.json proposed_${DS}_test.json \
             privacy_total_${DS}.json; do
      [[ -e $P/$f && ! -e $W/$f ]] && mv "$P/$f" "$W/$f"
    done
    [[ -e checkpoints/best_${DS}.pt && ! -e checkpoints/worst_client/best_${DS}.pt ]] && \
      mv checkpoints/best_${DS}.pt checkpoints/worst_client/
    cp "$O/dp_s42/run.csv"        "$P/proposed_${DS}.csv"
    cp "$O/dp_s42/run_test.json"  "$P/proposed_${DS}_test.json"
    [[ -f "$O/dp_s42/run_final.json" ]] && cp "$O/dp_s42/run_final.json" "$P/proposed_${DS}_final.json"
    cp "$O/dp_s42/privacy_total_${DS}.json" "$P/privacy_total_${DS}.json"
    cp "$O/dp_s42/ckpt.pt"        "checkpoints/best_${DS}.pt"
  fi
  python -u scripts/check_objectives.py --dataset "$DS" --results_dir "$SIM/results/phase5" \
    --output "$SIM/results/phase5/objectives_${DS}.json" | grep -E "O[0-9]|PASS|FAIL|DEGEN"
  python -u scripts/dpfix_compare.py "$DS"
  mkdir -p "$(dirname "$MARK")"; touch "$MARK"
  echo "[$(stamp)] $DS stage F DONE"
done
echo "[$(stamp)] STAGE F DONE"
exec bash scripts/run_dpfix_stageBE.sh
