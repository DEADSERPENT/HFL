"""
device_utils.py — GPU/CPU Auto-Detection Utility
=================================================
Project: Hierarchical Federated Learning for Privacy-Aware, Low-Latency Multimodal IoT
Student: Samartha H V | MIT Bengaluru | 2026

This module is imported by ALL Python scripts in the HFL project.
It automatically detects and configures the best available compute device:
  - NVIDIA GPU with CUDA  → uses GPU (primary)
  - No GPU / CUDA error   → falls back to CPU gracefully

Usage:
    from device_utils import get_device, device_info, move_to_device
    device = get_device()
    model  = model.to(device)
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("device_utils")


def get_device(verbose: bool = True) -> "torch.device":
    """
    Auto-detect and return the best available compute device.

    Priority:
        1. NVIDIA GPU (CUDA) — if torch.cuda.is_available()
        2. Apple Silicon MPS  — if torch.backends.mps.is_available()
        3. CPU                — fallback

    Returns:
        torch.device: selected device object ready for .to(device) calls.
    """
    try:
        import torch
    except ImportError:
        log.warning("PyTorch not installed. Returning CPU device string.")
        return _CpuFallback()

    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        gpu_name  = torch.cuda.get_device_name(0)
        vram_gb   = torch.cuda.get_device_properties(0).total_memory / 1e9
        if verbose:
            log.info(f"GPU SELECTED  : {gpu_name}")
            log.info(f"VRAM          : {vram_gb:.2f} GB")
            log.info(f"CUDA Version  : {torch.version.cuda}")
            log.info(f"cuDNN Version : {torch.backends.cudnn.version()}")
            log.info(f"Device        : {device}")
        return device

    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        if verbose:
            log.info(f"Apple MPS GPU SELECTED")
            log.info(f"Device        : {device}")
        return device

    else:
        device = torch.device("cpu")
        if verbose:
            log.warning("No GPU detected. Falling back to CPU.")
            import multiprocessing
            log.info(f"CPU Cores     : {multiprocessing.cpu_count()}")
            log.info(f"Device        : {device}")
        return device


def device_info() -> dict:
    """
    Return a dictionary of all device information.
    Used for logging into result CSV files (reproducibility).
    """
    info = {
        "device_type": "cpu",
        "device_name": "CPU",
        "cuda_available": False,
        "cuda_version": "N/A",
        "cudnn_version": "N/A",
        "vram_gb": 0.0,
        "pytorch_version": "N/A",
    }

    try:
        import torch
        info["pytorch_version"] = torch.__version__

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info.update({
                "device_type":    "cuda",
                "device_name":    torch.cuda.get_device_name(0),
                "cuda_available": True,
                "cuda_version":   torch.version.cuda,
                "cudnn_version":  str(torch.backends.cudnn.version()),
                "vram_gb":        round(props.total_memory / 1e9, 2),
                "gpu_multiprocessors": props.multi_processor_count,
            })
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            info.update({
                "device_type": "mps",
                "device_name": "Apple Silicon GPU",
                "cuda_available": False,
            })
    except ImportError:
        pass

    return info


def move_to_device(obj, device):
    """
    Safely move a model or tensor to the target device.
    Works even if torch is not installed (returns obj unchanged).
    """
    try:
        return obj.to(device)
    except Exception as e:
        log.warning(f"Could not move to {device}: {e}. Keeping on original device.")
        return obj


def set_seed(seed: int = 42, device=None):
    """
    Set random seeds for full reproducibility across CPU and GPU.
    Call this at the start of every simulation/training script.
    """
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark     = False
        log.info(f"Random seed set: {seed} (CPU + GPU)")
    except ImportError:
        log.info(f"Random seed set: {seed} (CPU only, torch not available)")


def get_dataloader_workers() -> int:
    """
    Return optimal number of DataLoader worker processes.
    GPU: use multiple workers. CPU: use 0 to avoid overhead.
    """
    try:
        import torch
        if torch.cuda.is_available():
            return min(8, os.cpu_count() // 2)
        else:
            return 0
    except ImportError:
        return 0


class _CpuFallback:
    """Minimal device object for when PyTorch is not installed."""
    def __str__(self): return "cpu"
    def __repr__(self): return "cpu"


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  HFL Device Detection — Self Test")
    print("=" * 60)
    device = get_device(verbose=True)
    info   = device_info()
    print("\nDevice Info Dictionary:")
    for k, v in info.items():
        print(f"  {k:<25} : {v}")
    set_seed(42, device)
    print(f"\nDataLoader workers : {get_dataloader_workers()}")
    print(f"\nActive device      : {device}")
    print("=" * 60)
