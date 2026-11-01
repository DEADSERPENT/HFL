"""lit_baselines_summary.py — HED-FL and FL2DP against the proposed system,
paired by seed.

Each baseline seed is paired with the stage-F runs of the same seed: the
private proposed model (dp_s<seed>) and its non-private reference
(nodp_s<seed>), which share data, partition, encoders and rounds with the
baselines. Differences are baseline minus proposed, so a positive AUROC
difference means the baseline ranks better; uplink is reported as a ratio.

Reads  results/phase5/baselines_lit/<ds>/{arm}_s<seed>_{test,final}.json
       results/phase5/o2b_system/<ds>/{dp,nodp}_s<seed>/run_{test,final}.json
Writes results/phase5/baselines_lit/<ds>/lit_paired.json

    python scripts/lit_baselines_summary.py <dataset>
"""
import argparse
import json
import os
import re
from glob import glob

from o2b_paired_summary import paired

METRICS = ("macro_auc", "auprc", "balanced_accuracy_valthr")
SIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load(prefix):
    t, f = prefix + "_test.json", prefix + "_final.json"
    if not (os.path.exists(t) and os.path.exists(f)):
        return None
    test, final = json.load(open(t)), json.load(open(f))
    return {**{m: test.get(m) for m in METRICS},
            "uplink": final.get("uplink_bytes_total")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    a = ap.parse_args()
    bdir = os.path.join(SIM, "results", "phase5", "baselines_lit", a.dataset)
    fdir = os.path.join(SIM, "results", "phase5", "o2b_system", a.dataset)
    arms = sorted({re.match(r"(\w+?)_s\d+_test\.json", os.path.basename(p)).group(1)
                   for p in glob(os.path.join(bdir, "*_s*_test.json"))})
    out = {"dataset": a.dataset, "arms": {}}
    for arm in arms:
        rows = {}
        for p in sorted(glob(os.path.join(bdir, f"{arm}_s*_test.json"))):
            sd = int(re.search(r"_s(\d+)_test", p).group(1))
            b = load(p[:-len("_test.json")])
            dp = load(os.path.join(fdir, f"dp_s{sd}", "run"))
            nodp = load(os.path.join(fdir, f"nodp_s{sd}", "run"))
            if b and dp and nodp:
                rows[sd] = dict(base=b, dp=dp, nodp=nodp)
        seeds = sorted(rows)
        res = {"seeds": seeds, "metrics": {}}
        for m in METRICS:
            res["metrics"][m] = {
                "baseline": sum(rows[s]["base"][m] for s in seeds) / len(seeds),
                "proposed_dp": sum(rows[s]["dp"][m] for s in seeds) / len(seeds),
                "nonprivate": sum(rows[s]["nodp"][m] for s in seeds) / len(seeds),
                "minus_proposed_dp": paired([rows[s]["base"][m] - rows[s]["dp"][m]
                                             for s in seeds]),
                "minus_nonprivate": paired([rows[s]["base"][m] - rows[s]["nodp"][m]
                                            for s in seeds]),
            }
        up_b = sum(rows[s]["base"]["uplink"] for s in seeds) / len(seeds)
        up_p = sum(rows[s]["dp"]["uplink"] for s in seeds) / len(seeds)
        res["uplink_mb"] = {"baseline": up_b / 1e6, "proposed": up_p / 1e6,
                            "ratio": up_b / up_p}
        out["arms"][arm] = res
        print(f"\n{a.dataset} {arm}  (n={len(seeds)})")
        for m, v in res["metrics"].items():
            d = v["minus_proposed_dp"]
            ci = f"[{d['ci_low']:+.4f}, {d['ci_high']:+.4f}]" if "ci_low" in d else ""
            print(f"  {m:25s} base {v['baseline']:.4f}  ours {v['proposed_dp']:.4f}"
                  f"  nonpriv {v['nonprivate']:.4f}  base-ours {d['mean']:+.4f} {ci}")
        print(f"  uplink MB  base {up_b/1e6:.1f}  ours {up_p/1e6:.1f}  "
              f"ratio {up_b/up_p:.2f}x")
    path = os.path.join(bdir, "lit_paired.json")
    json.dump(out, open(path, "w"), indent=2)
    print("wrote", path)


if __name__ == "__main__":
    main()
