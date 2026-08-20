"""
vitaldb_dataset.py — Dataset + partition loaders for VitalDB.

Mirrors the 4-tuple contract of `HealthcareDataset` and `WEARDataset`
`(modality_a, modality_b, tabular, label)` so `hfl_trainer.py`, the DP engine,
the compressor and the aggregation code need no changes — only `--data_dir` /
`--partition_dir` move.

    modality_a : (18, W) float32 — 9 intraoperative numeric trends @0.5 Hz
                                   stacked with their 9 binary observed-masks
    modality_b : (34,)   float32 — preoperative clinical + laboratory vector
    tabular    : (1,)    float32 — unused placeholder, kept for contract parity
    label      : int64            — postoperative ICU admission (0/1)

The mask channels matter: an arterial line or a preoperative lab is ordered
only for patients judged at risk, so *whether* a channel was recorded is
itself evidence about acuity. They are carried explicitly rather than being
hidden inside a zero-fill.
"""

import os
import json

import numpy as np
import torch
from torch.utils.data import Dataset


class VitalDBDataset(Dataset):
    """Intraoperative monitoring + preoperative clinical, same patient/second."""

    def __init__(self, signals: np.ndarray, clinical: np.ndarray, labels: np.ndarray):
        assert len(signals) == len(clinical) == len(labels), "modality length mismatch"
        # np.array(..., copy) — sources are memory-mapped and therefore
        # read-only; one owned copy up front, shared by all clients.
        self.signals  = torch.from_numpy(np.array(signals,  dtype=np.float32))
        self.clinical = torch.from_numpy(np.array(clinical, dtype=np.float32))
        self.label    = torch.from_numpy(np.array(labels,   dtype=np.int64))
        self._tab     = torch.zeros(1, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.label)

    def __getitem__(self, i: int):
        return self.signals[i], self.clinical[i], self._tab, self.label[i]


def build_full_vitaldb_dataset(processed_dir: str) -> VitalDBDataset:
    """Load the arrays written by preprocess_vitaldb.py."""
    signals  = np.load(os.path.join(processed_dir, "signals", "windows.npy"),
                       mmap_mode="r")
    labels   = np.load(os.path.join(processed_dir, "signals", "labels.npy"))
    clinical = np.load(os.path.join(processed_dir, "clinical", "features.npy"),
                       mmap_mode="r")
    return VitalDBDataset(signals, clinical, labels)


def vitaldb_meta(processed_dir: str) -> dict:
    with open(os.path.join(processed_dir, "meta", "dataset_meta.json")) as f:
        return json.load(f)


def load_vitaldb_partition(partition_dir: str, device_id: int) -> dict:
    """Window indices for one FL client (= one surgical operation type)."""
    return {
        split: np.load(os.path.join(partition_dir,
                                    f"device_{device_id:02d}_{split}.npy"))
        for split in ("train", "val", "test")
    }


def case_ids(processed_dir: str) -> np.ndarray:
    """Case id per window — needed to aggregate window predictions to the
    case level, which is the clinically meaningful unit of evaluation."""
    return np.load(os.path.join(processed_dir, "meta", "case_ids.npy"))
