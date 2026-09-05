"""
ONNX Edge Deployment — Phase 5 (D5.10)
Exports HFL-MM-HC to ONNX FP32, then INT8-quantizes for edge inference.
Target: model size < 4 MB, compatible with ONNXRuntime CUDAExecutionProvider.
"""

import os
import sys
import argparse
import torch

# model/ is split into subfolders by concern — add them all so flat imports
# ("from hfl_mm_model import ...") keep resolving regardless of which
# subfolder a module lives in.
_MODEL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # model/
for _sub in ("privacy", "architecture", "training", "deploy", "utils"):
    sys.path.insert(0, os.path.join(_MODEL_ROOT, _sub))
from hfl_mm_model import build_hfl_mm_hc
from device_utils import get_device, optimize_gpu


def dataset_io(dataset: str):
    """Model kwargs and dummy input shapes for a registered dataset.

    The exporter previously hardcoded ECG [1,12,1000] + CXR [1,3,224,224], so
    after a dataset change it silently kept exporting the previously configured
    architecture — the shipped .onnx files did not correspond to any model in
    use. Shapes are now derived from the registry.
    """
    import sys
    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, os.path.join(_root, "data", "loaders"))
    from datasets import get_spec, window_len
    sp = get_spec(dataset)
    kw = {"n_classes": sp.n_classes, "n_channels_a": sp.n_channels_a}
    if sp.modality_b == "image":
        kw_extra, shape_b = {}, (1, 3, 224, 224)
        win = window_len(sp, 1000)
    else:
        kw_extra = {"modality_b": "features", "feat_b_dim": sp.feat_b_dim}
        shape_b = (1, sp.feat_b_dim)
        # Read off the array, not a per-dataset map: see datasets.window_len.
        win = window_len(sp)
    kw.update(kw_extra)
    return kw, (1, sp.n_channels_a, win), shape_b, sp


def load_model_from_checkpoint(checkpoint: str, n_classes: int = 5,
                               model_kw: dict = None) -> torch.nn.Module:
    """
    Build an HFL-MM-HC model via build_hfl_mm_hc (GroupNorm + Opacus-safe
    patches, matching the trained architecture) and load a checkpoint.

    Handles both the trainer's save format ({"model_state": ...}) and a
    raw state_dict. Missing checkpoint → random weights (with a warning).
    """
    model = build_hfl_mm_hc(**(model_kw or {"n_classes": n_classes}))
    if checkpoint and os.path.exists(checkpoint):
        dev = get_device(verbose=False)
        state = torch.load(checkpoint, map_location=dev)
        if isinstance(state, dict):
            sd = state.get("model_state",
                           state.get("model_state_dict", state))
        else:
            sd = state
        missing, unexpected = model.load_state_dict(sd, strict=False)
        print(f"[LOAD] Checkpoint loaded from {checkpoint} "
              f"(missing={len(missing)}, unexpected={len(unexpected)})")
    else:
        print(f"[WARN] Checkpoint not found at {checkpoint}. Using random weights.")
    model.eval()
    return model


def export_onnx(args) -> dict:
    """
    Programmatic entry point used by run_phase5.step8.
    Expects args with: checkpoint, n_classes, output_fp32, output_int8.
    Returns {"fp32": path, "int8": path}.
    """
    model = load_model_from_checkpoint(getattr(args, "checkpoint", None),
                                       getattr(args, "n_classes", 5))
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[INFO] Total parameters: {n_params:,}  (~{n_params * 4 / 1e6:.1f} MB FP32)")

    export_fp32(model, args.output_fp32)
    optimize_and_quantize_int8(args.output_fp32, args.output_int8)
    if os.path.exists(args.output_fp32) and os.path.exists(args.output_int8):
        verify_onnx_outputs(args.output_fp32, args.output_int8)
    return {"fp32": args.output_fp32, "int8": args.output_int8}


def export_fp32(model: torch.nn.Module, output_path: str,
                shape_a=(1, 12, 1000), shape_b=(1, 3, 224, 224)) -> None:
    device = get_device(verbose=False)
    model.eval().to(device)
    dummy_a = torch.zeros(*shape_a).to(device)
    dummy_b = torch.zeros(*shape_b).to(device)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.onnx.export(
        model,
        (dummy_a, dummy_b),
        output_path,
        opset_version=17,
        # Generic names: the graph is exported for whichever dataset is
        # selected, so modality-specific names would mislabel every input
        # for every dataset but the one they were coined for.
        input_names=["x_a", "x_b"],
        output_names=["logits"],
        dynamic_axes={
            "x_a": {0: "batch"},
            "x_b": {0: "batch"},
        },
        do_constant_folding=True,
    )
    size_mb = os.path.getsize(output_path) / 1e6
    print(f"[ONNX FP32] Exported → {output_path}  ({size_mb:.2f} MB)")


def optimize_and_quantize_int8(fp32_path: str, int8_path: str) -> None:
    try:
        from onnxruntime.quantization import quantize_dynamic, QuantType
        import onnxruntime as ort
    except ImportError:
        print("[WARN] onnxruntime not installed. Skipping INT8 quantization.")
        print("       pip install onnxruntime-gpu")
        return

    # Graph-level optimization via OnnxRuntime
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opt_path = fp32_path.replace(".onnx", "_opt.onnx")
    sess_options.optimized_model_filepath = opt_path
    _providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    ort.InferenceSession(fp32_path, sess_options=sess_options,
                         providers=_providers)
    print(f"[ONNX OPT] Graph-optimized → {opt_path}")

    # Quantize from the ORIGINAL FP32 export, not from opt_path. The
    # ORT_ENABLE_ALL pass above bakes in hardware-specific ops (NchwcTransformer,
    # x86-only) — ORT warns about this itself. Those ops (a) defeat the shape
    # inference the quantizer needs, and (b) would make the INT8 artifact
    # non-portable to ARM edge targets, which is the opposite of what this
    # export is for. opt_path stays as a same-machine GPU artifact only.
    #
    # quant_pre_process runs the symbolic-shape-inference pass ORT's own
    # quantization guide asks for; without it the GRU MatMul outputs have no
    # inferrable type and quantize_dynamic raises.
    pre_path = fp32_path.replace(".onnx", "_pre.onnx")
    try:
        from onnxruntime.quantization.shape_inference import quant_pre_process
        quant_pre_process(input_model=fp32_path, output_model_path=pre_path,
                          skip_optimization=True)
        print(f"[ONNX PRE] Shape-inferred  → {pre_path}")
        quant_input = pre_path
    except Exception as e:
        print(f"[WARN] quant_pre_process failed ({e}); quantizing raw FP32 export.")
        quant_input = fp32_path

    # INT8 dynamic quantization (MatMul + Gemm weights).
    # No optimize_model= : onnxruntime removed that argument by 1.25.
    # DefaultTensorType is a backstop for any tensor whose type still cannot be
    # inferred after pre-processing.
    # Exclude the recurrent path from quantisation. ORT's dynamic quantiser
    # emits a MatMulInteger for the reverse GRU direction whose shapes fail
    # inference ("Incompatible dimensions for matrix multiplication"), so the
    # resulting model will not load. Leaving the GRU in FP32 costs nothing that
    # matters: INT8 was measured 1.9x slower than FP32 on CPU and 3.25x slower
    # on GPU for this architecture (see RESULTS.md 3b), because quantize_dynamic
    # only accelerates MatMul/Gemm while the cost here is convolutions and the
    # recurrent path. The dense layers still quantise, which is where the size
    # reduction comes from.
    import onnx as _onnx
    _m = _onnx.load(quant_input)
    _rec = [n.name for n in _m.graph.node
            if "gru" in n.name.lower() or "lstm" in n.name.lower()]
    # ORT decomposes Gemm -> MatMul + Add BEFORE quantising, so the node it
    # actually quantises is "<name>_MatMul", which does not exist yet when this
    # list is built. Excluding only the original name silently misses it and the
    # produced model fails to load. Cover both spellings.
    _excl = _rec + [f"{n}_MatMul" for n in _rec] + [f"{n}_Add" for n in _rec]
    if _excl:
        print(f"[ONNX INT8] excluding {len(_excl)} recurrent nodes from quantisation")
    quantize_dynamic(
        model_input=quant_input,
        model_output=int8_path,
        weight_type=QuantType.QInt8,
        nodes_to_exclude=_excl or None,
        extra_options={"DefaultTensorType": _onnx.TensorProto.FLOAT},
    )
    size_mb = os.path.getsize(int8_path) / 1e6
    print(f"[ONNX INT8] Quantized    → {int8_path}  ({size_mb:.2f} MB)")
    if size_mb > 4.0:
        print(f"[WARN] INT8 model size {size_mb:.2f} MB exceeds 4 MB target.")
    else:
        print(f"[PASS] INT8 model size {size_mb:.2f} MB ≤ 4 MB target.")


def verify_fp32_runs(path: str, shape_a, shape_b) -> bool:
    """Load the exported FP32 graph and run one inference. An .onnx file that
    writes successfully but cannot be loaded is worse than no file at all."""
    try:
        import onnxruntime as ort
        import numpy as np
    except ImportError:
        return False
    try:
        sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        out = sess.run(None, {"x_a": np.zeros(shape_a, dtype=np.float32),
                              "x_b": np.zeros(shape_b, dtype=np.float32)})[0]
        print(f"[VERIFY FP32] loads and runs — logits {tuple(out.shape)}")
        return True
    except Exception as e:
        print(f"[VERIFY FP32][FAIL] {type(e).__name__}: {str(e)[:140]}")
        return False


def verify_onnx_outputs(fp32_path: str, int8_path: str,
                        shape_a=(1, 12, 1000), shape_b=(1, 3, 224, 224)) -> None:
    """Sanity check: FP32 and INT8 produce outputs within tolerance."""
    try:
        import onnxruntime as ort
        import numpy as np
    except ImportError:
        return

    dummy_a = np.zeros(shape_a, dtype=np.float32)
    dummy_b = np.zeros(shape_b, dtype=np.float32)

    def run(path):
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        sess = ort.InferenceSession(path, providers=providers)
        return sess.run(None, {"x_a": dummy_a, "x_b": dummy_b})[0]

    out_fp32 = run(fp32_path)
    out_int8 = run(int8_path)
    max_diff = float(np.abs(out_fp32 - out_int8).max())
    print(f"[VERIFY] FP32 vs INT8 max logit diff: {max_diff:.4f}")
    if max_diff < 0.5:
        print("[PASS] Output agreement within tolerance (< 0.5 logit units).")
    else:
        print("[WARN] Large discrepancy — check quantization settings.")


def main():
    parser = argparse.ArgumentParser(description="Export HFL-MM-HC to ONNX")
    parser.add_argument("--int8", action="store_true",
                        help="Also attempt INT8 dynamic quantisation. OFF by "
                             "default: measured 1.9x slower than FP32 on CPU "
                             "and 3.25x on GPU for this architecture "
                             "(RESULTS.md 3b), so FP32 is the shipping "
                             "artifact. Non-fatal if ORT cannot produce a "
                             "loadable model.")
    parser.add_argument("--dataset", default="vitaldb",
                        choices=["wear", "vitaldb"],
                        help="Determines input shapes and encoder-B type.")
    parser.add_argument("--checkpoint", default="checkpoints/best_model_hc.pt",
                        help="Path to trained model checkpoint (.pt)")
    parser.add_argument("--output_fp32", default="onnx/hfl_mm_hc.onnx",
                        help="Output path for FP32 ONNX model")
    parser.add_argument("--output_int8", default="onnx/hfl_mm_hc_int8.onnx",
                        help="Output path for INT8 quantized ONNX model")
    parser.add_argument("--n_classes", type=int, default=5)
    parser.add_argument("--n_mamba_blocks", type=int, default=4)
    args = parser.parse_args()

    # Load model via load_model_from_checkpoint (build_hfl_mm_hc), NOT the
    # raw HFLMMHC() constructor: build_hfl_mm_hc applies the GroupNorm/
    # inplace-activation patches the model was actually trained under, so
    # the checkpoint's state_dict keys/architecture line up.
    model_kw, shape_a, shape_b, _sp = dataset_io(args.dataset)
    print(f"[INFO] dataset={args.dataset}  A{shape_a}  B{shape_b}  "
          f"classes={model_kw['n_classes']}")
    model = load_model_from_checkpoint(args.checkpoint, args.n_classes, model_kw)

    # Count parameters
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[INFO] Total parameters: {n_params:,}  (~{n_params * 4 / 1e6:.1f} MB FP32)")

    # Export
    export_fp32(model, args.output_fp32, shape_a, shape_b)
    verify_fp32_runs(args.output_fp32, shape_a, shape_b)

    if args.int8:
        try:
            optimize_and_quantize_int8(args.output_fp32, args.output_int8)
            if os.path.exists(args.output_int8):
                verify_onnx_outputs(args.output_fp32, args.output_int8,
                                    shape_a, shape_b)
        except Exception as e:
            # ORT's Gemm->MatMul rewrite produces an invalid graph for some
            # GRU shapes ("Incompatible dimensions for matrix multiplication"),
            # independently of quantisation. Not fatal: FP32 is what ships.
            print(f"[ONNX INT8][SKIP] quantisation failed: {type(e).__name__}: "
                  f"{str(e)[:120]}")
            print("[ONNX INT8][SKIP] FP32 artifact is unaffected and is the "
                  "deployment target.")

    print("\n[DONE] ONNX export complete.")
    print(f"  FP32 : {args.output_fp32}")
    print(f"  INT8 : {args.output_int8}")
    print("  Next : python model/inference_bench.py --model", args.output_int8)


if __name__ == "__main__":
    main()
