"""
traceability.py — every documented requirement, checked against the codebase.

The study is defined by four documents. Nothing may be left out of them:

  document/DOCUMENT PDF/Problem statement and objectives.pdf   → O1-O4
  document/DOCUMENT PDF/Research Problem Statements ...pdf     → O1-O4 thresholds
  document/PHASE REPORT/Phase 4.txt                            → D4.1-D4.5
  document/PHASE REPORT/Phase 5.txt                            → D5.1-D5.13
  document/PHASE REPORT/Phase 6.txt                            → D6.1-D6.7,
                                                                  S0-S4, A0-A5,
                                                                  Fig 1-10
  document/OVERALL PROJECT OUTPUT/*.txt                        → IP claims

Two kinds of requirement, and the difference matters:

  CODE     — an implementation exists and is dataset-agnostic. Checked by
             looking for the file AND for registry-awareness, because a file
             that only works on one retired dataset satisfies
             nothing. `probe` names the file; `needs_dataset_aware` demands
             it resolve shapes from the registry rather than hardcode them.

  ARTIFACT — a measured result exists FOR A GIVEN DATASET. Checked per
             dataset, because a result on one dataset says nothing about
             another. This is the whole point: artifacts must be traced to
             the dataset that produced them.

Run:
    python tests/traceability.py --dataset vitaldb
    python tests/traceability.py --dataset vitaldb --todo     # only gaps
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

_SIM = Path(__file__).resolve().parent.parent
_DOC = _SIM.parent / "document"

CODE, ARTIFACT = "code", "artifact"


def R(rid, phase, title, kind, probe, source, dataset_aware=False, note=""):
    """`dataset_aware` may be True (use the default CLI/registry hints) or a
    tuple of tokens. Architecture modules are parameterised rather than
    registry-driven — hfl_mm_model.py is dataset-agnostic precisely because it
    takes n_channels_a/feat_b_dim as arguments and never imports the registry,
    so demanding `get_spec` there would flag correct code as hardcoded."""
    return dict(id=rid, phase=phase, title=title, kind=kind, probe=probe,
                source=source, dataset_aware=dataset_aware, note=note)


def requirements(ds: str):
    res = f"results/phase5"
    base = f"{res}/baselines/{ds}"
    p6 = f"results/phase6/{ds}"
    return [
        # ── Phase 4 — simulators ─────────────────────────────────────
        R("D4.1", 4, "NS-3 network simulation", CODE,
          "scripts/ns3_phase5_integration.py", "Phase 4.txt:14", True),
        R("D4.2", 4, "CloudSim Plus compute simulation", CODE,
          "cloudsim-plus/hfl-simulation/src/main/java/hfl/HFLCloudSimulation.java",
          "Phase 4.txt:15"),
        R("D4.3", 4, "Simulation results (network + compute)", ARTIFACT,
          [f"{res}/ns3_{ds}.csv", f"{res}/cloudsim_{ds}.csv"], "Phase 4.txt:16"),
        R("D4.4", 4, "QoS target validation", ARTIFACT,
          f"{res}/objectives_{ds}.json", "Phase 4.txt:17"),
        R("D4.5", 4, "GPU/CPU auto-detection", CODE,
          "model/utils/device_utils.py", "Phase 4.txt:18"),

        # ── Phase 5 — model, privacy, deployment ─────────────────────
        R("D5.1", 5, "Dataset pipeline", CODE,
          "data/loaders/datasets.py", "Phase 5.txt:27", True),
        R("D5.2", 5, "FedMamba-HC encoder", CODE,
          "model/architecture/hfl_mm_model.py", "Phase 5.txt:28",
          ("n_channels_a",)),
        R("D5.3", 5, "FedConform-HC conformal prediction", CODE,
          "model/utils/fedconform_hc.py", "Phase 5.txt:29", ("n_classes",)),
        R("D5.4", 5, "ClinicalCMGA cross-modal attention", CODE,
          "model/architecture/clinical_cmga_design.py", "Phase 5.txt:30", False,
          "DESIGN ONLY — zero references from the training path"),
        R("D5.5", 5, "HFL-MM model", CODE,
          "model/architecture/hfl_mm_model.py", "Phase 5.txt:31",
          ("modality_b", "feat_b_dim")),
        R("D5.6", 5, "Baseline suite", CODE,
          "model/training/baselines.py", "Phase 5.txt:32", True),
        R("D5.7", 5, "HFL training engine", CODE,
          "model/training/hfl_trainer.py", "Phase 5.txt:33", True),
        R("D5.8", 5, "DP-SGD integration", CODE,
          "model/privacy/dp_engine.py", "Phase 5.txt:34"),
        R("D5.9", 5, "Gradient compression", CODE,
          "model/utils/compression.py", "Phase 5.txt:35"),
        R("D5.10", 5, "ONNX edge deployment", CODE,
          "model/deploy/onnx_exporter.py", "Phase 5.txt:36", True),
        R("D5.11", 5, "Inference latency validator", CODE,
          "model/deploy/inference_bench.py", "Phase 5.txt:37"),
        R("D5.12", 5, "Epsilon sweep", CODE,
          "model/training/epsilon_sweep.py", "Phase 5.txt:38", True),
        R("D5.13", 5, "Phase 5 results", ARTIFACT,
          f"{res}/proposed_{ds}.csv", "Phase 5.txt:39"),
        R("D5.6a", 5, "Baseline results B0-B6", ARTIFACT,
          f"{base}/baselines_summary.csv", "Phase 5.txt:32"),
        R("D5.12a", 5, "Epsilon sweep results", ARTIFACT,
          f"{res}/epsilon_sweep/{ds}/epsilon_sweep.csv", "Phase 5.txt:38"),
        R("D5.10a", 5, "Exported ONNX model", ARTIFACT,
          f"deploy/hfl_mm_{ds}_fp32.onnx", "Phase 5.txt:36"),
        R("D5.11a", 5, "Measured inference latency", ARTIFACT,
          f"{res}/latency_{ds}.json", "Phase 5.txt:37"),

        # ── Phase 6 — joint evaluation, ablation, figures ────────────
        R("D6.1", 6, "Joint evaluation S0-S4", ARTIFACT,
          f"{p6}/joint_eval.csv", "Phase 6.txt:14"),
        R("D6.2", 6, "Component ablation A0-A5", ARTIFACT,
          f"{p6}/ablation.csv", "Phase 6.txt:15"),
        R("D6.3", 6, "Publication figures 1-10", ARTIFACT,
          f"{p6}/figures", "Phase 6.txt:16"),
        R("D6.4", 6, "Statistical analysis (>=5 seeds, CIs, tests)", ARTIFACT,
          f"{p6}/statistics.txt", "Phase 6.txt:17"),
        R("D6.5", 6, "Thesis chapters (draft)", ARTIFACT,
          "../THESIS/chapters", "Phase 6.txt:18"),
        R("D6.6", 6, "Journal paper (draft)", ARTIFACT,
          "../PAPER", "Phase 6.txt:19"),
        R("D6.7", 6, "Reproducibility package", ARTIFACT,
          "README_reproduce.md", "Phase 6.txt:20"),

        # ── Phase 6 §6.2.1 — the five compared systems ───────────────
        R("S0", 6, "CentralizedFL  (= baseline B0)", ARTIFACT,
          f"{base}/baseline_b0.csv", "Phase 6.txt:52"),
        R("S1", 6, "FlatFL_NoDP  (= baseline B2 FedAvg)", ARTIFACT,
          f"{base}/baseline_b2.csv", "Phase 6.txt:53"),
        R("S2", 6, "FL2DP  (flat + DP; = baseline B4)", ARTIFACT,
          f"{base}/baseline_b4.csv", "Phase 6.txt:54"),
        R("B7", 6, "flat + full-model DP, PRETRAINED init", ARTIFACT,
          f"{base}/baseline_b7.csv", "confound control for B4->B6", False,
          "separates 'pretrained encoders' from 'head-only DP'"),
        R("S3", 6, "HED-FL  (hierarchical, NO DP)", ARTIFACT,
          f"{p6}/s3_hedfl_{ds}.csv", "Phase 6.txt:55", False,
          "no arm exists: hierarchy without DP is never run"),
        R("S4", 6, "HFL-MM proposed", ARTIFACT,
          f"{res}/proposed_{ds}.csv", "Phase 6.txt:56"),

        # ── Phase 6 §6.3.1 — component ablation ──────────────────────
        R("A1", 6, "C1 removed — flat tier", ARTIFACT,
          f"{p6}/ablation_A1.csv", "Phase 6.txt:117"),
        R("A2", 6, "C2 removed — no DP", ARTIFACT,
          f"{p6}/ablation_A2.csv", "Phase 6.txt:118"),
        R("A3", 6, "C3 removed — no sparsification", ARTIFACT,
          f"{p6}/ablation_A3.csv", "Phase 6.txt:119"),
        R("A4", 6, "C4 removed — float32, no quantization", ARTIFACT,
          f"{p6}/ablation_A4.csv", "Phase 6.txt:120"),
        R("A5", 6, "C5 removed — unimodal, no fusion", ARTIFACT,
          f"{res}/ablation_{ds}.json", "Phase 6.txt:121"),

        # ── Problem statement objectives ─────────────────────────────
        R("O1", 1, "Uplink reduction >= 50 %", ARTIFACT,
          f"{res}/objectives_{ds}.json", "Problem statement, Obj. 1"),
        R("O2", 1, "eps <= 1 with accuracy loss <= 2 %", ARTIFACT,
          f"{res}/objectives_{ds}.json", "Problem statement, Obj. 2"),
        R("O3", 1, "Inference < 100 ms, reliability > 99 %", ARTIFACT,
          f"{res}/objectives_{ds}.json", "Problem statement, Obj. 3"),
        R("O4", 1, "Energy saving >= 20 % per round", ARTIFACT,
          f"{res}/objectives_{ds}.json", "Problem statement, Obj. 4"),
    ]


DATASET_AWARE_HINTS = ("get_spec", "--dataset", "DatasetSpec", "REGISTRY")


def check(req, ds):
    """Return (status, detail). Statuses: OK, PARTIAL, MISSING."""
    probes = req["probe"] if isinstance(req["probe"], list) else [req["probe"]]
    paths = [(_SIM / p).resolve() for p in probes]
    present = [p for p in paths if p.exists()]

    if req["kind"] == CODE:
        if not present:
            return "MISSING", "file not found"
        da = req["dataset_aware"]
        if da:
            src = ""
            for p in present:
                if p.is_file() and p.suffix in (".py", ".java"):
                    src += p.read_text(errors="ignore")
            if da is True:
                # Default: ANY registry/CLI marker proves the file is driven by
                # the dataset rather than hardcoded to one. Requiring all of
                # them would fail datasets.py (the registry itself needs no
                # --dataset flag) and baselines.py (get_spec, never REGISTRY).
                ok, want = any(h in src for h in DATASET_AWARE_HINTS), \
                    f"one of {list(DATASET_AWARE_HINTS)}"
            else:
                # Explicit tokens name the specific parameters that make a
                # parameterised module shape-agnostic, so all must be present.
                miss = [h for h in da if h not in src]
                ok, want = not miss, f"missing {miss}"
            if not ok:
                return "PARTIAL", f"exists but NOT dataset-aware — {want}"
        return "OK", str(present[0].relative_to(_SIM))

    # ARTIFACT
    if not present:
        return "MISSING", f"no result for '{ds}' at {probes[0]}"
    if len(present) < len(paths):
        miss = [str(p.relative_to(_SIM)) for p in paths if not p.exists()]
        return "PARTIAL", f"missing {miss}"
    for p in present:
        if p.is_dir() and not any(p.iterdir()):
            return "PARTIAL", "directory exists but is empty"
    return "OK", str(present[0].relative_to(_SIM))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--todo", action="store_true", help="show only gaps")
    ap.add_argument("--phase", type=int, default=None, help="filter by phase")
    ap.add_argument("--json", default=None, help="write machine-readable status")
    a = ap.parse_args()

    reqs = requirements(a.dataset)
    if a.phase:
        reqs = [r for r in reqs if r["phase"] == a.phase]

    rows, counts = [], {"OK": 0, "PARTIAL": 0, "MISSING": 0}
    for r in reqs:
        st, detail = check(r, a.dataset)
        counts[st] += 1
        rows.append({**r, "status": st, "detail": detail})

    mark = {"OK": "✓", "PARTIAL": "◐", "MISSING": "✗"}
    print("=" * 96)
    print(f"REQUIREMENTS TRACEABILITY — dataset '{a.dataset}'")
    print("  every row is a requirement written in document/ ; artifacts are "
          "checked PER DATASET")
    print("=" * 96)

    last_phase = None
    for r in rows:
        if a.todo and r["status"] == "OK":
            continue
        if r["phase"] != last_phase:
            print(f"\n── Phase {r['phase']} " + "─" * 70)
            last_phase = r["phase"]
        print(f"  {mark[r['status']]} {r['id']:<7}{r['title']:<46}"
              f"{r['status']:<9}{r['detail']}")
        if r["note"]:
            print(f"      ↳ {r['note']}")

    total = sum(counts.values())
    print("\n" + "=" * 96)
    print(f"  {counts['OK']} OK   {counts['PARTIAL']} PARTIAL   "
          f"{counts['MISSING']} MISSING   (of {total})")
    done = counts["OK"] / total * 100 if total else 0
    print(f"  complete for '{a.dataset}': {done:.0f}%")
    print("=" * 96)

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(
            {"dataset": a.dataset, "summary": counts, "requirements": rows},
            indent=2))
        print(f"written: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
