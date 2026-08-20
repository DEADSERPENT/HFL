"""
Regression tests — guard fixes so they cannot silently come back.

Every test here corresponds to a bug that once produced PLAUSIBLE BUT WRONG
numbers rather than a crash. That is the selection criterion: a bug that
crashes announces itself, a bug that returns 0.87 instead of 0.83 does not.

  R1  one shared dataset across device loaders keeps RAM bounded
  R2  a saved checkpoint loads strict into a freshly built model
  R3  PyTorch and ONNX outputs agree within float tolerance
  R4  preflight passes for the selected dataset
  R5  model forward produces the shape the registry says it should
  R6  a reused PrivacyEngine COMPOSES epsilon across calls
  R7  the compressor transmits nothing for an all-zero tensor
  R8  --no_dp is genuinely no-DP, not a loose budget

Dataset-driven: every shape, path, client count and class count comes from
the registry, so this suite tests the model that actually trains.

  python tests/test_regression.py --dataset vitaldb
  python tests/test_regression.py --dataset wear

Exit code 0 = all pass, 1 = a test failed.
"""

import os
import sys
import argparse
import tempfile

# model/ is split by concern (architecture/privacy/training/deploy/utils);
# adding only "model" leaves `from hfl_trainer import ...` unresolvable.
for _sub in ("training", "architecture", "privacy", "deploy", "utils"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model", _sub))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "loaders"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import torch

from datasets import get_spec, REGISTRY

_results = []
SPEC = None          # set in main() from --dataset


def _check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}"
          f"{'  — ' + detail if detail else ''}")
    return cond


def _model_kw():
    kw = {"n_channels_a": SPEC.n_channels_a}
    if SPEC.modality_b != "image":
        kw.update(modality_b="features", feat_b_dim=SPEC.feat_b_dim)
    return kw


def _dummy_inputs(batch=2):
    """Inputs shaped from the registry and the arrays on disk."""
    import glob
    a_files = sorted(glob.glob(os.path.join(SPEC.data_dir, "*", "*.npy")))
    t_a = 300 if SPEC.name == "vitaldb" else 100
    for f in a_files:
        if "window" in os.path.basename(f) or "signal" in os.path.basename(f):
            t_a = np.load(f, mmap_mode="r").shape[-1]
            break
    xa = torch.randn(batch, SPEC.n_channels_a, t_a)
    if SPEC.modality_b == "image":
        xb = torch.randn(batch, 3, 224, 224)
    else:
        xb = torch.randn(batch, SPEC.feat_b_dim)
    return xa, xb


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
    Every device loader must SHARE one materialised dataset. Building one
    dataset per device multiplies resident memory by the client count and
    freezes the machine — and it does so only at scale, so it survives every
    small test.
    """
    from hfl_trainer import load_partitioned_data
    full = SPEC.build_full(SPEC.data_dir)
    rss_after_dataset = _cur_rss_gb()
    n = min(SPEC.n_devices, 6)
    for d in range(n):
        load_partitioned_data(SPEC.partition_dir, SPEC.data_dir, d, 32, full_ds=full)
    growth = _cur_rss_gb() - rss_after_dataset
    _check("R1 shared-dataset RAM bounded", growth < 0.5,
           f"{n} loaders added {growth*1000:.0f} MB over the shared dataset")


def test_r5_forward_shape():
    from hfl_mm_model import build_hfl_mm_hc
    m = build_hfl_mm_hc(n_classes=SPEC.n_classes, **_model_kw()).eval()
    xa, xb = _dummy_inputs(2)
    with torch.no_grad():
        out = m(xa, xb)
    _check("R5 forward output shape",
           tuple(out.shape) == (2, SPEC.n_classes),
           f"got {tuple(out.shape)}, registry says (2, {SPEC.n_classes})")
    return m


def test_r2_checkpoint_strict_load():
    from hfl_mm_model import build_hfl_mm_hc
    ckpt = f"checkpoints/best_{SPEC.name}.pt"
    if not os.path.exists(ckpt):
        _check("R2 checkpoint strict load", True,
               f"{ckpt} not present — skipped (run the proposed stage first)")
        return None
    state = torch.load(ckpt, map_location="cpu", weights_only=False)
    sd = state["model_state"] if isinstance(state, dict) and "model_state" in state else state
    m = build_hfl_mm_hc(n_classes=SPEC.n_classes, **_model_kw()).eval()
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
    """GroupNorm needs a shim to export. If the shim is wrong the export
    SUCCEEDS and the exported graph computes something subtly different, so
    only a numerical comparison catches it."""
    if model is None:
        model = test_r5_forward_shape()
    try:
        import onnxruntime as ort
    except ImportError:
        _check("R3 ONNX parity", True, "onnxruntime absent — skipped")
        return
    model.eval()
    xa, xb = _dummy_inputs(3)
    with torch.no_grad():
        pt = model(xa, xb).numpy()
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "m.onnx")
        torch.onnx.export(model, (xa[:1], xb[:1]), path, opset_version=17,
                          input_names=["mod_a", "mod_b"], output_names=["logits"],
                          dynamic_axes={"mod_a": {0: "batch"}, "mod_b": {0: "batch"}},
                          do_constant_folding=True)
        sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        onx = sess.run(None, {"mod_a": xa.numpy(), "mod_b": xb.numpy()})[0]
    max_abs = float(np.abs(pt - onx).max())
    argmatch = bool((pt.argmax(1) == onx.argmax(1)).all())
    _check("R3 ONNX parity (max_abs<1e-3 & argmax match)",
           max_abs < 1e-3 and argmatch,
           f"max_abs={max_abs:.2e}, argmax_match={argmatch}")


def test_r4_preflight():
    from engineering.preflight import run_preflight
    ok, _ = run_preflight(SPEC.data_dir, SPEC.partition_dir, "checkpoints",
                          "results", n_devices=SPEC.n_devices,
                          required_files=SPEC.required_files)
    _check("R4 preflight passes", ok, f"dataset={SPEC.name}")


def test_r6_dp_epsilon_composes():
    """
    A persistent PrivacyEngine reused across calls must show epsilon strictly
    INCREASING call-over-call. Creating a fresh engine each call makes epsilon
    stay flat no matter how many rounds ran — under-reporting the true
    cumulative privacy loss while looking entirely healthy.
    """
    from dp_engine import make_dp_model, get_epsilon_spent
    from torch.utils.data import TensorDataset, DataLoader as TDL

    torch.manual_seed(0)
    ds = TensorDataset(torch.randn(200, 10), torch.randint(0, 2, (200,)))
    delta, sigma, n_calls = 1e-5, 1.2, 4

    engine, eps_seq = None, []
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

    inc = all(eps_seq[i] > eps_seq[i - 1] + 1e-9 for i in range(1, len(eps_seq)))
    _check("R6 DP epsilon composes across calls", inc,
           f"eps sequence: {[round(e, 4) for e in eps_seq]}")


def test_r7_compressor_skips_zero_tensors():
    """
    Under frozen encoders the encoder deltas are exactly zero. A fixed-k top-k
    selector still "selects" k entries of an all-zero tensor and transmits
    them, inflating measured uplink with traffic carrying no information —
    the run completes normally and only the communication figure is wrong.
    The selector must be capped by the non-zero count.
    """
    from compression import GradientCompressor
    c = GradientCompressor(sparsity=0.2, quant_bits=8)

    zero = {"frozen.weight": torch.zeros(1000)}
    out_zero = c.compress(zero, use_error_feedback=False)
    sent_zero = sum(len(v["indices"]) if isinstance(v, dict) and "indices" in v else 0
                    for v in out_zero.values())

    dense = {"head.weight": torch.randn(1000)}
    out_dense = c.compress(dense, use_error_feedback=False)
    sent_dense = sum(len(v["indices"]) if isinstance(v, dict) and "indices" in v else 0
                     for v in out_dense.values())

    _check("R7 compressor sends nothing for an all-zero tensor",
           sent_zero == 0 and sent_dense > 0,
           f"zero-tensor sent {sent_zero} coords, dense sent {sent_dense}")


def test_r8_no_dp_is_genuinely_no_dp():
    """
    --no_dp must bypass DP entirely: no clipping, no noise, no accountant.
    A large epsilon is NOT equivalent — it still clips per-sample gradients,
    so using it as a stand-in for "no privacy" understates what privacy costs
    in the flattering direction. Phase 6 arms S3 and A2 depend on this.
    """
    from hfl_trainer import local_dp_train
    from torch.utils.data import TensorDataset, DataLoader as TDL
    from hfl_mm_model import build_hfl_mm_hc

    xa, xb = _dummy_inputs(8)
    y = torch.randint(0, SPEC.n_classes, (8,))
    # local_dp_train consumes 4-tuples (mod_a, mod_b, tabular, label)
    ds = TensorDataset(xa, xb, torch.zeros(8, 1), y)
    loader = TDL(ds, batch_size=4)
    m = build_hfl_mm_hc(n_classes=SPEC.n_classes, **_model_kw())

    before = [p.detach().clone() for p in m.parameters() if p.requires_grad]
    r = local_dp_train(m, loader, torch.device("cpu"), delta=1e-5,
                       max_grad_norm=1.0, lr=1e-3, noise_multiplier=None,
                       n_epochs=1, no_dp=True)
    after = [p.detach() for p in m.parameters() if p.requires_grad]
    moved = any(not torch.equal(b, a) for b, a in zip(before, after))

    _check("R8 --no_dp reports epsilon=inf and still trains",
           r.get("epsilon_spent") == float("inf") and r.get("dp") is False and moved,
           f"epsilon_spent={r.get('epsilon_spent')}, dp={r.get('dp')}, "
           f"weights_updated={moved}")


def main():
    global SPEC
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--skip", nargs="*", default=[],
                    help="e.g. --skip r1 r3  (r1 loads the full dataset)")
    a = ap.parse_args()
    SPEC = get_spec(a.dataset)
    skip = [s.lower() for s in a.skip]

    print(f"Running HFL regression tests — dataset '{SPEC.name}'\n")
    if "r1" not in skip:
        test_r1_shared_dataset_ram_bounded()
    m = test_r5_forward_shape()
    m2 = test_r2_checkpoint_strict_load()
    if "r3" not in skip:
        test_r3_onnx_parity(m2 if m2 is not None else m)
    if "r4" not in skip:
        test_r4_preflight()
    test_r6_dp_epsilon_composes()
    test_r7_compressor_skips_zero_tensors()
    test_r8_no_dp_is_genuinely_no_dp()

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n{'='*54}\nRESULT: {passed}/{total} passed  (dataset={SPEC.name})")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
