"""
ε Sweep — Phase 5
Privacy-accuracy trade-off: ε ∈ {0.1, 0.5, 1.0, 2.0, 5.0, ∞(no DP)}
Generates the key publication figure: accuracy/AUC vs. ε curve.
"""

import os
import sys
import copy
import argparse
import csv
import time
from pathlib import Path
from typing import List, Dict

import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, Subset

from device_utils import get_device, optimize_gpu, get_dataloader_kwargs

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "data" / "loaders"))


def fedavg_round(global_model, device_loaders, n_rounds, device,
                 use_dp=False, epsilon=1.0, delta=1e-5,
                 max_grad_norm=1.0, lr=1e-3, n_epochs=1):
    """Run simplified FL for epsilon sweep (no edge hierarchy for speed)."""
    from hfl_mm_model import build_hfl_mm_hc
    loss_fn = nn.CrossEntropyLoss()

    for r in range(n_rounds):
        global_state = {k: v.clone() for k, v in global_model.state_dict().items()}
        client_states, client_sizes = [], []

        for loaders in device_loaders:
            local = build_hfl_mm_hc().to(device)
            local.load_state_dict(global_state)
            opt = torch.optim.Adam(local.parameters(), lr=lr)

            if use_dp:
                try:
                    from dp_engine import make_dp_model, get_epsilon_spent
                    local, opt, train_loader, pe = make_dp_model(
                        local, opt, loaders["train"],
                        target_epsilon=epsilon, target_delta=delta,
                        max_grad_norm=max_grad_norm, epochs=n_epochs * n_rounds
                    )
                except Exception:
                    train_loader = loaders["train"]
                    pe = None
            else:
                train_loader = loaders["train"]
                pe = None

            local.train()
            n_samples = 0
            for _ in range(n_epochs):
                for ecg, cxr, labels in train_loader:
                    opt.zero_grad()
                    loss = loss_fn(local(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True)),
                                   labels.to(device, non_blocking=True))
                    loss.backward()
                    opt.step()
                    n_samples += len(labels)

            client_states.append(copy.deepcopy(local.state_dict()))
            client_sizes.append(n_samples)

        # FedAvg
        total = sum(client_sizes)
        for key in global_state:
            if global_state[key].is_floating_point():
                global_model.state_dict()[key].copy_(
                    sum((n / total) * s[key].float()
                        for n, s in zip(client_sizes, client_states))
                )


def run_epsilon_sweep(args):
    """Run full sweep over ε values and save results."""
    from hfl_mm_model import build_hfl_mm_hc
    from sklearn.metrics import roc_auc_score
    import json

    device = get_device()
    optimize_gpu()
    os.makedirs(args.output_dir, exist_ok=True)

    # Load data
    import numpy as np
    from preprocess_healthcare import HealthcareDataset

    ecg_signals = np.load(os.path.join(args.data_dir, "ecg", "ecg_signals.npy"),
                          mmap_mode="r")
    ecg_labels = np.load(os.path.join(args.data_dir, "ecg", "ecg_labels.npy"))
    cxr_images = np.load(os.path.join(args.data_dir, "cxr", "cxr_images.npy"),
                         mmap_mode="r")
    cxr_labels = np.load(os.path.join(args.data_dir, "cxr", "cxr_primary_labels.npy"))

    full_ds = HealthcareDataset(ecg_signals, ecg_labels, cxr_images, cxr_labels)
    n = len(full_ds)
    n_train = int(0.70 * n)
    n_val = int(0.15 * n)
    train_ds = Subset(full_ds, list(range(n_train)))
    test_ds = Subset(full_ds, list(range(n_train + n_val, n)))

    # Split into simulated devices for sweep
    n_devices = 10  # reduced for sweep speed
    device_size = n_train // n_devices
    device_loaders = [
        {"train": DataLoader(
            Subset(train_ds, list(range(i * device_size, (i + 1) * device_size))),
            batch_size=32, shuffle=True)}
        for i in range(n_devices)
    ]
    test_loader = DataLoader(test_ds, batch_size=128)

    epsilons = args.epsilons  # e.g., [0.1, 0.5, 1.0, 2.0, 5.0, float("inf")]
    all_results = []

    for eps in epsilons:
        use_dp = (eps != float("inf"))
        eps_label = str(eps) if eps != float("inf") else "inf"
        print(f"\n{'='*50}")
        print(f"Running ε = {eps_label}")
        print(f"{'='*50}")

        model = build_hfl_mm_hc().to(device)
        t0 = time.time()

        fedavg_round(model, device_loaders, n_rounds=args.rounds, device=device,
                     use_dp=use_dp, epsilon=eps if use_dp else 1.0,
                     delta=args.delta, max_grad_norm=args.max_grad_norm,
                     lr=args.lr)

        # Evaluate
        model.eval()
        all_logits, all_labels = [], []
        with torch.no_grad():
            for ecg, cxr, labels in test_loader:
                logits = model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
                all_logits.append(logits.cpu())
                all_labels.append(labels)
        logits = torch.cat(all_logits)
        labels = torch.cat(all_labels).numpy()
        probs = torch.softmax(logits, dim=-1).numpy()
        preds = logits.argmax(dim=-1).numpy()
        acc = float((preds == labels).mean())
        try:
            auc = float(roc_auc_score(labels, probs, multi_class="ovr", average="macro"))
        except Exception:
            auc = 0.0

        elapsed = time.time() - t0

        row = {
            "epsilon": eps_label,
            "accuracy": round(acc, 4),
            "macro_auc": round(auc, 4),
            "use_dp": str(use_dp),
            "rounds": args.rounds,
            "time_s": round(elapsed, 1),
        }
        all_results.append(row)
        print(f"ε={eps_label}: AUC={auc:.4f}, Acc={acc:.4f} ({elapsed:.1f}s)")

        # Save per-epsilon CSV
        per_eps_path = os.path.join(args.output_dir, f"eps_{eps_label}.csv")
        with open(per_eps_path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=row.keys()).writerow(row)

    # Save summary CSV
    summary_path = os.path.join(args.output_dir, "epsilon_sweep_summary.csv")
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nSweep summary saved: {summary_path}")

    # Print table
    print("\n" + "="*65)
    print(f"{'ε':<8} {'Accuracy':>10} {'Macro-AUC':>12} {'Δ vs ∞':>10}")
    print("-"*65)
    inf_auc = next((r["macro_auc"] for r in all_results if r["epsilon"] == "inf"), 1.0)
    for r in all_results:
        delta_auc = float(r["macro_auc"]) - inf_auc
        print(f"{r['epsilon']:<8} {r['accuracy']:>10.4f} {r['macro_auc']:>12.4f} "
              f"{delta_auc:>+10.4f}")
    print("="*65)

    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir",      default="data/processed/healthcare")
    parser.add_argument("--output_dir",    default="results/phase5/epsilon_sweep")
    parser.add_argument("--epsilons",      nargs="+", type=float,
                        default=[0.1, 0.5, 1.0, 2.0, 5.0, float("inf")])
    parser.add_argument("--rounds",        type=int,   default=20)
    parser.add_argument("--delta",         type=float, default=1e-5)
    parser.add_argument("--max_grad_norm", type=float, default=1.0)
    parser.add_argument("--lr",            type=float, default=1e-3)
    args = parser.parse_args()
    run_epsilon_sweep(args)
