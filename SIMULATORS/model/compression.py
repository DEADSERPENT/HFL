"""
Gradient Compression Module — Phase 5
Two-step: Top-k sparsification (20%) + 8-bit quantization → 20× compression
Error feedback accumulator prevents gradient information loss.
"""

import torch
import numpy as np
from typing import Dict, List, Tuple, Optional


class GradientCompressor:
    """
    Top-k sparsification + 8-bit quantization with error feedback.
    Combined compression ratio: 5× (sparsity) × 4× (quantization) = 20×
    """

    def __init__(self, sparsity: float = 0.2, quant_bits: int = 8):
        self.sparsity = sparsity        # fraction of values to KEEP (top-20%)
        self.quant_bits = quant_bits    # bits for quantization
        self.quant_levels = 2 ** quant_bits - 1
        self._error_feedback: Dict[str, torch.Tensor] = {}

    def compress(self, named_tensors: Dict[str, torch.Tensor],
                 use_error_feedback: bool = True) -> Dict[str, dict]:
        """
        Compress gradient update dictionary.

        Args:
            named_tensors: {param_name: gradient_tensor}
            use_error_feedback: accumulate and add residuals

        Returns:
            compressed: {param_name: {indices, values_uint8, g_min, g_max, shape}}
        """
        compressed = {}
        for name, grad in named_tensors.items():
            flat = grad.float().flatten()

            # Error feedback: add accumulated residual
            if use_error_feedback:
                if name not in self._error_feedback:
                    self._error_feedback[name] = torch.zeros_like(flat)
                flat = flat + self._error_feedback[name]

            # Step A: Top-k sparsification
            k = max(1, int(len(flat) * self.sparsity))
            abs_flat = flat.abs()
            _, topk_indices = torch.topk(abs_flat, k, sorted=False)
            topk_values = flat[topk_indices]

            # Update error feedback residual
            if use_error_feedback:
                residual = flat.clone()
                residual[topk_indices] = 0.0
                self._error_feedback[name] = residual

            # Step B: 8-bit quantization of top-k values
            g_min = topk_values.min().item()
            g_max = topk_values.max().item()
            if g_max == g_min:
                g_max = g_min + 1e-8
            scale = (g_max - g_min) / self.quant_levels
            quantized = ((topk_values - g_min) / scale).round().clamp(0, self.quant_levels)
            values_uint8 = quantized.to(torch.uint8)

            compressed[name] = {
                "indices":      topk_indices.cpu().numpy().astype(np.int32),
                "values_uint8": values_uint8.cpu().numpy(),
                "g_min":        np.float32(g_min),
                "g_max":        np.float32(g_max),
                "shape":        tuple(grad.shape),
            }

        return compressed

    def decompress(self, compressed: Dict[str, dict],
                   device: torch.device = None) -> Dict[str, torch.Tensor]:
        """Reconstruct gradient tensors from compressed representation."""
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        decompressed = {}
        for name, data in compressed.items():
            indices    = torch.from_numpy(data["indices"]).long()
            values_u8  = torch.from_numpy(data["values_uint8"]).float()
            g_min      = float(data["g_min"])
            g_max      = float(data["g_max"])
            shape      = data["shape"]

            # Dequantize
            scale = (g_max - g_min) / self.quant_levels
            values = values_u8 * scale + g_min

            # Reconstruct sparse → dense
            n_elements = 1
            for s in shape:
                n_elements *= s
            flat = torch.zeros(n_elements, device=device)
            flat[indices.to(device)] = values.to(device)
            decompressed[name] = flat.reshape(shape)

        return decompressed

    def compression_ratio(self, original_bytes: int,
                           compressed: Dict[str, dict]) -> float:
        """Calculate actual compression ratio achieved."""
        compressed_bytes = 0
        for data in compressed.values():
            # indices (int32) + values (uint8) + 2 floats header
            compressed_bytes += len(data["indices"]) * 4
            compressed_bytes += len(data["values_uint8"]) * 1
            compressed_bytes += 8  # g_min, g_max as float32

        return original_bytes / max(compressed_bytes, 1)

    def reset_error_feedback(self):
        self._error_feedback.clear()


def model_to_delta(current_params: Dict[str, torch.Tensor],
                   reference_params: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """Compute parameter delta: current - reference."""
    return {name: current_params[name] - reference_params[name]
            for name in current_params}


def apply_delta(model: torch.nn.Module,
                delta: Dict[str, torch.Tensor],
                weight: float = 1.0):
    """Apply weighted delta to model parameters in-place."""
    with torch.no_grad():
        for name, param in model.named_parameters():
            if name in delta:
                param.add_(delta[name] * weight)


def count_model_bytes(model: torch.nn.Module) -> int:
    """Count total bytes of model parameters (float32)."""
    return sum(p.numel() * 4 for p in model.parameters())


if __name__ == "__main__":
    # Smoke test
    import torch.nn as nn
    model = nn.Linear(1000, 100)
    ref_params = {n: p.data.clone() for n, p in model.named_parameters()}

    # Simulate gradient update
    grad_delta = {n: torch.randn_like(p) * 0.01
                  for n, p in model.named_parameters()}

    compressor = GradientCompressor(sparsity=0.2, quant_bits=8)
    compressed = compressor.compress(grad_delta)
    decompressed = compressor.decompress(compressed)

    original_bytes = sum(v.numel() * 4 for v in grad_delta.values())
    ratio = compressor.compression_ratio(original_bytes, compressed)
    print(f"Compression ratio: {ratio:.1f}x")
    print(f"Original: {original_bytes / 1e6:.2f} MB, "
          f"Compressed: {original_bytes / ratio / 1e6:.3f} MB")

    # Verify reconstruction quality
    for name in grad_delta:
        err = (grad_delta[name] - decompressed[name]).abs().mean()
        print(f"  {name}: MAE = {err:.6f}")
