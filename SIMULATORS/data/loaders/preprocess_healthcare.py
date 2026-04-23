"""
Healthcare Preprocessing Pipeline — Phase 5
  Modality A (Signal)  : PTB-XL 12-lead ECG  -> [12, 1000] float32 tensors
  Modality B (Image)   : Kermany Chest X-Ray  -> [3, 224, 224] float32 tensors
  Modality C (Tabular) : PTB-XL metadata      -> [8] float32 feature vector

Subset size: 3,000 records each (stratified / balanced)
Output:      data/processed/healthcare/{ecg, cxr, tabular}/
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from torch.utils.data import Dataset
from typing import Optional, Tuple


# ── Label Definitions ──────────────────────────────────────────────────────────

PTBXL_SUPERCLASS = {
    "NORM": 0,   # Normal
    "MI":   1,   # Myocardial Infarction
    "STTC": 2,   # ST/T Change
    "CD":   3,   # Conduction Disturbance
    "HYP":  4,   # Hypertrophy
}

CXR_LABELS = {
    "NORMAL":    0,
    "PNEUMONIA": 1,
}

N_ECG_CLASSES = 5
N_CXR_CLASSES = 2

# ECG -> CXR class pairing (for multimodal dataset pairing)
# NORM ECG  ↔  NORMAL CXR
# Abnormal ECG (MI/STTC/CD/HYP) ↔  PNEUMONIA CXR
ECG_TO_CXR_BUCKET = {0: 0, 1: 1, 2: 1, 3: 1, 4: 1}


# ── PTB-XL: Metadata ──────────────────────────────────────────────────────────

def load_ptbxl_metadata(ptbxl_dir: str) -> pd.DataFrame:
    import ast
    csv_path = os.path.join(ptbxl_dir, "ptbxl_database.csv")
    df = pd.read_csv(csv_path, index_col="ecg_id")
    df["scp_codes"] = df["scp_codes"].apply(ast.literal_eval)

    scp_df = pd.read_csv(os.path.join(ptbxl_dir, "scp_statements.csv"), index_col=0)
    superclass_map = scp_df[scp_df["diagnostic"] == 1]["diagnostic_class"].to_dict()

    def get_superclass(scp_codes: dict) -> Optional[str]:
        best_code, best_conf = None, 0.0
        for code, conf in scp_codes.items():
            if code in superclass_map and conf >= best_conf:
                best_code, best_conf = superclass_map[code], conf
        return best_code

    df["superclass"] = df["scp_codes"].apply(get_superclass)
    df = df.dropna(subset=["superclass"])
    df["label"] = df["superclass"].map(PTBXL_SUPERCLASS)
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    print(f"PTB-XL metadata: {len(df):,} records with valid labels")
    for cls, idx in PTBXL_SUPERCLASS.items():
        print(f"  Class {idx} ({cls}): {(df['label'] == idx).sum():,}")
    return df


def stratified_subset_ptbxl(df: pd.DataFrame, n_total: int = 3000,
                              seed: int = 42) -> pd.DataFrame:
    """
    Stratified sample: equal records per class.
    n_per_class = n_total // N_ECG_CLASSES (600 for 3000 total)
    """
    n_per_class = n_total // N_ECG_CLASSES
    parts = []
    for cls_idx in range(N_ECG_CLASSES):
        pool = df[df["label"] == cls_idx]
        n = min(n_per_class, len(pool))
        parts.append(pool.sample(n=n, random_state=seed))

    subset = pd.concat(parts).sample(frac=1, random_state=seed)
    print(f"\nStratified PTB-XL subset: {len(subset):,} records "
          f"({n_per_class} per class)")
    return subset


# ── PTB-XL: ECG Signal ────────────────────────────────────────────────────────

def load_ecg_record(ptbxl_dir: str, filename: str) -> np.ndarray:
    """Load one ECG record at 100 Hz -> [12, 1000] float32."""
    import wfdb
    from scipy.signal import butter, filtfilt, resample

    # Use 100 Hz records for speed; fall back to 500 Hz if absent
    path_100 = os.path.join(ptbxl_dir,
                            filename.replace("records500", "records100"))
    path_500 = os.path.join(ptbxl_dir, filename)
    record_path = path_100 if os.path.exists(path_100 + ".hea") else path_500

    record = wfdb.rdrecord(record_path)
    signal = record.p_signal.T  # [12, n_samples]

    if signal.shape[1] != 1000:
        signal = resample(signal, 1000, axis=1)

    b, a = butter(N=3, Wn=[0.5, 40], btype="bandpass", fs=100)
    signal = filtfilt(b, a, signal, axis=1)

    mean = signal.mean(axis=1, keepdims=True)
    std  = signal.std(axis=1,  keepdims=True) + 1e-8
    return ((signal - mean) / std).astype(np.float32)


def preprocess_ecg(ptbxl_dir: str, subset_df: pd.DataFrame,
                   output_dir: str) -> Tuple[np.ndarray, np.ndarray]:
    os.makedirs(output_dir, exist_ok=True)
    records, labels, ecg_ids = [], [], []
    failed = 0

    for ecg_id, row in subset_df.iterrows():
        try:
            sig = load_ecg_record(ptbxl_dir, row["filename_lr"])
            records.append(sig)
            labels.append(row["label"])
            ecg_ids.append(ecg_id)
        except Exception:
            failed += 1

        if len(records) % 500 == 0 and len(records) > 0:
            print(f"  ECG: {len(records):,} / {len(subset_df):,} loaded...")

    X = np.stack(records)             # [N, 12, 1000]
    y = np.array(labels, dtype=int)   # [N]

    np.save(os.path.join(output_dir, "ecg_signals.npy"), X)
    np.save(os.path.join(output_dir, "ecg_labels.npy"),  y)
    np.save(os.path.join(output_dir, "ecg_ids.npy"),
            np.array(ecg_ids))
    np.save(os.path.join(output_dir, "ecg_folds.npy"),
            subset_df.loc[ecg_ids, "strat_fold"].values)

    print(f"ECG saved: {len(records):,} records  (failed: {failed})  -> {output_dir}")
    return X, y


# ── PTB-XL: Tabular Metadata ──────────────────────────────────────────────────

def preprocess_tabular(subset_df: pd.DataFrame, output_dir: str) -> np.ndarray:
    """
    Extract tabular features from PTB-XL metadata — numeric columns only.
    Preferred: age, sex, height, weight, strat_fold + any other numeric cols up to 8.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Always work on numeric columns only — avoids string arithmetic errors
    numeric_df = subset_df.select_dtypes(include=[np.number])

    # Prefer known meaningful columns, fall back to whatever is available
    preferred = ["age", "sex", "height", "weight", "strat_fold",
                 "baseline_drift", "static_noise", "burst_noise"]
    available = [c for c in preferred if c in numeric_df.columns]

    # Pad with remaining numeric columns if fewer than 4 preferred found
    if len(available) < 4:
        extras = [c for c in numeric_df.columns if c not in available]
        available += extras[:max(0, 8 - len(available))]

    available = available[:8]   # cap at 8 features

    tab = numeric_df[available].copy()
    tab = tab.fillna(tab.median())

    # Normalize each feature to [0, 1]
    for col in tab.columns:
        col_min, col_max = float(tab[col].min()), float(tab[col].max())
        if col_max > col_min:
            tab[col] = (tab[col] - col_min) / (col_max - col_min)

    X = tab.values.astype(np.float32)      # [N, n_features]
    np.save(os.path.join(output_dir, "tabular_features.npy"), X)
    np.save(os.path.join(output_dir, "tabular_labels.npy"),
            subset_df["label"].values.astype(int))

    with open(os.path.join(output_dir, "tabular_columns.json"), "w") as f:
        json.dump(available, f)

    print(f"Tabular saved: {X.shape}  ({len(available)} features)  -> {output_dir}")
    return X


# ── Kermany Chest X-Ray ───────────────────────────────────────────────────────

def load_cxr_paths(cxr_dir: str) -> pd.DataFrame:
    """Collect all image paths + binary labels from Kermany folder structure."""
    chest_root = os.path.join(cxr_dir, "chest_xray")
    rows = []

    for split in ["train", "val", "test"]:
        for cls_name, cls_id in CXR_LABELS.items():
            folder = os.path.join(chest_root, split, cls_name)
            if not os.path.isdir(folder):
                continue
            for fname in os.listdir(folder):
                if fname.lower().endswith((".jpeg", ".jpg", ".png")):
                    rows.append({
                        "path":  os.path.join(folder, fname),
                        "label": cls_id,
                        "split": split,
                    })

    df = pd.DataFrame(rows)
    print(f"\nChest X-Ray found: {len(df):,} total images")
    for cls, idx in CXR_LABELS.items():
        print(f"  {cls} ({idx}): {(df['label'] == idx).sum():,}")
    return df


def balanced_subset_cxr(df: pd.DataFrame, n_total: int = 3000,
                         seed: int = 42) -> pd.DataFrame:
    """Balanced: equal NORMAL and PNEUMONIA images."""
    n_per_class = n_total // N_CXR_CLASSES
    parts = []
    for cls_idx in range(N_CXR_CLASSES):
        pool = df[df["label"] == cls_idx]
        n = min(n_per_class, len(pool))
        parts.append(pool.sample(n=n, random_state=seed))
    subset = pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    print(f"Balanced CXR subset: {len(subset):,} images "
          f"({n_per_class} per class)")
    return subset


def preprocess_cxr(subset_df: pd.DataFrame, output_dir: str,
                   img_size: int = 224) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load JPEG images (any colour mode), convert to RGB [3, H, W] float32.
    ImageNet normalisation applied.
    """
    from PIL import Image
    from torchvision import transforms

    os.makedirs(output_dir, exist_ok=True)

    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),                               # -> [3, H, W], [0,1]
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std= [0.229, 0.224, 0.225]),
    ])

    images, labels = [], []
    failed = 0

    for _, row in subset_df.iterrows():
        try:
            img = Image.open(row["path"]).convert("RGB")    # handles JPEG/PNG/grey
            images.append(transform(img).numpy())           # [3, 224, 224]
            labels.append(int(row["label"]))
        except Exception:
            failed += 1

        if len(images) % 500 == 0 and len(images) > 0:
            print(f"  CXR: {len(images):,} / {len(subset_df):,} loaded...")

    X = np.stack(images).astype(np.float32)  # [N, 3, 224, 224]
    y = np.array(labels, dtype=int)          # [N]  0=NORMAL, 1=PNEUMONIA

    np.save(os.path.join(output_dir, "cxr_images.npy"), X)
    np.save(os.path.join(output_dir, "cxr_labels.npy"), y)

    print(f"CXR saved: {X.shape}  (failed: {failed})  -> {output_dir}")
    return X, y


# ── Multimodal Dataset ────────────────────────────────────────────────────────

class HealthcareDataset(Dataset):
    """
    Multimodal dataset pairing ECG (5-class) + CXR (binary) + tabular.

    Pairing logic (synthetic, within-bucket):
      ECG class 0 (NORM)  ↔  CXR class 0 (NORMAL)
      ECG class 1-4 (any) ↔  CXR class 1 (PNEUMONIA)

    Returns: (ecg [12,1000], cxr [3,224,224], tabular [F], label [int])
    label = ECG 5-class label (primary classification target)
    """

    def __init__(self,
                 ecg_signals:   np.ndarray,
                 ecg_labels:    np.ndarray,
                 cxr_images:    np.ndarray,
                 cxr_labels:    np.ndarray,
                 tabular_feats: np.ndarray,
                 seed: int = 42):
        self.ecg = torch.FloatTensor(ecg_signals)
        self.cxr = torch.FloatTensor(cxr_images)
        self.tab = torch.FloatTensor(tabular_feats)
        self.ecg_labels = ecg_labels
        self.label      = torch.LongTensor(ecg_labels)

        np.random.seed(seed)
        cxr_by_bucket = {0: np.where(cxr_labels == 0)[0],
                         1: np.where(cxr_labels == 1)[0]}

        self.pair_idx = []
        for ecg_idx, ecg_cls in enumerate(ecg_labels):
            bucket = ECG_TO_CXR_BUCKET[int(ecg_cls)]
            pool   = cxr_by_bucket[bucket]
            if len(pool) == 0:
                pool = np.arange(len(cxr_labels))
            self.pair_idx.append(int(np.random.choice(pool)))

    def __len__(self):
        return len(self.ecg)

    def __getitem__(self, idx: int):
        cxr_idx = self.pair_idx[idx]
        return (
            self.ecg[idx],          # [12, 1000]
            self.cxr[cxr_idx],      # [3, 224, 224]
            self.tab[idx],          # [F]
            self.label[idx],        # scalar ECG 5-class label
        )


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Preprocess healthcare datasets (PTB-XL + Chest X-Ray)"
    )
    parser.add_argument("--ptbxl_dir",  default="data/raw/ptb-xl")
    parser.add_argument("--cxr_dir",    default="data/raw/chest-xray-pneumonia")
    parser.add_argument("--output_dir", default="data/processed/healthcare")
    parser.add_argument("--n_ecg",      type=int, default=5000,
                        help="Total PTB-XL records to use (stratified, max=n_records from download)")
    parser.add_argument("--n_cxr",      type=int, default=3000,
                        help="Total CXR images to use (balanced)")
    parser.add_argument("--img_size",   type=int, default=224)
    parser.add_argument("--seed",       type=int, default=42)
    parser.add_argument("--skip_ecg",   action="store_true",
                        help="Skip ECG preprocessing if already done")
    args = parser.parse_args()

    print("=" * 60)
    print("Healthcare Preprocessing Pipeline")
    print("=" * 60)

    # ── Modality A: ECG Signal ─────────────────────────────────────
    ecg_out = os.path.join(args.output_dir, "ecg")
    ecg_signals_path = os.path.join(ecg_out, "ecg_signals.npy")

    if args.skip_ecg and os.path.exists(ecg_signals_path):
        print("\n[1/3] PTB-XL ECG — already done, loading from disk...")
        ecg_X = np.load(ecg_signals_path)
        ecg_y = np.load(os.path.join(ecg_out, "ecg_labels.npy"))
        ecg_ids = np.load(os.path.join(ecg_out, "ecg_ids.npy"))
        meta_df = load_ptbxl_metadata(args.ptbxl_dir)
        subset  = stratified_subset_ptbxl(meta_df, n_total=args.n_ecg, seed=args.seed)
        print(f"  Loaded {ecg_X.shape[0]:,} ECG records from {ecg_out}")
    else:
        print("\n[1/3] PTB-XL ECG (Signal modality)")
        meta_df = load_ptbxl_metadata(args.ptbxl_dir)
        subset  = stratified_subset_ptbxl(meta_df, n_total=args.n_ecg, seed=args.seed)
        ecg_X, ecg_y = preprocess_ecg(args.ptbxl_dir, subset, ecg_out)

    # ── Modality C: Tabular Metadata (from PTB-XL, no extra download) ─
    print("\n[2/3] PTB-XL Metadata (Tabular modality)")
    tab_out = os.path.join(args.output_dir, "tabular")
    tab_X   = preprocess_tabular(subset, tab_out)

    # ── Modality B: Chest X-Ray Image ──────────────────────────────
    print("\n[3/3] Kermany Chest X-Ray (Image modality)")
    cxr_paths  = load_cxr_paths(args.cxr_dir)
    cxr_subset = balanced_subset_cxr(cxr_paths, n_total=args.n_cxr, seed=args.seed)
    cxr_out    = os.path.join(args.output_dir, "cxr")
    cxr_X, cxr_y = preprocess_cxr(cxr_subset, cxr_out, img_size=args.img_size)

    # ── Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PREPROCESSING COMPLETE")
    print("=" * 60)
    print(f"  ECG signals  : {ecg_X.shape}   -> {ecg_out}")
    print(f"  Tabular      : {tab_X.shape}    -> {tab_out}")
    print(f"  CXR images   : {cxr_X.shape} -> {cxr_out}")
    print()
    print("Next step:")
    print("  python data/loaders/partition_noniid.py \\")
    print(f"    --input_dir {os.path.join(args.output_dir, 'ecg')} \\")
    print(f"    --output_dir data/processed/partitions/healthcare")
