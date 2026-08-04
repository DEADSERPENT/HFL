import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  ClipboardList, FileText, BarChart3, TrendingUp, CheckCircle2,
  AlertTriangle, Award, Target
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function ProjectReport() {
  const [activeTab, setActiveTab] = useState('status')

  return (
    <>
      <div className="page-header">
        <h2>Overall Project Report</h2>
        <p>Execution Plan — What is built, how it will be run, and what each experiment will establish</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box success">
              <strong>Student:</strong> Samartha H V | MIT Bengaluru | Regd. 251580130019<br/>
              <strong>Guide:</strong> Dr. Shreyas J | <strong>Industry:</strong> Mr. Tejas J (Capgemini)<br/>
              <strong>Report Date:</strong> 2026-08-04 | <strong>Status:</strong> CODE COMPLETE, RUNS PENDING
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="info-box note">
              <strong>What this document is:</strong> The EXECUTION PLAN. Where a number exists it is quoted and its artifact named. Where an experiment is designed but not yet run, it says what it will measure and what outcome would count as meeting the objective — so the answer is defined in advance.
            </div>
          </motion.div>

          {/* Tabs */}
          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'status', icon: <ClipboardList size={14} />, label: 'Phase Status' },
                { key: 'objectives', icon: <Target size={14} />, label: 'Objective Traceability' },
                { key: 'experimental', icon: <BarChart3 size={14} />, label: 'Experimental Design' },
                { key: 'negative', icon: <AlertTriangle size={14} />, label: 'Negative Results' },
                { key: 'contributions', icon: <Award size={14} />, label: 'Contributions' }
              ].map(tab => (
                <button
                  key={tab.key}
                  className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* PHASE STATUS */}
          {activeTab === 'status' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">1</div>
                <h3>Phase Status</h3>
              </div>

              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Phase</th><th>Description</th><th>Status</th></tr></thead>
                  <tbody>
                    <tr><td>1</td><td>Research understanding, gap analysis, objectives</td><td><span className="badge done">COMPLETE</span></td></tr>
                    <tr><td>2</td><td>Simulator selection and justification</td><td><span className="badge done">COMPLETE</span></td></tr>
                    <tr><td>3</td><td>Environment setup (NS-3, CloudSim Plus, Python)</td><td><span className="badge done">COMPLETE</span></td></tr>
                    <tr><td>4</td><td>Simulator implementation</td><td><span className="badge pending">CODE COMPLETE · runs pending</span></td></tr>
                    <tr><td>5</td><td>Model, privacy, deployment</td><td><span className="badge pending">CODE COMPLETE · runs pending</span></td></tr>
                    <tr><td>6</td><td>Joint evaluation, ablation, statistics, figures</td><td><span className="badge pending">CODE COMPLETE · runs pending</span></td></tr>
                  </tbody>
                </table>
              </div>

              <div className="info-box note" style={{ marginBottom: 20 }}>
                <strong>"Code complete, runs pending"</strong> — every implementation requirement traced from the phase reports is satisfied and dataset-agnostic. What remains is execution on the current datasets.<br/><br/>
                Machine-checkable: <code>python tests/traceability.py --dataset vitaldb</code>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>The One Headline Result That Is Measured</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="table-container">
                  <table className="data-table">
                    <thead><tr><th>Arm</th><th>AUROC</th><th>AUPRC</th><th>Case AUROC</th><th>Case AUPRC</th></tr></thead>
                    <tbody>
                      <tr><td>Signals only</td><td>0.8283</td><td>0.5281</td><td>0.8590</td><td>0.6446</td></tr>
                      <tr><td>Clinical only</td><td>0.7700</td><td>0.5022</td><td>0.7713</td><td>0.4961</td></tr>
                      <tr className="highlight-row"><td><strong>FUSED</strong></td><td><strong>0.8694</strong></td><td><strong>0.6343</strong></td><td><strong>0.8875</strong></td><td><strong>0.6740</strong></td></tr>
                    </tbody>
                  </table>
                </div>
                <div className="info-box success" style={{ marginTop: 12 }}>
                  <strong>VitalDB, centralised, non-private, 2 seeds.</strong> Gain over best unimodal: +0.0411 AUROC, +0.1062 AUPRC = 14.1× seed SD. Fusion beats BOTH arms → Gap #1 demonstrated.
                </div>
              </div>
            </motion.div>
          )}

          {/* OBJECTIVE TRACEABILITY */}
          {activeTab === 'objectives' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>Objective Traceability</h3></div>

              <div className="info-box note" style={{ marginBottom: 20 }}>
                Each objective is owned by exactly one tool. Thresholds live in <code>scripts/check_objectives.py</code>. An objective with no evidence reports NOT MEASURED, never FAIL for an unrun experiment.
              </div>

              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Obj.</th><th>Pass Condition</th><th>Owner</th><th>Stage</th><th>How Measured</th></tr></thead>
                  <tbody>
                    <tr><td><strong>O1</strong></td><td>Uplink reduction ≥50%</td><td>NS-3</td><td>ns3_network</td><td>From MEASURED compressed uplink bytes vs centralised arm</td></tr>
                    <tr><td><strong>O2a</strong></td><td>ε ≤ 1</td><td>Training</td><td>proposed</td><td>Live privacy accountant at end of training, including conformal budget</td></tr>
                    <tr><td><strong>O2b</strong></td><td>Accuracy loss ≤ 2pp</td><td>ε sweep</td><td>epsilon_sweep</td><td>PAIRED comparison — same model, same data, same seed, DP on vs off</td></tr>
                    <tr><td><strong>O3a</strong></td><td>P95 latency &lt;100ms</td><td>ONNX</td><td>inference_bench</td><td>Portable runtime, CPU provider, end-to-end including conformal prediction</td></tr>
                    <tr><td><strong>O3b</strong></td><td>Update reliability &gt;99%</td><td>NS-3</td><td>ns3_network</td><td>PER UPDATE, not per run (compound decays fast)</td></tr>
                    <tr><td><strong>O4</strong></td><td>Energy saving ≥20%</td><td>CloudSim</td><td>cloudsim_energy</td><td>Host power model, GPU charged to edge only (end devices have no GPU)</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Research Gaps Status</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Gap</th><th>Description</th><th>Status</th></tr></thead>
                  <tbody>
                    <tr><td>1</td><td>No multimodal fusion in existing FL</td><td><span className="badge done">DEMONSTRATED on VitalDB</span></td></tr>
                    <tr><td>2</td><td>Privacy-efficiency trade-off unresolved</td><td><span className="badge pending">Apparatus complete, measurement pending</span></td></tr>
                    <tr><td>3</td><td>Real-time QoS not addressed</td><td><span className="badge pending">Apparatus complete (ONNX + benchmark)</span></td></tr>
                    <tr><td>4</td><td>Static privacy budgets</td><td><span className="badge" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#EF4444' }}>NEGATIVE — adaptive measured worse</span></td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* EXPERIMENTAL DESIGN */}
          {activeTab === 'experimental' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>Experimental Design — How Claims Will Be Separated</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Baselines B0–B6</h4>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Baseline</th><th>Description</th><th>Role</th></tr></thead>
                  <tbody>
                    <tr><td>B0</td><td>Centralized</td><td>Pooled data, no FL, no DP</td><td>Upper bound</td></tr>
                    <tr><td>B1</td><td>Local only</td><td>No federation</td><td>Lower bound</td></tr>
                    <tr><td>B2</td><td>FedAvg</td><td>FL, no privacy</td><td>Standard FL</td></tr>
                    <tr><td>B3</td><td>FedProx</td><td>+ heterogeneity handling</td><td>Robust FL</td></tr>
                    <tr><td>B4</td><td>DP-FedAvg</td><td>Flat FL + DP on WHOLE model</td><td>Prior art</td></tr>
                    <tr><td>B5</td><td>MOON</td><td>+ model-contrastive</td><td>SOTA FL</td></tr>
                    <tr className="highlight-row"><td>B6</td><td>DP-FedAvg-Head</td><td>Flat FL + DP on HEAD only</td><td>Isolates recipe from topology</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                <strong>B6 exists to remove a confound:</strong> The proposed system differs from B4 in TWO ways — edge tier AND head-only DP. B4→B6 isolates recipe effect; B6→HFL isolates topology effect.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Five-System Comparison</h4>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>System</th><th>Description</th></tr></thead>
                  <tbody>
                    <tr><td>S0</td><td>Centralized</td></tr>
                    <tr><td>S1</td><td>Flat FL, no DP</td></tr>
                    <tr><td>S2</td><td>Flat FL + DP</td></tr>
                    <tr><td>S3</td><td>Hierarchical, NO DP (genuinely no-privacy: no clip, no noise, no accountant)</td></tr>
                    <tr><td>S4</td><td>Proposed (hierarchical + head-only DP)</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Component Ablation A0–A5</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Remove one component at a time from the full system: C1 hierarchy · C2 differential privacy · C3 sparsification · C4 quantization · C5 multimodal fusion. Each arm is a single invocation with one flag changed.</p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Statistics</h4>
              <div className="info-box success">
                Contrasts are <strong>PAIRED by seed</strong>. Intervals are <strong>Student-t</strong> (3-5 seeds → normal approximation too narrow). Verdicts driven by whether CI contains zero, not p-value alone. Target ≥5 seeds; current ablation uses 2 (flagged as underpowered).
              </div>
            </motion.div>
          )}

          {/* NEGATIVE RESULTS */}
          {activeTab === 'negative' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>Negative & Null Results</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                Recorded because a thesis that reports only its successes is not reporting its work. All must be re-measured on current datasets before restating as findings.
              </div>

              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Finding</th><th>Status</th><th>Explanation</th></tr></thead>
                  <tbody>
                    <tr><td><strong>Adaptive per-layer privacy</strong></td><td style={{ color: '#EF4444' }}>NEGATIVE</td><td>Composition across parameter groups charges more total budget than single release. Adaptivity buys better allocation but pays in MORE noise; second effect dominates.</td></tr>
                    <tr><td><strong>Personalised local adaptation</strong></td><td style={{ color: '#6B7280' }}>NULL</td><td>No measurable pooled effect. May help extreme clients only — re-measure per-client, not pooled.</td></tr>
                    <tr><td><strong>Edge knowledge distillation</strong></td><td style={{ color: '#6B7280' }}>EXCLUDED</td><td>Not freeze-aware: would update frozen parameters, breaking privacy accounting. Disabled in every run.</td></tr>
                    <tr><td><strong>Cross-modal gated attention</strong></td><td style={{ color: '#6B7280' }}>NOT BUILT</td><td>Design-only. Entangles modality streams — no separable head left for DP-training. Conflicts with IP-1.</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Known Limitations</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Limitation</th></tr></thead>
                  <tbody>
                    <tr><td>L1</td><td><strong>Encoder pretraining provenance</strong> — the largest open item. If pretrained on pooled client data, ε is an upper bound. Genuinely external public corpus required.</td></tr>
                    <tr><td>L2</td><td><strong>WEAR cannot evidence fusion</strong> — at ceiling (0.9976). Pipeline dataset only.</td></tr>
                    <tr><td>L3</td><td><strong>Seed count</strong> — target ≥5; current ablation uses 2. Flagged as underpowered.</td></tr>
                    <tr><td>L4</td><td><strong>ASWA unablated</strong> — runs but effect not isolated. Not claimed.</td></tr>
                    <tr><td>L5</td><td><strong>CloudSim argument interface</strong> — unverified. O4 reports NOT MEASURED until wired.</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* CONTRIBUTIONS */}
          {activeTab === 'contributions' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Defensible Contributions</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                These are the contributions that survive the evidence-bound filter. C1 and C2 are the paper. C3 is a section. C4 is what makes the rest believable.
              </div>

              <div className="insight-grid">
                <div className="insight-card">
                  <div className="insight-number">C1</div>
                  <div className="insight-content">
                    <h4>Head-Only DP Fine-Tuning as a Recipe</h4>
                    <p>For hierarchical multimodal FL under strict budget. The same sigma becomes survivable because the optimisation geometry changes. Testable via ε sweep + B4→B6 decomposition.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">C2</div>
                  <div className="insight-content">
                    <h4>Genuinely Paired Multimodal FL Benchmark</h4>
                    <p>Fusion gain demonstrated against BOTH unimodal arms, with each arm retrained on its own inputs. VitalDB: +0.0411 AUROC, +0.1062 AUPRC = 14.1× seed SD.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">C3</div>
                  <div className="insight-content">
                    <h4>Negative Result on Adaptive Privacy</h4>
                    <p>Composition-tax explanation for why adaptive per-layer privacy allocation loses against uniform budget. Publishable as a negative result.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">C4</div>
                  <div className="insight-content">
                    <h4>Methodological Rigour as Artifact</h4>
                    <p>Leakage-controlled splits, per-dataset scoring units, objective checker reporting NOT MEASURED rather than guessing, traceability matrix binding every deliverable to code.</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Reproduction */}
          <motion.div variants={fadeUp} className="section" style={{ marginTop: 40 }}>
            <div className="section-header"><div className="section-number"><CheckCircle2 size={16}/></div><h3>How to Reproduce</h3></div>
            <div className="code-block">
{`cd SIMULATORS
python scripts/run_pipeline.py --dataset vitaldb    # 16 stages, resumable

# Inspect without running
python scripts/run_pipeline.py --dataset vitaldb --dry-run

# Check what exists
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
