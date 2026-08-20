"""
wear_dataset.py — Dataset + partition loaders for WEAR.

Deliberately mirrors the 4-tuple contract of `HealthcareDataset`
`(modality_a, modality_b, tabular, label)` so `hfl_trainer.py`, the DP engine,
the compressor and the aggregation code need no changes at all — only
`--data_dir` / `--partition_dir` move.

    modality_a : (12, W) float32  — 4 accelerometers x 3 axes, 2 s @ 50 Hz
    modality_b : (2048,) float32  — two-stream I3D features for the SAME 2 s
    tabular    : (1,)    float32  — unused placeholder, kept for contract parity
    label      : int64            — one of 18 workout activities

Arrays are materialised once and shared across all client loaders (as the
a naive pipeline would), so 22 clients cost one copy of the data, not 22.
"""

import os
import json

import numpy as np
import torch
from torch.utils.data import Dataset


class WEARDataset(Dataset):
    """Hardware-synchronised inertial + egocentric-video windows."""

    def __init__(self, inertial: np.ndarray, i3d: np.ndarray, labels: np.ndarray):
        assert len(inertial) == len(i3d) == len(labels), "modality length mismatch"
        # np.array(..., copy=True): the source arrays are memory-mapped and
        # therefore read-only, which makes torch.from_numpy emit a non-writable
        # tensor warning. One owned copy up front, shared by all 22 clients.
        self.inertial = torch.from_numpy(np.array(inertial, dtype=np.float32))
        self.i3d      = torch.from_numpy(np.array(i3d,      dtype=np.float32))
        self.label    = torch.from_numpy(np.array(labels,   dtype=np.int64))
        self._tab     = torch.zeros(1, dtype=torch.float32)   # contract placeholder

    def __len__(self) -> int:
        return len(self.label)

    def __getitem__(self, i: int):
        return self.inertial[i], self.i3d[i], self._tab, self.label[i]


def build_full_wear_dataset(processed_dir: str) -> WEARDataset:
    """Load the arrays written by preprocess_wear.py."""
    inertial = np.load(os.path.join(processed_dir, "inertial", "inertial_windows.npy"),
                       mmap_mode="r")
    labels   = np.load(os.path.join(processed_dir, "inertial", "labels.npy"))
    i3d      = np.load(os.path.join(processed_dir, "video", "i3d_features.npy"),
                       mmap_mode="r")
    return WEARDataset(inertial, i3d, labels)


def wear_meta(processed_dir: str) -> dict:
    with open(os.path.join(processed_dir, "meta", "dataset_meta.json")) as f:
        return json.load(f)


def load_wear_partition(partition_dir: str, device_id: int) -> dict:
    """Index arrays for one FL client (= one WEAR subject = one edge device)."""
    return {
        split: np.load(os.path.join(partition_dir,
                                    f"device_{device_id:02d}_{split}.npy"))
        for split in ("train", "val", "test")
    }
