"""
HFL-MM-HC: Hierarchical Federated Multimodal Model.

Encoder A: multi-scale 1-D CNN + BiGRU + attention pooling over a
           multichannel time series [B, C, T], any T -> 256-d
Encoder B: FeatureEncoder over a fixed-length vector      -> 576-d
Fusion:    late-fusion FC head, GroupNorm throughout
Wrapper:   FedConform-HC (federated conformal prediction)

Every normalisation layer is GroupNorm or LayerNorm, never BatchNorm: BN mixes
statistics across a batch, which makes the per-sample (and hence per-patient)
gradient ill-defined and breaks DP-SGD accounting.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from fedmamba_hc import build_fedmamba_hc


class GroupNormND(nn.GroupNorm):
    """
    GroupNorm that also accepts 2-D [B, C] input by momentarily adding a
    singleton spatial dimension.

    Output is numerically identical to nn.GroupNorm on the same input, and
    because this subclasses nn.GroupNorm the parameters (weight, bias) keep
    the exact same state_dict keys — existing checkpoints load unchanged.

    Reason: torch's ONNX exporter decomposes GroupNorm via a symbolic that
    unsqueezes over spatial axes; with a 2-D input those axes are empty and
    export crashes (IndexError). The late-fusion head normalises flattened
    [B, C] features, so it needs this shim to be ONNX-exportable.
    """

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 2:
            return super().forward(x.unsqueeze(-1)).squeeze(-1)
        return super().forward(x)


def replace_bn_with_gn(module: nn.Module, num_groups: int = 8) -> nn.Module:
    """Replace all BatchNorm layers with GroupNorm for Opacus DP-SGD compatibility."""
    for name, child in module.named_children():
        if isinstance(child, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)):
            num_features = child.num_features
            gn = nn.GroupNorm(min(num_groups, num_features), num_features)
            setattr(module, name, gn)
        else:
            replace_bn_with_gn(child, num_groups)
    return module


def replace_inplace_activations(module: nn.Module) -> nn.Module:
    """
    Replace all inplace activations with non-inplace equivalents.
    Required for Opacus DP-SGD: inplace ops conflict with per-sample gradient hooks.
    Covers Hardswish, Hardsigmoid, ReLU, ReLU6 and SiLU.
    """
    for name, child in module.named_children():
        if isinstance(child, nn.Hardswish):
            setattr(module, name, nn.Hardswish(inplace=False))
        elif isinstance(child, nn.Hardsigmoid):
            setattr(module, name, nn.Hardsigmoid(inplace=False))
        elif isinstance(child, nn.ReLU):
            setattr(module, name, nn.ReLU(inplace=False))
        elif isinstance(child, nn.ReLU6):
            setattr(module, name, nn.ReLU6(inplace=False))
        elif isinstance(child, nn.SiLU):
            setattr(module, name, nn.SiLU(inplace=False))
        else:
            replace_inplace_activations(child)
    return module


class FeatureEncoder(nn.Module):
    """
    Encoder for a modality that arrives as a precomputed feature VECTOR rather
    than raw pixels, projecting it to the fusion width (576)
    so `LateFusionHead` — and therefore the whole DP/FL stack — is unchanged.

    Used for:
      * WEAR   — 2048-d two-stream I3D video features per 2 s window
      * VitalDB— preoperative clinical + laboratory vector

    GroupNormND throughout (never BatchNorm): Opacus rejects BatchNorm because
    it mixes statistics across a batch, which breaks per-sample gradients.
    """

    def __init__(self, in_dim: int, out_dim: int = 576,
                 hidden: int = 1024, dropout: float = 0.3):
        super().__init__()
        self.in_dim, self.out_dim = in_dim, out_dim
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            GroupNormND(16, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, out_dim),
            GroupNormND(16, out_dim),
            nn.GELU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, in_dim] → [B, out_dim]
        return self.net(x)


class LateFusionHead(nn.Module):
    """Late fusion of the two modality embeddings → class logits."""

    def __init__(self, d_a: int = 256, d_b: int = 576,
                 hidden: int = 512, n_classes: int = 5,
                 dropout: float = 0.3):
        super().__init__()
        d_in = d_a + d_b
        # GroupNormND (not nn.GroupNorm): fusion features are 2-D [B, C] after
        # concatenation; the ND shim keeps identical params/outputs while making
        # the layer ONNX-exportable. See GroupNormND docstring.
        self.fc = nn.Sequential(
            nn.Linear(d_in, hidden),
            GroupNormND(16, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 256),
            GroupNormND(8, 256),
            nn.GELU(),
            nn.Linear(256, n_classes),
        )

    def forward(self, f_a: torch.Tensor, f_b: torch.Tensor) -> torch.Tensor:
        return self.fc(torch.cat([f_a, f_b], dim=-1))


class HFLMMHC(nn.Module):
    """
    Complete HFL-MM-HC model.
    Input:  x_a [B, C_a, T]  (multichannel time series, any T)
            x_b [B, feat_b_dim]  (fixed-length feature vector)
    Output: logits [B, n_classes]
    """

    def __init__(self, n_classes: int = 5, n_mamba_blocks: int = 4,
                 dropout: float = 0.3,
                 modality_b: str = "features", feat_b_dim: int = None,
                 n_channels_a: int = 12):
        """
        modality_b:
          "features" — encoder_b is FeatureEncoder over [B,feat_b_dim]
                       (WEAR I3D video features; VitalDB clinical vector)

        n_channels_a: input channels for encoder_a. 12 for WEAR's 4x3
          accelerometer; 18 for VitalDB (9 signals + 9 binary missingness
          masks, since an absent arterial line is itself clinical information
          about patient acuity).

        encoder_a takes [B,C,T] for ANY T (adaptive pooling → 256-d), which is
        why accelerometer and intraoperative vitals both fit it unchanged.
        """
        super().__init__()
        self.modality_b = modality_b
        self.encoder_a = build_fedmamba_hc(n_mamba_blocks=n_mamba_blocks,
                                          n_leads=n_channels_a)
        if modality_b == "features":
            if not feat_b_dim:
                raise ValueError("modality_b='features' requires feat_b_dim")
            self.encoder_b = FeatureEncoder(feat_b_dim, out_dim=576,
                                            dropout=dropout)
        else:
            raise ValueError(f"unknown modality_b={modality_b!r}")
        self.fusion = LateFusionHead(
            d_a=self.encoder_a.output_dim,
            d_b=self.encoder_b.out_dim,
            n_classes=n_classes,
            dropout=dropout,
        )
        self.n_classes = n_classes

    def forward(self, x_a: torch.Tensor, x_b: torch.Tensor) -> torch.Tensor:
        f_a = self.encoder_a(x_a)    # [B, 256]
        f_b = self.encoder_b(x_b)    # [B, 576]
        return self.fusion(f_a, f_b) # [B, n_classes]

    def encode(self, x_a: torch.Tensor,
               x_b: torch.Tensor) -> tuple:
        """Return raw features (used by MOON baseline and FedKD-E)."""
        return self.encoder_a(x_a), self.encoder_b(x_b)

    def trainable_params(self):
        return [p for p in self.parameters() if p.requires_grad]

    @property
    def n_trainable(self) -> int:
        return sum(p.numel() for p in self.trainable_params())

    @property
    def n_total(self) -> int:
        return sum(p.numel() for p in self.parameters())


def build_hfl_mm_hc(n_classes: int = 5, **kwargs) -> HFLMMHC:
    model = HFLMMHC(n_classes=n_classes, **kwargs)
    replace_bn_with_gn(model)
    replace_inplace_activations(model)
    # Opacus DP-SGD requires zero BatchNorm. Fail loudly at construction
    # rather than letting it surface as an opaque Opacus validation error.
    leftover = [name for name, m in model.named_modules()
                if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d))]
    if leftover:
        raise RuntimeError(
            f"build_hfl_mm_hc: BatchNorm layers remain after replacement: "
            f"{leftover}. Opacus DP-SGD will fail."
        )
    return model


def freeze_encoders(model: "HFLMMHC") -> "HFLMMHC":
    """
    Freeze both feature encoders (encoder_a: temporal, encoder_b: static
    so ONLY the fusion head trains — the DP fine-tuning setup.

    Rationale: a small head over frozen, already-discriminative features is a
    near-linear probe (convex, low-dimensional), which DP-SGD optimises
    robustly even at the large σ a strict ε forces (σ≈11.3 at ε=1 here) —
    unlike training encoders from scratch under that noise, where the
    encoders' gradients are destroyed before they can form useful features.
    Freezing does NOT change σ (σ depends on ε/steps/sample-rate, not param
    count); it changes the optimisation geometry so the same σ is tolerable.

    requires_grad is NOT stored in state_dict, so this MUST be re-applied
    after every load_state_dict / model rebuild (e.g. each FL round's fresh
    local_model), or the encoders silently become trainable again.
    """
    for p in model.encoder_a.parameters():
        p.requires_grad = False
    for p in model.encoder_b.parameters():
        p.requires_grad = False
    return model


def load_pretrained_encoders(model: "HFLMMHC", ckpt_path: str,
                             strict: bool = True) -> "HFLMMHC":
    """
    Load encoder_a + encoder_b weights from a checkpoint written by
    pretrain_encoders.py (keys "encoder_a" / "encoder_b"). The fusion head is
    left at its fresh init — it is the part DP-trained on the private FL data.

    For a valid ε guarantee the checkpoint MUST come from NON-private data
    (an external public ECG corpus for the Mamba, analogous to encoder_b's
    ImageNet pretraining) — pretraining on the FL clients' own data and then
    claiming ε=1 would leak. See pretrain_encoders.py's --public_data.
    """
    ckpt = torch.load(ckpt_path, map_location="cpu")
    enc = ckpt.get("encoders", ckpt)  # accept either {"encoders": {...}} or flat
    model.encoder_a.load_state_dict(enc["encoder_a"], strict=strict)
    model.encoder_b.load_state_dict(enc["encoder_b"], strict=strict)
    return model


class PersonalizationAdapter(nn.Module):
    """
    pFAL — Personalised FL Adapter (PHANTOM-FL Innovation IP-5).

    A small per-edge/hospital head applied on top of the shared global
    model's logits. Only this adapter is fit on a given edge's own local
    data; it is never sent to the cloud or averaged with any other edge's
    adapter, so a hospital's local label distribution never leaves that
    hospital — only the shared backbone (HFLMMHC) participates in FedAvg.

    Initialised as an identity map (weight=I, bias=0) so an untrained
    adapter reproduces the shared model's own logits exactly, and training
    only needs to learn a small local correction on top of that.
    """

    def __init__(self, n_classes: int = 5):
        super().__init__()
        self.affine = nn.Linear(n_classes, n_classes)
        with torch.no_grad():
            self.affine.weight.copy_(torch.eye(n_classes))
            self.affine.bias.zero_()

    def forward(self, shared_logits: torch.Tensor) -> torch.Tensor:
        return self.affine(shared_logits)


def fit_personalization_adapter(backbone: nn.Module, adapter: "PersonalizationAdapter",
                                loader, device, epochs: int = 3,
                                lr: float = 1e-3) -> "PersonalizationAdapter":
    """
    Fit a pFAL adapter to one edge's own local (calibration/val) data with
    the shared backbone frozen — only the small adapter head trains.
    """
    backbone.eval()
    for p in backbone.parameters():
        p.requires_grad = False
    adapter.train().to(device)
    optimizer = torch.optim.Adam(adapter.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    for _ in range(epochs):
        for x_a, x_b, _tab, labels in loader:
            with torch.no_grad():
                shared_logits = backbone(x_a.to(device, non_blocking=True),
                                         x_b.to(device, non_blocking=True))
            optimizer.zero_grad()
            personalized_logits = adapter(shared_logits)
            loss = loss_fn(personalized_logits, labels.to(device, non_blocking=True))
            loss.backward()
            optimizer.step()
    return adapter


if __name__ == "__main__":
    model = build_hfl_mm_hc(n_classes=5, n_channels_a=18,
                            modality_b="features", feat_b_dim=34)
    x_a = torch.randn(2, 18, 300)
    x_b = torch.randn(2, 34)
    logits = model(x_a, x_b)
    print(f"Output shape: {logits.shape}")          # [2, 5]
    print(f"Total params: {model.n_total:,}")
    print(f"Trainable:    {model.n_trainable:,}")
    # Check no BN remains (Opacus requirement)
    for name, m in model.named_modules():
        if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d)):
            print(f"WARNING: BatchNorm found at {name}")
    print("BatchNorm check passed — all replaced with GroupNorm.")
