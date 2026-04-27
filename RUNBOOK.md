# HFL Project Runbook
**Hierarchical Federated Learning for Privacy-Aware, Low-Latency Multimodal Healthcare IoT**
Student: Samartha H V | MIT Bengaluru | Regd. 251580130019
Guide: Dr. Shreyas J | Industry: Mr. Tejas J (Capgemini)

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [One-Time Setup](#2-one-time-setup)
3. [Project Structure](#3-project-structure)
4. [Every Session — Start Here](#4-every-session--start-here)
5. [Phase 5 Pipeline — Full Run](#5-phase-5-pipeline--full-run)
   - [QUICK: Run All Phase 5 Steps (One Command)](#quick-run-all-phase-5-steps-one-command)
6. [Running Individual Components](#6-running-individual-components)
7. [Expected Outputs & Results](#7-expected-outputs--results)
8. [Verify GPU is Working](#8-verify-gpu-is-working)
9. [Troubleshooting](#9-troubleshooting)
10. [Phase Status Summary](#10-phase-status-summary)

---

## 1. System Requirements

| Requirement | Value |
|---|---|
| OS | Ubuntu 20.04 / 22.04 / 24.04 LTS (any) |
| Python | 3.11 (exact) |
| GPU | NVIDIA GPU with CUDA 11.8+ (primary) — CPU fallback works but is slow |
| VRAM | ≥ 8 GB recommended (RTX A2000 12GB confirmed working) |
| RAM | ≥ 16 GB |
| Disk | ≥ 20 GB free (PTB-XL subset ~500 MB, Kermany CXR ~1.15 GB, models + results ~5 GB) |
| Internet | Required for dataset download (PTB-XL auto via wfdb, Kermany CXR via Kaggle) |

Check your GPU before anything:

```bash
nvidia-smi
```

---

## 2. One-Time Setup

Do this **once** on any new machine. Skip if already done.

### 2.1 Install Python 3.11

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

Verify:

```bash
python3.11 --version   # must print Python 3.11.x
```

### 2.2 Clone or copy the project

```bash
# If using git:
git clone <your-repo-url> ~/HFL
cd ~/HFL

# If copying from USB/drive:
cp -r /path/to/HFL ~/HFL
cd ~/HFL
```

### 2.3 Create virtual environment

```bash
cd ~/HFL
python3.11 -m venv hfl_env
source hfl_env/bin/activate
pip install --upgrade pip setuptools wheel
```

### 2.4 Install PyTorch (check your CUDA version first)

```bash
# Check CUDA version:
nvidia-smi | grep "CUDA Version"

# CUDA 11.8 (most common on older lab GPUs):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1 (newer GPUs):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# CUDA 12.4:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### 2.5 Install all project dependencies

```bash
# Core ML
pip install opacus
pip install wfdb
pip install scipy scikit-learn
pip install Pillow pandas numpy tqdm matplotlib

# Mamba SSM — IP-1 FedMamba-HC (requires CUDA GPU)
pip install mamba-ssm causal-conv1d

# ONNX edge deployment
pip install onnx onnxruntime-gpu

# Utilities
pip install seaborn
```

> **Note:** `mamba-ssm` has prebuilt wheels only for Python 3.11 + CUDA. On CPU-only machines it will fail to import — the code automatically skips it and logs a warning.

### 2.6 Verify everything installed

```bash
cd ~/HFL
source hfl_env/bin/activate

python -c "
import torch, torchvision, opacus, wfdb, scipy, sklearn
import PIL, pandas, numpy, onnx, onnxruntime
print('torch      :', torch.__version__)
print('CUDA avail :', torch.cuda.is_available())
print('GPU name   :', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')
print('opacus     :', opacus.__version__)
print('onnxruntime:', onnxruntime.__version__)
try:
    from mamba_ssm import Mamba
    print('mamba-ssm  : OK')
except ImportError as e:
    print('mamba-ssm  : NOT available (CPU machine) -', e)
"
```

### 2.7 Run device utility self-test

```bash
cd ~/HFL/SIMULATORS
python scripts/device_utils.py
```

Expected output (GPU machine):
```
[Device] GPU  : NVIDIA RTX A2000 12GB
[Device] VRAM : 12.0 GB  |  SMs: 26  |  CUDA 11.8  |  cuDNN 8700
[GPU Opt] cuDNN benchmark=True | TF32=True | memory_fraction=0.95
```

---

## 3. Project Structure

```
~/HFL/
├── RUNBOOK.md                          ← this file
├── hfl_env/                            ← Python venv (do not commit)
│
├── PHASE REPORT/
│   ├── Phase 1.txt                     ← System design & topology
│   ├── Phase 2.txt                     ← Algorithm design
│   ├── Phase 3.txt                     ← NS-3 + CloudSim setup
│   ├── Phase 4.txt                     ← Simulation validation (PASS)
│   ├── Phase 5.txt                     ← Healthcare dataset + model (ACTIVE)
│   └── Phase 6.txt                     ← PHANTOM-FL (next)
│
├── DATASET & MODEL GUIDE/
│   ├── 01_Datasets.txt                 ← PTB-XL + Kermany CXR details
│   ├── 02_Model_Design.txt             ← HFL-MM-HC + PHANTOM-FL architecture
│   └── 03_NS3_CloudSim_Integration.txt
│
└── SIMULATORS/
    ├── config/
    │   └── hfl_config.json             ← Shared topology + QoS config
    │
    ├── data/
    │   ├── raw/                        ← Downloaded datasets (git-ignored)
    │   │   ├── ptb-xl/                 ← Auto-downloaded by download_datasets.py
    │   │   └── chest-xray-pneumonia/   ← Downloaded via Kaggle (Kermany CXR)
    │   ├── processed/
    │   │   ├── healthcare/             ← Preprocessed tensors (.npy)
    │   │   └── partitions/             ← Non-IID device splits (.npy)
    │   └── loaders/
    │       ├── download_datasets.py    ← Step 1: download PTB-XL + Kermany CXR
    │       ├── preprocess_healthcare.py ← Step 2: ECG + CXR preprocessing
    │       └── partition_noniid.py     ← Step 3: Dirichlet α=0.5 partition
    │
    ├── model/
    │   ├── device_utils.py             ← GPU/CPU auto-select + optimization
    │   ├── fedmamba_hc.py              ← IP-1: Mamba SSM ECG encoder
    │   ├── fedconform_hc.py            ← IP-9: Federated conformal prediction
    │   ├── clinical_cmga_design.py     ← IP-3: Phase 6 design spec
    │   ├── hfl_mm_model.py             ← Full HFL-MM-HC model
    │   ├── dp_engine.py                ← DP-SGD via Opacus
    │   ├── compression.py              ← Top-k (20%) + 8-bit quantization
    │   ├── baselines.py                ← B0–B5 baseline suite
    │   ├── hfl_trainer.py              ← Two-tier FL training engine
    │   ├── epsilon_sweep.py            ← ε ∈ {0.1,0.5,1.0,2.0,5.0,∞} sweep
    │   ├── onnx_exporter.py            ← ONNX FP32 → INT8 export
    │   └── inference_bench.py          ← P50/P95/P99 latency benchmark
    │
    ├── scripts/
    │   ├── device_utils.py             ← Source of truth for device_utils
    │   ├── ns3_phase5_integration.py   ← NS-3 network metrics (Phase 5)
    │   ├── collect_phase5_results.py   ← Aggregate all → phase5_results.csv
    │   ├── ns3_hfl_smoketest.py        ← Phase 3/4 NS-3 smoke test
    │   ├── install_ns3.sh              ← NS-3 one-time installer
    │   ├── install_cloudsim.sh         ← CloudSim one-time installer
    │   └── verify_setup.sh             ← Environment verification
    │
    ├── results/
    │   ├── ns3/ns3_results.csv         ← Phase 4 NS-3 results (DONE)
    │   ├── cloudsim/cloudsim_results.csv ← Phase 4 CloudSim results (DONE)
    │   └── phase5/
    │       ├── phase5_results.csv      ← D5.13 final aggregated results
    │       ├── baseline_b0.csv         ← Centralized baseline
    │       ├── baseline_b1.csv … b5.csv
    │       ├── hfl_mm_hc_results.csv   ← Per-round FL training log
    │       ├── epsilon_sweep/          ← ε vs AUC CSVs
    │       ├── convergence_curves/     ← Per-round accuracy logs
    │       └── inference_latency/
    │           └── bench_results.csv   ← P50/P95/P99 latency
    │
    ├── checkpoints/
    │   └── best_model_hc.pt            ← Best FL checkpoint (saved by trainer)
    │
    └── onnx/
        ├── hfl_mm_hc.onnx              ← FP32 ONNX model
        └── hfl_mm_hc_int8.onnx         ← INT8 quantized (edge deployment)
```

---

## 4. Every Session — Start Here

Every time you open a terminal, run these two lines before anything else:

```bash
cd ~/HFL
source hfl_env/bin/activate
```

Your prompt will show `(hfl_env)` — that means the environment is active.

All commands below assume you are in `~/HFL/SIMULATORS/` unless stated otherwise:

```bash
cd ~/HFL/SIMULATORS
```

---

## 5. Phase 5 Pipeline — Full Run

Run these steps **in order**. Each step's output is required by the next.

---

### QUICK: Run All Phase 5 Steps (One Command)

After datasets are downloaded and preprocessed (Steps 1–3), run the entire ML pipeline in one shot:

```bash
cd ~/HFL
source hfl_env/bin/activate
cd SIMULATORS

# Full pipeline: Steps 1-3 (data) + Steps 4-11 (training, evaluation, export)
python data/loaders/download_datasets.py && \
python data/loaders/preprocess_healthcare.py \
    --ptbxl_dir  data/raw/ptb-xl \
    --cxr_dir    data/raw/chest-xray-pneumonia \
    --output_dir data/processed/healthcare && \
python data/loaders/partition_noniid.py \
    --domain healthcare --alpha 0.5 --n_devices 20 --n_edges 3 \
    --input_dir  data/processed/healthcare \
    --output_dir data/processed/partitions && \
python run_phase5.py 2>&1 | tee results/phase5/run_log.txt
```

Or if data is already prepared (Steps 1–3 already done), just run the ML steps:

```bash
cd ~/HFL/SIMULATORS
python run_phase5.py 2>&1 | tee results/phase5/run_log.txt
```

`run_phase5.py` defaults to all steps (4 through 11): B0 baseline → baselines B1–B5 → HFL-MM-HC training → ε sweep → ONNX export → latency benchmark → collect results.

Monitor training in real-time:

```bash
tail -f results/phase5/run_log.txt
```

**Convenience script** (activates env + runs all ML steps):

```bash
bash ~/HFL/run_phase5.sh
```

---

---

### Step 1 — Download Datasets

**Dataset summary:**

| Modality | Dataset | Size | Download |
|---|---|---|---|
| ECG (Signal) | PTB-XL 12-lead | ~500 MB (stratified 5,500 records) | Auto via `wfdb` |
| CXR (Image) | Kermany Chest X-Ray | ~1.15 GB (5,863 JPEGs) | Kaggle API key required |
| Tabular | PTB-XL metadata CSV | included with PTB-XL | Auto |

#### 1a — Install prerequisites (first time only)

```bash
pip install wfdb opendatasets pandas
```

#### 1b — Get a Kaggle API key (first time only, for Chest X-Ray)

1. Log in at [kaggle.com](https://www.kaggle.com) → **Profile → Account → Create New API Token**
2. This downloads `kaggle.json`. When `opendatasets` prompts you, enter the **username** and **key** from that file.

#### 1c — Run the downloader

```bash
cd ~/HFL/SIMULATORS
python data/loaders/download_datasets.py
```

When prompted enter your Kaggle username and API key (from `kaggle.json`).

**What it does:**
- Downloads a stratified 5,500-record subset of PTB-XL from PhysioNet via `wfdb` (~500 MB, ~25% of full dataset)
- Downloads Kermany Chest X-Ray from Kaggle via `opendatasets` (~1.15 GB)

**Skip flags (if one dataset is already downloaded):**

```bash
# PTB-XL already present, only download Chest X-Ray:
python data/loaders/download_datasets.py --skip_ptbxl

# Chest X-Ray already present, only download PTB-XL:
python data/loaders/download_datasets.py --skip_cxr

# Just verify what's already downloaded:
python data/loaders/download_datasets.py --verify_only
```

**Alternative: Kaggle CLI (if opendatasets fails)**

```bash
pip install kaggle
mkdir -p ~/.kaggle
cp /path/to/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

# Download and unzip directly:
kaggle datasets download -d paultimothymooney/chest-xray-pneumonia \
      --unzip -p data/raw/
```

**Expected output:**
```
Step 1/3 — Downloading PTB-XL metadata CSVs...
  Metadata downloaded.
Step 2/3 — Selecting 5,500 records (stratified)...
  Stratified subset: 5,500 records (~1100 per class × 5 classes)
Step 3/3 — Downloading 11,000 record files (~440 MB estimated)...
[OK] PTB-XL selective download complete. 5,500 records downloaded
Downloading Kermany Chest X-Ray dataset from Kaggle...
Please provide your Kaggle credentials.
Username: <your-kaggle-username>
Key: <your-api-key>
[OK] Chest X-Ray complete: 1341 NORMAL + 3875 PNEUMONIA (train)

[OK] PTB-XL       : selective download complete → data/raw/ptb-xl
[OK] PTB-XL meta  : scp_statements.csv present (tabular modality)
[OK] Chest X-Ray  : 1341 NORMAL + 3875 PNEUMONIA images → data/raw/chest-xray-pneumonia
```

---

### Step 2 — Preprocess Healthcare Data

```bash
python data/loaders/preprocess_healthcare.py \
    --ptbxl_dir  data/raw/ptb-xl \
    --cxr_dir    data/raw/chest-xray-pneumonia \
    --output_dir data/processed/healthcare
```

**What it does:**
- ECG: loads at 100 Hz, bandpass 0.5–40 Hz, per-lead z-score → `[12, 1000]`
- CXR: resize 224×224, ImageNet normalization → `[3, 224, 224]`
- Pairs ECG + CXR records (70% direct patient match / 30% within-class synthetic)
- Saves `.npy` tensors + label files

**Runtime:** ~15–30 min depending on disk speed

**Expected output files:**
```
data/processed/healthcare/ecg/ecg_signals.npy    (21837, 12, 1000)
data/processed/healthcare/ecg/ecg_labels.npy     (21837,)
data/processed/healthcare/cxr/cxr_images.npy     (N, 3, 224, 224)
data/processed/healthcare/cxr/cxr_primary_labels.npy
data/processed/healthcare/pairs.json
```

---

### Step 3 — Non-IID Partition

```bash
python data/loaders/partition_noniid.py \
    --domain healthcare \
    --alpha 0.5 \
    --n_devices 20 \
    --n_edges 3 \
    --input_dir  data/processed/healthcare \
    --output_dir data/processed/partitions
```

**What it does:**
- Dirichlet(α=0.5) split across 20 IoT devices → realistic non-IID patient cohorts
- 70% train / 15% val / 15% test per device
- Assigns devices to 3 edge clusters (6–7 devices each)

**Expected output:**
```
data/processed/partitions/device_00_train.npy  …  device_19_test.npy
data/processed/partitions/partition_meta.json
[Partition] Avg TVD from uniform: 0.42  (0=IID, 1=extreme non-IID)
```

---

### Step 4 — Centralized Baseline B0

```bash
python model/baselines.py \
    --mode centralized \
    --data_dir data/processed/healthcare \
    --output results/phase5/baseline_b0.csv
```

**What it does:** Upper bound — trains on all 20 devices' data pooled, no FL, no DP

**Expected result:** Macro-AUC ~0.87, Accuracy ~85%

---

### Step 5 — Baselines B1 through B5

Run all 5 in sequence (or in separate terminals for speed):

```bash
# B1: Local Only (lower bound — no federation)
python model/baselines.py \
    --mode local \
    --partition_dir data/processed/partitions \
    --data_dir data/processed/healthcare \
    --output results/phase5/baseline_b1.csv

# B2: Standard FedAvg (McMahan 2017)
python model/baselines.py \
    --mode fedavg \
    --partition_dir data/processed/partitions \
    --data_dir data/processed/healthcare \
    --output results/phase5/baseline_b2.csv

# B3: FedProx (Li 2020) — proximal regularization
python model/baselines.py \
    --mode fedprox \
    --mu 0.01 \
    --partition_dir data/processed/partitions \
    --data_dir data/processed/healthcare \
    --output results/phase5/baseline_b3.csv

# B4: DP-FedAvg (Geyer 2017) — flat DP, no hierarchy
python model/baselines.py \
    --mode dp_fedavg \
    --epsilon 1.0 \
    --partition_dir data/processed/partitions \
    --data_dir data/processed/healthcare \
    --output results/phase5/baseline_b4.csv

# B5: MOON (Li 2021) — model-contrastive FL
python model/baselines.py \
    --mode moon \
    --mu 5.0 \
    --partition_dir data/processed/partitions \
    --data_dir data/processed/healthcare \
    --output results/phase5/baseline_b5.csv
```

**Expected results summary:**

| Baseline | Macro-AUC | Accuracy | Privacy |
|---|---|---|---|
| B0 Centralized | ~0.87 | ~85% | none |
| B1 Local Only | ~0.73 | ~71% | none |
| B2 FedAvg | ~0.84 | ~82% | none |
| B3 FedProx | ~0.845 | ~82.5% | none |
| B4 DP-FedAvg | ~0.82 | ~80% | ε=1.0 |
| B5 MOON | ~0.835 | ~81.5% | none |

---

### Step 6 — HFL-MM-HC Training (P1 — Our Model)

```bash
python model/hfl_trainer.py \
    --rounds 20 \
    --tau_e 5 \
    --n_devices 20 \
    --n_edges 3 \
    --epsilon 1.0 \
    --delta 1e-5 \
    --noise_mult 1.1 \
    --max_grad_norm 1.0 \
    --sparsity 0.2 \
    --quant_bits 8 \
    --batch_size 32 \
    --n_classes 5 \
    --partition_dir data/processed/partitions \
    --data_dir data/processed/healthcare \
    --save_checkpoint checkpoints/best_model_hc.pt \
    --output results/phase5/hfl_mm_hc_results.csv
```

**What it does:**
- Two-tier FedAvg: 20 devices → 3 edges → 1 cloud
- DP-SGD via Opacus (ε=1.0, σ=1.1, C=1.0)
- Gradient compression: Top-20% sparsification + INT8 → 20× compression
- FedConform-HC conformal calibration every edge round
- Saves best checkpoint by macro-AUC

**Runtime:** ~2–4 hours on GPU (RTX A2000), ~12–18 hours on CPU

**Per-round log columns:**
```
round, edge_round, val_accuracy, macro_auc, epsilon_spent,
uplink_bytes, round_time_ms, q_global, avg_set_size
```

**Expected final result:** Macro-AUC ~0.85, Accuracy ~83%, ε≤1.0

**Monitor training:**
```bash
tail -f results/phase5/hfl_mm_hc_results.csv
```

---

### Step 7 — Privacy-Accuracy ε Sweep

```bash
python model/epsilon_sweep.py \
    --epsilons 0.1 0.5 1.0 2.0 5.0 inf \
    --data_dir data/processed/healthcare \
    --rounds 10 \
    --output_dir results/phase5/epsilon_sweep/
```

**What it does:** Trains HFL-MM-HC at 6 privacy budgets and records accuracy/AUC at each

**Expected output files:**
```
results/phase5/epsilon_sweep/eps_0.1.csv   → AUC ~0.74
results/phase5/epsilon_sweep/eps_0.5.csv   → AUC ~0.80
results/phase5/epsilon_sweep/eps_1.0.csv   → AUC ~0.83  ← QoS target
results/phase5/epsilon_sweep/eps_2.0.csv   → AUC ~0.85
results/phase5/epsilon_sweep/eps_5.0.csv   → AUC ~0.86
results/phase5/epsilon_sweep/eps_inf.csv   → AUC ~0.87
```

**QoS check:** Accuracy loss at ε=1.0 vs B0 must be ≤ 2%

---

### Step 8 — ONNX Export + INT8 Quantization

```bash
python model/onnx_exporter.py \
    --checkpoint checkpoints/best_model_hc.pt \
    --output_fp32 onnx/hfl_mm_hc.onnx \
    --output_int8 onnx/hfl_mm_hc_int8.onnx \
    --n_classes 5
```

**What it does:**
- Exports trained model to ONNX opset 17 (FP32)
- Graph optimization via ONNXRuntime
- INT8 dynamic quantization (MatMul + Gemm)
- Verifies FP32 vs INT8 output agreement

**Expected output:**
```
[ONNX FP32] Exported → onnx/hfl_mm_hc.onnx  (12.80 MB)
[ONNX OPT]  Graph-optimized → onnx/hfl_mm_hc_opt.onnx
[ONNX INT8] Quantized    → onnx/hfl_mm_hc_int8.onnx  (3.20 MB)
[PASS] INT8 model size 3.20 MB ≤ 4 MB target.
[VERIFY] FP32 vs INT8 max logit diff: 0.0312
```

---

### Step 9 — Inference Latency Benchmark

```bash
python model/inference_bench.py \
    --model onnx/hfl_mm_hc_int8.onnx \
    --n_runs 1000 \
    --warmup 100 \
    --output results/phase5/inference_latency/bench_results.csv
```

**What it does:** Measures end-to-end P50/P95/P99 latency across 1000 runs

**Expected output:**
```
Component            Mean      P50      P95      P99  (ms)
preproc_ms          14.20    13.80    18.40    21.10
inference_ms        38.50    37.20    47.80    52.30
conformal_ms         0.42     0.40     0.61     0.74
post_ms              0.18     0.17     0.26     0.31
total_ms            53.30    51.60    67.07    74.45

QoS target (P95 < 100ms): 67.07ms → [PASS]
```

---

### Step 10 — NS-3 Network Integration

```bash
python scripts/ns3_phase5_integration.py \
    --hfl_results results/phase5/hfl_mm_hc_results.csv \
    --n_rounds 20 \
    --output results/ns3/ns3_phase5_results.csv
```

**What it does:**
- Reads actual uplink bytes from HFL training log
- Recomputes NS-3 network metrics (comm reduction, energy saving, reliability)
- Validates Phase 4 QoS targets still hold with Phase 5 payload sizes

**Expected output:**
```
[✓] O1 Comm reduction ≥ 50%:   ~95%
[✓] O4 Energy saving ≥ 20%:    ~95%
[✓] Update reliability > 99%:  ~99.05%
[PASS] All Phase 4 QoS targets maintained in Phase 5.
```

---

### Step 11 — Collect All Results

```bash
python scripts/collect_phase5_results.py \
    --results_dir results/phase5 \
    --output results/phase5/phase5_results.csv
```

**What it does:** Reads all CSVs from Steps 4–10 and writes one consolidated result file

**Expected output:**
```
[OK] B0 Centralized: acc=0.850 auc=0.870
[OK] B1 Local Only:  acc=0.710 auc=0.730
...
[OK] HFL-MM-HC (P1): acc=0.830 auc=0.850
[OK] ε sweep: 6 epsilon points loaded
[OK] Latency: P95=67.07 ms
[OK] NS-3: comm_reduction=95%

QoS SUMMARY:
  [✓] Comm reduction ≥ 50%:   95%   → PASS
  [✓] Energy saving ≥ 20%:    95%   → PASS
  [✓] Update reliability > 99%: 99.05% → PASS
  [✓] Inference P95 < 100ms:  67ms  → PASS
  [✓] Accuracy loss ≤ 2%:     1.5%  → PASS

[PASS] All Phase 5 QoS targets met.
```

---

## 6. Running Individual Components

### Run a single baseline only

```bash
cd ~/HFL/SIMULATORS
source ~/HFL/hfl_env/bin/activate

python model/baselines.py --mode fedavg \
    --partition_dir data/processed/partitions \
    --data_dir data/processed/healthcare \
    --output results/phase5/baseline_b2.csv
```

### Test FedMamba-HC encoder alone

```bash
cd ~/HFL/SIMULATORS
python model/fedmamba_hc.py
# Output: FedMamba-HC output: torch.Size([4, 256])  Parameters: 1,704,960
```

### Test the full HFL-MM-HC model forward pass

```bash
cd ~/HFL/SIMULATORS
python model/hfl_mm_model.py
# Output: HFL-MM-HC output: torch.Size([4, 5])  Total params: ~3.2M
```

### Test device detection

```bash
cd ~/HFL/SIMULATORS
python scripts/device_utils.py
```

### Test gradient compression

```bash
cd ~/HFL/SIMULATORS
python model/compression.py
```

### View conformal prediction design

```bash
cd ~/HFL/SIMULATORS
python model/fedconform_hc.py
```

### View ClinicalCMGA design spec (Phase 6 preview)

```bash
cd ~/HFL/SIMULATORS
python model/clinical_cmga_design.py
```

---

## 7. Expected Outputs & Results

### All 5 QoS Targets

| QoS Objective | Target | Phase 4 | Phase 5 | Status |
|---|---|---|---|---|
| Communication reduction | ≥ 50% | 76.4% | ~95% | PASS |
| Energy saving | ≥ 20% | 74.9% | ~95% | PASS |
| Update reliability | > 99% | 99.05% | ~99.05% | PASS |
| Inference latency (P95) | < 100 ms | — | ~67 ms | PASS |
| Accuracy loss at ε=1 | ≤ 2% | — | ~1.5% | PASS |

### Phase 5 Model Comparison

| System | Macro-AUC | Accuracy | ε | Notes |
|---|---|---|---|---|
| B0 Centralized | ~0.870 | ~85% | ∞ | Upper bound |
| B1 Local Only | ~0.730 | ~71% | ∞ | Lower bound |
| B2 FedAvg | ~0.840 | ~82% | ∞ | Standard FL |
| B3 FedProx | ~0.845 | ~82.5% | ∞ | Non-IID aware |
| B4 DP-FedAvg | ~0.820 | ~80% | 1.0 | Flat DP-FL |
| B5 MOON | ~0.835 | ~81.5% | ∞ | Contrastive FL |
| **P1 HFL-MM-HC (Ours)** | **~0.850** | **~83%** | **1.0** | **Our model** |

### Key result files

| File | Contents |
|---|---|
| `results/phase5/phase5_results.csv` | All metrics consolidated |
| `results/phase5/hfl_mm_hc_results.csv` | Per-round FL training log |
| `results/phase5/epsilon_sweep/*.csv` | Privacy-accuracy trade-off |
| `results/phase5/inference_latency/bench_results.csv` | Latency P50/P95/P99 |
| `results/ns3/ns3_phase5_results.csv` | Network QoS metrics |
| `checkpoints/best_model_hc.pt` | Best trained model |
| `onnx/hfl_mm_hc_int8.onnx` | Edge-deployed model |

---

## 8. Verify GPU is Working

Run this at any time to confirm the GPU is being used:

```bash
cd ~/HFL/SIMULATORS
python -c "
from device_utils import get_device, optimize_gpu, gpu_memory_info
import torch
device = get_device()
optimize_gpu()
# Move a dummy tensor and model to verify
x = torch.randn(4, 12, 1000).to(device)
print('Tensor device:', x.device)
gpu_memory_info()
"
```

**GPU output:**
```
[Device] GPU  : NVIDIA RTX A2000 12GB
[GPU Opt] cuDNN benchmark=True | TF32=True | memory_fraction=0.95
Tensor device: cuda:0
[GPU Mem] Allocated 0.00 GB | Reserved 0.02 GB | Free 11.98 GB / 12.00 GB total
```

**CPU output (no GPU):**
```
[Device] CPU fallback — 16 cores
Tensor device: cpu
```

Watch GPU usage during training:

```bash
watch -n 1 nvidia-smi
```

---

## 9. Troubleshooting

### `mamba-ssm` import error

```
ImportError: mamba-ssm not installed
```

Fix:
```bash
pip install mamba-ssm causal-conv1d
# If it fails (no CUDA or wheel not found):
pip install mamba-ssm causal-conv1d --no-build-isolation
```

If still failing (CPU-only machine): the project runs on CPU with a warning — mamba blocks fall back gracefully.

---

### `opacus` error during training

```
RuntimeError: [HFL-Trainer] DP-SGD training failed
```

Fix — ensure no BatchNorm in model:
```bash
python -c "
from opacus.validators import ModuleValidator
from model.hfl_mm_model import build_hfl_mm_hc
model = build_hfl_mm_hc()
errors = ModuleValidator.validate(model, strict=False)
print(errors)
"
```

If errors shown: all BatchNorm must be GroupNorm. The project code already uses GroupNorm — this error means a PyTorch/Opacus version mismatch. Fix:
```bash
pip install opacus --upgrade
```

---

### ONNX export fails

```
torch.onnx.errors.UnsupportedOperatorError
```

Fix:
```bash
pip install onnx --upgrade
pip install onnxruntime-gpu --upgrade
```

---

### CUDA out of memory (OOM)

Reduce batch size:
```bash
python model/hfl_trainer.py --batch_size 16 ...
```

Or reduce Mamba blocks:
```bash
# In model/hfl_mm_model.py, change n_mamba_layers=4 to 2
python model/hfl_trainer.py --n_mamba_layers 2 ...
```

---

### PTB-XL download fails

```bash
pip install wfdb --upgrade
python -c "import wfdb; wfdb.dl_database('ptb-xl', dl_dir='data/raw/ptb-xl')"
```

---

### `No module named 'device_utils'`

Make sure you're running from `SIMULATORS/model/` or `SIMULATORS/`:
```bash
cd ~/HFL/SIMULATORS
python model/hfl_trainer.py ...       # correct
# NOT:
python ~/HFL/SIMULATORS/model/hfl_trainer.py  # may break imports
```

---

### Chest X-Ray (Kermany) not found — ECG-only testing

If you only have PTB-XL and want to test the pipeline without Chest X-Ray images, the preprocessing script generates synthetic CXR tensors as stand-ins. The model still trains — just note the CXR branch uses synthetic data.

To force ECG-only mode, delete or rename `data/raw/chest-xray-pneumonia/` and run the preprocessor — it will detect the missing directory and warn you before falling back to synthetic CXR.

---

## 10. Phase Status Summary

| Phase | Title | Status | Key Output |
|---|---|---|---|
| Phase 1 | System Design & Topology | COMPLETE | Topology: 20 devices → 3 edges → 1 cloud |
| Phase 2 | Algorithm Design | COMPLETE | HFL-MM + PHANTOM-FL design |
| Phase 3 | NS-3 + CloudSim Setup | COMPLETE | Simulators installed and validated |
| Phase 4 | Simulation Validation | COMPLETE | Comm -76.4%, Energy -74.9%, Reliability 99.05% |
| **Phase 5** | **Healthcare Dataset + Model** | **ACTIVE** | PTB-XL + Kermany CXR, HFL-MM-HC, B0–B5, ONNX |
| Phase 6 | PHANTOM-FL + ClinicalCMGA | NEXT | Full novel model, ablation, paper figures |

### What is implemented as of Phase 5

- Dataset pipeline: `download_datasets.py`, `preprocess_healthcare.py`, `partition_noniid.py`
- IP-1 FedMamba-HC: `fedmamba_hc.py` — Mamba SSM ECG encoder
- IP-9 FedConform-HC: `fedconform_hc.py` — federated conformal prediction
- IP-3 ClinicalCMGA: `clinical_cmga_design.py` — full design, Phase 6 implementation
- Full model: `hfl_mm_model.py` — HFL-MM-HC (FedMamba + MobileNetV3 + FedConform)
- Training engine: `hfl_trainer.py` — two-tier FedAvg + DP-SGD + compression + conformal
- Baselines: `baselines.py` — B0 through B5
- Privacy sweep: `epsilon_sweep.py` — 6 ε values
- Edge deploy: `onnx_exporter.py` + `inference_bench.py`
- Network metrics: `ns3_phase5_integration.py`
- Results: `collect_phase5_results.py` → `phase5_results.csv`
- Device management: `device_utils.py` — GPU primary, CPU fallback, full optimization

### What comes in Phase 6

- `PHANTOM-FL` with `ClinicalCMGA` replacing the late-fusion head
- Full ablation study: P1 vs P1-no-Mamba vs P1-no-Conform vs P2 vs P2-no-CMGA
- 10 thesis-grade publication figures
- Paper draft: IEEE JBHI (primary) / npj Digital Medicine (secondary)
- Reproducible codebase packaging

---

*Last updated: 2026-04-27 | Phase 5 active*
