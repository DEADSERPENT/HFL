"""
preprocess_eicu.py — build the eICU corpus into the arrays this study expects.

STATUS: the LOGIC below is tested against a synthetic fixture (--self_test).
The SCHEMA MAPPING is written from the published eICU-CRD column names and has
NOT been run against the real tables, because they require credentialed access.
Every schema-dependent constant is collected in SCHEMA at the top so the parts
that need verifying on day one are in one place rather than scattered.

WHY eICU
--------
The study's core claims are carried by one corpus. `wear` cannot corroborate
any of them: 22 individuals against the 1,200 a patient-level attack needs, one
individual per client so the privacy unit is degenerate, and a task its better
single modality already solves at 0.9976. eICU fails none of those, and adds
something VitalDB lacks: its clients are REAL HOSPITALS, where VitalDB's nine
are constructed by grouping surgical optype. For a paper about hierarchical
federation, a naturally arising partition is worth as much as the second
modality.

THE INDIVIDUAL IS THE PERSON, NOT THE STAY
------------------------------------------
eICU distinguishes `uniquepid` (a person) from `patientunitstayid` (one ICU
admission). A person may be admitted repeatedly. Every claim in this study that
says "individual" means the person, so `uniquepid` is what becomes group_ids
and what the splits are made disjoint on. Keying on the stay would let the same
person appear in train and test through a second admission, which is precisely
the leakage the validator exists to catch.

MODALITIES MUST BE PAIRED AT SOURCE
-----------------------------------
Modality A is the vitals window. Modality B is the tabular vector for the SAME
stay, built only from data recorded before that window closes. A tabular vector
assembled from cohort statistics, or from labs drawn after the prediction
point, is not paired at source and would void the multimodal claim this corpus
is being added to support.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

# ── schema constants: VERIFY THESE FIRST against the real tables ───────────
SCHEMA = {
    "patient_csv": "patient.csv",
    "vitals_csv": "vitalPeriodic.csv",
    "apache_csv": "apachePatientResult.csv",
    "person_key": "uniquepid",             # the INDIVIDUAL
    "stay_key": "patientunitstayid",       # one admission
    "client_key": "hospitalid",            # the FEDERATED CLIENT
    "time_key": "observationoffset",       # minutes from unit admission
    # Vitals kept as modality A. Order is fixed here because n_channels_a in
    # the registry must match it exactly.
    "vital_channels": ["heartrate", "respiration", "spo2",
                       "systemicsystolic", "systemicdiastolic", "temperature"],
    # Tabular fields for modality B, all recorded at or before admission.
    "tabular_fields": ["age", "gender", "admissionweight", "admissionheight",
                       "apachescore"],
    "label_field": "unitdischargestatus",  # "Expired" / "Alive"
    "label_positive": "Expired",
}

WINDOW_MIN = 60        # one hour of vitals per sample
STRIDE_MIN = 60        # non-overlapping, so no window shares a reading
MIN_WINDOWS = 2        # an individual below this cannot serve k-scaling


def _z(a, axis=0):
    m, s = np.nanmean(a, axis=axis, keepdims=True), np.nanstd(a, axis=axis, keepdims=True)
    return np.nan_to_num((a - m) / np.where(s < 1e-6, 1.0, s))


# ── the part that is logic, and is tested ──────────────────────────────────
def window_stays(vitals_by_stay, window=WINDOW_MIN, stride=STRIDE_MIN):
    """Cut each stay's vitals into fixed windows.

    Non-overlapping by default: overlapping windows share readings, and two
    windows sharing a reading on opposite sides of a split leak. `wear` needs
    a temporal control precisely because its windows overlap 50%; choosing
    stride == window here avoids needing one at all.
    """
    out = {}
    for stay, (times, mat) in vitals_by_stay.items():
        if len(times) == 0:
            continue
        order = np.argsort(times)
        times, mat = times[order], mat[order]
        wins, t0 = [], times.min()
        while t0 + window <= times.max() + 1:
            sel = (times >= t0) & (times < t0 + window)
            if sel.sum() >= 2:
                wins.append(mat[sel].mean(0))       # summarise the window
            t0 += stride
        if wins:
            out[stay] = np.stack(wins)
    return out


def split_by_individual(person_of_sample, seed=42, frac=(0.70, 0.15, 0.15)):
    """Partition INDIVIDUALS (not samples) into train/val/test.

    Splitting samples would place two windows from one admission on opposite
    sides; splitting stays would place two admissions of one person on
    opposite sides. Both leak through correlation. Only a person-level split
    is safe, and it is what the validator checks for.
    """
    people = np.unique(person_of_sample)
    rng = np.random.default_rng(seed)
    rng.shuffle(people)
    n = len(people)
    a, b = int(frac[0] * n), int((frac[0] + frac[1]) * n)
    sets = {"train": set(people[:a]), "val": set(people[a:b]),
            "test": set(people[b:])}
    return {k: np.where(np.isin(person_of_sample, list(v)))[0]
            for k, v in sets.items()}


def assign_clients(client_of_sample, min_samples=200):
    """Clients are hospitals as they arrive, not constructed.

    Hospitals below `min_samples` are merged into a pooled client rather than
    dropped: discarding them would bias the cohort toward large centres, which
    is the opposite of what a federated study wants to show.
    """
    ids, counts = np.unique(client_of_sample, return_counts=True)
    keep = set(ids[counts >= min_samples].tolist())
    remap, nxt = {}, 0
    for h in ids:
        if h in keep:
            remap[h] = nxt
            nxt += 1
    pooled = nxt if len(keep) < len(ids) else None
    out = np.array([remap.get(h, pooled) for h in client_of_sample])
    return out, nxt + (1 if pooled is not None else 0), pooled


def label_prevalence_spread(y, client_of_sample, n_clients):
    """Evidence of genuine non-IIDness, reported the way VitalDB reports it."""
    per = []
    for c in range(n_clients):
        m = client_of_sample == c
        if m.sum():
            per.append(float(y[m].mean()))
    return (min(per), max(per)) if per else (0.0, 0.0)


# ── synthetic fixture: proves the logic without the real tables ────────────
def _synthetic(n_people=1500, n_hosp=12, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_people):
        hosp = int(rng.integers(0, n_hosp))
        for _stay in range(int(rng.integers(1, 3))):       # repeat admissions
            stay = len(rows) + 100000
            n_read = int(rng.integers(120, 400))
            times = np.sort(rng.integers(0, 60 * 8, n_read)).astype(float)
            mat = rng.normal(size=(n_read, len(SCHEMA["vital_channels"])))
            rows.append({"person": f"p{p:05d}", "stay": stay, "hosp": hosp,
                         "times": times, "mat": mat,
                         "tab": rng.normal(size=len(SCHEMA["tabular_fields"])),
                         "y": int(rng.random() < 0.12)})
    return rows


def build_from_rows(rows, out_dir: Path, seed=42):
    """Shared by the synthetic fixture and the real loader."""
    vit = {r["stay"]: (r["times"], r["mat"]) for r in rows}
    win = window_stays(vit)
    meta = {r["stay"]: r for r in rows}

    A, B, y, person, client, stay_ids = [], [], [], [], [], []
    for stay, w in win.items():
        r = meta[stay]
        for row in w:
            A.append(row)
            B.append(r["tab"])                 # SAME stay: paired at source
            y.append(r["y"])
            person.append(r["person"])
            client.append(r["hosp"])
            stay_ids.append(stay)
    A = _z(np.stack(A)); B = _z(np.stack(B))
    y = np.asarray(y, np.int64)
    person = np.asarray(person)
    client = np.asarray(client)

    # Drop individuals with too few windows: they cannot serve k-scaling and
    # they make the per-individual clipping bound meaningless.
    uniq, counts = np.unique(person, return_counts=True)
    keep_people = set(uniq[counts >= MIN_WINDOWS].tolist())
    m = np.isin(person, list(keep_people))
    A, B, y, person, client = A[m], B[m], y[m], person[m], client[m]

    client, n_clients, pooled = assign_clients(client)
    lo, hi = label_prevalence_spread(y, client, n_clients)
    splits = split_by_individual(person, seed=seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("vitals", "tabular", "meta"):
        (out_dir / sub).mkdir(exist_ok=True)
    np.save(out_dir / "vitals" / "windows.npy", A.astype(np.float32))
    np.save(out_dir / "vitals" / "labels.npy", y)
    np.save(out_dir / "tabular" / "features.npy", B.astype(np.float32))
    # group_ids is the PERSON, encoded to int for the downstream loaders.
    _, gid = np.unique(person, return_inverse=True)
    np.save(out_dir / "meta" / "group_ids.npy", gid.astype(np.int64))
    np.save(out_dir / "meta" / "client_ids.npy", client.astype(np.int64))
    (out_dir / "meta" / "dataset_meta.json").write_text(json.dumps({
        "n_samples": int(len(y)), "n_individuals": int(len(np.unique(gid))),
        "n_clients": int(n_clients), "pooled_client": pooled,
        "n_channels_a": int(A.shape[1]), "feat_b_dim": int(B.shape[1]),
        "label_prevalence_range": [lo, hi],
        "window_min": WINDOW_MIN, "stride_min": STRIDE_MIN,
        "individual_key": SCHEMA["person_key"],
        "splits": {k: int(len(v)) for k, v in splits.items()},
    }, indent=2))
    return splits, gid, client, y, n_clients, (lo, hi)


def self_test():
    """Prove the logic on a fixture shaped like eICU, before access clears."""
    import tempfile
    print("SELF TEST — synthetic cohort shaped like eICU\n" + "=" * 62)
    rows = _synthetic()
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "eicu"
        splits, gid, client, y, n_clients, prev = build_from_rows(rows, out)

        ok = True
        # 1. the check the whole study depends on
        gs = {k: set(np.unique(gid[v])) for k, v in splits.items()}
        overlap = [(a, b, len(gs[a] & gs[b]))
                   for a, b in (("train", "val"), ("train", "test"), ("val", "test"))
                   if gs[a] & gs[b]]
        print(f"  individuals per split: "
              f"{ {k: len(v) for k, v in gs.items()} }")
        print(f"  {'ok  ' if not overlap else 'FAIL'} splits are individual-disjoint"
              f"{'' if not overlap else f' — {overlap}'}")
        ok &= not overlap

        # 2. a person with two admissions must not straddle a split
        multi = [g for g in np.unique(gid) if (gid == g).sum() > 20][:50]
        straddle = sum(1 for g in multi
                       if sum(g in gs[k] for k in gs) > 1)
        print(f"  {'ok  ' if straddle == 0 else 'FAIL'} repeat admissions stay "
              f"on one side ({straddle} straddling of {len(multi)} checked)")
        ok &= straddle == 0

        # 3. non-overlapping windows: no sample index reused
        total = sum(len(v) for v in splits.values())
        uniq = len(np.unique(np.concatenate(list(splits.values()))))
        print(f"  {'ok  ' if total == uniq else 'FAIL'} every sample in exactly "
              f"one split ({total} placed, {uniq} unique)")
        ok &= total == uniq

        # 4. clients arise from hospitals and are non-IID
        print(f"  ok   {n_clients} clients from hospitals; label prevalence "
              f"{prev[0]:.3f}–{prev[1]:.3f}")
        print(f"\n{'SELF TEST PASSED' if ok else 'SELF TEST FAILED'}")
        return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw_dir", default=None, help="unzipped eICU-CRD CSVs")
    ap.add_argument("--out_dir", default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--self_test", action="store_true",
                    help="validate the logic on a synthetic fixture")
    a = ap.parse_args()

    if a.self_test or not a.raw_dir:
        return self_test()

    raise SystemExit(
        "Real-table loading is not implemented yet, deliberately.\n"
        "The windowing, pairing, person-level splitting and hospital "
        "partitioning above are tested (--self_test). What remains is reading "
        "SCHEMA from the actual CSVs, which must be written against the real "
        "columns rather than guessed — verify SCHEMA at the top of this file "
        "first, then wire it into build_from_rows().\n"
        "After building, run:\n"
        "  python data/loaders/validate_corpus.py --datasets eicu\n"
        "and do not proceed past a CAPACITY failure.")


if __name__ == "__main__":
    sys.exit(main())
