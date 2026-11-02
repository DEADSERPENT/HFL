import type { DatasetId, MetricDefinition, MetricKind, MetricRecord } from "@/lib/types";

/**
 * Curated aggregate results.
 *
 * Authored by hand from the final manuscript's Results section and its
 * objective table. Values were cross-checked against the manuscript on the
 * review date below. Nothing in this file is generated from research files.
 *
 * Release checklist before changing any value: see README.md, "Content review".
 */

export const REVIEWED_AT = "2026-11-02";
export const PROVENANCE =
  "Curated from the final manuscript's evaluation summary; cross-checked for public release.";

const ENERGY_CAVEAT =
  "Estimated by CloudSim Plus simulation; not a physical hardware energy measurement.";
const NETWORK_CAVEAT =
  "Simulated at packet level in ns-3 for every round; not measured on a physical network.";

const base = { publicProvenanceLabel: PROVENANCE, reviewedAt: REVIEWED_AT } as const;

export const METRIC_DEFINITIONS: Record<MetricKind, MetricDefinition> = {
  communication: {
    kind: "communication",
    objective: "O1",
    name: "Uplink traffic reduction",
    shortName: "Communication",
    unit: "%",
    definition:
      "Relative reduction in uplink bytes per cloud round when clients send compressed head updates to edge aggregators, compared with the centralized baseline. The count includes the index array that sparsification transmits with the retained values, which analytical estimates often omit.",
    baseline: "Centralized (single-tier) federated training of the same model.",
    context:
      "Two edge aggregators; 10 cloud rounds of 5 edge rounds each; update encoding: top-20% sparsification, 8-bit uniform quantization, local error feedback.",
    limitations:
      "A payload measurement for the evaluated model, topology and encoding. It is not a field measurement on a deployed network.",
    better: "higher",
  },
  "round-latency": {
    kind: "round-latency",
    objective: "O1b",
    name: "Round-latency reduction",
    shortName: "Round latency",
    unit: "%",
    definition:
      "Relative reduction in the wall-clock duration of one federated training round (communication plus computation) compared with the centralized baseline.",
    baseline: "Centralized (single-tier) federated training of the same model.",
    context:
      "Network simulated at packet level in ns-3 in every round. Not the same quantity as inference latency.",
    limitations:
      "Simulated, not measured on a physical network. The reduction is smaller than the traffic reduction because the hierarchy shortens link time, not computation.",
    better: "higher",
  },
  utility: {
    kind: "utility",
    objective: "O2b",
    name: "Utility cost of privacy",
    shortName: "Utility",
    unit: "points",
    definition:
      "Paired difference between an identical non-private system and the private system, in AUROC points (1 point = 0.01 AUROC) on the clinical corpora and in accuracy percentage points on WEAR. Positive values are a cost; negative values mean the private model scored higher in that evaluation.",
    baseline: "An otherwise identical system trained without differential privacy, paired by seed.",
    context:
      "Five paired seeds on VitalDB and eICU; fifteen seeds on WEAR. Intervals are paired t-intervals over per-seed differences.",
    limitations:
      "A target of at most two points is classified with the prespecified interval rule: met only when the whole interval is at or below two points.",
    better: "lower",
  },
  "inference-latency": {
    kind: "inference-latency",
    objective: "O3a",
    name: "P95 inference latency",
    shortName: "Inference latency",
    unit: "ms",
    definition:
      "95th-percentile end-to-end time to produce one prediction: preprocessing, forward pass, the evaluated (non-deployed) conformal-set step and post-processing.",
    baseline: "Absolute value against a 100 ms budget.",
    context:
      "Timed on a workstation CPU (Intel Core i7-14700) with ONNX Runtime, 1,000 timed runs after 100 warm-up runs.",
    limitations:
      "Measured on a workstation, not on edge or medical-device hardware. It is not a deployment service-level guarantee.",
    better: "lower",
  },
  "update-delivery": {
    kind: "update-delivery",
    objective: "O3b",
    name: "Update delivery",
    shortName: "Update delivery",
    unit: "%",
    definition:
      "Share of client model updates that reach their aggregator within a round.",
    baseline: "Target of more than 99% of updates delivered.",
    context:
      "Network simulated at packet level in ns-3; clients contend for a shared medium at each edge.",
    limitations:
      "Simulated, not measured on a physical network. Delivery depends strongly on how many clients share each edge.",
    better: "higher",
  },
  energy: {
    kind: "energy",
    objective: "O4",
    name: "Modelled energy saving per FL round",
    shortName: "Energy",
    unit: "%",
    definition:
      "Relative reduction in modelled total energy per federated round across device, edge and cloud tiers, compared with the centralized baseline.",
    baseline: "Centralized (single-tier) federated training of the same model.",
    context: "Energy model in the CloudSim Plus simulator.",
    limitations: ENERGY_CAVEAT,
    better: "higher",
  },
  privacy: {
    kind: "privacy",
    objective: "O2a",
    name: "Privacy budget",
    shortName: "Privacy",
    unit: "ε",
    definition:
      "Total reported (ε, δ) differential-privacy budget: the training budget computed by the privacy-loss-distribution accountant, plus the budget of an evaluated conformal calibration release.",
    baseline: "Target of ε ≤ 1 at δ = 10⁻⁵.",
    context:
      "Poisson-subsampled Gaussian mechanism with per-client noise calibration; budgets composed across all hierarchical releases.",
    limitations:
      "Valid only under the stated adjacency definition, sampling and accounting assumptions. A budget is not a measurement of leakage and does not cover channels outside the mechanism.",
    better: "lower",
  },
};

export const METRICS: MetricRecord[] = [
  // ── O1 Communication ────────────────────────────────────────────────
  {
    ...base,
    id: "communication-vitaldb",
    kind: "communication",
    objective: "O1",
    title: "Uplink traffic reduction",
    dataset: "VitalDB",
    value: 90.8,
    unit: "%",
    decimals: 1,
    target: { operator: ">=", value: 50, unit: "%" },
    basis: "measured",
    evidenceStatus: "measured",
    evaluationContext: `${METRIC_DEFINITIONS.communication.context} VitalDB system results use the case-level partition (unit: surgical case).`,
    baseline: METRIC_DEFINITIONS.communication.baseline,
    interpretation:
      "Edge aggregation of compressed head updates sends about one tenth of the baseline's uplink bytes.",
    caveat: "Payload measurement for the evaluated model, topology and encoding, not a field network trace.",
    headline: true,
  },
  {
    ...base,
    id: "communication-wear",
    kind: "communication",
    objective: "O1",
    title: "Uplink traffic reduction",
    dataset: "WEAR",
    value: 96.1,
    unit: "%",
    decimals: 1,
    target: { operator: ">=", value: 50, unit: "%" },
    basis: "measured",
    evidenceStatus: "measured",
    evaluationContext: METRIC_DEFINITIONS.communication.context,
    baseline: METRIC_DEFINITIONS.communication.baseline,
    interpretation: "The largest reduction of the three corpora under the same encoding.",
    caveat: "Payload measurement for the evaluated model, topology and encoding, not a field network trace.",
    headline: true,
  },
  {
    ...base,
    id: "communication-eicu",
    kind: "communication",
    objective: "O1",
    title: "Uplink traffic reduction",
    dataset: "eICU",
    value: 92.3,
    unit: "%",
    decimals: 1,
    target: { operator: ">=", value: 50, unit: "%" },
    basis: "measured",
    evidenceStatus: "measured",
    evaluationContext: METRIC_DEFINITIONS.communication.context,
    baseline: METRIC_DEFINITIONS.communication.baseline,
    interpretation: "The reduction holds on the external 187-hospital corpus.",
    caveat: "Payload measurement for the evaluated model, topology and encoding, not a field network trace.",
    headline: true,
  },

  // ── O1b Round latency ───────────────────────────────────────────────
  {
    ...base,
    id: "round-latency-vitaldb",
    kind: "round-latency",
    objective: "O1b",
    title: "Round-latency reduction",
    dataset: "VitalDB",
    value: 16.9,
    unit: "%",
    decimals: 1,
    target: { operator: ">", value: 0, unit: "%" },
    basis: "modelled",
    evidenceStatus: "modelled",
    evaluationContext: `${METRIC_DEFINITIONS["round-latency"].context} Round duration fell from 90.5 ms to 75.2 ms. VitalDB system results use the case-level partition (unit: surgical case).`,
    baseline: METRIC_DEFINITIONS["round-latency"].baseline,
    interpretation:
      "Rounds are shorter, but by far less than the traffic cut, because computation time is unchanged.",
    caveat: NETWORK_CAVEAT,
    headline: true,
  },
  {
    ...base,
    id: "round-latency-wear",
    kind: "round-latency",
    objective: "O1b",
    title: "Round-latency reduction",
    dataset: "WEAR",
    value: 21.7,
    unit: "%",
    decimals: 1,
    target: { operator: ">", value: 0, unit: "%" },
    basis: "modelled",
    evidenceStatus: "modelled",
    evaluationContext: `${METRIC_DEFINITIONS["round-latency"].context} Round duration fell from 104.5 ms to 81.8 ms.`,
    baseline: METRIC_DEFINITIONS["round-latency"].baseline,
    interpretation: "A positive reduction in every simulated round.",
    caveat: NETWORK_CAVEAT,
    headline: true,
  },
  {
    ...base,
    id: "round-latency-eicu",
    kind: "round-latency",
    objective: "O1b",
    title: "Round-latency reduction",
    dataset: "eICU",
    value: 33.4,
    unit: "%",
    decimals: 1,
    target: { operator: ">", value: 0, unit: "%" },
    basis: "modelled",
    evidenceStatus: "modelled",
    evaluationContext: `${METRIC_DEFINITIONS["round-latency"].context} Round duration fell from 261.4 ms to 174.1 ms.`,
    baseline: METRIC_DEFINITIONS["round-latency"].baseline,
    interpretation:
      "The benefit is largest here because more stations share each medium, so shortening link time matters more.",
    caveat: NETWORK_CAVEAT,
    headline: true,
  },

  // ── O4 Energy ───────────────────────────────────────────────────────
  {
    ...base,
    id: "energy-vitaldb",
    kind: "energy",
    objective: "O4",
    title: "Modelled energy saving per FL round",
    dataset: "VitalDB",
    value: 72.3,
    unit: "%",
    decimals: 1,
    target: { operator: ">=", value: 20, unit: "%" },
    basis: "modelled",
    evidenceStatus: "modelled",
    evaluationContext: `${METRIC_DEFINITIONS.energy.context} VitalDB system results use the case-level partition (unit: surgical case).`,
    baseline: METRIC_DEFINITIONS.energy.baseline,
    interpretation:
      "Adding an edge tier alone raises modelled energy (1,266 J to 1,344 J); the saving comes from reduced device computation and transmission, which lowers the device term about fivefold.",
    caveat: ENERGY_CAVEAT,
    headline: true,
  },
  {
    ...base,
    id: "energy-wear",
    kind: "energy",
    objective: "O4",
    title: "Modelled energy saving per FL round",
    dataset: "WEAR",
    value: 76.8,
    unit: "%",
    decimals: 1,
    target: { operator: ">=", value: 20, unit: "%" },
    basis: "modelled",
    evidenceStatus: "modelled",
    evaluationContext: METRIC_DEFINITIONS.energy.context,
    baseline: METRIC_DEFINITIONS.energy.baseline,
    interpretation: "The modelled saving clears the 20% target by a wide margin.",
    caveat: ENERGY_CAVEAT,
    headline: true,
  },
  {
    ...base,
    id: "energy-eicu",
    kind: "energy",
    objective: "O4",
    title: "Modelled energy saving per FL round",
    dataset: "eICU",
    value: 79.6,
    unit: "%",
    decimals: 1,
    target: { operator: ">=", value: 20, unit: "%" },
    basis: "modelled",
    evidenceStatus: "modelled",
    evaluationContext: METRIC_DEFINITIONS.energy.context,
    baseline: METRIC_DEFINITIONS.energy.baseline,
    interpretation: "The highest modelled saving of the three corpora.",
    caveat: ENERGY_CAVEAT,
    headline: true,
  },

  // ── O3a Inference latency ───────────────────────────────────────────
  {
    ...base,
    id: "inference-latency-vitaldb",
    kind: "inference-latency",
    objective: "O3a",
    title: "P95 inference latency",
    dataset: "VitalDB",
    value: 2.3,
    unit: "ms",
    decimals: 2,
    target: { operator: "<", value: 100, unit: "ms" },
    basis: "measured",
    evidenceStatus: "measured",
    evaluationContext: `${METRIC_DEFINITIONS["inference-latency"].context} The forward pass dominates (P95 2.165 ms of 2.299 ms). VitalDB system results use the case-level partition (unit: surgical case).`,
    baseline: METRIC_DEFINITIONS["inference-latency"].baseline,
    interpretation:
      "Well inside the 100 ms budget. The privacy mechanism adds no inference cost, because noise acts only on training gradients.",
    caveat:
      "Workstation CPU, not edge hardware. An 8-bit inference graph was evaluated and rejected because it raised P95 to 17.34 ms.",
    headline: true,
  },
  {
    ...base,
    id: "inference-latency-wear",
    kind: "inference-latency",
    objective: "O3a",
    title: "P95 inference latency",
    dataset: "WEAR",
    value: 0.75,
    unit: "ms",
    decimals: 2,
    target: { operator: "<", value: 100, unit: "ms" },
    basis: "measured",
    evidenceStatus: "measured",
    evaluationContext: METRIC_DEFINITIONS["inference-latency"].context,
    baseline: METRIC_DEFINITIONS["inference-latency"].baseline,
    interpretation: "Well inside the 100 ms budget under the stated conditions.",
    caveat: "Workstation CPU, not edge hardware; not a deployment service-level guarantee.",
    headline: true,
  },
  {
    ...base,
    id: "inference-latency-eicu",
    kind: "inference-latency",
    objective: "O3a",
    title: "P95 inference latency",
    dataset: "eICU",
    value: 0.24,
    unit: "ms",
    decimals: 2,
    target: { operator: "<", value: 100, unit: "ms" },
    basis: "measured",
    evidenceStatus: "measured",
    evaluationContext: METRIC_DEFINITIONS["inference-latency"].context,
    baseline: METRIC_DEFINITIONS["inference-latency"].baseline,
    interpretation: "The lowest of the three corpora, and well inside the 100 ms budget under the stated conditions.",
    caveat: "Workstation CPU, not edge hardware; not a deployment service-level guarantee.",
    headline: true,
  },

  // ── O3b Update delivery ─────────────────────────────────────────────
  {
    ...base,
    id: "update-delivery-vitaldb",
    kind: "update-delivery",
    objective: "O3b",
    title: "Update delivery",
    dataset: "VitalDB",
    value: 100.0,
    unit: "%",
    decimals: 2,
    target: { operator: ">", value: 99, unit: "%" },
    basis: "modelled",
    evidenceStatus: "modelled",
    evaluationContext: `${METRIC_DEFINITIONS["update-delivery"].context} Two edge aggregators, nine clients. VitalDB system results use the case-level partition (unit: surgical case).`,
    baseline: METRIC_DEFINITIONS["update-delivery"].baseline,
    interpretation: "Every simulated update was delivered; nine clients share the two edges.",
    caveat: NETWORK_CAVEAT,
    headline: true,
  },
  {
    ...base,
    id: "update-delivery-wear",
    kind: "update-delivery",
    objective: "O3b",
    title: "Update delivery",
    dataset: "WEAR",
    value: 99.94,
    unit: "%",
    decimals: 2,
    target: { operator: ">", value: 99, unit: "%" },
    basis: "modelled",
    evidenceStatus: "modelled",
    evaluationContext: `${METRIC_DEFINITIONS["update-delivery"].context} Two edge aggregators, 22 clients.`,
    baseline: METRIC_DEFINITIONS["update-delivery"].baseline,
    interpretation: "Above the 99% target in the simulated network.",
    caveat: NETWORK_CAVEAT,
    headline: true,
  },
  {
    ...base,
    id: "update-delivery-eicu",
    kind: "update-delivery",
    objective: "O3b",
    title: "Update delivery",
    dataset: "eICU",
    variant: "Two-edge configuration",
    value: 97.83,
    unit: "%",
    decimals: 2,
    target: { operator: ">", value: 99, unit: "%" },
    basis: "modelled",
    evidenceStatus: "target-not-met",
    evaluationContext: `${METRIC_DEFINITIONS["update-delivery"].context} Two edge aggregators shared by 187 hospital clients.`,
    baseline: `${METRIC_DEFINITIONS["update-delivery"].baseline} Centralized training delivered 95.11% in the same simulation.`,
    interpretation:
      "Below target at the reported two-edge configuration, because 187 clients contend for two shared media.",
    caveat: `${NETWORK_CAVEAT} In a separate edge-count sensitivity test (everything else fixed), delivery rose monotonically with the number of edges: it met the target on average from six edges, in every round from eight edges (minimum 99.49%), and reached 99.94% at sixteen. That test does not change the headline result, which is the two-edge configuration.`,
    headline: true,
  },

  // ── O2a Privacy budget ──────────────────────────────────────────────
  {
    ...base,
    id: "privacy-vitaldb",
    kind: "privacy",
    objective: "O2a",
    title: "Total privacy budget",
    dataset: "VitalDB",
    value: 1.0,
    unit: "ε",
    decimals: 3,
    target: { operator: "<=", value: 1, unit: "ε" },
    basis: "measured",
    evidenceStatus: "measured",
    privacy: { training: 0.9, conformal: 0.1, delta: 1e-5, unit: "person" },
    evaluationContext:
      "Person-level guarantee: neighbouring datasets differ by all records of one person. Training budget from the privacy-loss-distribution accountant with per-client noise; conformal budget from an evaluated calibration release.",
    baseline: METRIC_DEFINITIONS.privacy.baseline,
    interpretation:
      "Training (ε = 0.900) plus the evaluated conformal release (ε = 0.100) composes to exactly the ε ≤ 1 target.",
    caveat:
      "An accounting result, not a measurement of leakage. It covers the training transcript, not the whole pipeline: standardization constants are fitted on the training cohort and the headline encoders do not meet the public-encoder assumption. The conformal release was evaluated but is not part of the deployed system.",
    headline: false,
  },
  {
    ...base,
    id: "privacy-wear",
    kind: "privacy",
    objective: "O2a",
    title: "Total privacy budget",
    dataset: "WEAR",
    value: 0.966,
    unit: "ε",
    decimals: 3,
    target: { operator: "<=", value: 1, unit: "ε" },
    basis: "measured",
    evidenceStatus: "measured",
    privacy: { training: 0.766, conformal: 0.2, delta: 1e-5, unit: "record" },
    evaluationContext:
      "Record-level guarantee: each WEAR client is one participant, so neighbouring datasets differ by one record. Training budget from the accountant; conformal budget from an evaluated calibration release.",
    baseline: METRIC_DEFINITIONS.privacy.baseline,
    interpretation: "Training (ε = 0.766) plus the conformal release (ε = 0.200) gives ε = 0.966.",
    caveat:
      "Record-level, so not comparable one-to-one with the patient-level budgets of the clinical corpora. An accounting result, not a measurement of leakage; covers the training transcript only.",
    headline: false,
  },
  {
    ...base,
    id: "privacy-eicu",
    kind: "privacy",
    objective: "O2a",
    title: "Total privacy budget",
    dataset: "eICU",
    variant: "Individuals held by one hospital",
    value: 1.0,
    unit: "ε",
    decimals: 3,
    target: { operator: "<=", value: 1, unit: "ε" },
    basis: "measured",
    evidenceStatus: "measured",
    privacy: { training: 0.9, conformal: 0.1, delta: 1e-5, unit: "patient" },
    evaluationContext:
      "Patient-level guarantee across 187 hospital clients, for individuals whose records lie at one hospital (97.1% of training individuals). Clients then act on disjoint individuals and compose in parallel.",
    baseline: METRIC_DEFINITIONS.privacy.baseline,
    interpretation:
      "For individuals at one hospital, training (ε = 0.900) plus the conformal release (ε = 0.100) composes to ε = 1.000. The budget is not uniform across the whole eICU training population.",
    caveat:
      "An accounting result, not a measurement of leakage. 2.9% of eICU training individuals have stays at two to four hospitals; for them the hospitals' mechanisms compose, and the training budget is bounded by \u03B5 \u2264 1.42 (two hospitals), 1.77 (three) or 2.08 (four) at \u03B4 = 10\u207B\u2075. Only the eICU rerun with disjoint encoders and pool-fitted standardization holds end to end; the headline eICU run covers the training transcript.",
    headline: false,
  },

  // ── O2b Utility ─────────────────────────────────────────────────────
  {
    ...base,
    id: "utility-vitaldb",
    kind: "utility",
    objective: "O2b",
    title: "Utility cost of privacy",
    dataset: "VitalDB",
    variant: "Person-level rerun",
    value: -1.18,
    unit: "AUROC points",
    decimals: 2,
    target: { operator: "<=", value: 2, unit: "AUROC points" },
    basis: "measured",
    evidenceStatus: "measured",
    confidenceInterval: {
      lower: -1.63,
      upper: -0.73,
      unit: "AUROC points",
      method: "95% paired t-interval over five seeds",
    },
    evaluationContext:
      "Person-level partition (each person in one split and one client). Private AUROC 0.8318 against 0.8200 for the non-private reference (raw difference −0.0118, p = 0.002).",
    baseline: METRIC_DEFINITIONS.utility.baseline,
    interpretation:
      "The private model scored higher in this evaluation, so the guarantee cost no AUROC here. This is consistent with regularization by clipping and noise, which this experiment does not isolate.",
    caveat:
      "Not a guarantee that privacy improves utility. On the earlier case-level partition the change was −0.90 [−1.82, +0.02], an unresolved estimate.",
    headline: true,
  },
  {
    ...base,
    id: "utility-wear",
    kind: "utility",
    objective: "O2b",
    title: "Utility cost of privacy",
    dataset: "WEAR",
    variant: "Record-level",
    value: 1.97,
    unit: "accuracy pp",
    decimals: 2,
    target: { operator: "<=", value: 2, unit: "accuracy pp" },
    basis: "measured",
    evidenceStatus: "inconclusive",
    confidenceInterval: {
      lower: 1.76,
      upper: 2.17,
      unit: "accuracy pp",
      method: "95% paired t-interval over fifteen seeds",
    },
    evaluationContext:
      "Record-level guarantee (one participant per client). Accuracy loss in percentage points against an identical non-private system.",
    baseline: METRIC_DEFINITIONS.utility.baseline,
    interpretation:
      "The point estimate is just under two points, but the interval spans the threshold, so the target is unresolved.",
    caveat:
      "Accuracy points on an activity-recognition task; not comparable with AUROC points on the clinical corpora.",
    headline: false,
  },
  {
    ...base,
    id: "utility-eicu-headline",
    kind: "utility",
    objective: "O2b",
    title: "Utility cost of privacy",
    dataset: "eICU",
    variant: "Headline (training-fitted standardization)",
    value: 3.09,
    unit: "AUROC points",
    decimals: 2,
    target: { operator: "<=", value: 2, unit: "AUROC points" },
    basis: "measured",
    evidenceStatus: "inconclusive",
    confidenceInterval: {
      lower: 1.37,
      upper: 4.81,
      unit: "AUROC points",
      method: "95% paired t-interval over five seeds",
    },
    evaluationContext:
      "AUROC fell from 0.8245 (non-private) to 0.7936 (private). Standardization constants fitted on the training cohort.",
    baseline: METRIC_DEFINITIONS.utility.baseline,
    interpretation:
      "A cost is resolved (the interval excludes zero) and the point estimate exceeds two points, but the interval spans the target, so it is inconclusive under the prespecified rule.",
    caveat:
      "The cost is driven by the smallest hospitals, which sample every patient at every step and carry the largest noise multipliers.",
    headline: true,
  },
  {
    ...base,
    id: "utility-eicu-end-to-end",
    kind: "utility",
    objective: "O2b",
    title: "Utility cost of privacy",
    dataset: "eICU",
    variant: "End to end (pool-fitted standardization)",
    value: 3.91,
    unit: "AUROC points",
    decimals: 2,
    target: { operator: "<=", value: 2, unit: "AUROC points" },
    basis: "measured",
    evidenceStatus: "target-not-met",
    confidenceInterval: {
      lower: 2.4,
      upper: 5.42,
      unit: "AUROC points",
      method: "95% paired t-interval over five seeds",
    },
    evaluationContext:
      "Standardization constants fitted on a disjoint pool and encoders pretrained in those units, so the guarantee holds end to end.",
    baseline: METRIC_DEFINITIONS.utility.baseline,
    interpretation:
      "A clear miss: the whole interval lies above the two-point target. This is the price of the strictest configuration.",
    caveat:
      "Kept separate from the headline eICU result; the two evaluation paths must not be averaged or collapsed.",
    headline: true,
  },
];

export function metricsFor(filter: { dataset?: DatasetId; kind?: MetricKind }): MetricRecord[] {
  return METRICS.filter(
    (m) => (!filter.dataset || m.dataset === filter.dataset) && (!filter.kind || m.kind === filter.kind),
  );
}

export function metricById(id: string): MetricRecord | undefined {
  return METRICS.find((m) => m.id === id);
}

/** Display order of metric kinds across the site. */
export const METRIC_ORDER: MetricKind[] = [
  "communication",
  "round-latency",
  "utility",
  "inference-latency",
  "update-delivery",
  "energy",
  "privacy",
];
