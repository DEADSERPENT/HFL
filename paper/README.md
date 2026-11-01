# PP-HFM: full-length manuscript

Full-length working version (31 pages, IEEEtran journal class) of *Patient-Level
Differential Privacy in Hierarchical Federated Learning for Multimodal Medical
IoT*. The condensed submission version is `../PLDP/`. The two are kept
consistent: identical abstracts and the same results, with `PLDP/` carrying
fewer derivations and supporting analyses.

## Build

```bash
bash paper/build_paper.sh        # -> paper/paper_build.pdf
```

The script runs the full LaTeX and bibliography sequence on `main.tex`. The
files under `sections/` are fragments and do not compile on their own.

## Structure

| Section | File |
|---|---|
| Abstract, index terms | `sections/abstract.tex` |
| I Introduction (gaps, contributions) | `sections/introduction.tex` |
| II Related work | `sections/related_work.tex` |
| III Methodology (system, threat model, mechanism, accounting, Theorem 1, deployment) | `sections/method.tex` |
| IV Experimental setup | `sections/experiments.tex` |
| V Results; the external scaling test and the matched-budget control are included from separate files | `sections/results.tex`, `sections/results_kscaling_eicu.tex`, `sections/results_a2_budget.tex` |
| VI Discussion, limitations | `sections/discussion.tex` |
| VII Conclusion | `sections/conclusion.tex` |
| Data availability, acknowledgment | `sections/backmatter.tex` |

## Figures

`figures/` holds one generator per figure (`fig00_workflow.py` … `fig10_ablation_mia.py`,
`make_method_figures.py`). Each reads only `SIMULATORS/results/` and writes PDF
and PNG next to itself. Copy regenerated PDFs to `../PLDP/figures/`. All
figures used by either manuscript regenerate pixel-identically from the
current results. Five older method figures that neither manuscript uses
(`fig1_architecture`, `fig3_sensitivity`, `fig5_patientdp`, `fig7_energy`,
`fig8_epsilon`) are stale relative to the current results.

## Evidence rules for editing

- Every number in the text is read from a file under `SIMULATORS/results/`. Source comments in the `.tex` files name it. `SIMULATORS/results/RESULTS_FINAL.md` is the index.
- VitalDB results are labeled person-level or case-level wherever they appear.
- Objective verdicts follow the prespecified interval rule. The eICU utility objective is inconclusive with training-fitted constants and missed end to end. eICU update delivery fails at two edges.
- Simulated (ns-3), modeled (CloudSim Plus) and measured quantities are named as such.

## Known source-level issues

- `sections/results_a2_budget.tex` names `results/phase5/k_scaling/a2_matched_budget.json` as its source and still carries a "PENDING C3" comment. The text already uses the post-fix eICU values. The JSON file predates the post-fix eICU rerun, and its eICU column must be regenerated (`scripts/analyze_k_matched.py`) for the section to be traceable to its source. The VitalDB columns are current.

## Open decisions (authors)

- Author block: a grid under the title (chosen by the authors) rather than IEEE `\thanks` footnotes. Confirm against the target journal's instructions.
- Corresponding author, biographies and photographs (at acceptance).
- AI-use disclosure in the acknowledgment, as IEEE policy requires.
- Deposit rights for any public copy of the manuscript.
