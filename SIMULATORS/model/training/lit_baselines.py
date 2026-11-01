"""
lit_baselines.py — the two prior-art systems the paper compares against,
re-implemented from their published descriptions and run inside hfl_trainer.py
so that data, partitions, model, rounds, class weighting, model selection and
scoring are identical to the proposed system's. Only the mechanism moves.

HED-FL  De Rango et al., Pervasive Mob. Comput. 92 (2023) 101804.
        Hierarchical FedAvg with NO privacy mechanism and dense model upload.
        Static algorithm (their Alg. 1-3): K1 low-level rounds between devices
        and edge aggregators, then one high-level aggregation; the
        equivalent-round budget K1*KY equals ours (tau_e * rounds), and
        Static(5-10) is one of the two configurations the authors recommend.
        In each low-level round a fixed fraction of each group's devices is
        drawn at random (3 of 5 in their Table 1) to emulate disconnections.

FL2DP   Gu et al., IEEE Trans. Ind. Inf. 20(4) (2024) 5100-5111.
        Flat FL. Every per-example gradient coordinate is replaced by one of N
        candidates drawn by an exponential mechanism (their Eqs. 11-13,
        Alg. 1); a trusted shuffler then reassigns updates across client
        identities with probability proportional to exp(eps*sim/2) (Eqs.
        15-16, Alg. 2).

        NOTE ON THE GUARANTEE. The candidate set of Eq. 12 is built from the
        private gradient value itself: every candidate lies within |C| of it,
        on the side given by C = g^l(k) - g^(l-1)(k). Replacing one training
        example therefore changes the SUPPORT of the output, and an output that
        is possible under one dataset has probability zero under its neighbour.
        The ratio in the DP definition is unbounded, so the mechanism satisfies
        no finite epsilon; the epsilon it is run with is a nominal parameter.
        The audit (lira_attack.py) measures what it leaks in practice.

Choices the papers leave open are made in the baseline's favour and stated
where they are made.
"""
import math
from typing import Dict, List, Optional, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.func import functional_call, grad, vmap


# ─────────────────────────────────────────────────────────────────────────────
# HED-FL
# ─────────────────────────────────────────────────────────────────────────────

def hedfl_select(edge_assignments: Dict[int, List[int]], fraction: float,
                 rng: np.random.Generator) -> set:
    """Devices that train in one low-level round: a random `fraction` of every
    group, at least one per group (HED-FL Table 1: 3 of 5 per group)."""
    chosen = set()
    for devs in edge_assignments.values():
        k = max(1, int(round(fraction * len(devs))))
        chosen.update(int(d) for d in rng.choice(devs, size=k, replace=False))
    return chosen


def dense_uplink_bytes(model: nn.Module) -> int:
    """Both baselines upload the trained parameters uncompressed in float32.
    Only the trainable head is counted: the frozen encoders never change, and
    counting them would charge the baselines for traffic a sensible
    implementation of either would not send."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad) * 4


# ─────────────────────────────────────────────────────────────────────────────
# FL2DP — gradient perturbation (Alg. 1)
# ─────────────────────────────────────────────────────────────────────────────

def _exp_mech_offsets(c: torch.Tensor, scale: float, n: int) -> torch.Tensor:
    """Draw g_bar - g for every coordinate under Eqs. 12-13.

    Candidates are g + j*C/N, j = 1..N, at distance d_j = j*|C|/N, chosen with
    probability proportional to exp(-(eta*eps/2) * d_j). With a = scale*|C|/N
    that is a geometric law on {1..N} with ratio exp(-a), sampled here by its
    inverse CDF so the N candidates never have to be materialised (the head has
    5.6e5 parameters per example).
    """
    a = scale * c.abs() / n
    u = torch.rand_like(c)
    big = a > 1e-8
    a_safe = torch.where(big, a, torch.ones_like(a))
    # P(J <= j) = (1 - r^j) / (1 - r^N), r = exp(-a)
    j_geo = torch.ceil(torch.log1p(u * torch.expm1(-a_safe * n)) / (-a_safe))
    j_uni = torch.ceil(u * n)                     # a -> 0: uniform over 1..N
    j = torch.where(big, j_geo, j_uni).clamp_(1, n)
    return j * c / n


def fl2dp_local_train(model: nn.Module, loader, device: torch.device,
                      lr: float, epsilon: float, n_candidates: int,
                      class_weight: Optional[torch.Tensor] = None,
                      n_epochs: int = 1) -> Dict:
    """One FL2DP local training call over the trainable fusion head.

    Choices left open by the paper:
      * eta in Eq. 13 is the learning rate (it is the only eta in Alg. 1).
      * g^(l-1)(k) is the k-th example's gradient in the previous iteration of
        this call; at l = 0 it is zero, so C = g^0(k).
      * The perturbed batch gradient feeds the same Adam optimiser every other
        arm uses rather than plain SGD — Alg. 1's plain step at our learning
        rate trains far more slowly, which would penalise the baseline for a
        reason unrelated to its mechanism.
      * Class weighting enters each example's loss so the batch mean equals
        the weighted objective every other arm optimises.
    """
    head = model.fusion
    names = [n for n, p in head.named_parameters() if p.requires_grad]
    params = {n: p for n, p in head.named_parameters() if p.requires_grad}
    optimizer = torch.optim.Adam(list(params.values()), lr=lr, weight_decay=1e-4)
    cw = class_weight.to(device) if class_weight is not None else None
    scale = lr * epsilon / 2.0

    def loss_one(p, fa, fb, y, w):
        out = functional_call(head, p, (fa.unsqueeze(0), fb.unsqueeze(0)))
        return w * F.cross_entropy(out, y.unsqueeze(0))

    per_example_grad = vmap(grad(loss_one), in_dims=(None, 0, 0, 0, 0),
                            randomness="different")

    model.train()
    prev: Optional[Dict[str, torch.Tensor]] = None
    total_loss, total = 0.0, 0
    for _ in range(n_epochs):
        for xa, xb, _tab, y in loader:
            xa = xa.to(device, non_blocking=True)
            xb = xb.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            b = len(y)
            with torch.no_grad():
                fa, fb = model.encode(xa, xb)       # encoders are frozen
                w = (cw[y] * b / cw[y].sum()) if cw is not None \
                    else torch.ones(b, device=device)
            detached = {n: params[n].detach() for n in names}
            g = per_example_grad(detached, fa, fb, y, w)
            optimizer.zero_grad()
            for n in names:
                gp = prev[n] if (prev is not None and prev[n].shape == g[n].shape) \
                    else torch.zeros_like(g[n])
                noisy = g[n] + _exp_mech_offsets(g[n] - gp, scale, n_candidates)
                params[n].grad = noisy.mean(0)
            optimizer.step()
            prev = g
            with torch.no_grad():
                logits = model.fusion(fa, fb)
                total_loss += float((w * F.cross_entropy(
                    logits, y, reduction="none")).mean()) * b
            total += b
    return {"loss": total_loss / max(total, 1), "n_samples": total,
            # Nominal only (see module docstring); inf keeps the trainer's
            # budget-exhaustion stop from firing, as for the no-DP arm.
            "epsilon_spent": float("inf"), "epsilon_nominal": epsilon}


# ─────────────────────────────────────────────────────────────────────────────
# FL2DP — gradient shuffling (Alg. 2)
# ─────────────────────────────────────────────────────────────────────────────

def fl2dp_shuffle(updates: Sequence[torch.Tensor], epsilon: float,
                  weights: Sequence[float], rng: np.random.Generator) -> List[int]:
    """Return perm with perm[i] = index of the update client identity i receives.

    sim(Gi, Gj) = -(w1 * dist + w2 * (1 - cos)/2), each term in [0, 1] so sim
    lies in [-1, 0] as Eq. 15 requires (dist is normalised by the largest
    distance from Gi within the pool). Identity i draws j from the remaining
    pool with probability proportional to exp(eps * sim / 2) (Eq. 16), and j
    leaves the pool (Alg. 2, line 8).
    """
    g = torch.stack([u.float().flatten() for u in updates])
    dist = torch.cdist(g, g)
    nrm = g.norm(dim=1, keepdim=True).clamp_min(1e-12)
    cos = (g / nrm) @ (g / nrm).T
    w1, w2 = weights
    pool = list(range(len(updates)))
    perm = [-1] * len(updates)
    for i in rng.permutation(len(updates)):
        cand = torch.tensor(pool, device=g.device)
        dmax = dist[i, cand].max().clamp_min(1e-12)
        sim = -(w1 * dist[i, cand] / dmax + w2 * (1 - cos[i, cand]) / 2)
        p = torch.softmax(epsilon * sim / 2, dim=0).double().cpu().numpy()
        j = pool[int(rng.choice(len(pool), p=p / p.sum()))]
        perm[int(i)] = j
        pool.remove(j)
    return perm
