"""
Dataset downloader for Phase 5 Healthcare datasets.
  - PTB-XL: automatic download via wfdb from PhysioNet (free, no registration)
  - CheXpert: manual download (Stanford registration required)
"""

import os
import sys
import argparse


def download_ptbxl(output_dir: str = "data/raw/ptb-xl"):
    """Download PTB-XL dataset from PhysioNet using wfdb."""
    try:
        import wfdb
    except ImportError:
        print("Installing wfdb...")
        os.system(f"{sys.executable} -m pip install wfdb --quiet")
        import wfdb

    os.makedirs(output_dir, exist_ok=True)

    print(f"Downloading PTB-XL to {output_dir}")
    print("Size: ~1.7 GB. This may take 5-15 minutes depending on connection.")

    wfdb.dl_database("ptb-xl", dl_dir=output_dir)

    # Verify download
    csv_path = os.path.join(output_dir, "ptbxl_database.csv")
    if os.path.exists(csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        print(f"PTB-XL download complete: {len(df):,} records")
        print(f"Location: {os.path.abspath(output_dir)}")
    else:
        print("ERROR: ptbxl_database.csv not found after download.")
        sys.exit(1)


def print_chexpert_instructions(output_dir: str = "data/raw/chexpert"):
    """CheXpert requires manual Stanford registration — print instructions."""
    print("\n" + "=" * 70)
    print("CHEXPERT DOWNLOAD — MANUAL STEP REQUIRED")
    print("=" * 70)
    print()
    print("CheXpert is free for non-commercial research but requires")
    print("registration with Stanford University.")
    print()
    print("STEPS:")
    print("  1. Go to: https://stanfordmlgroup.github.io/competitions/chexpert/")
    print("  2. Click 'Request Dataset Access'")
    print("  3. Fill the form (name, institution, email)")
    print("  4. Download: CheXpert-v1.0-small.zip (~11 GB downsampled version)")
    print("  5. Extract to:", os.path.abspath(output_dir))
    print()
    print("EXPECTED STRUCTURE after extraction:")
    print(f"  {output_dir}/")
    print(f"  ├── train/")
    print(f"  │   ├── patient00001/study1/view1_frontal.jpg")
    print(f"  │   └── ...")
    print(f"  ├── valid/")
    print(f"  ├── train.csv")
    print(f"  └── valid.csv")
    print()
    print("NOTE: Use the SMALL version (320×320 downsampled).")
    print("      Full resolution (~439 GB) is NOT needed.")
    print("=" * 70)


def verify_downloads(ptbxl_dir: str, chexpert_dir: str):
    """Check both datasets are present and print status."""
    print("\n--- DOWNLOAD VERIFICATION ---")

    # PTB-XL check
    ptbxl_csv = os.path.join(ptbxl_dir, "ptbxl_database.csv")
    if os.path.exists(ptbxl_csv):
        import pandas as pd
        df = pd.read_csv(ptbxl_csv)
        print(f"[OK] PTB-XL: {len(df):,} records at {ptbxl_dir}")
    else:
        print(f"[MISSING] PTB-XL not found at {ptbxl_dir}")

    # CheXpert check
    chexpert_csv = os.path.join(chexpert_dir, "train.csv")
    if os.path.exists(chexpert_csv):
        import pandas as pd
        df = pd.read_csv(chexpert_csv)
        print(f"[OK] CheXpert: {len(df):,} records at {chexpert_dir}")
    else:
        print(f"[MISSING] CheXpert not found at {chexpert_dir}")
        print(f"          Follow instructions above to download manually.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Phase 5 healthcare datasets")
    parser.add_argument("--ptbxl_dir", default="data/raw/ptb-xl")
    parser.add_argument("--chexpert_dir", default="data/raw/chexpert")
    parser.add_argument("--skip_ptbxl", action="store_true")
    parser.add_argument("--verify_only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify_downloads(args.ptbxl_dir, args.chexpert_dir)
        sys.exit(0)

    print("Phase 5 Dataset Downloader")
    print("=" * 50)

    if not args.skip_ptbxl:
        download_ptbxl(args.ptbxl_dir)
    else:
        print("Skipping PTB-XL download (--skip_ptbxl set).")

    print_chexpert_instructions(args.chexpert_dir)
    verify_downloads(args.ptbxl_dir, args.chexpert_dir)
