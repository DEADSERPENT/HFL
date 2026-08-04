import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Radio, Zap, Cpu, Settings, AlertTriangle,
  Server, Network, Timer, Shield
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function NS3Integration() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <>
      <div className="page-header">
        <h2>Simulator & Deployment Integration</h2>
        <p>NS-3 · CloudSim Plus · ONNX Runtime — what each owns, how they connect</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'overview', icon: <Settings size={14} />, label: 'Architecture' },
                { key: 'handoff', icon: <Network size={14} />, label: 'The Handoff' },
                { key: 'ns3', icon: <Radio size={14} />, label: 'NS-3' },
                { key: 'cloudsim', icon: <Server size={14} />, label: 'CloudSim Plus' },
                { key: 'onnx', icon: <Cpu size={14} />, label: 'ONNX Runtime' },
                { key: 'repro', icon: <Shield size={14} />, label: 'Reproducibility' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* ARCHITECTURE */}
          {activeTab === 'overview' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Why Three Tools, and What Each One Owns</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                The four objectives are not answerable by the same kind of evidence. Training measures utility; it cannot measure a wireless channel, a datacentre power draw, or a portable runtime's latency.
              </div>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Objective</th><th>Question</th><th>Owned By</th></tr></thead>
                  <tbody>
                    <tr><td><strong>O1</strong></td><td>Uplink traffic reduction</td><td>NS-3</td></tr>
                    <tr><td><strong>O2</strong></td><td>ε ≤ 1, accuracy loss ≤ 2pp</td><td>Training (PyTorch)</td></tr>
                    <tr><td><strong>O3a</strong></td><td>Inference latency &lt;100ms</td><td>ONNX Runtime</td></tr>
                    <tr><td><strong>O3b</strong></td><td>Update reliability &gt;99%</td><td>NS-3</td></tr>
                    <tr><td><strong>O4</strong></td><td>Energy saving per round</td><td>CloudSim Plus</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box success">
                <strong>NEITHER SIMULATOR RUNS THE MODEL.</strong> Training produces measured per-round quantities; the simulators consume those quantities as inputs. This keeps the division honest: a network simulator that also "trained" the model would report its own assumptions back as results.
              </div>
            </motion.div>
          )}

          {/* THE HANDOFF */}
          {activeTab === 'handoff' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>The Handoff — Data Flow Between Tools</h3></div>
              <div className="arch-diagram">
                <div className="arch-layer device">
                  <div className="arch-layer-label">Training (Python / PyTorch)</div>
                  <div className="arch-layer-content">
                    Measures per client per round: actual compressed uplink bytes, participating clients, rounds completed, ε spent<br/>
                    Writes: <code>results/phase5/proposed_&lt;dataset&gt;.csv</code>
                  </div>
                </div>
                <div className="arch-arrow">↓ measured bytes and topology</div>
                <div className="arch-layer edge">
                  <div className="arch-layer-label">NS-3 (Network Layer)</div>
                  <div className="arch-layer-content">
                    Models: device→edge wireless, edge→cloud backhaul, queuing, loss<br/>
                    Writes: <code>results/phase5/ns3_&lt;dataset&gt;.csv</code>
                  </div>
                </div>
                <div className="arch-arrow">↓ topology and round counts</div>
                <div className="arch-layer cloud">
                  <div className="arch-layer-label">CloudSim Plus (Compute/Energy Layer)</div>
                  <div className="arch-layer-content">
                    Models: edge/cloud VMs, FL task scheduling, host power<br/>
                    Writes: <code>results/phase5/cloudsim_&lt;dataset&gt;.csv</code>
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'center', padding: '8px 0', color: 'var(--text-secondary)', fontSize: 13 }}>↓ exported model graph</div>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="kv-grid">
                  <div className="kv-item"><div className="kv-label">ONNX Runtime</div><div className="kv-value">End-to-end inference latency distribution → <code>results/phase5/latency_&lt;dataset&gt;.json</code></div></div>
                </div>
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>Ordering constraint:</strong> NS-3 and CloudSim consume the proposed run's CSV. Run them against a stale CSV and they report a previous run's uplink figure without complaint. <code>run_pipeline.py</code> encodes this dependency and REFUSES to run a stage whose inputs are missing.
              </div>
            </motion.div>
          )}

          {/* NS-3 */}
          {activeTab === 'ns3' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>NS-3 — Network Layer</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Version</div><div className="kv-value">v3.46.1</div></div>
                <div className="kv-item"><div className="kv-label">Path</div><div className="kv-value"><code>SIMULATORS/ns3/ns-3-dev/</code></div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Two Programs — Do Not Confuse</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Script</th><th>What It Is</th></tr></thead>
                  <tbody>
                    <tr><td><code>ns3/hfl-scenarios/hfl_network_sim.py</code></td><td><strong>PACKET-LEVEL simulation.</strong> Builds real 3-tier topology (802.11ax device→edge, P2P edge→cloud), TCP bulk transfers of actual compressed payload, FlowMonitor readback.</td></tr>
                    <tr><td><code>scripts/ns3_phase5_integration.py</code></td><td><strong>ANALYTICAL post-processor.</strong> No NS-3 calls. Rescales figures from measured payloads. NOT a network simulation — must never be reported as one.</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Build Requirement — Read Before Trusting Any Number</h4>
              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)', marginBottom: 16 }}>
                NS-3 source tree being present is NOT sufficient. Without a built tree the packet-level script falls back to an analytical path and still prints results under an NS-3 heading — <strong>an unbuilt environment produces plausible numbers that were never simulated.</strong>
              </div>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`cd ns3/ns-3-dev
./ns3 configure --enable-python-bindings
./ns3 build -j28
pip install cppyy    # required by the bindings

# v3.36+ API is FLAT: from ns import ns, then ns.NodeContainer
# The old ns.core / ns.network / ns.wifi namespaces no longer exist
# Check startup for: [OK] NS-3 packet-level bindings loaded from ...`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Reliability Is Per Update, Not Per Run</h4>
              <div className="info-box note">
                <code>per_update_reliability = P(one model update delivered)</code><br/>
                <code>whole_run_reliability = per_update ^ n_rounds</code><br/><br/>
                The objective (&gt;99% successful model updates) is about a single UPDATE. Reporting whole-run compound makes a healthy per-update rate look like a failure. The reported metric is per-update; field is named so it cannot be confused.
              </div>
            </motion.div>
          )}

          {/* CLOUDSIM */}
          {activeTab === 'cloudsim' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>CloudSim Plus — Compute & Energy Layer</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Version</div><div className="kv-value">v8.5.6</div></div>
                <div className="kv-item"><div className="kv-label">Path</div><div className="kv-value"><code>SIMULATORS/cloudsim-plus/hfl-simulation/</code></div></div>
                <div className="kv-item"><div className="kv-label">Entry</div><div className="kv-value"><code>hfl.HFLCloudSimulation</code></div></div>
                <div className="kv-item"><div className="kv-label">Maven</div><div className="kv-value"><code>org.cloudsimplus:cloudsimplus</code></div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>What It Models</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Cloudlets are FL training tasks; VMs are edge and cloud servers. Host power models convert utilisation into energy, attributed to device, edge and cloud layers separately.</p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Where the GPU Belongs</h4>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                GPU energy overhead applied to <strong>EDGE servers only</strong>. End devices are embedded-class monitors and wearables — no GPU. Charging GPU power to them inflates the baseline and therefore inflates the saving.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>API Notes (v8.5.6)</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="code-block">
{`PowerModelHostSimple requires staticPower >= 1.0 W
Cloudlet exposes getStartTime(), getFinishTime(), getLifeTime()
No getActualCpuTime() in this version`}
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Current Integration Status</h4>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>OPTIONAL stage.</strong> Not yet confirmed that the Java entry point accepts dataset name and round count in the form the driver passes them. Until verified, the stage may fail harmlessly and O4 will correctly report <strong>NOT MEASURED</strong>. Wiring the argument interface is a known outstanding item.
              </div>
            </motion.div>
          )}

          {/* ONNX RUNTIME */}
          {activeTab === 'onnx' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>ONNX Runtime — Deployment Layer</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Exporter</div><div className="kv-value"><code>model/deploy/onnx_exporter.py</code></div></div>
                <div className="kv-item"><div className="kv-label">Benchmark</div><div className="kv-value"><code>model/deploy/inference_bench.py</code></div></div>
                <div className="kv-item"><div className="kv-label">Artifact</div><div className="kv-value"><code>deploy/hfl_mm_&lt;dataset&gt;_fp32.onnx</code></div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Why ONNX Is Part of the Research</h4>
              <div className="info-box success" style={{ marginBottom: 16 }}>
                Objective 3 is about <strong>DEPLOYED</strong> inference. Latency inside the training framework, on the training machine, with training batch size and graph still attached, does not support that claim. ONNX is the third simulator — it owns an objective neither of the other two can answer.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Export Pipeline</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`checkpoint (best_<dataset>.pt)
  → build model from REGISTRY (shapes, class count)
  → load state_dict strict
  → torch.onnx.export, opset 17, dynamic batch axis
  → verify the exported graph actually runs
  → [optional] INT8 dynamic quantization`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>GroupNorm Shim — Numerical Check</h4>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 16 }}>
                A wrong shim exports successfully and yields a graph that computes something subtly different. Nothing raises — the deployed model simply predicts differently, permanently.<br/><br/>
                Regression test R3: PyTorch vs ONNX Runtime, identical inputs, max |diff| &lt; 1e-3 AND identical argmax.<br/>
                <strong>Measured:</strong> 4.5e-07 (VitalDB), 8.9e-07 (WEAR).
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>What Is Actually Timed</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description"><strong>End-to-end:</strong> preprocessing, inference, and conformal prediction-set construction + serialisation. Timing only the matrix multiply understates deployed latency.</p>
                <div className="kv-grid" style={{ marginTop: 12 }}>
                  <div className="kv-item"><div className="kv-label">Protocol</div><div className="kv-value">Warmup discarded → measured runs → P50, P95, P99</div></div>
                  <div className="kv-item"><div className="kv-label">Objective Metric</div><div className="kv-value">P95 (real-time guarantee is about the tail)</div></div>
                  <div className="kv-item"><div className="kv-label">Provider Rule</div><div className="kv-value">IoT claim = CPU provider. CUDA measures edge server (different question).</div></div>
                </div>
              </div>
            </motion.div>
          )}

          {/* REPRODUCIBILITY */}
          {activeTab === 'repro' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>Shared Configuration & Reproducibility</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Shared Config</div><div className="kv-value"><code>SIMULATORS/config/hfl_config.json</code></div></div>
                <div className="kv-item"><div className="kv-label">Registry</div><div className="kv-value"><code>SIMULATORS/data/loaders/datasets.py</code></div></div>
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Every run captures via <code>engineering/runctx.py</code>: git commit + dirty flag, seed, device + CUDA/cuDNN versions, package versions, full argv, and a DATASET FINGERPRINT (MD5 of label array + partition_meta.json).</p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Running It</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`# Everything, one command per dataset:
python scripts/run_pipeline.py --dataset vitaldb

# Inspect without running:     --dry-run
# List stages:                 --list
# Re-run one stage:            --force-stage ns3_network

# The driver is RESUMABLE: completed stages are skipped.
# Per-stage logs and manifest.json under results/pipeline/<dataset>/

# Score objectives:
python scripts/check_objectives.py --dataset vitaldb
# Reports NOT MEASURED for unrun experiments, never FAIL or PASS from defaults`}
              </div>
            </motion.div>
          )}

        </motion.div>
      </div>
    </>
  )
}
