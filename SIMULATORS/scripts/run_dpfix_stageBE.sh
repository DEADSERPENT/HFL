#!/usr/bin/env bash
#==============================================================================
# run_dpfix_stageBE.sh — stages after A of the 2026-10-22 privacy re-run.
# Every patient-level result below was produced by the pre-fix mechanism
# (|S| divisor, one-client calibration, per-call aggregation weights). Each
# stage MOVES the old patient-arm artifacts to results/_archive_pre_dpfix_20261022/
# (same relative path) and re-runs the original script with its original
# arguments, so record-level arms are reused and only patient arms retrain.
#
#   bash SIMULATORS/scripts/run_dpfix_stageBE.sh
#
# Order (paper priority): C1 k-law VitalDB eps1  C2 k-law VitalDB eps0.8
#   E MIA patient arm + attribution   B pretrained-init sweep (VitalDB)
#   C3 k-law eICU   D1 clip rule VitalDB   D2 clip rule eICU (natural)
# Waits for stage A. Resumable: a stage with its marker is skipped; inside a
# stage the original scripts resume by checkpoint.
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
ARCH="$SIM/results/_archive_pre_dpfix_20261022"
MARKS="$SIM/results/phase5/.dpfix"
mkdir -p "$MARKS"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

# Move a path (relative to SIMULATORS/) into the archive, once.
archive() {
  local p
  for p in "$@"; do
    [[ -e "$p" ]] || continue
    if [[ -e "$ARCH/$p" ]]; then rm -rf "$p"; continue; fi   # archived already
    mkdir -p "$ARCH/$(dirname "$p")"; mv "$p" "$ARCH/$p"
  done
}
stage() {    # stage <name> : returns 0 if it must run
  [[ -f "$MARKS/$1.done" ]] && { echo "[$(stamp)] $1 done, skipping"; return 1; }
  echo; echo "=================== $1  ($(stamp)) ==================="; return 0
}
done_mark() { touch "$MARKS/$1.done"; echo "[$(stamp)] $1 DONE"; }

echo "[$(stamp)] waiting for stage A ..."
while pgrep -f run_dpfix_stageA.sh >/dev/null; do sleep 300; done
grep -q "STAGE A DONE" results/pipeline/_detached/dpfix_stageA.log \
  || echo "[WARN] stage A log has no STAGE A DONE line; continuing"

# ── k-law grids ────────────────────────────────────────────────────────────
klaw() {     # klaw <grid> <dataset> <k...> -- <k_scaling args>
  local grid=$1 ds=$2; shift 2
  local ks=(); while [[ $1 != "--" ]]; do ks+=("$1"); shift; done; shift
  local d
  for d in results/phase5/k_scaling/$grid/k*_seed*; do
    archive "$d/ckpt_patient.pt" "$d/hist_patient.csv" "$d/patient.log" \
            "$d/hist_patient_final.json" "$d/hist_patient_test.json"
  done
  mkdir -p "$ARCH/results/phase5/k_scaling/$grid"
  cp -n results/phase5/k_scaling/$grid/k_scaling_$ds.csv \
        "$ARCH/results/phase5/k_scaling/$grid/" 2>/dev/null
  python -u scripts/k_scaling.py --dataset "$ds" --k "${ks[@]}" \
    --out_dir "results/phase5/k_scaling/$grid" "$@"
}

if stage C1_klaw_vitaldb; then
  klaw vitaldb vitaldb 1 2 4 8 -- --epsilon 1.0 --batch_size 32 && done_mark C1_klaw_vitaldb
fi
if stage C2_klaw_vitaldb_eps080; then
  klaw vitaldb_eps080 vitaldb 1 2 4 8 -- --epsilon 0.8 --epsilon_conf 0.2 --batch_size 64 \
    && python -u scripts/analyze_k_matched.py && done_mark C2_klaw_vitaldb_eps080
fi
python -u scripts/klaw_theory_check.py | tail -25

# ── E: membership inference, patient arm ──────────────────────────────────
if stage E_mia_patient; then
  T=results/phase5/patient_dp/vitaldb
  for sd in 42 43 44 45 46; do
    if [[ ! -f "$MARKS/E_target_$sd.done" ]]; then
      archive "$T/ckpt_patient_$sd.pt" "$T/patient_seed$sd.csv" \
              "$T/patient_seed${sd}_final.json" "$T/patient_seed${sd}_test.json"
      python -u model/training/hfl_trainer.py --dataset vitaldb --rounds 10 --tau_e 5 \
        --batch_size 64 --epsilon 1.0 --seed $sd --dp_unit patient --patients_per_batch 32 \
        --freeze_encoders --pretrained_encoders checkpoints/pretrained_encoders_vitaldb.pt \
        --save_checkpoint $T/ckpt_patient_$sd.pt --output $T/patient_seed$sd.csv --no_monitor \
        && touch "$MARKS/E_target_$sd.done" || echo "[FAIL] MIA target seed $sd"
    fi
  done
  archive results/phase5/lira/vitaldb/shadows/patient
  python -u scripts/lira_attack.py --dataset vitaldb --arms patient --phase train \
    && python -u scripts/lira_attack.py --dataset vitaldb --arms sample patient \
         --phase score,attack \
    || echo "[FAIL] LiRA"
  A=results/phase5/attribution/vitaldb
  archive $A/attribution_ckpt_patient_* $A/stability_summary.json $A/attribution_paired.json
  for sd in 42 43 44 45 46; do
    python -u scripts/attribution.py --dataset vitaldb --ckpt $T/ckpt_patient_$sd.pt --baseline mean
  done
  for sd in 42 43 44; do
    python -u scripts/attribution.py --dataset vitaldb --ckpt $T/ckpt_patient_$sd.pt --baseline zero
  done
  python -u scripts/attribution_stability.py --dataset vitaldb
  python -u scripts/attribution_paired.py vitaldb
  done_mark E_mia_patient
fi

# ── B: pretrained initialisation, patient level (VitalDB) ─────────────────
if stage B_pretrained_vitaldb; then
  archive results/phase5/epsilon_sweep/vitaldb
  python -u scripts/run_b467_multiseed.py --datasets vitaldb --dp_unit patient \
    && done_mark B_pretrained_vitaldb
fi

# ── C3: k-law eICU (k <= 16: k = 32 is unsound on this cohort) ─────────────
if stage C3_klaw_eicu; then
  klaw eicu eicu 1 2 4 8 16 -- --epsilon 0.8 --batch_size 64 && done_mark C3_klaw_eicu
  python -u scripts/klaw_theory_check.py | tail -25
fi

# ── D: clipping-rule test (N-A2) ──────────────────────────────────────────
if stage D1_clip_vitaldb; then
  archive results/phase5/nd_clipnorm/vitaldb
  python -u scripts/run_nd_clipnorm.py --dataset vitaldb --k 8 --seeds 42 43 44 \
    --modes none k sqrt_k --epsilon 0.80 --batch_size 64 --rounds 10 --tau_e 5 \
    && done_mark D1_clip_vitaldb
fi
if stage D2_clip_eicu; then
  archive results/phase5/nd_clipnorm/eicu
  python -u scripts/run_nd_clipnorm.py --dataset eicu \
    --partition_dir "$SIM/data/processed/partitions/eicu" \
    --seeds 42 43 44 --modes none k sqrt_k \
    --epsilon 0.80 --batch_size 64 --rounds 10 --tau_e 5 \
    && done_mark D2_clip_eicu
fi
echo "[$(stamp)] STAGES B-E DONE"
