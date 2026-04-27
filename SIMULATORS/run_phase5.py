"""
Phase 5 Pipeline Runner — runs all steps sequentially.
Usage: python run_phase5.py [--steps 4,5,6,7,8,9,11]
       (default: all steps 4-11)
"""

import os, sys, argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "model"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "data", "loaders"))

import numpy as np
import torch
from torch.utils.data import DataLoader, Subset, ConcatDataset

from preprocess_healthcare import HealthcareDataset
from hfl_mm_model import build_hfl_mm_hc
from device_utils import get_device, optimize_gpu, get_dataloader_kwargs
import baselines

# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR      = "data/processed/healthcare"
PART_DIR      = "data/processed/partitions/healthcare"
RESULTS_DIR   = "results/phase5"
CKPT_DIR      = "checkpoints"
ONNX_DIR      = "onnx"

N_CLASSES     = 5
N_DEVICES     = 6
N_EDGES       = 2
ROUNDS        = 15
TAU_E         = 3
EPSILON       = 1.0
DELTA         = 1e-5
LR            = 1e-3
BATCH_SIZE    = 64   # larger batch = faster
EPOCHS_B0     = 10
EPOCHS_B1     = 5

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CKPT_DIR,    exist_ok=True)
os.makedirs(ONNX_DIR,    exist_ok=True)


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_full_dataset():
    ecg    = np.load(f"{DATA_DIR}/ecg/ecg_signals.npy",   mmap_mode="r")
    labels = np.load(f"{DATA_DIR}/ecg/ecg_labels.npy")
    cxr    = np.load(f"{DATA_DIR}/cxr/cxr_images.npy",    mmap_mode="r")
    cxr_lb = np.load(f"{DATA_DIR}/cxr/cxr_labels.npy")
    tab    = np.load(f"{DATA_DIR}/tabular/tabular_features.npy")
    return HealthcareDataset(ecg, labels, cxr, cxr_lb, tab)


def load_device_loaders(batch_size=BATCH_SIZE):
    from hfl_trainer import load_partitioned_data
    loaders = []
    for dev_id in range(N_DEVICES):
        loaders.append(load_partitioned_data(PART_DIR, DATA_DIR, dev_id, batch_size))
    return loaders


def model_fn():
    return build_hfl_mm_hc(n_classes=N_CLASSES)


# ── Step 4: B0 Centralized ────────────────────────────────────────────────────

def step4_b0():
    log("=== STEP 4: Baseline B0 — Centralized (upper bound) ===")
    device = get_device(); optimize_gpu()
    ds = load_full_dataset()
    result = baselines.run_centralized(
        model_fn, ds, n_classes=N_CLASSES,
        epochs=EPOCHS_B0, lr=LR, device=device,
        output_path=f"{RESULTS_DIR}/baseline_b0.csv"
    )
    log(f"B0 done: AUC={result['test_macro_auc']:.4f}, Acc={result['test_accuracy']:.4f}")
    return result


# ── Step 5: Baselines B1–B5 ───────────────────────────────────────────────────

def step5_b1(device_loaders):
    log("=== STEP 5a: Baseline B1 — Local Only (lower bound) ===")
    device = get_device()
    result = baselines.run_local_only(
        model_fn, device_loaders, n_classes=N_CLASSES,
        epochs=EPOCHS_B1, lr=LR, device=device,
        output_path=f"{RESULTS_DIR}/baseline_b1.csv"
    )
    log(f"B1 done: AUC={result['test_macro_auc']:.4f}±{result['std_auc']:.4f}")
    return result


def step5_b2(device_loaders):
    log("=== STEP 5b: Baseline B2 — FedAvg ===")
    device = get_device()
    result = baselines.run_fedavg(
        model_fn, device_loaders, rounds=ROUNDS,
        local_epochs=1, lr=LR, device=device,
        output_path=f"{RESULTS_DIR}/baseline_b2.csv"
    )
    log(f"B2 done: AUC={result['test_macro_auc']:.4f}")
    return result


def step5_b3(device_loaders):
    log("=== STEP 5c: Baseline B3 — FedProx (mu=0.01) ===")
    device = get_device()
    result = baselines.run_fedprox(
        model_fn, device_loaders, rounds=ROUNDS,
        local_epochs=1, lr=LR, mu=0.01, device=device,
        output_path=f"{RESULTS_DIR}/baseline_b3.csv"
    )
    log(f"B3 done: AUC={result['test_macro_auc']:.4f}")
    return result


def step5_b4(device_loaders):
    log("=== STEP 5d: Baseline B4 — DP-FedAvg (ε=1.0) ===")
    device = get_device()
    result = baselines.run_dp_fedavg(
        model_fn, device_loaders, rounds=ROUNDS,
        local_epochs=1, lr=LR,
        epsilon=EPSILON, delta=DELTA, max_grad_norm=1.0,
        device=device,
        output_path=f"{RESULTS_DIR}/baseline_b4.csv"
    )
    log(f"B4 done: AUC={result['test_macro_auc']:.4f}, ε={result['epsilon_spent']:.4f}")
    return result


def step5_b5(device_loaders):
    log("=== STEP 5e: Baseline B5 — MOON (mu=5.0) ===")
    device = get_device()
    result = baselines.run_moon(
        model_fn, device_loaders, rounds=ROUNDS,
        local_epochs=1, lr=LR, mu=5.0, temperature=0.5,
        device=device,
        output_path=f"{RESULTS_DIR}/baseline_b5.csv"
    )
    log(f"B5 done: AUC={result['test_macro_auc']:.4f}")
    return result


# ── Step 6: HFL-MM-HC Training (P1) ──────────────────────────────────────────

def step6_hfl():
    log("=== STEP 6: HFL-MM-HC Training (P1, two-tier FedAvg + DP-SGD) ===")
    import types
    from hfl_trainer import train_hfl_mm_hc
    args = types.SimpleNamespace(
        data_dir       = DATA_DIR,
        partition_dir  = PART_DIR,
        rounds         = ROUNDS,
        tau_e          = TAU_E,
        n_devices      = N_DEVICES,
        n_edges        = N_EDGES,
        n_classes      = N_CLASSES,
        epsilon        = EPSILON,
        delta          = DELTA,
        max_grad_norm  = 1.0,
        alpha_conf     = 0.1,
        lr             = LR,
        batch_size     = BATCH_SIZE,
        sparsity       = 0.2,
        quant_bits     = 8,
        save_checkpoint= f"{CKPT_DIR}/best_model_hc.pt",
        output         = f"{RESULTS_DIR}/hfl_mm_hc_results.csv",
    )
    result = train_hfl_mm_hc(args)
    log(f"P1 done: Test AUC={result['test_metrics']['macro_auc']:.4f}, "
        f"Acc={result['test_metrics']['accuracy']:.4f}")
    return result


# ── Step 7: ε Sweep ───────────────────────────────────────────────────────────

def step7_epsilon_sweep():
    log("=== STEP 7: ε Privacy-Accuracy Sweep ===")
    import types
    from epsilon_sweep import run_epsilon_sweep
    args = types.SimpleNamespace(
        data_dir      = DATA_DIR,
        partition_dir = PART_DIR,
        n_classes     = N_CLASSES,
        n_devices     = N_DEVICES,
        n_edges       = N_EDGES,
        rounds        = 10,    # fewer rounds for sweep speed
        tau_e         = 3,
        epsilons      = [0.5, 1.0, 2.0],   # key points only — 0.1 too noisy, inf = B0
        delta         = DELTA,
        output_dir    = f"{RESULTS_DIR}/epsilon_sweep",
    )
    result = run_epsilon_sweep(args)
    log("ε sweep done")
    return result


# ── Step 8: ONNX Export ───────────────────────────────────────────────────────

def step8_onnx():
    log("=== STEP 8: ONNX Export + INT8 Quantization ===")
    import types
    from onnx_exporter import export_onnx
    ckpt_path = f"{CKPT_DIR}/best_model_hc.pt"
    if not os.path.exists(ckpt_path):
        log("WARNING: No checkpoint found, exporting untrained model.")
    args = types.SimpleNamespace(
        checkpoint   = ckpt_path,
        n_classes    = N_CLASSES,
        output_fp32  = f"{ONNX_DIR}/hfl_mm_hc.onnx",
        output_int8  = f"{ONNX_DIR}/hfl_mm_hc_int8.onnx",
    )
    result = export_onnx(args)
    log("ONNX export done")
    return result


# ── Step 9: Inference Benchmark ───────────────────────────────────────────────

def step9_bench():
    log("=== STEP 9: Inference Latency Benchmark ===")
    import types
    from inference_bench import run_benchmark
    args = types.SimpleNamespace(
        model    = f"{ONNX_DIR}/hfl_mm_hc_int8.onnx",
        n_runs   = 200,
        warmup   = 20,
        provider = "CPUExecutionProvider",
        output   = f"{RESULTS_DIR}/inference_latency/bench_results.csv",
    )
    result = run_benchmark(args)
    log(f"Inference benchmark done: P50={result.get('p50_ms','?')}ms, "
        f"P95={result.get('p95_ms','?')}ms")
    return result


# ── Step 11: Collect Results ──────────────────────────────────────────────────

def step11_collect():
    log("=== STEP 11: Collecting All Phase 5 Results ===")
    import csv, glob

    summary = []
    for csv_file in sorted(glob.glob(f"{RESULTS_DIR}/baseline_b*.csv")):
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                summary.append(row)

    hfl_csv = f"{RESULTS_DIR}/hfl_mm_hc_results.csv"
    if os.path.exists(hfl_csv):
        with open(hfl_csv) as f:
            rows = list(csv.DictReader(f))
            if rows:
                last = rows[-1]
                summary.append({"baseline": "P1_HFL_MM_HC",
                                 "test_accuracy": last.get("val_accuracy", "N/A"),
                                 "test_macro_auc": last.get("val_macro_auc", "N/A"),
                                 "epsilon_spent": last.get("epsilon_spent", "N/A")})

    out = f"{RESULTS_DIR}/phase5_summary.csv"
    if summary:
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=summary[0].keys())
            writer.writeheader()
            writer.writerows(summary)
        log(f"Summary saved: {out}")

    # Print table
    print("\n" + "="*70)
    print("PHASE 5 RESULTS SUMMARY")
    print("="*70)
    for row in summary:
        name = row.get("baseline", "?")
        auc  = row.get("test_macro_auc", "N/A")
        acc  = row.get("test_accuracy", "N/A")
        try: auc = f"{float(auc):.4f}"
        except: pass
        try: acc = f"{float(acc):.4f}"
        except: pass
        print(f"  {name:<22} AUC={auc}  Acc={acc}")
    print("="*70)


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_steps(s):
    steps = set()
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            steps.update(range(int(a), int(b)+1))
        else:
            steps.add(int(part))
    return steps


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", default="4,5,6,7,8,9,11",
                        help="Comma-separated step numbers to run (e.g. 4,5,6)")
    args = parser.parse_args()
    steps = parse_steps(args.steps)

    t0 = time.time()
    log(f"Starting Phase 5 pipeline — steps: {sorted(steps)}")

    device_loaders = None

    if 4 in steps:
        step4_b0()

    if any(s in steps for s in [5, 6, 7, 8, 9]):
        log("Loading device loaders for steps 5/6...")
        device_loaders = load_device_loaders()

    if 5 in steps:
        step5_b1(device_loaders)
        step5_b2(device_loaders)
        step5_b3(device_loaders)
        step5_b4(device_loaders)
        step5_b5(device_loaders)

    if 6 in steps:
        step6_hfl()

    if 7 in steps:
        step7_epsilon_sweep()

    if 8 in steps:
        step8_onnx()

    if 9 in steps:
        step9_bench()

    if 11 in steps:
        step11_collect()

    elapsed = time.time() - t0
    log(f"Pipeline complete in {elapsed/60:.1f} min")
