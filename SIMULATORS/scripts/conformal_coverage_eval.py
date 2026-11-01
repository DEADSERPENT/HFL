"""Empirical coverage of the released private conformal threshold (stage F runs).

For each private run of results/phase5/o2b_system/<dataset><tag>/dp_s<seed>, the
final-round threshold q_global (run.csv) is applied to the saved checkpoint on
the pooled TEST split: a window is covered when 1 - p(y|x) <= q_global. Target
coverage is 1 - alpha. Only valid when the selected checkpoint is the round the
threshold was calibrated on; other runs are reported and excluded.

    python scripts/conformal_coverage_eval.py vitaldb [--tag _disjoint] [--alpha 0.1]

CPU only (never competes with a GPU job). Writes coverage_<dataset><tag>.json.
"""
import argparse, csv, json, sys
from pathlib import Path
import numpy as np, torch
from scipy import stats

SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "scripts"))
import lira_attack as L

ap = argparse.ArgumentParser()
ap.add_argument("dataset")
ap.add_argument("--tag", default="")
ap.add_argument("--alpha", type=float, default=0.1)
ap.add_argument("--arm", default="dp")
ap.add_argument("--stride", type=int, default=1, help="evaluate every n-th test window")
a = ap.parse_args()

spec = L.get_spec(a.dataset); dev = torch.device("cpu")
pdir = SIM / spec.partition_dir
meta = json.load(open(pdir / "partition_meta.json"))
test = np.sort(np.concatenate([np.load(pdir / f"device_{d:02d}_test.npy")
                               for d in range(meta["n_devices"])]))[::a.stride]
ds = spec.build_full(str(SIM / spec.data_dir))
y = np.array([int(ds[int(i)][3]) for i in test])
m = L.build_model(spec, dev)
root = SIM / "results/phase5/o2b_system" / f"{a.dataset}{a.tag}"

def probs():
    out = []
    with torch.no_grad():
        for s in range(0, len(test), 1024):
            idx = test[s:s + 1024]
            xa = torch.stack([ds[int(i)][0] for i in idx])
            xb = torch.stack([ds[int(i)][1] for i in idx])
            out.append(torch.softmax(m(xa, xb).float(), 1).numpy())
    return np.concatenate(out)

rows = {}
for run in sorted(root.glob(f"{a.arm}_s*")):
    fin = json.load(open(run / "run_final.json"))
    last = list(csv.DictReader(open(run / "run.csv")))[-1]
    q = float(last["q_global"])
    valid = int(fin["selected_round"]) == int(last["global_round"])
    L.load_into(m, run / "ckpt.pt", dev); m.eval()
    p = probs()
    score = 1.0 - p[np.arange(len(y)), y]
    cov = float(np.mean(score <= q))
    by_class = {int(c): float(np.mean(score[y == c] <= q)) for c in np.unique(y)}
    size = float(np.mean((1.0 - p <= q).sum(1)))
    rows[run.name] = dict(q=q, coverage=cov, coverage_by_class=by_class,
                          mean_set_size=size, valid=valid,
                          selected_round=fin["selected_round"])
    print(run.name, rows[run.name], flush=True)

v = np.array([r["coverage"] for r in rows.values() if r["valid"]])
summary = dict(dataset=a.dataset + a.tag, target=1 - a.alpha, n=len(v),
               mean=float(v.mean()) if len(v) else None,
               ci95=(float(stats.t.ppf(.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v)))
                     if len(v) > 1 else None),
               runs=rows)
print(json.dumps({k: summary[k] for k in ("dataset", "target", "n", "mean", "ci95")}))
json.dump(summary, open(SIM / f"results/phase5/coverage_{a.dataset}{a.tag}_{a.arm}.json", "w"), indent=2)
