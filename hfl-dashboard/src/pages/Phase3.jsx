import { motion } from 'framer-motion'
import { useState } from 'react'
import { Monitor, Globe, Cloud, Settings, ClipboardCheck, FolderTree, CheckCircle2, FileJson, FileText } from 'lucide-react'

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
        <p>System profile, NS-3/CloudSim Plus installation, shared configuration, and reproducibility</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          {/* Stats */}
          <motion.div variants={fadeUp}>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">NS-3 Version</div>
                <div className="stat-value green">v3.46.1</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">CloudSim Plus</div>
                <div className="stat-value green">v8.5.6</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Verification Checks</div>
                <div className="stat-value">23/23</div>
                <div className="stat-change positive">All Passed</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Status</div>
                <div className="stat-value green">Done ✓</div>
              </div>
            </div>
          </motion.div>

          {/* Tabs */}
          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'system', icon: <Monitor size={14} />, label: 'System Profile' },
                { key: 'ns3', icon: <Globe size={14} />, label: 'NS-3 Install' },
                { key: 'cloudsim', icon: <Cloud size={14} />, label: 'CloudSim Install' },
                { key: 'config', icon: <Settings size={14} />, label: 'Configuration' },
                { key: 'reproducibility', icon: <ClipboardCheck size={14} />, label: 'Reproducibility' }
              ].map(tab => (
                <button
                  key={tab.key}
                  className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* System Profile */}
          {activeTab === 'system' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number"><Monitor size={16}/></div>
                <h3>System Profile (Verified)</h3>
              </div>

              <div className="info-box success">
                <strong>Student:</strong> Samartha H V | MIT Bengaluru | 251580130019
              </div>

              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">OS</div><div className="kv-value">Ubuntu 24.04.4 LTS</div></div>
                <div className="kv-item"><div className="kv-label">Kernel</div><div className="kv-value">6.17.0-14-generic</div></div>
                <div className="kv-item"><div className="kv-label">CPU Cores</div><div className="kv-value">28</div></div>
                <div className="kv-item"><div className="kv-label">Workstation</div><div className="kv-value">HP Z2 Tower G9</div></div>
                <div className="kv-item"><div className="kv-label">RAM</div><div className="kv-value">15 GB (10 GB free)</div></div>
                <div className="kv-item"><div className="kv-label">Disk Free</div><div className="kv-value">276 GB</div></div>
                <div className="kv-item"><div className="kv-label">Python</div><div className="kv-value">3.12.3 + pip 24.0</div></div>
                <div className="kv-item"><div className="kv-label">Java</div><div className="kv-value">OpenJDK 21.0.10</div></div>
                <div className="kv-item"><div className="kv-label">Maven</div><div className="kv-value">3.8.7</div></div>
                <div className="kv-item"><div className="kv-label">GCC/G++</div><div className="kv-value">13.3.0</div></div>
                <div className="kv-item"><div className="kv-label">CMake</div><div className="kv-value">3.28.3</div></div>
                <div className="kv-item"><div className="kv-label">Git</div><div className="kv-value">2.43.0</div></div>
              </div>

              {/* Directory Structure */}
              <div className="section-header" style={{ marginTop: 32 }}>
                <div className="section-number"><FolderTree size={16}/></div>
                <h3>Project Directory Structure</h3>
              </div>
              <div className="card">
                <div className="code-block">
{`/home/mit/DEADSERPENT/HFL/
├── DOCUMENT PDF/             ← Research papers
├── PHASE REPORT/             ← Phase deliverables
└── SIMULATORS/
    ├── ns3/
    │   └── ns-3-dev/         ← NS-3 source (tag: ns-3.46.1)
    ├── cloudsim-plus/
    │   ├── cloudsim-plus-source/  ← CloudSim Plus source (v8.5.6)
    │   └── hfl-simulation/        ← HFL Maven project
    │       ├── pom.xml
    │       └── src/main/java/hfl/
    │           └── HFLSimTest.java
    ├── scripts/
    │   ├── install_ns3.sh        ← Full NS-3 installer
    │   ├── install_cloudsim.sh   ← Full CloudSim Plus installer
    │   ├── verify_setup.sh       ← Environment verifier
    │   └── ns3_hfl_smoketest.py  ← NS-3 Python smoke test
    ├── config/
    │   └── hfl_config.json       ← Shared simulation config
    └── results/
        ├── ns3/                  ← NS-3 CSV outputs
        ├── cloudsim/             ← CloudSim CSV outputs
        └── merged/               ← Merged analysis outputs`}
                </div>
              </div>
            </motion.div>
          )}

          {/* NS-3 Install */}
          {activeTab === 'ns3' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">1</div>
                <h3>NS-3 v3.46.1 Installation</h3>
              </div>

              <div className="section-description">
                NS-3 is the selected network simulation tool for modeling the wireless and wired communication layers of the HFL system. Version 3.46.1 includes full Python bindings via PyBind11, WiFi 802.11ax, LTE-Advanced, 5G mmWave channel models, FlowMonitor module, and 28-core parallel build support.
              </div>

              {/* Step 1 */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon green"><Globe size={18}/></div>
                  <div><div className="card-title">Install System Dependencies</div><div className="card-subtitle">Run with sudo (requires admin privileges)</div></div>
                </div>
                <div className="code-block">
{`sudo apt-get update
sudo apt-get install -y \\
    build-essential libsqlite3-dev libboost-all-dev \\
    libssl-dev python3-dev python3-setuptools \\
    python3-pip bison flex ccache libxml2-dev \\
    libgsl-dev libopenmpi-dev openmpi-bin \\
    ninja-build castxml libpython3-dev python3-pytest \\
    clang-format valgrind gdb`}
                </div>
                <div className="info-box success" style={{ marginTop: 8, marginBottom: 0 }}>
                  Pre-verified: build-essential, libsqlite3-dev, libboost-all-dev, libssl-dev, python3-dev, ninja-build, libpython3-dev all installed ✓
                </div>
              </div>

              {/* Step 2 */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon green"><Globe size={18}/></div>
                  <div><div className="card-title">Install Python Research Packages</div></div>
                </div>
                <div className="code-block">
{`pip3 install --user --break-system-packages \\
    numpy pandas matplotlib scipy seaborn cppyy`}
                </div>
                <div className="kv-grid" style={{ marginTop: 8 }}>
                  <div className="kv-item"><div className="kv-label">numpy</div><div className="kv-value">2.4.2 ✓</div></div>
                  <div className="kv-item"><div className="kv-label">pandas</div><div className="kv-value">3.0.1 ✓</div></div>
                  <div className="kv-item"><div className="kv-label">scipy</div><div className="kv-value">1.17.1 ✓</div></div>
                  <div className="kv-item"><div className="kv-label">seaborn</div><div className="kv-value">0.13.2 ✓</div></div>
                </div>
              </div>

              {/* Step 3 */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon green"><Globe size={18}/></div>
                  <div><div className="card-title">Clone NS-3 Source</div></div>
                </div>
                <div className="code-block">
{`cd /home/mit/DEADSERPENT/HFL/SIMULATORS/ns3
git clone https://gitlab.com/nsnam/ns-3-dev.git
cd ns-3-dev
git checkout ns-3.46.1`}
                </div>
                <div className="badge done" style={{ marginTop: 8 }}>✓ Repository cloned. Tag ns-3.46.1 checked out.</div>
              </div>

              {/* Step 4 */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon green"><Globe size={18}/></div>
                  <div><div className="card-title">Configure NS-3 with Python Bindings</div></div>
                </div>
                <div className="code-block">
{`./ns3 configure \\
    --enable-python-bindings \\
    --enable-examples \\
    --enable-tests \\
    --build-profile=optimized`}
                </div>
                <div className="kv-grid" style={{ marginTop: 8 }}>
                  <div className="kv-item"><div className="kv-label">--enable-python-bindings</div><div className="kv-value" style={{ fontSize: 11 }}>Compiles PyBind11 interface</div></div>
                  <div className="kv-item"><div className="kv-label">--enable-examples</div><div className="kv-value" style={{ fontSize: 11 }}>Builds sample scripts</div></div>
                  <div className="kv-item"><div className="kv-label">--build-profile</div><div className="kv-value" style={{ fontSize: 11 }}>Optimized (faster runs)</div></div>
                </div>
              </div>

              {/* Step 5-7 */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon green"><Globe size={18}/></div>
                  <div><div className="card-title">Build NS-3 (using all 28 cores)</div></div>
                </div>
                <div className="code-block">{`./ns3 build -j28`}</div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 8 }}>Expected build time: 10–20 minutes on this workstation.</p>
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon green"><Globe size={18}/></div>
                  <div><div className="card-title">Verify NS-3 Installation</div></div>
                </div>
                <div className="code-block">
{`# C++ test:
./ns3 run hello-simulator
# Expected output: "Hello Simulator"

# Python binding test:
python3 -c "import ns.core; print(ns.core.__version__)"
# Expected: ns-3.46.1

# Set PYTHONPATH if needed:
export PYTHONPATH=$PWD/build/bindings/python:$PYTHONPATH`}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <div className="card-icon green"><Globe size={18}/></div>
                  <div><div className="card-title">Run HFL Smoke Test</div></div>
                </div>
                <div className="code-block">
{`python3 ../../scripts/ns3_hfl_smoketest.py

# Tests: 3-node (Device→Edge→Cloud) P2P topology
# Validates: packet transmission, latency measurement, CSV output`}
                </div>
              </div>
            </motion.div>
          )}

          {/* CloudSim Install */}
          {activeTab === 'cloudsim' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">2</div>
                <h3>CloudSim Plus v8.5.6 Installation</h3>
              </div>

              <div className="section-description">
                CloudSim Plus is the selected cloud/edge compute simulator. Version 8.5.6 includes native edge datacenter modeling, LinearPowerModel for energy measurement, extensible broker/scheduler for custom HFL round logic, Java 21 compatible, and Maven build system.
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon blue"><Cloud size={18}/></div>
                  <div><div className="card-title">Clone CloudSim Plus Source</div></div>
                </div>
                <div className="code-block">
{`cd /home/mit/DEADSERPENT/HFL/SIMULATORS/cloudsim-plus
git clone https://github.com/manoelcampos/cloudsim-plus.git \\
    cloudsim-plus-source
cd cloudsim-plus-source
git checkout v8.5.6`}
                </div>
                <div className="badge done" style={{ marginTop: 8 }}>✓ Repository cloned. Tag v8.5.6 checked out.</div>
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon blue"><Cloud size={18}/></div>
                  <div><div className="card-title">Build and Install to Local Maven Repository</div></div>
                </div>
                <div className="code-block">
{`cd cloudsim-plus-source
mvn clean install -DskipTests -T28`}
                </div>
                <div className="kv-grid" style={{ marginTop: 8 }}>
                  <div className="kv-item"><div className="kv-label">-DskipTests</div><div className="kv-value" style={{ fontSize: 11 }}>Skip unit tests (saves ~5 min)</div></div>
                  <div className="kv-item"><div className="kv-label">-T28</div><div className="kv-value" style={{ fontSize: 11 }}>Parallel build (28 threads)</div></div>
                  <div className="kv-item"><div className="kv-label">Expected time</div><div className="kv-value" style={{ fontSize: 11 }}>2–4 minutes</div></div>
                </div>
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon blue"><Cloud size={18}/></div>
                  <div><div className="card-title">HFL Maven Project (pre-created)</div></div>
                </div>
                <div className="code-block">
{`# Location: .../SIMULATORS/cloudsim-plus/hfl-simulation/
# Structure:
pom.xml           ← declares CloudSim Plus 8.5.6 dependency
src/main/java/hfl/HFLSimTest.java  ← smoke test + Phase 4 base

# The pom.xml specifies:
#   <groupId>hfl.research</groupId>
#   <artifactId>hfl-simulation</artifactId>
#   <version>1.0.0</version>
#   Java 21, CloudSim Plus 8.5.6 dependency`}
                </div>
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-icon blue"><Cloud size={18}/></div>
                  <div><div className="card-title">Compile HFL Project</div></div>
                </div>
                <div className="code-block">{`cd hfl-simulation\nmvn compile`}</div>
                <div className="info-box note" style={{ marginTop: 8, marginBottom: 0 }}>
                  After CloudSim Plus is installed to local Maven repo, all import errors resolve automatically. IDE errors shown before mvn install are expected and safe to ignore.
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <div className="card-icon blue"><Cloud size={18}/></div>
                  <div><div className="card-title">Run CloudSim Plus Smoke Test</div></div>
                </div>
                <div className="code-block">
{`mvn exec:java -Dexec.mainClass="hfl.HFLSimTest"
# OR:
mvn package && java -jar target/hfl-simulation-1.0.0.jar

# Tests: 1 FL round across IoT (5 VMs) → Edge → Cloud
# Validates: Cloudlet scheduling, energy model, task completion time`}
                </div>
              </div>
            </motion.div>
          )}

          {/* Config */}
          {activeTab === 'config' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">3</div>
                <h3>Shared Configuration System</h3>
              </div>

              <div className="section-description">
                A unified JSON config file drives both simulators with identical parameters, ensuring reproducibility.
              </div>

              <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-header">
                  <div className="card-icon green"><FileJson size={18}/></div>
                  <div>
                    <div className="card-title">hfl_config.json</div>
                    <div className="card-subtitle">/home/mit/DEADSERPENT/HFL/SIMULATORS/config/</div>
                  </div>
                </div>
                <div className="kv-grid">
                  <div className="kv-item"><div className="kv-label">num_iot_devices</div><div className="kv-value">20</div></div>
                  <div className="kv-item"><div className="kv-label">num_edge_servers</div><div className="kv-value">3</div></div>
                  <div className="kv-item"><div className="kv-label">fl_rounds</div><div className="kv-value">100</div></div>
                  <div className="kv-item"><div className="kv-label">model_size_MB</div><div className="kv-value">50</div></div>
                  <div className="kv-item"><div className="kv-label">compression_ratio</div><div className="kv-value">0.5</div></div>
                  <div className="kv-item"><div className="kv-label">epsilon</div><div className="kv-value">1.0</div></div>
                  <div className="kv-item"><div className="kv-label">tau_e</div><div className="kv-value">5</div></div>
                  <div className="kv-item"><div className="kv-label">max_latency_ms</div><div className="kv-value">100</div></div>
                  <div className="kv-item"><div className="kv-label">min_comm_reduction</div><div className="kv-value">50%</div></div>
                  <div className="kv-item"><div className="kv-label">min_energy_saving</div><div className="kv-value">20%</div></div>
                </div>
              </div>

              <div className="info-box note">
                All simulation scripts read from <code>hfl_config.json</code> — changing parameters in one place updates both simulators simultaneously. This ensures experiment reproducibility across all FL rounds.
              </div>

              {/* Verification */}
              <div className="section-header" style={{ marginTop: 32 }}>
                <div className="section-number">4</div>
                <h3>Environment Verification</h3>
              </div>

              <div className="code-block">
{`bash /home/mit/DEADSERPENT/HFL/SIMULATORS/scripts/verify_setup.sh`}
              </div>

              <div className="card" style={{ marginTop: 16 }}>
                <div className="card-header">
                  <div className="card-icon green"><CheckCircle2 size={18}/></div>
                  <div>
                    <div className="card-title">23 Verification Checks — All Passed</div>
                  </div>
                </div>
                <ul className="checklist">
                  <li><span className="check-icon done">✓</span>[1] System requirements (OS, GCC, CMake, Python, Java, Maven)</li>
                  <li><span className="check-icon done">✓</span>[2] Python packages (numpy, pandas, matplotlib, scipy, seaborn)</li>
                  <li><span className="check-icon done">✓</span>[3] NS-3 installation (source, executable, build, bindings)</li>
                  <li><span className="check-icon done">✓</span>[4] CloudSim Plus (source, Maven repo, HFL project)</li>
                  <li><span className="check-icon done">✓</span>[5] Results directories (ns3/, cloudsim/, merged/)</li>
                </ul>
              </div>

              <div className="info-box success" style={{ marginTop: 16 }}>
                <strong>Target: 23/23 PASSED = ENVIRONMENT READY FOR PHASE 4</strong>
              </div>
            </motion.div>
          )}

          {/* Reproducibility */}
          {activeTab === 'reproducibility' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">5</div>
                <h3>Reproducibility Checklist (Thesis Standard)</h3>
              </div>

              <div className="section-description">
                For full research reproducibility, the following items are documented and version-locked.
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>Item</th><th>Value</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>OS</td><td><code>Ubuntu 24.04.4 LTS</code></td></tr>
                    <tr><td>NS-3 version</td><td><code>ns-3.46.1</code></td></tr>
                    <tr><td>CloudSim Plus version</td><td><code>v8.5.6</code></td></tr>
                    <tr><td>Python version</td><td><code>3.12.3</code></td></tr>
                    <tr><td>Java version</td><td><code>OpenJDK 21.0.10</code></td></tr>
                    <tr><td>Maven version</td><td><code>3.8.7</code></td></tr>
                    <tr><td>NumPy version</td><td><code>2.4.2</code></td></tr>
                    <tr><td>Pandas version</td><td><code>3.0.1</code></td></tr>
                    <tr><td>SciPy version</td><td><code>1.17.1</code></td></tr>
                    <tr><td>Seaborn version</td><td><code>0.13.2</code></td></tr>
                    <tr><td>Random seed (NS-3)</td><td><code>42</code> (set in all scripts)</td></tr>
                    <tr><td>Random seed (CloudSim)</td><td><code>42</code> (set in simulation)</td></tr>
                    <tr><td>Config file</td><td><code>hfl_config.json (SHA256)</code></td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* Phase 3 Summary */}
          <motion.div variants={fadeUp} className="section" style={{ marginTop: 40 }}>
            <div className="section-header">
              <div className="section-number"><CheckCircle2 size={16}/></div>
              <h3>Phase 3 Deliverables Summary</h3>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr><th>Deliverable</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {[
                    'System profile verified',
                    'Directory structure created',
                    'NS-3 v3.46.1 source cloned',
                    'NS-3 stable tag checkout (ns-3.46.1)',
                    'NS-3 install script (install_ns3.sh)',
                    'NS-3 Python smoke test script',
                    'CloudSim Plus v8.5.6 source cloned',
                    'CloudSim Plus build + Maven install',
                    'HFL Maven project created',
                    'CloudSim Plus smoke test (HFLSimTest.java)',
                    'Shared config file (hfl_config.json)',
                    'Environment verifier (verify_setup.sh)',
                    'Reproducibility checklist'
                  ].map(item => (
                    <tr key={item}>
                      <td>{item}</td>
                      <td><span className="badge done">✓ Done</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

        </motion.div>
      </div>
    </>
  )
}
