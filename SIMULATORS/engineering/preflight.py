"""
preflight — fail-fast environment and data safety checks before a long run.

Catches the cheap-to-detect, expensive-to-hit-late problems: missing/empty
datasets, absent partition files, unwritable checkpoint paths, low disk, low
RAM headroom, and CUDA availability. Returns a structured report; the caller
decides whether a FAIL should abort. Read-only — never mutates anything.
"""

import os
import json
import shutil
from typing import List, Dict, Tuple

try:
    import numpy as np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False

try:
    import torch
    _HAS_TORCH = True
except Exception:
    _HAS_TORCH = False


# status levels
OK, WARN, FAIL = "OK", "WARN", "FAIL"


def _check(name: str, status: str, detail: str) -> Dict[str, str]:
    return {"check": name, "status": status, "detail": detail}


def _dataset_checks(data_dir: str) -> List[Dict[str, str]]:
    out = []
    expected = {
        "ecg/ecg_signals.npy":      (3,),   # [N,12,1000]
        "ecg/ecg_labels.npy":       (1,),
        "cxr/cxr_images.npy":       (4,),   # [N,3,224,224]
        "cxr/cxr_labels.npy":       (1,),
        "tabular/tabular_features.npy": (2,),
    }
    for rel, dims in expected.items():
        path = os.path.join(data_dir, rel)
        if not os.path.exists(path):
            out.append(_check(f"dataset:{rel}", FAIL, f"missing at {path}"))
            continue
        if os.path.getsize(path) == 0:
            out.append(_check(f"dataset:{rel}", FAIL, "file is empty"))
            continue
        if _HAS_NUMPY:
            try:
                arr = np.load(path, mmap_mode="r")
                if arr.ndim not in dims:
                    out.append(_check(f"dataset:{rel}", WARN,
                                      f"ndim={arr.ndim}, expected {dims}, "
                                      f"shape={tuple(arr.shape)}"))
                else:
                    out.append(_check(f"dataset:{rel}", OK,
                                      f"shape={tuple(arr.shape)} {arr.dtype}"))
            except Exception as e:
                out.append(_check(f"dataset:{rel}", FAIL, f"unreadable: {e}"))
        else:
            out.append(_check(f"dataset:{rel}", OK, "present (numpy absent, "
                                                    "shape unchecked)"))
    return out


def _partition_checks(part_dir: str, n_devices: int) -> List[Dict[str, str]]:
    out = []
    meta = os.path.join(part_dir, "partition_meta.json")
    if not os.path.exists(meta):
        out.append(_check("partition:meta", FAIL, f"missing at {meta}"))
    else:
        try:
            with open(meta) as f:
                json.load(f)
            out.append(_check("partition:meta", OK, "valid JSON"))
        except Exception as e:
            out.append(_check("partition:meta", FAIL, f"invalid JSON: {e}"))
    missing = []
    for d in range(n_devices):
        for split in ("train", "val", "test"):
            p = os.path.join(part_dir, f"device_{d:02d}_{split}.npy")
            if not os.path.exists(p):
                missing.append(os.path.basename(p))
    if missing:
        out.append(_check("partition:index_files", FAIL,
                          f"{len(missing)} missing: {missing[:4]}..."))
    else:
        out.append(_check("partition:index_files", OK,
                          f"{n_devices}×3 index files present"))
    return out


def _writable_dir_check(name: str, path: str) -> Dict[str, str]:
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".preflight_write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        return _check(name, OK, f"writable: {path}")
    except OSError as e:
        return _check(name, FAIL, f"not writable ({path}): {e}")


def run_preflight(data_dir: str,
                  part_dir: str,
                  checkpoint_dir: str = "checkpoints",
                  results_dir: str = "results",
                  n_devices: int = 6,
                  min_disk_gb: float = 5.0,
                  min_ram_gb: float = 3.0,
                  require_cuda: bool = False) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Run all checks. Returns (ok, report). ok is False if any check is FAIL.
    WARN items do not fail the run but are surfaced to the caller/log.
    """
    report: List[Dict[str, str]] = []

    # CUDA
    if _HAS_TORCH and torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        report.append(_check("cuda", OK, f"{name}, {vram:.1f} GB VRAM"))
    else:
        report.append(_check("cuda", FAIL if require_cuda else WARN,
                             "CUDA not available — training will use CPU"))

    # Disk
    try:
        free_gb = shutil.disk_usage(os.path.abspath(results_dir) if
                                    os.path.exists(results_dir) else ".").free / 1e9
        report.append(_check("disk", OK if free_gb >= min_disk_gb else FAIL,
                             f"{free_gb:.1f} GB free (need ≥ {min_disk_gb})"))
    except OSError as e:
        report.append(_check("disk", WARN, f"could not stat disk: {e}"))

    # RAM headroom
    try:
        with open("/proc/meminfo") as f:
            avail_kb = next(int(l.split()[1]) for l in f
                            if l.startswith("MemAvailable:"))
        avail_gb = avail_kb / (1024 ** 2)
        report.append(_check("ram", OK if avail_gb >= min_ram_gb else WARN,
                             f"{avail_gb:.1f} GB available (want ≥ {min_ram_gb})"))
    except (OSError, StopIteration, ValueError):
        report.append(_check("ram", WARN, "could not read /proc/meminfo"))

    # Data + partitions + writable dirs
    report += _dataset_checks(data_dir)
    report += _partition_checks(part_dir, n_devices)
    report.append(_writable_dir_check("checkpoint_dir", checkpoint_dir))
    report.append(_writable_dir_check("results_dir", results_dir))

    ok = all(r["status"] != FAIL for r in report)
    return ok, report


def format_report(report: List[Dict[str, str]]) -> str:
    icon = {OK: "✓", WARN: "!", FAIL: "✗"}
    lines = ["Preflight checks:"]
    for r in report:
        lines.append(f"  [{icon.get(r['status'], '?')}] "
                     f"{r['check']:<28} {r['detail']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="HFL preflight checks")
    p.add_argument("--data_dir", default="data/processed/healthcare")
    p.add_argument("--part_dir", default="data/processed/partitions/healthcare")
    p.add_argument("--checkpoint_dir", default="checkpoints")
    p.add_argument("--results_dir", default="results")
    p.add_argument("--n_devices", type=int, default=6)
    p.add_argument("--require_cuda", action="store_true")
    a = p.parse_args()
    ok, rep = run_preflight(a.data_dir, a.part_dir, a.checkpoint_dir,
                            a.results_dir, a.n_devices,
                            require_cuda=a.require_cuda)
    print(format_report(rep))
    print("\nPREFLIGHT:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
