# Phase 5 artifact status

`RESULTS.md` is the authoritative record. This file exists so nobody cites a
superseded CSV by accident.

## ✅ CURRENT — safe to cite
| artifact | what it is |
|---|---|
| `RESULTS.md` | authoritative Phase 5 record |
| `phase5_results.csv` | D5.13, regenerated 2026-08-01, all 5 QoS targets PASS |
| `eps1_headonly_dpft.{csv,log}` | ε=1 head-only DP-FT, seed 42 |
| `eps1000_headonly_nodp.{csv,log}` | DP-off comparator, seed 42 |
| `seeds/eps{1.0,1000}_s{43,44}.{csv,log}` | seeds 43–44 |
| `inference_latency/` | D5.10/D5.11, Objective 3 (16.36 ms P95) |
| `baselines/` | B0–B5 |

## ⚠️ SUPERSEDED — do not cite
| artifact | why |
|---|---|
| `epsilon_sweep/` | broken end-to-end recipe — see its README |
| `pre_m7_fix_backup/` | pre-accounting-fix — see its README |
| `hfl_mm_hc_results.csv` | collapsed model (Acc 0.2471 / AUC 0.494) |
| `hfl_mm_hc_sadp_results.csv`, `hfl_mm_hc_sadp_full_results.csv` | SADP characterised **negative** (worse than uniform DP at equal ε; cross-group composition tax drives σ 11.3 → 70). Cite as a negative result only |
| `hfl_training.log`, `sadp_full_run.log`, `epsilon_sweep_run.log` | logs of the above |

## 🔴 Caveat applying to ALL Phase 5 results
Every run above used the **rule-paired healthcare data**, where the chest X-ray
is assigned by `CXR bucket = f(ECG label)`. Measured consequence: a CXR-only
model scores 0.3523 accuracy against a 0.20 random baseline. **These accuracy
figures are not evidence of multimodal fusion.** Communication, DP-accounting,
latency and energy results are unaffected — they do not depend on pairing.
