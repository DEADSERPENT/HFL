import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';
import { useFLStore } from '../../store/useFLStore';

interface Props { height?: number; showGrid?: boolean; compact?: boolean; }

export function LossChart({ height = 110, showGrid = true, compact = true }: Props) {
  const { roundHistory } = useFLStore();

  const data = roundHistory.map((r) => ({
    round: r.round,
    loss: parseFloat(r.globalLoss.toFixed(5)),
  }));

  const latest = data[data.length - 1];

  return (
    <div className="flex flex-col gap-1.5 h-full">
      <div className="flex items-baseline justify-between px-1">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-fl-muted">Global Loss</span>
        {latest && (
          <span className="font-mono text-sm font-medium" style={{ color: latest.loss < 0.15 ? '#059669' : '#0F172A' }}>
            {latest.loss.toFixed(4)}
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 4, right: 4, left: compact ? -22 : 0, bottom: 0 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />}
          <XAxis
            dataKey="round"
            tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            domain={[0, 'auto']}
            tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{ border: '1px solid #E2E8F0', borderRadius: 6, padding: '5px 10px', fontFamily: 'JetBrains Mono', fontSize: 11 }}
            formatter={(v: number) => [v.toFixed(5), 'Loss']}
            labelFormatter={(l) => `Round ${l}`}
          />
          <Line
            type="monotone" dataKey="loss"
            stroke="#DC2626" strokeWidth={1.8}
            dot={false}
            activeDot={{ r: 3, fill: '#DC2626' }}
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
