import type { DatasetId, EvidenceStatus, MetricKind, MetricRecord } from "./types";

export type ResultFilters = {
  dataset: DatasetId | "all";
  metric: MetricKind | "all";
  statuses: EvidenceStatus[];
};

export function filterMetrics(records: MetricRecord[], f: ResultFilters): MetricRecord[] {
  return records.filter(
    (r) =>
      (f.dataset === "all" || r.dataset === f.dataset) &&
      (f.metric === "all" || r.kind === f.metric) &&
      (f.statuses.length === 0 || f.statuses.includes(r.evidenceStatus)),
  );
}

export function groupByKind(records: MetricRecord[], order: MetricKind[]): [MetricKind, MetricRecord[]][] {
  return order
    .map((k) => [k, records.filter((r) => r.kind === k)] as [MetricKind, MetricRecord[]])
    .filter(([, rs]) => rs.length > 0);
}

/** Short screen-reader summary of the active filter, announced politely. */
export function describeFilters(f: ResultFilters, count: number, metricName?: string): string {
  const ds = f.dataset === "all" ? "all datasets" : f.dataset;
  const m = f.metric === "all" ? "all metrics" : (metricName ?? f.metric);
  const st = f.statuses.length ? ` with status ${f.statuses.join(", ")}` : "";
  return `Showing ${count} result${count === 1 ? "" : "s"} for ${m}, ${ds}${st}.`;
}
