# Presentation Script — Slide by Slide

**Total duration:** about 20 minutes + questions (timings in brackets; compress the Results
slides for a 15-minute slot, expand them for 30 minutes).
**Figures:** all in `figures/` (PDF for slides, PNG for preview).
**Style:** each slide has (1) what to put **on the slide**, (2) what to **say**, and (3) the
**transition** to the next slide. Keep slides sparse; the detail belongs in your speech.

---

## Slide 1 — Title  [0:30]

**On the slide**
- Patient-Level Differential Privacy in Hierarchical Federated Learning for Multimodal Medical IoT
- Samartha H V, Shreyas J, Gururaj H L, Udayaprasad P K, Shreelakshmi Yadav N, Sowmya T Rao
- Manipal Institute of Technology Bengaluru, MAHE

**Say**
> "Good morning. My work is on training medical AI models across hospitals and IoT devices
> without moving patient data, and with a mathematical guarantee that protects every *patient* —
> not just every data record. I will present the system, which we call PP-HFM, its privacy proof,
> and a careful measurement of what that protection costs."

---

## Slide 2 — Motivation  [1:00]

**On the slide**
- Medical IoT is multimodal: waveforms + clinical records, motion + video
- Data cannot be pooled: consent, data-protection law, volume
- Federated learning: train where the data lives; share only model updates
- Hierarchical FL: client → edge → cloud reduces traffic and energy

**Say**
> "Monitoring in the operating room, the ICU and through wearables produces several kinds of data
> about the same person. A model that sees both streams can recognize states that neither shows
> alone. But this data cannot be collected in one place. Federated learning solves that by training
> locally and sending only updates, and a hierarchical design adds an edge tier so most aggregation
> happens close to the data."

**Transition:** "Keeping the data local, however, does not by itself keep it private."

---

## Slide 3 — The Problem: The Privacy Unit  [1:30]

**On the slide**
- Updates leak: membership inference can tell whether data was used in training
- Differential privacy (DP-SGD): clip each unit's gradient + add noise → protects *the clipped unit*
- Standard unit = **one record** (a 10-minute window)
- One patient = many records: **~8 (VitalDB), ~28 (eICU)**
- Group privacy: ε = 1 per record → **ε ≈ 8, δ ≈ 0.09 per patient**

**Say**
> "Differential privacy is the standard defence. It bounds the influence of each training unit and
> adds noise, so it protects whatever unit you clip. In nearly every system that unit is a record —
> here a short window of signal. But each patient contributes many windows. A record-level guarantee
> answers 'was this window used?', while a hospital must answer 'was this patient used?'. Converting
> after the fact with group privacy turns ε of 1 into about 8, which supports no clinical claim. So
> the patient must be the unit from the start."

---

## Slide 4 — Research Gaps  [1:00]

**On the slide** (numbered)
1. No patient-level guarantee across a hierarchy
2. The cost of protecting individuals vs. records is unmeasured
3. Pretrained-feature condition implicit; source of the benefit unknown
4. Audits done per record — the wrong unit

**Say**
> "From the literature review we identified four gaps. Hierarchical systems like HED-FL save
> communication but have no guarantee; private systems like FL2DP have a guarantee but ignore the
> edge tier. Nobody measured the cost of protecting individuals. Private training on pretrained
> features is valid only if the pretraining data is disjoint from the patients, which is rarely
> stated. And audits are done per record."

**Optional:** show the comparison table (Table I of the paper) — PP-HFM is the only row with
hierarchy + individual unit + all-tier accounting + audit.

---

## Slide 5 — Research Questions and Objectives  [1:00]

**On the slide**
- RQ1 Patient-level guarantee across all tiers — what does it cost?
- RQ2 How does the cost scale with records per patient k?
- RQ3 Pretrained initialization or fewer privatized parameters?
- RQ4 System targets, prior systems, audit
- Seven targets fixed *before* any experiment: uplink ≥ 50 %, round latency ↓, ε ≤ 1,
  utility loss ≤ 2 pts, P95 latency < 100 ms, delivery > 99 %, energy ≥ 20 %

**Say**
> "These gaps give four research questions, one per contribution. To make them testable, seven
> quantitative targets were fixed before any experiment was run — that matters, because it means
> we cannot move the goalposts after seeing results."

---

## Slide 6 — Architecture  [1:30]

**On the slide:** `figures/fig01_overview_core.pdf`

**Say**
> "This is PP-HFM. Clients — hospitals, surgical specialties, or wearable users — hold the records.
> Each record passes through two frozen pretrained encoders, one per modality. Only the small
> fusion head is trained, under patient-level privacy. The client sends a sparsified, 8-bit
> update to its edge; each edge averages its clients for five rounds, then the cloud averages the
> edges and broadcasts. That is one cloud round; we run ten."

---

## Slide 7 — The Model  [0:45]

**On the slide:** `figures/fig2_backbone.pdf`
- Temporal encoder: multi-scale 1-D CNN → 2-layer bidirectional recurrent layer → attention pooling
- Static encoder: 2-layer MLP
- Fusion head: 559,874 of 1.86 M parameters (30 %) — the only part privatized and sent
- Group/layer norm only — batch norm would mix patients

**Say**
> "The temporal encoder handles the time series; the static encoder the clinical vector. Only the
> head — thirty percent of the parameters — is trained privately. We use no batch normalization,
> because it mixes statistics across patients and would break the per-patient accounting."

---

## Slide 8 — Core Mechanism: Patient-Level DP-SGD  [2:00]  ★ key slide

**On the slide:** `figures/fig02_privacy_unit.pdf` + the 5 steps
1. Poisson-sample **patients**, q = B / |P_k|
2. **Sum** all of a patient's gradients
3. **Clip the sum** to C → patient influence ≤ C, regardless of record count
4. Add Gaussian noise **once** per step
5. Divide by the **expected** batch size (not the realized one)

**Say**
> "This is the heart of the work. Instead of clipping each record, we first sum the gradients of
> all of a patient's records and clip that sum. So a patient with fifty records has exactly the same
> maximum influence as a patient with one. Then noise is added once. One subtle detail: we divide by
> the *expected* number of sampled patients, not the realized number, because the realized number
> depends on whether a given patient is present and would leak. We actually found and fixed this
> issue while writing the proof, and re-ran every patient-level experiment."

---

## Slide 9 — Per-Client Calibration and Aggregation  [1:00]

**On the slide**
- Hospitals vary hugely in size → each client gets its own noise multiplier σ_k
- eICU: σ_k from 4.85 to 29.34 (median 13.76); one global σ would impose 29.34 on all 187
- Valid by parallel composition — each patient is at one client
- Public fixed aggregation weights; compression is post-processing

**Say**
> "A small hospital samples nearly all its patients every step and needs a lot of noise. If one
> noise level were used for everyone, the smallest hospital would degrade all 187. Because each
> patient belongs to one client, we can calibrate each client separately. Aggregation weights are
> fixed public numbers — weights computed from the sampled records would leak."

---

## Slide 10 — The Guarantee (Theorem 1)  [1:30]

**On the slide**
- Assumptions: A1 one client per patient · A2 public fixed parameters & disjoint encoders ·
  A3 record-independent forward pass
- **Theorem:** the entire transcript (all updates, edge and cloud models, selected checkpoint)
  is (ε, δ)-DP per patient
- Proof: one step → composition → other clients → hierarchy = post-processing
- Independent recomputation: ε ∈ [0.880, 0.900] (PLD); 0.974 (Rényi) — both < 1

**Say**
> "Under three conditions we prove the whole transcript — every message any tier releases — is
> differentially private per patient. The proof has four steps: each step is a subsampled Gaussian
> mechanism, the steps compose, other clients never touch this patient's records, and everything
> the edge and cloud do is post-processing. We also recomputed the budget independently for every
> client of every run. And we are precise about scope: the fully end-to-end guarantee holds for the
> eICU configuration with disjoint encoders and pool-fitted normalization."

---

## Slide 11 — The Scaling Hypothesis  [0:45]

**On the slide**
- Record-level: P·k units → error ∝ 1/(Pk) · Patient-level: P units → error ∝ 1/P
- Gap = **A(1 − 1/k)**: zero at k = 1, grows, saturates
- Corollary: at k = 1 the two mechanisms are identical → built-in control

**Say**
> "We also predict the cost. With P patients each having k records, record-level training has Pk
> units, patient-level only P. This motivates a gap of the form A times one minus one over k. It is
> zero at k equals one, where a patient *is* a record — which gives us a built-in control."

---

## Slide 12 — Datasets and Setup  [1:00]

**On the slide:** dataset table (VitalDB / WEAR / eICU) + `figures/fig00_workflow.pdf` (optional)
- VitalDB: 9 specialties, 5,974 people, ICU admission
- WEAR: 22 participants, inertial + video, 18 activities (non-clinical)
- eICU: **187 hospitals**, 132,736 people, mortality
- Paired at source · split by individual · pre-op features only · 5 paired seeds
- ns-3 (network), CloudSim Plus (energy), ONNX Runtime (latency)

**Say**
> "We use three public datasets in which both modalities come from the same person — needed for any
> fusion claim. VitalDB is surgical, eICU is an external ICU corpus with 187 hospitals, and WEAR is
> a non-clinical wearable workload. We controlled leakage carefully: splits by person, only
> pre-operative variables, and normalization from training data only. Every comparison is paired
> over five seeds."

---

## Slide 13 — Result 1: System Objectives  [1:30]

**On the slide:** objectives table + `figures/fig09_system_cost.pdf`
- Uplink ↓ **90.8–96.1 %** · Energy ↓ **72.3–79.6 %** · P95 latency **≤ 2.3 ms**
- Delivery: 100 / 99.94 % ; eICU 97.83 % at 2 edges, met from 8 edges

**Say**
> "The system targets are met on all three datasets for traffic, latency and energy — far beyond
> the targets of 50 and 20 percent. Inference takes at most 2.3 milliseconds against a 100 ms
> budget. The one system miss is delivery on eICU: 187 clients sharing two edges contend for the
> medium. With eight edges or more it is met in every round."

---

## Slide 14 — Result 2: Cost of Patient-Level Privacy (RQ1)  [1:30]  ★

**On the slide**
- ε = 0.9, δ = 10⁻⁵, every training patient, all tiers
- VitalDB: 0.820 → **0.832** AUROC (cost **−1.18** pts) — no cost
- eICU: 0.824 → 0.793 (cost **3.10** [1.55, 4.65]); end to end 3.88
- Cost driven by the smallest hospitals

**Say**
> "On VitalDB the private model is actually slightly better than the non-private one — consistent
> with the noise regularizing the small head. On eICU there is a resolved cost of about three AUROC
> points, inconclusive against the two-point target, and about four end to end. The cost comes from
> the smallest hospitals, which must add the most noise."

---

## Slide 15 — Result 3: Initialization, Not Subset (RQ3)  [1:15]

**On the slide:** `figures/fig05_init_vs_subset.pdf`
- Init effect grows as ε tightens: **+0.199 AUROC at ε = 0.5** (WEAR +0.358)
- Subset effect ≈ 0 at every finite ε
- Head-only training is justified by communication, not accuracy

**Say**
> "PP-HFM differs from standard private training in two ways: pretrained start and privatizing only
> the head. We separated them. The pretrained start is worth up to 0.2 AUROC at the tightest budget
> and grows as the budget tightens. Privatizing fewer parameters is worth essentially nothing. So the
> practical lesson is: secure a legitimate pretrained initialization first."

---

## Slide 16 — Result 4: The k-Law (RQ2)  [2:00]  ★

**On the slide:** `figures/fig03_klaw.pdf` (optionally `fig04_arms.pdf`)
- VitalDB: k = 1 gap ≈ 0 (control passes); grows to +0.087 AUPRC at k = 8
- Fit A(1 − 1/k), A = 0.1015; out-of-sample prediction 0.090 vs 0.087 observed
- Patient-level model flat; record-level improves
- eICU (pre-registered forecast): shape and saturation reproduce; magnitude ~1/9

**Say**
> "This is the central scientific finding. We varied the records kept per person. At k = 1 the two
> units are indistinguishable, as the corollary requires — so the control works. From k = 2 the gap
> grows and saturates, matching the one-parameter curve; fitted on small k only, it predicted the
> k = 8 value out of sample. The patient-level model stays flat while the record-level model keeps
> improving, so protecting patients gets relatively more expensive as you collect more per patient.
> We registered a forecast before building eICU: the shape transferred, the magnitude did not —
> about one ninth. We also ruled out the budget and the clipping rule as explanations."

---

## Slide 17 — Result 5: Fusion and Ablation  [1:00]

**On the slide:** `figures/fig06_fusion_map.pdf` (or a two-column table)
- Fusion: VitalDB +0.037 AUROC; eICU none (one stream dominates); restored at parity (+0.029, 5/5 seeds)
- Ablation: compression costs no accuracy (5× and 1.6× traffic); hierarchy costs ≈ 0.005;
  removing privacy *lowers* AUROC (regularization)

**Say**
> "Fusion helps when the streams are balanced: clearly on VitalDB, not on eICU's natural data where
> admission variables dominate — but when we weakened that stream to parity in a pre-specified
> test, the gain appeared on all five seeds. The ablation shows compression and the hierarchy cost
> essentially no accuracy while saving traffic."

---

## Slide 18 — Result 6: Membership-Inference Audit  [1:30]  ★

**On the slide:** `figures/fig10_ablation_mia.pdf` (panel b) + MIA table
- LiRA, 16 shadow models, patient-level, with a **positive control**
- Control (no DP): 0.605 · Record-level DP: **0.576** (above floor) · Patient-level DP: **0.503** (at floor)
- Paired difference +0.073 [0.054, 0.092], p < 0.001

**Say**
> "A proof says what an attacker *can* learn; an audit measures what a real attack *does*. We ran
> the strongest standard attack, LiRA, at the patient level, and first showed on a non-private
> control that it detects leakage. Record-level training still leaks above its difficulty floor;
> patient-level training sits at its floor. The effect is smaller than we predicted — 0.58, not 0.7
> — and we report that."

---

## Slide 19 — Result 7: Comparison with Prior Systems  [1:00]

**On the slide:** prior-systems table
- vs HED-FL and FL2DP (re-implemented, same data/encoders/seeds)
- **2.2–4.0× less uplink**, lower measured leakage on VitalDB
- eICU: non-private HED-FL +3.2 pts = the price of the guarantee
- FL2DP leaks *more* than HED-FL: no finite ε

**Say**
> "Against re-implemented HED-FL and FL2DP, PP-HFM uploads two to four times less and leaks less. On
> eICU HED-FL is more accurate, but it matches our own non-private reference, so that gap is exactly
> the price of the patient guarantee. Interestingly, FL2DP adds noise yet leaks more than HED-FL —
> its mechanism has no finite ε, which only an audit reveals."

---

## Slide 20 — Answers, Implications, Limitations  [1:15]

**On the slide**
- RQ1 yes, 0 cost (VitalDB) / ~3 pts (eICU) · RQ2 A(1 − 1/k) · RQ3 initialization · RQ4 targets met (except eICU utility, delivery < 8 edges)
- Recommendations: choose the unit explicitly · pretrain first · per-client calibration · use compression + edge tier
- Limitations: oracle encoders on VitalDB/WEAR · 3-seed grids · simulated network/energy · audit VitalDB only

**Say**
> "To summarize the answers… [read the RQ line]. For practitioners: choose the unit explicitly,
> secure a pretrained initialization, calibrate per client, and use compression and the edge tier.
> The main limitations are the oracle encoders on two datasets, three-seed grids, simulated network
> and energy, and an audit on VitalDB only."

---

## Slide 21 — Conclusion and Future Work  [0:45]

**On the slide**
- Protecting **patients, not records**, is feasible in client–edge–cloud medical IoT
- Cost depends on records per patient and the size of the smallest clients
- Next: third corpus · cross-client patient sampling · mean-centred clipping · eICU audit

**Say**
> "Protecting patients rather than records is feasible in a hierarchical deployment, with a proof,
> complete accounting and large efficiency gains. Its cost depends mainly on how many records each
> patient contributes and how small the smallest clients are. Thank you — I am happy to take
> questions."

---

## Delivery Tips

- The three ★ slides (8, 14, 16, 18) carry the research; slow down on them.
- Always say the **unit** when quoting a privacy number ("per patient", "record-level").
- When a result is unresolved or missed, say it plainly — the pre-registration and the honest
  reporting are strengths, not weaknesses.
- Say "consistent with" for explanations that were not isolated (e.g. regularization).
- Keep `03_Key_Numbers.md` open or printed for questions.
