import type { Metadata } from "next";
import Link from "next/link";
import { LongformLayout, PageHeader, Section } from "@/components/layout/Page";
import { ExperimentMatrix } from "@/components/content/ExperimentMatrix";
import { BASELINES, EXPERIMENT_FAMILIES, OBJECTIVES, SENSITIVITY, STATISTICS } from "@/content/experiments";
import { DATASETS } from "@/content/datasets";
import { EvidenceStatusLabel } from "@/components/metrics/EvidenceStatusLabel";
import { pageMeta } from "@/content/site";

const meta = pageMeta("/experiments/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

const SECTIONS = [
  { id: "objectives", label: "Evaluation objectives" },
  { id: "matrix", label: "Experiment matrix" },
  { id: "baselines", label: "Baselines" },
  { id: "data", label: "Datasets and partitioning" },
  { id: "families", label: "Experiment families" },
  { id: "sensitivity", label: "Sensitivity and ablation" },
  { id: "statistics", label: "Statistical reporting" },
];

export default function ExperimentsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Methods"
        title="Experiment design and evaluation protocol"
        lead="Seven prespecified objectives, evaluated on three corpora with paired seeds and an interval-based decision rule."
      >
        <nav aria-label="Methods pages" className="flex flex-wrap gap-2">
          <Link href="/reproducibility/" className="btn btn-ghost btn-sm">Reproducibility</Link>
          <Link href="/limitations/" className="btn btn-ghost btn-sm">Limitations</Link>
        </nav>
      </PageHeader>
      <LongformLayout sections={SECTIONS}>
        <Section id="objectives" title="Evaluation objectives">
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {OBJECTIVES.map((o) => (
              <li key={o.id} className="card p-4">
                <span className="tnum font-semibold text-accent">{o.id}</span>
                <p className="mt-1 font-medium text-ink">{o.title}</p>
                <p className="tnum mt-1 text-sm text-muted">Target {o.target}</p>
                {o.note && <p className="mt-1 text-xs text-subtle">{o.note}</p>}
              </li>
            ))}
          </ul>
        </Section>
        <Section id="matrix" title="Experiment matrix" intro={<p>Select a cell for the scope, metric definition and caveats of that result.</p>}>
          <ExperimentMatrix />
        </Section>
        <Section id="baselines" title="Baselines and comparison systems">
          <dl className="grid gap-3">
            {BASELINES.map((b) => (
              <div key={b.name} className="card p-5">
                <dt className="font-medium text-ink">{b.name}</dt>
                <dd className="mt-1 text-sm leading-relaxed text-muted">{b.role}</dd>
              </div>
            ))}
          </dl>
        </Section>
        <Section id="data" title="Datasets and partitioning">
          <ul className="grid gap-3 md:grid-cols-3">
            {DATASETS.map((d) => (
              <li key={d.id} className="card p-5">
                <p className="font-medium text-ink">{d.name}</p>
                <p className="mt-1 text-sm text-muted">{d.clients}</p>
                <p className="mt-2 text-sm text-muted">{d.partitioning}</p>
              </li>
            ))}
          </ul>
        </Section>
        <Section id="families" title="Experiment families">
          <ul className="grid gap-3 md:grid-cols-2">
            {EXPERIMENT_FAMILIES.map((f) => (
              <li key={f.id} className="card p-5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-medium text-ink">{f.title}</h3>
                  {f.basis === "mixed" ? (
                    <span className="flex gap-1.5">
                      <EvidenceStatusLabel status="measured" size="sm" />
                      <EvidenceStatusLabel status="modelled" size="sm" />
                    </span>
                  ) : (
                    <EvidenceStatusLabel status={f.basis} size="sm" />
                  )}
                </div>
                <p className="mt-2 text-sm leading-relaxed text-muted">{f.body}</p>
              </li>
            ))}
          </ul>
        </Section>
        <Section id="sensitivity" title="Sensitivity and ablation experiments">
          <ul className="grid gap-3 md:grid-cols-2">
            {SENSITIVITY.map((s) => (
              <li key={s.title} className="card p-5">
                <h3 className="font-medium text-ink">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
              </li>
            ))}
          </ul>
        </Section>
        <Section id="statistics" title="Statistical reporting">
          <p className="card inline-block px-4 py-3 font-mono text-ink">{STATISTICS.interval}</p>
          <ul className="mt-5 grid gap-2 text-muted">
            {STATISTICS.body.map((b) => (
              <li key={b} className="flex gap-3">
                <span aria-hidden className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                {b}
              </li>
            ))}
          </ul>
        </Section>
      </LongformLayout>
    </>
  );
}
