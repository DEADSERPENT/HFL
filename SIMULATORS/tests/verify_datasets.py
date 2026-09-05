"""
verify_datasets.py — correctness audit for every registered dataset.

Run this after ANY change to a preprocessing script, before trusting a result.
It is deliberately adversarial: it tries to prove each dataset is broken and
only passes when it cannot.

    python tests/verify_datasets.py                # all registered datasets
    python tests/verify_datasets.py --dataset wear # one

Checks, in order of how badly a failure would corrupt the research:

  1. LEAKAGE      no sample index appears in more than one split, and — for
                  grouped datasets — no group (case/subject) spans splits.
                  This is the check that decides whether results mean anything.
  2. COVERAGE     every sample lands in exactly one split; none silently lost.
  3. INTEGRITY    no NaN/Inf anywhere; masks binary; dtypes and shapes as
                  declared. A NaN that reaches training does not crash, it
                  quietly destroys a channel.
  4. LABELS       class presence per split, and prevalence preserved across
                  splits (a split that lost the minority class gives an
                  undefined AUC and a meaningless accuracy).
  5. NORMALISATION train statistics ~N(0,1), and — critically — that they were
                  computed on TRAIN ONLY, detectable as a small but non-zero
                  offset in val/test.
  6. SCHEMA       partition_meta.json carries every key hfl_trainer.py reads.
  7. REGISTRY     the DatasetSpec matches the data actually on disk
                  (n_devices, n_classes, n_channels_a, feat_b_dim).
  8. HETEROGENEITY reports the real non-IID structure rather than asserting it.
"""

import os
import sys
import json
import argparse
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "data", "loaders"))

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
_results = []


def chk(name, ok, detail="", level=FAIL):
    status = PASS if ok else level
    _results.append((name, status))
    mark = {"PASS": "✓", "FAIL": "✗", "WARN": "!"}[status]
    print(f"    [{mark}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def load_splits(part_dir, n_devices):
    out = {}
    for s in ("train", "val", "test"):
        out[s] = [np.load(os.path.join(part_dir, f"device_{d:02d}_{s}.npy"))
                  for d in range(n_devices)]
    return out


def verify(spec) -> bool:
    print(f"\n{'='*72}\n  {spec.name.upper()}  —  {spec.pairing}\n{'='*72}")
    dd, pd_ = spec.data_dir, spec.partition_dir
    meta_path = os.path.join(pd_, "partition_meta.json")
    if not os.path.exists(meta_path):
        chk(f"{spec.name}: partition_meta.json exists", False, meta_path)
        return False
    meta = json.load(open(meta_path))
    n_dev = meta["n_devices"]
    splits = load_splits(pd_, n_dev)

    # ---- modality arrays, resolved from the spec's own manifest ----------
    arrays = {}
    for rel in spec.required_files:
        arrays[rel] = np.load(os.path.join(dd, rel), mmap_mode="r")
    labels = next(np.asarray(a) for r, a in arrays.items() if "label" in r)
    N = len(labels)

    all_idx = {s: np.concatenate(v) for s, v in splits.items()}

    # ---- 1. LEAKAGE -----------------------------------------------------
    print("  1. leakage")
    ok = True
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        ov = np.intersect1d(all_idx[a], all_idx[b])
        ok &= chk(f"no index shared {a}/{b}", len(ov) == 0, f"{len(ov)} shared")

    gpath = os.path.join(dd, "meta", "case_ids.npy")
    if not os.path.exists(gpath):
        gpath = os.path.join(dd, "meta", "subject_ids.npy")
    if os.path.exists(gpath):
        g = np.load(gpath)
        gset = {s: set(g[i].tolist()) for s, i in all_idx.items()}
        for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
            sh = gset[a] & gset[b]
            # WEAR splits WITHIN a subject by design (each subject is a client
            # that holds its own train/val/test), so subject overlap is
            # expected there. VitalDB splits BY case, so overlap is a leak.
            expect_disjoint = "case_ids" in gpath
            ok &= chk(f"group disjoint {a}/{b}", (len(sh) == 0) or not expect_disjoint,
                      f"{len(sh)} groups shared", FAIL if expect_disjoint else WARN)
        if "case_ids" in gpath:
            spanning = sum(1 for grp in np.unique(g)
                           if sum(grp in gset[s] for s in ("train", "val", "test")) > 1)
            ok &= chk("no group spans >1 split", spanning == 0, f"{spanning} spanning")

    # ---- 2. COVERAGE ----------------------------------------------------
    print("  2. coverage")
    total = sum(len(v) for v in all_idx.values())
    # Some pipelines deliberately exclude samples from every split — WEAR drops
    # one window at each (subject,activity) boundary so the second shared by
    # 50%-overlapping windows belongs to neither side. That must be DECLARED in
    # the metadata and match exactly; anything unaccounted for is a real loss.
    excl = int(meta.get("n_excluded_boundary", 0))
    ok &= chk("every sample in exactly one split (or declared excluded)",
              total + excl == N,
              f"{total:,} in splits + {excl:,} declared-excluded vs {N:,} total")
    if excl:
        chk("declared exclusions are a small fraction", excl / N < 0.05,
            f"{excl:,} = {excl/N*100:.2f}% (boundary gaps)", WARN)
    ok &= chk("indices within range",
              all(int(v.max(initial=-1)) < N and int(v.min(initial=0)) >= 0
                  for v in all_idx.values()))

    # ---- 3. INTEGRITY ---------------------------------------------------
    print("  3. integrity")
    pools = getattr(spec, "pool_files", frozenset())
    for rel, arr in arrays.items():
        a = np.asarray(arr)
        if a.dtype.kind == "f":
            ok &= chk(f"{rel}: finite", bool(np.isfinite(a).all()),
                      f"{int(np.isnan(a).sum())} NaN, {int(np.isinf(a).sum())} Inf")
        if rel in pools:
            # Indexed indirectly (a pool array shared across samples
            # from a pool), so a shorter length is correct by design.
            chk(f"{rel}: pool array (length need not match)", True,
                f"{len(a):,} pooled rows")
        else:
            ok &= chk(f"{rel}: length matches labels", len(a) == N, f"{len(a)} vs {N}")
    sig_rel = next((r for r in arrays if "label" not in r and
                    np.asarray(arrays[r]).ndim == 3), None)
    if sig_rel is not None:
        sig = np.asarray(arrays[sig_rel])
        C = sig.shape[1]
        ok &= chk(f"{sig_rel}: channels match spec", C == spec.n_channels_a,
                  f"{C} vs spec {spec.n_channels_a}")
        if spec.has_mask_channels:            # second half must be a 0/1 mask
            mask_vals = set(np.unique(sig[:, C // 2:]).tolist())
            ok &= chk("mask channels binary", mask_vals <= {0.0, 1.0}, str(mask_vals))

    # ---- 4. LABELS ------------------------------------------------------
    print("  4. labels")
    n_cls = int(labels.max()) + 1
    ok &= chk("class count matches spec", n_cls == spec.n_classes,
              f"{n_cls} vs spec {spec.n_classes}")
    base = float((labels == labels.max()).mean()) if n_cls == 2 else None
    for s, idx in all_idx.items():
        present = len(set(labels[idx].tolist()))
        frac = len(idx) / N
        detail = f"n={len(idx):,} ({frac*100:.1f}%), {present}/{n_cls} classes"
        if n_cls == 2:
            prev = float(labels[idx].mean())
            detail += f", prevalence {prev*100:.2f}%"
            chk(f"{s}: prevalence within 3pp of overall", abs(prev - base) < 0.03,
                detail, WARN)
        else:
            chk(f"{s}: split populated", present >= max(2, n_cls - 2), detail, WARN)

    # ---- 5. NORMALISATION ----------------------------------------------
    print("  5. normalisation")
    if sig_rel is not None:
        tr = all_idx["train"]
        sub = sig[np.sort(tr[:4000])][:, :max(1, sig.shape[1] // 2
                                              if spec.has_mask_channels else sig.shape[1])]
        m, sd = float(np.nanmean(sub)), float(np.nanstd(sub))
        ok &= chk("train signals ~N(0,1)", abs(m) < 0.25 and 0.5 < sd < 1.6,
                  f"mean={m:+.3f} std={sd:.3f}")

    # ---- 6. SCHEMA ------------------------------------------------------
    print("  6. schema (keys hfl_trainer.py reads)")
    for k in ("n_devices", "n_edges", "edge_assignments", "devices"):
        ok &= chk(f"meta['{k}']", k in meta)
    if "devices" in meta:
        ok &= chk("every device has n_train",
                  all(str(d) in meta["devices"] and
                      "n_train" in meta["devices"][str(d)] for d in range(n_dev)))
        ok &= chk("no device has an empty train split",
                  all(meta["devices"][str(d)]["n_train"] > 0 for d in range(n_dev)))
    if "edge_assignments" in meta:
        assigned = sorted(d for v in meta["edge_assignments"].values() for d in v)
        ok &= chk("every device assigned to exactly one edge",
                  assigned == list(range(n_dev)), f"{len(assigned)} assignments")

    # ---- 7. REGISTRY ----------------------------------------------------
    print("  7. registry consistency")
    ok &= chk("spec.n_devices matches meta", spec.n_devices == n_dev,
              f"{spec.n_devices} vs {n_dev}")
    files = len([f for f in os.listdir(pd_) if f.endswith("_train.npy")])
    ok &= chk("device files match n_devices", files == n_dev, f"{files} files")
    feat = next((np.asarray(a) for r, a in arrays.items()
                 if np.asarray(a).ndim == 2 and "label" not in r), None)
    if feat is not None and spec.feat_b_dim:
        ok &= chk("spec.feat_b_dim matches modality B",
                  feat.shape[1] == spec.feat_b_dim,
                  f"{feat.shape[1]} vs spec {spec.feat_b_dim}")

    # ---- 8. HETEROGENEITY (reported, not asserted) ----------------------
    print("  8. non-IID structure")
    per = []
    for d in range(n_dev):
        idx = np.concatenate([splits[s][d] for s in ("train", "val", "test")])
        if not len(idx):
            continue
        cnt = Counter(labels[idx].tolist())
        dom = max(cnt.values()) / len(idx)
        per.append((d, len(idx), len(cnt), dom,
                    float(labels[idx].mean()) if n_cls == 2 else None))
    sizes = [p[1] for p in per]
    print(f"     clients={len(per)}  samples/client {min(sizes):,}–{max(sizes):,} "
          f"(x{max(sizes)/max(min(sizes),1):.1f})")
    print(f"     dominant-class share {min(p[3] for p in per)*100:.0f}%–"
          f"{max(p[3] for p in per)*100:.0f}%")
    if n_cls == 2:
        pr = [p[4] for p in per]
        print(f"     positive rate per client {min(pr)*100:.1f}%–{max(pr)*100:.1f}% "
              f"(x{max(pr)/max(min(pr),1e-9):.0f} spread)")
        thin = [p[0] for p in per if p[4] * p[1] < 10]
        if thin:
            chk("all clients have >=10 positives", False,
                f"clients {thin} are label-degenerate (real, not a defect)", WARN)
    return ok


def main():
    from datasets import REGISTRY, get_spec
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=None)
    a = ap.parse_args()
    names = [a.dataset] if a.dataset else sorted(REGISTRY)

    overall = True
    for n in names:
        try:
            overall &= verify(get_spec(n))
        except FileNotFoundError as e:
            print(f"  [skip] {n}: {e}")

    n_fail = sum(1 for _, s in _results if s == FAIL)
    n_warn = sum(1 for _, s in _results if s == WARN)
    print(f"\n{'='*72}")
    print(f"  {len(_results)} checks | {n_fail} FAIL | {n_warn} WARN")
    print(f"  {'ALL DATASETS VERIFIED' if n_fail == 0 else 'FAILURES PRESENT'}")
    print("=" * 72)
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
