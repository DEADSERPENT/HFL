"""
IP-1: FedMamba-HC — Mamba SSM ECG Encoder for Federated Healthcare FL
Phase 5 implementation. Requires: pip install mamba-ssm causal-conv1d
CUDA GPU required — no CPU fallback.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math

try:
    from mamba_ssm import Mamba
except ImportError as _e:
    raise ImportError(
        "[FedMamba-HC] mamba-ssm not installed. Run:\n"
        "  pip install mamba-ssm causal-conv1d\n"
        "Requires CUDA GPU + CUDA 11.8+."
    ) from _e


class PatchEmbedECG(nn.Module):
    """Embed 12-lead ECG into temporal patches for Mamba blocks."""

    def __init__(self, n_leads=12, d_model=128, patch_size=10, stride=5):
        super().__init__()
        self.proj = nn.Conv1d(n_leads, d_model, kernel_size=patch_size, stride=stride)
        self.norm = nn.GroupNorm(8, d_model)

    def forward(self, x):
        # x: [B, 12, 1000] → [B, d_model, n_patches] → [B, n_patches, d_model]
        x = F.gelu(self.norm(self.proj(x)))
        return x.transpose(1, 2)


class MambaBlock(nn.Module):
    """Single Mamba block with residual and FFN."""

    def __init__(self, d_model=128, d_state=16, d_conv=4, expand=2):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.mamba = Mamba(d_model=d_model, d_state=d_state,
                           d_conv=d_conv, expand=expand)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.GELU(),
            nn.Linear(d_model * 4, d_model),
        )

    def forward(self, x):
        x = x + self.mamba(self.norm1(x))
        x = x + self.ffn(self.norm2(x))
        return x



class FedMambaHC(nn.Module):
    """
    IP-1: FedMamba-HC — Mamba SSM ECG Encoder
    Input:  [B, 12, 1000]  (12-lead ECG, 100Hz, 10 seconds)
    Output: [B, 256]       (feature vector for late fusion)
    DP-SGD compatible: no BatchNorm, uses GroupNorm throughout.
    """

    def __init__(self, n_leads=12, d_model=128, n_mamba_blocks=4,
                 d_state=16, d_conv=4, expand=2, out_dim=256):
        super().__init__()
        self.patch_embed = PatchEmbedECG(n_leads, d_model, patch_size=10, stride=5)
        seq_len = (1000 - 10) // 5 + 1  # = 199
        self.pos_embed = nn.Parameter(torch.zeros(1, seq_len, d_model))
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        self.blocks = nn.ModuleList([
            MambaBlock(d_model, d_state, d_conv, expand)
            for _ in range(n_mamba_blocks)
        ])
        self.norm = nn.LayerNorm(d_model)
        self.out_proj = nn.Sequential(
            nn.Linear(d_model, out_dim),
            nn.GELU(),
        )

    def forward(self, x):
        # x: [B, 12, 1000]
        x = self.patch_embed(x)        # [B, 199, 128]
        x = x + self.pos_embed
        for block in self.blocks:
            x = block(x)
        x = self.norm(x)
        x = x.mean(dim=1)              # global average pooling
        return self.out_proj(x)        # [B, 256]

    @property
    def output_dim(self):
        return 256


def build_fedmamba_hc(**kwargs):
    """Factory: builds FedMamba-HC. Runs on GPU if CUDA available, else CPU."""
    from device_utils import get_device
    device = get_device(verbose=False)
    model = FedMambaHC(**kwargs).to(device)
    print(f"[FedMamba-HC] mamba-ssm CUDA encoder ready on {device}.")
    return model


if __name__ == "__main__":
    from device_utils import get_device
    device = get_device()
    model  = build_fedmamba_hc().to(device)
    x      = torch.randn(4, 12, 1000).to(device)
    out    = model(x)
    print(f"FedMamba-HC output: {out.shape}")  # [4, 256]
    params = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {params:,}")
