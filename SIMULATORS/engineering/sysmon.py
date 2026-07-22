"""
sysmon — dependency-free resource sampling + background watchdog.

Samples process RSS, system RAM, CPU load, GPU VRAM, and disk free space
using only /proc, os, shutil, and torch (no psutil). The ResourceMonitor runs
a single daemon thread that samples on an interval, logs early warnings when
resources approach danger thresholds, and streams samples to a CSV so memory
stays bounded even over multi-hour runs.

This module is observability-only: it never mutates training state.
"""

import os
import csv
import time
import shutil
import threading
from typing import Optional, Dict

try:
    import torch
    _HAS_TORCH = True
except Exception:                     # torch optional for pure-CPU contexts
    _HAS_TORCH = False


# ── Low-level readers ───────────────────────────────────────────────────────

def _read_proc_rss_gb() -> float:
    """Resident set size of this process, in GB (Linux /proc)."""
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / (1024 ** 2)   # kB → GB
    except (OSError, ValueError):
        pass
    return float("nan")


def _read_sys_mem_gb() -> Dict[str, float]:
    """System RAM total/available in GB (Linux /proc/meminfo)."""
    total = avail = float("nan")
    try:
        with open("/proc/meminfo") as f:
            vals = {}
            for line in f:
                k, _, rest = line.partition(":")
                vals[k] = int(rest.split()[0])          # kB
        total = vals.get("MemTotal", 0) / (1024 ** 2)
        avail = vals.get("MemAvailable", 0) / (1024 ** 2)
    except (OSError, ValueError):
        pass
    return {"total_gb": total, "avail_gb": avail}


def _read_vram_gb() -> Dict[str, float]:
    """Torch process VRAM allocated/reserved and device total, in GB."""
    if not (_HAS_TORCH and torch.cuda.is_available()):
        return {"alloc_gb": 0.0, "reserved_gb": 0.0, "total_gb": 0.0}
    try:
        total = torch.cuda.get_device_properties(0).total_memory / 1e9
        return {
            "alloc_gb":    torch.cuda.memory_allocated(0) / 1e9,
            "reserved_gb": torch.cuda.memory_reserved(0) / 1e9,
            "total_gb":    total,
        }
    except Exception:
        return {"alloc_gb": 0.0, "reserved_gb": 0.0, "total_gb": 0.0}


def _read_cpu_load() -> float:
    """1-minute load average normalized per core (1.0 == fully loaded)."""
    try:
        return os.getloadavg()[0] / max(os.cpu_count() or 1, 1)
    except (OSError, AttributeError):
        return float("nan")


def _read_disk_free_gb(path: str) -> float:
    try:
        return shutil.disk_usage(path).free / 1e9
    except OSError:
        return float("nan")


def sample_resources(disk_path: str = ".") -> Dict[str, float]:
    """One-shot snapshot of all tracked resources."""
    mem = _read_sys_mem_gb()
    vram = _read_vram_gb()
    return {
        "t":              time.time(),
        "rss_gb":         _read_proc_rss_gb(),
        "sys_ram_avail_gb": mem["avail_gb"],
        "sys_ram_total_gb": mem["total_gb"],
        "cpu_load_norm":  _read_cpu_load(),
        "vram_alloc_gb":  vram["alloc_gb"],
        "vram_reserved_gb": vram["reserved_gb"],
        "vram_total_gb":  vram["total_gb"],
        "disk_free_gb":   _read_disk_free_gb(disk_path),
    }


# ── Background watchdog ──────────────────────────────────────────────────────

class ResourceMonitor:
    """
    Background resource watchdog. Use as a context manager:

        with ResourceMonitor(csv_path="results/monitoring/run.csv",
                              logger=log) as mon:
            train(...)
        print(mon.summary())      # peak RSS / VRAM, min free RAM/disk

    Early-warning: logs a (rate-limited) WARNING when system RAM available
    drops below `min_ram_gb`, VRAM reservation exceeds `max_vram_frac` of the
    device, or disk free drops below `min_disk_gb`. Warnings are advisory —
    the monitor never kills or throttles the training process itself.
    """

    def __init__(self,
                 csv_path: Optional[str] = None,
                 interval_s: float = 5.0,
                 disk_path: str = ".",
                 min_ram_gb: float = 1.5,
                 max_vram_frac: float = 0.95,
                 min_disk_gb: float = 2.0,
                 logger=None,
                 warn_cooldown_s: float = 30.0):
        self.csv_path = csv_path
        self.interval_s = max(0.5, interval_s)
        self.disk_path = disk_path
        self.min_ram_gb = min_ram_gb
        self.max_vram_frac = max_vram_frac
        self.min_disk_gb = min_disk_gb
        self.logger = logger
        self.warn_cooldown_s = warn_cooldown_s

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_warn: Dict[str, float] = {}
        self._peak = {
            "rss_gb": 0.0, "vram_reserved_gb": 0.0,
            "min_ram_avail_gb": float("inf"), "min_disk_free_gb": float("inf"),
            "n_samples": 0,
        }
        self._csv_file = None
        self._csv_writer = None

    # -- logging helpers --
    def _log(self, level: str, msg: str):
        if self.logger is not None:
            getattr(self.logger, level, self.logger.info)(msg)
        else:
            print(f"[sysmon:{level.upper()}] {msg}", flush=True)

    def _warn_ratelimited(self, key: str, msg: str):
        now = time.time()
        if now - self._last_warn.get(key, 0.0) >= self.warn_cooldown_s:
            self._last_warn[key] = now
            self._log("warning", msg)

    # -- sampling loop --
    def _check_thresholds(self, s: Dict[str, float]):
        if s["sys_ram_avail_gb"] == s["sys_ram_avail_gb"] and \
                s["sys_ram_avail_gb"] < self.min_ram_gb:
            self._warn_ratelimited(
                "ram", f"System RAM low: {s['sys_ram_avail_gb']:.2f} GB "
                       f"available (< {self.min_ram_gb} GB). OOM risk.")
        if s["vram_total_gb"] > 0:
            frac = s["vram_reserved_gb"] / s["vram_total_gb"]
            if frac > self.max_vram_frac:
                self._warn_ratelimited(
                    "vram", f"VRAM high: {s['vram_reserved_gb']:.2f}/"
                            f"{s['vram_total_gb']:.2f} GB reserved "
                            f"({frac*100:.0f}%).")
        if s["disk_free_gb"] == s["disk_free_gb"] and \
                s["disk_free_gb"] < self.min_disk_gb:
            self._warn_ratelimited(
                "disk", f"Disk low: {s['disk_free_gb']:.2f} GB free "
                        f"(< {self.min_disk_gb} GB).")

    def _update_peak(self, s: Dict[str, float]):
        p = self._peak
        if s["rss_gb"] == s["rss_gb"]:
            p["rss_gb"] = max(p["rss_gb"], s["rss_gb"])
        p["vram_reserved_gb"] = max(p["vram_reserved_gb"], s["vram_reserved_gb"])
        if s["sys_ram_avail_gb"] == s["sys_ram_avail_gb"]:
            p["min_ram_avail_gb"] = min(p["min_ram_avail_gb"], s["sys_ram_avail_gb"])
        if s["disk_free_gb"] == s["disk_free_gb"]:
            p["min_disk_free_gb"] = min(p["min_disk_free_gb"], s["disk_free_gb"])
        p["n_samples"] += 1

    def _loop(self):
        while not self._stop.is_set():
            s = sample_resources(self.disk_path)
            self._update_peak(s)
            self._check_thresholds(s)
            if self._csv_writer is not None:
                try:
                    self._csv_writer.writerow(s)
                    self._csv_file.flush()
                except (ValueError, OSError):
                    pass
            # Event.wait so stop() interrupts sleep immediately (no lag on exit)
            self._stop.wait(self.interval_s)

    # -- lifecycle --
    def start(self):
        if self.csv_path:
            os.makedirs(os.path.dirname(self.csv_path) or ".", exist_ok=True)
            self._csv_file = open(self.csv_path, "w", newline="")
            fields = list(sample_resources(self.disk_path).keys())
            self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=fields)
            self._csv_writer.writeheader()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="ResourceMonitor")
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval_s + 5.0)
            self._thread = None
        if self._csv_file is not None:
            try:
                self._csv_file.close()
            finally:
                self._csv_file = None
                self._csv_writer = None

    def summary(self) -> Dict[str, float]:
        p = dict(self._peak)
        if p["min_ram_avail_gb"] == float("inf"):
            p["min_ram_avail_gb"] = float("nan")
        if p["min_disk_free_gb"] == float("inf"):
            p["min_disk_free_gb"] = float("nan")
        return p

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False                  # never suppress exceptions


if __name__ == "__main__":
    # Self-test: sample once, then run the monitor for a few seconds.
    print("One-shot sample:")
    for k, v in sample_resources(".").items():
        print(f"  {k:20} {v}")
    print("\nMonitor 3s @1s interval:")
    with ResourceMonitor(interval_s=1.0) as m:
        time.sleep(3.2)
    print("Summary:", m.summary())
