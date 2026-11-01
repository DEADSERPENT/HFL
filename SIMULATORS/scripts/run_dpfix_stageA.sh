#!/usr/bin/env bash
#==============================================================================
# run_dpfix_stageA.sh — Stage A of the 2026-10-22 privacy re-run: the proposed
# system at the PATIENT level, which is what the paper claims and what no
# pre-fix system run used (all were --dp_unit sample).
#
#   bash SIMULATORS/scripts/run_dpfix_stageA.sh [dataset ...]
#   default: vitaldb eicu   (vitaldb first: an hour, not a day)
#
# Per dataset:
#   1. archive the pre-fix artifacts under results/_archive_pre_dpfix_20261022/
#      (copied; the O2b directory is MOVED so --resume cannot reuse old rows)
#   2. proposed system: the archived run's own recipe + --dp_unit patient
#   3. O2b multi-seed sweep, eps=1 vs inf, private arm at the patient level
#   4. rescore objectives, paired O2b summary, before/after comparison
#
# WEAR is excluded by design: one participant per client, so the patient-level
# local mechanism degenerates (q = 1 on a single person). Its record-level
# results stand and are labelled as such in the paper.
# Resumable: a dataset whose stage-A marker exists is skipped.
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
DSETS=("$@"); [[ ${#DSETS[@]} -eq 0 ]] && DSETS=(vitaldb eicu)
ARCH="$SIM/results/_archive_pre_dpfix_20261022"
PPB=64     # patients per batch: the value every patient-level run has used
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

for DS in "${DSETS[@]}"; do
  MARK="$SIM/results/phase5/.dpfix_stageA_${DS}.done"
  [[ -f "$MARK" ]] && { echo "[$(stamp)] $DS stage A done, skipping"; continue; }
  echo; echo "=== $DS stage A ($(stamp)) ==="

  # 1. archive (idempotent: never overwrite an existing archive copy)
  mkdir -p "$ARCH/phase5/o2b_multiseed" "$ARCH/checkpoints"
  for f in proposed_${DS}.csv proposed_${DS}_final.json proposed_${DS}_test.json \
           objectives_${DS}.json privacy_total_${DS}.json; do
    [[ -e results/phase5/$f && ! -e $ARCH/phase5/$f ]] && cp -p results/phase5/$f $ARCH/phase5/$f
  done
  [[ -e checkpoints/best_${DS}.pt && ! -e $ARCH/checkpoints/best_${DS}.pt ]] && \
    cp -p checkpoints/best_${DS}.pt $ARCH/checkpoints/
  if [[ -d results/phase5/o2b_multiseed/$DS && ! -d $ARCH/phase5/o2b_multiseed/$DS ]]; then
    mv results/phase5/o2b_multiseed/$DS $ARCH/phase5/o2b_multiseed/$DS
  fi

  # 2. proposed system, patient level. Recipe = the archived run's argv.
  SYS_OK="$SIM/results/phase5/.dpfix_sys_${DS}.done"
  if [[ ! -f "$SYS_OK" ]]; then
    ARGV=$(python - "$DS" <<'EOF'
import glob, json, re, sys
ds = sys.argv[1]
best = None
for f in glob.glob("results/phase5/run_metadata_*.json"):
    d = json.load(open(f)); a = d.get("argv")
    a = a if isinstance(a, str) else " ".join(map(str, a or []))
    if re.search(rf"--output\s+\S*proposed_{ds}\.csv", a) and "--dp_unit" not in a \
            and (best is None or d["timestamp"] > best[0]):
        best = (d["timestamp"], a)
toks = best[1].split()
print(" ".join(toks[1:]))          # drop the script path
EOF
)
    [[ -z "$ARGV" ]] && { echo "[FAIL] no archived recipe for $DS"; continue; }
    echo "[$(stamp)] recipe: $ARGV --dp_unit patient --patients_per_batch $PPB"
    # shellcheck disable=SC2086
    python -u model/training/hfl_trainer.py $ARGV --dp_unit patient \
      --patients_per_batch $PPB --no_monitor \
      && touch "$SYS_OK" || { echo "[FAIL] $DS proposed system"; continue; }
  fi

  # 3. O2b multi-seed at the patient level
  DP_UNIT=patient bash scripts/run_o2b_multiseed.sh "$DS"
  python -u scripts/o2b_paired_summary.py "$DS"

  # 4. rescore + compare
  python -u scripts/check_objectives.py --dataset "$DS" \
    --results_dir "$SIM/results/phase5" \
    --output "$SIM/results/phase5/objectives_${DS}.json" | grep -E "O[0-9]|PASS|FAIL|DEGEN"
  python -u scripts/dpfix_compare.py "$DS"
  touch "$MARK"
  echo "[$(stamp)] $DS stage A DONE"
done
echo "[$(stamp)] STAGE A DONE"
