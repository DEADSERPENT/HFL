import Link from "next/link";
import { Check, CircleHelp } from "lucide-react";
import { HeroVisual } from "@/components/architecture/HeroVisual";
import { SystemGlance } from "@/components/architecture/SystemGlance";
import { EvidenceLedger } from "@/components/metrics/EvidenceLedger";
import { PrivacyBudgetStack } from "@/components/privacy/PrivacyBudgetStack";
import { CitationPanel } from "@/components/content/CitationPanel";
import { DATASETS } from "@/content/datasets";
import { RESEARCH_QUESTION_CARDS } from "@/content/research";

const SUPPORTS = [
  "Strong uplink reductions in the reported evaluation.",
  "Low reported inference latency under the stated evaluation conditions.",
  "Modelled energy savings in the simulator.",
  "A person-level VitalDB rerun with a favourable utility result under the reported protocol.",
];

const UNRESOLVED = [
  "eICU privacy utility cost remains above the two-point point-estimate target, with the headline interval classified as inconclusive by the prespecified rule.",
  "eICU end-to-end AUROC cost is a clear miss against the target.",
  "eICU update delivery at two edge servers is below the >99% target.",
  "The eICU budget of ε = 0.9 applies to individuals at one hospital; for the 2.9% at several hospitals the composed bound reaches ε ≤ 2.08.",
  "Simulator estimates are not physical deployment measurements.",
  "Membership-inference audit results do not prove zero leakage.",
  "Clinical usefulness and production readiness have not been established by these experiments.",
];

const METHODS_LINKS = [
  { href: "/architecture/", title: "Architecture", body: "The device, edge and cloud tiers in 3D and 2D." },
  { href: "/privacy/", title: "Privacy laboratory", body: "The mechanism, its accounting boundary and the audit." },
  { href: "/experiments/", title: "Experiments", body: "Objectives, baselines and the evaluation matrix." },
  { href: "/reproducibility/", title: "Reproducibility", body: "Protocol, assumptions and a checklist." },
  { href: "/limitations/", title: "Limitations", body: "What is unresolved, simulated or out of scope." },
];

function H2({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="font-display t-36 max-w-[22ch] text-ink">
      {children}
    </h2>
  );
}

export default function HomePage() {
  return (
    <>
      {/* Hero: the one bold element on the page */}
      <section aria-labelledby="hero-title" className="overflow-x-clip">
        <div className="container-site grid items-center gap-x-12 gap-y-10 pb-20 pt-10 md:pt-16 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:pb-28">
          <div className="hero-in">
            <p className="eyebrow">Privacy-aware collaborative learning</p>
            <h1 id="hero-title" className="font-display t-72 mt-5 text-ink">
              Learning across the edge. Privacy at the patient level.
            </h1>
            <p className="mt-7 max-w-[58ch] text-[1.0625rem] leading-relaxed text-muted">
              PP-HFM explores a hierarchical federated learning design for multimodal medical IoT, combining device-level learning, edge
              coordination, cloud aggregation, and patient-level differential privacy. The Observatory presents its design, evaluation evidence,
              and limitations in an interactive format.
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-x-6 gap-y-3">
              <Link href="/architecture/" className="btn btn-primary">
                Explore the architecture
              </Link>
              <Link href="/results/" className="font-semibold text-ink underline decoration-coral decoration-2 underline-offset-[6px] hover:text-accent">
                Read the results
              </Link>
            </div>
          </div>
          <HeroVisual />
        </div>
      </section>

      <div className="container-site">
        {/* Research question */}
        <section aria-labelledby="rq-title" className="grid gap-10 border-t border-line py-20 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
          <H2 id="rq-title">Can hierarchical collaboration reduce communication and energy costs while maintaining a bounded privacy budget?</H2>
          <div>
            <dl className="grid gap-8 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              {RESEARCH_QUESTION_CARDS.map((c) => (
                <div key={c.title}>
                  <dt className="t-21 font-semibold text-ink">{c.title}</dt>
                  <dd className="mt-2 leading-relaxed text-muted">{c.body}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-10 max-w-[60ch] text-sm text-caution">This is a research evaluation, not a validated clinical system.</p>
          </div>
        </section>

        {/* System at a glance */}
        <section aria-labelledby="glance-title" className="border-t border-line py-20">
          <H2 id="glance-title">Three tiers, one privacy boundary</H2>
          <p className="mt-4 max-w-[60ch] text-muted">Choose a layer, or trace one update up the hierarchy and one model broadcast back down.</p>
          <div className="mt-10">
            <SystemGlance />
          </div>
        </section>

        {/* Evidence */}
        <section aria-labelledby="ev-title" className="border-t border-line py-20">
          <H2 id="ev-title">What the system results show</H2>
          <p className="mt-4 max-w-[62ch] text-muted">
            Each value says how it was obtained. Energy comes from a CloudSim Plus model, and round latency and update delivery from an ns-3
            simulation; none of them is a field measurement. Select a value for its definition and caveats.
          </p>
          <div className="mt-10">
            <EvidenceLedger />
          </div>
        </section>

        {/* Datasets */}
        <section aria-labelledby="ds-title" className="border-t border-line py-20">
          <H2 id="ds-title">Two clinical corpora and one wearable workload</H2>
          <ul className="mt-10 grid gap-10 md:grid-cols-3">
            {DATASETS.map((d) => (
              <li key={d.id}>
                <h3 className="font-display t-28 text-ink">
                  <Link href={`/datasets/?dataset=${d.id}`} className="underline-offset-4 hover:text-accent hover:underline">
                    {d.name}
                  </Link>
                </h3>
                <p className="mt-1 text-sm text-subtle">
                  {d.accessKind === "credentialed" ? "Credentialed access under a data-use agreement" : "Public research data"}
                </p>
                <p className="mt-4 leading-relaxed text-muted">{d.role}</p>
                <p className="mt-3 text-sm leading-relaxed text-muted">
                  <span className="font-semibold text-ink">Evaluated: </span>
                  {d.task}
                </p>
              </li>
            ))}
          </ul>
          <p className="mt-10 max-w-[62ch] text-sm text-subtle">
            No records, samples, images, time series or per-hospital statistics appear on this site.
          </p>
        </section>

        {/* Privacy in context */}
        <section aria-labelledby="pv-title" className="grid gap-12 border-t border-line py-20 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <div>
            <H2 id="pv-title">A bounded guarantee, not a promise that attacks are impossible</H2>
            <div className="prose-site mt-6">
              <p>
                Each reported budget is the training budget plus the budget of an evaluated conformal calibration release, at <strong>δ = 10⁻⁵</strong>.
              </p>
              <p>
                The guarantee depends on the stated adjacency definition (all records of one patient), the sampling and accounting assumptions, and
                the implemented mechanism. Epsilon alone does not capture every real-world risk.
              </p>
            </div>
            <Link href="/privacy/" className="mt-6 inline-block font-semibold text-ink underline decoration-coral decoration-2 underline-offset-[6px] hover:text-accent">
              Open the privacy laboratory
            </Link>
          </div>
          <PrivacyBudgetStack compact />
        </section>

        {/* Does / does not show */}
        <section aria-labelledby="dd-title" className="border-t border-line py-20">
          <H2 id="dd-title">What the evidence does and does not show</H2>
          <div className="mt-10 grid gap-12 md:grid-cols-2">
            <div>
              <h3 className="t-21 flex items-center gap-2 font-semibold text-ink">
                <Check size={20} aria-hidden className="text-sage" /> Evidence supports
              </h3>
              <ul className="mt-5 space-y-3 text-muted">
                {SUPPORTS.map((s) => (
                  <li key={s} className="border-l-2 border-sage/40 pl-4 leading-relaxed">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="t-21 flex items-center gap-2 font-semibold text-ink">
                <CircleHelp size={20} aria-hidden className="text-caution" /> Still unresolved
              </h3>
              <ul className="mt-5 space-y-3 text-muted">
                {UNRESOLVED.map((s) => (
                  <li key={s} className="border-l-2 border-caution/50 pl-4 leading-relaxed">
                    {s}
                  </li>
                ))}
              </ul>
              <Link href="/limitations/" className="mt-6 inline-block font-semibold text-ink underline decoration-caution decoration-2 underline-offset-[6px] hover:text-caution">
                Read all limitations
              </Link>
            </div>
          </div>
        </section>

        {/* Methods */}
        <section aria-labelledby="mp-title" className="border-t border-line py-20">
          <H2 id="mp-title">Read the method in depth</H2>
          <ul className="mt-8 divide-y divide-line border-y border-line">
            {METHODS_LINKS.map((l) => (
              <li key={l.href}>
                <Link href={l.href} className="group flex flex-wrap items-baseline justify-between gap-x-8 gap-y-1 py-5">
                  <span className="font-display t-28 text-ink group-hover:text-accent">{l.title}</span>
                  <span className="text-muted">{l.body}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        {/* Publication */}
        <section aria-labelledby="pub-title" className="border-t border-line py-20">
          <H2 id="pub-title">Publication</H2>
          <div className="mt-8 max-w-3xl">
            <CitationPanel />
          </div>
        </section>
      </div>
    </>
  );
}
