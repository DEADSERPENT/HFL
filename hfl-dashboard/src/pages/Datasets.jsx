import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Database, HardDrive,
  FolderTree, Cpu, Beaker, BarChart3, Shield
} from 'lucide-react'

const stagger = { animate: { transition: { staggerChildren: 0.06 } } }
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } }
}

export default function Datasets() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <>
      <div className="page-header">
        <h2>Dataset Selection, Access & Integration Guide</h2>
        <p>VitalDB (PRIMARY, clinical IoMT) + WEAR (fast iteration, wearable IoT)</p>
      </div>
      <div className="page-body">
        <motion.div variants={stagger} initial="initial" animate="animate">

          <motion.div variants={fadeUp}>
            <div className="tabs">
              {[
                { key: 'overview', icon: <Database size={14} />, label: 'Selection Criteria' },
                { key: 'vitaldb', icon: <Cpu size={14} />, label: 'VitalDB (PRIMARY)' },
                { key: 'wear', icon: <HardDrive size={14} />, label: 'WEAR (Iteration)' },
                { key: 'fusion', icon: <Beaker size={14} />, label: 'Fusion Test' },
                { key: 'partition', icon: <FolderTree size={14} />, label: 'Non-IID & Splits' },
                { key: 'provenance', icon: <Shield size={14} />, label: 'Provenance' }
              ].map(tab => (
                <button key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* SELECTION CRITERIA */}
          {activeTab === 'overview' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">1</div><h3>The Selection Criterion That Decides Everything</h3></div>
              <div className="info-box success" style={{ marginBottom: 16 }}>
                <strong>Research Gap #1:</strong> "No multimodal fusion in existing FL." To DEMONSTRATE that gap rather than assert it, a dataset must satisfy two conditions:
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Condition A — Genuine Pairing</h4>
                <p className="section-description">The two modalities must describe the SAME entity at the SAME time, and must have been RECORDED that way by the instrument. Pairing two independent sources by a rule manufactures a correlation that does not exist in the world.</p>
                <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, marginTop: 16 }}>Condition B — A Shared Target</h4>
                <p className="section-description" style={{ marginBottom: 0 }}>Both modalities must independently carry information about the label. Genuine pairing with a target only one modality can predict is still a fake fusion task.</p>
              </div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                <strong>The Test That Settles It:</strong> Train three models on identical splits — modality A alone, modality B alone, and fused. Fusion must beat BOTH unimodal arms by more than the seed-to-seed standard deviation. Implemented in <code>scripts/modality_ablation.py</code>.
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead><tr><th></th><th>VitalDB</th><th>WEAR</th></tr></thead>
                  <tbody>
                    <tr><td><strong>Role</strong></td><td>PRIMARY (clinical)</td><td>Fast iteration</td></tr>
                    <tr><td><strong>Windows</strong></td><td>48,712</td><td>38,578</td></tr>
                    <tr><td><strong>Clients</strong></td><td>9 (surgical type)</td><td>22 (subject)</td></tr>
                    <tr><td><strong>Classes</strong></td><td>2</td><td>18</td></tr>
                    <tr><td><strong>Modality A</strong></td><td>(18, 300) @ 0.5 Hz</td><td>(12, 100) @ 50 Hz</td></tr>
                    <tr><td><strong>Modality B</strong></td><td>(34,) clinical vector</td><td>(2048,) I3D video</td></tr>
                    <tr><td><strong>Pairing</strong></td><td>Same patient, same second</td><td>Hardware-synchronised</td></tr>
                    <tr><td><strong>Split unit</strong></td><td>Case (operation)</td><td>Time within (subject, activity)</td></tr>
                    <tr><td><strong>Non-IID source</strong></td><td>Surgical specialty</td><td>Per-subject style</td></tr>
                    <tr><td><strong>Imbalance</strong></td><td>19.7% positive</td><td>Near-uniform</td></tr>
                    <tr><td><strong>Selection metric</strong></td><td>AUPRC</td><td>AUROC</td></tr>
                    <tr><td><strong>Edge servers</strong></td><td>2</td><td>2</td></tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* VITALDB */}
          {activeTab === 'vitaldb' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">2</div><h3>VitalDB — Clinical IoMT (PRIMARY)</h3></div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Source</div><div className="kv-value">Lee et al., Scientific Data 9:279, 2022</div></div>
                <div className="kv-item"><div className="kv-label">Access</div><div className="kv-value">https://vitaldb.net — open, no credentialing</div></div>
                <div className="kv-item"><div className="kv-label">Domain</div><div className="kv-value">Intraoperative patient monitoring</div></div>
                <div className="kv-item"><div className="kv-label">Licence</div><div className="kv-value">CC BY 3.0</div></div>
                <div className="kv-item"><div className="kv-label">Windows</div><div className="kv-value">48,712 from 6,257 surgeries</div></div>
                <div className="kv-item"><div className="kv-label">Clients</div><div className="kv-value">9 (surgical operation type)</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Modality A — Intraoperative Vital-Sign Trends</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="kv-grid">
                  <div className="kv-item"><div className="kv-label">Shape</div><div className="kv-value">(18, 300)</div></div>
                  <div className="kv-item"><div className="kv-label">Content</div><div className="kv-value">9 numeric trend channels + 9 observed-masks</div></div>
                  <div className="kv-item"><div className="kv-label">Sampling</div><div className="kv-value">0.5 Hz over 10-min window</div></div>
                </div>
                <div className="info-box note" style={{ marginTop: 12 }}>
                  <strong>Why 18 channels for 9 signals?</strong> Missingness-as-signal (GRU-D style). Operating-theatre monitoring is intermittently observed — which signals are being watched is itself clinically meaningful. Each signal carries a parallel binary mask channel marking observed vs imputed.
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Modality B — Preoperative Clinical Vector</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="kv-grid">
                  <div className="kv-item"><div className="kv-label">Shape</div><div className="kv-value">(34,)</div></div>
                  <div className="kv-item"><div className="kv-label">Content</div><div className="kv-value">Demographics, comorbidities, preoperative labs, surgical context</div></div>
                </div>
                <div className="info-box note" style={{ marginTop: 12 }}>
                  Fields that encode the outcome (ICU stay length, in-hospital death, timestamps, identifiers) are excluded by an explicit forbidden-field list.
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Label & Splits</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="kv-grid">
                  <div className="kv-item"><div className="kv-label">Label</div><div className="kv-value">Postoperative ICU admission (19.7% positive)</div></div>
                  <div className="kv-item"><div className="kv-label">Split</div><div className="kv-value">By CASE, stratified within surgical type, 70/15/15</div></div>
                  <div className="kv-item"><div className="kv-label">Train</div><div className="kv-value">34,044 windows</div></div>
                  <div className="kv-item"><div className="kv-label">Val</div><div className="kv-value">7,308 windows</div></div>
                  <div className="kv-item"><div className="kv-label">Test</div><div className="kv-value">7,360 windows / 947 operations</div></div>
                </div>
                <div className="info-box note" style={{ marginTop: 12 }}>
                  <strong>Why split by case?</strong> Consecutive windows from one operation are near-duplicates. Random window split measures memorisation, not generalisation. No case appears in more than one split.
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Scoring — Windows Train, Cases Count</h4>
              <div className="info-box success">
                Every result carries BOTH window-level (optimised) and case-level (averaged per operation) metrics. Case-level is the statistically honest and clinically meaningful number. At 19.7% positive rate, accuracy is uninformative — <strong>AUPRC</strong> is the selection metric.
              </div>
            </motion.div>
          )}

          {/* WEAR */}
          {activeTab === 'wear' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">3</div><h3>WEAR — Wearable IoT (Fast Iteration)</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                WEAR is the <strong>fast-iteration</strong> dataset. Its arms train in seconds — right for pipeline bugs and flag verification. It is <strong>NOT</strong> the dataset the multimodal claim rests on (at ceiling, see Fusion Test tab).
              </div>
              <div className="kv-grid" style={{ marginBottom: 20 }}>
                <div className="kv-item"><div className="kv-label">Source</div><div className="kv-value">Bock et al., Proc. ACM IMWUT, 2024</div></div>
                <div className="kv-item"><div className="kv-label">Access</div><div className="kv-value">Open download, no credentialing</div></div>
                <div className="kv-item"><div className="kv-label">Domain</div><div className="kv-value">Outdoor activity recognition</div></div>
                <div className="kv-item"><div className="kv-label">Windows</div><div className="kv-value">38,578</div></div>
                <div className="kv-item"><div className="kv-label">Clients</div><div className="kv-value">22 (one per subject)</div></div>
                <div className="kv-item"><div className="kv-label">Classes</div><div className="kv-value">18 activities</div></div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Modalities</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Modality</th><th>Shape</th><th>Content</th><th>Sampling</th></tr></thead>
                  <tbody>
                    <tr><td><strong>A — Inertial</strong></td><td>(12, 100)</td><td>4 body-worn accelerometers × 3 axes</td><td>50 Hz, 2-sec window</td></tr>
                    <tr><td><strong>B — Video</strong></td><td>(2048,)</td><td>Two-stream I3D features, same 2 seconds</td><td>Hardware-synchronised</td></tr>
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Splits & Leakage Control</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="kv-grid">
                  <div className="kv-item"><div className="kv-label">Split</div><div className="kv-value">Temporal within (subject, activity), 70/15/15</div></div>
                  <div className="kv-item"><div className="kv-label">Train</div><div className="kv-value">26,424 windows</div></div>
                  <div className="kv-item"><div className="kv-label">Val</div><div className="kv-value">5,395 windows</div></div>
                  <div className="kv-item"><div className="kv-label">Test</div><div className="kv-value">5,969 windows</div></div>
                </div>
                <div className="info-box note" style={{ marginTop: 12 }}>
                  <strong>Why temporal within (subject, activity)?</strong> Windows overlap 50% — random split puts shared signal on both sides. Whole-recording temporal split is label-disjoint (activities in blocks). One-window gap dropped at each boundary removes shared seconds.
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Handled Data Defect</h4>
              <div className="info-box note">
                One subject has 25.8% missing inertial samples. NaN-aware normalisation (nanmean/nanstd on train only). Without this, a single NaN propagates across every window of that subject.
              </div>
            </motion.div>
          )}

          {/* FUSION TEST */}
          {activeTab === 'fusion' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><BarChart3 size={16} /></div><h3>The Fusion Test — Measured Result</h3></div>
              <div className="info-box success" style={{ marginBottom: 16 }}>
                <strong>Protocol:</strong> Centralised and non-private, so the question is about the DATA. All three arms share encoder architecture, head depth, optimiser, schedule, epochs and seed. Each arm RETRAINED on its own inputs. 2 seeds.
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>VitalDB (7,360 test windows / 947 test cases)</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Arm</th><th>AUROC</th><th>AUPRC</th><th>Case AUROC</th><th>Case AUPRC</th></tr></thead>
                  <tbody>
                    <tr><td>Signals only</td><td>0.8283</td><td>0.5281</td><td>0.8590</td><td>0.6446</td></tr>
                    <tr><td>Clinical only</td><td>0.7700</td><td>0.5022</td><td>0.7713</td><td>0.4961</td></tr>
                    <tr className="highlight-row"><td><strong>FUSED</strong></td><td><strong>0.8694</strong></td><td><strong>0.6343</strong></td><td><strong>0.8875</strong></td><td><strong>0.6740</strong></td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box success" style={{ marginBottom: 20 }}>
                <strong>Gain over BEST unimodal:</strong> +0.0411 AUROC, +0.1062 AUPRC = 14.1× seed standard deviation. Fusion beats BOTH arms. → <strong>Research Gap #1 is DEMONSTRATED.</strong>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>WEAR (5,969 test windows)</h4>
              <div className="table-container" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead><tr><th>Arm</th><th>AUROC</th><th>AUPRC</th></tr></thead>
                  <tbody>
                    <tr><td>Inertial only</td><td>0.9976</td><td>0.9761</td></tr>
                    <tr><td>Video only</td><td>0.9957</td><td>0.9629</td></tr>
                    <tr><td>FUSED</td><td>0.9980</td><td>0.9831</td></tr>
                  </tbody>
                </table>
              </div>
              <div className="info-box" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.03)' }}>
                <strong>AT CEILING.</strong> Best single modality already 0.9976 AUROC. The +0.0004 gain is reported as a ceiling effect, NOT as supporting evidence. The multimodal claim rests on VitalDB alone.
              </div>
            </motion.div>
          )}

          {/* NON-IID & SPLITS */}
          {activeTab === 'partition' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number">5</div><h3>Non-IID Partitioning — Naturally Derived</h3></div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>VitalDB — Surgical Specialty (N-3)</h4>
              <div className="info-box success" style={{ marginBottom: 16 }}>
                <strong>Not synthesised, measured.</strong> Clients are surgical operation types. ICU base rate spans 3.2%–50.7% across 9 clients — a sixteen-fold spread. This is a property of clinical practice, not a Dirichlet parameter.
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description" style={{ marginBottom: 0 }}>
                  Operation types with too few positive cases are merged into one combined client, so every client holds ≥10 positive cases. Without that merge, a single-class client has undefined AUROC and is silently dropped from any average.
                </p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>WEAR — Per-Subject</h4>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description" style={{ marginBottom: 0 }}>
                  22 clients, one per subject. Temporal split within (subject, activity), 70/15/15 with a one-window gap at each boundary. Every split sees every class.
                </p>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Dataset Verification</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`# Adversarial audit, not smoke test (8-category verifier)
python tests/verify_datasets.py --dataset vitaldb
python tests/verify_datasets.py --dataset wear

# Checks: split disjointness, case/subject leakage, NaN presence,
#          label range, class coverage per split, index bounds,
#          partition completeness, metadata agreement`}
              </div>
            </motion.div>
          )}

          {/* PROVENANCE */}
          {activeTab === 'provenance' && (
            <motion.div variants={fadeUp} className="section">
              <div className="section-header"><div className="section-number"><Shield size={16} /></div><h3>Provenance & Fingerprinting</h3></div>
              <div className="info-box note" style={{ marginBottom: 20 }}>
                <strong>Paths do not identify data.</strong> Rebuilding a dataset with different window settings leaves every stored path unchanged. A result file recording only the path cannot be traced to the arrays that produced it.
              </div>
              <div className="card" style={{ marginBottom: 20 }}>
                <p className="section-description">Every run records a dataset fingerprint (MD5 of label array + partition_meta.json) via <code>engineering/runctx.py</code>.</p>
                <div className="table-container" style={{ marginTop: 12 }}>
                  <table className="data-table">
                    <thead><tr><th>Dataset</th><th>Labels Hash</th><th>Partition Meta Hash</th></tr></thead>
                    <tbody>
                      <tr><td>vitaldb</td><td><code>d3fa814dd4396efd</code></td><td><code>69feba3f786f9e64</code></td></tr>
                      <tr><td>wear</td><td><code>8aeb2aeeb2bba951</code></td><td><code>38c58aadc2a84eee</code></td></tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>How to Build</h4>
              <div className="code-block" style={{ marginBottom: 16 }}>
{`# VitalDB
python data/loaders/fetch_vitaldb.py          # resumable API fetch
python data/loaders/preprocess_vitaldb.py     # window + split + partition

# WEAR
python data/loaders/preprocess_wear.py

# Both write under data/processed/<name>/:
#   modality arrays, labels, meta/case_ids.npy,
#   per-client partition indices with partition_meta.json

# Registry (single source of truth):
#   SIMULATORS/data/loaders/datasets.py`}
              </div>
            </motion.div>
          )}

        </motion.div>
      </div>
    </>
  )
}
