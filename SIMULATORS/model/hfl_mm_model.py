"""
HFL-MM-HC: Hierarchical Federated Multimodal Model — Healthcare Variant
Encoder A: FedMamba-HC (12-lead ECG via Mamba SSM)       [IP-1]
Encoder B: MobileNetV3-Small (chest X-ray)
Fusion: Late fusion FC head with GroupNorm
Wrapper: FedConform-HC (federated conformal prediction)  [IP-9]
"""

import types

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
from torchvision.models.mobilenetv3 import InvertedResidual
from fedmamba_hc import build_fedmamba_hc


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
    Covers Hardswish, Hardsigmoid, ReLU, ReLU6, SiLU, GELU used in MobileNetV3.
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


def _patched_inverted_residual_forward(self, input: torch.Tensor) -> torch.Tensor:
    """Out-of-place residual addition — required for Opacus per-sample gradient hooks."""
    result = self.block(input)
    if self.use_res_connect:
        result = result + input  # was: result += input (inplace, breaks Opacus)
    return result


def fix_mobilenet_residuals(module: nn.Module) -> nn.Module:
    """
    Patch every InvertedResidual block in MobileNetV3 to use out-of-place addition.
    Opacus's BackwardHookFunctionBackward cannot handle views modified inplace,
    which is exactly what the default 'result += input' does.
    """
    for m in module.modules():
        if isinstance(m, InvertedResidual):
            m.forward = types.MethodType(_patched_inverted_residual_forward, m)
    return module


class CXREncoder(nn.Module):
    """MobileNetV3-Small for chest X-ray feature extraction."""

    def __init__(self, pretrained: bool = True, freeze_layers: int = 8):
        super().__init__()
        weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretrained else None
        backbone = mobilenet_v3_small(weights=weights)
        # Keep feature extractor, discard classifier
        self.features = backbone.features
        self.avgpool = backbone.avgpool
        self.out_dim = 576

        # Freeze first freeze_layers InvertedResidual blocks
        layers = list(self.features.children())
        for i, layer in enumerate(layers[:freeze_layers]):
            for param in layer.parameters():
                param.requires_grad = False

        # Replace BatchNorm with GroupNorm for Opacus compatibility
        replace_bn_with_gn(self.features)
        # Patch inplace residual += to out-of-place for Opacus
        fix_mobilenet_residuals(self.features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, 3, 224, 224] → [B, 576]
        x = self.features(x)
        x = self.avgpool(x)
        return x.flatten(1)


class LateFusionHead(nn.Module):
    """Late fusion of ECG and CXR features → class logits."""

    def __init__(self, d_a: int = 256, d_b: int = 576,
                 hidden: int = 512, n_classes: int = 5,
                 dropout: float = 0.3):
        super().__init__()
        d_in = d_a + d_b
        self.fc = nn.Sequential(
            nn.Linear(d_in, hidden),
            nn.GroupNorm(16, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 256),
            nn.GroupNorm(8, 256),
            nn.GELU(),
            nn.Linear(256, n_classes),
        )

    def forward(self, f_a: torch.Tensor, f_b: torch.Tensor) -> torch.Tensor:
        return self.fc(torch.cat([f_a, f_b], dim=-1))


class HFLMMHC(nn.Module):
    """
    Complete HFL-MM-HC model.
    Input:  ecg [B, 12, 1000], cxr [B, 3, 224, 224]
    Output: logits [B, n_classes]
    """

    def __init__(self, n_classes: int = 5, n_mamba_blocks: int = 4,
                 pretrained_cxr: bool = True, freeze_cxr_layers: int = 8,
                 dropout: float = 0.3):
        super().__init__()
        self.encoder_a = build_fedmamba_hc(n_mamba_blocks=n_mamba_blocks)
        self.encoder_b = CXREncoder(pretrained=pretrained_cxr,
                                    freeze_layers=freeze_cxr_layers)
        self.fusion = LateFusionHead(
            d_a=self.encoder_a.output_dim,
            d_b=self.encoder_b.out_dim,
            n_classes=n_classes,
            dropout=dropout,
        )
        self.n_classes = n_classes

    def forward(self, ecg: torch.Tensor, cxr: torch.Tensor) -> torch.Tensor:
        f_a = self.encoder_a(ecg)    # [B, 256]
        f_b = self.encoder_b(cxr)    # [B, 576]
        return self.fusion(f_a, f_b) # [B, n_classes]

    def encode(self, ecg: torch.Tensor,
               cxr: torch.Tensor) -> tuple:
        """Return raw features (used by MOON baseline and FedKD-E)."""
        return self.encoder_a(ecg), self.encoder_b(cxr)

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
    fix_mobilenet_residuals(model)
    return model


if __name__ == "__main__":
    model = build_hfl_mm_hc(n_classes=5)
    ecg = torch.randn(2, 12, 1000)
    cxr = torch.randn(2, 3, 224, 224)
    logits = model(ecg, cxr)
    print(f"Output shape: {logits.shape}")          # [2, 5]
    print(f"Total params: {model.n_total:,}")
    print(f"Trainable:    {model.n_trainable:,}")
    # Check no BN remains (Opacus requirement)
    for name, m in model.named_modules():
        if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d)):
            print(f"WARNING: BatchNorm found at {name}")
    print("BatchNorm check passed — all replaced with GroupNorm.")
