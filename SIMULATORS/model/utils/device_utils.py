"""
device_utils.py — GPU/CPU Auto-Select + Optimization
"""

import os
import torch


def get_device(verbose: bool = True) -> torch.device:
    if torch.cuda.is_available():
        device = torch.device("cuda")
        if verbose:
            props = torch.cuda.get_device_properties(0)
            vram  = props.total_memory / 1e9
            print(f"[Device] GPU  : {torch.cuda.get_device_name(0)}")
            print(f"[Device] VRAM : {vram:.1f} GB  |  CUDA {torch.version.cuda}")
    else:
        device = torch.device("cpu")
        if verbose:
            import multiprocessing
            print(f"[Device] CPU fallback — {multiprocessing.cpu_count()} cores")
    return device


def optimize_gpu(memory_fraction: float = 0.95) -> None:
    if not torch.cuda.is_available():
        return
    torch.backends.cudnn.benchmark        = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32       = True
    torch.cuda.set_per_process_memory_fraction(memory_fraction, device=0)
    torch.cuda.empty_cache()
    print(f"[GPU Opt] cuDNN benchmark=True | TF32=True | mem={memory_fraction}")


def get_dataloader_kwargs(device: torch.device) -> dict:
    # Per-device splits here are small (400-930 samples/device) and fully
    # resident in RAM as tensors (HealthcareDataset materialises the mmap in
    # __init__), so __getitem__ is a trivial tensor index. Under Opacus the
    # loader is re-wrapped into a Poisson DPDataLoader ~30×/round, and with
    # num_workers>0 that respawns worker processes each time — pure IPC/spawn
    # overhead that starves the GPU (observed 31% util / 1200MHz). Default to
    # 0 workers (main-process loading, no spawn) for this in-RAM regime.
    # Override with HFL_NUM_WORKERS to A/B test (e.g. HFL_NUM_WORKERS=2).
    n_workers = int(os.environ.get("HFL_NUM_WORKERS", "0"))
    if device.type == "cuda":
        kw = {"num_workers": n_workers, "pin_memory": True}
        if n_workers > 0:
            kw["persistent_workers"] = True  # avoid per-epoch respawn if workers are used
        return kw
    return {"num_workers": 0, "pin_memory": False}


def to_device(obj, device: torch.device, non_blocking: bool = True):
    if device.type == "cuda":
        return obj.to(device, non_blocking=non_blocking)
    return obj.to(device)


def set_seed(seed: int = 42) -> None:
    import random, numpy as np
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def gpu_memory_info() -> None:
    if not torch.cuda.is_available():
        return
    alloc    = torch.cuda.memory_allocated(0) / 1e9
    reserved = torch.cuda.memory_reserved(0)  / 1e9
    total    = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"[GPU Mem] Allocated {alloc:.2f} GB | Reserved {reserved:.2f} GB | "
          f"Free {total - reserved:.2f} GB / {total:.2f} GB total")


def device_info() -> dict:
    """Device metadata, logged into result CSVs for reproducibility.

    Keys are always present (filled with CPU-safe defaults) so a CSV written
    on a CPU box has the same columns as one written on the GPU box — a
    reader must not have to branch on which machine produced a row.
    """
    import platform
    info = {"device_type": "cpu", "device_name": "CPU",
            "cuda_available": False, "cuda_version": "N/A",
            "cudnn_version": "N/A", "vram_gb": 0.0, "gpu_sm_count": 0,
            "pytorch_version": torch.__version__,
            "python_platform": platform.platform()}
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        info.update({
            "device_type": "cuda",
            "device_name": torch.cuda.get_device_name(0),
            "cuda_available": True,
            "cuda_version": torch.version.cuda,
            "cudnn_version": str(torch.backends.cudnn.version()),
            "vram_gb": round(props.total_memory / 1e9, 2),
            "gpu_sm_count": props.multi_processor_count,
        })
    return info
