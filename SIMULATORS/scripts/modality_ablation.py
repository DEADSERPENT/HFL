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

from datasets import get_spec                     # noqa: E402
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

    best, best_state = -1.0, None
    key = "auprc" if spec.n_classes == 2 else "auroc"
    for ep in range(1, args.epochs + 1):
        model.train()
        for xa, xb, _t, y in tr:
            opt.zero_grad()
            loss_fn(model(xa.to(device), xb.to(device)), y.to(device)).backward()
            opt.step()
        m = evaluate(model, va, device)
        if not np.isnan(m[key]) and m[key] > best:
            best = m[key]
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        print(f"      ep{ep:2d}  val AUROC={m['auroc']:.4f} AUPRC={m['auprc']:.4f}", flush=True)
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
    ap.add_argument("--dataset", required=True, choices=["wear", "vitaldb"])
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    spec = get_spec(args.dataset)
    device = get_device()
    full_ds = spec.build_full(spec.data_dir)
    meta = json.load(open(os.path.join(spec.partition_dir, "partition_meta.json")))
    n_dev = meta["n_devices"]

    idx = {k: np.concatenate([np.load(os.path.join(
        spec.partition_dir, f"device_{d:02d}_{k}.npy")) for d in range(n_dev)])
        for k in ("train", "val", "test")}

    gpath = os.path.join(spec.data_dir, "meta", "case_ids.npy")
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
        for mode in ("a", "b", "both"):
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
    for mode in ("a", "b", "both"):
        rs = results[mode]
        f = lambda k: (np.mean([r[k] for r in rs]), np.std([r[k] for r in rs]))
        agg[mode] = {k: f(k) for k in rs[0] if isinstance(rs[0][k], float)}
        line = (f"  {mode:<8}{f('auroc')[0]:>10.4f}±{f('auroc')[1]:.4f}"
                f"{f('auprc')[0]:>10.4f}±{f('auprc')[1]:.4f}{f('acc')[0]:>10.4f}")
        if groups_test is not None:
            line += f"{f('case_auroc')[0]:>14.4f}{f('case_auprc')[0]:>14.4f}"
        print(line)

    ga = agg["both"]["auroc"][0] - max(agg["a"]["auroc"][0], agg["b"]["auroc"][0])
    gp = agg["both"]["auprc"][0] - max(agg["a"]["auprc"][0], agg["b"]["auprc"][0])
    v = verdict(agg, ga, gp)
    print(f"\n  fusion gain over the BEST unimodal arm:  "
          f"AUROC {ga:+.4f}   AUPRC {gp:+.4f}"
          f"   ({v['gain_over_sd']:.1f}x seed-sd)")
    print("  => " + v["text"])

    out = args.out or f"results/phase5/ablation_{args.dataset}.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"dataset": args.dataset, "pairing": spec.pairing,
               "epochs": args.epochs, "seeds": args.seeds,
               "n_train": int(len(idx["train"])), "n_test": int(len(idx["test"])),
               "runs": results,
               "fusion_gain_auroc": ga, "fusion_gain_auprc": gp,
               "verdict": v},
              open(out, "w"), indent=2)
    print(f"\n[SAVED] {out}")


if __name__ == "__main__":
    main()
