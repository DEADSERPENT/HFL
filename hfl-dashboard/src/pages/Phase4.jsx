import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Radio, Server, Zap, BarChart3, AlertTriangle,
  CheckCircle2, Bug
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Phase4() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <>
      <div className="page-header">
        <h2>Phase 4 — Simulator Implementation</h2>
        <p>NS-3 network simulation, CloudSim Plus energy, measured QoS results</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box success" style={{ marginBottom: 16 }}>
              <strong>Status:</strong> CODE COMPLETE — NS-3 packet-level simulation + CloudSim Plus energy model implemented. Measured results on both datasets.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'overview', icon: <BarChart3 size={14} />, label: 'Architecture' },
                { key: 'ns3', icon: <Radio size={14} />, label: 'NS-3 Simulation' },
                { key: 'cloudsim', icon: <Server size={14} />, label: 'CloudSim Plus' },
                { key: 'uplink', icon: <Zap size={14} />, label: 'Uplink Results' },
                { key: 'reliability', icon: <CheckCircle2 size={14} />, label: 'Reliability' },
                { key: 'energy', icon: <Zap size={14} />, label: 'Energy Results' },
                { key: 'defects', icon: <Bug size={14} />, label: 'Defects Fixed' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {activeTab === 'overview' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Simulation Architecture</h3></div>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Simulator</th><th>File</th><th>Models</th><th>Output</th></tr></thead>
                  <tbody>
                    <tr><td><strong>NS-3</strong></td><td><code>hfl_network_sim.py</code></td><td>Latency, throughput, loss, reliability</td><td><code>ns3_results.csv</code></td></tr>
                    <tr><td><strong>CloudSim+</strong></td><td><code>HFLCloudSimulation.java</code></td><td>Energy, task completion, scheduling</td><td><code>cloudsim_results.csv</code></td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Five Comparison Scenarios</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Scenario</th><th>Topology</th><th>DP</th><th>Compression</th></tr></thead>
                  <tbody>
                    <tr><td>CentralizedFL</td><td>Flat (device→cloud)</td><td>No</td><td>None</td></tr>
                    <tr><td>FlatFL_NoDP</td><td>Flat</td><td>No</td><td>None</td></tr>
                    <tr><td>FlatFL_DP</td><td>Flat</td><td>Yes</td><td>None</td></tr>
                    <tr><td>HierarchicalFL_NoDP</td><td>Hierarchical</td><td>No</td><td>Top-k + quant</td></tr>
                    <tr className="highlight-row"><td><strong>HFL_Proposed</strong></td><td>Hierarchical</td><td>Yes</td><td>Top-k + quant + freeze</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box note">
                Device counts and model sizes come from the DATASET REGISTRY, never hardcoded. VitalDB: 9 clients / 2 edges / 7.46 MB model. WEAR: 22 clients / 2 edges / 15.70 MB model.
              </div>
            </motion.div>
          )}

          {activeTab === 'ns3' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>NS-3 Network Simulation Design</h3></div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Latency Decomposition</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`L_total = L_sensor + L_preproc + L_inference + L_comm + L_aggregation

L_sensor      ~ Uniform(2, 10) ms        sensor sampling jitter
L_preproc     ~ Uniform(10, 25) ms       data normalisation/windowing
L_inference   ~ Uniform(10, 50) ms       local model forward pass
L_aggregation = 15 ms (flat) / 35 ms (hierarchical, 2 hops)
L_comm        = bandwidth-limited (scenario-dependent, dominant term)`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Packet-Level Topology</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">
                  N IoT nodes ←[WiFi 802.11ax]→ Edge AP ←[P2P]→ Cloud. N and edge count from registry. Each edge cell gets its OWN wireless channel. BulkSendApplication carrying COMPRESSED payload. FlowMonitor reads per-flow throughput, loss, delay.
                </p>
              </div>

              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>Reliability is PER UPDATE, not per run:</strong><br/>
                <code>per_update = P(one model update delivered)</code><br/>
                <code>whole_run = per_update ^ n_rounds</code><br/>
                The objective (&gt;99%) is about a single update. Devices are placed on a disc of radius r around the AP, so path loss degrades SNR with distance.
              </div>
            </motion.div>
          )}

          {activeTab === 'cloudsim' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>CloudSim Plus Energy Model</h3></div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Three-Phase FL Scheduling</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Phase</th><th>Where</th><th>MI</th><th>PEs</th></tr></thead>
                  <tbody>
                    <tr><td>Local Training</td><td>IoT VMs (parallel)</td><td>15,000 (CPU) / 3,000 (compressed)</td><td>2/device</td></tr>
                    <tr><td>Edge Aggregation</td><td>Edge VMs (hier. only)</td><td>2,000/edge</td><td>4/edge</td></tr>
                    <tr><td>Cloud Aggregation</td><td>Cloud VM</td><td>500</td><td>8</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Analytical Energy Model</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`E_IoT   = [P_idle + (P_max - P_idle) × 0.9] × t_train × N_devices
E_Edge  = [P_idle + (P_max - P_idle) × 0.7 + GPU_overhead] × t_edge × N_edges
E_Cloud = [P_idle + (P_max - P_idle) × 0.5] × t_cloud

Power: IoT idle=1W/max=3W, Edge 50W/200W, Cloud 500W/2000W
GPU overhead: 30W, EDGE ONLY (IoT is 300-MIPS embedded, no GPU)`}
              </div>
            </motion.div>
          )}

          {activeTab === 'uplink' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>Measured Uplink Results (O1)</h3></div>

              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)', marginBottom: 16 }}>
                <strong>Key finding:</strong> Top-k indices (int32) cost 4× what quantized values (uint8) cost. Indices = 80% of transmitted bytes. Nominal "5××4× = 20×" overstates actual full-model compression by 6×. Measured full-model = 3.2×. Head-only = 13.3× (gain from what is trained, not the codec).
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Per-Client Per-Round (VitalDB, dense = 7.111 MB)</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Arm</th><th>Transmitted</th><th>Compression</th><th>Indices</th><th>Values</th></tr></thead>
                  <tbody>
                    <tr><td>Full model</td><td>2.250 MB</td><td>3.2×</td><td>1.799 MB</td><td>0.450 MB</td></tr>
                    <tr className="highlight-row"><td><strong>Head only</strong></td><td><strong>0.534 MB</strong></td><td><strong>13.3×</strong></td><td>0.427 MB</td><td>0.107 MB</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>System Uplink Per Round</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Dataset</th><th>Centralised</th><th>Full-Model</th><th>Head-Only</th></tr></thead>
                  <tbody>
                    <tr><td>VitalDB</td><td>64.00 MB</td><td>24.75 MB (−61.3%)</td><td style={{ color: 'var(--success)' }}><strong>5.87 MB (−90.8%)</strong></td></tr>
                    <tr><td>WEAR</td><td>329.47 MB</td><td>101.19 MB (−69.3%)</td><td style={{ color: 'var(--success)' }}><strong>12.91 MB (−96.1%)</strong></td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box success" style={{ marginTop: 16 }}>
                <strong>O1 (≥50% uplink reduction): PASS on both datasets.</strong> Passes even in the full-model arm. Head-only turns a comfortable margin into a large one.
              </div>
            </motion.div>
          )}

          {activeTab === 'reliability' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Measured Reliability & Delay (O3b)</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>VitalDB — cell radius 30m, 5 packet-level rounds/scenario</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Scenario</th><th>rx (MB)</th><th>Delay (ms)</th><th>Loss (%)</th><th>Reliability</th></tr></thead>
                  <tbody>
                    <tr><td>CentralizedFL</td><td>73.59</td><td>24.20</td><td>0.274±0.080</td><td>99.726%</td></tr>
                    <tr><td>FlatFL_NoDP</td><td>73.59</td><td>21.27</td><td>0.236±0.128</td><td>99.764%</td></tr>
                    <tr><td>FlatFL_DP</td><td>75.08</td><td>23.44</td><td>0.226±0.131</td><td>99.774%</td></tr>
                    <tr><td>HierarchicalFL_NoDP</td><td>5.52</td><td>17.90</td><td>0.000±0.000</td><td>100.000%</td></tr>
                    <tr className="highlight-row"><td><strong>HFL_Proposed</strong></td><td>5.68</td><td>17.26</td><td>0.000±0.000</td><td style={{ color: 'var(--success)' }}><strong>100.000%</strong></td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>WEAR — cell radius 30m, 5 packet-level rounds/scenario</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Scenario</th><th>rx (MB)</th><th>Delay (ms)</th><th>Loss (%)</th><th>Reliability</th></tr></thead>
                  <tbody>
                    <tr><td>CentralizedFL</td><td>284.63</td><td>39.21</td><td>0.485±0.113</td><td>99.515%</td></tr>
                    <tr><td>FlatFL_NoDP</td><td>293.01</td><td>35.74</td><td>0.497±0.079</td><td>99.503%</td></tr>
                    <tr><td>FlatFL_DP</td><td>287.00</td><td>40.44</td><td>0.545±0.127</td><td>99.455%</td></tr>
                    <tr><td>HierarchicalFL_NoDP</td><td>13.58</td><td>22.84</td><td>0.000±0.000</td><td>100.000%</td></tr>
                    <tr className="highlight-row"><td><strong>HFL_Proposed</strong></td><td>13.99</td><td>21.66</td><td>0.013±0.027</td><td style={{ color: 'var(--success)' }}><strong>99.987%</strong></td></tr>
                  </tbody>
                </table>
              </div>

              <div className="info-box success" style={{ marginBottom: 16 }}>
                <strong>O3b (&gt;99% reliability): PASS on all scenarios.</strong> Hierarchical arms reach target with zero or near-zero measured loss and 29–45% lower delay.
              </div>
              <div className="info-box note">
                <strong>Honest reading:</strong> All five architectures clear &gt;99% at this radius. The claim is NOT "only proposed system is reliable" — the proposed system reaches it with ZERO loss and lower delay. WEAR loss gap widens vs VitalDB as expected (20× vs 13× payload ratio).
              </div>
            </motion.div>
          )}

          {activeTab === 'energy' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>Energy Results (O4)</h3></div>
              <div className="stats-grid" style={{ marginBottom: 20 }}>
                <div className="stat-card"><div className="stat-label">VitalDB Saving</div><div className="stat-value green">72.3%</div></div>
                <div className="stat-card"><div className="stat-label">WEAR Saving</div><div className="stat-value green">76.8%</div></div>
                <div className="stat-card"><div className="stat-label">Target</div><div className="stat-value">≥20%</div></div>
                <div className="stat-card"><div className="stat-label">O4 Status</div><div className="stat-value green">PASS</div></div>
              </div>
              <div className="info-box note">
                GPU overhead (30W) charged to EDGE only. IoT devices are 300-MIPS embedded class with no GPU. HFL_Proposed benefit: compressed gradients → IoT trains 5× faster (3,000 vs 15,000 MI).
              </div>
            </motion.div>
          )}

          {activeTab === 'defects' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">7</div><h3>Defects Found & Fixed</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Defect</th><th>Impact</th><th>Fix</th></tr></thead>
                  <tbody>
                    <tr><td>B3</td><td>All cells shared one WiFi channel</td><td>Inter-cell interference absent → reliability inflated</td><td>Each edge AP gets own WifiChannel</td></tr>
                    <tr><td>B6</td><td>All nodes at (0,0,0)</td><td>Perfect channel → 100% reliability always → objective is a tautology</td><td>Devices placed on disc of radius r</td></tr>
                    <tr><td>B7</td><td>Reliability from rng.uniform() range</td><td>Same number (99.05%) on both datasets</td><td>Now from FlowMonitor rx/tx packets</td></tr>
                    <tr><td>B8</td><td>Uplink = model_size × sparsity</td><td>Restated compression ratio, not measured</td><td>Real compressor, real byte count</td></tr>
                    <tr><td>B9</td><td>Top-k sends 20% of all-zero encoder delta</td><td>Inflated uplink with zero-information traffic</td><td>Capped by non-zero entry count</td></tr>
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
