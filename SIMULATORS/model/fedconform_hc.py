"""
IP-9: FedConform-HC — Federated Conformal Prediction for Healthcare FL
Provides statistically rigorous prediction sets with coverage guarantee:
    P(Y_true in C(X)) >= 1 - alpha
Phase 5 implementation.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple, Optional


class ConformScoreComputer(nn.Module):
    """Computes nonconformity scores on calibration data."""

    def __init__(self, score_type: str = "lac"):
        super().__init__()
        self.score_type = score_type  # "lac" = 1 - p_true

    @torch.no_grad()
    def compute(self, logits: torch.Tensor,
                labels: torch.Tensor) -> torch.Tensor:
        """
        logits: [N, C] raw model output
        labels: [N]    ground truth class indices
        returns: [N]   nonconformity scores in [0,1]
        """
        probs = torch.softmax(logits, dim=-1)
        if self.score_type == "lac":
            scores = 1.0 - probs[torch.arange(len(labels)), labels]
        elif self.score_type == "aps":
            # Adaptive Prediction Sets (more efficient for skewed distributions)
            sorted_probs, sorted_idx = probs.sort(dim=-1, descending=True)
            cum_probs = sorted_probs.cumsum(dim=-1)
            # score = cum prob up to and including true class
            ranks = (sorted_idx == labels.unsqueeze(1)).nonzero(as_tuple=True)[1]
            scores = cum_probs[torch.arange(len(labels)), ranks]
        else:
            raise ValueError(f"Unknown score_type: {self.score_type}")
        return scores


class LocalConformCalibrator:
    """Per-device calibration: computes DP-noised quantile from local cal set."""

    def __init__(self, alpha: float = 0.1, epsilon_conf: float = 0.1,
                 score_type: str = "lac"):
        self.alpha = alpha
        self.epsilon_conf = epsilon_conf
        self.scorer = ConformScoreComputer(score_type)

    def calibrate(self, model: nn.Module, cal_loader,
                  device: torch.device) -> float:
        """
        Run forward pass on calibration data, compute DP-noised quantile.
        Returns: q_tilde (noised local quantile)
        """
        model.eval()
        all_scores = []
        with torch.no_grad():
            for batch in cal_loader:
                ecg, cxr, labels = batch
                ecg   = ecg.to(device, non_blocking=True)
                cxr   = cxr.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                logits = model(ecg, cxr)
                scores = self.scorer.compute(logits, labels)
                all_scores.append(scores.cpu())

        scores_np = torch.cat(all_scores).numpy()
        n = len(scores_np)
        level = np.ceil((1 - self.alpha) * (1 + 1.0 / n)) / (1 + 1.0 / n)
        level = min(level, 1.0)
        q_local = float(np.quantile(scores_np, level))

        # DP noise: Laplace(0, sensitivity/epsilon_conf)
        # sensitivity of quantile = range of scores = 1.0 for LAC
        sensitivity = 1.0
        noise_scale = sensitivity / self.epsilon_conf
        noise = np.random.laplace(0, noise_scale)
        q_tilde = float(np.clip(q_local + noise, 0.0, 1.0))
        return q_tilde


class FedConformAggregator:
    """Aggregates DP-noised quantiles from devices → global quantile."""

    @staticmethod
    def edge_aggregate(q_tildes: List[float]) -> float:
        return float(np.median(q_tildes))

    @staticmethod
    def cloud_aggregate(q_edges: List[float]) -> float:
        return float(np.mean(q_edges))


class FedConformHC(nn.Module):
    """
    IP-9: FedConform-HC Wrapper
    Wraps the base HFL-MM-HC classifier with federated conformal prediction.
    Produces prediction SETS instead of single predictions.

    Usage:
        conform = FedConformHC(base_model, alpha=0.1)
        conform.set_quantile(q_global)  # after federated calibration
        output = conform(ecg, cxr)
        # output['prediction']      = argmax class
        # output['prediction_set']  = list of plausible classes
        # output['set_size']        = number of classes in set
        # output['coverage_flag']   = True if set_size > 1 (uncertain)
    """

    def __init__(self, base_model: nn.Module, alpha: float = 0.1,
                 n_classes: int = 5):
        super().__init__()
        self.base_model = base_model
        self.alpha = alpha
        self.n_classes = n_classes
        self.register_buffer('q_global', torch.tensor(0.9))

    def set_quantile(self, q: float):
        self.q_global.fill_(q)

    def forward(self, ecg: torch.Tensor, cxr: torch.Tensor,
                return_set: bool = True) -> Dict:
        logits = self.base_model(ecg, cxr)
        probs = torch.softmax(logits, dim=-1)
        prediction = probs.argmax(dim=-1)

        if not return_set:
            return {"logits": logits, "prediction": prediction}

        # Prediction set: include class y if score(y) <= q_global
        # Score for class y = 1 - prob[y]
        scores = 1.0 - probs              # [B, C]
        in_set = scores <= self.q_global  # [B, C] boolean mask
        set_size = in_set.sum(dim=-1)     # [B]

        # Ensure prediction always in set (override if needed)
        in_set[torch.arange(len(prediction)), prediction] = True

        return {
            "logits": logits,
            "probs": probs,
            "prediction": prediction,
            "prediction_set_mask": in_set,
            "set_size": set_size,
            "coverage_flag": (set_size > 1),
            "q_global": self.q_global.item(),
        }

    def clinical_triage(self, output: Dict) -> List[str]:
        """
        Maps set_size to clinical action:
          1 → "CONFIDENT: proceed with AI recommendation"
          2 → "REVIEW: secondary diagnosis possible, confirm"
          3+ → "REFER: insufficient confidence, physician required"
        """
        actions = []
        for sz in output["set_size"].tolist():
            if sz == 1:
                actions.append("CONFIDENT")
            elif sz == 2:
                actions.append("REVIEW")
            else:
                actions.append("REFER")
        return actions

    def get_federated_calibrator(self, epsilon_conf: float = 0.1):
        return LocalConformCalibrator(self.alpha, epsilon_conf)


class ConformCoverageMonitor:
    """Tracks empirical coverage during evaluation (sanity check)."""

    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha
        self.n_total = 0
        self.n_covered = 0
        self.set_sizes = []

    def update(self, output: Dict, labels: torch.Tensor):
        B = len(labels)
        for i in range(B):
            covered = output["prediction_set_mask"][i, labels[i]].item()
            self.n_covered += int(covered)
            self.set_sizes.append(output["set_size"][i].item())
        self.n_total += B

    def coverage(self) -> float:
        return self.n_covered / max(self.n_total, 1)

    def avg_set_size(self) -> float:
        return float(np.mean(self.set_sizes)) if self.set_sizes else 0.0

    def report(self) -> Dict:
        return {
            "empirical_coverage": self.coverage(),
            "target_coverage": 1 - self.alpha,
            "avg_set_size": self.avg_set_size(),
            "coverage_satisfied": self.coverage() >= (1 - self.alpha),
        }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from hfl_mm_model import HFLMMHC

    base = HFLMMHC(n_classes=5)
    model = FedConformHC(base, alpha=0.1, n_classes=5)
    model.set_quantile(0.85)

    ecg = torch.randn(4, 12, 1000)
    cxr = torch.randn(4, 3, 224, 224)
    out = model(ecg, cxr)

    print(f"Prediction:     {out['prediction']}")
    print(f"Set sizes:      {out['set_size']}")
    print(f"Coverage flags: {out['coverage_flag']}")
    print(f"q_global:       {out['q_global']:.3f}")
    print(f"Actions: {model.clinical_triage(out)}")
