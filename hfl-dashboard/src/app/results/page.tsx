import type { Metadata } from "next";
import { PageHeader } from "@/components/layout/Page";
import { ResultsExplorer } from "@/components/content/ResultsExplorer";
import { StatusLegend } from "@/components/metrics/EvidenceStatusLabel";
import { pageMeta } from "@/content/site";
import { PROVENANCE, REVIEWED_AT } from "@/content/metrics";

const meta = pageMeta("/results/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

export default function ResultsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Evidence"
        title="Results explorer"
        lead="Every curated result with its unit, evaluation setting, interval, target, evidence status and caveat. Filters update the charts, tables and summaries together."
      >
        <p className="text-sm text-subtle">
          {PROVENANCE} Last reviewed <time dateTime={REVIEWED_AT}>{REVIEWED_AT}</time>.
        </p>
      </PageHeader>
      <div className="container-site py-10">
        <ResultsExplorer />
        <section aria-labelledby="legend-title" className="mt-16">
          <h2 id="legend-title" className="font-display text-2xl text-ink">
            Evidence labels
          </h2>
          <p className="mt-2 text-sm text-muted">Each label has its own icon, outline and text, so status never depends on colour alone.</p>
          <div className="mt-5">
            <StatusLegend />
          </div>
        </section>
      </div>
    </>
  );
}
