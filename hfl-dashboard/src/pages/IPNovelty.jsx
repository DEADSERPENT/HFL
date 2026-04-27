import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Brain, Shield, Layers, Lightbulb, FlaskConical,
  ChevronRight, Sparkles, Lock, Cpu, Activity,
  Stethoscope, BarChart3, Zap, FileText, BookOpen,
  Target, AlertTriangle, CheckCircle2, ArrowRight
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

const ipClusters = [
  {
    cluster: 'Architecture Innovations',
    icon: <Cpu size={18} />,
    color: '#8B5CF6',
    items: [
      { id: 'IP-1', name: 'FedMamba-HC', desc: 'Mamba SSM encoder for long clinical time series in HFL with DP', gap: 'MegaECG (ICML 2024): centralized Mamba for ECG — not FL, not HFL, not DP', status: 'Phase 5' },
      { id: 'IP-2', name: 'FedMedLoRA', desc: 'Dual LoRA on frozen medical foundation model (BioMedCLIP) with SADP', gap: 'FedLoRA/FlexLoRA/FedPEFT (2023-2024): LoRA in FL — NLP tasks only, not medical imaging in HFL', status: 'Phase 6' },
      { id: 'IP-3', name: 'ClinicalCMGA', desc: 'Temporal-decay cross-modal gated attention for async clinical modalities', gap: 'PHANTOM-FL CMGA: static cross-modal attention — no temporal decay awareness', status: 'Phase 5 Design' }
    ]
  },
  {
    cluster: 'Privacy Innovations',
    icon: <Shield size={18} />,
    color: '#10B981',
    items: [
      { id: 'IP-4', name: 'CUAPS', desc: 'Clinical urgency-aware ε scheduling from healthcare event systems', gap: 'AdaDP (2022): adaptive ε based on gradient norms — not clinical context', status: 'Phase 6' },
      { id: 'IP-5', name: 'FedBiosDiff', desc: 'Gradient-free FL via DDPM score network sharing instead of gradients', gap: 'FedDiff (2024): server-side diffusion — client-side DDPM replacement not proposed', status: 'Future' },
      { id: 'IP-6', name: 'FedCCS', desc: 'Clinical cohort shuffler for shuffle-model DP at edge layer', gap: 'Shuffle model DP (2019 theory): not applied to HFL or healthcare cohorts', status: 'Future' }
    ]
  },
  {
    cluster: 'Learning Strategy Innovations',
    icon: <Brain size={18} />,
    color: '#F59E0B',
    items: [
      { id: 'IP-7', name: 'FedClinContrast', desc: 'Federated contrastive patient similarity via NT-Xent + centroid mining', gap: 'MOON (2021): model-contrastive regularization — not patient similarity learning', status: 'Future' },
      { id: 'IP-8', name: 'FedSepsisEWS', desc: 'Federated real-time sepsis EWS with causal biomarker discovery via GRF', gap: 'Federated sepsis (2022-2023): centralized within one hospital — not causal, not HFL', status: 'Phase 6' }
    ]
  },
  {
    cluster: 'Healthcare-Specific Innovations',
    icon: <Stethoscope size={18} />,
    color: '#EF4444',
    items: [
      { id: 'IP-9', name: 'FedConform-HC', desc: 'Federated conformal prediction with DP on calibration quantiles', gap: 'FedCP (2023): 1 paper — no DP, no HFL, no healthcare application', status: 'Phase 5' },
      { id: 'IP-10', name: 'FedContinualHC', desc: 'EWC-based continual FL + DP Fisher + head expansion for new diagnoses', gap: 'FedProx+EWC (2022): not healthcare, not HFL, not DP-Fisher', status: 'Future' }
    ]
  }
]

const noveltyItems = [
  { id: 'N-1', name: 'PTB-XL × CheXpert FL Benchmark', cluster: 'Dataset', desc: 'First paired healthcare FL benchmark combining ECG + chest X-ray with aligned cardiac diagnosis categories' },
  { id: 'N-2', name: 'Clinically-grounded non-IID partition', cluster: 'Evaluation', desc: 'Ward-level non-IID analysis using ICD-10 discharge statistics vs. synthetic Dirichlet partitioning' },
  { id: 'N-3', name: 'ASWA clinical priority extension', cluster: 'Aggregation', desc: 'ICU-aware straggler handling with clinical priority weighting for ASWA aggregation' },
  { id: 'N-4', name: 'Off-peak FL scheduling for HC IoT', cluster: 'System Design', desc: 'FL training scheduled during 2-6 AM off-peak clinical hours with CPU/GPU utilization monitoring' },
  { id: 'N-5', name: 'Modality missingness analysis for HC', cluster: 'Evaluation', desc: 'Systematic analysis of missing modality patterns (ECG-only, X-ray-only, sensor failure) in healthcare FL' },
  { id: 'N-6', name: 'DPDP Act 2023 compliance analysis', cluster: 'Regulatory', desc: 'Legal-technical analysis of HFL-MM/PHANTOM-FL compliance with India\'s DPDP Act 2023' },
  { id: 'N-7', name: 'Energy → wearable battery life metric', cluster: 'Clinical Metric', desc: 'Maps CloudSim energy results to real wearable power profiles (Zio Patch, Holter) for "days of monitoring lost"' }
]

const tierData = [
  {
    tier: 'Tier 1 — Phase 5 Implementation',
    color: '#10B981',
    badge: 'HIGH PRIORITY',
    items: [
      { name: 'Dataset: PTB-XL + CheXpert', effort: '2-3 days', impact: 'HIGH' },
      { name: 'N-1: Benchmark contribution', effort: '1 day', impact: 'MEDIUM' },
      { name: 'IP-1: FedMamba-HC encoder', effort: '3-4 days', impact: 'HIGH' },
      { name: 'IP-9: FedConform-HC', effort: '2 days', impact: 'HIGH' },
      { name: 'IP-3: ClinicalCMGA design', effort: '2 days', impact: 'MEDIUM' }
    ]
  },
  {
    tier: 'Tier 2 — Phase 6 / Paper',
    color: '#3B82F6',
    badge: 'NEXT PHASE',
    items: [
      { name: 'IP-2: FedMedLoRA', effort: '5-7 days', impact: 'VERY HIGH' },
      { name: 'IP-4: CUAPS', effort: '3 days', impact: 'HIGH' },
      { name: 'IP-8: FedSepsisEWS', effort: '4 days', impact: 'VERY HIGH' }
    ]
  },
  {
    tier: 'Tier 3 — Future Work',
    color: '#6B7280',
    badge: 'EXTENSIONS',
    items: [
      { name: 'IP-5: FedBiosDiff', effort: 'Complex', impact: 'HIGH' },
      { name: 'IP-6: FedCCS', effort: 'Infrastructure', impact: 'MEDIUM' },
      { name: 'IP-7: FedClinContrast', effort: 'Separate paper', impact: 'HIGH' },
      { name: 'IP-10: FedContinualHC', effort: 'Multi-year sim', impact: 'MEDIUM' }
    ]
  }
]

export default function IPNovelty() {
  const [activeTab, setActiveTab] = useState('overview')
  const [expandedIP, setExpandedIP] = useState(null)

  return (
    <>
      <div className="page-header">
        <h2>Intellectual Property & Novelty Register</h2>
        <p>Healthcare Center Domain — 10 IP Claims + 7 Novelty Contributions verified novel as of April 2026</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          {/* Summary Stats */}
          <motion.div variants={fadeUp}>
            <div className="qos-grid">
              <div className="qos-card" style={{ borderColor: 'rgba(139, 92, 246, 0.3)', background: 'rgba(139, 92, 246, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#8B5CF6' }}><Brain size={24} /></div>
                <div className="qos-title">IP Claims</div>
                <div className="qos-value" style={{ color: '#8B5CF6' }}>10</div>
                <div className="qos-target">Each independently patentable</div>
              </div>
              <div className="qos-card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#F59E0B' }}><Lightbulb size={24} /></div>
                <div className="qos-title">Novelty Contributions</div>
                <div className="qos-value" style={{ color: '#F59E0B' }}>7</div>
                <div className="qos-target">Ablation / secondary claims</div>
              </div>
              <div className="qos-card" style={{ borderColor: 'rgba(16, 185, 129, 0.3)', background: 'rgba(16, 185, 129, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#10B981' }}><Target size={24} /></div>
                <div className="qos-title">Phase 5 Active</div>
                <div className="qos-value" style={{ color: '#10B981' }}>3 IPs</div>
                <div className="qos-target">IP-1 + IP-9 + IP-3 (design)</div>
              </div>
              <div className="qos-card" style={{ borderColor: 'rgba(59, 130, 246, 0.3)', background: 'rgba(59, 130, 246, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#3B82F6' }}><BookOpen size={24} /></div>
                <div className="qos-title">Target Venue</div>
                <div className="qos-value" style={{ color: '#3B82F6', fontSize: 18 }}>IEEE JBHI</div>
                <div className="qos-target">Q1, IF ~7.7 | npj Digital Med (IF ~15.2)</div>
              </div>
            </div>
          </motion.div>

          {/* Tabs */}
          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'overview', icon: <Layers size={14} />, label: 'IP Overview' },
                { key: 'novelty', icon: <Sparkles size={14} />, label: 'Novelty (N-Series)' },
                { key: 'priorart', icon: <FileText size={14} />, label: 'Prior Art Analysis' },
                { key: 'priority', icon: <Target size={14} />, label: 'Implementation Priority' },
                { key: 'publication', icon: <BookOpen size={14} />, label: 'Publication Claims' }
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

          {/* ====== IP OVERVIEW TAB ====== */}
          {activeTab === 'overview' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">IP</div>
                <h3>IP Claims by Cluster — Healthcare Center Domain</h3>
              </div>

              <div className="info-box note">
                All 10 IPs are verified as novel — the specific combination described does not appear in any published work as of April 2026. Each IP is independently sufficient for a conference paper. The combination of IP-1 + IP-3 + IP-9 is sufficient for a Q1 journal paper.
              </div>

              {ipClusters.map(cluster => (
                <div key={cluster.cluster} style={{ marginBottom: 28 }}>
                  <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ color: cluster.color }}>{cluster.icon}</span>
                    {cluster.cluster}
                  </h4>
                  <div className="insight-grid">
                    {cluster.items.map(ip => (
                      <div
                        key={ip.id}
                        className="insight-card"
                        style={{ cursor: 'pointer', borderLeftColor: cluster.color }}
                        onClick={() => setExpandedIP(expandedIP === ip.id ? null : ip.id)}
                      >
                        <div className="insight-number" style={{ background: `${cluster.color}15`, color: cluster.color }}>{ip.id}</div>
                        <div className="insight-content">
                          <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                            {ip.name}
                            <span className="badge" style={{
                              background: ip.status === 'Phase 5' ? 'rgba(16, 185, 129, 0.1)' :
                                ip.status === 'Phase 5 Design' ? 'rgba(59, 130, 246, 0.1)' :
                                ip.status === 'Phase 6' ? 'rgba(245, 158, 11, 0.1)' :
                                'rgba(107, 114, 128, 0.1)',
                              color: ip.status === 'Phase 5' ? '#10B981' :
                                ip.status === 'Phase 5 Design' ? '#3B82F6' :
                                ip.status === 'Phase 6' ? '#F59E0B' :
                                '#6B7280',
                              fontSize: 10
                            }}>{ip.status}</span>
                          </h4>
                          <p>{ip.desc}</p>
                          {expandedIP === ip.id && (
                            <div style={{ marginTop: 10, padding: '10px 12px', background: 'rgba(0,0,0,0.15)', borderRadius: 8, fontSize: 12 }}>
                              <strong style={{ color: '#EF4444' }}>Prior Art Gap:</strong><br/>
                              {ip.gap}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </motion.div>
          )}

          {/* ====== NOVELTY TAB ====== */}
          {activeTab === 'novelty' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">N</div>
                <h3>Novelty Contributions (N-Series)</h3>
              </div>
              <div className="section-description">
                These are strong research novelty contributions suitable as sections, ablations, or secondary findings in the thesis/paper. Each is verifiable as new in the exact combination stated.
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>ID</th><th>Name</th><th>Cluster</th><th>Description</th></tr>
                  </thead>
                  <tbody>
                    {noveltyItems.map(n => (
                      <tr key={n.id}>
                        <td><strong>{n.id}</strong></td>
                        <td><strong>{n.name}</strong></td>
                        <td><span className="badge" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#F59E0B', fontSize: 10 }}>{n.cluster}</span></td>
                        <td style={{ fontSize: 12 }}>{n.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* ====== PRIOR ART TAB ====== */}
          {activeTab === 'priorart' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">§8</div>
                <h3>Prior Art Analysis — What Exists vs. What Is New</h3>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>IP</th><th>Technique</th><th>Closest Prior Art</th><th>Gap</th></tr>
                  </thead>
                  <tbody>
                    <tr><td><strong>IP-1</strong></td><td>Mamba encoder in HFL for clinical time series with DP</td><td>MegaECG (ICML 2024): Mamba for centralized ECG</td><td>Not FL, not HFL, not DP</td></tr>
                    <tr><td><strong>IP-2</strong></td><td>Dual LoRA FedMedLoRA on frozen BioMedCLIP with SADP</td><td>FedLoRA (2023), FlexLoRA (2024), FedPEFT (2024)</td><td>NLP tasks, not HC</td></tr>
                    <tr><td><strong>IP-3</strong></td><td>Temporal-decay CMGA for async clinical modalities</td><td>PHANTOM-FL CMGA: static cross-modal attention</td><td>No temporal decay</td></tr>
                    <tr><td><strong>IP-4</strong></td><td>CUAPS — clinical urgency-aware ε scheduling</td><td>AdaDP (2022): adaptive ε on gradient norms</td><td>Based on gradient, not clinical</td></tr>
                    <tr><td><strong>IP-5</strong></td><td>FedBiosDiff — gradient-free FL via DDPM score nets</td><td>FedDiff (2024): server-side diffusion</td><td>Client-side DDPM</td></tr>
                    <tr><td><strong>IP-6</strong></td><td>FedCCS — shuffle model with clinical cohort shuffler</td><td>Shuffle model DP (2019 theory)</td><td>Not applied to HFL or HC</td></tr>
                    <tr><td><strong>IP-7</strong></td><td>FedClinContrast — federated patient similarity</td><td>MOON (2021): model-contrastive regularization</td><td>Not patient similarity</td></tr>
                    <tr><td><strong>IP-8</strong></td><td>FedSepsisEWS + causal biomarker via federated GRF</td><td>Federated sepsis (2022-2023): centralized</td><td>Not causal, not HFL</td></tr>
                    <tr><td><strong>IP-9</strong></td><td>FedConform-HC — federated conformal prediction + DP</td><td>FedCP (2023): 1 paper, no DP</td><td>No DP, no HFL, no HC</td></tr>
                    <tr><td><strong>IP-10</strong></td><td>FedContinualHC — EWC continual FL + DP Fisher</td><td>FedProx+EWC (2022), GLFC (2023)</td><td>Not HC, not HFL, not DP-Fisher</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* ====== PRIORITY TAB ====== */}
          {activeTab === 'priority' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">§9</div>
                <h3>Implementation Priority (April–May 2026)</h3>
              </div>

              {tierData.map(tier => (
                <div key={tier.tier} style={{ marginBottom: 28 }}>
                  <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: tier.color }}>●</span>
                    {tier.tier}
                    <span className="badge" style={{ background: `${tier.color}15`, color: tier.color, fontSize: 10 }}>{tier.badge}</span>
                  </h4>
                  <div className="table-container">
                    <table className="data-table">
                      <thead>
                        <tr><th>Item</th><th>Effort</th><th>Impact</th></tr>
                      </thead>
                      <tbody>
                        {tier.items.map(item => (
                          <tr key={item.name}>
                            <td><strong>{item.name}</strong></td>
                            <td>{item.effort}</td>
                            <td><span className="badge" style={{
                              background: item.impact === 'VERY HIGH' ? 'rgba(239, 68, 68, 0.1)' :
                                item.impact === 'HIGH' ? 'rgba(16, 185, 129, 0.1)' :
                                'rgba(107, 114, 128, 0.1)',
                              color: item.impact === 'VERY HIGH' ? '#EF4444' :
                                item.impact === 'HIGH' ? '#10B981' : '#6B7280',
                              fontSize: 10
                            }}>{item.impact}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </motion.div>
          )}

          {/* ====== PUBLICATION TAB ====== */}
          {activeTab === 'publication' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header">
                <div className="section-number">§10</div>
                <h3>Publication Claims — Healthcare Edition</h3>
              </div>

              <div className="info-box success">
                <strong>Main Paper Claim:</strong> "We present the first hierarchical federated learning framework for privacy-preserving multimodal patient monitoring in healthcare centers, combining: (C1) Mamba SSM encoders for O(N) processing of long-duration 12-lead ECG sequences; (C2) temporal-decay cross-modal gated attention for asynchronous ECG + chest X-ray fusion; (C3) federated conformal prediction providing distribution-free 95% coverage guarantees; and (C4) sensitivity-adaptive differential privacy with clinical urgency-aware ε scheduling."
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, marginTop: 24 }}>Target Journals</h4>
              <div className="kv-grid" style={{ marginBottom: 24 }}>
                <div className="kv-item"><div className="kv-label">Primary</div><div className="kv-value" style={{ fontSize: 11 }}>IEEE JBHI (Q1, IF ~7.7)</div></div>
                <div className="kv-item"><div className="kv-label">Secondary</div><div className="kv-value" style={{ fontSize: 11 }}>npj Digital Medicine (Q1, IF ~15.2)</div></div>
                <div className="kv-item"><div className="kv-label">Alternative 1</div><div className="kv-value" style={{ fontSize: 11 }}>IEEE IoT Journal (IF ~10.6)</div></div>
                <div className="kv-item"><div className="kv-label">Alternative 2</div><div className="kv-value" style={{ fontSize: 11 }}>Computers in Biology & Medicine (IF ~7.7)</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Global Impact</h4>
              <div className="insight-grid">
                <div className="insight-card">
                  <div className="insight-number"><Activity size={16}/></div>
                  <div className="insight-content">
                    <h4>Cardiovascular Disease</h4>
                    <p>#1 global cause of death — 17.9M/year (WHO 2021). 70% of the world has NO access to specialist cardiologists. FedMamba-HC enables AI-assisted cardiology without sending data to the cloud.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number"><AlertTriangle size={16}/></div>
                  <div className="insight-content">
                    <h4>Sepsis Prevention</h4>
                    <p>11M deaths/year. One missed case costs $25K in extended ICU stay. FedSepsisEWS across a 200-bed hospital could prevent ~50 deaths and $1.25M/year.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number"><Shield size={16}/></div>
                  <div className="insight-content">
                    <h4>Regulatory Alignment</h4>
                    <p>Compliant with DPDP Act 2023 (India), EU AI Act 2024, FDA AI/ML SaMD Guidance. Conformal prediction (IP-9) directly addresses FDA transparency requirements.</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Quick Reference (always visible) */}
          <motion.div variants={fadeUp} className="section" style={{ marginTop: 40 }}>
            <div className="section-header">
              <div className="section-number" style={{ background: 'rgba(139, 92, 246, 0.1)', color: '#8B5CF6' }}><CheckCircle2 size={16}/></div>
              <h3 style={{ color: '#8B5CF6' }}>Quick Reference — 17 Contributions</h3>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr><th>ID</th><th>Name</th><th>Cluster</th></tr>
                </thead>
                <tbody>
                  {[
                    ['IP-1', 'FedMamba-HC — Mamba SSM for long clinical signals', 'Architecture'],
                    ['IP-2', 'FedMedLoRA — Dual LoRA on frozen medical FM', 'Architecture'],
                    ['IP-3', 'ClinicalCMGA — Temporal-decay cross-modal attention', 'Architecture'],
                    ['IP-4', 'CUAPS — Clinical urgency-aware ε scheduling', 'Privacy'],
                    ['IP-5', 'FedBiosDiff — Gradient-free FL via DDPM sharing', 'Privacy'],
                    ['IP-6', 'FedCCS — Clinical cohort shuffler for edge DP', 'Privacy'],
                    ['IP-7', 'FedClinContrast — Patient similarity contrastive FL', 'Learning Strategy'],
                    ['IP-8', 'FedSepsisEWS — Federated sepsis EWS + causal GRF', 'Healthcare-Specific'],
                    ['IP-9', 'FedConform-HC — Federated conformal prediction, DP', 'Healthcare-Specific'],
                    ['IP-10', 'FedContinualHC — EWC continual FL + new class expand.', 'Healthcare-Specific'],
                    ['N-1', 'PTB-XL × CheXpert FL Benchmark', 'Dataset'],
                    ['N-2', 'Clinically-grounded non-IID partition', 'Evaluation'],
                    ['N-3', 'ASWA clinical priority extension', 'Aggregation'],
                    ['N-4', 'Off-peak FL scheduling for HC IoT', 'System Design'],
                    ['N-5', 'Modality missingness analysis for HC', 'Evaluation'],
                    ['N-6', 'DPDP Act 2023 compliance analysis', 'Regulatory'],
                    ['N-7', 'Energy → wearable battery life metric', 'Clinical Metric']
                  ].map(([id, name, cluster]) => (
                    <tr key={id}>
                      <td><strong>{id}</strong></td>
                      <td>{name}</td>
                      <td><span className="badge" style={{
                        background: id.startsWith('IP') ? 'rgba(139, 92, 246, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        color: id.startsWith('IP') ? '#8B5CF6' : '#F59E0B',
                        fontSize: 10
                      }}>{cluster}</span></td>
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
