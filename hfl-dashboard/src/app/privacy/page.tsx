import type { Metadata } from "next";
import Link from "next/link";
import { LongformLayout, PageHeader, Section } from "@/components/layout/Page";
import { PrivacyBudgetStack } from "@/components/privacy/PrivacyBudgetStack";
import { MiaChart } from "@/components/privacy/MiaChart";
import { MetricChart } from "@/components/charts/MetricChart";
import { LimitationsCallout } from "@/components/content/LimitationsCallout";
import { ACCOUNTING_EXPLANATION, MECHANISM_STEPS, MIA_AUDIT, THREAT_MODEL } from "@/content/privacy";
import { METRICS } from "@/content/metrics";
import { pageMeta } from "@/content/site";

const meta = pageMeta("/privacy/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

const SECTIONS = [
  { id: "goal", label: "Privacy goal" },
  { id: "unit", label: "Unit and adjacency" },
  { id: "mechanism", label: "Mechanism overview" },
  { id: "clipping", label: "Clipping and noise" },
  { id: "accounting", label: "Accounting and budgets" },
  { id: "utility", label: "Utility trade-off" },
  { id: "audit", label: "Membership-inference audit" },
  { id: "threat", label: "Threat model" },
  { id: "limits", label: "Limitations" },
];

export default function PrivacyPage() {
  const utility = METRICS.filter((m) => m.kind === "utility");
  return (
    <>
      <PageHeader
        eyebrow="Privacy laboratory"
        title="A bounded guarantee, stated precisely"
        lead="Privacy here is a defined mechanism with an accounting claim under stated assumptions. It is not a promise that every attack is impossible."
      />
      <LongformLayout sections={SECTIONS}>
        <Section
          id="goal"
          title="Privacy goal"
          intro={<p>Bound how much the training transcript, every message sent between tiers and the released model, can depend on any one patient, at a total budget of ε ≤ 1 with δ = 10⁻⁵.</p>}
        />
        <Section id="unit" title="Unit of privacy and adjacency definition" intro={<p>{ACCOUNTING_EXPLANATION.adjacency}</p>} />
        <Section id="mechanism" title="Mechanism overview" intro={<p>Applied inside every client, before anything leaves it.</p>}>
          <ol className="grid gap-3 md:grid-cols-5">
            {MECHANISM_STEPS.map((s, i) => (
              <li key={s.id} className="card p-4">
                <span className="tnum text-xs text-subtle">Step {i + 1}</span>
                <h3 className="mt-1 font-medium text-ink">{s.title}</h3>
              </li>
            ))}
          </ol>
        </Section>
        <Section id="clipping" title="Clipping and noise">
          <dl className="grid gap-4 md:grid-cols-2">
            {MECHANISM_STEPS.map((s) => (
              <div key={s.id} className="card p-5">
                <dt className="font-medium text-ink">{s.title}</dt>
                <dd className="mt-1 text-sm leading-relaxed text-muted">{s.body}</dd>
              </div>
            ))}
          </dl>
        </Section>
        <Section id="accounting" title="Accounting and budget composition" intro={<p>{ACCOUNTING_EXPLANATION.composition}</p>}>
          <PrivacyBudgetStack />
        </Section>
        <Section id="utility" title="Utility trade-off" intro={<p>The paired cost of privacy against an identical non-private system. A negative value means the private model scored higher in that evaluation.</p>}>
          <MetricChart kind="utility" records={utility} showInterpretation />
          <p className="mt-4 text-sm text-muted">
            Full definitions and caveats are in the{" "}
            <Link href="/results/?metric=utility" className="text-accent hover:underline">
              results explorer
            </Link>
            .
          </p>
        </Section>
        <Section id="audit" title="Membership-inference audit" intro={<p>{MIA_AUDIT.attack}</p>}>
          <MiaChart />
          <ul className="mt-5 grid gap-2 text-sm text-muted">
            {MIA_AUDIT.interpretation.map((x) => (
              <li key={x} className="flex gap-3">
                <span aria-hidden className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-caution" />
                {x}
              </li>
            ))}
          </ul>
          <p className="prose-site mt-4 text-sm">{MIA_AUDIT.caveat}</p>
          <p className="mt-3 text-xs text-subtle">Other audit arms used different setups and are not ranked against this result here.</p>
        </Section>
        <Section id="threat" title="Threat model and assumptions">
          <dl className="grid gap-4">
            <div className="card p-5">
              <dt className="font-medium text-ink">Protected unit</dt>
              <dd className="mt-1 text-sm text-muted">{THREAT_MODEL.protectedUnit}</dd>
            </div>
            <div className="card p-5">
              <dt className="font-medium text-ink">Adversary scope</dt>
              <dd className="mt-1 text-sm text-muted">{THREAT_MODEL.adversary}</dd>
            </div>
            <div className="card p-5">
              <dt className="font-medium text-ink">Trusted components and assumptions</dt>
              <dd className="mt-1">
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
                  {THREAT_MODEL.trusted.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              </dd>
            </div>
            <div className="card border-caution/30 p-5">
              <dt className="font-medium text-ink">Potential leakage channels outside the mechanism</dt>
              <dd className="mt-1">
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
                  {THREAT_MODEL.outside.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
                <p className="mt-2 text-sm text-caution">Model outputs, metadata, repeated participation, preprocessing and deployment operations each need separate scrutiny.</p>
              </dd>
            </div>
          </dl>
        </Section>
        <Section id="limits" title="Limitations">
          <div className="grid gap-3">
            {ACCOUNTING_EXPLANATION.doesNot.map((x) => (
              <LimitationsCallout key={x} title="Outside the guarantee" tone="scope">
                {x}
              </LimitationsCallout>
            ))}
          </div>
        </Section>
      </LongformLayout>
    </>
  );
}
