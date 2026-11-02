"use client";

import { useId, useState } from "react";
import { METRICS } from "@/content/metrics";
import { ACCOUNTING_EXPLANATION } from "@/content/privacy";
import { formatDelta, formatNumber } from "@/lib/format";
import { DATASETS, type DatasetId } from "@/lib/types";
import { DatasetSelector } from "@/components/content/DatasetSelector";

const SCALE_MAX = 1.2;

const DEFS = {
  training:
    "Training budget: the ε of every private training step, composed across all rounds and tiers by the privacy-loss-distribution accountant.",
  conformal:
    "Conformal calibration budget: the ε of one evaluated, non-deployed release of a private calibration threshold (exponential mechanism over ranks).",
  total: "Total reported budget: training + conformal, at the stated δ.",
  target: "Target: total ε ≤ 1.",
};

/**
 * Stacked budget bar per dataset. Values come from curated records; nothing is
 * recomputed in the browser, and there is no slider pretending to recompute a guarantee.
 */
export function PrivacyBudgetStack({ compact = false }: { compact?: boolean }) {
  const [dataset, setDataset] = useState<DatasetId>("VitalDB");
  const [focus, setFocus] = useState<keyof typeof DEFS | null>(null);
  const [explain, setExplain] = useState(false);
  const id = useId();
  const rec = METRICS.find((m) => m.kind === "privacy" && m.dataset === dataset)!;
  const p = rec.privacy!;
  const w = (v: number) => `${((v / SCALE_MAX) * 100).toFixed(2)}%`;

  return (
    <div className="clay p-5 md:p-7">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-medium text-ink">Privacy budget composition</h3>
        <DatasetSelector value={dataset} onChange={(d) => d !== "all" && setDataset(d)} label="Dataset for privacy budget" />
      </div>

      <p className="mt-2 text-sm text-muted" aria-live="polite">
        {dataset}: training ε = {formatNumber(p.training, 3)} + conformal ε = {formatNumber(p.conformal, 3)} = total ε ={" "}
        {formatNumber(rec.value, 3)}, δ = {formatDelta(p.delta)}; {p.unit}-level guarantee. Target ε ≤ 1.
      </p>

      <div className="relative mt-6 h-12" role="group" aria-label="Budget bar. Focus a segment for its definition.">
        <div className="inset-well absolute inset-0 !rounded-full" />
        <div className="absolute inset-y-[5px] left-[5px] flex overflow-hidden rounded-full">
          <button
            type="button"
            className="bar-grow h-full bg-sage text-left text-xs font-semibold text-white focus-visible:outline-offset-[-3px]"
            style={{ width: w(p.training), minWidth: 0 }}
            onMouseEnter={() => setFocus("training")}
            onFocus={() => setFocus("training")}
            aria-describedby={`${id}-def`}
            aria-label={`Training budget ε = ${formatNumber(p.training, 3)}`}
          >
            <span className="px-3">Training {formatNumber(p.training, 3)}</span>
          </button>
          <button
            type="button"
            className="bar-grow h-full bg-[repeating-linear-gradient(135deg,var(--color-accent)_0_6px,#ffa58c_6px_11px)] text-xs font-semibold text-white focus-visible:outline-offset-[-3px]"
            style={{ width: `calc(${w(p.conformal)})` }}
            onMouseEnter={() => setFocus("conformal")}
            onFocus={() => setFocus("conformal")}
            aria-describedby={`${id}-def`}
            aria-label={`Conformal calibration budget ε = ${formatNumber(p.conformal, 3)}`}
          >
            <span className="sr-only">Conformal</span>
          </button>
        </div>
        <span aria-hidden className="absolute -bottom-2 -top-2 border-l-2 border-dashed border-caution" style={{ left: w(1) }} />
      </div>
      <div aria-hidden className="relative mt-3 h-5 text-[0.7rem] text-subtle">
        {[0, 0.2, 0.4, 0.6, 0.8, 1, 1.2].map((t) => (
          <span key={t} className="tnum absolute -translate-x-1/2" style={{ left: w(t) }}>
            {t.toFixed(1)}
          </span>
        ))}
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
        <li className="flex items-center gap-2">
          <span aria-hidden className="h-2.5 w-4 rounded-sm bg-sage" /> Training ε
        </li>
        <li className="flex items-center gap-2">
          <span aria-hidden className="h-2.5 w-4 rounded-sm bg-[repeating-linear-gradient(135deg,var(--color-accent)_0_3px,#ffa58c_3px_6px)]" /> Conformal ε
        </li>
        <li className="flex items-center gap-2">
          <span aria-hidden className="h-3 border-l-2 border-dashed border-caution" /> Target ε ≤ 1
        </li>
      </ul>

      <p id={`${id}-def`} className="mt-4 min-h-[3rem] rounded-md border border-line bg-surface/60 px-3 py-2 text-sm text-muted" aria-live="polite">
        {focus ? DEFS[focus] : "Hover or focus a segment for its definition."}
      </p>

      {!compact && (
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
          {DATASETS.map((d) => {
            const r = METRICS.find((m) => m.kind === "privacy" && m.dataset === d)!;
            return (
              <div key={d} className={`rounded-md border p-3 ${d === dataset ? "border-accent/50" : "border-line"}`}>
                <dt className="text-[0.8125rem] font-semibold text-subtle">{d}</dt>
                <dd className="tnum mt-1 text-ink">
                  {formatNumber(r.privacy!.training, 3)} + {formatNumber(r.privacy!.conformal, 3)} = {formatNumber(r.value, 3)}
                </dd>
              </div>
            );
          })}
        </dl>
      )}

      <button type="button" className="btn btn-ghost btn-sm mt-5" aria-expanded={explain} aria-controls={`${id}-acc`} onClick={() => setExplain((e) => !e)}>
        {explain ? "Hide the accounting" : "Explain the accounting"}
      </button>
      <div id={`${id}-acc`} hidden={!explain} className="mt-4 space-y-3 text-sm leading-relaxed text-muted">
        <p>
          <span className="font-medium text-ink">Adjacency. </span>
          {ACCOUNTING_EXPLANATION.adjacency}
        </p>
        <p className="rounded-md border border-line bg-bg-elevated px-3 py-2 font-mono text-[0.85rem] text-ink">{ACCOUNTING_EXPLANATION.guarantee}</p>
        <p>
          <span className="font-medium text-ink">Composition. </span>
          {ACCOUNTING_EXPLANATION.composition}
        </p>
        <p>
          <span className="font-medium text-ink">Across hospitals. </span>
          {ACCOUNTING_EXPLANATION.parallel}
        </p>
        <div>
          <p className="font-medium text-ink">What the budget does not guarantee</p>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {ACCOUNTING_EXPLANATION.doesNot.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        </div>
        <p className="text-caution">{rec.caveat}</p>
      </div>
    </div>
  );
}
