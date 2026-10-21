# Pre-registration — why fusion pays on one corpus and not another

Written 2026-09-20, **before the experiment below was run**. Same rule as
`PREREGISTRATION_EICU.md`: the prediction is frozen first so that a hit cannot
be retrofitted and a miss cannot be buried.

## 1. What is being explained

Fusion gain over the better single modality, five seeds, AUROC:

| corpus | A | B | best | fused | gain | headroom | \|A−B\| | % of headroom |
|---|---|---|---|---|---|---|---|---|
| vitaldb | 0.8283 | 0.7680 | 0.8283 | 0.8653 | +0.0370 | 0.1717 | 0.0603 | 21.5% |
| wear | 0.9976 | 0.9957 | 0.9976 | 0.9980 | +0.0004 | 0.0024 | 0.0019 | 15.0% |
| eicu | 0.6748 | 0.8212 | 0.8212 | 0.8249 | +0.0037 | 0.1788 | 0.1463 | 2.1% |

## 2. Hypothesis 1 — headroom. REFUTED, before any new run

The paper's Discussion currently explains WEAR's null by ceiling effects, and
it is tempting to extend that to eICU. **It does not extend.** eICU has *more*
headroom than VitalDB (0.1788 vs 0.1717) and captures a tenth as much of it
(2.1% vs 21.5%). Headroom explains WEAR and fails on eICU, so it cannot be the
general account. This is recorded because the reframing was proposed and is
now withdrawn.

## 3. Hypothesis 2 — modality balance. THE CLAIM UNDER TEST

Fusion pays only when a second stream is *competitive*, not merely present.
Where one modality dominates, the fused model can do no better than defer to
it, and the weaker stream contributes noise rather than complement.

Three observational corpora cannot separate this from any other property of
eICU. So it is tested by **manipulation within eICU**, holding the corpus,
partitions, encoders, seeds and protocol fixed.

**Intervention.** Modality B is the 5-d admission vector
`[age, gender, admissionweight, admissionheight, apachescore]`. APACHE is an
established severity score and is expected to carry most of B's signal.
Zeroing index 4 removes its information while leaving dimensionality,
architecture and every other setting identical (the features are z-scored, so
zero is the mean and the channel becomes uninformative).

**Frozen predictions.** With APACHE zeroed, on eICU at five seeds:

- **F1** B falls below 0.75 AUROC (from 0.8212).
- **F2** Imbalance |A−B| falls below 0.08 (from 0.1463).
- **F3** Fusion gain over the better single modality **rises to at least
  +0.015** (from +0.0037), i.e. more than 3× its current value and well
  outside the five-seed spread of ~0.004.
- **F4** The direction of F3 is the test. A gain that stays flat or falls
  refutes the balance account.

## 4. What each outcome means

| Outcome | Reading |
|---|---|
| F1–F3 all hold | Balance is the operative condition. Fusion requires a competitive second stream, and the per-task criterion is stated in those terms. |
| F1, F2 hold but F3 fails | Balance is NOT sufficient. eICU's vitals stream carries no complement to admission data at this horizon, and the null is a property of the task. Report as such. |
| F1 fails | APACHE is not B's dominant signal; the lever is wrong and the test is inconclusive, not the hypothesis refuted. Try a different lever before concluding. |

Every row is reportable. The claim "fusion is conditional" is only worth making
if the condition is named and tested; otherwise it is a rationalisation of a
null.

## 5. Method fixed in advance

- `modality_ablation.py --dataset eicu --seeds 42 43 44 45 46
  --eval_every 250 --val_cap 40000 --max_steps 8000 --feat_b_zero 4`
- Identical to the run that produced the eICU row above, except `--feat_b_zero`.
- Primary metric AUROC for comparability with the table in §1; AUPRC reported.

## 6. Amendment F-A1 — 2026-09-20, before any result was read

The §1 eICU row was measured on `train = 2,649,217`. `make_public_split.py` has
since carved a disjoint pretraining pool out of the client training data, so the
current partitions hold `train = 2,122,350` — 20% smaller. A comparison of the
`--feat_b_zero` run against the §1 row would therefore confound the removal of
APACHE with a 20% reduction in training data.

**Correction, fixed before reading any output:** the control is re-measured on
the CURRENT partitions. Both conditions are run identically and differ only in
`--feat_b_zero`:

    control  : --out results/phase5/ablation_eicu_matched.json
    treatment: --feat_b_zero 4 --out results/phase5/ablation_eicu_noapache.json

Predictions F1–F4 stand unchanged, but are evaluated **against the matched
control**, not against the §1 row. The §1 row remains the number quoted in the
paper for eICU fusion, since it was measured on the full client training data;
it is not the comparator for this experiment.

## 7. Stage 2 — a titrated lever, registered 2026-09-20 after Stage 1 failed F2

Stage 1 used an all-or-nothing lever (zero APACHE) and **overshot**. It did not
produce balance; it reversed which modality dominates:

| condition | A | B | imbalance | fusion gain |
|---|---|---|---|---|
| matched control (APACHE intact) | 0.7068 | 0.8221 | 0.1153 | +0.0020 |
| Stage 1 treatment (APACHE zeroed) | 0.6973 | 0.5947 | 0.1026 | −0.0062 |

Imbalance moved only 0.115 → 0.103 against a target of <0.08, so **F2 was never
satisfied and the balance hypothesis was never actually tested.** Under §4's
outcome table this is "the lever is wrong", not "the hypothesis is refuted".

Worth recording separately: the matched control's +0.0020 is close to the §1
figure of +0.0037, so the 20% partition carve-out did not move the fusion
result. **The eICU fusion null is robust to that change.**

### The replacement lever

`--feat_b_scale 4:ALPHA` multiplies the APACHE channel by ALPHA. ALPHA=1 is
intact, ALPHA=0 reproduces Stage 1, and intermediate values titrate B's strength
continuously. This can hit a balance target, which a binary switch could not.

### Two stages, and why the split is not a search

**Stage 2a — calibration (NOT a test).** Run arm `b` only at
ALPHA ∈ {0.15, 0.30, 0.50}, two seeds, and pick ALPHA* whose B-arm AUROC lands
nearest to the A arm (~0.70). *Calibration targets the strength of modality B, a
property of one arm alone. It does not look at the fusion gain, so it is not
selection on the outcome.* This distinction is the whole legitimacy of the
design and must be stated in the paper.

**Stage 2b — the test.** Five seeds at ALPHA*, all three arms.

### Frozen predictions for Stage 2b

- **G1** imbalance |A−B| < 0.05 — i.e. the lever achieves what Stage 1 could not.
  *If G1 fails the lever is still wrong and no conclusion about balance follows.*
- **G2** fusion gain ≥ +0.015 over the better single modality.
- **G3** if G1 holds and G2 fails, **the balance hypothesis is refuted**, and the
  eICU fusion null is a property of the task: 24 h of vitals carries no
  complement to admission data. That is the conclusion the paper then states,
  and it is a stronger statement than "inconclusive".

G3 is the point of this stage. Stage 1 could not reach any conclusion; this
design reaches one either way.

## 8. Amendment F-A2 — 2026-09-21. The §7 lever was invalid; replaced before any test ran.

Stage 2a calibration returned arm B at **0.8214 ± 0.0007** under
`--feat_b_scale 4:0.15`, against **0.8221** intact. The lever did nothing.

The reason is arithmetic, not implementation, and the log confirms the scaling
was applied (`mean |value| 0.7120 -> 0.1068`). **Multiplying a feature by a
constant is information-preserving**: a linear encoder compensates with a
weight of 1/alpha, so every alpha > 0 is close to a no-op. Only alpha = 0
destroys anything, which is why §7's zeroing moved B to 0.5947 while a 0.15
scaling moved it nowhere. A multiplicative lever cannot titrate a modality's
strength, and §7's design could never have worked.

Caught by the calibration stage in about thirty minutes, before the five-seed
test consumed anything. That is what the stage was for.

### Replacement lever

`--feat_b_noise IDX:ALPHA` sets

    x' = ALPHA * x + sqrt(1 - ALPHA^2) * eps,    eps ~ N(0, 1)

Features are z-scored, so this **holds the channel's variance fixed while
degrading its signal-to-noise ratio monotonically**: ALPHA = 1 is intact,
ALPHA = 0 is pure noise. Information is genuinely removed and cannot be
recovered by rescaling a weight. The noise draw is seeded at a fixed constant so
every arm and seed sees the identical corruption, making the manipulation a
property of the data rather than a source of variance.

### Predictions carried over unchanged

G1 (imbalance < 0.05), G2 (gain >= +0.015) and G3 (if G1 holds and G2 fails, the
balance hypothesis is refuted and the eICU null is a property of the task) stand
exactly as frozen in §7. Only the instrument changed, and it changed because the
old one was measured to be inert — not because of anything observed about the
fusion gain, which stage 2a never looked at.

### Status

Deferred behind the multi-seed B4/B7/B6 sweep and the matched-budget VitalDB
k-grid, both of which bear on the paper's headline rather than on a secondary
question.

## 7. Amendment F-A1 — 2026-10-19. The registered lever is inert; replaced.

Recorded **before** any value of the replacement lever was computed.

§5 fixed the intervention as `--feat_b_zero 4` and the executing script
titrated it as `--feat_b_scale 4:ALPHA`. That lever does not work.
Modality B is z-scored and its encoder is linear in the first layer, so
multiplying one feature by `ALPHA` is undone exactly by a `1/ALPHA` weight:
the transformation is **information-preserving**, and no `ALPHA > 0` changes
what B can predict.

This is not inferred. It is measured on the single calibration point that
completed before the 2026-09-21 crash:

| lever | arm B AUROC | intended |
|---|---|---|
| intact | 0.8221 | — |
| `--feat_b_scale 4:0.15` | 0.8214 | move B toward A = 0.7068 |

The lever moved B by 0.0007 when it was asked to move it by about 0.115. A
titration grid built on it would have returned a flat curve and an `ALPHA*`
chosen from noise.

**Replacement.** `--feat_b_noise IDX:ALPHA` mixes the channel with fixed-seed
Gaussian noise, `x -> a*x + sqrt(1 - a^2) * eps`, which destroys information
rather than rescaling it. `a = 1` is intact and `a = 0` is pure noise, so the
endpoints still bracket `--feat_b_zero`. The calibration grid is
`a in {0.20, 0.40, 0.60, 0.80}` at two seeds, and `ALPHA*` is the point whose
arm-B AUROC is nearest arm A's, read from `ablation_eicu_matched.json` rather
than hardcoded. If no grid point brings B within 0.04 of A the script says so
and the stage-2b result is not to be read as a balanced comparison.

**What does not change.** F1-F4 stand exactly as written in §3, including the
registered decision table in §4. Only the mechanism of the intervention is
replaced, because the registered one provably cannot effect the intervention
it describes. F1's threshold ("B falls below 0.75 AUROC") is now the
calibration target rather than a prediction, since `ALPHA*` is selected to
approach A = 0.7068; F2 follows by construction for the same reason. **F3 is
therefore the whole of the test**, and it is untouched: fusion gain over the
better single modality rises to at least +0.015, against +0.0020 measured on
the matched control. F4's reading is unchanged — flat or falling refutes the
balance account.

Noted for the write-up: because `ALPHA*` is now chosen to equalise the arms,
F1 and F2 may no longer be cited as confirmed predictions. They are
preconditions the calibration establishes. Reporting them as hits would be
exactly the retrofit this registration exists to prevent.
