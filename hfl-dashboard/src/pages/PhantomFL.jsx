import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Sparkles, Brain, Shield, Zap, Network, Users, Cpu, BarChart3,
  Layers, GitCompare, Code, Rocket
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function PhantomFL() {
  const [activeTab, setActiveTab] = useState('motivation')

  return (
    <>
      <div className="page-header">
        <h2>PHANTOM-FL — Novel Model</h2>
        <p>Privacy-Hierarchical Adaptive Multimodal Transformer Optimized Network for Federated Learning</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'motivation', icon: <Sparkles size={14} />, label: 'Why PHANTOM-FL' },
                { key: 'innovations', icon: <Brain size={14} />, label: '5 Innovations' },
                { key: 'architecture', icon: <Layers size={14} />, label: 'Architecture' },
                { key: 'cmga', icon: <Network size={14} />, label: 'CMGA (I1)' },
                { key: 'sadp', icon: <Shield size={14} />, label: 'SADP (I2)' },
                { key: 'aswa', icon: <Zap size={14} />, label: 'ASWA (I3)' },
                { key: 'fedkd', icon: <Users size={14} />, label: 'FedKD-E (I4)' },
                { key: 'pfal', icon: <Cpu size={14} />, label: 'pFAL (I5)' },
                { key: 'comparison', icon: <GitCompare size={14} />, label: 'vs HFL-MM' },
                { key: 'training', icon: <Code size={14} />, label: 'Training Algo' },
                { key: 'onnx', icon: <Rocket size={14} />, label: 'ONNX & Claims' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* MOTIVATION */}
          {activeTab === 'motivation' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>Why a New Model — Limitations of HFL-MM</h3></div>
              <p className="section-description">HFL-MM succeeds at all QoS targets but has 5 fundamental architectural weaknesses that limit its novelty ceiling:</p>
              <div className="insight-grid">
                {[
                  { id: 'W1', title: 'Late Fusion is BLIND', desc: 'Encoders train independently. A vibration anomaly CANNOT influence how the spectrogram is processed — they never "talk" to each other.' },
                  { id: 'W2', title: 'Static Privacy Budget', desc: 'Same σ=1.1 noise for every parameter in every layer in every round. Over-noises early layers (hurting accuracy), under-noises sensitive layers.' },
                  { id: 'W3', title: 'Synchronous Aggregation', desc: 'All 20 devices must complete before edge aggregates. Bottlenecked by the SLOWEST device — the straggler problem.' },
                  { id: 'W4', title: 'Gradient FedAvg Fragile', desc: 'FedAvg averaging with α=0.5 Dirichlet causes gradient conflict (opposite directions). No conflict resolution mechanism.' },
                  { id: 'W5', title: 'No Personalization', desc: 'One global model for all 20 devices. A device in a steel mill trains the same model as one in a food processing plant.' }
                ].map(item => (
                  <div key={item.id} className="insight-card">
                    <div className="insight-number">{item.id}</div>
                    <div className="insight-content">
                      <h4>{item.title}</h4>
                      <p>{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* 5 INNOVATIONS */}
          {activeTab === 'innovations' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>PHANTOM-FL: 5 Core Innovations</h3></div>
              <p className="section-description">Each innovation directly solves one weakness. Each is independently publishable; together they form a unified system.</p>

              <div className="insight-grid">
                <div className="insight-card">
                  <div className="insight-number">I1</div>
                  <div className="insight-content">
                    <h4>Cross-Modal Gated Attention (CMGA)</h4>
                    <p>Modalities attend to each other during encoding — not just at fusion time. Bidirectional cross-attention with learned relevance gates.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">I2</div>
                  <div className="insight-content">
                    <h4>Sensitivity-Adaptive Differential Privacy (SADP)</h4>
                    <p>Different σ per layer per round, driven by per-parameter gradient sensitivity scores. Expected accuracy loss: ~0.8% vs HFL-MM's ~1.5%.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">I3</div>
                  <div className="insight-content">
                    <h4>Asynchronous Staleness-Weighted Aggregation (ASWA)</h4>
                    <p>Edge aggregates when 70% devices have responded — not all. Staleness discount factor: s_i = 1/(1+staleness). Up to 40% round time reduction.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">I4</div>
                  <div className="insight-content">
                    <h4>Federated Knowledge Distillation at Edge (FedKD-E)</h4>
                    <p>Edge distills local models using a small proxy dataset (500 samples, no labels). Avoids gradient conflict under non-IID conditions.</p>
                  </div>
                </div>
                <div className="insight-card">
                  <div className="insight-number">I5</div>
                  <div className="insight-content">
                    <h4>Personalized Federated Adapter Layers (pFAL)</h4>
                    <p>64KB adapter per device. FC(128→64)→GELU→FC(64→128). Only backbone is federated; adapter is device-local, never shared, no DP needed.</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* ARCHITECTURE */}
          {activeTab === 'architecture' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>PHANTOM-FL Architecture Diagram</h3></div>
              <div className="arch-diagram">
                <div style={{ display: 'flex', gap: 16, marginBottom: 8 }}>
                  <div className="arch-layer device" style={{ flex: 1 }}>
                    <div className="arch-layer-label">Modality A: Signal/Wearable</div>
                    <div className="arch-layer-content">(B, C_a, L)</div>
                  </div>
                  <div className="arch-layer edge" style={{ flex: 1 }}>
                    <div className="arch-layer-label">Modality B: Image/Spectrogram</div>
                    <div className="arch-layer-content">(B, 3, 224, 224)</div>
                  </div>
                </div>
                <div className="arch-arrow">↓</div>
                <div className="arch-layer cloud">
                  <div className="arch-layer-label">Unified Patch Tokenizer (shared weights)</div>
                  <div className="arch-layer-content">
                    Signal → Patch1D: stride 64 → N_a=16 patches → dim D=128<br/>
                    Image → Patch2D: 14×14 patches (ViT-style) → N_b=196 → proj D=128<br/>
                    + Learnable domain-type embeddings + positional embeddings
                  </div>
                </div>
                <div className="arch-arrow">↓ z_a: (B,17,128) | z_b: (B,197,128)</div>
                <div className="arch-layer device">
                  <div className="arch-layer-label">Cross-Modal Gated Attention (CMGA) × 3 blocks</div>
                  <div className="arch-layer-content">
                    Self-Attn(z_a) → z_a' | Self-Attn(z_b) → z_b'<br/>
                    Cross-Attn: z_a' queries z_b' → gate_a → z_a''<br/>
                    Cross-Attn: z_b' queries z_a' → gate_b → z_b''<br/>
                    gate = σ(W·cross_output) — learned relevance filter
                  </div>
                </div>
                <div className="arch-arrow">↓ CLS_a: (B,128) | CLS_b: (B,128)</div>
                <div className="arch-layer edge">
                  <div className="arch-layer-label">Fusion</div>
                  <div className="arch-layer-content">concat([CLS_a, CLS_b]) → LayerNorm(256) → FC(128) → GELU</div>
                </div>
                <div className="arch-arrow">↓ (B, 128)</div>
                <div className="arch-layer cloud" style={{ borderColor: 'var(--accent)' }}>
                  <div className="arch-layer-label">Personal Adapter (pFAL) — NEVER shared, NO DP</div>
                  <div className="arch-layer-content">FC(128→64) → GELU → FC(64→128) + residual</div>
                </div>
                <div className="arch-arrow">↓</div>
                <div className="arch-layer device">
                  <div className="arch-layer-label">Classification Head</div>
                  <div className="arch-layer-content">FC(128 → num_classes)</div>
                </div>
              </div>
            </motion.div>
          )}

          {/* CMGA */}
          {activeTab === 'cmga' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">I1</div><h3>Cross-Modal Gated Attention (CMGA)</h3></div>
              <div className="info-box success" style={{ marginBottom: 20 }}>
                Signal tokens attend over image tokens: "Which parts of the spectrogram are most relevant given what the raw signal is showing right now?" The 340Hz harmonic in the signal directly attends to the 340Hz band in the spectrogram.
              </div>
              <div className="code-block">
{`class CrossModalGatedAttention(nn.Module):
    def __init__(self, dim=128, n_heads=8, dropout=0.1):
        self.self_attn_a  = nn.MultiheadAttention(dim, n_heads)
        self.self_attn_b  = nn.MultiheadAttention(dim, n_heads)
        self.cross_attn_a = nn.MultiheadAttention(dim, n_heads)  # A→B
        self.cross_attn_b = nn.MultiheadAttention(dim, n_heads)  # B→A
        self.gate_a = nn.Linear(dim, dim)
        self.gate_b = nn.Linear(dim, dim)

    def forward(self, z_a, z_b):
        # Self-attention within each modality
        z_a' = self.norm1a(z_a + SelfAttn(z_a))
        z_b' = self.norm1b(z_b + SelfAttn(z_b))
        # Cross-attention with learned relevance gates
        z_a'' = norm(z_a' + σ(W_g · CrossAttn(Q=z_a', K=z_b', V=z_b')))
        z_b'' = norm(z_b' + σ(W_g · CrossAttn(Q=z_b', K=z_a', V=z_a')))
        return z_a'' + FFN(z_a''), z_b'' + FFN(z_b'')`}
              </div>
              <div className="info-box note" style={{ marginTop: 16 }}>
                <strong>Missing Modality:</strong> If modality A is absent (sensor failure): z_a = zero tensor, mask_a = all-True. Cross-attention returns zero weights → z_b processed via self-attention only. Graceful degradation.
              </div>
            </motion.div>
          )}

          {/* SADP */}
          {activeTab === 'sadp' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">I2</div><h3>Sensitivity-Adaptive Differential Privacy (SADP)</h3></div>
              <div className="info-box success" style={{ marginBottom: 20 }}>
                HFL-MM accuracy loss: ~1.5% at ε=1.0 → SADP accuracy loss: ~0.8% at same ε=1.0 budget. Early layers get 30% noise, classification head gets 100%.
              </div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`For each layer l after backward pass:
  s_l = ||∇_l||₂  (gradient L2 norm, before clipping)
  rank_l = argsort(s_l)  [lower = less sensitive]
  σ_l = σ_base × (s_l / max(s))^α   [α=0.5 default]

Example:
  Feature extractor Conv1D layer 1: s_l small → σ_l = 0.3 × σ_base
  Fusion FC layers: moderate → σ_l = 0.7 × σ_base  
  Classification head: s_l ≈ max → σ_l = 1.0 × σ_base (full noise)`}
              </div>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Base σ</div><div className="kv-value">1.1</div></div>
                <div className="kv-item"><div className="kv-label">α (steepness)</div><div className="kv-value">0.5</div></div>
                <div className="kv-item"><div className="kv-label">Min ratio</div><div className="kv-value">0.1 (floor: 10% base noise)</div></div>
                <div className="kv-item"><div className="kv-label">Accountant</div><div className="kv-value">RDP (Opacus, conservative)</div></div>
              </div>
            </motion.div>
          )}

          {/* ASWA */}
          {activeTab === 'aswa' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">I3</div><h3>Asynchronous Staleness-Weighted Aggregation (ASWA)</h3></div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`EDGE ASWA AGGREGATION:
  τ_min = floor(0.7 × N_cluster)  [wait for 70%, not 100%]

  WHILE round not complete:
    WHEN device i sends update (W_i, t_i, n_i):
      arrival_queue.push(i, W_i, t_i, n_i)

    IF len(arrival_queue) >= τ_min:
      FOR each (i, W_i, t_i, n_i) in queue:
        staleness_i = current_time - t_i
        s_i = 1 / (1 + staleness_i)    [staleness factor]
      W_edge = Σ_i (n_i × s_i × W_i) / Σ_i (n_i × s_i)
      BREAK`}
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Staleness</th><th>Factor s_i</th><th>Effect</th></tr></thead>
                  <tbody>
                    <tr><td>0s (on time)</td><td>1.0</td><td>Full weight</td></tr>
                    <tr><td>10s late</td><td>0.09</td><td>Barely weighted</td></tr>
                    <tr><td>Never arrives</td><td>—</td><td>Excluded</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box note" style={{ marginTop: 16 }}>
                <strong>Expected benefit:</strong> HFL-MM round blocked until slowest device (~50s). ASWA completes at 70% arrival (~30s). Up to 40% round time reduction.
              </div>
            </motion.div>
          )}

          {/* FedKD-E */}
          {activeTab === 'fedkd' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">I4</div><h3>Federated Knowledge Distillation at Edge (FedKD-E)</h3></div>
              <div className="info-box success" style={{ marginBottom: 20 }}>
                Gradient averaging: conflicts when Device 1 → "ball fault" and Device 2 → "normal" cancel out.<br/>
                Distillation: both models AGREE their respective classes have HIGH probability → edge model learns both.
              </div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`Ensemble teacher from received local models:
  teacher_logits(x) = Σ_i (w_i × softmax(W_i(x) / T)) / Σ w_i
  [temperature T=3.0 for soft labels]

DISTILL into edge student model:
  FOR k=1..50 steps on D_proxy (500 unlabeled samples):
    student_logits = softmax(W_edge(x) / T)
    loss_kd = T² × KLDivLoss(student_logits, teacher_logits)
    W_edge ← W_edge - lr × ∇ loss_kd

Privacy-safe: distillation on proxy data adds no DP cost
(D_proxy is not private data from any device)`}
              </div>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">Proxy Dataset</div><div className="kv-value">500 public/synthetic samples</div></div>
                <div className="kv-item"><div className="kv-label">KD Steps</div><div className="kv-value">50 per round</div></div>
                <div className="kv-item"><div className="kv-label">Temperature</div><div className="kv-value">T=3.0</div></div>
                <div className="kv-item"><div className="kv-label">Communication</div><div className="kv-value">Only head weights: 2.1 MB (25% of HFL-MM)</div></div>
              </div>
            </motion.div>
          )}

          {/* pFAL */}
          {activeTab === 'pfal' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">I5</div><h3>Personalized Federated Adapter Layers (pFAL)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Architecture</div><div className="kv-value">FC(128→64) → GELU → FC(64→128)</div></div>
                <div className="kv-item"><div className="kv-label">Params</div><div className="kv-value">16,576 ≈ 16K (0.5% of total)</div></div>
                <div className="kv-item"><div className="kv-label">Transmitted?</div><div className="kv-value">NEVER (stays on device)</div></div>
                <div className="kv-item"><div className="kv-label">DP Applied?</div><div className="kv-value">NO (local only, standard SGD)</div></div>
                <div className="kv-item"><div className="kv-label">Accuracy Boost</div><div className="kv-value">+2–4% per device</div></div>
                <div className="kv-item"><div className="kv-label">Init</div><div className="kv-value">Zeros (starts as identity)</div></div>
              </div>
              <div className="code-block">
{`class PersonalAdapter(nn.Module):
    def __init__(self, dim=128, bottleneck=64):
        self.down = nn.Linear(dim, bottleneck)
        self.up   = nn.Linear(bottleneck, dim)
        self.act  = nn.GELU()
        nn.init.zeros_(self.up.weight)
        nn.init.zeros_(self.up.bias)
    
    def forward(self, x):
        return x + self.up(self.act(self.down(x)))  # residual

During inference at device i:
  output = backbone(signal, image) + adapter_i(backbone(signal, image))`}
              </div>
            </motion.div>
          )}

          {/* HFL-MM vs PHANTOM-FL */}
          {activeTab === 'comparison' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>PHANTOM-FL vs HFL-MM — Head-to-Head</h3></div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Dimension</th><th>HFL-MM</th><th>PHANTOM-FL</th></tr></thead>
                  <tbody>
                    <tr><td>Fusion strategy</td><td>Late fusion (concatenation)</td><td>Cross-modal gated attention (CMGA)</td></tr>
                    <tr><td>Cross-modal interaction</td><td>None (blind encoders)</td><td>Bidirectional cross-attention</td></tr>
                    <tr><td>Privacy mechanism</td><td>Uniform σ=1.1</td><td>Per-layer adaptive σ_l (SADP)</td></tr>
                    <tr><td>FL aggregation</td><td>Gradient FedAvg (sync)</td><td>Knowledge Distill. at edge (FedKD-E)</td></tr>
                    <tr><td>Straggler handling</td><td>None (waits for all)</td><td>ASWA: 70% threshold + staleness weight</td></tr>
                    <tr><td>Personalization</td><td>None (global only)</td><td>pFAL: 64KB private adapter per device</td></tr>
                    <tr><td>Model params (total)</td><td>~3.0M</td><td>~4.2M + 16K adapter</td></tr>
                    <tr><td>ONNX INT8 size</td><td>~2.1 MB</td><td>~2.8 MB</td></tr>
                    <tr className="highlight-row"><td>Expected IIoT accuracy</td><td>~93%</td><td><strong>~95–97%</strong></td></tr>
                    <tr className="highlight-row"><td>Accuracy loss at ε=1</td><td>~1.5%</td><td><strong>~0.8% (SADP)</strong></td></tr>
                    <tr className="highlight-row"><td>Inference P95</td><td>~68ms ✓</td><td>~72ms ✓</td></tr>
                    <tr className="highlight-row"><td>Convergence rounds</td><td>~14–18</td><td><strong>~10–13</strong></td></tr>
                    <tr><td>Energy saving</td><td>~79%</td><td>~82%</td></tr>
                    <tr><td>Non-IID robustness</td><td>Moderate</td><td>HIGH (FedKD-E avoids conflict)</td></tr>
                    <tr><td>Novelty level</td><td>MEDIUM (4 contributions)</td><td><strong>VERY HIGH (5 contributions)</strong></td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box success">
                <strong>Strategic Recommendation:</strong> Option A (Safer): Implement HFL-MM fully; add PHANTOM-FL as "Section VII: Advanced Architecture" for extra novelty. Option B (Maximum Impact): Implement PHANTOM-FL directly (+3–4 weeks) for a substantially stronger paper with 5 contributions.
              </div>
            </motion.div>
          )}

          {/* TRAINING ALGORITHM */}
          {activeTab === 'training' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>PHANTOM-FL Training Algorithm (Pseudocode)</h3></div>
              <div className="code-block">
{`INITIALIZE:
  Global backbone W_g ← Xavier init (4.2M params)
  For each device i: local adapter A_i ← zeros (16K params)
  For each edge e: edge student model W_e ← W_g
  Proxy dataset D_proxy ← 500 public domain samples

FOR global round r = 1..15:

  STEP 1: DISTRIBUTE W_g → all edges → all devices
          Each device i: W_local_i ← W_g (backbone; keep A_i unchanged)

  STEP 2: DEVICE LOCAL TRAINING (parallel, asynchronous)
    FOR each device i (PARALLEL):
      // 2a: Train backbone with SADP
      FOR batch B_i in local_data_i:
        loss = CrossEntropy(W_local_i(batch, A_i), labels)
        backward()
        sadp.calibrate(W_local_i)  // per-layer σ_l
        CLIP each per-sample gradient to norm C=1.0
        sadp.inject_noise(W_local_i, C)
        optimizer.step()

      // 2b: Train personal adapter (no DP — local only)
      FOR epoch e_a = 1..3:
        loss_a = CrossEntropy(W_g(batch, A_i), labels)
        backward() → only A_i gradients
        optimizer_adapter.step()  // standard SGD, no noise

      // 2c: SEND (W_local_i, t_send, n_i) → Edge(cluster(i))

  STEP 3: EDGE ASWA + FedKD-E
    τ_min = floor(0.7 × |cluster_e|)
    WAIT until enough arrivals, compute staleness weights
    Teacher ensemble → Distill into edge student (50 steps on D_proxy)

  STEP 4: CLOUD AGGREGATION
    W_g ← FedAvg of all edge models (standard at cloud level)

  STEP 5: PRIVACY CHECK
    ε_spent = SADP_RDP_Accountant.compute(rounds=r, δ=1e-5)
    IF ε_spent > 1.0: STOP`}
              </div>
            </motion.div>
          )}

          {/* ONNX & CLAIMS */}
          {activeTab === 'onnx' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">7–8</div><h3>ONNX Deployment & Publication Claims</h3></div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>ONNX Export</h4>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">ONNX Opset</div><div className="kv-value">17 (attention ops support)</div></div>
                <div className="kv-item"><div className="kv-label">SDPA Backend</div><div className="kv-value">MATH (FlashAttention not ONNX-compatible)</div></div>
                <div className="kv-item"><div className="kv-label">FP32 Size</div><div className="kv-value">~16.8 MB</div></div>
                <div className="kv-item"><div className="kv-label">INT8 Size</div><div className="kv-value">~4.2 MB</div></div>
                <div className="kv-item"><div className="kv-label">FP32 Latency</div><div className="kv-value">~55–75ms P95</div></div>
                <div className="kv-item"><div className="kv-label">INT8 Latency</div><div className="kv-value">~65–82ms P95 (&lt;100ms ✓)</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>5 Novel Publication Claims</h4>
              <div className="insight-grid">
                {[
                  { id: 'C1', title: 'CMGA for Federated IoT', desc: 'First cross-modal attention FL model with formal DP. Prior art (ViLBERT, FLAVA) never in FL+DP+edge context.' },
                  { id: 'C2', title: 'Sensitivity-Adaptive DP (SADP)', desc: 'First per-layer adaptive DP in multimodal hierarchical FL. Prior theory (Mironov 2019) never applied in multimodal FL.' },
                  { id: 'C3', title: 'Edge-Level Knowledge Distillation', desc: 'FedKD-E: distillation at EDGE level (not global) + ASWA for async IoT. Novel combination.' },
                  { id: 'C4', title: 'ASWA for Hierarchical FL', desc: 'Async aggregation with staleness weighting per-edge for IoT-specific straggler tolerance.' },
                  { id: 'C5', title: 'pFAL — DP-Aware Personalization', desc: 'Separates adapter (private, no DP) from backbone (federated, DP). Adapter trains without DP since it never leaves device.' }
                ].map(item => (
                  <div key={item.id} className="insight-card">
                    <div className="insight-number">{item.id}</div>
                    <div className="insight-content"><h4>{item.title}</h4><p>{item.desc}</p></div>
                  </div>
                ))}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginTop: 24, marginBottom: 12 }}>Parameter Summary</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Component</th><th>Params</th><th>Federated?</th><th>DP Applied?</th></tr></thead>
                  <tbody>
                    <tr><td>Signal PatchTokenizer</td><td>~170K</td><td>YES</td><td>YES (SADP)</td></tr>
                    <tr><td>Image PatchTokenizer</td><td>~790K</td><td>YES</td><td>YES (SADP)</td></tr>
                    <tr><td>CMGA Blocks (×3)</td><td>~1,600K</td><td>YES</td><td>YES (SADP, lower σ)</td></tr>
                    <tr><td>Fusion FC</td><td>~33K</td><td>YES</td><td>YES (SADP, high σ)</td></tr>
                    <tr><td>Classification Head</td><td>~516</td><td>YES</td><td>YES (SADP, max σ)</td></tr>
                    <tr><td>Personal Adapter</td><td>~16K</td><td><strong>NO (local)</strong></td><td><strong>NO (never shared)</strong></td></tr>
                    <tr className="highlight-row"><td><strong>TOTAL</strong></td><td><strong>~4.2M</strong></td><td>Backbone: 4.2M</td><td>Adapter: 16K local</td></tr>
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
