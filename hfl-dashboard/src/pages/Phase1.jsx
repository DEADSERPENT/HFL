import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  FileText, Target, Building, Map, CalendarDays,
  CheckCircle2, BarChart3, AlertTriangle,
  Camera, Mic, Activity, Thermometer, Cloud, Monitor, Smartphone,
  ArrowUpDown, FolderOpen, FlaskConical
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

const papers = [
  {
    id: 'Paper 1',
    title: 'FL2DP',
    authors: 'Gu et al.',
    source: 'IEEE Trans. Industrial Informatics, 2024',
    description: 'Combines Differential Privacy with a shuffling mechanism. Uses an exponential noise mechanism (instead of standard Gaussian/Laplace) to perturb gradients. Introduces a "shuffler" entity to break the identity link between users and gradients.',
    findings: 'Achieves "gradient indistinguishability" — better accuracy than standard DP while maintaining formal privacy guarantees.',
    gaps: [
      'Flat single-tier architecture — no hierarchical edge-cloud structure',
      'Does not address multimodal data fusion (treats all data as generic gradient vectors)',
      'No bandwidth optimization for high-volume multimodal streams (camera + vibration + audio)'
    ]
  },
  {
    id: 'Paper 2',
    title: 'HED-FL',
    authors: 'De Rango et al.',
    source: 'Pervasive and Mobile Computing, 2023',
    description: 'Hierarchical FL with dynamic device clustering at the edge. Reduces communication distance and energy cost by avoiding long-range transmissions to the cloud.',
    findings: 'Hierarchical clustering significantly extends IoT network lifetime vs. flat FL.',
    gaps: [
      'No Differential Privacy — privacy risks are unaddressed',
      'Treats all data generically — no awareness of heterogeneous QoS needs (high-bandwidth video vs. low-bandwidth sensor data)',
      'No multimodal fusion strategy'
    ]
  },
  {
    id: 'Paper 3',
    title: 'HCEF',
    authors: 'Zhang et al.',
    source: 'IEEE Trans. Mobile Computing, 2025',
    description: 'Heterogeneity-Aware Cooperative Edge-based Federated Averaging. Online control algorithm dynamically adjusts computation frequencies and gradient compression ratios per device to prevent straggler bottlenecks.',
    findings: 'Reduces training time and energy by adapting to each device\'s capability.',
    gaps: [
      'Focuses on compression, not privacy-preserving noise injection — no guarantee of ε ≤ 1',
      'Does not target real-time inference latency < 100ms for fused multimodal streams',
      'Optimizes convergence speed, not end-to-end QoS'
    ]
  },
  {
    id: 'Paper 4',
    title: 'RoPPFL',
    authors: 'Zhou et al.',
    source: 'Computer Networks, 2024',
    description: 'Edge nodes perform similarity-based robust aggregation to detect poisoned model updates, while Local Differential Privacy (LDP) protects user data. Dual-layer defense: privacy + robustness.',
    findings: 'Edge nodes can serve as effective security verifiers, reducing cloud computational burden.',
    gaps: [
      'Treats learning task as generic vector aggregation — no multimodal fusion',
      'Does not target ≥50% uplink traffic reduction',
      'Prioritizes security robustness over strict latency QoS (<100ms)'
    ]
  },
  {
    id: 'Paper 5',
    title: 'Mhaisen et al.',
    authors: 'Mhaisen et al.',
    source: 'IEEE Trans. Netw. Sci. Eng., 2022',
    description: 'Dynamic user-edge assignment in hierarchical FL based on data distribution statistics. Uses FedSGD at user-edge layer and FedAvg at edge-cloud layer to optimize convergence under non-IID data.',
    findings: 'Statistically optimized assignment reduces model weight divergence and accelerates convergence on MNIST and CIFAR-10.',
    gaps: [
      'Single modality only (image classification) — no multimodal extension',
      'Relies on exposing local class label statistics, which directly violates ε ≤ 1 privacy budget',
      'No cross-modal fusion, no QoS latency targets'
    ]
  }
]

export default function Phase1() {
  const [activeTab, setActiveTab] = useState('papers')

  return (
    <>
      <div className="page-header">
        <h2>Phase 1 — Research Understanding & Planning</h2>
        <p>Literature synthesis, gap analysis, objectives, architecture, and roadmap</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          {/* Phase Status */}
          <motion.div variants={fadeUp}>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Papers Analyzed</div>
                <div className="stat-value green">5</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Core Gaps Identified</div>
                <div className="stat-value">4</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Research Objectives</div>
                <div className="stat-value">4</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Status</div>
                <div className="stat-value green">Done ✓</div>
              </div>
            </div>
          </motion.div>

          {/* Tabs */}
          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'papers', icon: <FileText size={14} />, label: 'Paper Summaries' },
                { key: 'objectives', icon: <Target size={14} />, label: 'Objectives' },
                { key: 'architecture', icon: <Building size={14} />, label: 'Architecture' },
                { key: 'vision', icon: <Map size={14} />, label: 'Vision Map' },
                { key: 'calendar', icon: <CalendarDays size={14} />, label: 'Eval Calendar' }
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

          {/* Paper Summaries Tab */}
          {activeTab === 'papers' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">1</div>
                <h3>Paper Summaries & Gap Analysis</h3>
              </div>
              <div className="paper-grid">
                {papers.map((paper, index) => (
                  <motion.div
                    key={paper.id}
                    className="paper-card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="paper-number">{paper.id}</div>
                    <div className="paper-title">{paper.title}</div>
                    <div className="paper-source">{paper.authors} — {paper.source}</div>

                    <div className="paper-section-label">What it does</div>
                    <div className="paper-finding">{paper.description}</div>

                    <div className="paper-section-label">Key Findings</div>
                    <div className="paper-finding">{paper.findings}</div>

                    <div className="paper-section-label">Gaps for  Work</div>
                    <ul className="gap-list">
                      {paper.gaps.map((gap, gi) => (
                        <li key={gi}>{gap}</li>
                      ))}
                    </ul>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Objectives Tab */}
          {activeTab === 'objectives' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">3</div>
                <h3>Research Objectives (Quantified)</h3>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Objective</th>
                      <th>Target Metric</th>
                      <th>Method</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong style={{ color: 'var(--primary)' }}>O1</strong></td>
                      <td>Reduce uplink communication</td>
                      <td><strong>≥50% vs. centralized FL</strong></td>
                      <td>Two-tier aggregation + gradient sparsification + quantization</td>
                    </tr>
                    <tr>
                      <td><strong style={{ color: 'var(--primary)' }}>O2</strong></td>
                      <td>Preserve model accuracy under privacy</td>
                      <td><strong>≤2% accuracy loss at ε ≤ 1</strong></td>
                      <td>Calibrated Gaussian noise + Moments Accountant + DP-SGD</td>
                    </tr>
                    <tr>
                      <td><strong style={{ color: 'var(--primary)' }}>O3</strong></td>
                      <td>Real-time inference QoS</td>
                      <td><strong>&lt;100ms end-to-end latency</strong></td>
                      <td>Edge-side inference + model pruning + async aggregation</td>
                    </tr>
                    <tr>
                      <td><strong style={{ color: 'var(--primary)' }}>O4</strong></td>
                      <td>Energy efficiency</td>
                      <td><strong>≥20% savings per round</strong></td>
                      <td>Local computation trade-off + DVFS + reduced transmission frequency</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="info-box success">
                <strong>Consolidated Problem:</strong> Design and validate a Hierarchical Federated Multimodal Learning (HFML) framework for edge-cloud IoT that enforces strict differential privacy (ε ≤ 1), achieves ≥50% uplink communication reduction through two-tier aggregation, maintains inference latency below 100 ms, and delivers ≥20% energy savings per training round — with model accuracy degradation limited to ≤2%.
              </div>
            </motion.div>
          )}

          {/* Architecture Tab */}
          {activeTab === 'architecture' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">5</div>
                <h3>Three-Layer HFL Architecture</h3>
              </div>
              <div className="arch-diagram">
                <div className="arch-layer cloud">
                  <div className="arch-layer-label"><Cloud size={14} style={{marginRight:4}} /> Layer 3: Cloud Server</div>
                  <div className="arch-layer-content">
                    Global Model Aggregation (FedAvg on edge-aggregated updates) → Global Model <code>W_global</code> distributed back to all edge servers
                  </div>
                </div>
                <div className="arch-arrow">↕</div>
                <div className="arch-flow">Encrypted Edge Updates (W_edge) ↑ | ↓ W_global</div>

                <div className="arch-layer edge" style={{ marginTop: 16 }}>
                  <div className="arch-layer-label"><Monitor size={14} style={{marginRight:4}} /> Layer 2: Edge Server (Multiple per region)</div>
                  <div className="arch-layer-content">
                    Partial Aggregation (FedAvg on device updates) → Compression + Sparsification → Encrypt → Forward to Cloud → Distribute local model back to cluster devices
                  </div>
                </div>
                <div className="arch-arrow">↕</div>
                <div className="arch-flow">Encrypted Local Updates ↑ | ↓ Local Aggregated Model</div>

                <div className="arch-layer device" style={{ marginTop: 16 }}>
                  <div className="arch-layer-label"><Smartphone size={14} style={{marginRight:4}} /> Layer 1: IoT / End Devices (Heterogeneous)</div>
                  <div className="arch-layer-content">
                    <p style={{ marginBottom: 8 }}>Each device performs: <strong>Multimodal Data Collection → Feature Extraction → Local Model Training → DP Mechanism (ε≤1 noise addition)</strong></p>
                    <div className="eval-targets" style={{ marginTop: 8 }}>
                      <span className="eval-tag" style={{display:'inline-flex',alignItems:'center',gap:4}}><Camera size={12}/> Camera</span>
                      <span className="eval-tag" style={{display:'inline-flex',alignItems:'center',gap:4}}><Mic size={12}/> Microphone</span>
                      <span className="eval-tag" style={{display:'inline-flex',alignItems:'center',gap:4}}><Activity size={12}/> Vibration</span>
                      <span className="eval-tag" style={{display:'inline-flex',alignItems:'center',gap:4}}><Thermometer size={12}/> Env. Sensor</span>
                    </div>
                  </div>
                </div>

                <div className="info-box note" style={{ marginTop: 24 }}>
                  <strong>Data Flow:</strong> Raw Sensors → Feature Extraction → Local Train → DP Noise → Encrypt → Edge Aggregate → Cloud Aggregate
                </div>
              </div>
            </motion.div>
          )}

          {/* Vision Map Tab */}
          {activeTab === 'vision' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">4</div>
                <h3>Research Vision Map</h3>
              </div>
              <div className="vision-grid">
                <div className="vision-card">
                  <div className="vision-problem">
                    <h4><AlertTriangle size={13} style={{marginRight:4}}/> Multimodal IoT Data Overload</h4>
                    <p>Heterogeneous data streams overwhelm network capacity</p>
                  </div>
                  <div className="vision-arrow">→</div>
                  <div className="vision-solution">
                    <h4><CheckCircle2 size={13} style={{marginRight:4}}/> HFL Framework</h4>
                    <p>Two-Tier Aggregation for bandwidth optimization</p>
                  </div>
                </div>
                <div className="vision-card">
                  <div className="vision-problem">
                    <h4><AlertTriangle size={13} style={{marginRight:4}}/> Privacy Risks</h4>
                    <p>Raw data transmission to cloud exposes sensitive information</p>
                  </div>
                  <div className="vision-arrow">→</div>
                  <div className="vision-solution">
                    <h4><CheckCircle2 size={13} style={{marginRight:4}}/> Differential Privacy</h4>
                    <p>ε ≤ 1 Guarantee via Gaussian Mechanism</p>
                  </div>
                </div>
                <div className="vision-card">
                  <div className="vision-problem">
                    <h4><AlertTriangle size={13} style={{marginRight:4}}/> High Latency</h4>
                    <p>&gt;100ms end-to-end delay for multimodal inference</p>
                  </div>
                  <div className="vision-arrow">→</div>
                  <div className="vision-solution">
                    <h4><CheckCircle2 size={13} style={{marginRight:4}}/> Edge Inference</h4>
                    <p>Model Pruning + Async Aggregation</p>
                  </div>
                </div>
                <div className="vision-card">
                  <div className="vision-problem">
                    <h4><AlertTriangle size={13} style={{marginRight:4}}/> Energy Waste</h4>
                    <p>Device exhaustion from continuous training</p>
                  </div>
                  <div className="vision-arrow">→</div>
                  <div className="vision-solution">
                    <h4><CheckCircle2 size={13} style={{marginRight:4}}/> Local Compute Balancing</h4>
                    <p>DVFS + D2D Offloading</p>
                  </div>
                </div>
              </div>

              <div className="eval-targets">
                <span className="eval-tag">≥50% Comm. Reduction</span>
                <span className="eval-tag">ε≤1 Privacy</span>
                <span className="eval-tag">&lt;100ms Latency</span>
                <span className="eval-tag">≥20% Energy Saved</span>
              </div>
            </motion.div>
          )}

          {/* Evaluation Calendar Tab */}
          {activeTab === 'calendar' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">7</div>
                <h3>Experiment & Evaluation Calendar</h3>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Period</th>
                      <th>Experiments & Metrics</th>
                      <th>Target</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>Feb–Mar 2026</strong></td>
                      <td>
                        <strong>Baseline Experiments</strong><br/>
                        • Centralized FL (no privacy, no hierarchy)<br/>
                        • Flat FL with DP (FL2DP baseline)<br/>
                        • Hierarchical FL without DP (HED-FL baseline)<br/>
                        <em>Metrics: accuracy, comm. overhead, latency</em>
                      </td>
                      <td>—</td>
                    </tr>
                    <tr>
                      <td><strong>Mar 2026</strong></td>
                      <td>
                        <strong>Objective 1: Communication Reduction</strong><br/>
                        • Vary τ_e (edge aggregation frequency)<br/>
                        • Compare: centralized vs. 2-tier aggregation<br/>
                        • Test gradient sparsification ratios (10–50%)<br/>
                        • Test quantization (8-bit vs. 4-bit)
                      </td>
                      <td><span className="badge pass">≥50% uplink reduction</span></td>
                    </tr>
                    <tr>
                      <td><strong>Apr 2026</strong></td>
                      <td>
                        <strong>Objective 2: Privacy-Accuracy Trade-off</strong><br/>
                        • Vary epsilon (0.1, 0.5, 1.0, 2.0, 5.0)<br/>
                        • Measure accuracy on multimodal task<br/>
                        • Compare: Gaussian vs. Laplace vs. Exponential<br/>
                        • Privacy accounting across FL rounds
                      </td>
                      <td><span className="badge pass">≤2% accuracy loss at ε=1</span></td>
                    </tr>
                    <tr>
                      <td><strong>Apr 2026</strong></td>
                      <td>
                        <strong>Objective 3: Latency QoS Validation</strong><br/>
                        • NS-3: simulate WiFi / LTE / 5G channels<br/>
                        • Measure L_sensor + L_preproc + L_infer + L_comm + L_agg<br/>
                        • Compare: flat FL vs. hierarchical FL latency
                      </td>
                      <td><span className="badge pass">&lt;100ms end-to-end</span></td>
                    </tr>
                    <tr>
                      <td><strong>Apr–May 2026</strong></td>
                      <td>
                        <strong>Objective 4: Energy Efficiency</strong><br/>
                        • CloudSim: model computation energy per round<br/>
                        • Vary local vs. comm computation balance<br/>
                        • Test DVFS impact<br/>
                        • Compare energy: centralized vs. HFL
                      </td>
                      <td><span className="badge pass">≥20% savings per round</span></td>
                    </tr>
                    <tr className="highlight-row">
                      <td><strong>May 2026</strong></td>
                      <td>
                        <strong>Joint Evaluation</strong><br/>
                        • Full system: all 4 objectives simultaneously<br/>
                        • Dataset: non-IID multimodal distribution<br/>
                        • Ablation study: remove each component, measure degradation<br/>
                        • Generate: graphs, tables, comparison plots
                      </td>
                      <td><span className="badge done">All targets</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Datasets */}
              <div className="section-header" style={{ marginTop: 32 }}>
                <div className="section-number"><FolderOpen size={16}/></div>
                <h3>Datasets & Baselines</h3>
              </div>

              <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-header">
                  <div className="card-icon green"><BarChart3 size={18}/></div>
                  <div>
                    <div className="card-title">Datasets to Be Used</div>
                    <div className="card-subtitle">Data Partitioning: non-IID (Dirichlet distribution, α=0.5)</div>
                  </div>
                </div>
                <div className="kv-grid">
                  <div className="kv-item">
                    <div className="kv-label">IIoT</div>
                    <div className="kv-value" style={{ fontSize: 12 }}>CWRU Bearing (vibration) + custom camera frames</div>
                  </div>
                  <div className="kv-item">
                    <div className="kv-label">Smart City</div>
                    <div className="kv-value" style={{ fontSize: 12 }}>MISR / air quality + traffic video</div>
                  </div>
                  <div className="kv-item">
                    <div className="kv-label">Healthcare</div>
                    <div className="kv-value" style={{ fontSize: 12 }}>WESAD (wearable) + ChestX-ray14 (imaging)</div>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <div className="card-icon blue"><FlaskConical size={18}/></div>
                  <div>
                    <div className="card-title">Key Comparison Baselines</div>
                  </div>
                </div>
                <ol style={{ paddingLeft: 20, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 2 }}>
                  <li>Centralized Training (upper bound accuracy)</li>
                  <li>Flat FL (FedAvg, no hierarchy, no DP)</li>
                  <li>FL2DP (flat FL + DP, no hierarchy)</li>
                  <li>HED-FL (hierarchy + no DP)</li>
                  <li><strong style={{ color: 'var(--primary)' }}>PROPOSED: HFL + DP + multimodal fusion ( system)</strong></li>
                </ol>
              </div>
            </motion.div>
          )}

          {/* Phase 1 Summary */}
          <motion.div variants={fadeUp} className="section" style={{ marginTop: 40 }}>
            <div className="section-header">
              <div className="section-number"><CheckCircle2 size={16}/></div>
              <h3>Phase 1 Deliverables Summary</h3>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr><th>Deliverable</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {[
                    'Paper summaries (5 papers)',
                    'Problem statement',
                    'Quantified objectives',
                    'Research gaps (4 core)',
                    'Vision Map',
                    'Architecture Map (3-layer)',
                    'Development Roadmap',
                    'Experiment & Evaluation Calendar'
                  ].map(item => (
                    <tr key={item}>
                      <td>{item}</td>
                      <td><span className="badge done">✓ Done</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

        </motion.div>
      </div>
    </>
  )
}
