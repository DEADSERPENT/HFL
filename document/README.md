# `document/` — index

All project documentation. Reorganised 2026-09-05; nothing was deleted, and
superseded items sit in `archive/` subfolders rather than being removed.

| Folder | Contents | Status |
|---|---|---|
| `01_planning/` | The live eICU work | **active** |
| `02_phase_reports/` | Phase 1–6 completion records | reference |
| `03_research_dossier/` | The full research narrative (3 docs × 3 formats) | **authoritative** |
| `04_experiment_results/` | Measured results, all experiments | **authoritative** |
| `05_reference/` | External material — PhysioNet pages, literature, guides | reference |
| `06_project_output/` | Overall report, PHANTOM-FL writeup, IP notes | reference |

---

## 01_planning — read these first

| File | What it is |
|---|---|
| `plan.md` | **The current plan.** Rev 3, eICU only. Execution order E0–E11, what each step gates, how each open gap closes. |
| `PREREGISTRATION_EICU.md` | **Frozen numeric forecast**, fitted on VitalDB alone: `gap(k) = 0.0878·(1−exp(−0.883(k−1)))`. **Must be committed before the first build run** — its entire value is that it predates the data. |
| `EICU_INTEGRATION_SPEC.md` | Why eICU and not MIMIC / HiRID / PTB-XL; what the preprocessing must guarantee. |

## 03_research_dossier — the authoritative narrative

| Document | Use it for |
|---|---|
| `HFL_Research_Dossier` | What the research is, what succeeded, what failed, objective-by-objective status, open issues. §9–§10 (the k-scaling law), §26–§31 (the validity gap and the path forward). |
| `HFL_Dossier_Part2_Technical` | Algorithms and why; why the MIA hypothesis failed (§2); **why we want eICU (§9)**. |
| `HFL_Dossier_Part3_Experiments` | Complete experiment log E1–E24, plus what has not been run. |

Each exists as `.docx` (editable source), `.html` (machine-readable — this is
what gets parsed) and `.pdf` (shareable). All three are kept deliberately.

## 04_experiment_results

`HFL_Experiment_Results_Complete.{docx,html,pdf}` — 20 sections covering every
measured result, including §18 negative results and §19 experiments not yet run.

`archive/Research Experiment Results.{docx,pdf}` — the earlier export from the
same day (15:47 against 22:41), superseded by the above. Kept because it is
untracked by git and therefore not recoverable if deleted.

## 05_reference

- `physionet/` — the eICU-CRD and BRSET project pages. Public documentation,
  not restricted data. Column names and schema descriptions only.
- `literature/` — problem statement, objectives, literature review, methodology.
  `traceability.py` maps O1–O4 back to these.
- `guides/` — dataset, model design and simulator integration notes.

---

## Where everything else lives

| | |
|---|---|
| Raw PhysioNet data | `SIMULATORS/data/raw/` — gitignored **and** deny-listed. Never committed. |
| Code | `SIMULATORS/` |
| Paper source | `paper/` (**not** `latex/` — that is a different paper) |
| Runbook / roadmap | `docs/` |
