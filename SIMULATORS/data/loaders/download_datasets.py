"""
Dataset Downloader — Healthcare Domain Only
  Modality A (Signal)  : PTB-XL 12-lead ECG        — PhysioNet (free, auto)
  Modality B (Image)   : Kermany Chest X-Ray        — Kaggle   (API key needed)
  Modality C (Tabular) : PTB-XL metadata CSV        — included with PTB-XL
"""

import os
import sys
import argparse


# ── PTB-XL ────────────────────────────────────────────────────────────────────

PTBXL_SUPERCLASS_MAP = {"NORM": 0, "MI": 1, "STTC": 2, "CD": 3, "HYP": 4}


def _select_ptbxl_subset(output_dir: str, n_records: int = 5500,
                          seed: int = 42) -> list:
    """
    Read ptbxl_database.csv (already downloaded), pick a stratified subset
    of n_records (equal per class), return list of filename_lr strings.
    """
    import ast
    import pandas as pd

    df = pd.read_csv(os.path.join(output_dir, "ptbxl_database.csv"),
                     index_col="ecg_id")
    df["scp_codes"] = df["scp_codes"].apply(ast.literal_eval)

    scp_df = pd.read_csv(os.path.join(output_dir, "scp_statements.csv"),
                         index_col=0)
    superclass_map = scp_df[scp_df["diagnostic"] == 1]["diagnostic_class"].to_dict()

    def get_superclass(scp_codes):
        best, best_conf = None, 0.0
        for code, conf in scp_codes.items():
            if code in superclass_map and conf >= best_conf:
                best, best_conf = superclass_map[code], conf
        return best

    df["superclass"] = df["scp_codes"].apply(get_superclass)
    df = df.dropna(subset=["superclass"])
    df = df[df["superclass"].isin(PTBXL_SUPERCLASS_MAP)]

    n_per_class = n_records // len(PTBXL_SUPERCLASS_MAP)
    parts = []
    for cls in PTBXL_SUPERCLASS_MAP:
        pool = df[df["superclass"] == cls]
        parts.append(pool.sample(n=min(n_per_class, len(pool)), random_state=seed))

    subset = pd.concat(parts)
    print(f"Stratified subset: {len(subset):,} records "
          f"(~{n_per_class} per class × {len(PTBXL_SUPERCLASS_MAP)} classes)")
    for cls in PTBXL_SUPERCLASS_MAP:
        print(f"  {cls}: {(subset['superclass'] == cls).sum():,}")

    return subset["filename_lr"].tolist()


def download_ptbxl(output_dir: str = "data/raw/ptb-xl",
                   n_records: int = 5500,
                   seed: int = 42):
    """
    Selective PTB-XL download:
      1. Download metadata CSVs only  (~few KB)
      2. Pick a stratified subset of n_records
      3. Download only those .dat + .hea files  (~400–500 MB for 5500 records)
    Saves ~75% bandwidth vs full 1.7 GB download.
    """
    try:
        import wfdb
    except ImportError:
        print("Installing wfdb...")
        os.system(f"{sys.executable} -m pip install wfdb --quiet")
        import wfdb

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "ptbxl_database.csv")
    marker   = os.path.join(output_dir, ".download_complete")

    if os.path.exists(marker):
        import pandas as pd
        n = len(pd.read_csv(csv_path))
        print(f"[SKIP] PTB-XL already downloaded: {n:,} records at {output_dir}")
        return

    # ── Step 1: metadata CSVs only ────────────────────────────────────────────
    if not os.path.exists(csv_path):
        print("Step 1/3 — Downloading PTB-XL metadata CSVs...")
        wfdb.dl_files("ptb-xl", output_dir,
                      ["ptbxl_database.csv", "scp_statements.csv"])
        print("  Metadata downloaded.")
    else:
        print("Step 1/3 — Metadata CSVs already present, skipping.")

    # ── Step 2: stratified subset selection ───────────────────────────────────
    print(f"\nStep 2/3 — Selecting {n_records:,} records (stratified)...")
    filenames = _select_ptbxl_subset(output_dir, n_records, seed)

    # ── Step 3: download only the selected record files ───────────────────────
    files_to_fetch = []
    for fn in filenames:
        # fn looks like "records100/00000/00001_lr"
        # Need both the signal (.dat) and header (.hea) files
        files_to_fetch.append(fn + ".dat")
        files_to_fetch.append(fn + ".hea")

    n_files = len(files_to_fetch)
    est_mb  = n_records * 0.08   # ~80 KB per record pair at 100 Hz
    print(f"\nStep 3/3 — Downloading {n_files:,} record files "
          f"(~{est_mb:.0f} MB estimated)...")
    print("This is ~25% of the full PTB-XL dataset. Please wait...")

    wfdb.dl_files("ptb-xl", output_dir, files_to_fetch)

    # Write marker so re-runs skip the download
    with open(marker, "w") as f:
        f.write(f"n_records={n_records}\nseed={seed}\n")

    import pandas as pd
    df = pd.read_csv(csv_path)
    print(f"\n[OK] PTB-XL selective download complete.")
    print(f"     {n_records:,} records downloaded  (full DB has {len(df):,})")
    print(f"     Saved to: {output_dir}")


# ── Kermany Chest X-Ray (Pneumonia) ───────────────────────────────────────────

def download_chest_xray(output_dir: str = "data/raw/chest-xray-pneumonia"):
    """
    Download Kermany 2018 Chest X-Ray dataset from Kaggle.
    Dataset: paultimothymooney/chest-xray-pneumonia
    Paper:   Kermany et al., Cell 2018 (citable, peer-reviewed)
    Size:    ~1.15 GB  |  5,863 JPEG images  |  NORMAL / PNEUMONIA
    """
    marker = os.path.join(output_dir, "chest_xray", "train", "NORMAL")
    if os.path.isdir(marker) and len(os.listdir(marker)) > 100:
        print(f"[SKIP] Chest X-Ray already present at {output_dir}")
        return

    print("\nDownloading Kermany Chest X-Ray dataset from Kaggle...")
    print("You need a Kaggle API key. Get it at:")
    print("  kaggle.com → Your Profile → Account → Create New API Token")
    print("  (downloads kaggle.json — you only need username + key from it)\n")

    try:
        import opendatasets as od
    except ImportError:
        print("Installing opendatasets...")
        os.system(f"{sys.executable} -m pip install opendatasets --quiet")
        import opendatasets as od

    os.makedirs(output_dir, exist_ok=True)

    # opendatasets downloads into a subfolder named after the dataset slug
    parent = os.path.dirname(output_dir) or "."
    od.download(
        "https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia",
        data_dir=parent
    )

    if os.path.isdir(marker):
        n_normal = len(os.listdir(marker))
        pneumonia_dir = os.path.join(output_dir, "chest_xray", "train", "PNEUMONIA")
        n_pneumonia = len(os.listdir(pneumonia_dir))
        print(f"[OK] Chest X-Ray complete: {n_normal} NORMAL + {n_pneumonia} PNEUMONIA (train)")
    else:
        _print_manual_instructions(output_dir)


def _print_manual_instructions(output_dir: str):
    print("\n" + "=" * 68)
    print("CHEST X-RAY — MANUAL DOWNLOAD (if opendatasets failed)")
    print("=" * 68)
    print()
    print("Option A — Kaggle CLI:")
    print("  pip install kaggle")
    print("  # Place kaggle.json in ~/.kaggle/kaggle.json then run:")
    print(f"  kaggle datasets download -d paultimothymooney/chest-xray-pneumonia \\")
    print(f"         --unzip -p {os.path.dirname(output_dir)}")
    print()
    print("Option B — Browser:")
    print("  1. Go to: kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia")
    print("  2. Click Download (ZIP ~1.15 GB)")
    print(f"  3. Extract so that this path exists:")
    print(f"     {output_dir}/chest_xray/train/NORMAL/")
    print("=" * 68)


# ── Verification ───────────────────────────────────────────────────────────────

def verify(ptbxl_dir: str, cxr_dir: str):
    print("\n--- VERIFICATION ---")

    # PTB-XL
    csv    = os.path.join(ptbxl_dir, "ptbxl_database.csv")
    marker = os.path.join(ptbxl_dir, ".download_complete")
    if os.path.exists(csv) and os.path.exists(marker):
        with open(marker) as f:
            info = f.read().strip()
        print(f"[OK] PTB-XL       : selective download complete ({info})  → {ptbxl_dir}")
    elif os.path.exists(csv):
        print(f"[PARTIAL] PTB-XL metadata present but records not yet downloaded → {ptbxl_dir}")
        print(f"          Run: python data/loaders/download_datasets.py")
    else:
        print(f"[MISSING] PTB-XL not found at {ptbxl_dir}")

    # PTB-XL tabular metadata (included in PTB-XL, no separate download)
    scp = os.path.join(ptbxl_dir, "scp_statements.csv")
    if os.path.exists(scp):
        print(f"[OK] PTB-XL meta  : scp_statements.csv present (tabular modality)")
    else:
        print(f"[MISSING] scp_statements.csv not found — re-download PTB-XL")

    # Chest X-Ray
    train_normal = os.path.join(cxr_dir, "chest_xray", "train", "NORMAL")
    train_pneumo = os.path.join(cxr_dir, "chest_xray", "train", "PNEUMONIA")
    test_normal  = os.path.join(cxr_dir, "chest_xray", "test",  "NORMAL")
    test_pneumo  = os.path.join(cxr_dir, "chest_xray", "test",  "PNEUMONIA")

    if all(os.path.isdir(d) for d in [train_normal, train_pneumo]):
        n = len(os.listdir(train_normal)) + len(os.listdir(test_normal or ""))
        p = len(os.listdir(train_pneumo)) + len(os.listdir(test_pneumo or ""))
        print(f"[OK] Chest X-Ray  : {n} NORMAL + {p} PNEUMONIA images → {cxr_dir}")
    else:
        print(f"[MISSING] Chest X-Ray not found at {cxr_dir}")
        _print_manual_instructions(cxr_dir)

    print()
    print("Ready to run: python data/loaders/preprocess_healthcare.py")


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download healthcare datasets (PTB-XL ECG + Chest X-Ray)"
    )
    parser.add_argument("--ptbxl_dir",  default="data/raw/ptb-xl")
    parser.add_argument("--cxr_dir",    default="data/raw/chest-xray-pneumonia")
    parser.add_argument("--n_records",  type=int, default=5500,
                        help="PTB-XL records to download (stratified, default 5500)")
    parser.add_argument("--skip_ptbxl", action="store_true",
                        help="Skip PTB-XL if already downloaded")
    parser.add_argument("--skip_cxr",   action="store_true",
                        help="Skip Chest X-Ray if already downloaded")
    parser.add_argument("--verify_only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify(args.ptbxl_dir, args.cxr_dir)
        sys.exit(0)

    print("Healthcare Dataset Downloader")
    print("=" * 50)
    print("Modality A : PTB-XL ECG       (Signal / Time-series)")
    print("Modality B : Kermany Chest CXR (Image — JPEG, RGB)")
    print("Modality C : PTB-XL metadata  (Tabular — included with A)")
    print("=" * 50)

    if not args.skip_ptbxl:
        download_ptbxl(args.ptbxl_dir, n_records=args.n_records)

    if not args.skip_cxr:
        download_chest_xray(args.cxr_dir)

    verify(args.ptbxl_dir, args.cxr_dir)
