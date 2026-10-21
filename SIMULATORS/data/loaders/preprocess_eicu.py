"""
preprocess_eicu.py — build the eICU-CRD corpus into the arrays this study expects.

STATUS: real-table loading is IMPLEMENTED. The schema mapping is written from
the published eICU-CRD documentation and is CHECKED AT RUNTIME by
`--verify_schema`, which reads only headers and prints a presence/absence
verdict. Run that first; it costs seconds and cannot fail destructively.

WHY eICU
--------
The study's core claims are carried by one corpus. `wear` cannot corroborate
any of them: 22 individuals against the 1,200 a patient-level attack needs, one
individual per client so the privacy unit is degenerate, and a task its better
single modality already solves at 0.9976. eICU fails none of those, and adds
something VitalDB lacks: its clients are REAL HOSPITALS (208 of them), where
VitalDB's nine are constructed by grouping surgical optype. For a paper about
hierarchical federation, a naturally arising partition is worth as much as the
second modality.

THE INDIVIDUAL IS THE PERSON, NOT THE STAY
------------------------------------------
eICU distinguishes `uniquepid` (a person) from `patientunitstayid` (one ICU
admission). A person may be admitted repeatedly. Every claim in this study that
says "individual" means the person, so `uniquepid` is what becomes the group
key and what the splits are made disjoint on. Keying on the stay would let the
same person appear in train and test through a second admission, which is
precisely the leakage the validator exists to catch.

MODALITIES MUST BE PAIRED AT SOURCE
-----------------------------------
Modality A is the vitals window. Modality B is the tabular vector for the SAME
stay, built only from data recorded at or before admission. A tabular vector
assembled from cohort statistics, or from labs drawn after the prediction
point, is not paired at source and would void the multimodal claim.

TWO CORRECTIONS AGAINST THE PREVIOUS DRAFT OF THIS FILE
-------------------------------------------------------
1. WINDOWS KEEP THEIR TIME AXIS. The previous `window_stays` reduced each
   window to `mat[sel].mean(0)`, producing modality A of shape [N, C]. The
   model's `encoder_a` is FedMambaHC, which takes [B, C, T] (see
   model/architecture/fedmamba_hc.py:47). A [N, C] array cannot be fed to it.
   Windows are now resampled onto a fixed grid of T_SLOTS, giving [N, C, T].
2. THE GROUP FILE IS `case_ids.npy`. The previous draft wrote
   `meta/group_ids.npy`, but nine downstream consumers hardcode
   `meta/case_ids.npy` (hfl_trainer, baselines, lira_attack, k_scaling,
   membership_inference, mia_difficulty_floor, make_public_split,
   modality_ablation, pretrain_encoders). Writing the wrong name makes
   patient-level DP, LiRA and k-scaling silently fall back to record level.

OBSERVED-MASK CHANNELS
----------------------
Each vital is carried with a binary observed-mask channel, as VitalDB does. In
an ICU an absent measurement is not missing at random: it reflects what the
team judged worth monitoring. Carrying the mask explicitly keeps that signal
instead of hiding it inside a zero-fill.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np

# ── schema constants: verified at runtime by --verify_schema ───────────────
SCHEMA = {
    "patient_csv": "patient.csv",
    "vitals_csv": "vitalPeriodic.csv",
    "apache_csv": "apachePatientResult.csv",
    "person_key": "uniquepid",             # the INDIVIDUAL
    "stay_key": "patientunitstayid",       # one admission
    "client_key": "hospitalid",            # the FEDERATED CLIENT
    "time_key": "observationoffset",       # minutes from unit admission
    # Vitals kept as modality A. Order is fixed here because n_channels_a in
    # the registry must equal 2x this length (values + observed masks).
    "vital_channels": ["heartrate", "respiration", "sao2",
                       "systemicsystolic", "systemicdiastolic", "temperature"],
    # Tabular fields for modality B, all recorded at or before admission.
    "tabular_fields": ["age", "gender", "admissionweight", "admissionheight"],
    "apache_field": "apachescore",         # lives in apachePatientResult
    "label_field": "unitdischargestatus",  # "Expired" / "Alive"
    # Minutes from unit admission to unit discharge. For an Expired stay this
    # is the time of death, and it is what the 24 h lead-time rule keys on.
    "discharge_offset_field": "unitdischargeoffset",
    "label_positive": "Expired",
}

WINDOW_MIN = 60         # one hour of vitals per sample
T_SLOTS = 12            # 12 slots x 5 min — vitalPeriodic archives ~every 5 min
# The whole reason for adding eICU is that it "stretches the curve into a range
# we cannot currently reach" (Research Dossier Pt2 §9.2). VitalDB tops out near
# k=8. Capping eICU at 8 would test exactly VitalDB's range and could not
# falsify the saturation prediction, which is only testable at k > 8. 48 hours
# gives k up to 32. The accumulator is memory-mapped when it exceeds MMAP_GB.
# EARLY-PREDICTION TASK DEFINITION (set 2026-09-08, replacing a 48 h window).
# Features come from the first OBS_WINDOW_H hours after unit admission, and an
# individual whose in-unit death falls inside that window is EXCLUDED: they
# pose no prediction problem, and their final windows are peri-mortem, which
# makes mortality look artificially easy. Features precede the outcome either
# way - this is clinical defensibility, not leakage. k-scaling reach falls from
# ~32 to ~24 windows/individual, still well past VitalDB's ~8.
OBS_WINDOW_H = 24
MIN_DEATH_LEAD_MIN = OBS_WINDOW_H * 60
MAX_WINDOWS_PER_STAY = OBS_WINDOW_H
MIN_SLOTS_OBSERVED = 3  # a window with fewer real readings is not a window
MMAP_GB = 1.0           # accumulators larger than this spill to disk
MIN_WINDOWS = 2         # an individual below this cannot serve k-scaling

# Raw tables live inside the repo, under the directory that SIMULATORS/.gitignore
# already excludes and that .claude/settings.local.json denies reading. Keeping
# them here rather than outside the tree means one protected location, not two.
DEFAULT_RAW_REL = "SIMULATORS/data/raw/eicu"


def _default_raw() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "raw" / "eicu"


def _z(a, axis=0):
    m, s = np.nanmean(a, axis=axis, keepdims=True), np.nanstd(a, axis=axis, keepdims=True)
    return np.nan_to_num((a - m) / np.where(s < 1e-6, 1.0, s))


def _open(path: Path):
    """eICU ships .csv.gz; accept either form transparently."""
    p = Path(path)
    if p.exists():
        return open(p, "rt", encoding="utf-8", errors="replace")
    gz = Path(str(p) + ".gz")
    if gz.exists():
        return gzip.open(gz, "rt", encoding="utf-8", errors="replace")
    raise FileNotFoundError(f"neither {p} nor {gz}")


def _resolve(raw_dir: Path, name: str) -> Path:
    p = raw_dir / name
    return p if p.exists() else Path(str(p) + ".gz")


# ── eICU-specific coercions. These are the documented quirks. ─────────────
def coerce_age(v):
    """eICU stores age as TEXT and masks ages over 89 as '> 89' for HIPAA.

    Dropping those rows would bias the cohort young, exactly against the
    acuity signal this task depends on, so they are mapped to 90.
    """
    s = str(v).strip()
    if s in ("", "nan", "None"):
        return np.nan
    if s.startswith(">"):
        return 90.0
    try:
        return float(s)
    except ValueError:
        return np.nan


def coerce_gender(v):
    s = str(v).strip().lower()
    return 1.0 if s == "male" else 0.0 if s == "female" else np.nan


def coerce_float(v):
    try:
        f = float(v)
        return f if np.isfinite(f) else np.nan
    except (TypeError, ValueError):
        return np.nan


COERCE = {"age": coerce_age, "gender": coerce_gender}


# ── the part that is logic, and is tested ──────────────────────────────────
def window_stay_series(times, mat, window=WINDOW_MIN, t_slots=T_SLOTS,
                       max_windows=MAX_WINDOWS_PER_STAY,
                       min_slots=MIN_SLOTS_OBSERVED):
    """Cut one stay's vitals into fixed [C, T] windows on a regular grid.

    Non-overlapping: overlapping windows share readings, and two windows
    sharing a reading on opposite sides of a split leak. `wear` needs a
    temporal control precisely because its windows overlap 50%; stride ==
    window avoids needing one at all.

    Returns (values [n, C, T], masks [n, C, T], window_index [n]).
    The time axis is PRESERVED — see the module docstring, correction 1.
    """
    C = mat.shape[1]
    slot_min = window / t_slots
    vals, msks, widx = [], [], []
    if len(times) == 0:
        return (np.zeros((0, C, t_slots), np.float32),
                np.zeros((0, C, t_slots), np.float32),
                np.zeros((0,), np.int64))
    for w in range(max_windows):
        lo, hi = w * window, (w + 1) * window
        sel = (times >= lo) & (times < hi)
        if not sel.any():
            continue
        t_in, m_in = times[sel], mat[sel]
        slot = np.minimum(((t_in - lo) / slot_min).astype(int), t_slots - 1)
        acc = np.zeros((C, t_slots), np.float64)
        cnt = np.zeros((C, t_slots), np.float64)
        for ci in range(C):
            v = m_in[:, ci]
            ok = np.isfinite(v)
            if ok.any():
                np.add.at(acc[ci], slot[ok], v[ok])
                np.add.at(cnt[ci], slot[ok], 1.0)
        mask = (cnt > 0).astype(np.float32)
        # A window whose best channel has fewer than min_slots real readings
        # is an artefact of sparse charting, not an hour of monitoring.
        if mask.sum(1).max() < min_slots:
            continue
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = np.where(cnt > 0, acc / np.maximum(cnt, 1), 0.0)
        vals.append(mean.astype(np.float32))
        msks.append(mask)
        widx.append(w)
    if not vals:
        return (np.zeros((0, C, t_slots), np.float32),
                np.zeros((0, C, t_slots), np.float32),
                np.zeros((0,), np.int64))
    return np.stack(vals), np.stack(msks), np.asarray(widx, np.int64)


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


def split_stratified_within_client(person, client, y, seed=42,
                                   frac=(0.70, 0.15, 0.15)):
    """Split INDIVIDUALS train/val/test, stratified by outcome INSIDE each client.

    A global split would be patient-disjoint but could leave a small hospital
    with no deaths in its test fold, making its client-level metrics undefined.
    VitalDB stratifies within optype for exactly this reason; with 208 hospitals
    the risk is larger, not smaller.

    Each individual is assigned to one split ONCE, keyed on their majority
    client, so a patient transferred between hospitals still cannot straddle a
    split. Patient-disjointness is the invariant; stratification is the refinement.
    """
    rng = np.random.default_rng(seed)
    people = np.unique(person)
    # one client and one label per individual
    p_client, p_label = {}, {}
    for pp in people:
        m = person == pp
        cs, ct = np.unique(client[m], return_counts=True)
        p_client[pp] = cs[np.argmax(ct)]
        # CLINICAL DEFINITION: patient-level in-unit mortality = 1 if ANY
        # eligible ICU stay for that individual has unitdischargestatus ==
        # "Expired", else 0. max() is the implementation of that definition,
        # not the definition itself - the paper must state the clinical form.
        p_label[pp] = int(y[m].max())

    buckets = {}
    for pp in people:
        buckets.setdefault((p_client[pp], p_label[pp]), []).append(pp)

    of_split = {}
    for key in sorted(buckets, key=lambda t: (str(t[0]), t[1])):
        grp = np.array(buckets[key])
        rng.shuffle(grp)
        n = len(grp)
        a = int(round(frac[0] * n))
        b = int(round((frac[0] + frac[1]) * n))
        # A bucket of 1-2 people cannot fill three folds; train is preferred
        # because an empty val/test fold is detected downstream, whereas an
        # empty train fold silently produces an untrained client.
        a, b = max(a, 1 if n >= 1 else 0), max(b, min(2, n))
        for pp in grp[:a]:
            of_split[pp] = "train"
        for pp in grp[a:b]:
            of_split[pp] = "val"
        for pp in grp[b:]:
            of_split[pp] = "test"

    split_of_sample = np.array([of_split[pp] for pp in person])
    return ({s: np.where(split_of_sample == s)[0]
             for s in ("train", "val", "test")}, of_split)


def write_partitions(part_dir: Path, splits, client, n_clients, y, person,
                     n_edges=2, extra=None, verbose=True):
    """Write device_XX_{train,val,test}.npy + partition_meta.json.

    Downstream code (hfl_trainer, k_scaling, lira_attack, attribution,
    make_figures, validate_corpus) reads these; without them the corpus builds
    but nothing can consume it. Format matches preprocess_vitaldb.py exactly.
    """
    import glob as _glob
    from collections import Counter

    part_dir.mkdir(parents=True, exist_ok=True)
    # Stale device_*.npy from a run with a different client count would be
    # picked up silently by a later run. VitalDB clears them for this reason.
    for old in _glob.glob(str(part_dir / "device_*.npy")):
        os.remove(old)

    split_of = np.empty(len(client), dtype=object)
    for name, idx in splits.items():
        split_of[idx] = name

    edge_assign = {e: [] for e in range(n_edges)}
    for d in range(n_clients):
        edge_assign[d % n_edges].append(d)
    d2e = {d: e for e, ds in edge_assign.items() for d in ds}

    devices, empty = {}, []
    for d in range(n_clients):
        dm = client == d
        parts = {}
        for name in ("train", "val", "test"):
            idx = np.where(dm & (split_of == name))[0].astype(np.int64)
            np.save(part_dir / f"device_{d:02d}_{name}.npy", idx)
            parts[name] = idx
        allw = np.concatenate(list(parts.values())).astype(int)
        if len(parts["train"]) == 0 or len(parts["test"]) == 0:
            empty.append(d)
        devices[str(d)] = {
            "edge_id": int(d2e[d]),
            "n_train": int(len(parts["train"])),
            "n_val": int(len(parts["val"])),
            "n_test": int(len(parts["test"])),
            "total": int(len(allw)),
            "n_patients": int(len(np.unique(person[dm]))),
            "mortality_rate_pct": round(float(y[allw].mean() * 100), 2) if len(allw) else 0.0,
            "class_distribution": {str(k): int(v) for k, v in
                                   sorted(Counter(y[allw].tolist()).items())},
        }

    meta = {
        "dataset": "eICU-CRD",
        "citation": "Pollard et al., Sci Data 5:180178, 2018",
        "licence": "PhysioNet Credentialed Health Data License 1.5.0",
        "domain": "clinical_iomt",
        "pairing": "same stay (patientunitstayid); tabular is admission-time only",
        "label": f'in-unit mortality ({SCHEMA["label_field"]} == '
                 f'"{SCHEMA["label_positive"]}")',
        "total_samples": int(len(y)), "n_devices": int(n_clients), "n_classes": 2,
        "n_edges": int(n_edges),
        "edge_assignments": {str(k): v for k, v in edge_assign.items()},
        "devices": devices,
        "client_key": f'{SCHEMA["client_key"]} (real hospitals, taken as given; '
                      f'hospitals under 200 windows OR with zero positive '
                      f'cases are merged into one pooled client)',
        "individual_key": SCHEMA["person_key"],
        "split": "by INDIVIDUAL (uniquepid), stratified by outcome within each "
                 "hospital; no individual spans splits",
        "n_individuals": int(len(np.unique(person))),
    }
    if extra:
        meta.update(extra)
    (part_dir / "partition_meta.json").write_text(json.dumps(meta, indent=2))

    if verbose and empty:
        print(f"[eicu][WARN] {len(empty)} client(s) with an empty train or test "
              f"fold: {empty[:10]}{' ...' if len(empty) > 10 else ''}")
    return meta


def assign_clients(client_of_sample, min_samples=200, y=None):
    """Clients are hospitals as they arrive, not constructed.

    TWO pooling criteria, both fixed in advance of any experimental result:

    1. SIZE. Hospitals below `min_samples` windows are merged into a pooled
       client rather than dropped: discarding them would bias the cohort
       toward large centres, the opposite of what a federated study wants.

    2. DEGENERATE OUTCOME. A hospital with zero positive cases is also pooled.
       It cannot contribute to a binary task's positive class and its
       within-client mortality is mathematically undefined.

       Criterion 2 reads the LABEL, so client construction is not purely
       label-independent. This is disclosed deliberately: it is applied to
       every eICU experiment identically, and it is decided here - before any
       model is trained - rather than adjusted after seeing a result. The
       affected patients are retained inside the pooled client, not discarded.

    Returns (clients, n_clients, pooled_index, report).
    """
    ids, counts = np.unique(client_of_sample, return_counts=True)
    too_small = set(ids[counts < min_samples].tolist())

    no_positive = set()
    if y is not None:
        y = np.asarray(y)
        for h in ids:
            if h in too_small:
                continue
            if int(y[client_of_sample == h].sum()) == 0:
                no_positive.add(h)

    drop = too_small | no_positive
    keep = [h for h in ids if h not in drop]
    remap, nxt = {}, 0
    for h in keep:
        remap[h] = nxt
        nxt += 1
    pooled = nxt if drop else None
    out = np.array([remap.get(h, pooled) for h in client_of_sample])

    report = {
        "hospitals_seen": int(len(ids)),
        "min_samples": int(min_samples),
        "pooled_for_size": int(len(too_small)),
        "pooled_for_zero_positives": int(len(no_positive)),
        "standalone_clients": int(nxt),
        "pooled_client_index": pooled,
        "n_clients": int(nxt + (1 if pooled is not None else 0)),
    }
    return out, report["n_clients"], pooled, report


def label_prevalence_spread(y, client_of_sample, n_clients):
    """Evidence of genuine non-IIDness, reported the way VitalDB reports it."""
    per = []
    for c in range(n_clients):
        m = client_of_sample == c
        if m.sum():
            per.append(float(y[m].mean()))
    return (min(per), max(per)) if per else (0.0, 0.0)


# ── schema verification: reads HEADERS ONLY, prints a verdict ─────────────
def verify_schema(raw_dir: Path) -> int:
    """Check every SCHEMA constant against the real column headers.

    Emits column NAMES and counts only — never a data value. eICU's column
    names are published openly at https://eicu-crd.mit.edu/, so this output
    is safe to share; the rows behind them are not.
    """
    import csv
    print("SCHEMA VERIFICATION — headers only, no data values read")
    print("=" * 66)
    wanted = {
        SCHEMA["patient_csv"]: [SCHEMA["person_key"], SCHEMA["stay_key"],
                                SCHEMA["client_key"], SCHEMA["label_field"],
                                SCHEMA["discharge_offset_field"]]
                               + SCHEMA["tabular_fields"],
        SCHEMA["vitals_csv"]: [SCHEMA["stay_key"], SCHEMA["time_key"]]
                              + SCHEMA["vital_channels"],
        SCHEMA["apache_csv"]: [SCHEMA["stay_key"], SCHEMA["apache_field"]],
    }
    ok = True
    for fname, cols in wanted.items():
        path = _resolve(raw_dir, fname)
        print(f"\n{fname}")
        if not path.exists():
            print(f"  FAIL  not found at {path}")
            ok = False
            continue
        with _open(raw_dir / fname) as fh:
            header = next(csv.reader(fh))
        header_l = {h.strip().lower(): h.strip() for h in header}
        print(f"  {len(header)} columns present")
        for c in cols:
            hit = header_l.get(c.lower())
            if hit:
                print(f"  ok    {c}" + ("" if hit == c else f"  (actual: {hit})"))
            else:
                near = [h for h in header_l if c.lower()[:5] in h][:4]
                print(f"  FAIL  {c}  MISSING"
                      + (f"  — near: {near}" if near else ""))
                ok = False
    print("\n" + "=" * 66)
    print("SCHEMA VERIFIED" if ok else "SCHEMA MISMATCH — fix SCHEMA at the "
          "top of this file before building")
    print("\nSafe to paste the whole of this output: it contains column names "
          "and counts only.")
    return 0 if ok else 1


# ── real-table loading ────────────────────────────────────────────────────
def apply_lead_time_rule(stays: dict, min_lead_min=MIN_DEATH_LEAD_MIN,
                         verbose=True):
    """Drop individuals whose in-unit death occurs inside the feature window.

    The task is: from the first OBS_WINDOW_H hours after admission, will this
    person die in the unit? Someone who dies at hour 10 of a 24 h window poses
    no such question, and their last windows are peri-mortem.

    Exclusion is at the INDIVIDUAL level, not the stay level: dropping only the
    fatal stay would silently relabel that person a survivor, because the
    patient-level outcome is "ever expired".

    Returns (kept_stays, report). Counts only - never record content.
    """
    died_early = {m["person"] for m in stays.values()
                  if m["y"] == 1 and np.isfinite(m.get("dc_off", np.nan))
                  and m["dc_off"] < min_lead_min}
    kept = {s: m for s, m in stays.items() if m["person"] not in died_early}

    def _prev(d):
        by = {}
        for m in d.values():
            by[m["person"]] = max(by.get(m["person"], 0), m["y"])
        return (sum(by.values()) / (len(by) or 1), sum(by.values()), len(by))

    p0, pos0, n0 = _prev(stays)
    p1, pos1, n1 = _prev(kept)
    report = {
        "rule": f"exclude individuals dying < {min_lead_min} min after admission",
        "observation_window_h": OBS_WINDOW_H,
        "individuals_before": n0, "individuals_after": n1,
        "individuals_excluded": len(died_early),
        "stays_before": len(stays), "stays_after": len(kept),
        "stays_excluded": len(stays) - len(kept),
        "deaths_before": pos0, "deaths_after": pos1,
        "mortality_prevalence_before": round(p0, 4),
        "mortality_prevalence_after": round(p1, 4),
    }
    if verbose:
        print(f"[eicu] lead-time rule (<{min_lead_min} min): individuals "
              f"{n0:,} -> {n1:,} ({len(died_early):,} excluded); "
              f"mortality {p0:.4f} -> {p1:.4f}")
    return kept, report


def load_patient_table(raw_dir: Path, max_stays=None, verbose=True):
    """Read patient.csv + apachePatientResult.csv into per-stay metadata.

    Returns dict: stay -> {person, hosp, tab (list[float]), y (int)}.
    Only stays with a usable label and person id survive.
    """
    import csv
    pth = SCHEMA
    apache = {}
    ap_path = _resolve(raw_dir, pth["apache_csv"])
    if ap_path.exists():
        with _open(raw_dir / pth["apache_csv"]) as fh:
            for row in csv.DictReader(fh):
                s = row.get(pth["stay_key"])
                v = coerce_float(row.get(pth["apache_field"]))
                if s and np.isfinite(v):
                    # a stay can have several APACHE versions; keep the worst
                    apache[s] = max(apache.get(s, -np.inf), v)
    if verbose:
        print(f"[eicu] apache scores for {len(apache):,} stays")

    stays = {}
    with _open(raw_dir / pth["patient_csv"]) as fh:
        for row in csv.DictReader(fh):
            s = row.get(pth["stay_key"])
            person = row.get(pth["person_key"])
            status = (row.get(pth["label_field"]) or "").strip()
            if not s or not person or status not in ("Alive", pth["label_positive"]):
                continue
            tab = [COERCE.get(f, coerce_float)(row.get(f))
                   for f in pth["tabular_fields"]]
            tab.append(apache.get(s, np.nan))
            stays[s] = {
                "person": person,
                "hosp": row.get(pth["client_key"]) or "unknown",
                "tab": tab,
                "y": int(status == pth["label_positive"]),
                # minutes admission -> discharge; for an Expired stay, death
                "dc_off": coerce_float(row.get(pth["discharge_offset_field"])),
            }
            if max_stays and len(stays) >= max_stays:
                break
    if verbose:
        print(f"[eicu] {len(stays):,} stays with a usable label and person id")
    return stays


def stream_vitals(raw_dir: Path, stays: dict, chunk_rows=2_000_000,
                  max_windows=MAX_WINDOWS_PER_STAY, scratch=None, verbose=True):
    """Stream vitalPeriodic and accumulate fixed [C, T] windows per stay.

    vitalPeriodic is ~1.7 GB gzipped and does not fit in memory, so readings
    are binned into (window, slot) on the fly and never held raw. Only the
    first MAX_WINDOWS_PER_STAY hours of each stay are kept, which bounds
    memory and still reaches k=8 for the scaling experiment.
    """
    try:
        import pandas as pd
    except ImportError:
        raise SystemExit("pandas is required to stream vitalPeriodic")

    chans = SCHEMA["vital_channels"]
    C, T = len(chans), T_SLOTS
    stay_list = list(stays)
    stay_ix = {s: i for i, s in enumerate(stay_list)}
    n_stay = len(stay_list)
    horizon = max_windows * WINDOW_MIN
    slot_min = WINDOW_MIN / T

    shape = (n_stay, max_windows, C, T)
    nbytes = int(np.prod(shape)) * 4
    use_mmap = (2 * nbytes / 1e9) > MMAP_GB
    if use_mmap:
        # Dense in RAM would be several GB at 48 windows. Spilling to disk
        # keeps the full k range reachable on an ordinary workstation.
        tmp = Path(scratch or ".") / "_eicu_acc"
        tmp.mkdir(parents=True, exist_ok=True)
        acc = np.memmap(tmp / "acc.f32", np.float32, "w+", shape=shape)
        cnt = np.memmap(tmp / "cnt.f32", np.float32, "w+", shape=shape)
        acc[:] = 0; cnt[:] = 0
    else:
        acc = np.zeros(shape, np.float32)
        cnt = np.zeros(shape, np.float32)
    if verbose:
        print(f"[eicu] accumulator {shape} = {2*nbytes/1e9:.2f} GB"
              f"{'  (memory-mapped to disk)' if use_mmap else ''}")

    usecols = [SCHEMA["stay_key"], SCHEMA["time_key"]] + chans
    path = _resolve(raw_dir, SCHEMA["vitals_csv"])
    seen = 0
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=chunk_rows,
                             dtype={SCHEMA["stay_key"]: str}, low_memory=False):
        seen += len(chunk)
        chunk = chunk[chunk[SCHEMA["stay_key"]].isin(stay_ix)]
        if chunk.empty:
            continue
        off = pd.to_numeric(chunk[SCHEMA["time_key"]], errors="coerce").values
        keep = np.isfinite(off) & (off >= 0) & (off < horizon)
        if not keep.any():
            continue
        chunk, off = chunk[keep], off[keep]
        si = chunk[SCHEMA["stay_key"]].map(stay_ix).values.astype(np.int64)
        wi = (off // WINDOW_MIN).astype(np.int64)
        sl = np.minimum(((off % WINDOW_MIN) / slot_min).astype(np.int64), T - 1)
        for ci, col in enumerate(chans):
            v = pd.to_numeric(chunk[col], errors="coerce").values
            ok = np.isfinite(v)
            if not ok.any():
                continue
            np.add.at(acc, (si[ok], wi[ok], ci, sl[ok]), v[ok])
            np.add.at(cnt, (si[ok], wi[ok], ci, sl[ok]), 1.0)
        if verbose:
            print(f"[eicu]   {seen:,} rows scanned", flush=True)

    # In place, block by block: a full-corpus np.where would double peak usage.
    block = max(1, 2_000_000 // (max_windows * C * T))
    for i in range(0, n_stay, block):
        c = np.asarray(cnt[i:i+block])
        a = np.asarray(acc[i:i+block])
        acc[i:i+block] = np.where(c > 0, a / np.maximum(c, 1.0), 0.0)
        cnt[i:i+block] = (c > 0).astype(np.float32)
    return stay_list, acc, cnt          # acc is now the mean, cnt is the mask


def rows_from_streamed(stay_list, mean, mask, stays):
    """mean/mask may be memmaps; indexing materialises one window at a time."""
    """Turn the accumulator into per-sample records, dropping empty windows."""
    rows = []
    per_win_obs = mask.sum(3).max(2)          # [n_stay, n_win] best-channel obs
    for si, stay in enumerate(stay_list):
        meta = stays[stay]
        for w in range(mean.shape[1]):
            if per_win_obs[si, w] < MIN_SLOTS_OBSERVED:
                continue
            rows.append({
                "stay": stay, "person": meta["person"], "hosp": meta["hosp"],
                "y": meta["y"], "tab": meta["tab"],
                "vals": np.asarray(mean[si, w]), "mask": np.asarray(mask[si, w]),
                "win": w,
            })
    return rows


# ── shared build: same code path for the fixture and the real tables ──────
def build_from_rows(rows, out_dir: Path, seed=42, verbose=True,
                    part_dir_override=None, n_edges=2):
    if not rows:
        raise SystemExit("no usable windows — check --raw_dir and --verify_schema")

    A_val = np.stack([r["vals"] for r in rows])        # [N, C, T]
    A_msk = np.stack([r["mask"] for r in rows])        # [N, C, T]
    B = np.asarray([r["tab"] for r in rows], np.float64)
    y = np.asarray([r["y"] for r in rows], np.int64)
    person = np.asarray([r["person"] for r in rows])
    client = np.asarray([r["hosp"] for r in rows])
    stay_ids = np.asarray([str(r["stay"]) for r in rows])

    # ORDER IS PART OF THE METHOD: cohort -> clients -> SPLIT -> statistics.
    #
    # Eligibility (MIN_WINDOWS) depends on how many windows an individual has,
    # so windows must exist before the cohort is final. Everything that FITS a
    # statistic, however, happens strictly after the split.
    #
    # Drop individuals with too few windows: they cannot serve k-scaling and
    # they make the per-individual clipping bound meaningless.
    uniq, counts = np.unique(person, return_counts=True)
    keep_people = set(uniq[counts >= MIN_WINDOWS].tolist())
    m = np.isin(person, list(keep_people))
    A_val, A_msk, B, y, person, client, stay_ids = (
        A_val[m], A_msk[m], B[m], y[m], person[m], client[m], stay_ids[m])

    # y is passed so a hospital with zero positives is pooled as well as one
    # that is too small; see assign_clients for why that is disclosed.
    prepool_ids, prepool_counts = np.unique(client, return_counts=True)
    prepool_prev = [float(y[client == h].mean()) for h in prepool_ids]
    client, n_clients, pooled, client_report = assign_clients(client, y=y)
    client_report["prepool_hospitals"] = int(len(prepool_ids))
    client_report["prepool_prevalence_min"] = round(min(prepool_prev), 4) if prepool_prev else None
    client_report["prepool_prevalence_max"] = round(max(prepool_prev), 4) if prepool_prev else None
    client_report["prepool_zero_mortality_hospitals"] = int(sum(1 for v in prepool_prev if v == 0.0))
    print(f"[eicu] clients: {client_report['prepool_hospitals']} hospitals -> "
          f"{n_clients} clients "
          f"({client_report['pooled_for_size']} pooled for size, "
          f"{client_report['pooled_for_zero_positives']} for zero positives)")
    lo, hi = label_prevalence_spread(y, client, n_clients)
    # Stratified WITHIN client, not globally: with 208 hospitals a global split
    # can leave a small site with no deaths in its test fold.
    splits, _ = split_stratified_within_client(person, client, y, seed=seed)
    _tr = splits["train"]

    # Per-channel z-score, FITTED ON TRAIN INDIVIDUALS ONLY and then applied to
    # every split. Until 2026-09-08 mu/sigma were fitted over the whole corpus,
    # which leaks the val/test distribution into the training features.
    # Patient-disjointness does not prevent that: feature statistics are a
    # separate leakage channel from record membership.
    # Masks are NOT normalised: they are indicator channels.
    #
    # CHUNKED. A_val[_tr] fancy-indexes a copy and .transpose().reshape() copies
    # again; at 20k stays that is 68 MB and invisible, at the full 3.78M-window
    # corpus it is ~1.4 GB per array. Together with np.concatenate allocating a
    # second full-size A, peak hit ~8.9 GB and the OOM killer took the build
    # after the client report and BEFORE the first np.save - leaving the
    # previous corpus intact and silently validated in its place.
    # Statistics are unchanged: same train-only entries, same masked selection,
    # two-pass variance so the result matches np.std rather than a
    # sum-of-squares approximation.
    N, C, T = A_val.shape
    CHUNK = 200_000

    cnt = np.zeros(C, np.float64)
    s1 = np.zeros(C, np.float64)
    for i in range(0, len(_tr), CHUNK):
        idx = _tr[i:i + CHUNK]
        v, m = A_val[idx], A_msk[idx] > 0
        for c in range(C):
            sel = v[:, c, :][m[:, c, :]]
            if sel.size:
                s1[c] += sel.sum(dtype=np.float64)
                cnt[c] += sel.size
    mu = np.where(cnt > 0, s1 / np.maximum(cnt, 1.0), 0.0)

    s2 = np.zeros(C, np.float64)
    for i in range(0, len(_tr), CHUNK):
        idx = _tr[i:i + CHUNK]
        v, m = A_val[idx], A_msk[idx] > 0
        for c in range(C):
            sel = v[:, c, :][m[:, c, :]]
            if sel.size:
                d = sel.astype(np.float64) - mu[c]
                s2[c] += float((d * d).sum())
    sd = np.where(cnt > 0, np.sqrt(s2 / np.maximum(cnt, 1.0)), 1.0)
    sd = np.where(sd < 1e-6, 1.0, sd)

    # Fill a pre-allocated A block by block rather than concatenating, which
    # would hold A_val, A_msk and a fresh 2x array live simultaneously.
    A = np.empty((N, 2 * C, T), np.float32)
    for i in range(0, N, CHUNK):
        sl = slice(i, min(i + CHUNK, N))
        A[sl, :C, :] = ((A_val[sl] - mu[None, :, None])
                        / sd[None, :, None]) * A_msk[sl]
        A[sl, C:, :] = A_msk[sl]
    del A_val, A_msk

    # Modality B: median-impute then z-score, BOTH fitted on train rows only.
    med = np.nanmedian(B[_tr], axis=0)
    med = np.where(np.isfinite(med), med, 0.0)       # column unobserved in train
    B = np.where(np.isfinite(B), B, med[None, :])
    b_mu = B[_tr].mean(axis=0)
    b_sd = B[_tr].std(axis=0)
    b_sd = np.where(b_sd < 1e-6, 1.0, b_sd)
    B = ((B - b_mu[None, :]) / b_sd[None, :]).astype(np.float32)

    out_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("vitals", "tabular", "meta"):
        (out_dir / sub).mkdir(exist_ok=True)
    np.save(out_dir / "vitals" / "windows.npy", A)
    np.save(out_dir / "vitals" / "labels.npy", y)
    np.save(out_dir / "tabular" / "features.npy", B)
    # case_ids.npy is the PERSON. The name matters — see correction 2 in the
    # module docstring. Nine downstream consumers hardcode this filename.
    _, gid = np.unique(person, return_inverse=True)
    np.save(out_dir / "meta" / "case_ids.npy", gid.astype(np.int64))
    np.save(out_dir / "meta" / "client_ids.npy", client.astype(np.int64))
    _, sid = np.unique(stay_ids, return_inverse=True)
    np.save(out_dir / "meta" / "stay_ids.npy", sid.astype(np.int64))

    meta = {
        "n_samples": int(len(y)), "n_individuals": int(len(np.unique(gid))),
        "n_stays": int(len(np.unique(sid))),
        "n_clients": int(n_clients), "pooled_client": pooled,
        "n_channels_a": int(A.shape[1]), "window_slots": int(A.shape[2]),
        "feat_b_dim": int(B.shape[1]),
        "label_prevalence_overall": float(y.mean()),
        "label_prevalence_range": [lo, hi],
        "window_min": WINDOW_MIN, "slot_min": WINDOW_MIN / T_SLOTS,
        "max_windows_per_stay": int(A.shape[0] and MAX_WINDOWS_PER_STAY),
        "max_k_reachable": None,
        "individual_key": SCHEMA["person_key"],
        "client_key": SCHEMA["client_key"],
        "label": f'{SCHEMA["label_field"]} == "{SCHEMA["label_positive"]}"',
        "splits": {k: int(len(v)) for k, v in splits.items()},
    }
    (out_dir / "meta" / "dataset_meta.json").write_text(json.dumps(meta, indent=2))

    # Partitions live beside the arrays. Without them the corpus builds but
    # validate_corpus, hfl_trainer, k_scaling and lira_attack all fail.
    part_dir = (Path(part_dir_override) if part_dir_override else
                out_dir.parent / "partitions" / "eicu")
    pmeta = write_partitions(part_dir, splits, client, n_clients, y, person,
                             n_edges=n_edges,
                             extra={"client_construction": client_report,
                                    "window_min": WINDOW_MIN,
                                    "slot_min": WINDOW_MIN / T_SLOTS,
                                    "signal_shape": list(A.shape),
                                    "clinical_shape": list(B.shape),
                                    "max_windows_per_stay": MAX_WINDOWS_PER_STAY},
                             verbose=verbose)

    if verbose:
        print("\n" + "=" * 66)
        print(f"  samples      : {meta['n_samples']:,}  shape {tuple(A.shape)}")
        print(f"  individuals  : {meta['n_individuals']:,}"
              f"   stays: {meta['n_stays']:,}")
        print(f"  clients      : {n_clients}  (pooled: {pooled})")
        print(f"  modality B   : {B.shape[1]}-d")
        print(f"  mortality    : {y.mean():.4f} overall, "
              f"{lo:.4f}-{hi:.4f} across clients")
        print(f"  splits       : { {k: len(v) for k, v in splits.items()} }")
        print(f"  partitions   : {part_dir}  ({n_clients} devices, "
              f"{n_edges} edges)")
        print("=" * 66)
    return splits, gid, client, y, n_clients, (lo, hi)


# ── synthetic fixture: proves the logic without the real tables ───────────
def _synthetic(n_people=1500, n_hosp=12, seed=0):
    rng = np.random.default_rng(seed)
    C = len(SCHEMA["vital_channels"])
    rows, stay_no = [], 100000
    for p in range(n_people):
        hosp = f"h{int(rng.integers(0, n_hosp)):02d}"
        person = f"p{p:05d}"
        for _stay in range(int(rng.integers(1, 3))):      # repeat admissions
            stay_no += 1
            y = int(rng.random() < 0.12)
            tab = list(rng.normal(size=len(SCHEMA["tabular_fields"]) + 1))
            for w in range(int(rng.integers(2, MAX_WINDOWS_PER_STAY + 1))):
                mask = (rng.random((C, T_SLOTS)) > 0.25).astype(np.float32)
                mask[0] = 1.0                              # heart rate always on
                rows.append({"stay": stay_no, "person": person, "hosp": hosp,
                             "y": y, "tab": tab, "win": w,
                             "vals": (rng.normal(size=(C, T_SLOTS)) * mask
                                      ).astype(np.float32),
                             "mask": mask})
    return rows


def self_test():
    """Prove the logic on a fixture shaped like eICU, before the real tables."""
    import tempfile
    print("SELF TEST — synthetic cohort shaped like eICU\n" + "=" * 66)
    rows = _synthetic()
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "eicu"
        part = Path(d) / "partitions" / "eicu"
        splits, gid, client, y, n_clients, prev = build_from_rows(
            rows, out, verbose=False, part_dir_override=part)

        ok = True
        gs = {k: set(np.unique(gid[v])) for k, v in splits.items()}
        overlap = [(a, b, len(gs[a] & gs[b]))
                   for a, b in (("train", "val"), ("train", "test"), ("val", "test"))
                   if gs[a] & gs[b]]
        print(f"  individuals per split: { {k: len(v) for k, v in gs.items()} }")
        print(f"  {'ok  ' if not overlap else 'FAIL'} splits are individual-disjoint"
              f"{'' if not overlap else f' — {overlap}'}")
        ok &= not overlap

        # A person with two admissions must not straddle a split. The previous
        # version selected candidates by window count > 20, which the fixture
        # never produces, so this check silently tested nothing. It now keys on
        # people who genuinely have more than one stay.
        person_of_row = np.asarray([r["person"] for r in rows])
        stay_of_row = np.asarray([str(r["stay"]) for r in rows])
        multi = [p for p in np.unique(person_of_row)
                 if len(np.unique(stay_of_row[person_of_row == p])) > 1]
        idx_of_person = {p: i for i, p in enumerate(np.unique(person_of_row))}
        multi_g = [idx_of_person[p] for p in multi]
        straddle = sum(1 for g in multi_g if sum(g in gs[k] for k in gs) > 1)
        print(f"  {'ok  ' if straddle == 0 else 'FAIL'} repeat admissions stay "
              f"on one side ({straddle} straddling of {len(multi_g)} checked)")
        ok &= straddle == 0 and len(multi_g) > 0

        total = sum(len(v) for v in splits.values())
        uniq = len(np.unique(np.concatenate(list(splits.values()))))
        print(f"  {'ok  ' if total == uniq else 'FAIL'} every sample in exactly "
              f"one split ({total} placed, {uniq} unique)")
        ok &= total == uniq

        A = np.load(out / "vitals" / "windows.npy", mmap_mode="r")
        want_c = 2 * len(SCHEMA["vital_channels"])
        shape_ok = A.ndim == 3 and A.shape[1] == want_c and A.shape[2] == T_SLOTS
        print(f"  {'ok  ' if shape_ok else 'FAIL'} modality A is [N, {want_c}, "
              f"{T_SLOTS}] for encoder_a — got {tuple(A.shape)}")
        ok &= shape_ok

        import json as _j
        pm = part / "partition_meta.json"
        files_ok = pm.exists() and all(
            (part / f"device_{d:02d}_{sp}.npy").exists()
            for d in range(n_clients) for sp in ("train", "val", "test"))
        print(f"  {'ok  ' if files_ok else 'FAIL'} partition files written for "
              f"all {n_clients} devices + partition_meta.json")
        ok &= files_ok

        if files_ok:
            pmj = _j.loads(pm.read_text())
            keys_ok = all(k in pmj for k in
                          ("n_devices", "n_edges", "edge_assignments", "devices"))
            print(f"  {'ok  ' if keys_ok else 'FAIL'} partition_meta carries "
                  f"n_devices / n_edges / edge_assignments / devices")
            ok &= keys_ok
            # every client must have a usable train AND test fold
            bad = [k for k, v in pmj["devices"].items()
                   if v["n_train"] == 0 or v["n_test"] == 0]
            print(f"  {'ok  ' if not bad else 'FAIL'} every client has a "
                  f"non-empty train and test fold ({len(bad)} bad)")
            ok &= not bad
            # patient-disjointness must survive the per-client stratification
            straddled = 0
            for dnum in range(n_clients):
                pass
            gsp = {}
            for sp in ("train", "val", "test"):
                allidx = np.concatenate([
                    np.load(part / f"device_{d:02d}_{sp}.npy")
                    for d in range(n_clients)]).astype(int)
                gsp[sp] = set(np.unique(gid[allidx]).tolist()) if len(allidx) else set()
            cross = (gsp["train"] & gsp["val"]) | (gsp["train"] & gsp["test"]) \
                    | (gsp["val"] & gsp["test"])
            print(f"  {'ok  ' if not cross else 'FAIL'} partitions are "
                  f"individual-disjoint across ALL clients ({len(cross)} shared)")
            ok &= not cross

        named = (out / "meta" / "case_ids.npy").exists()
        print(f"  {'ok  ' if named else 'FAIL'} group file is meta/case_ids.npy "
              f"(nine consumers hardcode this name)")
        ok &= named

        print(f"  ok   {n_clients} clients from hospitals; label prevalence "
              f"{prev[0]:.3f}-{prev[1]:.3f}")
        print(f"\n{'SELF TEST PASSED' if ok else 'SELF TEST FAILED'}")
        return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw_dir", default=None,
                    help="eICU-CRD CSVs (.csv or .csv.gz). "
                         f"Default: {DEFAULT_RAW_REL}")
    ap.add_argument("--out_dir", default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max_stays", type=int, default=None,
                    help="bound the cohort for a fast first pass")
    ap.add_argument("--chunk_rows", type=int, default=2_000_000)
    ap.add_argument("--max_windows", type=int, default=MAX_WINDOWS_PER_STAY,
                    help="hours of vitals per stay; sets the reachable k range")
    ap.add_argument("--scratch", default=None,
                    help="directory for the memory-mapped accumulator")
    ap.add_argument("--verify_schema", action="store_true",
                    help="check SCHEMA against real headers; reads no data values")
    ap.add_argument("--self_test", action="store_true",
                    help="validate the logic on a synthetic fixture")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    raw = Path(os.path.expanduser(a.raw_dir)) if a.raw_dir else _default_raw()
    if not raw.exists() or not any(raw.glob("patient.csv*")):
        print(f"no eICU tables found in {raw}\n"
              "Download them there first (see README.local.txt in that "
              "directory), or pass --raw_dir. To exercise the logic without "
              "data, run with --self_test.", file=sys.stderr)
        return 2
    if a.verify_schema:
        return verify_schema(raw)

    out = Path(a.out_dir) if a.out_dir else (
        Path(__file__).resolve().parents[2] / "data" / "processed" / "eicu")
    print(f"[eicu] raw_dir  {raw}\n[eicu] out_dir  {out}\n")
    stays = load_patient_table(raw, max_stays=a.max_stays)
    stays, lead_report = apply_lead_time_rule(stays)
    stay_list, mean, mask = stream_vitals(
        raw, stays, chunk_rows=a.chunk_rows, max_windows=a.max_windows,
        scratch=a.scratch or os.environ.get("TMPDIR", "."))
    rows = rows_from_streamed(stay_list, mean, mask, stays)
    print(f"[eicu] {len(rows):,} usable windows")
    build_from_rows(rows, out, seed=a.seed)
    print("\nNext:\n  python data/loaders/validate_corpus.py --datasets eicu"
          "\nand do not proceed past a CAPACITY failure.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
