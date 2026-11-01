# PP-HFM — standard IEEE journal manuscript

Condensed submission version of `../paper/` (the full-length working draft),
written to the IEEEtran `journal` class at 15–18 pages.

Build: `bash build_paper.sh` (output `../build/PLDP/main.pdf`, copy
`PLDP_build.pdf`), or upload this folder to Overleaf and compile
`main.tex` (pdflatex → bibtex → pdflatex ×2).

## Structure

| Section | File |
|---|---|
| Abstract (≤250 words), Index Terms | `sections/abstract.tex`, `main.tex` |
| I Introduction (contributions) | `sections/introduction.tex` |
| II Related Work (Table I comparison) | `sections/related.tex` |
| III System and Threat Model (notation, objectives) | `sections/model.tex` |
| IV PP-HFM: mechanism, calibration, aggregation, conformal, Theorem 1, Corollary 1, Proposition 1, audit | `sections/method.tex` |
| V Experimental Setup | `sections/setup.tex` |
| VI Results | `sections/results.tex` |
| VII Discussion (prior art, implications, limitations) | `sections/discussion.tex` |
| VIII Conclusion | `sections/conclusion.tex` |

Figures are copies of `../paper/figures/*.pdf`; regenerate there with the
`fig*.py` scripts and copy them here.

## Status (2026-11-01)

- **Values:** all values are final; no `\pend{}` markers remain (`\pend` is defined as a pass-through in `main.tex`).
- **Results:** the person-level VitalDB results, the prior-system comparison and the membership-inference audit are written in. Objective verdicts follow the prespecified interval rule: eICU utility is inconclusive with training-fitted constants and missed end to end; eICU update delivery fails at two edges.
- **Build:** 18 pages; no errors, undefined references or overfull boxes.
- **Consistency:** this version and `../paper/` are updated together and report the same results; their abstracts are identical.

## Scope (2026-10-27)

Conformal calibration is NOT a contribution: a per-client private threshold at
eps_conf = 0.1 fails coverage (reported as a negative result in Sec. VI-B).
The protected population is the training cohort at eps = 0.9. `../paper/`
keeps the full record, including the conformal component.

