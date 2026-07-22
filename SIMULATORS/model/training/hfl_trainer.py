"""
HFL-MM-HC Training Engine — Phase 5
Two-tier FedAvg: 6 healthcare IoT devices -> 2 Edge servers -> 1 Cloud server
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
from datetime import datetime
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, Subset

_MODEL_ROOT = Path(__file__).parent.parent   # model/ — now split into subfolders
                                              # by concern (privacy/architecture/
                                              # training/deploy/utils); add them
                                              # all so existing flat imports
                                              # ("from dp_engine import ...")
                                              # keep resolving regardless of
                                              # which subfolder a module lives in.
for _sub in ("privacy", "architecture", "training", "deploy", "utils"):
    sys.path.insert(0, str(_MODEL_ROOT / _sub))
sys.path.insert(0, str(_MODEL_ROOT.parent / "data" / "loaders"))

from device_utils import (get_device, optimize_gpu, get_dataloader_kwargs,
                          gpu_memory_info, set_seed)


def build_full_healthcare_dataset(processed_dir: str):
    """
    Materialise the full multimodal dataset ONCE.

    Each HealthcareDataset instance copies the entire ECG (240 MB) + CXR
    (1.8 GB) arrays into resident torch tensors (~2 GB RSS). Building one
    instance per device would multiply that by n_devices and OOM a 16 GB
    machine. Callers must build this once and share it across all devices
    via Subset (see load_partitioned_data).
    """
    from preprocess_healthcare import HealthcareDataset

    ecg_signals    = np.load(os.path.join(processed_dir, "ecg", "ecg_signals.npy"),
                             mmap_mode="r")
    ecg_labels     = np.load(os.path.join(processed_dir, "ecg", "ecg_labels.npy"))
    cxr_images     = np.load(os.path.join(processed_dir, "cxr", "cxr_images.npy"),
                             mmap_mode="r")
    cxr_labels     = np.load(os.path.join(processed_dir, "cxr", "cxr_labels.npy"))
    tabular_feats  = np.load(os.path.join(processed_dir, "tabular",
                                          "tabular_features.npy"))

    return HealthcareDataset(ecg_signals, ecg_labels,
                             cxr_images, cxr_labels,
                             tabular_feats)


def load_partitioned_data(partition_dir: str, processed_dir: str,
                          device_id: int, batch_size: int = 32,
                          full_ds=None):
    """
    Load train/val/test loaders for a specific device.

    Pass `full_ds` (from build_full_healthcare_dataset) to share a single
    in-RAM dataset across all devices. Omitting it builds a fresh full copy
    per call — safe for one-off use, but NEVER do that in a per-device loop.
    """
    if full_ds is None:
        full_ds = build_full_healthcare_dataset(processed_dir)

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
        for ecg, cxr, _tab, labels in loader:
            logits = model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
            all_logits.append(logits.cpu())
            all_labels.append(labels.cpu())
    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels).numpy()
    probs = torch.softmax(logits, dim=-1).numpy()
    preds = logits.argmax(dim=-1).numpy()
    acc = float((preds == labels).mean())
    unique_classes = np.unique(labels)
    try:
        auc = float(roc_auc_score(labels, probs, multi_class="ovr", average="macro",
                                  labels=list(range(probs.shape[1]))))
    except Exception as e:
        print(f"[AUC ERROR] {e} | unique labels: {unique_classes}")
        auc = 0.0
    return {"accuracy": acc, "macro_auc": auc}


def local_dp_train(model: nn.Module, loader: DataLoader,
                   device: torch.device, delta: float,
                   max_grad_norm: float, lr: float,
                   noise_multiplier: float,
                   n_epochs: int = 1,
                   privacy_engine=None,
                   dp_mode: str = "uniform",
                   group_of: Optional[Dict[str, int]] = None) -> Dict:
    """
    DP-SGD local training for one FL round.

    noise_multiplier must be pre-computed once via compute_fl_noise_multiplier()
    (dp_mode="uniform") or compute_sadp_noise_multiplier() (dp_mode="sadp")
    for the full training budget (global_rounds × edge_rounds × local_epochs).
    Using the same fixed σ each round is what makes the end-to-end privacy
    accounting valid.

    privacy_engine: pass the SAME tracking object across every call for a
    given device (an Opacus PrivacyEngine for "uniform", a SADPPrivacyTracker
    for "sadp" — see get_persistent_privacy_engines / SADPPrivacyTracker).
    Both accumulate step history additively across calls, so reusing one
    instance per device for its whole FL lifetime is what makes the reported
    ε the true *cumulative* ε for that device. Passing None (uniform mode
    only) creates a fresh engine whose ε only reflects this single call —
    do not use None inside the FL round loop.

    dp_mode="sadp": per-layer-depth-group clip+noise (PHANTOM-FL Innovation
    I2 — see model/sadp_engine.py) instead of one global clip+noise for the
    whole model. group_of (from sadp_engine.assign_depth_groups) is required.
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()

    try:
        if dp_mode == "sadp":
            from sadp_engine import make_sadp_model
            dp_model, dp_opt = make_sadp_model(
                model, optimizer, sigma_base=noise_multiplier,
                max_grad_norm=max_grad_norm, group_of=group_of,
            )
            dp_model.train()
            total_loss, total = 0.0, 0
            for _ in range(n_epochs):
                for ecg, cxr, _tab, labels in loader:
                    dp_opt.zero_grad()
                    logits = dp_model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
                    loss = loss_fn(logits, labels.to(device, non_blocking=True))
                    loss.backward()
                    dp_opt.step()
                    total_loss += loss.item() * len(labels)
                    total += len(labels)
            sample_rate = min(loader.batch_size / max(len(loader.dataset), 1), 1.0)
            steps_this_call = n_epochs * len(loader)
            privacy_engine.record(noise_multiplier, sample_rate, steps_this_call)
            eps_spent = privacy_engine.get_epsilon(delta)
        else:
            from dp_engine import make_dp_model, get_epsilon_spent
            dp_model, dp_opt, dp_loader, pe = make_dp_model(
                model, optimizer, loader,
                noise_multiplier=noise_multiplier,
                max_grad_norm=max_grad_norm,
                privacy_engine=privacy_engine,
            )
            dp_model.train()
            total_loss, total = 0.0, 0
            for _ in range(n_epochs):
                for ecg, cxr, _tab, labels in dp_loader:
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

    # Reproducibility: fix the RNG stream (python/numpy/torch/CUDA). This does
    # not change the algorithm — it only makes a run repeatable. Defensive so
    # the trainer still runs if the engineering package is unavailable.
    _seed = int(getattr(args, "seed", 42))
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # SIMULATORS/ — engineering/ lives here
        from engineering.runctx import set_global_seed
        set_global_seed(_seed, deterministic=bool(getattr(args, "deterministic", False)))
    except Exception:
        set_seed(_seed)   # fallback to device_utils.set_seed

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

    # Build the full multimodal dataset ONCE (~2 GB RSS) and share it across
    # all devices via Subset. Building one dataset per device would multiply
    # RAM by n_devices (~12 GB for 6 devices) and OOM/freeze a 16 GB machine.
    print("Loading full healthcare dataset (shared across devices)...")
    full_ds = build_full_healthcare_dataset(args.data_dir)

    # Lazy-load device loaders: build on first access, reuse thereafter.
    # All loaders index into the single shared `full_ds` above.
    _loader_cache: Dict[int, dict] = {}

    def get_device_loaders(dev_id: int) -> dict:
        if dev_id not in _loader_cache:
            _loader_cache[dev_id] = load_partitioned_data(
                args.partition_dir, args.data_dir, dev_id, args.batch_size,
                full_ds=full_ds)
        return _loader_cache[dev_id]

    # Pre-compute σ for the full FL budget once.
    # Each device trains for (global_rounds × edge_rounds) local calls.
    # Using a fixed σ across all calls is what makes end-to-end DP valid.
    # n_train is read from partition metadata (no data pre-load needed here).
    n_fl_calls_total = args.rounds * args.tau_e   # per-device total local calls
    sadp_group_of = None
    if args.dp_mode == "sadp":
        from sadp_engine import assign_depth_groups, compute_sadp_noise_multiplier, SADPPrivacyTracker
        # Group assignment only depends on architecture (module names), not
        # on any trained weights, so a throwaway instance is enough.
        sadp_group_of = assign_depth_groups(build_hfl_mm_hc(n_classes=args.n_classes))
        if args.noise_multiplier is not None:
            noise_multiplier = args.noise_multiplier
            print(f"[SADP-Engine] Using manually specified σ_base={noise_multiplier:.4f}")
        else:
            _n_train_min = min(
                meta["devices"][str(d)]["n_train"] for d in range(n_devices)
            )
            noise_multiplier = compute_sadp_noise_multiplier(
                target_epsilon=args.epsilon,
                target_delta=args.delta,
                n_fl_calls=n_fl_calls_total,
                n_samples=_n_train_min,
                batch_size=args.batch_size,
                local_epochs=1,
            )
        # One tracker per device, reused for every local-training call that
        # device makes across the ENTIRE run — same reasoning as the Opacus
        # PrivacyEngine reuse below, just for SADP's own RDP composition.
        device_privacy_engines = {d: SADPPrivacyTracker() for d in range(n_devices)}
    elif args.noise_multiplier is not None:
        noise_multiplier = args.noise_multiplier
        print(f"[DP-Engine] Using manually specified σ={noise_multiplier:.4f}")
    else:
        from dp_engine import compute_fl_noise_multiplier
        _n_train_min = min(
            meta["devices"][str(d)]["n_train"] for d in range(n_devices)
        )
        noise_multiplier = compute_fl_noise_multiplier(
            target_epsilon=args.epsilon,
            target_delta=args.delta,
            n_fl_calls=n_fl_calls_total,
            n_samples=_n_train_min,
            batch_size=args.batch_size,
            local_epochs=1,
        )

    # One PrivacyEngine per device, reused for every local-training call that
    # device makes across the ENTIRE run. Opacus's accountant lives on the
    # engine and composes ε additively across make_private() calls — reusing
    # one engine per device (not a fresh one per call) is what makes
    # cumulative_eps below the true composed privacy loss, per device, rather
    # than a proxy that only reflects the most recent local training call.
    if args.dp_mode != "sadp":
        from dp_engine import new_device_privacy_engines
        device_privacy_engines = new_device_privacy_engines(n_devices)

    # Results log
    results_log = []
    best_auc, best_state = 0.0, None
    q_global = 0.9  # initial conformal quantile
    cumulative_eps = 0.0  # true per-device cumulative ε, max across devices

    print(f"\nStarting HFL-MM-HC training: {args.rounds} global rounds, "
          f"{args.tau_e} edge rounds, {n_devices} devices, {n_edges} edges")
    print(f"DP: ε_total={args.epsilon}, δ={args.delta}, σ={noise_multiplier:.4f}, "
          f"C={args.max_grad_norm}, n_fl_calls={n_fl_calls_total}")

    for global_round in range(1, args.rounds + 1):
        round_start = time.time()
        global_state = {k: v.clone() for k, v in global_model.state_dict().items()}

        edge_states = {e: copy.deepcopy(global_state) for e in range(n_edges)}
        round_eps_spent = []
        round_uplink_bytes = 0   # total compressed bytes uploaded this global round

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
                    local_model, get_device_loaders(dev_id)["train"],
                    device, args.delta,
                    args.max_grad_norm, args.lr,
                    noise_multiplier=noise_multiplier,
                    n_epochs=1,
                    privacy_engine=device_privacy_engines[dev_id],
                    dp_mode=args.dp_mode,
                    group_of=sadp_group_of,
                )
                # epsilon_spent is now this device's TRUE cumulative ε across
                # every local-training call it has made so far this run (the
                # persistent per-device PrivacyEngine composes it), not just
                # this one call.
                round_eps_spent.append(train_result["epsilon_spent"])

                # Compress delta
                delta_params = {
                    n: local_model.state_dict()[n] - edge_states[edge_id][n]
                    for n in global_state
                    if global_state[n].is_floating_point()
                }
                compressed = compressor.compress(delta_params)
                # Measure actual uplink bytes: int32 indices + uint8 values + 8B header per layer
                _uplink_bytes = sum(
                    len(v["indices"]) * 4 + len(v["values_uint8"]) + 8
                    for v in compressed.values()
                )
                round_uplink_bytes += _uplink_bytes
                decompressed = compressor.decompress(compressed, device)

                # Reconstruct full state with compressed delta
                updated_state = copy.deepcopy(edge_states[edge_id])
                for n in decompressed:
                    updated_state[n] = updated_state[n] + decompressed[n]

                edge_client_states[edge_id].append(updated_state)
                edge_client_sizes[edge_id].append(train_result["n_samples"])

                # Conformal calibration
                cal_loader = get_device_loaders(dev_id)["val"]
                cal = LocalConformCalibrator(alpha=args.alpha_conf,
                                            epsilon_conf=0.1)
                q_tilde = cal.calibrate(local_model, cal_loader, device)
                edge_q_tildes[edge_id].append(q_tilde)

                # Free GPU memory — critical: without this, 18 models accumulate per global round
                del local_model
                torch.cuda.empty_cache()

            # Step 2: Edge aggregation
            for edge_id in range(n_edges):
                if edge_client_states[edge_id]:
                    edge_states[edge_id] = edge_fedavg(
                        edge_states[edge_id],
                        edge_client_states[edge_id],
                        edge_client_sizes[edge_id],
                    )

        # Step 3: Cloud aggregation
        edge_sizes = [sum(get_device_loaders(d)["n_train"]
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
        val_metrics = evaluate_model(global_model, get_device_loaders(0)["val"], device)
        # Each device's PrivacyEngine persists across the whole run (see
        # device_privacy_engines above), so round_eps_spent already holds each
        # device's TRUE cumulative ε via Opacus's RDP/PRV composition — not a
        # single-call estimate. The FL-wide privacy guarantee is bounded by the
        # worst-case (highest-ε) device, so we report the max across devices.
        # This value is monotonically non-decreasing round over round because
        # the accountants' history only grows.
        cumulative_eps = max(round_eps_spent) if round_eps_spent else cumulative_eps
        round_time = time.time() - round_start

        log_entry = {
            "global_round": global_round,
            "val_accuracy": round(val_metrics["accuracy"], 4),
            "val_macro_auc": round(val_metrics["macro_auc"], 4),
            "epsilon_spent": round(cumulative_eps, 4),
            "q_global": round(q_global, 4),
            "round_time_s": round(round_time, 2),
            "uplink_bytes": round_uplink_bytes,   # feeds ns3_phase5_integration.py
        }
        results_log.append(log_entry)

        print(f"Round {global_round:3d}/{args.rounds} | "
              f"AUC={val_metrics['macro_auc']:.4f} | "
              f"Acc={val_metrics['accuracy']:.4f} | "
              f"ε={cumulative_eps:.4f} | "
              f"q={q_global:.4f} | "
              f"{round_time:.1f}s")

        if val_metrics["macro_auc"] > best_auc:
            best_auc = val_metrics["macro_auc"]
            best_state = copy.deepcopy(global_model.state_dict())

        if cumulative_eps >= args.epsilon:
            print(f"Privacy budget exhausted at round {global_round}. Stopping.")
            break

    # Final test evaluation
    global_model.load_state_dict(best_state)
    test_metrics = evaluate_model(global_model, get_device_loaders(0)["test"], device)
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
    import json as _json, os as _os
    # Load shared config defaults (overridable by CLI args)
    _cfg_path = _os.path.join(_os.path.dirname(__file__), "..", "config", "hfl_config.json")
    _cfg = {}
    if _os.path.exists(_cfg_path):
        with open(_cfg_path) as _f:
            _raw = _json.load(_f)
        _cfg = {
            "rounds":    _raw.get("federated_learning", {}).get("total_fl_rounds", 20),
            "tau_e":     _raw.get("federated_learning", {}).get("tau_e", 5),
            "epsilon":   _raw.get("privacy", {}).get("epsilon", 1.0),
            "delta":     _raw.get("privacy", {}).get("delta", 1e-5),
            "lr":        _raw.get("federated_learning", {}).get("learning_rate", 1e-3),
            "batch_size":_raw.get("federated_learning", {}).get("batch_size", 32),
        }
        print(f"[Config] Loaded defaults from {_cfg_path}")

    parser = argparse.ArgumentParser(description="HFL-MM-HC Trainer")
    parser.add_argument("--data_dir",       default="data/processed/healthcare")
    parser.add_argument("--partition_dir",  default="data/processed/partitions/healthcare")
    parser.add_argument("--rounds",         type=int,   default=_cfg.get("rounds",     20))
    parser.add_argument("--tau_e",          type=int,   default=_cfg.get("tau_e",      5))
    parser.add_argument("--n_devices",      type=int,   default=6)
    parser.add_argument("--n_edges",        type=int,   default=2)
    parser.add_argument("--n_classes",      type=int,   default=5)
    parser.add_argument("--epsilon",        type=float, default=_cfg.get("epsilon",    1.0))
    parser.add_argument("--delta",          type=float, default=_cfg.get("delta",      1e-5))
    parser.add_argument("--max_grad_norm",  type=float, default=1.0)
    parser.add_argument("--noise_multiplier", type=float, default=None,
                        help="Fixed DP noise multiplier σ (or σ_base under --dp_mode sadp). "
                             "If set, overrides automatic calibration from --epsilon. Use "
                             "when you want direct control over σ (e.g. --noise_multiplier "
                             "1.1 for fast convergence).")
    parser.add_argument("--dp_mode",        choices=["uniform", "sadp"], default="uniform",
                        help="uniform: one clip norm + noise multiplier for the whole model "
                             "(dp_engine.py). sadp: PHANTOM-FL Innovation I2 — per-layer-depth "
                             "clip+noise groups, full noise on the classification head, "
                             "reduced noise on the two feature-extractor encoders "
                             "(sadp_engine.py). See sadp_engine.py module docstring.")
    parser.add_argument("--alpha_conf",     type=float, default=0.1)
    parser.add_argument("--lr",             type=float, default=_cfg.get("lr",         1e-3))
    parser.add_argument("--batch_size",     type=int,   default=_cfg.get("batch_size", 32))
    parser.add_argument("--sparsity",       type=float, default=0.2)
    parser.add_argument("--quant_bits",     type=int,   default=8)
    parser.add_argument("--save_checkpoint", default="checkpoints/best_model_hc.pt")
    parser.add_argument("--output",          default="results/phase5/hfl_mm_hc_results.csv")
    # Engineering / observability flags (do not affect the FL algorithm)
    parser.add_argument("--seed",          type=int, default=42,
                        help="RNG seed for reproducibility")
    parser.add_argument("--deterministic", action="store_true",
                        help="Force deterministic cuDNN/algorithms (slower)")
    parser.add_argument("--no_preflight",  action="store_true",
                        help="Skip pre-run environment/data safety checks")
    parser.add_argument("--no_monitor",    action="store_true",
                        help="Disable the background resource watchdog")
    args = parser.parse_args()

    # ── Engineering wrapper: preflight → metadata → monitored training ──────
    # All defensively imported so a missing engineering package never blocks
    # a training run.
    _monitor_cm = None
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # SIMULATORS/
        from engineering.preflight import run_preflight, format_report
        from engineering.runctx import capture_metadata
        from engineering.sysmon import ResourceMonitor

        if not args.no_preflight:
            _ok, _report = run_preflight(
                args.data_dir, args.partition_dir,
                os.path.dirname(args.save_checkpoint) or "checkpoints",
                os.path.dirname(args.output) or "results",
                n_devices=args.n_devices)
            print(format_report(_report))
            if not _ok:
                print("[Preflight] FAIL — aborting. Re-run with --no_preflight "
                      "to override.")
                sys.exit(2)

        # Unique per-run suffix (timestamp + PID) so two runs writing to the
        # same results/monitoring directory — e.g. one launched while another
        # is still training — never clobber each other's metadata/monitor
        # files. A fixed shared filename here previously let a second run
        # silently overwrite an in-progress run's metadata.
        _run_tag = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_pid{os.getpid()}"

        _meta_path = os.path.join(os.path.dirname(args.output) or ".",
                                  f"run_metadata_{_run_tag}.json")
        capture_metadata(vars(args), seed=args.seed, out_path=_meta_path)
        print(f"[Metadata] Run metadata → {_meta_path}")

        if not args.no_monitor:
            _mon_csv = os.path.join("results", "monitoring",
                                    f"hfl_train_{_run_tag}.csv")
            _monitor_cm = ResourceMonitor(csv_path=_mon_csv, interval_s=10.0)
    except Exception as _e:
        print(f"[Engineering] utilities unavailable ({_e}); running plain.")

    if _monitor_cm is not None:
        with _monitor_cm as _mon:
            train_hfl_mm_hc(args)
        _s = _mon.summary()
        print(f"[Monitor] peak RSS={_s['rss_gb']:.2f} GB | "
              f"peak VRAM={_s['vram_reserved_gb']:.2f} GB | "
              f"min free RAM={_s['min_ram_avail_gb']:.2f} GB")
    else:
        train_hfl_mm_hc(args)
