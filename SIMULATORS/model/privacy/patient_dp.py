"""
patient_dp.py — PATIENT-level (user-level) differential privacy.

WHY THIS EXISTS
---------------
Standard DP-SGD, including Opacus, clips and accounts PER SAMPLE. In this
project a sample is a 10-minute window, and every patient contributes several
of them:

    VitalDB: 48,712 windows / 6,257 cases
             mean 7.79 windows per case, median 8, max 8
             100 % of cases contribute more than one window

So an epsilon obtained from per-sample DP-SGD answers

    "was this 10-minute WINDOW in the training set?"

while the clinical guarantee the system is supposed to make is

    "was this PATIENT in the training set?"

Those differ. Removing one patient perturbs ~8 training records, not one.
Converting a window-level guarantee to a patient-level one costs group
privacy: for (eps, delta)-DP a group of size k degrades to roughly
(k*eps, k*e^{(k-1)eps}*delta). At k=8 and eps=1 that is eps~8 with
delta~0.09 — not a usable clinical claim.

Reporting a per-sample epsilon as though it were a patient guarantee would be
the single most consequential overstatement this project could make, so this
module implements the guarantee directly instead.

HOW IT WORKS
------------
Per-patient gradient descent (user-level DP-SGD, Abadi-style but with the
group as the unit):

  1. Poisson-sample PATIENTS (not windows) with rate q = B / n_patients.
  2. For each selected patient, run all of that patient's windows, sum their
     gradients into ONE per-patient gradient.
  3. Clip that per-patient gradient to norm C. This is the step that makes
     the sensitivity patient-level: one patient can move the sum by at most C
     no matter how many windows they contributed.
  4. Sum the clipped per-patient gradients, add N(0, sigma^2 C^2 I) ONCE.
  5. Step.

Accounting then uses q = B / n_patients and the same RDP accountant, so the
reported epsilon is patient-level by construction rather than by a group
privacy conversion applied afterwards.

WHAT IT COSTS
-------------
Fewer effective units per step (6,257 patients rather than 48,712 windows),
and a patient with many windows has its summed gradient clipped harder. That
cost is real and is the point of measuring it: "what does a patient-level
guarantee cost over a window-level one on genuinely paired clinical
multimodal data" is a number this field does not have.
"""

from typing import Dict, List, Optional, Sequence, Union

import numpy as np
import torch
import torch.nn as nn


# ─────────────────────────────────────────────────────────────────────
# Grouping
# ─────────────────────────────────────────────────────────────────────

def group_indices_by_patient(sample_indices: Union[Sequence[int], np.ndarray],
                             case_ids: np.ndarray) -> List[np.ndarray]:
    """Partition dataset indices into per-patient groups.

    `case_ids` is the per-window array written by the preprocessor; two
    windows share a patient iff they share a case id. Groups preserve the
    caller's index space so they can be used directly with a Subset.
    """
    idx = np.asarray(sample_indices)
    cids = case_ids[idx]
    order = np.argsort(cids, kind="stable")
    idx_sorted, cids_sorted = idx[order], cids[order]
    boundaries = np.flatnonzero(np.diff(cids_sorted)) + 1
    return np.split(idx_sorted, boundaries)


def patient_level_noise_multiplier(target_epsilon: float,
                                   target_delta: float,
                                   n_patients: int,
                                   patients_per_batch: int,
                                   n_fl_calls: int,
                                   local_epochs: int = 1) -> float:
    """Sigma for a PATIENT-level budget.

    The only difference from the per-sample calibration is that the sampling
    rate is patients-per-batch over TOTAL PATIENTS, not samples over samples.
    That single substitution is what makes the resulting epsilon a statement
    about patients. Using the window counts here while clipping per patient
    would silently report a budget that matches neither unit.
    """
    from opacus.accountants.utils import get_noise_multiplier

    steps_per_call = max(n_patients // max(patients_per_batch, 1), 1)
    total_steps = n_fl_calls * local_epochs * steps_per_call
    q = min(patients_per_batch / max(n_patients, 1), 1.0)
    sigma = get_noise_multiplier(target_epsilon=target_epsilon,
                                 target_delta=target_delta,
                                 sample_rate=q, steps=total_steps)
    print(f"[patient-DP] eps={target_epsilon} delta={target_delta} | "
          f"patients={n_patients} q={q:.5f} steps={total_steps} -> sigma={sigma:.4f}")
    return sigma


# ─────────────────────────────────────────────────────────────────────
# Accountant
# ─────────────────────────────────────────────────────────────────────

class PatientPrivacyAccountant:
    """Cumulative patient-level RDP accounting across FL rounds.

    ONE instance per client for that client's whole lifetime. Creating a fresh
    accountant each round drops cross-round composition and reports a budget
    far smaller than the one actually spent — the same defect this project
    already fixed once on the per-sample path.
    """

    def __init__(self, sample_rate: float, noise_multiplier: float):
        from opacus.accountants import RDPAccountant
        self._acct = RDPAccountant()
        self.sample_rate = sample_rate
        self.noise_multiplier = noise_multiplier
        self.steps = 0

    def step(self, n: int = 1):
        for _ in range(n):
            self._acct.step(noise_multiplier=self.noise_multiplier,
                            sample_rate=self.sample_rate)
        self.steps += n

    def epsilon(self, delta: float = 1e-5) -> float:
        if self.steps == 0:
            return 0.0
        return float(self._acct.get_epsilon(delta=delta))


# ─────────────────────────────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────────────────────────────

def _flat_grad(params) -> torch.Tensor:
    return torch.cat([p.grad.detach().reshape(-1) if p.grad is not None
                      else torch.zeros(p.numel(), device=p.device)
                      for p in params])


def _assign_flat(params, flat: torch.Tensor):
    off = 0
    for p in params:
        n = p.numel()
        p.grad = flat[off:off + n].view_as(p).clone()
        off += n


def patient_level_dp_train(model: nn.Module,
                           dataset,
                           patient_groups: List[np.ndarray],
                           device: torch.device,
                           noise_multiplier: float,
                           max_grad_norm: float,
                           lr: float,
                           n_epochs: int = 1,
                           patients_per_batch: int = 16,
                           accountant: Optional[PatientPrivacyAccountant] = None,
                           class_weight: Optional[torch.Tensor] = None,
                           max_windows_per_patient: int = 64,
                           generator: Optional[torch.Generator] = None) -> Dict:
    """One local training call under a PATIENT-level guarantee.

    `patient_groups[i]` holds the dataset indices belonging to patient i.
    Sensitivity is enforced by clipping each patient's SUMMED gradient, so a
    patient's influence is bounded by `max_grad_norm` regardless of how many
    windows they contributed.
    """
    params = [p for p in model.parameters() if p.requires_grad]
    if not params:
        raise ValueError("patient_level_dp_train: no trainable parameters — "
                         "under --freeze_encoders the head must stay trainable.")

    opt = torch.optim.Adam(params, lr=lr, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss(
        weight=class_weight.to(device) if class_weight is not None else None)

    n_pat = len(patient_groups)
    q = min(patients_per_batch / max(n_pat, 1), 1.0)
    steps_per_epoch = max(n_pat // max(patients_per_batch, 1), 1)
    total_loss, total_seen, n_steps, n_pat_seen = 0.0, 0, 0, 0
    model.train()

    for _ in range(n_epochs):
        for _ in range(steps_per_epoch):
            # ── Poisson sampling over PATIENTS ───────────────────────
            # Poisson (not fixed-size) sampling is what the RDP accountant's
            # subsampled-Gaussian analysis assumes. A fixed-size shuffle is a
            # different mechanism and its epsilon would not be the one we
            # report.
            mask = torch.rand(n_pat, generator=generator) < q
            chosen = torch.nonzero(mask, as_tuple=False).flatten().tolist()
            if not chosen:
                continue

            summed = torch.zeros(sum(p.numel() for p in params), device=device)

            for pi in chosen:
                gi = patient_groups[pi]
                if len(gi) == 0:
                    continue
                # Cap windows per patient so one unusually long record cannot
                # dominate compute. It does NOT affect the guarantee — the
                # clip already bounds a patient's influence — only cost.
                if len(gi) > max_windows_per_patient:
                    gi = gi[:max_windows_per_patient]

                opt.zero_grad(set_to_none=False)
                xa = torch.stack([dataset[int(j)][0] for j in gi]).to(device)
                xb = torch.stack([dataset[int(j)][1] for j in gi]).to(device)
                y = torch.tensor([int(dataset[int(j)][3]) for j in gi],
                                 device=device)
                # SUM, not mean: the per-patient gradient is that patient's
                # total contribution, which is exactly what must be clipped.
                loss = loss_fn(model(xa, xb), y) * len(gi)
                loss.backward()

                g = _flat_grad(params)
                nrm = g.norm(2)
                g = g * min(1.0, max_grad_norm / (nrm + 1e-6))   # per-PATIENT clip
                summed += g

                # Divide by len(gi) to recover mean CE for this patient — the
                # loss was scaled by len(gi) above so the SUM could be clipped.
                total_loss += float(loss.detach()) / max(len(gi), 1)
                total_seen += len(gi)
                n_pat_seen += 1

            # ── one noise draw per step, scaled to the patient clip ──
            noise = torch.normal(0.0, noise_multiplier * max_grad_norm,
                                 size=summed.shape, device=device)
            avg = (summed + noise) / max(len(chosen), 1)

            opt.zero_grad(set_to_none=False)
            _assign_flat(params, avg)
            opt.step()
            n_steps += 1
            if accountant is not None:
                accountant.step()

    eps = accountant.epsilon() if accountant is not None else float("nan")
    # Per-PATIENT mean, so this is directly comparable to the per-sample
    # arms' reported loss rather than scaled by the batch width.
    return {"loss": total_loss / max(n_pat_seen, 1),
            "epsilon_spent": eps,
            "n_samples": total_seen,
            "n_steps": n_steps,
            "n_patients": n_pat,
            "sample_rate": q,
            "dp": True,
            "dp_unit": "patient"}


if __name__ == "__main__":
    # Self-check on the grouping logic only — no model required.
    cids = np.array([5, 5, 5, 7, 7, 9, 9, 9, 9])
    groups = group_indices_by_patient(np.arange(len(cids)), cids)
    assert len(groups) == 3, groups
    assert sorted(len(g) for g in groups) == [2, 3, 4], groups
    print("group_indices_by_patient OK:", [g.tolist() for g in groups])
