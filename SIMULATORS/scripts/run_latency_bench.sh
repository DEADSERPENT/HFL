#!/usr/bin/env bash
#==============================================================================
# run_latency_bench.sh — inference latency at the protocol the paper states:
# CPU provider, 1000 timed runs after 100 warm-up runs, FP32 AND INT8.
#
#   bash SIMULATORS/scripts/run_latency_bench.sh [dataset ...]   (default: all
#   datasets that have a trained checkpoint)
#
# Why: results.tex reported an INT8 / 1000-run table while the pipeline's
# latency_<ds>.csv (legacy name .json) is FP32 / 200 runs (inference_bench via run_pipeline uses
# --n_runs 200). onnx_exporter.py ships FP32 because INT8 dynamic quantisation
# measured 1.9x SLOWER on CPU for this architecture. This driver measures both
# precisions under one protocol so the paper can state which one it reports.
#
# Waits for any running training job first: a latency figure taken while the
# GPU trainer holds CPU cores is contaminated. Writes only to
# results/phase5/latency_bench/ — never overwrites the pipeline's
# latency_<ds>.csv (legacy .json), which objectives_<ds>.json cites.
#==============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROOT="$PWD"; SIM="$ROOT/SIMULATORS"
source "$ROOT/hfl_env/bin/activate"
OUT="$SIM/results/phase5/latency_bench"; ONNX="$OUT/onnx"
mkdir -p "$ONNX"
N_RUNS=1000; WARMUP=100

stamp() { date '+%Y-%m-%d %H:%M:%S'; }

# Datasets: argv, else every registry dataset with a checkpoints/best_<ds>.pt.
if [ $# -gt 0 ]; then DATASETS=("$@"); else
  mapfile -t DATASETS < <(cd "$SIM/data/loaders" && python -c \
    "from datasets import REGISTRY; print('\n'.join(sorted(REGISTRY)))")
fi

echo "[$(stamp)] waiting for training to finish before timing anything ..."
while pgrep -f "hfl_trainer\.py|run_pipeline\.py" >/dev/null 2>&1; do sleep 60; done
echo "[$(stamp)] machine idle — starting"

for ds in "${DATASETS[@]}"; do
  ckpt="$SIM/checkpoints/best_${ds}.pt"
  if [ ! -f "$ckpt" ]; then echo "[skip] $ds: no $ckpt"; continue; fi
  echo; echo "=== $ds  ($(stamp)) ==="
  fp32="$ONNX/hfl_mm_${ds}_fp32.onnx"; int8="$ONNX/hfl_mm_${ds}_int8.onnx"
  python -u "$SIM/model/deploy/onnx_exporter.py" --dataset "$ds" \
    --checkpoint "$ckpt" --output_fp32 "$fp32" --output_int8 "$int8" --int8 \
    || { echo "[FAIL] export $ds"; continue; }
  for prec in fp32 int8; do
    m="$ONNX/hfl_mm_${ds}_${prec}.onnx"
    [ -f "$m" ] || { echo "[skip] $ds $prec: export produced no model"; continue; }
    python -u "$SIM/model/deploy/inference_bench.py" --model "$m" \
      --n_runs $N_RUNS --warmup $WARMUP --provider CPUExecutionProvider \
      --output "$OUT/latency_${ds}_${prec}.csv" \
      || echo "[FAIL] bench $ds $prec"
  done
done

echo; echo "[$(stamp)] DONE. Summary (total_ms):"
for f in "$OUT"/latency_*.csv; do
  [ -f "$f" ] || continue
  printf "  %-28s " "$(basename "$f" .csv)"
  awk -F, '$1=="total_ms"{printf "mean %s  p95 %s  p99 %s\n",$2,$4,$5}' "$f"
done
