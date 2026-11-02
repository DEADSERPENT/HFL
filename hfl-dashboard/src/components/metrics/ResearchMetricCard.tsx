"use client";

import Link from "next/link";
import { METRIC_DEFINITIONS } from "@/content/metrics";
import { formatInterval, formatTarget, formatValue } from "@/lib/format";
import type { MetricRecord } from "@/lib/types";
import { EvidenceStatusLabel } from "./EvidenceStatusLabel";

/**
 * Shows metric, value, unit, dataset, status, target and caveat. The detail
 * action is either a button (opens the in-page drawer) or a link (deep-links
 * to the results explorer).
 */
export function ResearchMetricCard({
  record,
  onOpen,
  href,
  showInterval = true,
  showTarget = true,
  showInterpretation = true,
  compact = false,
}: {
  record: MetricRecord;
  onOpen?: (r: MetricRecord, trigger: HTMLElement) => void;
  href?: string;
  showInterval?: boolean;
  showTarget?: boolean;
  showInterpretation?: boolean;
  compact?: boolean;
}) {
  const def = METRIC_DEFINITIONS[record.kind];
  const titleId = `card-${record.id}-title`;
  return (
    <article aria-labelledby={titleId} className="card flex h-full flex-col p-5" data-metric={record.id}>
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[0.8125rem] font-semibold text-subtle">{record.dataset}</p>
          <h3 id={titleId} className="mt-1 text-[0.98rem] font-medium leading-snug text-ink">
            {def.name}
            {record.variant && <span className="block text-sm font-normal text-muted">{record.variant}</span>}
          </h3>
        </div>
        <EvidenceStatusLabel status={record.evidenceStatus} size="sm" />
      </header>

      <p className="tnum mt-4 font-display text-[2.4rem] leading-none text-ink">{formatValue(record)}</p>

      <dl className="mt-3 space-y-1 text-sm">
        {showInterval && record.confidenceInterval && (
          <div className="flex gap-2">
            <dt className="text-subtle">95% CI</dt>
            <dd className="tnum text-muted">{formatInterval(record.confidenceInterval, record.decimals)}</dd>
          </div>
        )}
        {showTarget && record.target && (
          <div className="flex gap-2">
            <dt className="text-subtle">Target</dt>
            <dd className="tnum text-muted">{formatTarget(record.target, record.kind)}</dd>
          </div>
        )}
        {!compact && (
          <div className="flex gap-2">
            <dt className="text-subtle">Basis</dt>
            <dd className="text-muted">{record.basis === "modelled" ? "Simulation / model" : "Measured in evaluation"}</dd>
          </div>
        )}
      </dl>

      {showInterpretation && <p className="mt-4 text-sm leading-relaxed text-muted">{record.interpretation}</p>}

      <p className="mt-3 border-l-2 border-caution/50 pl-3 text-[0.82rem] leading-relaxed text-caution/90">
        <span className="sr-only">Caveat: </span>
        {record.caveat.split(". ")[0]!.replace(/\.$/, "")}.
      </p>

      <div className="mt-auto pt-5">
        {onOpen ? (
          <button
            type="button"
            className="inline-flex min-h-10 items-center gap-1.5 text-sm font-medium text-accent hover:underline"
            onClick={(e) => onOpen(record, e.currentTarget)}
            aria-label={`Details: ${def.name}, ${record.dataset}${record.variant ? `, ${record.variant}` : ""}`}
          >
            Details and caveats
          </button>
        ) : href ? (
          <Link
            href={href}
            className="inline-flex min-h-10 items-center gap-1.5 text-sm font-medium text-accent hover:underline"
            aria-label={`Detailed result and limitations: ${def.name}, ${record.dataset}`}
          >
            Detailed result and limitations
          </Link>
        ) : null}
      </div>
    </article>
  );
}
