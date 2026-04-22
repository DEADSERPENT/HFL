"""
device_utils.py — GPU/CPU Auto-Select + Full GPU Optimization
=============================================================
Project: Hierarchical Federated Learning — Healthcare IoT
Student: Samartha H V | MIT Bengaluru | 2026

Priority: CUDA GPU → CPU fallback (works on any Linux system).
All GPU performance flags are set automatically when CUDA is available.

Usage (from any script):
    from device_utils import get_device, optimize_gpu, get_dataloader_kwargs
    device = get_device()
    optimize_gpu()
"""

import os
import torch


def get_device(verbose: bool = True) -> torch.device:
    """
    Return best available device: CUDA GPU if present, else CPU.
    Works on any Linux machine regardless of GPU vendor/driver version.
    """
    if torch.cuda.is_available():
        device = torch.device("cuda")
        if verbose:
            props = torch.cuda.get_device_properties(0)
            vram  = props.total_memory / 1e9
            print(f"[Device] GPU  : {torch.cuda.get_device_name(0)}")
            print(f"[Device] VRAM : {vram:.1f} GB  |  "
                  f"SMs: {props.multi_processor_count}  |  "
                  f"CUDA {torch.version.cuda}  |  "
                  f"cuDNN {torch.backends.cudnn.version()}")
    else:
        device = torch.device("cpu")
        if verbose:
            import multiprocessing
            print(f"[Device] CPU fallback — {multiprocessing.cpu_count()} cores")
            print("[Device] TIP: Install CUDA + nvidia drivers to enable GPU.")
    return device


def optimize_gpu(memory_fraction: float = 0.95) -> None:
    """
    Enable every available GPU performance flag.
    Safe no-op if no CUDA GPU is present.

    Flags set:
      cudnn.benchmark   — cuDNN auto-tunes fastest kernel per input shape
      allow_tf32        — TF32 on Ampere+ GPUs (~3× faster matmul, <0.1% accuracy diff)
      memory_fraction   — reserve 95% VRAM upfront, prevents fragmentation OOM
      empty_cache       — flush leftover allocations before training starts
    """
    if not torch.cuda.is_available():
        return

    torch.backends.cudnn.benchmark    = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32   = True
    torch.cuda.set_per_process_memory_fraction(memory_fraction, device=0)
    torch.cuda.empty_cache()

    print(f"[GPU Opt] cuDNN benchmark=True | TF32=True | "
          f"memory_fraction={memory_fraction}")


def get_dataloader_kwargs(device: torch.device) -> dict:
    """
    Return DataLoader constructor kwargs tuned for the active device.

    GPU path: pin_memory=True overlaps CPU→GPU transfer with GPU compute.
              num_workers ≥ 2 keeps the GPU fed without stalling on disk I/O.
              persistent_workers keeps worker processes alive between epochs.
    CPU path: num_workers=0 avoids multiprocessing overhead on CPU-only runs.
    """
    if device.type == "cuda":
        n_cpu   = os.cpu_count() or 2
        workers = min(4, max(2, n_cpu // 2))
        return {
            "num_workers":        workers,
            "pin_memory":         True,
            "persistent_workers": True,
            "prefetch_factor":    2,
        }
    return {
        "num_workers": 0,
        "pin_memory":  False,
    }


def to_device(obj, device: torch.device, non_blocking: bool = True):
    """
    Move tensor or model to device.
    non_blocking=True enables async CPU→GPU transfer when pin_memory is used.
    """
    if device.type == "cuda":
        return obj.to(device, non_blocking=non_blocking)
    return obj.to(device)


def set_seed(seed: int = 42) -> None:
    """Full reproducibility: CPU + all GPUs."""
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    print(f"[Seed] Set to {seed}")


def gpu_memory_info() -> None:
    """Print current GPU memory allocation (call after model.to(device))."""
    if not torch.cuda.is_available():
        return
    alloc    = torch.cuda.memory_allocated(0)  / 1e9
    reserved = torch.cuda.memory_reserved(0)   / 1e9
    total    = torch.cuda.get_device_properties(0).total_memory / 1e9
    free     = total - reserved
    print(f"[GPU Mem] Allocated {alloc:.2f} GB | "
          f"Reserved {reserved:.2f} GB | "
          f"Free {free:.2f} GB / {total:.2f} GB total")


def device_info() -> dict:
    """Return device metadata dict — logged into result CSVs for reproducibility."""
    import platform
    info = {
        "device_type":     "cpu",
        "device_name":     "CPU",
        "cuda_available":  False,
        "cuda_version":    "N/A",
        "cudnn_version":   "N/A",
        "vram_gb":         0.0,
        "pytorch_version": torch.__version__,
        "python_platform": platform.platform(),
    }
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        info.update({
            "device_type":          "cuda",
            "device_name":          torch.cuda.get_device_name(0),
            "cuda_available":       True,
            "cuda_version":         torch.version.cuda,
            "cudnn_version":        str(torch.backends.cudnn.version()),
            "vram_gb":              round(props.total_memory / 1e9, 2),
            "gpu_sm_count":         props.multi_processor_count,
        })
    return info


# ── Self-test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  HFL Device Utility — Self Test")
    print("=" * 60)
    device = get_device()
    optimize_gpu()
    gpu_memory_info()
    set_seed(42)
    dl_kwargs = get_dataloader_kwargs(device)
    print(f"[DataLoader] kwargs: {dl_kwargs}")
    print(f"\nDevice info:")
    for k, v in device_info().items():
        print(f"  {k:<22}: {v}")
    print("=" * 60)
