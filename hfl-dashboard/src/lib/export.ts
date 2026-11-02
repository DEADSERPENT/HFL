import type { MetricRecord } from "./types";
import { METRIC_DEFINITIONS } from "@/content/metrics";
import { formatTarget, plainNumber } from "./format";
import { STATUS_META } from "./metric-status";

/**
 * Exports contain only the curated aggregate summary that is already visible
 * on the page, including each row's caveat (so the energy simulation caveat
 * travels with the numbers).
 */
export const EXPORT_COLUMNS = [
  "dataset",
  "metric",
  "variant",
  "value",
  "unit",
  "ci_lower",
  "ci_upper",
  "target",
  "evidence_status",
  "basis",
  "evaluation_context",
  "caveat",
  "provenance",
] as const;

export type ExportRow = Record<(typeof EXPORT_COLUMNS)[number], string>;

export function toExportRows(records: MetricRecord[]): ExportRow[] {
  return records.map((r) => ({
    dataset: r.dataset,
    metric: METRIC_DEFINITIONS[r.kind].name,
    variant: r.variant ?? "",
    value: plainNumber(r.value, r.decimals),
    unit: r.unit,
    ci_lower: r.confidenceInterval ? plainNumber(r.confidenceInterval.lower, r.decimals) : "",
    ci_upper: r.confidenceInterval ? plainNumber(r.confidenceInterval.upper, r.decimals) : "",
    target: r.target ? formatTarget(r.target, r.kind) : "",
    evidence_status: STATUS_META[r.evidenceStatus].label,
    basis: r.basis,
    evaluation_context: r.evaluationContext,
    caveat: r.caveat,
    provenance: r.publicProvenanceLabel,
  }));
}

function csvCell(v: string): string {
  return /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
}

export function toCsv(records: MetricRecord[]): string {
  const rows = toExportRows(records);
  const header = EXPORT_COLUMNS.join(",");
  return [header, ...rows.map((r) => EXPORT_COLUMNS.map((c) => csvCell(r[c])).join(","))].join("\n") + "\n";
}

export function toJson(records: MetricRecord[]): string {
  return JSON.stringify(
    {
      source: "PP-HFM Research Observatory: curated aggregate summary",
      note: "Approved aggregate summaries only. Energy figures are CloudSim Plus estimates, not physical measurements.",
      results: toExportRows(records),
    },
    null,
    2,
  );
}

export function download(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
