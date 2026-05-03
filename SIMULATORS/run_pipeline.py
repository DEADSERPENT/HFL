#!/usr/bin/env python3
"""
HFL Unified Pipeline Runner — Phase 5
======================================
Single entry point for the complete Phase 5 experiment.

Full automation chain:
  0. Data readiness check  (or --prepare-data to download/preprocess/partition)
  1. Baseline training      (B0 Centralized → B5 MOON)
  2. HFL-MM-HC training     (P1 — two-tier FedAvg + DP-SGD + conformal)
  3. ONNX export + latency  (FP32 → INT8 quantize → inference benchmark)
  4. NS-3 simulation        (network QoS from actual uplink bytes)
  5. CloudSim simulation    (energy/resource from Maven)
  6. Results + QoS dash     (aggregate all CSVs, pass/fail table)

Usage
-----
  python run_pipeline.py                          # full pipeline
  python run_pipeline.py --mode hfl               # train + export + sim + collect
  python run_pipeline.py --mode baselines         # baselines only + sim + collect
  python run_pipeline.py --mode sim               # re-run sim on existing results
  python run_pipeline.py --mode collect           # re-print results/dashboard only
  python run_pipeline.py --prepare-data           # download + preprocess + partition
  python run_pipeline.py --no-sim                 # skip NS-3 + CloudSim
  python run_pipeline.py --no-bench               # skip ONNX export + bench
  python run_pipeline.py --skip B4,B5             # skip specific baselines

Options
-------
  --mode           all | baselines | hfl | sim | collect  (default: all)
  --rounds N       FL rounds for HFL-MM-HC                (default: 20)
  --tau_e N        edge rounds per global round            (default: 5)
  --batch_size N   mini-batch size                         (default: 64)
  --epsilon F      DP privacy budget                       (default: 1.0)
  --lr F           learning rate                           (default: 1e-3)
  --n_devices N    healthcare IoT devices                  (default: 6)
  --n_edges N      edge servers                            (default: 2)
  --n_classes N    output classes                          (default: 5)
  --skip B         comma-separated baselines to skip (e.g. B4,B5)
  --no-sim         skip NS-3 and CloudSim steps
  --no-cloudsim    skip CloudSim only
  --no-bench       skip ONNX export + inference benchmark
  --prepare-data   run data download + preprocess + partition
  --data_dir PATH  path to processed healthcare data
  --part_dir PATH  path to partition index files
  --results_dir P  output directory
"""

import os
import sys
import csv
import time
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent.resolve()
MODEL_DIR    = SCRIPT_DIR / "model"
SCRIPTS_DIR  = SCRIPT_DIR / "scripts"
DATA_DIR     = SCRIPT_DIR / "data"
RESULTS_BASE = SCRIPT_DIR / "results"
PYTHON       = sys.executable


# ── Console helpers ───────────────────────────────────────────────────────────

class _Col:
    GRN = "\033[92m"
    YEL = "\033[93m"
    RED = "\033[91m"
    CYN = "\033[96m"
    BLD = "\033[1m"
    RST = "\033[0m"


def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "·", "OK": "✓", "WARN": "!", "ERR": "✗"}
    icon  = icons.get(level, "·")
    color = {"OK": _Col.GRN, "WARN": _Col.YEL, "ERR": _Col.RED}.get(level, "")
    print(f"[{ts}] {color}{icon} {msg}{_Col.RST}", flush=True)


def banner(title: str, step: int = 0, total: int = 0) -> None:
    step_tag = f"  STEP {step}/{total}  —  " if step > 0 else "  "
    full_title = f"{step_tag}{title}"
    line = "═" * (len(full_title) + 4)
    print(f"\n{_Col.CYN}{_Col.BLD}{line}", flush=True)
    print(f"  {full_title}", flush=True)
    print(f"{line}{_Col.RST}\n", flush=True)


def elapsed(t0: float) -> str:
    s = int(time.time() - t0)
    return f"{s // 60}m {s % 60}s"


def run_subprocess(cmd: list, cwd: str = None, label: str = "") -> tuple:
    """Run cmd, stream output live, return (returncode, last_line)."""
    log(f"Running: {' '.join(str(c) for c in cmd)}" +
        (f"  [cwd={cwd}]" if cwd else ""))
    last_line = ""
    try:
        proc = subprocess.Popen(
            [str(c) for c in cmd],
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                print(f"    {line}", flush=True)
                last_line = line
        proc.wait()
        return proc.returncode, last_line
    except FileNotFoundError as e:
        log(f"{label} binary not found: {e}", "ERR")
        return 1, str(e)


# ── Step 0: Data readiness ────────────────────────────────────────────────────

def _data_exists(args) -> tuple:
    """Return (processed_ok, partitions_ok)."""
    ecg_ok  = (Path(args.data_dir) / "ecg" / "ecg_signals.npy").exists()
    part_ok = (Path(args.part_dir) / "partition_meta.json").exists()
    return ecg_ok, part_ok


def check_data(args) -> bool:
    """Verify processed data and partition indices exist. Exit with help if not."""
    ecg_ok, part_ok = _data_exists(args)
    if ecg_ok and part_ok:
        log("Processed data and partition indices found.", "OK")
        return True

    log("Processed data or partition indices missing.", "ERR")
    if not ecg_ok:
        log(f"  Missing: {args.data_dir}/ecg/ecg_signals.npy", "ERR")
    if not part_ok:
        log(f"  Missing: {args.part_dir}/partition_meta.json", "ERR")

    print(f"\n{_Col.YEL}To prepare data automatically, run:{_Col.RST}")
    print(f"  python {Path(__file__).name} --prepare-data\n")
    print("Or manually:")
    print(f"  python data/loaders/download_datasets.py")
    print(f"  python data/loaders/preprocess_healthcare.py")
    print(f"  python data/loaders/partition_noniid.py "
          f"--n_devices {args.n_devices} --n_edges {args.n_edges}\n")
    return False


def run_prepare_data(args) -> bool:
    """Download → preprocess → partition. Skips steps already done."""
    banner("DATA PREPARATION  (download + preprocess + partition)")
    t0 = time.time()
    ok = True

    raw_ptbxl = str(DATA_DIR / "raw" / "ptb-xl")
    raw_cxr   = str(DATA_DIR / "raw" / "chest-xray-pneumonia")

    # ── 0a: Download ──────────────────────────────────────────────────────────
    log("Step 0a: Downloading datasets (PTB-XL + Chest X-Ray)...")
    rc, _ = run_subprocess([
        PYTHON, "-u",
        str(DATA_DIR / "loaders" / "download_datasets.py"),
        "--ptbxl_dir", raw_ptbxl,
        "--cxr_dir",   raw_cxr,
    ], cwd=SCRIPT_DIR, label="download_datasets.py")
    if rc != 0:
        log("Dataset download failed. See messages above.", "ERR")
        log("Chest X-Ray (Kaggle) requires a Kaggle API key or manual download.", "WARN")
        ok = False

    # ── 0b: Preprocess ────────────────────────────────────────────────────────
    ecg_ok, _ = _data_exists(args)
    if not ecg_ok or True:  # always rerun if --prepare-data explicitly requested
        log("Step 0b: Preprocessing ECG + CXR + tabular...")
        rc, _ = run_subprocess([
            PYTHON, "-u",
            str(DATA_DIR / "loaders" / "preprocess_healthcare.py"),
            "--ptbxl_dir",  raw_ptbxl,
            "--cxr_dir",    raw_cxr,
            "--output_dir", args.data_dir,
        ], cwd=SCRIPT_DIR, label="preprocess_healthcare.py")
        if rc != 0:
            log("Preprocessing failed.", "ERR")
            ok = False
    else:
        log("Step 0b: Processed data already present — skipping.", "INFO")

    # ── 0c: Partition ─────────────────────────────────────────────────────────
    _, part_ok = _data_exists(args)
    if not part_ok or True:
        log("Step 0c: Creating Dirichlet partitions...")
        rc, _ = run_subprocess([
            PYTHON, "-u",
            str(DATA_DIR / "loaders" / "partition_noniid.py"),
            "--input_dir",  str(Path(args.data_dir) / "ecg"),
            "--output_dir", args.part_dir,
            "--n_devices",  str(args.n_devices),
            "--n_edges",    str(args.n_edges),
        ], cwd=SCRIPT_DIR, label="partition_noniid.py")
        if rc != 0:
            log("Partitioning failed.", "ERR")
            ok = False
    else:
        log("Step 0c: Partition indices already present — skipping.", "INFO")

    if ok:
        log(f"Data preparation complete in {elapsed(t0)}", "OK")
    return ok


# ── Step 1: Baselines ─────────────────────────────────────────────────────────

def run_baselines(args, step: int, total: int) -> bool:
    banner("Baseline Training  (B0 Centralized → B5 MOON)", step, total)
    t0 = time.time()

    # Convert comma-separated skip list to space-separated for baselines.py
    skip_list = [b.strip() for b in args.skip.split(",") if b.strip()] if args.skip else []

    cmd = [
        PYTHON, "-u",
        str(MODEL_DIR / "baselines.py"),
        "--data_dir",      args.data_dir,
        "--partition_dir", args.part_dir,
        "--output_dir",    args.results_dir,
        "--rounds",        str(args.rounds),
        "--local_epochs",  "1",
        "--batch_size",    str(args.batch_size),
        "--lr",            str(args.lr),
        "--epsilon",       str(args.epsilon),
    ]
    if skip_list:
        cmd += ["--skip"] + [b.lower() for b in skip_list]

    rc, _ = run_subprocess(cmd, cwd=SCRIPT_DIR, label="baselines.py")
    if rc == 0:
        log(f"Baselines complete in {elapsed(t0)}", "OK")
    else:
        log(f"Baselines exited with code {rc}", "ERR")
    return rc == 0


# ── Step 2: HFL-MM-HC training ────────────────────────────────────────────────

def run_hfl(args, step: int, total: int) -> bool:
    banner("HFL-MM-HC Training  (P1 — two-tier FedAvg + DP-SGD + conformal)",
           step, total)
    t0 = time.time()

    hfl_csv = str(Path(args.results_dir) / "hfl_mm_hc_results.csv")
    ckpt    = str(SCRIPT_DIR / "checkpoints" / "best_model_hc.pt")

    cmd = [
        PYTHON, "-u",
        str(MODEL_DIR / "hfl_trainer.py"),
        "--data_dir",        args.data_dir,
        "--partition_dir",   args.part_dir,
        "--rounds",          str(args.rounds),
        "--tau_e",           str(args.tau_e),
        "--n_devices",       str(args.n_devices),
        "--n_edges",         str(args.n_edges),
        "--n_classes",       str(args.n_classes),
        "--batch_size",      str(args.batch_size),
        "--epsilon",         str(args.epsilon),
        "--lr",              str(args.lr),
        "--save_checkpoint", ckpt,
        "--output",          hfl_csv,
    ]
    rc, _ = run_subprocess(cmd, cwd=SCRIPT_DIR, label="hfl_trainer.py")
    if rc == 0:
        log(f"HFL-MM-HC training complete in {elapsed(t0)}", "OK")
    else:
        log(f"hfl_trainer.py exited with code {rc}", "ERR")
    return rc == 0


# ── Step 3: ONNX export + inference benchmark ─────────────────────────────────

def run_onnx_bench(args, step: int, total: int) -> bool:
    banner("ONNX Export + Inference Latency Benchmark", step, total)
    t0 = time.time()

    ckpt_path   = str(SCRIPT_DIR / "checkpoints" / "best_model_hc.pt")
    onnx_fp32   = str(SCRIPT_DIR / "onnx" / "hfl_mm_hc.onnx")
    onnx_int8   = str(SCRIPT_DIR / "onnx" / "hfl_mm_hc_int8.onnx")
    bench_csv   = str(Path(args.results_dir) / "inference_latency" / "bench_results.csv")

    if not Path(ckpt_path).exists():
        log(f"Checkpoint not found at {ckpt_path} — skipping ONNX export.", "WARN")
        log("Train the HFL-MM-HC model first (--mode hfl).", "WARN")
        return True  # non-fatal: benchmark result contributes to QoS but isn't blocking

    # 3a: ONNX export
    log("Step 3a: Exporting model to ONNX FP32 → INT8...")
    rc, _ = run_subprocess([
        PYTHON, "-u",
        str(MODEL_DIR / "onnx_exporter.py"),
        "--checkpoint",   ckpt_path,
        "--output_fp32",  onnx_fp32,
        "--output_int8",  onnx_int8,
        "--n_classes",    str(args.n_classes),
    ], cwd=SCRIPT_DIR, label="onnx_exporter.py")
    if rc != 0:
        log("ONNX export failed — skipping benchmark.", "WARN")
        return True

    # 3b: Inference benchmark
    log("Step 3b: Benchmarking inference latency (1000 runs, 100 warmup)...")
    rc, _ = run_subprocess([
        PYTHON, "-u",
        str(MODEL_DIR / "inference_bench.py"),
        "--model",  onnx_int8,
        "--output", bench_csv,
    ], cwd=SCRIPT_DIR, label="inference_bench.py")
    if rc == 0:
        log(f"ONNX export + benchmark complete in {elapsed(t0)}", "OK")
    else:
        log("Inference benchmark failed — continuing without latency data.", "WARN")

    return True  # non-fatal


# ── Step 4: NS-3 simulation ───────────────────────────────────────────────────

def _get_actual_rounds(results_dir: str, requested_rounds: int) -> int:
    """
    Read hfl_mm_hc_results.csv to find rounds actually completed.
    Falls back to requested_rounds if file missing or unreadable.
    """
    csv_path = Path(results_dir) / "hfl_mm_hc_results.csv"
    if not csv_path.exists():
        return requested_rounds
    try:
        with open(csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        if rows:
            return int(rows[-1].get("global_round", requested_rounds))
    except Exception:
        pass
    return requested_rounds


def run_ns3(args, step: int, total: int) -> bool:
    banner("NS-3 Network Simulation  (Phase 5 payload + QoS update)", step, total)
    t0 = time.time()

    # Use actual rounds completed, not just the requested count
    actual_rounds = _get_actual_rounds(args.results_dir, args.rounds)
    if actual_rounds != args.rounds:
        log(f"Training stopped at round {actual_rounds}/{args.rounds} "
            f"(DP budget) — using actual round count for NS-3.", "WARN")

    hfl_csv = str(Path(args.results_dir) / "hfl_mm_hc_results.csv")
    out_csv = str(RESULTS_BASE / "ns3" / "ns3_phase5_results.csv")
    os.makedirs(str(RESULTS_BASE / "ns3"), exist_ok=True)

    cmd = [
        PYTHON, "-u",
        str(SCRIPTS_DIR / "ns3_phase5_integration.py"),
        "--hfl_results", hfl_csv,
        "--n_rounds",    str(actual_rounds),
        "--output",      out_csv,
    ]
    rc, _ = run_subprocess(cmd, cwd=SCRIPT_DIR, label="ns3_phase5_integration.py")
    if rc == 0:
        log(f"NS-3 integration complete in {elapsed(t0)}", "OK")
    else:
        log(f"ns3_phase5_integration.py exited with code {rc}", "ERR")
    return rc == 0


# ── Step 5: CloudSim simulation ───────────────────────────────────────────────

def run_cloudsim(args, step: int, total: int) -> bool:
    banner("CloudSim Plus  Energy / Resource Simulation", step, total)
    t0 = time.time()

    cloudsim_dir = SCRIPT_DIR / "cloudsim-plus" / "hfl-simulation"
    pom = cloudsim_dir / "pom.xml"

    if not pom.exists():
        log(f"CloudSim pom.xml not found at {pom} — skipping.", "WARN")
        log("Phase 4 CloudSim results remain valid.", "INFO")
        return True

    cloudsim_out = str(RESULTS_BASE / "cloudsim")
    cmd = [
        "mvn", "-q",
        "exec:java",
        "-Dexec.mainClass=hfl.HFLCloudSimulation",
        f"-Dhfl.rounds={args.rounds}",
        f"-Dhfl.devices={args.n_devices}",
        f"-Dhfl.edges={args.n_edges}",
        f"-Dhfl.outputDir={cloudsim_out}",
    ]
    rc, _ = run_subprocess(cmd, cwd=str(cloudsim_dir), label="CloudSim")
    if rc == 0:
        log(f"CloudSim complete in {elapsed(t0)}", "OK")
    else:
        log("CloudSim exited with non-zero code — Phase 4 data remains valid.", "WARN")

    return True  # non-fatal


# ── Step 6: Results collection ────────────────────────────────────────────────

def run_collect(args, step: int, total: int) -> bool:
    banner("Results Collection + QoS Dashboard", step, total)
    t0 = time.time()

    ns3_dir = str(RESULTS_BASE / "ns3")
    cmd = [
        PYTHON, "-u",
        str(SCRIPTS_DIR / "collect_phase5_results.py"),
        "--results_dir", args.results_dir,
        "--ns3_dir",     ns3_dir,
        "--output",      str(Path(args.results_dir) / "phase5_results.csv"),
    ]
    rc, _ = run_subprocess(cmd, cwd=SCRIPT_DIR, label="collect_phase5_results.py")
    if rc == 0:
        log(f"Results collected in {elapsed(t0)}", "OK")
    else:
        log(f"collect_phase5_results.py exited with code {rc}", "ERR")
    return rc == 0


# ── QoS dashboard ─────────────────────────────────────────────────────────────

def print_qos_dashboard(results_dir: str) -> None:
    banner("QoS TARGET DASHBOARD  (Phase 5 Final Validation)")

    csv_path = Path(results_dir) / "phase5_results.csv"
    if not csv_path.exists():
        log("phase5_results.csv not found.", "WARN")
        return

    systems, qos_rows = [], []
    current_section = None
    header = None

    with open(csv_path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.rstrip("\r\n").strip()
            if not raw:
                continue
            if raw.startswith("## SECTION"):
                current_section = raw
                header = None
                continue
            if raw.startswith("#"):
                continue
            cols = [c.strip() for c in raw.split(",")]
            if header is None:
                header = cols
                continue
            row = dict(zip(header, cols))
            if current_section and "SECTION 1" in current_section:
                systems.append(row)
            elif current_section and "SECTION 3" in current_section:
                qos_rows.append(row)

    if systems:
        print(f"  {'System':<26} {'AUC':>8}  {'Acc':>7}  {'ε':>7}")
        print(f"  {'-'*26} {'-'*8}  {'-'*7}  {'-'*7}")
        for s in systems:
            name = s.get("system", "?")
            auc  = s.get("macro_auc", "N/A")
            acc  = s.get("accuracy", "N/A")
            eps  = s.get("epsilon", "N/A")
            try:    auc_f = f"{float(auc):.4f}"
            except: auc_f = auc
            try:    acc_f = f"{float(acc):.4f}"
            except: acc_f = acc
            highlight = _Col.GRN if ("P1" in name or "HFL-MM" in name) else ""
            print(f"  {highlight}{name:<26} {auc_f:>8}  {acc_f:>7}  {eps:>7}{_Col.RST}")
        print()

    if qos_rows:
        all_pass = True
        for q in qos_rows:
            target = q.get("qos_target", "?")
            value  = q.get("value", "?")
            status = q.get("status", "?")
            if status == "PASS":
                icon = f"{_Col.GRN}✓ PASS{_Col.RST}"
            elif status == "FAIL":
                icon = f"{_Col.RED}✗ FAIL{_Col.RST}"
                all_pass = False
            else:
                icon = f"{_Col.YEL}? {status}{_Col.RST}"
            print(f"  {icon}  {target:<38}  {value}")
        print()
        if all_pass:
            print(f"  {_Col.GRN}{_Col.BLD}All Phase 5 QoS targets PASSED ✓{_Col.RST}")
        else:
            print(f"  {_Col.YEL}Some targets pending — see FAILs above.{_Col.RST}")
    else:
        log("No QoS rows found in phase5_results.csv", "WARN")
    print()


# ── Argument parsing ──────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="HFL Unified Pipeline Runner — Phase 5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--mode", default="all",
                   choices=["all", "baselines", "hfl", "sim", "collect"],
                   help="Which stages to run (default: all)")
    # Hyperparameters
    p.add_argument("--rounds",      type=int,   default=20)
    p.add_argument("--tau_e",       type=int,   default=5,
                   help="Edge rounds per global round (default: 5)")
    p.add_argument("--batch_size",  type=int,   default=64)
    p.add_argument("--epsilon",     type=float, default=1.0)
    p.add_argument("--lr",          type=float, default=1e-3)
    p.add_argument("--n_devices",   type=int,   default=6)
    p.add_argument("--n_edges",     type=int,   default=2)
    p.add_argument("--n_classes",   type=int,   default=5)
    # Skip / flags
    p.add_argument("--skip",        default="",
                   help="Comma-separated baselines to skip (e.g. B4,B5)")
    p.add_argument("--no-sim",      dest="no_sim",      action="store_true",
                   help="Skip NS-3 and CloudSim")
    p.add_argument("--no-cloudsim", dest="no_cloudsim", action="store_true",
                   help="Skip CloudSim only")
    p.add_argument("--no-bench",    dest="no_bench",    action="store_true",
                   help="Skip ONNX export + inference benchmark")
    p.add_argument("--prepare-data", dest="prepare_data", action="store_true",
                   help="Run data download + preprocess + partition before training")
    # Paths
    p.add_argument("--data_dir",
                   default=str(DATA_DIR / "processed" / "healthcare"))
    p.add_argument("--part_dir",
                   default=str(DATA_DIR / "processed" / "partitions" / "healthcare"))
    p.add_argument("--results_dir",
                   default=str(RESULTS_BASE / "phase5"))
    return p.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    os.makedirs(args.results_dir, exist_ok=True)
    t_total = time.time()

    # Compute total step count for display
    n_steps = 0
    if args.prepare_data:
        n_steps += 1
    if args.mode in ("all", "baselines"):
        n_steps += 1
    if args.mode in ("all", "hfl"):
        n_steps += 1
        if not args.no_bench:
            n_steps += 1
    if args.mode in ("all", "baselines", "hfl", "sim") and not args.no_sim:
        n_steps += 1  # NS-3
        if not args.no_cloudsim:
            n_steps += 1  # CloudSim
    if args.mode in ("all", "baselines", "hfl", "sim", "collect"):
        n_steps += 1  # collect

    step = 0
    ok_train = True

    banner("HFL UNIFIED PIPELINE  —  Phase 5  (Healthcare IoT)")
    log(f"Mode: {args.mode}  |  Rounds: {args.rounds}  |  tau_e: {args.tau_e}  |  "
        f"Batch: {args.batch_size}  |  ε: {args.epsilon}  |  LR: {args.lr}")
    log(f"Topology: {args.n_devices} devices → {args.n_edges} edges → 1 cloud  |  "
        f"{args.n_classes} classes")
    log(f"Results → {args.results_dir}")
    print()

    # ── Step 0: Data ──────────────────────────────────────────────────────────
    if args.prepare_data:
        step += 1
        run_prepare_data(args)
    elif args.mode not in ("sim", "collect"):
        # For training modes, abort if data is missing
        if not check_data(args):
            sys.exit(1)

    # ── Step 1: Baselines ─────────────────────────────────────────────────────
    if args.mode in ("all", "baselines"):
        step += 1
        ok = run_baselines(args, step, n_steps)
        ok_train = ok_train and ok

    # ── Step 2: HFL-MM-HC training ────────────────────────────────────────────
    if args.mode in ("all", "hfl"):
        step += 1
        ok = run_hfl(args, step, n_steps)
        ok_train = ok_train and ok

    # ── Step 3: ONNX export + benchmark ───────────────────────────────────────
    if args.mode in ("all", "hfl") and not args.no_bench:
        step += 1
        run_onnx_bench(args, step, n_steps)

    # ── Step 4: NS-3 simulation ───────────────────────────────────────────────
    if args.mode in ("all", "baselines", "hfl", "sim") and not args.no_sim:
        step += 1
        run_ns3(args, step, n_steps)

    # ── Step 5: CloudSim simulation ───────────────────────────────────────────
    if args.mode in ("all", "baselines", "hfl", "sim") and not args.no_sim \
            and not args.no_cloudsim:
        step += 1
        run_cloudsim(args, step, n_steps)

    # ── Step 6: Results collection + QoS dashboard ───────────────────────────
    if args.mode in ("all", "baselines", "hfl", "sim", "collect"):
        step += 1
        run_collect(args, step, n_steps)
        print_qos_dashboard(args.results_dir)

    # ── Summary ───────────────────────────────────────────────────────────────
    log(f"Total pipeline time: {elapsed(t_total)}", "OK" if ok_train else "WARN")
    if not ok_train:
        log("One or more training steps failed — check output above.", "WARN")
        sys.exit(1)


if __name__ == "__main__":
    main()
