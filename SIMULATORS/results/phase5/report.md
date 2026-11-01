> **Superseded (2026-10-29).** Historical record of the August state. The final, authoritative results are in [`../RESULTS_FINAL.md`](../RESULTS_FINAL.md).

# Codebase Audit & Migration Report

**Project:** Hierarchical Federated Learning for Privacy-Aware, Low-Latency Multimodal IoT
**Student:** Samartha H V (251580130019) · MIT Bengaluru (MAHE)
**Date:** 2026-08-03
**Scope:** full sweep of every directory after the dataset redesign

---

## 0. Answer to the question asked

> *"so now everything is perfectly syncing here right with new dataset … and all phase 1,2,3,4 done with the new model"*

**No.** Two things must be corrected before anything else in this report is read:

1. **You have THREE datasets registered, not two.** `data/processed/healthcare/` (2.0 GB)
   still exists and `--dataset healthcare` is still selectable. Only its *raw*
   sources were deleted. It is kept deliberately so previously published Phase 5
   numbers remain reproducible.

2. **Phases 1–4 were NOT redone with the new model or data.** They were executed
   against the old plan. Phase 4's NS-3 script was in fact *broken* (a stale
   `set_seed(42, device)` call) and its config described 20 devices / 3 edges /
   100 rounds / 50 MB — a configuration that has never existed in this project.
   Both are fixed as of today, but "Phase 4 done with the new model" means only
   that it now *runs* on the new topology, not that its Phase-4 conclusions were
   re-derived and re-validated.

The rest of this report separates what is genuinely synced and verified from
what is not.

---

## 1. Datasets — VERIFIED

| key | role | modalities | pairing | clients | samples |
|---|---|---|---|---|---|
| `vitaldb` | **primary research** | 9 intraop trends + 9 masks / 34-d preop clinical | same patient, same second | 9 | 48,712 windows (6,257 cases) |
| `wear` | fast iteration | 12-ch accelerometer / 2048-d I3D video | hardware-synchronised | 22 | 38,578 windows |
| `healthcare` | **LEGACY** | ECG / chest X-ray | ⚠ synthetic rule | 6 | 5,000 |

`tests/verify_datasets.py` — **89 checks, 0 FAIL, 0 WARN.** Covers leakage,
coverage, integrity, label balance, normalisation, schema, registry consistency
and heterogeneity. Run it after ANY preprocessing change.

Six further properties were tested directly rather than assumed:

| property | result |
|---|---|
| VitalDB clinical features aligned to the right case | corr(raw age, encoded) = **1.000000** |
| All windows of a case share identical modality B | 0/50 disagree |
| WEAR I3D row *k* ↔ inertial `[k·50, k·50+100)` | 2,232 labels identical to independent rebuild |
| Stored windows == independent raw-slice reconstruction | 4/4 exact |
| Loaders return exactly what preprocessing wrote | exact, both datasets |
| Preprocessing deterministic on re-run | **27/27 byte-identical** |

Non-IID structure, measured not asserted:

```
vitaldb : 9 clients · 2,038–15,383 samples (x7.5) · positive rate 3.2%–50.7% (x16)
wear    : 22 clients · 1,499–2,196 samples (x1.5) · dominant class 6–12%
```

---

## 2. What is SYNCED with the new datasets

| component | how it is kept in sync |
|---|---|
| `data/loaders/datasets.py` | **registry** — single source of truth for paths, client/class counts, channel counts, modality-B contract, required files |
| `data/loaders/{preprocess,fetch}_*.py`, `*_dataset.py` | one module per dataset, fully separate |
| `model/architecture/hfl_mm_model.py` | `n_channels_a` + `modality_b` — 12/18/24-channel and image/feature variants all build |
| `model/training/hfl_trainer.py` | `--dataset` resolves everything; pooled val; AUPRC; case aggregation; class weighting |
| `model/deploy/onnx_exporter.py` | input shapes derived from the registry |
| `model/deploy/inference_bench.py` | shapes + class count read off the ONNX graph |
| `engineering/preflight.py` | validates each dataset's own `required_files` |
| `scripts/ns3_phase5_integration.py` | `resolve_topology()` reads `partition_meta.json` + real model params |
| `cloudsim-plus/.../HFLCloudSimulation.java` | CLI args `--dataset --devices --edges --rounds --model_mb` |
| `config/hfl_config.json` | corrected; per-dataset block under `datasets{}` |
| `ns3/hfl-scenarios/hfl_network_sim.py` | reads the corrected config |
| `tests/` | `verify_datasets.py` (new) + `test_regression.py` (repaired) |
| `onnx/` | regenerated per dataset |

### Verified outputs

```
DATA AUDIT   89 checks · 0 FAIL · 0 WARN
REGRESSION   6/6 passed
TRAINER      vitaldb AUROC 0.6762 AUPRC 0.3521 | wear AUROC 0.5349 AUPRC 0.0671   (1-round smoke)
ONNX         vitaldb_fp32 (18,300)+(34,) -> 2 cls   wear_fp32 (12,100)+(2048,) -> 18 cls
LATENCY      vitaldb 3.07 ms P95 · wear 1.22 ms P95        (target <100 ms)
NS-3 P5      vitaldb comm 93.7% · wear comm 94.4% · reliability 99.800%
NS-3 P4      9 dev / 2 edge / 7.46 MB · comm 75.0% · reliability 99.01%
CLOUDSIM     vitaldb energy 72.3% saving · wear 76.8% saving
```

---

## 3. Bugs found and fixed in this migration

Ordered by how badly each would have corrupted results.

| # | bug | impact |
|---|---|---|
| 1 | **Model selection used ONE client's val split** (`device 0`) | every best-checkpoint decision in the project was made on one client's distribution |
| 2 | **One subject's sensor dropout destroyed 25 % of WEAR input** — `np.mean` over a channel containing NaN propagated to all 38,578 windows | an entire sensor silently zeroed while training reported an accuracy |
| 3 | **WEAR temporal split was label-disjoint** — subjects perform activities in sequence, so val held 3–4 of 18 classes | undefined macro AUC, 2 % accuracy, no crash |
| 4 | **Conformal calibration emitted pure noise** — Laplace scale 10 on a [0,1] statistic; \|noise\| exceeded the range 90.5 % of the time | FedConform-HC (D5.3) was non-functional |
| 5 | **Conformal privacy budget never accounted** — spent per device per edge round (100× at 20 rounds) | the reported ε was not the ε actually spent |
| 6 | **Binary AUC silently returned 0.0** — sklearn raised, except-branch returned a plausible zero | a working binary task looked like total failure |
| 7 | **ONNX exported the OLD healthcare architecture** after the dataset change | shipped artifacts corresponded to no model in use |
| 8 | **`inference_bench.py` could not run any current model** — hardcoded `(1,12,1000)`, 5-class name list | Objective 3 unmeasurable |
| 9 | **CloudSim configured for 20 devices / 3 edges / 50 MB** | never matched any experiment |
| 10 | **Stale `device_09/10_*.npy`** survived the 11→9 client change | a later run could have picked them up |
| 11 | **`test_regression.py` broken at import** | the regression suite had not run in some time |
| 12 | **Phase-4 NS-3 script broken** (`set_seed(42, device)`) | Phase 4 was not reproducible |
| 13 | VitalDB `'>89'` age string; `dtype == object` check never fired on pandas 3 | crash, then silent miss |
| 14 | WEAR INT8 unloadable (ORT Gemm→MatMul rewrite) | INT8 now opt-in, non-fatal; FP32 ships |

Earlier in the same effort: the ε=1 DP collapse (head-only fine-tuning), the
compressor zero-padding (−78.9 % uplink), the NS-3 reliability definition bug,
and the D5.13 val-vs-test metric mismatch.

---

## 4. What is NOT synced — remaining work

### 4.1 🔴 Blocking the scientific claim

**The modality ablation has never been run.** Nobody has shown that fusion beats
either modality alone on the new data. This is the entire reason the datasets
were changed. If the clinical vector does all the work on VitalDB, or the I3D
features do it on WEAR, the multimodal claim fails again — for a different
reason but just as fatally.

Required: retrained unimodal baselines (not input-zeroing) — signals-only,
clinical-only, fused on VitalDB; inertial-only, video-only, fused on WEAR.

### 4.2 🔴 Still healthcare-only

| file | state |
|---|---|
| `model/training/baselines.py` | **0 dataset-aware refs, 7 healthcare refs.** B0–B5 cannot run on the new data — so there is currently NO baseline comparison for either new domain |
| `model/training/epsilon_sweep.py` | 0 dataset-aware refs, 3 healthcare refs |
| `run_phase5.py` | hardcoded `DATA_DIR = data/processed/healthcare` |
| `run_pipeline.py` | 7 healthcare refs |

Until `baselines.py` is ported there is nothing to compare the proposed method
against on VitalDB or WEAR.

### 4.3 🟠 Documents describing superseded work

| document | state |
|---|---|
| `DATASET & MODEL GUIDE/01_Datasets.txt` | ✅ **rewritten** for the three datasets |
| `DATASET & MODEL GUIDE/02_Model_Design.txt` | ⚠ no `FeatureEncoder`, no `n_channels_a`, no modality-B switch |
| `DATASET & MODEL GUIDE/03_NS3_CloudSim_Integration.txt` | ⚠ predates the topology corrections |
| `document/02_phase_reports/Phase 1–4.txt` | ⚠ describe the old plan and old data |
| `document/02_phase_reports/Phase 5.txt` | ⚠ stale results |
| `OVERALL PROJECT OUTPUT/01_PHANTOM_FL_Novel_Model.txt` | ⚠ claims 5 innovations; see §5 |
| `OVERALL PROJECT OUTPUT/00_Overall_Project_Report.txt`, `IP & N.txt` | ⚠ pending |
| `document/05_reference/literature/*` | ✅ unaffected — problem statement, objectives, literature review still valid |
| `results/phase5/RESULTS.md` | ⚠ describes healthcare-era Phase 5; needs a new-domain edition |

### 4.4 🟡 Methodological

- **≥5 seeds** per configuration (3 gives 2 df and very wide intervals)
- **Case-level metrics** are computed for VitalDB but window-level still drives
  checkpoint selection
- **Objective 2 wording** — "≤2 % accuracy loss" must be restated as AUROC/AUPRC
  for a 19.7 %-positive task where 80 % accuracy is free
- **Energy figures are not corroborating** — NS-3's 93–94 % is a linear
  bytes→Joules proxy, CloudSim's 72–77 % comes from a power model. Different
  quantities; do not present them as agreeing
- `clinical_cmga_design.py` — the I1 flagship, still implemented nowhere

---

## 5. The uncomfortable finding about PHANTOM-FL

Of the five claimed innovations, measured against the code:

| # | innovation | status |
|---|---|---|
| I1 | Cross-Modal Gated Attention | ❌ **not wired at all** — 0 references; the model uses `LateFusionHead`, which is the very "blind late fusion" I1 was written to fix |
| I2 | SADP (adaptive DP) | ⚠ wired, **measured worse** than uniform (cross-group composition tax, σ 11.3 → 70) |
| I3 | ASWA | ✅ wired, **never ablated** |
| I4 | FedKD-E | ⚠ wired but **excluded from every headline run** (not freeze-aware) |
| I5 | pFAL | ⚠ **measured zero effect** |

**Zero validated positive innovations today.** The genuinely strong result is the
one not on that list: diagnosing the ε=1 DP collapse and fixing it with head-only
DP fine-tuning, at no measurable utility cost.

---

## 6. Recommended order of work

1. **Modality ablation** on both domains — decides whether the redesign worked
2. **Port `baselines.py`** to the registry — without it there is no comparison
3. **Re-run the headline experiments** (5 seeds, ε=1 vs ε=1000, both domains)
4. **Decide I1** — implement cross-modal attention or drop the claim
5. **Ablate I3/I4/I5** — keep what measures, cut what does not
6. **Rewrite the documents** to match measurement
7. **Regenerate D5.13 / RESULTS.md** for the new domains

---

## 7. Honest summary

**Data and preprocessing: verified.** Leakage, alignment, determinism, label
integrity and non-IID structure are tested rather than asserted, with a
repeatable 89-check audit as the guarantee.

**Infrastructure: synced.** Trainer, ONNX, latency, NS-3 (both phases),
CloudSim, preflight, config and tests all read the dataset registry rather than
hardcoded constants — the failure mode that produced most of the bugs above.

**Results: not yet established.** Every number in §2 is a 1–3 round smoke test.
They prove the plumbing works; they say nothing about achievable performance.

**The claim "multimodal fusion improves performance" is still unsupported.** It
was unsupported before because of the pairing rule; it is unsupported now
because the experiment has not been run. That is the next thing to do.
