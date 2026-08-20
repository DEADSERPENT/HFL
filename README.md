# PP-HFM — Patient-Private Hierarchical Federated Multimodal Learning

Privacy-preserving federated learning for multimodal clinical IoT, with
differential privacy at the **patient** level rather than the record level.

**Samartha H V** · M.Tech CSE, MIT Bengaluru (MAHE) · Regd. 251580130019
Guide: Dr. Shreyas J · Industry: Mr. Tejas J (Capgemini)
Target venue: IEEE Trans. Industrial Informatics / IEEE IoT Journal

---

## What this is

Hospital data cannot be centralised, and model updates leak. This system trains
across sites without moving raw records, fuses two genuinely co-recorded
modalities per patient, and bounds what the trained model reveals about any
individual — validated end to end across network, compute, energy and deployed
inference.

The distinguishing claim: a sample here is a 10-minute window, and each patient
contributes about eight of them. A textbook ε answers *"was this window in the
training set?"*; the clinical guarantee must answer *"was this **patient** in
the training set?"* Those differ, and the naive conversion is unusable.

---

## Repository layout

```
├── README.md                  this file
├── docs/                      research narrative, roadmap, runbook
│   ├── Research.md            the work explained (plain + technical)
│   ├── roadmap.md             what is done, what is next
│   └── RUNBOOK.md             operational procedures
├── figures/                   publication figures + their generator
├── document/                  formal project documents
│   ├── DOCUMENT PDF/          problem statement, literature
│   ├── PHASE REPORT/          Phases 1-6
│   ├── DATASET & MODEL GUIDE/ data, model, simulator integration
│   └── OVERALL PROJECT OUTPUT/ status, IP & novelty register
└── SIMULATORS/                the codebase
    ├── data/loaders/          dataset registry + preprocessors
    ├── model/
    │   ├── architecture/      encoders, fusion head
    │   ├── privacy/           DP-SGD, patient-level DP, accounting
    │   ├── training/          trainer, baselines, epsilon sweep
    │   ├── deploy/            ONNX export, inference benchmark
    │   └── utils/             compression, conformal prediction
    ├── engineering/           preflight, run context, monitoring
    ├── scripts/               pipeline driver, analysis, simulators
    ├── tests/                 dataset audit, regression, traceability
    ├── ns3/                   NS-3 network simulation
    ├── cloudsim-plus/         CloudSim Plus energy simulation
    ├── config/                shared configuration
    ├── deploy/                exported ONNX artifacts
    └── results/               measured outputs
```

---

## Quick start

```bash
cd SIMULATORS && source ../hfl_env/bin/activate

python scripts/run_pipeline.py --dataset vitaldb   # full study, 16 stages
python tests/traceability.py --dataset vitaldb     # what exists
python scripts/check_objectives.py --dataset vitaldb   # O1-O4 vs targets
```

The pipeline is resumable: completed stages are skipped, and a stage whose
inputs are missing refuses to run rather than producing a number from stale
data. Per-stage logs and a manifest recording the exact command behind every
result land in `results/pipeline/<dataset>/`.

---

## Datasets

| | VitalDB (primary) | WEAR (fast iteration) |
|---|---|---|
| Domain | clinical IoMT | wearable IoT |
| Windows | 48,712 from 6,257 surgeries | 38,578 |
| Clients | 9 (surgical specialty) | 22 (subject) |
| Modality A | (18, 300) intraop trends + masks | (12, 100) inertial |
| Modality B | (34,) preoperative clinical | (2048,) egocentric video |
| Pairing | same patient, same second | hardware-synchronised |
| Split | by case | temporal within (subject, activity) |

Both are open published corpora. No private patient data is used — the privacy
mechanism is *demonstrated* on open research data, which is how DP methods are
validated.

---

## Results

**Objectives** — vitaldb 6/6 PASS · wear 5 PASS + 1 INCONCLUSIVE, 0 FAIL

| | Target | vitaldb | wear |
|---|---|---|---|
| O1 uplink reduction | ≥ 50 % | 90.8 % | 96.1 % |
| O2a privacy budget | ε ≤ 1 | 0.963 | 0.989 |
| O2b accuracy loss | ≤ 2 pp | −0.92 pp | +1.97 pp † |
| O3a P95 latency | < 100 ms | 2.99 ms | 1.22 ms |
| O3b update reliability | > 99 % | 99.27 % | 99.05 % |
| O4 energy saving | ≥ 20 % | 72.3 % | 76.8 % |

† INCONCLUSIVE: pre-registered n=15, 95 % CI [+1.760, +2.173] spans the target.

**Head-only DP** — the gap over full-model DP widens as the budget tightens and
nearly vanishes without privacy, which is the pre-registered signature of a
noise-tolerance effect rather than a parameter-count effect:

| ε | 0.5 | 1 | 2 | 4 | 8 | ∞ |
|---|---|---|---|---|---|---|
| vitaldb | +0.131 | +0.113 | +0.097 | +0.078 | +0.060 | +0.009 |
| wear | +0.395 | +0.309 | +0.208 | +0.131 | +0.088 | +0.002 |

**Multimodal fusion** — beats *both* single modalities, not just the weaker one:
+0.0411 AUROC / +0.1062 AUPRC over the best unimodal arm (14× seed sd).

---

## Verification

```bash
python tests/verify_datasets.py --dataset vitaldb   # adversarial data audit
python tests/test_regression.py --dataset vitaldb   # 8 regression guards
python tests/traceability.py   --dataset vitaldb    # deliverables vs code
```

Every reported ε is checked against its budget. Every objective reports
`NOT MEASURED` rather than guessing when its artifact is absent, and
`INCONCLUSIVE` when a confidence interval spans the threshold.

---

## Known limitations

1. Encoder pretraining uses a disjoint in-corpus pool; the strongest claim needs
   an external public corpus.
2. WEAR is at ceiling — it cannot evidence fusion, and its O2b is inconclusive.
3. Most contrasts are single-seed; only O2b and the patient-level comparison
   carry intervals.
4. ASWA is implemented but unablated, so it is not claimed.
5. No feature-level explainability — the system outputs a calibrated conformal
   prediction set, not attributions.

PHANTOM-FL is **not** part of this system. Its components were either unbuilt,
measured negative, or architecturally incompatible with head-only DP. See
`document/OVERALL PROJECT OUTPUT/01_PHANTOM_FL_Novel_Model.txt`.

---

## Environment

Python 3.11 · PyTorch + Opacus · NS-3 v3.46.1 (cppyy bindings) ·
CloudSim Plus v8.5.6 · ONNX Runtime

```bash
bash SIMULATORS/scripts/install_ns3.sh
bash SIMULATORS/scripts/install_cloudsim.sh
pip install cppyy      # required by NS-3 >= 3.36 Python bindings
```

NS-3 and CloudSim Plus are third-party checkouts fetched by those scripts.
