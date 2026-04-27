import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';
import { useFLStore } from '../../store/useFLStore';

interface Props { height?: number; compact?: boolean; }

export function LatencyChart({ height = 110, compact = true }: Props) {
  const { roundHistory } = useFLStore();

  const data = roundHistory.map((r) => ({
    round: r.round,
    latency: parseFloat(r.avgLatency.toFixed(1)),
    bytes: parseFloat((r.communicationBytes / 1e6).toFixed(2)),
  }));

  const latest = data[data.length - 1];

  return (
    <div className="flex flex-col gap-1.5 h-full">
      <div className="flex items-baseline justify-between px-1">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-fl-muted">Avg Latency</span>
        {latest && (
          <span className="font-mono text-sm font-medium text-fl-text">
            {latest.latency.toFixed(0)}ms
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 4, right: 4, left: compact ? -22 : 0, bottom: 0 }}>
          <defs>
            <linearGradient id="latency-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#7C3AED" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#7C3AED" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
          <XAxis
            dataKey="round"
            tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}ms`}
          />
          <Tooltip
            contentStyle={{ border: '1px solid #E2E8F0', borderRadius: 6, padding: '5px 10px', fontFamily: 'JetBrains Mono', fontSize: 11 }}
            formatter={(v: number) => [`${v.toFixed(0)}ms`, 'Latency']}
            labelFormatter={(l) => `Round ${l}`}
          />
          <Area
            type="monotone" dataKey="latency"
            stroke="#7C3AED" strokeWidth={1.8}
            fill="url(#latency-grad)"
            dot={false}
            activeDot={{ r: 3, fill: '#7C3AED' }}
            animationDuration={300}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
