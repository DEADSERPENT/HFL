"""
DP-SGD Engine — Phase 5
Wraps Opacus PrivacyEngine for differentially private FL training.
All BatchNorm must be replaced with GroupNorm before calling make_private.
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Tuple, Optional
import warnings


def make_dp_model(model: nn.Module, optimizer: torch.optim.Optimizer,
                  data_loader: DataLoader,
                  target_epsilon: float = 1.0,
                  target_delta: float = 1e-5,
                  max_grad_norm: float = 1.0,
                  epochs: int = 1) -> Tuple:
    """
    Wrap model and optimizer with Opacus PrivacyEngine.

    Returns: (dp_model, dp_optimizer, dp_loader, privacy_engine)

    IMPORTANT: model must have NO BatchNorm layers.
    Call replace_bn_with_gn(model) before this function.
    """
    try:
        from opacus import PrivacyEngine
        from opacus.validators import ModuleValidator
    except ImportError:
        raise ImportError(
            "Opacus not installed. Run: pip install opacus"
        )

    # Validate model for Opacus compatibility
    errors = ModuleValidator.validate(model, strict=False)
    if errors:
        raise ValueError(
            f"Model has Opacus-incompatible layers:\n" +
            "\n".join(str(e) for e in errors) +
            "\nCall replace_bn_with_gn(model) before make_dp_model()."
        )

    privacy_engine = PrivacyEngine()
    dp_model, dp_optimizer, dp_loader = privacy_engine.make_private_with_epsilon(
        module=model,
        optimizer=optimizer,
        data_loader=data_loader,
        target_epsilon=target_epsilon,
        target_delta=target_delta,
        max_grad_norm=max_grad_norm,
        epochs=epochs,
    )

    # Log computed noise multiplier
    sigma = dp_optimizer.noise_multiplier
    print(f"[DP-Engine] ε={target_epsilon}, δ={target_delta}, "
          f"σ={sigma:.4f}, C={max_grad_norm}")

    return dp_model, dp_optimizer, dp_loader, privacy_engine


def get_epsilon_spent(privacy_engine, delta: float = 1e-5) -> float:
    """Query current ε spent from the privacy accountant."""
    return privacy_engine.get_epsilon(delta=delta)


def train_one_round_dp(model: nn.Module,
                       dp_optimizer,
                       dp_loader: DataLoader,
                       device: torch.device,
                       privacy_engine,
                       loss_fn=None,
                       n_epochs: int = 1,
                       target_epsilon: Optional[float] = None,
                       target_delta: float = 1e-5) -> dict:
    """
    Train model for n_epochs with DP-SGD.
    Stops early if epsilon budget is exceeded.

    Returns: dict with keys: loss, accuracy, epsilon_spent
    """
    if loss_fn is None:
        loss_fn = nn.CrossEntropyLoss()

    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for epoch in range(n_epochs):
        for batch in dp_loader:
            ecg, cxr, labels = batch
            ecg    = ecg.to(device, non_blocking=True)
            cxr    = cxr.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            dp_optimizer.zero_grad()
            logits = model(ecg, cxr)
            loss = loss_fn(logits, labels)
            loss.backward()
            dp_optimizer.step()

            total_loss += loss.item() * len(labels)
            correct += (logits.argmax(1) == labels).sum().item()
            total += len(labels)

        # Early stopping on privacy budget
        if target_epsilon is not None:
            eps_spent = get_epsilon_spent(privacy_engine, target_delta)
            if eps_spent > target_epsilon:
                print(f"[DP-Engine] Budget exceeded: ε_spent={eps_spent:.4f} "
                      f"> ε_target={target_epsilon}. Stopping.")
                break

    eps_spent = get_epsilon_spent(privacy_engine, target_delta)

    return {
        "loss": total_loss / max(total, 1),
        "accuracy": correct / max(total, 1),
        "epsilon_spent": eps_spent,
        "n_samples_trained": total,
    }


class PrivacyAccountant:
    """Tracks cumulative privacy cost across FL rounds."""

    def __init__(self, target_epsilon: float = 1.0,
                 target_delta: float = 1e-5):
        self.target_epsilon = target_epsilon
        self.target_delta = target_delta
        self.history = []

    def log_round(self, round_id: int, epsilon_spent: float):
        self.history.append({"round": round_id, "epsilon": epsilon_spent})

    def budget_remaining(self, current_epsilon: float) -> float:
        return self.target_epsilon - current_epsilon

    def is_exhausted(self, current_epsilon: float,
                     tolerance: float = 0.0) -> bool:
        return current_epsilon >= (self.target_epsilon - tolerance)

    def report(self) -> dict:
        if not self.history:
            return {}
        last_eps = self.history[-1]["epsilon"]
        return {
            "rounds_completed": len(self.history),
            "epsilon_final": last_eps,
            "epsilon_target": self.target_epsilon,
            "delta": self.target_delta,
            "budget_remaining": self.budget_remaining(last_eps),
            "budget_exhausted": self.is_exhausted(last_eps),
        }
