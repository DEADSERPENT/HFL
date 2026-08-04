import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Award, Shield, GitCompare, Beaker, XCircle,
  CheckCircle2, AlertTriangle
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function IPNovelty() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <>
      <div className="page-header">
        <h2>IP & Novelty Register v2.0</h2>
        <p>Three IP claims. Five novelty contributions. Evidence-bound.</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)', marginBottom: 16 }}>
              <strong>v2.0 Rule:</strong> Every entry is either evidence-bound (implemented, measurable, and bounded) or it is explicitly rejected. Nothing is claimed on the basis of intention or design alone. Where an entry is negative, it says so and says why.
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'overview', icon: <Award size={14} />, label: 'Status Summary' },
                { key: 'ip1', icon: <Shield size={14} />, label: 'IP-1 Head-Only DP' },
                { key: 'ip2', icon: <GitCompare size={14} />, label: 'IP-2 Two-Axis Decomp' },
                { key: 'ip3', icon: <Beaker size={14} />, label: 'IP-3 Conformal DP' },
                { key: 'n1', icon: <CheckCircle2 size={14} />, label: 'N-1 Paired Benchmark' },
                { key: 'n2', icon: <AlertTriangle size={14} />, label: 'N-2 Missingness' },
                { key: 'n3n5', icon: <CheckCircle2 size={14} />, label: 'N-3, N-4, N-5' },
                { key: 'excluded', icon: <XCircle size={14} />, label: 'Not Claimed' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* STATUS SUMMARY */}
          {activeTab === 'overview' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Claim Status at a Glance</h3></div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Claim</th><th>Status</th><th>Proving Experiment</th></tr></thead>
                  <tbody>
                    <tr><td><strong>IP-1</strong></td><td>Head-only DP fine-tuning for hierarchical multimodal FL</td><td style={{ color: '#F59E0B' }}>TO PROVE</td><td>ε sweep, both recipes, shared seeds</td></tr>
                    <tr><td><strong>IP-2</strong></td><td>Two-axis decomposition of a privacy result</td><td style={{ color: '#F59E0B' }}>TO PROVE</td><td>B4 vs B6; S2→S3→S4</td></tr>
                    <tr><td><strong>IP-3</strong></td><td>Exponential-mechanism DP quantile for conformal prediction</td><td style={{ color: '#F59E0B' }}>TO PROVE</td><td>Empirical coverage vs nominal</td></tr>
                    <tr className="highlight-row"><td><strong>N-1</strong></td><td>Genuinely-paired multimodal benchmark + both-arms test</td><td style={{ color: 'var(--success)' }}>PROVEN</td><td>Modality ablation → ablation_vitaldb.json</td></tr>
                    <tr><td><strong>N-2</strong></td><td>Missingness-as-signal encoding for intraoperative FL</td><td style={{ color: '#F59E0B' }}>TO PROVE</td><td>Mask-channel ablation (NOT YET WIRED)</td></tr>
                    <tr className="highlight-row"><td><strong>N-3</strong></td><td>Specialty-derived non-IID partition</td><td style={{ color: 'var(--success)' }}>PROVEN</td><td>Measured property of data</td></tr>
                    <tr><td><strong>N-4</strong></td><td>Composition tax of adaptive privacy</td><td style={{ color: '#EF4444' }}>NEGATIVE</td><td>Adaptive vs uniform; re-measure on current data</td></tr>
                    <tr className="highlight-row"><td><strong>N-5</strong></td><td>Case-level scoring for window-based clinical FL</td><td style={{ color: 'var(--success)' }}>PROVEN</td><td>Method in force across every result</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box success">
                <strong>3 PROVEN, 1 NEGATIVE (reported), 4 TO PROVE.</strong> All TO PROVE rows are produced by: <code>python scripts/run_pipeline.py --dataset vitaldb</code>
              </div>
            </motion.div>
          )}

          {/* IP-1 */}
          {activeTab === 'ip1' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><Shield size={16} /></div><h3>IP-1 — Head-Only DP Fine-Tuning</h3></div>
              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>The Claim</h4>
                <p className="section-description">A method for training a multimodal federated model under a strict privacy budget in which: (a) both modality encoders are pretrained on data disjoint from every client's private data and then frozen; (b) DP-SGD is applied ONLY to the late-fusion head; (c) only the head delta is aggregated hierarchically — such that a noise multiplier large enough to satisfy a strict budget, which prevents convergence when applied to the full network, is tolerated by the head.</p>
              </div>

              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)', marginBottom: 16 }}>
                <strong>THE PRECISE MECHANISM:</strong> Freezing does NOT reduce the noise. Sigma is determined by the budget, steps, and sampling rate — no dependence on the number of trained parameters. Freezing changes the OPTIMISATION GEOMETRY: a small head over frozen features is close to a linear probe — low-dimensional and well-conditioned — which DP-SGD optimises robustly at a sigma that destroys end-to-end training.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Why It Is Novel</h4>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                Parameter-efficient private fine-tuning is established in centralised settings. What is NOT established is its use as the mechanism that makes a strict budget viable in a HIERARCHICAL, MULTIMODAL federation — where the frozen/trained boundary determines what is transmitted and couples the privacy result to the communication result.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Scope Limit</h4>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 16 }}>
                Valid only when encoders are pretrained on data <strong>DISJOINT from client data</strong>. If pretrained on pooled client training data, ε is an upper bound, not a guarantee. Genuinely external public corpus required — single largest outstanding item.
              </div>

              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Evidence</div><div className="kv-value"><code>hfl_trainer.py --freeze_encoders</code>, <code>pretrain_encoders.py --public_data</code>, <code>epsilon_sweep.py → epsilon_sweep.csv</code></div></div>
                <div className="kv-item"><div className="kv-label">Proving</div><div className="kv-value">ε sweep runs BOTH recipes at every budget, shared seeds. Curves should WIDEN as ε tightens.</div></div>
                <div className="kv-item"><div className="kv-label">Would Refute</div><div className="kv-value">Curves failing to separate as ε tightens, or separating equally at all budgets.</div></div>
                <div className="kv-item"><div className="kv-label">Status</div><div className="kv-value" style={{ color: '#F59E0B' }}>TO PROVE — built and wired; run pending</div></div>
              </div>
            </motion.div>
          )}

          {/* IP-2 */}
          {activeTab === 'ip2' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><GitCompare size={16} /></div><h3>IP-2 — Two-Axis Decomposition of a Privacy Result</h3></div>
              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>The Claim</h4>
                <p className="section-description">An evaluation design that separates the two changes a hierarchical private FL system makes relative to flat private FL — the TOPOLOGY (adding an edge tier) and the RECIPE (restricting DP to a frozen-encoder head) — by constructing the two intermediate arms:</p>
                <div className="code-block" style={{ marginTop: 12 }}>
{`flat + full-model DP  →  flat + head-only DP     = recipe effect
flat + head-only DP   →  hierarchical + head-only = topology effect
hierarchical, no DP   →  hierarchical + DP        = privacy cost

All arms share data, partitions, seed, budget and sigma.`}
                </div>
              </div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Why it's not mere bookkeeping:</strong> A system that differs from its baseline in two ways simultaneously cannot attribute the gain. The intermediate arms convert an aggregate win into an attributable one.
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 16 }}>
                <strong>Critical:</strong> The no-privacy arm must be genuinely no-privacy — no clipping, no noise, no accountant. A large ε still applies per-sample gradient clipping and changes the optimisation. Using it understates the privacy cost.
              </div>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Evidence</div><div className="kv-value"><code>baselines.py</code> (B4 vs B6), <code>joint_eval.py</code> (S2→S3→S4), <code>hfl_trainer.py --no_dp</code></div></div>
                <div className="kv-item"><div className="kv-label">Would Refute</div><div className="kv-value">Intermediate contrasts summing to less than end-to-end difference — axes interact and cannot be attributed.</div></div>
                <div className="kv-item"><div className="kv-label">Status</div><div className="kv-value" style={{ color: '#F59E0B' }}>TO PROVE — all four arms built; run pending</div></div>
              </div>
            </motion.div>
          )}

          {/* IP-3 */}
          {activeTab === 'ip3' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><Beaker size={16} /></div><h3>IP-3 — Exponential-Mechanism DP Quantile for Conformal Prediction</h3></div>
              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>The Claim</h4>
                <p className="section-description">A federated conformal prediction procedure in which each client's local calibration quantile is released under DP using the EXPONENTIAL MECHANISM over the empirical score distribution, rather than by additive noise — with the calibration budget composed into the total reported ε.</p>
              </div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Why the mechanism choice is the claim:</strong> A quantile is a value drawn from the data, not an average. Additive noise at strict budget is comparable in magnitude to the spread of the statistic — the released quantile is dominated by noise. Exponential mechanism SELECTS a value from the observed distribution with utility-weighted probability. Measured: bias ~0.001 vs additive SD ~0.416 — three orders of magnitude better.
              </div>
              <div className="info-box success" style={{ marginBottom: 16 }}>
                <strong>Clinical significance:</strong> A point prediction is not actionable at the bedside. A calibrated set with stated coverage IS. Delivering that under formal privacy, in a federation, is the useful combination.
              </div>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Evidence</div><div className="kv-value"><code>model/utils/fedconform_hc.py</code></div></div>
                <div className="kv-item"><div className="kv-label">Proving</div><div className="kv-value">Calibrate on held-out split, measure EMPIRICAL COVERAGE on test split. Compare set sizes against additive mechanism.</div></div>
                <div className="kv-item"><div className="kv-label">Would Refute</div><div className="kv-value">Coverage falling below nominal (invalid) or set sizes including every label (vacuous).</div></div>
                <div className="kv-item"><div className="kv-label">Status</div><div className="kv-value" style={{ color: '#F59E0B' }}>TO PROVE — mechanism implemented; coverage run pending</div></div>
              </div>
            </motion.div>
          )}

          {/* N-1 */}
          {activeTab === 'n1' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><CheckCircle2 size={16} /></div><h3>N-1 — Genuinely-Paired Multimodal Clinical FL Benchmark</h3></div>
              <div className="stats-grid" style={{ marginBottom: 20 }}>
                <div className="stat-card"><div className="stat-label">Status</div><div className="stat-value green">PROVEN</div></div>
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Part (a) — The Benchmark</h4>
                <p className="section-description">Two modalities recorded by ONE system from ONE patient during ONE operation. Pairing is a property of the instrument — no pairing rule, no pairing artefact.</p>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginTop: 16, marginBottom: 12 }}>Part (b) — The Test Protocol</h4>
                <p className="section-description">Fusion must beat BOTH unimodal arms, with each arm RETRAINED on its own inputs rather than fed zeros. Beating only the weaker arm is not evidence.</p>
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Measured Result (VitalDB, centralised, non-private, 2 seeds)</h4>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>Arm</th><th>AUROC</th><th>AUPRC</th></tr></thead>
                  <tbody>
                    <tr><td>Signals only</td><td>0.8283</td><td>0.5281</td></tr>
                    <tr><td>Clinical only</td><td>0.7700</td><td>0.5022</td></tr>
                    <tr className="highlight-row"><td><strong>FUSED</strong></td><td><strong>0.8694</strong></td><td><strong>0.6343</strong></td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box success" style={{ marginBottom: 16 }}>
                Gain over best unimodal: <strong>+0.0411 AUROC, +0.1062 AUPRC = 14.1× seed SD</strong>
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>BOUNDED:</strong> WEAR is at ceiling (0.9976 AUROC). Its +0.0004 gain is a ceiling effect, NOT corroboration. The protocol writes this verdict into its own output.
              </div>
            </motion.div>
          )}

          {/* N-2 */}
          {activeTab === 'n2' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><AlertTriangle size={16} /></div><h3>N-2 — Missingness-as-Signal Encoding</h3></div>
              <div className="stats-grid" style={{ marginBottom: 20 }}>
                <div className="stat-card"><div className="stat-label">Status</div><div className="stat-value" style={{ color: '#F59E0B' }}>TO PROVE</div></div>
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Operating-theatre monitoring is intermittently observed. WHICH signals are being watched is itself clinically informative — an anaesthetist escalates monitoring when a patient deteriorates. Each of the 9 signal channels carries a parallel binary observed-mask, giving the 18-channel input.</p>
              </div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Contribution:</strong> Applying missingness-as-signal in a FEDERATED setting, where the missingness pattern is client-specific (different surgical specialties monitor differently) — so mask channels carry part of the non-IID structure.
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.03)' }}>
                <strong>Ablation NOT YET WIRED:</strong> Must train identical model on 9 signal channels alone (dropping 9 masks) and compare paired by seed. Until this exists, N-2 may NOT be stated as a contribution.
              </div>
            </motion.div>
          )}

          {/* N-3, N-4, N-5 */}
          {activeTab === 'n3n5' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>N-3, N-4, N-5 — Remaining Novelty Contributions</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>N-3 — Specialty-Derived Non-IID Partition <span className="badge done" style={{ marginLeft: 8 }}>PROVEN</span></h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Clients are surgical operation types. ICU base rate spans 3.2% to 50.7% — a sixteen-fold spread. This is a <strong>measured property of clinical practice</strong>, not a Dirichlet parameter.</p>
                <div className="info-box note" style={{ marginTop: 12 }}>
                  Operation types with too few positive cases are merged so every client holds ≥10 positives. Single-class clients have undefined AUROC and are silently dropped from averages.
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>N-4 — Composition Tax of Adaptive Privacy <span className="badge" style={{ marginLeft: 8, background: 'rgba(239, 68, 68, 0.1)', color: '#EF4444' }}>NEGATIVE</span></h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Adaptive allocation measured <strong>WORSE</strong> than uniform. Splitting one mechanism into per-group mechanisms does not split the cost proportionally — composition across groups charges more total budget. Holding ε fixed forces every group to be noisier.</p>
                <div className="info-box success" style={{ marginTop: 12 }}>
                  A clean negative result with mechanism-level explanation is publishable and useful. It is <strong>reported as negative, not omitted</strong>. Must be re-measured on current datasets.
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>N-5 — Case-Level Scoring for Window-Based Clinical FL <span className="badge done" style={{ marginLeft: 8 }}>PROVEN</span></h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">The model consumes 10-minute windows; the clinical question is about the operation. Windows within one case are correlated, so window-level metrics overstate effective sample size.</p>
                <div className="info-box note" style={{ marginTop: 12 }}>
                  Every result reports BOTH levels: window (optimised) and case (per-operation average). Split is by case — no operation spans train and test. <strong>Case-level is what should be quoted.</strong> Reporting only window-level on this data is a common and material overstatement.
                </div>
              </div>
            </motion.div>
          )}

          {/* NOT CLAIMED */}
          {activeTab === 'excluded' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><XCircle size={16} /></div><h3>Design History — Ideas Considered and Not Claimed</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                Recorded to preserve reasoning. <strong>NONE</strong> of these is a contribution and none may be cited as one.
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Idea</th><th>What Happened</th></tr></thead>
                  <tbody>
                    <tr><td><strong>Cross-modal gated attention</strong></td><td>Not built. Entangles streams → no separable head → forfeits IP-1.</td></tr>
                    <tr><td><strong>Edge knowledge distillation</strong></td><td>Built but not freeze-aware → updates frozen parameters → invalidates privacy accounting. Disabled in every run.</td></tr>
                    <tr><td><strong>Staleness-weighted aggregation</strong></td><td>Built and running, never ablated. Its effect is baked into hierarchical results — implementation detail, not a claim.</td></tr>
                    <tr><td><strong>Personalised local adaptation</strong></td><td>Built; no measurable pooled effect. Re-measure per-client on current data.</td></tr>
                    <tr><td><strong>Foundation-model adaptation</strong></td><td>Proposed in earlier planning. Not built. Future direction.</td></tr>
                    <tr><td><strong>Generative gradient-free training</strong></td><td>Proposed, not built. Future direction.</td></tr>
                    <tr><td><strong>Cohort-shuffling amplification</strong></td><td>Proposed, not built. Future direction.</td></tr>
                    <tr><td><strong>Contrastive patient similarity</strong></td><td>Proposed, not built. Future direction.</td></tr>
                    <tr><td><strong>Real-time deterioration alerting</strong></td><td>Proposed, not built. Future direction.</td></tr>
                    <tr><td><strong>Continual learning across classes</strong></td><td>Proposed, not built. Future direction.</td></tr>
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
