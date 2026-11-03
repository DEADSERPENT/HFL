#!/usr/bin/env bash
#==============================================================================
# run_a1_eicu.sh — eICU rerun on the (A1) partition (every individual on one
# client), so that the patient-level training budget eps <= 0.9 holds for every
# eICU individual (FINAL_AUDIT_2026-11-02.md, B5).
#
# Matrix: {headline, pool-fitted} x {dp, nodp} x seeds 42-46 = 20 runs.
# Each run REUSES the exact recorded argv of its counterpart in
#   results/phase5/o2b_system/{eicu,eicu_poolnorm}/<arm>_s<seed>/
# and changes only --partition_dir (-> <registry partition>_a1), --output and
# --save_checkpoint. Outputs: results/phase5/o2b_system/eicu_a1{,_poolnorm}/.
# Existing results are never touched.
#
#   bash SIMULATORS/scripts/run_a1_eicu.sh [dataset]     (default eicu)
# Serial, resumable (a run with run_test.json is skipped), waits for any other
# training job. Ledger: <out>/runs.tsv (start, end, exit, partition md5).
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
DS=${1:-eicu}
SEEDS=(42 43 44 45 46)
stamp() { date '+%Y-%m-%d %H:%M:%S'; }
PDIR=$(python - "$DS" <<'EOF'
import sys; sys.path.insert(0, "data/loaders")
from datasets import get_spec
print(get_spec(sys.argv[1]).partition_dir + "_a1")
EOF
)
[[ -f "$PDIR/partition_meta.json" ]] || { echo "[FAIL] $PDIR missing; run scripts/make_a1_partition_eicu.py"; exit 1; }
PMD5=$(md5sum "$PDIR/partition_meta.json" | cut -d' ' -f1)

while ps -eo args | grep -E "[h]fl_trainer\.py|[k]_scaling\.py|[l]ira_attack\.py" >/dev/null; do
  echo "[$(stamp)] another training job is running; waiting"; sleep 300
done

recipe() {   # recipe <source run dir> <new out dir>: recorded argv, partition/outputs swapped
  python - "$1" "$2" "$PDIR" <<'EOF'
import glob, json, sys
src, dst, pdir = sys.argv[1:4]
m = sorted(glob.glob(f"{src}/run_metadata_*.json"))
if not m:
    sys.exit(f"[FAIL] no run metadata in {src}")
toks = json.load(open(m[-1]))["argv"]
toks = toks if isinstance(toks, list) else toks.split()
drop = {"--output", "--save_checkpoint", "--partition_dir"}
out, i = [], 1                                   # argv[0] is the script
while i < len(toks):
    if toks[i] in drop:
        i += 2; continue
    out.append(toks[i]); i += 1
out += ["--partition_dir", pdir, "--save_checkpoint", f"{dst}/ckpt.pt", "--output", f"{dst}/run.csv"]
print(" ".join(out))
EOF
}

for TAG in "" "_poolnorm"; do
  SRC="$SIM/results/phase5/o2b_system/${DS}${TAG}"
  O="$SIM/results/phase5/o2b_system/${DS}_a1${TAG}"
  mkdir -p "$O"
  [[ -f "$O/runs.tsv" ]] || printf "run\tstart\tend\texit\tpartition_meta_md5\n" > "$O/runs.tsv"
  for sd in "${SEEDS[@]}"; do
    for arm in dp nodp; do
      R="$O/${arm}_s$sd"; mkdir -p "$R"
      [[ -f "$R/run_test.json" ]] && continue
      ARGS=$(recipe "$SRC/${arm}_s$sd" "$R") || { echo "$ARGS"; exit 1; }
      t0=$(stamp); echo "[$t0] ${DS}_a1${TAG} $arm seed $sd"
      # shellcheck disable=SC2086
      python -u model/training/hfl_trainer.py $ARGS > "$R/train.log" 2>&1
      rc=$?
      printf "%s\t%s\t%s\t%s\t%s\n" "${arm}_s$sd" "$t0" "$(stamp)" "$rc" "$PMD5" >> "$O/runs.tsv"
      if [[ $rc -ne 0 || ! -f "$R/run_test.json" ]]; then
        echo "[FAIL] ${DS}_a1${TAG} $arm seed $sd exit $rc (see $R/train.log)"; exit 1
      fi
      grep -E "Final Test|TOTAL reportable" "$R/train.log"
    done
  done
  python -u scripts/o2b_system_collect.py "$DS" --tag "_a1${TAG}" \
    && python -u scripts/o2b_paired_summary.py "${DS}_a1${TAG}" --root "$SIM/results/phase5/o2b_system" \
    || { echo "[FAIL] summary ${DS}_a1${TAG}"; exit 1; }
done
echo "[$(stamp)] A1 RERUN DONE"
