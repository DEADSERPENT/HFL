#!/usr/bin/env python3
"""
HFL Unified Pipeline Runner
============================
Single entry point for the full Phase 5 experiment.

Automatically chains:
  1. Model training  (baselines B0-B5  and/or  HFL-MM-HC P1)
  2. NS-3 network simulation   (ns3_phase5_integration.py)
  3. CloudSim resource/energy simulation  (Maven hfl.HFLCloudSimulation)
  4. Results collection  (collect_phase5_results.py)
  5. QoS dashboard  (printed to stdout)

Usage
-----
  # Full pipeline — train everything + simulate + collect
  python run_pipeline.py

  # Only run baselines, then simulate
  python run_pipeline.py --mode baselines

  # Only run HFL-MM-HC, then simulate  (most common during dev)
  python run_pipeline.py --mode hfl

  # Skip training — just re-run simulations on existing results
  python run_pipeline.py --mode sim

  # Skip training AND simulation — just re-collect/print results
  python run_pipeline.py --mode collect

  # Skip NS-3 + CloudSim (for quick model-only runs)
  python run_pipeline.py --no-sim

Options
-------
  --mode          all | baselines | hfl | sim | collect  (default: all)
  --rounds N      FL rounds for HFL-MM-HC  (default: 20)
  --batch_size N  mini-batch size           (default: 64)
  --epsilon F     DP privacy budget         (default: 1.0)
  --lr F          learning rate             (default: 1e-3)
  --no-sim        skip NS-3 + CloudSim steps
  --no-cloudsim   skip CloudSim only (NS-3 still runs)
  --skip B        comma-separated baseline names to skip (e.g. B0,B4)
  --data_dir      path to processed data    (default: data/processed/healthcare)
  --part_dir      path to partition indices (default: data/processed/partitions/healthcare)
  --results_dir   output directory          (default: results/phase5)
"""

import os
import sys
import time
import subprocess
import argparse
import csv
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR    = os.path.join(SCRIPT_DIR, "model")
SCRIPTS_DIR  = os.path.join(SCRIPT_DIR, "scripts")
RESULTS_DIR  = os.path.join(SCRIPT_DIR, "results", "phase5")
NS3_DIR      = os.path.join(SCRIPT_DIR, "results", "ns3")
CLOUDSIM_DIR = os.path.join(SCRIPT_DIR, "cloudsim-plus", "hfl-simulation")
PYTHON       = sys.executable   # same venv that launched this script

# ── Helpers ───────────────────────────────────────────────────────────────────

class _Col:
    GRN  = "\033[92m"
    YEL  = "\033[93m"
    RED  = "\033[91m"
    CYN  = "\033[96m"
    BLD  = "\033[1m"
    RST  = "\033[0m"

def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "·", "OK": "✓", "WARN": "!", "ERR": "✗", "HEAD": "═"}
    icon  = icons.get(level, "·")
    color = {
        "OK":   _Col.GRN,
        "WARN": _Col.YEL,
        "ERR":  _Col.RED,
        "HEAD": _Col.CYN + _Col.BLD,
    }.get(level, "")
    print(f"[{ts}] {color}{icon} {msg}{_Col.RST}", flush=True)


def banner(title: str) -> None:
    line = "═" * (len(title) + 4)
    print(f"\n{_Col.CYN}{_Col.BLD}{line}", flush=True)
    print(f"  {title}", flush=True)
    print(f"{line}{_Col.RST}\n", flush=True)


def run_subprocess(cmd: list[str], cwd: str | None = None,
                   label: str = "") -> tuple[int, str]:
    """Run cmd, stream stdout/stderr live, return (returncode, last_line)."""
    log(f"Running: {' '.join(cmd)}" + (f"  [cwd={cwd}]" if cwd else ""))
    last_line = ""
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
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


def elapsed(t0: float) -> str:
    s = int(time.time() - t0)
    return f"{s//60}m {s%60}s"

# ── Step implementations ──────────────────────────────────────────────────────

def run_baselines(args) -> bool:
    """Run baselines B0-B5 via baselines.py __main__."""
    banner("STEP 1/4 — Baseline Training  (B0 Centralized → B5 MOON)")
    t0 = time.time()

    cmd = [
        PYTHON, "-u",
        os.path.join(MODEL_DIR, "baselines.py"),
        "--data_dir",      args.data_dir,
        "--partition_dir", args.part_dir,
        "--output_dir",    args.results_dir,
        "--rounds",        str(args.rounds),
        "--local_epochs",  "2",
        "--batch_size",    str(args.batch_size),
        "--lr",            str(args.lr),
        "--epsilon",       str(args.epsilon),
    ]
    if args.skip:
        cmd += ["--skip", args.skip]

    rc, _ = run_subprocess(cmd, cwd=SCRIPT_DIR, label="baselines.py")
    if rc == 0:
        log(f"Baselines complete in {elapsed(t0)}", "OK")
    else:
        log(f"Baselines exited with code {rc}", "ERR")
    return rc == 0


def run_hfl(args) -> bool:
    """Run HFL-MM-HC (P1) via hfl_trainer.py __main__."""
    banner("STEP 1/4 — HFL-MM-HC Training  (P1 — two-tier FedAvg + DP-SGD)")
    t0 = time.time()

    hfl_csv = os.path.join(args.results_dir, "hfl_mm_hc_results.csv")
    cmd = [
        PYTHON, "-u",
        os.path.join(MODEL_DIR, "hfl_trainer.py"),
        "--data_dir",      args.data_dir,
        "--partition_dir", args.part_dir,
        "--rounds",        str(args.rounds),
        "--tau_e",         "5",
        "--batch_size",    str(args.batch_size),
        "--epsilon",       str(args.epsilon),
        "--lr",            str(args.lr),
        "--output",        hfl_csv,
    ]
    rc, _ = run_subprocess(cmd, cwd=SCRIPT_DIR, label="hfl_trainer.py")
    if rc == 0:
        log(f"HFL-MM-HC training complete in {elapsed(t0)}", "OK")
    else:
        log(f"hfl_trainer.py exited with code {rc}", "ERR")
    return rc == 0


def run_ns3(args) -> bool:
    """
    NS-3 Phase 5 integration.
    Reads hfl_mm_hc_results.csv (uplink_bytes per round) and re-derives
    all network QoS metrics analytically (Phase 5 equivalent of NS-3 run).
    """
    banner("STEP 2/4 — NS-3 Network Simulation  (Phase 5 payload update)")
    t0 = time.time()

    hfl_csv = os.path.join(args.results_dir, "hfl_mm_hc_results.csv")
    out_csv = os.path.join(NS3_DIR, "ns3_phase5_results.csv")
    os.makedirs(NS3_DIR, exist_ok=True)

    cmd = [
        PYTHON, "-u",
        os.path.join(SCRIPTS_DIR, "ns3_phase5_integration.py"),
        "--hfl_results", hfl_csv,
        "--n_rounds",    str(args.rounds),
        "--output",      out_csv,
    ]
    rc, _ = run_subprocess(cmd, cwd=SCRIPT_DIR, label="ns3_phase5_integration.py")
    if rc == 0:
        log(f"NS-3 integration complete in {elapsed(t0)}", "OK")
    else:
        log(f"ns3_phase5_integration.py exited with code {rc}", "ERR")
    return rc == 0


def run_cloudsim(args) -> bool:
    """
    Trigger CloudSim Plus energy/resource simulation (Maven project).
    Passes Phase 5 round count and baseline comparisons via system properties.
    """
    banner("STEP 3/4 — CloudSim Plus Energy/Resource Simulation")
    t0 = time.time()

    pom = os.path.join(CLOUDSIM_DIR, "pom.xml")
    if not os.path.exists(pom):
        log(f"CloudSim pom.xml not found at {pom} — skipping.", "WARN")
        return True   # not a fatal error — Phase 4 results still valid

    # Pass Phase 5 config as Maven system properties
    # These are read by HFLCloudSimulation.java if present
    cmd = [
        "mvn", "-q",
        "exec:java",
        "-Dexec.mainClass=hfl.HFLCloudSimulation",
        f"-Dhfl.rounds={args.rounds}",
        f"-Dhfl.devices=6",
        f"-Dhfl.edges=2",
        f"-Dhfl.outputDir={os.path.join(SCRIPT_DIR, 'results', 'cloudsim')}",
    ]
    rc, _ = run_subprocess(cmd, cwd=CLOUDSIM_DIR, label="CloudSim")
    if rc == 0:
        log(f"CloudSim simulation complete in {elapsed(t0)}", "OK")
    else:
        log(f"CloudSim exited with code {rc} — check Maven/Java setup.", "WARN")
        log("Phase 4 CloudSim results (results/cloudsim/cloudsim_results.csv) remain valid.", "INFO")
    return True   # CloudSim failure is non-fatal; Phase 4 data is still usable


def run_collect(args) -> bool:
    """Aggregate all results and print QoS dashboard."""
    banner("STEP 4/4 — Results Collection & QoS Dashboard")
    t0 = time.time()

    cmd = [
        PYTHON, "-u",
        os.path.join(SCRIPTS_DIR, "collect_phase5_results.py"),
        "--results_dir", args.results_dir,
        "--output",      os.path.join(args.results_dir, "phase5_results.csv"),
    ]
    rc, _ = run_subprocess(cmd, cwd=SCRIPT_DIR, label="collect_phase5_results.py")
    if rc == 0:
        log(f"Results collected in {elapsed(t0)}", "OK")
    else:
        log(f"collect_phase5_results.py exited with code {rc}", "ERR")
    return rc == 0


def print_qos_dashboard(results_dir: str) -> None:
    """Read phase5_results.csv and print a colored QoS pass/fail dashboard."""
    banner("QoS TARGET DASHBOARD  (Phase 5 Final Validation)")

    csv_path = os.path.join(results_dir, "phase5_results.csv")
    if not os.path.exists(csv_path):
        log("phase5_results.csv not found — run collect step first.", "WARN")
        return

    # Parse sections from the custom CSV format
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
            if raw.startswith("#"):   # plain comment — skip after section-check
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

    # Accuracy table
    if systems:
        print(f"  {'System':<24} {'AUC':>8}  {'Acc':>7}  {'ε':>6}")
        print(f"  {'-'*24} {'-'*8}  {'-'*7}  {'-'*6}")
        for s in systems:
            name = s.get("system", "?")
            auc  = s.get("macro_auc", "N/A")
            acc  = s.get("accuracy", "N/A")
            eps  = s.get("epsilon", "N/A")
            try:   auc_f = f"{float(auc):.4f}"
            except: auc_f = auc
            try:   acc_f = f"{float(acc):.4f}"
            except: acc_f = acc
            color = _Col.GRN if "P1" in name or "HFL" in name else ""
            print(f"  {color}{name:<24} {auc_f:>8}  {acc_f:>7}  {eps:>6}{_Col.RST}")
        print()

    # QoS table
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
            print(f"  {icon}  {target:<35}  {value}")

        print()
        if all_pass:
            print(f"  {_Col.GRN}{_Col.BLD}All Phase 5 QoS targets PASSED ✓{_Col.RST}")
        else:
            print(f"  {_Col.YEL}Some targets incomplete — re-run full pipeline.{_Col.RST}")
    else:
        log("No QoS rows found in phase5_results.csv", "WARN")

    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="HFL Unified Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--mode", default="all",
                   choices=["all", "baselines", "hfl", "sim", "collect"],
                   help="Which stages to run (default: all)")
    p.add_argument("--rounds",      type=int,   default=20)
    p.add_argument("--batch_size",  type=int,   default=64)
    p.add_argument("--epsilon",     type=float, default=1.0)
    p.add_argument("--lr",          type=float, default=1e-3)
    p.add_argument("--skip",        default="",
                   help="Baseline names to skip, comma-separated (e.g. B0,B4)")
    p.add_argument("--no-sim",      action="store_true",
                   help="Skip NS-3 and CloudSim steps")
    p.add_argument("--no-cloudsim", action="store_true",
                   help="Skip CloudSim only")
    p.add_argument("--data_dir",
                   default=os.path.join(SCRIPT_DIR, "data", "processed", "healthcare"))
    p.add_argument("--part_dir",
                   default=os.path.join(SCRIPT_DIR, "data", "processed",
                                        "partitions", "healthcare"))
    p.add_argument("--results_dir", default=RESULTS_DIR)
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.results_dir, exist_ok=True)
    t_total = time.time()

    banner("HFL UNIFIED PIPELINE  —  Phase 5  (Healthcare IoT)")
    log(f"Mode: {args.mode}  |  Rounds: {args.rounds}  |  "
        f"Batch: {args.batch_size}  |  ε: {args.epsilon}  |  LR: {args.lr}")
    log(f"Results → {args.results_dir}")
    print()

    ok_train = True   # set to False if training fails

    # ── Training ─────────────────────────────────────────────────────────────
    if args.mode in ("all", "baselines"):
        ok_train = run_baselines(args)

    if args.mode in ("all", "hfl"):
        ok_train = run_hfl(args) and ok_train

    # ── Simulation (always runs unless --no-sim or mode=collect) ─────────────
    if args.mode in ("all", "baselines", "hfl", "sim"):
        if args.no_sim:
            log("Skipping simulations (--no-sim)", "WARN")
        else:
            # NS-3 always runs (fast Python script, ~2 s)
            run_ns3(args)

            # CloudSim runs unless --no-cloudsim or Maven not available
            if not args.no_cloudsim:
                run_cloudsim(args)
            else:
                log("Skipping CloudSim (--no-cloudsim)", "WARN")

    # ── Collect + dashboard ───────────────────────────────────────────────────
    if args.mode in ("all", "baselines", "hfl", "sim", "collect"):
        run_collect(args)
        print_qos_dashboard(args.results_dir)

    # ── Summary ───────────────────────────────────────────────────────────────
    log(f"Total pipeline time: {elapsed(t_total)}", "OK")
    if not ok_train:
        log("One or more training steps failed — check output above.", "WARN")
        sys.exit(1)


if __name__ == "__main__":
    main()
