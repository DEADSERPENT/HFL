#!/usr/bin/env bash
#==============================================================================
# run_final_experiments.sh — the two runs holding up the manuscript, in order.
#
#   1. eICU fusion-balance titration   (~40 min)   amendment F-A1
#   2. N-D normalised clipping, eICU   (~27 h)     amendment N-A2
#
# SERIAL, DELIBERATELY. The box has one GPU (A2000 12 GB) and ~8 GB of free
# RAM, and the eICU corpus is 3,782,805 windows. Two concurrent loaders have
# OOM-killed work on this machine before. Neither experiment measures time or
# energy, so contention would not corrupt their metrics -- it would just risk
# killing the 27 h job to save 40 min. Not worth it.
#
# Stage 2 runs even if stage 1 fails: they test unrelated hypotheses, and the
# long job should not be lost to a short job's error.
#
# LAUNCH FROM A PLAIN TERMINAL, NOT VS CODE'S. VS Code gives its children
# oom_score_adj=100, making them preferred OOM victims, and setsid does not
# escape that cgroup.
#
#   setsid nohup bash SIMULATORS/scripts/run_final_experiments.sh \
#     > SIMULATORS/results/phase5/final_experiments.log 2>&1 < /dev/null &
#   tail -f SIMULATORS/results/phase5/final_experiments.log
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"
source "$ROOT/hfl_env/bin/activate"
NDLOG="$ROOT/SIMULATORS/results/phase5/nd_clipnorm/eicu/nd_eicu_natural.log"
mkdir -p "$(dirname "$NDLOG")"

stamp() { date '+%Y-%m-%d %H:%M:%S'; }
banner() { echo; echo "=============================================================="; \
           echo "  $1   [$(stamp)]"; echo "=============================================="; }

banner "STAGE 1/2 — eICU fusion-balance titration (F-A1, ~40 min)"
bash "$ROOT/SIMULATORS/scripts/run_fusion_balance.sh"
S1=$?
echo "[stage 1] exit=$S1 at $(stamp)"
[ $S1 -ne 0 ] && echo "[stage 1] FAILED — continuing to stage 2 regardless (independent hypotheses)."

banner "STAGE 2/2 — N-D normalised clipping on eICU (N-A2, ~27 h)"
echo "  NATURAL partition (uncapped). Amendment N-A1 established that a"
echo "  k-capped partition cannot test N-D; do not substitute one."
python -u "$ROOT/SIMULATORS/scripts/run_nd_clipnorm.py" \
  --dataset eicu \
  --partition_dir "$ROOT/SIMULATORS/data/processed/partitions/eicu" \
  --seeds 42 43 44 --modes none k sqrt_k \
  --epsilon 0.80 --batch_size 64 --rounds 10 --tau_e 5 \
  2>&1 | tee "$NDLOG"
S2=${PIPESTATUS[0]}
echo "[stage 2] exit=$S2 at $(stamp)"

banner "DONE — stage1=$S1 stage2=$S2"
cat <<'EOS'
Next, against the PRE-REGISTERED predictions (do not read these backwards):

  F3  fusion gain rises to >= +0.015      -> results/phase5/fusbal_test_n*.json
      F1/F2 are calibration preconditions, NOT hits. A flat or falling gain
      REFUTES the balance account and is reported as such.

  N2e patient-arm AUPRC under clip_norm=k beats 'none' by >= +0.010
      -> results/phase5/nd_clipnorm/eicu/nd_clipnorm_eicu_natural.json
      N3e is NOT TESTED on eICU (no natural-partition record arm).
      A failure STRENGTHENS the k-law cost claim. Report either way.

Then replace [PENDING F-A1] and [PENDING N-A2] in discussion.tex and
conclusion.tex and rebuild:  cd paper && ./build_paper.sh --clean
EOS
