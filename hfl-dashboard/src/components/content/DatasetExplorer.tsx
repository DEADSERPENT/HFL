"use client";

import { useEffect, useState } from "react";
import { DATASETS, datasetById } from "@/content/datasets";
import { METRICS, METRIC_DEFINITIONS, METRIC_ORDER } from "@/content/metrics";
import { formatInterval, formatValue } from "@/lib/format";
import { DATASETS as DATASET_IDS, type DatasetId, type MetricKind, type MetricRecord } from "@/lib/types";
import { Tabs } from "./Tabs";
import { EvidenceStatusLabel } from "@/components/metrics/EvidenceStatusLabel";
import { MetricChart } from "@/components/charts/MetricChart";
import { ResultDetailDrawer } from "@/components/metrics/ResultDetailDrawer";

export function DatasetExplorer() {
  const [active, setActive] = useState<DatasetId>("VitalDB");
  const [detail, setDetail] = useState<MetricRecord | null>(null);

  useEffect(() => {
    const d = new URLSearchParams(window.location.search).get("dataset");
    if (d && (DATASET_IDS as readonly string[]).includes(d)) setActive(d as DatasetId);
  }, []);

  const d = datasetById(active);
  const rows = METRIC_ORDER.flatMap((k) => METRICS.filter((m) => m.dataset === active && m.kind === k));

  return (
    <div>
      <Tabs items={DATASETS.map((x) => ({ id: x.id, label: x.name }))} value={active} onChange={setActive} label="Evaluation dataset">
        <div key={active} className="chart-animate grid gap-6 lg:grid-cols-[1fr_1.15fr]">
          <div className="card p-6">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-display text-3xl text-ink">{d.name}</h3>
              <span className={`rounded-full border px-2 py-0.5 text-xs ${d.accessKind === "credentialed" ? "border-caution/50 text-caution" : "border-line-strong text-muted"}`}>
                {d.accessKind === "credentialed" ? "Credentialed access" : "Public research data"}
              </span>
              <span className="rounded-full border border-line-strong px-2 py-0.5 text-xs text-muted">{d.clinical ? "Clinical" : "Non-clinical"}</span>
            </div>
            <p className="mt-1 text-subtle">{d.tagline}</p>
            <dl className="mt-6 space-y-4 text-[0.95rem]">
              <Item term="Evaluation role">{d.role}</Item>
              <Item term="Modalities">
                <ul className="list-disc space-y-1 pl-5">
                  {d.modality.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </Item>
              <Item term="Task">{d.task}</Item>
              <Item term="Clients">{d.clients}</Item>
              <Item term="Split and partitioning">{d.partitioning}</Item>
              <Item term="Privacy unit">{d.privacyUnit}</Item>
              <Item term="Access and licensing">{d.access}</Item>
              <Item term="Dataset-specific limitations">
                <ul className="list-disc space-y-1 pl-5 text-caution/90">
                  {d.limitations.map((l) => (
                    <li key={l}>{l}</li>
                  ))}
                </ul>
              </Item>
            </dl>
          </div>
          <div className="card overflow-x-auto p-2 md:p-4">
            <table className="data-table">
              <caption className="px-3 pb-3 pt-2 text-left text-sm font-medium text-ink">{d.name}: all curated results</caption>
              <thead>
                <tr>
                  <th scope="col">Metric</th>
                  <th scope="col" className="num">
                    Result
                  </th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <th scope="row" className="normal-case tracking-normal text-[0.9rem] font-normal text-muted">
                      <button type="button" className="text-left text-ink hover:text-accent hover:underline" onClick={() => setDetail(r)}>
                        {METRIC_DEFINITIONS[r.kind].name}
                      </button>
                      {r.variant && <span className="block text-xs text-subtle">{r.variant}</span>}
                      {r.kind === "energy" && <span className="block text-xs text-model">CloudSim Plus estimate</span>}
                    </th>
                    <td className="num tnum text-ink">
                      {formatValue(r)}
                      {r.confidenceInterval && <span className="block text-xs text-subtle">{formatInterval(r.confidenceInterval, r.decimals)}</span>}
                    </td>
                    <td>
                      <EvidenceStatusLabel status={r.evidenceStatus} size="sm" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Tabs>
      <ResultDetailDrawer record={detail} onClose={() => setDetail(null)} />
    </div>
  );
}

function Item({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-[0.8125rem] font-semibold text-subtle">{term}</dt>
      <dd className="mt-1 leading-relaxed text-muted">{children}</dd>
    </div>
  );
}

const COMPARE: { kind: MetricKind; label: string }[] = [
  { kind: "communication", label: "Communication" },
  { kind: "utility", label: "Utility" },
  { kind: "inference-latency", label: "Latency" },
  { kind: "energy", label: "Energy" },
  { kind: "update-delivery", label: "Update delivery" },
  { kind: "privacy", label: "Privacy budget" },
];

export function DatasetComparison() {
  const [kind, setKind] = useState<MetricKind>("communication");
  const [selected, setSelected] = useState<DatasetId[]>([...DATASET_IDS]);
  const [targets, setTargets] = useState(true);
  const [intervals, setIntervals] = useState(true);
  const [interp, setInterp] = useState(false);
  const [detail, setDetail] = useState<MetricRecord | null>(null);
  const records = METRICS.filter((m) => m.kind === kind && selected.includes(m.dataset));
  const hasCI = records.some((r) => r.confidenceInterval);

  return (
    <div>
      <div className="clay flex flex-wrap items-center gap-x-6 gap-y-3 p-4">
        <div role="radiogroup" aria-label="Metric" className="flex flex-wrap gap-1.5">
          {COMPARE.map((c) => (
            <button key={c.kind} type="button" role="radio" aria-checked={kind === c.kind} className="chip" onClick={() => setKind(c.kind)}>
              {c.label}
            </button>
          ))}
        </div>
        <div role="group" aria-label="Datasets to compare" className="flex flex-wrap gap-1.5">
          {DATASET_IDS.map((d) => (
            <button
              key={d}
              type="button"
              className="chip"
              aria-pressed={selected.includes(d)}
              onClick={() => setSelected((s) => (s.includes(d) ? s.filter((x) => x !== d) : [...s, d]))}
            >
              {d}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-1.5">
          <button type="button" className="chip" aria-pressed={targets} onClick={() => setTargets((t) => !t)}>
            Target line
          </button>
          <button
            type="button"
            className="chip"
            aria-pressed={intervals && hasCI}
            disabled={!hasCI}
            onClick={() => setIntervals((t) => !t)}
            title={hasCI ? undefined : "No intervals are reported for this metric"}
          >
            Confidence intervals
          </button>
          <button type="button" className="chip" aria-pressed={interp} onClick={() => setInterp((t) => !t)}>
            Show interpretation
          </button>
        </div>
      </div>
      <div className="mt-5" aria-live="polite">
        {records.length ? (
          <MetricChart kind={kind} records={records} showTargets={targets} showIntervals={intervals} showInterpretation={interp} onSelect={(r) => setDetail(r)} />
        ) : (
          <p className="card p-6 text-muted">Select at least one dataset.</p>
        )}
      </div>
      <ResultDetailDrawer record={detail} onClose={() => setDetail(null)} />
    </div>
  );
}
