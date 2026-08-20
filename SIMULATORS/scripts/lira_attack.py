"""
lira_attack.py — likelihood-ratio membership inference, at the PATIENT level.

WHY THIS EXISTS
---------------
`membership_inference.py` mounted a loss-threshold attack and found almost
nothing: record-level DP 0.5461 vs patient-level DP 0.5374 at eps=1, a gap of
0.0087 where the pre-registered prediction was 0.7 vs 0.5.

That result cannot be reported as "record-level DP does not leak". A loss
threshold is the WEAKEST attack in the literature: it compares a patient's loss
against a single global threshold, so an easy non-member outscores a hard
member and the signal is buried in per-patient difficulty. Any AUC it produces
is a LOWER BOUND on leakage, and a reviewer will say exactly that.

LiRA (Carlini et al., "Membership Inference Attacks From First Principles",
IEEE S&P 2022) removes the difficulty confound. For each patient it learns what
the model output looks like when that patient WAS in training and when it was
NOT, by training shadow models on random halves of the patients. Membership is
then a likelihood ratio between two fitted Gaussians rather than a comparison
against a global constant. It is the strongest practical attack, so a null
result under LiRA is worth reporting, whereas a null under loss thresholding is
mostly a statement about the attack.

    loss threshold says "this patient has low loss"
    LiRA says          "this patient has low loss FOR THIS PATIENT"

WHAT IS PATIENT-LEVEL HERE
--------------------------
Everything is aggregated to the person before any decision is made. The per
window statistic is averaged over a patient's windows, shadow membership is
drawn per patient (all of a patient's windows move together), and the
likelihood ratio is fitted per patient. Averaging is what converts weak
per-record signal into per-person signal, and it is precisely the step a
record-level guarantee does not cover.

THE STATISTIC
-------------
Carlini's logit-scaled confidence, in its numerically stable form

    phi = z_y - logsumexp_{j != y} z_j        ( = log( p_y / (1 - p_y) ) )

computed per window from the raw logits and averaged over the patient. Logits,
not loss: phi is unbounded and roughly Gaussian after the logit transform,
which is what makes the parametric fit legitimate. Class weighting is
deliberately NOT applied to phi — it rescales the loss, not the logits, and
would only add a per-class constant. The weighted loss is recorded alongside so
the old loss-threshold attack is recomputed on the identical patient set and
the two attacks are directly comparable in one table.

SHADOW MODELS
-------------
Canonical LiRA needs each target patient IN the training set of some shadows
and OUT of others. The released checkpoints cannot supply that: every existing
run uses the same fixed partition, so every train patient is IN for all of them
and no OUT distribution exists. Shadows therefore have to be trained.

Each shadow gets its own partition directory in which a random half of the
patients are members. Only the .npy index files and partition_meta.json change
— hfl_trainer.py is not modified and does not know it is training a shadow.
A patient's windows never split across the member boundary, and each patient
keeps its original client, so shadow models inherit the same specialty-derived
non-IID structure as the target.

The training recipe is READ FROM THE TARGET RUN's own run_metadata.json
(`argv`) rather than restated here. A shadow trained with a different recipe
than the model it calibrates is a silently wrong attack, and the recipes in
this project differ in ways that matter (--dp_unit, --freeze_encoders,
--patients_per_batch). Deriving it means the shadow recipe cannot drift from
the target's.

Shadows see half the data, so their sigma calibration and their difficulty
distribution differ slightly from the target's. That is inherent to LiRA
(Carlini's shadows are likewise trained on half) and is why the fitted
Gaussians are only a calibration device, never a claim about the target's
budget.

THE POSITIVE CONTROL — READ THIS BEFORE BELIEVING A NULL
--------------------------------------------------------
An attack that finds nothing is indistinguishable from an attack that is broken
until it is shown to find something. `mia_factorial_head_nodp.csv` established
that the head-only NO-DP recipe memorises hard: loss threshold already reaches
0.5847 with member loss 0.013 against non-member 4.95.

So run that arm too. LiRA must beat 0.5847 there. If it does not, the
implementation is underpowered and its null on the DP arms says nothing. This
mirrors the k=1 collapse check in roadmap item B: a validity condition the
attack has to satisfy before its negative results are admissible.

REPORTED METRICS
----------------
AUC, plus TPR at 1 % and 0.1 % FPR. Carlini's central methodological point is
that average-case AUC hides the tail: an attack can sit at 0.51 AUC and still
identify a handful of patients with near-certainty, and for a clinical privacy
claim those few confident identifications ARE the disclosure. An attack is
reported as finding nothing only when the low-FPR corner is empty too.

Four attacks are scored on the same patients, same models, same code path:

    loss            the old threshold attack, recomputed for comparability
    lira_offline    one-sided, OUT shadows only (no IN model needed)
    lira_online     two-sided likelihood ratio, per-patient variance
    lira_online_gv  two-sided, variance pooled across patients

The global-variance variant exists because a per-patient sd fitted from ~8 IN
samples is noisy; pooling trades a little specificity for a lot of stability
and often wins with few shadows. The attacker is entitled to pick the best of
the four, so the headline leakage estimate is the MAX over them — reported as
such rather than quietly selected.

USAGE
-----
    # 1. splits + shadow training (long; resumable — rerun to continue)
    python scripts/lira_attack.py --dataset vitaldb --arms sample patient \
        --n_shadows 16 --phase splits,train

    # 2. the attack itself (minutes)
    python scripts/lira_attack.py --dataset vitaldb --arms sample patient \
        --n_shadows 16 --phase score,attack

    # positive control — must beat 0.5847 or the null above is inadmissible
    python scripts/lira_attack.py --dataset vitaldb --arms head_nodp \
        --target_dir results/phase5/mia_factorial/vitaldb \
        --ckpt_pattern "ckpt_{arm}_seed{seed}.pt" --seeds 42 43 44 \
        --n_shadows 16

    # see the training commands without running them
    python scripts/lira_attack.py --dataset vitaldb --phase train --dry_run
"""

import os
import sys
import csv
import json
import math
import shutil
import argparse
import subprocess
from pathlib import Path

import numpy as np
import torch

_SIM = Path(__file__).resolve().parent.parent
for _s in ("data/loaders", "model/architecture", "model/utils", "model/privacy",
           "scripts"):
    sys.path.insert(0, str(_SIM / _s))

from datasets import get_spec, REGISTRY                          # noqa: E402
from hfl_mm_model import build_hfl_mm_hc                         # noqa: E402
from device_utils import get_device                              # noqa: E402
from run_statistics import mean_ci, paired_test                  # noqa: E402


def auc_scores(y, s):
    """AUC where a HIGHER score means more member-like.

    Deliberately not `membership_inference.attack_auc`, which takes LOSSES and
    negates them internally. Feeding it a likelihood ratio — where high already
    means member — silently returns 1 - AUC, and 0.93 reads out as 0.07. The
    two conventions cannot share one helper without inviting that mistake, so
    they do not.
    """
    from sklearn.metrics import roc_auc_score
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


# ── patient bookkeeping ─────────────────────────────────────────────────────

def load_partition(pdir: Path, n_dev: int):
    """Every index file of the released partition, keyed by (device, split)."""
    out = {}
    for d in range(n_dev):
        for sp in ("train", "val", "test"):
            f = pdir / f"device_{d:02d}_{sp}.npy"
            if f.exists():
                out[(d, sp)] = np.load(f)
    return out


def patient_table(part: dict, case_ids: np.ndarray):
    """Map every patient to its windows, its client and its released split.

    Fails loudly if a patient spans two clients or two splits. Both would break
    the attack's premise rather than merely degrade it: a patient present in
    both train and test is simultaneously member and non-member, and every AUC
    computed over such a set is meaningless. The released partition is supposed
    to be case-level; this is where that is verified instead of assumed.
    """
    windows, dev_of, split_of = {}, {}, {}
    for (d, sp), idx in part.items():
        for cid, w in zip(case_ids[idx], idx):
            windows.setdefault(int(cid), []).append(int(w))
            dev_of.setdefault(int(cid), d)
            split_of.setdefault(int(cid), sp)

    bad_dev, bad_split = [], []
    for (d, sp), idx in part.items():
        for cid in np.unique(case_ids[idx]):
            if dev_of[int(cid)] != d:
                bad_dev.append(int(cid))
            if split_of[int(cid)] != sp:
                bad_split.append(int(cid))
    if bad_dev or bad_split:
        raise SystemExit(
            f"[FATAL] partition is not case-level: {len(set(bad_dev))} patients "
            f"span clients, {len(set(bad_split))} span train/val/test splits.\n"
            f"        Membership is undefined for those patients, so no "
            f"membership-inference result computed here would mean anything.")

    return ({c: np.asarray(sorted(w)) for c, w in windows.items()},
            dev_of, split_of)


# ── phase 1: shadow splits ──────────────────────────────────────────────────

def build_shadow_splits(a, spec, meta, windows, dev_of, out_root: Path):
    """Write one partition directory per shadow, plus the membership matrix.

    Membership is drawn per PATIENT over the whole universe (train, val and
    test patients alike) so that every patient the attack later scores has both
    IN and OUT shadows. Non-members of a shadow are not discarded — they become
    that shadow's val/test, so the trainer's model selection still runs on data
    it did not train on, exactly as in the target run.
    """
    n_dev = meta["n_devices"]
    patients = np.array(sorted(windows), dtype=np.int64)
    pos = {int(c): i for i, c in enumerate(patients)}
    mask = np.zeros((a.n_shadows, len(patients)), dtype=bool)

    print(f"  universe: {len(patients):,} patients, "
          f"{sum(len(w) for w in windows.values()):,} windows")

    for s in range(a.n_shadows):
        sdir = out_root / f"shadow_{s:02d}"
        sdir.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(a.split_seed * 10_000 + s)

        n_in = int(round(len(patients) * a.member_frac))
        in_pat = set(int(c) for c in rng.choice(patients, n_in, replace=False))
        mask[s] = np.array([int(c) in in_pat for c in patients])

        smeta = json.loads(json.dumps(meta))
        counts = {}
        for d in range(n_dev):
            dev_pat = [c for c in patients if dev_of[int(c)] == d]
            tr = [c for c in dev_pat if int(c) in in_pat]
            out = [c for c in dev_pat if int(c) not in in_pat]
            # OUT patients carry the shadow's val and test. Splitting them by a
            # coin per patient keeps whole patients on one side, which is the
            # same case-level rule the released partition follows.
            coin = rng.random(len(out)) < 0.5
            va = [c for c, k in zip(out, coin) if k]
            te = [c for c, k in zip(out, coin) if not k]
            if not tr or not va or not te:
                raise SystemExit(
                    f"[FATAL] shadow {s} client {d} would get "
                    f"train/val/test = {len(tr)}/{len(va)}/{len(te)} patients. "
                    f"An empty split crashes the trainer or silently disables "
                    f"model selection. Lower --n_shadows or raise "
                    f"--member_frac.")

            for name, group in (("train", tr), ("val", va), ("test", te)):
                idx = np.concatenate([windows[int(c)] for c in group])
                np.save(sdir / f"device_{d:02d}_{name}.npy", np.sort(idx))
                if name == "train":
                    counts[d] = len(idx)
            smeta["devices"][str(d)]["n_train"] = counts[d]
            smeta["devices"][str(d)]["n_val"] = int(sum(len(windows[int(c)]) for c in va))
            smeta["devices"][str(d)]["n_test"] = int(sum(len(windows[int(c)]) for c in te))

        # sigma is calibrated from the FILES (hfl_trainer.py:562), but the meta
        # is written truthfully anyway — stale counts here are what breached a
        # budget once before.
        smeta["lira_shadow"] = {
            "shadow_id": s, "member_frac": a.member_frac,
            "split_seed": a.split_seed, "n_member_patients": int(mask[s].sum()),
            "note": "synthetic partition for membership inference; not a "
                    "reportable training configuration",
        }
        smeta.pop("public_split", None)
        with open(sdir / "partition_meta.json", "w") as f:
            json.dump(smeta, f, indent=2)

        print(f"  shadow {s:02d}  members {mask[s].sum():>5,}/{len(patients):,} "
              f"patients   min client train {min(counts.values()):>6,} windows")

    np.savez(out_root / "membership.npz", patients=patients, mask=mask)

    # Every patient needs both sides, or its likelihood ratio is undefined.
    per = mask.sum(0)
    thin = int(((per < 2) | (per > a.n_shadows - 2)).sum())
    print(f"\n  IN-shadows per patient: min {per.min()}, max {per.max()}, "
          f"median {int(np.median(per))}")
    if thin:
        print(f"  [warn] {thin} patients have <2 IN or <2 OUT shadows; their "
              f"variance estimate falls back to the pooled one.")
    return patients, mask, pos


# ── phase 2: shadow training ────────────────────────────────────────────────

_RUN_SPECIFIC = {"--seed", "--save_checkpoint", "--output", "--partition_dir"}


def derive_recipe(target_dir: Path, ckpt_name: str):
    """Recover the exact training argv of the model being attacked.

    Matched on the checkpoint the run wrote, not on a filename convention, so a
    renamed or copied checkpoint cannot silently pick up another run's recipe.
    """
    best = None
    for f in sorted(target_dir.glob("run_metadata_*.json")):
        try:
            argv = json.load(open(f)).get("argv") or []
        except Exception:
            continue
        for i, tok in enumerate(argv):
            if tok == "--save_checkpoint" and i + 1 < len(argv) \
                    and Path(argv[i + 1]).name == ckpt_name:
                best = (f, argv)          # last match wins: the newest rerun
    if best is None:
        raise SystemExit(
            f"[FATAL] no run_metadata in {target_dir} records writing "
            f"{ckpt_name}.\n        The shadow recipe must come from the target "
            f"run; guessing it would calibrate the attack against a model "
            f"trained differently from the one under attack.")
    src, argv = best
    kept, i = [], 1                        # argv[0] is the trainer path
    while i < len(argv):
        if argv[i] in _RUN_SPECIFIC:
            i += 2
            continue
        kept.append(argv[i])
        i += 1
    return argv[0], kept, src.name


def train_shadows(a, arm, out_root: Path, target_dir: Path):
    trainer, recipe, src = derive_recipe(target_dir,
                                         a.ckpt_pattern.format(arm=arm, seed=a.seeds[0]))
    print(f"  recipe from {src}")
    print(f"  {' '.join(recipe)}\n")

    done = skipped = 0
    for s in range(a.n_shadows):
        sdir = out_root / f"shadow_{s:02d}"
        ckpt = sdir / "ckpt.pt"
        if ckpt.exists():
            skipped += 1
            continue
        cmd = [sys.executable, trainer, *recipe,
               "--partition_dir", str(sdir.relative_to(_SIM)),
               "--seed", str(a.split_seed * 10_000 + s),
               "--save_checkpoint", str((sdir / "ckpt.pt").relative_to(_SIM)),
               "--output", str((sdir / "history.csv").relative_to(_SIM))]
        print(f"  [shadow {s:02d}/{a.n_shadows - 1}] " + " ".join(cmd[1:]))
        if a.dry_run:
            continue
        r = subprocess.run(cmd, cwd=_SIM)
        if r.returncode != 0 or not ckpt.exists():
            raise SystemExit(
                f"[FATAL] shadow {s} failed (exit {r.returncode}). Fix it and "
                f"rerun — completed shadows are skipped, so nothing is lost. "
                f"Attacking with a partial shadow set biases the fitted "
                f"Gaussians toward whichever shadows happened to succeed.")
        done += 1
    print(f"\n  trained {done}, already present {skipped}")


# ── phase 3: scoring ────────────────────────────────────────────────────────

@torch.no_grad()
def score_patients(model, ds, groups, device, class_weight, max_windows):
    """Per-patient (phi, loss). phi is the logit-scaled confidence of Carlini."""
    model.eval()
    cw = class_weight.to(device) if class_weight is not None else None
    phi_out, loss_out = [], []
    for g in groups:
        g = g[:max_windows]
        xa = torch.stack([ds[int(i)][0] for i in g]).to(device)
        xb = torch.stack([ds[int(i)][1] for i in g]).to(device)
        y = torch.tensor([int(ds[int(i)][3]) for i in g], device=device)
        z = model(xa, xb).float()

        # phi = z_y - logsumexp_{j != y} z_j, the stable form of
        # log(p_y / (1 - p_y)). Masking the true class with -inf keeps it exact
        # instead of going through a softmax and back, which loses the tails
        # that the low-FPR corner of the attack lives in.
        zy = z.gather(1, y[:, None]).squeeze(1)
        zo = z.masked_fill(
            torch.zeros_like(z, dtype=torch.bool).scatter_(1, y[:, None], True),
            float("-inf"))
        phi_out.append(float((zy - torch.logsumexp(zo, dim=1)).mean()))
        loss_out.append(float(torch.nn.functional.cross_entropy(
            z, y, weight=cw, reduction="mean")))
    return np.asarray(phi_out), np.asarray(loss_out)


def build_model(spec, device):
    kw = {"n_channels_a": spec.n_channels_a}
    if spec.modality_b != "image":
        kw.update(modality_b="features", feat_b_dim=spec.feat_b_dim)
    return build_hfl_mm_hc(n_classes=spec.n_classes, **kw).to(device)


def load_into(model, ckpt, device):
    sd = torch.load(ckpt, map_location=device, weights_only=False)
    sd = sd.get("model_state", sd) if isinstance(sd, dict) else sd
    model.load_state_dict(sd, strict=False)
    return model


def score_all(a, spec, ds, device, cw, groups, out_root: Path, n_eval: int):
    """Score every shadow on the evaluated patients, caching per shadow."""
    model = build_model(spec, device)
    phis = np.full((a.n_shadows, n_eval), np.nan)
    for s in range(a.n_shadows):
        cache = out_root / f"shadow_{s:02d}" / "scores.npz"
        if cache.exists() and not a.rescore:
            z = np.load(cache)
            if len(z["phi"]) == n_eval:
                phis[s] = z["phi"]
                continue
        ckpt = out_root / f"shadow_{s:02d}" / "ckpt.pt"
        if not ckpt.exists():
            raise SystemExit(f"[FATAL] {ckpt} missing — run --phase train first.")
        load_into(model, ckpt, device)
        phi, loss = score_patients(model, ds, groups, device, cw, a.max_windows)
        np.savez(cache, phi=phi, loss=loss)
        phis[s] = phi
        print(f"  shadow {s:02d} scored  (phi mean {phi.mean():+.3f})")
    return phis


# ── phase 4: the likelihood ratio ───────────────────────────────────────────

def _norm_logpdf(x, mu, sd):
    return -0.5 * ((x - mu) / sd) ** 2 - np.log(sd) - 0.5 * math.log(2 * math.pi)


def lira_scores(phi_target, phi_shadow, in_mask, floor=1e-3):
    """Membership scores under each LiRA variant. Higher = more member-like.

    in_mask[s, p] is True when patient p was a member of shadow s, so the IN
    and OUT Gaussians are fitted from disjoint sets of shadows for every
    patient independently.
    """
    n_s, n_p = phi_shadow.shape
    mu_i = np.full(n_p, np.nan); sd_i = np.full(n_p, np.nan)
    mu_o = np.full(n_p, np.nan); sd_o = np.full(n_p, np.nan)
    for p in range(n_p):
        vi = phi_shadow[in_mask[:, p], p]
        vo = phi_shadow[~in_mask[:, p], p]
        vi = vi[~np.isnan(vi)]; vo = vo[~np.isnan(vo)]
        if len(vi):
            mu_i[p] = vi.mean()
            sd_i[p] = vi.std(ddof=1) if len(vi) > 1 else np.nan
        if len(vo):
            mu_o[p] = vo.mean()
            sd_o[p] = vo.std(ddof=1) if len(vo) > 1 else np.nan

    # Pooled (global) variance: with ~8 shadows a side, a per-patient sd is
    # itself noisy enough to dominate the ratio. Carlini's fixed-variance
    # variant trades per-patient specificity for a far steadier estimate.
    gsd_i = float(np.nanmean(sd_i)) if np.isfinite(sd_i).any() else 1.0
    gsd_o = float(np.nanmean(sd_o)) if np.isfinite(sd_o).any() else 1.0
    gsd_i, gsd_o = max(gsd_i, floor), max(gsd_o, floor)

    si = np.where(np.isfinite(sd_i), np.maximum(sd_i, floor), gsd_i)
    so = np.where(np.isfinite(sd_o), np.maximum(sd_o, floor), gsd_o)
    mi = np.where(np.isfinite(mu_i), mu_i, np.nanmean(mu_i))
    mo = np.where(np.isfinite(mu_o), mu_o, np.nanmean(mu_o))

    return {
        # NOT an attack — the confound floor. mo is the OUT-shadow mean, so it
        # is a pure per-patient difficulty estimate that never touches the
        # target model. Shadow membership is randomised over the whole patient
        # universe, so this should score 0.5; anything above it is a property
        # of how the evaluated split was drawn, not of what the target
        # memorised. Measured 0.5731 on the eps=16 record arm, i.e. ABOVE the
        # loss threshold's 0.5465 — which is why every attack AUC has to be
        # read against this number rather than against 0.5.
        "difficulty":     mo,
        "lira_offline":   (phi_target - mo) / so,
        "lira_online":    _norm_logpdf(phi_target, mi, si)
                          - _norm_logpdf(phi_target, mo, so),
        "lira_online_gv": _norm_logpdf(phi_target, mi, gsd_i)
                          - _norm_logpdf(phi_target, mo, gsd_o),
    }


# Keys returned by lira_scores that are diagnostics rather than attacks. They
# are scored and reported like everything else, but must never win "strongest
# attack" — an adversary cannot mount the difficulty floor, it is what the
# adversary has to beat.
_NOT_ATTACKS = ("difficulty",)


def tpr_at_fpr(y, s, target_fpr):
    """TPR at a fixed low FPR — the metric AUC hides.

    Interpolated on the ROC, and reported as nan when the attack has too few
    non-members to resolve the requested FPR at all (with 600 non-members,
    0.1 % FPR is below the resolution of the curve and any number quoted there
    would be an artefact of interpolation).
    """
    from sklearn.metrics import roc_curve
    if len(y) - int(sum(y)) < 1 / target_fpr:
        return float("nan")
    fpr, tpr, _ = roc_curve(y, s)
    return float(np.interp(target_fpr, fpr, tpr))


# ── driver ──────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--arms", nargs="+", default=["sample", "patient"],
                    help="checkpoint arms to attack; each gets its OWN shadow "
                         "set, because a shadow must be trained the way its "
                         "target was")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
    ap.add_argument("--target_dir", default=None,
                    help="default: results/phase5/patient_dp/<dataset>")
    ap.add_argument("--ckpt_pattern", default="ckpt_{arm}_{seed}.pt")
    ap.add_argument("--out_dir", default=None,
                    help="default: results/phase5/lira/<dataset>")
    ap.add_argument("--n_shadows", type=int, default=16,
                    help="more is better: the per-patient Gaussians are fitted "
                         "from ~half this many samples each")
    ap.add_argument("--member_frac", type=float, default=0.5,
                    help="fraction of patients IN each shadow (0.5 maximises "
                         "the number of patients with both IN and OUT models)")
    ap.add_argument("--split_seed", type=int, default=7)
    ap.add_argument("--max_patients", type=int, default=600,
                    help="patients per group; equal-sized member and "
                         "non-member sets keep the AUC unbiased")
    ap.add_argument("--max_windows", type=int, default=64,
                    help="windows per patient (matches membership_inference.py "
                         "so the loss baseline is comparable)")
    ap.add_argument("--phase", default="splits,train,score,attack",
                    help="comma-separated subset of splits,train,score,attack")
    ap.add_argument("--dry_run", action="store_true",
                    help="print the shadow training commands without running")
    ap.add_argument("--rescore", action="store_true",
                    help="ignore cached shadow scores")
    a = ap.parse_args()

    # Shadow training runs for hours and its progress lines are the only way to
    # see where it is. Block buffering holds them until exit, so a redirected
    # log shows the trainer subprocess talking and this driver apparently idle.
    sys.stdout.reconfigure(line_buffering=True)

    phases = {p.strip() for p in a.phase.split(",") if p.strip()}
    spec = get_spec(a.dataset)
    target_dir = Path(a.target_dir) if a.target_dir else \
        _SIM / "results" / "phase5" / "patient_dp" / a.dataset
    if not target_dir.is_absolute():
        target_dir = _SIM / target_dir
    out_dir = Path(a.out_dir) if a.out_dir else \
        _SIM / "results" / "phase5" / "lira" / a.dataset
    if not out_dir.is_absolute():
        out_dir = _SIM / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cid_path = _SIM / spec.data_dir / "meta" / "case_ids.npy"
    if not cid_path.exists():
        raise SystemExit(f"[FATAL] no case ids at {cid_path}: without patient "
                         f"identity there is no patient-level attack to mount.")
    case_ids = np.load(cid_path)
    pdir = _SIM / spec.partition_dir
    with open(pdir / "partition_meta.json") as f:
        meta = json.load(f)

    part = load_partition(pdir, meta["n_devices"])
    windows, dev_of, split_of = patient_table(part, case_ids)

    print("=" * 74)
    print(f"LiRA PATIENT-LEVEL MEMBERSHIP INFERENCE — {a.dataset}")
    print("=" * 74)

    # Evaluated patients: members are the released TRAIN patients, non-members
    # the released TEST patients. Val patients stay out of the evaluation —
    # model selection ran on them, which is a second, different leak, and
    # mixing it in would confound the question being asked. They still take
    # part in shadow training.
    mem_pool = sorted(c for c, sp in split_of.items() if sp == "train")
    non_pool = sorted(c for c, sp in split_of.items() if sp == "test")
    rng = np.random.default_rng(0)
    n = min(a.max_patients, len(mem_pool), len(non_pool))
    mem = [int(c) for c in rng.choice(mem_pool, n, replace=False)]
    non = [int(c) for c in rng.choice(non_pool, n, replace=False)]
    eval_pat = mem + non
    y_true = np.r_[np.ones(len(mem)), np.zeros(len(non))]
    groups = [windows[c] for c in eval_pat]
    print(f"  evaluated: {len(mem)} members + {len(non)} non-members "
          f"(of {len(mem_pool):,} / {len(non_pool):,} available)")

    rows, summary = [], {}
    for arm in a.arms:
        root = out_dir / "shadows" / arm
        root.mkdir(parents=True, exist_ok=True)
        print(f"\n── arm: {arm} " + "─" * (60 - len(arm)))

        if "splits" in phases:
            build_shadow_splits(a, spec, meta, windows, dev_of, root)
        if "train" in phases:
            train_shadows(a, arm, root, target_dir)
        if not {"score", "attack"} & phases:
            continue
        if a.dry_run:
            continue

        mfile = root / "membership.npz"
        if not mfile.exists():
            raise SystemExit(f"[FATAL] {mfile} missing — run --phase splits.")
        z = np.load(mfile)
        pos = {int(c): i for i, c in enumerate(z["patients"])}
        in_mask = z["mask"][:, [pos[c] for c in eval_pat]]

        device = get_device()
        ds = spec.build_full(str(_SIM / spec.data_dir))
        # Same class weighting the models trained under, so the loss baseline
        # reproduces what membership_inference.py measured.
        tr_all = np.concatenate([part[(d, "train")] for d in range(meta["n_devices"])])
        ytr = np.array([int(ds[int(i)][3]) for i in tr_all[:20000]])
        cnt = np.bincount(ytr, minlength=spec.n_classes).astype(float)
        cw = torch.tensor(len(ytr) / (spec.n_classes * np.maximum(cnt, 1)),
                          dtype=torch.float32)

        phi_shadow = score_all(a, spec, ds, device, cw, groups, root, len(eval_pat))

        model = build_model(spec, device)
        per_attack = {}
        for seed in a.seeds:
            ckpt = target_dir / a.ckpt_pattern.format(arm=arm, seed=seed)
            if not ckpt.exists():
                print(f"  [skip] {ckpt.name} missing")
                continue
            load_into(model, ckpt, device)
            phi_t, loss_t = score_patients(model, ds, groups, device, cw,
                                           a.max_windows)
            # Every score here is oriented so that HIGHER means more
            # member-like: the loss baseline is negated once, at source.
            cand = {"loss": -loss_t, **lira_scores(phi_t, phi_shadow, in_mask)}
            aucs = {}
            for name, s in cand.items():
                auc = aucs[name] = auc_scores(y_true, s)
                r = {"dataset": a.dataset, "arm": arm, "attack": name,
                     "seed": seed, "attack_auc": auc,
                     "tpr_at_1pct_fpr": tpr_at_fpr(y_true, s, 0.01),
                     "tpr_at_0.1pct_fpr": tpr_at_fpr(y_true, s, 0.001),
                     "n_shadows": a.n_shadows,
                     "n_members": len(mem), "n_nonmembers": len(non)}
                rows.append(r)
                per_attack.setdefault(name, []).append(auc)
            print(f"  seed {seed}: " + "  ".join(
                f"{k} {v:.4f}" for k, v in aucs.items()))

        summary[arm] = {k: mean_ci(v) for k, v in per_attack.items()}

    if not rows:
        print("\nnothing scored.")
        return 0

    # Arms are attacked in separate invocations because each needs its own
    # shadow set. A per-dataset filename would mean the second invocation
    # silently overwrote the first — and the positive control is the run whose
    # result everything else is judged against.
    out_csv = out_dir / f"lira_{a.dataset}_{'_'.join(a.arms)}.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # ── report ──────────────────────────────────────────────────────
    print("\n" + "=" * 74)
    print("  RESULTS — mean attack AUC (95 % t-CI over seeds)")
    print("=" * 74)
    print(f"  {'arm':<12}{'attack':<17}{'AUC':>18}{'TPR@1%':>10}{'TPR@0.1%':>10}")
    print("  " + "-" * 65)
    for arm, per in summary.items():
        for name, (m, half, k) in per.items():
            t1 = np.nanmean([r["tpr_at_1pct_fpr"] for r in rows
                             if r["arm"] == arm and r["attack"] == name])
            t01 = np.nanmean([r["tpr_at_0.1pct_fpr"] for r in rows
                              if r["arm"] == arm and r["attack"] == name])
            ci = f"[{m-half:.4f}, {m+half:.4f}]" if half == half else "     —     "
            print(f"  {arm:<12}{name:<17}{m:>8.4f} {ci:<20}"
                  f"{t1:>7.3f}{t01:>10.3f}")

    best = {arm: max(((k, v) for k, v in per.items() if k not in _NOT_ATTACKS),
                     key=lambda kv: kv[1][0])
            for arm, per in summary.items()
            if any(k not in _NOT_ATTACKS for k in per)}
    print("\n" + "=" * 74)
    print("  VERDICT — strongest attack per arm, against the confound floor")
    print("=" * 74)
    print("  An attack only demonstrates memorisation if it beats the floor.")
    print("  The floor uses NO target model: it ranks patients by shadow")
    print("  difficulty alone, so it measures how the split was drawn.\n")
    for arm, (name, (m, half, k)) in best.items():
        floor = summary[arm].get("difficulty", (float("nan"),))[0]
        margin = m - floor
        if margin != margin:                       # floor unavailable
            note = ""
        elif margin <= 0:
            note = "   NO SIGNAL — attack does not beat difficulty"
        elif margin < 0.02:
            note = "   marginal over difficulty"
        else:
            note = "   beats difficulty"
        print(f"    {arm:<12} attack {m:.4f} via {name:<15}"
              f" floor {floor:.4f}   margin {margin:+.4f}{note}")

    # Is LiRA actually stronger than the loss threshold it replaces? If not,
    # the null is a null of the whole attack class, not of LiRA specifically.
    for arm, per in summary.items():
        if "loss" not in per:
            continue
        lira_best = max((v[0] for k, v in per.items()
                         if k != "loss" and k not in _NOT_ATTACKS), default=None)
        if lira_best is None:
            continue
        d = lira_best - per["loss"][0]
        print(f"    {arm:<12} LiRA - loss = {d:+.4f}"
              + ("   (LiRA adds nothing here)" if d <= 0.002 else ""))

    if len(summary) == 2 and {"sample", "patient"} <= set(summary):
        rec = [r["attack_auc"] for r in rows if r["arm"] == "sample"
               and r["attack"] == best["sample"][0]]
        pat = [r["attack_auc"] for r in rows if r["arm"] == "patient"
               and r["attack"] == best["patient"][0]]
        t = paired_test(pat, rec)          # rec - pat, paired by seed
        if t:
            print(f"\n    record - patient = {t['mean_diff']:+.4f} "
                  f"[{t['ci_low']:+.4f}, {t['ci_high']:+.4f}]  "
                  f"{'excludes' if t['significant'] else 'includes'} zero")

    print(f"""
  HOW TO READ THIS
    The claim under test is that a record-level guarantee fails to protect a
    PATIENT. It is supported only if the record-level arm leaks materially more
    than the patient-level arm — in AUC or in the low-FPR corner.

    Before accepting a null, check the positive control: the head-only no-DP
    arm must exceed the 0.5847 the loss threshold already reached there. An
    attack that cannot beat a threshold on a model known to memorise is not
    evidence of absence.

  Written: {out_csv}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
