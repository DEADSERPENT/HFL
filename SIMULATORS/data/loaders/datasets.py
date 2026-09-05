"""
datasets.py — dataset registry for the HFL-MM stack.

One entry per dataset. Each entry owns its paths, its client count, its class
count and its modality-B contract; the loading code itself lives in that
dataset's OWN module (`wear_dataset.py`, `vitaldb_dataset.py`) and is imported
lazily, so the datasets stay fully separate and adding one never touches
`hfl_trainer.py`.

    ┌───────────────┬──────────────────────────────────────┬─────────────────┐
    │ wear          │ accelerometer + egocentric I3D video  │ fast iteration   │
    │ vitaldb       │ intraop vitals + preop clinical/labs  │ primary research │
    │ eicu          │ ICU vitals + admission clinical       │ external validation │
    └───────────────┴──────────────────────────────────────┴─────────────────┘

Use `wear` for quick iteration and `vitaldb` for the headline results.

The former `healthcare` entry (ECG + chest X-ray) was removed: its two
modalities were paired by a RULE (CXR bucket = f(ECG label)) rather than by
provenance, so no result computed on it was evidence of multimodal fusion.
Every dataset in this registry is now genuinely paired at source.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    data_dir: str
    partition_dir: str
    n_devices: int
    n_classes: int
    n_channels_a: int                # input channels for encoder_a
    modality_b: str                  # "image" | "features"  → HFLMMHC(modality_b=)
    feat_b_dim: Optional[int]        # required when modality_b == "features"
    modality_a_desc: str
    modality_b_desc: str
    pairing: str                     # how the two modalities were paired
    required_files: dict = field(default_factory=dict)
    # Arrays that are POOLS indexed indirectly rather than one row per sample,
    # and so are legitimately shorter than the label array. No current dataset
    # uses this — both are paired at source, one row per sample — but the
    # field is kept because the validators consult it.
    # True when the second half of modality A's channels are binary
    # observed-masks paired with the first half. Verifiers check mask
    # integrity only for such corpora; testing `spec.name == "vitaldb"`
    # instead silently skipped every corpus added afterwards.
    has_mask_channels: bool = False
    pool_files: frozenset = frozenset()
    build_full: Callable = field(repr=False, default=None)
    notes: str = ""

    def describe(self) -> str:
        return (f"[dataset] {self.name}: {self.n_devices} clients, "
                f"{self.n_classes} classes\n"
                f"          A: {self.modality_a_desc}\n"
                f"          B: {self.modality_b_desc}\n"
                f"          pairing: {self.pairing}")


# ── lazy builders (import inside, so an unused dataset costs nothing) ───────

def _build_wear(processed_dir: str):
    from wear_dataset import build_full_wear_dataset
    return build_full_wear_dataset(processed_dir)


def _build_vitaldb(processed_dir: str):
    from vitaldb_dataset import build_full_vitaldb_dataset
    return build_full_vitaldb_dataset(processed_dir)


def _build_eicu(processed_dir: str):
    from eicu_dataset import build_full_eicu_dataset
    return build_full_eicu_dataset(processed_dir)


def _meta(rel: str, key: str, default):
    """Resolve a shape from the corpus's own dataset_meta.json when it exists.

    n_devices for eICU is the number of hospitals surviving the minimum-size
    filter, which is a property of the built corpus rather than something that
    can be declared in advance. Reading it here keeps the registry free of a
    number that would silently go stale after a rebuild.
    """
    import json as _json
    from pathlib import Path as _Path
    _here = _Path(__file__).resolve().parents[2]      # -> SIMULATORS/
    _p = _here / rel / "meta" / "dataset_meta.json"
    try:
        with open(_p) as _f:
            return _json.load(_f).get(key, default)
    except (OSError, ValueError):
        return default


# ── registry ────────────────────────────────────────────────────────────────

REGISTRY = {
    "wear": DatasetSpec(
        name="wear",
        data_dir="data/processed/wear",
        partition_dir="data/processed/partitions/wear",
        n_devices=22, n_classes=18, n_channels_a=12,
        modality_b="features", feat_b_dim=2048,
        modality_a_desc="12-ch accelerometer (4 sensors x 3 axes), 2 s @ 50 Hz",
        modality_b_desc="2048-d two-stream I3D egocentric-video features, same 2 s",
        pairing="HARDWARE-SYNCHRONISED (same person, same instant)",
        required_files={"inertial/inertial_windows.npy": (3,),   # [N,12,W]
                        "inertial/labels.npy": (1,),
                        "video/i3d_features.npy": (2,)},          # [N,2048]
        build_full=_build_wear,
        notes="Fast-iteration domain: wearable IoT. Bock et al., IMWUT 2024.",
    ),
    "vitaldb": DatasetSpec(
        name="vitaldb",
        data_dir="data/processed/vitaldb",
        partition_dir="data/processed/partitions/vitaldb",
        n_devices=9, n_classes=2, n_channels_a=18,
        modality_b="features", feat_b_dim=34,
        modality_a_desc="9 intraop numeric trends + 9 observed-masks, 10 min @0.5 Hz",
        modality_b_desc="34-d preoperative clinical + laboratory vector",
        pairing="SAME PATIENT, SAME SECOND (Vital Recorder, one operation)",
        has_mask_channels=True,
        required_files={"signals/windows.npy": (3,),      # [N,18,W]
                        "signals/labels.npy": (1,),
                        "clinical/features.npy": (2,)},   # [N,34]
        build_full=_build_vitaldb,
        notes="PRIMARY research domain: clinical IoMT. Label = postoperative "
              "ICU admission (19.7% of windows). Clients = surgical optype, "
              "low-acuity types merged so every client has >=10 positive "
              "cases; ICU base rate 3.2%-50.7% => genuinely non-IID. "
              "Lee et al., Sci Data 2022.",
    ),
    "eicu": DatasetSpec(
        name="eicu",
        data_dir="data/processed/eicu",
        partition_dir="data/processed/partitions/eicu",
        n_devices=_meta("data/processed/eicu", "n_clients", 0),
        n_classes=2,
        n_channels_a=_meta("data/processed/eicu", "n_channels_a", 12),
        modality_b="features",
        feat_b_dim=_meta("data/processed/eicu", "feat_b_dim", 5),
        modality_a_desc="6 ICU vital trends + 6 observed-masks, 60 min @12 slots",
        modality_b_desc="5-d admission clinical vector (age, sex, wt, ht, APACHE)",
        pairing="SAME STAY (patientunitstayid); tabular is admission-time only",
        has_mask_channels=True,
        required_files={"vitals/windows.npy": (3,),      # [N,12,T]
                        "vitals/labels.npy": (1,),
                        "tabular/features.npy": (2,)},   # [N,5]
        build_full=_build_eicu,
        notes="EXTERNAL VALIDATION corpus: multi-centre ICU. Label = in-unit "
              "mortality. Clients = REAL HOSPITALS (hospitalid), taken as "
              "given rather than constructed, hospitals under 200 windows "
              "pooled. Individual = uniquepid (the person), not the stay: a "
              "patient may be admitted more than once. Pollard et al., Sci "
              "Data 2018. n_devices/feat_b_dim resolve from dataset_meta.json "
              "after the build.",
    ),
}


def window_len(spec: "DatasetSpec", default: int = 100) -> int:
    """Length of modality A's time axis, read off the array on disk.

    `onnx_exporter.py` previously carried `{"wear": 100, "vitaldb": 300}` and
    defaulted anything else to 100. eICU's windows are 12 slots, so a new
    corpus would have exported a wrongly shaped graph — the same class of
    defect that file's own docstring records having already been fixed once.
    Reading the shape cannot go stale.
    """
    import numpy as _np
    from pathlib import Path as _Path
    _here = _Path(__file__).resolve().parents[2]      # -> SIMULATORS/
    for rel, dims in (spec.required_files or {}).items():
        if dims and dims[0] == 3:
            try:
                return int(_np.load(_here / spec.data_dir / rel,
                                    mmap_mode="r").shape[-1])
            except (OSError, ValueError):
                continue
    return default


def get_spec(name: str) -> DatasetSpec:
    if name not in REGISTRY:
        raise KeyError(f"unknown dataset {name!r}; available: {sorted(REGISTRY)}")
    return REGISTRY[name]
