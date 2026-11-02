/**
 * Types for the curated public content layer.
 *
 * Every number on the site is a `MetricRecord` (or a record in privacy.ts /
 * publication.ts) authored by hand from the final manuscript. Nothing here is
 * loaded from research files at build or run time.
 */

export const DATASETS = ["VitalDB", "WEAR", "eICU"] as const;
export type DatasetId = (typeof DATASETS)[number];

/** The six public evidence labels (spec §2.3). */
export const EVIDENCE_STATUSES = [
  "measured",
  "modelled",
  "inconclusive",
  "target-not-met",
  "not-evaluated",
  "illustrative",
] as const;
export type EvidenceStatus = (typeof EVIDENCE_STATUSES)[number];

/** How a number was produced, independent of whether it meets a target. */
export type Basis = "measured" | "modelled";

export const METRIC_KINDS = [
  "communication",
  "round-latency",
  "utility",
  "inference-latency",
  "update-delivery",
  "energy",
  "privacy",
] as const;
export type MetricKind = (typeof METRIC_KINDS)[number];

export type ObjectiveId = "O1" | "O1b" | "O2a" | "O2b" | "O3a" | "O3b" | "O4";

export type ComparisonOperator = "<" | "<=" | ">" | ">=";

export type Target = {
  operator: ComparisonOperator;
  value: number;
  unit: string;
};

export type ConfidenceInterval = {
  lower: number;
  upper: number;
  unit: string;
  /** Plain-language description of how the interval was computed. */
  method: string;
};

export type PrivacyComponents = {
  training: number;
  conformal: number;
  delta: number;
  /** Protected unit, e.g. "person", "patient", "record". */
  unit: string;
};

export type MetricRecord = {
  id: string;
  kind: MetricKind;
  objective: ObjectiveId;
  title: string;
  dataset: DatasetId;
  /** Distinguishes several records for one dataset/metric (e.g. two eICU utility paths). */
  variant?: string;
  value: number;
  unit: string;
  /** Number of decimals to display. */
  decimals: number;
  target?: Target;
  basis: Basis;
  evidenceStatus: EvidenceStatus;
  evaluationContext: string;
  baseline?: string;
  confidenceInterval?: ConfidenceInterval;
  interpretation: string;
  caveat: string;
  publicProvenanceLabel: string;
  reviewedAt?: string;
  /** Only for kind === "privacy". */
  privacy?: PrivacyComponents;
  /** Appears in the homepage evidence snapshot. */
  headline: boolean;
};

export type MetricDefinition = {
  kind: MetricKind;
  objective: ObjectiveId;
  name: string;
  shortName: string;
  unit: string;
  definition: string;
  baseline: string;
  context: string;
  limitations: string;
  /** Direction in which the quantity is better. */
  better: "higher" | "lower";
};

export type TargetOutcome = "met" | "not-met" | "inconclusive" | "no-target";
