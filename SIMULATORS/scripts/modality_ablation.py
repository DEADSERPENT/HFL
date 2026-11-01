"""
modality_ablation.py — does multimodal fusion actually help?

This is the experiment the whole dataset redesign was for. Research Gap #1
claims "no multimodal fusion in existing FL"; demonstrating that requires
showing fusion beats EITHER modality alone on honestly-paired data.

Deliberately CENTRALISED and NON-PRIVATE
----------------------------------------
No federation, no DP. The question is about the DATA — whether two modalities
carry complementary information — and FL/DP would only add variance and
confounds. A fusion gain that survives here is real; one that needs DP noise to
appear is not.

Fair comparison
---------------
All three arms share encoder architecture, head depth, optimiser, schedule,
epochs and seed. Only the head's input width differs (256 / 576 / 832), which
is inherent to the comparison and cannot be avoided.

RETRAINED, not input-zeroing. Feeding zeros to a jointly-trained model is
off-distribution and understates the ablated modality — it measures "what
happens when a modality breaks", not "what that modality is worth". Each arm is
trained from scratch on its own inputs.

Splits come from the dataset's own partition files, so the leakage controls
(case-level for VitalDB, (subject,activity)-temporal for WEAR) carry over.
"""

import os
import sys
import json
import time
import argparse

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _s in ("data/loaders", "model/architecture", "model/utils", "model/training"):
    sys.path.insert(0, os.path.join(_ROOT, _s))

from datasets import get_spec, REGISTRY# noqa: E402
from hfl_mm_model import (build_hfl_mm_hc, GroupNormND)   # noqa: E402
from device_utils import get_device, set_seed     # noqa: E402


class AblationModel(nn.Module):
    """One arm of the ablation: modality A only, B only, or both.

    Reuses the real encoders so the comparison reflects the actual system, and
    keeps the same 3-layer head shape as LateFusionHead so only the input width
    differs between arms.
    """

    def __init__(self, spec, mode: str, dropout: float = 0.3):
        super().__init__()
        base = build_hfl_mm_hc(
            n_classes=spec.n_classes, n_channels_a=spec.n_channels_a,
            **({} if spec.modality_b == "image"
               else {"modality_b": "features", "feat_b_dim": spec.feat_b_dim}))
        self.mode = mode
        self.encoder_a = base.encoder_a if mode in ("a", "both") else None
        self.encoder_b = base.encoder_b if mode in ("b", "both") else None
        d = (256 if mode == "a" else 576 if mode == "b" else 832)
        self.head = nn.Sequential(
            nn.Linear(d, 512), GroupNormND(16, 512), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(512, 256), GroupNormND(8, 256), nn.GELU(),
            nn.Linear(256, spec.n_classes),
        )

    def forward(self, xa, xb):
        if self.mode == "a":
            f = self.encoder_a(xa)
        elif self.mode == "b":
            f = self.encoder_b(xb)
        else:
            f = torch.cat([self.encoder_a(xa), self.encoder_b(xb)], dim=-1)
        return self.head(f)


def metrics(y, p, groups=None):
    from sklearn.metrics import roc_auc_score, average_precision_score
    n = p.shape[1]
    out = {"acc": float((p.argmax(1) == y).mean())}

    def ap(yy, pp):
        try:
            if n == 2:
                return (float(roc_auc_score(yy, pp[:, 1])),
                        float(average_precision_score(yy, pp[:, 1])))
            return (float(roc_auc_score(yy, pp, multi_class="ovr", average="macro",
                                        labels=list(range(n)))),
                    float(average_precision_score(np.eye(n)[yy], pp, average="macro")))
        except Exception:
            return float("nan"), float("nan")

    out["auroc"], out["auprc"] = ap(y, p)
    if groups is not None:
        g = np.unique(groups)
        gp = np.stack([p[groups == k].mean(0) for k in g])
        gy = np.array([y[groups == k][0] for k in g])
        out["case_auroc"], out["case_auprc"] = ap(gy, gp)
        out["case_acc"] = float((gp.argmax(1) == gy).mean())
    return out


@torch.no_grad()
def evaluate(model, loader, device, groups=None):
    model.eval()
    P, Y = [], []
    for xa, xb, _t, y in loader:
        P.append(torch.softmax(model(xa.to(device), xb.to(device)), -1).cpu().numpy())
        Y.append(y.numpy())
    return metrics(np.concatenate(Y), np.concatenate(P), groups)


def run_arm(spec, mode, idx, full_ds, device, args, groups_test):
    set_seed(args.seed)
    model = AblationModel(spec, mode).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)

    w = None
    if spec.n_classes == 2:                       # VitalDB is 19.7 % positive
        ytr = np.array([int(full_ds[int(i)][3]) for i in idx["train"]])
        cnt = np.bincount(ytr, minlength=2).astype(np.float64)
        w = torch.tensor(len(ytr) / (2 * np.maximum(cnt, 1)),
                         dtype=torch.float32, device=device)
    loss_fn = nn.CrossEntropyLoss(weight=w)

    dl = lambda k, bs, sh: DataLoader(Subset(full_ds, idx[k].tolist()),
                                      batch_size=bs, shuffle=sh, num_workers=0)
    tr, va, te = dl("train", args.batch_size, True), dl("val", 256, False), dl("test", 256, False)

    # Intra-epoch validation. On a small corpus one epoch is a few hundred
    # steps and a per-epoch checkpoint lands near the model's peak. On eICU an
    # epoch is ~41k steps and the model peaks near step ~1k before collapsing
    # to a constant output (val AUROC exactly 0.5000), so the FIRST per-epoch
    # eval already runs ~40x past the peak and best_state never sees it.
    # eval_every/val_cap/max_steps all default to 0 = OFF, which reproduces the
    # original per-epoch cadence exactly, so vitaldb and wear are unchanged.
    every    = max(0, int(getattr(args, "eval_every", 0) or 0))
    val_cap  = max(0, int(getattr(args, "val_cap", 0) or 0))
    max_step = max(0, int(getattr(args, "max_steps", 0) or 0))

    # A capped val loader keeps frequent checks affordable; the epoch-boundary
    # check always uses the FULL val split so the reported number is exact.
    va_quick = va
    if val_cap and val_cap < len(idx["val"]):
        sub = np.random.default_rng(args.seed).choice(
            idx["val"], val_cap, replace=False)
        va_quick = DataLoader(Subset(full_ds, np.sort(sub).tolist()),
                              batch_size=256, shuffle=False, num_workers=0)

    best, best_state = -1.0, None
    key = "auprc" if spec.n_classes == 2 else "auroc"
    stop = False

    def _check(tag, loader):
        nonlocal best, best_state
        m = evaluate(model, loader, device)
        if not np.isnan(m[key]) and m[key] > best:
            best = m[key]
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        print(f"      {tag}  val AUROC={m['auroc']:.4f} AUPRC={m['auprc']:.4f}", flush=True)
        model.train()

    step = 0
    for ep in range(1, args.epochs + 1):
        model.train()
        for xa, xb, _t, y in tr:
            opt.zero_grad()
            loss_fn(model(xa.to(device), xb.to(device)), y.to(device)).backward()
            opt.step()
            step += 1
            if every and step % every == 0:
                _check(f"ep{ep:2d} s{step:<7d}", va_quick)
            if max_step and step >= max_step:
                stop = True
                break
        _check(f"ep{ep:2d}         ", va)
        if stop:
            print(f"      [stop] max_steps={max_step} reached", flush=True)
            break
    model.load_state_dict(best_state)
    return evaluate(model, te, device, groups_test)


def verdict(agg, ga, gp):
    """Decide what the gain actually evidences.

    A positive gain is not on its own a result. Two things can hollow it out:

    * seed noise — a +0.0004 AUROC gain next to a +-0.0002 seed sd says nothing;
    * a ceiling — when the best single modality already reaches ~0.998 AUROC
      there is no headroom left for a second modality to fill, so the task
      cannot evidence fusion no matter what the gain sign is.

    WEAR hits both; VitalDB hits neither. Reporting one verdict for both would
    overclaim on WEAR, so the ceiling test is applied first.
    """
    best_uni = max(agg["a"]["auroc"][0], agg["b"]["auroc"][0])
    # Pool over arms rather than trusting the fused arm's own sd: with few seeds
    # a single arm can land on near-identical values and drive sd toward zero,
    # inflating the ratio arbitrarily. The widest arm is the honest yardstick.
    sd = max(max(agg[m]["auroc"][1] for m in ("a", "b", "both")), 1e-4)
    ratio = ga / sd
    if best_uni >= 0.99:
        return {"supports_gap1": False, "reason": "ceiling", "gain_over_sd": ratio,
                "best_unimodal_auroc": best_uni,
                "text": (f"CEILING — the best single modality already reaches "
                         f"{best_uni:.4f} AUROC. Fusion gain is real in sign but "
                         f"this task cannot evidence Gap #1.")}
    if ga > 0 and gp > 0 and ratio >= 3.0:
        return {"supports_gap1": True, "reason": "significant", "gain_over_sd": ratio,
                "best_unimodal_auroc": best_uni,
                "text": (f"fusion HELPS — beats both unimodal arms by "
                         f"{ratio:.1f}x seed-sd. Gap #1 demonstrated on this data.")}
    if ga > 0 and gp > 0:
        return {"supports_gap1": False, "reason": "within_noise", "gain_over_sd": ratio,
                "best_unimodal_auroc": best_uni,
                "text": (f"gain is positive but only {ratio:.1f}x seed-sd — "
                         f"within noise, not reportable as evidence.")}
    return {"supports_gap1": False, "reason": "no_gain", "gain_over_sd": ratio,
            "best_unimodal_auroc": best_uni,
            "text": "fusion does NOT beat the best single modality here."}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--eval_every", type=int, default=0,
                    help="validate every N optimiser steps (0 = only at epoch "
                         "end, the original behaviour). Needed on corpora whose "
                         "epoch is long enough to hide the model's peak.")
    ap.add_argument("--val_cap", type=int, default=0,
                    help="cap the val split used by intra-epoch checks "
                         "(0 = full). Epoch-boundary checks always use full val.")
    ap.add_argument("--max_steps", type=int, default=0,
                    help="stop each arm after N optimiser steps (0 = unlimited).")
    ap.add_argument("--feat_b_noise", type=str, default=None,
                    help="IDX:ALPHA — replace modality-B feature IDX with "
                         "ALPHA*x + sqrt(1-ALPHA^2)*eps, eps ~ N(0,1). Features "
                         "are z-scored, so this holds the channel's variance "
                         "fixed while degrading its signal-to-noise ratio "
                         "monotonically: ALPHA=1 is intact, ALPHA=0 is pure "
                         "noise. Unlike --feat_b_scale this actually removes "
                         "information, which is what titrating a modality's "
                         "strength requires.")
    ap.add_argument("--feat_b_scale", type=str, default=None,
                    help="IDX:ALPHA — multiply modality-B feature IDX by ALPHA. "
                         "Features are z-scored, so ALPHA=1 leaves it intact, "
                         "ALPHA=0 is equivalent to --feat_b_zero, and values "
                         "between titrate that modality's strength. Lets the "
                         "relative strength of the two modalities be set to a "
                         "TARGET rather than switched off, which is what "
                         "--feat_b_zero could not do.")
    ap.add_argument("--arms", nargs="+", default=["a", "b", "both"],
                    choices=["a", "b", "both"],
                    help="which arms to run. Calibration needs only 'b'.")
    ap.add_argument("--feat_b_zero", type=int, nargs="+", default=None,
                    help="zero these modality-B feature indices in EVERY split. "
                         "Features are z-scored, so zero is the mean and the "
                         "channel becomes uninformative while dimensionality, "
                         "architecture and all other settings stay identical. "
                         "Used to vary the relative strength of the two "
                         "modalities inside one corpus.")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    spec = get_spec(args.dataset)
    device = get_device()
    full_ds = spec.build_full(spec.data_dir)

    if args.feat_b_noise:
        import torch as _t
        _i, _al = args.feat_b_noise.split(":")
        _i, _al = int(_i), float(_al)
        tgt = None
        for attr in ("clinical", "features", "B", "feat_b", "modality_b", "xb"):
            if hasattr(full_ds, attr):
                tgt = getattr(full_ds, attr); break
        if tgt is None:
            raise SystemExit("--feat_b_noise: could not locate modality-B array")
        if _i >= tgt.shape[1]:
            raise SystemExit(f"--feat_b_noise: index {_i} out of range for width "
                             f"{tgt.shape[1]}")
        _g = _t.Generator().manual_seed(12345)   # fixed: the same corruption
        _eps = _t.randn(tgt.shape[0], generator=_g).to(tgt.dtype)
        _b = float(_t.as_tensor(tgt[:, _i]).float().std())
        tgt[:, _i] = _al * tgt[:, _i] + (1.0 - _al ** 2) ** 0.5 * _eps
        print(f"  [feat_b_noise] clinical[:, {_i}] -> {_al}*x + "
              f"{(1-_al**2)**0.5:.3f}*N(0,1)   (sd {_b:.4f} -> "
              f"{float(_t.as_tensor(tgt[:, _i]).float().std()):.4f}) over "
              f"{tgt.shape[0]:,} rows", flush=True)

    if args.feat_b_scale:
        print("  [warn] --feat_b_scale is INFORMATION-PRESERVING: a linear "
              "encoder compensates with a 1/alpha weight, so any alpha>0 is "
              "close to a no-op. Measured: alpha=0.15 left arm b at 0.8214 "
              "against 0.8221 intact. Use --feat_b_noise to titrate strength.",
              flush=True)
        # Titrated version of --feat_b_zero. Same in-place-on-the-tensor
        # reasoning: every split must see it, or the unimodal-B arm reads an
        # untouched feature and the comparison is meaningless.
        import torch as _t
        _i, _a = args.feat_b_scale.split(":")
        _i, _a = int(_i), float(_a)
        tgt = None
        for attr in ("clinical", "features", "B", "feat_b", "modality_b", "xb"):
            if hasattr(full_ds, attr):
                tgt = getattr(full_ds, attr); break
        if tgt is None:
            raise SystemExit("--feat_b_scale: could not locate modality-B array")
        if _i >= tgt.shape[1]:
            raise SystemExit(f"--feat_b_scale: index {_i} out of range for "
                             f"modality B of width {tgt.shape[1]}")
        _b = float(_t.as_tensor(tgt[:, _i]).float().abs().mean())
        tgt[:, _i] = tgt[:, _i] * _a
        _after = float(_t.as_tensor(tgt[:, _i]).float().abs().mean())
        print(f"  [feat_b_scale] {attr}[:, {_i}] x {_a}  "
              f"(mean |value| {_b:.4f} -> {_after:.4f}) over "
              f"{tgt.shape[0]:,} rows", flush=True)

    if args.feat_b_zero:
        # Zero in place on the underlying tensor so train, val and test all see
        # it; doing it in the arm loop would leave the unimodal-B arm reading
        # the untouched feature and make the comparison meaningless.
        import torch as _t
        tgt, name = None, None
        for attr in ("clinical", "features", "B", "feat_b", "modality_b", "xb"):
            if hasattr(full_ds, attr):
                tgt, name = getattr(full_ds, attr), attr
                break
        if tgt is None:
            raise SystemExit("--feat_b_zero: could not locate modality-B array "
                             f"on {type(full_ds).__name__}; looked for "
                             "clinical/features/B/feat_b/modality_b/xb")
        idx = list(args.feat_b_zero)
        if max(idx) >= tgt.shape[1]:
            raise SystemExit(f"--feat_b_zero: index {max(idx)} out of range for "
                             f"modality B of width {tgt.shape[1]}")
        before = [float(_t.as_tensor(tgt[:, i]).float().abs().mean()) for i in idx]
        tgt[:, idx] = 0
        print(f"  [feat_b_zero] zeroed {name}[:, {idx}] "
              f"(mean |value| before: {[round(b,4) for b in before]}) "
              f"over all {tgt.shape[0]:,} rows", flush=True)
    meta = json.load(open(os.path.join(spec.partition_dir, "partition_meta.json")))
    n_dev = meta["n_devices"]

    idx = {k: np.concatenate([np.load(os.path.join(
        spec.partition_dir, f"device_{d:02d}_{k}.npy")) for d in range(n_dev)])
        for k in ("train", "val", "test")}

    # Registry metric grouping (eICU: stay, not person; see baselines.py).
    gpath = os.path.join(spec.data_dir, spec.metric_group_file)
    groups_test = np.load(gpath)[idx["test"]] if os.path.exists(gpath) else None

    names = {"a": spec.modality_a_desc[:44], "b": spec.modality_b_desc[:44],
             "both": "FUSED"}
    print("=" * 74)
    print(f"  MODALITY ABLATION — {args.dataset}   ({spec.pairing})")
    print(f"  train={len(idx['train']):,} val={len(idx['val']):,} test={len(idx['test']):,}"
          f"  classes={spec.n_classes}  epochs={args.epochs}  seeds={args.seeds}")
    print("=" * 74)

    results = {}
    for seed in args.seeds:
        args.seed = seed
        for mode in args.arms:
            print(f"\n  [seed {seed}] arm '{mode}'  ({names[mode]})")
            t0 = time.time()
            r = run_arm(spec, mode, idx, full_ds, device, args, groups_test)
            r["seed"], r["mode"], r["secs"] = seed, mode, round(time.time() - t0, 1)
            results.setdefault(mode, []).append(r)
            print(f"      -> TEST AUROC={r['auroc']:.4f} AUPRC={r['auprc']:.4f} "
                  f"acc={r['acc']:.4f}" +
                  (f" | case AUROC={r['case_auroc']:.4f} AUPRC={r['case_auprc']:.4f}"
                   if "case_auroc" in r else "") + f"  ({r['secs']}s)")

    print("\n" + "=" * 74)
    print(f"  RESULT — {args.dataset}")
    print("=" * 74)
    hdr = f"  {'arm':<8}{'AUROC':>18}{'AUPRC':>18}{'acc':>10}"
    print(hdr + ("" if groups_test is None else f"{'case AUROC':>14}{'case AUPRC':>14}"))
    agg = {}
    for mode in args.arms:
        rs = results[mode]
        f = lambda k: (np.mean([r[k] for r in rs]), np.std([r[k] for r in rs]))
        agg[mode] = {k: f(k) for k in rs[0] if isinstance(rs[0][k], float)}
        line = (f"  {mode:<8}{f('auroc')[0]:>10.4f}±{f('auroc')[1]:.4f}"
                f"{f('auprc')[0]:>10.4f}±{f('auprc')[1]:.4f}{f('acc')[0]:>10.4f}")
        if groups_test is not None:
            line += f"{f('case_auroc')[0]:>14.4f}{f('case_auprc')[0]:>14.4f}"
        print(line)

    # A fusion verdict needs all three arms. Under --arms this run may be a
    # calibration of one modality's strength, which has no fusion gain to report.
    if {"a", "b", "both"} <= set(args.arms):
        ga = agg["both"]["auroc"][0] - max(agg["a"]["auroc"][0], agg["b"]["auroc"][0])
        gp = agg["both"]["auprc"][0] - max(agg["a"]["auprc"][0], agg["b"]["auprc"][0])
        v = verdict(agg, ga, gp)
        print(f"\n  fusion gain over the BEST unimodal arm:  "
              f"AUROC {ga:+.4f}   AUPRC {gp:+.4f}"
              f"   ({v['gain_over_sd']:.1f}x seed-sd)")
        print("  => " + v["text"])
        if "a" in agg and "b" in agg:
            print(f"  arm imbalance |A-B| AUROC: "
                  f"{abs(agg['a']['auroc'][0]-agg['b']['auroc'][0]):.4f}")
    else:
        ga = gp = None
        v = {"verdict": "not_a_fusion_test", "arms": list(args.arms),
             "text": "calibration run — a fusion gain needs all three arms"}
        print(f"\n  arms run: {args.arms} — no fusion verdict "
              f"(calibration run, not a test).")

    out = args.out or f"results/phase5/ablation_{args.dataset}.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"dataset": args.dataset, "pairing": spec.pairing,
               "epochs": args.epochs, "seeds": args.seeds,
               "n_train": int(len(idx["train"])), "n_test": int(len(idx["test"])),
               "runs": results,
               # Absent on a partial-arm run: a fusion gain needs all three arms.
               "arms": args.arms,
               "fusion_gain_auroc": ga, "fusion_gain_auprc": gp,
               "verdict": v},
              open(out, "w"), indent=2)
    print(f"\n[SAVED] {out}")


if __name__ == "__main__":
    main()
