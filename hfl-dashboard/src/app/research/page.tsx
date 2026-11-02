import type { Metadata } from "next";
import { LongformLayout, PageHeader, Section } from "@/components/layout/Page";
import { LimitationsCallout } from "@/components/content/LimitationsCallout";
import { RESEARCH } from "@/content/research";
import { pageMeta } from "@/content/site";

const meta = pageMeta("/research/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

const SECTIONS = [
  { id: "problem", label: "Problem statement" },
  { id: "hierarchy", label: "Why hierarchical FL" },
  { id: "unit", label: "Patient vs record privacy" },
  { id: "multimodal", label: "Multimodal medical IoT" },
  { id: "questions", label: "Research questions" },
  { id: "contributions", label: "Contributions" },
  { id: "evaluation", label: "Evaluation overview" },
  { id: "scope", label: "Scope boundaries" },
];

export default function ResearchPage() {
  return (
    <>
      <PageHeader
        eyebrow="Research"
        title="Protecting patients, not just records"
        lead="Why the unit of privacy matters in hierarchical federated learning, what this work set out to test, and what it does not claim."
      />
      <LongformLayout sections={SECTIONS}>
        <Section id="problem" title="Problem statement" intro={<p>{RESEARCH.problem}</p>} />
        <Section id="hierarchy" title="Why hierarchical federated learning" intro={<p>{RESEARCH.whyHierarchy}</p>} />
        <Section id="unit" title="Why patient-level privacy differs from record-level privacy" intro={<p>{RESEARCH.patientVsRecord}</p>}>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="card p-5">
              <p className="font-medium text-ink">Record-level</p>
              <p className="mt-1 text-sm text-muted">Neighbouring datasets differ by one record. A patient with k records can shift the model up to k times the per-record bound.</p>
            </div>
            <div className="card border-sage/40 p-5">
              <p className="font-medium text-ink">Patient-level (PP-HFM)</p>
              <p className="mt-1 text-sm text-muted">Neighbouring datasets differ by all records of one patient. Each patient&apos;s gradients are summed before clipping, so the bound holds per patient.</p>
            </div>
          </div>
        </Section>
        <Section id="multimodal" title="Why multimodal medical IoT is challenging" intro={<p>{RESEARCH.multimodal}</p>} />
        <Section id="questions" title="Research questions">
          <ol className="grid gap-3">
            {RESEARCH.questions.map((q, i) => (
              <li key={q} className="card flex gap-4 p-5">
                <span className="tnum font-display text-2xl text-accent">RQ{i + 1}</span>
                <span className="text-muted">{q}</span>
              </li>
            ))}
          </ol>
        </Section>
        <Section id="contributions" title="Claimed contributions" intro={<p>Design and evaluation contributions, under stated assumptions; not universal proofs.</p>}>
          <ul className="grid gap-4 md:grid-cols-2">
            {RESEARCH.contributions.map((c) => (
              <li key={c.title} className="card p-5">
                <h3 className="font-medium text-ink">{c.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">{c.body}</p>
              </li>
            ))}
          </ul>
          <div className="mt-6">
            <LimitationsCallout title="What this work does not claim" tone="scope" href="/limitations/" linkLabel="Read the limitations">
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {RESEARCH.notClaimed.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </LimitationsCallout>
          </div>
        </Section>
        <Section
          id="evaluation"
          title="Evaluation overview"
          intro={
            <p>
              Seven objectives (O1&ndash;O4) are evaluated on three corpora against centralized training, the hierarchy alone and an identical non-private system. Each result on this site carries its own evidence label: measured, modelled, inconclusive or target not met.
            </p>
          }
        />
        <Section id="scope" title="Scope boundaries">
          <ul className="grid gap-2 text-muted">
            {RESEARCH.scope.map((s) => (
              <li key={s} className="flex gap-3">
                <span aria-hidden className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                {s}
              </li>
            ))}
          </ul>
        </Section>
      </LongformLayout>
    </>
  );
}
