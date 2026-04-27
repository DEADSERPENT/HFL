import { motion } from 'framer-motion'
import { useState } from 'react'
import { Globe, Cloud, Building, Link, BarChart3, MapPin, CheckCircle2, FileCode2 } from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Phase2() {
  const [activeTab, setActiveTab] = useState('ns3')

  return (
    <>
      <div className="page-header">
        <h2>Phase 2 — Simulator Selection & Design</h2>
        <p>NS-3 and CloudSim Plus justification, simulation architecture, and integration model</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          {/* Stats */}
          <motion.div variants={fadeUp}>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Simulators Selected</div>
                <div className="stat-value green">2</div>
                <div className="stat-change positive">NS-3 + CloudSim Plus</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Integration Model</div>
                <div className="stat-value">Sequential</div>
                <div className="stat-change target">Decoupled</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Output Format</div>
                <div className="stat-value">CSV/JSON</div>
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
                { key: 'ns3', icon: <Globe size={14} />, label: 'NS-3 Justification' },
                { key: 'cloudsim', icon: <Cloud size={14} />, label: 'CloudSim Plus' },
                { key: 'architecture', icon: <Building size={14} />, label: 'Sim Architecture' },
                { key: 'integration', icon: <Link size={14} />, label: 'Integration' },
                { key: 'comparison', icon: <BarChart3 size={14} />, label: 'Comparison' }
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

          {/* NS-3 */}
          {activeTab === 'ns3' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">1</div>
                <h3>Why NS-3? — Research-Grade Justification</h3>
              </div>
              <div className="section-description">
                NS-3 (Network Simulator 3) is the de facto standard for academic network simulation and is mandatory for credible QoS validation in FL research.
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>Criterion</th><th>NS-3</th><th>Alternatives</th><th>Verdict</th></tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>Wireless channel fidelity</strong></td>
                      <td>Full PHY/MAC stack (WiFi 802.11, LTE, 5G NR)</td>
                      <td>OMNET++ (no built-in LTE), GNS3 (emulation only)</td>
                      <td><span className="badge wins">NS-3 wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>Packet-level accuracy</strong></td>
                      <td>True packet-level simulation with queuing, loss, delay models</td>
                      <td>Matlab (abstract only), NS2 (outdated)</td>
                      <td><span className="badge wins">NS-3 wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>Python interface</strong></td>
                      <td>PyBind11-based Python bindings (ns3-gym, direct API)</td>
                      <td>OMNET++ (C++ only), NS2 (TCL only)</td>
                      <td><span className="badge wins">NS-3 wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>FL research adoption</strong></td>
                      <td>Cited in HED-FL, RoPPFL, HCEF for network evaluation</td>
                      <td>—</td>
                      <td><span className="badge wins">Standard</span></td>
                    </tr>
                    <tr>
                      <td><strong>Open-source + reproducible</strong></td>
                      <td>BSD license, fully open</td>
                      <td>Qualnet (commercial)</td>
                      <td><span className="badge wins">NS-3 wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>Topology flexibility</strong></td>
                      <td>Star, mesh, tree, hybrid (exactly the 3-tier you need)</td>
                      <td>—</td>
                      <td><span className="badge wins">NS-3 wins</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="card" style={{ marginTop: 20 }}>
                <div className="card-header">
                  <div className="card-icon green"><Globe size={18}/></div>
                  <div>
                    <div className="card-title">What NS-3 Models in  Project</div>
                  </div>
                </div>
                <ul className="gap-list" style={{ listStyle: 'none' }}>
                  {[
                    'Device → Edge wireless link (WiFi 802.11ax or LTE-Advanced)',
                    'Edge → Cloud wired/fiber link (CSMA or point-to-point)',
                    'Packet loss, jitter, channel congestion under load',
                    'Uplink traffic volume per round (for ≥50% reduction measurement)',
                    'End-to-end latency (L_comm component of the <100ms target)',
                    'Reliability: % of model update packets successfully delivered (>99% target)'
                  ].map((item, i) => (
                    <li key={i} style={{ padding: '6px 0 6px 24px' }}>{item}</li>
                  ))}
                </ul>
              </div>
            </motion.div>
          )}

          {/* CloudSim Plus */}
          {activeTab === 'cloudsim' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">2</div>
                <h3>Why CloudSim Plus? — Research-Grade Justification</h3>
              </div>
              <div className="section-description">
                CloudSim Plus is the most actively maintained fork of the original CloudSim, purpose-built for modern edge-cloud research.
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>Criterion</th><th>CloudSim Plus</th><th>Alternatives</th><th>Verdict</th></tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>Edge computing support</strong></td>
                      <td>Native edge datacenter + VM modeling</td>
                      <td>Original CloudSim (cloud only, outdated), GreenCloud (limited)</td>
                      <td><span className="badge wins">CS+ wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>Energy modeling</strong></td>
                      <td>Built-in power models (LinearPowerModel, SquareRootPowerModel)</td>
                      <td>ECOVISOR (specialized), PeerSim (P2P focus)</td>
                      <td><span className="badge wins">CS+ wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>Task scheduling</strong></td>
                      <td>Custom broker + scheduler extensible in Java</td>
                      <td>EdgeCloudSim (CS+ based, less flexible)</td>
                      <td><span className="badge wins">CS+ wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>FL workload mapping</strong></td>
                      <td>Cloudlets = FL training tasks; VMs = edge/cloud nodes</td>
                      <td>—</td>
                      <td><span className="badge wins">Natural mapping</span></td>
                    </tr>
                    <tr>
                      <td><strong>Java + performance</strong></td>
                      <td>Java 17+; suitable for large-scale simulation</td>
                      <td>Python-based sims (slow for large scale)</td>
                      <td><span className="badge wins">CS+ wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>Active maintenance</strong></td>
                      <td>v8.x (2024), IEEE-cited, 600+ publications</td>
                      <td>CloudSim (last update 2013)</td>
                      <td><span className="badge wins">CS+ wins</span></td>
                    </tr>
                    <tr>
                      <td><strong>Reproducibility</strong></td>
                      <td>Maven/Gradle build, deterministic simulation</td>
                      <td>—</td>
                      <td><span className="badge wins">Thesis standard</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="card" style={{ marginTop: 20 }}>
                <div className="card-header">
                  <div className="card-icon blue"><Cloud size={18}/></div>
                  <div>
                    <div className="card-title">What CloudSim Plus Models in  Project</div>
                  </div>
                </div>
                <ul className="gap-list" style={{ listStyle: 'none' }}>
                  {[
                    'Edge server resource provisioning (CPU, RAM, bandwidth per VM)',
                    'FL round scheduling: local training → edge aggregation → cloud aggregation tasks',
                    'Computation energy: E_comp = κ · f² · C · D per device per round',
                    'Communication energy: E_comm = P_tx · t_tx + P_rx · t_rx',
                    'VM migration / dynamic clustering (for HED-FL-style edge grouping)',
                    'Total energy per training round (for ≥20% savings comparison)'
                  ].map((item, i) => (
                    <li key={i} style={{ padding: '6px 0 6px 24px' }}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="info-box note" style={{ marginTop: 20 }}>
                <strong>Note on EdgeCloudSim:</strong> EdgeCloudSim is a wrapper built on top of CloudSim, specifically designed for mobile edge computing. We recommend CloudSim Plus for maximum flexibility in customizing the HFL-specific scheduling logic, with EdgeCloudSim modules imported selectively where mobility models are needed.
              </div>
            </motion.div>
          )}

          {/* Simulation Architecture */}
          {activeTab === 'architecture' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">3</div>
                <h3>Dual-Simulator Architecture for HFL Evaluation</h3>
              </div>

              <div className="arch-diagram">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                  {/* NS-3 Side */}
                  <div className="arch-layer edge">
                    <div className="arch-layer-label"><Globe size={14} style={{marginRight:4}}/> NS-3 (Network Layer)</div>
                    <div className="arch-layer-content">
                      <p style={{ marginBottom: 8 }}><strong>Models:</strong></p>
                      <ul style={{ paddingLeft: 16, fontSize: 13 }}>
                        <li>3-tier topology (Device-Edge-Cloud)</li>
                        <li>WiFi 802.11ax (L1→L2)</li>
                        <li>LTE/5G (L1→L2)</li>
                        <li>CSMA (L2→L3)</li>
                        <li>Packet loss / jitter</li>
                        <li>Channel congestion</li>
                      </ul>
                      <p style={{ marginTop: 12, marginBottom: 8 }}><strong>Outputs:</strong></p>
                      <ul style={{ paddingLeft: 16, fontSize: 13 }}>
                        <li>Latency (ms)</li>
                        <li>Throughput (Mbps)</li>
                        <li>Packet loss rate (%)</li>
                        <li>Uplink traffic (MB)</li>
                        <li>Reliability (%)</li>
                      </ul>
                    </div>
                  </div>

                  {/* CloudSim Side */}
                  <div className="arch-layer cloud">
                    <div className="arch-layer-label"><Cloud size={14} style={{marginRight:4}}/> CloudSim Plus (Compute Layer)</div>
                    <div className="arch-layer-content">
                      <p style={{ marginBottom: 8 }}><strong>Models:</strong></p>
                      <ul style={{ paddingLeft: 16, fontSize: 13 }}>
                        <li>IoT Device VMs (Layer 1)</li>
                        <li>Edge Server VMs (Layer 2)</li>
                        <li>Cloud Datacenter (Layer 3)</li>
                        <li>FL Cloudlets (training tasks)</li>
                        <li>Energy power models</li>
                        <li>Task scheduler (HFL logic)</li>
                      </ul>
                      <p style={{ marginTop: 12, marginBottom: 8 }}><strong>Outputs:</strong></p>
                      <ul style={{ paddingLeft: 16, fontSize: 13 }}>
                        <li>Energy per round (J)</li>
                        <li>CPU utilization (%)</li>
                        <li>Task completion time (ms)</li>
                        <li>VM allocation efficiency</li>
                        <li>Cost per training round</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="arch-arrow" style={{ marginTop: 16 }}>↓ ↓</div>

                <div className="arch-layer device" style={{ marginTop: 8 }}>
                  <div className="arch-layer-label"><FileCode2 size={14} style={{marginRight:4}}/> Result Aggregator (Python Post-Processor)</div>
                  <div className="arch-layer-content">
                    Merge NS-3 + CloudSim output CSV/JSON logs → Compute composite QoS score → Generate plots (matplotlib/seaborn)
                  </div>
                </div>
              </div>

              {/* NS-3 Detailed Design */}
              <div className="section-header" style={{ marginTop: 32 }}>
                <div className="section-number">4</div>
                <h3>NS-3: Network Simulation Design</h3>
              </div>

              <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-header">
                  <div className="card-icon green"><MapPin size={18}/></div>
                  <div><div className="card-title">Topology: 3-Tier Hierarchical</div></div>
                </div>
                <div className="code-block">
                  <span className="comment">{'  [IoT Device Cluster A]          [IoT Device Cluster B]'}</span>{'\n'}
                  <span className="comment">{'   Dev-1  Dev-2  Dev-3             Dev-4  Dev-5  Dev-6'}</span>{'\n'}
                  <span className="string">{'     \\      |      /                 \\      |      /'}</span>{'\n'}
                  <span className="string">{'      WiFi 802.11ax/5GHz              LTE-A'}</span>{'\n'}
                  <span className="command">{'       [Edge Server 1]               [Edge Server 2]'}</span>{'\n'}
                  <span className="string">{'              \\                           /'}</span>{'\n'}
                  <span className="string">{'               Point-to-Point Link (1 Gbps fiber)'}</span>{'\n'}
                  <span className="command">{'                    [     CLOUD SERVER     ]'}</span>
                </div>
              </div>

              <div className="kv-grid">
                <div className="kv-item">
                  <div className="kv-label">L1→L2 WiFi</div>
                  <div className="kv-value" style={{ fontSize: 11 }}>YansWifiChannel + LogDistance</div>
                </div>
                <div className="kv-item">
                  <div className="kv-label">L1→L2 LTE</div>
                  <div className="kv-value" style={{ fontSize: 11 }}>LteHelper + EpcHelper</div>
                </div>
                <div className="kv-item">
                  <div className="kv-label">5G</div>
                  <div className="kv-value" style={{ fontSize: 11 }}>MmWave module extension</div>
                </div>
                <div className="kv-item">
                  <div className="kv-label">L2→L3</div>
                  <div className="kv-value" style={{ fontSize: 11 }}>PointToPoint 1Gbps, 5ms</div>
                </div>
              </div>

              <div className="table-container" style={{ marginTop: 20 }}>
                <table className="data-table">
                  <thead>
                    <tr><th>Metric</th><th>How Measured</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>End-to-end latency (ms)</td><td>FlowMonitor + timestamps</td></tr>
                    <tr><td>Uplink traffic volume (MB)</td><td>PacketSink byte counter</td></tr>
                    <tr><td>Packet loss rate (%)</td><td>FlowMonitor lost packets</td></tr>
                    <tr><td>Throughput (Mbps)</td><td>FlowMonitor rx bytes/sec</td></tr>
                    <tr><td>Update reliability (%)</td><td>ACK success rate</td></tr>
                  </tbody>
                </table>
              </div>

              {/* CloudSim Detailed Design */}
              <div className="section-header" style={{ marginTop: 32 }}>
                <div className="section-number">5</div>
                <h3>CloudSim Plus: Compute Simulation Design</h3>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>HFL Concept</th><th>CloudSim Plus Entity</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>IoT Device</td><td>VM (low MIPS: 100-500, 512MB RAM)</td></tr>
                    <tr><td>Edge Server</td><td>VM (medium MIPS: 4000-8000, 8GB RAM)</td></tr>
                    <tr><td>Cloud Server</td><td>Datacenter Host (high MIPS: 20000+)</td></tr>
                    <tr><td>FL Local Training</td><td>Cloudlet (length = ops per round)</td></tr>
                    <tr><td>Edge Aggregation</td><td>Cloudlet (aggregation task)</td></tr>
                    <tr><td>Cloud Aggregation</td><td>Cloudlet (global FedAvg task)</td></tr>
                    <tr><td>Training Round</td><td>Simulation clock tick / broker cycle</td></tr>
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: 20 }}>
                <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Datacenters Defined:</h4>
                <div className="kv-grid">
                  <div className="kv-item">
                    <div className="kv-label">DC1: IoT Layer</div>
                    <div className="kv-value" style={{ fontSize: 11 }}>20 hosts, 500 MIPS, 512MB, 10Mbps</div>
                  </div>
                  <div className="kv-item">
                    <div className="kv-label">DC2: Edge Layer</div>
                    <div className="kv-value" style={{ fontSize: 11 }}>3 hosts, 8000 MIPS, 16GB, 1Gbps</div>
                  </div>
                  <div className="kv-item">
                    <div className="kv-label">DC3: Cloud</div>
                    <div className="kv-value" style={{ fontSize: 11 }}>1 host, 100000 MIPS, 256GB, 10Gbps</div>
                  </div>
                </div>
              </div>

              <div style={{ marginTop: 20 }}>
                <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Energy Model:</h4>
                <div className="code-block">
                  <span className="comment">{'// LinearPowerModel: P = P_idle + (P_max - P_idle) × utilization'}</span>{'\n\n'}
                  <span className="command">IoT device</span>: <span className="string">P_idle = 0.5W, P_max = 2W</span> (battery-constrained){'\n'}
                  <span className="command">Edge server</span>: <span className="string">P_idle = 50W, P_max = 200W</span> (rack server){'\n'}
                  <span className="command">Cloud</span>: <span className="string">P_idle = 500W, P_max = 2000W</span> (data center){'\n\n'}
                  <span className="flag">E_total = Σ [ P(t) × Δt ] over all FL rounds</span>
                </div>
              </div>

              <div className="table-container" style={{ marginTop: 20 }}>
                <table className="data-table">
                  <thead>
                    <tr><th>Metric</th><th>Source</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>Energy per round (Joules)</td><td>PowerModel.getEnergyConsumed</td></tr>
                    <tr><td>Task completion time (sec)</td><td>Cloudlet.getFinishTime</td></tr>
                    <tr><td>CPU utilization (%)</td><td>Host.getCpuPercentUtilization</td></tr>
                    <tr><td>VM allocation success (%)</td><td>DatacenterBroker logs</td></tr>
                    <tr><td>Aggregation overhead (ms)</td><td>Cloudlet exec time diff</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* Integration */}
          {activeTab === 'integration' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">6</div>
                <h3>Simulator Integration Model (Loose Coupling)</h3>
              </div>

              <div className="info-box note">
                <strong>Strategy: Sequential Decoupled Integration (research standard)</strong> — NS-3 and CloudSim Plus run independently. They share data through structured output files (CSV/JSON). A Python Orchestrator merges results for joint analysis.
              </div>

              <div className="info-box warning" style={{ marginTop: 12 }}>
                <strong>Why Not Tight Coupling?</strong> Tight coupling (real-time co-simulation) is complex to implement and not required for academic validation. Sequential decoupling is used by HED-FL, RoPPFL, and HCEF papers — it is the accepted standard.
              </div>

              <h4 style={{ fontSize: 16, fontWeight: 700, marginTop: 24, marginBottom: 16 }}>Integration Workflow</h4>

              <div className="timeline">
                <div className="timeline-item completed">
                  <div className="timeline-title">Step 1: Define Scenario Parameters</div>
                  <div className="timeline-period">Shared config file (config.json)</div>
                  <div className="code-block" style={{ marginTop: 8 }}>
{`{
  "num_devices": 20,
  "num_edge_servers": 3,
  "fl_rounds": 100,
  "model_size_MB": 50,
  "compression_ratio": 0.5,
  "epsilon": 1.0,
  "tau_e": 5
}`}
                  </div>
                </div>
                <div className="timeline-item completed">
                  <div className="timeline-title">Step 2a: NS-3 Run</div>
                  <div className="timeline-content">
                    Simulate network traffic for all FL rounds → Output: <code>ns3_results.csv</code> [round, latency, uplink_MB, pkt_loss, reliability]
                  </div>
                </div>
                <div className="timeline-item completed">
                  <div className="timeline-title">Step 2b: CloudSim Run</div>
                  <div className="timeline-content">
                    Simulate compute + energy for all FL rounds → Output: <code>cloudsim_results.csv</code> [round, energy, cpu_util, task_time, vm_alloc_success]
                  </div>
                </div>
                <div className="timeline-item completed">
                  <div className="timeline-title">Step 3: Python Orchestrator (merge + analyze)</div>
                  <div className="code-block" style={{ marginTop: 8 }}>
{`merged_df = pd.merge(ns3_df, cloudsim_df, on='round')

# Compute composite metrics:
comm_reduction = (baseline_uplink - hfl_uplink) / baseline_uplink × 100
energy_saving  = (baseline_energy - hfl_energy) / baseline_energy × 100
latency_target = latency < 100 (ms)
reliability    = successful_updates / total × 100

# Generate: matplotlib / seaborn plots for thesis`}
                  </div>
                </div>
              </div>

              <h4 style={{ fontSize: 16, fontWeight: 700, marginTop: 32, marginBottom: 16 }}>Shared Parameters Across Simulators</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>Parameter</th><th>NS-3 Usage</th><th>CloudSim Usage</th></tr>
                  </thead>
                  <tbody>
                    <tr><td><code>num_devices</code></td><td>Node count</td><td>VM count (DC1)</td></tr>
                    <tr><td><code>model_size_MB</code></td><td>Packet payload</td><td>Cloudlet length</td></tr>
                    <tr><td><code>compression_ratio</code></td><td>Uplink size ×</td><td>Aggregation cost</td></tr>
                    <tr><td><code>tau_e</code></td><td>Round trigger</td><td>Phase 2 trigger</td></tr>
                    <tr><td><code>fl_rounds</code></td><td>Simulation time</td><td>Broker cycles</td></tr>
                    <tr><td><code>bandwidth (Mbps)</code></td><td>Channel capacity</td><td>VM BW attribute</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* Comparison */}
          {activeTab === 'comparison' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">7</div>
                <h3>Simulator Comparison Summary (Thesis Table)</h3>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>Dimension</th><th>NS-3</th><th>CloudSim Plus</th><th>Scope in  Project</th></tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>Simulation type</strong></td>
                      <td>Packet-level network</td>
                      <td>Discrete-event compute</td>
                      <td>Complementary</td>
                    </tr>
                    <tr>
                      <td><strong>Layer modeled</strong></td>
                      <td>Physical + MAC + Network</td>
                      <td>Application + Resource</td>
                      <td>Different layers</td>
                    </tr>
                    <tr>
                      <td><strong>Language</strong></td>
                      <td>C++ / Python bindings</td>
                      <td>Java</td>
                      <td>Separate runtimes</td>
                    </tr>
                    <tr>
                      <td><strong>Key output</strong></td>
                      <td>Latency, throughput, packet loss</td>
                      <td>Energy, CPU, task time</td>
                      <td>Merged for QoS analysis</td>
                    </tr>
                    <tr>
                      <td><strong>FL relevance</strong></td>
                      <td>Communication overhead measurement</td>
                      <td>Computation cost measurement</td>
                      <td>Both required</td>
                    </tr>
                    <tr className="highlight-row">
                      <td><strong>Validation target</strong></td>
                      <td>O1 (comm reduction) + O3 (latency)</td>
                      <td>O4 (energy)</td>
                      <td>O2 (privacy) validated analytically</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* Phase 2 Summary */}
          <motion.div variants={fadeUp} className="section" style={{ marginTop: 40 }}>
            <div className="section-header">
              <div className="section-number"><CheckCircle2 size={16}/></div>
              <h3>Phase 2 Deliverables Summary</h3>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr><th>Deliverable</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {[
                    'NS-3 selection + full justification',
                    'CloudSim Plus selection + full justification',
                    'NS-3 architecture design (topology, channels, metrics)',
                    'CloudSim Plus architecture design (entities, energy, scheduler)',
                    'Simulator integration model (decoupled + Python orchestrator)',
                    'Shared parameter mapping table',
                    'Thesis-ready comparison table'
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
