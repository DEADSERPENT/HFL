import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Database, Download, Layers, BarChart3, FileText, HardDrive,
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
        <p>5 datasets across 3 IoT domains — download, preprocessing, non-IID partitioning</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'overview', icon: <Database size={14} />, label: 'Overview' },
                { key: 'cwru', icon: <Layers size={14} />, label: 'CWRU (IIoT)' },
                { key: 'urban', icon: <BarChart3 size={14} />, label: 'UrbanSound8K' },
                { key: 'epa', icon: <FileText size={14} />, label: 'EPA AQS' },
                { key: 'wesad', icon: <Cpu size={14} />, label: 'WESAD' },
                { key: 'chest', icon: <HardDrive size={14} />, label: 'ChestX-ray14' },
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
              <div className="section-header"><div className="section-number">1</div><h3>Why These Datasets</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                The HFL-MM framework targets THREE IoT application domains, each requiring TWO heterogeneous modalities. Selection criteria: publicly available, multi-class (≥3), appropriate size (12GB VRAM, 500GB disk), used in recent FL literature, represents real IoT data.
              </div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Domain</th><th>Primary Modality</th><th>Secondary Modality</th><th>Classes</th></tr></thead>
                  <tbody>
                    <tr><td><strong>IIoT</strong></td><td>CWRU vibration</td><td>STFT spectrograms</td><td>4</td></tr>
                    <tr><td><strong>Smart City</strong></td><td>UrbanSound8K audio</td><td>EPA air quality CSV</td><td>5</td></tr>
                    <tr><td><strong>Healthcare</strong></td><td>WESAD wearable EEG</td><td>ChestX-ray14 images</td><td>4/14</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Dataset</th><th>Source</th><th>Size</th><th>Samples</th><th>Access</th></tr></thead>
                  <tbody>
                    <tr><td>CWRU Bearing</td><td>Case Western Reserve Univ.</td><td>~800 MB</td><td>~48K windows</td><td>Public (web)</td></tr>
                    <tr><td>UrbanSound8K</td><td>NYU MARL / Salamon et al.</td><td>~6 GB</td><td>8,732 clips</td><td>Public (Zenodo)</td></tr>
                    <tr><td>EPA AQS</td><td>US EPA</td><td>~500 MB</td><td>~365K hourly</td><td>Public (API/CSV)</td></tr>
                    <tr><td>WESAD</td><td>ETH Zürich / UCI ML Repo</td><td>~4 GB</td><td>15 subjects</td><td>Public (UCI)</td></tr>
                    <tr><td>ChestX-ray14</td><td>NIH Clinical Center</td><td>~42 GB</td><td>112,120 images</td><td>Public (Box)</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* CWRU */}
          {activeTab === 'cwru' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>CWRU Bearing Vibration (IIoT Primary)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Task</div><div className="kv-value">Rotating machinery fault detection</div></div>
                <div className="kv-item"><div className="kv-label">Sampling Rate</div><div className="kv-value">12,000 Hz (drive-end)</div></div>
                <div className="kv-item"><div className="kv-label">Load Conditions</div><div className="kv-value">0, 1, 2, 3 HP</div></div>
                <div className="kv-item"><div className="kv-label">File Format</div><div className="kv-value">.mat (MATLAB)</div></div>
                <div className="kv-item"><div className="kv-label">Total Size</div><div className="kv-value">~800 MB</div></div>
                <div className="kv-item"><div className="kv-label">URL</div><div className="kv-value" style={{ fontSize: 10 }}>engineering.case.edu/bearingdatacenter</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Classes</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Class</th><th>Condition</th><th>Fault Diameter</th></tr></thead>
                  <tbody>
                    <tr><td>0</td><td>Normal (healthy bearing)</td><td>—</td></tr>
                    <tr><td>1</td><td>Ball fault</td><td>0.007", 0.014", 0.021"</td></tr>
                    <tr><td>2</td><td>Inner race fault</td><td>0.007", 0.014", 0.021"</td></tr>
                    <tr><td>3</td><td>Outer race fault</td><td>0.007", 0.014", 0.021"</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Preprocessing Pipeline</h4>
              <div className="code-block">
{`Step 1: Load .mat files → scipy.io.loadmat("97.mat")
Step 2: Sliding window: size=1024, stride=512 (50% overlap)
        → Each file yields ~500–2000 windows
Step 3: Normalize: (signal - mean) / std, clip [-3, 3]
Step 4: Generate spectrogram (second modality):
        STFT(window, fs=12000, nperseg=256) → resize 224×224 → jet colormap RGB
Step 5: Save: signals.npy (N, 1024), spectrograms.npy (N, 3, 224, 224)
Total: ~35,000–50,000 windows`}
              </div>
            </motion.div>
          )}

          {/* URBANSOUND8K */}
          {activeTab === 'urban' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>UrbanSound8K (Smart City Primary)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Task</div><div className="kv-value">Urban sound event classification</div></div>
                <div className="kv-item"><div className="kv-label">Clips</div><div className="kv-value">8,732 (≤4s each)</div></div>
                <div className="kv-item"><div className="kv-label">Format</div><div className="kv-value">.wav (variable sample rate)</div></div>
                <div className="kv-item"><div className="kv-label">Size</div><div className="kv-value">~6 GB (full), ~3 GB (5 classes)</div></div>
                <div className="kv-item"><div className="kv-label">Source</div><div className="kv-value">Salamon et al., ACM MM 2014</div></div>
                <div className="kv-item"><div className="kv-label">Folds</div><div className="kv-value">10 pre-defined</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Classes Used (5 of 10)</h4>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Class 0</div><div className="kv-value">air_conditioner</div></div>
                <div className="kv-item"><div className="kv-label">Class 1</div><div className="kv-value">car_horn</div></div>
                <div className="kv-item"><div className="kv-label">Class 2</div><div className="kv-value">children_playing</div></div>
                <div className="kv-item"><div className="kv-label">Class 3</div><div className="kv-value">dog_bark</div></div>
                <div className="kv-item"><div className="kv-label">Class 4</div><div className="kv-value">street_music</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Preprocessing (Mel-Spectrogram)</h4>
              <div className="code-block">
{`librosa.load(file, sr=22050, duration=4.0, mono=True)
→ Pad/trim to fixed duration → Mel spectrogram:
  librosa.feature.melspectrogram(n_mels=128, hop=512, n_fft=1024)
→ Power to dB → Normalize [0,1]
→ Repeat 1ch → 3ch (gray → RGB) → resize to (3, 224, 224)
→ Ready for MobileNetV3 (Encoder B)`}
              </div>
            </motion.div>
          )}

          {/* EPA AQS */}
          {activeTab === 'epa' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>EPA Air Quality System (Smart City Secondary)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Task</div><div className="kv-value">Air quality index classification</div></div>
                <div className="kv-item"><div className="kv-label">Source</div><div className="kv-value">US Environmental Protection Agency</div></div>
                <div className="kv-item"><div className="kv-label">URL</div><div className="kv-value" style={{ fontSize: 10 }}>aqs.epa.gov/aqsweb/airdata/download_files.html</div></div>
                <div className="kv-item"><div className="kv-label">Size</div><div className="kv-value">~500 MB</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Feature Vector (6 dimensions)</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`Per hourly aggregation window:
  [PM2.5_mean, NO2_mean, O3_mean, CO_mean, AQI, temperature]
Normalize each to [0,1] across training set.
Label: AQI category (0=Good, 1=Moderate, 2=Unhealthy for Sensitive,
                      3=Unhealthy, 4=Very Unhealthy)`}
              </div>
              <div className="info-box note">
                <strong>Note:</strong> For Smart City domain, Encoder A is simplified to an FC encoder for the 6-dim environmental vector: FC(6)→FC(64)→FC(128) (no convolution needed). Encoder B processes the UrbanSound8K mel-spectrogram.
              </div>
            </motion.div>
          )}

          {/* WESAD */}
          {activeTab === 'wesad' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>WESAD — Wearable Stress and Affect Detection (Healthcare Primary)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Task</div><div className="kv-value">Physiological stress detection</div></div>
                <div className="kv-item"><div className="kv-label">Subjects</div><div className="kv-value">15 participants</div></div>
                <div className="kv-item"><div className="kv-label">Sensors</div><div className="kv-value">ACC (32Hz), EDA (4Hz), TEMP (4Hz)</div></div>
                <div className="kv-item"><div className="kv-label">Format</div><div className="kv-value">.pkl per subject</div></div>
                <div className="kv-item"><div className="kv-label">Size</div><div className="kv-value">~4 GB</div></div>
                <div className="kv-item"><div className="kv-label">Source</div><div className="kv-value">Schmidt et al., ACM ICMI 2018</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Classes</h4>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Class 0</div><div className="kv-value">Baseline (relaxed)</div></div>
                <div className="kv-item"><div className="kv-label">Class 1</div><div className="kv-value">Stress (Trier Social Stress)</div></div>
                <div className="kv-item"><div className="kv-label">Class 2</div><div className="kv-value">Amusement (comedy video)</div></div>
                <div className="kv-item"><div className="kv-label">Class 3</div><div className="kv-value">Meditation (optional)</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Preprocessing</h4>
              <div className="code-block">
{`load_wesad_subject(id) → acc(3-axis), eda(1ch), temp(1ch), labels
create_windows(signals, labels, window_sec=5, fs=32)
  → 160 samples per window (5s × 32Hz)
Output: (N, 5, 160) → [5 channels: ACC×3, EDA, TEMP]
Reshape for 1D-CNN: (N, 5, 160) → Encoder A input
in_channels=5 for Healthcare domain`}
              </div>
            </motion.div>
          )}

          {/* CHESTXRAY14 */}
          {activeTab === 'chest' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>NIH ChestX-ray14 (Healthcare Secondary)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Task</div><div className="kv-value">Chest pathology detection</div></div>
                <div className="kv-item"><div className="kv-label">Images</div><div className="kv-value">112,120 frontal-view X-rays</div></div>
                <div className="kv-item"><div className="kv-label">Resolution</div><div className="kv-value">1024×1024 grayscale</div></div>
                <div className="kv-item"><div className="kv-label">Full Size</div><div className="kv-value">~45 GB</div></div>
                <div className="kv-item"><div className="kv-label">4-class Subset</div><div className="kv-value">~11 GB</div></div>
                <div className="kv-item"><div className="kv-label">Source</div><div className="kv-value">Wang et al., CVPR 2017</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>4-Class Subset</h4>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Class 0</div><div className="kv-value">No Finding (normal)</div></div>
                <div className="kv-item"><div className="kv-label">Class 1</div><div className="kv-value">Atelectasis</div></div>
                <div className="kv-item"><div className="kv-label">Class 2</div><div className="kv-value">Cardiomegaly</div></div>
                <div className="kv-item"><div className="kv-label">Class 3</div><div className="kv-value">Effusion</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Preprocessing</h4>
              <div className="code-block">
{`T.Compose([
    T.Grayscale(num_output_channels=3),  # Gray → RGB (MobileNetV3)
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet stats
                std=[0.229, 0.224, 0.225])
])`}
              </div>
            </motion.div>
          )}

          {/* NON-IID PARTITION */}
          {activeTab === 'partition' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">8</div><h3>Non-IID Partitioning Across 20 Devices</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                Dirichlet distribution (α=0.5) across devices per cluster. Strong class imbalance tests the HFL-MM framework's ability to converge under severe non-IID conditions — a key challenge addressed by two-tier FedAvg with weighted aggregation.
              </div>

              <div className="code-block" style={{ marginBottom: 20 }}>
{`Algorithm (Dirichlet Non-IID, standard in FL literature):
  For each class c in domain d:
    proportions = np.random.dirichlet(α × ones(n_devices_in_cluster))
    Assign fraction proportions[i] of class-c samples to device i.`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Example: IIoT Domain (7 devices, 4 classes, α=0.5)</h4>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Device</th><th>Normal</th><th>Ball</th><th>Inner</th><th>Outer</th><th>Total</th></tr></thead>
                  <tbody>
                    <tr><td>Dev-0</td><td>62.4%</td><td>18.3%</td><td>12.5%</td><td>6.8%</td><td>4,210</td></tr>
                    <tr><td>Dev-1</td><td>8.1%</td><td>71.2%</td><td>15.3%</td><td>5.4%</td><td>3,870</td></tr>
                    <tr><td>Dev-2</td><td>4.3%</td><td>3.2%</td><td>78.9%</td><td>13.6%</td><td>4,550</td></tr>
                    <tr><td>Dev-3</td><td>21.7%</td><td>12.4%</td><td>4.8%</td><td>61.1%</td><td>3,990</td></tr>
                    <tr><td>Dev-4</td><td>45.2%</td><td>30.1%</td><td>19.0%</td><td>5.7%</td><td>4,100</td></tr>
                    <tr><td>Dev-5</td><td>7.8%</td><td>8.9%</td><td>6.4%</td><td>76.9%</td><td>3,750</td></tr>
                    <tr><td>Dev-6</td><td>50.5%</td><td>6.0%</td><td>38.5%</td><td>5.0%</td><td>4,630</td></tr>
                  </tbody>
                </table>
              </div>

              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Cluster 1 (IIoT)</div><div className="kv-value">Devices 0–6</div></div>
                <div className="kv-item"><div className="kv-label">Cluster 2 (Smart City)</div><div className="kv-value">Devices 7–13</div></div>
                <div className="kv-item"><div className="kv-label">Cluster 3 (Healthcare)</div><div className="kv-value">Devices 14–19</div></div>
                <div className="kv-item"><div className="kv-label">Train/Val/Test</div><div className="kv-value">70% / 15% / 15%</div></div>
              </div>
            </motion.div>
          )}

          {/* STORAGE & COMPUTE */}
          {activeTab === 'storage' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">9–10</div><h3>Storage Structure & Compute Requirements</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Disk Space Requirements</h4>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Dataset</th><th>Raw Size</th><th>Processed</th><th>Download Time</th></tr></thead>
                  <tbody>
                    <tr><td>CWRU Bearing</td><td>~800 MB</td><td>~2 GB</td><td>~5 min</td></tr>
                    <tr><td>UrbanSound8K</td><td>~6 GB</td><td>~4 GB</td><td>~20 min</td></tr>
                    <tr><td>EPA AQS</td><td>~500 MB</td><td>~100 MB</td><td>~5 min</td></tr>
                    <tr><td>WESAD</td><td>~4 GB</td><td>~500 MB</td><td>~15 min</td></tr>
                    <tr><td>ChestX-ray14 (4-cls)</td><td>~11 GB</td><td>~8 GB</td><td>~45 min</td></tr>
                    <tr className="highlight-row"><td><strong>TOTAL</strong></td><td><strong>~22 GB</strong></td><td><strong>~15 GB</strong></td><td><strong>~90 min</strong></td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Storage Structure</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`SIMULATORS/data/
├── raw/
│   ├── cwru/           # Raw .mat files
│   ├── urbansound/     # Raw .wav files (10 folds)
│   ├── epa_aqs/        # Raw .zip / .csv files
│   ├── wesad/          # Raw .pkl files (S2–S17)
│   └── chestxray/      # Raw .png images + CSV
├── processed/
│   ├── cwru/           # signals.npy, spectrograms.npy, labels.npy
│   ├── smartcity/      # melspecs.npy, env_vectors.npy, labels.npy
│   └── healthcare/     # wearable.npy, xray.npy, labels.npy
└── partitioned/
    ├── iiot/           # device_0/ → device_6/ (train.pt, val.pt, test.pt)
    ├── smartcity/      # device_7/ → device_13/
    └── healthcare/     # device_14/ → device_19/`}
              </div>

              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">GPU</div><div className="kv-value">RTX A2000 12GB VRAM</div></div>
                <div className="kv-item"><div className="kv-label">Batch Size</div><div className="kv-value">32 per device (federated)</div></div>
                <div className="kv-item"><div className="kv-label">GPU Memory/Step</div><div className="kv-value">~4–6 GB</div></div>
                <div className="kv-item"><div className="kv-label">Training Time</div><div className="kv-value">20 rounds × ~8 min ≈ 2.7h</div></div>
              </div>
            </motion.div>
          )}

          {/* Backup Datasets */}
          <motion.div variants={fadeUp} className="section" style={{ marginTop: 40 }}>
            <div className="section-header"><div className="section-number">7</div><h3>Backup Datasets</h3></div>
            <div className="table-container">
              <table className="data-table">
                <thead><tr><th>Domain</th><th>Primary</th><th>Backup</th><th>Size</th></tr></thead>
                <tbody>
                  <tr><td>IIoT vibration</td><td>CWRU Bearing</td><td>MFPT Bearing (mfpt.org)</td><td>~1 GB</td></tr>
                  <tr><td>Smart City audio</td><td>UrbanSound8K</td><td>ESC-50 (50 classes)</td><td>~600 MB</td></tr>
                  <tr><td>Smart City env.</td><td>EPA AQS</td><td>Beijing PM2.5 (UCI)</td><td>Simpler</td></tr>
                  <tr><td>Healthcare signal</td><td>WESAD</td><td>MIT-BIH Arrhythmia (PhysioNet)</td><td>Well-known</td></tr>
                  <tr><td>Healthcare imaging</td><td>ChestX-ray14</td><td>CheXpert (Stanford)</td><td>Similar</td></tr>
                </tbody>
              </table>
            </div>
          </motion.div>

        </motion.div>
      </div>
    </>
  )
}
