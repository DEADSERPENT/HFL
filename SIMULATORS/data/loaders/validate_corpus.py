"""
validate_corpus.py — does a corpus support the claims this study makes?

Run this BEFORE integrating a new dataset, and before trusting one already
integrated. It answers two different questions, and keeps them apart:

  INTEGRITY  is the data built correctly? (pairing, alignment, leakage)
             A failure here invalidates any result computed from the corpus.

  CAPACITY   can this corpus evidence the claims at all?
             A failure here is not a bug. It means some claim cannot be made
             on this data and must not be attempted.

WHY THIS EXISTS
---------------
`wear` was fully integrated, partitioned, pretrained and evaluated before it
emerged that it cannot corroborate a single core claim: each client is one
participant, so client-level and individual-level DP coincide; there are 22
individuals where patient-level membership inference needs 600 members and 600
non-members; and its better single modality already reaches 0.9976 AUROC, so
fusion has no headroom to demonstrate anything. Every one of those is
computable from the arrays in minutes. Discovering them after the fact cost
weeks and produced a table of results that cannot be used.

The split-leakage check exists for a different reason: nothing in preflight
verifies that an individual appears in only one split. Windows from one patient
are highly correlated, so a patient spanning train and test inflates every
utility figure in the paper, and it fails silently — the run completes, the
numbers merely become wrong.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

_LOADERS = Path(__file__).resolve().parent
sys.path.insert(0, str(_LOADERS))
from datasets import get_spec, REGISTRY                      # noqa: E402

_SIM = _LOADERS.parent.parent

OK, WARN, FAIL = "ok  ", "WARN", "FAIL"

# Thresholds are stated here, with the claim each one gates, so that a corpus
# is judged against what the paper needs rather than against a feeling.
MIN_INDIVIDUALS_MIA = 1200      # patient-level LiRA uses 600 members + 600 non
MIN_RECORDS_PER_IND = 2.0       # k-scaling needs something to vary
CEILING_AUROC = 0.95            # above this, fusion has no headroom to show


class Report:
    def __init__(self):
        self.rows = []
        self.worst = 0

    def add(self, kind, name, status, detail):
        self.rows.append((kind, name, status, detail))
        self.worst = max(self.worst, {OK: 0, WARN: 1, FAIL: 2}[status])

    def show(self):
        for kind in ("INTEGRITY", "CAPACITY"):
            rows = [r for r in self.rows if r[0] == kind]
            if not rows:
                continue
            print(f"\n  {kind}")
            print("  " + "-" * 74)
            for _, name, status, detail in rows:
                print(f"  [{status}] {name:<28} {detail}")
        return self.worst


def _load_group_ids(spec, processed: Path):
    """Per-sample individual identity, aligned to labels.

    Every claim about individuals — patient-level DP, the MIA, k-scaling,
    case-level metrics — keys on this. A corpus without it can carry none of
    them.
    """
    for cand in ("meta/case_ids.npy", "meta/group_ids.npy",
                 "meta/subject_ids.npy", "meta/patient_ids.npy"):
        p = processed / cand
        if p.exists():
            return np.load(p), cand
    return None, None


def validate(name: str, rep: Report):
    spec = get_spec(name)
    processed = _SIM / spec.data_dir
    partdir = _SIM / spec.partition_dir

    # ── integrity: files, shapes, pairing ───────────────────────────────
    shapes = {}
    for rel in spec.required_files:
        p = processed / rel
        if not p.exists():
            rep.add("INTEGRITY", "files", FAIL, f"missing {rel}")
            return
        shapes[rel] = np.load(p, mmap_mode="r").shape
    n = {rel: s[0] for rel, s in shapes.items() if rel not in spec.pool_files}
    if len(set(n.values())) == 1:
        rep.add("INTEGRITY", "pairing (one row/sample)", OK,
                f"all arrays agree at N={next(iter(n.values())):,}")
    else:
        rep.add("INTEGRITY", "pairing (one row/sample)", FAIL,
                f"row counts disagree: {n} — modalities are not paired at "
                f"source, or an array is a pool")
    N = max(n.values())

    gids, src = _load_group_ids(spec, processed)
    if gids is None:
        rep.add("INTEGRITY", "individual identity", FAIL,
                "no case/group/subject id array under meta/ — patient-level "
                "DP, MIA and k-scaling are all impossible")
    elif len(gids) != N:
        rep.add("INTEGRITY", "individual identity", FAIL,
                f"{src} has {len(gids):,} entries against N={N:,}")
    else:
        rep.add("INTEGRITY", "individual identity", OK,
                f"{src}, {len(np.unique(gids)):,} unique")

    # ── integrity: split leakage, the silent one ────────────────────────
    meta_p = partdir / "partition_meta.json"
    if not meta_p.exists():
        rep.add("INTEGRITY", "partition", FAIL, f"missing {meta_p}")
        return
    meta = json.loads(meta_p.read_text())
    n_dev = meta["n_devices"]

    splits = {}
    for split in ("train", "val", "test"):
        idx = []
        for d in range(n_dev):
            f = partdir / f"device_{d:02d}_{split}.npy"
            if f.exists():
                idx.append(np.load(f))
        splits[split] = np.concatenate(idx) if idx else np.array([], int)

    total = sum(len(v) for v in splits.values())
    dup = total - len(np.unique(np.concatenate(list(splits.values()))))
    rep.add("INTEGRITY", "sample-level overlap", OK if dup == 0 else FAIL,
            f"{dup} sample(s) appear in more than one split")

    if gids is not None and len(gids) == N:
        gs = {k: set(np.unique(gids[v])) for k, v in splits.items() if len(v)}
        bad = []
        for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
            if a in gs and b in gs:
                shared = gs[a] & gs[b]
                if shared:
                    bad.append(f"{a}/{b}:{len(shared)}")

        if not bad:
            rep.add("INTEGRITY", "leakage control", OK,
                    "splits are individual-disjoint")
        else:
            # An individual spanning splits is NOT automatically leakage. A
            # corpus with few individuals cannot hold out whole individuals and
            # still represent every class, so the legitimate alternative is a
            # split that is temporal WITHIN each individual, with a gap dropped
            # at the boundary. `wear` does exactly that by design. Flagging it
            # as leakage would condemn valid results, so check for the
            # alternative control before failing: under a temporal split, an
            # individual's training rows precede its test rows in storage
            # order, which is time order for a windowed recording.
            # Granularity matters: a temporal split may be taken within
            # (individual, class) rather than within individual, so that every
            # class survives in every split. Checking per individual alone
            # would miss it — one class's training rows can follow another
            # class's test rows in storage order while each class is still
            # correctly ordered internally. `wear` is exactly this case.
            labels = None
            for rel, dims in spec.required_files.items():
                if dims == (1,) and (processed / rel).exists():
                    labels = np.load(processed / rel)
                    break
            tr, te = splits.get("train"), splits.get("test")
            ordered = spanning = 0
            if tr is not None and te is not None and len(tr) and len(te):
                keys_tr = (list(zip(gids[tr], labels[tr])) if labels is not None
                           else list(zip(gids[tr], np.zeros(len(tr), int))))
                keys_te = (list(zip(gids[te], labels[te])) if labels is not None
                           else list(zip(gids[te], np.zeros(len(te), int))))
                ktr, kte = np.array(keys_tr), np.array(keys_te)
                common = {tuple(k) for k in ktr} & {tuple(k) for k in kte}
                for g, c in list(common)[:400]:
                    a_idx = tr[(gids[tr] == g) & ((labels[tr] == c)
                               if labels is not None else True)]
                    b_idx = te[(gids[te] == g) & ((labels[te] == c)
                               if labels is not None else True)]
                    if len(a_idx) and len(b_idx):
                        spanning += 1
                        ordered += int(a_idx.max() < b_idx.min())
            temporal = spanning and ordered / spanning >= 0.95
            rep.add("INTEGRITY", "leakage control",
                    WARN if temporal else FAIL,
                    (f"individuals span splits ({', '.join(bad)}) but "
                     f"{ordered}/{spanning} are time-ordered — consistent with "
                     f"a temporal within-individual split; confirm a boundary "
                     f"gap is dropped"
                     if temporal else
                     f"individuals span splits ({', '.join(bad)}) with no "
                     f"temporal ordering — correlated records leak and inflate "
                     f"every reported utility"))

    # ── capacity: can this corpus carry the claims? ─────────────────────
    if gids is not None and len(gids) == N:
        uniq = len(np.unique(gids))
        per = N / max(uniq, 1)
        rep.add("CAPACITY", "individuals", OK if uniq >= MIN_INDIVIDUALS_MIA
                else FAIL,
                f"{uniq:,} — patient-level MIA needs >= {MIN_INDIVIDUALS_MIA:,} "
                f"(600 members + 600 non-members)")
        rep.add("CAPACITY", "records per individual",
                OK if per >= MIN_RECORDS_PER_IND else FAIL,
                f"{per:.2f} — k-scaling and individual-level clipping need "
                f">= {MIN_RECORDS_PER_IND}")

        # The distinction the paper's central contribution rests on.
        dev_of = np.full(N, -1, int)
        for d in range(n_dev):
            for split in ("train", "val", "test"):
                f = partdir / f"device_{d:02d}_{split}.npy"
                if f.exists():
                    dev_of[np.load(f)] = d
        seen = dev_of >= 0
        if seen.any():
            per_client = [len(np.unique(gids[dev_of == d]))
                          for d in range(n_dev)]
            med = float(np.median(per_client))
            rep.add("CAPACITY", "individuals per client",
                    OK if med > 1 else FAIL,
                    f"median {med:.0f} — at 1, client-level and "
                    f"individual-level DP coincide and the unit contribution "
                    f"cannot be measured")

    # ── capacity: headroom for fusion ───────────────────────────────────
    abl = _SIM / "results" / "phase5" / f"ablation_{name}.json"
    if abl.exists():
        d = json.loads(abl.read_text())
        best = d.get("verdict", {}).get("best_unimodal_auroc")
        gain = d.get("fusion_gain_auroc")
        if best is not None:
            rep.add("CAPACITY", "fusion headroom",
                    OK if best < CEILING_AUROC else FAIL,
                    f"best single modality {best:.4f}, fusion gain "
                    f"{gain:+.4f} — above {CEILING_AUROC} there is no room "
                    f"for a second modality to demonstrate anything")
    else:
        rep.add("CAPACITY", "fusion headroom", WARN,
                f"not measured — run modality_ablation.py --dataset {name} "
                f"FIRST; it is the cheapest disqualifying test")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", nargs="+", default=sorted(REGISTRY))
    a = ap.parse_args()

    worst = 0
    for name in a.datasets:
        print("=" * 78)
        print(f"CORPUS VALIDATION — {name}")
        print("=" * 78)
        rep = Report()
        try:
            validate(name, rep)
        except Exception as e:
            rep.add("INTEGRITY", "validator", FAIL, f"{type(e).__name__}: {e}")
        worst = max(worst, rep.show())
        print()

    print("=" * 78)
    print("A CAPACITY failure is not a defect in the data. It means a claim "
          "cannot be\nmade on this corpus and must not be attempted on it.")
    print("=" * 78)
    return 0 if worst < 2 else 1


if __name__ == "__main__":
    sys.exit(main())
