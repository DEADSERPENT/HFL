"""
ASWA — Adaptive Self-Weighted Aggregation (PHANTOM-FL Innovation IP-3)

Plain FedAvg weights each edge/client purely by how much data it holds
(n_e / N). That treats a cluster with 200 noisy, hard-to-fit samples the
same as a cluster with 200 clean, well-fit ones. ASWA re-weights each edge
by BOTH its data volume and a "quality" signal — how well that edge's local
training actually converged this round — so a cluster whose clients are
struggling (high local loss, e.g. because DP noise or non-IID skew hit it
harder this round) contributes less to the global average than one that
converged cleanly, instead of always contributing proportionally to raw
sample count regardless of fit quality.
"""

from typing import Dict, List


def compute_aswa_weights(edge_sizes: List[int], edge_losses: List[float],
                          temperature: float = 1.0) -> List[float]:
    """
    Combine data volume and inverse-loss quality into cloud aggregation
    weights, normalized to sum to 1.

    quality_e = 1 / (mean_local_loss_e + eps)   -- lower loss -> higher weight
    weight_e  ∝ n_e * quality_e ** temperature

    temperature=0 recovers plain sample-weighted FedAvg (quality ignored).
    temperature=1.0 (default) is a moderate quality tilt; higher values make
    the re-weighting more aggressive.
    """
    eps = 1e-6
    if temperature == 0:
        raw = [float(n) for n in edge_sizes]
    else:
        raw = [
            n * (1.0 / (loss + eps)) ** temperature
            for n, loss in zip(edge_sizes, edge_losses)
        ]
    total = sum(raw)
    if total <= 0:
        # Degenerate case (e.g. all losses huge / edges empty): fall back to
        # plain sample weighting rather than dividing by ~0.
        total_n = sum(edge_sizes) or 1
        return [n / total_n for n in edge_sizes]
    return [r / total for r in raw]


def mean_edge_loss(edge_client_losses: Dict[int, List[float]], edge_id: int) -> float:
    losses = edge_client_losses.get(edge_id, [])
    return sum(losses) / len(losses) if losses else 0.0
