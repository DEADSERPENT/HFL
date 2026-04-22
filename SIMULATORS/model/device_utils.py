"""
device_utils.py — re-export from scripts/device_utils.py
Model files import from here (same directory); scripts import from scripts/.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from device_utils import (
    get_device,
    optimize_gpu,
    get_dataloader_kwargs,
    to_device,
    set_seed,
    gpu_memory_info,
    device_info,
)
__all__ = [
    "get_device", "optimize_gpu", "get_dataloader_kwargs",
    "to_device", "set_seed", "gpu_memory_info", "device_info",
]
