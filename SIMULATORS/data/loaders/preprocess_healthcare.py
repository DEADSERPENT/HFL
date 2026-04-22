"""
Healthcare Data Preprocessing Pipeline — Phase 5
  Modality A: PTB-XL (12-lead ECG) → [12, 1000] tensors
  Modality B: CheXpert (chest X-ray) → [3, 224, 224] tensors
  Output: paired multimodal dataset saved to processed/healthcare/
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from pathlib import Path
from typing import Optional, Tuple, Dict, List

# PTB-XL 5-class label mapping (superclass from SNOMED codes)
PTBXL_SUPERCLASS = {
    "NORM": 0,
    "MI":   1,   # Myocardial Infarction
    "STTC": 2,   # ST/T Change
    "CD":   3,   # Conduction Disturbance
    "HYP":  4,   # Hypertrophy
}

# CheXpert 5-label subset indices in train.csv (columns)
CHEXPERT_LABELS = [
    "No Finding",
    "Pleural Effusion",
    "Cardiomegaly",
    "Atelectasis",
    "Consolidation",
]


def load_ptbxl_metadata(ptbxl_dir: str) -> pd.DataFrame:
    """Load PTB-XL metadata and map to 5 superclasses."""
    import ast
    csv_path = os.path.join(ptbxl_dir, "ptbxl_database.csv")
    df = pd.read_csv(csv_path, index_col="ecg_id")

    # Parse scp_codes dict from string
    df["scp_codes"] = df["scp_codes"].apply(ast.literal_eval)

    # Load SCP statement labels
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

    print(f"PTB-XL metadata: {len(df):,} records with valid superclass labels")
    for cls, idx in PTBXL_SUPERCLASS.items():
        n = (df["label"] == idx).sum()
        print(f"  Class {idx} ({cls}): {n:,}")
    return df


def load_ecg_record(ptbxl_dir: str, filename: str,
                    sampling_rate: int = 100) -> np.ndarray:
    """
    Load ECG record using wfdb and resample to 100 Hz.
    Returns: [12, 1000] numpy array (12 leads, 1000 samples at 100Hz)
    """
    import wfdb
    from scipy.signal import butter, filtfilt, resample

    # PTB-XL records are at 100Hz or 500Hz; prefer 100Hz for efficiency
    if sampling_rate == 100:
        record_path = os.path.join(ptbxl_dir, filename.replace("records500", "records100"))
    else:
        record_path = os.path.join(ptbxl_dir, filename)

    record = wfdb.rdrecord(record_path)
    signal = record.p_signal.T  # [12, n_samples]

    # Ensure exactly 1000 samples (10s at 100Hz)
    target_len = 1000
    if signal.shape[1] != target_len:
        signal = resample(signal, target_len, axis=1)

    # Bandpass filter: 0.5–40 Hz
    b, a = butter(N=3, Wn=[0.5, 40], btype="bandpass", fs=100)
    signal = filtfilt(b, a, signal, axis=1)

    # Per-lead z-score normalization
    mean = signal.mean(axis=1, keepdims=True)
    std = signal.std(axis=1, keepdims=True) + 1e-8
    signal = (signal - mean) / std

    return signal.astype(np.float32)  # [12, 1000]


def preprocess_ptbxl(ptbxl_dir: str, output_dir: str,
                     max_records: Optional[int] = None):
    """Preprocess all PTB-XL records and save as .npy tensors."""
    os.makedirs(output_dir, exist_ok=True)
    df = load_ptbxl_metadata(ptbxl_dir)

    if max_records is not None:
        df = df.head(max_records)

    records = []
    labels = []
    ecg_ids = []
    failed = 0

    for ecg_id, row in df.iterrows():
        try:
            signal = load_ecg_record(ptbxl_dir, row["filename_lr"])
            records.append(signal)
            labels.append(row["label"])
            ecg_ids.append(ecg_id)
        except Exception:
            failed += 1
            continue

        if len(records) % 1000 == 0:
            print(f"  Processed {len(records):,} / {len(df):,} ECGs...")

    X = np.stack(records, axis=0)   # [N, 12, 1000]
    y = np.array(labels)            # [N]
    ids = np.array(ecg_ids)         # [N]
    strat_fold = df.loc[ecg_ids, "strat_fold"].values  # fold 1-10

    np.save(os.path.join(output_dir, "ecg_signals.npy"), X)
    np.save(os.path.join(output_dir, "ecg_labels.npy"), y)
    np.save(os.path.join(output_dir, "ecg_ids.npy"), ids)
    np.save(os.path.join(output_dir, "ecg_folds.npy"), strat_fold)

    print(f"PTB-XL preprocessing complete: {len(records):,} records saved.")
    print(f"  Failed: {failed}, Saved to: {output_dir}")
    return X, y, ids, strat_fold


def preprocess_chexpert(chexpert_dir: str, output_dir: str,
                        img_size: int = 224,
                        max_records: Optional[int] = None):
    """Preprocess CheXpert images and save metadata."""
    from PIL import Image
    from torchvision import transforms

    os.makedirs(output_dir, exist_ok=True)

    train_csv = os.path.join(chexpert_dir, "train.csv")
    df = pd.read_csv(train_csv)

    # Keep only frontal view
    df = df[df["Frontal/Lateral"] == "Frontal"].reset_index(drop=True)

    # Select 5 labels, apply U-zeros policy
    label_cols = CHEXPERT_LABELS
    for col in label_cols:
        df[col] = df[col].fillna(0.0).replace(-1.0, 0.0).astype(np.float32)

    if max_records is not None:
        df = df.head(max_records)

    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    images = []
    labels = []
    patient_ids = []
    failed = 0

    for idx, row in df.iterrows():
        img_path = os.path.join(chexpert_dir, row["Path"].lstrip("/"))
        try:
            img = Image.open(img_path).convert("RGB")
            img_tensor = transform(img).numpy()  # [3, 224, 224]
            label = row[label_cols].values.astype(np.float32)
            images.append(img_tensor)
            labels.append(label)
            patient_ids.append(row["Path"].split("/")[2])
        except Exception:
            failed += 1
            continue

        if len(images) % 5000 == 0:
            print(f"  Processed {len(images):,} / {len(df):,} CXRs...")

    X = np.stack(images, axis=0)  # [N, 3, 224, 224]
    y = np.stack(labels, axis=0)  # [N, 5]

    # Save primary label (most prevalent pathology) for 5-class task
    primary_labels = []
    for lab in y:
        pos = np.where(lab > 0)[0]
        if len(pos) == 0 or (len(pos) == 1 and pos[0] == 0):
            primary_labels.append(0)  # No Finding
        else:
            pos_pathology = pos[pos > 0]
            primary_labels.append(int(pos_pathology[0]))

    np.save(os.path.join(output_dir, "cxr_images.npy"), X)
    np.save(os.path.join(output_dir, "cxr_multilabels.npy"), y)
    np.save(os.path.join(output_dir, "cxr_primary_labels.npy"),
            np.array(primary_labels))
    np.save(os.path.join(output_dir, "cxr_patient_ids.npy"),
            np.array(patient_ids))

    print(f"CheXpert preprocessing complete: {len(images):,} images saved.")
    print(f"  Failed: {failed}, Saved to: {output_dir}")
    return X, y


class HealthcareDataset(Dataset):
    """
    Paired PTB-XL ECG + CheXpert CXR dataset.
    Pairing: within-class synthetic pairing when patient IDs don't match.
    """

    def __init__(self, ecg_signals: np.ndarray, ecg_labels: np.ndarray,
                 cxr_images: np.ndarray, cxr_labels: np.ndarray,
                 mode: str = "train"):
        self.ecg = torch.FloatTensor(ecg_signals)   # [N, 12, 1000]
        self.cxr = torch.FloatTensor(cxr_images)    # [M, 3, 224, 224]
        self.ecg_labels = torch.LongTensor(ecg_labels)
        self.cxr_labels = torch.LongTensor(cxr_labels)
        self.mode = mode

        # Build within-class pairing index
        self._build_pairing()

    def _build_pairing(self):
        """Map each ECG sample to a CXR sample of the same class."""
        n_classes = 5
        cxr_by_class = {c: [] for c in range(n_classes)}
        for i, lbl in enumerate(self.cxr_labels.tolist()):
            cxr_by_class[lbl].append(i)

        self.pairs = []
        for ecg_idx, lbl in enumerate(self.ecg_labels.tolist()):
            class_pool = cxr_by_class.get(lbl, [])
            if len(class_pool) == 0:
                class_pool = list(range(len(self.cxr)))
            cxr_idx = int(np.random.choice(class_pool))
            self.pairs.append((ecg_idx, cxr_idx))

    def __len__(self):
        return len(self.ecg)

    def __getitem__(self, idx: int) -> Tuple:
        ecg_idx, cxr_idx = self.pairs[idx]
        return (
            self.ecg[ecg_idx],       # [12, 1000]
            self.cxr[cxr_idx],       # [3, 224, 224]
            self.ecg_labels[ecg_idx] # scalar label (PTB-XL 5-class)
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ptbxl_dir",   default="data/raw/ptb-xl")
    parser.add_argument("--chexpert_dir", default="data/raw/chexpert")
    parser.add_argument("--output_dir",  default="data/processed/healthcare")
    parser.add_argument("--max_ptbxl",   type=int, default=None)
    parser.add_argument("--max_chexpert", type=int, default=None)
    args = parser.parse_args()

    print("Preprocessing PTB-XL ECG data...")
    preprocess_ptbxl(args.ptbxl_dir,
                     os.path.join(args.output_dir, "ecg"),
                     args.max_ptbxl)

    print("\nPreprocessing CheXpert X-ray data...")
    preprocess_chexpert(args.chexpert_dir,
                        os.path.join(args.output_dir, "cxr"),
                        args.max_chexpert)

    print("\nPreprocessing complete.")
