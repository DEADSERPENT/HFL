"""
eicu_dataset.py — Dataset + partition loaders for eICU-CRD.

Mirrors the 4-tuple contract of `VitalDBDataset` and `WEARDataset`
`(modality_a, modality_b, tabular, label)` so `hfl_trainer.py`, the DP engine,
the compressor and the aggregation code need no changes.

    modality_a : (2C, T) float32 — C intraoperative-style vital trends binned
                                   onto a fixed grid, stacked with their C
                                   binary observed-masks
    modality_b : (D,)   float32 — admission-time clinical vector for the SAME
                                  stay (age, sex, weight, height, APACHE)
    tabular    : (1,)   float32 — unused placeholder, kept for contract parity
    label      : int64           — in-unit mortality (unitdischargestatus)

The mask channels matter for the same reason they do in VitalDB: in an ICU a
measurement is charted because someone judged it worth charting, so *whether*
a channel was recorded is itself evidence about acuity. Carried explicitly
rather than hidden inside a zero-fill.
"""

import os
import json

import numpy as np
import torch
from torch.utils.data import Dataset


class EICUDataset(Dataset):
    """ICU vitals window + admission clinical vector, same stay."""

    def __init__(self, signals: np.ndarray, clinical: np.ndarray, labels: np.ndarray):
        assert len(signals) == len(clinical) == len(labels), "modality length mismatch"
        self.signals  = torch.from_numpy(np.array(signals,  dtype=np.float32))
        self.clinical = torch.from_numpy(np.array(clinical, dtype=np.float32))
        self.label    = torch.from_numpy(np.array(labels,   dtype=np.int64))
        self._tab     = torch.zeros(1, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.label)

    def __getitem__(self, i: int):
        return self.signals[i], self.clinical[i], self._tab, self.label[i]


def build_full_eicu_dataset(processed_dir: str) -> EICUDataset:
    """Load the arrays written by preprocess_eicu.py."""
    signals  = np.load(os.path.join(processed_dir, "vitals", "windows.npy"),
                       mmap_mode="r")
    labels   = np.load(os.path.join(processed_dir, "vitals", "labels.npy"))
    clinical = np.load(os.path.join(processed_dir, "tabular", "features.npy"),
                       mmap_mode="r")
    return EICUDataset(signals, clinical, labels)


def eicu_meta(processed_dir: str) -> dict:
    with open(os.path.join(processed_dir, "meta", "dataset_meta.json")) as f:
        return json.load(f)


def load_eicu_partition(partition_dir: str, device_id: int) -> dict:
    """Window indices for one FL client (= one hospital)."""
    return {
        split: np.load(os.path.join(partition_dir,
                                    f"device_{device_id:02d}_{split}.npy"))
        for split in ("train", "val", "test")
    }


def case_ids(processed_dir: str) -> np.ndarray:
    """Person id per window — the PATIENT, not the stay. Patient-level DP,
    LiRA, k-scaling and case-level metrics all key on this."""
    return np.load(os.path.join(processed_dir, "meta", "case_ids.npy"))
