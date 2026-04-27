import React, { useRef, useEffect, useState, useCallback } from 'react';
import clsx from 'clsx';
import { useFLStore } from '../../store/useFLStore';

function accColor(acc: number): string {
  if (acc >= 0.80) return '#059669';
  if (acc >= 0.68) return '#D97706';
  return '#DC2626';
}

interface Pos { x: number; y: number; }

const CLOUD_R = 26;
const EDGE_R  = 20;

// Radius scaled by dataset size, capped so circles never touch
function devR(size: number, maxSize: number): number {
  return 11 + 6 * Math.sqrt(size / maxSize);   // 11–17 px
}

export function NetworkGraph() {
  const {
    clients, edges, selectedClientId,
    trainingPhase, activeClientIds, activeEdgeIds, isTraining,
  } = useFLStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 600, h: 400 });
  const [hovered, setHovered] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setDims({ w: Math.max(width, 1), h: Math.max(height, 1) });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const handleNodeClick = useCallback((id: string) => {
    const cur = useFLStore.getState().selectedClientId;
    useFLStore.getState().selectClient(cur === id ? null : id);
  }, []);

  const { w, h } = dims;

  // ── Hierarchy positions ─────────────────────────────────────────────────
  // Cloud: top-centre
  const cloudPos: Pos = { x: w * 0.50, y: h * 0.14 };

  // Edges: centred above their device clusters
  // Edge-A covers devices 0,1,2  →  centre = x * 0.24
  // Edge-B covers devices 3,4,5  →  centre = x * 0.76
  const edgePos: Pos[] = [
    { x: w * 0.24, y: h * 0.44 },
    { x: w * 0.76, y: h * 0.44 },
  ];

  // Devices: three under each edge, spread at 0.12 spacing
  // Group A: 0.12, 0.24, 0.36   Group B: 0.64, 0.76, 0.88
  const devicePos: Pos[] = [
    { x: w * 0.12, y: h * 0.76 },
    { x: w * 0.24, y: h * 0.76 },
    { x: w * 0.36, y: h * 0.76 },
    { x: w * 0.64, y: h * 0.76 },
    { x: w * 0.76, y: h * 0.76 },
    { x: w * 0.88, y: h * 0.76 },
  ];

  const maxData = Math.max(...clients.map((c) => c.datasetSize), 1);

  const isLocalTraining = trainingPhase === 'local-training';
  const isEdgeAgg       = trainingPhase === 'edge-agg';
  const isCloudAgg      = trainingPhase === 'cloud-agg';

  const phaseLabel =
    isLocalTraining ? '↑ Local Training'
    : isEdgeAgg     ? '⇑ Edge Aggregating'
    : isCloudAgg    ? '⇑ Cloud Aggregating'
    : isTraining    ? '· Waiting' : '';

  const phaseCls = isLocalTraining
    ? 'bg-blue-50 text-blue-600 border-blue-200'
    : isEdgeAgg
    ? 'bg-violet-50 text-violet-600 border-violet-200'
    : isCloudAgg
    ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
    : 'bg-slate-100 text-slate-500 border-slate-200';

  // Separator y midpoints (for dashed tier lines)
  const sep1Y = (cloudPos.y + edgePos[0].y) / 2;   // between cloud & edge tier
  const sep2Y = (edgePos[0].y + devicePos[0].y) / 2; // between edge & IoT tier

  return (
    <div ref={containerRef} className="relative w-full h-full select-none overflow-hidden bg-fl-panel">
      <svg width={w} height={h} className="absolute inset-0">
        <defs>
          <radialGradient id="ng-cloud-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%"  stopColor="#2563EB" stopOpacity="0.20" />
            <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="ng-edge-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%"  stopColor="#7C3AED" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#7C3AED" stopOpacity="0" />
          </radialGradient>
          <filter id="ng-shadow" x="-40%" y="-40%" width="180%" height="180%">
            <feDropShadow dx="0" dy="1" stdDeviation="2.5" floodColor="#0F172A" floodOpacity="0.10" />
          </filter>
        </defs>

        {/* ── Tier separator dashes (drawn first, behind everything) ── */}
        <line x1={0} y1={sep1Y} x2={w} y2={sep1Y}
          stroke="#E2E8F0" strokeWidth={1} strokeDasharray="4 5" />
        <line x1={0} y1={sep2Y} x2={w} y2={sep2Y}
          stroke="#E2E8F0" strokeWidth={1} strokeDasharray="4 5" />

        {/* Tier labels on the separators — centred on the line, not the node rows */}
        <text x={8} y={sep1Y - 4} fontSize={7} fontFamily="JetBrains Mono, monospace"
          fill="#CBD5E1" fontWeight="600">EDGE TIER</text>
        <text x={8} y={sep2Y - 4} fontSize={7} fontFamily="JetBrains Mono, monospace"
          fill="#CBD5E1" fontWeight="600">IoT TIER</text>

        {/* ── Cloud glow (cloud-agg phase) ── */}
        {isCloudAgg && (
          <circle cx={cloudPos.x} cy={cloudPos.y} fill="url(#ng-cloud-glow)">
            <animate attributeName="r"
              values={`${CLOUD_R + 14};${CLOUD_R + 28};${CLOUD_R + 14}`}
              dur="1.6s" repeatCount="indefinite" />
          </circle>
        )}

        {/* ── Edge → Cloud links ── */}
        {edgePos.map((ep, ei) => {
          const active = activeEdgeIds.includes(ei) || isCloudAgg;
          const dx = cloudPos.x - ep.x, dy = cloudPos.y - ep.y;
          const len = Math.sqrt(dx * dx + dy * dy);
          const ux = dx / len, uy = dy / len;
          const x1 = ep.x + ux * (EDGE_R + 2), y1 = ep.y + uy * (EDGE_R + 2);
          const x2 = cloudPos.x - ux * (CLOUD_R + 2), y2 = cloudPos.y - uy * (CLOUD_R + 2);
          return (
            <g key={`cloud-link-${ei}`}>
              <line x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={active ? '#2563EB' : '#CBD5E1'}
                strokeWidth={active ? 2 : 1.2}
                strokeOpacity={active ? 0.7 : 0.4} />
              {isCloudAgg && (
                <line x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke="#2563EB" strokeWidth={2}
                  strokeDasharray="6 5" strokeOpacity={0.8}
                  className="edge-upload" />
              )}
            </g>
          );
        })}

        {/* ── Device → Edge links ── */}
        {clients.map((c, i) => {
          const dp = devicePos[i];
          const ep = edgePos[c.edgeId];
          const isSel = selectedClientId === c.id;
          const isHov = hovered === c.id;
          const r = devR(c.datasetSize, maxData);
          const col = accColor(c.accuracy);
          const dx = ep.x - dp.x, dy = ep.y - dp.y;
          const len = Math.sqrt(dx * dx + dy * dy);
          const ux = dx / len, uy = dy / len;
          const x1 = dp.x + ux * (r + 2),    y1 = dp.y + uy * (r + 2);
          const x2 = ep.x - ux * (EDGE_R + 2), y2 = ep.y - uy * (EDGE_R + 2);
          return (
            <g key={`dev-link-${c.id}`}>
              <line x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={isSel || isHov ? col : '#E2E8F0'}
                strokeWidth={isSel ? 2 : 1}
                strokeOpacity={isSel || isHov ? 0.85 : 0.7} />
              {isLocalTraining && activeClientIds.includes(c.id) && (
                <line x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={col} strokeWidth={1.8}
                  strokeDasharray="5 5" strokeOpacity={0.75}
                  className="edge-upload" />
              )}
              {isEdgeAgg && (
                <line x1={x2} y1={y2} x2={x1} y2={y1}
                  stroke="#7C3AED" strokeWidth={1.5}
                  strokeDasharray="5 5" strokeOpacity={0.65}
                  className="edge-download" />
              )}
            </g>
          );
        })}

        {/* ── Edge servers ── */}
        {edgePos.map((ep, ei) => {
          const edge   = edges[ei];
          const isAgg  = activeEdgeIds.includes(ei) || isEdgeAgg;
          const label  = ei === 0 ? 'Edge-A' : 'Edge-B';
          const accTxt = edge?.accuracy > 0
            ? `${(edge.accuracy * 100).toFixed(0)}%`
            : `${edge?.deviceIds.length ?? 3} dev`;
          return (
            <g key={`edge-${ei}`} transform={`translate(${ep.x},${ep.y})`}>
              {isAgg && (
                <circle fill="url(#ng-edge-glow)">
                  <animate attributeName="r"
                    values={`${EDGE_R + 10};${EDGE_R + 22};${EDGE_R + 10}`}
                    dur="1.4s" repeatCount="indefinite" />
                </circle>
              )}
              <circle r={EDGE_R} fill={isAgg ? '#7C3AED' : '#6D28D9'}
                filter="url(#ng-shadow)" />
              {/* inner gloss */}
              <circle r={EDGE_R * 0.55} fill="white" opacity={0.10} />
              <text textAnchor="middle" fontSize={8}
                fontFamily="JetBrains Mono, monospace" fontWeight="700"
                fill="white" y={-5} dominantBaseline="middle">
                {label}
              </text>
              <text textAnchor="middle" fontSize={7}
                fontFamily="JetBrains Mono, monospace"
                fill="white" opacity={0.80} y={6} dominantBaseline="middle">
                {accTxt}
              </text>
            </g>
          );
        })}

        {/* ── IoT Device nodes ── */}
        {clients.map((c, i) => {
          const dp    = devicePos[i];
          const isSel = selectedClientId === c.id;
          const isHov = hovered === c.id;
          const color = accColor(c.accuracy);
          const r     = devR(c.datasetSize, maxData);
          const isTrain = activeClientIds.includes(c.id) && isLocalTraining;
          return (
            <g key={c.id} transform={`translate(${dp.x},${dp.y})`}
              className="graph-node" style={{ cursor: 'pointer' }}
              onClick={() => handleNodeClick(c.id)}
              onMouseEnter={() => setHovered(c.id)}
              onMouseLeave={() => setHovered(null)}>
              <g className="graph-node-body">
                {/* Selection / hover ring */}
                {(isSel || isHov) && (
                  <circle r={r + 6} fill="none" stroke={color}
                    strokeWidth={1.5} opacity={0.30} />
                )}
                {/* Training pulse */}
                {isTrain && (
                  <>
                    <circle r={r + 4} fill="none" stroke={color} strokeWidth={1} opacity={0}>
                      <animate attributeName="r"
                        values={`${r + 2};${r + 10};${r + 2}`}
                        dur="1.2s" repeatCount="indefinite" />
                      <animate attributeName="opacity"
                        values="0.45;0;0.45" dur="1.2s" repeatCount="indefinite" />
                    </circle>
                  </>
                )}
                {/* Circle */}
                <circle r={r} fill={color} filter="url(#ng-shadow)"
                  opacity={c.status === 'disconnected' ? 0.35 : 1} />
                {/* Gloss */}
                <circle r={r * 0.48} fill="white" opacity={0.14} />
                {/* Accuracy inside */}
                <text textAnchor="middle" dominantBaseline="central"
                  fontSize={r > 14 ? 8 : 7}
                  fontFamily="JetBrains Mono, monospace" fontWeight="600" fill="white">
                  {(c.accuracy * 100).toFixed(0)}%
                </text>
              </g>

              {/* Device name — single line below circle */}
              <text y={r + 12} textAnchor="middle" fontSize={8.5}
                fontFamily="Plus Jakarta Sans, sans-serif"
                fontWeight={isSel ? 700 : 400}
                fill={isSel ? '#0F172A' : '#64748B'}>
                {c.name}
              </text>
            </g>
          );
        })}

        {/* ── Cloud server (drawn last = on top) ── */}
        <g transform={`translate(${cloudPos.x},${cloudPos.y})`}>
          {/* Outer ring */}
          <circle r={CLOUD_R + 7} fill="none"
            stroke="#2563EB" strokeWidth={0.8} opacity={0.18} />
          <circle r={CLOUD_R} fill="#1D4ED8" filter="url(#ng-shadow)" />
          <circle r={CLOUD_R * 0.55} fill="white" opacity={0.12} />
          <text textAnchor="middle" fontSize={8}
            fontFamily="JetBrains Mono, monospace" fontWeight="700"
            fill="white" y={-5} dominantBaseline="middle">
            CLOUD
          </text>
          <text textAnchor="middle" fontSize={6.5}
            fontFamily="JetBrains Mono, monospace"
            fill="white" opacity={0.75} y={5} dominantBaseline="middle">
            HFL-MM-HC
          </text>
        </g>

        {/* ── Legend (inside SVG, bottom-left, clear of device labels) ── */}
        <g transform={`translate(8, ${h - 16})`}>
          {[
            { color: '#059669', label: '≥80%',   x: 0  },
            { color: '#D97706', label: '68-80%',  x: 50 },
            { color: '#DC2626', label: '<68%',    x: 108 },
          ].map((l) => (
            <g key={l.label} transform={`translate(${l.x}, 0)`}>
              <circle r={4} fill={l.color} />
              <text x={9} dominantBaseline="middle" fontSize={7.5}
                fontFamily="Plus Jakarta Sans, sans-serif" fill="#94A3B8">
                {l.label}
              </text>
            </g>
          ))}
          <text x={165} dominantBaseline="middle" fontSize={7}
            fontFamily="Plus Jakarta Sans, sans-serif" fill="#CBD5E1">
            size = samples · click to inspect
          </text>
        </g>
      </svg>

      {/* Phase indicator — top-right, pointer-events-none so it doesn't block clicks */}
      {isTraining && phaseLabel && (
        <div className="absolute top-2 right-2 pointer-events-none">
          <span className={clsx(
            'text-[10px] font-semibold px-2 py-1 rounded border uppercase tracking-wide',
            phaseCls,
          )}>
            {phaseLabel}
          </span>
        </div>
      )}
    </div>
  );
}
