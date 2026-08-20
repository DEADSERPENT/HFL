"""
membership_inference.py — does record-level DP actually protect a PATIENT?

THE CLAIM THIS TESTS
--------------------
Standard DP-SGD clips per SAMPLE. Here a sample is a 10-minute window and each
patient contributes ~8 of them. So a record-level epsilon answers "was this
WINDOW in training?" while the clinical guarantee must answer "was this PATIENT
in training?".

That is an argument. This turns it into a measurement: mount a patient-level
membership inference attack against both models and see which one leaks.

    record-level DP  -> attack AUC well above 0.5  => guarantee does NOT hold
    patient-level DP -> attack AUC near 0.5        => guarantee holds

A demonstrated vulnerability is worth far more than an analytical argument,
because it shows the failure is reachable rather than merely possible.

THE ATTACK
----------
Loss-thresholding, aggregated to the patient. For each patient the adversary
computes the mean per-window loss under the released model and predicts
"member" when that loss is low — members are fitted better than strangers.
Attack strength is the AUC of that score against true membership.

Why AGGREGATE per patient: a per-window attack measures window membership,
which is exactly the quantity record-level DP does protect. Averaging a
patient's windows is what converts weak per-record signal into a strong
per-person one — and it is the reason a per-record guarantee does not transfer.
The averaging is the attack.

MEMBERS vs NON-MEMBERS
----------------------
members     = patients in the clients' TRAIN splits (the model saw them)
non-members = patients in the TEST split (never seen, and case-level splitting
              guarantees no window of theirs leaked into training)

Both groups are scored by the same model with the same code path, so any
separation is membership signal rather than a distribution difference.

FAIRNESS
--------
Both arms are attacked with the identical routine, the identical patient sets
and the identical seeds. Only the defence differs.
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

_SIM = Path(__file__).resolve().parent.parent
for _s in ("data/loaders", "model/architecture", "model/utils", "model/privacy"):
    sys.path.insert(0, str(_SIM / _s))

from datasets import get_spec, REGISTRY                       # noqa: E402
from hfl_mm_model import build_hfl_mm_hc                      # noqa: E402
from device_utils import get_device                           # noqa: E402


def per_patient_loss(model, dataset, groups, device, class_weight=None,
                     max_windows=64):
    """Mean per-window loss for each patient. Lower => more likely a member."""
    lf = nn.CrossEntropyLoss(
        reduction="none",
        weight=class_weight.to(device) if class_weight is not None else None)
    model.eval()
    out = []
    with torch.no_grad():
        for g in groups:
            g = g[:max_windows]
            if len(g) == 0:
                continue
            xa = torch.stack([dataset[int(i)][0] for i in g]).to(device)
            xb = torch.stack([dataset[int(i)][1] for i in g]).to(device)
            y = torch.tensor([int(dataset[int(i)][3]) for i in g], device=device)
            out.append(float(lf(model(xa, xb), y).mean()))
    return np.asarray(out)


def attack_auc(member_scores, nonmember_scores):
    """AUC of the membership decision.

    Score is NEGATIVE loss, so higher = more member-like. AUC 0.5 means the
    adversary cannot distinguish; 1.0 means perfectly.
    """
    from sklearn.metrics import roc_auc_score
    y = np.r_[np.ones(len(member_scores)), np.zeros(len(nonmember_scores))]
    s = np.r_[-member_scores, -nonmember_scores]
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--ckpt_dir", default=None,
                    help="default: results/phase5/patient_dp/<dataset>")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
    ap.add_argument("--max_patients", type=int, default=600,
                    help="patients sampled per group (equal-sized member and "
                         "non-member sets keep the AUC unbiased)")
    ap.add_argument("--ckpt_pattern", default="ckpt_{unit}_{seed}.pt",
                    help="checkpoint filename template; {unit} and {seed} are "
                         "substituted. Lets one attack routine sweep models "
                         "trained at different budgets.")
    ap.add_argument("--output", default=None)
    a = ap.parse_args()

    spec = get_spec(a.dataset)
    ckpt_dir = Path(a.ckpt_dir or _SIM / "results" / "phase5" / "patient_dp" / a.dataset)
    device = get_device()

    cid_path = _SIM / spec.data_dir / "meta" / "case_ids.npy"
    if not cid_path.exists():
        raise SystemExit(
            f"[FATAL] no case ids at {cid_path}. Without patient identity there "
            f"is no patient-level membership question to ask.")
    case_ids = np.load(cid_path)

    full_ds = spec.build_full(str(_SIM / spec.data_dir))
    pdir = _SIM / spec.partition_dir
    with open(pdir / "partition_meta.json") as f:
        n_dev = json.load(f)["n_devices"]

    train_idx = np.concatenate([np.load(pdir / f"device_{d:02d}_train.npy")
                                for d in range(n_dev)])
    test_idx = np.concatenate([np.load(pdir / f"device_{d:02d}_test.npy")
                               for d in range(n_dev)])

    def groups_of(idx):
        cids = case_ids[idx]
        order = np.argsort(cids, kind="stable")
        idx_s, cid_s = idx[order], cids[order]
        return np.split(idx_s, np.flatnonzero(np.diff(cid_s)) + 1)

    mem_all, non_all = groups_of(train_idx), groups_of(test_idx)
    rng = np.random.default_rng(0)
    n = min(a.max_patients, len(mem_all), len(non_all))
    mem = [mem_all[i] for i in rng.choice(len(mem_all), n, replace=False)]
    non = [non_all[i] for i in rng.choice(len(non_all), n, replace=False)]

    # Same class weighting the models trained under, so the loss the adversary
    # sees is the loss the model was optimised for.
    ytr = np.array([int(full_ds[int(i)][3]) for i in train_idx[:20000]])
    cnt = np.bincount(ytr, minlength=spec.n_classes).astype(float)
    cw = torch.tensor(len(ytr) / (spec.n_classes * np.maximum(cnt, 1)),
                      dtype=torch.float32)

    kw = {"n_channels_a": spec.n_channels_a}
    if spec.modality_b != "image":
        kw.update(modality_b="features", feat_b_dim=spec.feat_b_dim)

    print("=" * 74)
    print(f"PATIENT-LEVEL MEMBERSHIP INFERENCE — {a.dataset}")
    print("=" * 74)
    print(f"  members (train patients)   : {len(mem)}")
    print(f"  non-members (test patients): {len(non)}")
    print(f"  attack: mean per-window loss, aggregated per patient")
    print(f"  AUC 0.5 = no leakage · >0.5 = patient membership detectable\n")

    rows = []
    for unit, label in (("sample", "record-level DP"), ("patient", "patient-level DP")):
        aucs = []
        for seed in a.seeds:
            ck = ckpt_dir / a.ckpt_pattern.format(unit=unit, seed=seed)
            if not ck.exists():
                print(f"  [skip] {ck.name} missing")
                continue
            model = build_hfl_mm_hc(n_classes=spec.n_classes, **kw).to(device)
            sd = torch.load(ck, map_location=device, weights_only=False)
            sd = sd.get("model_state", sd) if isinstance(sd, dict) else sd
            model.load_state_dict(sd, strict=False)

            ms = per_patient_loss(model, full_ds, mem, device, cw)
            ns = per_patient_loss(model, full_ds, non, device, cw)
            auc = attack_auc(ms, ns)
            aucs.append(auc)
            rows.append({"dataset": a.dataset, "defence": unit, "seed": seed,
                         "attack_auc": auc,
                         "mean_loss_member": float(ms.mean()),
                         "mean_loss_nonmember": float(ns.mean()),
                         "loss_gap": float(ns.mean() - ms.mean())})
            print(f"  {label:<18} seed {seed}  attack AUC = {auc:.4f}"
                  f"   (loss gap {ns.mean()-ms.mean():+.4f})")
        if aucs:
            m = float(np.mean(aucs))
            sd_ = float(np.std(aucs, ddof=1)) if len(aucs) > 1 else 0.0
            print(f"  {label:<18} MEAN attack AUC = {m:.4f} ± {sd_:.4f}\n")

    out = a.output or str(_SIM / "results" / "phase5" / f"mia_{a.dataset}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if rows:
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    # ── verdict ─────────────────────────────────────────────────────
    import statistics as st
    by = {}
    for r in rows:
        by.setdefault(r["defence"], []).append(r["attack_auc"])
    if len(by) == 2:
        rec, pat = by.get("sample", []), by.get("patient", [])
        print("=" * 74)
        print("  VERDICT")
        print("=" * 74)
        print(f"    record-level DP  attack AUC {st.mean(rec):.4f}")
        print(f"    patient-level DP attack AUC {st.mean(pat):.4f}")
        print(f"    reduction        {st.mean(rec)-st.mean(pat):+.4f}")
        # NB: a verdict must not be read off ONE cell. An earlier version of the
        # factorial driver looked only at the unprotected full-model arm, saw
        # 0.5122, and concluded "the task does not memorise" — while the
        # head-only no-DP arm was leaking at 0.5847 (p=1e-09, sd 0.0018 over 6
        # runs). Memorisation here is a property of the RECIPE, not of the task,
        # and a single-cell test cannot see that.
        if st.mean(rec) > 0.55 and st.mean(pat) < 0.55:
            print("\n    => record-level DP leaks PATIENT membership;"
                  " patient-level DP closes it.")
        elif st.mean(rec) <= 0.55:
            print("\n    => neither leaks detectably at this budget. The"
                  " theoretical gap does not\n       materialise as an attack"
                  " here — report that honestly; it does not\n       invalidate"
                  " the guarantee argument, but it does weaken the"
                  " motivation.")
        else:
            print("\n    => both leak. Patient-level DP is not sufficient at"
                  " this budget.")
    print(f"\nWritten: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
