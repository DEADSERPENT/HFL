import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Box, Layers, Shield, Shrink, HardDrive, Settings, Cpu,
  AlertTriangle, CheckCircle2
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function ModelDesign() {
  const [activeTab, setActiveTab] = useState('constraints')

  return (
    <>
      <div className="page-header">
        <h2>Model Design Guide — HFL-MM</h2>
        <p>Architecture, privacy design, compression, conformal prediction, deployment</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box note" style={{ marginBottom: 16 }}>
              This file documents the model that is <strong>IMPLEMENTED and TRAINED</strong>: HFL-MM, defined in <code>model/architecture/hfl_mm_model.py</code>. Component status is stated explicitly throughout.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'constraints', icon: <Box size={14} />, label: 'Constraints' },
                { key: 'architecture', icon: <Layers size={14} />, label: 'Architecture' },
                { key: 'privacy', icon: <Shield size={14} />, label: 'Privacy Design' },
                { key: 'compression', icon: <Shrink size={14} />, label: 'Uplink Compression' },
                { key: 'conformal', icon: <CheckCircle2 size={14} />, label: 'FedConform-HC' },
                { key: 'training', icon: <Settings size={14} />, label: 'Training Loop' },
                { key: 'status', icon: <Cpu size={14} />, label: 'Component Status' },
                { key: 'deployment', icon: <HardDrive size={14} />, label: 'Deployment Path' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* CONSTRAINTS */}
          {activeTab === 'constraints' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>The Four Hard Constraints</h3></div>
              <p className="section-description">The architecture is not a free choice. Four constraints bind it simultaneously, and each eliminates otherwise-attractive options.</p>
              <div className="objective-grid" style={{ marginTop: 16 }}>
                <div className="objective-card">
                  <div className="objective-id">C1</div>
                  <div className="objective-title">Inference Under 100ms on Edge Hardware</div>
                  <div className="objective-method">Eliminates ViT, ResNet-50, EfficientNet-B7, transformer language backbones. Admits small 1D conv stacks, GRUs, MobileNet-class image nets, MLP feature encoders.</div>
                </div>
                <div className="objective-card">
                  <div className="objective-id">C2</div>
                  <div className="objective-title">DP-SGD Compatibility</div>
                  <div className="objective-method">Opacus requires per-sample gradients. BatchNorm makes each sample's output depend on other samples — per-sample gradient is undefined. Every normalisation is therefore <strong>GroupNorm</strong>. Enforced: build_hfl_mm_hc() walks the module tree and RAISES if any BatchNorm survives.</div>
                </div>
                <div className="objective-card">
                  <div className="objective-id">C3</div>
                  <div className="objective-title">Two Heterogeneous Modalities</div>
                  <div className="objective-method">One branch consumes multi-channel time series; the other consumes either an image or a dense feature vector. The two cannot share an encoder.</div>
                </div>
                <div className="objective-card">
                  <div className="objective-id">C4</div>
                  <div className="objective-title">Small Enough to Transmit Every Round</div>
                  <div className="objective-method">Uplink objective (≥50% reduction) is a property of what is SENT. This drives the freeze-and-compress design.</div>
                </div>
              </div>
            </motion.div>
          )}

          {/* ARCHITECTURE */}
          {activeTab === 'architecture' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>HFL-MM Architecture</h3></div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`modality A ──> encoder_a (FedMamba-HC) ──> 256 ─┐
                                                 ├─> LateFusionHead ──> n_classes
modality B ──> encoder_b ──────────────> 576 ────┘`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>encoder_a — FedMamba-HC</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Stacked 1D convolutional front end → bidirectional GRU over temporal axis, GroupNorm throughout. Input channel count is a CONSTRUCTOR ARGUMENT (<code>n_channels_a</code>), never a constant — same class serves 18-channel intraoperative tensor and 12-channel inertial tensor without modification.</p>
                <div className="kv-grid" style={{ marginTop: 12 }}>
                  <div className="kv-item"><div className="kv-label">Output</div><div className="kv-value">256-dimensional embedding</div></div>
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>encoder_b — Modality-B Encoder</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="table-container">
                  <table className="data-table">
                    <thead><tr><th>modality_b</th><th>Implementation</th><th>Current Use</th></tr></thead>
                    <tbody>
                      <tr><td><code>"features"</code></td><td>FeatureEncoder: in_dim → 1024 → 576 MLP, GroupNorm</td><td>VitalDB (34-d clinical), WEAR (2048-d video)</td></tr>
                      <tr><td><code>"image"</code></td><td>MobileNetV3 backbone</td><td>Retained in code, not exercised by current datasets</td></tr>
                    </tbody>
                  </table>
                </div>
                <div className="kv-grid" style={{ marginTop: 12 }}>
                  <div className="kv-item"><div className="kv-label">Output</div><div className="kv-value">576-dimensional embedding</div></div>
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>LateFusionHead</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="code-block" style={{ marginBottom: 12 }}>
{`Concatenate(256, 576) = 832 → 512 → 256 → n_classes
GELU activations, GroupNorm, dropout 0.3`}
                </div>
                <div className="info-box note">
                  <strong>Why late fusion and NOT cross-attention:</strong> Late fusion keeps each encoder independent until the final head. That property is what makes the privacy design possible: the head is a small, self-contained block that can be trained separately. Cross-attention entangles the streams throughout — no small separable block left to DP-train.
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Measured Parameter Counts</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Dataset</th><th>Total</th><th>encoder_a</th><th>encoder_b</th><th>Head (DP-trained)</th></tr></thead>
                  <tbody>
                    <tr><td>VitalDB</td><td>1,864,227</td><td>674,913</td><td>629,440</td><td>559,874 (30.0%)</td></tr>
                    <tr><td>WEAR</td><td>3,925,875</td><td>670,113</td><td>2,691,776</td><td>563,986 (14.4%)</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box note" style={{ marginTop: 12 }}>
                Head is roughly the same absolute size; percentage differs because WEAR's 2048-d input makes encoder_b large. Transmitted fraction is a property of the dataset, not a tunable claim.
              </div>
            </motion.div>
          )}

          {/* PRIVACY DESIGN */}
          {activeTab === 'privacy' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>Privacy Design — Head-Only DP Fine-Tuning</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>The Problem</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">A strict budget forces a large noise multiplier. Training the full network from scratch under that noise destroys encoder gradients before they form useful features — the system collapses toward chance.</p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>The Mechanism</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`1. Pretrain both encoders non-privately (pretrain_encoders.py)
2. FREEZE both encoders
3. DP-train ONLY the fusion head, federated across clients`}
              </div>

              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)', marginBottom: 16 }}>
                <strong>THE POINT MOST LIKELY TO BE MISREAD:</strong> Freezing does NOT reduce the noise. Sigma is a function of the budget, the number of steps, and the sampling rate. It does not depend on how many parameters are trained. Freezing changes the OPTIMISATION GEOMETRY so the same sigma becomes survivable. Stating "we froze most of the model so we needed less noise" would be false.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Implementation Hazard</h4>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <code>requires_grad</code> is NOT part of <code>state_dict</code>. Every rebuild or reload in the federated loop must RE-APPLY the freeze, or encoders silently become trainable again. <code>freeze_encoders()</code> is called after every load, not once at setup.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Accounting</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">One sigma precomputed for the whole budget. ONE persistent privacy engine per client reused across rounds. Calling the accountant afresh each round drops cross-round composition and reports budget far smaller than actually spent. Conformal calibration budget is composed into reported total.</p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Limitation — Stated Plainly</h4>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                If encoders are pretrained on pooled federated training data, they have seen private data non-privately. Numbers from that mode measure the UPPER BOUND — not a valid end-to-end guarantee. <code>pretrain_encoders.py</code> prints PROXY/ORACLE warning and stamps the mode into checkpoint metadata. Closing this gap with a genuinely external public corpus is the <strong>single most important outstanding item</strong>.
              </div>
            </motion.div>
          )}

          {/* COMPRESSION */}
          {activeTab === 'compression' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>What Travels on the Uplink</h3></div>
              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Compression Chain (applied to head delta)</h4>
                <div className="table-container">
                  <table className="data-table">
                    <thead><tr><th>Step</th><th>Technique</th><th>Nominal Factor</th></tr></thead>
                    <tbody>
                      <tr><td>1</td><td>Top-k sparsification, keep 20%</td><td>5×</td></tr>
                      <tr><td>2</td><td>8-bit quantization</td><td>4×</td></tr>
                      <tr><td>3</td><td>Error feedback (residual carried to next round)</td><td>—</td></tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>A Subtle Defect, Fixed</h4>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 16 }}>
                Under frozen encoders the encoder deltas are exactly zero. A fixed-k top-k selector will nonetheless "select" 20% of an all-zero tensor and transmit those zeros as if they were updates. The selector is now <strong>capped by the number of non-zero entries</strong>, so an all-zero tensor sends nothing. Without that cap the measured uplink would be inflated by traffic carrying no information.
              </div>
              <div className="info-box note">
                Dense (non-frozen) path is unaffected by the cap and was verified bit-identical before and after the fix.
              </div>
            </motion.div>
          )}

          {/* FEDCONFORM-HC */}
          {activeTab === 'conformal' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>FedConform-HC — Calibrated Prediction Sets</h3></div>
              <div className="info-box success" style={{ marginBottom: 16 }}>
                <strong>Status:</strong> IMPLEMENTED in <code>model/utils/fedconform_hc.py</code>
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">A point prediction is insufficient for a clinical decision. Split conformal prediction converts model scores into a set that contains the true label with a user-chosen probability, using a held-out calibration split. The federated version aggregates a per-client quantile hierarchically.</p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Why the DP Mechanism Matters</h4>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                The quantile must be released privately. Additive noise on a quantile is a poor fit: the noise scale needed for a strict budget is comparable to the spread of the statistic. The released quantile is dominated by noise → sets are either vacuous (every label) or invalid (coverage lost).
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Uses the <strong>EXPONENTIAL MECHANISM</strong>, which selects a value from the score distribution with probability weighted by utility rather than perturbing additively.</p>
                <div className="table-container" style={{ marginTop: 12 }}>
                  <table className="data-table">
                    <thead><tr><th>Metric</th><th>Exponential Mechanism</th><th>Additive Mechanism</th></tr></thead>
                    <tbody>
                      <tr><td>Bias</td><td>~0.001</td><td>—</td></tr>
                      <tr><td>Std. deviation</td><td>—</td><td>~0.416</td></tr>
                      <tr className="highlight-row"><td>Difference</td><td colSpan={2}>Three orders of magnitude better behaved</td></tr>
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>Budget:</strong> Calibration runs on the final round only. Its ε is composed into the reported total — NOT reported separately. A system that counts only its training epsilon and performs data-dependent calibration has understated its true budget.
              </div>
            </motion.div>
          )}

          {/* TRAINING LOOP */}
          {activeTab === 'training' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>Hierarchical Training Loop</h3></div>
              <div className="arch-diagram">
                <div className="arch-layer device">
                  <div className="arch-layer-label">Layer 1: Client</div>
                  <div className="arch-layer-content">Local DP-SGD on the head; compress the delta</div>
                </div>
                <div className="arch-arrow">↓ Compressed head delta</div>
                <div className="arch-layer edge">
                  <div className="arch-layer-label">Layer 2: Edge (×2)</div>
                  <div className="arch-layer-content">FedAvg over its clients every τ_e rounds; ASWA staleness weighting</div>
                </div>
                <div className="arch-arrow">↓ Aggregated updates</div>
                <div className="arch-layer cloud">
                  <div className="arch-layer-label">Layer 3: Cloud</div>
                  <div className="arch-layer-content">FedAvg over edges; redistribute</div>
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginTop: 24, marginBottom: 12 }}>Model Selection</h4>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                On a POOLED validation split across all clients, never on a single client's split. One client's split is small and class-skewed enough that a handful of misclassifications swings the score by points — selecting on it selects noise. Selection metric: AUPRC (binary) / macro AUROC (multiclass).
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Ablation Knobs</h4>
              <div className="code-block">
{`--n_edges / --tau_e    hierarchy
--no_dp               privacy off, genuinely: no clipping, no noise,
                      no accountant. NOT the same as a large epsilon
                      (which still clips per-sample gradients).
--sparsity            top-k fraction
--quant_bits          quantization width`}
              </div>
            </motion.div>
          )}

          {/* COMPONENT STATUS */}
          {activeTab === 'status' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">7</div><h3>Component Status — Implemented vs Designed</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                No component is credited on the strength of merely existing in the repository.
              </div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Component</th><th>Built</th><th>Run That Establishes Contribution</th></tr></thead>
                  <tbody>
                    <tr><td>FedMamba-HC encoder_a</td><td style={{ color: 'var(--success)' }}>YES</td><td>Modality ablation</td></tr>
                    <tr><td>FeatureEncoder encoder_b</td><td style={{ color: 'var(--success)' }}>YES</td><td>Modality ablation</td></tr>
                    <tr><td>LateFusionHead</td><td style={{ color: 'var(--success)' }}>YES</td><td>Modality ablation (C5)</td></tr>
                    <tr><td>Head-only DP fine-tuning</td><td style={{ color: 'var(--success)' }}>YES</td><td>ε sweep, B4→B6</td></tr>
                    <tr><td>Gradient compression</td><td style={{ color: 'var(--success)' }}>YES</td><td>Ablation A3, A4</td></tr>
                    <tr><td>Two-tier hierarchy</td><td style={{ color: 'var(--success)' }}>YES</td><td>Ablation A1, S3→S4</td></tr>
                    <tr><td>FedConform-HC</td><td style={{ color: 'var(--success)' }}>YES</td><td>Empirical coverage vs nominal</td></tr>
                    <tr><td>ASWA</td><td style={{ color: 'var(--success)' }}>YES</td><td style={{ color: '#F59E0B' }}>NOT YET DEFINED — unablated</td></tr>
                    <tr><td>FedKD-E distillation</td><td style={{ color: '#F59E0B' }}>YES (not freeze-aware)</td><td style={{ color: '#EF4444' }}>Blocked; disabled in every run</td></tr>
                    <tr><td>ClinicalCMGA</td><td style={{ color: '#EF4444' }}>NO</td><td>Not a component of this system</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* DEPLOYMENT PATH */}
          {activeTab === 'deployment' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">8</div><h3>Deployment Path</h3></div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">The trained checkpoint is exported to ONNX — a runtime-independent artifact whose input shapes and class count are read FROM THE GRAPH by the benchmark, not assumed by it.</p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>GroupNorm Export Shim</h4>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                GroupNorm requires a shim for ONNX export. Applied at export time only; does not alter trained weights.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>INT8 Dynamic Quantization</h4>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 16 }}>
                <strong>OPT-IN and non-fatal.</strong> ONNX Runtime decomposes Gemm into MatMul before quantizing — node-exclusion by original layer name does not match the rewritten node. Rather than ship a model that silently fails on some runtimes, INT8 is offered as an option and its failure never blocks the FP32 path.
              </div>

              <div className="info-box note">
                <strong>Latency figure must state its execution provider.</strong> The IoT deployment claim is a CPU claim. Measuring on CUDA benchmarks the edge server, which is a different question.
              </div>
            </motion.div>
          )}

        </motion.div>
      </div>
    </>
  )
}
