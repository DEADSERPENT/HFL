"""
preprocess_wear.py — WEAR → HFL-MM pipeline arrays.

WEAR (Bock et al., IMWUT 2024, DOI 10.1145/3699776) is an outdoor-sports dataset
of 22 participants performing 18 workout activities, recorded with FOUR 3D
accelerometers (left/right wrist + left/right ankle, 50 Hz) and a head-mounted
egocentric camera (1080p@60fps). The two streams are HARDWARE-SYNCHRONISED, so
there is no pairing rule to defend — a
window's inertial samples and its video features describe the same instant of
the same person.

Licence: CC BY-NC-SA 4.0 (non-commercial research use, attribution required).

Why this shape
--------------
* Inertial gives 4 sensors × 3 axes = **12 channels**, matching the existing
  `encoder_a` input contract exactly (it accepts any window length: 12×100 and
  12×1000 both pool to 256-d).
* Video uses the dataset's official I3D features at `120_frames_60_stride`
  @60fps = a 2 s window every 1 s — i.e. the same 2 s/50 %-overlap grid the
  inertial windows use. Alignment is therefore exact by construction (verified:
  i3d_windows / inertial_seconds = 0.999–1.000 for all 22 subjects).
  Using the published feature representation also keeps us directly comparable
  to WEAR's own reported baselines.

Leakage control
---------------
Windows overlap by 50 %, so a RANDOM split would put two windows sharing one
second of signal on both sides. But a split by wall-clock time over the whole
recording is LABEL-DISJOINT: subjects perform the 18 activities in sequence, so
the last 15 % of time holds only the final 3-4 activities.

Splits are therefore temporal **within each (subject, activity) group**, with a
1-window gap dropped at each boundary. That keeps every class in every split
AND removes the shared second. Normalisation statistics are TRAIN-ONLY and
nan-aware (see the sbj_10 dropout note below).

Output (the layout the FL stack expects):
    data/processed/wear/
        inertial/inertial_windows.npy   (N, 12, W)  float32
        inertial/labels.npy             (N,)        int64
        video/i3d_features.npy          (N, 2048)   float32
        meta/subject_ids.npy            (N,)        int64
        meta/{label_names.json, norm_stats.json, dataset_meta.json}
    data/processed/partitions/wear/
        device_XX_{train,val,test}.npy  + partition_meta.json
"""

import os
import re
import json
import glob
import argparse
from collections import Counter

import numpy as np
import pandas as pd

ACC_COLS = [
    "right_arm_acc_x", "right_arm_acc_y", "right_arm_acc_z",
    "right_leg_acc_x", "right_leg_acc_y", "right_leg_acc_z",
    "left_leg_acc_x",  "left_leg_acc_y",  "left_leg_acc_z",
    "left_arm_acc_x",  "left_arm_acc_y",  "left_arm_acc_z",
]
SAMPLE_RATE = 50          # Hz, inertial
I3D_STRIDE_S = 1.0        # one I3D row per second (120 frames @60fps, stride 60)


def _sbj_num(path: str) -> int:
    return int(re.findall(r"\d+", os.path.basename(path))[0])


def build_windows(inertial_dir: str, i3d_dir: str, window_s: float,
                  min_labelled_frac: float):
    """Cut each subject into aligned (inertial-window, i3d-row, label) triples."""
    win = int(window_s * SAMPLE_RATE)              # inertial samples per window
    stride = int(I3D_STRIDE_S * SAMPLE_RATE)       # 1 s hop → 50 % overlap at 2 s

    inertial_files = sorted(glob.glob(os.path.join(inertial_dir, "sbj_*.csv")),
                            key=_sbj_num)
    X_in, X_v, Y, S = [], [], [], []
    label_set, per_subject = set(), {}

    for ip in inertial_files:
        s = _sbj_num(ip)
        vp = os.path.join(i3d_dir, f"sbj_{s}.npy")
        if not os.path.exists(vp):
            print(f"  [skip] sbj_{s}: no I3D features")
            continue

        df = pd.read_csv(ip, low_memory=False)
        acc = df[ACC_COLS].to_numpy(dtype=np.float32)          # (T, 12)
        lab = df["label"].to_numpy(dtype=object)
        i3d = np.load(vp).astype(np.float32)                   # (Wv, 2048)

        n = 0
        for w_idx in range(len(i3d)):
            a, b = w_idx * stride, w_idx * stride + win
            if b > len(acc):
                break
            seg = lab[a:b]
            valid = [v for v in seg if isinstance(v, str)]
            if len(valid) / win < min_labelled_frac:
                continue                                       # mostly NULL → drop
            top, cnt = Counter(valid).most_common(1)[0]
            if cnt / len(valid) < 0.5:
                continue                                       # ambiguous boundary
            X_in.append(acc[a:b].T)                            # (12, win)
            X_v.append(i3d[w_idx])
            Y.append(top); S.append(s)
            label_set.add(top); n += 1
        per_subject[s] = n
        print(f"  sbj_{s:<3} inertial={len(acc)/SAMPLE_RATE:8.1f}s  i3d={len(i3d):5d}  windows={n:5d}")

    names = sorted(label_set)
    idx = {c: i for i, c in enumerate(names)}
    return (np.stack(X_in), np.stack(X_v),
            np.array([idx[y] for y in Y], dtype=np.int64),
            np.array(S, dtype=np.int64), names, per_subject)


def temporal_split(subject_ids, labels, train=0.70, val=0.15, gap=1):
    """
    Split by TIME **within each (subject, activity) group**.

    Two failure modes this avoids:

    1. A RANDOM split leaks: windows overlap 50 %, so two windows sharing one
       second of signal would land on opposite sides.

    2. A split by wall-clock time over the whole recording is LABEL-DISJOINT.
       Subjects perform the 18 activities in sequence (~20 contiguous blocks),
       so the last 15 % of time contains only the final 3-4 activities. That
       produced validation sets holding 3-4 of 18 classes, an undefined macro
       AUC, and 2 % accuracy — while still "training" without error.

    Splitting within each (subject, label) group keeps every class in every
    split and preserves time order inside the group. `gap` windows are dropped
    at each boundary so the second shared across it belongs to neither side.
    """
    tr, va, te = [], [], []
    for s in np.unique(subject_ids):
        s_tr, s_va, s_te = [], [], []
        s_mask = subject_ids == s
        for c in np.unique(labels[s_mask]):
            idx = np.where(s_mask & (labels == c))[0]      # time-ordered
            n = len(idx)
            if n < 3 * (gap + 1):                          # too small to split
                s_tr.append(idx)
                continue
            a, b = int(n * train), int(n * (train + val))
            s_tr.append(idx[:max(a - gap, 1)])
            s_va.append(idx[a:max(b - gap, a + 1)])
            s_te.append(idx[b:])
        tr.append(np.concatenate(s_tr) if s_tr else np.array([], dtype=int))
        va.append(np.concatenate(s_va) if s_va else np.array([], dtype=int))
        te.append(np.concatenate(s_te) if s_te else np.array([], dtype=int))
    return tr, va, te


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw_dir", default="data/raw/wear")
    p.add_argument("--out_dir", default="data/processed/wear")
    p.add_argument("--partition_dir", default="data/processed/partitions/wear")
    p.add_argument("--window_s", type=float, default=2.0)
    p.add_argument("--min_labelled_frac", type=float, default=0.5,
                   help="Drop windows whose labelled fraction is below this")
    p.add_argument("--n_edges", type=int, default=2,
                   help="Edge gateways in the 3-layer hierarchy")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    print("=" * 70)
    print("  WEAR → HFL-MM preprocessing")
    print("  Bock et al., IMWUT 2024 · CC BY-NC-SA 4.0 · hardware-synchronised")
    print("=" * 70)

    Xi, Xv, y, sids, names, per_sub = build_windows(
        os.path.join(args.raw_dir, "inertial_50hz"),
        os.path.join(args.raw_dir, "i3d_120f_60s"),
        args.window_s, args.min_labelled_frac)

    print(f"\n  windows={len(y):,}  inertial={Xi.shape}  i3d={Xv.shape}  classes={len(names)}")

    tr, va, te = temporal_split(sids, y)
    train_idx = np.concatenate(tr)

    # ---- normalise with TRAIN-ONLY statistics ---------------------------
    # NAN-AWARE, and this matters: sbj_10 has a genuine 25.8 % dropout on
    # left_arm_acc_x. With plain np.mean, that single subject's gap makes the
    # channel statistic NaN, which then propagates to ALL windows of ALL
    # subjects — silently destroying one of the four sensors (25 % of the
    # input) while training still "runs" and reports an accuracy.
    n_nan_before = int(np.isnan(Xi).sum())
    m_i = np.nanmean(Xi[train_idx], axis=(0, 2), keepdims=True)
    s_i = np.nanstd(Xi[train_idx],  axis=(0, 2), keepdims=True) + 1e-8
    Xi = ((Xi - m_i) / s_i).astype(np.float32)
    m_v = np.nanmean(Xv[train_idx], 0, keepdims=True)
    s_v = np.nanstd(Xv[train_idx],  0, keepdims=True) + 1e-8
    Xv = ((Xv - m_v) / s_v).astype(np.float32)

    # Residual gaps -> 0.0, which AFTER z-scoring is exactly the channel mean,
    # i.e. "no information" rather than a fabricated reading. Done after
    # normalisation so the zero carries that meaning; doing it before would
    # bias the statistics toward zero.
    nan_frac = float(np.isnan(Xi).mean())
    Xi = np.nan_to_num(Xi, nan=0.0).astype(np.float32)
    Xv = np.nan_to_num(Xv, nan=0.0).astype(np.float32)
    print(f"\n  sensor dropout: {n_nan_before:,} NaN samples "
          f"({nan_frac*100:.2f}% of values) imputed to channel mean")

    for sub in ("inertial", "video", "meta"):
        os.makedirs(os.path.join(args.out_dir, sub), exist_ok=True)
    os.makedirs(args.partition_dir, exist_ok=True)
    # Remove stale device_*.npy from an earlier run with a different client
    # count. Without this, reducing the number of clients leaves orphaned
    # device_NN files behind that the verifier (rightly) flags and that a
    # later run could silently pick up.
    for _old in glob.glob(os.path.join(args.partition_dir, "device_*.npy")):
        os.remove(_old)

    np.save(f"{args.out_dir}/inertial/inertial_windows.npy", Xi)
    np.save(f"{args.out_dir}/inertial/labels.npy", y)
    np.save(f"{args.out_dir}/video/i3d_features.npy", Xv)
    np.save(f"{args.out_dir}/meta/subject_ids.npy", sids)
    json.dump(names, open(f"{args.out_dir}/meta/label_names.json", "w"), indent=2)
    json.dump({"inertial_mean": m_i.ravel().tolist(), "inertial_std": s_i.ravel().tolist(),
               "i3d_mean_first16": m_v.ravel()[:16].tolist(),
               "note": "statistics computed on TRAIN windows only"},
              open(f"{args.out_dir}/meta/norm_stats.json", "w"), indent=2)

    subs = np.unique(sids)
    for d, s in enumerate(subs):
        np.save(f"{args.partition_dir}/device_{d:02d}_train.npy", tr[d])
        np.save(f"{args.partition_dir}/device_{d:02d}_val.npy",   va[d])
        np.save(f"{args.partition_dir}/device_{d:02d}_test.npy",  te[d])

    # Edge assignment for the 3-layer hierarchy (device → edge → cloud).
    # hfl_trainer.py reads n_edges and edge_assignments from this file, so they
    # must be written here even though the split itself is per-device.
    # Contiguous balanced blocks: subjects carry no ordering meaning in WEAR.
    edge_assignments = {e: [] for e in range(args.n_edges)}
    for d in range(len(subs)):
        edge_assignments[d % args.n_edges].append(d)

    # Per-device block. hfl_trainer.py reads meta["devices"][str(d)]["n_train"]
    # to size DP sampling rates, so this schema is shared by every dataset.
    device_to_edge = {d: e for e, ds in edge_assignments.items() for d in ds}
    devices_meta = {}
    for d in range(len(subs)):
        devices_meta[str(d)] = {
            "edge_id": int(device_to_edge[d]),
            "n_train": int(len(tr[d])), "n_val": int(len(va[d])),
            "n_test": int(len(te[d])),
            "total": int(len(tr[d]) + len(va[d]) + len(te[d])),
            "class_distribution": {
                str(c): int(n) for c, n in
                sorted(Counter(y[np.concatenate([tr[d], va[d], te[d]])].tolist()).items())
            },
        }

    meta = {
        "dataset": "WEAR", "citation": "Bock et al., IMWUT 2024, 10.1145/3699776",
        "licence": "CC BY-NC-SA 4.0", "pairing": "hardware-synchronised (no pairing rule)",
        "domain": "wearable_iot", "seed": args.seed,
        "total_samples": int(len(y)),
        # Windows deliberately excluded from every split: 1 dropped at each
        # side of each (subject,activity) boundary so the second shared by
        # 50%-overlapping windows belongs to neither side. Recorded so the
        # verifier can tell "excluded by design" from "silently lost".
        "n_excluded_boundary": int(len(y) - sum(len(x) for x in tr)
                                   - sum(len(x) for x in va)
                                   - sum(len(x) for x in te)),
        "n_devices": int(len(subs)), "n_classes": len(names),
        "n_edges": args.n_edges,
        "edge_assignments": {str(k): v for k, v in edge_assignments.items()},
        "devices": devices_meta,
        "window_s": args.window_s, "stride_s": I3D_STRIDE_S,
        "inertial_shape": list(Xi.shape), "i3d_shape": list(Xv.shape),
        "split": "temporal within (subject,activity) 70/15/15, 1-window gap (overlap-safe, class-complete)",
        "class_counts": {names[k]: int(v) for k, v in
                         sorted(Counter(y.tolist()).items())},
        "windows_per_subject": {str(k): v for k, v in per_sub.items()},
    }
    json.dump(meta, open(f"{args.partition_dir}/partition_meta.json", "w"), indent=2)
    json.dump(meta, open(f"{args.out_dir}/meta/dataset_meta.json", "w"), indent=2)

    print(f"\n  devices={len(subs)}  train={sum(len(x) for x in tr):,}"
          f"  val={sum(len(x) for x in va):,}  test={sum(len(x) for x in te):,}")
    print("\n  class distribution:")
    for k, v in sorted(Counter(y.tolist()).items()):
        print(f"    {names[k]:<32}{v:>7,}")
    print(f"\n[SAVED] {args.out_dir}  and  {args.partition_dir}")


if __name__ == "__main__":
    main()
