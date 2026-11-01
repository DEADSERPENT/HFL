# PP-HFM — Figure Specification (10 new figures)

Reference sheet for redrawing every figure in the paper from scratch.
Written 2026-10-21. Every number quoted below is read from a file under
`SIMULATORS/results/`; draw from the file, never from this sheet.

---

## Status (as built, updated 2026-10-21 21:10)

All 10 figures are drawn and placed. Each one has its own script in
`paper/figures/`, shares the house style in `_figstyle.py`, and reads its
numbers from the result files. Run a script with `cd paper/figures && python3
figNN_*.py`. It writes `figNN_*.pdf`, which the paper uses, and a 300 dpi
`figNN_*.png` for previewing. The paper builds cleanly at 26 pages.

| Spec # | Script → PDF | `\label` | Printed as | Placed in | Status |
|---|---|---|---|---|---|
| 1 | `fig01_overview.py` | `fig:pphfm_arch` | Fig. 1 | method.tex | done, but see open item 1 |
| 2 | `fig02_privacy_unit.py` | `fig:sensitivity` | Fig. 3 | method.tex | done; (b) from a transcribed CSV, see Fig. 2 |
| 3 | `fig03_klaw.py` | `fig:klaw` | Fig. 8 | results.tex | done |
| 4 | `fig04_arms.py` | `fig:arms` | Fig. 9 | results.tex | done |
| 5 | `fig05_init_vs_subset.py` | `fig:epsilon` (reused) | Fig. 7 | results.tex | done; replaced `fig8_epsilon` |
| 6 | `fig06_fusion_map.py` | `fig:fusionmap` | Fig. 12 | results.tex | done |
| 7 | `fig07_titration.py` | `fig:titration` | Fig. 11 | results.tex | done |
| 8 | `fig08_clipnorm.py` | `fig:clipnorm` | Fig. 10 | results.tex | done |
| 9 | `fig09_system_cost.py` | `fig:energy` (reused) | Fig. 6 | results.tex | done, all three deployments |
| 10 | `fig10_ablation_mia.py` | `fig:ablation` | Fig. 13 | results.tex | done |

"Printed as" is the number LaTeX gives it, in order of first appearance.
**The spec numbers are not the printed numbers**, because three earlier figures
are still in the paper and float between the new ones. These three are kept:

| Old figure | `\label` | Printed as | Where | Why it was kept |
|---|---|---|---|---|
| `fig2_backbone.pdf` | `fig:backbone` | Fig. 2 | method.tex | encoder–fusion backbone; no new figure covers it |
| `fig4_lira.pdf` | `fig:lira` | Fig. 4 | method.tex | method diagram (per-patient calibration). Spec 10 was meant to replace it, but it explains the method, not a result |
| `fig6_noniid.pdf` | `fig:noniid` | Fig. 5 | experiments.tex | partition heterogeneity; no new figure covers it |

Removed from the paper: `fig1_architecture`, `fig3_sensitivity`,
`fig5_patientdp` (its text now points to Algorithm `alg:patientdp`),
`fig7_energy`, `fig8_epsilon`. The old PDFs and `make_method_figures.py` are
still on disk.

**Open items.** None of these need a new experiment.
1. ~~Fig. 1 prints larger than drawn.~~ **Fixed 2026-10-21.** The tight-cropped
   PDF was 5.59 in wide and printed at 1.28×. It is now drawn on full-bleed
   axes, so the PDF is 7.20 in wide and prints at 0.99×.
2. **Printed order does not follow the spec.** Fig. 7 (titration) prints
   before Fig. 6 (fusion map), and Fig. 9 (system cost) prints as Fig. 6.
   That is fine as long as each figure is cited in the text before or on the
   page it floats to. Re-check this after the length cut.
3. **The paper has 13 figures in total**: these 10 plus the 3 kept ones. The
   cut advice under "Overview" (merge 4 into 3, drop 10b) still applies. The
   length cut is deferred until the journal is chosen.
4. ~~Two small rounding differences between figure and text.~~ **Fixed
   2026-10-21.**
   - results.tex now says ε = 0.7704, matching the file (0.770429) and Fig. 1.
   - Fig. 3 no longer refits the law. It reads the registered A = 0.0878 and
     b = 0.8827 from the `A = …` / `b = …` lines of
     `document/01_planning/PREREGISTRATION_EICU.md`. That file fitted the
     4-decimal table gaps; refitting the unrounded means gives b = 0.8819.
     Panel (b) claims to test the curve frozen before eICU existed, so
     drawing the frozen curve is the correct fix, not just a cosmetic one.
5. ~~Fig. 9(b) has no eICU bars yet.~~ **Done 2026-10-22 06:57.**
   `run_eicu_finalize.sh` redrew the figure from `ns3_results_eicu.csv`:
   eICU 261.4 → 174.1 ms, with communication 194.6 → 115.5 ms. On eICU,
   unlike the other two deployments, communication dominates the round.

---

## 0. House rules (IEEE TII / IEEE IoT-J, Q1)

These apply to **every** figure. A Q1 reviewer rejects figures on these grounds
before reading the caption.

| Item | Requirement |
|---|---|
| Width | Single column **3.5 in (88.9 mm)**; double column **7.16 in (181.9 mm)**. Never in between. |
| Height | ≤ 0.6 × width for plots; ≤ 9.0 in absolute. Leave room for the caption. |
| File format | **Vector PDF** (or EPS) for every plot and diagram. Raster only for photos: ≥ 300 dpi colour, ≥ 600 dpi line art. Embed all fonts (`pdffonts` must show `emb yes`). |
| Font | Times New Roman / Helvetica, matching the paper. **8 pt** axis labels and legends, **7 pt** minimum anywhere, **9 pt** panel letters. Same size in every figure. |
| Lines | ≥ 0.5 pt; data lines 1.0–1.5 pt; error bars 0.75 pt with caps. |
| Colour | Colour-blind safe (Okabe–Ito palette below). Must still be readable in **greyscale**, so pair colour with marker shape or line style. |
| Panels | Bold lowercase **(a), (b), (c)** at top-left, outside the axes. |
| Axes | Label + unit in brackets, e.g. `Average precision`, `Uplink per round [MB]`. Ticks inward or outward, consistent across figures. No top/right spines. |
| Uncertainty | Every point estimate has its interval. State the interval type (Student-*t* 95 %) and *n* seeds in the caption. |
| No chart junk | No 3-D, no shadows, no gradient fills, no titles inside the plot (the caption is the title), no grid except faint y-grid where values must be read. |
| Caption | First sentence = what is plotted. Then n, interval type, and the one thing the reader should see. Define every abbreviation. |
| Numbering | In order of first citation in the text; each figure cited at least once. |

### Fixed colour and marker code (use in all 10 figures)

| Meaning | Colour (Okabe–Ito) | Hex | Marker / line |
|---|---|---|---|
| Individual-level DP (proposed unit) | vermilion | `#D55E00` | ● solid |
| Record-level DP | blue | `#0072B2` | ■ dashed |
| Non-private / control | grey | `#7F7F7F` | ◆ dotted |
| Pretrained initialization | bluish green | `#009E73` | ▲ |
| Random initialization | orange | `#E69F00` | ▼ |
| Fused model | reddish purple | `#CC79A7` | ★ |
| Forecast / reference curve | black | `#000000` | thin dashed |
| Corpus: VitalDB / WEAR / eICU | `#0072B2` / `#E69F00` / `#009E73` | | ○ / □ / △ |

Corpus names in all figures: **VitalDB (clinical)**, **WEAR (wearable)**,
**eICU (external)**. Do not alternate with "first/second corpus".

---

## Overview

| # | Short title | Type | Width | Section | Replaces |
|---|---|---|---|---|---|
| 1 | Accounting-aware system overview | Diagram | double | Method §III-A | fig1_architecture |
| 2 | Where the privacy unit is fixed | Diagram, 2 panels | single | Method §III-D | fig3 + fig5 |
| 3 | Records-per-individual law, two corpora | Line + forecast band | double | Results §V-B | new (headline) |
| 4 | Which arm moves | Slope chart, 2 panels | single | Results §V-B | new |
| 5 | Initialization vs privatized subset | Decomposition bars | double | Results §V-B | fig8_epsilon |
| 6 | When fusion pays | Bubble map | single | Results §V-C | new |
| 7 | Fusion-balance titration | 3 panels | double | Results §V-C | new |
| 8 | Clipping normalisation test | 3 panels | double | Results §V-B | new |
| 9 | System cost per deployment | 3 panels | double | Results §V-A | fig7_energy |
| 10 | Component ablation + audit | 2 panels | double | Results §V-D/E | new (`fig4_lira` kept in Method) |

Ten figures for a ~24-page two-column paper is at the upper end of what TII and
IoT-J accept. If the editor asks for fewer, cut 4 (merge into 3) and 10b
(Table IV already carries it).

---

## Fig. 1 — Accounting-aware system overview

**Claim it carries.** The three tiers, and *where each privacy cost is charged*.
The current architecture figure shows boxes; this one shows the ledger.

**Size.** Double column, 7.16 × 3.0 in. Vector diagram, not a plot.
*As built:* drawn in matplotlib (`fig01_overview.py`), so the ledger values,
τ_e and the sparsity ratio are read from files rather than typed in. Edge
boxes are drawn from `n_edges` in the partition metadata.

**Layout, left to right.**
1. **Client tier** (left third). Three stacked hospital cards labelled
   `Client 1 … K`. Inside one card, expanded: patient icons → windows
   `W_p` → *frozen* encoders (grey hatched boxes, lock icon) → *fusion head*
   (vermilion box) → "group by patient → clip C → +N(0,σ²C²)" chip.
2. **Edge tier** (middle). Two edge servers, each with a loop arrow labelled
   `τ_e = 5 edge rounds`. Client→edge arrows thin and frequent (WLAN).
3. **Cloud tier** (right). One cloud; edge→cloud arrow thick, single
   (point-to-point backhaul), labelled `once per cloud round`.
4. **Privacy ledger** strip along the bottom, full width, like a receipt:
   `ε_train = 0.7704` (under the client tier; file value 0.770429) `+ ε_conf = 0.2000` (under the
   conformal step at the cloud) `= ε_total = 0.970 ≤ 1`. The calibration
   quantile path drawn as a dashed purple arrow client→edge→cloud.
5. **Boundary**: a dashed vermilion rectangle around each client labelled
   "nothing crosses except the compressed, privatized head update".
6. Uplink payload annotation on the client→edge arrow:
   `top-20 % + 8-bit, error feedback`.

**Data.** ε values: `results/phase6/vitaldb/privacy_total_vitaldb.json`.
τ_e, K, edges: `data/processed/partitions/vitaldb/partition_meta.json`.

**Caption draft.** *Architecture of PP-HFM and its privacy accounting. Clients
hold patient-grouped multimodal records and train only the fusion head under
patient-level DP; edges aggregate τ_e = 5 rounds per cloud round. The ledger
(bottom) shows that the conformal calibration release is charged to the same
budget as training, giving the reported composed ε = 0.970.*

**Pitfalls.** Do not draw the encoders as trainable. Do not draw raw data
leaving a client. Keep icons monochrome line art.

---

## Fig. 2 — Where the privacy unit is fixed

**Claim.** Clipping each window bounds a window; summing a patient's windows
*before* clipping bounds the patient. And it costs nothing in budget, only in
geometry.

**Size.** Single column, 3.5 × 3.4 in, two stacked panels.

**(a) Vector diagram, "per-record" vs "per-individual".** Two rows.
- Top row (blue, record-level): a patient with k_p = 8 window-gradient arrows,
  each clipped to a circle of radius C; their sum drawn as a long arrow of
  length up to `8C`. Label: `sensitivity = k_p · C`.
- Bottom row (vermilion, individual-level): the same 8 arrows summed first into
  one arrow, then clipped to radius C. Label: `sensitivity = C`.
- Right margin: the group-privacy conversion as a one-line callout:
  `ε = 1 → ε ≈ 8, δ ≈ 9·10⁻²` (record budget converted at k̄ = 8).

**(b) Plot, "how often the bound binds".** x = records per individual (bins
1–4, 5–12, 13–24, 25–48, 49+); y = fraction of individuals whose summed
gradient is clipped [0–0.6]. Vermilion bars; above each bar write `n` patients
(27, 125, 1,937, 605, 229). Values 0.148, 0.216, 0.384, 0.436, 0.502.
Annotate `Spearman ρ = 0.138, p = 6·10⁻¹⁴`.

**Data.** (b): `document/01_planning/PREREGISTRATION_ND_CLIPNORM.md` §6 table
(N-A1 probe on eICU, 2,923 per-patient gradients, C = 1), produced by
`SIMULATORS/scripts/probe_clip_saturation.py`.
*As built:* the probe never wrote its per-bin numbers to a file. The bins
were transcribed from the frozen preregistration table into
`paper/figures/data/fig02_clip_bins.csv`, which has comments giving the
source. The probe was not re-run because it would have run out of memory
alongside the eICU training job (15 GB RAM). To replace the transcription with
raw output, re-run the probe on an idle machine and write the CSV directly.

**Caption draft.** *(a) Clipping per window bounds the influence of a window;
summing a patient's windows before clipping bounds the patient. (b) On eICU,
the fraction of individuals clipped rises with the number of records they
contribute (C = 1; bar labels give individuals per bin).*

---

## Fig. 3 — The records-per-individual law, forecast vs measurement (HEADLINE)

**Claim.** The cost of individual-level DP grows with records per individual
and saturates; the shape transfers to an external corpus, the magnitude does
not; the k = 1 control holds on both.

**Size.** Double column, 7.16 × 2.6 in, **two panels side by side, shared y**.

**(a) VitalDB (clinical).** x = k ∈ {1, 2, 4, 8}, log₂ axis, ticks at data
points. y = AUPRC gap (record − individual) [−0.08 … 0.12].
- Per-seed gaps as small open circles (jitter ±0.05 in log₂ k).
- Mean ± Student-t 95 % as filled vermilion circles with caps.
- Fitted curve `gap(k) = A(1 − e^{−b(k−1)})` as a black line, with
  A = 0.0878 and b = 0.8827 read from the frozen forecast in
  `PREREGISTRATION_EICU.md`. Do not refit it (see open item 4).
- Shade y ∈ [−0.020, +0.020] at k = 1 only, as a grey "control tolerance"
  box; label `k = 1 control`.

**(b) eICU (external).** Same axes; x ∈ {1, 2, 4, 8, 16}.
- Same per-seed / mean encoding.
- The *frozen forecast* curve (same A, b) as a **dashed** black line with a
  ±0.030 grey band ("pre-registered acceptance band").
- Bracket between k = 8 and k = 16 annotated `Δ = −0.0030 [−0.032, +0.026]`
  ("saturation, as registered").
- Grey hatched region at k = 32 labelled `untested (20 % of individuals reach
  k = 32)`.

**Data.** `results/phase5/k_scaling/vitaldb/k_scaling_vitaldb.csv` and
`results/phase5/k_scaling/eicu/k_scaling_eicu.csv` (columns
`k, seed, arm, auprc`). Gap = `auprc[arm=sample] − auprc[arm=patient]` paired
by `(k, seed)`. Means in paper Tables `tab:kscaling` and `tab:kscaling_eicu`.

**Caption draft.** *Cost of the individual-level guarantee as a function of
records per individual k (AUPRC, record arm minus individual arm, paired by
seed). Open circles: seeds; filled: mean ± 95 % Student-t interval (n = 3).
(a) VitalDB with the fitted law. (b) eICU against the law frozen before the
corpus was built: the ordering and saturation transfer, the magnitude is about
one sixth. At k = 1 both corpora pass the control.*

**Pitfalls.** Same y-limits in both panels, or the "one sixth" is invisible.
Don't join seed points with lines.

---

## Fig. 4 — Which arm moves

**Claim.** The gap widens because the record arm *improves* with more records,
not because the individual arm degrades.

**Size.** Single column, 3.5 × 2.4 in, two panels side by side.

**(a) VitalDB, (b) eICU.** Slope chart: x = k (categorical), y = AUPRC
(own scale per panel, but the same *range span* of 0.12 so slopes are
comparable). Two lines per panel: record arm (blue ■ dashed) and individual
arm (vermilion ● solid), mean ± 95 % CI. Shade the individual arm's min–max
band lightly (VitalDB [0.4967, 0.5176]; eICU [0.2185, 0.2258]).

**Data.** Same CSVs as Fig. 3, aggregated by `(k, arm)`.

**Caption draft.** *Average precision of each arm against k. The individual
arm is flat on both corpora (shaded band: its range); the widening gap of
Fig. 3 is the record arm improving.*

---

## Fig. 5 — Initialization, not the privatized subset

**Claim.** Under a tight budget almost all of the advantage of the recipe comes
from pretrained initialization; privatizing 3.3× fewer parameters adds ~0.

**Size.** Double column, 7.16 × 2.5 in, two panels: (a) VitalDB, (b) WEAR.

**Type.** Grouped "decomposition" bars, one group per ε ∈ {0.5, 1, 2, 4, 8, ∞}
(x categorical, ∞ last). Within each group, two adjacent bars:
- green ▲ bar: **initialization step** B4→B7 (ΔAUROC),
- vermilion bar: **subset step** B7→B6 (ΔAUROC) with its Student-t 95 % error
  bar.
y = ΔAUROC [−0.02 … 0.40], same scale in both panels. Thin zero line.
Overlay on a secondary axis *only if needed*: none — keep it single-axis.

**Data.** `results/phase5/epsilon_sweep/{vitaldb,wear}/epsilon_sweep.csv`,
columns `epsilon, recipe, seed, macro_auc`. `recipe`: `full` = B4,
`full_pre` = B7, `head` = B6. Steps paired by seed. Values match
`tab:recipe` (e.g. VitalDB ε = 0.5: +0.1447 and +0.0030 ± 0.0204).

**Caption draft.** *Decomposition of the recipe's advantage across the privacy
budget (macro AUROC, n = 3 seeds). Green: changing only the initialization
(full model, random → pretrained). Vermilion: changing only the privatized
subset (full model → head only, pretrained), mean ± 95 % CI. The subset step is
indistinguishable from zero at every ε although it privatizes 3.3× fewer
parameters.*

**Pitfalls.** Don't plot absolute AUROC curves (that is the old figure).
Write "ε = ∞ (no DP)" on the axis.

---

## Fig. 6 — When fusion pays: headroom × balance

**Claim.** Headroom alone does not explain the fusion results; the gain
appears only where the two streams are comparable *and* there is headroom.

**Size.** Single column, 3.5 × 3.0 in.

**Type.** Bubble map. x = modality imbalance |AUROC_A − AUROC_B| (log x,
0.001–0.3). y = headroom 1 − max(AUROC_A, AUROC_B) (linear, 0–0.35).
Bubble area ∝ fusion gain (AUROC fused − best single); negative gain drawn as
hollow bubble. Colour = corpus. Label every bubble.

| Point | A | B | best | imbalance | headroom | gain | source |
|---|---|---|---|---|---|---|---|
| VitalDB | 0.8283 | 0.7680 | 0.8283 | 0.0603 | 0.1717 | +0.0370 | `phase5/ablation_vitaldb.json` |
| WEAR | 0.9976 | 0.9957 | 0.9976 | 0.0019 | 0.0024 | +0.0004 | `phase5/ablation_wear.json` |
| eICU natural | 0.6748 | 0.8212 | 0.8212 | 0.1464 | 0.1788 | +0.0037 | `phase5/ablation_eicu.json` |
| eICU matched ctrl | 0.7068 | 0.8221 | 0.8221 | 0.1153 | 0.1779 | +0.0020 | `phase5/ablation_eicu_matched.json` |
| eICU APACHE zeroed | 0.6973 | 0.5947 | 0.6973 | 0.1026 | 0.3027 | −0.0062 | `phase5/ablation_eicu_noapache.json` |
| eICU titrated (α = 0.4) | 0.6992 | 0.6845 | 0.6992 | 0.0147 | 0.3008 | **+0.0291** | `phase5/fusbal_test_n0.4.json` |

Recompute every row from the JSONs (`runs.{a,b,both}[].auroc`, 5 seeds).
Draw a faint arrow eICU matched → zeroed → titrated ("titration path").

**Caption draft.** *Fusion gain (bubble area) against modality imbalance and
headroom, five seeds per point. WEAR is balanced but at ceiling; eICU has
headroom but is imbalanced; the gain appears when eICU's streams are titrated
to parity. Hollow: negative gain.*

---

## Fig. 7 — The fusion-balance titration (F-A1)

**Claim.** A calibrated, information-destroying lever brings the streams to
parity, and at parity fusion gains +0.029 AUROC on every seed.

**Size.** Double column, 7.16 × 2.4 in, three panels.

**(a) Calibration of the lever.** x = noise-mix α ∈ {0.2, 0.4, 0.6, 0.8, 1.0};
y = AUROC of arm B alone. Points: 2 seeds each (0.625, 0.685, 0.741, 0.786;
α = 1.0 intact 0.822 from the matched control). Horizontal dashed line at arm
A = 0.707; mark the chosen α* = 0.4 with a vertical line. Inset text:
`calibration uses arm B only — never the fused model`.

**(b) Three arms at parity.** Dot plot, 5 seeds per arm, mean ± 95 % CI: vitals
(A) 0.6992, admission (B) 0.6845, fused 0.7282. Same panel, a lighter second
column of the matched control (0.7068, 0.8221, 0.8241) for contrast.

**(c) Seed-paired gain.** One line per seed from best single (A) to fused,
5 lines, all rising; right-side annotation `+0.0291 ± 0.0211, 5/5 seeds,
paired t p = 0.019`. Horizontal dashed reference at the registered threshold
+0.015 drawn as a short bracket.

**Data.** `results/phase5/fusbal_calib_n{0.20,0.40,0.60,0.80}.json`
(`runs.b[].auroc`), `results/phase5/fusbal_test_n0.4.json`
(`runs.{a,b,both}[]` with `seed`), `results/phase5/ablation_eicu_matched.json`.

**Caption draft.** *Fusion-balance test on eICU. (a) Mixing the dominant
admission feature with fixed-seed noise weakens arm B monotonically; α* = 0.4
is the level nearest arm A. (b) At parity the fused model exceeds both single
modalities (n = 5, mean ± 95 % CI); grey: unbalanced control. (c) The gain is
positive on all five seeds.*

**Pitfalls.** State AUPRC (+0.0121, unresolved) in the caption, not the plot.

---

## Fig. 8 — Is the cost a clipping artefact? (N-A2)

**Claim.** Normalising the clip by record count *does* change clipping
(intervention is live) but recovers *no* utility; the registered effect is
excluded.

**Size.** Double column, 7.16 × 2.4 in, three panels.

**(a) Clip saturation per round.** x = global round 1–10; y = fraction of
individuals clipped [0–1]. Three rules: none (vermilion solid), √k (purple
dash-dot), k (blue dashed). Thin lines per seed, thick line = mean of 3.
Annotate "rules diverge from round 3".

**(b) Utility under each rule.** Dot plot, AUPRC per seed (3 dots) + mean,
for none 0.2266, √k 0.2242, k 0.2265. y range 0.20–0.25.

**(c) Equivalence-style plot.** Horizontal axis = paired AUPRC difference
(k − none). Point −0.0001 with two-sided 95 % CI ±0.0087 and the **one-sided
95 % upper bound +0.0058** as a bold tick. Vertical dashed line at the
registered threshold **+0.010**, shaded region to its right labelled
`recovery predicted by N-D`. The UB tick sitting left of the line is the
result.

**Data.** `results/phase5/nd_clipnorm/eicu/hist_natural_seed{42,43,44}_{none,sqrt_k,k}.csv`
(columns `global_round, clip_saturation`), and
`results/phase5/nd_clipnorm/eicu/nd_clipnorm_eicu_natural.json` (`rows[]` with
`seed, mode, auprc`).

**Caption draft.** *Normalised clipping on eICU's natural partition (n = 3
seeds, ε = 0.8). (a) Normalising by record count k lowers the fraction of
individuals clipped from round 3 onward. (b–c) It does not change average
precision: the one-sided 95 % upper bound on the gain (+0.0058) lies below the
registered threshold (+0.010).*

**Pitfalls.** Mention in caption: on seed 42 every rule selected round 1.

---

## Fig. 9 — System cost per deployment

**Claim.** The hierarchy cuts uplink by > 90 % and energy by > 70 %, and the
saving appears only when the device tier's work shrinks — the edge tier alone
is a net energy *cost*.

**Size.** Double column, 7.16 × 2.6 in, three panels, columns = deployments
inside each panel (VitalDB, WEAR, eICU*).

*As built (`fig09_system_cost.py`).* Three colours are used throughout: grey
for Centralized, blue for Hierarchy only, vermilion for PP-HFM. A deployment
is drawn in a panel only if its result file exists, so eICU fills in without
any edit.

**(a) Uplink per cloud round [MB], log y.** Three bars per deployment:
Centralized, Hierarchy only (full model, compressed), and PP-HFM (head only,
compressed). The proposed bar carries its reduction: −90.8 % VitalDB,
−96.1 % WEAR, −92.3 % eICU. *Changed from the original spec:* the bars are
the **measured** compressor payload, the same source as O1 in the text. The
earlier plan used CloudSim's `uplink_MB` column. Those are modelled values,
and they give a different reduction (−77 % on VitalDB), which would
contradict the text. The measured file has no separate "Flat FL + DP" arm:
a flat dense upload is identical to the centralized payload. So the panel
has 3 bars, not 4.

**(b) Round latency decomposition [ms].** Stacked horizontal bars,
Centralized vs PP-HFM for each deployment: communication (solid) plus
compute (light). Values are means over the packet-level rounds:
- VitalDB: 90.5 → 75.2 ms (communication 23.6 → 16.5)
- WEAR: 104.5 → 81.8 ms (communication 37.6 → 23.2)
- eICU: 261.4 → 174.1 ms (communication 194.6 → 115.5)

The point: compute dominates and is unchanged.

**(c) Energy per round by tier.** Stacked bars (device, edge, cloud; shown by
opacity) for Centralized, Hierarchy only and PP-HFM. *Changed from the
original spec:* the y axis is **% of the centralized total**, and the absolute
joules are printed above each bar. Without that, eICU (26 186 J) would flatten
the other two deployments. Values:
- VitalDB: 1266 → 1344 (hierarchy alone, +6 %) → 351 J
- WEAR: 3086 → 3164 → 715 J
- eICU: 26 186 → 26 264 → 5335 J

**Data.**
- (a): `results/phase5/uplink_measured_<ds>.json`, using the keys
  `centralized_mb_per_round`, `system.full_model.mb_per_round`,
  `system.head_only.{mb_per_round,reduction_pct}`.
- (b): `results/ns3/ns3_results_<ds>.csv` (`scenario, L_comm_ms, L_total_ms`,
  averaged over rounds). Do **not** use `ns3_phase5_<ds>.csv` or
  `results/phase5/ns3_*.csv`: those are the analytical per-round model, not
  packet-level.
- (c): `results/cloudsim/cloudsim_results_<ds>.csv` (`iot_energy_J,
  edge_energy_J, cloud_energy_J, total_energy_J`, averaged per scenario).

**Caption (as placed).** *System cost per deployment. (a) Uplink per cloud
round, measured from the deployed compressor, for centralized training, the
hierarchy with the full model, and the proposed configuration. (b) End-to-end
round latency from packet-level simulation, split into communication (solid)
and computation (light); the hierarchy shortens link time while computation is
unchanged. (c) Energy per round by tier (device, edge, cloud) as a share of
centralized training, with absolute values in joules. The hierarchy alone adds
edge energy without reducing device energy; only the proposed configuration
reduces the energy of the constrained tier.*

---

## Fig. 10 — Component necessity and the leakage audit

**Claim.** Only the privacy mechanism changes accuracy (and removing it hurts);
compression is free and buys an 8× payload cut; the patient-level arm leaks
little, while the attack provably works on the control.

**Size.** Double column, 7.16 × 2.6 in, two panels.

**(a) Ablation forest plot with payload.** Rows: −C1 hierarchy, −C2 privacy,
−C3 sparsification, −C4 quantization, +C6 ASWA. Left: ΔAUROC vs full system,
mean ± 95 % CI (n = 3), vertical zero line; −C2 in bold vermilion (only
interval excluding zero). Right, aligned on the same rows: horizontal bar of
total uplink [MB, log x] (full = 252; −C3 = 1260; −C4 = 403; −C1 = 50, marked
"not comparable — different schedule").

**(b) Membership-inference audit.** Dot plot, attack AUC with 95 % CI per
configuration (control non-private, record-level DP, patient-level DP),
two markers per configuration: loss threshold (○) and likelihood ratio (●).
Chance line at 0.5. Secondary small strip below: TPR at 1 % FPR (0.029 control,
0.010 patient-level). Annotate on the control: "attack verified: 0.623".

**Data.** (a): `results/phase6/vitaldb/ablation_A{0..6}_seed{42,43,44}*.json`
/ `_test.json` (AUROC) and the uplink totals in the `uplink_bytes` column of
`ablation_A*_seed*.csv`; values match `tab:ablation`.
(b): `results/phase5/lira/vitaldb/lira_vitaldb_{head_nodp,sample,patient}.csv`
(columns `arm, attack, seed, attack_auc, tpr_at_1pct_fpr`); use the
`head_nodp` file, not the `_1round_` archive.

**Caption draft.** *(a) Component ablation on VitalDB (ΔAUROC vs the full
system, n = 3, 95 % CI) beside each arm's total uplink. Only removing DP
resolves, and it lowers AUROC. (b) Patient-level membership inference (16
shadow models, 600 members / 600 non-members). The control shows the attack
detects leakage where it exists; both DP arms are near chance.*

---

## Checklist before submitting the figures

Checked on 2026-10-21.

- [x] All 10 exported as vector PDF with fonts embedded: `pdffonts` shows
      `emb yes` for every font in every file. The "Mismatch between font type"
      line it prints is a harmless poppler warning about TrueType fonts in
      OpenType wrappers.
- [x] Widths are 3.5 in or 7.16 in, with text 7–9 pt at final size. The
      tight-cropped PDFs are 3.27–3.31 in or 6.88–7.39 in wide and are scaled
      to the column by 0.97–1.07×.
- [ ] Printed in greyscale and still readable: not yet checked on paper.
      Colour is paired with marker or line style throughout, and Fig. 9 also
      uses opacity for the tiers.
- [x] Every number in a figure equals the number in the text and tables.
- [x] Every interval says n and "Student-t 95 %" in the caption.
- [x] Every figure is cited in the text, and the labels are the ones in the
      status table. `fig:patientdp` no longer exists; nothing references it.
      The printed order differs from the spec order (open item 2).
- [x] Every figure is drawn from the listed result files, with no re-typed
      numbers. The one exception is the Fig. 2(b) CSV, which is transcribed
      and documented.
- [x] One plotting script per figure, next to the PDF.
