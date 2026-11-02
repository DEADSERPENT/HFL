import type { Metadata } from "next";
import { PageHeader, Section } from "@/components/layout/Page";
import { DatasetComparison, DatasetExplorer } from "@/components/content/DatasetExplorer";
import { LimitationsCallout } from "@/components/content/LimitationsCallout";
import { pageMeta } from "@/content/site";

const meta = pageMeta("/datasets/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

export default function DatasetsPage() {
  return (
    <>
      <PageHeader
        eyebrow="System"
        title="Evaluation datasets"
        lead="Three corpora cover the two regimes that matter for the mechanism: clients holding many individuals (VitalDB, eICU) and a client holding one (WEAR). Descriptions are aggregate only."
      />
      <div className="container-site">
        <Section id="explorer" title="Dataset explorer">
          <DatasetExplorer />
        </Section>
        <Section id="compare" title="Compare across datasets" intro={<p>Pick a metric to compare datasets on one axis. Incompatible units are never mixed on one axis.</p>}>
          <DatasetComparison />
        </Section>
        <Section id="rules" title="What is never shown here">
          <LimitationsCallout title="Public content rules" tone="scope">
            No patient records, individual time series, medical images, row-level features, identifiers or sample payloads; no restricted extracts or downloadable intermediate data; no per-hospital counts. eICU access is governed by the provider&apos;s terms and data-use agreement, and this site grants access to no dataset.
          </LimitationsCallout>
        </Section>
      </div>
    </>
  );
}
