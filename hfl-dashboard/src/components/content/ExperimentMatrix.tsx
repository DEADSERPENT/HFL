"use client";

import { useState } from "react";
import { OBJECTIVES } from "@/content/experiments";
import { METRICS } from "@/content/metrics";
import { formatValue } from "@/lib/format";
import { DATASETS, type MetricRecord } from "@/lib/types";
import { EvidenceStatusLabel } from "@/components/metrics/EvidenceStatusLabel";
import { ResultDetailDrawer } from "@/components/metrics/ResultDetailDrawer";

/** Objectives x datasets. Each cell opens the result's detail panel. */
export function ExperimentMatrix() {
  const [detail, setDetail] = useState<MetricRecord | null>(null);
  return (
    <div className="card overflow-x-auto">
      <table className="data-table min-w-[760px]">
        <caption className="sr-only">Experiment matrix: objectives by dataset. Select a cell for its scope, metric and caveats.</caption>
        <thead>
          <tr>
            <th scope="col">Objective</th>
            {DATASETS.map((d) => (
              <th key={d} scope="col">
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {OBJECTIVES.map((o) => (
            <tr key={o.id}>
              <th scope="row" className="normal-case tracking-normal text-[0.9rem]">
                <span className="tnum font-semibold text-accent">{o.id}</span> <span className="font-medium text-ink">{o.title}</span>
                <span className="block text-xs font-normal text-subtle">
                  Target {o.target}.{o.note ? ` ${o.note}` : ""}
                </span>
              </th>
              {DATASETS.map((d) => {
                const rs = METRICS.filter((m) => m.objective === o.id && m.dataset === d);
                return (
                  <td key={d}>
                    {rs.length === 0 ? (
                      <EvidenceStatusLabel status="not-evaluated" size="sm" />
                    ) : (
                      <ul className="space-y-2">
                        {rs.map((r) => (
                          <li key={r.id}>
                            <button
                              type="button"
                              onClick={() => setDetail(r)}
                              className="group w-full rounded-md border border-transparent p-1.5 text-left hover:border-line-strong focus-visible:border-line-strong"
                              aria-label={`${o.id} ${o.title}, ${d}${r.variant ? `, ${r.variant}` : ""}: ${formatValue(r)}. Open details.`}
                            >
                              <span className="tnum block font-medium text-ink">{formatValue(r)}</span>
                              {r.variant && <span className="block text-xs text-subtle">{r.variant}</span>}
                              <span className="mt-1 block">
                                <EvidenceStatusLabel status={r.evidenceStatus} size="sm" />
                              </span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <ResultDetailDrawer record={detail} onClose={() => setDetail(null)} />
    </div>
  );
}
