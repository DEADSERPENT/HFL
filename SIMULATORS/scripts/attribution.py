"""
attribution.py — which inputs drive the prediction, and how much of that is
MISSINGNESS rather than measurement.

WHY
---
Two gaps close here.

1. "No feature attribution" is a stated limitation. For a clinical venue the
   question "which channels drove it" is expected, and a model that cannot
   answer it reads as a black box regardless of its AUROC.

2. Claim N-7, missingness-as-signal, is unproved. VitalDB carries missingness
   explicitly — 9 `*_observed` channels beside 9 numeric trends, 12
   `*_missing` flags beside the preoperative labs — because an arterial line
   or a coagulation panel is ordered only for patients already judged at risk.
   Attribution measures how much of the decision actually rides on those
   indicators.

   Read this honestly: attribution is EVIDENCE FOR N-7, not proof of it. It
   says the trained model leans on missingness; it does not say the model
   would lose accuracy without it. Only the mask-channel ablation shows that,
   because only removing a channel is a causal test. This script motivates
   that ablation and quantifies the effect; it does not replace it.

METHOD — integrated gradients
-----------------------------
    attr_i = (x_i - x'_i) * mean_over_alpha  dF(x' + alpha (x - x')) / dx_i

Implemented directly rather than pulled from captum: it is twenty lines, the
project gains no dependency, and the completeness identity below is a stronger
correctness check than trusting a library import.

IG is used rather than raw gradients or attention weights because it satisfies
completeness — attributions sum to the change in model output between the
baseline and the input. That identity is verified numerically on every run and
printed; a large error means the step count is too low or the model is not
smooth enough for the attribution to be trusted, and it is reported rather
than hidden.

THE BASELINE IS A MODELLING CHOICE, SO IT IS EXPLICIT
-----------------------------------------------------
IG measures deviation FROM a baseline, and the baseline defines what
"attribution" even means. A zero baseline is the usual default and is wrong
here in an interesting way: the preprocessing imputes missing values to the
channel mean AFTER normalisation and pins the corresponding mask at 0, so on
the value channels zero already means "average patient", while on the mask
channels zero means "nothing was ever recorded". One baseline vector would
silently mix "typical" and "absent".

Default `--baseline mean` therefore takes the empirical per-channel mean over
the reference split, computed from the data rather than assumed. Value
channels land near zero (the data is z-scored) and mask channels land at their
observation RATE, so the baseline is a coherent "average patient" and
attributions read as departures from one. `--baseline zero` remains available
and is labelled in the output, because the two answer different questions.

NO RETRAINING
-------------
Runs on released checkpoints. Nothing here trains, so it can run while the GPU
is busy with something else, and it cannot perturb any result already
measured.
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path

import numpy as np
import torch

_SIM = Path(__file__).resolve().parent.parent
for _s in ("data/loaders", "model/architecture", "model/utils"):
    sys.path.insert(0, str(_SIM / _s))

from datasets import get_spec, REGISTRY                          # noqa: E402
from hfl_mm_model import build_hfl_mm_hc                         # noqa: E402
from device_utils import get_device                              # noqa: E402


# Suffixes that mark an input as a missingness indicator rather than a
# measurement. Read from the channel names, not hardcoded per dataset, so a
# dataset that names its masks differently simply reports no mask group
# instead of silently mislabelling ordinary features as masks.
_MASK_SUFFIXES = ("_observed", "_missing")
_MASK_EXACT = ("abg_done",)


def is_mask(name: str) -> bool:
    return name.endswith(_MASK_SUFFIXES) or name in _MASK_EXACT


def load_names(spec, n_a: int, n_b: int):
    """Channel and feature names, falling back to indices when absent."""
    meta_p = _SIM / spec.data_dir / "meta" / "dataset_meta.json"
    names_a = names_b = None
    if meta_p.exists():
        m = json.loads(meta_p.read_text())
        names_a = m.get("signal_channels")
        names_b = m.get("clinical_features")
    if not names_a or len(names_a) != n_a:
        names_a = [f"ch_{i}" for i in range(n_a)]
    if not names_b or len(names_b) != n_b:
        names_b = [f"feat_{i}" for i in range(n_b)]
    return names_a, names_b


def integrated_gradients(model, xa, xb, base_a, base_b, target, steps):
    """IG for both modalities at once, returning per-element attributions.

    Both inputs are interpolated along the SAME path. Attributing one modality
    while holding the other at its true value would credit the fusion head's
    use of the fixed one to the interpolated one, and the completeness check
    below would fail — which is how that mistake gets caught.
    """
    ga = torch.zeros_like(xa)
    gb = torch.zeros_like(xb)
    # MIDPOINT rule over alpha, not the usual right Riemann sum. Measured
    # completeness error with right Riemann was 1.35 / 0.35 / 0.086 at 16 / 64
    # / 256 steps — first-order, so trustworthy attributions cost 256 forward
    # and backward passes per batch. The midpoint rule is second-order at
    # identical cost, which buys the same accuracy for a fraction of the
    # compute. The completeness check below is what makes this substitution
    # verifiable rather than a matter of taste.
    for k in range(1, steps + 1):
        alpha = (k - 0.5) / steps
        ia = (base_a + alpha * (xa - base_a)).detach().requires_grad_(True)
        ib = (base_b + alpha * (xb - base_b)).detach().requires_grad_(True)
        out = model(ia, ib)
        sel = out[:, target].sum()
        da, db = torch.autograd.grad(sel, [ia, ib])
        ga += da
        gb += db
    return (xa - base_a) * ga / steps, (xb - base_b) * gb / steps


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--ckpt", default=None,
                    help="default: results/phase5/patient_dp/<ds>/ckpt_patient_42.pt")
    ap.add_argument("--split", default="test", choices=["train", "val", "test"],
                    help="which split to attribute over (default test: the "
                         "model never saw it, so the attribution is not a "
                         "readout of memorised training points)")
    ap.add_argument("--n_samples", type=int, default=512)
    ap.add_argument("--steps", type=int, default=64,
                    help="IG interpolation steps. Default 64 measured at 3.6 %% "
                         "completeness error on vitaldb (16 -> 0.99, 32 -> 0.29, "
                         "64 -> 0.036); raise it if the check at the end warns")
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--baseline", choices=["mean", "zero"], default="mean")
    ap.add_argument("--target", choices=["positive", "predicted"],
                    default="positive",
                    help="logit to attribute: the positive class (default, the "
                         "clinically meaningful one) or each sample's own "
                         "prediction")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output", default=None)
    ap.add_argument("--skip_existing", action="store_true",
                    help="no-op if the output already exists, so a batch of "
                         "runs can be resumed after an interruption")
    a = ap.parse_args()

    sys.stdout.reconfigure(line_buffering=True)
    spec = get_spec(a.dataset)
    ckpt = Path(a.ckpt) if a.ckpt else (
        _SIM / "results" / "phase5" / "patient_dp" / a.dataset / "ckpt_patient_42.pt")
    if not ckpt.is_absolute():
        ckpt = _SIM / ckpt
    if not ckpt.exists():
        raise SystemExit(f"[FATAL] checkpoint not found: {ckpt}")

    # Resolved before any loading so --skip_existing costs nothing.
    out = Path(a.output) if a.output else (
        _SIM / "results" / "phase5" / "attribution" / a.dataset /
        f"attribution_{ckpt.stem}_{a.baseline}.csv")
    if not out.is_absolute():
        out = _SIM / out
    if a.skip_existing and out.exists():
        print(f"[skip] {out.name} already present")
        return 0

    device = get_device()
    ds = spec.build_full(str(_SIM / spec.data_dir))
    pdir = _SIM / spec.partition_dir
    n_dev = json.loads((pdir / "partition_meta.json").read_text())["n_devices"]
    idx = np.concatenate([np.load(pdir / f"device_{d:02d}_{a.split}.npy")
                          for d in range(n_dev)])

    rng = np.random.default_rng(a.seed)
    take = rng.choice(idx, min(a.n_samples, len(idx)), replace=False)

    kw = {"n_channels_a": spec.n_channels_a}
    if spec.modality_b != "image":
        kw.update(modality_b="features", feat_b_dim=spec.feat_b_dim)
    model = build_hfl_mm_hc(n_classes=spec.n_classes, **kw).to(device)
    sd = torch.load(ckpt, map_location=device, weights_only=False)
    sd = sd.get("model_state", sd) if isinstance(sd, dict) else sd
    model.load_state_dict(sd, strict=False)
    model.eval()

    x0 = ds[int(take[0])]
    n_a, n_b = x0[0].shape[0], x0[1].shape[0]
    names_a, names_b = load_names(spec, n_a, n_b)

    print("=" * 74)
    print(f"INTEGRATED-GRADIENT ATTRIBUTION — {a.dataset}")
    print("=" * 74)
    print(f"  checkpoint : {ckpt.relative_to(_SIM)}")
    print(f"  split      : {a.split}  ({len(take):,} of {len(idx):,} windows)")
    print(f"  baseline   : {a.baseline}   steps: {a.steps}   target: {a.target}")

    # ── baseline ────────────────────────────────────────────────────
    if a.baseline == "zero":
        base_a_np = np.zeros((n_a, x0[0].shape[1]), dtype=np.float32)
        base_b_np = np.zeros((n_b,), dtype=np.float32)
    else:
        ref = rng.choice(idx, min(2048, len(idx)), replace=False)
        sa = torch.stack([ds[int(i)][0] for i in ref]).float()
        sb = torch.stack([ds[int(i)][1] for i in ref]).float()
        base_a_np = sa.mean(0).numpy()
        base_b_np = sb.mean(0).numpy()
    base_a = torch.from_numpy(base_a_np).to(device)[None]
    base_b = torch.from_numpy(base_b_np).to(device)[None]

    attr_a = np.zeros(n_a)
    attr_b = np.zeros(n_b)
    abs_a = np.zeros(n_a)
    abs_b = np.zeros(n_b)
    comp_err, n_done = [], 0

    for s in range(0, len(take), a.batch_size):
        g = take[s:s + a.batch_size]
        xa = torch.stack([ds[int(i)][0] for i in g]).float().to(device)
        xb = torch.stack([ds[int(i)][1] for i in g]).float().to(device)
        ba = base_a.expand_as(xa)
        bb = base_b.expand_as(xb)

        if a.target == "positive":
            tgt = spec.n_classes - 1
        else:
            with torch.no_grad():
                tgt = int(model(xa, xb).argmax(1).mode().values)

        aa, ab = integrated_gradients(model, xa, xb, ba, bb, tgt, a.steps)

        # Completeness: sum of attributions should equal F(x) - F(baseline).
        with torch.no_grad():
            fx = model(xa, xb)[:, tgt]
            fb = model(ba, bb)[:, tgt]
        total = aa.flatten(1).sum(1) + ab.flatten(1).sum(1)
        denom = (fx - fb).abs().clamp(min=1e-6)
        comp_err.extend(((total - (fx - fb)).abs() / denom).cpu().tolist())

        # Sum over time for the signal channels; the clinical vector has no
        # time axis. Signed mean shows direction, absolute mean shows how much
        # the channel is used at all — a channel can matter greatly and still
        # average to zero across patients.
        attr_a += aa.sum(-1).sum(0).detach().cpu().numpy()
        abs_a += aa.sum(-1).abs().sum(0).detach().cpu().numpy()
        attr_b += ab.sum(0).detach().cpu().numpy()
        abs_b += ab.abs().sum(0).detach().cpu().numpy()
        n_done += len(g)
        print(f"  {n_done:>5}/{len(take)} windows", end="\r")

    attr_a /= n_done; abs_a /= n_done
    attr_b /= n_done; abs_b /= n_done
    print(" " * 40, end="\r")

    rows = []
    for nm, sg, ab_ in zip(names_a, attr_a, abs_a):
        rows.append({"modality": "A_signal", "name": nm,
                     "is_mask": int(is_mask(nm)),
                     "mean_attr": float(sg), "mean_abs_attr": float(ab_)})
    for nm, sg, ab_ in zip(names_b, attr_b, abs_b):
        rows.append({"modality": "B_clinical", "name": nm,
                     "is_mask": int(is_mask(nm)),
                     "mean_attr": float(sg), "mean_abs_attr": float(ab_)})

    tot = sum(r["mean_abs_attr"] for r in rows) or 1.0
    for r in rows:
        r["share_pct"] = 100.0 * r["mean_abs_attr"] / tot

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    # ── report ──────────────────────────────────────────────────────
    print(f"\n  TOP 15 INPUTS BY ATTRIBUTION MASS")
    print(f"  {'input':<26}{'modality':<12}{'mask':>6}{'share %':>10}{'signed':>12}")
    print("  " + "-" * 64)
    for r in sorted(rows, key=lambda r: -r["mean_abs_attr"])[:15]:
        print(f"  {r['name']:<26}{r['modality']:<12}"
              f"{'yes' if r['is_mask'] else '—':>6}"
              f"{r['share_pct']:>9.2f}%{r['mean_attr']:>+12.4f}")

    # The signed column is (x - baseline) * grad averaged over patients, so
    # for a binary mask it carries the sign of the DEVIATION as well as the
    # direction of the effect: an indicator observed in only 30 % of windows
    # sits below its own baseline for the other 70 %, and averages negative
    # even when observing it raises risk. Rank on share, read direction per
    # patient, and never quote the population sign as a clinical effect.
    print("\n  NB: 'signed' mixes effect direction with deviation from the "
          "baseline\n      rate; it is not a per-patient effect size. Rank on "
          "share %.")

    mask_rows = [r for r in rows if r["is_mask"]]
    val_rows = [r for r in rows if not r["is_mask"]]
    m_share = sum(r["share_pct"] for r in mask_rows)

    print(f"\n  MISSINGNESS vs MEASUREMENT  (evidence for N-7)")
    print(f"    missingness indicators : {len(mask_rows):>3} inputs"
          f"   {m_share:>6.2f} % of attribution mass")
    print(f"    measured values        : {len(val_rows):>3} inputs"
          f"   {100 - m_share:>6.2f} %")
    if mask_rows:
        per_mask = m_share / len(mask_rows)
        per_val = (100 - m_share) / max(len(val_rows), 1)
        print(f"    per-input average      : mask {per_mask:.3f} %"
              f"  vs value {per_val:.3f} %"
              f"   ({per_mask / per_val:.2f}x)" if per_val else "")
        print(f"    top missingness input  : "
              f"{max(mask_rows, key=lambda r: r['mean_abs_attr'])['name']}")

    err = float(np.mean(comp_err)) if comp_err else float("nan")
    print(f"\n  COMPLETENESS CHECK")
    print(f"    mean |sum(attr) - (F(x) - F(baseline))| / |F(x) - F(baseline)|"
          f" = {err:.4f}")
    if err > 0.10:
        print(f"    [warn] above 10 %: attributions are only indicative at "
              f"this step count. Re-run with a larger --steps before quoting "
              f"these numbers in the paper.")
    else:
        print(f"    within tolerance — attributions account for the model's "
              f"output shift.")

    json.dump({"dataset": a.dataset, "checkpoint": str(ckpt),
               "split": a.split, "n_windows": int(n_done),
               "baseline": a.baseline, "steps": a.steps, "target": a.target,
               "missingness_share_pct": m_share,
               "completeness_rel_err": err},
              open(out.with_suffix(".json"), "w"), indent=2)

    print(f"""
  N-7 reads: {m_share:.1f} % of the model's attribution mass sits on inputs that
  encode WHETHER something was measured rather than WHAT was measured. That
  motivates the mask-channel ablation; it does not substitute for it, because
  only removing the channels shows what the model would lose.

  Written: {out}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
