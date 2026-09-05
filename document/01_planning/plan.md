# eICU-CRD External Validation — the complete plan

Rev 3 · 2026-09-05 · **eICU only.** BRSET/mBRSET are parked until this is
finished. The BRSET-focused rev 1 has been deleted; if that corpus is revived
later, the image-encoder audit is re-derivable from the code in minutes.

Sources this plan is built from: `document/03_research_dossier/HFL_Research_Dossier.html`
(§9–§10, §26–§31), `HFL_Dossier_Part2_Technical.html` (§2, §9),
`HFL_Dossier_Part3_Experiments.html` (E13, E16–E19, E24),
`document/01_planning/EICU_INTEGRATION_SPEC.md`, `document/01_planning/PREREGISTRATION_EICU.md`,
`document/05_reference/physionet/eICU Collaborative Research Database.txt`.

---

## 1. What is lacking, in one line

> *"Is this a property of patient-level private federated learning, or a
> property of your dataset?"* — Dossier Pt2 §9.1

Every privacy claim in this research rests on **one dataset from one hospital**.
VitalDB is a single institution and its nine "clients" are a partition we
invented. WEAR cannot help: 22 people, one client each, no patient contributing
enough records for the k-law to even be defined. The project cannot currently
answer the reviewer's question. That is the whole gap. Nothing else is missing.

Dossier §27.1 is explicit that exactly **one** work item is blocked on data
access — *running the eICU arms*. Everything else was always doable. So this
plan is short by design: it is one experiment, done properly.

## 2. Why eICU specifically, and not something else

| Property | Why the research needs it |
|---|---|
| **208 real hospitals** | Clients become actual institutions instead of a partition we invented. Federated learning is supposed to model this; we currently only simulate it. |
| **~139k independent patients** | Different demographics, care patterns, equipment. If the k-law survives that, it is structural. |
| **Many records per patient** | The k-law needs it. VitalDB tops out near k=8; eICU **stretches the curve into a range VitalDB cannot reach**. This is the decisive property. |
| **Same modality structure** | Time-series vitals + static clinical. `modality_b="features"` applies, **no new encoder**. Weeks, not months. |
| **Credentialed + CITI** | Reviewers trust PhysioNet, and the access process is itself evidence of proper conduct. |
| **Widely used benchmark** | Comparable against published work. A private partition is not. |

Rejected in `EICU_INTEGRATION_SPEC.md`: MIMIC-IV+CXR (4.7 TB, new encoder —
next paper), HiRID (same structure as VitalDB, corroborates little), PTB-XL
(single-modality, fails pairing and headroom).

## 3. What we are proving

The headline result (Dossier §10, E18) is the **k-scaling law**: the utility
cost of a patient-level privacy guarantee grows with the number of records each
patient contributes. Measured on VitalDB, AUPRC gap = record arm − patient arm:

| k | 1 | 2 | 4 | 8 |
|---|---|---|---|---|
| gap | −0.0052 | +0.0507 | +0.0832 | +0.0866 |
| p | 0.75 | 0.0017 | 0.0015 | 0.0049 |

Two properties make it strong (§10.1):

1. **It carries its own positive control.** At k=1 a patient *is* a record, so
   the two guarantees are mathematically identical and the arms must collapse.
   They do (p=0.75). A validated null inside the same experiment as the positive
   effects — the design property the membership-inference work initially lacked.
2. **The mechanism is asymmetric and must be stated that way.** The patient arm
   is flat in k (0.4967–0.5176 at every k); the record arm rises (0.5015 →
   0.5955). The widening gap is *the record arm improving*, not the patient arm
   degrading. Patient-level noise scales with per-patient contribution, so extra
   records buy the patient arm nothing.

**The forecast is now numeric.** Fitted on VitalDB alone, frozen in
`document/01_planning/PREREGISTRATION_EICU.md`:

```
gap(k) = 0.0878 · (1 − exp(−0.883·(k−1)))
A = 0.0878 ± 0.0035   b = 0.883 ± 0.129   RMSE = 0.0028
```

**The curve saturates — 90% of the ceiling by k = 3.6.** That is the risky,
falsifiable content, and it is testable **only at k > 8**, which is precisely
what VitalDB cannot do and eICU can.

## 4. How we prove it — and the one rule

Dossier Pt2 §9.3:

> *"We will not simply run the same experiment and add another table. That is
> worth little. Instead: fit the k-curve on VitalDB, write down a numeric
> prediction of what the gap should be at eICU's k, **freeze that prediction
> before touching the data**, then test it."*

The pre-registration is written and dated. **It must be committed before the
first build run.** Its value is that it can fail: per §30, a hit yields a
transferable design rule practitioners actually need — *given your k, this is
what patient-level ε=1 costs you*, which nobody has published — and a miss
yields a boundary condition with a dated forecast proving nothing was
retrofitted. A paper testing two independent clinical corpora, one confirming
and one exposing a limit, is stronger than one where everything worked.

## 5. Implementation state

| Component | State |
|---|---|
| `data/loaders/preprocess_eicu.py` | **Rewritten, real-table loading implemented** (previously raised `SystemExit`). Streams `vitalPeriodic` in chunks; memory-mapped accumulator. Self-test passes. |
| `data/loaders/eicu_dataset.py` | **New.** Same 4-tuple contract as VitalDB. |
| `datasets.py` REGISTRY | **`eicu` added.** `n_devices` / `n_channels_a` / `feat_b_dim` resolve from `dataset_meta.json` after the build. `wear` (22/12/2048) and `vitaldb` (9/18/34) verified unchanged. |
| `document/01_planning/PREREGISTRATION_EICU.md` | **Written**, with the numeric curve fit. **Uncommitted — commit before E2.** |
| Data location | `SIMULATORS/data/raw/eicu/` — gitignored (`SIMULATORS/.gitignore:9`) and deny-listed (64 rules, 4 roots). Claude cannot read it. |

### Three defects fixed during the rewrite

1. **Windows lost their time axis.** The old `window_stays` did
   `mat[sel].mean(0)`, collapsing each hour to `[C]` → modality A of `[N, 6]`.
   `encoder_a` is FedMambaHC and takes `[B, C, T]` (`fedmamba_hc.py:47`). That
   data could never have been fed to the model. Windows now resample onto a
   fixed 12-slot grid → `[N, 12, 12]` (6 vitals + 6 observed-masks).
2. **`case_ids.npy`, not `group_ids.npy`.** Nine consumers hardcode
   `meta/case_ids.npy`; only `validate_corpus.py:85` accepted both. The wrong
   name makes patient-level DP, LiRA and k-scaling silently fall back to record
   level. Fixed; the self-test now asserts the filename.
3. **The window cap defeated the purpose.** `MAX_WINDOWS_PER_STAY` was 8 —
   exactly VitalDB's range, so P1c (saturation) would have been untestable and
   the corpus would have added nothing beyond a second table. Raised to **48**,
   giving k up to 32, with the accumulator memory-mapped so it still runs on an
   ordinary workstation.

Also handled: eICU stores `age` as text with `"> 89"` masked for HIPAA (mapped
to 90, not dropped — dropping biases the cohort young against the acuity
signal); `gender` as strings; APACHE in a separate table joined on stay.

## 6. Execution order

Cheapest disqualifier first. Every step has a gate.

| # | Step | Command (from `SIMULATORS/`) | Gate |
|---|---|---|---|
| **E0** | **Commit the pre-registration** | `git add document/01_planning/PREREGISTRATION_EICU.md` | **Must precede E2. Non-negotiable.** |
| E1 | Verify schema | `preprocess_eicu.py --verify_schema` | Headers only, no data values. Fix any mismatched `SCHEMA` constant first. |
| E2 | Build corpus | `preprocess_eicu.py` | `--max_stays 20000` for a fast first pass. |
| E3 | Validate corpus | `validate_corpus.py --datasets eicu` | **Do not proceed past a CAPACITY failure.** Needs ≥1,200 individuals, ≥2.0 records/individual, headroom < 0.95. |
| E4 | Ceiling check | `modality_ablation.py --dataset eicu --seeds 42 43 44 45 46` | **P2a. Stop if the better arm > 0.95 AUROC.** |
| E5 | Pretrain encoders | `pretrain_encoders.py --dataset eicu` | **Disjoint population, not oracle** — so eICU does not inherit the §26 validity gap. |
| E6 | Main operating point | `hfl_trainer.py --dataset eicu --epsilon 0.80 --epsilon_conf 0.20 --batch_size 64 --rounds 10 --tau_e 5` | The published configuration. |
| E7 | Objectives | `check_objectives.py --dataset eicu` | O1, O1b, O2a/b, O3a/b, O4. |
| **E8** | **k-scaling — the experiment** | `k_scaling.py --dataset eicu --k 1 2 4 8 16 32 --seeds 42 43 44` | **P1a–P1f.** k=1 is the built-in control. **k=16, 32 are the point of the corpus.** |
| E9 | LiRA + positive control | `lira_attack.py --dataset eicu` | P3a–P3d. Null inadmissible without a passing control. |
| E10 | Component ablation | `component_ablation.py --dataset eicu --seeds 42 43 44` | A0–A5; P4b. |
| E11 | Uplink / compression | `measure_uplink.py --dataset eicu` | Re-measure, do not assume. |

## 7. How this completes the research

Mapping each remaining hole to the step that closes it:

| Gap (Dossier) | Closed by |
|---|---|
| §9.1 — every claim rests on one single-institution dataset | E8 on 208 real hospitals |
| §27 — k-law structural or dataset-specific? unanswerable | E8 against a frozen numeric forecast |
| §9.2 — curve cannot be stretched past VitalDB's k | E8 at k=16, 32 (the reason the cap was raised) |
| §26 — encoders pretrained in oracle mode, ε=1 not end-to-end | E5 with the disjoint population |
| §21–22 — fusion single-domain, gain shrank at 5 seeds | E4 at 5 seeds, reported as a setting result |
| §16 — MIA null needs power | E9 at ~139k patients |
| Federation is constructed, not natural | E10 / P4a–P4b |

## 8. Reporting rules, fixed now

- **Never write "there is no effect"** for the MIA null (§2.3). Write: the large
  predicted effect is refuted; a small effect is not excluded.
- **Accuracy is not quoted** for k-scaling arms — pinned at 0.8005 by an
  uncalibrated 0.5 threshold on imbalanced data (§10.2).
- **AUPRC resolves; AUROC is directionally consistent but underpowered** at n=3.
- **Fusion: 5 seeds only.** The 2-seed figure fell 37% in AUPRC.
- The k=1 control is reported in every k-scaling table, always, as the thing
  that licenses reading the rest.

## 9. Not in scope

BRSET and mBRSET. DUAs may be signed — that costs nothing and preserves
optionality — but **no code, no registry entry, no image encoder, no
preprocessing** until eICU is complete through E11. The image encoder path is
REMOVED from this codebase (`hfl_mm_model.py:170` raises on
`modality_b="image"`; no `Conv2d` under `model/`); reviving it is ~200 lines
across 6 files and is a distraction from the one experiment that answers the
reviewer's question. That audit is re-derivable from the code
whenever it is next needed.

Also out of scope until E11: window-count-normalised patient clipping,
conformal coverage validation, mask-channel ablation, multi-seed baselines.
Real items, all of them — none of them is the validity gap.

## 10. Immediate next action

Download finishes → `preprocess_eicu.py --verify_schema` → paste the output
(column names and counts only, safe to share) → fix any `SCHEMA` mismatch →
**commit the pre-registration** → build.
