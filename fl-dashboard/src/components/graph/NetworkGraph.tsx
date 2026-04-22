import React, { useRef, useEffect, useState, useCallback } from 'react';
import clsx from 'clsx';
import { useFLStore } from '../../store/useFLStore';
import { ClientNode } from '../../types';

// ── Color helpers ─────────────────────────────────────────────────────────────
function accuracyColor(acc: number): string {
  if (acc >= 0.85) return '#059669';
  if (acc >= 0.70) return '#D97706';
  return '#DC2626';
}

function nodeRadius(datasetSize: number, maxSize: number): number {
  const MIN = 13, MAX = 27;
  return MIN + (MAX - MIN) * Math.sqrt(datasetSize / maxSize);
}

interface NodePos {
  x: number; y: number;
  r: number;
  client: ClientNode;
}

interface Props {
  onSelectClient?: (id: string | null) => void;
}

export function NetworkGraph({ onSelectClient }: Props) {
  const { clients, selectedClientId, trainingPhase, activeClientIds, isTraining } = useFLStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 600, h: 400 });
  const [hovered, setHovered] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDims({ w: width, h: height });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const { w, h } = dims;
  const cx = w / 2;
  const cy = h / 2;
  const radius = Math.min(w, h) * 0.34;
  const maxData = Math.max(...clients.map((c) => c.datasetSize));

  const positions: NodePos[] = clients.map((c, i) => {
    const angle = (i / clients.length) * 2 * Math.PI - Math.PI / 2;
    return {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
      r: nodeRadius(c.datasetSize, maxData),
      client: c,
    };
  });

  const handleNodeClick = useCallback((id: string) => {
    const current = useFLStore.getState().selectedClientId;
    useFLStore.getState().selectClient(current === id ? null : id);
    onSelectClient?.(current === id ? null : id);
  }, [onSelectClient]);

  const isUploading   = trainingPhase === 'local-training';
  const isDownloading = trainingPhase === 'aggregating';
  const SERVER_R = 28;

  return (
    <div ref={containerRef} className="relative w-full h-full select-none overflow-hidden">
      <svg width={w} height={h} className="absolute inset-0">
        <defs>
          <radialGradient id="server-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#2563EB" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
          </radialGradient>
          <filter id="node-shadow">
            <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="#0F172A" floodOpacity="0.08" />
          </filter>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#2563EB" opacity="0.5" />
          </marker>
        </defs>

        {/* Server glow */}
        {isTraining && (
          <circle cx={cx} cy={cy} r={SERVER_R + 20} fill="url(#server-glow)">
            <animate attributeName="r" values={`${SERVER_R + 16};${SERVER_R + 26};${SERVER_R + 16}`} dur="3s" repeatCount="indefinite" />
          </circle>
        )}

        {/* Edges */}
        {positions.map((pos) => {
          const isActive = activeClientIds.includes(pos.client.id);
          const isSelected = selectedClientId === pos.client.id;
          const isHov = hovered === pos.client.id;

          // Direction vector
          const dx = pos.x - cx, dy = pos.y - cy;
          const len = Math.sqrt(dx * dx + dy * dy);
          const ux = dx / len, uy = dy / len;
          const x1 = cx + ux * (SERVER_R + 2),  y1 = cy + uy * (SERVER_R + 2);
          const x2 = pos.x - ux * (pos.r + 2),  y2 = pos.y - uy * (pos.r + 2);

          return (
            <g key={`edge-${pos.client.id}`}>
              {/* Base edge */}
              <line x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={isSelected || isHov ? '#2563EB' : '#E2E8F0'}
                strokeWidth={isSelected ? 2 : 1}
                strokeOpacity={isSelected || isHov ? 0.6 : 0.8}
              />
              {/* Animated data flow */}
              {(isActive && isUploading) && (
                <line x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke="#2563EB"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  strokeOpacity={0.7}
                  className="edge-upload"
                />
              )}
              {(isDownloading) && (
                <line x1={x2} y1={y2} x2={x1} y2={y1}
                  stroke="#7C3AED"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  strokeOpacity={0.55}
                  className="edge-download"
                />
              )}
            </g>
          );
        })}

        {/* Client nodes */}
        {positions.map((pos) => {
          const c = pos.client;
          const isSelected = selectedClientId === c.id;
          const isHov = hovered === c.id;
          const color = accuracyColor(c.accuracy);

          return (
            // Outer <g>: only handles positioning (SVG translate — never animated)
            // Inner <g class="graph-node-body">: handles CSS scale with smooth transition
            // This split is required because CSS transition cannot animate SVG transform attributes.
            <g
              key={c.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              className={clsx('graph-node', (isSelected || isHov) && 'node-active')}
              onClick={() => handleNodeClick(c.id)}
              onMouseEnter={() => setHovered(c.id)}
              onMouseLeave={() => setHovered(null)}
            >
              {/* Scaleable body — uses CSS transform-box:fill-box so origin is node center */}
              <g className="graph-node-body">
                {/* Selection / hover ring */}
                {(isSelected || isHov) && (
                  <circle r={pos.r + 6} fill="none" stroke={color} strokeWidth={1.5} opacity={0.3} />
                )}
                {/* Node fill */}
                <circle r={pos.r} fill={color} filter="url(#node-shadow)" opacity={c.status === 'disconnected' ? 0.4 : 1} />
                {/* Inner shine */}
                <circle r={pos.r * 0.55} fill="white" opacity={0.18} />
                {/* Accuracy label */}
                <text
                  textAnchor="middle" dominantBaseline="central"
                  fontSize={pos.r > 19 ? 9 : 8}
                  fontFamily="JetBrains Mono, monospace"
                  fontWeight="500"
                  fill="white"
                >
                  {(c.accuracy * 100).toFixed(0)}%
                </text>
              </g>
              {/* Name label — kept outside scaleable group so it stays at fixed position */}
              <text
                y={pos.r + 14}
                textAnchor="middle"
                fontSize={10}
                fontFamily="Plus Jakarta Sans, sans-serif"
                fontWeight={isSelected ? 600 : 400}
                fill={isSelected ? '#0F172A' : '#64748B'}
              >
                {c.name.split(' ')[0]}
              </text>
            </g>
          );
        })}

        {/* Server node */}
        <g transform={`translate(${cx}, ${cy})`}>
          <circle r={SERVER_R + 4} fill="none" stroke="#2563EB" strokeWidth={1} opacity={0.2} />
          <circle r={SERVER_R} fill="#2563EB" filter="url(#node-shadow)" />
          <circle r={SERVER_R * 0.6} fill="white" opacity={0.15} />
          <text
            textAnchor="middle" dominantBaseline="central"
            fontSize={9}
            fontFamily="JetBrains Mono, monospace"
            fontWeight="500"
            fill="white"
            y={-4}
          >
            SERVER
          </text>
          <text
            textAnchor="middle" dominantBaseline="central"
            fontSize={8}
            fontFamily="JetBrains Mono, monospace"
            fill="white"
            opacity={0.75}
            y={6}
          >
            GLOBAL
          </text>
        </g>
      </svg>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex items-center gap-3">
        {[
          { color: '#059669', label: '≥85% acc' },
          { color: '#D97706', label: '70–85%' },
          { color: '#DC2626', label: '<70%' },
        ].map((l) => (
          <div key={l.label} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: l.color }} />
            <span className="text-[10px] text-fl-muted">{l.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5 ml-1">
          <span className="text-[10px] text-fl-subtle">· node size = dataset size</span>
        </div>
      </div>

      {/* Phase indicator */}
      {isTraining && (
        <div className="absolute top-3 right-3">
          <span className={clsx(
            'text-[10px] font-medium px-2 py-1 rounded border uppercase tracking-wide',
            trainingPhase === 'local-training' && 'bg-blue-50 text-blue-600 border-blue-200',
            trainingPhase === 'aggregating'    && 'bg-violet-50 text-violet-600 border-violet-200',
            trainingPhase === 'waiting'        && 'bg-slate-100 text-slate-500 border-slate-200',
          )}>
            {trainingPhase === 'local-training' && '↑ Local Training'}
            {trainingPhase === 'aggregating'    && '↓ Aggregating'}
            {trainingPhase === 'waiting'        && '· Waiting'}
          </span>
        </div>
      )}
    </div>
  );
}
