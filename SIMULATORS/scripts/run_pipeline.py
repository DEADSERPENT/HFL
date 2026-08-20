"""
run_pipeline.py — one command runs the whole study for one dataset.

    python scripts/run_pipeline.py --dataset vitaldb

Nothing about a stage is hardcoded here: paths, class counts, channel counts,
device counts and checkpoint names all resolve from the dataset registry
(data/loaders/datasets.py) or from this file's CLI. Adding a dataset to the
registry is enough to make the whole pipeline runnable on it.

Why a driver at all
-------------------
The stages have real ordering constraints that are easy to get wrong by hand,
and getting them wrong does not raise — it produces a plausible number:

  * the epsilon sweep's 'head' recipe and baseline B6 both need pretrained
    encoders; run them first and they silently freeze RANDOM encoders;
  * the NS-3 and CloudSim stages consume the proposed run's results CSV, so
    running them against a stale CSV reports last week's uplink figure;
  * ONNX export needs the checkpoint the proposed run writes.

Every stage therefore declares what it `needs`, and the driver refuses to run a
stage whose inputs are missing rather than producing a number from stale ones.

Resumability
------------
A stage whose outputs already exist is SKIPPED. Re-running after a crash costs
nothing already paid for. `--force` re-runs everything, `--force-stage NAME`
re-runs one. Every stage writes results/pipeline/<dataset>/logs/<stage>.log and
the driver maintains manifest.json with per-stage status, duration and the exact
argv used, so any published number can be traced back to the command that made
it.
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

_SIM = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import get_spec, REGISTRY                       # noqa: E402


class Stage:
    """One pipeline step: how to run it, what it needs, what it produces."""

    def __init__(self, name, argv, produces=(), needs=(), optional=False, desc=""):
        self.name = name
        self.argv = argv
        self.produces = [Path(p) for p in produces]
        self.needs = [Path(p) for p in needs]
        self.optional = optional
        self.desc = desc

    def satisfied(self):
        return bool(self.produces) and all(p.exists() for p in self.produces)

    def missing_inputs(self):
        return [p for p in self.needs if not p.exists()]


def build_stages(a, spec) -> list:
    """Declarative stage table. `a` is the parsed CLI namespace."""
    # -u (unbuffered) matters here. A child's stdout is a PIPE, not a tty, so
    # Python block-buffers it and a long stage — pretraining runs for tens of
    # minutes — produces an empty log until it exits. That is
    # indistinguishable from a hang, and the natural response to an apparent
    # hang is to kill a run that was working.
    py = [sys.executable, "-u"]
    ds = a.dataset
    res = _SIM / "results" / "phase5"
    ckpt_dir = _SIM / "checkpoints"
    enc = ckpt_dir / f"pretrained_encoders_{ds}.pt"
    model_ckpt = ckpt_dir / f"best_{ds}.pt"
    prop_csv = res / f"proposed_{ds}.csv"
    base_dir = res / "baselines" / ds
    sweep_dir = res / "epsilon_sweep" / ds
    onnx_fp32 = _SIM / "deploy" / f"hfl_mm_{ds}_fp32.onnx"
    ns3_out = res / f"ns3_{ds}.csv"

    # Model size in MB and edge count must match what is actually trained.
    import json as _json
    try:
        _n_edges = _json.loads(
            (_SIM / spec.partition_dir / "partition_meta.json").read_text()
        ).get("n_edges", 2)
    except Exception:
        _n_edges = 2
    try:
        _cfg = _json.loads((_SIM / "config" / "hfl_config.json").read_text())
        spec_params_mb = _cfg["datasets"][ds]["model_size_MB"]
    except Exception:
        spec_params_mb = 0.0
    lat_out = res / f"latency_{ds}.json"

    S = []

    S.append(Stage(
        "verify_data",
        [*py, str(_SIM / "tests" / "verify_datasets.py"), "--dataset", ds],
        produces=[], desc="adversarial dataset audit (leakage, NaNs, splits)"))

    S.append(Stage(
        "pretrain_encoders",
        [*py, str(_SIM / "model" / "training" / "pretrain_encoders.py"),
         "--dataset", ds, "--epochs", str(a.pretrain_epochs),
         "--batch_size", str(a.batch_size), "--seed", str(a.seed),
         "--deterministic", "--output", str(enc)],
        produces=[enc],
        desc="non-private encoder pretraining (PROXY mode unless --public_data)"))

    S.append(Stage(
        "baselines",
        [*py, str(_SIM / "model" / "training" / "baselines.py"),
         "--dataset", ds, "--rounds", str(a.rounds),
         "--local_epochs", str(a.local_epochs), "--batch_size", str(a.batch_size),
         "--epsilon", str(a.epsilon), "--seed", str(a.seed),
         "--b0_epochs", str(a.b0_epochs), "--b1_epochs", str(a.b1_epochs),
         "--max_physical_batch_size", str(a.max_physical_batch_size),
         "--pretrained_encoders", str(enc)],
        produces=[base_dir / "baselines_summary.csv"],
        needs=[enc],                      # B6 freezes these; random ones measure nothing
        desc="B0-B6 including the B4-vs-B6 privacy-recipe contrast"))

    S.append(Stage(
        "proposed",
        # hfl_trainer has no --local_epochs: local work per round is fixed at one
        # epoch and the edge cadence is --tau_e. Passing the wrong flag made the
        # stage die in 1 s with an argparse error, AFTER 68 minutes of upstream
        # work had already succeeded.
        [*py, str(_SIM / "model" / "training" / "hfl_trainer.py"),
         "--dataset", ds, "--rounds", str(a.rounds),
         "--tau_e", str(a.tau_e), "--batch_size", str(a.batch_size),
         "--epsilon", str(a.epsilon), "--seed", str(a.seed),
         "--freeze_encoders", "--pretrained_encoders", str(enc),
         "--save_checkpoint", str(model_ckpt), "--output", str(prop_csv)],
        produces=[prop_csv, model_ckpt], needs=[enc],
        desc="proposed hierarchical HFL-MM, head-only DP"))

    S.append(Stage(
        "ablation",
        [*py, str(_SIM / "scripts" / "modality_ablation.py"),
         "--dataset", ds, "--epochs", str(a.ablation_epochs),
         "--seeds", *[str(s) for s in a.ablation_seeds],
         "--out", str(res / f"ablation_{ds}.json")],
        produces=[res / f"ablation_{ds}.json"],
        desc="does fusion beat either modality alone (Gap #1)"))

    S.append(Stage(
        "epsilon_sweep",
        [*py, str(_SIM / "model" / "training" / "epsilon_sweep.py"),
         "--dataset", ds, "--rounds", str(a.rounds),
         "--local_epochs", str(a.local_epochs), "--batch_size", str(a.batch_size),
         "--epsilons", *a.epsilons, "--seeds", *[str(s) for s in a.sweep_seeds],
         "--max_physical_batch_size", str(a.max_physical_batch_size),
         "--pretrained_encoders", str(enc), "--resume"],
        produces=[sweep_dir / "epsilon_sweep.csv"], needs=[enc],
        desc="privacy-utility curve, full-model vs head-only DP"))

    S.append(Stage(
        "onnx_export",
        [*py, str(_SIM / "model" / "deploy" / "onnx_exporter.py"),
         "--dataset", ds, "--checkpoint", str(model_ckpt),
         "--output_fp32", str(onnx_fp32)],
        produces=[onnx_fp32], needs=[model_ckpt],
        desc="standardise the trained model for portable inference"))

    S.append(Stage(
        "inference_bench",
        [*py, str(_SIM / "model" / "deploy" / "inference_bench.py"),
         "--model", str(onnx_fp32), "--n_runs", str(a.bench_runs),
         "--provider", a.provider, "--output", str(lat_out)],
        produces=[lat_out], needs=[onnx_fp32],
        desc="end-to-end inference latency vs the <100 ms objective"))

    S.append(Stage(
        "ns3_network",
        [*py, str(_SIM / "scripts" / "ns3_phase5_integration.py"),
         "--dataset", ds, "--hfl_results", str(prop_csv),
         "--n_rounds", str(a.rounds), "--output", str(ns3_out)],
        produces=[ns3_out], needs=[prop_csv],
        desc="NS-3: uplink volume, per-update reliability, network latency"))

    # HFLCloudSimulation parses FLAGS (--dataset/--devices/--edges/--rounds/
    # --model_mb), not positional args. Passing "<ds> <rounds>" left every
    # value at its compiled-in default (20 devices / 3 edges / 50 MB), so the
    # energy figure described a topology that was never trained.
    _mb = round(spec_params_mb, 2)
    S.append(Stage(
        "cloudsim_energy",
        ["mvn", "-q", "-f", str(_SIM / "cloudsim-plus" / "hfl-simulation" / "pom.xml"),
         "compile", "exec:java", "-Dexec.mainClass=hfl.HFLCloudSimulation",
         f"-Dexec.args=--dataset {ds} --devices {spec.n_devices} "
         f"--edges {_n_edges} --rounds {a.rounds} --model_mb {_mb}"],
        produces=[_SIM / "results" / "cloudsim" / f"cloudsim_results_{ds}.csv"],
        optional=True,
        desc="CloudSim Plus: edge-cloud scheduling and energy per round"))

    S.append(Stage(
        "collect",
        [*py, str(_SIM / "scripts" / "collect_phase5_results.py"),
         "--results_dir", str(res), "--baselines_dir", str(base_dir),
         "--hfl_results", str(prop_csv), "--latency", str(lat_out),
         "--ns3_dir", str(res), "--output", str(res / f"RESULTS_{ds}.md")],
        produces=[res / f"RESULTS_{ds}.md"], needs=[prop_csv], optional=True,
        desc="assemble every artifact into one report"))

    # ── Phase 6 ──────────────────────────────────────────────────
    p6 = _SIM / "results" / "phase6" / ds
    S.append(Stage(
        "joint_eval",
        [*py, str(_SIM / "scripts" / "joint_eval.py"),
         "--dataset", ds, "--rounds", str(a.rounds),
         "--local_epochs", str(a.local_epochs), "--batch_size", str(a.batch_size),
         "--epsilon", str(a.epsilon), "--seed", str(a.seed),
         "--pretrained_encoders", str(enc)],
        produces=[p6 / "joint_eval.csv"], needs=[enc, prop_csv],
        desc="S0-S4 five-system table; trains the S3 HED-FL arm"))

    S.append(Stage(
        "component_ablation",
        [*py, str(_SIM / "scripts" / "component_ablation.py"),
         "--dataset", ds, "--rounds", str(a.rounds),
         "--local_epochs", str(a.local_epochs), "--batch_size", str(a.batch_size),
         "--epsilon", str(a.epsilon), "--seed", str(a.seed),
         "--pretrained_encoders", str(enc)],
        produces=[p6 / "ablation.csv"], needs=[enc],
        desc="A0-A5: remove one component at a time"))

    S.append(Stage(
        "statistics",
        [*py, str(_SIM / "scripts" / "run_statistics.py"), "--dataset", ds],
        produces=[p6 / "statistics.txt"],
        desc="paired tests, 95% CIs, seed-count warnings"))

    S.append(Stage(
        "figures",
        [*py, str(_SIM / "scripts" / "make_figures.py"), "--dataset", ds],
        produces=[p6 / "figures"],
        desc="Fig 2-10 from measured artifacts only"))

    # Closes the loop back to the founding document: every objective in
    # Problem Statement 1 scored against its stated threshold, with the
    # artifact each number came from.
    S.append(Stage(
        "objectives",
        [*py, str(_SIM / "scripts" / "check_objectives.py"),
         "--dataset", ds, "--results_dir", str(res),
         "--output", str(res / f"objectives_{ds}.json")],
        produces=[res / f"objectives_{ds}.json"],
        desc="score O1-O4 against the problem statement's thresholds"))

    return S


def run_stage(st, log_dir, dry=False, env=None):
    log_path = log_dir / f"{st.name}.log"
    print(f"\n{'='*74}\n  ▶ {st.name}  —  {st.desc}\n{'='*74}")
    print("  $ " + " ".join(str(x) for x in st.argv))
    if dry:
        return {"status": "dry-run", "seconds": 0.0}

    t0 = time.time()
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as lf:
        lf.write(f"# {datetime.now().isoformat(timespec='seconds')}\n")
        lf.write("# " + " ".join(str(x) for x in st.argv) + "\n\n")
        lf.flush()
        proc = subprocess.Popen(st.argv, cwd=str(_SIM), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                bufsize=1, env=env)
        for line in proc.stdout:
            sys.stdout.write(line)
            lf.write(line)
            # Flush per line. Without this the per-stage log is block-buffered
            # and appears FROZEN — during the epsilon sweep it showed nothing for
            # 28 minutes while the stage was progressing normally, which is
            # indistinguishable from a hang.
            lf.flush()
        proc.wait()
    dt = round(time.time() - t0, 1)
    ok = proc.returncode == 0
    print(f"  {'✓' if ok else '✗'} {st.name} finished in {dt}s "
          f"(exit {proc.returncode}) → {log_path}")
    return {"status": "ok" if ok else "failed", "returncode": proc.returncode,
            "seconds": dt, "log": str(log_path)}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    p.add_argument("--stages", nargs="*", default=None,
                   help="run only these stages (default: all, in order)")
    p.add_argument("--skip", nargs="*", default=[])
    p.add_argument("--force", action="store_true", help="re-run even if outputs exist")
    p.add_argument("--force-stage", nargs="*", default=[], dest="force_stage")
    p.add_argument("--dry-run", action="store_true", help="print the plan, run nothing")
    p.add_argument("--continue-on-error", action="store_true",
                   help="keep going after a failed stage (default: stop)")
    p.add_argument("--list", action="store_true", help="show stages and exit")

    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--rounds", type=int, default=10)
    p.add_argument("--local_epochs", type=int, default=1,
                   help="local epochs for the BASELINE arms")
    p.add_argument("--tau_e", type=int, default=5,
                   help="edge aggregation cadence for the proposed run")
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--epsilon", type=float, default=1.0)
    p.add_argument("--pretrain_epochs", type=int, default=30)
    p.add_argument("--b0_epochs", type=int, default=5)
    p.add_argument("--b1_epochs", type=int, default=10)
    p.add_argument("--max_physical_batch_size", type=int, default=0,
                   help="0 = no micro-batching (fastest). Set only if a DP arm OOMs; "
                        "measured cost of splitting 64 into 8 was 5.5x slower.")
    p.add_argument("--ablation_epochs", type=int, default=8)
    p.add_argument("--ablation_seeds", type=int, nargs="+", default=[42, 43])
    p.add_argument("--sweep_seeds", type=int, nargs="+", default=[42])
    p.add_argument("--epsilons", nargs="+",
                   default=["0.5", "1.0", "2.0", "4.0", "8.0", "inf"])
    p.add_argument("--bench_runs", type=int, default=200)
    p.add_argument("--provider", default="cpu", choices=["cpu", "cuda"],
                   help="ONNX Runtime provider for the latency figure. The IoT "
                        "deployment claim is a CPU claim; 'cuda' measures the "
                        "edge server instead, so state which one you report.")
    a = p.parse_args()

    spec = get_spec(a.dataset)
    stages = build_stages(a, spec)
    order = [s.name for s in stages]

    if a.list:
        print(f"Pipeline stages for --dataset {a.dataset}:\n")
        for i, s in enumerate(stages, 1):
            print(f"  {i:2d}. {s.name:<18} {s.desc}"
                  + ("   [optional]" if s.optional else ""))
        return 0

    selected = a.stages or order
    unknown = [s for s in list(selected) + list(a.skip) if s not in order]
    if unknown:
        raise SystemExit(f"[pipeline] unknown stage(s): {unknown}\n"
                         f"available: {order}")

    run_dir = _SIM / "results" / "pipeline" / a.dataset
    log_dir = run_dir / "logs"
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists() and not a.force:
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            manifest = {}
    manifest.setdefault("dataset", a.dataset)
    manifest.setdefault("stages", {})
    manifest["config"] = vars(a)
    manifest["started"] = datetime.now().isoformat(timespec="seconds")

    print("=" * 74)
    print(f"HFL-MM PIPELINE — {a.dataset.upper()}")
    print("=" * 74)
    print(spec)
    print(f"  run dir : {run_dir}")
    print(f"  stages  : {', '.join(selected)}")

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [
        str(_SIM), str(_SIM / "data" / "loaders"), env.get("PYTHONPATH", "")]))

    failed = []
    planned = set()          # outputs earlier selected stages will create
    for st in stages:
        if st.name not in selected or st.name in a.skip:
            continue

        if st.name == "cloudsim_energy" and not shutil.which("mvn"):
            print(f"\n  ⊘ {st.name}: maven not on PATH — skipped (optional).")
            manifest["stages"][st.name] = {"status": "skipped-no-tool"}
            continue

        missing = st.missing_inputs()
        if missing and a.dry_run:
            # In a plan, an input produced by an earlier selected stage counts
            # as satisfied — otherwise --dry-run always stops at the first
            # stage whose dependency has not been built yet, which is exactly
            # the situation you use --dry-run to inspect.
            missing = [m for m in missing if m not in planned]
        if missing:
            msg = (f"  ✗ {st.name}: required input(s) missing: "
                   f"{[str(m) for m in missing]}")
            print("\n" + msg)
            print("     Refusing to run — this stage would otherwise produce a "
                  "number from absent or stale inputs.")
            manifest["stages"][st.name] = {"status": "blocked",
                                           "missing": [str(m) for m in missing]}
            failed.append(st.name)
            if not a.continue_on_error:
                break
            continue

        rerun = a.force or st.name in a.force_stage
        if st.satisfied() and not rerun:
            print(f"\n  ⊙ {st.name}: outputs already exist — skipped "
                  f"(--force-stage {st.name} to redo)")
            manifest["stages"].setdefault(st.name, {})["status"] = "cached"
            continue

        planned.update(st.produces)
        info = run_stage(st, log_dir, dry=a.dry_run, env=env)
        info["argv"] = [str(x) for x in st.argv]
        info["finished"] = datetime.now().isoformat(timespec="seconds")
        manifest["stages"][st.name] = info
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str))

        if info["status"] == "failed":
            failed.append(st.name)
            if st.optional:
                print(f"  (…{st.name} is optional — continuing)")
                failed.pop()
            elif not a.continue_on_error:
                print(f"\n[pipeline] stopping at failed stage '{st.name}'. "
                      f"Fix it and re-run — completed stages are cached.")
                break

    manifest["finished"] = datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str))

    print("\n" + "=" * 74)
    print(f"PIPELINE SUMMARY — {a.dataset}")
    print("=" * 74)
    for name in order:
        st_info = manifest["stages"].get(name)
        if not st_info:
            print(f"  {name:<18} —")
            continue
        s = st_info.get("status", "?")
        mark = {"ok": "✓", "cached": "⊙", "failed": "✗", "blocked": "✗",
                "dry-run": "·", "skipped-no-tool": "⊘"}.get(s, "?")
        secs = st_info.get("seconds")
        print(f"  {mark} {name:<18} {s:<16}"
              + (f"{secs:>8.1f}s" if isinstance(secs, (int, float)) else ""))
    print("=" * 74)
    print(f"manifest: {manifest_path}")
    if failed:
        print(f"\nFAILED: {failed}")
        return 1
    print("\nAll requested stages completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
