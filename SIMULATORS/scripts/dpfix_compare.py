"""dpfix_compare.py — objectives and O2b costs before and after the 2026-10-22
privacy fix, side by side.

Before: record-level DP (every pre-fix system run) with the |S| divisor on
the patient path. After: patient-level DP, expected-batch divisor,
worst-client calibration, patient-level conformal release.

Reads  results/_archive_pre_dpfix_20261022/phase5/{objectives_<ds>.json,
           o2b_multiseed/<ds>/o2b_paired.json}
       results/phase5/... (current)
Writes results/phase5/dpfix_compare_<ds>.json
"""
import argparse
import json
import os

SIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NOW = os.path.join(SIM, "results", "phase5")
OLD = os.path.join(SIM, "results", "_archive_pre_dpfix_20261022", "phase5")


def _load(path):
    return json.load(open(path)) if os.path.exists(path) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    a = ap.parse_args()
    out = dict(dataset=a.dataset, objectives={}, o2b_cost={})
    rel = f"objectives_{a.dataset}.json"
    old, new = _load(os.path.join(OLD, rel)), _load(os.path.join(NOW, rel))
    print(f"{'obj':5s} {'before':>10s} {'':6s} {'after':>10s}")
    for k in (new or old or {}).get("objectives", {}):
        o = (old or {}).get("objectives", {}).get(k, {})
        n = (new or {}).get("objectives", {}).get(k, {})
        out["objectives"][k] = dict(before=o.get("measured"), before_verdict=o.get("verdict"),
                                    after=n.get("measured"), after_verdict=n.get("verdict"))
        f = lambda v: f"{v:10.4f}" if isinstance(v, (int, float)) else f"{str(v):>10s}"
        print(f"{k:5s} {f(o.get('measured'))} {str(o.get('verdict', '')):6s} "
              f"{f(n.get('measured'))} {n.get('verdict', '')}")
    rel = os.path.join("o2b_multiseed", a.dataset, "o2b_paired.json")
    old, new = _load(os.path.join(OLD, rel)), _load(os.path.join(NOW, rel))
    for m in (new or old or {}).get("metrics", {}):
        g = lambda d: (d or {}).get("metrics", {}).get(m, {}).get("cost", {})
        out["o2b_cost"][m] = dict(before=g(old), after=g(new))
        b, n = g(old).get("mean"), g(new).get("mean")
        print(f"O2b cost {m:11s} before {b if b is None else round(b, 4)}"
              f"  after {n if n is None else round(n, 4)}"
              f"  [{g(new).get('ci_low', float('nan')):+.4f}, "
              f"{g(new).get('ci_high', float('nan')):+.4f}]" if new else "")
    path = os.path.join(NOW, f"dpfix_compare_{a.dataset}.json")
    json.dump(out, open(path, "w"), indent=2)
    print("wrote", path)


if __name__ == "__main__":
    main()
