"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import { LAYERS, type LayerId } from "@/content/architecture";
import { ArchitectureDiagram2D } from "./ArchitectureDiagram2D";

const ORDER: LayerId[] = ["device", "edge", "cloud"];

export function SystemGlance() {
  const [layer, setLayer] = useState<LayerId | null>(null);
  const [direction, setDirection] = useState<"up" | "down">("up");
  const [tracing, setTracing] = useState(false);

  const stepThrough = () => {
    const seq = direction === "up" ? ORDER : [...ORDER].reverse();
    const i = layer ? seq.indexOf(layer) : -1;
    setLayer(seq[(i + 1) % seq.length]!);
    setTracing(true);
  };

  const explanation = tracing
    ? direction === "up"
      ? "Tracing an update: a client privatizes and compresses its update, its edge averages the group's updates over several edge rounds, and the cloud averages the edges."
      : "Tracing a model broadcast: the cloud sends the global model to every edge, and each edge passes it to its clients for the next round."
    : "Select a layer to highlight it, or trace an update or a model broadcast.";

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
      <div>
        <ul className="grid gap-3">
          {LAYERS.map((l) => (
            <li key={l.id}>
              <button
                type="button"
                aria-pressed={layer === l.id}
                onClick={() => setLayer(layer === l.id ? null : l.id)}
                className={`card card-interactive w-full p-5 text-left ${layer === l.id ? "!border-accent/60 !bg-surface-raised" : ""}`}
              >
                <span className="block font-semibold text-ink">{l.name}</span>
                <span className="mt-1 block text-sm text-muted">{l.summary}</span>
              </button>
            </li>
          ))}
        </ul>
        <div className="mt-5 flex flex-wrap gap-2">
          <button
            type="button"
            className="chip"
            aria-pressed={tracing && direction === "up"}
            onClick={() => {
              setDirection("up");
              setTracing(true);
              setLayer("device");
            }}
          >
            <ArrowUp size={14} aria-hidden /> Trace an update
          </button>
          <button
            type="button"
            className="chip"
            aria-pressed={tracing && direction === "down"}
            onClick={() => {
              setDirection("down");
              setTracing(true);
              setLayer("cloud");
            }}
          >
            <ArrowDown size={14} aria-hidden /> Trace a model broadcast
          </button>
          <button type="button" className="chip" onClick={stepThrough}>
            Step to next layer
          </button>
        </div>
        <p className="mt-4 text-sm leading-relaxed text-muted" aria-live="polite">
          {explanation}
          {layer && (
            <>
              {" "}
              <span className="text-ink">Now: {LAYERS.find((l) => l.id === layer)!.name}.</span> {LAYERS.find((l) => l.id === layer)!.detail}
            </>
          )}
        </p>
        <Link href="/architecture/" className="mt-5 inline-block font-semibold text-ink underline decoration-coral decoration-2 underline-offset-[6px] hover:text-accent">
          Open the interactive architecture
        </Link>
      </div>
      <div className="clay-stage p-5">
        <ArchitectureDiagram2D
          edges={2}
          highlightLayer={layer}
          showFlow={tracing}
          showPrivacy
          showCompression={tracing && direction === "up"}
          showEdgeAggregation
          direction={direction}
          onSelectLayer={(l) => setLayer(layer === l ? null : l)}
        />
      </div>
    </div>
  );
}
