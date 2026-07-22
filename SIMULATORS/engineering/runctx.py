"""
runctx — structured logging, experiment metadata, and seed management.

- setup_logging: one logger writing to both console and a timestamped file,
  with a consistent structured format. Idempotent (no duplicate handlers).
- capture_metadata: snapshot git commit, config, seed, device, and package
  versions to a JSON file for reproducibility / experiment tracking.
- set_global_seed: seed python/numpy/torch (+CUDA). Optional deterministic
  mode is OFF by default because full determinism can change kernel selection
  and throughput — seeding alone does not alter the algorithm, only fixes the
  RNG stream so a run is reproducible.
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any


# ── Logging ─────────────────────────────────────────────────────────────────

def setup_logging(log_dir: str = "logs",
                  name: str = "hfl",
                  level: int = logging.INFO,
                  to_file: bool = True) -> logging.Logger:
    """Return a logger with console + rotating-per-run file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Idempotent: don't stack handlers if called twice in one process.
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if to_file:
        os.makedirs(log_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fh = logging.FileHandler(os.path.join(log_dir, f"{name}_{stamp}.log"))
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# ── Metadata ────────────────────────────────────────────────────────────────

def _git_info() -> Dict[str, Any]:
    def _run(args):
        try:
            return subprocess.check_output(args, stderr=subprocess.DEVNULL,
                                           text=True).strip()
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return None
    sha = _run(["git", "rev-parse", "--short", "HEAD"])
    dirty = _run(["git", "status", "--porcelain"])
    return {"commit": sha,
            "dirty": bool(dirty) if dirty is not None else None}


def _device_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {"cuda_available": False}
    try:
        import torch
        info["torch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["device_name"] = torch.cuda.get_device_name(0)
            info["cuda_version"] = torch.version.cuda
            info["vram_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1e9, 2)
    except Exception:
        pass
    return info


def _package_versions() -> Dict[str, str]:
    import importlib.metadata as md
    out = {}
    for pkg in ("torch", "numpy", "pandas", "scipy", "opacus",
                "onnxruntime", "scikit-learn", "torchvision"):
        try:
            out[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            pass
    return out


def capture_metadata(config: Dict[str, Any],
                     seed: Optional[int] = None,
                     out_path: Optional[str] = None,
                     extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Assemble a reproducibility metadata dict and optionally write JSON."""
    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "seed": seed,
        "git": _git_info(),
        "device": _device_info(),
        "packages": _package_versions(),
        "python": sys.version.split()[0],
        "argv": sys.argv,
        "config": config,
    }
    if extra:
        meta["extra"] = extra
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(meta, f, indent=2, default=str)
    return meta


# ── Seeding ─────────────────────────────────────────────────────────────────

def set_global_seed(seed: int = 42, deterministic: bool = False) -> None:
    """
    Seed python/numpy/torch(+CUDA). Seeding only fixes the RNG stream; it does
    not change the training algorithm. `deterministic=True` additionally forces
    deterministic cuDNN/algorithms — this can slow training and error on ops
    without deterministic kernels, so it is opt-in.
    """
    import random
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
            try:
                torch.use_deterministic_algorithms(True, warn_only=True)
            except Exception:
                pass
    except Exception:
        pass


if __name__ == "__main__":
    log = setup_logging(name="runctx_selftest", to_file=False)
    set_global_seed(123)
    meta = capture_metadata({"demo": True}, seed=123)
    log.info("metadata keys: %s", list(meta.keys()))
    log.info("git: %s | device cuda=%s", meta["git"], meta["device"]["cuda_available"])
