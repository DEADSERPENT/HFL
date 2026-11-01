# PP-HFM: Patient-Level Differential Privacy in Hierarchical Federated Multimodal Learning

Research code, results and manuscripts for *Patient-Level Differential Privacy in
Hierarchical Federated Learning for Multimodal Medical IoT* (Samartha H V, Shreyas J,
Udayaprasad P K, Shreelakshmi Yadav N, Sowmya T Rao; MIT Bengaluru, MAHE). This
private repository is the study's research record: every reported number traces to a
file and the command that produced it, and inconclusive and failed outcomes are kept.

## Research question

Differentially private training protects one unit of data. In sensing that unit is a
window of signal, but a clinical deployment must protect the *patient*, who contributes
many correlated windows. PP-HFM gives a client–edge–cloud federated system a guarantee
whose unit is the patient: each client sums a patient's gradients before clipping and
calibrates noise to its own population, and every release of the hierarchy is accounted for.

The guarantee is proved for the training transcript (Theorem 1). It holds end to end only
with public encoders and standardization constants: eICU, and the VitalDB disjoint
variant.

## Manuscripts

| Folder | Content | Build |
|---|---|---|
| `PLDP/` | submission manuscript (IEEEtran, 18 pp.); copy `PLDP.pdf` | `bash PLDP/build_paper.sh`; Overleaf: `bash PLDP/make_overleaf.sh` |
| `paper/` | full-length manuscript (31 pp.) and figure generators | `bash paper/build_paper.sh` |

Both manuscripts are updated together. Compile through these scripts; the files in
`sections/` are fragments.

## Data

| | VitalDB | WEAR | eICU-CRD |
|---|---|---|---|
| Clients / individuals | 9 specialties / 5,974 | 22 participants / 22 | 187 hospitals / 132,736 |
| Modalities | 18 vital trends + 34 preoperative variables | inertial + video features | 12 vitals + 5 admission variables |
| Task | ICU admission | 18 activities | in-unit mortality |
| Privacy unit evaluated | patient | record (one participant per client) | patient |
| Access | open (CC BY 4.0) | public; redistribution unverified | credentialed (PhysioNet DUA) |

Splits are by individual. For VitalDB, four analyses use the **person-level** partition:
the privacy cost, the cost of the unit, the prior-system comparison and the audit. All
other VitalDB analyses are **case-level** and labeled so.

## Reviewed objective assessment

Scored by `SIMULATORS/scripts/check_objectives.py` from the final result files. Each
verdict follows the prespecified rule, taken from the interval, not the point estimate.
An inconclusive result is neither a pass nor evidence of equivalence.

| Objective | Target | VitalDB | WEAR | eICU |
|---|---|---|---|---|
| O1 uplink reduction (measured payload) | ≥ 50 % | 90.8 % | 96.1 % | 92.3 % |
| O1b round-latency reduction (ns-3) | > 0 % | 16.9 % | 21.7 % | 33.4 % |
| O2a training ε (total incl. conformal) | ≤ 1 | 0.900 (1.0) | 0.766 (0.966) | 0.900 (1.0) |
| O2b utility loss | ≤ 2 | −1.18 [−1.63, −0.73] AUROC | 1.97 [1.76, 2.17] acc. pp | 3.09 [1.37, 4.81] AUROC |
| O3a P95 latency (workstation CPU) | < 100 ms | 2.30 ms | 0.75 ms | 0.24 ms |
| O3b update delivery (ns-3) | > 99 % | 100.00 % | 99.94 % | 97.83 % |
| O4 energy saving (CloudSim Plus model) | ≥ 20 % | 72.3 % | 76.8 % | 79.6 % |
| **Verdict** | | **7 of 7** | **6 of 7; utility inconclusive** | **5 of 7; utility inconclusive, delivery fails** |

- **eICU utility:** the point estimate exceeds 2. End to end (pool-fitted constants) the cost is 3.91 [2.40, 5.42], a miss.
- **eICU delivery** reaches 99 % from eight edges. **WEAR utility** is a record-level accuracy loss, not comparable with the clinical AUROC costs.
- **Score files:** canonical `SIMULATORS/results/phase5/objectives_*.json`; earlier scorings kept as `*_superseded.json`.
- **Full record:** [`SIMULATORS/results/RESULTS_FINAL.md`](SIMULATORS/results/RESULTS_FINAL.md).

## Further findings, with their scope

- **Initialization, not the privatized subset** (VitalDB case-level, WEAR): from ε = ∞ to 0.5, a random initialization loses 0.19 AUROC and a pretrained one 0.004. Head-only noise changes AUROC by ≤ 0.006.
- **Cost of the unit:** at a matched budget, VitalDB AUROC changes by −0.0170 [−0.0269, −0.0071] (person-level). The cost follows A(1 − 1/k) in records per patient (VitalDB case-level). On eICU the shape transfers at about one ninth of the forecast magnitude, mostly unresolved at three seeds.
- **Membership inference (VitalDB, person-level):** under offline LiRA, record-level training remains above its floor (0.576 vs 0.511) and patient-level does not (0.503 vs 0.508), a difference of +0.073 [0.054, 0.092]. Two of four attacks resolve it, and the positive control is resolved by a different attack. The audit does not establish absence of leakage.
- **Prior systems** (re-implemented HED-FL, FL2DP): PP-HFM uploads 2.2–4.0× less; on VitalDB, under offline LiRA, it leaks less than both (margin −0.005 vs +0.026 and +0.049); on eICU, non-private HED-FL is more accurate (AUROC 0.825 vs 0.794).
- **Fusion is conditional:** +0.037 AUROC on VitalDB; on eICU +0.002 on the natural streams and +0.029 (p = 0.019) only when the streams are balanced; no headroom on WEAR.
- **Hierarchy:** removing the edge tier changes accuracy by about −0.005. This is not a benefit of hierarchy, because the flat arm also changes the aggregation schedule.

## Repository layout

```
├── PLDP/, paper/            manuscripts (paper/figures/: one generator per figure)
├── docs/, document/         notes, plans, pre-registrations (document/01_planning/)
├── report/                  plain-language project report
└── SIMULATORS/              codebase: data/loaders, model, engineering, scripts, tests,
                             ns3, cloudsim-plus, config, results (RESULTS_FINAL.md = index)
```

The release staging copy (`pp-hfm-release/`) and its review folder are git-ignored.

## Reproducing

```bash
source hfl_env/bin/activate && cd SIMULATORS
python tests/test_regression.py --dataset vitaldb_person      # 17 regression guards
bash scripts/run_dpfix_stageF.sh                              # privacy cost, five paired seeds
bash scripts/run_person_vitaldb.sh                            # person-level cost, unit, baselines, LiRA
bash scripts/run_lit_baselines.sh                             # HED-FL and FL2DP
python scripts/check_objectives.py --dataset vitaldb --headline vitaldb_person
```

Drivers are resumable and refuse to run on missing inputs. Run one GPU job at a time,
using `scripts/run_detached.sh`. Every run writes `run_metadata_*.json` with its command,
commit and package versions. `RESULTS_FINAL.md` §9 maps each result to its driver.

Environment: Python 3.11, PyTorch 2.5.1 (CUDA 12.1), Opacus 1.5.4, ns-3 3.46.1
(`scripts/install_ns3.sh`), CloudSim Plus 8.5.6 (`scripts/install_cloudsim.sh`), ONNX
Runtime 1.25.

## Data policy and integrity

- **eICU:** used under the PhysioNet DUA. Only code and aggregate results are kept. Patient-level arrays, per-hospital counts, partitions and eICU-trained models are git-ignored and must never be committed.
- **Redistribution:** public availability is not permission to redistribute. Check each dataset's terms first.
- **Pre-registrations:** amendments are dated in the text. The eICU forecast was committed on 2026-09-05, before its corpus was built; the fusion and clipping ones first appear in git on 2026-10-21.
- **Measurement types:** network is simulated (ns-3), energy is modeled (CloudSim Plus), and latency was timed on a workstation CPU. Nothing was measured on edge hardware.

## Limitations

1. eICU utility is inconclusive against the two-point target and missed end to end.
2. VitalDB and WEAR headline runs use oracle encoders (utilities are upper bounds); disjoint encoders cost 1.6 AUROC on VitalDB.
3. Scaling grids and the recipe sweep use three seeds, fixed in advance.
4. WEAR's guarantee is record-level, and private conformal prediction did not attain coverage.
5. The membership-inference audit covers VitalDB only, at a 1 % false-positive rate.
