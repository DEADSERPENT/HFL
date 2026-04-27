import React, { useState, useMemo } from 'react';
import { FlaskConical, CheckCircle2, XCircle, PauseCircle, Tag, Shield, Zap } from 'lucide-react';
import clsx from 'clsx';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts';
import { useFLStore } from '../store/useFLStore';
import { StatusBadge } from '../components/common/StatusBadge';
import { ExperimentRun } from '../types';

// Colors aligned with RUNBOOK baseline ordering B0-B5, P1
const EXP_COLORS: Record<string, string> = {
  b0: '#94A3B8', b1: '#CBD5E1', b2: '#2563EB', b3: '#0EA5E9',
  b4: '#D97706', b5: '#7C3AED', p1: '#059669',
};

function duration(exp: ExperimentRun): string {
  const end = exp.endTime ?? Date.now();
  const s = Math.floor((end - exp.startTime) / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

function StatusIcon({ status }: { status: ExperimentRun['status'] }) {
  if (status === 'completed') return <CheckCircle2 size={13} className="text-fl-green" />;
  if (status === 'failed')    return <XCircle size={13} className="text-fl-danger" />;
  if (status === 'paused')    return <PauseCircle size={13} className="text-fl-warning" />;
  return <FlaskConical size={13} className="text-fl-primary training-dot" />;
}

// QoS targets from RUNBOOK
const QOS_TARGETS = [
  { label: 'B0 (ceiling)', value: 85.0, color: '#94A3B8' },
  { label: 'B4 DP-FedAvg', value: 82.0, color: '#D97706' },
  { label: 'P1 Target ≥83%', value: 83.0, color: '#059669' },
];

export function Experiments() {
  const { experiments, activeExperimentId } = useFLStore();
  const [selected, setSelected] = useState<string[]>(experiments.map((e) => e.id));
  const [metric, setMetric] = useState<'globalAccuracy' | 'globalLoss' | 'epsilonSpent'>('globalAccuracy');

  const maxRound = useMemo(() =>
    Math.max(...experiments.map((e) => e.metrics.length), 1), [experiments]);

  const chartData = useMemo(() => {
    const rows: Record<string, number | string>[] = [];
    for (let r = 1; r <= maxRound; r++) {
      const row: Record<string, number | string> = { round: r };
      experiments.forEach((exp) => {
        if (!selected.includes(exp.id)) return;
        const m = exp.metrics[r - 1];
        if (!m) return;
        const v = metric === 'globalAccuracy' ? parseFloat((m.globalAccuracy * 100).toFixed(3))
          : metric === 'globalLoss' ? parseFloat(m.globalLoss.toFixed(5))
          : parseFloat(m.epsilonSpent.toFixed(4));
        row[exp.shortName] = v;
      });
      rows.push(row);
    }
    return rows;
  }, [experiments, selected, metric, maxRound]);

  const toggleExp = (id: string) =>
    setSelected((prev) => prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]);

  const fmtVal = (v: number) =>
    metric === 'globalAccuracy' ? `${v.toFixed(2)}%`
    : metric === 'globalLoss' ? v.toFixed(5)
    : v.toFixed(4);

  // Accuracy delta: P1 best vs B4 (fairest DP comparison)
  const p1 = experiments.find((e) => e.id === 'p1');
  const b4 = experiments.find((e) => e.id === 'b4');
  const b0 = experiments.find((e) => e.id === 'b0');
  const accLoss = p1 && b0 && p1.bestAccuracy > 0
    ? (b0.bestAccuracy - p1.bestAccuracy) * 100 : null;

  return (
    <div className="flex flex-col h-full overflow-hidden p-4 gap-4 page-enter">
      {/* QoS summary strip */}
      {p1 && p1.bestAccuracy > 0 && (
        <div className="grid grid-cols-4 gap-2 shrink-0 stagger">
          {[
            { label: 'P1 Best Acc', value: `${(p1.bestAccuracy * 100).toFixed(2)}%`, target: '≥83%', ok: p1.bestAccuracy >= 0.83 },
            { label: 'Acc Loss vs B0', value: accLoss !== null ? `${accLoss.toFixed(2)}%` : '—', target: '≤2%', ok: accLoss !== null && accLoss <= 2 },
            { label: 'P1 vs B4 DP-FL', value: p1 && b4 && b4.bestAccuracy > 0 ? `+${((p1.bestAccuracy - b4.bestAccuracy) * 100).toFixed(2)}%` : '—', target: 'P1 > B4', ok: p1.bestAccuracy > (b4?.bestAccuracy ?? 0) },
            { label: 'Privacy ε', value: '1.0', target: '≤1.0 δ=1e-5', ok: true },
          ].map((s) => (
            <div key={s.label} className={clsx('panel px-3 py-2.5 border-l-2', s.ok ? 'border-fl-green' : 'border-fl-danger')}>
              <p className="text-[9px] uppercase tracking-widest text-fl-muted font-semibold">{s.label}</p>
              <p className="font-mono text-base font-semibold mt-0.5" style={{ color: s.ok ? '#059669' : '#DC2626' }}>{s.value}</p>
              <p className="text-[9px] text-fl-subtle mt-0.5">target: {s.target}</p>
            </div>
          ))}
        </div>
      )}

      {/* Comparison chart */}
      <div className="panel p-4 shrink-0" style={{ height: 270 }}>
        <div className="flex items-center justify-between mb-3">
          <span className="panel-header-title">
            <FlaskConical size={11} />
            B0–B5 Baseline Comparison + P1 HFL-MM-HC
          </span>
          <div className="flex gap-1">
            {(['globalAccuracy', 'globalLoss', 'epsilonSpent'] as const).map((m) => (
              <button key={m} onClick={() => setMetric(m)}
                className={clsx(
                  'text-[10px] px-2 py-1 rounded border transition-all',
                  metric === m ? 'bg-fl-primary text-white border-fl-primary' : 'bg-fl-secondary text-fl-muted border-fl-border hover:border-fl-primary',
                )}>
                {m === 'globalAccuracy' ? 'Accuracy' : m === 'globalLoss' ? 'Loss' : 'ε Spent'}
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height="85%">
          <LineChart data={chartData} margin={{ top: 4, right: 16, left: -8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
            <XAxis dataKey="round" tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
              tickLine={false} axisLine={false} label={{ value: 'Round', position: 'insideBottom', offset: -1, fontSize: 9, fill: '#94A3B8' }} />
            <YAxis tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#94A3B8' }}
              tickLine={false} axisLine={false}
              tickFormatter={(v) => metric === 'globalAccuracy' ? `${v}%` : v.toFixed(3)} />
            <Tooltip
              contentStyle={{ border: '1px solid #E2E8F0', borderRadius: 6, padding: '5px 10px', fontFamily: 'JetBrains Mono', fontSize: 10 }}
              formatter={(v: number, name: string) => [fmtVal(v), name]}
              labelFormatter={(l) => `Round ${l}`}
            />
            <Legend wrapperStyle={{ fontSize: 10, fontFamily: 'Plus Jakarta Sans' }} />
            {/* P1 target reference line */}
            {metric === 'globalAccuracy' && (
              <ReferenceLine y={83} stroke="#059669" strokeDasharray="4 4" strokeOpacity={0.5}
                label={{ value: 'P1 target 83%', position: 'right', fontSize: 8, fill: '#059669' }} />
            )}
            {experiments.map((exp) => selected.includes(exp.id) && (
              <Line key={exp.id} type="monotone" dataKey={exp.shortName}
                stroke={EXP_COLORS[exp.id] ?? '#94A3B8'}
                strokeWidth={exp.id === activeExperimentId ? 2.5 : exp.id === 'b0' ? 1.5 : 1.5}
                strokeDasharray={exp.status === 'running' ? '6 3' : exp.id === 'b0' || exp.id === 'b1' ? '3 3' : undefined}
                dot={false} animationDuration={300}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Experiment cards */}
      <div className="flex flex-col gap-3 overflow-y-auto flex-1">
        {experiments.map((exp) => {
          const color = EXP_COLORS[exp.id] ?? '#94A3B8';
          const isActive = activeExperimentId === exp.id;
          const isSel = selected.includes(exp.id);
          const hp = exp.hyperparams;

          return (
            <div key={exp.id}
              className={clsx(
                'panel p-4 flex flex-col gap-3 transition-all cursor-pointer',
                !isSel && 'opacity-50',
              )}
              style={{ borderLeft: `3px solid ${color}` }}
              onClick={() => toggleExp(exp.id)}>
              {/* Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <StatusIcon status={exp.status} />
                    <span className="font-mono text-[11px] font-bold px-1.5 py-0.5 rounded text-white"
                      style={{ background: color }}>{exp.shortName}</span>
                    <span className="font-semibold text-[13px] text-fl-text">{exp.name.replace(/^[A-Z][0-9]? — /, '')}</span>
                    {isActive && (
                      <span className="text-[9px] px-1.5 py-0.5 bg-green-50 text-fl-green border border-green-200 rounded uppercase tracking-wide font-semibold">
                        Active
                      </span>
                    )}
                    {exp.privacyEnabled && (
                      <span className="text-[9px] px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded flex items-center gap-1">
                        <Shield size={8} /> DP ε={hp.privacyBudget}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-fl-muted leading-relaxed">{exp.description}</p>
                </div>
                <StatusBadge variant={exp.status} size="xs" pulse={exp.status === 'running'} />
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {exp.tags.map((tag) => (
                  <span key={tag} className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 bg-fl-secondary text-fl-muted rounded border border-fl-border">
                    <Tag size={7} />{tag}
                  </span>
                ))}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-7 gap-3 pt-2 border-t border-fl-border">
                {[
                  { label: 'Best Acc', value: exp.bestAccuracy > 0 ? `${(exp.bestAccuracy * 100).toFixed(2)}%` : '—', ok: exp.bestAccuracy >= exp.targetAccuracy },
                  { label: 'Target',   value: `${(exp.targetAccuracy * 100).toFixed(0)}%`, ok: null },
                  { label: 'Rounds',   value: `${exp.metrics.length}/${hp.rounds}`, ok: null },
                  { label: 'Agg',      value: hp.aggregation, ok: null },
                  { label: 'τ_e',      value: `${hp.tauE}`, ok: null },
                  { label: 'ε',        value: exp.privacyEnabled ? `${hp.privacyBudget}` : '∞', ok: null },
                  { label: 'Duration', value: duration(exp), ok: null },
                ].map((s) => (
                  <div key={s.label} className="flex flex-col gap-0.5">
                    <span className="text-[9px] uppercase tracking-widest text-fl-subtle">{s.label}</span>
                    <span className={clsx(
                      'font-mono text-[11px] font-semibold',
                      s.ok === true ? 'text-fl-green' : s.ok === false ? 'text-fl-danger' : 'text-fl-text',
                    )}>{s.value}</span>
                  </div>
                ))}
              </div>

              {/* Progress bar for running */}
              {exp.status === 'running' && (
                <div>
                  <div className="h-1 bg-fl-secondary rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${(exp.metrics.length / hp.rounds) * 100}%`, background: color }} />
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
