#!/usr/bin/env bash
#==============================================================================
# run_dpfix_lira.sh — LiRA patient arm on the post-fix mechanism (stage E part 2).
#
# Stage E's archive step moved shadows/patient wholesale, partitions included,
# so `lira_attack.py --phase train` aborted on missing partition files. The
# partitions are seeded (split_seed 7) and were restored from the archive
# (membership identical to the sample arm, so the comparison stays paired);
# only the shadow checkpoints are retrained here.
#
#   bash SIMULATORS/scripts/run_dpfix_lira.sh
# Waits for every other dpfix stage (one GPU job at a time). Resumable:
# completed shadows are skipped by lira_attack.py.
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
DS=vitaldb
MARK="$SIM/results/phase5/.dpfix/E2_lira_${DS}.done"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "[$(stamp)] waiting for the other dpfix stages ..."
while pgrep -f "run_dpfix_stage[A-Z0-9]*\.sh" >/dev/null; do sleep 300; done
[[ -f "$MARK" ]] && { echo "[$(stamp)] LiRA done"; exit 0; }

S=results/phase5/lira/$DS/shadows/patient
n_part=$(ls -d $S/shadow_*/partition_meta.json 2>/dev/null | wc -l)
[[ -f $S/membership.npz && $n_part -gt 0 ]] || { echo "[FAIL] LiRA partitions missing in $S"; exit 1; }

python -u scripts/lira_attack.py --dataset $DS --arms patient --phase train \
  && python -u scripts/lira_attack.py --dataset $DS --arms sample patient --phase score,attack \
  && { touch "$MARK"; echo "[$(stamp)] STAGE E2 LiRA DONE"; } \
  || echo "[FAIL] LiRA"
