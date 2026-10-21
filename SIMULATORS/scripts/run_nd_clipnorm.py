#!/usr/bin/env python3
"""
N-D: is the cost of a patient-level guarantee partly an artefact of clipping?

Runs the PATIENT arm at one k over clip_norm in {none, k, sqrt_k}, seeds paired,
reusing the k-scaling partitions so every arm sees identical data at an
identical budget. Predictions are frozen in
document/01_planning/PREREGISTRATION_ND_CLIPNORM.md.

Nothing is hardcoded: paths resolve from the registry and the k-scaling tree.
"""
import argparse, json, subprocess, sys
from pathlib import Path

_SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import get_spec, REGISTRY          # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--modes", nargs="+", default=["none", "k", "sqrt_k"])
    ap.add_argument("--epsilon", type=float, default=0.80)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--tau_e", type=int, default=5)
    ap.add_argument("--partition_dir", default=None,
                    help="default is the k-scaling partition for --k, which is "
                         "CAPPED at k windows per individual. Pass the registry "
                         "partition to run on the NATURAL window distribution. "
                         "Amendment N-A1: VitalDB's natural partition is already "
                         "flat (sd 0.67) so capping changes nothing there, but "
                         "eICU's spans 2-192 windows (sd 18.13) and ONLY the "
                         "natural partition can test N-D on it.")
    a = ap.parse_args()

    spec = get_spec(a.dataset)
    natural = a.partition_dir is not None
    ksrc = _SIM / "results" / "phase5" / "k_scaling" / a.dataset
    nat_dir = Path(a.partition_dir).resolve() if natural else None
    # "natural" and "k8" name different experiments; keep their artefacts apart.
    slug = "natural" if natural else f"k{a.k}"
    out = _SIM / "results" / "phase5" / "nd_clipnorm" / a.dataset
    out.mkdir(parents=True, exist_ok=True)
    enc = _SIM / "checkpoints" / f"pretrained_encoders_{a.dataset}.pt"

    print("=" * 74)
    print(f"N-D CLIP NORMALISATION — {a.dataset}  {slug}  seeds={a.seeds}")
    print(f"  modes: {a.modes}   eps={a.epsilon} (identical across modes)")
    print(f"  partitions: {nat_dir if natural else ksrc / ('k%d_seed<seed>' % a.k)}")
    if natural:
        print("  NATURAL window distribution (uncapped) — per amendment N-A1")
    print("=" * 74, flush=True)

    rows = []
    for seed in a.seeds:
        pdir = nat_dir if natural else ksrc / f"k{a.k}_seed{seed}"
        if not (pdir / "partition_meta.json").exists():
            sys.exit(f"[N-D] missing partition {pdir}"
                     + ("" if natural else f" — run k_scaling for k={a.k} first"))
        for mode in a.modes:
            tag = f"{slug}_seed{seed}_{mode}"
            ck = out / f"ckpt_{tag}.pt"
            hist = out / f"hist_{tag}.csv"
            if not ck.exists():
                cmd = [sys.executable,
                       str(_SIM / "model" / "training" / "hfl_trainer.py"),
                       "--dataset", a.dataset,
                       "--rounds", str(a.rounds), "--tau_e", str(a.tau_e),
                       "--epsilon", str(a.epsilon),
                       "--batch_size", str(a.batch_size),
                       "--patients_per_batch", str(a.batch_size),
                       "--dp_unit", "patient",
                       "--clip_norm", mode,
                       "--freeze_encoders",
                       "--pretrained_encoders", str(enc.relative_to(_SIM)),
                       "--partition_dir", str(pdir.relative_to(_SIM)),
                       "--seed", str(seed),
                       "--save_checkpoint", str(ck.relative_to(_SIM)),
                       "--output", str(hist.relative_to(_SIM)),
                       "--no_monitor"]
                print(f"  [run ] seed={seed} clip_norm={mode}", flush=True)
                with open(out / f"{tag}.log", "w") as lf:
                    r = subprocess.run(cmd, cwd=_SIM, stdout=lf,
                                       stderr=subprocess.STDOUT)
                if r.returncode != 0:
                    print(f"        FAILED — see {out/(tag+'.log')}", flush=True)
                    continue
            tj = out / f"hist_{tag}_test.json"
            if tj.exists():
                j = json.loads(tj.read_text())
                rows.append({"seed": seed, "mode": mode,
                             "auprc": j.get("auprc"),
                             "auroc": j.get("macro_auc")})
                print(f"        seed={seed} {mode:7s} AUPRC={j.get('auprc')}",
                      flush=True)

    (out / f"nd_clipnorm_{a.dataset}_{slug}.json").write_text(
        json.dumps({"dataset": a.dataset, "k": None if natural else a.k,
                    "partition": slug,
                    "partition_dir": str(nat_dir) if natural else None,
                    "epsilon": a.epsilon,
                    "note": "epsilon identical across modes; clip_norm changes "
                            "optimisation geometry only, never sensitivity",
                    "rows": rows}, indent=2))

    if rows:
        import statistics as st
        print("\n" + "=" * 74)
        print("  mode      n   mean AUPRC   vs none")
        print("  " + "-" * 44)
        base = [r["auprc"] for r in rows if r["mode"] == "none" and r["auprc"]]
        bm = st.mean(base) if base else None
        for mode in a.modes:
            v = [r["auprc"] for r in rows if r["mode"] == mode and r["auprc"]]
            if not v:
                continue
            d = f"{st.mean(v)-bm:+.4f}" if bm is not None and mode != "none" else "—"
            print(f"  {mode:8s} {len(v):2d}   {st.mean(v):10.4f}   {d:>8}")
    print(f"\n  written: {out}", flush=True)


if __name__ == "__main__":
    main()
