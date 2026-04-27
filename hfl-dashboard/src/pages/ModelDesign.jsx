import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Box, Code2, Layers, Shield, Shrink, HardDrive, Settings, Package,
  GitCompare, Cpu
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function ModelDesign() {
  const [activeTab, setActiveTab] = useState('selection')

  return (
    <>
      <div className="page-header">
        <h2>Model Design Guide</h2>
        <p>HFL-MM & PHANTOM-FL — Architecture selection, PyTorch implementation, DP-SGD, compression, ONNX</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="tabs" style={{ flexWrap: 'wrap' }}>
              {[
                { key: 'selection', icon: <Box size={14} />, label: 'Arch Selection' },
                { key: 'hflmm', icon: <Layers size={14} />, label: 'HFL-MM Code' },
                { key: 'dpsgd', icon: <Shield size={14} />, label: 'DP-SGD (Opacus)' },
                { key: 'compression', icon: <Shrink size={14} />, label: 'Compression' },
                { key: 'onnx', icon: <HardDrive size={14} />, label: 'ONNX Export' },
                { key: 'hyperparams', icon: <Settings size={14} />, label: 'Hyperparameters' },
                { key: 'params', icon: <Cpu size={14} />, label: 'Parameter Count' },
                { key: 'domains', icon: <GitCompare size={14} />, label: 'Domain Configs' },
                { key: 'deps', icon: <Package size={14} />, label: 'Dependencies' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* SELECTION */}
          {activeTab === 'selection' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1–2</div><h3>Architecture Selection & Constraints</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                <strong>Constraints:</strong> Opacus DP-SGD compatible (no BatchNorm), fits 12GB VRAM (RTX A2000), ONNX-exportable, &lt;100ms P95 inference, handles signal + image dual-modality, supports non-IID FL.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Architecture Candidates Evaluated</h4>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Architecture</th><th>Pros</th><th>Cons</th><th>Verdict</th></tr></thead>
                  <tbody>
                    <tr><td>Simple FC + ResNet18</td><td>Easy to implement</td><td>ResNet18 too heavy (11.7M), slow ONNX</td><td><span className="badge fail">REJECTED</span></td></tr>
                    <tr><td>1D-CNN + EfficientNet-B0</td><td>Efficient net = ONNX edge friendly</td><td>EfficientNetB0 uses Swish+SE → Opacus partial support issues</td><td><span className="badge fail">REJECTED</span></td></tr>
                    <tr><td>GRU + ViT-Tiny</td><td>Attention-based both</td><td>ViT-Tiny: 5.7M params → VRAM concern in FL × 20 batch</td><td><span className="badge fail">REJECTED</span></td></tr>
                    <tr><td>LSTM + MobileNetV2</td><td>Well-tested combo</td><td>LSTM not supported by opacus &lt;1.4, MobileNetV2 lower accuracy</td><td><span className="badge fail">REJECTED</span></td></tr>
                    <tr className="highlight-row"><td><strong>1D-CNN+GRU + MobileNetV3-Small</strong></td><td>All Opacus compat, 3M params, ~68ms P95</td><td>Late fusion limits cross-modal interaction</td><td><span className="badge pass">SELECTED ✓</span></td></tr>
                    <tr><td><strong>PHANTOM-FL (Patch + CMGA + SADP)</strong></td><td>5 innovations, 95-97% accuracy</td><td>+3-4 weeks implementation</td><td><span className="badge pass">RECOMMENDED</span></td></tr>
                  </tbody>
                </table>
              </div>

              <div className="arch-diagram">
                <div className="arch-layer device">
                  <div className="arch-layer-label">HFL-MM Selected Architecture</div>
                  <div className="arch-layer-content">
                    <strong>Encoder A:</strong> 1D-CNN(3 layers, Conv→GroupNorm→ReLU→MaxPool) + 2-layer GRU(128) → (B, 128)<br/>
                    <strong>Encoder B:</strong> MobileNetV3-Small (GroupNorm, frozen first 8 blocks) → (B, 576)<br/>
                    <strong>Fusion:</strong> concat(128 + 576) = 704 → FC(512) → FC(256) → FC(num_classes)
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* HFL-MM CODE */}
          {activeTab === 'hflmm' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>Complete Model Implementation (PyTorch)</h3></div>
              <div className="info-box warning" style={{ marginBottom: 16 }}>
                <strong>NOTE:</strong> GroupNorm replaces ALL BatchNorm layers throughout. This is MANDATORY for Opacus DP-SGD compatibility. Opacus will raise an error if BatchNorm layers are present.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Encoder A — 1D-CNN + GRU</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`class Encoder_A_1DCNN_GRU(nn.Module):
    # Input: (B, C_in, L) where C_in=1 (vibration) or 5 (WESAD)
    # Output: (B, 128) feature vector
    def __init__(self, in_channels=1, gru_hidden=128):
        self.conv1 = Conv1d(in_ch, 32, k=7, p=3) + GroupNorm(8, 32) + ReLU + MaxPool1d(4)
        self.conv2 = Conv1d(32, 64, k=5, p=2)    + GroupNorm(8, 64) + ReLU + MaxPool1d(4)
        self.conv3 = Conv1d(64, 128, k=3, p=1)   + GroupNorm(8, 128)+ ReLU + MaxPool1d(4)
        self.gru   = GRU(128, hidden=128, layers=2, batch_first=True, dropout=0.2)

    def forward(self, x):  # x: (B, C, 1024)
        x = conv1(x)       # (B, 32, 256)
        x = conv2(x)       # (B, 64, 64)
        x = conv3(x)       # (B, 128, 16)
        x = x.permute(0,2,1) # (B, 16, 128) for GRU
        _, h_n = gru(x)      # h_n: (2, B, 128)
        return h_n[-1]        # (B, 128)`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Encoder B — MobileNetV3-Small</h4>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`class Encoder_B_MobileNetV3(nn.Module):
    # Input: (B, 3, 224, 224)
    # Output: (B, 576) feature vector
    def __init__(self, pretrained=True, freeze_backbone=True):
        backbone = mobilenet_v3_small(weights='IMAGENET1K_V1')
        backbone = replace_bn_with_gn(backbone)  # Opacus compat
        self.features = backbone.features
        self.avgpool = backbone.avgpool
        if freeze_backbone: freeze first 8 feature blocks

    def forward(self, x):
        x = self.features(x)   # (B, 576, 7, 7)
        x = self.avgpool(x)    # (B, 576, 1, 1)
        return x.flatten(1)    # (B, 576)`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>HFL-MM Full Model</h4>
              <div className="code-block">
{`class HFL_MM(nn.Module):
    def __init__(self, in_channels_a=1, num_classes=4):
        self.encoder_a = Encoder_A_1DCNN_GRU(in_channels_a, 128)
        self.encoder_b = Encoder_B_MobileNetV3(pretrained=True)
        self.fusion = nn.Sequential(
            FC(704, 512) + LayerNorm(512) + ReLU + Dropout(0.3),
            FC(512, 256) + LayerNorm(256) + ReLU,
            FC(256, num_classes)
        )

    def forward(self, signal, image, mask_a=None, mask_b=None):
        feat_a = encoder_a(signal)  # (B, 128)
        feat_b = encoder_b(image)   # (B, 576)
        # Graceful degradation: zero-vector for missing modality
        if mask_a: feat_a = feat_a * mask_a.float().unsqueeze(1)
        if mask_b: feat_b = feat_b * mask_b.float().unsqueeze(1)
        fused = torch.cat([feat_a, feat_b], dim=1)  # (B, 704)
        return self.fusion(fused)                    # (B, num_classes)

File: SIMULATORS/model/hfl_mm_model.py`}
              </div>
            </motion.div>
          )}

          {/* DP-SGD */}
          {activeTab === 'dpsgd' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">4</div><h3>DP-SGD Training with Opacus</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Library</div><div className="kv-value">Opacus (Meta AI, official PyTorch DP)</div></div>
                <div className="kv-item"><div className="kv-label">Target ε</div><div className="kv-value">1.0</div></div>
                <div className="kv-item"><div className="kv-label">Target δ</div><div className="kv-value">1e-5</div></div>
                <div className="kv-item"><div className="kv-label">Gradient Clip C</div><div className="kv-value">1.0</div></div>
                <div className="kv-item"><div className="kv-label">Noise σ</div><div className="kv-value">~1.1 (auto-calibrated)</div></div>
                <div className="kv-item"><div className="kv-label">Accountant</div><div className="kv-value">RDP (Rényi DP)</div></div>
              </div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`from opacus import PrivacyEngine
from opacus.validators import ModuleValidator

# Validate model (checks for BN, unsupported layers)
model = ModuleValidator.fix(model)
errors = ModuleValidator.validate(model, strict=False)
assert len(errors) == 0

# Privacy engine
privacy_engine = PrivacyEngine()
model, optimizer, train_loader = privacy_engine.make_private_with_epsilon(
    module=model, optimizer=optimizer, data_loader=train_loader,
    epochs=local_epochs,        # 1 epoch per FL round
    target_epsilon=1.0, target_delta=1e-5,
    max_grad_norm=1.0,          # gradient clip norm C
)

# After each FL round:
epsilon = privacy_engine.get_epsilon(delta=1e-5)
print(f"Privacy budget spent: ε = {epsilon:.3f}")`}
              </div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Key Opacus Constraints</h4>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">✓ Supported</div><div className="kv-value">DataLoader with batch_size, GRU, BatchMemoryManager</div></div>
                <div className="kv-item"><div className="kv-label">✗ Not Supported</div><div className="kv-value">BatchNorm (use GroupNorm), weight-tied layers</div></div>
              </div>
            </motion.div>
          )}

          {/* COMPRESSION */}
          {activeTab === 'compression' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Gradient Compression</h3></div>
              <div className="info-box note" style={{ marginBottom: 16 }}>
                <strong>Why compression AFTER DP:</strong> DP noise is added to gradients first. Compression after DP = gradient already privacy-safe → compressing does not violate DP (post-processing theorem).
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Step 1: Top-k Sparsification with Error Feedback</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`class GradientCompressor:
    def compress(self, gradient_dict, round_id):
        for name, grad in gradient_dict.items():
            grad = grad + self.residuals[name]  # error feedback
            k = int(len(grad.flatten()) * 0.2)  # top 20%
            values, indices = torch.topk(grad.abs().flatten(), k)
            # Save residual (unselected gradients for next round)
            residual = grad.clone(); residual.flatten()[indices] = 0
            self.residuals[name] = residual
        → Keep 20% → 5× reduction`}
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Step 2: 8-bit Quantization</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`def quantize_8bit(values):
    scale = (v_max - v_min) / 255.0 + 1e-8
    quantized = ((values - v_min) / scale).round().clamp(0, 255).byte()
    → float32 → uint8 → 4× reduction`}
              </div>

              <div className="stats-grid">
                <div className="stat-card"><div className="stat-label">Top-k</div><div className="stat-value">5×</div><div className="stat-change target">sparsity=0.2</div></div>
                <div className="stat-card"><div className="stat-label">Quantization</div><div className="stat-value">4×</div><div className="stat-change target">float32→uint8</div></div>
                <div className="stat-card"><div className="stat-label">Combined</div><div className="stat-value green">20×</div><div className="stat-change positive">5× × 4×</div></div>
                <div className="stat-card"><div className="stat-label">Per Device</div><div className="stat-value">2.5 MB</div><div className="stat-change positive">was 10 MB in P4</div></div>
              </div>
            </motion.div>
          )}

          {/* ONNX */}
          {activeTab === 'onnx' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">6</div><h3>ONNX Export & Optimization</h3></div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`# Export
torch.onnx.export(model, (dummy_signal, dummy_image), "hfl_mm.onnx",
    opset_version=17, input_names=["signal", "image"],
    output_names=["logits"], dynamic_axes={...},
    do_constant_folding=True)

# INT8 Quantization
quantize_dynamic(model_input="hfl_mm.onnx", model_output="hfl_mm_int8.onnx",
    weight_type=QuantType.QInt8, per_channel=True)

# Benchmark (1000 runs + 100 warmup)
session = ort.InferenceSession("hfl_mm_int8.onnx",
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
→ latencies: Mean, P50, P95, P99, Max`}
              </div>
              <div className="stats-grid">
                <div className="stat-card"><div className="stat-label">FP32 ONNX</div><div className="stat-value">~8.4 MB</div></div>
                <div className="stat-card"><div className="stat-label">INT8 ONNX</div><div className="stat-value green">~2.1 MB</div></div>
                <div className="stat-card"><div className="stat-label">P95 Latency</div><div className="stat-value green">~68ms</div></div>
                <div className="stat-card"><div className="stat-label">Target</div><div className="stat-value">&lt;100ms ✓</div></div>
              </div>
            </motion.div>
          )}

          {/* HYPERPARAMETERS */}
          {activeTab === 'hyperparams' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">7</div><h3>Hyperparameter Reference Table</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Category</th><th>Parameter</th><th>Value</th><th>Justification</th></tr></thead>
                  <tbody>
                    <tr><td rowSpan="5"><strong>Architecture</strong></td><td>Encoder A type</td><td>1D-CNN+GRU</td><td>Time-series, low-mem</td></tr>
                    <tr><td>GRU hidden dim</td><td>128</td><td>Balance: capacity/speed</td></tr>
                    <tr><td>Encoder B type</td><td>MobileNetV3-Small</td><td>Edge-friendly, &lt;100ms</td></tr>
                    <tr><td>Fusion dim</td><td>[512, 256]</td><td>Reduce from 704</td></tr>
                    <tr><td>Normalization</td><td>GroupNorm</td><td>Required for Opacus</td></tr>
                    <tr><td rowSpan="5"><strong>FL Training</strong></td><td>Global rounds</td><td>20</td><td>Convergence target</td></tr>
                    <tr><td>Edge rounds (τ_e)</td><td>5</td><td>HED-FL optimal</td></tr>
                    <tr><td>Local epochs</td><td>1</td><td>Prevents client drift</td></tr>
                    <tr><td>Learning rate</td><td>1e-3</td><td>Adam default</td></tr>
                    <tr><td>Batch size</td><td>32</td><td>GPU memory safe</td></tr>
                    <tr><td rowSpan="4"><strong>Privacy</strong></td><td>Target ε</td><td>1.0</td><td>Privacy budget</td></tr>
                    <tr><td>Target δ</td><td>1e-5</td><td>= 1/dataset_size</td></tr>
                    <tr><td>Gradient clip C</td><td>1.0</td><td>Standard in DP-FL</td></tr>
                    <tr><td>Noise σ</td><td>~1.1</td><td>Auto-set by Opacus</td></tr>
                    <tr><td rowSpan="3"><strong>Compression</strong></td><td>Sparsity k</td><td>0.20</td><td>Top-20% gradients</td></tr>
                    <tr><td>Quant bits</td><td>8</td><td>uint8, 4× reduction</td></tr>
                    <tr><td>Error feedback</td><td>Yes</td><td>Prevents accuracy drop</td></tr>
                    <tr><td rowSpan="3"><strong>ONNX</strong></td><td>Opset</td><td>17</td><td>PyTorch 2.x compat</td></tr>
                    <tr><td>Quant type</td><td>QInt8</td><td>Dynamic quantization</td></tr>
                    <tr><td>Warmup runs</td><td>100</td><td>JIT compilation cache</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* PARAMETER COUNT */}
          {activeTab === 'params' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">8</div><h3>Model Parameter Count & Sizes</h3></div>
              <div className="table-container" style={{ marginBottom: 24 }}>
                <table className="data-table">
                  <thead><tr><th>Component</th><th>Params</th><th>% of Total</th><th>Notes</th></tr></thead>
                  <tbody>
                    <tr><td>Encoder A (1D-CNN)</td><td>~200K</td><td>6.5%</td><td>Conv layers + GN</td></tr>
                    <tr><td>Encoder A (GRU)</td><td>~220K</td><td>7.2%</td><td>2-layer GRU (128 hidden)</td></tr>
                    <tr><td>Encoder B (MobileNetV3)</td><td>~2,500K</td><td>81.3%</td><td>1,000K trainable, 1,500K frozen</td></tr>
                    <tr><td>Fusion head</td><td>~150K</td><td>4.9%</td><td>FC512→FC256→FC_cls</td></tr>
                    <tr className="highlight-row"><td><strong>Total trainable</strong></td><td><strong>~1,570K</strong></td><td>100%</td><td>—</td></tr>
                    <tr className="highlight-row"><td><strong>Total parameters</strong></td><td><strong>~3,070K</strong></td><td>—</td><td>—</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="stats-grid">
                <div className="stat-card"><div className="stat-label">PyTorch .pt</div><div className="stat-value">~12 MB</div><div className="stat-change target">params + optimizer</div></div>
                <div className="stat-card"><div className="stat-label">ONNX FP32</div><div className="stat-value">~8.4 MB</div><div className="stat-change target">params only</div></div>
                <div className="stat-card"><div className="stat-label">ONNX INT8</div><div className="stat-value green">~2.1 MB</div><div className="stat-change positive">4× compression</div></div>
                <div className="stat-card"><div className="stat-label">Gradient/round</div><div className="stat-value">~2.5 MB</div><div className="stat-change positive">20× compressed</div></div>
              </div>
            </motion.div>
          )}

          {/* DOMAIN CONFIGS */}
          {activeTab === 'domains' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">9</div><h3>Domain-Specific Configurations</h3></div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th>Config</th><th>IIoT (CWRU)</th><th>Smart City (Urban+EPA)</th><th>Healthcare (WESAD+CXR)</th></tr></thead>
                  <tbody>
                    <tr><td>Encoder A in_channels</td><td>1 (vibration)</td><td>6 (env. vector, FC encoder)</td><td>5 (ACC×3, EDA, TEMP)</td></tr>
                    <tr><td>Encoder A length L</td><td>1024</td><td>N/A (FC, not conv)</td><td>160 (5s window)</td></tr>
                    <tr><td>Encoder B input</td><td>STFT spectrogram (RGB)</td><td>Mel-spectrogram (RGB)</td><td>X-ray (grayscale→RGB)</td></tr>
                    <tr><td>num_classes</td><td>4</td><td>5</td><td>4</td></tr>
                    <tr><td>Loss</td><td>CrossEntropy</td><td>CrossEntropy</td><td>WeightedCrossEntropy</td></tr>
                    <tr><td>Signal augment</td><td>jitter ±2%, time-shift ±50</td><td>—</td><td>Gaussian noise σ=0.01</td></tr>
                    <tr><td>Image augment</td><td>hflip, brightness ±20%</td><td>—</td><td>hflip, rotation ±5°</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* DEPENDENCIES */}
          {activeTab === 'deps' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">10</div><h3>Package Dependencies</h3></div>
              <div className="code-block" style={{ marginBottom: 20 }}>
{`# Core ML
pip install torch torchvision torchaudio           # PyTorch 2.x
pip install opacus                                 # DP-SGD
pip install onnx onnxruntime-gpu                   # ONNX export+inference
pip install onnxruntime-extensions                 # extra ops

# Data Processing
pip install librosa soundfile                      # audio
pip install scipy wfdb                             # signal processing
pip install numpy pandas matplotlib seaborn        # analysis/viz
pip install scikit-learn                           # metrics
pip install tqdm tensorboard                       # training utilities
pip install soundata                               # UrbanSound8K loader

# Additional for PHANTOM-FL
pip install einops                                 # tensor rearrange
pip install timm                                   # ViT reference`}
              </div>
              <div className="kv-grid">
                <div className="kv-item"><div className="kv-label">torch</div><div className="kv-value">2.1.x (CUDA 12.1, RTX A2000)</div></div>
                <div className="kv-item"><div className="kv-label">opacus</div><div className="kv-value">1.4.x (GRU support)</div></div>
                <div className="kv-item"><div className="kv-label">onnxruntime</div><div className="kv-value">1.16.x (CUDA EP)</div></div>
                <div className="kv-item"><div className="kv-label">python</div><div className="kv-value">3.10.x</div></div>
              </div>
            </motion.div>
          )}

        </motion.div>
      </div>
    </>
  )
}
