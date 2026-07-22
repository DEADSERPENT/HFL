"""
Regression tests for the engineering-hardening pass.

Guards the fixes made so far so they can't silently regress:
  R1  shared dataset keeps RAM bounded (C1 OOM fix)
  R2  trained checkpoint loads strict into build_hfl_mm_hc (H5 + GroupNormND)
  R3  PyTorch and ONNX outputs match within float tolerance (GroupNormND fix)
  R4  preflight passes on the current environment
  R5  model forward produces correct output shape
  R6  reusing one PrivacyEngine across calls composes epsilon (M7 fix):
      epsilon must strictly increase call-over-call, not stay flat

Runnable without pytest:  python tests/test_regression.py
Exit code 0 = all pass, 1 = a test failed.
"""

import os
import sys
import resource
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "loaders"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import torch

DATA = "data/processed/healthcare"
PART = "data/processed/partitions/healthcare"
CKPT = "checkpoints/best_model_hc.pt"

_results = []


def _check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}"
          f"{'  — ' + detail if detail else ''}")
    return cond


def _cur_rss_gb():
    """Current resident set size (steady-state, not peak) in GB."""
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / (1024 ** 2)
    except (OSError, ValueError):
        pass
    return float("nan")


def test_r1_shared_dataset_ram_bounded():
    """
    6 device loaders sharing one dataset must not multiply RAM. Measured on
    steady-state RSS growth from 1 dataset → 6 loaders: sharing keeps this
    near zero, whereas independent per-device datasets would add ~10 GB (the
    original C1 OOM-freeze bug).
    """
    from hfl_trainer import build_full_healthcare_dataset, load_partitioned_data
    full = build_full_healthcare_dataset(DATA)
    rss_after_dataset = _cur_rss_gb()
    for d in range(6):
        load_partitioned_data(PART, DATA, d, 32, full_ds=full)
    rss_after_loaders = _cur_rss_gb()
    growth = rss_after_loaders - rss_after_dataset
    _check("R1 shared-dataset RAM bounded", growth < 0.5,
           f"6 loaders added {growth*1000:.0f} MB over the shared dataset "
           f"(independent copies would add ~10 GB)")


def test_r5_forward_shape():
    from hfl_mm_model import build_hfl_mm_hc
    m = build_hfl_mm_hc(n_classes=5).eval()
    with torch.no_grad():
        out = m(torch.randn(2, 12, 1000), torch.randn(2, 3, 224, 224))
    _check("R5 forward output shape", tuple(out.shape) == (2, 5),
           f"got {tuple(out.shape)}")
    return m


def test_r2_checkpoint_strict_load():
    from hfl_mm_model import build_hfl_mm_hc
    if not os.path.exists(CKPT):
        _check("R2 checkpoint strict load", True, "no checkpoint present — skipped")
        return None
    state = torch.load(CKPT, map_location="cpu", weights_only=False)
    sd = state["model_state"] if isinstance(state, dict) and "model_state" in state else state
    m = build_hfl_mm_hc(n_classes=5).eval()
    try:
        missing, unexpected = m.load_state_dict(sd, strict=True)
        ok = (len(missing) == 0 and len(unexpected) == 0)
        _check("R2 checkpoint strict load", ok,
               f"missing={len(missing)}, unexpected={len(unexpected)}")
    except Exception as e:
        _check("R2 checkpoint strict load", False, str(e)[:80])
        m = None
    return m


def test_r3_onnx_parity(model):
    if model is None:
        model = test_r5_forward_shape()
    try:
        import onnxruntime as ort
    except ImportError:
        _check("R3 ONNX parity", True, "onnxruntime absent — skipped")
        return
    model.eval()
    ecg, cxr = torch.randn(3, 12, 1000), torch.randn(3, 3, 224, 224)
    with torch.no_grad():
        pt = model(ecg, cxr).numpy()
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "m.onnx")
        torch.onnx.export(model, (ecg[:1], cxr[:1]), path, opset_version=17,
                          input_names=["ecg", "cxr"], output_names=["logits"],
                          dynamic_axes={"ecg": {0: "batch"}, "cxr": {0: "batch"}},
                          do_constant_folding=True)
        sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        onx = sess.run(None, {"ecg": ecg.numpy(), "cxr": cxr.numpy()})[0]
    max_abs = float(np.abs(pt - onx).max())
    argmatch = bool((pt.argmax(1) == onx.argmax(1)).all())
    _check("R3 ONNX parity (max_abs<1e-3 & argmax match)",
           max_abs < 1e-3 and argmatch,
           f"max_abs={max_abs:.2e}, argmax_match={argmatch}")


def test_r4_preflight():
    from engineering.preflight import run_preflight
    ok, _ = run_preflight(DATA, PART, "checkpoints", "results", n_devices=6)
    _check("R4 preflight passes", ok)


def test_r6_dp_epsilon_composes():
    """
    M7 fix: a persistent PrivacyEngine reused across calls must show ε
    strictly increasing call-over-call. Before the fix, make_dp_model()
    created a fresh PrivacyEngine every call, so ε stayed flat regardless of
    how many calls/rounds had actually run — silently under-reporting the
    true cumulative privacy loss.
    """
    from dp_engine import make_dp_model, get_epsilon_spent
    from torch.utils.data import TensorDataset, DataLoader as TDL

    torch.manual_seed(0)
    X, y = torch.randn(200, 10), torch.randint(0, 2, (200,))
    ds = TensorDataset(X, y)
    delta, sigma, n_calls = 1e-5, 1.2, 4

    engine = None
    eps_seq = []
    for _ in range(n_calls):
        loader = TDL(ds, batch_size=20, shuffle=True)
        m = torch.nn.Linear(10, 2)
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        dp_model, dp_opt, dp_loader, pe = make_dp_model(
            m, opt, loader, noise_multiplier=sigma, max_grad_norm=1.0,
            privacy_engine=engine)
        engine = pe
        loss_fn = torch.nn.CrossEntropyLoss()
        for xb, yb in dp_loader:
            dp_opt.zero_grad()
            loss_fn(dp_model(xb), yb).backward()
            dp_opt.step()
        eps_seq.append(get_epsilon_spent(pe, delta))

    strictly_increasing = all(eps_seq[i] > eps_seq[i - 1] + 1e-9
                              for i in range(1, len(eps_seq)))
    _check("R6 DP epsilon composes across calls", strictly_increasing,
           f"eps sequence: {[round(e, 4) for e in eps_seq]}")


def main():
    print("Running HFL regression tests...\n")
    test_r1_shared_dataset_ram_bounded()
    m = test_r5_forward_shape()
    m2 = test_r2_checkpoint_strict_load()
    test_r3_onnx_parity(m2 if m2 is not None else m)
    test_r4_preflight()
    test_r6_dp_epsilon_composes()

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n{'='*50}\nRESULT: {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
