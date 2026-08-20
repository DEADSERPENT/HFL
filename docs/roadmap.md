# Roadmap

**Updated 2026-08-15** · Target: **Q2 @ 9.5** (primary) / Q1 @ 8.5–9 (stretch)

---

## Where we are

| Phase | State |
|---|---|
| 1 Research & gaps | ✅ COMPLETE |
| 2 Simulator selection | ✅ COMPLETE |
| 3 Environment setup | ✅ COMPLETE |
| 4 Simulator implementation | ✅ COMPLETE |
| 5 Model, privacy, deployment | ✅ COMPLETE — 17/17, O1–O4 measured |
| 6 Joint eval, ablation, figures | ⬜ code complete, runs pending |

Objectives: vitaldb **7/7** · wear 6 PASS + 1 INCONCLUSIVE (O1b added 2026-08-15)
Traceability: 32/44 both datasets

**Item A (patient MIA) is CLOSED. N-A is not supported.** LiRA ran on all
three arms (2026-08-14/15) with a passing positive control, and every paired
record-vs-patient interval includes zero. The pre-registered fallback branch is
now the live plan. See "Item A — the answer" below before planning around it.

---

## Current honest rating

| | now | after A–D |
|---|---|---|
| Q1 (TII / IoT-J) | 4 | **8.5–9** |
| Q2 (JBHI / CBM) | 6.5 | **9–9.5** |
| M.Tech thesis | 7.5 | 9+ |

**Why capped now:** contributions are *measurements of known mechanisms*.
User-level DP (McMahan 2018), parameter-efficient DP fine-tuning (Li 2021,
Yu 2021), DP quantile release (Smith 2011) are all prior art.

**No claim here is patentable.** Drop "IP" framing → all become N.

---

## Item A — the record (closed)

Loss-threshold attack, patient-aggregated, 5 paired seeds, vitaldb
(`results/phase5/mia_*.csv`):

| arm | ε=1 | ε=4 | ε=8 |
|---|---|---|---|
| record-level DP | 0.5461 | 0.5512 | 0.5459 |
| patient-level DP | 0.5374 | 0.5417 | 0.5430 |
| **Δ** | **+0.0087** | +0.0095 | +0.0030 |

Against a prediction of 0.7 vs 0.5. The demonstrated-vulnerability claim in its
pre-registered form **did not survive**.

The factorial is the more interesting result — leakage is a property of the
**recipe**, not the task:

| recipe | attack AUC | member / non-member loss |
|---|---|---|
| full-model, no DP | 0.5122 | 1.81 / 2.31 |
| **head-only, no DP** | **0.5847** | **0.013 / 4.95** |
| full-model, DP | 0.5206 | 6.93 / 7.46 |

Head-only fine-tuning — *our own recipe* — memorises its members far harder
than full-model training. p=1e-09, sd 0.0018 over 6 runs.

### Why the threshold null was not reportable on its own

Loss thresholding is the weakest attack in the literature: one global threshold
against per-patient difficulty. Its AUC is a **lower bound on leakage**, and a
reviewer will say so. `scripts/lira_attack.py` (built 2026-08-14) mounts LiRA
— per-patient IN/OUT Gaussians fitted from shadow models, likelihood ratio
instead of threshold, TPR at 1 % and 0.1 % FPR alongside AUC because average
AUC hides the confident-identification tail that *is* the clinical disclosure.

On synthetic data where per-patient difficulty (sd 3.0) swamps the membership
shift (0.8), the threshold gets 0.567 and LiRA gets **0.93–0.95**. The
machinery works, so a null it produces is a statement about the models.

**Gate:** the head-only no-DP arm is the positive control. LiRA must exceed the
0.5847 the threshold already reached there. If it does not, the attack is
underpowered and its nulls are inadmissible — same logic as the k=1 collapse
check in B.

### Item A — the answer (2026-08-15)

Three arms, 16 shadows each, identical splits (`--split_seed 7`), 5 paired
seeds. Strongest attack per arm:

| arm | AUC (95 % CI) | via |
|---|---|---|
| **control** head-only no-DP | **0.6277** [0.5905, 0.6649] | lira_offline |
| record-level DP | 0.5477 [0.4876, 0.6079] | lira_offline |
| patient-level DP | 0.5224 [0.5175, 0.5274] | loss |

Paired Δ (record − patient), all four attack variants:

| attack | Δ | 95 % CI | p |
|---|---|---|---|
| loss | +0.0138 | [−0.0034, +0.0310] | 0.090 |
| lira_offline | +0.0325 | [−0.0280, +0.0929] | 0.210 |
| lira_online | +0.0034 | [−0.0059, +0.0128] | 0.365 |
| lira_online_gv | −0.0211 | [−0.0487, +0.0065] | 0.101 |

**Every CI includes zero.** The control cleared its gate (+0.0513 over plain
thresholding on a model known to memorise), so the null is a statement about
the models, not the attack.

**State it precisely.** The *predicted* effect (0.7 vs 0.5, Δ≈0.20) is refuted
— it lies far outside every interval. A *small* effect is NOT excluded: at
n=5 the half-width on the best attack is ±0.060, and 3 of 4 attacks point the
predicted direction with the loss threshold at p=0.090. Write "the large
effect predicted is refuted; a small one cannot be resolved at this sample
size", never "there is no effect".

Diagnostic worth keeping: on the patient arm **LiRA adds nothing** (−0.0071;
the plain loss threshold wins at 0.5224). That is what a defence with no
difficulty-confounded signal left to recover looks like — not a failing attack.

### Consequence — the fallback branch is live

The argument that record-level ε ≠ patient-level ε is *analytic*, survives a
failed attack, and is priced at 1.77× σ. What dies is the "demonstrated
vulnerability" framing. Headline moves to **N-B (k-scaling)** and **N-A′**
(head-only DP fine-tuning memorises), the latter now measured under LiRA at
0.6277 rather than 0.5847 under thresholding.

The MIA section stays in the paper as a **validated negative result**. That is
publishable; a negative result from a weak attack would have been a hole.

---

## THE FOUR THAT RAISE THE CEILING

### A. Patient-level membership inference attack ← **CLOSED, NEGATIVE**
Predicted record-DP ~0.7+ vs patient-DP ~0.5. Measured under LiRA with a
passing control: **0.5477 vs 0.5224, paired Δ CI includes zero on all four
attack variants.** N-A does not survive. Retained in the paper as a validated
negative result. **Delivered value ≈ +0.5 (credibility), not the +1.5–2
projected.**

### B. k-scaling law
Subsample so each patient contributes k ∈ {1,2,4,8} windows. Re-run both arms.
k=1 must collapse the two arms — built-in validity check.
Output: cost as a **curve in k**, not one number.
**~days · +0.5 to +1**

### C. Second clinical dataset
eICU or MIMIC-IV waveform. Same patient→many-windows structure.
Removes the most predictable rejection.
**~weeks · +0.5 to +1**

### D. Own mechanism — window-count-normalised clipping
Flaw: patient gradient is a SUM over k windows then clipped to C → long
recordings systematically down-weighted.
Fix: normalise by k or √k before clipping. Test vs fixed-C at equal ε.
**~low · +1 if it wins, 0 if not**

---

## NEXT — in order

```
 0  patient-level DP run                 ✅ done
 1  A. loss-threshold MIA                ✅ run — negative, see above
 2  LiRA positive control (head_nodp)    ✅ 0.6277 — gate cleared
 3  LiRA record vs patient DP            ✅ Δ CI includes zero, all variants
 4  decide N-A on the evidence           ✅ NOT SUPPORTED — fallback branch live
 5  B. k-scaling law                     ← RUNNING (started 2026-08-15)
 6  D. normalised clipping mechanism     rating mover · only IP candidate
 7  attribution + A0/A6                  ✅ done 2026-08-15 — ASWA dropped
 8  component_ablation A1–A4             ⬜ NEVER RUN — 3 bugs, see below
 9  S3 hierarchical no-DP                completes topology axis
10  conformal coverage validation
11  mask-channel ablation                turns N-7 evidence into proof
12  multi-seed B4/B6/B7 + ε=1            intervals on headline claims
13  Phase 6: joint eval → statistics → figures
13  C. second clinical dataset
14  update register → all N, rename PP-HFM
15  regenerate all figures (incl. Fig 4 from MEASURED IN/OUT, not illustrative)
16  Phase 6 report
17  paper draft
18  thesis chapters
19  reproducibility package
```

5–6 are the remaining rating movers · 7–12 completion · 13 generalisation

**Fig 4 note:** `paper/figures/fig4_lira.pdf` currently uses synthetic curves
and is captioned "Illustrative". The measured per-patient IN/OUT distributions
now exist in `results/phase5/lira/vitaldb/shadows/*/scores.npz` — redraw it
from those and the figure becomes evidence rather than a teaching diagram.

### Commands for 2–3

```bash
# positive control FIRST — it gates everything after it (~15 min)
python scripts/lira_attack.py --dataset vitaldb --arms head_nodp \
    --target_dir results/phase5/mia_factorial/vitaldb \
    --ckpt_pattern "ckpt_{arm}_seed{seed}.pt" --seeds 42 43 44 --n_shadows 16

# only if the control clears 0.5847
python scripts/lira_attack.py --dataset vitaldb --arms sample --n_shadows 16
python scripts/lira_attack.py --dataset vitaldb --arms patient --n_shadows 16
```

Resumable — completed shadows are skipped, so an interrupted run continues.
Shadow recipes are read from each target's own `run_metadata.json`, so they
cannot drift from the model they calibrate.

---

## Claims — final register

| ID | Claim | /10 | State |
|---|---|---|---|
| ~~N-A~~ | ~~Patient MIA: record-DP exploitable~~ | — | ❌ **REFUTED** — Δ CI includes zero on all 4 attacks, control passed. Kept as a validated negative |
| **N-A′** | **Head-only DP fine-tuning memorises** | **7** | ✅ 0.6277 under LiRA (0.5847 threshold) vs 0.5122 full-model — **fallback headline** |
| **N-B** | **Cost scales with windows-per-patient** | **8** | ⬜ item 5 |
| **N-D** | **Normalised patient clipping** | **8** | ⬜ item 6 |
| N-1 | Genuinely-paired multimodal benchmark | 7.5 | ✅ +0.0411 AUROC, 14× sd |
| N-2 | Patient-level DP cost measured | 7.5 | ◐ run finishing |
| N-3 | Cost of a valid guarantee | 6.5 | ✅ −0.022 AUROC |
| N-4 | Head-only DP in hierarchical MM FL | 6 | ✅ gap widens, both ds |
| N-5 | Adaptive-DP composition tax (negative) | 5.5 | ✅ |
| N-6 | Specialty-derived non-IID | 4 | ✅ 3.2–50.7 % |
| N-7 | Missingness-as-signal | 4 | ◐ IG over 5 seeds: masks carry 22.0 % of attribution mass; `ART_MBP_observed` 4.99 % ± 0.33 (top-5 on 4/5 seeds — say "consistently among the strongest", NOT "#2"). Evidence, not proof — needs the mask ablation |
| — | DP shifts attention to missingness | 5 | ✅ mask share by recipe: full_dp 28.2 % > patient 22.0 % ≈ sample 21.6 % > full_nodp 19.9 % > head_nodp 15.8 %; rank ρ stays 0.95 head-only private vs not |
| — | Two-axis decomposition | 3 | methods section |
| — | Case-level scoring | 2 | correct practice |

**Dropped:** CMGA · FedKD-E · pFAL · PHANTOM-FL brand · all "IP" framing

---

## Positioning — non-negotiable

Cite and position against:
- McMahan et al. 2018 — user-level DP
- Li et al. 2021 / Yu et al. 2021 — parameter-efficient DP fine-tuning
- Smith 2011 — DP quantile, exponential mechanism
- Rieke et al. 2020 · Sheller et al. 2020 — clinical FL

**Claim:** *we quantify what has not been quantified, and demonstrate the
vulnerability that motivates it.*
**NOT:** *we invented patient-level DP.* ← desk reject

---

## Paper structure

| § | Content |
|---|---|
| 1 | Data cannot move; record-level ε ≠ patient-level ε |
| 2 | Prior art, positioned honestly |
| 3 | **Patient MIA under LiRA — a validated NULL.** Control 0.6277; record 0.5477 vs patient 0.5224; paired Δ CI includes zero. Large predicted effect refuted; small effect unresolved at n=5 |
| 4 | PP-HFM: hierarchy · head-only DP · patient clipping · conformal |
| 5 | k-scaling law; normalised clipping |
| 6 | VitalDB + 2nd dataset; leakage controls; case-level scoring |
| 7 | B0–B7, ε sweep, patient vs record, proxy vs rigorous, O1–O4 |
| 8 | Limits: wear ceiling, O2b inconclusive, PHANTOM-FL not claimed |

**Figures:** 1 architecture · 2 **MIA attack AUC** · 3 **k-scaling curve** ·
4 ε sweep both recipes · 5 patient vs record · 6 B4→B7→B6 · 7 latency CDF ·
8 non-IID heatmap

---

## Where this finishes

**Deliverables** — PP-HFM codebase (one command, reproducible) · both datasets
measured with intervals · Q2 paper draft · thesis chapters · repro package

**Defensible claims**
- Record-level ε ≠ patient-level ε — analytically, and costed at 1.77× σ.
  It is **not** demonstrably exploitable: under LiRA with a passing positive
  control the paired Δ is +0.0325 [−0.0280, +0.0929]
- Head-only DP fine-tuning memorises members far harder than full-model
  training (0.5847 vs 0.5122) — a caveat to parameter-efficient DP
- Cost of a patient-level guarantee scales as f(k), measured
- Normalised clipping beats fixed-C *(if D wins)*
- Fusion beats **both** modalities: +0.0411 AUROC
- Head-only DP makes ε≤1 viable: gap widens as budget tightens
- Valid guarantee costs −0.022 AUROC vs oracle
- vitaldb 7/7 PASS: O1 90.8 % · **O1b 73.2 %** (round latency 1170.2→314.0 ms) ·
  O2a 0.970 · O2b −0.92 pp · O3a 4.58 ms (INT8/CPU, P95) · O3b 99.27 % · O4 72.3 %
- wear 6 PASS + 1 INCONCLUSIVE: O1 96.1 % · **O1b 75.2 %** (2393.7→594.1 ms) ·
  O2a 0.966 · O2b 1.967 pp INCONCLUSIVE · O3a 1.22 ms · O3b 99.05 % · O4 76.8 %

**Limitations stated** — wear at ceiling · external pretraining corpus needed ·
single clinical dataset · O2b inconclusive (pre-registered n=15; extending it
would be p-hacking)

**Retired 2026-08-15**
- *no feature attribution* — `scripts/attribution.py`, integrated gradients on
  released checkpoints, midpoint rule, completeness 6.06 % (64 steps).
  20 runs across 5 recipes x 2 baselines; seed stability in
  `attribution_stability.py`.
- *ASWA unablated* — **A6 inclusion arm run: ΔAUROC +0.0005** (A0 0.8460 vs
  A6 0.8465 test AUROC, accuracy −0.0042, n=1 seed). No measurable
  contribution. **DELETE ASWA** from `hfl_trainer.py` and `model/utils/aswa.py`
  — it is a scrapped-PHANTOM-FL leftover that was never in A0.

### `component_ablation.py` — three bugs, A1–A4 have never run

Discovered 2026-08-15 while wiring A6. Every training arm of the Phase-6
component ablation had been failing silently:

1. passed `--local_epochs`, which `hfl_trainer.py` does not define → argparse
   rejected the command and printed usage. **Fixed.**
2. summary reads `test_accuracy` / `test_macro_auc` / `test_auprc`; the
   trainer's CSV has `val_*` columns → table printed dashes. **Not yet fixed.**
3. the honest **test** metrics are only printed to the log (`Final Test
   AUROC=...`), never written to any CSV, so the table could not populate even
   with the right names. Reading the `val_*` columns instead would be
   selection-biased, since the trainer picks its best round on val AUC.

`results/phase6/vitaldb/` therefore holds only A5 (read from
`modality_ablation.py`, not trained) plus A0/A6 from 2026-08-15. **A1–A4 have
never produced a result.**

---

## Strategic call

**Target Q2 and hit 9.5** rather than stretch for Q1 at 6.
A strong JBHI paper beats a marginal TII one, and is the better PhD foundation.

**Immediate:** start **B (k-scaling)**. With N-A refuted it is the highest-value
remaining item, and it shares the patient-DP machinery LiRA just exercised, so
the k=1 collapse check can reuse the same partition generator.

The strategic call is unchanged and is now better supported: **target Q2 at
9–9.5.** N-A was the main lever for a Q1 attempt and it did not survive; a
validated null plus N-A′ plus N-B is a strong JBHI paper, not a marginal TII
one.
