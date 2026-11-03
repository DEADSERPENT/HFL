"""make_a1_partition_eicu.py — eICU partition in which every individual is held
by exactly one client (assumption (A1) of Theorem 1).

Why. In the original partition clients are hospitals (`hospitalid`) and the
privacy unit is the individual (`uniquepid`). 2,177 training individuals have
stays at two to four hospitals, so their records sit on several clients and
their guarantee is the composition of those clients' mechanisms, not the
per-client budget (audit 2026-11-02, FINAL_AUDIT_2026-11-02.md, B4).

What. Starting from the registry partition, every individual whose records
(in their one split) lie on more than one client is moved, with ALL of their
records, to a single client: the one holding most of their stays; ties go to
the client holding most of their windows, then to the lowest client index.
Nothing is excluded: every record keeps its split, the public pretraining pool
(`public_indices.npy`) is copied unchanged, client count, edge map and split
membership are unchanged. Only which client holds the moved records changes.

Fail-closed checks before anything is written:
  * every individual is on exactly one client and in exactly one split
  * the multiset of records per split is identical to the source
  * no record is on two clients; the public pool is disjoint from every client
    and no pool individual is in a training split
  * no client loses all its training records or all its positive training
    labels (11 source clients already have none; that is not changed)

Output: <registry partition_dir>_a1/ with device_XX_{train,val,test}.npy,
partition_meta.json (recomputed device statistics + an `a1_reassignment`
block with the source hashes and what moved), public pool files copied.

    python scripts/make_a1_partition_eicu.py [--dataset eicu] [--dry_run]
"""
import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "data" / "loaders"))
from datasets import get_spec  # noqa: E402

SPLITS = ("train", "val", "test")


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def fail(msg: str):
    raise SystemExit(f"[FAIL] {msg}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="eicu")
    ap.add_argument("--suffix", default="_a1")
    ap.add_argument("--dry_run", action="store_true")
    a = ap.parse_args()

    spec = get_spec(a.dataset)
    src = SIM / spec.partition_dir
    dst = SIM / (spec.partition_dir + a.suffix)
    data = SIM / spec.data_dir
    meta = json.loads((src / "partition_meta.json").read_text())
    n_dev = meta["n_devices"]
    if n_dev != spec.n_devices:
        fail(f"partition has {n_dev} devices, registry says {spec.n_devices}")

    pid = np.load(data / "meta" / "case_ids.npy")          # individual (uniquepid)
    stay = np.load(data / "meta" / "stay_ids.npy")
    lab_rel = next(k for k in spec.required_files if "label" in k)
    y = np.load(data / lab_rel)

    part = {(d, s): np.load(src / f"device_{d:02d}_{s}.npy")
            for d in range(n_dev) for s in SPLITS}

    # ---- source state ------------------------------------------------------
    owners = {s: defaultdict(Counter) for s in SPLITS}      # pid -> client -> windows
    stays = {s: defaultdict(lambda: defaultdict(set)) for s in SPLITS}
    split_of = {}
    for (d, s), idx in part.items():
        for p, st in zip(pid[idx].tolist(), stay[idx].tolist()):
            owners[s][p][d] += 1
            stays[s][p][d].add(st)
            if split_of.setdefault(p, s) != s:
                fail(f"source partition: individual {p} spans splits {split_of[p]} and {s}")

    # ---- choose one client per individual -----------------------------------
    target = {s: {} for s in SPLITS}
    moved = {s: {"individuals": 0, "records": 0, "by_m": Counter()} for s in SPLITS}
    for s in SPLITS:
        for p, cnt in owners[s].items():
            if len(cnt) == 1:
                target[s][p] = next(iter(cnt))
                continue
            best = min(cnt, key=lambda d: (-len(stays[s][p][d]), -cnt[d], d))
            target[s][p] = best
            moved[s]["individuals"] += 1
            moved[s]["by_m"][len(cnt)] += 1
            moved[s]["records"] += sum(v for d, v in cnt.items() if d != best)

    # ---- build new device index arrays --------------------------------------
    new = {}
    for s in SPLITS:
        allidx = np.concatenate([part[(d, s)] for d in range(n_dev)])
        tgt = np.array([target[s][p] for p in pid[allidx].tolist()])
        for d in range(n_dev):
            new[(d, s)] = np.sort(allidx[tgt == d]).astype(part[(0, s)].dtype)

    # ---- fail-closed verification -------------------------------------------
    for s in SPLITS:
        before = np.sort(np.concatenate([part[(d, s)] for d in range(n_dev)]))
        after = np.sort(np.concatenate([new[(d, s)] for d in range(n_dev)]))
        if not np.array_equal(before, after):
            fail(f"{s}: record multiset changed")
        if len(np.unique(after)) != len(after):
            fail(f"{s}: a record is on two clients")
    seen = {}
    for (d, s), idx in new.items():
        for p in np.unique(pid[idx]).tolist():
            if (p in seen) and seen[p] != (d, s):
                fail(f"individual {p} on {seen[p]} and {(d, s)}")
            seen[p] = (d, s)
    pub_path = src / "public_indices.npy"
    if pub_path.exists():
        pub = np.load(pub_path)
        allc = np.concatenate(list(new.values()))
        if np.intersect1d(pub, allc).size:
            fail("public pool overlaps client records")
        train_p = set(np.unique(pid[np.concatenate([new[(d, 'train')] for d in range(n_dev)])]).tolist())
        if set(np.unique(pid[pub]).tolist()) & train_p:
            fail("a public-pool individual is in the training split")
    # Inclusion criteria are those of the source partition (some clients have
    # no positive TRAINING label there already); the reassignment must not
    # create a new empty or label-free client.
    for d in range(n_dev):
        tr, tr0 = new[(d, "train")], part[(d, "train")]
        if tr.size == 0 and tr0.size > 0:
            fail(f"client {d} lost all training records")
        if not (y[tr] == 1).any() and (y[tr0] == 1).any():
            fail(f"client {d} lost its only positive training labels")

    # ---- statistics -----------------------------------------------------------
    devices = {}
    size_change = []
    for d in range(n_dev):
        old = meta["devices"][str(d)]
        n = {s: int(new[(d, s)].size) for s in SPLITS}
        allidx = np.concatenate([new[(d, s)] for s in SPLITS])
        cls = Counter(y[allidx].tolist())
        devices[str(d)] = dict(old, n_train=n["train"], n_val=n["val"], n_test=n["test"],
                               total=int(allidx.size),
                               n_patients=int(np.unique(pid[allidx]).size),
                               mortality_rate_pct=round(100 * cls.get(1, 0) / max(allidx.size, 1), 2),
                               class_distribution={str(k): int(v) for k, v in sorted(cls.items())})
        size_change.append(n["train"] - int(old["n_train"]))
    train_pat = [len(np.unique(pid[new[(d, 'train')]])) for d in range(n_dev)]
    old_train_pat = [len(np.unique(pid[part[(d, 'train')]])) for d in range(n_dev)]
    sc = np.array(size_change)
    report = {
        "rule": "each individual moved with all records to the client holding most of "
                "their stays (ties: most windows, then lowest index); splits, records, "
                "public pool, client count and edge map unchanged; nothing excluded",
        "source_partition": str(src.relative_to(SIM)),
        "source_partition_meta_md5": md5(src / "partition_meta.json"),
        "moved": {s: {"individuals": v["individuals"], "records": v["records"],
                      "by_original_client_count": {str(k): c for k, c in sorted(v["by_m"].items())}}
                  for s, v in moved.items()},
        "clients_with_changed_train_size": int((sc != 0).sum()),
        "train_records_change_min_max": [int(sc.min()), int(sc.max())],
        "train_individuals_per_client_before_min_median_max":
            [int(min(old_train_pat)), float(np.median(old_train_pat)), int(max(old_train_pat))],
        "train_individuals_per_client_after_min_median_max":
            [int(min(train_pat)), float(np.median(train_pat)), int(max(train_pat))],
        "individuals_on_more_than_one_client_after": 0,
    }
    print(json.dumps(report, indent=1))
    if a.dry_run:
        print("[dry run] nothing written")
        return 0

    if dst.exists():
        fail(f"{dst} exists; refusing to overwrite")
    dst.mkdir(parents=True)
    for (d, s), idx in new.items():
        np.save(dst / f"device_{d:02d}_{s}.npy", idx)
    for f in ("public_indices.npy", "public_split_meta.json"):
        if (src / f).exists():
            shutil.copy2(src / f, dst / f)
    out = dict(meta, devices=devices, a1_reassignment=report)
    (dst / "partition_meta.json").write_text(json.dumps(out, indent=2))
    print(f"[ok] wrote {dst.relative_to(SIM)} ({len(new)} index files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
