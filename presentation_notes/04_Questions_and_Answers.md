# Anticipated Questions and Model Answers

Grouped by topic. Answers are short enough to say in 30–60 seconds. Numbers match
`03_Key_Numbers.md`.

---

## A. Concept and Motivation

**Q1. What exactly is new here? User-level DP and hierarchical FL already exist.**
Correct — none of the building blocks is new on its own. The contribution is (1) composing
patient-level DP *inside a client–edge–cloud hierarchy* with a proof that covers every tier,
including the edge; (2) per-client noise calibration that is valid by parallel composition;
(3) measuring the cost of the unit and showing it follows A(1 − 1/k); (4) showing that pretrained
initialization, not the reduced subset, drives robustness; and (5) a patient-level audit with a
positive control. To our knowledge no prior system groups an individual's records before clipping
across a hierarchy.

**Q2. Why not simply use record-level DP and convert with group privacy?**
Because at our group sizes group privacy turns ε = 1 into roughly ε ≈ 8 with δ ≈ 0.09. That is not
a meaningful clinical guarantee. Fixing the unit at the point of clipping gives ε = 0.9 per patient
directly.

**Q3. Why is the patient the right unit, not the hospital (client-level DP)?**
The legal and ethical question in medicine is about individuals. Client-level DP protects a whole
hospital and needs many hospitals to be affordable; record-level protects too little. The patient is
the unit that matches the question "was this person in the training data?".

**Q4. Why hierarchical FL at all?**
Most aggregation happens near the data, so the wide-area link is used once every several rounds.
That is why uplink falls 90.8–96.1 % and energy 72.3–79.6 %. The ablation shows the hierarchy costs
only about 0.005 AUROC.

---

## B. Mechanism and Proof

**Q5. Explain the mechanism in one sentence.**
At each step each client samples patients, sums all of each sampled patient's gradients, clips the
sum to norm C, adds Gaussian noise once, and divides by the expected batch size.

**Q6. Why divide by the expected batch size and not the actual one?**
The actual number of sampled patients depends on whether a particular patient is present. Dividing by
it would reveal information the accountant does not cover, especially at small hospitals. Dividing by
the public expected size keeps the operation post-processing. We found this issue while writing the
proof and re-ran every patient-level experiment after fixing it.

**Q7. Why different noise per client — doesn't that leak client sizes?**
The multiplier σ_k is computed only from the *declared, public* client size and step count, so it
releases nothing beyond those declared sizes. Validity comes from parallel composition: each patient
is held by one client, so their guarantee is that of their client. Using one worst-case σ would
impose 29.34 on every eICU hospital instead of a median of 13.76.

**Q8. What are the assumptions of the theorem, and do they hold?**
A1: each patient at one client and disjoint from validation. A2: architecture, encoders (pretrained on
a disjoint pool), hyperparameters, edge map, standardization constants and declared sizes are public
and fixed. A3: no cross-record operations such as batch norm. They hold fully for the eICU end-to-end
configuration (disjoint encoders, pool-fitted constants, one hospital per person). For VitalDB and
WEAR the oracle encoders violate A2, so those results are comparisons of the private head, which the
paper states explicitly in a scope table.

**Q9. Is the guarantee end to end?**
Only for the eICU configuration with disjoint encoders and pool-fitted standardization. For the
headline runs it covers the training transcript; standardization constants fitted on training data
are an unprotected release, and we measured its size (removing one person moves any mean by at most
0.0017 SD).

**Q10. How do you know the ε is correct?**
The budget was recomputed independently for every client of every run with the same sampling rates,
step counts, multipliers and δ: the PLD accountant gives [0.880, 0.900] and the looser Rényi
accountant 0.974. Seven of 17 regression checks cover the accounting.

**Q11. What about the 2.9 % of eICU patients at several hospitals?**
For them A1 fails on the source partition, and their per-hospital budgets compose to at most 1.32,
1.64 or 1.92. For the headline privacy-cost runs we built a partition that moves each such person,
with all their records, to their main hospital, so every person has ε = 0.9. The cost of privacy was
unchanged within resolution between the two partitions.

**Q12. Is the validation set protected?**
No. It selects the reported checkpoint without noise, which is conventional in DP-SGD literature. It
is listed in the privacy ledger as unprotected and is disjoint from the training patients.

---

## C. Results

**Q13. Why is the private model better than the non-private one on VitalDB?**
The result (−1.18 points, p = 0.002) is consistent with clipping and noise regularizing a compact head
over frozen features: in the ablation, non-private seeds peak in the first round and then degrade,
while private seeds peak at rounds 6–9. The experiment does not isolate this mechanism, so we say
"consistent with".

**Q14. eICU misses the 2-point target. Isn't that a failure?**
It is reported as it is: 3.10 [1.55, 4.65] is inconclusive under the pre-specified interval criterion
and 3.88 end to end is a miss. The cause is identified — the smallest hospitals sample every patient
every step and need the largest noise. A minimum cohort size or cross-client sampling at the edge are
the remedies, listed as future work. Non-private HED-FL matches our non-private reference, so this gap
is the price of the guarantee, not a weakness of the system.

**Q15. Explain the k-law in simple terms.**
If each person contributes k records, record-level training "sees" P·k units and patient-level only P.
So the patient-level model cannot exploit additional records per person, while the record-level model
can. The gap therefore grows like A(1 − 1/k): zero at k = 1 and saturating. On VitalDB it fits with
one parameter (A = 0.1015) and predicted k = 8 out of sample.

**Q16. Why did the eICU magnitude not match the forecast?**
The shape and saturation transferred but the magnitude was about one ninth. Plausible reasons are a
lower attainable precision (AUPRC ≈ 0.22 at 4.2 % prevalence versus 0.5) and differences in client
sizes and features. We tested and excluded the budget and the clipping rule. Separating the rest needs
a third corpus. Importantly, the forecast was registered before the corpus was built, so this is an
honest external test.

**Q17. Why AUPRC for the k-law and AUROC elsewhere?**
AUROC is the pre-declared primary measure for the privacy-cost comparisons. For the k-law, AUPRC was
fixed in advance as the primary measure, because the tasks are imbalanced and the registered forecast
was stated in AUPRC; AUROC moves in the same direction (+0.0026 to +0.0159) but is unresolved at
three seeds. Both are reported.

**Q18. Why pretrained initialization rather than head-only training?**
We separated them with three models. Changing only the initialization is worth up to +0.199 AUROC at
ε = 0.5 and grows as the budget tightens; changing only the privatized subset is indistinguishable
from zero. If dimensionality were the reason, the full pretrained model would trail the head-only
model most at small ε — it does not. Head-only training is still used because it reduces communication.

**Q19. Why did fusion not help on eICU?**
The admission stream (0.8221 AUROC) dominates the vital signs (0.7068). In a pre-specified test,
weakening the dominant stream to parity produced a +0.0291 fusion gain on all five seeds. So balance is
sufficient for a gain; it is not shown to be necessary.

**Q20. Delivery on eICU is 97.83 %. Why?**
187 clients share two edges' wireless medium, causing contention. Centralized training is even worse
(95.11 %). Increasing edges to 8 meets the target in every round; 16 edges give 99.94 %.

---

## D. Audit and Baselines

**Q21. What is LiRA and why use it?**
The likelihood-ratio attack trains shadow models with and without each patient and models the
patient's confidence under both, giving a per-patient calibrated membership score. It is among the
strongest standard membership-inference attacks. We adapted it to the patient unit with 16 shadows.

**Q22. Why a positive control and a difficulty floor?**
A null result is meaningless unless the attack could have detected leakage, so we first show it
detects leakage in a non-private model (0.605). The difficulty floor removes the effect of members and
non-members simply differing in how hard they are. Patient-level training sits at its floor (0.503 vs
0.508); record-level is above it (0.576 vs 0.511).

**Q23. The predicted attack AUC was 0.7 but you got 0.576. Comment?**
The direction is as predicted and resolved (p < 0.001), but the magnitude is smaller. We report it.
The audit bounds what these attacks achieve; it does not prove absence of leakage, and it cannot
resolve a 0.1 % false-positive rate with 16 shadows.

**Q24. Why is FL2DP leaking more than HED-FL, which has no noise?**
FL2DP builds its candidate set from the private gradient value, so its mechanism satisfies no finite
ε. Adding noise without a valid bound is not a weaker guarantee but no guarantee — and only an audit
reveals it.

**Q25. Are the baselines fair?**
Both were re-implemented from their papers and trained through the same trainer, splits, frozen
encoders, rounds and seeds. FL2DP was run on VitalDB only because its per-coordinate mechanism would
take about two GPU days per seed on eICU. This is listed as a limitation.

---

## E. System and Methodology

**Q26. Are the network and energy results real measurements?**
Uplink payload and inference latency are measured. Delivery and round latency are simulated at packet
level in ns-3 on every round; energy is modeled in CloudSim Plus per tier. Latency was timed on a
workstation CPU, not edge hardware. Confirming on physical hardware is future work.

**Q27. Why not 8-bit quantized inference?**
It was evaluated and rejected: it raised P95 latency from 2.30 ms to 17.34 ms on the CPU provider.

**Q28. Why only 3 or 5 seeds?**
Seed counts were fixed before each comparison and never increased after seeing results, to avoid
optional stopping. Five paired seeds resolve the main effects; three-seed grids estimate trends. We
state that resolving the eICU k-gaps would need about 25 seeds.

**Q29. How did you prevent data leakage?**
Splits by person (or case), never by window; only pre-operative variables in modality B; explicit
missingness indicators; normalization from training data or a disjoint pool; and no test case used
to pretrain encoders. VitalDB was rebuilt at person level after we found 55 of 940 test persons also
had a training case in the case-level split.

**Q30. What would you do next?**
Test a third corpus; sample patients across all clients of an edge so small hospitals are not alone;
clip around each person's mean gradient, which has rates that improve with k; extend the audit to
eICU; and validate on physical edge hardware.

---

## F. Quick One-Liners

- **Main result:** patient-level DP across all tiers at ε = 0.9 — free on VitalDB, ~3 pts on eICU.
- **Main science:** the cost of the unit follows A(1 − 1/k).
- **Main practical lesson:** pretrain first; the head-only trick is for bandwidth, not accuracy.
- **Main system result:** 90.8–96.1 % less uplink, 72.3–79.6 % less energy, ≤ 2.3 ms inference.
- **Main audit:** record-level leaks (0.576), patient-level at floor (0.503).
