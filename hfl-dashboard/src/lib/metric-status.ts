import type {
  ComparisonOperator,
  EvidenceStatus,
  MetricRecord,
  Target,
  TargetOutcome,
} from "./types";

/** Round to a fixed number of decimals to avoid floating-point noise in comparisons. */
export function roundTo(value: number, decimals: number): number {
  const f = 10 ** decimals;
  return Math.round(value * f) / f;
}

export function compare(value: number, operator: ComparisonOperator, threshold: number): boolean {
  switch (operator) {
    case "<":
      return value < threshold;
    case "<=":
      return value <= threshold;
    case ">":
      return value > threshold;
    case ">=":
      return value >= threshold;
  }
}

/**
 * Classify a result against its target.
 *
 * With a confidence interval, the manuscript's prespecified interval rule is
 * applied: the target is met only if the whole interval satisfies it, missed
 * only if the whole interval violates it, and otherwise inconclusive. Without
 * an interval the point estimate is compared directly.
 */
export function classifyTarget(
  value: number,
  target: Target | undefined,
  interval?: { lower: number; upper: number },
): TargetOutcome {
  if (!target) return "no-target";
  const v = roundTo(value, 9);
  if (!interval) return compare(v, target.operator, target.value) ? "met" : "not-met";
  const lo = roundTo(interval.lower, 9);
  const hi = roundTo(interval.upper, 9);
  const loOk = compare(lo, target.operator, target.value);
  const hiOk = compare(hi, target.operator, target.value);
  if (loOk && hiOk) return "met";
  if (!loOk && !hiOk) return "not-met";
  return "inconclusive";
}

export function targetOutcomeOf(record: MetricRecord): TargetOutcome {
  return classifyTarget(record.value, record.target, record.confidenceInterval);
}

/**
 * The evidence status a record *must* carry, derived from its basis and its
 * target outcome. Content validation fails if the authored status differs, so
 * an inconclusive or missed result can never be published as a success.
 */
export function expectedEvidenceStatus(record: MetricRecord): EvidenceStatus {
  const outcome = targetOutcomeOf(record);
  if (outcome === "not-met") return "target-not-met";
  if (outcome === "inconclusive") return "inconclusive";
  return record.basis;
}

export const STATUS_META: Record<
  EvidenceStatus,
  { label: string; description: string; tone: "measured" | "modelled" | "warn" | "miss" | "neutral" }
> = {
  measured: {
    label: "Measured",
    description: "Directly measured in the described experiment or evaluation.",
    tone: "measured",
  },
  modelled: {
    label: "Modelled",
    description:
      "Produced by a simulator or analytical model, not measured on physical deployment hardware.",
    tone: "modelled",
  },
  inconclusive: {
    label: "Inconclusive",
    description: "The evidence does not resolve the prespecified decision rule.",
    tone: "warn",
  },
  "target-not-met": {
    label: "Target not met",
    description: "The stated target was not reached.",
    tone: "miss",
  },
  "not-evaluated": {
    label: "Not evaluated",
    description: "No evidence is being claimed.",
    tone: "neutral",
  },
  illustrative: {
    label: "Illustrative",
    description: "A conceptual visual or example, not experimental evidence.",
    tone: "neutral",
  },
};

export const OUTCOME_LABEL: Record<TargetOutcome, string> = {
  met: "Target met",
  "not-met": "Target not met",
  inconclusive: "Inconclusive against target",
  "no-target": "No target",
};
