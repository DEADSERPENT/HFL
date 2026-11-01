"""klaw_theory_check.py — does the shape predicted by the excess-risk bounds
(Proposition 2) describe the measured k-law?

With P individuals fixed and k records each, DP-SGD's excess-risk bound scales
as 1/(P k eps) for the record-level arm (P k units) and as 1/(P eps) for the
clipped-sum individual-level arm (P units), so the difference of the bounds,
normalised by its limit, is 1 - 1/k. The predicted gap is therefore

    gap(k) = A (1 - 1/k)          one free parameter, zero at k = 1

against the registered two-parameter law A (1 - exp(-b (k - 1))).

Reported per corpus: paired gap (record - individual, AUPRC) per k, the
least-squares A, RMSE of both forms, and an out-of-sample test: A fitted on
k <= 4 only, then the largest k predicted.

Reads  results/phase5/k_scaling/<grid>/k_scaling_<ds>.csv
Writes results/phase5/k_scaling/klaw_theory_check.json
"""
import csv
import glob
import json
import os
import numpy as np
from scipy.optimize import curve_fit

SIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KS = os.path.join(SIM, "results", "phase5", "k_scaling")


def inv_k(k, A):
    return A * (1.0 - 1.0 / k)


def sat_exp(k, A, b):
    return A * (1.0 - np.exp(-b * (k - 1.0)))


def fit_A(k, g):
    f = 1.0 - 1.0 / k
    return float(np.dot(f, g) / np.dot(f, f))


def main():
    out = {}
    for path in sorted(glob.glob(os.path.join(KS, "*", "k_scaling_*.csv"))):
        grid = os.path.basename(os.path.dirname(path))
        rows = list(csv.DictReader(open(path)))
        by = {}
        for r in rows:
            by.setdefault((int(r["k"]), int(r["seed"])), {})[r["arm"]] = float(r["auprc"])
        pairs = [(k, v["sample"] - v["patient"], v["patient"])
                 for (k, s), v in sorted(by.items()) if {"sample", "patient"} <= v.keys()]
        k = np.array([p[0] for p in pairs], float)
        g = np.array([p[1] for p in pairs], float)
        pat = np.array([p[2] for p in pairs], float)
        ks = sorted(int(x) for x in set(k.astype(int)))
        A = fit_A(k, g)
        res = dict(ks=ks, n_pairs=len(g),
                   gap_mean={int(x): float(g[k == x].mean()) for x in ks},
                   individual_arm_mean={int(x): float(pat[k == x].mean()) for x in ks},
                   individual_arm_slope_per_log2k=float(np.polyfit(np.log2(k), pat, 1)[0]),
                   inv_k=dict(A=A, rmse_seed=float(np.sqrt(np.mean((g - inv_k(k, A)) ** 2)))))
        try:
            (A2, b2), _ = curve_fit(sat_exp, k, g, p0=[0.08, 0.8], maxfev=20000)
            res["sat_exp"] = dict(A=float(A2), b=float(b2),
                                  rmse_seed=float(np.sqrt(np.mean((g - sat_exp(k, A2, b2)) ** 2))))
        except Exception as e:                      # noqa: BLE001
            res["sat_exp"] = dict(error=str(e))
        # out of sample: fit on k <= 4, predict the largest k
        kmax = int(max(ks))
        tr = k <= 4
        if kmax > 4 and tr.sum() >= 2:
            A_tr = fit_A(k[tr], g[tr])
            obs = float(g[k == kmax].mean())
            res["out_of_sample"] = dict(fit_on="k<=4", A=A_tr, k=kmax,
                                        predicted=inv_k(kmax, A_tr), observed=obs,
                                        error=obs - inv_k(kmax, A_tr))
        out[grid] = res
        print(f"\n{grid}  ({len(g)} paired seeds)")
        for x in ks:
            print(f"  k={x:<3d} gap {res['gap_mean'][x]:+.4f}   1/k-law {inv_k(x, A):+.4f}"
                  f"   individual arm {res['individual_arm_mean'][x]:.4f}")
        print(f"  A={A:.4f}  rmse 1/k-law {res['inv_k']['rmse_seed']:.4f}"
              f"  | 2-param exp rmse {res['sat_exp'].get('rmse_seed', float('nan')):.4f}")
        if "out_of_sample" in res:
            o = res["out_of_sample"]
            print(f"  out of sample: A(k<=4)={o['A']:.4f} predicts k={o['k']} "
                  f"{o['predicted']:+.4f}, observed {o['observed']:+.4f}")
    path = os.path.join(KS, "klaw_theory_check.json")
    json.dump(out, open(path, "w"), indent=2)
    print("\nwrote", path)


if __name__ == "__main__":
    main()
