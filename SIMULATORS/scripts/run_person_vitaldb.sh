#!/usr/bin/env bash
#==============================================================================
# run_person_vitaldb.sh — VitalDB experiments on the PERSON-level partitions.
#
# The case partitions let 55 test persons also appear in training and 68
# training persons sit on two clients, so the VitalDB patient-level results
# were case-level. make_person_partitions_vitaldb.py derives person-level
# partitions (registry entry vitaldb_person); this driver reruns, on them and
# with the exact argv of the original runs (only --dataset changes):
#
#   P1  stage F: private vs non-private, oracle encoders, five seeds
#   P2  cost of the unit: record- vs patient-level at matched eps = 1
#   P3  HED-FL and FL2DP baselines
#   P4  LiRA: control (no DP), record, patient, HED-FL, FL2DP
#
# Everything else on VitalDB stays case-level and is labelled so in the paper.
#   bash SIMULATORS/scripts/run_person_vitaldb.sh      (resumable)
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
DS=vitaldb_person; SRC=vitaldb
SEEDS=(42 43 44 45 46)
P=results/phase5; MARKS="$SIM/$P/.person"; mkdir -p "$MARKS"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }
done_mark() { touch "$MARKS/$1.done"; echo "[$(stamp)] $1 DONE"; }
stage() { [[ ! -f "$MARKS/$1.done" ]]; }

echo "[$(stamp)] waiting for any other training job ..."
while pgrep -f "run_dpfix_|run_lit_baselines|lira_attack\.py|hfl_trainer\.py" >/dev/null; do
  sleep 300; done

[[ -f "$SIM/data/processed/partitions/$DS/partition_meta.json" ]] \
  || python -u scripts/make_person_partitions_vitaldb.py || exit 1

# argv of an original run, minus per-run fields, with --dataset swapped
recipe() {   # metadata glob, extra options to drop, extra flags to drop
python - "$1" "${2:-}" "${3:-}" "$SRC" "$DS" <<'EOF'
import glob, json, sys
pat, extra, flags, src, dst = (sys.argv[1], sys.argv[2].split(), sys.argv[3].split(),
                               sys.argv[4], sys.argv[5])
f = sorted(glob.glob(pat))[-1]
a = json.load(open(f))["argv"]
toks = (a if isinstance(a, list) else a.split())[1:]
drop2 = {"--seed", "--output", "--save_checkpoint", "--partition_dir"} | set(extra)
out, i = [], 0
while i < len(toks):
    if toks[i] in drop2: i += 2; continue
    if toks[i] in {"--no_monitor", *flags}: i += 1; continue
    out.append(dst if (i and toks[i - 1] == "--dataset" and toks[i] == src) else toks[i])
    i += 1
assert "--dataset" in out and dst in out, out
print(" ".join(out))
EOF
}
# ── P1: stage F ─────────────────────────────────────────────────────────────
if stage P1_stageF; then
  O="$SIM/$P/o2b_system/$DS"
  for sd in "${SEEDS[@]}"; do
    for arm in dp nodp; do
      R="$O/${arm}_s$sd"; mkdir -p "$R"
      [[ -f "$R/run_test.json" ]] && continue
      read -r -a RC <<< "$(recipe "$P/o2b_system/$SRC/${arm}_s$sd/run_metadata_*.json")"
      echo "[$(stamp)] P1 $arm seed $sd"
      python -u model/training/hfl_trainer.py "${RC[@]}" --seed $sd \
        --save_checkpoint "$R/ckpt.pt" --output "$R/run.csv" --no_monitor \
        > "$R/train.log" 2>&1 || { echo "[FAIL] P1 $arm $sd (see $R/train.log)"; exit 1; }
      grep -E "Final Test|TOTAL reportable" "$R/train.log"
    done
  done
  python -u scripts/o2b_system_collect.py "$DS"
  python -u scripts/o2b_paired_summary.py "$DS" --root "$SIM/$P/o2b_system"
  done_mark P1_stageF
fi

# ── P2: cost of the unit (record vs patient, eps = 1) ──────────────────────
if stage P2_unit; then
  T="$P/patient_dp/$DS"; mkdir -p "$T"
  for sd in "${SEEDS[@]}"; do
    for arm in sample patient; do
      [[ -f "$T/ckpt_${arm}_$sd.pt" && -f "$T/${arm}_seed${sd}_test.json" ]] && continue
      SRCMETA=$(grep -l "ckpt_${arm}_$sd.pt" $P/patient_dp/$SRC/run_metadata_*.json | tail -1)
      read -r -a RC <<< "$(recipe "$SRCMETA")"
      echo "[$(stamp)] P2 $arm seed $sd"
      python -u model/training/hfl_trainer.py "${RC[@]}" --seed $sd \
        --save_checkpoint "$T/ckpt_${arm}_$sd.pt" --output "$T/${arm}_seed$sd.csv" \
        --no_monitor > "$T/${arm}_seed$sd.log" 2>&1 \
        || { echo "[FAIL] P2 $arm $sd"; exit 1; }
      grep -E "Final Test" "$T/${arm}_seed$sd.log"
    done
  done
  python -u scripts/person_unit_summary.py "$DS"
  done_mark P2_unit
fi

# ── P3: HED-FL and FL2DP ────────────────────────────────────────────────────
if stage P3_baselines; then
  O="$P/baselines_lit/$DS"; mkdir -p "$O"
  read -r -a RC <<< "$(recipe "$P/o2b_system/$DS/nodp_s42/run_metadata_*.json" \
    "--dp_unit --patients_per_batch --sigma_mode --accountant --epsilon_conf" "--no_dp")"
  for sd in "${SEEDS[@]}"; do
    for arm in hedfl fl2dp; do
      [[ -f "$O/${arm}_s${sd}_test.json" ]] && continue
      echo "[$(stamp)] P3 $arm seed $sd"
      python -u model/training/hfl_trainer.py "${RC[@]}" --baseline "$arm" --seed $sd \
        --save_checkpoint "$O/ckpt_${arm}_${sd}.pt" --output "$O/${arm}_s${sd}.csv" \
        --no_monitor > "$O/${arm}_s${sd}.log" 2>&1 \
        || { echo "[FAIL] P3 $arm $sd"; exit 1; }
      grep -E "Final Test" "$O/${arm}_s${sd}.log"
    done
  done
  python -u scripts/lit_baselines_summary.py "$DS"
  done_mark P3_baselines
fi

# ── P4: LiRA on every configuration ────────────────────────────────────────
if stage P4a_control_targets; then
  T="$P/mia_factorial/$DS"; mkdir -p "$T"
  for sd in 42 43 44; do
    [[ -f "$T/ckpt_head_nodp_seed$sd.pt" ]] && continue
    SRCMETA=$(grep -l "ckpt_head_nodp_seed$sd.pt" $P/mia_factorial/$SRC/run_metadata_*.json | tail -1)
    read -r -a RC <<< "$(recipe "$SRCMETA")"
    python -u model/training/hfl_trainer.py "${RC[@]}" --seed $sd \
      --save_checkpoint "$T/ckpt_head_nodp_seed$sd.pt" --output "$T/head_nodp_seed$sd.csv" \
      --no_monitor > "$T/head_nodp_seed$sd.log" 2>&1 || { echo "[FAIL] P4 control $sd"; exit 1; }
  done
  done_mark P4a_control_targets
fi
lira() { python -u scripts/lira_attack.py --dataset "$DS" "$@"; }
if stage P4b_lira_unit; then
  lira --arms sample patient --target_dir "$P/patient_dp/$DS" \
       --phase splits,train,score,attack || { echo "[FAIL] LiRA unit"; exit 1; }
  done_mark P4b_lira_unit
fi
if stage P4c_lira_control; then
  lira --arms head_nodp --target_dir "$P/mia_factorial/$DS" \
       --ckpt_pattern "ckpt_{arm}_seed{seed}.pt" --seeds 42 43 44 \
       --phase splits,train,score,attack || { echo "[FAIL] LiRA control"; exit 1; }
  done_mark P4c_lira_control
fi
if stage P4d_lira_baselines; then
  lira --arms hedfl fl2dp --target_dir "$P/baselines_lit/$DS" \
       --phase splits,train,score,attack || { echo "[FAIL] LiRA baselines"; exit 1; }
  done_mark P4d_lira_baselines
fi
echo "[$(stamp)] PERSON-LEVEL VITALDB DONE"
