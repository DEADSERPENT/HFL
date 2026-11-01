"""
joint_eval.py — Phase 6 deliverable D6.1 (Phase 6.txt §6.2).

Assembles the five-system comparison table:

  S0  CentralizedFL   pooled data, no federation, no DP     → baseline B0
  S1  FlatFL_NoDP     FedAvg, single tier, no DP            → baseline B2
  S2  FL2DP           FedAvg + DP (eps=1), flat tier        → baseline B4
  S3  HED-FL          hierarchical, NO DP                   → run here
  S4  HFL-MM          proposed: 2-tier + DP + fusion        → proposed run

S0/S1/S2/S4 already exist as artifacts, so this script READS them rather than
retraining — re-running an arm under slightly different code is how two numbers
for the same system end up in one thesis. Only S3 has no existing artifact
(nothing else runs hierarchy without DP), so it is trained here via
hfl_trainer --no_dp.

Why S3 has to exist
-------------------
S4 differs from S2 in two ways at once: it adds the edge tier AND it changes
the DP recipe. S3 holds the topology of S4 while removing privacy entirely, so:

    S2 -> S3   what the hierarchy buys   (both non-comparable on privacy)
    S3 -> S4   what privacy costs        (same topology, DP on vs off)

Without S3 the table can report that S4 beats S2 but cannot say why, and the
hierarchy contribution stays unproven.

A note on the accuracy-loss column: it is computed against S0, per §6.2.2
("Accuracy loss vs. S0, <=2% at eps=1"), NOT against the best arm. S0 is the
no-privacy no-federation ceiling, which is what Objective 2 is written against.
"""

import os
import re
import sys
import csv
import io
import json
import time
import argparse
import subprocess
from pathlib import Path

_SIM = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import get_spec, REGISTRY                       # noqa: E402

SYSTEMS = [
    ("S0", "CentralizedFL", "pooled data, no FL, no DP"),
    ("S1", "FlatFL_NoDP", "FedAvg, single tier, no DP"),
    ("S2", "FL2DP", "FedAvg + DP, flat tier"),
    ("S3", "HED-FL", "hierarchical, no DP"),
    ("S4", "HFL-MM (PROPOSED)", "2-tier + head-only DP + fusion"),
]


def latency_path(res, ds):
    """inference_bench.py writes CSV. Older runs saved it as latency_<ds>.json;
    read that legacy name when no .csv exists (the content is the same CSV)."""
    p = res / f"latency_{ds}.csv"
    return p if p.exists() or not (res / f"latency_{ds}.json").exists() \
        else res / f"latency_{ds}.json"


def rows_of(path):
    if not Path(path).exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def last_row(path):
    r = rows_of(path)
    return r[-1] if r else {}


def num(d, *keys):
    for k in keys:
        if k in d and str(d[k]).strip() not in ("", "nan", "None"):
            try:
                return float(d[k])
            except ValueError:
                pass
    return None


def trainer_test_metrics(csv_path):
    """Held-out TEST metrics for an arm trained by hfl_trainer.py.

    hfl_trainer writes per-round VAL metrics to its CSV and reports the pooled
    TEST metrics separately (now a <stem>_test.json artifact; older runs only
    printed them). The baselines write test_* columns directly, so mixing the
    two sources without this would tabulate S3/S4 on validation against S0-S2
    on test - a comparison that flatters the proposed system.
    """
    stem = os.path.splitext(str(csv_path))[0]
    tj = stem + "_test.json"
    if os.path.exists(tj):
        try:
            with open(tj) as f:
                d = json.load(f)
            return {k: float(d[k]) for k in ("accuracy", "macro_auc", "auprc")
                    if d.get(k) is not None}
        except (ValueError, OSError, TypeError):
            pass

    base = os.path.basename(stem)
    cands = [stem + ".log",
             os.path.join(os.path.dirname(stem), "logs", base + ".log")]
    # the driver's own log location: results/pipeline/<ds>/logs/<stage>.log
    stage, _, ds_ = base.partition("_")
    cands.append(os.path.join(str(_SIM), "results", "pipeline", ds_,
                              "logs", stage + ".log"))
    lp = next((c for c in cands if os.path.exists(c)), None)
    if lp is None:
        return {}
    # A log OLDER than the CSV belongs to a different, earlier run: the CSV was
    # regenerated afterwards (possibly with different hyperparameters) while the
    # driver's log was not. Scraping it would splice one run's test metrics onto
    # another run's epsilon/uplink. Refuse instead of silently mixing runs.
    try:
        if os.path.getmtime(lp) < os.path.getmtime(str(csv_path)) - 1:
            return {}
    except OSError:
        return {}
    line = None
    with open(lp, errors="ignore") as f:
        for ln in f:
            if ln.lstrip().startswith("Final Test"):
                line = ln.strip()
    if not line:
        return {}
    head = line.split("|", 1)[0]
    out = {}
    for key, field in (("AUROC", "macro_auc"), ("AUC", "macro_auc"),
                       ("AUPRC", "auprc"), ("Acc", "accuracy")):
        if field in out:
            continue
        m = re.search(rf"\b{key}=([0-9.]+)", head)
        if m:
            out[field] = float(m.group(1))
    return out


def a0_full_system_metrics(out_dir):
    """S4's test metrics from the A0 ablation arm.

    A0 is defined in component_ablation.py as `removes=None, flags=[]` - the
    full system, i.e. the proposed configuration - and it is run over several
    seeds, each writing a structured ablation_A0_seed<N>_final.json with a
    "test" block. Preferring it over the single `proposed` run gives a
    multi-seed mean instead of one draw, and it carries its own test metrics
    so nothing has to be scraped from a log that may belong to another run.

    Only used when its privacy accounting matches the proposed run's, so the
    two cannot silently diverge.
    """
    import glob as _glob
    files = sorted(_glob.glob(str(Path(out_dir) / "ablation_A0_seed*_final.json")))
    acc, auc, apr, eps, seeds = [], [], [], set(), []
    for f in files:
        try:
            with open(f) as fh:
                d = json.load(fh)
            t = d.get("test") or {}
            if t.get("accuracy") is None:
                continue
            acc.append(float(t["accuracy"]))
            auc.append(float(t["macro_auc"]))
            apr.append(float(t["auprc"]))
            eps.add(round(float(d.get("epsilon_spent", -1)), 4))
            seeds.append(d.get("seed"))
        except (ValueError, OSError, KeyError, TypeError):
            continue
    if not acc:
        return {}
    return {"accuracy": sum(acc) / len(acc),
            "macro_auc": sum(auc) / len(auc),
            "auprc": sum(apr) / len(apr),
            "n_seeds": len(acc),
            "epsilon_spent_set": eps,
            "seeds": seeds}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--local_epochs", type=int, default=1,
                    help="accepted for pipeline compatibility; hfl_trainer.py "
                         "has no such flag (local work is fixed at one epoch "
                         "per round) so it is NOT forwarded to the S3 arm")
    ap.add_argument("--tau_e", type=int, default=2,
                    help="edge aggregation cadence; must match the proposed "
                         "arm so the S3->S4 contrast isolates privacy cost")
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--epsilon", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--pretrained_encoders", default=None)
    ap.add_argument("--skip_s3", action="store_true",
                    help="do not train S3; report it as missing")
    ap.add_argument("--force_s3", action="store_true")
    ap.add_argument("--output_dir", default=None)
    a = ap.parse_args()

    ds = a.dataset
    spec = get_spec(ds)
    res = _SIM / "results" / "phase5"
    base = res / "baselines" / ds
    out_dir = Path(a.output_dir or _SIM / "results" / "phase6" / ds)
    out_dir.mkdir(parents=True, exist_ok=True)
    enc = a.pretrained_encoders or str(
        _SIM / "checkpoints" / f"pretrained_encoders_{ds}.pt")
    s3_csv = out_dir / f"s3_hedfl_{ds}.csv"

    print("=" * 84)
    print(f"JOINT EVALUATION — {ds.upper()}   (Phase 6, D6.1)")
    print("=" * 84)
    print(spec)

    # ── S3: the only arm with no existing artifact ──────────────────
    if not a.skip_s3 and (a.force_s3 or not s3_csv.exists()):
        if not os.path.exists(enc):
            print(f"\n[S3 SKIPPED] pretrained encoders missing: {enc}")
        else:
            # hfl_trainer.py has no --local_epochs: local work per round is
            # fixed at one epoch and the edge cadence is --tau_e. Passing it
            # killed this arm in ~1 s with an argparse error, which is why the
            # S3 row (and both contrasts that need it) read "not run". The same
            # mistake was already fixed for the `proposed` stage in the driver.
            argv = [sys.executable, str(_SIM / "model" / "training" / "hfl_trainer.py"),
                    "--dataset", ds, "--rounds", str(a.rounds),
                    "--tau_e", str(a.tau_e),
                    "--batch_size", str(a.batch_size), "--seed", str(a.seed),
                    "--no_dp",
                    "--freeze_encoders", "--pretrained_encoders", enc,
                    "--save_checkpoint", str(out_dir / f"ckpt_s3_{ds}.pt"),
                    "--output", str(s3_csv)]
            print("\n" + "=" * 84)
            print("  ▶ S3 HED-FL — hierarchical, NO differential privacy")
            print("=" * 84)
            print("  $ " + " ".join(argv))
            t0 = time.time()
            log = out_dir / "logs"; log.mkdir(exist_ok=True)
            with open(log / "s3_hedfl.log", "w") as lf:
                p = subprocess.Popen(argv, cwd=str(_SIM), stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in p.stdout:
                    sys.stdout.write(line); lf.write(line)
                p.wait()
            if p.returncode != 0:
                print(f"  ✗ S3 failed (exit {p.returncode}) — see {log/'s3_hedfl.log'}")
            else:
                print(f"  ✓ S3 done in {time.time()-t0:.0f}s")
    elif s3_csv.exists():
        print(f"\n  ⊙ S3 cached — {s3_csv.name}")

    # ── gather every system ─────────────────────────────────────────
    src = {
        "S0": base / "baseline_b0.csv",
        "S1": base / "baseline_b2.csv",
        "S2": base / "baseline_b4.csv",
        "S3": s3_csv,
        "S4": res / f"proposed_{ds}.csv",
    }
    ns3 = last_row(res / f"ns3_{ds}.csv")
    lat_path = latency_path(res, ds)

    def p95_ms(path):
        """End-to-end p95 inference latency, in ms, for the O3 (<100 ms) claim.

        inference_bench.py writes CSV (one row per pipeline component, columns
        mean_ms/p50_ms/p95_ms/...); older runs named that CSV file .json, so
        parse CSV first and fall back to JSON. The value we want is the
        `total_ms` row: a component row such as `preproc_ms` is ~20x smaller
        and would silently understate the reported latency.
        """
        if not path.exists():
            return None
        text = path.read_text().strip()
        if not text:
            return None

        # CSV form (what inference_bench.py actually produces).
        try:
            rows = list(csv.DictReader(io.StringIO(text)))
        except csv.Error:
            rows = []
        if rows and "p95_ms" in (rows[0].keys() or {}):
            by_name = {(r.get("component") or "").strip(): r for r in rows}
            row = by_name.get("total_ms")
            if row is None:
                return None          # no end-to-end row -> report nothing
            try:
                return float(row["p95_ms"])
            except (TypeError, ValueError, KeyError):
                return None

        # JSON fallback: accept {"total_ms": {"p95_ms": ...}} or a flat p95 key.
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        if isinstance(obj, dict):
            tot = obj.get("total_ms")
            if isinstance(tot, dict):
                for k, v in tot.items():
                    if "p95" in k.lower():
                        try:
                            return float(v)
                        except (TypeError, ValueError):
                            return None
            for k, v in obj.items():
                if "p95" in k.lower():
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
        return None

    _eps_total_composed = None
    _ptot = res / f"privacy_total_{ds}.json"
    if _ptot.exists():
        try:
            _eps_total_composed = float(json.loads(_ptot.read_text())["epsilon_TOTAL"])
        except (ValueError, OSError, KeyError, TypeError):
            _eps_total_composed = None

    table = []
    for sid, name, desc in SYSTEMS:
        r = last_row(src[sid])
        # S0-S2 are baselines and carry test_* columns. S3/S4 come from
        # hfl_trainer, whose CSV is VAL-only, so their test numbers come from
        # the run's own test artifact/log instead of the final val row.
        tm = trainer_test_metrics(src[sid]) if sid in ("S3", "S4") else {}
        _nseeds = 1 if tm else None
        if sid == "S4":
            # Prefer the multi-seed A0 arm when its privacy accounting matches
            # this run's, so S4 is a mean over seeds rather than one draw.
            a0 = a0_full_system_metrics(out_dir)
            _eps_csv = num(r, "epsilon_spent")
            if a0 and (_eps_csv is None
                       or round(_eps_csv, 4) in a0["epsilon_spent_set"]):
                tm = {k: a0[k] for k in ("accuracy", "macro_auc", "auprc")}
                _nseeds = a0["n_seeds"]
        _acc = num(r, "test_accuracy", "accuracy")
        _auc = num(r, "test_macro_auc", "macro_auc")
        _apr = num(r, "test_auprc", "auprc")
        if _acc is None and tm.get("accuracy") is not None:
            _acc, _auc, _apr = (tm.get("accuracy"), tm.get("macro_auc"),
                                tm.get("auprc"))
            _split = "test"
        else:
            _split = "test" if _acc is not None else ""
        table.append({
            "system": sid, "name": name, "description": desc,
            "source": str(src[sid].relative_to(_SIM)) if src[sid].exists() else "",
            "present": bool(r),
            "metric_split": _split,
            "n_seeds": _nseeds,
            "accuracy": _acc,
            "macro_auc": _auc,
            "auprc": _apr,
            "case_auc": num(r, "test_case_auc", "case_auc"),
            # epsilon_spent is the TRAINING term only. The conformal
            # calibration touches private val data and composes with it, so the
            # reportable budget is privacy_total_<ds>.json's epsilon_TOTAL
            # (0.9705 vs 0.7705 on vitaldb). check_objectives.py already scores
            # O2 on the total; this table must agree with it.
            "epsilon_spent": (_eps_total_composed
                              if (sid == "S4" and _eps_total_composed is not None)
                              else num(r, "epsilon_spent")),
            "uplink_mb": num(r, "uplink_mb", "total_uplink_mb", "uplink_total_mb"),
        })

    s0 = next((t for t in table if t["system"] == "S0"), None)
    ref_acc = s0["accuracy"] if s0 else None
    ref_up = s0["uplink_mb"] if s0 else None

    for t in table:
        # §6.2.2: accuracy loss is measured against S0, the no-privacy ceiling.
        t["acc_loss_vs_S0_pp"] = (
            (ref_acc - t["accuracy"]) * 100.0
            if (ref_acc is not None and t["accuracy"] is not None) else None)
        t["uplink_reduction_pct"] = (
            (1 - t["uplink_mb"] / ref_up) * 100.0
            if (ref_up and t["uplink_mb"] is not None) else None)
        # Latency and reliability are system-level QoS properties measured once
        # by ONNX/NS-3 on the deployed proposed model; they are not per-arm
        # training outputs, so they are attributed to S4 only rather than
        # copied across every row as if each arm had been benchmarked.
        t["p95_latency_ms"] = p95_ms(lat_path) if t["system"] == "S4" else None
        t["update_reliability_pct"] = (
            num(ns3, "update_reliability_pct", "reliability_pct")
            if t["system"] == "S4" else None)

    # ── write + print ───────────────────────────────────────────────
    out_csv = out_dir / "joint_eval.csv"
    fields = ["system", "name", "description", "present", "metric_split",
              "n_seeds", "accuracy", "macro_auc",
              "auprc", "case_auc", "acc_loss_vs_S0_pp", "uplink_mb",
              "uplink_reduction_pct", "p95_latency_ms", "update_reliability_pct",
              "epsilon_spent", "source"]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for t in table:
            w.writerow({k: ("" if t.get(k) is None else t.get(k)) for k in fields})

    def g(v, fmt="{:.4f}"):
        return fmt.format(v) if isinstance(v, float) else "—"

    print("\n" + "=" * 84)
    print(f"JOINT EVALUATION TABLE — {ds}")
    print("=" * 84)
    hdr = (f"{'':<4}{'System':<20}{'acc':>9}{'AUROC':>9}{'AUPRC':>9}"
           f"{'ΔaccS0':>9}{'eps':>8}")
    print(hdr); print("-" * len(hdr))
    for t in table:
        if not t["present"]:
            print(f"{t['system']:<4}{t['name']:<20}{'— not run —':>44}")
            continue
        print(f"{t['system']:<4}{t['name']:<20}{g(t['accuracy']):>9}"
              f"{g(t['macro_auc']):>9}{g(t['auprc']):>9}"
              f"{g(t['acc_loss_vs_S0_pp'], '{:+.2f}'):>9}"
              f"{g(t['epsilon_spent'], '{:.2f}'):>8}")
    print("-" * len(hdr))

    missing = [t["system"] for t in table if not t["present"]]
    if missing:
        hint = {"S0": "baselines (B0)", "S1": "baselines (B2)",
                "S2": "baselines (B4)", "S3": "this script without --skip_s3",
                "S4": "the proposed run"}
        print("\n  not yet measured:")
        for m in missing:
            print(f"    {m} → run {hint[m]}")

    # ── the two contrasts the table exists to support ───────────────
    def get(sid, key):
        t = next((x for x in table if x["system"] == sid), {})
        return t.get(key)

    print("\n  CONTRASTS")
    for lhs, rhs, label in (("S2", "S3", "hierarchy (both vs flat, ignoring DP)"),
                            ("S3", "S4", "privacy cost at fixed topology")):
        a_, b_ = get(lhs, "macro_auc"), get(rhs, "macro_auc")
        if a_ is not None and b_ is not None:
            print(f"    {lhs} → {rhs}   ΔAUROC {b_ - a_:+.4f}   ({label})")
        else:
            print(f"    {lhs} → {rhs}   —   ({label}; needs both arms)")

    print(f"\nWritten: {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
