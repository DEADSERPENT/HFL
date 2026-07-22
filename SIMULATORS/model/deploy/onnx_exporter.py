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


def load_model_from_checkpoint(checkpoint: str, n_classes: int = 5) -> torch.nn.Module:
    """
    Build an HFL-MM-HC model via build_hfl_mm_hc (GroupNorm + Opacus-safe
    patches, matching the trained architecture) and load a checkpoint.

    Handles both the trainer's save format ({"model_state": ...}) and a
    raw state_dict. Missing checkpoint → random weights (with a warning).
    """
    model = build_hfl_mm_hc(n_classes=n_classes)
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


def export_fp32(model: torch.nn.Module, output_path: str) -> None:
    device = get_device(verbose=False)
    model.eval().to(device)
    dummy_ecg = torch.zeros(1, 12, 1000).to(device)
    dummy_cxr = torch.zeros(1, 3, 224, 224).to(device)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.onnx.export(
        model,
        (dummy_ecg, dummy_cxr),
        output_path,
        opset_version=17,
        input_names=["ecg", "cxr"],
        output_names=["logits"],
        dynamic_axes={
            "ecg": {0: "batch"},
            "cxr": {0: "batch"},
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

    # INT8 dynamic quantization (MatMul + Gemm ops)
    quantize_dynamic(
        model_input=opt_path,
        model_output=int8_path,
        weight_type=QuantType.QInt8,
        optimize_model=True,
    )
    size_mb = os.path.getsize(int8_path) / 1e6
    print(f"[ONNX INT8] Quantized    → {int8_path}  ({size_mb:.2f} MB)")
    if size_mb > 4.0:
        print(f"[WARN] INT8 model size {size_mb:.2f} MB exceeds 4 MB target.")
    else:
        print(f"[PASS] INT8 model size {size_mb:.2f} MB ≤ 4 MB target.")


def verify_onnx_outputs(fp32_path: str, int8_path: str) -> None:
    """Sanity check: FP32 and INT8 produce outputs within tolerance."""
    try:
        import onnxruntime as ort
        import numpy as np
    except ImportError:
        return

    dummy_ecg = np.zeros((1, 12, 1000), dtype=np.float32)
    dummy_cxr = np.zeros((1, 3, 224, 224), dtype=np.float32)

    def run(path):
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        sess = ort.InferenceSession(path, providers=providers)
        return sess.run(None, {"ecg": dummy_ecg, "cxr": dummy_cxr})[0]

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
    model = load_model_from_checkpoint(args.checkpoint, args.n_classes)

    # Count parameters
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[INFO] Total parameters: {n_params:,}  (~{n_params * 4 / 1e6:.1f} MB FP32)")

    # Export
    export_fp32(model, args.output_fp32)
    optimize_and_quantize_int8(args.output_fp32, args.output_int8)

    if os.path.exists(args.output_fp32) and os.path.exists(args.output_int8):
        verify_onnx_outputs(args.output_fp32, args.output_int8)

    print("\n[DONE] ONNX export complete.")
    print(f"  FP32 : {args.output_fp32}")
    print(f"  INT8 : {args.output_int8}")
    print("  Next : python model/inference_bench.py --model", args.output_int8)


if __name__ == "__main__":
    main()
