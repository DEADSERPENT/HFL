import type { ObjectiveId } from "@/lib/types";

export type Objective = {
  id: ObjectiveId;
  title: string;
  target: string;
  note?: string;
};

export const OBJECTIVES: Objective[] = [
  { id: "O1", title: "Uplink traffic reduction", target: "≥ 50%" },
  { id: "O1b", title: "Round-latency reduction", target: "> 0%" },
  {
    id: "O2a",
    title: "Total privacy budget",
    target: "ε ≤ 1",
    note: "Under the stated accounting protocol, δ = 10⁻⁵.",
  },
  { id: "O2b", title: "Utility cost of privacy", target: "≤ 2 points", note: "Prespecified interval rule." },
  { id: "O3a", title: "P95 inference latency", target: "< 100 ms" },
  { id: "O3b", title: "Update-delivery reliability", target: "> 99%" },
  { id: "O4", title: "Energy saving per round", target: "≥ 20%", note: "Modelled in CloudSim Plus." },
];

export const BASELINES = [
  {
    name: "Centralized (single-tier) federated training",
    role: "Comparator for all system objectives (communication, latency, delivery, energy).",
  },
  {
    name: "Hierarchy alone",
    role: "Two-tier aggregation without PP-HFM\u2019s other components, used to isolate the effect of adding an edge tier.",
  },
  {
    name: "Identical non-private system",
    role: "Comparator for the utility cost of privacy, paired by seed.",
  },
  {
    name: "Re-implemented HED-FL and FL2DP",
    role: "Published hierarchical and differentially private FL designs, re-implemented for comparison. PP-HFM uploads 2.2–4.0 times less than both and shows lower measured leakage than both in the VitalDB audit. Non-private HED-FL is more accurate on eICU (AUROC 0.825 against 0.794).",
  },
];

export const EXPERIMENT_FAMILIES = [
  {
    id: "communication",
    title: "Communication experiments",
    body: "Uplink bytes per cloud round of the deployed update encoding (top-20% sparsification, 8-bit quantization, error feedback), including the sparsification index array.",
    basis: "measured",
  },
  {
    id: "privacy-utility",
    title: "Privacy and utility experiments",
    body: "Private against identical non-private systems over five paired seeds. AUROC is primary; AUPRC and balanced accuracy were declared as secondary measures before the runs.",
    basis: "measured",
  },
  {
    id: "latency-delivery",
    title: "Latency and update-delivery experiments",
    body: "Round latency and delivery from a packet-level ns-3 simulation of every round. Inference latency timed on a workstation CPU, 1,000 runs after 100 warm-up runs.",
    basis: "mixed",
  },
  {
    id: "energy",
    title: "Energy simulation",
    body: "Per-tier energy per round from a CloudSim Plus model of devices, edges and cloud.",
    basis: "modelled",
  },
  {
    id: "audit",
    title: "Membership-inference audit",
    body: "Patient-level membership inference on VitalDB: loss thresholding and a patient-adapted likelihood-ratio attack (LiRA) with 16 shadow models, compared with a difficulty floor and checked against a non-private positive control.",
    basis: "measured",
  },
] as const;

export const SENSITIVITY = [
  {
    title: "Recipe decomposition",
    body: "Three training recipes across ε ∈ {0.5, 1, 2, 4, 8, ∞} separate the roles of pretrained initialization and head-only noise. On VitalDB and WEAR, pretrained initialization, not head-only noise, is what makes a strict budget survivable.",
  },
  {
    title: "Cost of the privacy unit",
    body: "At a matched budget, the utility cost of protecting the patient rather than the record grows with records per patient k, following A(1 − 1/k). With one record per patient the two units coincide, which serves as a built-in control.",
  },
  {
    title: "Edge-count scaling (eICU)",
    body: "Edge aggregators varied from 2 to 16 with everything else fixed. Update delivery rises monotonically, meets the target on average from six edges and in every round from eight.",
  },
  {
    title: "Inference graph precision",
    body: "An 8-bit inference graph was evaluated and rejected: it raised VitalDB P95 latency from 2.30 ms to 17.34 ms.",
  },
];

export const STATISTICS = {
  interval: "d̄ ± t(S−1, 0.975) · s_d / √S",
  body: [
    "Comparisons between arms are paired by seed. Intervals are paired t-intervals over S seeds with per-seed differences d_s.",
    "An effect is called resolved when the interval excludes zero. An unresolved estimate is reported as such and is not read as evidence of absence.",
    "Targets with an interval are classified by the prespecified rule: met only if the whole interval satisfies the target, missed if the whole interval violates it, otherwise inconclusive.",
    "Seed counts were fixed before each comparison and were not increased after inspecting results. Grids at three seeds estimate how a cost changes across a factor, not each cell individually.",
    "The reported checkpoint is the one with the best validation AUROC; each is evaluated once on the test split.",
  ],
};
