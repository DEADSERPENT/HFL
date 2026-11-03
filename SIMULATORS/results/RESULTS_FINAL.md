# PP-HFM — Final Results Record

**Status:** final for the manuscript, 2026-10-30. This file supersedes
`phase5/RESULTS.md`, `phase5/README_ARTIFACT_STATUS.md` and `phase5/report.md`,
which are kept as historical records of the August state.

Every number below is from the corrected patient-level mechanism (noise divided
by the *expected* batch size, fixed 2026-10-22) and appears in the manuscript
(`PLDP/`). Results produced before that fix are archived, never
overwritten, in `_archive_pre_dpfix_20261022/`.

**Update 2026-11-01 (person-level VitalDB).** The VitalDB numbers in
sections 2, 7 and 8 below were obtained on the *case-level* partition, in which
55 of 940 test persons also had a training case and 68 training persons had
cases on two clients. They are kept unchanged as the historical case-level
record. The manuscript now quotes the person-level rerun of section 8a for the
privacy cost, the cost of the unit, the baselines and the audit; all other
VitalDB results (sections 3–6, disjoint encoders, attribution) remain
case-level and are labeled so in the paper.

All paths are relative to `SIMULATORS/results/`. Costs are *non-private minus
private* and paired by seed unless stated; intervals are 95 % Student-t.

---

## 1. System objectives (O1–O4)

| Objective | VitalDB | WEAR | eICU | Target | Source |
|---|---|---|---|---|---|
| O1 uplink reduction | 90.8 % | 96.1 % | 92.3 % | ≥ 50 % | `phase5/uplink_measured_*.json`, `ns3/` |
| O1b round-latency cut | 16.9 % | 21.7 % | 33.4 % | > 0 % | `ns3/ns3_results_*.csv` |
| O2a training budget ε | 0.900 (+0.1 conformal = 1.000) | 0.766 (record; +0.2 conformal = 0.966) | 0.900 (+0.1 conformal = 1.000) | ≤ 1 | `phase5/privacy_total_*.json`; VitalDB person-level `o2b_system/vitaldb_person/dp_s*/privacy_total_vitaldb_person.json` |
| O2b utility loss | −1.18 AUROC pts (person-level; case-level −0.90) | 1.97 pp acc. [1.76, 2.17] (**inconclusive**: interval spans 2; record-level) | 3.09 [1.37, 4.81] AUROC pts (**inconclusive**: interval spans 2, point estimate above; end to end 3.91 [2.40, 5.42] **not met**) | ≤ 2 | `phase5/o2b_system/{vitaldb_person,eicu}/o2b_paired.json` (case-level: `vitaldb/`) |
| O3a P95 inference latency | 2.30 ms | 0.75 ms | 0.24 ms | < 100 ms | `phase5/latency_bench/` |
| O3b update delivery | 100.00 % | 99.94 % | 97.83 % (**not met** at 2 edges; met from 8) | > 99 % | `ns3/edge_scaling/` |
| O4 energy saving per round | 72.3 % | 76.8 % | 79.6 % | ≥ 20 % | `cloudsim/cloudsim_results_*.csv` |

Scored by `scripts/check_objectives.py` → `phase5/objectives_*.json`, re-scored
2026-11-01 from the final sources (VitalDB with `--headline vitaldb_person`):
O2a is the training budget of the final headline runs (total with conformal
recorded alongside), O2b on the clinical corpora is the paired AUROC cost from
`o2b_system/<ds>/o2b_paired.json`, and O3a comes from `latency_bench/`. The
verdict is taken from the interval, so the eICU utility loss is INCONCLUSIVE.
The earlier files (old latency benchmark, O2b scored on accuracy) are kept as
`phase5/objectives_*_superseded.json`.

## 2. Cost of the patient-level guarantee (stage F, five seeds 42–46)

| Corpus | Private | Non-private | AUROC cost [CI] | AUPRC cost [CI] | Bal. acc. cost [CI] |
|---|---|---|---|---|---|
| VitalDB (oracle encoders) | 0.8395 | 0.8304 | −0.90 [−1.82, +0.02] | −1.88 [−3.84, +0.07] | −1.08 [−3.17, +1.01] |
| VitalDB (disjoint encoders, F2) | 0.8237 | 0.8252 | +0.14 [−0.33, +0.62] | +2.21 [−0.03, +4.46] | — |
| eICU (training-fitted constants) | 0.7936 | 0.8245 | 3.09 [1.37, 4.81] | 1.72 [0.84, 2.60] | 0.50 [−0.18, +1.18] |
| eICU end to end (pool-fitted constants, G) | 0.7819 | 0.8209 | 3.91 [2.40, 5.42] | 2.66 [1.82, 3.49] | 2.69 [1.57, 3.82] |

Points of AUROC/AUPRC/balanced accuracy. Sources:
`phase5/o2b_system/{vitaldb,vitaldb_disjoint,eicu,eicu_poolnorm}/o2b_paired.json`.
Drivers: `scripts/run_dpfix_stageF.sh`, `run_dpfix_stageF2.sh`,
`run_dpfix_poolnorm.sh`; summary `scripts/o2b_paired_summary.py`.

**Cost of the unit** (record → patient at matched ε = 1, VitalDB, five seeds):
AUROC −0.0147 [−0.0253, −0.0042], AUPRC −0.0783 [−0.1035, −0.0532].
Source `phase5/patient_dp/vitaldb/`.

## 3. Initialization versus privatized subset (recipe decomposition)

B4 full-model DP, random init → B7 full-model DP, pretrained init → B6 head-only
DP, pretrained init. Three seeds per ε.

| ε | VitalDB B4→B7 | VitalDB B7→B6 | WEAR B4→B7 | WEAR B7→B6 |
|---|---|---|---|---|
| ∞ | +0.0129 | +0.0139 ± 0.0124 | +0.0021 | −0.0002 ± 0.0003 |
| 1 | +0.1841 | −0.0059 ± 0.0063 | +0.2827 | +0.0003 ± 0.0008 |
| 0.5 | +0.1991 | −0.0042 ± 0.0043 | +0.3580 | +0.0013 ± 0.0088 |

**Finding:** initialization carries the advantage at every budget; restricting
noise to the head changes AUROC by at most 0.006. Source
`phase5/epsilon_sweep_rigorous/`, driver `scripts/run_b467_multiseed.py`.

## 4. Scaling law of the unit's cost, A(1 − 1/k)

AUPRC gap (record arm − patient arm), three seeds.

| k | VitalDB gap | p | eICU gap | eICU forecast |
|---|---|---|---|---|
| 1 | −0.0071 ± 0.0599 | 0.661 | −0.0011 ± 0.0369 | 0.0000 |
| 2 | +0.0486 ± 0.0129 | 0.004 | +0.0048 ± 0.0057 | 0.0515 |
| 4 | +0.0796 ± 0.0163 | 0.002 | +0.0081 ± 0.0554 | 0.0816 |
| 8 | +0.0872 ± 0.0248 | 0.004 | +0.0099 ± 0.0437 | 0.0876 |
| 16 | — | — | +0.0103 ± 0.0332 | 0.0878 |

VitalDB fit A = 0.1015 (RMSE 0.0119); fitted on k ≤ 4 it predicts 0.0904 at
k = 8 against 0.0872 observed. On eICU the shape transfers (k = 1 control holds,
saturation by k = 8) but the magnitude is about one ninth of the forecast,
which was registered before the corpus was built. Sources
`phase5/k_scaling/`, `phase6/*/k_scaling_*.csv`,
`phase5/k_scaling/{a2_matched_budget,klaw_theory_check}.json`; driver
`scripts/k_scaling.py`. `a2_matched_budget.json` was regenerated on 2026-11-01
with `scripts/analyze_k_matched.py` (no training). Its eICU column had been
written from the pre-fix eICU grid, and only that column changed. The earlier
file is kept as `a2_matched_budget_superseded.json` (SHA-256 `677eb2f5…`); the
refreshed one is `58fa962d…`.

**Clipping rule (N-A2/D):** count-normalized clipping does not recover the cost
on eICU (upper bound +0.0043 < registered +0.010) and explains at most one
eighth of it on VitalDB. Source `phase5/nd_clipnorm/`.

## 5. Multimodal fusion

VitalDB: fused 0.8653 ± 0.0072 against 0.8283 ± 0.0087 for the better single
modality (five seeds). eICU: +0.0020 natural; +0.0291 ± 0.0211 (p = 0.019)
after titrating the stronger stream to parity. Sources
`phase5/ablation_*.json`, `phase5/fusbal_*.json`.

## 6. Component ablation (VitalDB, record-level, three seeds)

Only removing privacy is resolved (−0.0234 ± 0.0205 AUROC); removing the
hierarchy −0.0058 ± 0.0088, sparsification +0.0012, quantization +0.0001.
Source `phase6/vitaldb/ablation_*`.

## 7. Patient-level membership-inference audit (VitalDB, 16 shadows)

| Configuration | Attack | AUC | 95 % CI | Floor | Margin |
|---|---|---|---|---|---|
| Control, no DP | LiRA | 0.6230 | [0.598, 0.648] | 0.563 | +0.060 |
| Record-level DP | LiRA | 0.5477 | [0.488, 0.608] | 0.525 | +0.023 |
| Patient-level DP | loss | 0.5243 | [0.520, 0.529] | 0.516 | +0.008 |

The predicted large difference between the units (0.7 vs 0.5) is refuted.
Sources `phase5/lira/vitaldb/*.csv`, `phase5/mia_difficulty_floor_vitaldb.csv`;
drivers `scripts/lira_attack.py`, `scripts/run_dpfix_lira.sh`.

## 8. Prior-art baselines (complete, 2026-10-30)

HED-FL (De Rango et al., 2023) and FL2DP (Gu et al., 2024), re-implemented in
`model/training/lit_baselines.py` and run through the same trainer, data,
encoders, rounds and seeds (42–46) as stage F. HED-FL: hierarchy, no DP, dense
upload, 60 % participation. FL2DP: per-coordinate exponential mechanism plus
shuffler, no hierarchy; VitalDB only (about two GPU days per seed on eICU).

| Corpus | System | ε | AUROC | Δ vs PP-HFM (DP) [CI], p | Δ vs non-private, p | AUPRC | Uplink MB |
|---|---|---|---|---|---|---|---|
| VitalDB | PP-HFM | 0.90 | 0.8395 | — | — | 0.5295 | 252.0 |
| VitalDB | HED-FL | ∞ | 0.8339 | −0.0056 [−0.0091, −0.0020], 0.012 | +0.0035, 0.33 | 0.5164 | 559.9 (2.22×) |
| VitalDB | FL2DP | none finite | 0.8265 | −0.0129 [−0.0214, −0.0044], 0.013 | −0.0039, 0.14 | 0.5191 | 1007.8 (4.00×) |
| eICU | PP-HFM | 0.90 | 0.7936 | — | — | 0.2390 | 5235.4 |
| eICU | HED-FL | ∞ | 0.8252 | +0.0317 [+0.0156, +0.0477], 0.005 | +0.0008, 0.39 | 0.2567 | 12541.2 (2.40×) |

AUPRC vs PP-HFM: VitalDB HED-FL −0.0131 [−0.050, +0.024], FL2DP −0.0104
[−0.026, +0.006] (unresolved); eICU HED-FL +0.0177 [+0.0075, +0.0278].

**Leakage (VitalDB, 16 shadows, same splits as §7):**

| System | Loss AUC | LiRA offline | Floor | LiRA margin | LiRA − PP-HFM [CI] |
|---|---|---|---|---|---|
| PP-HFM (patient DP) | 0.524 | 0.519 | 0.516 | +0.003 | — |
| HED-FL | 0.570 [0.562, 0.579] | 0.585 [0.554, 0.617] | 0.570 | +0.016 | +0.066 [0.032, 0.100] |
| FL2DP | 0.584 [0.581, 0.587] | 0.618 [0.608, 0.629] | 0.573 | +0.045 | +0.099 [0.087, 0.111] |

FL2DP's candidate set is built from the private gradient value (its Eqs.
11–12), so it satisfies no finite ε, and it leaks more than HED-FL, which adds
no noise. HED-FL matches the non-private reference, so on eICU its lead is the
price of the patient-level guarantee. No eICU LiRA for the baselines.

Sources `phase5/baselines_lit/{vitaldb,eicu}/lit_paired.json`,
`phase5/lira/vitaldb/lira_vitaldb_hedfl_fl2dp.csv` (paired against
`lira_vitaldb_sample_patient.csv`). Driver `scripts/run_lit_baselines.sh`;
summary `scripts/lit_baselines_summary.py`.

## 8a. Person-level VitalDB rerun (2026-11-01)

Partition `vitaldb_person` (`scripts/make_person_partitions_vitaldb.py`,
report `phase5/vitaldb_person/partition_report.json`): each person in one split
and on one client; 200 cases (1,553 windows) dropped, never moved. Train /
val / test: 4,221 / 868 / 885 persons, 33,491 / 6,773 / 6,895 windows;
prevalence 18.84 %. Metadata note: the `split` field of
`data/processed/partitions/vitaldb_person/partition_meta.json` still reads
"by CASE" (copied from the case-level file). It is left unedited because every
run records its MD5 (`partition_meta_md5` 85739fdff91617b5); the `unit` field
and `partition_report.json` are correct, the sidecar
`partitions/vitaldb_person/PROVENANCE.json` records hashes, counts and the
legacy label, and the generator now writes a
person-level label. Driver `scripts/run_person_vitaldb.sh` (exact argv of the
original runs, only `--dataset` changed), finished 2026-11-01 02:43.

**Privacy cost (stage F, seeds 42–46, ε_train 0.900 + ε_conf 0.100).** Source
`phase5/o2b_system/vitaldb_person/o2b_paired.json`. Cost = non-private − private.

| Measure | Private | Non-private | Cost [95 % CI] | p |
|---|---|---|---|---|
| AUROC | 0.8318 | 0.8200 | −0.0118 [−0.0163, −0.0073] | 0.002 |
| AUPRC | 0.4826 | 0.4479 | −0.0347 [−0.0633, −0.0061] | 0.028 |
| Balanced acc. (val thr.) | 0.7653 | 0.7622 | −0.0031 [−0.0123, +0.0062] | 0.41 |

Per-client σ 6.34–15.56. Case-level was −0.0090 [−0.0182, +0.0002].

**Cost of the unit (ε = 1, five seeds).** Source
`phase5/patient_dp/vitaldb_person/unit_paired.json` (`scripts/person_unit_summary.py`).
AUROC 0.8423 → 0.8254, −0.0170 [−0.0269, −0.0071], p = 0.009; AUPRC
0.5275 → 0.4694, −0.0582 [−0.0701, −0.0462], p < 0.001. Case-level was −0.0147.

**Prior systems (five seeds).** Source `phase5/baselines_lit/vitaldb_person/lit_paired.json`.

| System | AUROC | AUPRC | Uplink MB | Baseline − PP-HFM (AUROC) | (AUPRC) |
|---|---|---|---|---|---|
| PP-HFM (private) | 0.8318 | 0.4826 | 252 | — | — |
| HED-FL | 0.8262 | 0.4527 | 560 | −0.0056 [−0.0131, +0.0018], p = 0.10 | −0.0299 [−0.0553, −0.0045] |
| FL2DP | 0.8195 | 0.4576 | 1008 | −0.0123 [−0.0181, −0.0064], p = 0.004 | −0.0250 [−0.0351, −0.0149] |

HED-FL − non-private reference: +0.0062 [0.0011, 0.0113] AUROC.

**Membership-inference audit (16 shadows, 600 members / 600 non-members).**
Sources `phase5/lira/vitaldb_person/lira_vitaldb_person_{head_nodp,sample_patient,hedfl_fl2dp}.csv`.

| Configuration | Seeds | Loss AUC | Offline LiRA AUC | Floor | LiRA margin |
|---|---|---|---|---|---|
| Control (no DP) | 3 | 0.556 [0.551, 0.561] | 0.605 [0.528, 0.681] | 0.553 | +0.052 |
| Record-level DP | 5 | 0.522 [0.514, 0.531] | 0.576 [0.557, 0.594] | 0.511 | +0.065 |
| Patient-level DP | 5 | 0.506 [0.502, 0.510] | 0.503 [0.475, 0.531] | 0.508 | −0.005 |
| HED-FL | 5 | 0.552 | 0.581 | 0.555 | +0.026 |
| FL2DP | 5 | 0.561 | 0.608 | 0.559 | +0.049 |

Control online LiRA (global variance) 0.597 [0.586, 0.609], above its floor.
Record − patient, paired: offline LiRA +0.073 [0.054, 0.092] (p < 0.001), loss
+0.016 [0.010, 0.023] (p = 0.002); online −0.010 and global-variance +0.016,
both unresolved. HED-FL − PP-HFM offline LiRA +0.078 [0.050, 0.106]; FL2DP −
PP-HFM +0.105 [0.079, 0.130]. Case-level (section 7) resolved no record −
patient difference. Figure: `paper/figures/fig10_ablation_mia.py` (panel b now
reads `vitaldb_person`).

## 8b. Privacy-accounting audit (2026-11-02)

Independent re-derivation of the patient-level accounting for the 20 headline
runs (`o2b_system/{eicu,eicu_poolnorm,vitaldb_person,vitaldb_disjoint}/dp_s42–46`).
Full report: `../../pp-hfm-release-review/FINAL_AUDIT_2026-11-02.md`.

| Check | Result |
|---|---|
| Per-client σ_k re-derived from partition + config | identical to `train.log` on every run (eICU 4.785–29.338; VitalDB person 6.343–15.556) |
| Per-client ε, Opacus PRV (the headline accountant) | 0.8998–0.9000; reported training ε 0.9000 |
| Same mechanism, independent PLD (own code, exact-mass lattice) | bracket [0.880, 0.900] |
| Same mechanism, RDP (Opacus and own code agree) | 0.974 — a looser bound on the *same* mechanism, not a discrepancy |
| Train / validation / test person overlap | 0 in every configuration |
| (A1) one client per training person | holds on VitalDB person-level; **fails on eICU** for 2,177 of 74,327 training persons (2.9 %) |

eICU persons held by several hospitals (clients = `hospitalid`, unit = `uniquepid`)
compose the mechanisms of every hospital holding them. Composed training ε at
δ = 10⁻⁵, Opacus PRV (independent PLD brackets the worst set at every m):

| Hospitals | Training persons | Composed ε (PRV) | RDP bound | Basic m·ε |
|---|---|---|---|---|
| 1 | 72,150 | ≤ 0.900 | 0.974 | 0.9 |
| 2 | 2,097 | ≤ 1.32 | 1.42 | 1.8 |
| 3 | 75 | ≤ 1.64 | 1.77 | 2.7 |
| 4 | 5 | ≤ 1.92 | 2.08 | 3.6 |

The evaluated conformal release (ε_conf = 0.1 per hospital, pure DP) composes to
at most 0.2 / 0.3 for the 509 of 19,916 eICU validation persons (2.6 %) at two or
three hospitals. Disclosed in both manuscripts; utility results unchanged.

**k = 1 diagnostic** (`phase5/diagnostics/k1_record_rerun_eps080/`, not part
of the prespecified analysis): the ε = 0.8 VitalDB grid reuses a record arm run
on 2026-09-21/22 code. Retrained on the current code with the identical partition
and seeds, it reproduces to within 0.002 AUPRC on all three seeds (0.5169/0.5171,
0.5058/0.5038, 0.5665/0.5662), so the grid's +0.0398 k = 1 offset is not a
code-version artefact.

## 9. Reproducing

```
bash SIMULATORS/scripts/run_dpfix_stageA.sh      # system runs, all corpora
bash SIMULATORS/scripts/run_dpfix_stageBE.sh     # k-law, clipping, MIA targets
bash SIMULATORS/scripts/run_dpfix_stageF.sh      # paired privacy cost
bash SIMULATORS/scripts/run_dpfix_stageF2.sh     # disjoint encoders (VitalDB)
bash SIMULATORS/scripts/run_dpfix_poolnorm.sh    # eICU end to end
bash SIMULATORS/scripts/run_dpfix_lira.sh        # LiRA audit
bash SIMULATORS/scripts/run_lit_baselines.sh     # HED-FL and FL2DP
```

Each driver is resumable and writes a completion marker under
`phase5/.dpfix/` or `phase5/.lit/`.

## 10. Data policy

eICU is credentialed PhysioNet data under a data-use agreement. Only
aggregate results are recorded here; patient-level arrays, per-hospital counts
and the `_eicu_acc` scratch are excluded by `.gitignore` and must never be
committed.
