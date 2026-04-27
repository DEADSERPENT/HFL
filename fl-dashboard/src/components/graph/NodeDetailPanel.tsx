import React, { useMemo } from 'react';
import { X, Database, Cpu, TrendingUp, TrendingDown, Shield } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis } from 'recharts';
import { useFLStore } from '../../store/useFLStore';
import { StatusBadge } from '../common/StatusBadge';
import { ECGClass } from '../../types';

const CLASS_COLORS: Record<ECGClass, string> = {
  NORM: '#059669', MI: '#DC2626', STTC: '#2563EB', CD: '#D97706', HYP: '#7C3AED',
};

function fmt(n: number, dec = 2) { return n.toFixed(dec); }
function fmtTime(ts: number) {
  return new Date(ts).toLocaleTimeString('en-US', { hour12: false });
}

export function NodeDetailPanel() {
  const { selectedClientId, clients, roundHistory, selectClient } = useFLStore();
  const client = clients.find((c) => c.id === selectedClientId);

  const clientHistory = useMemo(() => {
    if (!client) return [];
    const seed = parseInt(client.id.replace('device_', ''), 10) * 0.009;
    return roundHistory.map((r, i) => {
      const noise = Math.sin(i * 3.7 + seed) * 0.013;
      return {
        round: r.round,
        acc: Math.min(0.97, Math.max(0.3, client.accuracy - (roundHistory.length - 1 - i) * 0.004 + noise)),
        loss: Math.max(0.05, client.loss + (roundHistory.length - 1 - i) * 0.011 - noise * 2),
      };
    });
  }, [client, roundHistory]);

  if (!client) return null;

  const color = client.accuracy >= 0.80 ? '#059669' : client.accuracy >= 0.68 ? '#D97706' : '#DC2626';
  const edgeName = `Edge-${client.edgeId === 0 ? 'A' : 'B'}`;
  const totalClassSamples = Object.values(client.classDist).reduce((a, b) => a + b, 0);
  const classEntries = (Object.entries(client.classDist) as [ECGClass, number][])
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1]);

  return (
    <div className="absolute right-3 top-3 bottom-3 w-64 panel flex flex-col z-20 animate-slide-left">
      {/* Header */}
      <div className="panel-header shrink-0">
        <div className="flex flex-col min-w-0">
          <span className="panel-header-title">
            <span className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
            {client.name}
          </span>
          <span className="text-[10px] text-fl-subtle mt-0.5 font-mono">
            {client.id} · {edgeName} · {client.dominantClass}-dominant
          </span>
        </div>
        <button onClick={() => selectClient(null)} className="fl-btn-ghost p-1 rounded ml-2 shrink-0">
          <X size={13} />
        </button>
      </div>

      {/* Status */}
      <div className="px-3 pt-3 pb-2 border-b border-fl-border shrink-0">
        <div className="flex items-center justify-between">
          <StatusBadge variant={client.status} pulse={client.status === 'training'} />
          <span className="text-[10px] text-fl-subtle font-mono">{fmtTime(client.lastUpdate)}</span>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-px bg-fl-border border-b border-fl-border shrink-0">
        {[
          { label: 'Accuracy', value: `${(client.accuracy * 100).toFixed(2)}%`, color },
          { label: 'Loss',     value: fmt(client.loss, 4), color: '#0F172A' },
          { label: 'Latency',  value: `${fmt(client.latency, 0)}ms`, color: '#0F172A' },
          { label: '‖∇‖ Norm', value: fmt(client.gradientNorm, 3), color: '#7C3AED' },
        ].map((m) => (
          <div key={m.label} className="bg-fl-panel p-3 flex flex-col gap-1">
            <span className="text-[9px] uppercase tracking-widest text-fl-subtle">{m.label}</span>
            <span className="font-mono text-base font-medium leading-none" style={{ color: m.color }}>
              {m.value}
            </span>
          </div>
        ))}
      </div>

      {/* Dataset + privacy */}
      <div className="px-3 py-2.5 border-b border-fl-border shrink-0 flex flex-col gap-1.5">
        <div className="flex justify-between text-[11px]">
          <span className="flex items-center gap-1.5 text-fl-muted"><Database size={10} />Total samples</span>
          <span className="font-mono font-medium">{client.datasetSize.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-fl-muted font-mono pl-4">train/val/test</span>
          <span className="font-mono text-fl-subtle">{client.nTrain}/{client.nVal}/{client.nTest}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="flex items-center gap-1.5 text-fl-muted"><Cpu size={10} />Local rounds</span>
          <span className="font-mono font-medium">{client.localRounds}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="flex items-center gap-1.5 text-fl-muted"><Shield size={10} />ε spent</span>
          <span className="font-mono font-medium" style={{ color: client.epsilonSpent > 0.8 ? '#DC2626' : '#059669' }}>
            {client.epsilonSpent.toFixed(3)} / 1.0
          </span>
        </div>
        {/* ε progress bar */}
        <div className="h-1 bg-fl-secondary rounded-full overflow-hidden">
          <div className="h-full rounded-full transition-all duration-500"
            style={{ width: `${client.epsilonSpent * 100}%`, background: client.epsilonSpent > 0.8 ? '#DC2626' : '#2563EB' }} />
        </div>
      </div>

      {/* Class distribution */}
      <div className="px-3 py-2.5 border-b border-fl-border shrink-0">
        <p className="text-[9px] uppercase tracking-widest text-fl-subtle mb-2 font-semibold">ECG Class Distribution</p>
        <div className="flex flex-col gap-1">
          {classEntries.map(([cls, count]) => {
            const pct = count / totalClassSamples;
            return (
              <div key={cls} className="flex items-center gap-2">
                <span className="font-mono text-[9px] w-9 text-fl-muted">{cls}</span>
                <div className="flex-1 h-1.5 bg-fl-secondary rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${pct * 100}%`, background: CLASS_COLORS[cls] }} />
                </div>
                <span className="font-mono text-[9px] text-fl-subtle w-7 text-right">{(pct * 100).toFixed(0)}%</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Accuracy chart */}
      <div className="flex-1 min-h-0 p-3 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase tracking-widest text-fl-muted font-semibold">Local Accuracy</span>
          <TrendingUp size={11} color="#059669" />
        </div>
        {clientHistory.length > 1 ? (
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={clientHistory} margin={{ top: 4, right: 2, left: -30, bottom: 0 }}>
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 8, fontFamily: 'JetBrains Mono' }} />
                <Tooltip
                  contentStyle={{ fontSize: 10, fontFamily: 'JetBrains Mono', border: '1px solid #E2E8F0', borderRadius: 4, padding: '4px 8px' }}
                  formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, 'Acc']}
                  labelFormatter={(l) => `R${l}`}
                />
                <Line type="monotone" dataKey="acc" stroke={color} dot={false} strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-[11px] text-fl-subtle">
            Waiting for training data…
          </div>
        )}
      </div>

      {/* Loss chart */}
      {clientHistory.length > 1 && (
        <div className="px-3 pb-3 h-20 flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-widest text-fl-muted font-semibold">Local Loss</span>
            <TrendingDown size={11} color="#DC2626" />
          </div>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={clientHistory} margin={{ top: 2, right: 2, left: -30, bottom: 0 }}>
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 8, fontFamily: 'JetBrains Mono' }} />
                <Tooltip
                  contentStyle={{ fontSize: 10, fontFamily: 'JetBrains Mono', border: '1px solid #E2E8F0', borderRadius: 4, padding: '4px 8px' }}
                  formatter={(v: number) => [v.toFixed(4), 'Loss']}
                  labelFormatter={(l) => `R${l}`}
                />
                <Line type="monotone" dataKey="loss" stroke="#DC2626" dot={false} strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
