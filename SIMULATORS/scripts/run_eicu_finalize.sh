#!/usr/bin/env bash
#==============================================================================
# run_eicu_finalize.sh — once both eICU evidence drivers have finished:
#   o2b_paired_summary.py -> results/phase5/o2b_multiseed/<ds>/o2b_paired.json
#   check_objectives.py   -> results/phase5/objectives_<ds>.json (O2b now 5-seed)
#   fig09_system_cost.py  -> paper/figures/fig09_system_cost.{pdf,png}
#   build_paper.sh        -> rebuild with the new figure
#
#   bash SIMULATORS/scripts/run_eicu_finalize.sh [dataset]   (default eicu)
#
# Completion is read from the drivers' own "] DONE" line, not from process
# names, so a crashed driver does not trigger a finalize on partial results.
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
DS="${1:-eicu}"
LOGS="$SIM/results/pipeline/_detached"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

for L in "$LOGS/${DS}_network_evidence.log" "$LOGS/o2b_multiseed_${DS}.log"; do
  echo "[$(stamp)] waiting for DONE in $(basename "$L") ..."
  until grep -q "\] DONE" "$L" 2>/dev/null; do sleep 120; done
done
echo "[$(stamp)] both drivers done — finalizing ($DS)"

echo; echo "=== o2b_paired_summary ($(stamp)) ==="
python -u "$SIM/scripts/o2b_paired_summary.py" "$DS" || echo "[FAIL] o2b_paired_summary"

echo; echo "=== objectives ($(stamp)) ==="
python -u "$SIM/scripts/check_objectives.py" --dataset "$DS" \
  --results_dir "$SIM/results/phase5" \
  --output "$SIM/results/phase5/objectives_${DS}.json" || echo "[FAIL] objectives"

echo; echo "=== fig09 ($(stamp)) ==="
(cd "$ROOT/paper/figures" && python -u fig09_system_cost.py) || echo "[FAIL] fig09"

echo; echo "=== paper build ($(stamp)) ==="
bash "$ROOT/paper/build_paper.sh" 2>&1 | grep -E "PDF:|errors|undefined|overfull|float warnings" \
  || echo "[FAIL] build"
echo "[$(stamp)] DONE"
