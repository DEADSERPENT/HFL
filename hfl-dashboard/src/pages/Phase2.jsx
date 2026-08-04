import { motion } from 'framer-motion'
import { useState } from 'react'
import { Search, Server, BarChart3, CheckCircle2, Settings } from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Phase2() {
  const [activeTab, setActiveTab] = useState('selection')

  return (
    <>
      <div className="page-header">
        <h2>Phase 2 — Simulator Selection</h2>
        <p>NS-3 + CloudSim Plus + ONNX Runtime — why these three tools, and why not others</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box success" style={{ marginBottom: 16 }}>
              <strong>Status:</strong> COMPLETE — dual-simulator architecture selected and justified. Each objective is owned by exactly one tool.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'selection', icon: <Search size={14} />, label: 'Selection Criteria' },
                { key: 'ns3', icon: <Server size={14} />, label: 'NS-3 Selection' },
                { key: 'cloudsim', icon: <Settings size={14} />, label: 'CloudSim Plus' },
                { key: 'comparison', icon: <BarChart3 size={14} />, label: 'Alternatives' },
                { key: 'ownership', icon: <CheckCircle2 size={14} />, label: 'Objective Ownership' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {activeTab === 'selection' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Why Two Simulators</h3></div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">The four objectives are not answerable by the same tool. Network simulation models channels and bandwidth (O1, O3b). Compute simulation models energy (O4). Training measures accuracy and privacy (O2). Deployment runtime measures inference latency (O3a). One tool per objective, no objective answered by more than one.</p>
              </div>
              <div className="info-box note">
                <strong>Neither simulator runs the model.</strong> Training produces measured per-round quantities; simulators consume those as inputs. This keeps the division honest.
              </div>
            </motion.div>
          )}

          {activeTab === 'ns3' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>NS-3 v3.46.1 — Network Simulator</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Version</div><div className="kv-value">v3.46.1 (latest stable LTR as of Jan 2026)</div></div>
                <div className="kv-item"><div className="kv-label">Type</div><div className="kv-value">Packet-level discrete-event network simulator</div></div>
                <div className="kv-item"><div className="kv-label">Owns</div><div className="kv-value">O1 (uplink reduction), O3b (update reliability)</div></div>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Why NS-3</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  <li style={{ padding: '6px 0' }}>✓ Packet-level fidelity — models contention, loss, jitter at the frame level</li>
                  <li style={{ padding: '6px 0' }}>✓ WiFi 802.11ax, LTE-Advanced, 5G mmWave channel models</li>
                  <li style={{ padding: '6px 0' }}>✓ FlowMonitor for per-flow latency/throughput/loss statistics</li>
                  <li style={{ padding: '6px 0' }}>✓ Python bindings via cppyy (NOT PyBind11)</li>
                  <li style={{ padding: '6px 0' }}>✓ Open-source, reproducible, industry-standard</li>
                </ul>
              </div>
            </motion.div>
          )}

          {activeTab === 'cloudsim' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>CloudSim Plus v8.5.6 — Compute & Energy</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Version</div><div className="kv-value">v8.5.6</div></div>
                <div className="kv-item"><div className="kv-label">Type</div><div className="kv-value">Cloud/edge compute simulation (Java)</div></div>
                <div className="kv-item"><div className="kv-label">Owns</div><div className="kv-value">O4 (energy saving per round)</div></div>
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  <li style={{ padding: '6px 0' }}>✓ Built-in host power models (PowerModelHostSimple)</li>
                  <li style={{ padding: '6px 0' }}>✓ Cloudlet = FL training task, VM = edge/cloud server</li>
                  <li style={{ padding: '6px 0' }}>✓ Energy attributed per layer (device / edge / cloud)</li>
                  <li style={{ padding: '6px 0' }}>✓ Maven-based, reproducible builds</li>
                </ul>
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>Current status:</strong> Argument interface not yet verified. O4 reports NOT MEASURED until wired.
              </div>
            </motion.div>
          )}

          {activeTab === 'comparison' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>Alternatives Considered & Rejected</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Tool</th><th>Pros</th><th>Reason Rejected</th></tr></thead>
                  <tbody>
                    <tr><td>EdgeCloudSim</td><td>Combined edge-cloud</td><td>Coarser network model, less active maintenance</td></tr>
                    <tr><td>iFogSim</td><td>Fog computing focus</td><td>No packet-level WiFi simulation</td></tr>
                    <tr><td>LEAF (CMU)</td><td>FL-native</td><td>No network channel model at all</td></tr>
                    <tr><td>FedML</td><td>FL framework</td><td>Framework, not a network simulator — different layer</td></tr>
                    <tr><td>MATLAB Simulink</td><td>Integrated</td><td>Licence cost, not reproducible in open-source context</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {activeTab === 'ownership' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Objective → Tool Ownership</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Objective</th><th>Tool</th><th>What It Produces</th></tr></thead>
                  <tbody>
                    <tr><td>O1 — Uplink reduction</td><td>NS-3</td><td>Measured compressed uplink bytes vs centralised</td></tr>
                    <tr><td>O2 — Privacy + accuracy</td><td>PyTorch training</td><td>Live accountant ε, paired accuracy comparison</td></tr>
                    <tr><td>O3a — Inference latency</td><td>ONNX Runtime</td><td>P95 end-to-end latency, CPU provider</td></tr>
                    <tr><td>O3b — Update reliability</td><td>NS-3</td><td>Per-update delivery success rate</td></tr>
                    <tr><td>O4 — Energy saving</td><td>CloudSim Plus</td><td>Host power model, GPU to edge only</td></tr>
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
