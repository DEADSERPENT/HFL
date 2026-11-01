"""How much can one patient move the standardization constants?

The z-score constants (per-channel mean and SD of modality A, mean and SD of
modality B) are fitted on the training individuals and applied to every split.
Theorem 1 holds with these constants fixed; their own release is outside the
guarantee. This script measures the size of that release, in the normalized
space the model sees (where the fitted constants are mean 0, SD 1):

  1. leave-one-patient-out: the largest change in any mean (in SD units) and
     in any SD (relative) when one training individual is removed;
  2. disjoint pool (eICU): the same constants fitted on the public
     pretraining pool alone, which is the fully public alternative.

    python scripts/standardization_sensitivity.py eicu

CPU only, memory-mapped. Writes results/phase5/standardization_<dataset>.json.
"""
import argparse, json
from pathlib import Path
import numpy as np

SIM = Path(__file__).resolve().parents[1]
LAYOUT = {  # modality-A array, number of value channels (masks follow), modality-B array
    "eicu": ("data/processed/eicu/vitals/windows.npy", 6, "data/processed/eicu/tabular/features.npy"),
    "vitaldb": ("data/processed/vitaldb/signals/windows.npy", 9, "data/processed/vitaldb/clinical/features.npy"),
}
ap = argparse.ArgumentParser(); ap.add_argument("dataset"); a = ap.parse_args()
fa, C, fb = LAYOUT[a.dataset]
A = np.load(SIM / fa, mmap_mode="r"); B = np.load(SIM / fb, mmap_mode="r")
pdir = SIM / "data/processed/partitions" / a.dataset
meta = json.load(open(pdir / "partition_meta.json"))
train = np.concatenate([np.load(pdir / f"device_{d:02d}_train.npy") for d in range(meta["n_devices"])])
pub = pdir / "public_indices.npy"
pool = np.load(pub) if pub.exists() else np.array([], int)
fit = np.sort(np.concatenate([train, pool]))          # the rows the constants were fitted on
pid = np.load(SIM / "data/processed" / a.dataset / "meta/case_ids.npy")
_, pinv = np.unique(pid[fit], return_inverse=True)
P = pinv.max() + 1
D = C + B.shape[1]

S = np.zeros((P, D)); Q = np.zeros((P, D)); N = np.zeros((P, D))
CH = 100_000
for i in range(0, len(fit), CH):
    idx = fit[i:i + CH]; g = pinv[i:i + CH]
    x = np.asarray(A[idx], np.float64); v, m = x[:, :C], x[:, C:2 * C] > 0
    b = np.asarray(B[idx], np.float64)
    for c in range(C):
        w = m[:, c].sum(-1)
        S[:, c] += np.bincount(g, (v[:, c] * m[:, c]).sum(-1), P)
        Q[:, c] += np.bincount(g, (v[:, c] ** 2 * m[:, c]).sum(-1), P)
        N[:, c] += np.bincount(g, w, P)
    for j in range(b.shape[1]):
        S[:, C + j] += np.bincount(g, b[:, j], P)
        Q[:, C + j] += np.bincount(g, b[:, j] ** 2, P)
        N[:, C + j] += np.bincount(g, None, P)

n, s, q = N.sum(0), S.sum(0), Q.sum(0)
mu0, var0 = s / n, q / n - (s / n) ** 2               # ~0 and ~1 by construction
rem_n = n - N
mu_loo = (s - S) / np.maximum(rem_n, 1)
var_loo = (q - Q) / np.maximum(rem_n, 1) - mu_loo ** 2
dmu = np.abs(mu_loo - mu0) / np.sqrt(var0)
dsd = np.abs(np.sqrt(np.maximum(var_loo, 0)) / np.sqrt(var0) - 1)
out = dict(dataset=a.dataset, individuals=int(P), fitted_rows=int(len(fit)),
           check_mean=float(np.abs(mu0).max()), check_sd=float(np.abs(np.sqrt(var0) - 1).max()),
           loo_max_mean_shift_sd=float(dmu.max()), loo_max_sd_rel=float(dsd.max()),
           loo_p99_mean_shift_sd=float(np.quantile(dmu.max(1), .99)),
           loo_max_sd_rel_by_channel=[round(float(x), 5) for x in dsd.max(0)],
           loo_p99_sd_rel=float(np.quantile(dsd.max(1), .99)))
if len(pool):
    ip = np.isin(fit, pool)
    pp = np.unique(pinv[ip])
    ns, ss, qs = N[pp].sum(0), S[pp].sum(0), Q[pp].sum(0)
    mup = ss / ns; sdp = np.sqrt(qs / ns - mup ** 2)
    out.update(pool_individuals=int(len(pp)),
               pool_max_mean_diff_sd=float(np.abs(mup - mu0).max()),
               pool_max_sd_rel_diff=float(np.abs(sdp / np.sqrt(var0) - 1).max()),
               pool_mean_diff_sd=[round(float(x), 5) for x in (mup - mu0)],
               pool_sd_rel=[round(float(x), 5) for x in sdp / np.sqrt(var0)])
print(json.dumps(out, indent=1))
json.dump(out, open(SIM / f"results/phase5/standardization_{a.dataset}.json", "w"), indent=1)
