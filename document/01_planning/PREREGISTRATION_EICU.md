# Pre-registration — external validation of the k-scaling law on eICU-CRD

**Frozen:** 2026-09-05, before any eICU table was read, built or inspected.
**Author:** Samartha H V (251580130019) · Guide: Dr. Shreyas J · MIT Bengaluru (MAHE)
**Corpus:** eICU Collaborative Research Database v2.0 (Pollard et al., *Sci Data*
2018), PhysioNet credentialed access, DOI 10.13026/C2WM1R.

## Why this document must exist, and must exist now

Research Dossier §27 states the condition, and Part 2 §9.3 states the method:

> *"fit the k-curve on VitalDB, write down a numeric prediction of what the gap
> should be at eICU's k, freeze that prediction before touching the data, then
> test it."*
>
> *"If we fit the curve, look at eICU, and then write the prediction, no
> reviewer can tell that apart from retrofitting — and neither can we."*

Everything below is derived **only** from VitalDB measurements already on
record. No eICU array existed when this was written. Commit this file before the
first `preprocess_eicu.py` build and cite the commit hash in the paper.

## The question this answers

Dossier Part 2 §9.1, verbatim — the question a reviewer will ask, and which the
project currently cannot answer:

> *"Is this a property of patient-level private federated learning, or a
> property of your dataset?"*

---

## 1. The fitted curve (VitalDB, n=3 seeds, AUPRC)

Measured gap = record-arm AUPRC − patient-arm AUPRC:

| k | record arm | patient arm | gap | p |
|---|---|---|---|---|
| 1 | 0.5015 | 0.5067 | −0.0052 | 0.75 |
| 2 | 0.5590 | 0.5084 | +0.0507 | 0.0017 |
| 4 | 0.5924 | 0.5092 | +0.0832 | 0.0015 |
| 8 | 0.5955 | 0.5089 | +0.0866 | 0.0049 |

Fitted saturating model, pinned to zero at k=1 by construction (k=1 is the
control: one record per patient makes the two privacy units identical):

```
gap(k) = A · (1 − exp(−b·(k−1)))

A = 0.0878 ± 0.0035     (asymptotic ceiling)
b = 0.8827 ± 0.1286     (approach rate)
RMSE = 0.0028           residuals: −0.0052, −0.0008, +0.0016, −0.0010
```

| k | fitted | observed |
|---|---|---|
| 1 | +0.0000 | −0.0052 |
| 2 | +0.0515 | +0.0507 |
| 4 | +0.0816 | +0.0832 |
| 8 | +0.0876 | +0.0866 |

**The curve saturates.** 90% of the ceiling is reached by **k = 3.6**. This is
the substantive, risky content of the forecast.

## 2. The frozen numeric predictions

### P1 — The primary forecast (falsifiable, quantitative)

**P1a — control.** At k=1, |gap| < 0.02 with p > 0.05.
*If this fails the harness is wrong, and no other eICU result may be reported.*

**P1b — point forecasts.** The eICU gap at each k falls within ±0.030 of:

| k | predicted gap | acceptance band |
|---|---|---|
| 1 | +0.000 | −0.030 … +0.030 |
| 2 | +0.052 | +0.022 … +0.082 |
| 4 | +0.082 | +0.052 … +0.112 |
| 8 | +0.088 | +0.058 … +0.118 |
| 16 | +0.088 | +0.058 … +0.118 |
| 32 | +0.088 | +0.058 … +0.118 |

The band is ±0.030, set from the VitalDB seed spread, and is fixed here.

**P1c — saturation.** This is the prediction VitalDB *cannot* test and eICU can.
The gap at k=32 exceeds the gap at k=8 by **less than 0.015**. The cost of a
patient-level guarantee is bounded, not unbounded, in records per patient.

**P1d — asymptote.** The fitted ceiling on eICU lies within ±0.030 of
**A = 0.0878**.

**P1e — mechanism.** The record arm rises with k while the patient arm stays
flat: patient-arm AUPRC range across all k < 0.020. The widening gap is the
record arm improving, not the patient arm degrading.

**P1f — AUROC.** Same sign, underpowered at n=3, as on VitalDB (+0.0006,
+0.0094, +0.0133, +0.0132; no k significant). Reported as directionally
consistent, not as a resolved effect.

### What refutes P1

| Outcome | Reading |
|---|---|
| k=1 gap outside ±0.020 | Harness fault. Not a finding. Fix before reporting anything. |
| Gap flat or negative at k ≥ 2, k=1 control passing | The law is VitalDB-specific. Report as a boundary condition. |
| Gap still climbing steeply past k=8 | Saturation model refuted; the ceiling is not bounded as forecast. |
| Ceiling far from 0.0878 but shape preserved | Shape is structural, magnitude is corpus-dependent. Report both. |

Per Dossier §30, **every row of that table is publishable.** A hit gives
practitioners a transferable design rule — *given your k, this is what
patient-level ε = 1 costs you.* A miss gives a boundary condition with a dated
forecast proving the story was not retrofitted.

### P2 — Fusion (secondary; §7, §14)

VitalDB: best unimodal 0.8283 → fusion 0.8653, **+0.0370 AUROC at 5 seeds**
(5.9× seed SD). WEAR ceilinged at 0.9976 and could not corroborate.

- **P2a** eICU's better single modality lands **below 0.95 AUROC** (the
  headroom check WEAR failed). Modality A beats modality B.
- **P2b** Fusion gain is positive but **smaller than +0.0370**, because eICU's
  modality B is 5-dimensional against VitalDB's 34.
- **P2c** Five seeds only. The 2-seed figure fell 37% in AUPRC at five seeds;
  that correction is on record and must not recur.

### P3 — Membership inference (§16, §24)

Refuted on VitalDB at ε=1 and again at ε=16, both with a passing positive
control. Dossier §2.3: at ε=1, σ=11.33 leaves almost no membership signal in
*either* arm; the large predicted effect is refuted but a small one is not
excluded (interval ±0.060 at n=5).

- **P3a** The null replicates at ε=1: attack AUC within noise of 0.5.
- **P3b** The non-private positive control passes (AUC significantly > 0.5).
  *A null without a passing control is inadmissible.*
- **P3c** Never write "there is no effect". Write: the large predicted effect is
  refuted; a small effect is not excluded.
- **P3d** eICU's ~139k patients give more power than VitalDB's cohort. A null
  here is a stronger negative result, not a weaker one.

### P4 — Federation from a natural partition (eICU-only claim)

VitalDB's 9 clients are **constructed** by grouping surgical optype. eICU's are
**208 real hospitals**, taken as given. Dossier §9.2: *"Our clients would be
actual institutions, not a partition we invented."*

- **P4a** Label prevalence across hospitals spans a range at least as wide as
  VitalDB's 3.2%–50.7%.
- **P4b** The hierarchy ablation arm shows a benefit at least as large as on
  VitalDB, since real-hospital heterogeneity exceeds constructed heterogeneity.

### P5 — Head-only DP memorisation caveat (§17)

Head-only DP fine-tuning memorised members *harder* than full-model training on
VitalDB (0.6277 vs 0.5122) — a caveat against our own recipe, and per §2.4
route 5, the finding that survived the refutation.

- **P5a** This reproduces on eICU. If it does not, the caveat is
  corpus-specific and must be softened.

---

## 3. Method fixed in advance

- Operating point: `--epsilon 0.80 --epsilon_conf 0.20 --batch_size 64 --rounds 10 --tau_e 5`
- k values: **1, 2, 4, 8, 16, 32** — the range past 8 is the point of the corpus
- Seeds: 42, 43, 44 (k-scaling, ablation); 42–46 (fusion)
- Individual = `uniquepid` (the person), never `patientunitstayid` (the stay)
- Clients = `hospitalid`, taken as given; hospitals under 200 windows pooled
- Splits patient-disjoint; primary metric **AUPRC**, AUROC secondary
- Accuracy is **not** quoted for the k-scaling arms (uncalibrated 0.5 threshold
  on imbalanced data pins it at 0.8005; §10.2)
- Encoders pretrained on the **disjoint** population, not the oracle
  configuration, so eICU does not inherit the §26 validity gap that qualifies
  every VitalDB utility figure

## 4. Stopping rules fixed in advance

1. A CAPACITY failure in `validate_corpus.py` halts that claim. It is not a bug.
2. If the better single modality exceeds 0.95 AUROC, eICU cannot evidence
   fusion and the fusion arm is abandoned. This is the check WEAR failed.
3. If the k=1 control fails, **no** eICU result is reported until it passes.
4. If the LiRA positive control fails, the null is inadmissible.
5. If the corpus yields fewer than 8 windows for most patients, P1c cannot be
   tested and must be reported as untested rather than quietly dropped.

---

## Amendment log

No amendments. Any change made after the first eICU build must be appended here
with a date and a reason, and disclosed in the paper.
