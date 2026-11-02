import type { Metadata } from "next";
import Link from "next/link";
import { PageHeader } from "@/components/layout/Page";
import { LIMITATIONS } from "@/content/limitations";
import { pageMeta } from "@/content/site";
import { AlertTriangle, Info } from "lucide-react";

const meta = pageMeta("/limitations/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

export default function LimitationsPage() {
  const unresolved = LIMITATIONS.filter((l) => l.severity === "unresolved");
  const scope = LIMITATIONS.filter((l) => l.severity === "scope");
  return (
    <>
      <PageHeader
        eyebrow="Methods"
        title="Limitations"
        lead="What is unresolved, what is simulated, and what the evidence does not show. These are part of the result, not a footnote."
      />
      <div className="container-site py-12">
        <section aria-labelledby="unresolved">
          <h2 id="unresolved" className="font-display flex items-center gap-3 text-3xl text-ink">
            <AlertTriangle aria-hidden className="text-caution" /> Unresolved or missed targets
          </h2>
          <ul className="mt-6 grid gap-4 md:grid-cols-2">
            {unresolved.map((l) => (
              <li key={l.id} id={l.id} className="card scroll-mt-24 border-caution/40 p-6">
                <h3 className="text-lg font-medium text-ink">{l.title}</h3>
                <p className="mt-2 leading-relaxed text-muted">{l.body}</p>
                {l.relatedMetric && (
                  <Link href={`/results/?detail=${l.relatedMetric}`} className="mt-3 inline-block text-sm font-medium text-accent hover:underline">
                    See the result
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </section>
        <section aria-labelledby="scope" className="mt-16">
          <h2 id="scope" className="font-display flex items-center gap-3 text-3xl text-ink">
            <Info aria-hidden className="text-model" /> Scope and interpretation
          </h2>
          <ul className="mt-6 grid gap-4 md:grid-cols-2">
            {scope.map((l) => (
              <li key={l.id} id={l.id} className="card scroll-mt-24 p-6">
                <h3 className="text-lg font-medium text-ink">{l.title}</h3>
                <p className="mt-2 leading-relaxed text-muted">{l.body}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
