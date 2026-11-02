import type { ComparisonOperator, ConfidenceInterval, MetricRecord, Target } from "./types";

const MINUS = "−";

/** Fixed-decimal number with a true minus sign (U+2212). */
export function formatNumber(value: number, decimals: number): string {
  const fixed = Math.abs(value).toFixed(decimals);
  const isZero = Number(fixed) === 0;
  return value < 0 && !isZero ? `${MINUS}${fixed}` : fixed;
}

/** Attach a unit: "%" and "ms"-style units are compact; word units get a space. */
export function withUnit(text: string, unit: string): string {
  if (unit === "%") return `${text}%`;
  if (unit === "") return text;
  return `${text} ${unit}`;
}

export function formatValue(record: Pick<MetricRecord, "value" | "unit" | "decimals" | "kind">): string {
  const n = formatNumber(record.value, record.decimals);
  if (record.kind === "privacy") return `ε = ${n}`;
  return withUnit(n, record.unit);
}

export function formatInterval(ci: ConfidenceInterval, decimals: number): string {
  return `[${formatNumber(ci.lower, decimals)}, ${formatNumber(ci.upper, decimals)}]`;
}

export const OPERATOR_TEXT: Record<ComparisonOperator, string> = {
  "<": "<",
  "<=": "≤",
  ">": ">",
  ">=": "≥",
};

export const OPERATOR_WORDS: Record<ComparisonOperator, string> = {
  "<": "below",
  "<=": "at most",
  ">": "above",
  ">=": "at least",
};

export function formatTarget(target: Target, kind?: MetricRecord["kind"]): string {
  const v = Number.isInteger(target.value) ? String(target.value) : String(target.value);
  if (kind === "privacy") return `ε ${OPERATOR_TEXT[target.operator]} ${v}`;
  return `${OPERATOR_TEXT[target.operator]} ${withUnit(v, target.unit)}`;
}

/** "10⁻⁵"-style rendering of a delta such as 1e-5. */
export function formatDelta(delta: number): string {
  const exp = Math.round(Math.log10(delta));
  const sup: Record<string, string> = {
    "-": "⁻",
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
  };
  return `10${String(exp)
    .split("")
    .map((c) => sup[c] ?? c)
    .join("")}`;
}

/** Plain-text version (ASCII hyphen-minus) for CSV/JSON exports. */
export function plainNumber(value: number, decimals: number): string {
  return value.toFixed(decimals);
}
