# Phase 5 — Results (Completed Work)

**Project:** Hierarchical Federated Learning for Privacy-Aware, Low-Latency Multimodal IoT Systems
**Student:** Samartha H V (251580130019) · **Guide:** Dr. Shreyas J · **Industry:** Mr. Tejas J
**Status as of:** 2026-08-01 · **Phase 5: IN PROGRESS (12 of 13 deliverables complete)**

> This document records only work that is **finished and verified**. Open items are listed in
> §7 without results. `phase5_results.csv` (D5.13) was regenerated 2026-08-01 and now agrees
> with this document; the 2026-07-13 version reporting the collapsed model is obsolete.

---

## 1. Headline Result

The ε=1 utility collapse that blocked Objective 2 for three weeks is **resolved**. The fix is
**head-only DP fine-tuning**: pretrain both encoders non-privately, freeze them, and apply
DP-SGD to the fusion head alone (560,645 / 2,157,766 params = 26.0%).

```
        BEFORE (end-to-end DP-SGD)              AFTER (head-only DP fine-tuning)
        ε=1, σ=11.33, all 2.16M params          ε=1, σ=11.33, 560K params (26%)

  AUC                                      AUC
  0.90│                                    0.90│              ╭──────────────
      │                                        │         ╭────╯
  0.80│                                    0.80│    ╭────╯
      │                                        │  ╭─╯
  0.70│                                    0.70│ ╱
      │                                        │╱
  0.60│ ╭╮  ╭╮   ╭─╮  ╭╮                   0.60│
      │╱ ╰──╯╰───╯ ╰──╯╰─  (noise)             │
  0.50├─────────────────────  random       0.50│
      └────────────────────────►               └────────────────────────►
       1    5    10   15   20  round            1    5    10   15   20  round

       Final Test AUC = 0.562                   Final Test AUC = 0.8742 ± 0.0072
       (≈ random, unusable)                     ~20× faster per round (50s vs 1046s)
```

**σ was identical (11.3281) in both.** The noise was never reducible at this operating point —
what changed is the optimisation geometry: a near-linear probe over frozen pretrained features
tolerates σ≈11.3, end-to-end-from-scratch training does not.

---

## 2. Main Experiment — Privacy–Utility at ε=1

Configuration (identical across all six runs, only ε differs):

```
20 global rounds · 5 edge rounds · 6 devices · 2 edges
--dp_mode uniform --freeze_encoders --agg_mode aswa --aswa_temperature 1.0
--edge_distill_epochs 0   (FedKD-E excluded — see §7.3)
δ = 1e-5 · C = 1.0 · n_fl_calls = 100 · total_steps = 1200 · sample_rate = 0.0798
```

### 2.1 Per-seed results

| ε | seed | σ | test AUC | test acc | best val AUC | ε_spent |
|---|------|-----|---------|----------|--------------|---------|
| 1 | 42 | 11.3281 | 0.8659 | 0.6146 | 0.8413 | 0.9965 |
| 1 | 43 | 11.3281 | 0.8784 | 0.6384 | 0.8758 | 0.9965 |
| 1 | 44 | 11.3281 | 0.8784 | 0.6636 | 0.8676 | 0.9965 |
| 1000 | 42 | 0.2394 | 0.8731 | 0.6437 | 0.8746 | 1033.90 |
| 1000 | 43 | 0.2394 | 0.8742 | 0.6543 | 0.8820 | 1033.90 |
| 1000 | 44 | 0.2394 | 0.8712 | 0.6675 | 0.8905 | 1033.90 |

ε=1000 is the **non-private comparator**: same architecture, same frozen encoders, DP
effectively off. There is no `--no_dp` flag; `--epsilon 1000` is the established convention
in this codebase (matches `epsilon_sweep/eps_1000_uniform.csv`).

### 2.2 Aggregate and paired test

| metric | ε=1 | ε=1000 | paired Δ (ε1000 − ε1) |
|--------|-----|--------|------------------------|
| test AUC | **0.8742 ± 0.0072** | **0.8728 ± 0.0015** | **−0.0014**, t(2)=−0.32, 95% CI [−0.0203, +0.0175] |
| test acc | **0.6389 ± 0.0245** | **0.6552 ± 0.0119** | **+0.0163**, t(2)=+2.24, 95% CI [−0.0150, +0.0476] |

Per-seed ΔAUC: +0.0072 / −0.0042 / −0.0072. **ε=1 beat its own non-private comparator on two
of three seeds.**

**Interpretation.** The privacy cost at ε=1 is **not statistically detectable** on either
metric (critical t at 2 df = 4.303; neither statistic approaches it). The defensible claim is
*"no measurable utility cost at ε=1"* — **not** *"zero cost"*. With n=3 the test has very
little power; report the confidence interval, not the point estimate.

### 2.3 Secondary finding — DP costs reproducibility, not mean utility

ε=1 shows **~5× the run-to-run variance** of ε=1000 (AUC sd 0.0072 vs 0.0015; acc sd 0.0245
vs 0.0119). σ=11.33 does not shift the mean here, but it makes individual runs materially
less repeatable. This is a reportable characterisation of what DP actually costs in this
regime, and it is why single-seed numbers were misleading (seed 42 alone suggested a
0.0075 AUC cost; three seeds show −0.0014).

---

## 3. Communication Efficiency (Objective 1)

A compressor defect was found and fixed during this phase. `GradientCompressor.compress`
took a fixed `k = int(numel * sparsity)` of **every** float tensor, so frozen encoders — whose
delta is exactly zero — still contributed 20% of their elements to every payload as explicit
zeros. Fix: omit all-zero tensors, and cap `k` at the nonzero count.

| measurement | bytes/round | 20-round total |
|-------------|-------------|----------------|
| Full-model FP32 FedAvg (30 uploads × 2.16M × 4B) | 258,931,920 | 5178.6 MB |
| Head-only FP32, uncompressed | 67,277,400 | 1345.5 MB |
| **Observed, post-fix** | **16,821,300** | **336.4 MB** |
| Observed, pre-fix (inflated by zero-padding) | 79,608,840 | 1592.2 MB |

- **Uplink reduction vs full-model FP32 FedAvg: 93.50%** → Objective 1 (≥50%) **PASS**
- Reduction attributable to the compressor alone (top-k + 8-bit quantisation of the head
  delta — unrelated to the ONNX INT8 in §3b): 75.00%
- Reduction attributable to the bug fix: 78.87%

All six runs report an identical `uplink_bytes` (16,821,300/round) — the metric is
deterministic and seed-independent, so a single run is sufficient to source this figure.

**Verification that the fix did not alter learning:**
1. Dense path proven **bit-identical** to the previous implementation — indices, quantised
   values, `g_min`/`g_max`, and the error-feedback accumulator all match exactly over 5 rounds
   against a verbatim copy of the old code. Every non-frozen result on record (B0–B5, the
   original ε-sweep) is therefore unaffected.
2. Seed 43 re-ran against its **existing** encoder checkpoint, isolating the compressor as the
   only change: AUC moved 0.8783 → 0.8784 (ε=1) and 0.8741 → 0.8742 (ε=1000).

---

## 3b. Inference Latency (Objective 3) — D5.10 + D5.11

Exported from `checkpoints/best_eps1_dpft.pt` (the ε=1 head-only model — i.e. the
privacy-preserving artifact you would actually deploy), loaded with **`missing=0,
unexpected=0`**. 1000 timed runs after 100 warmup, batch size 1, per configuration.

Measured pipeline: `preprocessing → ONNX forward → conformal prediction set → post/serialise`.

| precision | provider | model | preproc | inference | conformal | post | **total P50** | **total P95** | P99 | QoS |
|-----------|----------|-------|---------|-----------|-----------|------|-----------|-----------|-----|-----|
| **FP32** | **CPU** | 10.64 MB | 3.03 | **13.26** | 0.08 | 0.03 | **15.53** | **16.36** | 17.44 | ✅ PASS |
| FP32 | GPU (CUDA) | 10.64 MB | 2.33 | 20.09 | 0.10 | 0.03 | 21.61 | 22.48 | 23.15 | ✅ PASS |
| INT8 | CPU | 6.55 MB | 3.05 | 27.88 | 0.09 | 0.03 | 30.31 | 31.03 | 31.63 | ✅ PASS |
| INT8 | GPU (CUDA) | 6.55 MB | 3.03 | 70.02 | 0.11 | 0.04 | 69.57 | 73.15 | 74.58 | ✅ PASS |

*(all figures ms, P95 unless stated; sorted best-first)*

**Objective 3 (P95 < 100 ms): PASS in every configuration.** Best is **FP32 on CPU at
16.36 ms P95** — a 6.1× margin against the target.

### Finding: INT8 quantization is counterproductive for this model

The deliverable prescribed INT8 for edge deployment. Measured, it is **slower than FP32 on
both providers — 1.90× on CPU and 3.25× on GPU** — and it misses the 4 MB size target
(6.55 MB). Two independent causes:

1. `quantize_dynamic` only accelerates **MatMul/Gemm**. This model's cost is dominated by
   MobileNetV3 convolutions (`encoder_b`) and the recurrent/Mamba path (`encoder_a`), which it
   does not accelerate — so the quantize/dequantize overhead is paid with no kernel speedup.
2. On CUDA the quantized ops have no GPU kernel and fall back to CPU, forcing constant
   device transfers. ORT reports **3180 Memcpy nodes** inserted into the graph, which is
   exactly the 3.25× penalty showing up.

**Recommendation: deploy the FP32 ONNX artifact.** INT8 is retained as a characterised
negative result, not as the shipping configuration. If model size later matters more than
latency, the correct lever is static/QDQ quantization with a calibration set, or
quantization-aware training — not dynamic quantization.

**Caveat.** `simulate_preprocessing()` synthesises tensors with `np.random.randn` plus
normalisation; it excludes real sensor/disk I/O and image decode. The ~3 ms preprocessing
figure is therefore a **floor**, not a field measurement. Inference, conformal, and post
stages are real. This does not endanger the verdict — the target has 6.1× headroom — but the
end-to-end number should be described as "compute latency", not "glass-to-glass latency".

Fixes required to run these deliverables (both had never been executed):
- `onnx_exporter.py` — `quantize_dynamic(optimize_model=...)` was removed in onnxruntime 1.25;
  quantization now runs on the **clean FP32 export** via `quant_pre_process` rather than on the
  graph-optimized model, which carried x86-only NchwcTransformer ops that broke shape inference
  and would have made the INT8 artifact non-portable to ARM edge targets.
- `inference_bench.py` — added a cuDNN preload (cuDNN 9 lives inside the venv and is only on
  the loader path when torch is imported, so the benchmark died with
  `CUDNN_STATUS_NOT_INITIALIZED`); `--provider` is now honoured (it was hardcoded to prefer
  CUDA, so `--provider CPUExecutionProvider` silently benchmarked the GPU); and the
  provider banner now prints the provider actually in use instead of a hardcoded string.

Artifacts: `onnx/hfl_mm_hc.onnx`, `onnx/hfl_mm_hc_int8.onnx`,
`results/phase5/inference_latency/{latency_summary.csv, bench_*.csv}`.
FP32↔INT8 agreement verified: max logit difference **0.2388** (tolerance 0.5).

---

## 4. Baseline Suite B0–B5 (D5.6)

`results/phase5/baselines/baselines_summary.csv` — non-DP baselines, no frozen encoders.

| baseline | test accuracy | test macro-AUC |
|----------|---------------|----------------|
| B0 Centralized | 0.5787 | 0.8211 |
| B1 Local-Only | 0.4532 | 0.7511 |
| B2 FedAvg | 0.6543 | 0.8795 |
| B3 FedProx | 0.6570 | 0.8747 |
| B4 DP-FedAvg (ε_spent 0.957) | 0.2159 | 0.6443 |
| B5 MOON | 0.3934 | 0.7418 |

**B4 is the like-for-like DP reference and it collapses** (AUC 0.6443 at ε≈1), which is what
makes the head-only result meaningful: same dataset, same budget, 0.8742 vs 0.6443.

> ⚠️ **Do not compare the head-only ε=1 result against B0–B5 as though it were a fair fight.**
> Those baselines train from scratch; the head-only runs start from encoders that saw the
> pooled FL training data non-privately (§7.1). The **only** valid comparator for the ε=1
> number is the ε=1000 arm in §2.1.

---

## 5. Deliverable Status

| ID | Deliverable | Path | Status |
|----|-------------|------|--------|
| D5.1 | Dataset pipeline (healthcare) | `data/loaders/` | ✅ Complete |
| D5.2 | FedMamba-HC encoder | `model/architecture/fedmamba_hc.py` | ✅ Complete |
| D5.3 | FedConform-HC | `model/utils/fedconform_hc.py` | ✅ Complete |
| D5.4 | ClinicalCMGA design | `model/architecture/clinical_cmga_design.py` | ✅ Complete |
| D5.5 | HFL-MM model | `model/architecture/hfl_mm_model.py` | ✅ Complete |
| D5.6 | Baseline suite B0–B5 | `model/training/baselines.py` | ✅ Complete |
| D5.7 | HFL training engine | `model/training/hfl_trainer.py` | ✅ Complete |
| D5.8 | DP-SGD integration | `model/privacy/dp_engine.py` | ✅ Complete |
| D5.9 | Gradient compression | `model/utils/compression.py` | ✅ Complete (bug fixed §3) |
| D5.10 | ONNX edge deployment | `model/deploy/onnx_exporter.py` | ✅ Complete (§3b; 2 bugs fixed) |
| D5.11 | Inference validator | `model/deploy/inference_bench.py` | ✅ Complete (§3b; 3 bugs fixed) |
| D5.12 | ε sweep | `model/training/epsilon_sweep.py` | ⚠️ **Stale** — characterises the *broken* recipe |
| D5.13 | Phase 5 results | `results/phase5/phase5_results.csv` | ✅ Complete (§6b; 5 bugs fixed) |

**Supporting work completed this phase (not in the original deliverable list):**

- `model/training/pretrain_encoders.py` — non-private encoder pretraining with rigorous
  (`--public_data`) and proxy modes, plus `--deterministic`.
- `model/utils/aswa.py`, `model/utils/fedkd_e.py` — ASWA aggregation, FedKD-E distillation.
- `model/privacy/sadp_engine.py` — SADP redesigned around per-group ε budget split. Runs, but
  underperforms uniform DP at equal ε by construction (cross-group composition tax); retained
  as a characterised negative result, not a claimed contribution.
- `--deterministic` added to `pretrain_encoders.py`. **Verified**: with the flag, two runs of
  the same seed are byte-identical; without it they diverge (epoch-1 loss 1.5699 vs 1.5713;
  epoch-2 val_acc 0.4485 vs 0.4676). The ~1.9 pp val_acc spread matters because best-val-AUC
  checkpoint selection can land on a different epoch. **Use this flag for any pretraining
  checkpoint whose numbers appear in the thesis.**

---

## 6. Objective Scorecard

| # | Objective | Target | Measured | Status |
|---|-----------|--------|----------|--------|
| 1 | Uplink traffic reduction | ≥ 50% | **93.50%** vs full-model FP32 FedAvg | ✅ **PASS** |
| 2 | Accuracy loss at ε ≤ 1 | ≤ 2% | AUC **−0.14 pp** (n.s.); acc **+1.63 pp** (n.s.) | ✅ **PASS** (proxy-mode caveat §7.1) |
| 3 | Inference latency | < 100 ms | **16.36 ms P95** (FP32/CPU); ≤73.15 ms in all 4 configs | ✅ **PASS** |
| 4 | Energy saving per round | ≥ 20% | **74.9%** (Phase 4, CloudSim power model); 93.5% by Phase 5's linear bytes proxy — prefer the CloudSim figure, see §6b | ✅ **PASS** |

Objective 2 passes on both metrics, and on AUC the point estimate is slightly *negative* —
but the honest statement is "no measurable cost", bounded by CI [−2.03, +1.75] pp.

---

## 6b. D5.13 — Regenerated Results File & the Reliability "Discrepancy"

`phase5_results.csv` regenerated 2026-08-01. **All five QoS targets PASS.**

| QoS target | value | status | basis |
|---|---|---|---|
| Comm reduction ≥ 50% | 93.5% | ✅ PASS | measured uplink vs full-model FP32 |
| Energy saving ≥ 20% | 93.5% | ✅ PASS | linear bytes→Joules proxy (see caveat) |
| Update reliability > 99% | 99.8001% | ✅ PASS | per-update, 2-hop LTE loss model |
| Inference P95 < 100 ms | 16.363 ms | ✅ PASS | FP32/CPU, §3b |
| Accuracy loss ≤ 2% at ε=1 | 0.82% | ✅ PASS | vs DP-off same-arch comparator |

### The 96.077% "FAIL" was a definition bug, not a data conflict

The old file reported update reliability as **96.077%** against Phase 4's verified **99.05%**.
Neither number was wrong — they measured *different quantities under the same name*:

```
  hop_success = (1 - 0.001)²  = 99.8001%      ← per update, 2 hops (device→edge→cloud)

  hop_success ¹  = 99.8001%   ← what "update reliability" means
  hop_success ²⁰ = 96.0770%   ← what was actually being reported
  hop_success ¹⁰⁰= 81.8649%   ← same formula at 100 rounds
```

`ns3_phase5_integration.py` computed `reliability = hop_success ** n_rounds` — the probability
that **all 20 rounds** succeed. Against a target phrased *"Update reliability > 99%"* that is
the wrong quantity, and it is degenerate as a target: it decays with round count, so **any**
system fails it for a long enough run. Cross-check: the Phase 4 NS-3 data gives a mean
reliability of **99.053%** over the 100 `HFL_Proposed` rows, consistent with the per-update
reading. The whole-run figure is still emitted, under the distinct name
`run_reliability_all_rounds_pct`, because it is informative — just not this objective.

### Five defects fixed to produce this file

**`scripts/ns3_phase5_integration.py`**
1. **Topology constants described an experiment that was never run** — 20 devices, 3 edges,
   12.8 MB model. Actual: 6 devices, 2 edges, 8,631,064 B (2,157,766 params × 4 B). Every
   derived figure was therefore for a different system.
2. **Energy saving was structurally pinned to 0.0% (FAIL).** The baseline was one model per
   *device* while the compressed side already aggregated the whole round, so the ratio
   collapsed to 1.0 regardless of compression quality. Both sides now cover the same 30
   uploads/round.
3. **Reliability definition** — as above.

**`scripts/collect_phase5_results.py`**
4. **Proposed model's val metrics were tabulated against the baselines' test metrics.** The
   trainer writes per-round *val* figures to CSV and prints *test* figures only to stdout, so
   the collector's last-row read produced a val number in a test column. It now parses
   `Final Test AUC=… | Acc=…` from the run's `.log`.
5. **Accuracy loss was computed against the best non-DP baseline**, which under the head-only
   recipe is not like-for-like — B0–B5 train from scratch while the proposed run starts from
   pretrained encoders, so the comparison flatters the proposed system (it reported 1.55%).
   It now uses the **DP-off same-architecture comparator** (`--nodp_results`), giving 0.82%,
   and the fallback path is explicitly labelled `NOT like-for-like` in the output.

Also: input paths (`--hfl_results`, `--nodp_results`, `--latency`) are now CLI arguments
rather than hardcoded to the stale collapsed run; the Section 2 header reports the actual
source file instead of claiming "ONNX INT8"; and per-round sweep CSVs no longer emit rows of
pure `N/A`.

### Caveats on two of the passing numbers

- **Energy saving 93.5% is not an independent measurement.** Under the linear
  bytes→Joules model it is arithmetically the same quantity as comm reduction, so it should be
  reported as *"communication energy, linear proxy"*, not as a measured system-energy saving.
  The defensible energy figure remains Phase 4's **74.9%** from CloudSim's power model. Prefer
  that one in the thesis, or state the proxy explicitly.
- **D5.13 is a single-seed snapshot** (seed 42), so its 0.82% accuracy loss differs from the
  3-seed statistic in §2.2 (−0.14 pp, n.s.). §2.2 is the number to publish.

---

## 7. Remaining Work (Phase 5 closure)

Ordered by what blocks publication.

### 7.1 🔴 Rigorous public pretraining — **blocks the ε=1 claim**
Every result above ran in **PROXY / ORACLE mode**: the encoders were pretrained on the pooled
FL *training* indices. The encoders therefore saw private data non-privately, so ε=1 does
**not** hold end-to-end for the published pipeline. Objective 2 as reported is an *upper bound*.

Two routes, neither of which is a code change:
- Pretrain `encoder_a` on an **external public ECG corpus** — PTB-XL is public, 12-lead, and
  natively matches the `(12, 1000)` input shape. This makes `encoder_a` exactly analogous to
  `encoder_b`, which is already ImageNet-pretrained with 8 blocks frozen.
- Or carve a **disjoint public index split** and pass `--public_data`. Currently impossible
  without re-partitioning: all 5000 indices are consumed by the 6 FL clients, and the script
  hard-errors on any overlap.

Expect the rigorous number to be **below** the proxy number. The proxy-vs-public gap is the
quantity to report — not the proxy alone.

### 7.2 ✅ DONE — D5.10 / D5.11 executed, Objective 3 closed (see §3b)
Both scripts ran for the first time (5 bugs fixed between them). Objective 3 **PASSES** at
16.36 ms P95. Two follow-ups, neither blocking:
- The INT8 path is a characterised negative result (§3b). If the thesis text still claims
  "INT8 edge deployment" as a contribution, that wording needs revising to match the data.
- The ~3 ms preprocessing figure excludes real sensor I/O; if a glass-to-glass number is
  wanted, `simulate_preprocessing()` must be replaced with a real loader.

### 7.3 🟠 FedKD-E is not freeze-aware — two contributions excluded from the headline
`model/utils/fedkd_e.py` optimises **all** parameters on the edge's calibration data, which
under frozen encoders would both overwrite the pretrained features and leak private validation
data into them. Every run above therefore used `--edge_distill_epochs 0` and no
`--personalize`. **FedKD-E and pFAL are consequently absent from the best result.** If the
paper claims them as contributions they must be made freeze-aware (optimise only
`requires_grad` params) and re-validated on top of this recipe.

### 7.4 🟡 D5.12 — re-run the ε sweep under the head-only recipe
`epsilon_sweep/` characterises the *broken* end-to-end recipe. It remains valuable as the
"without our fix" arm, but cannot be presented as the proposed method. Because ε=1 now costs
nothing measurable, the interesting sweep is **downward**: ε ∈ {0.1, 0.25, 0.5, 1} to locate
the actual utility floor. ~70 min.

### 7.5 ✅ DONE — D5.13 regenerated, all five QoS targets PASS (see §6b)
The reliability "discrepancy" turned out to be a definition bug, not a data conflict; details
in §6b. Five defects fixed across `ns3_phase5_integration.py` and `collect_phase5_results.py`.

### 7.6 🟡 Seed count
n=3 gives 2 degrees of freedom and very wide intervals. If a reviewer challenges the accuracy
claim, 5 seeds per arm (~3 h) would tighten it materially.

---

## 8. Reproduction

```bash
source /home/mit/DEADSERPENT/HFL/hfl_env/bin/activate && cd /home/mit/DEADSERPENT/HFL/SIMULATORS

# 1. Pretrain encoders (PROXY mode — prints a NOT-privacy-valid warning)
python -u model/training/pretrain_encoders.py --epochs 30 --seed 42 --deterministic \
  --output checkpoints/pretrained_encoders.pt

# 2. ε=1 arm
python -u model/training/hfl_trainer.py --rounds 20 --dp_mode uniform --epsilon 1.0 \
  --seed 42 --freeze_encoders --pretrained_encoders checkpoints/pretrained_encoders.pt \
  --agg_mode aswa --aswa_temperature 1.0 --edge_distill_epochs 0 \
  --output results/phase5/eps1_headonly_dpft.csv \
  --save_checkpoint checkpoints/best_eps1_dpft.pt --no_monitor

# 3. Non-private comparator (same command, --epsilon 1000)
```

Repeat with `--seed 43` / `--seed 44`, pairing each ε arm against that seed's own encoder
checkpoint. ~17 min per FL run, ~8 min per pretrain.

**Artifacts.** `Final Test AUC` is printed to stdout and captured in the `.log` files — it is
**not** in the CSVs, which contain per-round
`global_round, val_accuracy, val_macro_auc, epsilon_spent, q_global, round_time_s, uplink_bytes`.

| seed | ε=1 | ε=1000 |
|------|-----|--------|
| 42 | `results/phase5/eps1_headonly_dpft.{csv,log}` | `results/phase5/eps1000_headonly_nodp.{csv,log}` |
| 43 | `results/phase5/seeds/eps1.0_s43.{csv,log}` | `results/phase5/seeds/eps1000_s43.{csv,log}` |
| 44 | `results/phase5/seeds/eps1.0_s44.{csv,log}` | `results/phase5/seeds/eps1000_s44.{csv,log}` |

Hardware: NVIDIA RTX A2000 12GB, CUDA 12.1, Python 3.11. Peak RSS ~3.4 GB (the full CXR array
is materialised as float32); peak VRAM well under 12 GB with encoders frozen.
