"""
FedKD-E — Edge-Level Knowledge Distillation (PHANTOM-FL Innovation IP-4)

Plain edge_fedavg only ever averages WEIGHTS. That throws away information
in how each client model actually behaves on data — two client models with
very different weights can still agree closely on what a given patient's
diagnosis should be, and plain weight-averaging doesn't preserve that
agreement. FedKD-E adds a short refinement pass after weight-averaging: the
averaged edge model (student) is fine-tuned for a few steps to match the
ensemble-averaged SOFT predictions (temperature-scaled logits) that this
edge's own client models produced on this edge's own calibration data —
distilling the clients' collective "opinion" into the averaged model, not
just their weights.

Scope/privacy note: this only uses data and models that already live inside
one edge's existing trust boundary (the same client updates and calibration
loaders edge_fedavg / FedConform-HC already use) — no new data or model
leaves a device, and nothing new is exposed to the cloud tier.
"""

import copy
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


@torch.no_grad()
def collect_teacher_soft_logits(local_model: nn.Module, distill_loader,
                                device, temperature: float,
                                max_batches: int = 1) -> Optional[torch.Tensor]:
    """
    Run a just-updated client model (before it's discarded) over a small
    slice of the edge's calibration data and return its temperature-scaled
    soft-label distribution, batch-order-aligned so multiple clients' outputs
    can be averaged into one ensemble teacher signal.
    """
    local_model.eval()
    logits_chunks = []
    for i, (ecg, cxr, _tab, _labels) in enumerate(distill_loader):
        if i >= max_batches:
            break
        logits = local_model(ecg.to(device, non_blocking=True),
                             cxr.to(device, non_blocking=True))
        logits_chunks.append(logits.cpu())
    if not logits_chunks:
        return None
    logits = torch.cat(logits_chunks, dim=0)
    return F.softmax(logits / temperature, dim=-1)


def edge_distill_refine(edge_state: Dict[str, torch.Tensor], model_builder,
                        teacher_soft_logits: List[torch.Tensor],
                        distill_loader, device, epochs: int = 3,
                        temperature: float = 3.0, lr: float = 1e-4,
                        max_batches: int = 1) -> Dict[str, torch.Tensor]:
    """
    Fine-tune the weight-averaged edge model to match the mean of its
    clients' soft-label outputs on the edge's own calibration data.

    teacher_soft_logits: one tensor per client that contributed to this
    edge's FedAvg this round (from collect_teacher_soft_logits), all aligned
    to the same first `max_batches` batches of distill_loader.
    """
    if not teacher_soft_logits:
        return edge_state  # nothing to distill from — skip cleanly

    teacher_probs = torch.stack(teacher_soft_logits, dim=0).mean(dim=0).to(device)

    student = model_builder().to(device)
    student.load_state_dict(edge_state)
    student.train()
    optimizer = torch.optim.Adam(student.parameters(), lr=lr)

    for _ in range(epochs):
        offset = 0
        for i, (ecg, cxr, _tab, _labels) in enumerate(distill_loader):
            if i >= max_batches:
                break
            bsz = ecg.shape[0]
            target = teacher_probs[offset:offset + bsz]
            offset += bsz
            if target.shape[0] != bsz:
                break  # ragged last batch mismatch — skip rather than crash
            optimizer.zero_grad()
            student_logits = student(ecg.to(device, non_blocking=True),
                                     cxr.to(device, non_blocking=True))
            student_log_probs = F.log_softmax(student_logits / temperature, dim=-1)
            loss = F.kl_div(student_log_probs, target, reduction="batchmean") * (temperature ** 2)
            loss.backward()
            optimizer.step()

    # Keep tensors on `device` — edge_states must stay device-resident to match
    # the local_model.state_dict() it gets diffed against next edge round.
    refined_state = {k: v.detach() for k, v in student.state_dict().items()}
    del student
    torch.cuda.empty_cache()
    return refined_state
