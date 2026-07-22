"""
Engineering hardening utilities for the HFL pipeline.

Dependency-free (stdlib + torch/numpy only) so it never adds install burden
to the research environment. Nothing here changes numerical behavior — these
modules only add observability, safety checks, reproducibility, and logging.

Modules
-------
sysmon    : resource sampling + ResourceMonitor background watchdog
preflight : pre-run environment / dataset / disk safety checks
runctx    : structured logging, experiment metadata, seed management
"""

from .sysmon import sample_resources, ResourceMonitor
from .preflight import run_preflight
from .runctx import setup_logging, capture_metadata, set_global_seed

__all__ = [
    "sample_resources", "ResourceMonitor",
    "run_preflight",
    "setup_logging", "capture_metadata", "set_global_seed",
]
