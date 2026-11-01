#!/usr/bin/env bash
#==============================================================================
# run_lit_baselines.sh — HED-FL and FL2DP against the proposed system.
#
# Each baseline is trained with the stage-F recipe of its corpus (same data,
# partition, frozen encoders, rounds, batch, learning rate and seeds), with the
# patient-level DP flags removed and --baseline added, so only the mechanism
# differs (model/training/lit_baselines.py). Then:
#   1  utility and uplink, paired by seed with stage F (lit_baselines_summary.py)
#   2  VitalDB only: patient-level LiRA on both baselines, 16 shadows each,
#      same shadow memberships and evaluated patients as the E2 audit
# Order: VitalDB, its audit, then eICU (the longest). Resumable throughout.
#
#   bash SIMULATORS/scripts/run_lit_baselines.sh
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
ARMS=(hedfl fl2dp)
# FL2DP draws an exponential-mechanism sample for every coordinate of every
# example's gradient; on eICU (2.1 M training windows, ~33 k batches per edge
# round) one seed would take about two GPU days, so it runs on VitalDB only and
# its per-round time there is reported as the overhead.
declare -A DS_ARMS=([vitaldb]="hedfl fl2dp" [eicu]="hedfl")
MARKS="$SIM/results/phase5/.lit"; mkdir -p "$MARKS"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "[$(stamp)] waiting for any other training job ..."
while pgrep -f "run_dpfix_|lira_attack\.py|hfl_trainer\.py" >/dev/null; do sleep 300; done

# Stage-F recipe of a corpus, from the run metadata of its non-private arm,
# minus the run-specific and patient-DP flags.
recipe() {
python - "$1" <<'EOF'
import glob, json, sys
ds = sys.argv[1]
f = sorted(glob.glob(f"results/phase5/o2b_system/{ds}/nodp_s*/run_metadata_*.json"))[0]
a = json.load(open(f))["argv"]
toks = (a if isinstance(a, list) else a.split())[1:]
drop2 = {"--seed", "--output", "--save_checkpoint", "--dp_unit", "--patients_per_batch",
         "--sigma_mode", "--accountant", "--epsilon_conf"}
drop1 = {"--no_dp", "--no_monitor"}
out, i = [], 0
while i < len(toks):
    if toks[i] in drop2: i += 2; continue
    if toks[i] in drop1: i += 1; continue
    out.append(toks[i]); i += 1
print(" ".join(out))
EOF
}
seeds() { ls -d results/phase5/o2b_system/$1/nodp_s* | sed 's/.*_s//' | sort -n | tr '\n' ' '; }

train() {   # dataset
  local DS=$1 R; R=$(recipe "$DS")
  [[ -z "$R" ]] && { echo "[FAIL] no stage-F recipe for $DS"; return 1; }
  local O="$SIM/results/phase5/baselines_lit/$DS"; mkdir -p "$O"
  echo "[$(stamp)] $DS recipe: $R"
  for sd in $(seeds "$DS"); do
    for arm in ${DS_ARMS[$DS]}; do
      [[ -f "$O/${arm}_s${sd}_test.json" ]] && continue
      echo "[$(stamp)] $DS $arm seed $sd"
      # shellcheck disable=SC2086
      python -u model/training/hfl_trainer.py $R --baseline "$arm" --seed "$sd" \
        --save_checkpoint "$O/ckpt_${arm}_${sd}.pt" --output "$O/${arm}_s${sd}.csv" \
        --no_monitor > "$O/${arm}_s${sd}.log" 2>&1 \
        || { echo "[FAIL] $DS $arm seed $sd (see $O/${arm}_s${sd}.log)"; return 1; }
      grep -E "Final Test" "$O/${arm}_s${sd}.log"
    done
  done
  python -u scripts/lit_baselines_summary.py "$DS"
}

if [[ ! -f "$MARKS/vitaldb.done" ]]; then
  train vitaldb && touch "$MARKS/vitaldb.done" || exit 1
fi

if [[ ! -f "$MARKS/lira_vitaldb.done" ]]; then
  echo "[$(stamp)] LiRA on the baselines (VitalDB)"
  python -u scripts/lira_attack.py --dataset vitaldb \
    --target_dir results/phase5/baselines_lit/vitaldb --arms "${ARMS[@]}" \
    --phase splits,train,score,attack \
    && touch "$MARKS/lira_vitaldb.done" || { echo "[FAIL] LiRA"; exit 1; }
fi

if [[ ! -f "$MARKS/eicu.done" ]]; then
  train eicu && touch "$MARKS/eicu.done" || exit 1
fi
echo "[$(stamp)] LITERATURE BASELINES DONE"
