import { motion } from 'framer-motion'
import { useState } from 'react'
import { Monitor, HardDrive, FolderTree, Terminal, CheckCircle2 } from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Phase3() {
  const [activeTab, setActiveTab] = useState('system')

  return (
    <>
      <div className="page-header">
        <h2>Phase 3 — Environment Setup</h2>
        <p>System profile, dependencies, directory structure, build verification</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box success" style={{ marginBottom: 16 }}>
              <strong>Status:</strong> COMPLETE — NS-3 v3.46.1 built with Python bindings, CloudSim Plus v8.5.6 installed, Python research stack verified.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'system', icon: <Monitor size={14} />, label: 'System Profile' },
                { key: 'structure', icon: <FolderTree size={14} />, label: 'Directory Structure' },
                { key: 'ns3build', icon: <Terminal size={14} />, label: 'NS-3 Build' },
                { key: 'cloudsim', icon: <HardDrive size={14} />, label: 'CloudSim Plus' },
                { key: 'python', icon: <CheckCircle2 size={14} />, label: 'Python Stack' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {activeTab === 'system' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>System Profile (Verified)</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Component</th><th>Version / Spec</th></tr></thead>
                  <tbody>
                    <tr><td>OS</td><td>Ubuntu 24.04.4 LTS (Noble Numbat)</td></tr>
                    <tr><td>Kernel</td><td>6.17.0-14-generic</td></tr>
                    <tr><td>CPU</td><td>28 cores (HP Z2 Tower G9 Workstation)</td></tr>
                    <tr><td>RAM</td><td>15 GB (10 GB free)</td></tr>
                    <tr><td>Disk Free</td><td>276 GB</td></tr>
                    <tr><td>Python</td><td>3.12.3 + pip 24.0</td></tr>
                    <tr><td>Java</td><td>OpenJDK 21.0.10</td></tr>
                    <tr><td>Maven</td><td>3.8.7</td></tr>
                    <tr><td>GCC/G++</td><td>13.3.0</td></tr>
                    <tr><td>CMake</td><td>3.28.3</td></tr>
                    <tr><td>NS-3</td><td>v3.46.1 (source + built with Python bindings)</td></tr>
                    <tr><td>CloudSim Plus</td><td>v8.5.6 (installed)</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {activeTab === 'structure' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>Directory Structure</h3></div>
              <div className="code-block">
{`/home/mit/DEADSERPENT/HFL/
├── DOCUMENT PDF/              ← Research papers
├── PHASE REPORT/              ← Phase deliverables
└── SIMULATORS/
    ├── ns3/
    │   └── ns-3-dev/          ← NS-3 source (tag: ns-3.46.1)
    ├── cloudsim-plus/
    │   ├── cloudsim-plus-source/  ← CloudSim source (v8.5.6)
    │   └── hfl-simulation/        ← HFL Maven project
    │       ├── pom.xml
    │       └── src/main/java/hfl/
    ├── model/                     ← HFL-MM model code
    │   ├── architecture/          ← hfl_mm_model.py
    │   ├── deploy/                ← ONNX exporter + benchmark
    │   └── utils/                 ← FedConform-HC, privacy
    ├── data/loaders/              ← Dataset registry
    ├── scripts/                   ← Pipeline drivers
    ├── config/
    │   └── hfl_config.json        ← Shared simulation config
    └── results/
        ├── ns3/                   ← NS-3 CSV outputs
        ├── cloudsim/              ← CloudSim CSV outputs
        └── merged/                ← Merged analysis outputs`}
              </div>
            </motion.div>
          )}

          {activeTab === 'ns3build' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>NS-3 v3.46.1 Build</h3></div>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`cd ns3/ns-3-dev
./ns3 configure --enable-python-bindings
./ns3 build -j28
pip install cppyy  # Required by Python bindings`}
              </div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>v3.36+ API change:</strong> Bindings are NOT installed into site-packages — they live in <code>build/bindings/python</code>. API is FLAT: <code>from ns import ns</code>, then <code>ns.NodeContainer</code>. The old per-module namespaces (<code>ns.core</code>, <code>ns.network</code>) no longer exist.
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)' }}>
                Without a built tree, the packet-level script falls back to analytical mode and still prints results under an NS-3 heading. Check startup for: <code>[OK] NS-3 packet-level bindings loaded from ...</code>
              </div>
            </motion.div>
          )}

          {activeTab === 'cloudsim' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>CloudSim Plus v8.5.6</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Entry Point</div><div className="kv-value"><code>hfl.HFLCloudSimulation</code></div></div>
                <div className="kv-item"><div className="kv-label">Maven</div><div className="kv-value"><code>org.cloudsimplus:cloudsimplus</code></div></div>
              </div>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`cd cloudsim-plus/hfl-simulation
mvn clean compile exec:java \\
  -Dexec.mainClass="hfl.HFLCloudSimulation"`}
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                Argument interface not yet verified. Stage runs as OPTIONAL — failure reports NOT MEASURED for O4 rather than blocking the pipeline.
              </div>
            </motion.div>
          )}

          {activeTab === 'python' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Python Research Stack</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Package</th><th>Version</th><th>Purpose</th></tr></thead>
                  <tbody>
                    <tr><td>PyTorch</td><td>2.6+</td><td>Model training, DP-SGD</td></tr>
                    <tr><td>Opacus</td><td>latest</td><td>DP-SGD implementation + RDP accountant</td></tr>
                    <tr><td>ONNX Runtime</td><td>latest</td><td>Deployment inference benchmark</td></tr>
                    <tr><td>NumPy</td><td>2.4.2</td><td>Array operations</td></tr>
                    <tr><td>Pandas</td><td>3.0.1</td><td>Data handling</td></tr>
                    <tr><td>SciPy</td><td>1.17.1</td><td>Statistical tests</td></tr>
                    <tr><td>Seaborn</td><td>0.13.2</td><td>Visualisation</td></tr>
                    <tr><td>cppyy</td><td>latest</td><td>NS-3 Python bindings</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

        </motion.div>
      </div>
    </>
  )
}
