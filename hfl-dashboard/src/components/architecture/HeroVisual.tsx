"use client";

import { useCallback, useState } from "react";
import { Image as ImageIcon, Pause, Play } from "lucide-react";
import { useMotion } from "@/components/motion/MotionPreference";
import { ArchitectureCanvas3D } from "./ArchitectureCanvas3D";
import { ArchitectureDiagram2D } from "./ArchitectureDiagram2D";

/** The hero's clay diorama: the device, edge and cloud tiers as a conceptual model. */
export function HeroVisual() {
  const { reduced, paused, setPaused } = useMotion();
  const [staticView, setStaticView] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const onUnavailable = useCallback(() => setUnavailable(true), []);
  const show3d = !staticView && !unavailable;

  return (
    <figure className="relative">
      <div className="clay-stage relative aspect-[5/4] w-full overflow-hidden lg:aspect-auto lg:h-[600px] lg:w-[calc(100%+max(0px,(100vw-var(--content-width))/2)+3.5rem)] lg:rounded-r-none">
        {show3d ? (
          <ArchitectureCanvas3D
            className="absolute inset-0"
            label="Conceptual clay model: patient-side devices at the bottom send updates to two edge aggregators, which report to one cloud aggregator at the top"
            onUnavailable={onUnavailable}
            edges={2}
            highlightLayer={null}
            showFlow
            showPrivacy
            showCompression={false}
            showEdgeAggregation
            playing={!reduced}
            direction="up"
            interactive={false}
            assemble
          />
        ) : (
          <div className="absolute inset-0 flex items-center p-6">
            <ArchitectureDiagram2D edges={2} highlightLayer={null} showFlow showPrivacy showCompression={false} showEdgeAggregation direction="up" />
          </div>
        )}
        {show3d && (
          <ul aria-hidden className="pointer-events-none absolute left-6 top-6 hidden space-y-1.5 text-sm text-muted md:block">
            <li className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#8fa6c2]" />
              Cloud aggregator
            </li>
            <li className="flex items-center gap-2">
              <span className="h-2.5 w-3.5 rounded-full bg-[#93b78c]" />
              Edge aggregators
            </li>
            <li className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#ff7a5c]" />
              Client devices, inside the privacy boundary
            </li>
          </ul>
        )}
      </div>
      <figcaption className="mt-4 flex flex-col gap-3 text-sm text-subtle sm:flex-row sm:items-center sm:justify-between">
        <span className="max-w-[44ch]">
          <span className="md:hidden">Coral pebbles are client devices inside the privacy boundary, green discs are edge aggregators and the blue sphere is the cloud. </span>
          A conceptual model. The moving beads are neutral signals, not patient data or a live network trace.
        </span>
        <span className="flex shrink-0 gap-2">
        {show3d && (
          <button type="button" className="btn btn-ghost btn-sm" aria-pressed={paused} onClick={() => setPaused(!paused)}>
            {paused ? <Play size={13} aria-hidden /> : <Pause size={13} aria-hidden />}
            {paused ? "Resume motion" : "Pause motion"}
          </button>
        )}
        {!unavailable && (
          <button type="button" className="btn btn-ghost btn-sm" aria-pressed={staticView} onClick={() => setStaticView((s) => !s)}>
            <ImageIcon size={13} aria-hidden />
            {staticView ? "Use 3D view" : "Use static view"}
          </button>
        )}
        </span>
      </figcaption>
    </figure>
  );
}
