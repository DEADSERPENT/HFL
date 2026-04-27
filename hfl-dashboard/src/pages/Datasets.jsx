import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Database, Download, HardDrive,
  FolderTree, Cpu
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Datasets() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <>
      <div className="page-header">
        <h2>Dataset Access, Selection & Integration Guide</h2>
        <p>Healthcare domain — PTB-XL (ECG) + CheXpert (CXR) · 6 devices · 2 edges · Dirichlet α=5.0</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'overview', icon: <Database size={14} />, label: 'Overview' },
                { key: 'ptbxl', icon: <Cpu size={14} />, label: 'PTB-XL (ECG)' },
                { key: 'chexpert', icon: <HardDrive size={14} />, label: 'CheXpert (CXR)' },
                { key: 'partition', icon: <FolderTree size={14} />, label: 'Non-IID Partition' },
                { key: 'storage', icon: <Download size={14} />, label: 'Storage & Compute' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* OVERVIEW */}
          {activeTab === 'overview' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Healthcare Dataset Selection</h3></div>
              <div className="info-box success" style={{ marginBottom: 16 }}>
                <strong>Scope (Healthcare-Only, 2026-04-22):</strong> PTB-XL (21,837 12-lead ECG records) + CheXpert (224,316 chest X-rays). FedMamba-HC encoder (IP-1) requires [B, 12, 1000] input — PTB-XL is the only large-scale dataset providing this format. 6 devices, 2 edge clusters, Dirichlet α=5.0.
              </div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                Selection criteria: publicly available, multi-class (≥3), fits 12 GB VRAM, used in recent FL literature, compatible with FedMamba-HC 12-lead input.
              </div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Dataset</th><th>Modality</th><th>Source</th><th>Size</th><th>Samples</th><th>Access</th></tr></thead>
                  <tbody>
                    <tr className="highlight-row"><td><strong>PTB-XL</strong></td><td>12-lead ECG (Primary)</td><td>PhysioNet / Wagner et al.</td><td>~1.7 GB</td><td>21,837 records</td><td>Public (CC-BY 4.0)</td></tr>
                    <tr className="highlight-row"><td><strong>CheXpert</strong></td><td>Chest X-ray (Secondary)</td><td>Stanford ML Group</td><td>~11 GB</td><td>224,316 images</td><td>Registration req.</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Configuration</th><th>Value</th></tr></thead>
                  <tbody>
                    <tr><td>IoT Devices</td><td>6 (HC-A1, HC-A2, HC-A3, HC-B1, HC-B2, HC-B3)</td></tr>
                    <tr><td>Edge Servers</td><td>2 (Edge-A: devices 0–2 · Edge-B: devices 3–5)</td></tr>
                    <tr><td>Cloud Server</td><td>1 (hospital aggregator)</td></tr>
                    <tr><td>Total Samples</td><td>5,000 (PTB-XL subset, Dirichlet α=5.0, seed=42)</td></tr>
                    <tr><td>Task</td><td>5-class cardiac health: NORM / MI / STTC / CD / HYP</td></tr>
                    <tr><td>Train / Val / Test</td><td>~70% / ~15% / ~15% per device</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* PTB-XL */}
          {activeTab === 'ptbxl' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>PTB-XL — 12-Lead ECG Waveform Dataset (Primary)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Task</div><div className="kv-value">5-class cardiac health classification</div></div>
                <div className="kv-item"><div className="kv-label">Records</div><div className="kv-value">21,837 ECGs / 18,885 patients</div></div>
                <div className="kv-item"><div className="kv-label">Sampling Rate</div><div className="kv-value">100 Hz (resampled from 500 Hz)</div></div>
                <div className="kv-item"><div className="kv-label">Tensor Shape</div><div className="kv-value">[B, 12, 1000]</div></div>
                <div className="kv-item"><div className="kv-label">Size</div><div className="kv-value">~1.7 GB</div></div>
                <div className="kv-item"><div className="kv-label">License</div><div className="kv-value">CC-BY 4.0 (PhysioNet)</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>5-Class Labels (SNOMED codes)</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Class</th><th>Label</th><th>SNOMED Code</th><th># Records</th></tr></thead>
                  <tbody>
                    <tr><td>0</td><td>Normal (NORM)</td><td>426783006</td><td>9,514</td></tr>
                    <tr><td>1</td><td>Myocardial Infarction (MI)</td><td>164865005</td><td>5,469</td></tr>
                    <tr><td>2</td><td>ST/T Change (STTC)</td><td>428750005</td><td>5,250</td></tr>
                    <tr><td>3</td><td>Conduction Disturbance (CD)</td><td>233917008</td><td>4,907</td></tr>
                    <tr><td>4</td><td>Hypertrophy (HYP)</td><td>164873001</td><td>2,649</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Download</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`# Option A — wfdb Python library (recommended)
pip install wfdb
import wfdb
wfdb.dl_database('ptb-xl', dl_dir='SIMULATORS/data/raw/ptbxl/')

# Option B — wget (PhysioNet, CC-BY 4.0, no registration)
wget -r -N -c -np https://physionet.org/files/ptb-xl/1.0.3/

# Option C — Kaggle
kaggle datasets download -d khyeh0719/ptb-xl-dataset`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Preprocessing Pipeline</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`Step 1: Load via wfdb
  record = wfdb.rdrecord("records100/{filename}")
  signal = record.p_signal  # (1000, 12) @ 100 Hz

Step 2: Transpose → [12, 1000]

Step 3: Bandpass filter 0.5–40 Hz (removes baseline wander + EMG)
  from scipy.signal import butter, filtfilt
  b, a = butter(4, [0.5, 40], btype='bandpass', fs=100)
  signal_filt = filtfilt(b, a, signal_t, axis=1)

Step 4: Per-lead z-score normalization
  (signal - mean) / (std + 1e-8)  per lead

Step 5: Handle missing leads → zero-pad + lead-failure flag

Step 6: Load labels from ptbxl_database.csv
  label_map = {'NORM':0, 'MI':1, 'STTC':2, 'CD':3, 'HYP':4}

Output: signals.npy (21837, 12, 1000) — ~2.0 GB float32`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Actual Partition (partition_meta.json, α=5.0, seed=42)</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Device</th><th>Name</th><th>Edge</th><th>Total</th><th>NORM</th><th>MI</th><th>STTC</th><th>CD</th><th>HYP</th><th>Dominant</th></tr></thead>
                  <tbody>
                    <tr><td>device_00</td><td>HC-A1</td><td>A</td><td>573</td><td>58</td><td>151</td><td>75</td><td>127</td><td>162</td><td>HYP</td></tr>
                    <tr><td>device_01</td><td>HC-A2</td><td>A</td><td>594</td><td>55</td><td>91</td><td>233</td><td>98</td><td>117</td><td>STTC</td></tr>
                    <tr><td>device_02</td><td>HC-A3</td><td>A</td><td>896</td><td>212</td><td>149</td><td>111</td><td>207</td><td>217</td><td>HYP</td></tr>
                    <tr><td>device_03</td><td>HC-B1</td><td>B</td><td>689</td><td>186</td><td>132</td><td>107</td><td>173</td><td>91</td><td>NORM</td></tr>
                    <tr><td>device_04</td><td>HC-B2</td><td>B</td><td>919</td><td>213</td><td>199</td><td>245</td><td>124</td><td>138</td><td>STTC</td></tr>
                    <tr className="highlight-row"><td>device_05</td><td>HC-B3</td><td>B</td><td>1329</td><td>276</td><td>278</td><td>229</td><td>271</td><td>275</td><td>MI</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* CHEXPERT */}
          {activeTab === 'chexpert' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>CheXpert — Stanford Chest Radiograph Dataset (Secondary)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Task</div><div className="kv-value">5-label multilabel CXR classification</div></div>
                <div className="kv-item"><div className="kv-label">Images</div><div className="kv-value">224,316 frontal chest X-rays</div></div>
                <div className="kv-item"><div className="kv-label">Patients</div><div className="kv-value">65,240</div></div>
                <div className="kv-item"><div className="kv-label">Resolution</div><div className="kv-value">224×224 (small version, pre-resized)</div></div>
                <div className="kv-item"><div className="kv-label">Size</div><div className="kv-value">~11 GB (small version)</div></div>
                <div className="kv-item"><div className="kv-label">Source</div><div className="kv-value">Irvin et al., AAAI 2019</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>5-Label Classification (u-zeros uncertainty policy)</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Label</th><th>Pathology</th><th># Positive</th><th>Uncertain →</th></tr></thead>
                  <tbody>
                    <tr><td>0</td><td>No Finding</td><td>16,627</td><td>N/A</td></tr>
                    <tr><td>1</td><td>Pleural Effusion</td><td>75,696</td><td>→ 0</td></tr>
                    <tr><td>2</td><td>Cardiomegaly</td><td>20,739</td><td>→ 0</td></tr>
                    <tr><td>3</td><td>Atelectasis</td><td>29,420</td><td>→ 0</td></tr>
                    <tr><td>4</td><td>Consolidation</td><td>12,730</td><td>→ 0</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Download</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`# Option A — Official Stanford (free registration required)
# 1. Register: stanfordmlgroup.github.io/projects/chexpert/
# 2. Download link sent by email — use small dataset (~11 GB)

# Option B — Kaggle
kaggle datasets download -d ashery/chexpert
unzip chexpert.zip -d SIMULATORS/data/raw/chexpert/`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Preprocessing</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`import torchvision.transforms as T
import pandas as pd

transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet stats
                std=[0.229, 0.224, 0.225])
])
# CheXpert small is already RGB — no Grayscale conversion needed

# Label loading (u-zeros: uncertain -1 → 0)
df = pd.read_csv("train.csv")
label_cols = ['No Finding','Pleural Effusion','Cardiomegaly',
              'Atelectasis','Consolidation']
labels = df[label_cols].fillna(0).replace(-1, 0).values`}
              </div>

              <div className="info-box note">
                <strong>Pairing with PTB-XL:</strong> 70% direct patient pairs (same patient has both ECG + CXR). 30% within-class synthetic pairs (matching cardiac condition label). Combined loss: 0.7 × CrossEntropy(ECG_logits) + 0.3 × BCE(CXR_logits).
              </div>
            </motion.div>
          )}

          {/* NON-IID PARTITION */}
          {activeTab === 'partition' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>Non-IID Partitioning — 6 Devices, Dirichlet α=5.0</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                α=5.0 produces mild non-IID — near-uniform class distribution per device. This reflects realistic hospital deployment where each ward or clinic sees a mix of cardiac conditions. Authoritative source: <code>partition_meta.json</code>.
              </div>

              <div className="code-block" style={{ marginBottom: 20 }}>
{`Algorithm (Dirichlet Non-IID, standard in FL literature):
  For each class c in {NORM, MI, STTC, CD, HYP}:
    proportions = np.random.dirichlet(α × ones(6), seed=42)
    Assign proportions[i] fraction of class-c samples to device i.

Run: python data/loaders/partition_noniid.py \\
       --domain healthcare --n_devices 6 --alpha 5.0 --seed 42`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Partition Table (partition_meta.json — 5,000 total samples)</h4>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Device</th><th>Name</th><th>Edge</th><th>Total</th><th>Train</th><th>Val</th><th>Test</th><th>NORM</th><th>MI</th><th>STTC</th><th>CD</th><th>HYP</th><th>Dominant</th></tr></thead>
                  <tbody>
                    <tr><td>device_00</td><td>HC-A1</td><td>A</td><td>573</td><td>401</td><td>85</td><td>87</td><td>58</td><td>151</td><td>75</td><td>127</td><td>162</td><td>HYP</td></tr>
                    <tr><td>device_01</td><td>HC-A2</td><td>A</td><td>594</td><td>415</td><td>89</td><td>90</td><td>55</td><td>91</td><td>233</td><td>98</td><td>117</td><td>STTC</td></tr>
                    <tr><td>device_02</td><td>HC-A3</td><td>A</td><td>896</td><td>627</td><td>134</td><td>135</td><td>212</td><td>149</td><td>111</td><td>207</td><td>217</td><td>HYP</td></tr>
                    <tr><td>device_03</td><td>HC-B1</td><td>B</td><td>689</td><td>482</td><td>103</td><td>104</td><td>186</td><td>132</td><td>107</td><td>173</td><td>91</td><td>NORM</td></tr>
                    <tr><td>device_04</td><td>HC-B2</td><td>B</td><td>919</td><td>643</td><td>137</td><td>139</td><td>213</td><td>199</td><td>245</td><td>124</td><td>138</td><td>STTC</td></tr>
                    <tr className="highlight-row"><td>device_05</td><td>HC-B3</td><td>B</td><td>1329</td><td>930</td><td>199</td><td>200</td><td>276</td><td>278</td><td>229</td><td>271</td><td>275</td><td>MI</td></tr>
                  </tbody>
                </table>
              </div>

              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Edge A (HC-A)</div><div className="kv-value">HC-A1 (573) + HC-A2 (594) + HC-A3 (896) = 2,063</div></div>
                <div className="kv-item"><div className="kv-label">Edge B (HC-B)</div><div className="kv-value">HC-B1 (689) + HC-B2 (919) + HC-B3 (1329) = 2,937</div></div>
                <div className="kv-item"><div className="kv-label">Dirichlet α</div><div className="kv-value">5.0 (mild non-IID, seed=42)</div></div>
                <div className="kv-item"><div className="kv-label">Split</div><div className="kv-value">70% train / 15% val / 15% test</div></div>
              </div>
            </motion.div>
          )}

          {/* STORAGE & COMPUTE */}
          {activeTab === 'storage' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Storage Structure & Compute Requirements</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Disk Space</h4>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Dataset</th><th>Raw Size</th><th>Processed</th><th>Download Time</th></tr></thead>
                  <tbody>
                    <tr><td>PTB-XL</td><td>~1.7 GB</td><td>~2 GB</td><td>~10 min</td></tr>
                    <tr><td>CheXpert (small)</td><td>~11 GB</td><td>~8 GB</td><td>~45 min</td></tr>
                    <tr className="highlight-row"><td><strong>TOTAL</strong></td><td><strong>~12.7 GB</strong></td><td><strong>~10 GB</strong></td><td><strong>~55 min</strong></td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Storage Structure</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`SIMULATORS/data/
├── raw/
│   ├── ptbxl/              # .hea/.dat waveforms + ptbxl_database.csv
│   └── chexpert/           # .jpg images + train.csv / valid.csv
├── processed/
│   └── healthcare/         # ecg_signals.npy  (21837, 12, 1000)
│                           # cxr_images.npy   (224316, 3, 224, 224)
│                           # labels_ecg.npy, labels_cxr.npy
└── partitions/
    └── healthcare/
        ├── partition_meta.json      # Ground-truth partition (α=5.0)
        ├── device_00/ (HC-A1)       # train.pt, val.pt, test.pt — 573 samples
        ├── device_01/ (HC-A2)       # 594 samples
        ├── device_02/ (HC-A3)       # 896 samples
        ├── device_03/ (HC-B1)       # 689 samples
        ├── device_04/ (HC-B2)       # 919 samples
        └── device_05/ (HC-B3)       # 1329 samples`}
              </div>

              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">GPU</div><div className="kv-value">RTX A2000 12GB VRAM</div></div>
                <div className="kv-item"><div className="kv-label">Batch Size</div><div className="kv-value">32 per device (virtual, federated)</div></div>
                <div className="kv-item"><div className="kv-label">GPU Memory/Step</div><div className="kv-value">~4–6 GB (FedMamba-HC + MobileNetV3)</div></div>
                <div className="kv-item"><div className="kv-label">Training Time</div><div className="kv-value">20 global rounds × τ_e=5 ≈ 2.7h</div></div>
              </div>
            </motion.div>
          )}

          {/* Backup Datasets */}
          <motion.div variants={fadeUp} className="section" style={{ marginTop: 40 }}>
            <div className="section-header"><div className="section-number">6</div><h3>Backup Datasets (Healthcare)</h3></div>
            <div className="table-container">
              <table className="data-table">
                <thead><tr><th>Modality</th><th>Primary (Active)</th><th>Backup</th><th>Reason</th></tr></thead>
                <tbody>
                  <tr><td>ECG (Primary)</td><td>PTB-XL (PhysioNet)</td><td>MIT-BIH Arrhythmia (PhysioNet)</td><td>Smaller (105 MB), 2-class only</td></tr>
                  <tr><td>CXR (Secondary)</td><td>CheXpert (Stanford)</td><td>ChestX-ray14 (NIH)</td><td>Larger (45 GB), 14 labels, slower download</td></tr>
                </tbody>
              </table>
            </div>
          </motion.div>

        </motion.div>
      </div>
    </>
  )
}
