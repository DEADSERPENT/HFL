import type { Metadata } from "next";
import { PageHeader } from "@/components/layout/Page";
import { ArchitectureExplorer } from "@/components/architecture/ArchitectureExplorer";
import { LimitationsCallout } from "@/components/content/LimitationsCallout";
import { LAYERS } from "@/content/architecture";
import { pageMeta } from "@/content/site";

const meta = pageMeta("/architecture/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

export default function ArchitecturePage() {
  return (
    <>
      <PageHeader
        eyebrow="System"
        title="Device, edge, cloud"
        lead="Explore how a training round moves through the hierarchy and where the privacy boundary sits. Every control has a button or keyboard alternative, and the 2D diagram carries the same information."
      />
      <div className="container-site py-12">
        <ArchitectureExplorer />
        <section aria-labelledby="text-explainer" className="mt-14 grid gap-6 md:grid-cols-3">
          <h2 id="text-explainer" className="sr-only">
            Text description of the architecture
          </h2>
          {LAYERS.map((l) => (
            <div key={l.id} className="card p-5">
              <h3 className="font-medium text-ink">{l.name}</h3>
              <p className="mt-1 text-sm leading-relaxed text-muted">{l.detail}</p>
            </div>
          ))}
        </section>
        <div className="mt-6">
          <LimitationsCallout title="An explanatory model, not telemetry" tone="scope">
            The scene is a conceptual model. Node counts are schematic, particles are neutral signals rather than data, and the animation does not trace real packets. Measured and simulated results are on the results page.
          </LimitationsCallout>
        </div>
      </div>
    </>
  );
}
