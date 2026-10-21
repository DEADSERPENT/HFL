# Pre-registration — N-D, normalised patient clipping

Written 2026-09-20, **before the experiment was run**. Same rule as the other
two registrations in this folder: the prediction is frozen first.

## 1. The mechanism being tested

Under `--dp_unit patient` a patient's gradient is summed over their k windows
and then clipped to a fixed norm C (`model/privacy/patient_dp.py`). The pre-clip
norm therefore grows with k, so patients with long recordings saturate the clip
and are systematically down-weighted. The module's own docstring already noted
this as a cost.

**The claim:** that penalty is an artefact of the clipping rule, not an inherent
cost of a patient-level guarantee. Rescaling the summed gradient by k or sqrt(k)
*before* the clip removes the dependence of the pre-clip norm on k.

**The guarantee is unchanged.** Sensitivity is set by the clip, not by what is
clipped: after rescaling, every patient's contribution is still bounded by C, so
removing one patient still moves the sum by at most C. Sigma, epsilon and delta
are identical across arms, verified by inspection — `clip_norm` appears nowhere
in the noise-multiplier or accountant code paths. The arms therefore compare at
a matched budget, and any difference is optimisation geometry.

Arithmetic check run before the experiment, C = 1, pre-clip norm proportional
to k: under `none` the clip binds from k = 8 upward; under `k` it never binds;
under `sqrt_k` it binds only at k = 32. The clipped norm is <= C in all three.

## 2. Why this matters to the headline result

The k-scaling law reports that the **patient arm is flat in k** while the record
arm rises, and concludes that extra records per patient buy the patient arm
nothing. If saturation is the cause, that flatness is a property of *this
clipping rule* rather than of the guarantee, and the paper's central cost
figure is partly an artefact of an implementation choice.

## 3. Frozen predictions — VitalDB, k = 8, patient arm, 3 seeds

Comparator is `clip_norm=none` at the same k, seeds, partitions and budget.

- **N1** `clip_saturation` under `none` exceeds 0.50, and falls below 0.10
  under `k`. *(This is the mechanism check. If N1 fails the lever does not do
  what it is designed to do and the rest is uninterpretable.)*
- **N2** The patient arm's AUPRC under `clip_norm=k` exceeds its value under
  `none` by at least **+0.02**.
- **N3** Consequently the record-minus-patient gap at k = 8 shrinks from the
  published $0.0866$ by at least $0.02$.
- **N4** AUROC moves in the same direction but is not required to resolve at
  three seeds.

## 4. What each outcome means

| Outcome | Reading |
|---|---|
| N1, N2, N3 hold | The cost of a patient-level guarantee is **partly an artefact of fixed-norm clipping and is reducible**. This is an original mechanism, not a measurement, and it becomes a contribution in its own right. |
| N1 holds, N2 fails | Saturation is real but is not what suppresses the patient arm. The cost is inherent to the guarantee, which **strengthens** the existing cost claim. Report as a negative. |
| N1 fails | The lever does not remove saturation; the implementation is wrong, not the hypothesis. Fix before concluding anything. |
| `sqrt_k` between the two | Expected if the effect is graded rather than binary; report the curve. |

Every row is reportable, and the second is as useful to the paper as the first.

## 5. Method fixed in advance

- `hfl_trainer.py --dataset vitaldb --dp_unit patient --clip_norm {none,k,sqrt_k}`
- Partitions reused from `results/phase5/k_scaling/vitaldb/k8_seed{42,43,44}`,
  so both arms see identical data.
- Operating point unchanged: `--epsilon 0.80 --batch_size 64 --patients_per_batch 64
  --rounds 10 --tau_e 5 --freeze_encoders`.
- Primary metric AUPRC, consistent with the k-scaling law.
- `none` is re-run rather than taken from the published table, so the
  comparison cannot be confounded by anything that changed since.

## 6. Amendment N-A1 — 2026-09-21. N1 FAILED AS WRITTEN; recorded, not rewritten.

N1 required clip saturation above 0.50 under `none` and below 0.10 under `k`.
Measured directly through `patient_level_dp_train` (probe
`scripts/probe_clip_saturation.py`):

| corpus / split | windows/patient sd | none | k | sqrt_k |
|---|---|---|---|---|
| VitalDB, k=8 partition | 0.67 | 0.6847 | 0.4069 | 0.5556 |
| eICU, natural partition | 18.13 | 0.3945 | 0.2039 | 0.2939 |

**N1 fails on both. The threshold was mis-specified, and the reason is a fact
about the data that was not known when it was written.**

Two findings explain it, and both are kept:

**(a) VitalDB cannot test N-D at all.** Its natural partition is identical to
the k=8 capped one — min 3, median 8, max 8, sd 0.67. Nearly every patient
contributes exactly eight windows, so there is no k-dependence to correct and
dividing by k is a uniform rescale. **The VitalDB N-D run is therefore not a
valid test of N-D and its utility numbers are not reported as one.** eICU is
~21x more heterogeneous (2 to 192 windows per patient) and is the only corpus
here that can carry the claim.

**(b) Saturation rises with k, but k is not its dominant driver.** On eICU,
across 2,923 per-patient gradients at C = 1:

    k bin     patients   mean pre-clip norm   saturation
    1–4             27                1.784        0.148
    5–12           125                2.708        0.216
    13–24        1,937               61.838        0.384
    25–48          605               58.622        0.436
    49+            229               69.070        0.502

    Spearman rho(k, pre-clip norm) = +0.245, p = 2.5e-41
    Spearman rho(k, saturated)     = +0.138, p = 6.0e-14

The direction N-D predicts is confirmed and highly significant: patients with
the most records are truncated at 0.502 against 0.148 for those with fewest, a
3.4x difference. But rho = 0.138 means k accounts for a small share of the
variance, and mean norms of 60+ against C = 1 show most patients saturate for
reasons independent of k. Dividing by k therefore **halves** saturation rather
than removing it, which is what was measured.

**N1 is reported as FAILED as written.** It is not restated to make it pass;
restating a gate after seeing its result is the move this project refuses
elsewhere. What replaces it is knowledge the gate produced: the premise holds
directionally, the effect is real and significant, and its magnitude is smaller
than N-D assumed.

**Consequence for N2/N3.** They remain as frozen. The utility test is worth
running on eICU because saturation halves there, but any result must be read
against a mechanism that is secondary rather than dominant — a large utility
gain would now be surprising, and its absence would not refute the measured
penalty in (b), which stands on its own as a finding.

## 7. Amendment N-A2 — 2026-10-19. N-D moves to eICU, on the NATURAL partition.

Written **before any eICU utility run exists**. The only eICU artefact on disk
at this date is the saturation probe quoted in N-A1
(`results/phase5/nd_clipnorm/eicu/clip_saturation_natural_seed42.json`); no
AUPRC under any `clip_norm` mode has been computed on this corpus.

### 7.1 Why the corpus changes

N-A1 established that VitalDB's natural partition is flat — min 3, median 8,
max 8, sd 0.67 — so dividing by `k` is a uniform rescale there and the VitalDB
run is not a valid test of N-D. That run stands in the record as reported, a
null of `+0.0014 ± 0.0072` (`k` vs `none`, p = 0.489) that is **not** evidence
about the hypothesis. eICU's natural partition spans 2 to 192 windows per
individual at sd 18.13, about 21x more heterogeneous, and is the only corpus
here that can carry the claim.

### 7.2 The partition is the substantive change

The N-D runner previously took its partitions from the k-scaling tree, which is
**capped at k windows per individual**. Running eICU that way would cap the
very dispersion that makes eICU able to test N-D, and would reproduce the
VitalDB defect on a second corpus. The runner now accepts `--partition_dir`
and the registered eICU run uses the registry partition, uncapped.

Consequence, recorded rather than worked around: the k-scaling record arm
exists only on capped partitions, so **N3 cannot be evaluated as written** on
this corpus — there is no natural-partition record arm to take a gap against.
N3 is therefore reported as NOT TESTED on eICU rather than restated into
something the available arms happen to support. The test reduces to N2, which
is internal to the patient arm and needs no comparator outside it.

### 7.3 Measured, not predicted

From the N-A1 probe, 2,965 individuals, `max_grad_norm` C = 1:

| mode | saturation |
|---|---|
| `none` | 0.3945 |
| `k` | 0.2039 |
| `sqrt_k` | 0.2939 |

The lever **halves** saturation on eICU; it does not remove it. This is already
in the record and is not restated as a prediction.

### 7.4 Frozen predictions — eICU, natural partition, patient arm, 3 seeds

Comparator is `clip_norm=none` at the same partition, seeds and budget
(`--epsilon 0.80`, identical across modes: `clip_norm` changes optimisation
geometry only and never sensitivity).

- **N2e** The patient arm's AUPRC under `clip_norm=k` exceeds its value under
  `none` by at least **+0.010**.

  *How the threshold was set, before seeing any value.* The original N2 asked
  for +0.02 on a corpus whose attainable AUPRC is about 0.50. eICU's arms move
  within [0.196, 0.245] against a prevalence of 0.0422, roughly 44% of
  VitalDB's attainable precision. An effect that is a fixed fraction of
  attainable precision therefore appears here at about 0.44 x 0.02 ~ +0.009,
  rounded to +0.010. This is the same scaling argument the eICU k-scaling
  section already offers as its hypothesis for the reduced ceiling, applied in
  advance rather than after the fact.

- **N3e** NOT TESTED on this corpus — see 7.2. Reported as such.

- **N4e** AUROC moves in the same direction as AUPRC but is not required to
  resolve at three seeds, consistent with every other result on this corpus.

- **N5e** `sqrt_k` falls between `none` and `k` on AUPRC, matching its
  intermediate saturation (0.2939 against 0.3945 and 0.2039). A `sqrt_k` that
  lands outside that interval is evidence the effect is not monotone in the
  normalisation and is reported as such.

### 7.5 What each outcome means

The decision table of §4 carries over unchanged, read against N2e:

| Outcome | Reading |
|---|---|
| N2e holds | The cost of an individual-level guarantee is **partly an artefact of fixed-norm clipping and is reducible**. An original mechanism, and a contribution in its own right. |
| N2e fails | Saturation is real and k-graded (N-A1 showed both, significantly) but is **not** what suppresses the individual arm. The cost is inherent to the guarantee, which **strengthens** the k-scaling cost claim. Reported as a negative, and it is as useful to the paper as the positive. |
| N5e fails | The effect is not monotone in the normalisation; report the curve and do not describe the lever as graded. |

Both N2e outcomes are reportable and the write-up is committed to reporting
whichever occurs. At three seeds the test is underpowered by the same argument
the k-scaling section makes about itself, and the result is to be quoted with
that stated, not laundered.

### 7.6 Method fixed in advance

    python SIMULATORS/scripts/run_nd_clipnorm.py \
      --dataset eicu \
      --partition_dir SIMULATORS/data/processed/partitions/eicu \
      --seeds 42 43 44 --modes none k sqrt_k \
      --epsilon 0.80 --batch_size 64 --rounds 10 --tau_e 5

Nine runs, patient arm only, frozen pretrained encoders
(`checkpoints/pretrained_encoders_eicu.pt`, public-split, no oracle caveat).
Primary metric AUPRC. Artefacts land under
`results/phase5/nd_clipnorm/eicu/` tagged `natural_seed{S}_{mode}`, which
cannot collide with a capped run. Estimated cost ~3 h per run, ~27 h total,
extrapolated from the eICU k-scaling grid (2.55 h per arm at k = 16).
