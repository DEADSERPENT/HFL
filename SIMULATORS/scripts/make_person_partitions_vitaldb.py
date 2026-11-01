"""make_person_partitions_vitaldb.py — person-level VitalDB partitions.

The VitalDB partitions were built by SURGICAL CASE. A person operated on more
than once can therefore sit in two splits (train and test) or on two clients
(two specialties), which breaks two assumptions of the paper: person-disjoint
evaluation, and parallel composition over clients (every individual on one
client). This script derives a person-level variant from the existing case
partitions with deterministic, documented rules:

  1. split:  a person belongs to train if any case of theirs is in train, else
             to test if any is in test, else to val (priority train>test>val).
             Their cases in any other split are DROPPED, never moved.
  2. client: a person belongs to the client holding most of their cases in
             their split; ties go to the client of their lowest caseid. Cases
             on other clients are DROPPED, never moved, because a client is a
             surgical specialty and moving a case would mislabel it.

The existing split is refined rather than redrawn so that the test set stays a
subset of the original test set: the oracle encoders were pretrained on the
original training cases, and a fresh split would place some of them in test.

Writes
  data/processed/vitaldb_person/          signals/, clinical/ -> symlinks to
                                          vitaldb; meta/case_ids.npy = PERSON
                                          id per window (the DP unit and split
                                          key); meta/surgical_case_ids.npy =
                                          the original case ids (metric groups)
  data/processed/partitions/vitaldb_person/  device_XX_{train,val,test}.npy,
                                          partition_meta.json
  results/phase5/vitaldb_person/partition_report.json   counts only

    python SIMULATORS/scripts/make_person_partitions_vitaldb.py
"""
import glob
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "data" / "loaders"))
from datasets import get_spec  # noqa: E402

SRC, DST = get_spec("vitaldb"), get_spec("vitaldb_person")
RAW = SIM / "data" / "raw" / "vitaldb" / "clinical_data.csv"
SPLITS = ("train", "test", "val")          # priority order of rule 1
REPORT = SIM / "results" / "phase5" / "vitaldb_person" / "partition_report.json"
PERSON_SPLIT = ("by PERSON (subjectid): each person in one split and one client; "
                "refines the case-level split, other-split/other-client cases dropped")


def main():
    src_data, dst_data = SIM / SRC.data_dir, SIM / DST.data_dir
    src_part, dst_part = SIM / SRC.partition_dir, SIM / DST.partition_dir
    case = np.load(src_data / "meta" / "case_ids.npy")
    labels = np.load(src_data / "signals" / "labels.npy", mmap_mode="r")
    cl = pd.read_csv(RAW, usecols=["caseid", "subjectid"])
    subj_of = dict(zip(cl.caseid.astype(int), cl.subjectid.astype(int)))
    missing = set(np.unique(case).tolist()) - set(subj_of)
    if missing:
        sys.exit(f"[FATAL] {len(missing)} cases have no subjectid in {RAW}")
    person = np.array([subj_of[int(c)] for c in case], dtype=np.int64)

    meta = json.load(open(src_part / "partition_meta.json"))
    n_dev = meta["n_devices"]
    part = {(d, s): np.load(src_part / f"device_{d:02d}_{s}.npy")
            for d in range(n_dev) for s in SPLITS}

    # where each case sits (a case is in exactly one device and split)
    case_loc = {}
    for (d, s), idx in part.items():
        for c in np.unique(case[idx]).tolist():
            if c in case_loc and case_loc[c] != (d, s):
                sys.exit(f"[FATAL] case {c} in two partitions")
            case_loc[c] = (d, s)
    cases_of = defaultdict(list)
    for c, loc in case_loc.items():
        cases_of[subj_of[c]].append(c)

    # rule 1 then rule 2
    home = {}
    for p, cs in cases_of.items():
        s = next(s for s in SPLITS if any(case_loc[c][1] == s for c in cs))
        in_s = sorted(c for c in cs if case_loc[c][1] == s)
        cnt = Counter(case_loc[c][0] for c in in_s)
        top = max(cnt.values())
        d = case_loc[min(c for c in in_s if cnt[case_loc[c][0]] == top)][0]
        home[p] = (d, s)
    keep_case = {c for c, loc in case_loc.items() if home[subj_of[c]] == loc}

    # write data dir: symlink the arrays, person ids as the unit
    (dst_data / "meta").mkdir(parents=True, exist_ok=True)
    for sub in ("signals", "clinical"):
        link = dst_data / sub
        if not link.exists():
            os.symlink(os.path.relpath(src_data / sub, dst_data), link)
    for f in glob.glob(str(src_data / "meta" / "*")):
        if not f.endswith("case_ids.npy"):
            shutil.copy2(f, dst_data / "meta")
    np.save(dst_data / "meta" / "case_ids.npy", person)
    np.save(dst_data / "meta" / "surgical_case_ids.npy", case)
    dm_path = dst_data / "meta" / "dataset_meta.json"
    dm = json.load(open(dm_path))
    dm["split"] = PERSON_SPLIT
    json.dump(dm, open(dm_path, "w"), indent=2)

    # write partitions
    dst_part.mkdir(parents=True, exist_ok=True)
    new = {}
    for (d, s), idx in part.items():
        new[(d, s)] = idx[np.isin(case[idx], list(keep_case))]
        np.save(dst_part / f"device_{d:02d}_{s}.npy", new[(d, s)])
    for d in range(n_dev):
        m = meta["devices"][str(d)]
        n = {s: len(new[(d, s)]) for s in SPLITS}
        allidx = np.concatenate([new[(d, s)] for s in SPLITS])
        y = np.asarray(labels[np.sort(allidx)]).astype(int)
        m.update(n_train=n["train"], n_val=n["val"], n_test=n["test"],
                 total=int(len(allidx)), n_cases=int(len(np.unique(case[allidx]))),
                 n_persons=int(len(np.unique(person[allidx]))),
                 icu_rate_pct=round(100 * float(np.mean(
                     [labels[np.flatnonzero(case == c)[0]] for c in
                      np.unique(case[allidx])])), 2),
                 class_distribution={str(k): int(v) for k, v in
                                     zip(*np.unique(y, return_counts=True))})
    meta["total_samples"] = int(sum(len(v) for v in new.values()))
    meta["n_cases"] = len(keep_case)
    meta["unit"] = "person (subjectid); derived by make_person_partitions_vitaldb.py"
    meta["split"] = PERSON_SPLIT
    json.dump(meta, open(dst_part / "partition_meta.json", "w"), indent=2)

    # verify: every person in one split and one client
    loc_of = defaultdict(set)
    for (d, s), idx in new.items():
        for p in np.unique(person[idx]).tolist():
            loc_of[p].add((d, s))
    bad = [p for p, l in loc_of.items() if len(l) > 1]
    if bad:
        sys.exit(f"[FATAL] {len(bad)} persons still span partitions")

    def stats(parts, unit):
        out = {}
        for s in SPLITS:
            idx = np.concatenate([parts[(d, s)] for d in range(n_dev)])
            out[s] = {"windows": int(len(idx)),
                      "cases": int(len(np.unique(case[idx]))),
                      "persons": int(len(np.unique(person[idx])))}
        return out

    def overlap(parts):
        P = {s: set(np.unique(person[np.concatenate(
            [parts[(d, s)] for d in range(n_dev)])]).tolist()) for s in SPLITS}
        dev = defaultdict(set)
        for (d, s), idx in parts.items():
            if s == "train":
                for p in np.unique(person[idx]).tolist():
                    dev[p].add(d)
        return {"train_test": len(P["train"] & P["test"]),
                "train_val": len(P["train"] & P["val"]),
                "val_test": len(P["val"] & P["test"]),
                "train_persons_on_several_clients": sum(len(v) > 1 for v in dev.values())}

    dropped = set(case_loc) - keep_case
    kk = Counter(subj_of[c] for c in keep_case if home[subj_of[c]][1] == "train")
    report = {
        "rules": {"split": "priority train > test > val; other-split cases dropped",
                  "client": "client with most of the person's cases in their split; "
                            "tie -> client of lowest caseid; other-client cases dropped"},
        "before": {"splits": stats(part, "case"), "person_overlap": overlap(part)},
        "after": {"splits": stats(new, "person"), "person_overlap": overlap(new)},
        "cases_dropped": len(dropped),
        "cases_dropped_by_split": dict(Counter(case_loc[c][1] for c in dropped)),
        "windows_dropped": int(sum(len(v) for v in part.values())
                               - sum(len(v) for v in new.values())),
        "train_persons_with_several_cases": int(sum(v > 1 for v in kk.values())),
        "train_max_cases_per_person": int(max(kk.values())),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(report, open(REPORT, "w"), indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
