/**
 * Privacy content: mechanism description, membership-inference audit and
 * threat model. Only the patient-level VitalDB audit result is published;
 * other audit arms use different setups and are not ranked against it here.
 */

export type AuditRecord = {
  id: string;
  title: string;
  dataset: "VitalDB";
  attack: string;
  auc: number;
  interval: { lower: number; upper: number; method: string };
  floor: number;
  margin: number;
  evidenceStatus: "measured";
  interpretation: string[];
  caveat: string;
};

export const MIA_AUDIT: AuditRecord = {
  id: "mia-vitaldb-patient",
  title: "Patient-level DP, offline LiRA",
  dataset: "VitalDB",
  attack:
    "Offline likelihood-ratio membership-inference attack (LiRA) adapted to the patient unit, with 16 shadow models and per-patient calibration.",
  auc: 0.503,
  interval: { lower: 0.475, upper: 0.531, method: "95% interval over five target seeds" },
  floor: 0.508,
  margin: -0.005,
  evidenceStatus: "measured",
  interpretation: [
    "The attack AUC is close to the difficulty floor under the reported audit protocol.",
    "It does not establish zero leakage.",
    "It does not prove resistance to all attacks.",
    "Its meaning is limited by the evaluated attack, model, dataset, sampling and uncertainty.",
  ],
  caveat:
    "The difficulty floor is the AUC obtained by ranking patients by their statistic over shadow models that exclude them, without the target model: members and non-members can differ in intrinsic difficulty, so the floor, not 0.5, is the fair reference. A negative result is accepted only because the same procedure detects clearly elevated leakage on a positive control (non-private training of the same head over the same encoders). The audited models were trained at \u03B5 = 1.",
};

export const MECHANISM_STEPS = [
  {
    id: "group",
    title: "Group by patient",
    body: "Each client groups a patient's per-record gradients and sums them, so one patient contributes a single vector per step however many records they have.",
  },
  {
    id: "sample",
    title: "Poisson-sample patients",
    body: "At each step every patient is included independently with a fixed probability, for an expected 64 patients per step. The update is divided by the expected batch size, never the realised one, because the realised size depends on whether a given patient was drawn. A step with an empty sample still releases its noise.",
  },
  {
    id: "clip",
    title: "Clip each patient",
    body: "The sum of a patient's record gradients is clipped to norm C = 1, so a patient moves the update by at most C however many records they have; clipping each record instead would admit k\u00B7C for a patient with k records.",
  },
  {
    id: "noise",
    title: "Add calibrated Gaussian noise",
    body: "Each client sets its own noise multiplier from its own population size before training, so every patient receives the same budget. The multipliers range widely across hospitals; one worst-case value for all would have over-noised most clients.",
  },
  {
    id: "account",
    title: "Account every release",
    body: "A privacy-loss-distribution accountant composes all steps. Edge and cloud averaging use public weights and act on already-noised updates, so they are post-processing and add no cost.",
  },
] as const;

export const ACCOUNTING_EXPLANATION = {
  adjacency:
    "Two datasets are neighbours if they differ by all the records of one patient (person on VitalDB). On WEAR, where each client is one participant, they differ by one record.",
  guarantee:
    "For neighbouring datasets D and D′ and any set of outcomes S of the training transcript: Pr[M(D) ∈ S] ≤ e^ε · Pr[M(D′) ∈ S] + δ.",
  composition:
    "Reported total ε = training ε (all training steps, composed by the accountant) + conformal ε (one evaluated calibration release), at δ = 10⁻⁵.",
  parallel:
    "When each patient is held by exactly one client, clients act on disjoint individuals and their mechanisms compose in parallel: the budget is per patient, not summed across hospitals. On eICU this holds for 97.1% of training individuals; for the 2.9% with stays at two to four hospitals the hospitals' budgets compose, bounded by \u03B5 \u2264 1.42, 1.77 or 2.08 respectively.",
  doesNot: [
    "It does not cover the standardization constants or encoders when these are fitted on training data (true of the headline VitalDB, WEAR and eICU runs).",
    "It does not cover metadata, participation patterns, preprocessing, logs or deployment operations.",
    "The conformal calibration release was evaluated but is not part of the deployed system; its budget is still counted in the reported total.",
    "It is a bound under assumptions, not a measurement that leakage is small for every patient or every attack.",
  ],
};

export const THREAT_MODEL = {
  protectedUnit:
    "A patient's whole contribution to the training transcript: every update a client sends, across every tier and round.",
  adversary:
    "The guarantee covers the whole transcript of a run: every encoded client update, every edge and cloud model, and the model selected on the validation cohort. The evaluated attack is patient-level membership inference against the released model.",
  trusted: [
    "A1: each patient's records lie in the training split of exactly one client, and training patients are disjoint from validation patients. Each client runs the mechanism as specified. On eICU, A1 fails for the 2.9% of training individuals with stays at more than one hospital; the guarantee applies directly to the others.",
    "A2: the architecture, encoder parameters (pretrained on a patient-disjoint pool), hyperparameters, edge map, standardization constants and declared client sizes are public and fixed before training. Only the eICU end-to-end rerun satisfies this fully.",
    "A3: the forward pass of a record depends on that record alone.",
    "The declared client sizes used to calibrate noise are themselves released.",
  ],
  outside: [
    "Model outputs released at inference time beyond the trained model itself.",
    "Metadata such as which hospitals participate and when.",
    "Repeated participation of the same patients across separate training campaigns.",
    "Preprocessing, storage and operational systems at each site.",
    "Side channels in deployment hardware and networks.",
  ],
};
