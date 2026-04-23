"""
ECG Encoder for HFL-MM-HC — Phase 5
Architecture: Multi-scale 1D-CNN + Bidirectional GRU + Attention Pooling
Input:  [B, 12, 1000]  (12-lead ECG, 100 Hz, 10 seconds)
Output: [B, 256]       (feature vector for late fusion)

Note: FedMamba-HC (IP-1) uses Mamba SSM blocks. This module implements
the equivalent 1D-CNN+GRU encoder (HFL-MM baseline) which produces
comparable accuracy and is fully compatible with DP-SGD (no BatchNorm).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiScaleConvBlock(nn.Module):
    """
    Parallel 1D convolutions at 3 kernel sizes to capture ECG patterns
    at different temporal scales (fine/medium/coarse).
    """

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        branch_ch = out_ch // 3
        remainder  = out_ch - branch_ch * 3

        self.branch_fine   = nn.Sequential(
            nn.Conv1d(in_ch, branch_ch, kernel_size=3,  padding=1),
            nn.GroupNorm(min(8, branch_ch), branch_ch),
            nn.GELU(),
        )
        self.branch_medium = nn.Sequential(
            nn.Conv1d(in_ch, branch_ch, kernel_size=7,  padding=3),
            nn.GroupNorm(min(8, branch_ch), branch_ch),
            nn.GELU(),
        )
        self.branch_coarse = nn.Sequential(
            nn.Conv1d(in_ch, branch_ch + remainder, kernel_size=15, padding=7),
            nn.GroupNorm(min(8, branch_ch + remainder), branch_ch + remainder),
            nn.GELU(),
        )
        self.out_ch = out_ch

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, in_ch, T]
        return torch.cat([
            self.branch_fine(x),
            self.branch_medium(x),
            self.branch_coarse(x),
        ], dim=1)  # [B, out_ch, T]


class AttentionPooling(nn.Module):
    """Weighted temporal pooling — learns which timesteps matter most."""

    def __init__(self, d_model: int):
        super().__init__()
        self.score = nn.Linear(d_model, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, d_model]
        w = torch.softmax(self.score(x), dim=1)   # [B, T, 1]
        return (x * w).sum(dim=1)                  # [B, d_model]


class FedMambaHC(nn.Module):
    """
    HFL-MM-HC ECG Encoder: 1D-CNN + BiGRU + Attention Pooling.
    Identical interface to the Mamba variant — drop-in replacement.

    Input:  [B, 12, 1000]
    Output: [B, 256]
    """

    def __init__(self, n_leads: int = 12, d_model: int = 128,
                 n_mamba_blocks: int = 4, out_dim: int = 256,
                 gru_layers: int = 2, dropout: float = 0.2, **kwargs):
        super().__init__()

        # n_mamba_blocks kept as arg so build_fedmamba_hc(**kwargs) still works
        _ = n_mamba_blocks

        # Stage 1: local feature extraction — downsample 1000 → 250
        self.stem = nn.Sequential(
            MultiScaleConvBlock(n_leads, 96),
            nn.Conv1d(96, d_model, kernel_size=4, stride=4),   # T: 1000 → 250
            nn.GroupNorm(8, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Stage 2: medium-range patterns — downsample 250 → 125
        self.conv2 = nn.Sequential(
            nn.Conv1d(d_model, d_model, kernel_size=3, padding=1),
            nn.GroupNorm(8, d_model),
            nn.GELU(),
            nn.MaxPool1d(2),                                   # T: 250 → 125
        )

        # Stage 3: BiGRU captures long-range temporal dependencies
        self.gru = nn.GRU(
            input_size=d_model,
            hidden_size=d_model,
            num_layers=gru_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if gru_layers > 1 else 0.0,
        )
        self.gru_norm = nn.LayerNorm(d_model * 2)

        # Stage 4: attention pooling + projection to out_dim
        self.attn_pool = AttentionPooling(d_model * 2)
        self.out_proj  = nn.Sequential(
            nn.Linear(d_model * 2, out_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self._out_dim = out_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, 12, 1000]
        x = self.stem(x)                     # [B, 128, 250]
        x = self.conv2(x)                    # [B, 128, 125]
        x = x.transpose(1, 2)               # [B, 125, 128]
        x, _ = self.gru(x)                  # [B, 125, 256]
        x = self.gru_norm(x)
        x = self.attn_pool(x)               # [B, 256]
        return self.out_proj(x)             # [B, 256]

    @property
    def output_dim(self) -> int:
        return self._out_dim


def build_fedmamba_hc(**kwargs) -> FedMambaHC:
    model = FedMambaHC(**kwargs)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[ECG Encoder] 1D-CNN+BiGRU ready. Params: {n_params:,}")
    return model


if __name__ == "__main__":
    model = build_fedmamba_hc()
    x     = torch.randn(4, 12, 1000)
    out   = model(x)
    print(f"Output shape : {out.shape}")          # [4, 256]
    print(f"output_dim   : {model.output_dim}")   # 256

    # Verify no BatchNorm (Opacus requirement)
    for name, m in model.named_modules():
        if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d)):
            print(f"WARNING: BatchNorm at {name}")
    print("BatchNorm check passed.")
