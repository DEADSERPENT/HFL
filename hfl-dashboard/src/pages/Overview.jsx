import { motion } from 'framer-motion'
import {
  Radio, Zap, ShieldCheck, Clock, Target,
  FileText, TrendingUp, Globe, Calendar,
  HeartPulse, Package, AlertTriangle, CheckCircle2
} from 'lucide-react'

const stagger = {
  animate: { transition: { staggerChildren: 0.08 } }
}
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Overview() {
  return (
    <>
      <div className="page-header">
        <h2>Research Overview</h2>
        <p>Hierarchical Federated Multimodal Learning for Clinical IoMT</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          {/* Objective Status */}
          <motion.div variants={fadeUp}>
            <div className="qos-grid">
              <div className="qos-card pass">
                <div className="qos-icon"><Radio size={24} strokeWidth={2} /></div>
                <div className="qos-title">O1 — Uplink Reduction</div>
                <div className="qos-value">≥50%</div>
                <div className="qos-target">Owner: NS-3 · runs pending</div>
              </div>
              <div className="qos-card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#F59E0B' }}><ShieldCheck size={24} strokeWidth={2} /></div>
                <div className="qos-title">O2 — Privacy ε≤1, ≤2% loss</div>
                <div className="qos-value" style={{ color: '#F59E0B' }}>Pending</div>
                <div className="qos-target">Owner: Training · ε sweep pending</div>
              </div>
              <div className="qos-card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#F59E0B' }}><Clock size={24} strokeWidth={2} /></div>
                <div className="qos-title">O3 — Latency &lt;100ms, &gt;99% reliable</div>
                <div className="qos-value" style={{ color: '#F59E0B' }}>Pending</div>
                <div className="qos-target">Owner: ONNX Runtime + NS-3</div>
              </div>
              <div className="qos-card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#F59E0B' }}><Zap size={24} strokeWidth={2} /></div>
                <div className="qos-title">O4 — Energy ≥20% saving</div>
                <div className="qos-value" style={{ color: '#F59E0B' }}>Pending</div>
                <div className="qos-target">Owner: CloudSim Plus · interface unverified</div>
              </div>
            </div>
          </motion.div>

          {/* Measured Headline Result */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><CheckCircle2 size={16} /></div>
              <h3>Measured Headline Result</h3>
            </div>
            <div className="info-box success" style={{ marginBottom: 16 }}>
              <strong>Multimodal Fusion Helps — VitalDB, centralised, non-private, 2 seeds:</strong><br />
              Fusion AUROC 0.8694 vs best unimodal 0.8283 → +0.0411 AUROC, +0.1062 AUPRC. Gain is 14.1× the seed standard deviation. Fusion beats BOTH arms, not merely the weaker one.
            </div>
            <div className="info-box note">
              <strong>WEAR is at ceiling</strong> — best single modality 0.9976 AUROC. The +0.0004 gain is a ceiling effect, not supporting evidence. The multimodal claim rests on VitalDB alone.
            </div>
          </motion.div>

          {/* Problem Statement */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><FileText size={16} /></div>
              <h3>Problem Statement</h3>
            </div>
            <div className="card" style={{ marginBottom: 20 }}>
              <p className="section-description" style={{ marginBottom: 0 }}>
                Multimodal IoT devices generate large, heterogeneous data that overloads networks and risks privacy when centralised. Transmitting raw streams to the cloud increases latency and energy use, harming real-time decisions. On-device models reduce transfer but struggle to stay accurate and coordinated across devices. A hierarchical, privacy-preserving approach is needed that balances local computation, communication, latency and energy across edge-cloud layers.
              </p>
            </div>
            <div className="info-box success">
              <strong>Formal Objectives (from source document):</strong> O1 ≥50% uplink reduction · O2 ε≤1 with ≤2% accuracy loss · O3 &lt;100ms P95 latency AND &gt;99% update reliability · O4 ≥20% energy saving per round. Thresholds encoded in <code>scripts/check_objectives.py</code>.
            </div>
          </motion.div>

          {/* Research Gaps */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><Target size={16} /></div>
              <h3>Research Gaps Addressed</h3>
            </div>
            <div className="objective-grid">
              <div className="objective-card">
                <div className="objective-id">Gap 1</div>
                <div className="objective-title">No Multimodal Fusion in FL</div>
                <div className="objective-target">
                  <span className="objective-target-label">Status:</span>
                  <span className="objective-target-value" style={{ color: 'var(--success)' }}>DEMONSTRATED (VitalDB)</span>
                </div>
                <div className="objective-method">Prior work treats client data as generic gradient vectors with no notion of two heterogeneous modalities</div>
              </div>
              <div className="objective-card">
                <div className="objective-id">Gap 2</div>
                <div className="objective-title">Privacy-Efficiency Trade-off</div>
                <div className="objective-target">
                  <span className="objective-target-label">Status:</span>
                  <span className="objective-target-value" style={{ color: '#F59E0B' }}>Apparatus complete, measurement pending</span>
                </div>
                <div className="objective-method">Hierarchical FL omits DP; DP work omits hierarchy. Neither reports what the other costs</div>
              </div>
              <div className="objective-card">
                <div className="objective-id">Gap 3</div>
                <div className="objective-title">Real-time QoS Unaddressed</div>
                <div className="objective-target">
                  <span className="objective-target-label">Status:</span>
                  <span className="objective-target-value" style={{ color: '#F59E0B' }}>Apparatus complete</span>
                </div>
                <div className="objective-method">Inference latency under deployment conditions is rarely reported. ONNX export + portable benchmark built</div>
              </div>
              <div className="objective-card">
                <div className="objective-id">Gap 4</div>
                <div className="objective-title">Static Privacy Budgets</div>
                <div className="objective-target">
                  <span className="objective-target-label">Status:</span>
                  <span className="objective-target-value" style={{ color: '#EF4444' }}>NEGATIVE RESULT</span>
                </div>
                <div className="objective-method">Adaptive allocation measured WORSE than uniform. Composition tax across parameter groups dominates</div>
              </div>
            </div>
          </motion.div>

          {/* Phase Progress */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><TrendingUp size={16} /></div>
              <h3>Phase Progress</h3>
            </div>
            <div className="card">
              <div className="progress-bar-container">
                <div className="progress-label">
                  <span>Phase 1 — Research & Gap Analysis</span><span>100%</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '100%' }} /></div>
              </div>
              <div className="progress-bar-container" style={{ marginTop: 16 }}>
                <div className="progress-label">
                  <span>Phase 2 — Simulator Selection</span><span>100%</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '100%' }} /></div>
              </div>
              <div className="progress-bar-container" style={{ marginTop: 16 }}>
                <div className="progress-label">
                  <span>Phase 3 — Environment Setup</span><span>100%</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '100%' }} /></div>
              </div>
              <div className="progress-bar-container" style={{ marginTop: 16 }}>
                <div className="progress-label">
                  <span>Phase 4 — Simulator Implementation</span><span style={{ color: '#F59E0B' }}>Code Complete</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '90%', background: 'linear-gradient(90deg, #10B981, #F59E0B)' }} /></div>
              </div>
              <div className="progress-bar-container" style={{ marginTop: 16 }}>
                <div className="progress-label">
                  <span>Phase 5 — Model, Privacy, Deployment</span><span style={{ color: '#F59E0B' }}>Code Complete</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '90%', background: 'linear-gradient(90deg, #10B981, #F59E0B)' }} /></div>
              </div>
              <div className="progress-bar-container" style={{ marginTop: 16 }}>
                <div className="progress-label">
                  <span>Phase 6 — Joint Evaluation & Paper</span><span style={{ color: '#F59E0B' }}>Code Complete</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '90%', background: 'linear-gradient(90deg, #10B981, #F59E0B)' }} /></div>
              </div>
              <div className="info-box note" style={{ marginTop: 16 }}>
                <strong>"Code complete, runs pending"</strong> — every implementation requirement is satisfied and dataset-agnostic. What remains is execution on the current datasets. Verify: <code>python tests/traceability.py --dataset vitaldb</code>
              </div>
            </div>
          </motion.div>

          {/* Application Domain */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><Globe size={16} /></div>
              <h3>Datasets</h3>
            </div>
            <div className="domain-grid">
              <div className="domain-card">
                <div className="domain-icon"><HeartPulse size={32} strokeWidth={1.5} color="var(--primary)" /></div>
                <div className="domain-title">VitalDB — PRIMARY</div>
                <div className="domain-desc">Clinical IoMT: 48,712 windows, 6,257 surgeries, 9 clients. Intraoperative trends (18,300) + clinical vector (34,). Genuinely paired by instrument.</div>
              </div>
              <div className="domain-card">
                <div className="domain-icon"><Globe size={32} strokeWidth={1.5} color="var(--primary)" /></div>
                <div className="domain-title">WEAR — Fast Iteration</div>
                <div className="domain-desc">Wearable IoT: 38,578 windows, 22 subjects, 18 activities. Inertial (12,100) + I3D video (2048,). Hardware-synchronised. At ceiling — pipeline dataset only.</div>
              </div>
            </div>
          </motion.div>

          {/* Negative & Null Results */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><AlertTriangle size={16} /></div>
              <h3>Negative & Null Results</h3>
            </div>
            <div className="card">
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Finding</th><th>Status</th><th>Detail</th></tr></thead>
                  <tbody>
                    <tr><td>Adaptive per-layer privacy</td><td style={{ color: '#EF4444' }}>NEGATIVE</td><td>Measured worse than uniform. Composition tax dominates.</td></tr>
                    <tr><td>Personalised local adaptation</td><td style={{ color: '#6B7280' }}>NULL</td><td>No measurable pooled effect. Re-measure per-client on current data.</td></tr>
                    <tr><td>Edge knowledge distillation</td><td style={{ color: '#6B7280' }}>EXCLUDED</td><td>Not freeze-aware; disabled in every reported run.</td></tr>
                    <tr><td>Cross-modal gated attention</td><td style={{ color: '#6B7280' }}>NOT BUILT</td><td>Design-only. Conflicts with head-only DP recipe.</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>

          {/* Known Limitations */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><AlertTriangle size={16} /></div>
              <h3>Known Limitations</h3>
            </div>
            <div className="card">
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Limitation</th></tr></thead>
                  <tbody>
                    <tr><td>L1</td><td><strong>Encoder pretraining provenance</strong> — if pretrained on pooled client data, ε is an upper bound, not a guarantee. Disjoint public corpus required.</td></tr>
                    <tr><td>L2</td><td><strong>WEAR cannot evidence fusion</strong> — at ceiling (0.9976 AUROC). Pipeline dataset only.</td></tr>
                    <tr><td>L3</td><td><strong>Seed count</strong> — target ≥5 seeds; current ablation uses 2. Flagged as underpowered.</td></tr>
                    <tr><td>L4</td><td><strong>ASWA unablated</strong> — runs but effect never isolated. Not claimed as contribution.</td></tr>
                    <tr><td>L5</td><td><strong>CloudSim argument interface</strong> — unverified. O4 will report NOT MEASURED until wired.</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>

          {/* Deliverables */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><Package size={16} /></div>
              <h3>Reproducibility</h3>
            </div>
            <div className="code-block">
{`# Run the full pipeline (16 stages, resumable)
cd SIMULATORS
python scripts/run_pipeline.py --dataset vitaldb

# Check traceability
python tests/traceability.py --dataset vitaldb

# Score objectives O1-O4
python scripts/check_objectives.py --dataset vitaldb`}
            </div>
          </motion.div>

        </motion.div>
      </div>
    </>
  )
}
