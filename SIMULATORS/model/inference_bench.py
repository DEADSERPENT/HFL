"""
Inference Latency Benchmark — Phase 5 (D5.11)
Measures end-to-end inference latency for ONNX INT8 model on edge hardware.
Reports P50, P95, P99 latency across 1000 runs (100 warmup).
QoS target: P95 < 100 ms.

Latency breakdown measured:
  L_preproc  — NumPy tensor construction + normalization (simulated)
  L_inference — ONNX Runtime forward pass
  L_conformal — Prediction set construction from logits
  L_post      — Softmax + argmax + formatting
"""

import os
import sys
import time
import argparse
import csv
import json

import numpy as np


def simulate_preprocessing(ecg_shape=(1, 12, 1000), cxr_shape=(1, 3, 224, 224)):
    """Simulate sensor data loading + normalization (no disk I/O in benchmark)."""
    ecg = np.random.randn(*ecg_shape).astype(np.float32)
    # Per-lead z-score normalization
    mean = ecg.mean(axis=2, keepdims=True)
    std  = ecg.std(axis=2, keepdims=True) + 1e-8
    ecg  = (ecg - mean) / std

    cxr = np.random.randn(*cxr_shape).astype(np.float32)
    # ImageNet normalization
    imagenet_mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 3, 1, 1)
    imagenet_std  = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 3, 1, 1)
    cxr = (cxr - imagenet_mean) / imagenet_std
    return ecg, cxr


def conformal_prediction_set(logits: np.ndarray, q_global: float = 0.9, alpha: float = 0.1):
    """Construct conformal prediction set from logits."""
    probs = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)  # softmax
    # Prediction set: all classes y where 1 - p[y] <= q_global
    nonconformity = 1.0 - probs
    pred_set = [list(np.where(nonconformity[i] <= q_global)[0]) for i in range(len(logits))]
    top_class = np.argmax(probs, axis=1)
    return pred_set, top_class, probs


CLASS_NAMES = ["NORM", "MI", "STTC", "CD", "HYP"]


def benchmark_onnx(model_path: str, n_runs: int, warmup: int, provider: str,
                   q_global: float, output_csv: str):
    try:
        import onnxruntime as ort
    except ImportError:
        print("[ERROR] onnxruntime not installed. pip install onnxruntime-gpu")
        sys.exit(1)

    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    sess = ort.InferenceSession(model_path, providers=providers)
    active_provider = sess.get_providers()[0]
    if active_provider != "CUDAExecutionProvider":
        print(f"[Benchmark] WARNING: GPU provider not active — running on {active_provider}.")
        print("            Install onnxruntime-gpu for GPU inference.")
    else:
        print(f"[Benchmark] Running on CUDAExecutionProvider (GPU).")
    print(f"[INFO] Model loaded: {model_path}")
    print(f"[INFO] Execution provider: {sess.get_providers()[0]}")

    timing = {
        "preproc_ms": [],
        "inference_ms": [],
        "conformal_ms": [],
        "post_ms": [],
        "total_ms": [],
    }

    for run_idx in range(warmup + n_runs):
        t0 = time.perf_counter()

        # L_preproc
        t_pre = time.perf_counter()
        ecg, cxr = simulate_preprocessing()
        t_pre_end = time.perf_counter()

        # L_inference
        t_inf = time.perf_counter()
        outputs = sess.run(None, {"ecg": ecg, "cxr": cxr})
        logits = outputs[0]
        t_inf_end = time.perf_counter()

        # L_conformal
        t_conf = time.perf_counter()
        pred_set, top_class, probs = conformal_prediction_set(logits, q_global=q_global)
        t_conf_end = time.perf_counter()

        # L_post
        t_post = time.perf_counter()
        result = {
            "prediction": CLASS_NAMES[int(top_class[0])],
            "confidence": float(probs[0, int(top_class[0])]),
            "prediction_set": [CLASS_NAMES[c] for c in pred_set[0]],
            "set_size": len(pred_set[0]),
        }
        _ = json.dumps(result)  # simulate serialization
        t_post_end = time.perf_counter()

        t1 = time.perf_counter()

        if run_idx >= warmup:
            timing["preproc_ms"].append((t_pre_end - t_pre) * 1000)
            timing["inference_ms"].append((t_inf_end - t_inf) * 1000)
            timing["conformal_ms"].append((t_conf_end - t_conf) * 1000)
            timing["post_ms"].append((t_post_end - t_post) * 1000)
            timing["total_ms"].append((t1 - t0) * 1000)

    def stats(arr):
        a = np.array(arr)
        return {
            "mean": float(np.mean(a)),
            "p50":  float(np.percentile(a, 50)),
            "p95":  float(np.percentile(a, 95)),
            "p99":  float(np.percentile(a, 99)),
            "min":  float(np.min(a)),
            "max":  float(np.max(a)),
        }

    results = {k: stats(v) for k, v in timing.items()}

    print("\n" + "=" * 60)
    print("  INFERENCE LATENCY BENCHMARK RESULTS")
    print(f"  Model : {os.path.basename(model_path)}")
    print(f"  Runs  : {n_runs}  |  Warmup: {warmup}")
    print("=" * 60)
    print(f"{'Component':<20} {'Mean':>8} {'P50':>8} {'P95':>8} {'P99':>8}  (ms)")
    print("-" * 60)
    for comp, s in results.items():
        print(f"  {comp:<18} {s['mean']:>7.2f} {s['p50']:>7.2f} {s['p95']:>7.2f} {s['p99']:>7.2f}")
    print("-" * 60)

    total_p95 = results["total_ms"]["p95"]
    target_ms = 100.0
    status = "PASS" if total_p95 < target_ms else "FAIL"
    print(f"\n  QoS target (P95 < {target_ms}ms): {total_p95:.2f}ms → [{status}]")
    print("=" * 60)

    # Write CSV
    os.makedirs(os.path.dirname(output_csv) if os.path.dirname(output_csv) else ".", exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        fieldnames = ["component", "mean_ms", "p50_ms", "p95_ms", "p99_ms", "min_ms", "max_ms"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for comp, s in results.items():
            writer.writerow({
                "component": comp,
                "mean_ms": round(s["mean"], 3),
                "p50_ms":  round(s["p50"], 3),
                "p95_ms":  round(s["p95"], 3),
                "p99_ms":  round(s["p99"], 3),
                "min_ms":  round(s["min"], 3),
                "max_ms":  round(s["max"], 3),
            })
    print(f"\n[SAVED] Latency results → {output_csv}")
    return results




def main():
    parser = argparse.ArgumentParser(description="Inference latency benchmark")
    parser.add_argument("--model", default="onnx/hfl_mm_hc_int8.onnx",
                        help="Path to ONNX model (INT8 recommended)")
    parser.add_argument("--n_runs", type=int, default=1000)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--provider", default="CUDAExecutionProvider",
                        choices=["CUDAExecutionProvider", "CPUExecutionProvider"])
    parser.add_argument("--q_global", type=float, default=0.9,
                        help="Conformal quantile threshold")
    parser.add_argument("--output", default="results/phase5/inference_latency/bench_results.csv")
    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"[Benchmark] ONNX model not found at {args.model}.")
        print("            Run: python model/onnx_exporter.py first.")
        sys.exit(1)

    benchmark_onnx(args.model, args.n_runs, args.warmup,
                   args.provider, args.q_global, args.output)


if __name__ == "__main__":
    main()
