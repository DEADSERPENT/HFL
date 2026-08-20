"""
make_figures.py — Phase 6 deliverable D6.3 (Phase 6.txt §6.5).

Generates the publication figures from measured artifacts only:

  Fig 2   Convergence curves (accuracy vs rounds, all systems)
  Fig 3   Communication volume comparison
  Fig 4   Privacy–accuracy trade-off (eps sweep, both recipes)
  Fig 5   Inference latency CDF (P50/P95/P99)
  Fig 6   Energy consumption breakdown
  Fig 7   Ablation radar chart
  Fig 8   Non-IID data distribution heatmap (device x class)
  Fig 9   Round-by-round privacy budget eps(t)
  Fig 10  Joint QoS validation summary vs the four objective thresholds

  (Fig 1, the architecture diagram, is produced by generate_framework_diagram.py
   at the repo root and is not regenerated here.)

A figure is SKIPPED, loudly, when its source artifact does not exist. It is
never drawn from placeholder or illustrative numbers: a plot in a thesis is
read as evidence, and a plausible-looking curve with invented values is worse
than a missing figure because nothing downstream reveals it was invented.
Every figure writes a sidecar .source.txt naming the artifact it was drawn
from, so any panel can be traced back to the run that produced it.
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_SIM = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import get_spec, REGISTRY                       # noqa: E402

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 200, "font.size": 10,
    "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
    "axes.spines.right": False, "figure.autolayout": True,
})
PAL = ["#2E6FD1", "#E8A33D", "#2E9E75", "#C0392B", "#7D3C98", "#5D6D7E"]

# Objective thresholds — imported from the single definition in check_objectives
sys.path.insert(0, str(_SIM / "scripts"))
try:
    from check_objectives import OBJECTIVES
except Exception:
    OBJECTIVES = {}


class Figures:
    def __init__(self, ds, out_dir):
        self.ds = ds
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.res = _SIM / "results" / "phase5"
        self.p6 = _SIM / "results" / "phase6" / ds
        self.made, self.skipped = [], []

    # ── helpers ─────────────────────────────────────────────────────
    def rows(self, p):
        p = Path(p)
        if not p.exists():
            return []
        with open(p) as f:
            return list(csv.DictReader(f))

    def jload(self, p):
        p = Path(p)
        return json.loads(p.read_text()) if p.exists() else None

    def skip(self, fig, why):
        self.skipped.append((fig, why))
        print(f"  ⊘ {fig:<8} skipped — {why}")

    def save(self, fig, name, sources):
        path = self.out / f"{name}.png"
        fig.savefig(path, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        (self.out / f"{name}.source.txt").write_text(
            "drawn from:\n" + "\n".join(f"  {s}" for s in sources) + "\n")
        self.made.append(name)
        print(f"  ✓ {name}")

    @staticmethod
    def f(r, *keys):
        for k in keys:
            try:
                v = float(r[k])
                if v == v:
                    return v
            except (KeyError, TypeError, ValueError):
                continue
        return None

    # ── Fig 2 — convergence ─────────────────────────────────────────
    def fig2(self):
        src, series = [], {}
        for label, p in (("S4 HFL-MM", self.res / f"proposed_{self.ds}.csv"),
                         ("S3 HED-FL", self.p6 / f"s3_hedfl_{self.ds}.csv")):
            rs = self.rows(p)
            ys = [self.f(r, "test_macro_auc", "macro_auc", "val_auc") for r in rs]
            ys = [y for y in ys if y is not None]
            if len(ys) > 1:
                series[label] = ys
                src.append(str(p.relative_to(_SIM)))
        # baselines record a per-round val history as a JSON list
        for label, fn in (("S1 FedAvg", "baseline_b2.csv"),
                          ("S2 DP-FedAvg", "baseline_b4.csv")):
            p = self.res / "baselines" / self.ds / fn
            for r in self.rows(p):
                try:
                    hist = json.loads(r.get("val_auc_history", "[]"))
                except json.JSONDecodeError:
                    hist = []
                if len(hist) > 1:
                    series[label] = hist
                    src.append(str(p.relative_to(_SIM)))
        if not series:
            return self.skip("Fig 2", "no per-round history in any run")
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for i, (k, v) in enumerate(sorted(series.items())):
            ax.plot(range(1, len(v) + 1), v, marker="o", ms=3,
                    color=PAL[i % len(PAL)], label=k)
        ax.set_xlabel("Communication round"); ax.set_ylabel("Macro AUROC")
        ax.set_title(f"Fig. 2 — Convergence ({self.ds})")
        ax.legend(frameon=False)
        self.save(fig, "Fig2_convergence", src)

    # ── Fig 3 — communication volume ────────────────────────────────
    def fig3(self):
        je = self.rows(self.p6 / "joint_eval.csv")
        pts = [(r["system"], self.f(r, "uplink_mb")) for r in je]
        pts = [(s, v) for s, v in pts if v is not None]
        if not pts:
            return self.skip("Fig 3", "no uplink_mb in joint_eval.csv")
        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.bar([s for s, _ in pts], [v for _, v in pts],
               color=[PAL[i % len(PAL)] for i in range(len(pts))])
        for i, (_, v) in enumerate(pts):
            ax.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=9)
        ax.set_ylabel("Uplink volume (MB / run)")
        ax.set_title(f"Fig. 3 — Communication volume ({self.ds})")
        self.save(fig, "Fig3_communication", ["results/phase6/joint_eval.csv"])

    # ── Fig 4 — privacy/accuracy trade-off ──────────────────────────
    def fig4(self):
        p = self.res / "epsilon_sweep" / self.ds / "epsilon_sweep.csv"
        rs = self.rows(p)
        if not rs:
            return self.skip("Fig 4", "epsilon_sweep.csv not found")
        by = {}
        for r in rs:
            v = self.f(r, "macro_auc")
            if v is None:
                continue
            by.setdefault(r["recipe"], {}).setdefault(r["epsilon"], []).append(v)
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for i, (rec, d) in enumerate(sorted(by.items())):
            fin = sorted([e for e in d if e != "inf"], key=float)
            if not fin:
                continue
            xs = [float(e) for e in fin]
            ys = [np.mean(d[e]) for e in fin]
            es = [np.std(d[e]) for e in fin]
            ax.errorbar(xs, ys, yerr=es, marker="o", capsize=3,
                        color=PAL[i % len(PAL)],
                        label={"head": "head-only DP (proposed)",
                               "full": "full-model DP"}.get(rec, rec))
        if "none" in by and "inf" in by["none"]:
            ref = np.mean(by["none"]["inf"])
            ax.axhline(ref, ls="--", color="#5D6D7E", lw=1.2,
                       label=f"no DP reference ({ref:.3f})")
        ax.set_xscale("log"); ax.set_xlabel("privacy budget ε (log scale)")
        ax.set_ylabel("Macro AUROC")
        ax.set_title(f"Fig. 4 — Privacy–utility trade-off ({self.ds})")
        ax.legend(frameon=False, fontsize=8.5)
        self.save(fig, "Fig4_privacy_tradeoff", [str(p.relative_to(_SIM))])

    # ── Fig 5 — latency CDF ─────────────────────────────────────────
    def fig5(self):
        d = self.jload(self.res / f"latency_{self.ds}.json")
        if not d:
            return self.skip("Fig 5", f"latency_{self.ds}.json not found")

        def samples(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, list) and len(v) > 20 and \
                       all(isinstance(z, (int, float)) for z in v):
                        return np.asarray(v, float)
                    r = samples(v)
                    if r is not None:
                        return r
            elif isinstance(o, list):
                for v in o:
                    r = samples(v)
                    if r is not None:
                        return r
            return None
        s = samples(d)
        if s is None:
            return self.skip("Fig 5", "no raw per-run latency samples "
                                      "(only summary percentiles) — a CDF "
                                      "needs the samples")
        s = np.sort(s)
        fig, ax = plt.subplots(figsize=(6.5, 4.2))
        ax.plot(s, np.arange(1, len(s) + 1) / len(s), color=PAL[0], lw=1.8)
        for q, c in ((50, PAL[2]), (95, PAL[1]), (99, PAL[3])):
            v = float(np.percentile(s, q))
            ax.axvline(v, ls="--", lw=1.1, color=c, label=f"P{q} = {v:.2f} ms")
        ax.axvline(100, color="#C0392B", lw=2,
                   label="objective < 100 ms")
        ax.set_xlabel("End-to-end inference latency (ms)")
        ax.set_ylabel("Cumulative probability")
        ax.set_title(f"Fig. 5 — Inference latency CDF ({self.ds})")
        ax.legend(frameon=False, fontsize=8.5)
        self.save(fig, "Fig5_latency_cdf", [f"results/phase5/latency_{self.ds}.json"])

    # ── Fig 6 — energy ──────────────────────────────────────────────
    def fig6(self):
        cands = list((self.res).glob(f"cloudsim*{self.ds}*.csv")) + \
                list((self.res).glob("cloudsim*.csv"))
        rs = self.rows(cands[0]) if cands else []
        if not rs:
            return self.skip("Fig 6", "no CloudSim energy CSV")
        keys = [k for k in rs[0] if "energy" in k.lower() and "pct" not in k.lower()]
        if not keys:
            return self.skip("Fig 6", "no energy columns in CloudSim CSV")
        labels = [r.get("scenario", r.get("system", f"row{i}"))
                  for i, r in enumerate(rs)]
        fig, ax = plt.subplots(figsize=(7, 4.2))
        bottom = np.zeros(len(rs))
        for i, k in enumerate(keys):
            vals = np.array([self.f(r, k) or 0.0 for r in rs])
            ax.bar(labels, vals, bottom=bottom, label=k, color=PAL[i % len(PAL)])
            bottom += vals
        ax.set_ylabel("Energy per round (J)")
        ax.set_title(f"Fig. 6 — Energy breakdown ({self.ds})")
        ax.legend(frameon=False, fontsize=8)
        plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
        self.save(fig, "Fig6_energy", [str(cands[0].relative_to(_SIM))])

    # ── Fig 7 — ablation radar ──────────────────────────────────────
    def fig7(self):
        rs = self.rows(self.p6 / "ablation.csv")
        rs = [r for r in rs if self.f(r, "test_macro_auc") is not None]
        if len(rs) < 3:
            return self.skip("Fig 7", "need >=3 ablation arms")
        metrics = [("test_macro_auc", "AUROC"), ("test_auprc", "AUPRC"),
                   ("test_accuracy", "Accuracy")]
        metrics = [(k, lb) for k, lb in metrics
                   if any(self.f(r, k) is not None for r in rs)]
        ang = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        ang += ang[:1]
        fig, ax = plt.subplots(figsize=(5.8, 5.8), subplot_kw=dict(polar=True))
        for i, r in enumerate(rs):
            vals = [self.f(r, k) or 0.0 for k, _ in metrics]
            vals += vals[:1]
            ax.plot(ang, vals, color=PAL[i % len(PAL)], lw=1.6,
                    label=f"{r.get('arm','')} {r.get('removes','')}")
            ax.fill(ang, vals, color=PAL[i % len(PAL)], alpha=0.07)
        ax.set_xticks(ang[:-1]); ax.set_xticklabels([lb for _, lb in metrics])
        ax.set_title(f"Fig. 7 — Component ablation ({self.ds})", pad=18)
        ax.legend(loc="upper right", bbox_to_anchor=(1.32, 1.12),
                  frameon=False, fontsize=8)
        self.save(fig, "Fig7_ablation_radar", ["results/phase6/ablation.csv"])

    # ── Fig 8 — non-IID heatmap ─────────────────────────────────────
    def fig8(self):
        spec = get_spec(self.ds)
        pdir = _SIM / spec.partition_dir
        meta_p = pdir / "partition_meta.json"
        if not meta_p.exists():
            return self.skip("Fig 8", "partition_meta.json not found")
        meta = json.loads(meta_p.read_text())
        n_dev = meta["n_devices"]
        lbl = None
        for c in (_SIM / spec.data_dir).rglob("*labels.npy"):
            lbl = np.load(c)
            break
        if lbl is None:
            return self.skip("Fig 8", "no labels.npy under the data dir")
        M = np.zeros((n_dev, spec.n_classes))
        for d in range(n_dev):
            f = pdir / f"device_{d:02d}_train.npy"
            if not f.exists():
                continue
            idx = np.load(f)
            for c, n in zip(*np.unique(lbl[idx], return_counts=True)):
                if 0 <= int(c) < spec.n_classes:
                    M[d, int(c)] = n
        row = M.sum(1, keepdims=True)
        frac = np.divide(M, row, out=np.zeros_like(M), where=row > 0)
        fig, ax = plt.subplots(figsize=(max(6, spec.n_classes * 0.5), max(3.6, n_dev * 0.3)))
        im = ax.imshow(frac, aspect="auto", cmap="YlGnBu", vmin=0, vmax=frac.max())
        ax.set_xlabel("Class"); ax.set_ylabel("Client / device")
        # Classes are categorical: without explicit ticks matplotlib labels the
        # imshow axis continuously (-0.5 … n-0.5), which reads as fractional
        # class indices that do not exist.
        ax.set_xticks(range(spec.n_classes))
        ax.set_xticklabels(range(spec.n_classes),
                           fontsize=8 if spec.n_classes <= 20 else 6)
        ax.set_yticks(range(n_dev)); ax.set_yticklabels(range(n_dev), fontsize=7)
        ax.set_title(f"Fig. 8 — Non-IID label distribution ({self.ds})")
        fig.colorbar(im, ax=ax, label="fraction of client's train split")
        ax.grid(False)
        self.save(fig, "Fig8_noniid_heatmap", [str(pdir.relative_to(_SIM))])

    # ── Fig 9 — epsilon(t) ──────────────────────────────────────────
    def fig9(self):
        rs = self.rows(self.res / f"proposed_{self.ds}.csv")
        ys = [self.f(r, "epsilon_spent") for r in rs]
        ys = [y for y in ys if y is not None]
        if len(ys) < 2:
            return self.skip("Fig 9", "no per-round epsilon_spent history")
        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(range(1, len(ys) + 1), ys, marker="o", ms=3, color=PAL[3])
        ax.axhline(1.0, ls="--", color="#C0392B", label="budget ε = 1")
        ax.set_xlabel("Communication round"); ax.set_ylabel("cumulative ε spent")
        ax.set_title(f"Fig. 9 — Privacy budget consumption ({self.ds})")
        ax.legend(frameon=False)
        self.save(fig, "Fig9_epsilon_budget", [f"results/phase5/proposed_{self.ds}.csv"])

    # ── Fig 10 — QoS summary ────────────────────────────────────────
    def fig10(self):
        d = self.jload(self.res / f"objectives_{self.ds}.json")
        if not d:
            return self.skip("Fig 10", f"objectives_{self.ds}.json not found")
        objs = d.get("objectives", {})
        got = [(k, v) for k, v in objs.items() if v.get("measured") is not None]
        if not got:
            return self.skip("Fig 10", "no objective has been measured yet")
        fig, ax = plt.subplots(figsize=(7.5, 4.2))
        xs = np.arange(len(got))
        # Normalise each objective to "fraction of its own threshold" so four
        # different units (%, ms, eps, pp) share one axis; 1.0 is the target.
        norm, cols, labs = [], [], []
        for k, v in got:
            t, m = v["target"], v["measured"]
            r = (m / t) if v["cmp"] in (">=", ">") else (t / m if m else 0)
            norm.append(r)
            cols.append("#1E8449" if v["verdict"] == "PASS" else "#C0392B")
            labs.append(f"{k}\n{v['name'][:18]}")
        ax.bar(xs, norm, color=cols)
        ax.axhline(1.0, ls="--", color="#1B2631", lw=1.4, label="objective threshold")
        for x, (k, v), r in zip(xs, got, norm):
            ax.text(x, r, f"{v['measured']:.2f}{v['unit']}", ha="center",
                    va="bottom", fontsize=8)
        ax.set_xticks(xs); ax.set_xticklabels(labs, fontsize=8)
        ax.set_ylabel("achieved / required  (1.0 = target met)")
        ax.set_title(f"Fig. 10 — Objective validation ({self.ds})")
        ax.legend(frameon=False)
        self.save(fig, "Fig10_qos_summary", [f"results/phase5/objectives_{self.ds}.json"])

    def run(self, only=None):
        for name in ("fig2", "fig3", "fig4", "fig5", "fig6",
                     "fig7", "fig8", "fig9", "fig10"):
            if only and name not in only:
                continue
            try:
                getattr(self, name)()
            except Exception as e:
                self.skip(name, f"{type(e).__name__}: {e}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--output_dir", default=None)
    ap.add_argument("--only", nargs="*", default=None,
                    help="e.g. --only fig4 fig8")
    a = ap.parse_args()

    out = a.output_dir or _SIM / "results" / "phase6" / a.dataset / "figures"
    print("=" * 74)
    print(f"FIGURES — {a.dataset.upper()}   (Phase 6, D6.3)")
    print("=" * 74)
    F = Figures(a.dataset, out)
    F.run(a.only)
    print("\n" + "=" * 74)
    print(f"  {len(F.made)} figure(s) written to {out}")
    if F.skipped:
        print(f"  {len(F.skipped)} skipped (missing evidence — NOT drawn from "
              f"placeholders):")
        for fig, why in F.skipped:
            print(f"    · {fig}: {why}")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
