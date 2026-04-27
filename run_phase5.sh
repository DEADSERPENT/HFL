#!/bin/bash
# Run all Phase 5 ML steps (4-11): baselines → HFL-MM-HC → ε sweep → ONNX → latency → collect
# Data must already be prepared (Steps 1-3). See RUNBOOK.md for dataset download.
set -e
source ~/HFL/hfl_env/bin/activate
cd ~/HFL/SIMULATORS
mkdir -p results/phase5 checkpoints onnx
python run_phase5.py 2>&1 | tee results/phase5/run_log.txt
