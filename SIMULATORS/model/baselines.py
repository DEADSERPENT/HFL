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
import copy
import json
import argparse
import time
import csv
from typing import Dict, List, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset, ConcatDataset
import numpy as np

from device_utils import get_device, optimize_gpu, get_dataloader_kwargs


def evaluate(model: nn.Module, loader: DataLoader,
             device: torch.device) -> Dict:
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
    try:
        auc = roc_auc_score(labels, probs, multi_class="ovr", average="macro")
    except Exception:
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

        if (epoch + 1) % 5 == 0:
            print(f"[B0 Centralized] Epoch {epoch+1}/{epochs} | "
                  f"Val AUC={val_metrics['macro_auc']:.4f} | "
                  f"Val Acc={val_metrics['accuracy']:.4f}")

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
        for _ in range(epochs):
            model.train()
            for batch in loaders["train"]:
                ecg, cxr, _tab, labels = batch
                optimizer.zero_grad()
                loss = loss_fn(model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True)), labels.to(device, non_blocking=True))
                loss.backward()
                optimizer.step()
        metrics = evaluate(model, loaders["test"], device)
        device_aucs.append(metrics["macro_auc"])
        device_accs.append(metrics["accuracy"])

    result = {"baseline": "B1_LocalOnly",
              "test_accuracy": float(np.mean(device_accs)),
              "test_macro_auc": float(np.mean(device_aucs)),
              "std_auc": float(np.std(device_aucs))}
    print(f"[B1] Avg Test AUC={result['test_macro_auc']:.4f}±{result['std_auc']:.4f}")
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
            # Evaluate on first device test set as proxy
            m = evaluate(global_model, device_loaders[0]["test"], device)
            round_aucs.append(m["macro_auc"])
            print(f"[B2 FedAvg] Round {r+1}/{rounds} | AUC={m['macro_auc']:.4f}")

    final_m = evaluate(global_model, device_loaders[0]["test"], device)
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

    final_m = evaluate(global_model, device_loaders[0]["test"], device)
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

    for loaders in device_loaders:
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
    final_m = evaluate(global_model, device_loaders[0]["test"], device)
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

    final_m = evaluate(global_model, device_loaders[0]["test"], device)
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
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=result.keys())
        writer.writeheader()
        writer.writerow(result)
    print(f"Saved: {path}")


if __name__ == "__main__":
    print("Baseline suite loaded. Run individual baselines via hfl_trainer.py --mode.")
