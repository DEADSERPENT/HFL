#!/usr/bin/env bash
#==============================================================================
# run_eicu_network_evidence.sh — the two evidence files objectives_<ds>.json
# reads for O1 / O1b / O3b, which the pipeline's ns3_network stage does not
# write (that stage is ns3_phase5_integration, an analytical per-round model):
#   measure_uplink.py   -> results/phase5/uplink_measured_<ds>.json   (O1)
#   hfl_network_sim.py  -> results/ns3/ns3_results_<ds>.csv            (O1b, O3b)
# then rescores the objectives.
#
#   bash SIMULATORS/scripts/run_eicu_network_evidence.sh [dataset]  (default eicu)
#
# Waits for the latency bench only: NS-3 is CPU-bound and would contaminate a
# latency figure taken at the same time. It may share the machine with GPU
# training, which slows both but biases neither (simulated time, not wall time).
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
DS="${1:-eicu}"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "[$(stamp)] waiting for latency bench / training to finish ..."
while pgrep -f "run_latency_bench\.sh|inference_bench\.py" \
      >/dev/null 2>&1; do sleep 60; done
echo "[$(stamp)] idle — starting ($DS)"

echo; echo "=== measure_uplink ($(stamp)) ==="
python -u "$SIM/scripts/measure_uplink.py" --dataset "$DS" \
  || echo "[FAIL] measure_uplink $DS"

echo; echo "=== hfl_network_sim, packet-level ($(stamp)) ==="
# --ns3_every 1: packet-level on EVERY round, as for vitaldb/wear and as the
# paper states; the default (10) composes 9 rounds in 10 analytically.
python -u "$SIM/ns3/hfl-scenarios/hfl_network_sim.py" --dataset "$DS" --ns3_every 1 \
  || echo "[FAIL] hfl_network_sim $DS"

echo; echo "=== objectives ($(stamp)) ==="
python -u "$SIM/scripts/check_objectives.py" --dataset "$DS" \
  --results_dir "$SIM/results/phase5" \
  --output "$SIM/results/phase5/objectives_${DS}.json"
echo "[$(stamp)] DONE"
