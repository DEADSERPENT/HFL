"""
DP-SGD Engine — Phase 5
Wraps Opacus PrivacyEngine for differentially private FL training.
All BatchNorm must be replaced with GroupNorm before calling make_private.
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Tuple, Optional, Dict
import warnings

# Opacus's default RDP orders only go up to alpha=63. The RDP→(ε,δ) conversion
# has a floor of ln(1/δ)/(α-1) that noise alone can never push below — with
# δ=1e-5 and α_max=63, that floor is ≈0.19, so any target_epsilon below ~0.2
# makes get_noise_multiplier() raise "privacy budget is too low" even though
# a valid σ exists — it's just outside the searchable order range. Extending
# the orders (more, and higher, alphas) lowers that floor and never makes the
# reported epsilon looser, so use this everywhere epsilon is computed OR
# queried — a mismatch between the alphas used to size σ and the alphas used
# to report ε would make the two inconsistent (e.g. spuriously early budget-
# exceeded stops from an inflated reported ε).
EXTENDED_RDP_ALPHAS = (
    [1 + x / 10.0 for x in range(1, 100)] + list(range(12, 64)) + list(range(64, 1024, 4))
)


def new_device_privacy_engines(n_devices: int) -> Dict[int, "PrivacyEngine"]:
    """
    One PrivacyEngine per FL device, to be reused for every local-training
    call that device makes across the entire training run.

    Opacus's accountant lives on the PrivacyEngine and accumulates step
    history additively across make_private() calls (confirmed against Opacus's
    accountant.step()/history implementation). Creating a fresh engine per
    call — as opposed to per device — silently resets that history, so
    get_epsilon() only ever reflects the single most recent call instead of
    the true cumulative privacy loss for that device.
    """
    from opacus import PrivacyEngine
    # accountant="rdp" explicitly: compute_fl_noise_multiplier sizes σ using the
    # RDP accountant (so it can take the EXTENDED_RDP_ALPHAS override), and
    # Opacus's PrivacyEngine() default ("prv") doesn't accept an alphas
    # argument at all — leaving the default here would size σ against one
    # accounting method while reporting ε against another.
    return {d: PrivacyEngine(accountant="rdp") for d in range(n_devices)}


def compute_fl_noise_multiplier(
        target_epsilon: float,
        target_delta: float,
        n_fl_calls: int,
        n_samples: int,
        batch_size: int,
        local_epochs: int = 1) -> float:
    """
    Compute the noise multiplier σ needed to achieve (ε, δ)-DP over the
    entire FL training run, using Opacus's RDP accountant.

    n_fl_calls = global_rounds × edge_rounds  (total local training calls per device)
    """
    try:
        from opacus.accountants.utils import get_noise_multiplier
    except ImportError:
        raise ImportError("Opacus not installed. Run: pip install opacus")

    steps_per_call = max(n_samples // batch_size, 1)
    total_steps = n_fl_calls * local_epochs * steps_per_call
    sample_rate = min(batch_size / max(n_samples, 1), 1.0)
    sigma = get_noise_multiplier(
        target_epsilon=target_epsilon,
        target_delta=target_delta,
        sample_rate=sample_rate,
        steps=total_steps,
        alphas=EXTENDED_RDP_ALPHAS,
    )
    print(f"[DP-Engine] FL budget: ε={target_epsilon}, δ={target_delta}, "
          f"n_fl_calls={n_fl_calls}, total_steps={total_steps}, "
          f"sample_rate={sample_rate:.4f} → σ={sigma:.4f}")
    return sigma


def make_dp_model(model: nn.Module, optimizer: torch.optim.Optimizer,
                  data_loader: DataLoader,
                  noise_multiplier: Optional[float] = None,
                  target_epsilon: float = 1.0,
                  target_delta: float = 1e-5,
                  max_grad_norm: float = 1.0,
                  epochs: int = 1,
                  privacy_engine=None) -> Tuple:
    """
    Wrap model and optimizer with Opacus PrivacyEngine.

    Preferred: pass noise_multiplier (pre-computed via compute_fl_noise_multiplier)
    so that the same σ is reused across all FL rounds for correct privacy accounting.

    Fallback: pass target_epsilon (uses make_private_with_epsilon, correct only for
    single-run training — NOT for FL where this is called once per round).

    privacy_engine: reuse an existing PrivacyEngine (e.g. one persistent engine
    per FL device) so Opacus's accountant composes ε across every call made
    with it, instead of starting a fresh (single-call) accountant each time.
    Pass None only for genuinely one-shot (non-FL) training.

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

    if privacy_engine is None:
        privacy_engine = PrivacyEngine(accountant="rdp")

    if noise_multiplier is not None:
        # Fixed σ path: correct for FL (same σ reused every round)
        dp_model, dp_optimizer, dp_loader = privacy_engine.make_private(
            module=model,
            optimizer=optimizer,
            data_loader=data_loader,
            noise_multiplier=noise_multiplier,
            max_grad_norm=max_grad_norm,
        )
        print(f"[DP-Engine] fixed σ={noise_multiplier:.4f}, C={max_grad_norm}")
    else:
        # Per-call target_epsilon path (only valid for single-run, not FL)
        dp_model, dp_optimizer, dp_loader = privacy_engine.make_private_with_epsilon(
            module=model,
            optimizer=optimizer,
            data_loader=data_loader,
            target_epsilon=target_epsilon,
            target_delta=target_delta,
            max_grad_norm=max_grad_norm,
            epochs=epochs,
        )
        sigma = dp_optimizer.noise_multiplier
        print(f"[DP-Engine] ε={target_epsilon}, δ={target_delta}, "
              f"σ={sigma:.4f}, C={max_grad_norm}")

    return dp_model, dp_optimizer, dp_loader, privacy_engine


def get_epsilon_spent(privacy_engine, delta: float = 1e-5) -> float:
    """
    Query current ε spent from the privacy accountant.

    Goes through privacy_engine.accountant directly (rather than
    PrivacyEngine.get_epsilon(), which doesn't forward an alphas argument) so
    the same EXTENDED_RDP_ALPHAS used to size σ in compute_fl_noise_multiplier
    is also used here — see the comment on EXTENDED_RDP_ALPHAS above.
    """
    return privacy_engine.accountant.get_epsilon(delta=delta, alphas=EXTENDED_RDP_ALPHAS)


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


def compute_fl_noise_multiplier_multidevice(
        target_epsilon: float, target_delta: float, n_fl_calls: int,
        device_n_train, batch_size: int, local_epochs: int = 1,
        tol: float = 1e-3, max_iter: int = 60) -> float:
    """Sigma such that NO device exceeds the budget.

    Two defects this replaces, both of which silently breached the guarantee:

    1. FLOOR vs CEIL. steps_per_call was n // batch_size, but a DataLoader
       yields ceil(n / batch_size) batches. One uncounted step per call is
       enough to push a nominally-1.0 budget to 1.01.

    2. ONE DEVICE STOOD IN FOR ALL. Sigma was calibrated from the SMALLEST
       device only. But each client has its own sampling rate q_d = B/n_d AND
       its own step count, and the reported epsilon is the MAXIMUM across
       clients. Small clients have large q (few steps, high rate); large
       clients have many steps at low rate. Neither dominates universally, so
       calibrating on either one alone can under-provision the other.

    Here epsilon is evaluated for EVERY device and sigma is bisected until the
    worst client fits. Monotonic in sigma, so bisection is exact to `tol`.
    """
    import math
    from opacus.accountants import RDPAccountant

    cfgs = []
    for n in device_n_train:
        n = max(int(n), 1)
        q = min(batch_size / n, 1.0)
        steps = math.ceil(n / batch_size) * local_epochs * n_fl_calls
        cfgs.append((q, steps))

    def worst_eps(sigma: float) -> float:
        worst = 0.0
        for q, steps in cfgs:
            acct = RDPAccountant()
            acct.history = [(sigma, q, steps)]      # composed in one entry
            try:
                worst = max(worst, acct.get_epsilon(delta=target_delta))
            except Exception:
                return float("inf")
        return worst

    lo, hi = 0.3, 2.0
    while worst_eps(hi) > target_epsilon and hi < 1024:
        hi *= 2.0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        if worst_eps(mid) > target_epsilon:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    sigma = hi
    print(f"[DP-Engine] multi-device calibration: {len(cfgs)} clients, "
          f"eps<={target_epsilon}, delta={target_delta} -> sigma={sigma:.4f} "
          f"(worst-client eps={worst_eps(sigma):.4f})")
    return sigma
