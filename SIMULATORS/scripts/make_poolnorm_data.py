"""make_poolnorm_data.py — re-standardize a corpus with constants fitted on the
disjoint public pool only.

WHY
---
Theorem 1 holds with the standardization constants fixed. The preprocessors
fit them on the TRAINING individuals, so the constants are an unprotected
release about the protected cohort (one eICU outlier moves a channel's SD by
5.2 %, see standardization_sensitivity.py). Fitting them on the public pool
(public_indices.npy, the encoders' pretraining pool, disjoint from every
client) makes them public, and the guarantee then covers the run end to end.

HOW
---
The stored arrays are z-scored with the training constants (mu0, sd0). For any
affine standardization, refitting on a subset is an affine map of the stored
values: x_pool = (x - m) / s, where m and s are the pool's mean and SD in the
stored (already standardized) units. This is exact only if the preprocessor
did nothing non-affine after standardizing; the script therefore first checks
that the stored training rows have mean 0 and SD 1 per channel and aborts
otherwise (VitalDB clips at +-CLIP_Z and fails this check by design).

Masked entries of mask-channel modalities stay 0. Imputed modality-B entries
(the training median, mapped to a constant) are re-imputed with the pool
median when the two differ.

    python scripts/make_poolnorm_data.py eicu

Writes data/processed/<dataset>_poolnorm/ (labels and meta symlinked) and
<out>/meta/norm_stats_pool.json. CPU only.
"""
import argparse, json, os, sys
from pathlib import Path
import numpy as np

SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "data" / "loaders"))
from datasets import get_spec

ap = argparse.ArgumentParser()
ap.add_argument("dataset")
ap.add_argument("--tol", type=float, default=1e-3, help="reproduction tolerance (SD units)")
ap.add_argument("--chunk", type=int, default=100_000)
a = ap.parse_args()

spec = get_spec(a.dataset)
src = SIM / spec.data_dir
dst = SIM / f"{spec.data_dir}_poolnorm"
pdir = SIM / spec.partition_dir
arrays = {rel: nd for rel, nd in spec.required_files.items()}
rel_a = next(r for r, nd in arrays.items() if nd == (3,))
rel_b = next(r for r, nd in arrays.items() if nd == (2,))
rel_y = next(r for r, nd in arrays.items() if nd == (1,))
A = np.load(src / rel_a, mmap_mode="r"); B = np.load(src / rel_b, mmap_mode="r")
C = A.shape[1] // 2 if spec.has_mask_channels else A.shape[1]

meta = json.load(open(pdir / "partition_meta.json"))
train = np.concatenate([np.load(pdir / f"device_{d:02d}_train.npy") for d in range(meta["n_devices"])])
pool = np.sort(np.load(pdir / "public_indices.npy"))
fit = np.sort(np.concatenate([train, pool]))           # rows the stored constants were fitted on
assert len(np.intersect1d(train, pool)) == 0, "pool is not disjoint from client training rows"


def moments(rows):
    n = np.zeros(C); s = np.zeros(C); q = np.zeros(C)
    bs = []
    for i in range(0, len(rows), a.chunk):
        idx = rows[i:i + a.chunk]
        x = np.asarray(A[idx], np.float64)
        v = x[:, :C]
        m = (x[:, C:2 * C] > 0) if spec.has_mask_channels else np.ones_like(v, bool)
        n += m.sum((0, 2)); s += (v * m).sum((0, 2)); q += (v * v * m).sum((0, 2))
        bs.append(np.asarray(B[idx], np.float64))
    mu = s / n
    return mu, np.sqrt(q / n - mu ** 2), np.concatenate(bs)


mu_f, sd_f, B_f = moments(fit)
b_mu_f, b_sd_f = B_f.mean(0), B_f.std(0)
err = max(np.abs(mu_f).max(), np.abs(sd_f - 1).max(), np.abs(b_mu_f).max(),
          np.abs(b_sd_f[b_sd_f > 0] - 1).max())
print(f"[poolnorm] reproduction of stored constants: max error {err:.2e} SD")
if err > a.tol:
    sys.exit(f"[FAIL] stored arrays are not a pure z-score of the fit rows (error {err:.3g} > "
             f"{a.tol}); the affine remap would not equal a pool refit. Re-run the "
             f"preprocessor with pool constants instead.")

mu_p, sd_p, B_p = moments(pool)
# Modality B: the training median was imputed before z-scoring. Re-impute
# with the pool median where the two differ.
med_f = np.median(B_f, 0)
b_new = []
for j in range(B.shape[1]):
    col = B_p[:, j]
    imputed = np.isclose(col, med_f[j], atol=1e-6)
    med_p = np.median(col) if np.isclose(np.median(col), med_f[j], atol=1e-6) \
        else np.median(col[~imputed])
    b_new.append((med_f[j], med_p))
B_p_imp = B_p.copy()
for j, (mf, mp) in enumerate(b_new):
    B_p_imp[np.isclose(B_p_imp[:, j], mf, atol=1e-6), j] = mp
b_mu_p, b_sd_p = B_p_imp.mean(0), B_p_imp.std(0)
b_sd_p = np.where(b_sd_p < 1e-6, 1.0, b_sd_p)
sd_p = np.where(sd_p < 1e-6, 1.0, sd_p)

dst.mkdir(exist_ok=True)
for sub in {Path(r).parent for r in arrays} | {Path("meta")}:
    (dst / sub).mkdir(parents=True, exist_ok=True)
for f in (src / "meta").iterdir():
    link = dst / "meta" / f.name
    if not link.exists():
        os.symlink(f, link)
if not (dst / rel_y).exists():
    os.symlink(src / rel_y, dst / rel_y)

outA = np.lib.format.open_memmap(dst / rel_a, mode="w+", dtype=A.dtype, shape=A.shape)
outB = np.lib.format.open_memmap(dst / rel_b, mode="w+", dtype=B.dtype, shape=B.shape)
for i in range(0, A.shape[0], a.chunk):
    sl = slice(i, min(i + a.chunk, A.shape[0]))
    x = np.asarray(A[sl], np.float64)
    v = x[:, :C]
    m = (x[:, C:2 * C] > 0) if spec.has_mask_channels else np.ones_like(v, bool)
    x[:, :C] = ((v - mu_p[None, :, None]) / sd_p[None, :, None]) * m
    outA[sl] = x.astype(A.dtype)
    b = np.asarray(B[sl], np.float64)
    for j, (mf, mp) in enumerate(b_new):
        b[np.isclose(b[:, j], mf, atol=1e-6), j] = mp
    outB[sl] = ((b - b_mu_p) / b_sd_p).astype(B.dtype)
outA.flush(); outB.flush()

stats = dict(dataset=a.dataset, source=str(src.relative_to(SIM)), fitted_on="public_indices.npy",
             pool_rows=int(len(pool)), reproduction_error_sd=float(err),
             a_mean_shift_sd=mu_p.round(6).tolist(), a_sd_ratio=sd_p.round(6).tolist(),
             b_mean_shift_sd=b_mu_p.round(6).tolist(), b_sd_ratio=b_sd_p.round(6).tolist(),
             b_median_train_vs_pool=[[round(float(x), 6) for x in t] for t in b_new])
json.dump(stats, open(dst / "meta" / "norm_stats_pool.json", "w") if not (dst / "meta" / "norm_stats_pool.json").is_symlink() else sys.exit("meta collision"), indent=1)
print(json.dumps(stats, indent=1))
print(f"[poolnorm] wrote {dst}")
