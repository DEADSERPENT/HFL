import React, { useState, useMemo } from 'react';
import { FlaskConical, Clock, CheckCircle2, XCircle, PauseCircle, Tag } from 'lucide-react';
import clsx from 'clsx';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { useFLStore } from '../store/useFLStore';
import { StatusBadge } from '../components/common/StatusBadge';
import { ExperimentRun } from '../types';

const EXP_COLORS = ['#2563EB', '#059669', '#7C3AED', '#D97706', '#DC2626'];

function duration(exp: ExperimentRun): string {
  const end = exp.endTime ?? Date.now();
  const ms  = end - exp.startTime;
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

function StatusIcon({ status }: { status: ExperimentRun['status'] }) {
  if (status === 'completed') return <CheckCircle2 size={13} className="text-fl-green" />;
  if (status === 'failed')    return <XCircle      size={13} className="text-fl-danger" />;
  if (status === 'paused')    return <PauseCircle  size={13} className="text-fl-warning" />;
  return <FlaskConical size={13} className="text-fl-primary training-dot" />;
}

export function Experiments() {
  const { experiments, activeExperimentId, roundHistory } = useFLStore();
  const [selected, setSelected] = useState<string[]>(experiments.map((e) => e.id));
  const [metric, setMetric] = useState<'globalAccuracy' | 'globalLoss'>('globalAccuracy');

  // Build comparison data (align by round)
  const maxRound = useMemo(() =>
    Math.max(...experiments.map((e) => e.metrics.length)), [experiments]);

  const chartData = useMemo(() => {
    const rows: Record<string, number | string>[] = [];
    for (let r = 1; r <= maxRound; r++) {
      const row: Record<string, number | string> = { round: r };
      experiments.forEach((exp) => {
        if (!selected.includes(exp.id)) return;
        const m = exp.metrics[r - 1];
        if (m) row[exp.name] = metric === 'globalAccuracy'
          ? parseFloat((m.globalAccuracy * 100).toFixed(3))
          : parseFloat(m.globalLoss.toFixed(5));
      });
      rows.push(row);
    }
    return rows;
  }, [experiments, selected, metric, maxRound]);

  const toggleExp = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  return (
    <div className="flex flex-col h-full overflow-hidden p-4 gap-4 page-enter">
      {/* Comparison chart */}
      <div className="panel p-4 shrink-0" style={{ height: 280 }}>
        <div className="flex items-center justify-between mb-3">
          <span className="panel-header-title">
            <FlaskConical size={11} />
            Experiment Comparison
          </span>
          <div className="flex gap-1">
            {(['globalAccuracy', 'globalLoss'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={clsx(
                  'text-[10px] px-2 py-1 rounded border transition-all',
                  metric === m
                    ? 'bg-fl-primary text-white border-fl-primary'
                    : 'bg-fl-secondary text-fl-muted border-fl-border hover:border-fl-primary'
                )}
              >
                {m === 'globalAccuracy' ? 'Accuracy' : 'Loss'}
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 4, right: 16, left: -8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
            <XAxis
              dataKey="round"
              tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
              tickLine={false} axisLine={false}
              label={{ value: 'Round', position: 'insideBottom', offset: -1, fontSize: 9, fill: '#94A3B8' }}
            />
            <YAxis
              tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
              tickLine={false} axisLine={false}
              tickFormatter={(v) => metric === 'globalAccuracy' ? `${v}%` : v.toFixed(3)}
            />
            <Tooltip
              contentStyle={{ border: '1px solid #E2E8F0', borderRadius: 6, padding: '5px 10px', fontFamily: 'JetBrains Mono', fontSize: 10 }}
              formatter={(v: number, name: string) => [metric === 'globalAccuracy' ? `${v.toFixed(2)}%` : v.toFixed(5), name]}
              labelFormatter={(l) => `Round ${l}`}
            />
            <Legend wrapperStyle={{ fontSize: 10, fontFamily: 'Plus Jakarta Sans' }} />
            {experiments.map((exp, i) => selected.includes(exp.id) && (
              <Line
                key={exp.id}
                type="monotone"
                dataKey={exp.name}
                stroke={EXP_COLORS[i % EXP_COLORS.length]}
                strokeWidth={exp.id === activeExperimentId ? 2 : 1.5}
                strokeDasharray={exp.status === 'running' ? '5 3' : undefined}
                dot={false}
                animationDuration={400}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Experiment cards */}
      <div className="flex flex-col gap-3 overflow-y-auto flex-1">
        {experiments.map((exp, i) => {
          const color = EXP_COLORS[i % EXP_COLORS.length];
          const isActive = activeExperimentId === exp.id;
          const isSelected = selected.includes(exp.id);
          const hp = exp.hyperparams;

          return (
            <div
              key={exp.id}
              className={clsx(
                'panel p-4 flex flex-col gap-3 transition-all cursor-pointer',
                isSelected && 'ring-1',
                !isSelected && 'opacity-60',
              )}
              style={{ borderLeft: `3px solid ${color}`, ...(isSelected ? { '--tw-ring-color': color } as React.CSSProperties : {}) }}
              onClick={() => toggleExp(exp.id)}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <StatusIcon status={exp.status} />
                    <span className="font-semibold text-[13px] text-fl-text">{exp.name}</span>
                    {isActive && (
                      <span className="text-[9px] px-1.5 py-0.5 bg-blue-50 text-fl-primary border border-blue-200 rounded uppercase tracking-wide">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-fl-muted">{exp.description}</p>
                </div>
                <StatusBadge variant={exp.status} size="xs" pulse={exp.status === 'running'} />
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {exp.tags.map((tag) => (
                  <span key={tag} className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 bg-fl-secondary text-fl-muted rounded border border-fl-border">
                    <Tag size={8} />{tag}
                  </span>
                ))}
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-6 gap-3 pt-2 border-t border-fl-border">
                {[
                  { label: 'Best Acc',   value: exp.bestAccuracy > 0 ? `${(exp.bestAccuracy * 100).toFixed(2)}%` : '—' },
                  { label: 'Rounds',     value: `${exp.metrics.length} / ${hp.rounds}` },
                  { label: 'LR',         value: hp.learningRate.toString() },
                  { label: 'Agg',        value: hp.aggregation },
                  { label: 'Epochs',     value: hp.localEpochs.toString() },
                  { label: 'Duration',   value: duration(exp) },
                ].map((s) => (
                  <div key={s.label} className="flex flex-col gap-0.5">
                    <span className="text-[9px] uppercase tracking-widest text-fl-subtle">{s.label}</span>
                    <span className="font-mono text-[11px] font-medium text-fl-text">{s.value}</span>
                  </div>
                ))}
              </div>

              {/* Mini progress bar */}
              {exp.status === 'running' && (
                <div>
                  <div className="h-1 bg-fl-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${(exp.metrics.length / hp.rounds) * 100}%`, background: color }}
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
