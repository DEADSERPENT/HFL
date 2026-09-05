# Adding a second clinical corpus (eICU) — integration spec

Written 2026-08-16. Purpose: remove the single-corpus exposure that caps this
work, without rebuilding the pipeline.

## Why eICU specifically

The weakness is not "only two datasets". It is that **one dataset carries every
core claim**, because `wear` is structurally unable to corroborate any of them:

| requirement | why the claim needs it | wear |
|---|---|---|
| many individuals per client | else client-level DP == individual-level DP | 1 per client |
| many records per individual | k-scaling needs something to vary | ✗ |
| ≥ ~1,200 individuals | patient-level MIA uses 600 + 600 | 22 |
| task with headroom | fusion must have room to help | ceilings at 0.9976 |

eICU satisfies all four. It also fixes a weakness not yet raised in review:
**VitalDB's nine clients are constructed by grouping surgical optype**, which is
a defensible but synthetic federation. eICU's clients are *actual hospitals* —
a naturally non-IID partition, which for a paper titled "Hierarchical Federated
Learning" is arguably worth more than the second modality.

**Cost is low because the modality structure matches.** eICU is vitals
time-series + tabular clinical, the same shape as VitalDB, so
`modality_b="features"` applies and **no new encoder is required**. The model,
DP engine, compression, conformal layer and every script transfer unchanged.

Rejected alternatives:
- **MIMIC-IV + MIMIC-CXR** — a stronger multimodality claim (image + tabular are
  genuinely distinct, where VitalDB's two streams are both physiological), and
  `modality_b="image"` is already supported. But CXR is ~4.7 TB and needs a new
  encoder path. Better as the *next* paper.
- **HiRID** — same domain and modality structure as VitalDB, so it corroborates
  little that VitalDB does not already show.
- **PTB-XL** — largely single-modality ECG; fails the headroom and pairing tests.

## What must be true of the preprocessing

The claims depend on these, so they are requirements and not preferences.

1. **Pairing must be at source.** Both modalities from the same patient over the
   same window. If the tabular vector is a hospital-level or cohort-level
   aggregate joined onto a patient, the multimodal claim is void — that is the
   synthetic pairing this work exists to avoid.
2. **Patient identity must survive into the arrays**, as a `group_ids` vector
   aligned to labels. Patient-level DP, patient-level MIA, k-scaling and
   case-level metrics all key on it. VitalDB carries case ids the same way.
3. **The split must be patient-disjoint**, never window-level. A patient
   appearing in both train and test leaks through correlated windows and would
   inflate every utility figure.
4. **Clients = hospitals**, taken as given rather than constructed. Report the
   resulting label-prevalence spread as evidence of genuine non-IIDness, as the
   VitalDB entry does (3.2%–50.7% ICU base rate).
5. **Check for a ceiling before committing.** Train the two single-modality arms
   first via `modality_ablation.py`. If the better one exceeds ~0.95 AUROC, the
   corpus cannot evidence fusion and is not worth the rest of the pipeline. This
   is the check `wear` failed, and it costs one afternoon rather than a month.

## Integration points

The registry interface is declarative; adding a corpus is a spec entry plus a
builder.

- `SIMULATORS/data/loaders/datasets.py` — add a `DatasetSpec` to `REGISTRY`:
  `n_devices` (hospital count after any minimum-size filter), `n_classes`,
  `n_channels_a`, `modality_b="features"`, `feat_b_dim`, `pairing` (state the
  at-source mechanism), `required_files`, and a lazy `build_full`.
- Preprocessed arrays under `data/processed/eicu/`, matching `required_files`.
- Partitions under `data/processed/partitions/eicu/`: per-device
  `device_XX_{train,val,test}.npy` plus `partition_meta.json` carrying
  `n_devices`, `n_edges`, `edge_assignments`.
- `checkpoints/pretrained_encoders_eicu.pt` via
  `model/training/pretrain_encoders.py`. Use the **disjoint** population, not
  the oracle configuration, so the new corpus does not inherit the upper-bound
  caveat that currently qualifies every VitalDB utility.

Nothing else needs editing: every downstream script resolves its dataset from
the registry, which is why no hardcoded paths exist in them.

## Order of execution

Cheapest disqualifying test first, so a corpus that cannot serve is abandoned
early.

1. Preprocess; verify pairing, `group_ids`, and patient-disjoint splits.
2. `modality_ablation.py --dataset eicu --seeds 42 43 44 45 46`
   — **stop here if the better single modality ceilings.**
3. `pretrain_encoders.py --dataset eicu` (disjoint population).
4. `hfl_trainer.py --dataset eicu ... --epsilon 0.80 --epsilon_conf 0.20
   --batch_size 64 --rounds 10 --tau_e 5` — the published operating point.
5. `check_objectives.py --dataset eicu` (O1, O1b, O2a/b, O3a/b, O4).
6. `k_scaling.py --dataset eicu` — the k=1 collapse is the built-in control;
   if the arms do not coincide at k=1, the harness is wrong, not the finding.
7. `lira_attack.py --dataset eicu` with a **non-private positive control**. A
   null without a passing control is inadmissible.
8. `component_ablation.py --dataset eicu --seeds 42 43 44`.

## Effort and calendar

| stage | effort |
|---|---|
| PhysioNet credentialing (CITI + DUA) | days–2 weeks calendar, little effort |
| preprocessing + partitioning | the real work |
| registry integration | small |
| full pipeline re-run | days of compute |

**2–4 weeks end to end**, dominated by access and preprocessing.

## Recommended sequencing against submission

Do **not** hold the current submission for this. Start credentialing now — it
costs calendar time regardless — and submit with the single-corpus limitation
stated plainly (`discussion.tex`, "The privacy-unit results are single-domain"
and "The fusion result is single-domain"). Reviewers are likely to ask for a
second corpus; when they do, their report says *which* claims they doubt, so the
three weeks of work go where they change the verdict. A revision window of 4–8
weeks is exactly this timeline.

A limitation that is measured, explained and disclosed reads as rigour. The same
limitation discovered by a reviewer reads as an oversight.
