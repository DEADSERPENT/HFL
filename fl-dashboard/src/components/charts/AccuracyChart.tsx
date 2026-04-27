import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { useFLStore } from '../../store/useFLStore';

interface Props { height?: number; showGrid?: boolean; compact?: boolean; }

export function AccuracyChart({ height = 110, showGrid = true, compact = true }: Props) {
  const { roundHistory } = useFLStore();

  const data = roundHistory.map((r) => ({
    round: r.round,
    accuracy: parseFloat((r.globalAccuracy * 100).toFixed(3)),
  }));

  const latest = data[data.length - 1];

  return (
    <div className="flex flex-col gap-1.5 h-full">
      <div className="flex items-baseline justify-between px-1">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-fl-muted">Global Accuracy</span>
        {latest && (
          <span className="font-mono text-sm font-medium" style={{ color: latest.accuracy >= 85 ? '#059669' : '#0F172A' }}>
            {latest.accuracy.toFixed(2)}%
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
            label={compact ? undefined : { value: 'Round', position: 'insideBottom', offset: -2, fontSize: 9, fill: '#94A3B8' }}
          />
          <YAxis
            domain={[50, 100]}
            tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            contentStyle={{ border: '1px solid #E2E8F0', borderRadius: 6, padding: '5px 10px', fontFamily: 'JetBrains Mono', fontSize: 11 }}
            formatter={(v: number) => [`${v.toFixed(3)}%`, 'Accuracy']}
            labelFormatter={(l) => `Round ${l}`}
          />
          <ReferenceLine y={83} stroke="#05966940" strokeDasharray="4 4"
            label={{ value: '83%', position: 'right', fontSize: 8, fill: '#059669' }} />
          <Line
            type="monotone" dataKey="accuracy"
            stroke="#2563EB" strokeWidth={1.8}
            dot={false}
            activeDot={{ r: 3, fill: '#2563EB' }}
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
