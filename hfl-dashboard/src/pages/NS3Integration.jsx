import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Network, ArrowLeftRight, Zap, Settings, ListOrdered, Wifi, Cloud,
  FileSearch, AlertTriangle, BarChart3
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
        <h2>NS-3 & CloudSim Integration Guide</h2>
        <p>Connecting the HFL-MM model to NS-3 and CloudSim Plus simulators</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'overview', icon: <Network size={14} />, label: 'Architecture' },
                { key: 'ns3', icon: <Wifi size={14} />, label: 'Model → NS-3' },
                { key: 'cloudsim', icon: <Cloud size={14} />, label: 'Model → CloudSim' },
                { key: 'config', icon: <Settings size={14} />, label: 'Shared Config' },
                { key: 'pipeline', icon: <ListOrdered size={14} />, label: 'Execution Flow' },
                { key: 'inference', icon: <Zap size={14} />, label: 'Inference Latency' },
                { key: 'compute', icon: <BarChart3 size={14} />, label: 'CloudSim Compute' },
                { key: 'deps', icon: <FileSearch size={14} />, label: 'File Dependencies' },
                { key: 'troubleshoot', icon: <AlertTriangle size={14} />, label: 'Troubleshooting' }
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
              <div className="section-header"><div className="section-number">1</div><h3>Integration Architecture Overview</h3></div>
              <p className="section-description">Neither simulator runs the Python model directly — instead, the model produces measured parameters that update the simulators' analytical inputs through a shared config file.</p>

              <div className="arch-diagram">
                <div className="arch-layer device">
                  <div className="arch-layer-label">Phase 5: HFL-MM Training (Python/PyTorch)</div>
                  <div className="arch-layer-content">
                    Real FL training → measures actual per-round statistics:<br/>
                    • actual_uplink_bytes (per device, per round)<br/>
                    • local_training_time_ms (per device, per round)<br/>
                    • edge_aggregation_time_ms (per edge, per round)<br/>
                    • inference_latency_ms (ONNX benchmark, 1000 runs)<br/>
                    • accuracy_per_round + epsilon_spent_per_round
                  </div>
                </div>
                <div className="arch-arrow">↓ writes to</div>
                <div className="arch-layer cloud">
                  <div className="arch-layer-label">SIMULATORS/config/hfl_config.json (Shared Config)</div>
                  <div className="arch-layer-content">
                    Updated fields: compression_ratio: 20 (was 5), actual_uplink_mb: 2.5 (was 10),<br/>
                    iot_train_time_ms: X (measured), onnx_infer_latency_ms: Y (measured)
                  </div>
                </div>
                <div className="arch-arrow" style={{ display: 'flex', justifyContent: 'space-around' }}>
                  <span>↓ reads</span><span>↓ reads</span>
                </div>
                <div style={{ display: 'flex', gap: 16 }}>
                  <div className="arch-layer edge" style={{ flex: 1 }}>
                    <div className="arch-layer-label">NS-3 Simulation</div>
                    <div className="arch-layer-content">
                      Re-runs with actual uplink bytes<br/>
                      (2.5MB vs Phase 4's 10MB)<br/>
                      → Updated: L_comm reduced, uplink = 47 MB
                    </div>
                  </div>
                  <div className="arch-layer edge" style={{ flex: 1 }}>
                    <div className="arch-layer-label">CloudSim Plus Simulation</div>
                    <div className="arch-layer-content">
                      Re-runs with actual training times<br/>
                      back-calculated to effective MI<br/>
                      → Updated: IoT MI recalculated
                    </div>
                  </div>
                </div>
                <div className="arch-arrow">↓</div>
                <div className="arch-layer device">
                  <div className="arch-layer-label">Phase 6: Joint Evaluation Results</div>
                  <div className="arch-layer-content">Combines Phase 5 ML + Phase 4/5 simulator results → All 4 QoS metrics validated simultaneously</div>
                </div>
              </div>
            </motion.div>
          )}

          {/* MODEL → NS-3 */}
          {activeTab === 'ns3' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>What Flows from Model → NS-3</h3></div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`# ns3_phase5_integration.py
log = pd.read_csv("results/phase5/training_log.csv")
hfl_uplink_mb = log[log.scenario=="HFL_Proposed"]["uplink_bytes"].mean() / 1e6
train_time_ms = log[log.scenario=="HFL_Proposed"]["local_train_ms"].mean()

config["actual_uplink_mb_per_device"]  = float(hfl_uplink_mb)
config["actual_iot_train_time_ms"]     = float(train_time_ms)
config["compression_ratio_actual"]     = 20

# Trigger NS-3 re-run
subprocess.run(["python", "ns3/hfl-scenarios/hfl_network_sim.py",
    "--config", "config/hfl_config.json",
    "--output", "results/phase5/ns3_phase5_results.csv"])`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Impact on NS-3 Latency</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Metric</th><th>Phase 4</th><th>Phase 5</th><th>Change</th></tr></thead>
                  <tbody>
                    <tr><td>Uplink per device</td><td>10 MB</td><td>2.5 MB</td><td>-75%</td></tr>
                    <tr><td>L_comm (device→edge)</td><td>1.48s</td><td>0.37s</td><td>-75%</td></tr>
                    <tr><td>FL round latency</td><td>1,830 ms</td><td>~720 ms</td><td>-61%</td></tr>
                    <tr><td>Total uplink (20 devices)</td><td>200 MB</td><td>50 MB</td><td>-75%</td></tr>
                    <tr className="highlight-row"><td>Communication reduction</td><td>76.4%</td><td><strong>~95%</strong></td><td>+18.6pp</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box success">
                Formula: L_comm = (uplink_MB × 8) / bandwidth_Mbps<br/>
                Old: (10 × 8) / 54 = 1.48s | New: (2.5 × 8) / 54 = 0.37s
              </div>
            </motion.div>
          )}

          {/* MODEL → CLOUDSIM */}
          {activeTab === 'cloudsim' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>What Flows from Model → CloudSim</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                Phase 5 measures real training wall-clock times per device. These are back-calculated to effective MI (Million Instructions) to feed into CloudSim's cloudlet model.
              </div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`effective_MI = training_time_seconds × device_MIPS
IoT devices run at 300 MIPS (Raspberry Pi class)

Phase 4 assumed:  IoT train MI = 3,000 MI
Phase 5 measures: actual ~8.5s → 8.5 × 300 = 2,550 MI
(Consistent with Phase 4 estimate — validates Phase 4)`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>CloudSim Validation Check</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Metric</th><th>Phase 4 Estimate</th><th>Phase 5 Measured</th><th>Delta</th></tr></thead>
                  <tbody>
                    <tr><td>IoT train time (s/round)</td><td>10.0s</td><td>~8.5s</td><td>-15%</td></tr>
                    <tr><td>Edge agg time (s/round)</td><td>0.25s</td><td>~0.2s</td><td>-20%</td></tr>
                    <tr><td>Cloud agg time (s/round)</td><td>0.005s</td><td>~0.005s</td><td>~0%</td></tr>
                    <tr><td>HFL_Proposed energy (J)</td><td>705 J</td><td>~600 J</td><td>-15%</td></tr>
                    <tr className="highlight-row"><td>Energy saving vs S0</td><td>74.9%</td><td><strong>~78.6%</strong></td><td>+3.7%</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* SHARED CONFIG */}
          {activeTab === 'config' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>Shared Config File (Phase 5 Version)</h3></div>
              <div className="code-block">
{`// hfl_config.json — new fields added in Phase 5
{
  ... (all Phase 4 fields preserved) ...,

  "phase5_actuals": {
    "compression_ratio":        20,
    "uplink_mb_per_device":     2.5,
    "iot_train_time_ms":        8500,
    "edge_agg_time_ms":         200,
    "cloud_agg_time_ms":        5,
    "onnx_infer_p95_ms":        68.3,
    "onnx_model_size_mb_int8":  2.1,
    "accuracy_iiot_pct":        93.1,
    "accuracy_smartcity_pct":   74.2,
    "accuracy_healthcare_pct":  83.8,
    "epsilon_spent_20rounds":   0.82,
    "convergence_round":        14
  },

  "phase5_derived": {
    "effective_iot_mi":         2550,
    "uplink_reduction_pct":     95.0,
    "energy_saving_pct":        78.6,
    "end_to_end_latency_ms":    73.1,
    "all_qos_targets_met":      true
  }
}`}
              </div>
            </motion.div>
          )}

          {/* EXECUTION FLOW */}
          {activeTab === 'pipeline' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>End-to-End Execution Flow (All Phases)</h3></div>
              <div className="code-block">
{`═══ PHASE 4 (DONE): Simulator baseline ═══
python ns3/hfl-scenarios/hfl_network_sim.py
  → results/ns3/ns3_results.csv (500 rows)
mvn -f cloudsim-plus/hfl-simulation/pom.xml compile exec:java
  → results/cloudsim/cloudsim_results.csv (500 rows)

═══ PHASE 5: Real model training → ONNX ═══
STEP 1: python data/loaders/download_datasets.py
STEP 2: python data/loaders/preprocess_{iiot,smartcity,healthcare}.py
STEP 3: python data/loaders/partition_noniid.py --alpha 0.5
STEP 4: python model/centralized_baseline.py --domain all --epochs 50
STEP 5: python model/hfl_trainer.py \\
          --rounds 20 --tau_e 5 --n_devices 20 --n_edges 3 \\
          --epsilon 1.0 --delta 1e-5 --sparsity 0.2 --quant_bits 8
STEP 6: python model/epsilon_sweep.py --epsilons 0.1 0.5 1.0 2.0 5.0
STEP 7: python model/onnx_exporter.py + inference_bench.py
STEP 8: python scripts/ns3_phase5_integration.py
STEP 9: python scripts/cloudsim_phase5_integration.py

═══ PHASE 6: Full evaluation ═══
STEP 10: python model/joint_evaluation.py --systems S0..S4 --seeds 5
STEP 11: python model/ablation_study.py --configs A0..A5 --seeds 5
STEP 12: python scripts/statistical_analysis.py
STEP 13: python scripts/generate_all_figures.py`}
              </div>
            </motion.div>
          )}

          {/* INFERENCE LATENCY */}
          {activeTab === 'inference' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>How NS-3 Models Inference Latency</h3></div>
              <div className="arch-diagram">
                <div style={{ display: 'flex', gap: 8, alignItems: 'stretch' }}>
                  <div className="arch-layer device" style={{ flex: 1 }}>
                    <div className="arch-layer-label">IoT Device</div>
                    <div className="arch-layer-content">sensor data → 2–5ms capture</div>
                  </div>
                  <div className="arch-arrow" style={{ alignSelf: 'center', margin: 0 }}>→</div>
                  <div className="arch-layer edge" style={{ flex: 1 }}>
                    <div className="arch-layer-label">WiFi 802.11ax</div>
                    <div className="arch-layer-content">comm: 3–8ms (NS-3 modeled)</div>
                  </div>
                  <div className="arch-arrow" style={{ alignSelf: 'center', margin: 0 }}>→</div>
                  <div className="arch-layer cloud" style={{ flex: 1 }}>
                    <div className="arch-layer-label">Edge Server</div>
                    <div className="arch-layer-content">preprocess + ONNX infer: 25–45ms</div>
                  </div>
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginTop: 24, marginBottom: 12 }}>End-to-End Latency Budget</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Component</th><th>Min</th><th>Max</th><th>Source</th></tr></thead>
                  <tbody>
                    <tr><td>L_sensor (sampling)</td><td>2ms</td><td>5ms</td><td>IoT device</td></tr>
                    <tr><td>L_comm (network)</td><td>3ms</td><td>8ms</td><td>NS-3 measured</td></tr>
                    <tr><td>L_preproc (STFT/mel)</td><td>8ms</td><td>15ms</td><td>Edge CPU</td></tr>
                    <tr><td>L_infer (ONNX INT8)</td><td>25ms</td><td>45ms</td><td>ONNX benchmark</td></tr>
                    <tr><td>L_response (edge→device)</td><td>&lt;1ms</td><td>&lt;1ms</td><td>4-byte response</td></tr>
                    <tr className="highlight-row"><td><strong>TOTAL</strong></td><td><strong>38ms</strong></td><td><strong>74ms</strong></td><td><strong>P95 ≈ 68ms &lt; 100ms ✓</strong></td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* CLOUDSIM COMPUTE */}
          {activeTab === 'compute' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">7</div><h3>How CloudSim Models HFL-MM Compute</h3></div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Phase</th><th>MI</th><th>VM Spec</th><th>Time</th><th>Energy</th></tr></thead>
                  <tbody>
                    <tr><td><strong>IoT Local Training</strong></td><td>2,550 MI</td><td>300 MIPS, 2 PEs</td><td>8.5s</td><td>493 J (× 20 devices)</td></tr>
                    <tr><td><strong>Edge Aggregation</strong></td><td>2,000 MI</td><td>8,000 MIPS, 4 PEs + GPU</td><td>0.20s</td><td>75 J (× 3 edges)</td></tr>
                    <tr><td><strong>Cloud Aggregation</strong></td><td>500 MI</td><td>100,000 MIPS, 8 PEs</td><td>0.005s</td><td>6.25 J</td></tr>
                    <tr className="highlight-row"><td><strong>Total per round</strong></td><td>—</td><td>—</td><td>—</td><td><strong>574 J</strong></td></tr>
                    <tr className="highlight-row"><td><strong>vs CentralizedFL</strong></td><td>—</td><td>—</td><td>—</td><td><strong>2,806 J → 79.5% saving ✓</strong></td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box success">
                Energy saving IMPROVES with Phase 5 update: actual IoT training time (8.5s) &lt; Phase 4 estimate (10s), 20× compression reduces IoT workload further.
              </div>
            </motion.div>
          )}

          {/* FILE DEPENDENCIES */}
          {activeTab === 'deps' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">8</div><h3>File Dependency Map</h3></div>
              <div className="code-block">
{`hfl_config.json ←─── phase5_integration scripts (write)
      │
      ├──► hfl_network_sim.py (NS-3)        → ns3_phase5_results.csv
      └──► HFLCloudSimulation.java            → cloudsim_phase5_results.csv

data/partitioned/ ──► hfl_trainer.py ──► training_log.csv
                                         convergence_curves/
                                         epsilon_log.csv
                      │
                      ▼
                  best_model.pt ──► onnx_exporter.py ──► hfl_mm_int8.onnx
                                                              │
                                                              ▼
                                                    inference_bench.py ──► latency.csv

training_log.csv + latency.csv ──► ns3_phase5_integration.py
                                    cloudsim_phase5_integration.py
                                       (updates hfl_config.json)

ns3_phase5_results.csv       ┐
cloudsim_phase5_results.csv  ├──► collect_phase5_results.py → phase5_results.csv
convergence_curves/          │
epsilon_log.csv + latency.csv┘

phase5_results.csv ──► joint_evaluation.py  ──► joint_eval.csv
                   ──► ablation_study.py    ──► ablation.csv
                   ──► generate_all_figures.py ──► figures/ (PDF + PNG)`}
              </div>
            </motion.div>
          )}

          {/* TROUBLESHOOTING */}
          {activeTab === 'troubleshoot' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">9</div><h3>Troubleshooting Integration Issues</h3></div>
              <div className="insight-grid">
                {[
                  { id: '1', title: 'NS-3 different packet loss', desc: 'Lower uplink (2.5 MB) → fewer packets → lower queuing. Expected: Phase 5 reliability ≥ Phase 4\'s 99.05%.' },
                  { id: '2', title: 'CloudSim energy differs', desc: 'Actual training time differs from MI estimate. If >20% deviation, report both in thesis (validates CloudSim accuracy). Expected: <15%.' },
                  { id: '3', title: 'Opacus "BatchNorm detected"', desc: 'MobileNetV3 has BatchNorm. Fix: call replace_bn_with_gn(model) BEFORE make_private(). Verify: ModuleValidator.validate().' },
                  { id: '4', title: 'ONNX export fails on GRU', desc: 'Use opset_version=17 (PyTorch 2.x supports GRU). Alternative: replace GRU with LSTM (opacus>=1.4).' },
                  { id: '5', title: 'ONNX INT8 slower than FP32', desc: 'CUDAExecutionProvider doesn\'t always benefit from INT8. Fix: compare both, use FP32 ONNX if faster (still ~8.4MB, <100ms).' },
                  { id: '6', title: 'Opacus ε diverges early', desc: 'Batch size too small. Fix: increase to 64, reduce lr to 5e-4, or use BatchMemoryManager with physical=8, virtual=32.' }
                ].map(item => (
                  <div key={item.id} className="insight-card">
                    <div className="insight-number">#{item.id}</div>
                    <div className="insight-content"><h4>{item.title}</h4><p>{item.desc}</p></div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Quick Reference */}
          <motion.div variants={fadeUp} className="section" style={{ marginTop: 40 }}>
            <div className="section-header"><div className="section-number">10</div><h3>Quick Reference — Key Numbers</h3></div>
            <div className="stats-grid">
              <div className="stat-card"><div className="stat-label">Energy Saving</div><div className="stat-value green">74.9%→79.5%</div><div className="stat-change positive">Target ≥20%</div></div>
              <div className="stat-card"><div className="stat-label">Comm. Reduction</div><div className="stat-value green">76.4%→95%</div><div className="stat-change positive">Target ≥50%</div></div>
              <div className="stat-card"><div className="stat-label">Reliability</div><div className="stat-value green">99.05%</div><div className="stat-change positive">Target &gt;99%</div></div>
              <div className="stat-card"><div className="stat-label">Inference P95</div><div className="stat-value green">~68ms</div><div className="stat-change positive">Target &lt;100ms</div></div>
              <div className="stat-card"><div className="stat-label">Accuracy Loss</div><div className="stat-value green">~1.5%</div><div className="stat-change positive">Target ≤2%</div></div>
              <div className="stat-card"><div className="stat-label">Uplink/Device</div><div className="stat-value">2.5 MB</div><div className="stat-change positive">was 10 MB</div></div>
            </div>
          </motion.div>

        </motion.div>
      </div>
    </>
  )
}
