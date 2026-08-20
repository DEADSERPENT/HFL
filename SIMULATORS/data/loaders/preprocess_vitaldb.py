"""
preprocess_vitaldb.py — VitalDB → HFL-MM pipeline arrays.

VitalDB (Lee et al., Scientific Data 9, 279, 2022) — 6,388 non-cardiac surgical
cases from Seoul National University Hospital, OPEN ACCESS on PhysioNet.
Every channel of a case comes from the SAME patient during the SAME operation,
time-aligned at capture by Vital Recorder across the SNUADC waveform digitiser,
the GE Solar8000 patient monitor and the Draeger Primus anaesthesia machine.
There is no pairing rule to defend.

TASK
----
    modality A : intraoperative monitoring, 18 channels x W steps @ 0.5 Hz
                 (9 numeric trends + 9 binary missingness masks)
    modality B : preoperative clinical + laboratory vector
    label      : postoperative ICU admission (icu_days > 0), 18.85 % positive
    clients    : surgical operation type (`optype`)

Both modalities genuinely inform the label — intraoperative haemodynamics and
preoperative comorbidity burden are independent evidence about whether a
patient will need intensive care. That is what makes this a real fusion task
rather than one modality plus decoration.

`death_inhosp` was rejected as the label: 57 of 6,388 cases (0.89 %) is too
rare to train or evaluate on this cohort.

FOUR CORRECTNESS CONTROLS
-------------------------
1. LEAKAGE — split BY CASE. All windows of one operation land in the same
   split, or windows minutes apart from the same patient would sit on both
   sides of the boundary.

2. LEAKAGE — modality B is PREOPERATIVE ONLY. Every `intraop_*` column
   (blood loss, transfusions, vasopressors) is excluded: those are known only
   after the operation, and `intraop_eph`/`intraop_phe` in particular are
   given *because* a patient is deteriorating, which is most of the outcome.

3. MISSINGNESS IS SIGNAL. An arterial line is placed only in sicker patients,
   so ART is absent in ~38 % of cases — and its absence is informative. Gaps
   are forward/backward-filled within the case and paired with an explicit
   binary mask channel, never silently zero-filled. Likewise the preoperative
   blood-gas panel is ~8 % complete; ordering an ABG at all signals acuity, so
   it becomes a single `abg_done` flag rather than six mostly-empty columns.

4. NAN-AWARE STATISTICS. Normalisation uses np.nanmean/np.nanstd over TRAIN
   cases only. With plain np.mean a single all-NaN channel makes the statistic
   NaN and propagates it to every window of every case — silently destroying
   that channel while training still reports an accuracy.

Output:
    data/processed/vitaldb/
        signals/windows.npy      (N, 18, W)  float32
        signals/labels.npy       (N,)        int64
        clinical/features.npy    (N, F)      float32
        meta/{case_ids,optype_ids}.npy, meta/*.json
    data/processed/partitions/vitaldb/
        device_XX_{train,val,test}.npy + partition_meta.json
"""

import os
import re
import json
import glob
import argparse
from collections import Counter

import numpy as np
import pandas as pd

# fetch_vitaldb.py writes 12 columns in this order:
FETCHED = ["ECG_II", "PLETH", "ART", "HR", "SPO2", "ART_MBP",
           "ETCO2", "BT", "NIBP_MBP", "RR_CO2", "FIO2", "MAC"]

# Only the 9 Solar8000/Primus NUMERIC trends are used. Columns 0-2 (SNUADC
# ECG_II, PLETH, ART) are 500 Hz WAVEFORMS point-sampled down to 0.5 Hz, which
# destroys them: one sample every 2 s lands at a random phase of the cardiac
# cycle. Measured on 400 raw cases — ECG_II median 0.01 mV but std 45.96;
# ART median 76 mmHg but std 3853. Those std values are recording artefact
# (electrocautery, line flushing, disconnection), not physiology, and no
# morphology survives at this rate. The monitor-derived numerics carry the
# same information properly: ART_MBP already gives mean arterial pressure, and
# arterial-line placement still registers through ART_MBP's missingness mask.
# Using raw waveforms would need a high-rate re-fetch — noted as future work.
KEEP_IDX     = [3, 4, 5, 6, 7, 8, 9, 10, 11]
SIGNAL_NAMES = [FETCHED[i] for i in KEEP_IDX]
FS = 0.5                       # Hz — one sample every 2 s

# Artefact clipping, in z units, applied AFTER standardisation and computed
# from TRAIN cases. Physiological channels carry impulsive artefacts (e.g. a
# single RR_CO2 sample at z=210 while p99.9 is 4.9). Left unclipped these
# dominate the loss; clipping at +/-10 SD keeps every real excursion while
# removing values no physiology produces.
CLIP_Z = 10.0

# Preoperative only. Demographics + risk + comorbidity + labs >=90 % complete.
DEMO_COLS = ["age", "height", "weight", "bmi"]
BIN_COLS  = ["emop", "preop_htn", "preop_dm"]
LAB_COLS  = ["preop_hb", "preop_plt", "preop_pt", "preop_aptt", "preop_na",
             "preop_k", "preop_gluc", "preop_alb", "preop_ast", "preop_alt",
             "preop_bun", "preop_cr"]
ABG_COLS  = ["preop_ph", "preop_hco3", "preop_be", "preop_pao2",
             "preop_paco2", "preop_sao2"]          # ~8 % complete -> one flag
# Never features: they are the label, its timing, the client id, or postop.
FORBIDDEN = {"icu_days", "death_inhosp", "caseid", "subjectid", "optype",
             "department", "adm", "dis", "casestart", "caseend",
             "anestart", "aneend", "opstart", "opend"}


def _case_id(path: str) -> int:
    return int(re.findall(r"\d+", os.path.basename(path))[-1])


def _numeric(cl: pd.DataFrame, cols) -> np.ndarray:
    """
    Coerce to float, handling VitalDB's de-identification of extreme ages.

    Ages of 90+ are stored as the STRING '>89' (8 cases), which makes the whole
    `age` column dtype=object and silently breaks a plain .to_numpy(float32).
    Mapped to 90 — the conventional floor for a censored age. No indicator
    flag: at 0.13 % of cases it would be near-constant and closer to a case
    identifier than a feature.
    """
    out = []
    for c in cols:
        s = cl[c]
        # is_numeric_dtype, NOT `s.dtype == object`: pandas 3.x reports this
        # column as dtype 'str', so an object check silently never fires and
        # the '>89' rows reach np.float32 unconverted.
        if not pd.api.types.is_numeric_dtype(s):
            s = (s.astype("object").astype(str).str.strip()
                  .str.replace(r"^>\s*89$", "90", regex=True))
            s = pd.to_numeric(s, errors="coerce")
        out.append(np.asarray(s, dtype=np.float32))
    return np.stack(out, axis=1)


def build_clinical_features(cl: pd.DataFrame):
    """Preoperative feature matrix + column names. No intraop/postop columns."""
    for c in FORBIDDEN:
        assert c not in DEMO_COLS + BIN_COLS + LAB_COLS, f"leakage: {c}"
    assert not any(c.startswith("intraop_") for c in DEMO_COLS + BIN_COLS + LAB_COLS)

    parts, names = [], []
    parts.append(_numeric(cl, DEMO_COLS)); names += DEMO_COLS
    parts.append((cl["sex"].astype(str).str.upper().str[0] == "M")
                 .to_numpy(np.float32)[:, None]); names.append("sex_is_m")
    parts.append(_numeric(cl, ["asa"])); names.append("asa")
    parts.append(_numeric(cl, BIN_COLS)); names += BIN_COLS
    parts.append(_numeric(cl, LAB_COLS)); names += LAB_COLS
    # missingness indicators — a lab not drawn is a clinical decision
    parts.append(cl[LAB_COLS].isna().to_numpy(np.float32))
    names += [f"{c}_missing" for c in LAB_COLS]
    parts.append(cl[ABG_COLS].notna().any(axis=1).to_numpy(np.float32)[:, None])
    names.append("abg_done")
    return np.concatenate(parts, axis=1).astype(np.float32), names


def window_case(arr: np.ndarray, win: int, max_windows: int):
    """
    (T,12) with NaNs -> list of (2C,win) windows: C imputed signals stacked
    with C binary observed-masks, where C = len(KEEP_IDX) = 9.

    Forward-fill then backward-fill WITHIN the case: a monitor reading persists
    until the next one, so carrying it forward is the physiologically correct
    reconstruction. Channels never observed at all stay NaN here and are set to
    the channel mean after normalisation, with their mask pinned at 0.
    """
    arr = arr[:, KEEP_IDX]                             # drop point-sampled waveforms
    obs = (~np.isnan(arr)).astype(np.float32)          # (T,C) 1 = measured
    df = pd.DataFrame(arr).ffill().bfill()             # within-case only
    filled = df.to_numpy(np.float32)

    T = len(filled)
    if T < win:
        return []
    n = min(T // win, max_windows)
    # Take the LAST n windows: the end of the operation is the most
    # informative period for a postoperative outcome.
    out = []
    for k in range(n):
        e = T - k * win
        s = e - win
        out.append(np.concatenate([filled[s:e].T, obs[s:e].T], axis=0))  # (24,win)
    return out[::-1]                                    # chronological


def merge_low_positive_clients(labels_by_case, optype_of_case, optypes,
                               min_positives: int):
    """
    Fold operation types that cannot supply `min_positives` positive CASES into
    one composite low-acuity client, smallest-prevalence first.

    Why this is necessary rather than cosmetic: Breast surgery has 1 ICU
    admission in 433 cases and Thyroid 3 in 257. After a 70/15/15 split such a
    client holds ZERO positives in training, so every gradient it contributes
    pushes the global model toward the negative class, and its local validation
    AUC is undefined. That is not "few-shot learning from rare positives", it is
    a client with one class.

    Why MERGE rather than drop: no case is discarded — 690 cases and their
    windows are retained, they simply share a client. The composite stays
    clinically coherent (the merged services are the low-ICU-risk ones), and
    heterogeneity remains severe: prevalence still spans roughly 3 %-51 %.

    Set --min_positives 0 to keep every optype separate and reproduce the
    unmerged, label-degenerate configuration.
    """
    order = sorted(range(len(optypes)),
                   key=lambda o: labels_by_case[optype_of_case == o].mean()
                   if (optype_of_case == o).any() else 0.0)
    merged, group = [], []
    for o in order:
        group.append(o)
        pos = int(labels_by_case[np.isin(optype_of_case, group)].sum())
        if pos >= min_positives:
            merged.append(list(group)); group = []
    if group:                       # leftovers join the last viable client
        if merged:
            merged[-1] += group
        else:
            merged.append(group)
    # untouched clients keep their own identity
    singles = [m for m in merged if len(m) == 1]
    combos = [m for m in merged if len(m) > 1]
    return combos + singles


def stratified_case_split(case_opt, case_lab, train=0.70, val=0.15, seed=42):
    """
    Split CASES (never windows) inside each client, stratified by outcome.

    Clients are operation types whose ICU base rate ranges from 0.2 % (Breast)
    to 50.7 % (Major resection). Stratifying within a client keeps that base
    rate intact in every split; low-prevalence clients simply contribute few
    positives, which is the real deployment condition, not a defect.
    """
    rng = np.random.default_rng(seed)
    tr, va, te = {}, {}, {}
    for o in np.unique(case_opt):
        tr[o], va[o], te[o] = [], [], []
        for y in (0, 1):
            ids = np.where((case_opt == o) & (case_lab == y))[0]
            rng.shuffle(ids)
            n = len(ids); a, b = int(n * train), int(n * (train + val))
            tr[o] += ids[:a].tolist(); va[o] += ids[a:b].tolist(); te[o] += ids[b:].tolist()
    return tr, va, te


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw_dir", default="data/raw/vitaldb")
    p.add_argument("--out_dir", default="data/processed/vitaldb")
    p.add_argument("--partition_dir", default="data/processed/partitions/vitaldb")
    p.add_argument("--window_min", type=float, default=10.0)
    p.add_argument("--max_windows", type=int, default=8,
                   help="Cap per case so long operations cannot dominate")
    p.add_argument("--min_positives", type=int, default=10,
                   help="Minimum positive CASES per client. Operation types "
                        "below this are merged into one low-acuity client. "
                        "0 = keep every optype separate (label-degenerate).")
    p.add_argument("--n_edges", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    win = int(args.window_min * 60 * FS)          # 10 min @0.5 Hz = 300 steps
    print(f"  channels: {len(KEEP_IDX)} numeric trends + {len(KEEP_IDX)} masks "
          f"= {2*len(KEEP_IDX)}  (raw waveforms dropped, see module docstring)")
    print("=" * 70)
    print("  VitalDB → HFL-MM preprocessing")
    print("  Lee et al., Sci Data 2022 · open access · same patient/second")
    print(f"  window={args.window_min:g} min ({win} steps @{FS} Hz), "
          f"max {args.max_windows}/case")
    print("=" * 70)

    cl = pd.read_csv(os.path.join(args.raw_dir, "clinical_data.csv"), low_memory=False)
    cl = cl.set_index("caseid")
    files = sorted(glob.glob(os.path.join(args.raw_dir, "cases", "*.npy")), key=_case_id)

    Xs, Yb, CID = [], [], []                       # windows, label, case id
    kept_cases = []
    for f in files:
        cid = _case_id(f)
        if cid not in cl.index:
            continue
        row = cl.loc[cid]
        if pd.isna(row.get("optype")):
            continue
        w = window_case(np.load(f), win, args.max_windows)
        if not w:
            continue
        y = int((0 if pd.isna(row["icu_days"]) else row["icu_days"]) > 0)
        Xs.extend(w); Yb.extend([y] * len(w)); CID.extend([cid] * len(w))
        kept_cases.append(cid)

    X = np.stack(Xs).astype(np.float32)            # (N,24,win)
    y = np.array(Yb, dtype=np.int64)
    cid_arr = np.array(CID, dtype=np.int64)
    del Xs
    print(f"\n  cases used : {len(kept_cases):,} of {len(files):,}")
    print(f"  windows    : {len(y):,}   ({len(y)/max(len(kept_cases),1):.1f} per case)")
    print(f"  ICU rate   : windows {y.mean()*100:.2f}%  |  "
          f"cases {cl.loc[kept_cases,'icu_days'].fillna(0).gt(0).mean()*100:.2f}%")

    sub = cl.loc[kept_cases]
    B_all, feat_names = build_clinical_features(sub)
    case_pos = {c: i for i, c in enumerate(kept_cases)}
    B = B_all[[case_pos[c] for c in cid_arr]]      # broadcast case -> its windows

    optypes = sorted(sub["optype"].unique())
    o2i = {o: i for i, o in enumerate(optypes)}
    case_opt_raw = np.array([o2i[sub.loc[c, "optype"]] for c in kept_cases])
    case_lab = np.array([int((0 if pd.isna(sub.loc[c, "icu_days"])
                              else sub.loc[c, "icu_days"]) > 0) for c in kept_cases])

    # Fold label-degenerate operation types into one low-acuity client.
    if args.min_positives > 0:
        groups = merge_low_positive_clients(case_lab, case_opt_raw, optypes,
                                            args.min_positives)
    else:
        groups = [[o] for o in range(len(optypes))]
    client_names = [" + ".join(optypes[o] for o in g) if len(g) > 1
                    else optypes[g[0]] for g in groups]
    o2c = {o: ci for ci, g in enumerate(groups) for o in g}
    case_opt = np.array([o2c[o] for o in case_opt_raw])
    n_clients = len(groups)
    merged_note = [(client_names[i], len(groups[i]))
                   for i in range(n_clients) if len(groups[i]) > 1]
    if merged_note:
        for nm, k in merged_note:
            print(f"\n  [merge] {k} operation types -> one client: {nm}")
    print(f"  clients: {n_clients} (from {len(optypes)} operation types)")

    tr_c, va_c, te_c = stratified_case_split(case_opt, case_lab, seed=args.seed)

    # case index -> window indices
    w_of_case = {}
    for i, c in enumerate(cid_arr):
        w_of_case.setdefault(c, []).append(i)
    kc = np.array(kept_cases)
    to_w = lambda cs: (np.concatenate([w_of_case[kc[i]] for i in cs])
                       if cs else np.array([], dtype=int))
    tr = [to_w(tr_c[o]) for o in range(n_clients)]
    va = [to_w(va_c[o]) for o in range(n_clients)]
    te = [to_w(te_c[o]) for o in range(n_clients)]
    train_idx = np.concatenate(tr)

    # ---- normalise: TRAIN-ONLY and NAN-AWARE --------------------------------
    C = len(KEEP_IDX)
    sig, msk = X[:, :C], X[:, C:]
    m_s = np.nanmean(sig[train_idx], axis=(0, 2), keepdims=True)
    s_s = np.nanstd(sig[train_idx],  axis=(0, 2), keepdims=True) + 1e-8
    sig = np.nan_to_num((sig - m_s) / s_s, nan=0.0)    # 0 == channel mean
    n_clip = int((np.abs(sig) > CLIP_Z).sum())
    sig = np.clip(sig, -CLIP_Z, CLIP_Z)                # impulsive artefacts
    print(f"  artefact clipping: {n_clip:,} values beyond ±{CLIP_Z:g} SD "
          f"({n_clip/sig.size*100:.4f}%)")
    X = np.concatenate([sig, msk], axis=1).astype(np.float32)
    m_b = np.nanmean(B[train_idx], 0, keepdims=True)
    s_b = np.nanstd(B[train_idx],  0, keepdims=True) + 1e-8
    B = np.nan_to_num((B - m_b) / s_b, nan=0.0).astype(np.float32)
    assert not np.isnan(X).any() and not np.isnan(B).any(), "NaN survived"

    for sd in ("signals", "clinical", "meta"):
        os.makedirs(os.path.join(args.out_dir, sd), exist_ok=True)
    os.makedirs(args.partition_dir, exist_ok=True)
    # Remove stale device_*.npy from an earlier run with a different client
    # count. Without this, reducing the number of clients leaves orphaned
    # device_NN files behind that the verifier (rightly) flags and that a
    # later run could silently pick up.
    for _old in glob.glob(os.path.join(args.partition_dir, "device_*.npy")):
        os.remove(_old)
    np.save(f"{args.out_dir}/signals/windows.npy", X)
    np.save(f"{args.out_dir}/signals/labels.npy", y)
    np.save(f"{args.out_dir}/clinical/features.npy", B)
    np.save(f"{args.out_dir}/meta/case_ids.npy", cid_arr)
    np.save(f"{args.out_dir}/meta/optype_ids.npy",
            np.array([o2i[sub.loc[c, "optype"]] for c in cid_arr]))

    edge_assign = {e: [] for e in range(args.n_edges)}
    for d in range(n_clients):
        edge_assign[d % args.n_edges].append(d)
    d2e = {d: e for e, ds in edge_assign.items() for d in ds}

    devices, dev_rows = {}, []
    for d, o in enumerate(client_names):
        np.save(f"{args.partition_dir}/device_{d:02d}_train.npy", tr[d])
        np.save(f"{args.partition_dir}/device_{d:02d}_val.npy",   va[d])
        np.save(f"{args.partition_dir}/device_{d:02d}_test.npy",  te[d])
        allw = np.concatenate([tr[d], va[d], te[d]]).astype(int)
        devices[str(d)] = {
            "optype": o, "edge_id": int(d2e[d]),
            "n_train": int(len(tr[d])), "n_val": int(len(va[d])),
            "n_test": int(len(te[d])), "total": int(len(allw)),
            "n_cases": int(len(tr_c[d]) + len(va_c[d]) + len(te_c[d])),
            "icu_rate_pct": round(float(y[allw].mean() * 100), 2) if len(allw) else 0.0,
            "class_distribution": {str(k): int(v) for k, v in
                                   sorted(Counter(y[allw].tolist()).items())},
        }
        dev_rows.append((d, o, devices[str(d)]))

    meta = {
        "dataset": "VitalDB", "citation": "Lee et al., Sci Data 9:279, 2022",
        "licence": "open access (PhysioNet)", "domain": "clinical_iomt",
        "pairing": "same patient, same second (Vital Recorder)",
        "label": "postoperative ICU admission (icu_days > 0)",
        "seed": args.seed, "total_samples": int(len(y)),
        "n_devices": n_clients, "n_classes": 2,
        "client_names": client_names,
        "min_positives": args.min_positives,
        "n_optypes_before_merge": len(optypes),
        "n_edges": args.n_edges,
        "edge_assignments": {str(k): v for k, v in edge_assign.items()},
        "devices": devices,
        "client_key": "optype (low-acuity types merged, see min_positives)",
        "window_min": args.window_min, "fs_hz": FS,
        "signal_shape": list(X.shape), "clinical_shape": list(B.shape),
        "signal_channels": SIGNAL_NAMES + [f"{s}_observed" for s in SIGNAL_NAMES],
        "clinical_features": feat_names,
        "split": "by CASE, stratified by outcome within each optype (no case spans splits)",
        "n_cases": len(kept_cases),
    }
    json.dump(meta, open(f"{args.partition_dir}/partition_meta.json", "w"), indent=2)
    json.dump(meta, open(f"{args.out_dir}/meta/dataset_meta.json", "w"), indent=2)
    json.dump({"signal_mean": m_s.ravel().tolist(), "signal_std": s_s.ravel().tolist(),
               "note": "TRAIN cases only, nan-aware"},
              open(f"{args.out_dir}/meta/norm_stats.json", "w"), indent=2)

    print(f"\n  signals={X.shape}  clinical={B.shape}  features={len(feat_names)}")
    print(f"  train={len(train_idx):,}  val={sum(len(v) for v in va):,}  "
          f"test={sum(len(t) for t in te):,}")
    print(f"\n  {'client':<34}{'cases':>7}{'windows':>9}{'ICU%':>7}{'edge':>6}")
    for d, o, m in dev_rows:
        print(f"  {d:>2} {o:<31}{m['n_cases']:>7}{m['total']:>9}"
              f"{m['icu_rate_pct']:>7.1f}{m['edge_id']:>6}")
    print(f"\n[SAVED] {args.out_dir}  and  {args.partition_dir}")


if __name__ == "__main__":
    main()
