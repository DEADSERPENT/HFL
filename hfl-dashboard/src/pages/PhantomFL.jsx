import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Sparkles, Brain, Shield, Zap, Network, Users, Cpu,
  AlertTriangle, CheckCircle2, XCircle
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function PhantomFL() {
  const [activeTab, setActiveTab] = useState('summary')

  return (
    <>
      <div className="page-header">
        <h2>Extended Innovations — Status & Evidence</h2>
        <p>Five proposed extensions to HFL-MM, and what each one is worth</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 20 }}>
              <strong>Purpose:</strong> Five extensions beyond the core HFL-MM system were proposed. This page records, for each one, three things kept strictly separate: <strong>PROPOSED</strong> (the idea), <strong>BUILT</strong> (whether it exists in the training path), <strong>MEASURED</strong> (what happened when tested). An idea that is proposed but not built is not a contribution. An idea that is built but measured to hurt is a negative result.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'summary', icon: <Sparkles size={14} />, label: 'Summary' },
                { key: 'i1', icon: <Network size={14} />, label: 'I1 — CMGA' },
                { key: 'i2', icon: <Shield size={14} />, label: 'I2 — Adaptive DP' },
                { key: 'i3', icon: <Zap size={14} />, label: 'I3 — ASWA' },
                { key: 'i4', icon: <Users size={14} />, label: 'I4 — FedKD-E' },
                { key: 'i5', icon: <Cpu size={14} />, label: 'I5 — pFAL' },
                { key: 'actual', icon: <CheckCircle2 size={14} />, label: 'Actual Contributions' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* SUMMARY TABLE */}
          {activeTab === 'summary' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Extension Status at a Glance</h3></div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Extension</th><th>Built?</th><th>Measured Outcome</th></tr></thead>
                  <tbody>
                    <tr><td><strong>I1</strong></td><td>Cross-modal gated attention fusion</td><td style={{ color: '#EF4444' }}>NO</td><td>n/a — no reference from training path</td></tr>
                    <tr><td><strong>I2</strong></td><td>Adaptive per-layer privacy allocation</td><td style={{ color: 'var(--success)' }}>YES</td><td style={{ color: '#EF4444' }}>WORSE than uniform budget</td></tr>
                    <tr><td><strong>I3</strong></td><td>Staleness-weighted aggregation (ASWA)</td><td style={{ color: 'var(--success)' }}>YES</td><td style={{ color: '#F59E0B' }}>UNABLATED — effect unknown</td></tr>
                    <tr><td><strong>I4</strong></td><td>Edge-side knowledge distillation</td><td style={{ color: 'var(--success)' }}>YES</td><td style={{ color: '#6B7280' }}>EXCLUDED — not freeze-aware</td></tr>
                    <tr><td><strong>I5</strong></td><td>Personalised local adaptation</td><td style={{ color: 'var(--success)' }}>YES</td><td style={{ color: '#6B7280' }}>NO MEASURABLE EFFECT</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)' }}>
                <strong>Of five proposed extensions, ZERO are currently defensible as positive contributions.</strong> One is unbuilt, one is negative, one is null, one is excluded, and one is untested. All measurements were obtained on a previous data pipeline and MUST be re-run on current datasets.
              </div>
            </motion.div>
          )}

          {/* I1 — CMGA */}
          {activeTab === 'i1' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><XCircle size={16} /></div><h3>I1 — Cross-Modal Gated Attention Fusion</h3></div>
              <div className="stats-grid" style={{ marginBottom: 20 }}>
                <div className="stat-card"><div className="stat-label">Built</div><div className="stat-value" style={{ color: '#EF4444' }}>NO</div></div>
                <div className="stat-card"><div className="stat-label">Measured</div><div className="stat-value" style={{ color: '#6B7280' }}>n/a</div></div>
                <div className="stat-card"><div className="stat-label">Status</div><div className="stat-value" style={{ color: '#6B7280' }}>Design Only</div></div>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Proposed</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Replace late concatenation with cross-attention between the two modality streams, so each encoder can attend to the other's representation and down-weight a missing or unreliable modality at inference time.</p>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Why Not Adopted — An Architectural Conflict</h4>
              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)' }}>
                The privacy design depends on the fusion head being a <strong>SMALL, SEPARABLE</strong> block on top of frozen encoders. Cross-attention <strong>entangles</strong> the two streams throughout the network — there is then no small separable head left to DP-train. The head-only recipe (IP-1, the strongest claim) cannot be applied. <strong>The two ideas are in direct conflict.</strong>
              </div>
              <div className="info-box note" style={{ marginTop: 16 }}>
                <strong>Honest position:</strong> I1 is not a contribution. It is a documented design alternative rejected for a stated architectural reason. Presenting it as an implemented innovation would be false.
              </div>
            </motion.div>
          )}

          {/* I2 — Adaptive DP */}
          {activeTab === 'i2' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><AlertTriangle size={16} /></div><h3>I2 — Adaptive Per-Layer Privacy Allocation</h3></div>
              <div className="stats-grid" style={{ marginBottom: 20 }}>
                <div className="stat-card"><div className="stat-label">Built</div><div className="stat-value green">YES</div></div>
                <div className="stat-card"><div className="stat-label">Measured</div><div className="stat-value" style={{ color: '#EF4444' }}>NEGATIVE</div></div>
                <div className="stat-card"><div className="stat-label">Verdict</div><div className="stat-value" style={{ color: '#EF4444' }}>Worse than uniform</div></div>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Proposed</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Group parameters by depth, allocate different clip and noise scale to each group — reasoning that layers differ in gradient scale and sensitivity.</p>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Why It Loses — The Composition Tax</h4>
              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)' }}>
                Splitting one mechanism into several does not split the privacy cost proportionally. Each group is its own release, and <strong>composition across groups charges more total budget</strong> than a single release. Holding overall ε fixed forces every group to be noisier. Adaptivity buys better ALLOCATION and pays in MORE noise overall — on this system the second effect dominates.
              </div>
              <div className="info-box success" style={{ marginTop: 16 }}>
                <strong>Value:</strong> A clean negative finding worth reporting. The literature proposes adaptive allocation frequently and ablates it against uniform rarely. Must be re-measured on current datasets.
              </div>
            </motion.div>
          )}

          {/* I3 — ASWA */}
          {activeTab === 'i3' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><Zap size={16} /></div><h3>I3 — Staleness-Weighted Aggregation (ASWA)</h3></div>
              <div className="stats-grid" style={{ marginBottom: 20 }}>
                <div className="stat-card"><div className="stat-label">Built</div><div className="stat-value green">YES</div></div>
                <div className="stat-card"><div className="stat-label">Ablated</div><div className="stat-value" style={{ color: '#F59E0B' }}>NO</div></div>
                <div className="stat-card"><div className="stat-label">Status</div><div className="stat-value" style={{ color: '#F59E0B' }}>Unablated</div></div>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Proposed</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Weight each client's contribution at the edge by how stale its update is, so a slow client's out-of-date update does not drag the edge model backwards.</p>
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>Problem:</strong> ASWA is ON in every hierarchical result — its effect is baked into those numbers and cannot be separated. It <strong>cannot be claimed as a contribution</strong> because no comparison against plain FedAvg weighting at the edge has been run.
              </div>
              <div className="info-box note" style={{ marginTop: 16 }}>
                <strong>What would settle it:</strong> An arm identical to the full system with staleness weighting replaced by uniform sample-count weighting, paired by seed. Until that exists, ASWA is an implementation detail, not a result.
              </div>
            </motion.div>
          )}

          {/* I4 — FedKD-E */}
          {activeTab === 'i4' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><Users size={16} /></div><h3>I4 — Edge-Side Knowledge Distillation (FedKD-E)</h3></div>
              <div className="stats-grid" style={{ marginBottom: 20 }}>
                <div className="stat-card"><div className="stat-label">Built</div><div className="stat-value green">YES</div></div>
                <div className="stat-card"><div className="stat-label">Used</div><div className="stat-value" style={{ color: '#EF4444' }}>DISABLED</div></div>
                <div className="stat-card"><div className="stat-label">Reason</div><div className="stat-value" style={{ color: '#EF4444' }}>Not freeze-aware</div></div>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Proposed</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">After edge aggregation, distil the aggregated edge model against its client models so the edge model absorbs client-specific knowledge that plain averaging discards.</p>
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)' }}>
                <strong>Excluded from every reported run:</strong> The distillation step is NOT freeze-aware. Under head-only recipe, encoders are frozen. The implementation would distil across parameters that are not being trained — producing updates to weights supposed to be fixed, <strong>silently invalidating both the freeze and the privacy accounting</strong>.
              </div>
              <div className="info-box note" style={{ marginTop: 16 }}>
                <strong>To make usable:</strong> Restrict distillation to trainable parameters, then ablate as a paired arm. Until then it contributes nothing and is not claimed.
              </div>
            </motion.div>
          )}

          {/* I5 — pFAL */}
          {activeTab === 'i5' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><Cpu size={16} /></div><h3>I5 — Personalised Local Adaptation (pFAL)</h3></div>
              <div className="stats-grid" style={{ marginBottom: 20 }}>
                <div className="stat-card"><div className="stat-label">Built</div><div className="stat-value green">YES</div></div>
                <div className="stat-card"><div className="stat-label">Measured</div><div className="stat-value" style={{ color: '#6B7280' }}>NULL</div></div>
                <div className="stat-card"><div className="stat-label">Effect</div><div className="stat-value" style={{ color: '#6B7280' }}>None (pooled)</div></div>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Proposed</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Give each client a small local adapter fine-tuned on its own data, so a client whose distribution differs from the federation average is not forced onto a single global model.</p>
              </div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Measured:</strong> No meaningful effect on the configuration tested. However, personalisation has the strongest case where client distributions differ most.
              </div>
              <div className="info-box success">
                <strong>Caveat worth keeping:</strong> VitalDB clients span 3.2% to 50.7% positive-class base rate — a substantially more heterogeneous federation. A method that helps the two extreme clients and does nothing for the middle seven shows no pooled effect while still being useful. Re-measure per-client, not pooled.
              </div>
            </motion.div>
          )}

          {/* ACTUAL CONTRIBUTIONS */}
          {activeTab === 'actual' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><CheckCircle2 size={16} /></div><h3>Where the Actual Contribution Lies</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                With all five extensions in the states above, the defensible contributions are <strong>not among them</strong>. They are:
              </div>
              <div className="insight-grid">
                <div className="insight-card">
                  <div className="insight-number">C1</div>
                  <div className="insight-content">
                    <h4>Head-Only DP Fine-Tuning as a Recipe</h4>
                    <p>For hierarchical multimodal FL under strict budget. The mechanism is not merely "freeze and train less" — the claim is that the same sigma becomes survivable because the optimisation geometry changes. Testable via B4→B6 + S3→S4.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">C2</div>
                  <div className="insight-content">
                    <h4>Genuinely Paired Multimodal FL Benchmark</h4>
                    <p>Fusion gain against BOTH unimodal arms, retrained on own inputs. VitalDB: +0.0411 AUROC, +0.1062 AUPRC = 14.1× seed SD.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">C3</div>
                  <div className="insight-content">
                    <h4>Negative Result on Adaptive Privacy</h4>
                    <p>Composition-tax explanation. The literature proposes adaptive allocation frequently and ablates it against uniform rarely.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">C4</div>
                  <div className="insight-content">
                    <h4>Methodological Rigour as Artifact</h4>
                    <p>Leakage-controlled splits, per-dataset scoring units, objective checker reporting NOT MEASURED rather than guessing, traceability matrix.</p>
                  </div>
                </div>
              </div>
              <div className="info-box success" style={{ marginTop: 20 }}>
                <strong>C1 and C2 are the paper. C3 is a section. C4 is what makes the rest believable.</strong>
              </div>
            </motion.div>
          )}

        </motion.div>
      </div>
    </>
  )
}
