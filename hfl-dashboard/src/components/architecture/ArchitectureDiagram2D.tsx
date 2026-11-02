"use client";

import { useMemo } from "react";
import type { LayerId } from "@/content/architecture";
import { schematicDeviceCount } from "./layout";

/**
 * Accessible SVG diagram with the same layers, arrows, privacy boundary and
 * compression marker as the 3D scene. Functionally sufficient on its own.
 */
export function ArchitectureDiagram2D({
  edges,
  highlightLayer,
  showFlow,
  showPrivacy,
  showCompression,
  showEdgeAggregation,
  direction,
  onSelectLayer,
}: {
  edges: number;
  highlightLayer: LayerId | null;
  showFlow: boolean;
  showPrivacy: boolean;
  showCompression: boolean;
  showEdgeAggregation: boolean;
  direction: "up" | "down";
  onSelectLayer?: (l: LayerId) => void;
}) {
  const W = 760;
  const H = 420;
  const yCloud = 70;
  const yEdge = 210;
  const yDev = 345;
  const nDev = Math.min(schematicDeviceCount(edges), edges > 8 ? 32 : 24);
  const shownEdges = Math.min(edges, 8);

  const layout = useMemo(() => {
    const devX = Array.from({ length: nDev }, (_, i) => 60 + (i * (W - 120)) / Math.max(1, nDev - 1));
    const perEdge = nDev / shownEdges;
    const edgeX = Array.from({ length: shownEdges }, (_, e) => {
      const first = Math.round(e * perEdge);
      const last = Math.round((e + 1) * perEdge) - 1;
      return (devX[first]! + devX[last]!) / 2;
    });
    const devEdge = devX.map((_, i) => Math.min(shownEdges - 1, Math.floor(i / perEdge)));
    return { devX, edgeX, devEdge };
  }, [nDev, shownEdges]);

  const dim = (l: LayerId) => (highlightLayer && highlightLayer !== l ? 0.35 : 1);
  const marker = direction === "up" ? "url(#arrow-up)" : "url(#arrow-down)";

  const layerBtn = (l: LayerId, y: number, label: string) => (
    <g
      role={onSelectLayer ? "button" : undefined}
      tabIndex={onSelectLayer ? 0 : undefined}
      aria-label={onSelectLayer ? `Select ${label}` : undefined}
      aria-pressed={onSelectLayer ? highlightLayer === l : undefined}
      onClick={() => onSelectLayer?.(l)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelectLayer?.(l);
        }
      }}
      className={onSelectLayer ? "cursor-pointer focus:outline-none [&:focus-visible>rect]:stroke-[var(--color-accent)]" : undefined}
    >
      <rect x={4} y={y - 18} width={110} height={36} rx={18} fill="var(--paper)" stroke="var(--color-border)" strokeWidth={1.5} />
      <text x={59} y={y + 5} textAnchor="middle" fill="var(--color-text)" fontSize={13} fontWeight={600}>
        {label}
      </text>
    </g>
  );

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="group" aria-label="Two-dimensional diagram of the device, edge and cloud architecture">
      <title>PP-HFM architecture: device, edge and cloud tiers</title>
      <desc>
        {`${nDev} schematic client devices connect to ${edges} edge aggregator${edges === 1 ? "" : "s"}${
          edges > shownEdges ? ` (${shownEdges} drawn)` : ""
        }, which connect to one cloud aggregator. Arrows point ${direction === "up" ? "upward: client updates flow to the edges and cloud" : "downward: the global model is broadcast to the clients"}.${
          showPrivacy ? " A privacy boundary surrounds the client tier, where clipping and noise are applied." : ""
        }${showCompression ? " A compression marker on each client link shows sparsification and quantization." : ""}`}
      </desc>
      <defs>
        <marker id="arrow-up" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0 0 10 5 0 10z" fill="var(--color-text-muted)" />
        </marker>
        <marker id="arrow-down" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0 0 10 5 0 10z" fill="var(--color-text-muted)" />
        </marker>
      </defs>

      {/* links */}
      <g stroke="var(--color-text-subtle)" strokeWidth={1.1} opacity={showFlow ? 0.75 : 0.3}>
        {layout.devX.map((x, i) => {
          const ex = layout.edgeX[layout.devEdge[i]!]!;
          const [x1, y1, x2, y2] = direction === "up" ? [x, yDev - 10, ex, yEdge + 20] : [ex, yEdge + 20, x, yDev - 10];
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} markerEnd={showFlow ? marker : undefined} />;
        })}
        {layout.edgeX.map((ex, e) => {
          const [x1, y1, x2, y2] = direction === "up" ? [ex, yEdge - 20, W / 2, yCloud + 24] : [W / 2, yCloud + 24, ex, yEdge - 20];
          return <line key={e} x1={x1} y1={y1} x2={x2} y2={y2} strokeWidth={1.6} markerEnd={showFlow ? marker : undefined} />;
        })}
      </g>

      {/* compression markers */}
      {showCompression &&
        layout.devX.map((x, i) => {
          const ex = layout.edgeX[layout.devEdge[i]!]!;
          const t = 0.38;
          const cx = x + (ex - x) * t;
          const cy = yDev - 10 + (yEdge + 20 - (yDev - 10)) * t;
          return <circle key={i} cx={cx} cy={cy} r={4} fill="none" stroke="var(--color-accent)" strokeWidth={1.5} />;
        })}

      {/* privacy boundary */}
      {showPrivacy && (
        <g>
          <rect x={30} y={yDev - 30} width={W - 60} height={60} rx={14} fill="rgba(119,214,174,0.06)" stroke="var(--color-sage)" strokeDasharray="6 5" strokeWidth={1.5} />
          <text x={W - 40} y={yDev + 48} textAnchor="end" fill="var(--color-sage)" fontSize={12}>
            Privacy boundary: per-patient clipping + noise inside each client
          </text>
        </g>
      )}

      {/* devices */}
      <g opacity={dim("device")}>
        {layout.devX.map((x, i) => (
          <rect key={i} x={x - 6} y={yDev - 6} width={12} height={12} transform={`rotate(45 ${x} ${yDev})`} fill="var(--color-accent)" />
        ))}
      </g>

      {/* edges */}
      <g opacity={dim("edge")}>
        {layout.edgeX.map((x, i) => (
          <g key={i}>
            {showEdgeAggregation && <circle cx={x} cy={yEdge} r={edges > 2 ? 24 : 30} fill="none" stroke="var(--color-sage)" strokeDasharray="4 4" />}
            <circle cx={x} cy={yEdge} r={edges > 2 ? 14 : 18} fill="rgba(86,203,180,0.25)" stroke="var(--color-sage)" strokeWidth={2} />
          </g>
        ))}
        {edges > shownEdges && (
          <text x={W - 20} y={yEdge + 4} textAnchor="end" fill="var(--color-text-subtle)" fontSize={12}>
            {`${shownEdges} of ${edges} edges drawn`}
          </text>
        )}
      </g>

      {/* cloud */}
      <g opacity={dim("cloud")}>
        <circle cx={W / 2} cy={yCloud} r={30} fill="none" stroke="var(--color-model)" strokeOpacity={0.5} />
        <circle cx={W / 2} cy={yCloud} r={18} fill="var(--color-model)" />
      </g>

      {layerBtn("cloud", yCloud, "Cloud")}
      {layerBtn("edge", yEdge, "Edge")}
      {layerBtn("device", yDev, "Device")}

      <text x={W - 10} y={H - 6} textAnchor="end" fill="var(--color-text-subtle)" fontSize={11}>
        Conceptual model with schematic node counts
      </text>
    </svg>
  );
}
