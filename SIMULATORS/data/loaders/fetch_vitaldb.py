"""
fetch_vitaldb.py — pull VitalDB intraoperative signals, one .npy per case.

VitalDB (Lee et al., Scientific Data 9, 279, 2022) — 6,388 non-cardiac surgical
cases from Seoul National University Hospital. OPEN ACCESS on PhysioNet, no
credentialing. This is genuine hospital machine data: anaesthesia monitors and
the Solar8000 patient monitor, recorded intraoperatively.

Why the track-level API instead of the .vital files
---------------------------------------------------
A full .vital case is ~21 MB (134 GB for the cohort). `vitaldb.load_case` pulls
only the requested channels at the requested rate: ~2 s and ~196 KB per case,
so the whole cohort lands in ~1.3 GB and a few hours, unattended.

Channel choice
--------------
Twelve channels, chosen by measured coverage across sampled cases at 0.5 Hz, so
the tensor is (12, T) and drops straight into the existing `encoder_a` contract
(12 leads → 256-d) with no architecture change:

    SNUADC/ECG_II  99.9% | SNUADC/PLETH 99.9% | Solar8000/PLETH_SPO2 88.9%
    Solar8000/HR   88.3% | Solar8000/ETCO2 72.4% | Solar8000/FIO2 72.4%
    Solar8000/NIBP_MBP 67.5% | Solar8000/RR_CO2 58.5% | SNUADC/ART 50.0%
    Solar8000/ART_MBP 44.1% | Solar8000/BT 40.4% | Primus/MAC 23.9%

Lower-coverage channels are kept deliberately: an arterial line is only placed
in sicker patients, so ART presence is itself clinically informative. Missing
values are preserved as NaN here and handled (ffill + missingness mask) at
window-building time, NOT silently zero-filled.

Resumable: existing per-case files are skipped, so it is safe to re-run.
"""

import os
import time
import argparse

import numpy as np
import pandas as pd

TRACKS = [
    "SNUADC/ECG_II", "SNUADC/PLETH", "SNUADC/ART",
    "Solar8000/HR", "Solar8000/PLETH_SPO2", "Solar8000/ART_MBP",
    "Solar8000/ETCO2", "Solar8000/BT", "Solar8000/NIBP_MBP",
    "Solar8000/RR_CO2", "Solar8000/FIO2", "Primus/MAC",
]
INTERVAL_S = 2.0     # 0.5 Hz — the rate at which Solar8000 numerics are populated


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out_dir", default="data/raw/vitaldb/cases")
    p.add_argument("--clinical", default="data/raw/vitaldb/clinical_data.csv")
    p.add_argument("--limit", type=int, default=0, help="0 = all cases")
    p.add_argument("--min_minutes", type=float, default=20.0,
                   help="Skip cases shorter than this (too short to window)")
    args = p.parse_args()

    import vitaldb

    os.makedirs(args.out_dir, exist_ok=True)
    cl = pd.read_csv(args.clinical, low_memory=False)
    dur_min = (cl["opend"] - cl["opstart"]) / 60.0
    cl = cl[dur_min >= args.min_minutes]
    ids = cl["caseid"].tolist()
    if args.limit:
        ids = ids[:args.limit]

    print(f"[VitalDB] {len(ids)} cases ≥{args.min_minutes:.0f} min | "
          f"{len(TRACKS)} tracks @ {1/INTERVAL_S:.1f} Hz -> {args.out_dir}", flush=True)

    ok = skip = fail = 0
    t0 = time.time()
    for i, cid in enumerate(ids, 1):
        dst = os.path.join(args.out_dir, f"case_{cid:05d}.npy")
        if os.path.exists(dst):
            skip += 1
            continue
        try:
            a = vitaldb.load_case(cid, TRACKS, INTERVAL_S)
            if a is None or len(a) < 10:
                fail += 1
                continue
            np.save(dst, a.astype(np.float32))    # (T, 12), NaNs preserved
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  [warn] case {cid}: {type(e).__name__}: {str(e)[:70]}", flush=True)

        if i % 100 == 0 or i == len(ids):
            el = time.time() - t0
            rate = i / max(el, 1e-9)
            print(f"  {i}/{len(ids)}  ok={ok} skip={skip} fail={fail}  "
                  f"{rate:.2f} case/s  eta={((len(ids)-i)/max(rate,1e-9))/60:.0f} min",
                  flush=True)

    print(f"[VitalDB] done: ok={ok} skipped={skip} failed={fail} "
          f"in {(time.time()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
