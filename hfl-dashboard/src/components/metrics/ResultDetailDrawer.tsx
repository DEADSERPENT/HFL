"use client";

import Link from "next/link";
import { METRIC_DEFINITIONS } from "@/content/metrics";
import { formatInterval, formatTarget, formatValue } from "@/lib/format";
import { OUTCOME_LABEL, targetOutcomeOf } from "@/lib/metric-status";
import type { MetricRecord } from "@/lib/types";
import { Dialog } from "@/components/content/Dialog";
import { EvidenceStatusLabel } from "./EvidenceStatusLabel";

export function ResultDetailDrawer({ record, onClose }: { record: MetricRecord | null; onClose: () => void }) {
  const def = record ? METRIC_DEFINITIONS[record.kind] : null;
  return (
    <Dialog
      open={!!record}
      onClose={onClose}
      title={def ? def.name : ""}
      description={record ? `${record.dataset}${record.variant ? `, ${record.variant}` : ""}` : undefined}
    >
      {record && def && <ResultDetailBody record={record} />}
    </Dialog>
  );
}

export function ResultDetailBody({ record }: { record: MetricRecord }) {
  const def = METRIC_DEFINITIONS[record.kind];
  const outcome = targetOutcomeOf(record);
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <p className="tnum font-display text-5xl leading-none text-ink">{formatValue(record)}</p>
        <EvidenceStatusLabel status={record.evidenceStatus} withDescription />
      </div>

      <dl className="grid gap-4 text-sm">
        <Row term="Exact definition">{def.definition}</Row>
        <Row term="Unit">{record.unit}</Row>
        <Row term="Dataset and evaluation setting">
          {record.dataset}
          {record.variant ? ` (${record.variant})` : ""}. {record.evaluationContext}
        </Row>
        <Row term="Result">
          <span className="tnum">{formatValue(record)}</span>
        </Row>
        <Row term="Target">
          {record.target ? (
            <>
              <span className="tnum">{formatTarget(record.target, record.kind)}</span>
              {" — "}
              {OUTCOME_LABEL[outcome]}
              {record.confidenceInterval ? " (prespecified interval rule)" : ""}
            </>
          ) : (
            "No target."
          )}
        </Row>
        <Row term="Basis">{record.basis === "modelled" ? "Modelled (simulation or analytical model)" : "Measured in the described evaluation"}</Row>
        <Row term="Confidence interval">
          {record.confidenceInterval ? (
            <>
              <span className="tnum">{formatInterval(record.confidenceInterval, record.decimals)}</span> {record.confidenceInterval.unit};{" "}
              {record.confidenceInterval.method}.
            </>
          ) : (
            "Not reported for this result."
          )}
        </Row>
        <Row term="Baseline / comparator">{record.baseline ?? def.baseline}</Row>
        <Row term="Interpretation">{record.interpretation}</Row>
        <Row term="Caveat" tone="caveat">
          {record.caveat}
        </Row>
        <Row term="Provenance">{record.publicProvenanceLabel}</Row>
        {record.reviewedAt && (
          <Row term="Last reviewed">
            <time dateTime={record.reviewedAt}>
              {new Date(`${record.reviewedAt}T00:00:00Z`).toLocaleDateString("en-GB", {
                day: "numeric",
                month: "long",
                year: "numeric",
                timeZone: "UTC",
              })}
            </time>
          </Row>
        )}
      </dl>

      <p className="text-sm text-muted">
        See also the{" "}
        <Link href="/limitations/" className="text-accent underline-offset-2 hover:underline">
          limitations
        </Link>{" "}
        and{" "}
        <Link href="/reproducibility/" className="text-accent underline-offset-2 hover:underline">
          reproducibility notes
        </Link>
        .
      </p>
    </div>
  );
}

function Row({ term, children, tone }: { term: string; children: React.ReactNode; tone?: "caveat" }) {
  return (
    <div className={tone === "caveat" ? "rounded-md border border-caution/30 bg-caution/5 p-3" : undefined}>
      <dt className={`text-[0.8125rem] font-semibold ${tone === "caveat" ? "text-caution" : "text-subtle"}`}>{term}</dt>
      <dd className={`mt-1 leading-relaxed ${tone === "caveat" ? "text-ink/90" : "text-muted"}`}>{children}</dd>
    </div>
  );
}
