import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  BarChart3, GitCompare, TestTubes, Image, BookOpen,
  FileText, CheckCircle2
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Phase6() {
  const [activeTab, setActiveTab] = useState('scope')

  return (
    <>
      <div className="page-header">
        <h2>Phase 6 — Full Evaluation, Ablation & Paper Writing</h2>
        <p>Joint evaluation, ablation study, statistical analysis, thesis & publication</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)', marginBottom: 16 }}>
              <strong>Status:</strong> CODE COMPLETE — apparatus for joint evaluation, ablation, statistics, and figures built. All runs pending on current datasets (VitalDB + WEAR).
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'scope', icon: <FileText size={14} />, label: 'Scope' },
                { key: 'joint', icon: <BarChart3 size={14} />, label: 'Joint Eval' },
                { key: 'ablation', icon: <GitCompare size={14} />, label: 'Ablation Study' },
                { key: 'stats', icon: <TestTubes size={14} />, label: 'Statistics' },
                { key: 'figures', icon: <Image size={14} />, label: 'Figures' },
                { key: 'thesis', icon: <BookOpen size={14} />, label: 'Thesis & Paper' }
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
              <div className="section-header"><div className="section-number">1</div><h3>Phase 6 Scope & Deliverables</h3></div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Phase 5 produces a fully trained and deployed HFL-MM system with all QoS targets validated individually. Phase 6 performs: (a) JOINT evaluation — all 4 objectives simultaneously on the same run; (b) ABLATION — remove each component to quantify contribution; (c) STATISTICS — confidence intervals, significance tests; (d) VISUALIZATIONS — publication-quality plots; (e) WRITING — thesis chapters + journal paper.</p>
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>ID</th><th>Deliverable</th><th>Output</th></tr></thead>
                  <tbody>
                    <tr><td>D6.1</td><td>Joint Evaluation Results</td><td><code>results/phase6/joint_eval.csv</code></td></tr>
                    <tr><td>D6.2</td><td>Ablation Study Results</td><td><code>results/phase6/ablation.csv</code></td></tr>
                    <tr><td>D6.3</td><td>All Figures & Tables</td><td><code>results/phase6/figures/</code> (PDF+PNG)</td></tr>
                    <tr><td>D6.4</td><td>Statistical Analysis</td><td><code>results/phase6/statistics.txt</code></td></tr>
                    <tr><td>D6.5</td><td>Thesis Chapters (draft)</td><td><code>THESIS/chapters/</code></td></tr>
                    <tr><td>D6.6</td><td>Journal Paper (draft)</td><td><code>PAPER/hfl_mm_paper.pdf</code></td></tr>
                    <tr><td>D6.7</td><td>Reproducibility Package</td><td><code>README_reproduce.md</code></td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {activeTab === 'joint' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>Joint Evaluation Design</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>5 Systems Compared</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>ID</th><th>System</th><th>Description</th></tr></thead>
                  <tbody>
                    <tr><td>S0</td><td>CentralizedFL</td><td>All data on cloud, no privacy</td></tr>
                    <tr><td>S1</td><td>FlatFL_NoDP</td><td>FedAvg, single tier, no DP</td></tr>
                    <tr><td>S2</td><td>FL2DP</td><td>FedAvg + DP (ε=1), flat tier</td></tr>
                    <tr><td>S3</td><td>HED-FL</td><td>Hierarchical FL, no DP</td></tr>
                    <tr className="highlight-row"><td><strong>S4</strong></td><td><strong>HFL-MM (PROPOSED)</strong></td><td>2-tier + DP + multimodal fusion + head-only</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Joint Evaluation Metrics</h4>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>Obj.</th><th>Metric</th><th>Unit</th><th>Target (S4)</th></tr></thead>
                  <tbody>
                    <tr><td>O1</td><td>Uplink volume reduction</td><td>%</td><td>≥50% vs S0</td></tr>
                    <tr><td>O2</td><td>Accuracy loss vs S0</td><td>%</td><td>≤2% at ε=1</td></tr>
                    <tr><td>O3</td><td>P95 inference latency</td><td>ms</td><td>&lt;100ms</td></tr>
                    <tr><td>O4</td><td>Energy per training round</td><td>J</td><td>≥20% below S0</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Secondary Metrics</h4>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Update Reliability</div><div className="kv-value">&gt;99% per update</div></div>
                <div className="kv-item"><div className="kv-label">Convergence</div><div className="kv-value">≤25 rounds to 90%</div></div>
                <div className="kv-item"><div className="kv-label">ε Spent</div><div className="kv-value">≤1.0 after 20 rounds (including conformal calibration)</div></div>
                <div className="kv-item"><div className="kv-label">Deployed Size</div><div className="kv-value">&lt;5 MB (ONNX FP32)</div></div>
              </div>

              <div className="info-box note" style={{ marginTop: 16 }}>
                All systems use same devices, same Dirichlet-partitioned dataset, same NS-3-verified topology, same CloudSim-verified compute. Only the FL algorithm and model architecture differ.
              </div>
            </motion.div>
          )}

          {activeTab === 'ablation' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>Ablation Study</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                Remove one component at a time from the full system (A0 = S4), measure impact on all metrics. 5 ablation variants + full system = 6 configurations.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>5 Core Components</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Config</th><th>C1 Hierarchy</th><th>C2 DP</th><th>C3 Sparsify</th><th>C4 Quant</th><th>C5 Fusion</th><th>Purpose</th></tr></thead>
                  <tbody>
                    <tr className="highlight-row"><td><strong>A0</strong></td><td>✓</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td><td>Full system (S4)</td></tr>
                    <tr><td>A1</td><td style={{ color: '#EF4444' }}>✗</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td><td>Flat tier (no hierarchy)</td></tr>
                    <tr><td>A2</td><td>✓</td><td style={{ color: '#EF4444' }}>✗</td><td>✓</td><td>✓</td><td>✓</td><td>No DP (genuinely, not large ε)</td></tr>
                    <tr><td>A3</td><td>✓</td><td>✓</td><td style={{ color: '#EF4444' }}>✗</td><td>✓</td><td>✓</td><td>No sparsification</td></tr>
                    <tr><td>A4</td><td>✓</td><td>✓</td><td>✓</td><td style={{ color: '#EF4444' }}>✗</td><td>✓</td><td>Float32 (no quantization)</td></tr>
                    <tr><td>A5</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td><td style={{ color: '#EF4444' }}>✗</td><td>Unimodal (no fusion)</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Expected Key Insights</h4>
              <div className="insight-grid">
                <div className="insight-card">
                  <div className="insight-number">A1</div>
                  <div className="insight-content"><h4>Removing Hierarchy</h4><p>2.6× latency increase → violates &lt;100ms target. Hierarchy drives latency.</p></div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">A2</div>
                  <div className="insight-content"><h4>Removing DP</h4><p>~1% accuracy improvement but breaks privacy guarantee. DP costs ~1% — the head-only recipe is what makes this tolerable.</p></div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">A5</div>
                  <div className="insight-content"><h4>Removing Fusion</h4><p>&gt;3.5% accuracy loss → violates ≤2% target. Fusion is not optional for meeting the accuracy objective.</p></div>
                </div>
              </div>
              <div className="info-box success" style={{ marginTop: 16 }}>
                <strong>Expected conclusion:</strong> All 5 components are necessary — no component is redundant. Each removal causes at least one objective to fail.
              </div>
            </motion.div>
          )}

          {activeTab === 'stats' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>Statistical Analysis</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Multiple Seed Runs</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">All experiments run <strong>5 times</strong> (seeds: 42, 123, 456, 789, 1024). Report mean ± std for each metric. Demonstrates reproducibility and validates statistical significance.</p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Statistical Tests</h4>
              <div className="table-container" style={{ marginBottom: 16 }}>
                <table className="data-table">
                  <thead><tr><th>Test</th><th>Comparison</th><th>Method</th><th>Expected</th></tr></thead>
                  <tbody>
                    <tr><td>T1</td><td>Accuracy: HFL-MM vs Centralised</td><td>Paired t-test (5 seeds)</td><td>p &gt;0.05 (loss not significant)</td></tr>
                    <tr><td>T2</td><td>Comm reduction: HFL-MM vs Flat</td><td>One-sided z-test</td><td>p &lt;0.001 (reduction &gt;&gt;50%)</td></tr>
                    <tr><td>T3</td><td>Energy: HFL-MM vs Centralised</td><td>One-sided paired t-test</td><td>p &lt;0.001 (74.9% saving)</td></tr>
                    <tr><td>T4</td><td>Latency: HFL-MM P95</td><td>One-sided t-test on distribution</td><td>p &lt;0.01 (&lt;100ms)</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Confidence Intervals</h4>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Accuracy</div><div className="kv-value">± 0.3–0.8% (Dirichlet sampling variance)</div></div>
                <div className="kv-item"><div className="kv-label">Latency</div><div className="kv-value">± 2–5ms (ONNX runtime variance)</div></div>
                <div className="kv-item"><div className="kv-label">Energy</div><div className="kv-value">± 5–15J (mostly deterministic; variance from batch timing)</div></div>
              </div>
            </motion.div>
          )}

          {activeTab === 'figures' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Publication-Quality Figures</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                All figures via Matplotlib + Seaborn, colorblind-safe palette. Saved as PDF (vector) and PNG (300 DPI).<br/>
                Generator: <code>scripts/generate_all_figures.py</code>
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Fig.</th><th>Title</th><th>Type</th><th>Proves</th></tr></thead>
                  <tbody>
                    <tr><td>1</td><td>System Architecture Diagram</td><td>Block diagram</td><td>—</td></tr>
                    <tr><td>2</td><td>Convergence Curves (accuracy vs rounds)</td><td>Line plot (5 systems, ±std)</td><td>Convergence speed</td></tr>
                    <tr><td>3</td><td>Communication Volume Comparison</td><td>Bar chart</td><td>O1</td></tr>
                    <tr><td>4</td><td>Privacy-Accuracy Trade-off (ε sweep)</td><td>Line plot (log scale)</td><td>O2, IP-1</td></tr>
                    <tr><td>5</td><td>Inference Latency CDF</td><td>CDF plot (P50/P95/P99)</td><td>O3</td></tr>
                    <tr><td>6</td><td>Energy Consumption Breakdown</td><td>Stacked bar (3 layers)</td><td>O4</td></tr>
                    <tr><td>7</td><td>Ablation Study Radar Chart</td><td>Spider/radar (6 configs)</td><td>Component necessity</td></tr>
                    <tr><td>8</td><td>Non-IID Data Distribution</td><td>Heatmap</td><td>N-3 partition</td></tr>
                    <tr><td>9</td><td>Round-by-Round Privacy Budget ε(t)</td><td>Line plot (RDP accountant)</td><td>Budget compliance</td></tr>
                    <tr><td>10</td><td>Joint QoS Validation Summary</td><td>Grouped bar (4 targets)</td><td>All objectives</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {activeTab === 'thesis' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>Thesis & Journal Paper Structure</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Thesis (8 Chapters)</h4>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Ch.</th><th>Title</th><th>Content</th></tr></thead>
                  <tbody>
                    <tr><td>1</td><td>Introduction</td><td>Motivation, problem statement, O1–O4, contributions</td></tr>
                    <tr><td>2</td><td>Literature Review</td><td>5 papers × 4 gaps, position of proposed work</td></tr>
                    <tr><td>3</td><td>System Design</td><td>3-layer architecture, HFL-MM, DP mechanism, compression</td></tr>
                    <tr><td>4</td><td>Simulation Framework</td><td>NS-3, CloudSim Plus, shared config (Phases 3–4)</td></tr>
                    <tr><td>5</td><td>Experimental Setup</td><td>VitalDB + WEAR, non-IID partition, evaluation protocol</td></tr>
                    <tr><td>6</td><td>Results & Analysis</td><td>Convergence, communication, privacy-accuracy, latency, energy, ablation</td></tr>
                    <tr><td>7</td><td>Discussion</td><td>Comparison with SOTA, limitations, future work</td></tr>
                    <tr><td>8</td><td>Conclusion</td><td>Summary, all 4 objectives status</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Journal Paper Target</h4>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Primary</div><div className="kv-value">IEEE JBHI (Q1, IF ~7.7) — AI + healthcare systems</div></div>
                <div className="kv-item"><div className="kv-label">Secondary</div><div className="kv-value">npj Digital Medicine (Q1, IF ~15.2, Nature portfolio)</div></div>
                <div className="kv-item"><div className="kv-label">References</div><div className="kv-value">30–40 cited papers</div></div>
              </div>
            </motion.div>
          )}

        </motion.div>
      </div>
    </>
  )
}
