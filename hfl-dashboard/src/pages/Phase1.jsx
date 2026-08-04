import { motion } from 'framer-motion'
import { useState } from 'react'
import { BookOpen, Target, Lightbulb, FileText, GitCompare } from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Phase1() {
  const [activeTab, setActiveTab] = useState('papers')

  return (
    <>
      <div className="page-header">
        <h2>Phase 1 — Research Understanding & Planning</h2>
        <p>Literature review, gap analysis, objectives, architecture vision</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box success" style={{ marginBottom: 16 }}>
              <strong>Status:</strong> COMPLETE — 5 papers reviewed, 4 gaps identified, 4 quantified objectives, architecture vision mapped, development roadmap created.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'papers', icon: <BookOpen size={14} />, label: 'Paper Summaries' },
                { key: 'gaps', icon: <Target size={14} />, label: 'Gap Analysis' },
                { key: 'objectives', icon: <Lightbulb size={14} />, label: 'Objectives' },
                { key: 'architecture', icon: <GitCompare size={14} />, label: 'Architecture' },
                { key: 'roadmap', icon: <FileText size={14} />, label: 'Roadmap' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {activeTab === 'papers' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Paper Summaries & Gap Analysis</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Paper</th><th>What It Does</th><th>Gap for This Work</th></tr></thead>
                  <tbody>
                    <tr><td><strong>FL2DP</strong> (Gu et al., IEEE TII, 2024)</td><td>DP + shuffling mechanism, exponential noise for gradient indistinguishability</td><td>Flat architecture, no multimodal fusion, no bandwidth optimisation</td></tr>
                    <tr><td><strong>HED-FL</strong> (De Rango et al., PMC, 2023)</td><td>Hierarchical FL with dynamic device clustering at edge</td><td>No DP, generic data treatment, no multimodal awareness</td></tr>
                    <tr><td><strong>HCEF</strong> (Zhang et al., IEEE TMC, 2025)</td><td>Heterogeneity-aware edge FL with adaptive compression ratios</td><td>No privacy, no real-time inference target, optimises convergence not QoS</td></tr>
                    <tr><td><strong>RoPPFL</strong> (Zhou et al., CN, 2024)</td><td>Edge-based similarity aggregation + LDP dual defence</td><td>No multimodal fusion, no ≥50% uplink reduction, no latency QoS</td></tr>
                    <tr><td><strong>Mhaisen et al.</strong> (IEEE TNSE, 2022)</td><td>Dynamic user-edge assignment for non-IID convergence</td><td>Single modality (image), exposes class stats (violates ε≤1), no QoS</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {activeTab === 'gaps' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>Consolidated Research Gaps</h3></div>
              <div className="objective-grid">
                <div className="objective-card">
                  <div className="objective-id">Gap 1</div>
                  <div className="objective-title">No Multimodal Fusion in FL</div>
                  <div className="objective-target">
                    <span className="objective-target-label">Current Status:</span>
                    <span className="objective-target-value" style={{ color: 'var(--success)' }}>DEMONSTRATED (VitalDB)</span>
                  </div>
                  <div className="objective-method">Prior work treats all client data as generic gradient vectors — no notion of two heterogeneous modalities requiring different encoders, normalisations, and fusion strategies.</div>
                </div>
                <div className="objective-card">
                  <div className="objective-id">Gap 2</div>
                  <div className="objective-title">Privacy-Efficiency Trade-off</div>
                  <div className="objective-target">
                    <span className="objective-target-label">Current Status:</span>
                    <span className="objective-target-value" style={{ color: '#F59E0B' }}>Apparatus complete</span>
                  </div>
                  <div className="objective-method">Hierarchical FL omits DP; DP work omits hierarchy. Neither reports what the other costs. Head-only recipe + B4→B6 decomposition address this.</div>
                </div>
                <div className="objective-card">
                  <div className="objective-id">Gap 3</div>
                  <div className="objective-title">Real-time QoS Unaddressed</div>
                  <div className="objective-target">
                    <span className="objective-target-label">Current Status:</span>
                    <span className="objective-target-value" style={{ color: '#F59E0B' }}>Apparatus complete</span>
                  </div>
                  <div className="objective-method">Inference latency under deployment conditions rarely reported. ONNX export + portable benchmark built to answer this.</div>
                </div>
                <div className="objective-card">
                  <div className="objective-id">Gap 4</div>
                  <div className="objective-title">Static Privacy Budgets</div>
                  <div className="objective-target">
                    <span className="objective-target-label">Current Status:</span>
                    <span className="objective-target-value" style={{ color: '#EF4444' }}>NEGATIVE RESULT</span>
                  </div>
                  <div className="objective-method">Adaptive allocation measured worse than uniform. Composition tax across parameter groups dominates. Reported as negative result.</div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'objectives' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>Research Objectives (Quantified)</h3></div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>#</th><th>Objective</th><th>Target</th><th>Method</th></tr></thead>
                  <tbody>
                    <tr><td><strong>O1</strong></td><td>Reduce uplink communication</td><td>≥50% vs centralised FL</td><td>Two-tier aggregation + gradient sparsification + quantisation</td></tr>
                    <tr><td><strong>O2</strong></td><td>Preserve accuracy under privacy</td><td>≤2% loss at ε≤1</td><td>Head-only DP-SGD + RDP accounting + conformal calibration budget</td></tr>
                    <tr><td><strong>O3</strong></td><td>Real-time inference QoS</td><td>&lt;100ms P95 latency, &gt;99% reliability</td><td>ONNX export + portable benchmark + NS-3 per-update delivery</td></tr>
                    <tr><td><strong>O4</strong></td><td>Energy efficiency</td><td>≥20% savings per round</td><td>CloudSim Plus host power model, GPU charged to edge only</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box note">
                Thresholds are encoded in <code>scripts/check_objectives.py</code>. An objective with no evidence reports NOT MEASURED, never FAIL for an unrun experiment.
              </div>
            </motion.div>
          )}

          {activeTab === 'architecture' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>Architecture Vision (3-Layer)</h3></div>
              <div className="arch-diagram">
                <div className="arch-layer device">
                  <div className="arch-layer-label">Layer 1: IoT/End Devices</div>
                  <div className="arch-layer-content">
                    Multimodal sensing → on-device feature extraction → DP-SGD on head only → compressed head delta
                  </div>
                </div>
                <div className="arch-arrow">↓ Compressed head deltas</div>
                <div className="arch-layer edge">
                  <div className="arch-layer-label">Layer 2: Edge Servers (×2)</div>
                  <div className="arch-layer-content">
                    FedAvg over assigned clients → ASWA staleness weighting → edge model redistribution
                  </div>
                </div>
                <div className="arch-arrow">↓ Aggregated updates</div>
                <div className="arch-layer cloud">
                  <div className="arch-layer-label">Layer 3: Cloud Server</div>
                  <div className="arch-layer-content">
                    Final global aggregation (FedAvg over edges) → global model redistributed
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'roadmap' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Development Roadmap</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Month</th><th>Phase</th><th>Deliverables</th><th>Status</th></tr></thead>
                  <tbody>
                    <tr><td>Jan 2026</td><td>Phase 1</td><td>Literature review, gap analysis, objectives</td><td><span className="badge done">COMPLETE</span></td></tr>
                    <tr><td>Feb 2026</td><td>Phase 2–3</td><td>Simulator selection, environment setup</td><td><span className="badge done">COMPLETE</span></td></tr>
                    <tr><td>Mar 2026</td><td>Phase 4</td><td>Simulator implementation</td><td><span className="badge pending">CODE COMPLETE</span></td></tr>
                    <tr><td>Apr 2026</td><td>Phase 5</td><td>Model, privacy, deployment</td><td><span className="badge pending">CODE COMPLETE</span></td></tr>
                    <tr><td>May 2026</td><td>Phase 6</td><td>Joint evaluation, ablation, thesis, paper</td><td><span className="badge pending">CODE COMPLETE</span></td></tr>
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
