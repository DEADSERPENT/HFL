"""
SADP — Sensitivity-Adaptive Differential Privacy (PHANTOM-FL Innovation I2).

Fixed per-layer-depth noise allocation: trainable parameters are split into
3 depth groups by their position in named_parameters() order (which matches
forward-pass depth for HFLMMHC: encoder_a -> encoder_b -> fusion, since
__init__ registers submodules in that order and forward() calls them in the
same order). Each group gets its own clip norm and its own noise multiplier,
so classifier-head parameters (highest sensitivity — map straight to labels)
get full noise while early feature-extractor parameters get a fraction of it.
The ratios are a fixed rule, not measured from live per-round gradients, so
determining them costs no privacy budget.

This corrects two problems in the original PHANTOM-FL sketch
(OVERALL PROJECT OUTPUT/01_PHANTOM_FL_Novel_Model.txt, Section 3.3):

1. That sketch adds noise directly to param.grad *after* Opacus's own
   DPOptimizer has already clipped the FULL per-sample gradient to one
   GLOBAL norm across every parameter combined — Opacus has no per-layer
   clip hook, so scaling noise per layer downstream of a global clip does
   not give each layer its own bounded sensitivity, which is what the DP
   guarantee actually rests on. Here each group is clipped independently
   (its own grad_sample norm, its own C_l), which does give each group a
   well-defined sensitivity C_l — this module bypasses Opacus's
   DPOptimizer.clip_and_accumulate entirely and does the per-group
   clip+noise directly against GradSampleModule's raw p.grad_sample.

2. That sketch composes privacy as "Total ε = Σ_l ε_l" (sum plain
   epsilons). Valid (basic composition) but looser than necessary. Since
   clip-to-C_l then noise sigma_l*C_l makes each group's release its own
   sampled-Gaussian mechanism depending only on sigma_l and the sample
   rate (the clip norm C_l cancels out of the RDP formula — sensitivity
   and noise-std scale together), the per-group RDP curves can be SUMMED
   at each order (Mironov 2017's RDP composition theorem applies to any
   sequence of mechanisms over the same data, including releasing them
   "simultaneously" as one vector — that's a restricted case of adaptive
   composition, still covered by the theorem) and converted to (eps,
   delta) ONCE at the end — see compute_sadp_noise_multiplier() and
   SADPPrivacyTracker below. This is both correct and tighter than the
   sum-of-epsilons approach.
"""

from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn

from opacus.accountants.analysis.rdp import compute_rdp, get_privacy_spent
from opacus.grad_sample import GradSampleModule

from dp_engine import EXTENDED_RDP_ALPHAS

# Fixed depth-group noise ratios (PHANTOM-FL Sec 3.3 examples): early
# feature-extractor layers get 30% of the base noise, mid layers 70%, the
# classifier head gets 100%.
DEPTH_GROUP_RATIOS: Tuple[float, ...] = (0.3, 0.7, 1.0)
N_GROUPS = len(DEPTH_GROUP_RATIOS)


def assign_depth_groups(model: nn.Module) -> Dict[str, int]:
    """
    Bucket every trainable parameter's NAME (as returned by the model's own,
    unwrapped named_parameters()) into one of 3 groups by module semantics —
    NOT by position/count. HFLMMHC's two encoders (encoder_a: FedMamba-HC,
    encoder_b: MobileNetV3) are ~93% of all trainable parameter tensors
    (139/149) but are feature extractors (lowest sensitivity, group 0); the
    fusion head is only 10 tensors, of which just the FINAL Linear (the one
    that maps straight to class logits) is the actual classification head
    (group 2) — an equal-thirds-by-count split would put most of encoder_b
    into the "head" group, which is backwards. Frozen parameters
    (requires_grad=False — e.g. MobileNet's frozen early blocks) are
    skipped: they never get a grad_sample.
    """
    names = [n for n, p in model.named_parameters() if p.requires_grad]
    fusion_layer_indices = sorted({
        int(n.split(".")[2]) for n in names
        if n.startswith("fusion.") and n.split(".")[2].isdigit()
    })
    head_layer_idx = fusion_layer_indices[-1] if fusion_layer_indices else None

    group_of = {}
    for name in names:
        if name.startswith("encoder_"):
            group_of[name] = 0  # feature extractors — lowest sensitivity
        elif name.startswith("fusion."):
            idx = int(name.split(".")[2])
            group_of[name] = 2 if idx == head_layer_idx else 1
        else:
            group_of[name] = 1  # unrecognized top-level module — default moderate
    return group_of


def _flat_grad_sample(p: torch.Tensor) -> torch.Tensor:
    """Concatenate p.grad_sample into one [batch, *param.shape] tensor (it's
    a list instead of a tensor once a param has been used across >1 backward
    call without clearing — see SADPOptimizer.zero_grad)."""
    gs = p.grad_sample
    if isinstance(gs, torch.Tensor):
        return gs
    return torch.cat(gs, dim=0)


def compute_sadp_noise_multiplier(target_epsilon: float, target_delta: float,
                                   n_fl_calls: int, n_samples: int,
                                   batch_size: int, local_epochs: int = 1,
                                   ratios: Tuple[float, ...] = DEPTH_GROUP_RATIOS,
                                   tolerance: float = 0.01) -> float:
    """
    Binary-search sigma_base such that summing the per-depth-group RDP
    curves (each group's own sigma_l = sigma_base * ratios[l], same
    sample_rate/steps as dp_engine.compute_fl_noise_multiplier) and
    converting once at the end hits target_epsilon.

    Mirrors opacus.accountants.utils.get_noise_multiplier's own binary
    search, but for a multi-noise-level combined mechanism that Opacus's
    accountant can't express directly (it hardcodes one noise_multiplier
    for the whole model).
    """
    steps_per_call = max(n_samples // batch_size, 1)
    total_steps = n_fl_calls * local_epochs * steps_per_call
    sample_rate = min(batch_size / max(n_samples, 1), 1.0)

    def combined_epsilon(sigma_base: float) -> float:
        total_rdp = None
        for ratio in ratios:
            rdp = compute_rdp(q=sample_rate, noise_multiplier=sigma_base * ratio,
                               steps=total_steps, orders=EXTENDED_RDP_ALPHAS)
            total_rdp = rdp if total_rdp is None else [a + b for a, b in zip(total_rdp, rdp)]
        eps, _ = get_privacy_spent(orders=EXTENDED_RDP_ALPHAS, rdp=total_rdp,
                                   delta=target_delta)
        return eps

    sigma_low, sigma_high = 0.0, 10.0
    eps_high = float("inf")
    while eps_high > target_epsilon:
        sigma_high *= 2
        eps_high = combined_epsilon(sigma_high)
        if sigma_high > 1e6:
            raise ValueError("SADP: privacy budget too low even at maximum searched sigma_base.")

    while target_epsilon - eps_high > tolerance:
        sigma_mid = (sigma_low + sigma_high) / 2
        eps_mid = combined_epsilon(sigma_mid)
        if eps_mid < target_epsilon:
            sigma_high, eps_high = sigma_mid, eps_mid
        else:
            sigma_low = sigma_mid

    group_sigmas = [round(sigma_high * r, 4) for r in ratios]
    print(f"[SADP-Engine] FL budget: ε={target_epsilon}, δ={target_delta}, "
          f"n_fl_calls={n_fl_calls}, total_steps={total_steps}, "
          f"sample_rate={sample_rate:.4f} → σ_base={sigma_high:.4f} "
          f"(group σ={group_sigmas})")
    return sigma_high


class SADPPrivacyTracker:
    """
    Per-device cumulative privacy tracker for SADP, analogous to reusing one
    Opacus PrivacyEngine per device (dp_engine.new_device_privacy_engines):
    accumulates (sigma_base, sample_rate, steps) history across every call
    this device makes over the FL run, so get_epsilon() reports the TRUE
    cumulative ε (summed RDP across every call AND every depth group),
    not just the most recent call.
    """

    def __init__(self, ratios: Tuple[float, ...] = DEPTH_GROUP_RATIOS):
        self.ratios = ratios
        self.history: List[Tuple[float, float, int]] = []  # (sigma_base, sample_rate, steps)

    def record(self, sigma_base: float, sample_rate: float, steps: int):
        self.history.append((sigma_base, sample_rate, steps))

    def get_epsilon(self, delta: float) -> float:
        if not self.history:
            return 0.0
        total_rdp = None
        for sigma_base, sample_rate, steps in self.history:
            for ratio in self.ratios:
                rdp = compute_rdp(q=sample_rate, noise_multiplier=sigma_base * ratio,
                                   steps=steps, orders=EXTENDED_RDP_ALPHAS)
                total_rdp = rdp if total_rdp is None else [a + b for a, b in zip(total_rdp, rdp)]
        eps, _ = get_privacy_spent(orders=EXTENDED_RDP_ALPHAS, rdp=total_rdp, delta=delta)
        return eps


class SADPOptimizer:
    """
    Drop-in replacement for Opacus's DPOptimizer that clips and noises each
    depth group independently instead of clipping the whole model as one
    global-norm vector. Wraps a GradSampleModule's parameters + a plain
    torch optimizer (constructed on the SAME parameters).

    Usage mirrors Opacus: zero_grad() -> forward/backward (populates
    p.grad_sample via GradSampleModule) -> step().
    """

    def __init__(self, gs_model: GradSampleModule, optimizer: torch.optim.Optimizer,
                 group_of: Dict[str, int], sigma_base: float,
                 max_grad_norm: float = 1.0,
                 ratios: Tuple[float, ...] = DEPTH_GROUP_RATIOS,
                 expected_batch_size: Optional[int] = None):
        self.gs_model = gs_model
        self.optimizer = optimizer
        self.ratios = ratios
        self.sigma_base = sigma_base
        self.expected_batch_size = expected_batch_size
        # Split max_grad_norm across groups so the combined per-sample
        # sensitivity (sqrt(sum C_l^2)) matches max_grad_norm — same overall
        # clipping strictness as the uniform baseline, just reallocating how
        # much NOISE each group's own clip budget gets.
        self.clip_norms = {i: max_grad_norm / (len(ratios) ** 0.5) for i in range(len(ratios))}
        self.sigmas = {i: sigma_base * r for i, r in enumerate(ratios)}

        # named_parameters() on GradSampleModule are prefixed "_module." —
        # strip that to match assign_depth_groups(), which is computed
        # against the ORIGINAL (unwrapped) module.
        self.named_params = [(n.replace("_module.", "", 1), p)
                              for n, p in gs_model.named_parameters() if p.requires_grad]
        self.group_of = group_of

    def zero_grad(self, set_to_none: bool = True):
        for _, p in self.named_params:
            p.grad_sample = None
            p.summed_grad = None
        self.optimizer.zero_grad(set_to_none)

    def step(self):
        batch_size = None
        for group_idx in range(len(self.ratios)):
            group_params = [(n, p) for n, p in self.named_params if self.group_of.get(n) == group_idx]
            if not group_params:
                continue
            grad_samples = [_flat_grad_sample(p) for _, p in group_params]
            batch_size = grad_samples[0].shape[0]
            per_param_norms = [g.reshape(batch_size, -1).norm(2, dim=-1) for g in grad_samples]
            per_sample_norms = torch.stack(per_param_norms, dim=1).norm(2, dim=1)
            clip_factor = (self.clip_norms[group_idx] / (per_sample_norms + 1e-6)).clamp(max=1.0)

            for (_, p), grad_sample in zip(group_params, grad_samples):
                summed = torch.einsum("i,i...", clip_factor, grad_sample)
                noise = torch.normal(
                    mean=0.0, std=self.sigmas[group_idx] * self.clip_norms[group_idx],
                    size=summed.shape, device=summed.device,
                )
                p.grad = (summed + noise).view_as(p)

        expected_batch_size = self.expected_batch_size or batch_size
        for _, p in self.named_params:
            p.grad /= expected_batch_size

        self.optimizer.step()


def make_sadp_model(model: nn.Module, optimizer: torch.optim.Optimizer,
                    sigma_base: float, max_grad_norm: float = 1.0,
                    group_of: Optional[Dict[str, int]] = None):
    """
    Wrap model + optimizer for SADP training. Returns (gs_model, sadp_optimizer).

    model must already have BatchNorm replaced with GroupNorm and inplace ops
    made out-of-place (same Opacus requirements as dp_engine.make_dp_model —
    GradSampleModule needs per-sample hooks, same as Opacus's own wrapping).
    """
    if group_of is None:
        group_of = assign_depth_groups(model)
    gs_model = GradSampleModule(model)
    sadp_opt = SADPOptimizer(gs_model, optimizer, group_of, sigma_base,
                             max_grad_norm=max_grad_norm)
    return gs_model, sadp_opt
