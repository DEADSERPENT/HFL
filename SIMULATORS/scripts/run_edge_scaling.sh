#!/usr/bin/env bash
#==============================================================================
# run_edge_scaling.sh — packet-level update delivery and round latency against
# the number of edge aggregators. Tests the claim in Results (quality of
# service) that the eICU delivery shortfall is contention, curable by adding
# edges, rather than a property of the protocol.
#
#   bash SIMULATORS/scripts/run_edge_scaling.sh [dataset] [edge counts...]
#   default: eicu 16 12 8 6 4 3   (cheapest first: per-sim cost falls as the
#   stations per channel fall, so early counts give usable results soonest)
#
# The dataset's own edge count is NOT re-run: results/ns3/ns3_results_<ds>.csv
# is that point. Resumable: an edge count whose CSV exists is skipped.
# CPU-only (NS-3), so it may share the machine with one GPU job.
#
#   SCENARIOS="HFL_Proposed" bash ... eicu 12 8   runs the proposed system only
#   (default: CentralizedFL HFL_Proposed). The Centralized baseline sends the
#   dense model from every client and costs ~7x more per simulated round.
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
cd "$SIM"
DS="${1:-eicu}"; shift || true
EDGES=("$@"); [[ ${#EDGES[@]} -eq 0 ]] && EDGES=(16 12 8 6 4 3)
read -ra SCN <<< "${SCENARIOS:-CentralizedFL HFL_Proposed}"
OUT="$SIM/results/ns3/edge_scaling"; mkdir -p "$OUT"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

for E in "${EDGES[@]}"; do
  CSV="$OUT/ns3_${DS}_e${E}.csv"
  if [[ -s "$CSV" ]]; then echo "[$(stamp)] e=$E exists, skipping"; continue; fi
  echo; echo "=== $DS  n_edges=$E  [${SCN[*]}]  ($(stamp)) ==="
  python -u ns3/hfl-scenarios/hfl_network_sim.py --dataset "$DS" --n_edges "$E" \
    --scenarios "${SCN[@]}" --ns3_every 1 --output "$CSV.tmp" \
    && mv "$CSV.tmp" "$CSV" || echo "[FAIL] n_edges=$E"
  python -u scripts/edge_scaling_summary.py "$DS" | tail -4
done

echo; echo "=== summary ($(stamp)) ==="
python -u scripts/edge_scaling_summary.py "$DS"
echo "[$(stamp)] DONE"
