# Hierarchical Federated Learning for Privacy-Aware, Low-Latency Multimodal IoT Systems

**Samartha H V** · MIT Bengaluru (MAHE) · Regd. 251580130019
**Guide:** Dr. Shreyas J · **Industry mentor:** Mr. Tejas J (Capgemini)
Target venue: IEEE Trans. Industrial Informatics / IEEE IoT Journal

---

## 1. The one-paragraph version

Hospitals generate enormous amounts of patient data from bedside monitors,
wearables and machines. That data is the raw material for better diagnosis and
earlier warning — but you are not allowed to collect it in one place, and even
if you were, pooling it would blur the individual patient into an average. This
research builds a system where **the model travels to the data instead of the
data travelling to the model**, where each patient's two different kinds of
record are used *together* rather than separately, and where a mathematical
guarantee limits what anyone can learn about any individual patient from the
trained model. It is validated end to end — network, compute, energy and
deployed inference — so the result is not just an accuracy number but a
deployable system.

---

## 2. What problem this solves

### In plain words

A patient in an operating theatre is monitored continuously. Machines record
blood pressure, heart rate, oxygen, temperature. Separately, the hospital
already holds that patient's history: age, existing conditions, blood test
results. Both describe the same person at the same time.

Right now, to build an AI model from this you would copy everyone's data to one
server and train there. Three things go wrong:

1. **You legally and ethically cannot.** Patient data leaving the hospital is
   the exact thing regulation exists to prevent.
2. **Even if you could, it is dangerous.** Once one patient's records are mixed
   into a shared training pool, that patient's information can leak back out of
   the finished model.
3. **Pooling averages people away.** A single "general" model trained on
   everyone fits nobody in particular, and different hospitals genuinely see
   different patients.

So the normal AI / ML / deep-learning recipe does not fit this problem. Not
because the algorithms are weak, but because the *data cannot be moved*.

### In technical terms

Centralised training is infeasible under data-governance constraints, and naive
federation is insufficient because model updates themselves leak information
about their training data. The setting further requires (a) fusion of
heterogeneous modalities that are genuinely co-recorded, (b) a formal privacy
guarantee at a unit that is clinically meaningful, and (c) deployability under
real network, compute and latency constraints — not just offline accuracy.

---

## 3. The approach

### Federated Learning — the model moves, not the data

Each site trains locally on its own patients. Only *model updates* are sent.
Raw records never leave. A server combines the updates into a shared model and
sends it back. Repeat.

### Hierarchical — three layers, not two

```
   Layer 1   DEVICES / CLIENTS      train locally, compress the update
                  |    updates only, never raw data
                  v
   Layer 2   EDGE SERVERS (x2)      aggregate their own clients first
                  |
                  v
   Layer 3   CLOUD                  combine the edges into a global model
```

The middle layer matters. Without it, every client talks to the cloud every
round and the uplink is the bottleneck. With it, most traffic terminates at the
edge and only summaries continue upward.

### Multimodal — two kinds of record, used together

Every client holds **both** modalities for the **same** patient:

| | Modality A | Modality B |
|---|---|---|
| **VitalDB** (primary, clinical) | intraoperative vital-sign trends `(18, 300)` | preoperative clinical + lab vector `(34,)` |
| **WEAR** (fast iteration) | body-worn inertial sensors `(12, 100)` | egocentric video features `(2048,)` |

Two independent encoders produce embeddings; a small fusion head combines them.

### Differential Privacy — a guarantee, not a promise

During local training, gradients are clipped and calibrated noise is added, so
the finished model is provably almost identical whether or not any given
individual was in the training set. The privacy budget **ε (epsilon)** measures
this: smaller is stronger. The target here is **ε ≤ 1**, which is strict.

---

## 4. What is genuinely novel

### N-1 · A genuinely paired multimodal clinical FL benchmark — **PROVEN**

Most "multimodal" FL work joins two unrelated
 datasets with a rule. If that rule
touches the label, any measured "fusion benefit" is leakage, not fusion.

Here both modalities come from **one acquisition system, one patient, one
operation**. The pairing is a property of the instrument, not an assumption.

The test is deliberately hard: fusion must beat **both** single modalities, not
just the weaker one — a fused model can match the weaker arm by ignoring it.

| arm | AUROC | AUPRC |
|---|---|---|
| signals only | 0.8283 | 0.5281 |
| clinical only | 0.7700 | 0.5022 |
| **fused** | **0.8694** | **0.6343** |

Gain over the *best* single modality: **+0.0411 AUROC, +0.1062 AUPRC** — 14× the
seed-to-seed variation. Fusion genuinely helps.

*Reported honestly:* the second dataset (WEAR) is at ceiling — one modality
alone already reaches 0.9976 AUROC, so it **cannot** evidence fusion and is not
counted as confirmation.

### IP-1 · Head-only DP fine-tuning — **TO PROVE**

A strict privacy budget forces large noise. Training a whole multimodal network
under that noise destroys the encoders before they learn anything.

Instead: pretrain the encoders, **freeze** them, and apply DP only to the small
fusion head. A small head over frozen features is close to a linear probe —
well-conditioned, and DP-SGD handles it at noise levels that would destroy
end-to-end training.

> **The precise claim, stated carefully:** freezing does **not** reduce the
> noise. σ depends on the budget, steps and sampling rate — never on parameter
> count. Freezing changes the *optimisation geometry* so the same noise becomes
> survivable. "We froze most of the model so we needed less noise" would be
> false and would not survive review.

This one decision also answers the communication objective, since only the head
is transmitted.

### IP-2 · Separating *what* earned the result — **TO PROVE**

A proposed system usually differs from its baseline in several ways at once, so
"it wins" cannot say *why*. Intermediate arms fix that:

```
flat + full-model DP  →  flat + head-only DP      = value of the RECIPE
flat + head-only DP   →  hierarchical + head-only = value of the TOPOLOGY
hierarchical, no DP   →  hierarchical + DP        = cost of PRIVACY
```

All arms share data, partitions, seed and budget.

### IP-3 · Private conformal prediction — **TO PROVE**

A point prediction is not clinically actionable. Conformal prediction returns a
*set* with a guaranteed coverage level. Releasing the calibration quantile
privately via the **exponential mechanism** rather than additive noise matters:
measured bias ~0.001 versus an additive mechanism's ~0.416 standard deviation —
three orders of magnitude better behaved. The calibration budget is composed
into the reported total rather than quietly omitted.

### N-2 · Missingness as signal — **TO PROVE**

Theatre monitoring is intermittent: cuffs cycle, probes detach, lines are
flushed. Standard practice imputes the gaps and discards the fact that they
*were* gaps — but **which signals are being watched is itself clinically
informative**, since staff escalate monitoring when a patient deteriorates.
Each of the 9 signals therefore carries a parallel observed/not-observed mask,
giving the 18-channel input.

### N-3 · Real non-IID, not synthetic — **PROVEN**

Most FL papers manufacture heterogeneity with a Dirichlet parameter. Here
clients are **surgical specialties**, and the measured ICU-admission rate spans
**3.2 % – 50.7 %** across nine clients: a sixteen-fold spread that is a genuine
property of clinical practice.

### N-4 · A negative result, reported — **NEGATIVE**

Adaptive per-layer privacy allocation is frequently proposed and rarely ablated.
Implemented here and measured **worse** than a uniform budget: splitting one
mechanism into per-group mechanisms does not split the privacy cost
proportionally — composition across groups charges more, so every group must be
noisier. Reported as a negative result rather than dropped.

### N-5 · Patient-level privacy, not window-level — **the most important finding**

This is the point where the research meets its own mission.

Standard DP-SGD clips and accounts **per sample**. Here a sample is a 10-minute
window — and **every patient contributes about 8 of them** (measured: 48,712
windows from 6,257 patients, mean 7.79, and 100 % of patients contribute more
than one).

So a textbook ε answers *"was this 10-minute window in the training set?"* when
the guarantee the system must make is *"was this **patient** in the training
set?"*

Those are not the same. Converting one to the other by group privacy at k ≈ 8
degrades ε ≈ 1 to **ε ≈ 8 with an unusable δ** — worthless as a clinical claim.

The system therefore implements **patient-level DP directly**: each patient's
windows are summed into one gradient, *that* is clipped, and sampling is over
patients. The measured cost:

| guarantee | noise multiplier σ |
|---|---|
| window-level (textbook) | 0.9985 |
| **patient-level (this work)** | **1.7676** — 1.77× |

**A patient-level guarantee costs 1.77× the noise, not 8× the epsilon.** Direct
accounting is dramatically tighter than converting after the fact — and that
number does not currently exist in the literature for multimodal clinical FL.

---

## 5. How it is validated

Four objectives, each owned by exactly one tool — no objective is answered twice.

| # | Objective | Target | Tool |
|---|---|---|---|
| O1 | Uplink reduction | ≥ 50 % | NS-3 (packet level) |
| O2 | Privacy budget + accuracy cost | ε ≤ 1, ≤ 2 % loss | training + accountant |
| O3a | Inference latency | < 100 ms | ONNX Runtime |
| O3b | Update reliability | > 99 % | NS-3 (packet level) |
| O4 | Energy per round | ≥ 20 % saving | CloudSim Plus |

**Why three tools.** Training measures utility; it cannot measure a wireless
channel, a datacentre's power draw, or a portable runtime's latency. NS-3
simulates the actual network packet by packet. CloudSim Plus models edge/cloud
scheduling and energy. ONNX Runtime measures inference on the exported model, so
the latency claim transfers to a device that has no PyTorch on it.

### Measured so far

| Result | vitaldb | wear |
|---|---|---|
| Uplink reduction (measured compressor) | **90.8 %** | **96.1 %** |
| Update reliability (NS-3 FlowMonitor) | **100.000 %** | **99.987 %** |
| Energy saving (CloudSim) | 72.3 % | 76.8 % |
| Fusion gain over best single modality | **+0.0411 AUROC** | at ceiling |

**A finding worth stating:** top-k sparsification must transmit an int32 *index*
for every uint8 value it keeps, so indices are **80 % of the payload**. The
textbook "5× sparsity × 4× quantization = 20×" is therefore wrong by more than
6× — real full-model compression is **3.2×**. Under the head-only recipe the
frozen encoders send nothing at all, giving **13.3×**. The compression advantage
comes from a *design decision*, not from the codec.

---

## 6. How the work is kept honest

This project was rebuilt after an earlier version was found to rest on invalid
foundations. The safeguards exist because of specific failures that were caught:

- **An adversarial dataset audit** — split disjointness, patient leakage, NaNs,
  class coverage, index bounds — run before any result is trusted.
- **Leakage controls matched to the data.** VitalDB splits by *case*, so no
  operation spans train and test. WEAR splits *temporally within each
  (subject, activity)* with a boundary gap, because its windows overlap by 50 %
  and a whole-recording split turned out to be label-disjoint.
- **Case-level scoring.** The model consumes windows; the clinical question is
  per operation. Both are reported; the case-level figure is the one to quote.
- **An objectives checker** that reports `NOT MEASURED` — never `FAIL` for an
  experiment that was not run, and never `PASS` from a default.
- **A traceability matrix** binding every documented deliverable to the code or
  artifact that satisfies it.
- **Provenance fingerprints.** Paths do not identify data, so every run records
  a hash of the labels and partition metadata.

**Failures are recorded, not hidden.** The NS-3 packet-level path was found to
have *never once executed* — the simulator was never built, so the code silently
fell back to an analytical model while printing results under an NS-3 heading.
Six defects were hiding in it, including a reliability figure drawn from a
hand-picked random range (which is why it returned an identical 99.05 % on two
completely different datasets). All are documented in the Phase 4 report.

---

## 7. Honest limitations

1. **Encoder pretraining provenance — the largest open item.** If encoders are
   pretrained on pooled client data they have seen private data non-privately,
   making the reported ε an *upper bound* on achievable utility rather than a
   valid end-to-end guarantee. A defensible claim needs an external public
   corpus. The tooling enforces disjointness; the corpus is not yet in place.
2. **WEAR cannot evidence fusion.** It is at ceiling and is described as a
   pipeline dataset, never as confirmation.
3. **Seed count.** Target is ≥ 5 per configuration; some current evidence uses 2,
   and every underpowered point is flagged as such.
4. **Energy rests on a stipulated input.** CloudSim's power model is real, but
   the advantage derives from an assumed 5× local-compute reduction. Correct
   phrasing: *"given a 5× reduction in local computation, CloudSim yields 72.3 %
   energy saving"* — not "we measured 5×".
5. **Clients are surgical specialties, not hospitals or patients.** Good for
   modelling heterogeneity; if the deployment story is per-hospital, the client
   definition should eventually match.
6. **No feature-level explainability.** The system outputs a risk estimate and a
   conformal prediction set with a coverage guarantee, but it cannot say *which
   inputs* drove a given prediction. For clinical adoption that gap matters, and
   it is future work — not a current capability (see §9).

---

## 8. Scope — what this research is, and what it is not

This is a frequent source of confusion, so it is worth stating flatly.

**This research produces an AI engine and the framework around it.** It is not
hospital software.

| It **is** | It is **not** |
|---|---|
| A hierarchical federated training framework | A hospital management system |
| A multimodal fusion model | An Electronic Health Record application |
| A patient-level privacy mechanism | A doctor-facing dashboard or mobile app |
| A communication + energy optimisation | Patient history storage or retrieval |
| A deployability validation (network, energy, latency) | Appointment scheduling or hospital databases |

The framework **does not store or retrieve patient records**. It is a *training*
system: data stays where it is, a model is trained across sites, and the trained
model is deployed back to each site for local inference. Anything that displays
a patient's history to a clinician is the hospital's existing EHR, not this work.

That boundary is correct for the scope of an M.Tech thesis, and it is also
honest: claiming a clinical application would invite the question "where is your
clinical validation?", which is a different and much larger undertaking
involving prospective studies and regulatory approval.

---

## 9. How it would be used in practice

**The system supports the clinician. It does not replace them.** The model
produces a risk estimate; the doctor makes the decision.

```
   Patient admitted
        │
        ▼
   Monitors + lab results + record        ← stays inside the hospital
        │
        ▼
   Hospital's own systems (EHR)
        │
        ▼
   THIS MODEL — local inference           ← no data leaves for a prediction
        │
        ▼
   Risk estimate + calibrated uncertainty
        │
        ▼
   Doctor reviews everything → final clinical decision
```

**Training** happens across sites: each hospital trains locally, only privatised
model updates travel, and the improved global model comes back. Every site
benefits from the others' data without any site seeing it.

**Inference** is entirely local. A new patient's data never leaves the building
to obtain a prediction, and the measured latency target is **< 100 ms**, so the
result is effectively immediate at the bedside.

### What the output actually is — an important correction

It is tempting to describe the output as a risk score plus a list of
"contributing factors" (abnormal ECG, low oxygen, and so on). **This system does
not produce that.** No feature-attribution method — SHAP, integrated gradients,
attention attribution — is implemented, and presenting one would be a claim the
code does not support.

What it *does* produce is arguably more rigorous:

- a **risk estimate** for the outcome, and
- a **conformal prediction set** carrying a formal coverage guarantee:
  `P(true label ∈ predicted set) ≥ 1 − α`.

That is a statement with a proof behind it, unlike a heuristic confidence score.
The prediction set widens when the model is genuinely uncertain about a case,
which is exactly the signal a clinician needs — and the calibration itself is
performed under differential privacy, with its budget counted in the total.

**Feature-level explanation is a real gap and is listed as future work**, not as
a current capability.

### Natural next step (future work / PhD direction)

A **Clinical Decision Support System** built *on top of* this engine: real-time
monitoring, trend analysis over time, deterioration alerts, feature-level
explanation, dashboards, and EHR integration. That is an application-layer
project which would consume this model as a component — properly a separate
piece of work, and a strong direction to continue in.

---

## 10. Why it matters beyond the thesis

The bet is that the constraint driving this work — *data that cannot move* —
gets stronger, not weaker, over the next decade. As monitoring becomes denser
and regulation tighter, the question stops being "can we centralise this?" and
becomes "what can we learn without ever centralising it?"

This research contributes a defensible answer for the multimodal clinical case
specifically: **that two genuinely co-recorded modalities are worth fusing
(measured), that a strict privacy budget is survivable when applied to the right
part of the model (mechanism identified), and that the guarantee can be made at
the level of a whole patient rather than an arbitrary time window (implemented,
with its cost quantified).**

The last of those is the part most likely to matter in ten years. A privacy
guarantee is only meaningful if its unit matches the thing you promised to
protect — and for medicine, that unit is the person.

---

## 11. Reproducing it

```bash
cd SIMULATORS && source ../hfl_env/bin/activate
python scripts/run_pipeline.py --dataset vitaldb      # 16 stages, resumable
python tests/traceability.py       --dataset vitaldb  # what exists
python scripts/check_objectives.py --dataset vitaldb  # O1–O4 vs thresholds
```

Every stage declares its inputs and refuses to run on missing or stale ones.
Per-stage logs and a manifest record the exact command behind every number.

**Documentation:** `document/DATASET & MODEL GUIDE/` (data, model, simulators),
`document/PHASE REPORT/` (Phases 1–6), `document/OVERALL PROJECT OUTPUT/`
(status and the IP & Novelty register).

---

*Last updated 2026-08-04. Claims marked TO PROVE have their proving experiment
and refutation condition defined in advance — see the IP & Novelty register.*
