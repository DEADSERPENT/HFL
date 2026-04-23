"""
Non-IID Data Partitioning for Federated Learning — Healthcare Domain
Dirichlet distribution (alpha=0.5) simulates heterogeneous patient
data distribution across 6 healthcare IoT devices (devices 14–19)
mapped to 2 edge servers (ward gateways).
"""

import os
import json
import argparse
import numpy as np
from typing import List, Dict, Tuple


# ── Dirichlet Partitioning ─────────────────────────────────────────────────────

def dirichlet_partition(labels: np.ndarray, n_clients: int,
                        alpha: float = 0.5,
                        seed: int = 42) -> List[np.ndarray]:
    """
    Partition dataset indices using Dirichlet distribution.
    Higher alpha → more IID. Lower alpha (0.1–0.5) → more heterogeneous.
    """
    np.random.seed(seed)
    n_classes = len(np.unique(labels))
    class_indices = [np.where(labels == c)[0] for c in range(n_classes)]
    for idx_list in class_indices:
        np.random.shuffle(idx_list)

    client_indices = [[] for _ in range(n_clients)]

    for c, cls_idx in enumerate(class_indices):
        proportions = np.random.dirichlet(np.repeat(alpha, n_clients))
        proportions = (proportions * len(cls_idx)).astype(int)
        proportions[-1] = len(cls_idx) - proportions[:-1].sum()
        proportions = np.maximum(proportions, 0)

        start = 0
        for client_id, count in enumerate(proportions):
            end = start + count
            client_indices[client_id].extend(cls_idx[start:end].tolist())
            start = end

    return [np.array(idx) for idx in client_indices]


# ── Edge Server Assignment ─────────────────────────────────────────────────────

def assign_to_edges(n_devices: int = 6,
                    n_edges:   int = 2) -> Dict[int, List[int]]:
    """
    Assign healthcare IoT devices to edge servers (ward gateways).
    Default: 6 devices → 2 edge servers (3 devices each).
    Returns: {edge_id: [device_ids]}
    """
    assignments = {}
    devices_per_edge = [n_devices // n_edges] * n_edges
    for i in range(n_devices % n_edges):
        devices_per_edge[i] += 1

    device_id = 0
    for edge_id, count in enumerate(devices_per_edge):
        assignments[edge_id] = list(range(device_id, device_id + count))
        device_id += count
    return assignments


# ── Train/Val/Test Split ───────────────────────────────────────────────────────

def split_local_data(indices: np.ndarray,
                     train_ratio: float = 0.70,
                     val_ratio:   float = 0.15,
                     seed: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    np.random.seed(seed)
    np.random.shuffle(indices)
    n = len(indices)
    n_train = int(n * train_ratio)
    n_val   = int(n * val_ratio)
    return (indices[:n_train],
            indices[n_train:n_train + n_val],
            indices[n_train + n_val:])


# ── Full Partition Pipeline ────────────────────────────────────────────────────

def partition_and_save(labels:    np.ndarray,
                       output_dir: str,
                       n_devices: int   = 6,
                       n_edges:   int   = 2,
                       alpha:     float = 0.5,
                       seed:      int   = 42):
    """
    Dirichlet split → edge assignment → train/val/test per device.
    Saves index .npy files + partition_meta.json.
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"Partitioning {len(labels):,} samples across {n_devices} devices "
          f"({n_edges} edge servers, Dirichlet α={alpha})")

    device_indices = dirichlet_partition(labels, n_devices, alpha, seed)
    edge_map = assign_to_edges(n_devices, n_edges)

    n_classes = len(np.unique(labels))
    partition_meta = {
        "domain":        "healthcare",
        "n_devices":     n_devices,
        "n_edges":       n_edges,
        "alpha":         alpha,
        "seed":          seed,
        "total_samples": int(len(labels)),
        "edge_assignments": edge_map,
        "devices": {}
    }

    for device_id, indices in enumerate(device_indices):
        if len(indices) == 0:
            indices = np.array([0])

        train_idx, val_idx, test_idx = split_local_data(
            indices, seed=seed + device_id)

        class_counts = {int(c): 0 for c in range(n_classes)}
        for lbl in labels[indices]:
            class_counts[int(lbl)] = class_counts.get(int(lbl), 0) + 1

        edge_id = next(e for e, devs in edge_map.items() if device_id in devs)

        np.save(os.path.join(output_dir, f"device_{device_id:02d}_train.npy"), train_idx)
        np.save(os.path.join(output_dir, f"device_{device_id:02d}_val.npy"),   val_idx)
        np.save(os.path.join(output_dir, f"device_{device_id:02d}_test.npy"),  test_idx)

        partition_meta["devices"][str(device_id)] = {
            "edge_id": edge_id,
            "n_train": int(len(train_idx)),
            "n_val":   int(len(val_idx)),
            "n_test":  int(len(test_idx)),
            "total":   int(len(indices)),
            "class_distribution": class_counts,
        }

        print(f"  Device {device_id:02d} (Edge {edge_id}): "
              f"train={len(train_idx):3d}  val={len(val_idx):3d}  "
              f"test={len(test_idx):3d}  | dist={class_counts}")

    meta_path = os.path.join(output_dir, "partition_meta.json")
    with open(meta_path, "w") as f:
        json.dump(partition_meta, f, indent=2)

    print(f"\nPartition metadata saved: {meta_path}")
    _print_heterogeneity_stats(device_indices, labels, n_classes)
    return partition_meta


# ── Diagnostics ───────────────────────────────────────────────────────────────

def _print_heterogeneity_stats(device_indices: List[np.ndarray],
                                labels: np.ndarray, n_classes: int):
    all_fracs = []
    for indices in device_indices:
        if len(indices) == 0:
            continue
        counts = np.bincount(labels[indices], minlength=n_classes)
        all_fracs.append(counts / counts.sum())

    fracs   = np.array(all_fracs)
    uniform = np.ones(n_classes) / n_classes
    avg_tvd = float(np.mean([0.5 * np.abs(f - uniform).sum() for f in fracs]))

    print(f"\nHeterogeneity (Dirichlet α):")
    print(f"  Avg TVD from uniform : {avg_tvd:.4f}  (0=IID, 1=extreme non-IID)")
    sizes = [len(i) for i in device_indices]
    print(f"  Samples per device   : min={min(sizes)}  "
          f"max={max(sizes)}  mean={np.mean(sizes):.0f}")


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Partition healthcare dataset for FL simulation"
    )
    parser.add_argument("--input_dir",  default="data/processed/healthcare/ecg",
                        help="Directory containing ecg_labels.npy")
    parser.add_argument("--output_dir", default="data/processed/partitions/healthcare")
    parser.add_argument("--n_devices",  type=int,   default=6,
                        help="Number of healthcare IoT devices (default: 6)")
    parser.add_argument("--n_edges",    type=int,   default=2,
                        help="Number of edge servers / ward gateways (default: 2)")
    parser.add_argument("--alpha",      type=float, default=0.5,
                        help="Dirichlet alpha (lower=more non-IID)")
    parser.add_argument("--seed",       type=int,   default=42)
    args = parser.parse_args()

    labels_path = os.path.join(args.input_dir, "ecg_labels.npy")
    if not os.path.exists(labels_path):
        raise FileNotFoundError(
            f"Labels not found: {labels_path}\n"
            f"Run preprocess_healthcare.py first."
        )

    labels = np.load(labels_path)
    partition_and_save(
        labels,
        output_dir=args.output_dir,
        n_devices=args.n_devices,
        n_edges=args.n_edges,
        alpha=args.alpha,
        seed=args.seed,
    )
