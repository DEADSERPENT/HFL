Diagnostic (2026-11-02), NOT part of the prespecified analysis.
Question: is the k=1 control failure of the eps=0.8 VitalDB grid (+0.0398) caused by
the record arm having been run on Sep-21/22 code and reused, while the patient arm
was rerun on Oct-24/25 code?
Partitions and patient-arm artefacts are copies of k_scaling/vitaldb_eps080/k1_seed*;
only the record (sample) arm is retrained here, on the current code.

Relocated 2026-11-02 from results/phase5/k_scaling/_diag_k1_record_rerun_eps080/ to
results/phase5/diagnostics/k1_record_rerun_eps080/ so that k-law scripts globbing
k_scaling/*/k_scaling_*.csv do not pick it up (it broke klaw_theory_check.py).
run_metadata_*.json inside still record the original output path.
