"""
Baseline Suite — Phase 5
B0: Centralized (upper bound, no privacy)
B1: Local Only   (lower bound, no federation)
B2: FedAvg       (McMahan et al., 2017)
B3: FedProx      (Li et al., 2020, proximal regularization)
B4: DP-FedAvg    (Geyer et al., 2017, DP + flat FL)
B5: MOON         (Li et al., 2021, model-contrastive FL)
All run on identical PTB-XL + CheXpert healthcare data splits.
"""

import os
import sys
import copy
import json
import argparse
import time
import csv
from typing import Dict, List, Tuple, Optional

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "data", "loaders"))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset, ConcatDataset
import numpy as np

from device_utils import get_device, optimize_gpu, get_dataloader_kwargs


def evaluate(model: nn.Module, loader: DataLoader,
             device: torch.device, n_classes: int = 5) -> Dict:
    """Compute accuracy and macro-AUC on loader."""
    from sklearn.metrics import roc_auc_score
    model.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for batch in loader:
            ecg, cxr, _tab, labels = batch
            logits = model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
            all_logits.append(logits.cpu())
            all_labels.append(labels.cpu())

    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels).numpy()
    probs = torch.softmax(logits, dim=-1).numpy()
    preds = logits.argmax(dim=-1).numpy()

    acc = float((preds == labels).mean())
    unique_classes = np.unique(labels)
    if len(unique_classes) < 2:
        # Degenerate test set — only 1 class present, AUC undefined
        print(f"[AUC WARNING] Only {len(unique_classes)} class(es) in test set: {unique_classes}. "
              f"Using a global/pooled test set is required for valid AUC.")
        auc = float("nan")  # use accuracy as proxy
    else:
        try:
            auc = float(roc_auc_score(
                labels, probs, multi_class="ovr", average="macro",
                labels=list(range(n_classes))
            ))
        except Exception as e:
            print(f"[AUC ERROR] {e} | unique labels: {unique_classes} | "
                  f"probs shape: {probs.shape} | labels shape: {labels.shape}")
            auc = 0.0

    return {"accuracy": acc, "macro_auc": auc}


def weighted_fedavg(global_state: dict,
                    client_states: List[dict],
                    client_sizes: List[int]) -> dict:
    """Federated Averaging: weighted mean of client model states."""
    total = sum(client_sizes)
    avg_state = {}
    for key in global_state:
        avg_state[key] = sum(
            (n / total) * state[key].float()
            for n, state in zip(client_sizes, client_states)
        )
    return avg_state


# ─────────────────────────────────────────────────────────────────────
# B0: Centralized Training
# ─────────────────────────────────────────────────────────────────────

def run_centralized(model_fn, full_dataset, n_classes: int = 5,
                    epochs: int = 30, lr: float = 1e-3,
                    device: torch.device = None,
                    output_path: str = None) -> dict:
    """B0: Train on pooled data from all devices. Upper bound."""
    if device is None:
        device = get_device(verbose=False)
        optimize_gpu()

    model = model_fn().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    loss_fn = nn.CrossEntropyLoss()

    n = len(full_dataset)
    n_train = int(0.70 * n)
    n_val = int(0.15 * n)
    train_ds = Subset(full_dataset, range(n_train))
    val_ds = Subset(full_dataset, range(n_train, n_train + n_val))
    test_ds = Subset(full_dataset, range(n_train + n_val, n))

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=128, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=128, num_workers=0)

    best_auc, best_state = 0.0, None
    for epoch in range(epochs):
        model.train()
        for batch in train_loader:
            ecg, cxr, _tab, labels = batch
            optimizer.zero_grad()
            loss = loss_fn(model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True)), labels.to(device, non_blocking=True))
            loss.backward()
            optimizer.step()
        scheduler.step()

        val_metrics = evaluate(model, val_loader, device)
        if val_metrics["macro_auc"] > best_auc:
            best_auc = val_metrics["macro_auc"]
            best_state = copy.deepcopy(model.state_dict())

        print(f"[B0 Centralized] Epoch {epoch+1}/{epochs} | "
              f"Val AUC={val_metrics['macro_auc']:.4f} | "
              f"Val Acc={val_metrics['accuracy']:.4f}")

    if best_state is not None:
        model.load_state_dict(best_state)
    test_metrics = evaluate(model, test_loader, device)
    result = {"baseline": "B0_Centralized",
              "test_accuracy": test_metrics["accuracy"],
              "test_macro_auc": test_metrics["macro_auc"],
              "epochs": epochs}
    print(f"[B0] Test AUC={result['test_macro_auc']:.4f}, Acc={result['test_accuracy']:.4f}")
    if output_path:
        _save_csv(result, output_path)
    return result


# ─────────────────────────────────────────────────────────────────────
# B1: Local Only
# ─────────────────────────────────────────────────────────────────────

def run_local_only(model_fn, device_loaders: List[Dict],
                   n_classes: int = 5, epochs: int = 20, lr: float = 1e-3,
                   device: torch.device = None,
                   output_path: str = None) -> dict:
    """B1: Each device trains independently. Lower bound."""
    if device is None:
        device = get_device(verbose=False)
        optimize_gpu()

    device_aucs, device_accs = [], []
    for dev_id, loaders in enumerate(device_loaders):
        model = model_fn().to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = nn.CrossEntropyLoss()
        for ep in range(epochs):
            model.train()
            for batch in loaders["train"]:
                ecg, cxr, _tab, labels = batch
                optimizer.zero_grad()
                loss = loss_fn(model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True)), labels.to(device, non_blocking=True))
                loss.backward()
                optimizer.step()
            if (ep + 1) % 5 == 0 or ep == 0:
                print(f"  [B1] Device {dev_id+1}/{len(device_loaders)} | Epoch {ep+1}/{epochs}")
        metrics = evaluate(model, loaders["test"], device)
        device_aucs.append(metrics["macro_auc"])
        device_accs.append(metrics["accuracy"])
        print(f"  [B1] Device {dev_id+1} done | AUC={metrics['macro_auc']:.4f} | Acc={metrics['accuracy']:.4f}")

    _auc = float(np.nanmean(device_aucs))
    _std = float(np.nanstd(device_aucs))
    _acc = float(np.nanmean(device_accs))
    result = {"baseline": "B1_LocalOnly",
              "test_accuracy": _acc,
              "test_macro_auc": _auc,
              "std_auc": _std}
    _nan_count = sum(1 for a in device_aucs if isinstance(a, float) and np.isnan(a))
    if _nan_count:
        print(f"[B1] {_nan_count}/{len(device_aucs)} devices had single-class test sets "
              f"(AUC undefined) — excluded from average.")
    print(f"[B1] Avg Test AUC={_auc:.4f}±{_std:.4f}")
    if output_path:
        _save_csv(result, output_path)
    return result


# ─────────────────────────────────────────────────────────────────────
# B2: FedAvg
# ─────────────────────────────────────────────────────────────────────

def run_fedavg(model_fn, device_loaders: List[Dict],
               rounds: int = 20, local_epochs: int = 1, lr: float = 1e-3,
               device: torch.device = None,
               output_path: str = None) -> dict:
    """B2: Standard FedAvg, no DP, no hierarchy."""
    if device is None:
        device = get_device(verbose=False)
        optimize_gpu()

    global_model = model_fn().to(device)
    loss_fn = nn.CrossEntropyLoss()
    round_aucs = []

    for r in range(rounds):
        global_state = copy.deepcopy(global_model.state_dict())
        client_states, client_sizes = [], []

        for loaders in device_loaders:
            local_model = model_fn().to(device)
            local_model.load_state_dict(global_state)
            optimizer = torch.optim.Adam(local_model.parameters(), lr=lr)
            local_model.train()
            n_samples = 0
            for _ in range(local_epochs):
                for batch in loaders["train"]:
                    ecg, cxr, _tab, labels = batch
                    optimizer.zero_grad()
                    loss = loss_fn(local_model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True)),
                                   labels.to(device, non_blocking=True))
                    loss.backward()
                    optimizer.step()
                    n_samples += len(labels)
            client_states.append(copy.deepcopy(local_model.state_dict()))
            client_sizes.append(n_samples)

        global_model.load_state_dict(weighted_fedavg(global_state, client_states, client_sizes))

        if (r + 1) % 5 == 0:
            # Evaluate on pooled global test set (all devices) for valid multi-class AUC
            global_test_ds = ConcatDataset([dl["test"].dataset for dl in device_loaders])
            global_test_loader = DataLoader(global_test_ds, batch_size=128, num_workers=0)
            m = evaluate(global_model, global_test_loader, device)
            round_aucs.append(m["macro_auc"])
            print(f"[B2 FedAvg] Round {r+1}/{rounds} | AUC={m['macro_auc']:.4f}")

    global_test_ds = ConcatDataset([dl["test"].dataset for dl in device_loaders])
    global_test_loader = DataLoader(global_test_ds, batch_size=128, num_workers=0)
    final_m = evaluate(global_model, global_test_loader, device)
    result = {"baseline": "B2_FedAvg",
              "test_accuracy": final_m["accuracy"],
              "test_macro_auc": final_m["macro_auc"],
              "rounds": rounds,
              "convergence_auc": round_aucs}
    if output_path:
        _save_csv(result, output_path)
    return result


# ─────────────────────────────────────────────────────────────────────
# B3: FedProx
# ─────────────────────────────────────────────────────────────────────

def run_fedprox(model_fn, device_loaders: List[Dict],
                rounds: int = 20, local_epochs: int = 1,
                lr: float = 1e-3, mu: float = 0.01,
                device: torch.device = None,
                output_path: str = None) -> dict:
    """B3: FedProx — adds proximal term μ/2 ||w - w_global||² to local loss."""
    if device is None:
        device = get_device(verbose=False)
        optimize_gpu()

    global_model = model_fn().to(device)
    loss_fn = nn.CrossEntropyLoss()

    for r in range(rounds):
        global_state = copy.deepcopy(global_model.state_dict())
        client_states, client_sizes = [], []

        for loaders in device_loaders:
            local_model = model_fn().to(device)
            local_model.load_state_dict(global_state)
            optimizer = torch.optim.Adam(local_model.parameters(), lr=lr)
            local_model.train()
            n_samples = 0
            for _ in range(local_epochs):
                for batch in loaders["train"]:
                    ecg, cxr, _tab, labels = batch
                    optimizer.zero_grad()
                    ce_loss = loss_fn(local_model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True)),
                                      labels.to(device, non_blocking=True))
                    # Proximal term
                    prox = sum(
                        ((p - global_state[n].to(device)) ** 2).sum()
                        for n, p in local_model.named_parameters()
                        if n in global_state
                    )
                    loss = ce_loss + (mu / 2.0) * prox
                    loss.backward()
                    optimizer.step()
                    n_samples += len(labels)
            client_states.append(copy.deepcopy(local_model.state_dict()))
            client_sizes.append(n_samples)

        global_model.load_state_dict(weighted_fedavg(global_state, client_states, client_sizes))
        print(f"  [B3 FedProx] Round {r+1}/{rounds} done")

    global_test_ds = ConcatDataset([dl["test"].dataset for dl in device_loaders])
    global_test_loader = DataLoader(global_test_ds, batch_size=128, num_workers=0)
    final_m = evaluate(global_model, global_test_loader, device)
    result = {"baseline": "B3_FedProx",
              "test_accuracy": final_m["accuracy"],
              "test_macro_auc": final_m["macro_auc"],
              "mu": mu, "rounds": rounds}
    print(f"[B3] FedProx AUC={final_m['macro_auc']:.4f}")
    if output_path:
        _save_csv(result, output_path)
    return result


# ─────────────────────────────────────────────────────────────────────
# B4: DP-FedAvg (flat, no hierarchy)
# ─────────────────────────────────────────────────────────────────────

def run_dp_fedavg(model_fn, device_loaders: List[Dict],
                  rounds: int = 20, local_epochs: int = 1,
                  lr: float = 1e-3, epsilon: float = 1.0,
                  delta: float = 1e-5, max_grad_norm: float = 1.0,
                  device: torch.device = None,
                  output_path: str = None) -> dict:
    """B4: DP-FedAvg — flat topology + DP-SGD (no 2-tier hierarchy)."""
    if device is None:
        device = get_device(verbose=False)
        optimize_gpu()

    from dp_engine import make_dp_model, get_epsilon_spent

    global_model = model_fn().to(device)
    global_state = copy.deepcopy(global_model.state_dict())
    client_states, client_sizes = [], []
    total_eps = 0.0

    for dev_idx, loaders in enumerate(device_loaders):
        print(f"  [B4 DP-FedAvg] Device {dev_idx+1}/{len(device_loaders)} — DP-SGD training...")
        local_model = model_fn().to(device)
        local_model.load_state_dict(global_state)
        optimizer = torch.optim.Adam(local_model.parameters(), lr=lr)
        try:
            dp_model, dp_opt, dp_loader, pe = make_dp_model(
                local_model, optimizer, loaders["train"],
                target_epsilon=epsilon, target_delta=delta,
                max_grad_norm=max_grad_norm, epochs=local_epochs * rounds
            )
            loss_fn = nn.CrossEntropyLoss()
            dp_model.train()
            n_samples = 0
            for _ in range(local_epochs):
                for batch in dp_loader:
                    ecg, cxr, _tab, labels = batch
                    dp_opt.zero_grad()
                    loss = loss_fn(dp_model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True)),
                                   labels.to(device, non_blocking=True))
                    loss.backward()
                    dp_opt.step()
                    n_samples += len(labels)
            total_eps = max(total_eps, get_epsilon_spent(pe, delta))
            client_states.append(copy.deepcopy(local_model.state_dict()))
            client_sizes.append(n_samples)
        except Exception as e:
            raise RuntimeError(f"[B4] DP-SGD setup failed: {e}") from e

    global_model.load_state_dict(weighted_fedavg(global_state, client_states, client_sizes))
    global_test_ds = ConcatDataset([dl["test"].dataset for dl in device_loaders])
    global_test_loader = DataLoader(global_test_ds, batch_size=128, num_workers=0)
    final_m = evaluate(global_model, global_test_loader, device)
    result = {"baseline": "B4_DP_FedAvg",
              "test_accuracy": final_m["accuracy"],
              "test_macro_auc": final_m["macro_auc"],
              "epsilon_target": epsilon,
              "epsilon_spent": total_eps}
    print(f"[B4] DP-FedAvg AUC={final_m['macro_auc']:.4f} | ε_spent={total_eps:.4f}")
    if output_path:
        _save_csv(result, output_path)
    return result


# ─────────────────────────────────────────────────────────────────────
# B5: MOON (Model-Contrastive FL)
# ─────────────────────────────────────────────────────────────────────

def run_moon(model_fn, device_loaders: List[Dict],
             rounds: int = 20, local_epochs: int = 1,
             lr: float = 1e-3, mu: float = 5.0, temperature: float = 0.5,
             device: torch.device = None,
             output_path: str = None) -> dict:
    """
    B5: MOON — Model-Contrastive FL.
    Contrastive loss pulls current model toward global, pushes from previous.
    Li et al., 2021. cos_sim(z_cur, z_global) > cos_sim(z_cur, z_prev)
    """
    if device is None:
        device = get_device(verbose=False)
        optimize_gpu()

    global_model = model_fn().to(device)
    prev_models = [model_fn().to(device) for _ in device_loaders]
    loss_fn = nn.CrossEntropyLoss()

    for r in range(rounds):
        global_state = copy.deepcopy(global_model.state_dict())
        client_states, client_sizes = [], []

        for dev_id, loaders in enumerate(device_loaders):
            local_model = model_fn().to(device)
            local_model.load_state_dict(global_state)
            optimizer = torch.optim.Adam(local_model.parameters(), lr=lr)
            local_model.train()
            n_samples = 0

            for _ in range(local_epochs):
                for batch in loaders["train"]:
                    ecg, cxr, _tab, labels = batch
                    ecg, cxr, labels = ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True), labels.to(device, non_blocking=True)
                    optimizer.zero_grad()

                    logits = local_model(ecg, cxr)
                    ce_loss = loss_fn(logits, labels)

                    # Contrastive term (MOON)
                    with torch.no_grad():
                        z_global_a, z_global_b = global_model.encode(ecg, cxr)
                        z_prev_a, z_prev_b = prev_models[dev_id].encode(ecg, cxr)

                    z_cur_a, z_cur_b = local_model.encode(ecg, cxr)
                    z_cur = torch.cat([z_cur_a, z_cur_b], dim=-1)
                    z_global = torch.cat([z_global_a, z_global_b], dim=-1)
                    z_prev = torch.cat([z_prev_a, z_prev_b], dim=-1)

                    sim_global = F.cosine_similarity(z_cur, z_global, dim=-1) / temperature
                    sim_prev = F.cosine_similarity(z_cur, z_prev, dim=-1) / temperature

                    contrastive_loss = -torch.log(
                        torch.exp(sim_global) / (torch.exp(sim_global) + torch.exp(sim_prev))
                    ).mean()

                    loss = ce_loss + mu * contrastive_loss
                    loss.backward()
                    optimizer.step()
                    n_samples += len(labels)

            prev_models[dev_id].load_state_dict(copy.deepcopy(global_state))
            client_states.append(copy.deepcopy(local_model.state_dict()))
            client_sizes.append(n_samples)

        global_model.load_state_dict(weighted_fedavg(global_state, client_states, client_sizes))
        print(f"  [B5 MOON] Round {r+1}/{rounds} done")

    global_test_ds = ConcatDataset([dl["test"].dataset for dl in device_loaders])
    global_test_loader = DataLoader(global_test_ds, batch_size=128, num_workers=0)
    final_m = evaluate(global_model, global_test_loader, device)
    result = {"baseline": "B5_MOON",
              "test_accuracy": final_m["accuracy"],
              "test_macro_auc": final_m["macro_auc"],
              "mu": mu, "temperature": temperature, "rounds": rounds}
    print(f"[B5] MOON AUC={final_m['macro_auc']:.4f}")
    if output_path:
        _save_csv(result, output_path)
    return result


def _save_csv(result: dict, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # Serialize list/dict values so csv.DictWriter doesn't choke
    serialized = {k: json.dumps(v) if isinstance(v, (list, dict)) else v
                  for k, v in result.items()}
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=serialized.keys())
        writer.writeheader()
        writer.writerow(serialized)
    print(f"Saved: {path}")


if __name__ == "__main__":
    # ─── Paths ────────────────────────────────────────────────────────
    _model_dir = os.path.dirname(os.path.abspath(__file__))
    _sim_dir   = os.path.dirname(_model_dir)

    parser = argparse.ArgumentParser(description="Run all FL baselines B0–B5")
    parser.add_argument("--data_dir",      default=os.path.join(_sim_dir, "data", "processed", "healthcare"))
    parser.add_argument("--partition_dir", default=os.path.join(_sim_dir, "data", "processed", "partitions", "healthcare"))
    parser.add_argument("--output_dir",    default=os.path.join(_sim_dir, "results", "phase5"))
    parser.add_argument("--b0_epochs",     type=int,   default=5,   help="B0 centralized training epochs")
    parser.add_argument("--b1_epochs",     type=int,   default=10,  help="B1 local-only epochs per device")
    parser.add_argument("--rounds",        type=int,   default=10,  help="FL rounds for B2–B5")
    parser.add_argument("--local_epochs",  type=int,   default=1,   help="Local epochs per FL round")
    parser.add_argument("--batch_size",    type=int,   default=16)
    parser.add_argument("--lr",            type=float, default=1e-3)
    parser.add_argument("--epsilon",       type=float, default=1.0, help="DP epsilon for B4")
    parser.add_argument("--skip",          nargs="*",  default=[],
                        help="Baselines to skip, e.g. --skip b4 b5")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # ─── Imports ──────────────────────────────────────────────────────
    from preprocess_healthcare import HealthcareDataset
    from hfl_mm_model import build_hfl_mm_hc

    # ─── Load data once (shared across all baselines) ─────────────────
    print("=" * 65)
    print("BASELINE SUITE — Phase 5 Healthcare FL")
    print("=" * 65)
    print(f"\nLoading healthcare data from:\n  {args.data_dir}")

    ecg_signals   = np.load(os.path.join(args.data_dir, "ecg", "ecg_signals.npy"),   mmap_mode="r")
    ecg_labels    = np.load(os.path.join(args.data_dir, "ecg", "ecg_labels.npy"))
    cxr_images    = np.load(os.path.join(args.data_dir, "cxr", "cxr_images.npy"),    mmap_mode="r")
    cxr_labels    = np.load(os.path.join(args.data_dir, "cxr", "cxr_labels.npy"))
    tabular_feats = np.load(os.path.join(args.data_dir, "tabular", "tabular_features.npy"))

    print(f"  ECG  : {ecg_signals.shape}  labels: {np.unique(ecg_labels, return_counts=True)[1].tolist()}")
    print(f"  CXR  : {cxr_images.shape}")
    print(f"  Tab  : {tabular_feats.shape}")

    print("\nBuilding HealthcareDataset (pairs ECG+CXR+tabular)...")
    full_ds = HealthcareDataset(ecg_signals, ecg_labels,
                                cxr_images, cxr_labels,
                                tabular_feats)
    print(f"  Full dataset: {len(full_ds)} samples")

    # ─── Load partition metadata ───────────────────────────────────────
    meta_path = os.path.join(args.partition_dir, "partition_meta.json")
    with open(meta_path) as _f:
        meta = json.load(_f)
    n_devices = meta["n_devices"]
    print(f"  Partitions  : {n_devices} devices loaded from {args.partition_dir}")

    # ─── Per-device DataLoaders (train + test) ─────────────────────────
    device_loaders = []
    for dev_id in range(n_devices):
        _train_idx = np.load(os.path.join(args.partition_dir, f"device_{dev_id:02d}_train.npy"))
        _test_idx  = np.load(os.path.join(args.partition_dir, f"device_{dev_id:02d}_test.npy"))
        _train_ds  = Subset(full_ds, _train_idx.tolist())
        _test_ds   = Subset(full_ds, _test_idx.tolist())
        device_loaders.append({
            "train": DataLoader(_train_ds, batch_size=args.batch_size,
                                shuffle=True, num_workers=0),
            "test":  DataLoader(_test_ds,  batch_size=args.batch_size * 2,
                                num_workers=0),
        })

    # ─── Device + model factory ───────────────────────────────────────
    _device = get_device()
    optimize_gpu()

    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)   # suppress opacus/sklearn noise

    def model_fn():
        return build_hfl_mm_hc(n_classes=5)

    all_results = []

    # ──────────────────────────────────────────────────────────────────
    # B0: Centralized  (upper bound — no DP, no federation)
    # ──────────────────────────────────────────────────────────────────
    if "b0" not in [s.lower() for s in args.skip]:
        print("\n" + "=" * 65)
        print(f"B0 CENTRALIZED  |  epochs={args.b0_epochs}  |  batch={args.batch_size}")
        print("=" * 65)
        r = run_centralized(
            model_fn, full_ds,
            epochs=args.b0_epochs, lr=args.lr,
            device=_device,
            output_path=os.path.join(args.output_dir, "baseline_b0.csv"),
        )
        all_results.append(r)

    # ──────────────────────────────────────────────────────────────────
    # B1: Local Only  (lower bound)
    # ──────────────────────────────────────────────────────────────────
    if "b1" not in [s.lower() for s in args.skip]:
        print("\n" + "=" * 65)
        print(f"B1 LOCAL ONLY   |  epochs={args.b1_epochs}  |  batch={args.batch_size}")
        print("=" * 65)
        r = run_local_only(
            model_fn, device_loaders,
            epochs=args.b1_epochs, lr=args.lr,
            device=_device,
            output_path=os.path.join(args.output_dir, "baseline_b1.csv"),
        )
        all_results.append(r)

    # ──────────────────────────────────────────────────────────────────
    # B2: FedAvg
    # ──────────────────────────────────────────────────────────────────
    if "b2" not in [s.lower() for s in args.skip]:
        print("\n" + "=" * 65)
        print(f"B2 FEDAVG       |  rounds={args.rounds}  local_epochs={args.local_epochs}  |  batch={args.batch_size}")
        print("=" * 65)
        r = run_fedavg(
            model_fn, device_loaders,
            rounds=args.rounds, local_epochs=args.local_epochs, lr=args.lr,
            device=_device,
            output_path=os.path.join(args.output_dir, "baseline_b2.csv"),
        )
        all_results.append(r)

    # ──────────────────────────────────────────────────────────────────
    # B3: FedProx
    # ──────────────────────────────────────────────────────────────────
    if "b3" not in [s.lower() for s in args.skip]:
        print("\n" + "=" * 65)
        print(f"B3 FEDPROX      |  rounds={args.rounds}  local_epochs={args.local_epochs}  |  batch={args.batch_size}")
        print("=" * 65)
        r = run_fedprox(
            model_fn, device_loaders,
            rounds=args.rounds, local_epochs=args.local_epochs, lr=args.lr,
            device=_device,
            output_path=os.path.join(args.output_dir, "baseline_b3.csv"),
        )
        all_results.append(r)

    # ──────────────────────────────────────────────────────────────────
    # B4: DP-FedAvg  (flat FL + differential privacy)
    # ──────────────────────────────────────────────────────────────────
    if "b4" not in [s.lower() for s in args.skip]:
        print("\n" + "=" * 65)
        print(f"B4 DP-FEDAVG    |  rounds={args.rounds}  ε={args.epsilon}  |  batch={args.batch_size}")
        print("=" * 65)
        try:
            r = run_dp_fedavg(
                model_fn, device_loaders,
                rounds=args.rounds, local_epochs=args.local_epochs,
                lr=args.lr, epsilon=args.epsilon,
                device=_device,
                output_path=os.path.join(args.output_dir, "baseline_b4.csv"),
            )
            all_results.append(r)
        except Exception as _e:
            print(f"[B4 SKIPPED] DP-FedAvg failed: {_e}")
            all_results.append({"baseline": "B4_DP_FedAvg",
                                 "test_accuracy": float("nan"),
                                 "test_macro_auc": float("nan"),
                                 "error": str(_e)})

    # ──────────────────────────────────────────────────────────────────
    # B5: MOON  (Model-Contrastive FL)
    # ──────────────────────────────────────────────────────────────────
    if "b5" not in [s.lower() for s in args.skip]:
        print("\n" + "=" * 65)
        print(f"B5 MOON         |  rounds={args.rounds}  local_epochs={args.local_epochs}  |  batch={args.batch_size}")
        print("=" * 65)
        r = run_moon(
            model_fn, device_loaders,
            rounds=args.rounds, local_epochs=args.local_epochs, lr=args.lr,
            device=_device,
            output_path=os.path.join(args.output_dir, "baseline_b5.csv"),
        )
        all_results.append(r)

    # ──────────────────────────────────────────────────────────────────
    # Summary table + combined CSV
    # ──────────────────────────────────────────────────────────────────
    summary_path = os.path.join(args.output_dir, "baselines_summary.csv")
    _summary_fields = ["baseline", "test_accuracy", "test_macro_auc"]
    with open(summary_path, "w", newline="") as _f:
        _w = csv.DictWriter(_f, fieldnames=_summary_fields, extrasaction="ignore")
        _w.writeheader()
        for _r in all_results:
            _w.writerow({k: _r.get(k, "") for k in _summary_fields})
    print(f"\nSummary CSV saved: {summary_path}")

    print("\n" + "=" * 65)
    print("BASELINE COMPARISON SUMMARY")
    print("=" * 65)
    print(f"{'Baseline':<28}  {'Accuracy':>9}  {'Macro-AUC':>10}")
    print("-" * 55)
    for _r in all_results:
        _name = _r.get("baseline", "?")
        _acc  = _r.get("test_accuracy", float("nan"))
        _auc  = _r.get("test_macro_auc", float("nan"))
        _acc_s = f"{_acc:.4f}" if isinstance(_acc, float) and not np.isnan(_acc) else "  N/A"
        _auc_s = f"{_auc:.4f}" if isinstance(_auc, float) and not np.isnan(_auc) else "  N/A"
        print(f"{_name:<28}  {_acc_s:>9}  {_auc_s:>10}")
    print("=" * 65)
    print("\nDone. Scores above establish baselines B0–B5 for Phase 5 comparison.")
