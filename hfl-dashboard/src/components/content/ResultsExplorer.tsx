"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";
import { METRICS, METRIC_DEFINITIONS, METRIC_ORDER, metricById } from "@/content/metrics";
import { describeFilters, filterMetrics, groupByKind, type ResultFilters } from "@/lib/filters";
import { download, toCsv, toJson } from "@/lib/export";
import { formatInterval, formatTarget, formatValue } from "@/lib/format";
import { STATUS_META } from "@/lib/metric-status";
import { DATASETS, METRIC_KINDS, type DatasetId, type EvidenceStatus, type MetricKind, type MetricRecord } from "@/lib/types";
import { DatasetSelector } from "./DatasetSelector";
import { MetricChart } from "@/components/charts/MetricChart";
import { ResearchMetricCard } from "@/components/metrics/ResearchMetricCard";
import { ResultDetailDrawer } from "@/components/metrics/ResultDetailDrawer";
import { MetricDefinitionPanel } from "@/components/metrics/MetricDefinitionPanel";
import { EvidenceStatusLabel } from "@/components/metrics/EvidenceStatusLabel";

const FILTER_STATUSES: EvidenceStatus[] = ["measured", "modelled", "inconclusive", "target-not-met"];
type View = "cards" | "charts" | "table";

export function ResultsExplorer() {
  const [filters, setFilters] = useState<ResultFilters>({ dataset: "all", metric: "all", statuses: [] });
  const [view, setView] = useState<View>("charts");
  const [showCI, setShowCI] = useState(true);
  const [showTargets, setShowTargets] = useState(true);
  const [explain, setExplain] = useState(false);
  const [detail, setDetail] = useState<MetricRecord | null>(null);

  // Deep links: ?dataset=eICU&metric=utility&detail=<id>&view=table
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const ds = q.get("dataset");
    const m = q.get("metric");
    const v = q.get("view");
    setFilters((f) => ({
      ...f,
      dataset: ds && (DATASETS as readonly string[]).includes(ds) ? (ds as DatasetId) : f.dataset,
      metric: m && (METRIC_KINDS as readonly string[]).includes(m) ? (m as MetricKind) : f.metric,
    }));
    if (v === "cards" || v === "charts" || v === "table") setView(v);
    const d = q.get("detail");
    if (d) {
      const r = metricById(d);
      if (r) setDetail(r);
    }
  }, []);

  useEffect(() => {
    const q = new URLSearchParams();
    if (filters.dataset !== "all") q.set("dataset", filters.dataset);
    if (filters.metric !== "all") q.set("metric", filters.metric);
    if (view !== "charts") q.set("view", view);
    if (detail) q.set("detail", detail.id);
    const s = q.toString();
    window.history.replaceState(null, "", `${window.location.pathname}${s ? `?${s}` : ""}`);
  }, [filters, view, detail]);

  const records = useMemo(() => filterMetrics(METRICS, filters), [filters]);
  const groups = useMemo(() => groupByKind(records, METRIC_ORDER), [records]);
  const open = useCallback((r: MetricRecord) => setDetail(r), []);
  const close = useCallback(() => setDetail(null), []);
  const announcement = describeFilters(filters, records.length, filters.metric !== "all" ? METRIC_DEFINITIONS[filters.metric].name : undefined);

  const toggleStatus = (s: EvidenceStatus) =>
    setFilters((f) => ({ ...f, statuses: f.statuses.includes(s) ? f.statuses.filter((x) => x !== s) : [...f.statuses, s] }));

  return (
    <div>
      <div className="clay sticky top-[80px] z-20 space-y-4 p-4 md:p-5" role="search" aria-label="Filter results">
        <div className="grid gap-4 lg:grid-cols-[auto_1fr]">
          <FilterRow label="Dataset">
            <DatasetSelector value={filters.dataset} onChange={(d) => setFilters((f) => ({ ...f, dataset: d }))} label="Dataset" includeAll />
          </FilterRow>
          <FilterRow label="Metric">
            <label className="sr-only" htmlFor="metric-select">
              Metric
            </label>
            <select
              id="metric-select"
              value={filters.metric}
              onChange={(e) => setFilters((f) => ({ ...f, metric: e.target.value as MetricKind | "all" }))}
              className="field-input min-h-10 w-full max-w-xs !rounded-full px-4 text-sm"
            >
              <option value="all">All metrics</option>
              {METRIC_ORDER.map((k) => (
                <option key={k} value={k}>
                  {METRIC_DEFINITIONS[k].name}
                </option>
              ))}
            </select>
          </FilterRow>
        </div>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <FilterRow label="Evidence status">
            <div className="flex flex-wrap gap-1.5" role="group" aria-label="Evidence status filter">
              {FILTER_STATUSES.map((s) => (
                <button key={s} type="button" className="chip" aria-pressed={filters.statuses.includes(s)} onClick={() => toggleStatus(s)}>
                  {STATUS_META[s].label}
                </button>
              ))}
            </div>
          </FilterRow>
          <FilterRow label="View">
            <div role="radiogroup" aria-label="View" className="flex gap-1.5">
              {(["cards", "charts", "table"] as View[]).map((v) => (
                <button key={v} type="button" role="radio" aria-checked={view === v} className="chip capitalize" onClick={() => setView(v)}>
                  {v}
                </button>
              ))}
            </div>
          </FilterRow>
          <div className="flex flex-wrap gap-1.5">
            <button type="button" className="chip" aria-pressed={showCI} onClick={() => setShowCI((s) => !s)}>
              Confidence intervals
            </button>
            <button type="button" className="chip" aria-pressed={showTargets} onClick={() => setShowTargets((s) => !s)}>
              Targets
            </button>
            <button type="button" className="chip" aria-pressed={explain} onClick={() => setExplain((s) => !s)}>
              Explain this metric
            </button>
          </div>
        </div>
        <p role="status" aria-live="polite" className="text-xs text-subtle">
          {announcement}
        </p>
      </div>

      {explain && (
        <div className="mt-6 space-y-4">
          {(filters.metric === "all" ? groups.map(([k]) => k) : [filters.metric]).map((k) => (
            <MetricDefinitionPanel key={k} kind={k} />
          ))}
        </div>
      )}

      <div className="mt-8">
        {records.length === 0 ? (
          <p className="card p-6 text-muted">No curated results match these filters. Clear a filter to see more.</p>
        ) : view === "table" ? (
          <ResultsTable records={records} showCI={showCI} showTargets={showTargets} onOpen={open} />
        ) : (
          <div className="space-y-12">
            {groups.map(([kind, rs]) => (
              <section key={kind} aria-labelledby={`grp-${kind}`}>
                <h2 id={`grp-${kind}`} className="font-display text-2xl text-ink">
                  {METRIC_DEFINITIONS[kind].name}{" "}
                  <span className="text-base text-subtle">({METRIC_DEFINITIONS[kind].objective})</span>
                </h2>
                <div className="mt-4">
                  {view === "charts" ? (
                    <MetricChart kind={kind} records={rs} showIntervals={showCI} showTargets={showTargets} showInterpretation onSelect={open} />
                  ) : (
                    <ul className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                      {rs.map((r) => (
                        <li key={r.id}>
                          <ResearchMetricCard record={r} onOpen={open} showInterval={showCI} showTarget={showTargets} />
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>

      <div className="mt-10 flex flex-wrap items-center gap-3 border-t border-line pt-6">
        <span className="text-sm text-muted">Export the current approved summary ({records.length} rows, with caveats):</span>
        <button type="button" className="btn btn-ghost btn-sm" disabled={!records.length} onClick={() => download("pp-hfm-summary.csv", toCsv(records), "text/csv")}>
          <Download size={14} aria-hidden /> CSV
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={!records.length}
          onClick={() => download("pp-hfm-summary.json", toJson(records), "application/json")}
        >
          <Download size={14} aria-hidden /> JSON
        </button>
      </div>

      <ResultDetailDrawer record={detail} onClose={close} />
    </div>
  );
}

function FilterRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="text-[0.8125rem] font-semibold text-subtle" aria-hidden>
        {label}
      </span>
      {children}
    </div>
  );
}

export function ResultsTable({
  records,
  showCI = true,
  showTargets = true,
  onOpen,
}: {
  records: MetricRecord[];
  showCI?: boolean;
  showTargets?: boolean;
  onOpen?: (r: MetricRecord) => void;
}) {
  return (
    <div className="card overflow-x-auto">
      <table className="data-table min-w-[820px]">
        <caption className="sr-only">Curated results matching the current filters</caption>
        <thead>
          <tr>
            <th scope="col">Metric</th>
            <th scope="col">Dataset</th>
            <th scope="col" className="num">
              Result
            </th>
            {showCI && (
              <th scope="col" className="num">
                95% CI
              </th>
            )}
            {showTargets && <th scope="col">Target</th>}
            <th scope="col">Status</th>
            <th scope="col">Caveat</th>
            {onOpen && <th scope="col"><span className="sr-only">Details</span></th>}
          </tr>
        </thead>
        <tbody>
          {records.map((r) => (
            <tr key={r.id}>
              <th scope="row" className="font-medium normal-case tracking-normal text-[0.92rem] text-ink">
                {METRIC_DEFINITIONS[r.kind].name}
              </th>
              <td className="text-muted">
                {r.dataset}
                {r.variant && <span className="block text-xs text-subtle">{r.variant}</span>}
              </td>
              <td className="num tnum text-ink">{formatValue(r)}</td>
              {showCI && <td className="num tnum text-muted">{r.confidenceInterval ? formatInterval(r.confidenceInterval, r.decimals) : "—"}</td>}
              {showTargets && <td className="tnum text-muted">{r.target ? formatTarget(r.target, r.kind) : "—"}</td>}
              <td>
                <EvidenceStatusLabel status={r.evidenceStatus} size="sm" />
              </td>
              <td className="max-w-xs text-xs text-caution/90">{r.caveat.split(". ")[0]!.replace(/\.$/, "")}.</td>
              {onOpen && (
                <td>
                  <button type="button" className="text-sm font-medium text-accent hover:underline" onClick={() => onOpen(r)}>
                    Details<span className="sr-only">: {METRIC_DEFINITIONS[r.kind].name}, {r.dataset}{r.variant ? `, ${r.variant}` : ""}</span>
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
