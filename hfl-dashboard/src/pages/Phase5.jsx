import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Database, Layers, Shield, Shrink, Cpu,
  BarChart3, Zap, FileText, AlertTriangle,
  Bug, CheckCircle2, ArrowRight
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
        <p>17 deliverables · VitalDB + WEAR · HFL-MM-HC · B0–B7 baselines · measured results</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box success" style={{ marginBottom: 16 }}>
              <strong>Status: COMPLETE (2026-08-05)</strong> — All 17 deliverables done on both datasets. Model evaluated: HFL-MM (NOT PHANTOM-FL). VitalDB: 6/6 PASS. WEAR: 5 PASS + 1 INCONCLUSIVE, 0 FAIL.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'scope', icon: <FileText size={14} />, label: 'Scope' },
                { key: 'datasets', icon: <Database size={14} />, label: 'Datasets' },
                { key: 'model', icon: <Layers size={14} />, label: 'HFL-MM-HC' },
                { key: 'ips', icon: <Zap size={14} />, label: 'IP Activations' },
                { key: 'baselines', icon: <BarChart3 size={14} />, label: 'Baselines B0–B7' },
                { key: 'privacy', icon: <Shield size={14} />, label: 'DP & ε Sweep' },
                { key: 'compression', icon: <Shrink size={14} />, label: 'Compression' },
                { key: 'deploy', icon: <Cpu size={14} />, label: 'ONNX Deploy' },
                { key: 'results', icon: <CheckCircle2 size={14} />, label: 'Measured Results' },
                { key: 'notdone', icon: <AlertTriangle size={14} />, label: 'NOT Established' },
                { key: 'defects', icon: <Bug size={14} />, label: 'Defects Fixed' },
                { key: 'pipeline', icon: <ArrowRight size={14} />, label: 'Pipeline' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* ── SCOPE ── */}
          {activeTab === 'scope' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Scope & Objectives</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Domain Decision (Final 2026-04-22):</strong> Healthcare domain exclusively. Target venues: IEEE JBHI (Q1, IF ~7.7) and npj Digital Medicine (Q1, IF ~15.2).
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Phase 4 Validated (measured 2026-08-04)</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Objective</th><th>VitalDB</th><th>WEAR</th><th>Target</th><th>Status</th></tr></thead>
                  <tbody>
                    <tr><td>O1 Uplink reduction</td><td>90.8%</td><td>96.1%</td><td>≥50%</td><td style={{ color: 'var(--success)' }}>PASS</td></tr>
                    <tr><td>O4 Energy saving</td><td>72.3%</td><td>76.8%</td><td>≥20%</td><td style={{ color: 'var(--success)' }}>PASS</td></tr>
                    <tr><td>Update reliability</td><td>100.000%</td><td>99.987%</td><td>&gt;99%</td><td style={{ color: 'var(--success)' }}>PASS</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Phase 5 Closes Two Remaining Gaps</h4>
              <div className="kv-grid" style={{ marginBottom: 16 }}>
                <div className="kv-item"><div className="kv-label">Inference latency &lt;100ms</div><div className="kv-value">Real model + ONNX deployment</div></div>
                <div className="kv-item"><div className="kv-label">Accuracy loss ≤2% at ε=1</div><div className="kv-value">Real FL training + DP-SGD</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Deployment Topology</h4>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">IoT Devices</div><div className="kv-value">20 (patient wearables + bedside units)</div></div>
                <div className="kv-item"><div className="kv-label">Edge Servers</div><div className="kv-value">3 (hospital ward gateways, 1 per 6-7 devices)</div></div>
                <div className="kv-item"><div className="kv-label">Cloud</div><div className="kv-value">1 central hospital aggregation server</div></div>
                <div className="kv-item"><div className="kv-label">Non-IID</div><div className="kv-value">Dirichlet α=0.5, 70/15/15 train/val/test</div></div>
              </div>
            </motion.div>
          )}

          {/* ── DATASETS ── */}
          {activeTab === 'datasets' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>Datasets</h3></div>

              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Selection Rule:</strong> A dataset must satisfy (A) GENUINE PAIRING — both modalities from the SAME entity at the SAME time, recorded that way; and (B) SHARED TARGET — both modalities independently carry information about the label. A dataset satisfying A but not B is not multimodal.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>VitalDB — Primary Clinical Evidence</h4>
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="kv-grid" style={{ marginBottom: 12 }}>
                  <div className="kv-item"><div className="kv-label">Windows</div><div className="kv-value">48,712 from 6,257 surgeries</div></div>
                  <div className="kv-item"><div className="kv-label">Clients</div><div className="kv-value">9 (surgical operation type)</div></div>
                  <div className="kv-item"><div className="kv-label">Classes</div><div className="kv-value">2 — postop ICU admission (19.7% positive)</div></div>
                  <div className="kv-item"><div className="kv-label">Modality A</div><div className="kv-value">Intraop vital-sign trends — shape (18, 300). 9 signals + 9 observed-masks, 0.5 Hz × 10 min</div></div>
                  <div className="kv-item"><div className="kv-label">Modality B</div><div className="kv-value">Preoperative clinical vector — shape (34,). Demographics, comorbidities, lab values</div></div>
                  <div className="kv-item"><div className="kv-label">Pairing</div><div className="kv-value">Same patient, same second — instrument-paired, no pairing rule</div></div>
                  <div className="kv-item"><div className="kv-label">Split</div><div className="kv-value">BY CASE, stratified by outcome. No case in &gt;1 split. Train 34,044 / Val 7,308 / Test 7,360</div></div>
                  <div className="kv-item"><div className="kv-label">Non-IID</div><div className="kv-value">ICU rate spans 3.2%–50.7% across 9 clients (16-fold spread)</div></div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
                  <strong>Metric:</strong> At 19.7% positive, ~80% accuracy is free. Checkpoint selection uses AUPRC. Scoring: case-level is what to quote (window-level overstates effective sample size).
                </p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>WEAR — Fast Iteration</h4>
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="kv-grid" style={{ marginBottom: 12 }}>
                  <div className="kv-item"><div className="kv-label">Windows</div><div className="kv-value">38,578</div></div>
                  <div className="kv-item"><div className="kv-label">Clients</div><div className="kv-value">22 (one per subject)</div></div>
                  <div className="kv-item"><div className="kv-label">Classes</div><div className="kv-value">18 activities</div></div>
                  <div className="kv-item"><div className="kv-label">Modality A</div><div className="kv-value">4 body-worn accelerometers × 3 axes — shape (12, 100), 50 Hz × 2s</div></div>
                  <div className="kv-item"><div className="kv-label">Modality B</div><div className="kv-value">Two-stream I3D egocentric video features — shape (2048,)</div></div>
                  <div className="kv-item"><div className="kv-label">Pairing</div><div className="kv-value">Hardware-synchronised (inertial + head-mounted camera, one wearer)</div></div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
                  <strong>Role:</strong> Fast-iteration domain (arms train in seconds). NOT the dataset the multimodal claim rests on.
                </p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Fusion Test — MEASURED</h4>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>Arm</th><th>AUROC</th><th>AUPRC</th><th>Case AUROC</th><th>Case AUPRC</th></tr></thead>
                  <tbody>
                    <tr><td>Signals only</td><td>0.8283</td><td>0.5281</td><td>0.8590</td><td>0.6446</td></tr>
                    <tr><td>Clinical only</td><td>0.7700</td><td>0.5022</td><td>0.7713</td><td>0.4961</td></tr>
                    <tr className="highlight-row"><td><strong>FUSED</strong></td><td><strong>0.8694</strong></td><td><strong>0.6343</strong></td><td><strong>0.8875</strong></td><td><strong>0.6740</strong></td></tr>
                    <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--success)', fontWeight: 600 }}>Gain over BEST unimodal: +0.0411 AUROC, +0.1062 AUPRC = 14.1× seed SD → Gap #1 DEMONSTRATED</td></tr>
                  </tbody>
                </table>
              </div>

              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>WEAR fusion at ceiling:</strong> Best single modality already 0.9976 AUROC — no headroom. Reported as ceiling effect, NOT counted as a second confirmation.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginTop: 16, marginBottom: 12 }}>Data Fingerprints</h4>
              <div className="code-block">
{`vitaldb  labels d3fa814dd4396efd  partition_meta 69feba3f786f9e64
wear     labels 8aeb2aeeb2bba951  partition_meta 38c58aadc2a84eee`}
              </div>
            </motion.div>
          )}

          {/* ── MODEL ── */}
          {activeTab === 'model' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>HFL-MM-HC Architecture</h3></div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`INPUT LAYER (per IoT device):
  Modality A: Intraop trends (18,300)    Modality B: Clinical vector (34,)

ENCODER A: FedMamba-HC [IP-1]            ENCODER B: FeatureEncoder (MLP)
  Conv1d(18→128) + biGRU → 256-d           FC layers → 576-d
                    │                              │
                    └──────── LATE FUSION ──────────┘
                              Concat 832-d
                    FC(512) → GN(16) → GELU → Drop(0.3)
                    FC(256) → GN(8) → GELU
                    FC(n_classes)

  FedConform-HC wrapper [IP-9] → calibrated prediction sets`}
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

              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Float32 Size</div><div className="kv-value">~12.8 MB</div></div>
                <div className="kv-item"><div className="kv-label">INT8 ONNX</div><div className="kv-value">~3.2 MB</div></div>
                <div className="kv-item"><div className="kv-label">Norm</div><div className="kv-value">GroupNorm throughout — build_hfl_mm_hc() raises if any BatchNorm survives</div></div>
              </div>
            </motion.div>
          )}

          {/* ── IP ACTIVATIONS ── */}
          {activeTab === 'ips' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>IP Activations — Three Healthcare Innovations</h3></div>

              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>IP-1: FedMamba-HC — Mamba SSM Encoder</h4>
                <div className="kv-grid" style={{ marginBottom: 12 }}>
                  <div className="kv-item"><div className="kv-label">Status</div><div className="kv-value" style={{ color: 'var(--success)' }}>IMPLEMENTED</div></div>
                  <div className="kv-item"><div className="kv-label">File</div><div className="kv-value"><code>model/fedmamba_hc.py</code></div></div>
                </div>
                <p className="section-description" style={{ marginBottom: 8 }}>Mamba SSM (Gu & Dao, NeurIPS 2024): O(N) time/memory vs O(N²) for Transformer. PatchEmbed(18→128, k=10, s=5) → 4 MambaBlocks(d=128, d_state=16, d_conv=4, expand=2) → AdaptiveAvgPool → 256-d. FLOPs: ~18M/sample.</p>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
                  <strong>Novel claim:</strong> First Mamba SSM within federated learning for clinical analysis with DP guarantees. No BatchNorm — GroupNorm(8) throughout.
                </p>
              </div>

              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>IP-9: FedConform-HC — Federated Conformal Prediction</h4>
                <div className="kv-grid" style={{ marginBottom: 12 }}>
                  <div className="kv-item"><div className="kv-label">Status</div><div className="kv-value" style={{ color: 'var(--success)' }}>IMPLEMENTED</div></div>
                  <div className="kv-item"><div className="kv-label">File</div><div className="kv-value"><code>model/fedconform_hc.py</code></div></div>
                </div>
                <p className="section-description" style={{ marginBottom: 8 }}>
                  Phase A: per-device nonconformity scores → local quantile. Phase B: add Laplace noise (ε_conf=0.1), edge median, cloud mean. Phase C: prediction set C(X) = {'{'} y : 1-p[y] ≤ q_global {'}'}.
                  Clinical: set_size=1 → high confidence; ≥3 → refer to physician.
                </p>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
                  Coverage guarantee: P(Y ∈ C(X)) ≥ 1 - α - O(ε_conf + 1/√n_cal). At α=0.1, n_cal=500: ≥89.5%.
                </p>
              </div>

              <div className="card">
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>IP-3: ClinicalCMGA — Temporal-Decay Cross-Modal Gated Attention</h4>
                <div className="kv-grid" style={{ marginBottom: 12 }}>
                  <div className="kv-item"><div className="kv-label">Status</div><div className="kv-value" style={{ color: '#F59E0B' }}>DESIGNED (Phase 6 impl.)</div></div>
                  <div className="kv-item"><div className="kv-label">File</div><div className="kv-value"><code>model/clinical_cmga_design.py</code></div></div>
                </div>
                <p className="section-description" style={{ marginBottom: 0 }}>
                  Temporal decay gates: τ_a = q_a · exp(-λ_a · Δt_a). Cross-modal attention with clinical urgency gating. λ_a=0.02 (ECG ~50min half-life), λ_b=0.005 (X-ray ~140min). All DP-compatible (GroupNorm, scalar multiplications only).
                </p>
              </div>
            </motion.div>
          )}

          {/* ── BASELINES ── */}
          {activeTab === 'baselines' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Baseline Suite B0–B7</h3></div>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>ID</th><th>System</th><th>What It Measures</th></tr></thead>
                  <tbody>
                    <tr><td>B0</td><td>Centralized (no privacy)</td><td>Upper bound: full data access, no FL, no DP</td></tr>
                    <tr><td>B1</td><td>Local Only (no federation)</td><td>Lower bound: no collaboration</td></tr>
                    <tr><td>B2</td><td>FedAvg (McMahan 2017)</td><td>Standard FL, no privacy</td></tr>
                    <tr><td>B3</td><td>FedProx (Li 2020) + μ</td><td>Heterogeneity-aware FL on non-IID</td></tr>
                    <tr><td>B4</td><td>DP-FedAvg (full-model DP)</td><td>Prior art recipe — privacy-aware but flat</td></tr>
                    <tr><td>B5</td><td>MOON (Li 2021)</td><td>Contrastive FL — nearest competitor</td></tr>
                    <tr><td style={{ color: '#3B82F6' }}>B6</td><td style={{ color: '#3B82F6' }}>Head-only DP (PROPOSED recipe)</td><td>Pretrained encoders + DP head only</td></tr>
                    <tr><td style={{ color: '#F59E0B' }}>B7</td><td style={{ color: '#F59E0B' }}>Pretrained + full-model DP</td><td>Confound control: separates pretrain effect from head-only effect</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>VitalDB AUROC Results</h4>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>B0</th><th>B1</th><th>B2</th><th>B3</th><th>B4</th><th>B5</th><th>B7</th><th style={{ color: 'var(--success)' }}>B6 (ours)</th></tr></thead>
                  <tbody>
                    <tr>
                      <td>0.8612</td><td>0.7873</td><td>0.8173</td><td>0.8154</td>
                      <td style={{ color: '#EF4444' }}>0.7347</td><td>0.8431</td><td>0.8470</td>
                      <td style={{ color: 'var(--success)', fontWeight: 700 }}>0.8589</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Publication Story</h4>
              <div className="card">
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: 14 }}>
                  <li style={{ padding: '4px 0' }}>B0→B1: Federation gap (value of FL)</li>
                  <li style={{ padding: '4px 0' }}>B1→B2: Heterogeneity handling (non-IID challenge)</li>
                  <li style={{ padding: '4px 0' }}>B2→B4: Privacy cost of DP (accuracy vs guarantee)</li>
                  <li style={{ padding: '4px 0' }}>B4→P1: Hierarchy benefit (2-tier HFL vs flat DP-FL)</li>
                  <li style={{ padding: '4px 0' }}>B3→P1: Non-IID handling (FedProx vs HFL-MM)</li>
                  <li style={{ padding: '4px 0' }}>B5→P1: Novelty — Mamba + conformal vs MOON</li>
                  <li style={{ padding: '4px 0', color: '#F59E0B' }}>B7: ~90% of apparent head-only gain was the pretrained encoders (confound control)</li>
                </ul>
              </div>
            </motion.div>
          )}

          {/* ── DP & EPSILON SWEEP ── */}
          {activeTab === 'privacy' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>DP-SGD Configuration & ε Sweep</h3></div>

              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Library</div><div className="kv-value">Opacus 1.x</div></div>
                <div className="kv-item"><div className="kv-label">Optimizer</div><div className="kv-value">DP-Adam (PrivacyEngine wrapping Adam)</div></div>
                <div className="kv-item"><div className="kv-label">Noise mult σ</div><div className="kv-value">1.1 (calibrated via RDP for ε=1.0)</div></div>
                <div className="kv-item"><div className="kv-label">Max grad norm C</div><div className="kv-value">1.0</div></div>
                <div className="kv-item"><div className="kv-label">Budget split</div><div className="kv-value">ε=0.9 (training) + ε_conf=0.1 (conformal) = 1.0 total</div></div>
                <div className="kv-item"><div className="kv-label">Target δ</div><div className="kv-value">1e-5 (≈1/N_total)</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Measured Privacy-Utility Curve (AUROC, head minus full)</h4>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>ε</th><th>0.5</th><th>1</th><th>2</th><th>4</th><th>8</th><th>∞</th></tr></thead>
                  <tbody>
                    <tr><td><strong>VitalDB</strong></td><td>+0.1314</td><td>+0.1134</td><td>+0.0969</td><td>+0.0782</td><td>+0.0602</td><td>+0.0087</td></tr>
                    <tr><td><strong>WEAR</strong></td><td>+0.3954</td><td>+0.3092</td><td>+0.2081</td><td>+0.1311</td><td>+0.0880</td><td>+0.0020</td></tr>
                  </tbody>
                </table>
              </div>

              <div className="info-box success">
                <strong>Pre-registered refutation condition HOLDS:</strong> The gap widens monotonically as the budget tightens and nearly vanishes at ε=∞. This was the refutation condition for the head-only claim, and it holds on both datasets.
              </div>
            </motion.div>
          )}

          {/* ── COMPRESSION ── */}
          {activeTab === 'compression' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">7</div><h3>Gradient Compression</h3></div>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>Step</th><th>Technique</th><th>Ratio</th><th>Details</th></tr></thead>
                  <tbody>
                    <tr><td>A</td><td>Top-k sparsification (k=0.2)</td><td>5×</td><td>Error feedback accumulator prevents information loss</td></tr>
                    <tr><td>B</td><td>8-bit quantization</td><td>4×</td><td>uint8 + 2× float32 header (g_min, g_max)</td></tr>
                    <tr><td></td><td><strong>Combined nominal</strong></td><td><strong>20×</strong></td><td>Model ~12.8 MB → ~0.64 MB/device/round</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box note">
                <strong>Measured vs nominal:</strong> Full-model compression is 3.2× (indices dominate at 80% of bytes). Head-only: 13.3× (frozen encoder deltas = zero → nothing sent). The nominal 20× applies to the dense gradient path only.
              </div>
            </motion.div>
          )}

          {/* ── ONNX DEPLOY ── */}
          {activeTab === 'deploy' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">8</div><h3>ONNX Edge Deployment</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Expected Inference Latency</h4>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>Component</th><th>Expected (ms)</th><th>Budget (ms)</th></tr></thead>
                  <tbody>
                    <tr><td>L_sensor (ECG + signals)</td><td>3–8</td><td>10</td></tr>
                    <tr><td>L_preproc (filter + norm)</td><td>10–18</td><td>20</td></tr>
                    <tr><td>L_inference (ONNX INT8)</td><td>30–50</td><td>50</td></tr>
                    <tr><td>L_comm (LTE 4G)</td><td>3–8</td><td>10</td></tr>
                    <tr><td>L_conformal (C(X) set)</td><td>&lt;1</td><td>5</td></tr>
                    <tr><td>L_post (softmax + output)</td><td>&lt;1</td><td>5</td></tr>
                    <tr className="highlight-row"><td><strong>TOTAL</strong></td><td><strong>47–86</strong></td><td><strong>100</strong></td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Measured P95 Latency (CPU provider)</h4>
              <div className="stats-grid">
                <div className="stat-card"><div className="stat-label">VitalDB</div><div className="stat-value green">2.99 ms</div></div>
                <div className="stat-card"><div className="stat-label">WEAR</div><div className="stat-value green">1.22 ms</div></div>
                <div className="stat-card"><div className="stat-label">Target</div><div className="stat-value">&lt;100 ms</div></div>
                <div className="stat-card"><div className="stat-label">O3a</div><div className="stat-value green">PASS</div></div>
              </div>
            </motion.div>
          )}

          {/* ── MEASURED RESULTS ── */}
          {activeTab === 'results' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">9</div><h3>Measured Results — Objective Status</h3></div>

              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Objective</th><th>VitalDB</th><th>WEAR</th><th>Status</th></tr></thead>
                  <tbody>
                    <tr><td>O1 Uplink reduction</td><td>90.8%</td><td>96.1%</td><td style={{ color: 'var(--success)' }}><strong>PASS / PASS</strong></td></tr>
                    <tr><td>O2a ε spent</td><td>0.963</td><td>0.989</td><td style={{ color: 'var(--success)' }}><strong>PASS / PASS</strong></td></tr>
                    <tr><td>O2b Accuracy loss</td><td>-0.916 pp</td><td>+1.967 pp</td><td><span style={{ color: 'var(--success)' }}>PASS</span> / <span style={{ color: '#F59E0B' }}>INCONCLUSIVE</span></td></tr>
                    <tr><td>O3a P95 latency</td><td>2.99 ms</td><td>1.22 ms</td><td style={{ color: 'var(--success)' }}><strong>PASS / PASS</strong></td></tr>
                    <tr><td>O3b Update reliability</td><td>99.27%</td><td>99.05%</td><td style={{ color: 'var(--success)' }}><strong>PASS / PASS</strong></td></tr>
                    <tr><td>O4 Energy saving</td><td>72.3%</td><td>76.8%</td><td style={{ color: 'var(--success)' }}><strong>PASS / PASS</strong></td></tr>
                  </tbody>
                </table>
              </div>

              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 16 }}>
                <strong>WEAR O2b is INCONCLUSIVE, not a pass.</strong> Pre-registered n=15 paired seeds: mean +1.967 pp, 95% CI [+1.760, +2.173]. The interval spans the 2 pp target. At n=5 the mean was 1.783 and looked like a pass; it moved UP with more seeds. n was fixed in advance — not being extended (optional stopping).
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Cost of a Valid DP Guarantee (VitalDB)</h4>
              <div className="card">
                <p className="section-description" style={{ margin: 0 }}>
                  Encoders pretrained on 874 patients disjoint from every client cost <strong>-0.0223 AUROC / -0.0424 AUPRC</strong> against the oracle upper bound. That delta is what makes the epsilon a guarantee rather than a bound.
                </p>
              </div>
            </motion.div>
          )}

          {/* ── WHAT IS NOT ESTABLISHED ── */}
          {activeTab === 'notdone' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">10</div><h3>What Is NOT Established — Read Before Writing Thesis</h3></div>
              <div className="card" style={{ marginBottom: 16 }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: 14, lineHeight: 2 }}>
                  <li style={{ padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <span style={{ color: '#EF4444', fontWeight: 700 }}>✗</span> <strong>PHANTOM-FL DID NOT RUN.</strong> Every result used dp_mode=uniform, agg_mode=fedavg, edge_distill_epochs=0. Of its five innovations: CMGA unbuilt, SADP measured worse than uniform, FedKD-E not freeze-aware, pFAL showed no effect, ASWA unablated. The system is HFL-MM, not PHANTOM-FL.
                  </li>
                  <li style={{ padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <span style={{ color: '#EF4444', fontWeight: 700 }}>✗</span> <strong>Patient-level DP is IMPLEMENTED but UNMEASURED.</strong> Mechanism runs (eps=0.9948 verified), noise cost calibrated (1.77× σ vs window-level), but no full result exists. Most novel component with no numbers.
                  </li>
                  <li style={{ padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <span style={{ color: '#F59E0B', fontWeight: 700 }}>!</span> <strong>Single-seed everywhere except O2b.</strong> No interval can be placed on baseline or sweep differences yet.
                  </li>
                  <li style={{ padding: '4px 0' }}>
                    <span style={{ color: '#F59E0B', fontWeight: 700 }}>!</span> <strong>Not run:</strong> S3 (hierarchical WITHOUT DP), conformal coverage validation, mask-channel ablation, all of Phase 6.
                  </li>
                </ul>
              </div>
            </motion.div>
          )}

          {/* ── DEFECTS FIXED ── */}
          {activeTab === 'defects' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">11</div><h3>Defects Found & Fixed</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                Recorded because each produced plausible-but-wrong numbers silently.
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>#</th><th>Defect</th><th>Impact</th><th>Fix</th></tr></thead>
                  <tbody>
                    <tr><td>1</td><td>Epsilon breach</td><td>σ calibrated from smallest client with floor(n/batch). Every DP arm exceeded its own budget (0.5→0.511, 1→1.018, 8→8.163) — invalid, not merely weak</td><td>Bisect σ against ALL clients with ceil(). All 25 DP points now inside budget</td></tr>
                    <tr><td>2</td><td>Stale metadata</td><td>partition_meta.json not rewritten when public split carved — calibration used pre-split counts</td><td>Calibration reads files and warns on drift</td></tr>
                    <tr><td>3</td><td>B4→B6 confound</td><td>Contrast moved initialisation AND recipe at once; B6 beat even non-private B2</td><td>B7 added. ~90% of apparent head-only gain was pretrained encoders</td></tr>
                    <tr><td>4</td><td>Broken ε=∞ reference</td><td>No-DP anchor used random-init full model — not comparable to head arm, O2b uncomputable</td><td>Now runs per recipe</td></tr>
                    <tr><td>5</td><td>epsilon_spent from round 1</td><td>Read 0.283 instead of composed final value 0.963</td><td>Reads final composed value</td></tr>
                    <tr><td>6</td><td>CSV into .json</td><td>inference_bench writes CSV into a .json file — measured objective reported NOT MEASURED</td><td>Fixed extension</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* ── PIPELINE ── */}
          {activeTab === 'pipeline' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">12</div><h3>Training Pipeline — 11 Steps</h3></div>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`# Execute from SIMULATORS/

# 1. Download datasets
python data/loaders/download_datasets.py

# 2. Preprocess
python data/loaders/preprocess_healthcare.py --dataset vitaldb

# 3. Non-IID partition
python data/loaders/partition_noniid.py --domain healthcare --alpha 0.5 --n_devices 20

# 4-5. Baselines B0-B5
python model/baselines.py --mode centralized  # B0
python model/baselines.py --mode local        # B1
python model/baselines.py --mode fedavg       # B2
python model/baselines.py --mode fedprox --mu 0.01    # B3
python model/baselines.py --mode dp_fedavg --epsilon 1.0  # B4
python model/baselines.py --mode moon --mu 5.0        # B5

# 6. HFL-MM-HC training (P1)
python model/hfl_trainer.py --rounds 20 --tau_e 5 --n_devices 20 \\
  --n_edges 3 --epsilon 1.0 --delta 1e-5 --noise_mult 1.1

# 7. ε sweep
python model/epsilon_sweep.py --epsilons 0.1 0.5 1.0 2.0 5.0 inf

# 8. ONNX export + INT8
python model/onnx_exporter.py --checkpoint checkpoints/best_model_hc.pt

# 9. Inference benchmark
python model/inference_bench.py --model onnx/hfl_mm_hc_int8.onnx --n_runs 1000

# 10. NS-3 re-run
python scripts/ns3_phase5_integration.py

# 11. Collect results
python scripts/collect_phase5_results.py`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Phase 5 → Phase 6 Handoff</h4>
              <div className="card">
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: 14 }}>
                  <li style={{ padding: '4px 0' }}>✓ Trained HFL-MM-HC with FedMamba-HC + FedConform-HC</li>
                  <li style={{ padding: '4px 0' }}>✓ Full baseline comparison (B0–B7 vs P1)</li>
                  <li style={{ padding: '4px 0' }}>✓ ONNX INT8 deployed model with measured latency</li>
                  <li style={{ padding: '4px 0' }}>✓ ε sweep results (privacy-accuracy trade-off curve)</li>
                  <li style={{ padding: '4px 0' }}>✓ ClinicalCMGA full design spec ready for Phase 6</li>
                  <li style={{ padding: '4px 0', color: '#F59E0B' }}>→ Phase 6: implement PHANTOM-FL, joint eval, ablation, figures, paper</li>
                </ul>
              </div>
            </motion.div>
          )}

        </motion.div>
      </div>
    </>
  )
}
