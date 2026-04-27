import { motion } from 'framer-motion'
import {
  Radio, Zap, ShieldCheck, Clock, Target,
  FileText, TrendingUp, Globe, Calendar,
  Factory, Building2, HeartPulse, Package,
  ArrowRight
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
        <p>Hierarchical Federated Learning for Privacy-Aware, Low-Latency Multimodal IoT</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          {/* QoS Targets */}
          <motion.div variants={fadeUp}>
            <div className="qos-grid">
              <div className="qos-card pass">
                <div className="qos-icon"><Radio size={24} strokeWidth={2} /></div>
                <div className="qos-title">Comm. Reduction</div>
                <div className="qos-value">76.4%</div>
                <div className="qos-target">Target: ≥50% — PASS ✓ (Phase 4)</div>
              </div>
              <div className="qos-card pass">
                <div className="qos-icon"><Zap size={24} strokeWidth={2} /></div>
                <div className="qos-title">Energy Saving</div>
                <div className="qos-value">74.9%</div>
                <div className="qos-target">Target: ≥20% — PASS ✓ (Phase 4)</div>
              </div>
              <div className="qos-card pass">
                <div className="qos-icon"><ShieldCheck size={24} strokeWidth={2} /></div>
                <div className="qos-title">Update Reliability</div>
                <div className="qos-value">99.05%</div>
                <div className="qos-target">Target: &gt;99% — PASS ✓ (Phase 4)</div>
              </div>
              <div className="qos-card" style={{ borderColor: 'rgba(59, 130, 246, 0.3)', background: 'rgba(59, 130, 246, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#3B82F6' }}><Clock size={24} strokeWidth={2} /></div>
                <div className="qos-title">Inference Latency</div>
                <div className="qos-value" style={{ color: '#3B82F6' }}>&lt;100ms</div>
                <div className="qos-target">Target: &lt;100ms — Planned (Phase 5)</div>
              </div>
              <div className="qos-card" style={{ borderColor: 'rgba(59, 130, 246, 0.3)', background: 'rgba(59, 130, 246, 0.03)' }}>
                <div className="qos-icon" style={{ color: '#3B82F6' }}><Target size={24} strokeWidth={2} /></div>
                <div className="qos-title">Accuracy Loss</div>
                <div className="qos-value" style={{ color: '#3B82F6' }}>≤2%</div>
                <div className="qos-target">Target: ≤2% (ε=1) — Planned (Phase 5)</div>
              </div>
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
                Multimodal IoT devices generate large, heterogeneous data streams (images, audio, vibration, environmental sensors) that overload networks and risk privacy when centralized. Existing federated learning frameworks fail to simultaneously address <strong>multimodal fusion</strong>, <strong>hierarchical bandwidth optimization</strong>, <strong>formal differential privacy guarantees</strong>, and <strong>real-time QoS constraints</strong>. No unified framework jointly optimizes communication efficiency, privacy, inference latency, and energy for heterogeneous edge-cloud IoT deployments.
              </p>
            </div>
            <div className="info-box success">
              <strong>Formal Problem Statement:</strong> Design and validate a Hierarchical Federated Multimodal Learning (HFML) framework for edge-cloud IoT that enforces strict differential privacy (ε ≤ 1), achieves ≥50% uplink communication reduction through two-tier aggregation, maintains inference latency below 100 ms, and delivers ≥20% energy savings per training round — with model accuracy degradation limited to ≤2%.
            </div>
          </motion.div>

          {/* Research Objectives */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><Target size={16} /></div>
              <h3>Research Objectives</h3>
            </div>
            <div className="objective-grid">
              <div className="objective-card">
                <div className="objective-id">O1</div>
                <div className="objective-title">Reduce Uplink Communication</div>
                <div className="objective-target">
                  <span className="objective-target-label">Target:</span>
                  <span className="objective-target-value">≥50%</span>
                </div>
                <div className="objective-method">Two-tier aggregation + gradient sparsification + quantization</div>
              </div>
              <div className="objective-card">
                <div className="objective-id">O2</div>
                <div className="objective-title">Preserve Model Accuracy Under Privacy</div>
                <div className="objective-target">
                  <span className="objective-target-label">Target:</span>
                  <span className="objective-target-value">≤2% loss at ε≤1</span>
                </div>
                <div className="objective-method">Calibrated Gaussian noise + Moments Accountant + DP-SGD</div>
              </div>
              <div className="objective-card">
                <div className="objective-id">O3</div>
                <div className="objective-title">Real-time Inference QoS</div>
                <div className="objective-target">
                  <span className="objective-target-label">Target:</span>
                  <span className="objective-target-value">&lt;100ms</span>
                </div>
                <div className="objective-method">Edge-side inference + model pruning + async aggregation</div>
              </div>
              <div className="objective-card">
                <div className="objective-id">O4</div>
                <div className="objective-title">Energy Efficiency</div>
                <div className="objective-target">
                  <span className="objective-target-label">Target:</span>
                  <span className="objective-target-value">≥20% savings</span>
                </div>
                <div className="objective-method">Local computation trade-off + DVFS + reduced transmission frequency</div>
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
                  <span>Phase 1 — Research & Planning</span><span>100%</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '100%' }} /></div>
              </div>
              <div className="progress-bar-container" style={{ marginTop: 16 }}>
                <div className="progress-label">
                  <span>Phase 2 — Simulator Design</span><span>100%</span>
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
                  <span>Phase 4 — Simulator Implementation</span><span>100%</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '100%' }} /></div>
              </div>
              <div className="progress-bar-container" style={{ marginTop: 16 }}>
                <div className="progress-label">
                  <span>Phase 5 — Model Integration & Training</span><span style={{ color: '#3B82F6' }}>Planned</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '0%', background: 'linear-gradient(90deg, #3B82F6, #60A5FA)' }} /></div>
              </div>
              <div className="progress-bar-container" style={{ marginTop: 16 }}>
                <div className="progress-label">
                  <span>Phase 6 — Evaluation & Paper Writing</span><span style={{ color: '#3B82F6' }}>Planned</span>
                </div>
                <div className="progress-track"><div className="progress-fill" style={{ width: '0%', background: 'linear-gradient(90deg, #3B82F6, #60A5FA)' }} /></div>
              </div>
            </div>
          </motion.div>

          {/* Application Domains */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><Globe size={16} /></div>
              <h3>Application Domains</h3>
            </div>
            <div className="domain-grid">
              <div className="domain-card">
                <div className="domain-icon"><Factory size={32} strokeWidth={1.5} color="var(--primary)" /></div>
                <div className="domain-title">Industrial IoT</div>
                <div className="domain-desc">Camera + Vibration Fusion</div>
              </div>
              <div className="domain-card">
                <div className="domain-icon"><Building2 size={32} strokeWidth={1.5} color="var(--primary)" /></div>
                <div className="domain-title">Smart City</div>
                <div className="domain-desc">Traffic + Pollution Monitoring</div>
              </div>
              <div className="domain-card">
                <div className="domain-icon"><HeartPulse size={32} strokeWidth={1.5} color="var(--primary)" /></div>
                <div className="domain-title">Healthcare</div>
                <div className="domain-desc">Wearable + Imaging Data</div>
              </div>
            </div>
          </motion.div>

          {/* Development Roadmap */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><Calendar size={16} /></div>
              <h3>Development Roadmap (Jan – May 2026)</h3>
            </div>
            <div className="card">
              <div className="timeline">
                <div className="timeline-item completed">
                  <div className="timeline-title">Phase 1: Research & Planning</div>
                  <div className="timeline-period">January 2026</div>
                  <ul className="timeline-tasks">
                    <li>Literature synthesis (5 papers)</li>
                    <li>Gap identification (4 gaps)</li>
                    <li>Vision & Architecture maps</li>
                    <li>Roadmap & Evaluation Calendar</li>
                  </ul>
                </div>
                <div className="timeline-item completed">
                  <div className="timeline-title">Phase 2: Simulator Selection & Design</div>
                  <div className="timeline-period">February 2026</div>
                  <ul className="timeline-tasks">
                    <li>Justify NS-3 (network layer modeling)</li>
                    <li>Justify CloudSim Plus / EdgeCloudSim</li>
                    <li>Design simulation architecture</li>
                    <li>Define conceptual integration between simulators</li>
                  </ul>
                </div>
                <div className="timeline-item completed">
                  <div className="timeline-title">Phase 3: Environment Setup</div>
                  <div className="timeline-period">February 2026</div>
                  <ul className="timeline-tasks">
                    <li>NS-3 installation (Python bindings)</li>
                    <li>CloudSim Plus / EdgeCloudSim setup</li>
                    <li>Reproducibility & compatibility check</li>
                  </ul>
                </div>
                <div className="timeline-item completed">
                  <div className="timeline-title">Phase 4: Simulator Implementation</div>
                  <div className="timeline-period">March 2026</div>
                  <ul className="timeline-tasks">
                    <li>NS-3: Network topology, traffic modeling, QoS metrics</li>
                    <li>CloudSim: Edge-cloud resource modeling</li>
                    <li>Baseline experiments (centralized FL vs. flat FL)</li>
                  </ul>
                </div>
                <div className="timeline-item" style={{ borderLeftColor: '#3B82F6' }}>
                  <div className="timeline-title" style={{ color: '#3B82F6' }}>Phase 5: Model Integration & Training</div>
                  <div className="timeline-period">April 2026 — <span style={{ color: '#3B82F6', fontWeight: 600 }}>PLANNED</span></div>
                  <ul className="timeline-tasks">
                    <li>HFL-MM model (1D-CNN+GRU + MobileNetV3 + Late Fusion)</li>
                    <li>DP-SGD via Opacus (ε=1.0, Gaussian mechanism)</li>
                    <li>20× gradient compression (sparsification + quantization)</li>
                    <li>ONNX INT8 edge deployment (target: &lt;100ms P95 latency)</li>
                    <li>Validate O2 (accuracy) and O3 (latency) targets</li>
                  </ul>
                </div>
                <div className="timeline-item" style={{ borderLeftColor: '#3B82F6' }}>
                  <div className="timeline-title" style={{ color: '#3B82F6' }}>Phase 6: Evaluation & Paper Writing</div>
                  <div className="timeline-period">May 2026 — <span style={{ color: '#3B82F6', fontWeight: 600 }}>PLANNED</span></div>
                  <ul className="timeline-tasks">
                    <li>Joint evaluation (5 systems × 5 seeds)</li>
                    <li>Ablation study (6 configs × 5 seeds)</li>
                    <li>Publication-quality figures & statistical analysis</li>
                    <li>Thesis chapters + IEEE journal paper</li>
                  </ul>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Deliverables */}
          <motion.div variants={fadeUp} className="section">
            <div className="section-header">
              <div className="section-number"><Package size={16} /></div>
              <h3>Final Deliverables</h3>
            </div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Thesis Report</div>
                <div className="stat-value">May 2026</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Journal Paper</div>
                <div className="stat-value">Q1/Q2</div>
                <div className="stat-change target">Submission Target</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Simulation Codebase</div>
                <div className="stat-value">NS-3 + CloudSim</div>
              </div>
            </div>
          </motion.div>

        </motion.div>
      </div>
    </>
  )
}
