# ⚠️ SUPERSEDED — do not cite as the proposed method

These sweeps characterise the **end-to-end DP-SGD recipe that collapses at ε=1**
(all 2.16 M parameters trained under σ=11.33). They predate the head-only
DP fine-tuning fix.

| ε | acc | AUC | σ |
|---|---|---|---|
| 0.1 | 0.213 | 0.554 | 45.0 |
| 1.0 | 0.219 | 0.610 | 5.43 |
| 5.0 | 0.229 | 0.636 | 1.51 |
| ∞ | 0.565 | 0.820 | — |

**Legitimate use:** the "without our fix" arm of the comparison — evidence that
naive fixed-σ DP-SGD fails at every budget in this regime.

**Illegitimate use:** quoting these as the proposed method's privacy–utility
curve. The proposed method reaches test AUC 0.8742 ± 0.0072 at ε=1
(see `../RESULTS.md` §2).

Also note these ran on the RULE-PAIRED healthcare data — see
`../../../data/processed/healthcare/README_LEGACY.md`.

Do not re-run. Superseded 2026-07-31.
