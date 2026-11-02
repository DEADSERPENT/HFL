"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Box, ChevronDown, ChevronUp, Minus, Pause, Play, Plus, RotateCcw, RotateCw, Square } from "lucide-react";
import { GUIDED_STEPS, LAYERS, TOPOLOGIES, type LayerId, type TopologyId } from "@/content/architecture";
import { useMotion } from "@/components/motion/MotionPreference";
import type { CameraApi } from "@/components/three/ArchitectureScene";
import { ArchitectureCanvas3D } from "./ArchitectureCanvas3D";
import { ArchitectureDiagram2D } from "./ArchitectureDiagram2D";
import { GuidedStepPanel } from "./GuidedStepPanel";
import { EvidenceStatusLabel } from "@/components/metrics/EvidenceStatusLabel";

type Toggles = { flow: boolean; privacy: boolean; compression: boolean; aggregation: boolean };

const STEP_DEG = Math.PI / 12;

export function ArchitectureExplorer({ initialView = "3d" }: { initialView?: "3d" | "2d" }) {
  const { reduced } = useMotion();
  const [view, setView] = useState<"3d" | "2d">(initialView);
  const [webglFailed, setWebglFailed] = useState(false);
  const [topology, setTopology] = useState<TopologyId>("edges-2");
  const [layer, setLayer] = useState<LayerId | null>(null);
  const [toggles, setToggles] = useState<Toggles>({ flow: true, privacy: true, compression: false, aggregation: true });
  const [userPlaying, setUserPlaying] = useState<boolean | null>(null);
  const [direction, setDirection] = useState<"up" | "down">("up");
  const [step, setStep] = useState<number | null>(null);
  const camera = useRef<CameraApi>(null);
  const live = useId();

  // Reduced motion: never autoplay; the visitor can still press Play.
  const playing = userPlaying ?? !reduced;

  const onUnavailable = useCallback(() => {
    setWebglFailed(true);
    setView("2d");
  }, []);

  useEffect(() => {
    if (step === null) return;
    const s = GUIDED_STEPS[step]!;
    setLayer(s.layer);
    setToggles({
      flow: true,
      privacy: !!s.highlight.privacy,
      compression: !!s.highlight.compression,
      aggregation: !!s.highlight.edgeAggregation,
    });
    setDirection(s.highlight.direction ?? "up");
  }, [step]);

  const edges = TOPOLOGIES.find((t) => t.id === topology)!.edges;
  const topo = TOPOLOGIES.find((t) => t.id === topology)!;
  const toggle = (k: keyof Toggles) => setToggles((t) => ({ ...t, [k]: !t[k] }));
  const is3d = view === "3d" && !webglFailed;

  const onCanvasKey = (e: React.KeyboardEvent) => {
    const api = camera.current;
    if (!api) return;
    const map: Record<string, () => void> = {
      ArrowLeft: () => api.rotate(-STEP_DEG),
      ArrowRight: () => api.rotate(STEP_DEG),
      ArrowUp: () => api.tilt(-STEP_DEG / 2),
      ArrowDown: () => api.tilt(STEP_DEG / 2),
      "+": () => api.zoom(0.88),
      "=": () => api.zoom(0.88),
      "-": () => api.zoom(1.14),
      "0": () => api.reset(),
    };
    const fn = map[e.key];
    if (fn) {
      e.preventDefault();
      fn();
    }
  };

  const status = `${is3d ? "3D view" : "2D diagram"}; ${topo.label}; ${layer ? `${LAYERS.find((l) => l.id === layer)!.name} highlighted` : "all layers"}; flow ${
    direction === "up" ? "update to cloud" : "model broadcast"
  }, ${playing ? "playing" : "paused"}.`;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
      <div className="min-w-0">
        <div className="clay relative overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
            <div className="flex items-center gap-2">
              <EvidenceStatusLabel status="illustrative" size="sm" />
              <span className="text-xs text-subtle">Conceptual model, not a live network trace</span>
            </div>
            <div role="radiogroup" aria-label="View" className="flex gap-1">
              <button
                type="button"
                role="radio"
                aria-checked={is3d}
                disabled={webglFailed}
                className="chip"
                onClick={() => setView("3d")}
              >
                <Box size={14} aria-hidden /> 3D
              </button>
              <button type="button" role="radio" aria-checked={!is3d} className="chip" onClick={() => setView("2d")}>
                <Square size={14} aria-hidden /> 2D diagram
              </button>
            </div>
          </div>

          {is3d ? (
            <div
              tabIndex={0}
              onKeyDown={onCanvasKey}
              aria-label="3D architecture view. Arrow keys rotate and tilt, plus and minus zoom, 0 resets. The same information is in the panel and the 2D diagram."
              aria-describedby={live}
              className="relative focus-visible:outline-offset-[-3px]"
            >
              <ArchitectureCanvas3D
                className="relative h-[420px] w-full md:h-[520px]"
                label="Interactive 3D model of the device, edge and cloud tiers"
                apiRef={camera}
                onUnavailable={onUnavailable}
                edges={edges}
                highlightLayer={layer}
                showFlow={toggles.flow}
                showPrivacy={toggles.privacy}
                showCompression={toggles.compression}
                showEdgeAggregation={toggles.aggregation}
                playing={playing}
                direction={direction}
                interactive
              />
              <ul aria-hidden className="pointer-events-none absolute left-4 top-4 space-y-1 text-[0.72rem] text-subtle">
                <li>
                  <span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-model" />
                  Cloud
                </li>
                <li>
                  <span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-sage" />
                  Edge aggregators
                </li>
                <li>
                  <span className="mr-1.5 inline-block h-2 w-2 rotate-45 bg-accent" />
                  Client devices (schematic)
                </li>
                {toggles.privacy && (
                  <li>
                    <span className="mr-1.5 inline-block h-2 w-3 rounded-sm border border-dashed border-sage" />
                    Privacy boundary
                  </li>
                )}
              </ul>
            </div>
          ) : (
            <div className="p-4">
              {webglFailed && (
                <p role="status" className="mb-3 rounded-md border border-line bg-surface px-3 py-2 text-sm text-muted">
                  3D is unavailable on this device, so the 2D diagram is shown. It carries the same layers, flows and labels.
                </p>
              )}
              <ArchitectureDiagram2D
                edges={edges}
                highlightLayer={layer}
                showFlow={toggles.flow}
                showPrivacy={toggles.privacy}
                showCompression={toggles.compression}
                showEdgeAggregation={toggles.aggregation}
                direction={direction}
                onSelectLayer={(l) => setLayer((cur) => (cur === l ? null : l))}
              />
            </div>
          )}

          {/* camera + playback controls */}
          <div className="flex flex-wrap items-center gap-2 border-t border-line px-4 py-3">
            <button type="button" className="btn btn-ghost btn-sm" aria-pressed={playing} onClick={() => setUserPlaying(!playing)}>
              {playing ? <Pause size={14} aria-hidden /> : <Play size={14} aria-hidden />}
              {playing ? "Pause flow" : "Play flow"}
            </button>
            <div role="radiogroup" aria-label="Flow direction" className="flex gap-1">
              <button type="button" role="radio" aria-checked={direction === "up"} className="chip" onClick={() => setDirection("up")}>
                Trace an update
              </button>
              <button type="button" role="radio" aria-checked={direction === "down"} className="chip" onClick={() => setDirection("down")}>
                Trace a model broadcast
              </button>
            </div>
            {is3d && (
              <div className="ml-auto flex flex-wrap gap-1" role="group" aria-label="Camera">
                <IconBtn label="Rotate left" onClick={() => camera.current?.rotate(-STEP_DEG)}>
                  <RotateCcw size={14} />
                </IconBtn>
                <IconBtn label="Rotate right" onClick={() => camera.current?.rotate(STEP_DEG)}>
                  <RotateCw size={14} />
                </IconBtn>
                <IconBtn label="Tilt up" onClick={() => camera.current?.tilt(-STEP_DEG / 2)}>
                  <ChevronUp size={14} />
                </IconBtn>
                <IconBtn label="Tilt down" onClick={() => camera.current?.tilt(STEP_DEG / 2)}>
                  <ChevronDown size={14} />
                </IconBtn>
                <IconBtn label="Zoom in" onClick={() => camera.current?.zoom(0.88)}>
                  <Plus size={14} />
                </IconBtn>
                <IconBtn label="Zoom out" onClick={() => camera.current?.zoom(1.14)}>
                  <Minus size={14} />
                </IconBtn>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => camera.current?.reset()}>
                  Reset view
                </button>
              </div>
            )}
          </div>
          <p id={live} role="status" aria-live="polite" className="sr-only">
            {status}
          </p>
        </div>

        {/* toggles */}
        <fieldset className="mt-4 flex flex-wrap gap-2">
          <legend className="sr-only">Show or hide scene elements</legend>
          {(
            [
              ["flow", "Show data flow"],
              ["privacy", "Show privacy boundary"],
              ["compression", "Show compression"],
              ["aggregation", "Show edge aggregation"],
            ] as const
          ).map(([k, label]) => (
            <button key={k} type="button" className="chip" aria-pressed={toggles[k]} onClick={() => toggle(k)}>
              {label}
            </button>
          ))}
        </fieldset>
      </div>

      <div className="space-y-5">
        {step === null ? (
          <section aria-label="Guided story" className="clay p-5">
            <p className="eyebrow">Guided story</p>
            <p className="mt-2 text-sm text-muted">Six short steps from local computation to evaluation.</p>
            <button type="button" className="btn btn-primary btn-sm mt-4" onClick={() => setStep(0)}>
              Start the story
            </button>
          </section>
        ) : (
          <GuidedStepPanel index={step} onChange={setStep} onExit={() => setStep(null)} />
        )}

        <section aria-labelledby="layer-sel" className="clay p-5">
          <h3 id="layer-sel" className="text-sm font-semibold text-subtle">
            Layer
          </h3>
          <div role="radiogroup" aria-labelledby="layer-sel" className="mt-3 flex flex-wrap gap-2">
            <button type="button" role="radio" aria-checked={layer === null} className="chip" onClick={() => setLayer(null)}>
              All
            </button>
            {LAYERS.map((l) => (
              <button key={l.id} type="button" role="radio" aria-checked={layer === l.id} className="chip" onClick={() => setLayer(l.id)}>
                {l.name.replace(" layer", "")}
              </button>
            ))}
          </div>
          <div className="mt-4" aria-live="polite">
            {(layer ? LAYERS.filter((l) => l.id === layer) : LAYERS).map((l) => (
              <div key={l.id} className="mt-3 first:mt-0">
                <p className="font-medium text-ink">{l.name}</p>
                <p className="text-sm leading-relaxed text-muted">{l.detail}</p>
              </div>
            ))}
          </div>
        </section>

        <section aria-labelledby="topo-sel" className="clay p-5">
          <h3 id="topo-sel" className="text-sm font-semibold text-subtle">
            Topology
          </h3>
          <p className="mt-1 text-xs text-subtle">Only configurations with verified result data.</p>
          <div role="radiogroup" aria-labelledby="topo-sel" className="mt-3 flex flex-wrap gap-2">
            {TOPOLOGIES.map((t) => (
              <button key={t.id} type="button" role="radio" aria-checked={topology === t.id} className="chip" onClick={() => setTopology(t.id)}>
                {t.label}
              </button>
            ))}
          </div>
          <div className="mt-3 text-sm" aria-live="polite">
            <p className="text-ink">{topo.description}</p>
            <p className="mt-1 text-muted">{topo.fact}</p>
            <p className="mt-2 text-xs text-subtle">Client nodes drawn are schematic, not the evaluated client count.</p>
          </div>
        </section>
      </div>
    </div>
  );
}

function IconBtn({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" className="btn btn-ghost btn-sm !px-2.5" aria-label={label} title={label} onClick={onClick}>
      <span aria-hidden>{children}</span>
    </button>
  );
}
