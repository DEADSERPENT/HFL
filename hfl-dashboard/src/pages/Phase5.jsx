import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Database, Layers, Shield, Shrink, Cpu,
  BarChart3, Zap, FileText
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Phase5() {
  const [activeTab, setActiveTab] = useState('scope')

  return (
    <>
      <div className="page-header">
        <h2>Phase 5 — Healthcare Dataset Integration & Model Implementation</h2>
        <p>Dataset pipeline, HFL-MM model, privacy engine, deployment, training results</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box success" style={{ marginBottom: 16 }}>
              <strong>Status:</strong> CODE COMPLETE — 13 deliverables (D5.1–D5.13). Healthcare-only scope finalised 2026-04-22. Runs pending on current datasets.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'scope', icon: <FileText size={14} />, label: 'Scope' },
                { key: 'datasets', icon: <Database size={14} />, label: 'Datasets' },
                { key: 'model', icon: <Layers size={14} />, label: 'HFL-MM-HC' },
                { key: 'privacy', icon: <Shield size={14} />, label: 'DP Engine' },
                { key: 'compression', icon: <Shrink size={14} />, label: 'Compression' },
                { key: 'deployment', icon: <Cpu size={14} />, label: 'ONNX Deploy' },
                { key: 'baselines', icon: <BarChart3 size={14} />, label: 'Baselines' },
                { key: 'results', icon: <Zap size={14} />, label: 'Results' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {activeTab === 'scope' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Scope & Objectives</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Domain Decision (Final 2026-04-22):</strong> Healthcare domain exclusively. Target venues: IEEE JBHI (Q1, IF ~7.7) and npj Digital Medicine (Q1, IF ~15.2).
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Phase 5 Closes Two Remaining Gaps</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Gap</th><th>Requires</th><th>Status</th></tr></thead>
                  <tbody>
                    <tr><td>Inference latency &lt;100ms</td><td>Real model + ONNX deployment</td><td style={{ color: '#F59E0B' }}>Apparatus built, run pending</td></tr>
                    <tr><td>Accuracy loss ≤2% at ε=1</td><td>Real FL training + DP-SGD</td><td style={{ color: '#F59E0B' }}>Apparatus built, run pending</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Deliverables (D5.1–D5.13)</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Deliverable</th><th>File</th></tr></thead>
                  <tbody>
                    <tr><td>D5.1</td><td>Dataset Pipeline</td><td><code>data/loaders/</code></td></tr>
                    <tr><td>D5.2</td><td>FedMamba-HC Encoder</td><td><code>model/fedmamba_hc.py</code></td></tr>
                    <tr><td>D5.3</td><td>FedConform-HC</td><td><code>model/fedconform_hc.py</code></td></tr>
                    <tr><td>D5.5</td><td>HFL-MM Model</td><td><code>model/hfl_mm_model.py</code></td></tr>
                    <tr><td>D5.6</td><td>Baseline Suite B0–B5</td><td><code>model/baselines.py</code></td></tr>
                    <tr><td>D5.7</td><td>HFL Training Engine</td><td><code>model/hfl_trainer.py</code></td></tr>
                    <tr><td>D5.8</td><td>DP-SGD Integration</td><td><code>model/dp_engine.py</code></td></tr>
                    <tr><td>D5.9</td><td>Gradient Compression</td><td><code>model/compression.py</code></td></tr>
                    <tr><td>D5.10</td><td>ONNX Edge Deployment</td><td><code>model/onnx_exporter.py</code></td></tr>
                    <tr><td>D5.12</td><td>ε Sweep</td><td><code>model/epsilon_sweep.py</code></td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {activeTab === 'datasets' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>Healthcare Datasets</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Upgrade decision (2026-04-22):</strong> WESAD → PTB-XL (1000× more data), ChestXray14 → CheXpert (better clinical labels). However, <strong>actual implementation uses VitalDB + WEAR</strong> (genuinely paired multimodal data, see Datasets page).
              </div>

              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Dataset</th><th>Role</th><th>Modalities</th><th>Task</th></tr></thead>
                  <tbody>
                    <tr><td><strong>VitalDB</strong></td><td>Primary clinical evidence</td><td>9 physiological signals + 34 clinical features</td><td>Binary ICU admission prediction</td></tr>
                    <tr><td><strong>WEAR</strong></td><td>Pipeline iteration / debug</td><td>12 inertial channels + 2048 video features</td><td>18-class activity recognition</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Deployment Topology</h4>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">VitalDB</div><div className="kv-value">9 clients (surgical specialties) / 2 edges / ICU rate 3.2%–50.7%</div></div>
                <div className="kv-item"><div className="kv-label">WEAR</div><div className="kv-value">22 clients (subjects) / 2 edges / balanced 18-class</div></div>
              </div>
            </motion.div>
          )}

          {activeTab === 'model' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>HFL-MM-HC Architecture</h3></div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`modality A ──> FedMamba-HC (1D conv + biGRU) ──> 256-d ─┐
                                                         ├─> LateFusionHead
modality B ──> FeatureEncoder (MLP)          ──> 576-d ──┘       │
                                                                  v
                                                              n_classes
FedConform-HC wrapper → calibrated prediction sets`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Parameter Counts</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Dataset</th><th>Total</th><th>encoder_a</th><th>encoder_b</th><th>Head (DP-trained)</th></tr></thead>
                  <tbody>
                    <tr><td>VitalDB</td><td>1,864,227</td><td>674,913</td><td>629,440</td><td>559,874 (30.0%)</td></tr>
                    <tr><td>WEAR</td><td>3,925,875</td><td>670,113</td><td>2,691,776</td><td>563,986 (14.4%)</td></tr>
                  </tbody>
                </table>
              </div>

              <div className="info-box note">
                GroupNorm throughout (no BatchNorm — DP-SGD requires per-sample gradients). <code>build_hfl_mm_hc()</code> raises if any BatchNorm survives.
              </div>
            </motion.div>
          )}

          {activeTab === 'privacy' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>DP-SGD Integration</h3></div>
              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Head-Only DP Fine-Tuning</h4>
                <div className="code-block" style={{ marginBottom: 12 }}>
{`1. Pretrain encoders non-privately (pretrain_encoders.py)
2. FREEZE both encoders
3. DP-train ONLY the fusion head, federated
4. Conformal calibration budget composed into total ε`}
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>ε Sweep Design</h4>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>Budget ε</th><th>Purpose</th></tr></thead>
                  <tbody>
                    <tr><td>0.1</td><td>Extreme privacy — survival test</td></tr>
                    <tr><td>0.5</td><td>Strict clinical budget</td></tr>
                    <tr><td>1.0</td><td>Target operational budget</td></tr>
                    <tr><td>2.0</td><td>Moderate privacy</td></tr>
                    <tr><td>5.0</td><td>Relaxed privacy</td></tr>
                    <tr><td>∞ (no DP)</td><td>Utility ceiling — no clipping, no noise, no accountant</td></tr>
                  </tbody>
                </table>
              </div>

              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)' }}>
                <strong>Proving pattern:</strong> Run BOTH recipes (head-only vs full-model) at every budget, shared seeds. Head-only advantage should WIDEN as ε tightens. If curves don't separate, the claim fails.
              </div>
            </motion.div>
          )}

          {activeTab === 'compression' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Gradient Compression</h3></div>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Step</th><th>Technique</th><th>Nominal</th><th>Measured</th></tr></thead>
                  <tbody>
                    <tr><td>1</td><td>Top-k sparsification (keep 20%)</td><td>5×</td><td rowSpan={2}>Full-model: 3.2× (indices dominate)</td></tr>
                    <tr><td>2</td><td>8-bit quantization</td><td>4×</td></tr>
                    <tr><td>3</td><td>Error feedback</td><td>—</td><td>Residual carried, coordinates delayed not lost</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box note">
                Head-only compression: <strong>13.3×</strong> — frozen encoder deltas are exactly zero and send nothing. The gain is from what is trained (design), not the codec.
              </div>
            </motion.div>
          )}

          {activeTab === 'deployment' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>ONNX Edge Deployment</h3></div>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`checkpoint (best_<dataset>.pt)
  → build model from REGISTRY
  → load state_dict strict
  → torch.onnx.export, opset 17, dynamic batch
  → numerical verification (max |diff| < 1e-3)
  → [optional] INT8 dynamic quantization`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Benchmark Protocol</h4>
              <div className="kv-grid" style={{ marginBottom: 16 }}>
                <div className="kv-item"><div className="kv-label">What's Timed</div><div className="kv-value">End-to-end: preprocess + inference + conformal set + serialisation</div></div>
                <div className="kv-item"><div className="kv-label">Provider</div><div className="kv-value">CPU (IoT claim). CUDA = edge server (different question).</div></div>
                <div className="kv-item"><div className="kv-label">Metric</div><div className="kv-value">P95 latency (tail guarantee for real-time clinical use)</div></div>
                <div className="kv-item"><div className="kv-label">Regression Test</div><div className="kv-value">R3: 4.5e-07 (VitalDB), 8.9e-07 (WEAR)</div></div>
              </div>
            </motion.div>
          )}

          {activeTab === 'baselines' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">7</div><h3>Baseline Suite</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Configuration</th><th>Purpose</th></tr></thead>
                  <tbody>
                    <tr><td>B0</td><td>Centralised, non-private</td><td>Utility ceiling</td></tr>
                    <tr><td>B1</td><td>Local-only (no federation)</td><td>FL value check</td></tr>
                    <tr><td>B2</td><td>FedAvg, flat, no DP</td><td>Federation baseline</td></tr>
                    <tr><td>B3</td><td>FedAvg, flat, DP (ε=1)</td><td>Privacy cost on flat</td></tr>
                    <tr><td>B4</td><td>FedAvg, flat, DP, full-model</td><td>Recipe comparison anchor</td></tr>
                    <tr><td>B5</td><td>FedAvg, flat, DP, head-only</td><td>Recipe effect (flat)</td></tr>
                    <tr><td>B6</td><td>Hierarchical, DP, head-only</td><td>Topology + recipe = proposed</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box note" style={{ marginTop: 16 }}>
                B4→B6 decomposition: recipe effect = B4 vs B5, topology effect = B5 vs B6. All arms share data, partitions, seed, budget, sigma.
              </div>
            </motion.div>
          )}

          {activeTab === 'results' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">8</div><h3>Current Results Status</h3></div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 16 }}>
                <strong>All apparatus built. Full pipeline runs pending on current datasets (VitalDB + WEAR).</strong>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Proven (Centralised, Non-Private, 2 Seeds)</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Arm</th><th>AUROC</th><th>AUPRC</th></tr></thead>
                  <tbody>
                    <tr><td>VitalDB — Signals only</td><td>0.8283</td><td>0.5281</td></tr>
                    <tr><td>VitalDB — Clinical only</td><td>0.7700</td><td>0.5022</td></tr>
                    <tr className="highlight-row"><td><strong>VitalDB — Fused</strong></td><td><strong>0.8694</strong></td><td><strong>0.6343</strong></td></tr>
                    <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--success)', fontWeight: 600 }}>Fusion gain: +0.0411 AUROC, +0.1062 AUPRC = 14.1× seed SD</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Pending</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Experiment</th><th>What It Proves</th><th>Command</th></tr></thead>
                  <tbody>
                    <tr><td>ε sweep (both recipes)</td><td>IP-1 head-only advantage</td><td><code>epsilon_sweep.py</code></td></tr>
                    <tr><td>B4→B6 decomposition</td><td>IP-2 two-axis attribution</td><td><code>baselines.py + joint_eval.py</code></td></tr>
                    <tr><td>Conformal coverage</td><td>IP-3 exponential mechanism</td><td><code>fedconform_hc.py</code></td></tr>
                    <tr><td>ONNX latency</td><td>O3a &lt;100ms</td><td><code>inference_bench.py --provider cpu</code></td></tr>
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
