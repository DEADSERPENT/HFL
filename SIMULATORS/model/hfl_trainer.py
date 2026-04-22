"""
HFL-MM-HC Training Engine — Phase 5
Two-tier FedAvg: 20 IoT devices → 3 Edge servers → 1 Cloud server
With DP-SGD (Opacus), gradient compression (Top-k + 8-bit), and
FedConform-HC conformal calibration updates.
"""

import os
import sys
import copy
import json
import time
import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, Subset

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "data" / "loaders"))

from device_utils import get_device, optimize_gpu, get_dataloader_kwargs, gpu_memory_info


def load_partitioned_data(partition_dir: str, processed_dir: str,
                          device_id: int, batch_size: int = 32):
    """Load train/val/test loaders for a specific device."""
    from preprocess_healthcare import HealthcareDataset

    ecg_signals = np.load(os.path.join(processed_dir, "ecg", "ecg_signals.npy"),
                          mmap_mode="r")
    ecg_labels = np.load(os.path.join(processed_dir, "ecg", "ecg_labels.npy"))
    cxr_images = np.load(os.path.join(processed_dir, "cxr", "cxr_images.npy"),
                         mmap_mode="r")
    cxr_labels = np.load(os.path.join(processed_dir, "cxr", "cxr_primary_labels.npy"))

    full_ds = HealthcareDataset(ecg_signals, ecg_labels,
                                cxr_images, cxr_labels)

    train_idx = np.load(os.path.join(partition_dir,
                                     f"device_{device_id:02d}_train.npy"))
    val_idx = np.load(os.path.join(partition_dir,
                                   f"device_{device_id:02d}_val.npy"))
    test_idx = np.load(os.path.join(partition_dir,
                                    f"device_{device_id:02d}_test.npy"))

    train_ds = Subset(full_ds, train_idx.tolist())
    val_ds = Subset(full_ds, val_idx.tolist())
    test_ds = Subset(full_ds, test_idx.tolist())

    _device  = get_device(verbose=False)
    _dl_kw   = get_dataloader_kwargs(_device)
    return {
        "train": DataLoader(train_ds, batch_size=batch_size,
                            shuffle=True, **_dl_kw),
        "val":   DataLoader(val_ds,   batch_size=batch_size * 2, **_dl_kw),
        "test":  DataLoader(test_ds,  batch_size=batch_size * 2, **_dl_kw),
        "n_train": len(train_idx),
    }


def evaluate_model(model: nn.Module, loader: DataLoader,
                   device: torch.device) -> Dict:
    from sklearn.metrics import roc_auc_score
    model.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for ecg, cxr, labels in loader:
            logits = model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
            all_logits.append(logits.cpu())
            all_labels.append(labels.cpu())
    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels).numpy()
    probs = torch.softmax(logits, dim=-1).numpy()
    preds = logits.argmax(dim=-1).numpy()
    acc = float((preds == labels).mean())
    try:
        auc = float(roc_auc_score(labels, probs, multi_class="ovr", average="macro"))
    except Exception:
        auc = 0.0
    return {"accuracy": acc, "macro_auc": auc}


def local_dp_train(model: nn.Module, loader: DataLoader,
                   device: torch.device, epsilon: float, delta: float,
                   max_grad_norm: float, lr: float,
                   n_epochs: int = 1) -> Dict:
    """DP-SGD local training for one FL round."""
    from dp_engine import make_dp_model, get_epsilon_spent

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()

    try:
        dp_model, dp_opt, dp_loader, pe = make_dp_model(
            model, optimizer, loader,
            target_epsilon=epsilon,
            target_delta=delta,
            max_grad_norm=max_grad_norm,
            epochs=n_epochs,
        )
        dp_model.train()
        total_loss, total = 0.0, 0
        for _ in range(n_epochs):
            for ecg, cxr, labels in dp_loader:
                dp_opt.zero_grad()
                logits = dp_model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
                loss = loss_fn(logits, labels.to(device, non_blocking=True))
                loss.backward()
                dp_opt.step()
                total_loss += loss.item() * len(labels)
                total += len(labels)
        eps_spent = get_epsilon_spent(pe, delta)
        return {"loss": total_loss / max(total, 1),
                "epsilon_spent": eps_spent,
                "n_samples": total}
    except Exception as e:
        raise RuntimeError(f"[HFL-Trainer] DP-SGD training failed: {e}") from e
    return {"loss": 0.0,
            "epsilon_spent": 0.0,
                "n_samples": total}


def edge_fedavg(global_state: dict, client_updates: List[Dict],
                client_sizes: List[int]) -> dict:
    """Weighted FedAvg at edge level."""
    total = sum(client_sizes)
    agg = {}
    for key in global_state:
        if not global_state[key].is_floating_point():
            agg[key] = global_state[key].clone()
            continue
        agg[key] = sum(
            (n / total) * upd[key].float()
            for n, upd in zip(client_sizes, client_updates)
        )
    return agg


def train_hfl_mm_hc(args) -> Dict:
    """
    Main HFL-MM-HC training loop: 2-tier FedAvg + DP-SGD + conformal.
    """
    from hfl_mm_model import build_hfl_mm_hc
    from compression import GradientCompressor
    from fedconform_hc import LocalConformCalibrator, FedConformAggregator

    device = get_device()
    optimize_gpu()

    # Load partition metadata
    meta_path = os.path.join(args.partition_dir, "partition_meta.json")
    with open(meta_path) as f:
        meta = json.load(f)

    n_devices = meta["n_devices"]
    n_edges = meta["n_edges"]
    edge_assignments = {int(k): v for k, v in meta["edge_assignments"].items()}

    # Build global model
    global_model = build_hfl_mm_hc(n_classes=args.n_classes).to(device)
    gpu_memory_info()
    compressor = GradientCompressor(sparsity=args.sparsity, quant_bits=args.quant_bits)
    conform_agg = FedConformAggregator()

    # Load device data
    print("Loading device data...")
    device_loaders = []
    for dev_id in range(n_devices):
        loaders = load_partitioned_data(
            args.partition_dir, args.data_dir, dev_id, args.batch_size)
        device_loaders.append(loaders)

    # Results log
    results_log = []
    best_auc, best_state = 0.0, None
    q_global = 0.9  # initial conformal quantile

    print(f"\nStarting HFL-MM-HC training: {args.rounds} global rounds, "
          f"{args.tau_e} edge rounds, {n_devices} devices, {n_edges} edges")
    print(f"DP: ε={args.epsilon}, δ={args.delta}, σ auto, C={args.max_grad_norm}")

    for global_round in range(1, args.rounds + 1):
        round_start = time.time()
        global_state = {k: v.clone() for k, v in global_model.state_dict().items()}

        edge_states = {e: copy.deepcopy(global_state) for e in range(n_edges)}
        round_eps_spent = []

        for edge_round in range(1, args.tau_e + 1):
            edge_client_states = {e: [] for e in range(n_edges)}
            edge_client_sizes = {e: [] for e in range(n_edges)}
            edge_q_tildes = {e: [] for e in range(n_edges)}

            # Step 1: Local DP training on all devices
            for dev_id in range(n_devices):
                edge_id = next(e for e, devs in edge_assignments.items()
                               if dev_id in devs)
                local_model = build_hfl_mm_hc(n_classes=args.n_classes).to(device)
                local_model.load_state_dict(edge_states[edge_id])

                train_result = local_dp_train(
                    local_model, device_loaders[dev_id]["train"],
                    device, args.epsilon, args.delta,
                    args.max_grad_norm, args.lr, n_epochs=1,
                )
                round_eps_spent.append(train_result["epsilon_spent"])

                # Compress delta
                delta_params = {
                    n: local_model.state_dict()[n] - edge_states[edge_id][n]
                    for n in global_state
                    if global_state[n].is_floating_point()
                }
                compressed = compressor.compress(delta_params)
                decompressed = compressor.decompress(compressed, device)

                # Reconstruct full state with compressed delta
                updated_state = copy.deepcopy(edge_states[edge_id])
                for n in decompressed:
                    updated_state[n] = updated_state[n] + decompressed[n]

                edge_client_states[edge_id].append(updated_state)
                edge_client_sizes[edge_id].append(train_result["n_samples"])

                # Conformal calibration
                cal_loader = device_loaders[dev_id]["val"]
                cal = LocalConformCalibrator(alpha=args.alpha_conf,
                                            epsilon_conf=0.1)
                q_tilde = cal.calibrate(local_model, cal_loader, device)
                edge_q_tildes[edge_id].append(q_tilde)

            # Step 2: Edge aggregation
            for edge_id in range(n_edges):
                if edge_client_states[edge_id]:
                    edge_states[edge_id] = edge_fedavg(
                        edge_states[edge_id],
                        edge_client_states[edge_id],
                        edge_client_sizes[edge_id],
                    )

        # Step 3: Cloud aggregation
        edge_sizes = [sum(device_loaders[d]["n_train"]
                          for d in edge_assignments[e])
                      for e in range(n_edges)]
        total_samples = sum(edge_sizes)
        new_global_state = {}
        for key in global_state:
            if not global_state[key].is_floating_point():
                new_global_state[key] = global_state[key].clone()
                continue
            new_global_state[key] = sum(
                (n / total_samples) * edge_states[e][key].float()
                for e, n in zip(range(n_edges), edge_sizes)
            )
        global_model.load_state_dict(new_global_state)
        compressor.reset_error_feedback()

        # Step 4: Global conformal quantile update
        q_edges = [conform_agg.edge_aggregate(edge_q_tildes[e])
                   for e in range(n_edges)]
        q_global = conform_agg.cloud_aggregate(q_edges)

        # Step 5: Evaluate
        val_metrics = evaluate_model(global_model, device_loaders[0]["val"], device)
        max_eps = max(round_eps_spent) if round_eps_spent else 0.0
        round_time = time.time() - round_start

        log_entry = {
            "global_round": global_round,
            "val_accuracy": round(val_metrics["accuracy"], 4),
            "val_macro_auc": round(val_metrics["macro_auc"], 4),
            "epsilon_spent": round(max_eps, 4),
            "q_global": round(q_global, 4),
            "round_time_s": round(round_time, 2),
        }
        results_log.append(log_entry)

        print(f"Round {global_round:3d}/{args.rounds} | "
              f"AUC={val_metrics['macro_auc']:.4f} | "
              f"Acc={val_metrics['accuracy']:.4f} | "
              f"ε={max_eps:.4f} | "
              f"q={q_global:.4f} | "
              f"{round_time:.1f}s")

        if val_metrics["macro_auc"] > best_auc:
            best_auc = val_metrics["macro_auc"]
            best_state = copy.deepcopy(global_model.state_dict())

        if max_eps >= args.epsilon:
            print(f"Privacy budget exhausted at round {global_round}. Stopping.")
            break

    # Final test evaluation
    global_model.load_state_dict(best_state)
    test_metrics = evaluate_model(global_model, device_loaders[0]["test"], device)
    print(f"\nFinal Test AUC={test_metrics['macro_auc']:.4f} | "
          f"Acc={test_metrics['accuracy']:.4f} | Best val AUC={best_auc:.4f}")

    # Save checkpoint
    if args.save_checkpoint:
        os.makedirs(os.path.dirname(args.save_checkpoint) or ".", exist_ok=True)
        torch.save({"model_state": best_state,
                    "args": vars(args),
                    "q_global": q_global,
                    "test_metrics": test_metrics},
                   args.save_checkpoint)
        print(f"Checkpoint saved: {args.save_checkpoint}")

    # Save CSV results
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results_log[0].keys())
            writer.writeheader()
            writer.writerows(results_log)
        print(f"Results saved: {args.output}")

    return {"test_metrics": test_metrics, "best_auc": best_auc, "log": results_log}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HFL-MM-HC Trainer")
    parser.add_argument("--data_dir",       default="data/processed/healthcare")
    parser.add_argument("--partition_dir",  default="data/processed/partitions/healthcare")
    parser.add_argument("--rounds",         type=int,   default=20)
    parser.add_argument("--tau_e",          type=int,   default=5)
    parser.add_argument("--n_devices",      type=int,   default=20)
    parser.add_argument("--n_edges",        type=int,   default=3)
    parser.add_argument("--n_classes",      type=int,   default=5)
    parser.add_argument("--epsilon",        type=float, default=1.0)
    parser.add_argument("--delta",          type=float, default=1e-5)
    parser.add_argument("--max_grad_norm",  type=float, default=1.0)
    parser.add_argument("--alpha_conf",     type=float, default=0.1)
    parser.add_argument("--lr",             type=float, default=1e-3)
    parser.add_argument("--batch_size",     type=int,   default=32)
    parser.add_argument("--sparsity",       type=float, default=0.2)
    parser.add_argument("--quant_bits",     type=int,   default=8)
    parser.add_argument("--save_checkpoint", default="checkpoints/best_model_hc.pt")
    parser.add_argument("--output",          default="results/phase5/hfl_mm_hc_results.csv")
    args = parser.parse_args()
    train_hfl_mm_hc(args)
