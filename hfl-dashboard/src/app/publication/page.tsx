import type { Metadata } from "next";
import { PageHeader, Section } from "@/components/layout/Page";
import { CitationPanel } from "@/components/content/CitationPanel";
import { PUBLICATION } from "@/content/publication";
import { pageMeta } from "@/content/site";

const meta = pageMeta("/publication/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

export default function PublicationPage() {
  const p = PUBLICATION;
  return (
    <>
      <PageHeader eyebrow="About" title={p.title} lead={<span>Status: {p.status}. Publication details are not yet finalized.</span>} />
      <div className="container-site">
        <Section id="abstract" title="Abstract for public readers">
          <div className="prose-site text-[1.05rem]">
            {p.publicAbstract.map((x) => (
              <p key={x.slice(0, 24)}>{x}</p>
            ))}
          </div>
        </Section>
        <Section id="keywords" title="Keywords">
          <ul className="flex flex-wrap gap-2">
            {p.keywords.map((k) => (
              <li key={k} className="rounded-full border border-line px-3 py-1 text-sm text-muted">
                {k}
              </li>
            ))}
          </ul>
        </Section>
        <Section id="citation" title="Status and citation">
          <CitationPanel />
          {p.approvedLinks.length === 0 && <p className="mt-4 text-sm text-subtle">No public links or supplementary materials have been approved yet.</p>}
        </Section>
        <Section id="data-and-privacy" title="Data and privacy statement" intro={<p>{p.dataAccess}</p>} />
        <Section id="code" title="Code availability" intro={<p>{p.codeAvailability}</p>} />
      </div>
    </>
  );
}
