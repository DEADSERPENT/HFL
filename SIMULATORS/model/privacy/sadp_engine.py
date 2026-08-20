"""
SADP — Sensitivity-Adaptive Differential Privacy (PHANTOM-FL Innovation I2).

Trainable parameters are split into 3 depth groups by module semantics
(HFLMMHC: encoder_a -> encoder_b -> fusion, see assign_depth_groups). Each
group gets its own clip norm and its own noise multiplier, sized from its
own slice of the (epsilon, delta) privacy budget rather than one shared
noise level for the whole model.

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
   epsilons) — basic composition, valid but loose. An EARLIER version of
   this module instead fixed per-group NOISE-MULTIPLIER ratios (e.g.
   group σ_l = σ_base * ratio_l for ratios (0.3, 0.7, 1.0)) and summed
   the per-group RDP curves to solve for one shared σ_base. That is
   tighter on paper, but empirically inflated σ_base by ~sqrt(Σ 1/ratio_l²)
   (≈3.76x for those ratios) relative to naive single-mechanism DP-SGD,
   because splitting one mechanism into N independently-composed ones is
   itself privacy-expensive — see git history / project memory
   "phase5_dp_collapse" update 2026-07-23 for the empirical trace (σ_base
   came out 42.5 vs. a naive 11.33, and because the classifier head's
   ratio was 1.0 it absorbed that entire inflation, collapsing the model
   to near-random accuracy).

   This version instead allocates each group its OWN (epsilon_l, delta_l)
   slice of the total budget up front (basic composition: Total ε = Σ ε_l,
   Total δ = Σ δ_l — see EPSILON_GROUP_FRACTIONS) and sizes each group's σ_l
   independently via the same single-mechanism RDP search
   dp_engine.compute_fl_noise_multiplier uses. This is looser per-bit than
   summing RDP curves across groups, but no group's σ pays a tax for the
   OTHER groups' composition — each group's own σ is exactly what a plain
   (non-SADP) DP-SGD run would need for THAT group's own (epsilon_l,
   delta_l), so a group given a generous epsilon_l fraction is guaranteed
   to end up no noisier than naive DP-SGD at that fraction, which the old
   ratio-based scheme could not guarantee for any group.
"""

from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn

from opacus.accountants.analysis.rdp import compute_rdp, get_privacy_spent
from opacus.accountants.utils import get_noise_multiplier
from opacus.grad_sample import GradSampleModule

from dp_engine import EXTENDED_RDP_ALPHAS

# Per-group epsilon-budget split (encoder, fusion, head — matches
# assign_depth_groups' group indices 0/1/2). The classifier head gets the
# LARGEST slice (loosest privacy / least noise): it has the fewest
# parameters and the most direct effect on utility (maps straight to class
# logits), so it tolerates noise worst — this is the group that collapsed
# the model under the old ratio-based scheme. The encoders get the
# SMALLEST slice (tightest privacy / most noise): they hold >90% of all
# trainable parameters, so a given epsilon buys much less noise reduction
# per parameter there, and they're the layers most existing DP-SGD schemes
# (including this project's own non-SADP baseline) already protect with
# uniform full-strength noise.
EPSILON_GROUP_FRACTIONS: Tuple[float, ...] = (0.15, 0.25, 0.60)
N_GROUPS = len(EPSILON_GROUP_FRACTIONS)


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


def compute_sadp_group_sigmas(target_epsilon: float, target_delta: float,
                               n_fl_calls: int, n_samples: int,
                               batch_size: int, local_epochs: int = 1,
                               epsilon_fractions: Tuple[float, ...] = EPSILON_GROUP_FRACTIONS
                               ) -> Tuple[List[float], List[float]]:
    """
    Size each depth group's own noise multiplier INDEPENDENTLY by splitting
    the (epsilon, delta) budget across groups (basic composition) instead of
    fixing noise-multiplier ratios and solving for one shared sigma_base
    (see module docstring for why the ratio scheme inflates noise).

    delta is split evenly across the N groups (so Σ delta_l == target_delta
    exactly); epsilon is split per epsilon_fractions (so Σ eps_l ==
    target_epsilon exactly, since the fractions sum to 1). Each group's
    sigma_l is then the single-mechanism sigma opacus.get_noise_multiplier
    would compute for THAT group's own (eps_l, delta_l) alone — identical
    to dp_engine.compute_fl_noise_multiplier, just called once per group.

    Returns (sigmas, deltas), both length N_GROUPS and index-aligned with
    epsilon_fractions — callers must keep `deltas` around (e.g. in
    SADPPrivacyTracker) to report cumulative epsilon consistently with how
    sigma was sized.
    """
    steps_per_call = max(n_samples // batch_size, 1)
    total_steps = n_fl_calls * local_epochs * steps_per_call
    sample_rate = min(batch_size / max(n_samples, 1), 1.0)

    n = len(epsilon_fractions)
    deltas = [target_delta / n] * n
    sigmas = []
    for frac, delta_l in zip(epsilon_fractions, deltas):
        eps_l = target_epsilon * frac
        sigma_l = get_noise_multiplier(
            target_epsilon=eps_l,
            target_delta=delta_l,
            sample_rate=sample_rate,
            steps=total_steps,
            alphas=EXTENDED_RDP_ALPHAS,
        )
        sigmas.append(sigma_l)

    print(f"[SADP-Engine] FL budget: ε={target_epsilon}, δ={target_delta}, "
          f"n_fl_calls={n_fl_calls}, total_steps={total_steps}, "
          f"sample_rate={sample_rate:.4f} → per-group ε="
          f"{[round(target_epsilon * f, 4) for f in epsilon_fractions]}, "
          f"δ={[round(d, 8) for d in deltas]}, σ={[round(s, 4) for s in sigmas]}")
    return sigmas, deltas


class SADPPrivacyTracker:
    """
    Per-device cumulative privacy tracker for SADP, analogous to reusing one
    Opacus PrivacyEngine per device (dp_engine.new_device_privacy_engines):
    accumulates (group_sigmas, sample_rate, steps) history across every call
    this device makes over the FL run, so get_epsilon() reports the TRUE
    cumulative ε — per group, RDP-composed across every call this device has
    made, then combined ACROSS groups via basic composition (Σ eps_l against
    each group's own delta_l — see compute_sadp_group_sigmas), not just the
    most recent call.

    deltas must be the SAME per-group delta split the group sigmas were
    originally sized against (compute_sadp_group_sigmas' second return
    value) — mixing a tracker's deltas with sigmas sized for a different
    split under-reports the true cumulative ε.
    """

    def __init__(self, deltas: Tuple[float, ...]):
        self.deltas = tuple(deltas)
        self.history: List[Tuple[List[float], float, int]] = []  # (group_sigmas, sample_rate, steps)

    def record(self, group_sigmas: List[float], sample_rate: float, steps: int):
        self.history.append((list(group_sigmas), sample_rate, steps))

    def get_epsilon(self, delta: Optional[float] = None) -> float:
        """
        `delta` is accepted (unused) only so call sites mirroring Opacus's
        PrivacyEngine.get_epsilon(delta) API don't need a special case for
        SADP — the per-group deltas fixed at construction already sum to
        the delta the group sigmas were actually sized for.
        """
        if not self.history:
            return 0.0
        total_eps = 0.0
        for g, delta_l in enumerate(self.deltas):
            group_rdp = None
            for group_sigmas, sample_rate, steps in self.history:
                rdp = compute_rdp(q=sample_rate, noise_multiplier=group_sigmas[g],
                                   steps=steps, orders=EXTENDED_RDP_ALPHAS)
                group_rdp = rdp if group_rdp is None else [a + b for a, b in zip(group_rdp, rdp)]
            eps_g, _ = get_privacy_spent(orders=EXTENDED_RDP_ALPHAS, rdp=group_rdp, delta=delta_l)
            total_eps += eps_g
        return total_eps


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
                 group_of: Dict[str, int], group_sigmas: List[float],
                 max_grad_norm: float = 1.0,
                 expected_batch_size: Optional[int] = None):
        self.gs_model = gs_model
        self.optimizer = optimizer
        self.group_sigmas = group_sigmas
        self.expected_batch_size = expected_batch_size
        # Split max_grad_norm across groups so the combined per-sample
        # sensitivity (sqrt(sum C_l^2)) matches max_grad_norm — same overall
        # clipping strictness as the uniform baseline, just reallocating how
        # much NOISE each group's own clip budget gets.
        n_groups = len(group_sigmas)
        self.clip_norms = {i: max_grad_norm / (n_groups ** 0.5) for i in range(n_groups)}
        self.sigmas = {i: s for i, s in enumerate(group_sigmas)}

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
        for group_idx in range(len(self.group_sigmas)):
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
                    group_sigmas: List[float], max_grad_norm: float = 1.0,
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
    sadp_opt = SADPOptimizer(gs_model, optimizer, group_of, group_sigmas,
                             max_grad_norm=max_grad_norm)
    return gs_model, sadp_opt
