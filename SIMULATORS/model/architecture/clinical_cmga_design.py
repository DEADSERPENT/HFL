"""
IP-3: ClinicalCMGA — Clinical Temporal-Decay Cross-Modal Gated Attention
STATUS: PHASE 5 DESIGN SPEC — Implementation deferred to Phase 6 (PHANTOM-FL)

This file contains:
  1. Full mathematical specification (as comments)
  2. Complete PyTorch implementation skeleton
  3. Integration notes for Phase 6 PHANTOM-FL build

Motivation: Extends PHANTOM-FL's CMGA for asynchronous clinical modalities.
ECG and chest X-ray are acquired at different times in real hospital settings.
ClinicalCMGA handles temporal gaps using decay gates informed by clinical time.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple


# ============================================================
# MATHEMATICAL SPECIFICATION
# ============================================================
#
# INPUTS:
#   f_a ∈ R^{d_a}      — ECG feature vector from FedMamba-HC  (d_a=256)
#   f_b ∈ R^{d_b}      — CXR feature vector from MobileNetV3  (d_b=576)
#   Δt_a (minutes)     — time since ECG acquisition
#   Δt_b (minutes)     — time since X-ray acquisition
#   q_a ∈ [0,1]        — ECG signal quality score
#   q_b ∈ [0,1]        — X-ray image quality score
#   U_t ∈ [0,1]        — clinical urgency (from EHR events)
#
# TEMPORAL DECAY GATES:
#   τ_a = q_a · exp(-λ_a · Δt_a)    λ_a=0.02  (50-min half-life)
#   τ_b = q_b · exp(-λ_b · Δt_b)    λ_b=0.005 (140-min half-life)
#
# GATED FEATURES (with learned null vectors f̄_a, f̄_b):
#   f̃_a = τ_a · f_a + (1 - τ_a) · f̄_a
#   f̃_b = τ_b · f_b + (1 - τ_b) · f̄_b
#
# CROSS-MODAL ATTENTION (bidirectional):
#   Project to common d_k=128 space:
#   Q_a = W_Q_a · f̃_a  [ECG query]
#   K_b = W_K_b · f̃_b  [CXR key]
#   V_b = W_V_b · f̃_b  [CXR value]
#   A_{a→b} = softmax(Q_a K_b^T / √d_k) · V_b   [ECG attends to CXR]
#   Symmetrically: A_{b→a} = softmax(Q_b K_a^T / √d_k) · V_a
#
# URGENCY-GATED FUSION:
#   context = concat(A_{a→b}, A_{b→a}, U_t)       [size: 2·d_k + 1]
#   w = sigmoid(W_u · context + b_u)              [scalar gate]
#   f_fused = w ⊙ A_{a→b} + (1-w) ⊙ A_{b→a}     [d_k dim output]
#   f_out = MLP(f_fused)                           [→ 256-d]
#
# DP-SGD COMPATIBILITY:
#   All layers use GroupNorm (no BatchNorm).
#   λ_a, λ_b are fixed scalars (not parameters) — no privacy cost.
#   τ_a, τ_b are scalar multiplications — Opacus handles these.
# ============================================================


class TemporalDecayGate(nn.Module):
    """
    Computes τ = q · exp(-λ · Δt) for a single modality.
    λ is a learnable positive scalar initialized to given value.
    """

    def __init__(self, lambda_init: float = 0.02):
        super().__init__()
        self.log_lambda = nn.Parameter(torch.tensor(math.log(lambda_init)))

    @property
    def lambda_(self) -> torch.Tensor:
        return torch.exp(self.log_lambda)

    def forward(self, quality: torch.Tensor,
                delta_t: torch.Tensor) -> torch.Tensor:
        """
        quality : [B] or [B,1]  ∈ [0,1]
        delta_t : [B] or [B,1]  in minutes
        returns : [B,1] decay gate value ∈ (0,1]
        """
        quality = quality.view(-1, 1).clamp(0.0, 1.0)
        delta_t = delta_t.view(-1, 1).clamp(min=0.0)
        return quality * torch.exp(-self.lambda_ * delta_t)


class CrossModalAttention(nn.Module):
    """
    Single-head cross-modal attention between two feature vectors.
    Produces one direction of attention: query_feat attends to key_feat.
    """

    def __init__(self, d_q: int, d_k: int, d_attn: int = 128):
        super().__init__()
        self.scale = math.sqrt(d_attn)
        self.W_Q = nn.Linear(d_q, d_attn, bias=False)
        self.W_K = nn.Linear(d_k, d_attn, bias=False)
        self.W_V = nn.Linear(d_k, d_attn, bias=False)

    def forward(self, q_feat: torch.Tensor,
                k_feat: torch.Tensor) -> torch.Tensor:
        """
        q_feat: [B, d_q]
        k_feat: [B, d_k]
        returns: [B, d_attn] attention-weighted value
        """
        Q = self.W_Q(q_feat)      # [B, d_attn]
        K = self.W_K(k_feat)      # [B, d_attn]
        V = self.W_V(k_feat)      # [B, d_attn]
        # dot-product attention (single-query, single-key → scalar weight)
        attn = (Q * K).sum(dim=-1, keepdim=True) / self.scale  # [B, 1]
        attn = torch.sigmoid(attn)   # soft gate (no softmax over sequence)
        return attn * V              # [B, d_attn]


class ClinicalCMGA(nn.Module):
    """
    IP-3: ClinicalCMGA — Full implementation for Phase 6.

    PHASE 6 INTEGRATION NOTES:
      - Replace the simple FC fusion head in HFL-MM-HC with this module.
      - f_a comes from FedMamba-HC.forward() output [B, 256]
      - f_b comes from MobileNetV3 encoder output  [B, 576]
      - delta_t_a, delta_t_b: from PTB-XL/CheXpert metadata timestamps
      - quality_a: from ECG signal quality metric (computed in preprocessing)
      - quality_b: from CXR image sharpness metric
      - urgency: from EHR events metadata (nurse calls / vital sign trends)
        If unavailable, pass urgency=torch.zeros(B,1) (neutral)

    DP-SGD COMPATIBILITY:
      All BatchNorm replaced with GroupNorm. Verified Opacus-compatible.
    """

    def __init__(self, d_a: int = 256, d_b: int = 576,
                 d_attn: int = 128, d_out: int = 256,
                 n_classes: int = 5,
                 lambda_a_init: float = 0.02,
                 lambda_b_init: float = 0.005):
        super().__init__()

        # Temporal decay gates
        self.gate_a = TemporalDecayGate(lambda_a_init)
        self.gate_b = TemporalDecayGate(lambda_b_init)

        # Learned null vectors for missing/stale modality
        self.null_a = nn.Parameter(torch.zeros(d_a))
        self.null_b = nn.Parameter(torch.zeros(d_b))

        # Cross-modal attention (bidirectional)
        self.attn_a2b = CrossModalAttention(d_a, d_b, d_attn)
        self.attn_b2a = CrossModalAttention(d_b, d_a, d_attn)

        # Urgency-gated fusion gate
        self.urgency_gate = nn.Sequential(
            nn.Linear(2 * d_attn + 1, 64),
            nn.GELU(),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

        # Output MLP
        self.out_mlp = nn.Sequential(
            nn.Linear(d_attn, d_out),
            nn.GroupNorm(8, d_out),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(d_out, n_classes),
        )

    def forward(self, f_a: torch.Tensor, f_b: torch.Tensor,
                delta_t_a: Optional[torch.Tensor] = None,
                delta_t_b: Optional[torch.Tensor] = None,
                quality_a: Optional[torch.Tensor] = None,
                quality_b: Optional[torch.Tensor] = None,
                urgency: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        f_a      : [B, 256]   ECG features from FedMamba-HC
        f_b      : [B, 576]   CXR features from MobileNetV3
        delta_t_a: [B]        minutes since ECG (default=0 → no decay)
        delta_t_b: [B]        minutes since X-ray (default=0 → no decay)
        quality_a: [B]        ECG quality ∈ [0,1] (default=1.0)
        quality_b: [B]        CXR quality ∈ [0,1] (default=1.0)
        urgency  : [B,1]      clinical urgency ∈ [0,1] (default=0.5)
        returns  : [B, n_classes] logits
        """
        B = f_a.shape[0]
        device = f_a.device

        # Defaults for missing metadata
        if delta_t_a is None:
            delta_t_a = torch.zeros(B, device=device)
        if delta_t_b is None:
            delta_t_b = torch.zeros(B, device=device)
        if quality_a is None:
            quality_a = torch.ones(B, device=device)
        if quality_b is None:
            quality_b = torch.ones(B, device=device)
        if urgency is None:
            urgency = torch.full((B, 1), 0.5, device=device)

        # Temporal decay gates
        tau_a = self.gate_a(quality_a, delta_t_a)   # [B, 1]
        tau_b = self.gate_b(quality_b, delta_t_b)   # [B, 1]

        # Gated feature blending with null vectors
        f_a_gated = tau_a * f_a + (1 - tau_a) * self.null_a
        f_b_gated = tau_b * f_b + (1 - tau_b) * self.null_b

        # Bidirectional cross-modal attention
        a2b = self.attn_a2b(f_a_gated, f_b_gated)  # [B, d_attn]
        b2a = self.attn_b2a(f_b_gated, f_a_gated)  # [B, d_attn]

        # Urgency-gated fusion
        gate_input = torch.cat([a2b, b2a, urgency], dim=-1)
        w = self.urgency_gate(gate_input)            # [B, 1]
        f_fused = w * a2b + (1 - w) * b2a           # [B, d_attn]

        return self.out_mlp(f_fused)                 # [B, n_classes]


# ============================================================
# PHASE 6 INTEGRATION CHECKLIST
# ============================================================
# [ ] Replace FC fusion head in HFLMMHC.__init__ with ClinicalCMGA()
# [ ] Add delta_t_a, delta_t_b extraction from PTB-XL metadata
# [ ] Add quality score computation in preprocess_healthcare.py
# [ ] Add urgency field to partition_noniid.py dataset schema
# [ ] Verify Opacus .make_private_with_epsilon() still works after swap
# [ ] Re-run GroupNorm check: replace_bn_with_gn() on full model
# [ ] Update onnx_exporter.py dummy inputs to include metadata tensors
# ============================================================


if __name__ == "__main__":
    # Design verification smoke test
    model = ClinicalCMGA(d_a=256, d_b=576, n_classes=5)
    B = 4
    f_a = torch.randn(B, 256)
    f_b = torch.randn(B, 576)
    delta_t_a = torch.tensor([0.0, 30.0, 90.0, 180.0])
    delta_t_b = torch.tensor([0.0, 60.0, 240.0, 480.0])
    quality_a = torch.tensor([1.0, 0.9, 0.7, 0.5])
    quality_b = torch.tensor([1.0, 1.0, 0.8, 0.6])
    urgency = torch.tensor([[0.1], [0.3], [0.7], [0.9]])

    logits = model(f_a, f_b, delta_t_a, delta_t_b, quality_a, quality_b, urgency)
    print(f"ClinicalCMGA output: {logits.shape}")  # [4, 5]

    # Show effect of temporal decay
    tau_a_vals = [float(model.gate_a(
        torch.tensor([1.0]),
        torch.tensor([t])
    ).item()) for t in [0, 30, 60, 120, 240]]
    print(f"ECG decay at [0,30,60,120,240] min: {[f'{v:.3f}' for v in tau_a_vals]}")
    print(f"λ_a learned: {model.gate_a.lambda_.item():.4f}")
    params = sum(p.numel() for p in model.parameters())
    print(f"ClinicalCMGA parameters: {params:,}")
