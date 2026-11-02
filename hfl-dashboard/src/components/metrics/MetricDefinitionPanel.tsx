import { METRIC_DEFINITIONS } from "@/content/metrics";
import type { MetricKind } from "@/lib/types";

export function MetricDefinitionPanel({ kind, headingLevel = 3 }: { kind: MetricKind; headingLevel?: 2 | 3 }) {
  const d = METRIC_DEFINITIONS[kind];
  const H = headingLevel === 2 ? "h2" : "h3";
  return (
    <section aria-label={`Definition: ${d.name}`} className="card p-5">
      <p className="eyebrow">Explain this metric</p>
      <H className="mt-2 text-lg font-medium text-ink">
        {d.name} <span className="text-sm font-normal text-subtle">({d.objective})</span>
      </H>
      <dl className="mt-4 grid gap-4 text-sm md:grid-cols-2">
        <Item term="Definition">{d.definition}</Item>
        <Item term="Unit">{d.unit === "points" ? "AUROC points (clinical) / accuracy percentage points (WEAR)" : d.unit}</Item>
        <Item term="Baseline / comparator">{d.baseline}</Item>
        <Item term="Evaluation context">{d.context}</Item>
        <Item term="Limitations" wide>
          {d.limitations}
        </Item>
      </dl>
    </section>
  );
}

function Item({ term, children, wide }: { term: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <div className={wide ? "md:col-span-2" : undefined}>
      <dt className="text-[0.8125rem] font-semibold text-subtle">{term}</dt>
      <dd className="mt-1 leading-relaxed text-muted">{children}</dd>
    </div>
  );
}
