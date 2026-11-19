# Key Numbers — One-Page Cheat Sheet

Print this page and keep it beside you while presenting. All values are from the final manuscript.

## Setup
| Item | Value |
|---|---|
| Privacy budget (training) | ε = 0.9, δ = 10⁻⁵, per patient (+ ε_conf = 0.1 for the evaluated conformal release → 1.0) |
| Independent recheck | PLD ε ∈ [0.880, 0.900]; Rényi 0.974 |
| Clip C; patients per step B | 1; 64 |
| Rounds | 10 cloud × 5 edge; 2 edges (2–16 in scaling test) |
| Update encoding | top-20 %, 8-bit, error feedback |
| Model | 1,864,227 params; head 559,874 (30 %) privatized |
| Seeds | 5 paired (3 for grids); 16 LiRA shadows |

## Datasets
| | VitalDB | WEAR | eICU |
|---|---|---|---|
| Clients | 9 specialties | 22 participants | 187 hospitals |
| Individuals | 5,974 | 22 | 132,736 |
| Records/individual | 7.9 | ≈ 1,750 | 28.5 |
| Task | ICU admission | 18 activities | mortality |
| Prevalence | 18.84 % | — | 4.22 % |

## System Objectives
| | VitalDB | WEAR | eICU | Target |
|---|---|---|---|---|
| Uplink reduction | 90.8 % | 96.1 % | 92.3 % | ≥ 50 % ✅ |
| Round latency cut | 16.9 % | 21.7 % | 33.4 % | > 0 ✅ |
| ε | 0.900 | 0.766 (record) | 0.900 | ≤ 1 ✅ |
| Utility loss (pts) | −1.18 ✅ | 1.97 pp ⚠ | 3.10 ⚠ | ≤ 2 |
| P95 inference | 2.30 ms | 0.75 ms | 0.24 ms | < 100 ms ✅ |
| Delivery | 100.00 % | 99.94 % | 97.83 % ❌ (met ≥ 8 edges) | > 99 % |
| Energy saving | 72.3 % | 76.8 % | 79.6 % | ≥ 20 % ✅ |

⚠ = inconclusive (interval spans target) · ❌ = not met

## Privacy Cost (RQ1)
- VitalDB (person-level): 0.8200 → **0.8318** AUROC; cost −1.18 [−1.63, −0.73], p = 0.002
- eICU transcript: 0.8239 → 0.7929; cost **3.10 [1.55, 4.65]**
- eICU end to end: **3.88 [2.60, 5.17]**
- Cost of the unit (record → patient, VitalDB, ε = 1): AUROC −0.0170; AUPRC −0.0582
- Per-client σ_k: eICU 4.85–29.34 (median 13.76); VitalDB 6.34–15.56
- Disjoint vs oracle encoders: −1.57 AUROC points

## Initialization vs Subset (RQ3)
- Init effect at ε = 0.5: **+0.199** (VitalDB), **+0.358** (WEAR)
- Subset effect: −0.006 to −0.0025 (VitalDB), ≤ 0.0013 (WEAR) — not resolved
- Random-init private model loses 0.19 AUROC; pretrained loses 0.004

## k-Law (RQ2), AUPRC gap record − patient
| k | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| VitalDB | −0.0071 | +0.0486 | +0.0796 | +0.0872 | — |
| eICU | −0.0011 | +0.0048 | +0.0081 | +0.0099 | +0.0103 |
| Forecast | 0 | 0.0515 | 0.0816 | 0.0876 | 0.0878 |
- Fit A = 0.1015, RMSE 0.0119; k ≤ 4 fit predicts 0.0904 at k = 8 (obs. 0.0872)
- eICU: shape transfers, magnitude ≈ 1/9

## Fusion
- VitalDB: +0.0370 AUROC (0.8653 vs 0.8283), +0.0671 AUPRC
- eICU natural: +0.0037 (no gain); at parity: **+0.0291**, 5/5 seeds, p = 0.019
- WEAR: single modality 0.9976 — no headroom

## Ablation (VitalDB)
- Full 0.8541 AUROC, 252 MB · no hierarchy −0.0058 · no privacy **−0.0234** · no sparsification +0.0012 (1260 MB) · no quantization +0.0001 (403 MB)

## Membership-Inference Audit (VitalDB, person-level)
| | Loss AUC | LiRA AUC | Floor |
|---|---|---|---|
| No DP (control) | 0.556 | 0.605 | 0.553 |
| Record-level DP | 0.522 | **0.576** | 0.511 |
| Patient-level DP | 0.506 | **0.503** | 0.508 |
- Record − patient (LiRA): +0.073 [0.054, 0.092], p < 0.001

## Prior Systems
| | ε | AUROC | Uplink MB | LiRA (margin) |
|---|---|---|---|---|
| PP-HFM (VitalDB) | 0.90 | 0.8318 | 252 | 0.503 (−0.005) |
| HED-FL (VitalDB) | ∞ | 0.8262 | 560 | 0.581 (+0.026) |
| FL2DP (VitalDB) | — | 0.8195 | 1008 | 0.608 (+0.049) |
| PP-HFM (eICU) | 0.90 | 0.7936 | 5235 | — |
| HED-FL (eICU) | ∞ | 0.8252 | 12541 | — |
- 2.2–4.0× less uplink

## Latency (VitalDB)
- Preprocess 0.110 · forward 2.165 · post 0.008 → **P95 2.299 ms**; 8-bit graph P95 17.34 ms (rejected)
- Round latency: VitalDB 90.5 → 75.2 ms · WEAR 104.5 → 81.8 · eICU 261.4 → 174.1
