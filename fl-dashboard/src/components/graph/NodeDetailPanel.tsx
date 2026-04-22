import React, { useMemo } from 'react';
import { X, Database, Clock, Cpu, TrendingUp, TrendingDown } from 'lucide-react';
import {
  LineChart, Line, ResponsiveContainer, Tooltip, YAxis,
} from 'recharts';
import { useFLStore } from '../../store/useFLStore';
import { StatusBadge } from '../common/StatusBadge';

function fmt(n: number, dec = 2) { return n.toFixed(dec); }
function fmtTime(ts: number) {
  const d = new Date(ts);
  return d.toLocaleTimeString('en-US', { hour12: false });
}

export function NodeDetailPanel() {
  const { selectedClientId, clients, roundHistory, selectClient } = useFLStore();
  const client = clients.find((c) => c.id === selectedClientId);

  // Build per-client history from global history with small noise
  const clientHistory = useMemo(() => {
    if (!client) return [];
    const seed = parseInt(client.id.replace('c', ''), 10) * 0.007;
    return roundHistory.map((r, i) => {
      const noise = Math.sin(i * 3.7 + seed) * 0.015;
      return {
        round: r.round,
        acc: Math.min(0.98, Math.max(0.3, client.accuracy - (roundHistory.length - 1 - i) * 0.0035 + noise)),
        loss: Math.max(0.05, client.loss + (roundHistory.length - 1 - i) * 0.012 - noise * 2),
      };
    });
  }, [client, roundHistory]);

  if (!client) return null;

  const accColor = client.accuracy >= 0.85 ? '#059669' : client.accuracy >= 0.70 ? '#D97706' : '#DC2626';

  return (
    <div className="absolute right-3 top-3 bottom-3 w-64 panel flex flex-col z-20 animate-slide-left">
      {/* Header */}
      <div className="panel-header shrink-0">
        <div className="flex flex-col min-w-0">
          <span className="panel-header-title">
            <span className="w-2 h-2 rounded-full shrink-0" style={{ background: accColor }} />
            {client.name}
          </span>
          <span className="text-[10px] text-fl-subtle mt-0.5 font-mono">{client.id.toUpperCase()} · {client.hospitalType}</span>
        </div>
        <button
          onClick={() => selectClient(null)}
          className="fl-btn-ghost p-1 rounded ml-2 shrink-0"
        >
          <X size={13} />
        </button>
      </div>

      {/* Status */}
      <div className="px-3 pt-3 pb-2 border-b border-fl-border shrink-0">
        <div className="flex items-center justify-between">
          <StatusBadge variant={client.status} pulse={client.status === 'training'} />
          <span className="text-[10px] text-fl-subtle font-mono">{fmtTime(client.lastUpdate)}</span>
        </div>
        <p className="text-[11px] text-fl-muted mt-1.5">{client.location}</p>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-px bg-fl-border border-b border-fl-border shrink-0">
        {[
          { label: 'Accuracy', value: `${(client.accuracy * 100).toFixed(2)}%`, color: accColor },
          { label: 'Loss',     value: fmt(client.loss, 4),    color: '#0F172A' },
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

      {/* Dataset */}
      <div className="px-3 py-2.5 border-b border-fl-border shrink-0">
        <div className="flex items-center justify-between text-[11px]">
          <span className="flex items-center gap-1.5 text-fl-muted"><Database size={11} />Dataset</span>
          <span className="font-mono font-medium">{client.datasetSize.toLocaleString()} samples</span>
        </div>
        <div className="flex items-center justify-between text-[11px] mt-1.5">
          <span className="flex items-center gap-1.5 text-fl-muted"><Cpu size={11} />Local Rounds</span>
          <span className="font-mono font-medium">{client.localRounds}</span>
        </div>
      </div>

      {/* Mini accuracy chart */}
      <div className="flex-1 min-h-0 p-3 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase tracking-widest text-fl-muted font-semibold">Local Accuracy</span>
          <TrendingUp size={11} color="#059669" />
        </div>
        {clientHistory.length > 1 ? (
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={clientHistory} margin={{ top: 4, right: 2, left: -30, bottom: 0 }}>
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 9, fontFamily: 'JetBrains Mono' }} />
                <Tooltip
                  contentStyle={{ fontSize: 10, fontFamily: 'JetBrains Mono', border: '1px solid #E2E8F0', borderRadius: 4, padding: '4px 8px' }}
                  formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, 'Acc']}
                  labelFormatter={(l) => `R${l}`}
                />
                <Line type="monotone" dataKey="acc" stroke={accColor} dot={false} strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-[11px] text-fl-subtle">
            Waiting for data…
          </div>
        )}
      </div>

      {/* Mini loss chart */}
      {clientHistory.length > 1 && (
        <div className="px-3 pb-3 h-24 flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-widest text-fl-muted font-semibold">Local Loss</span>
            <TrendingDown size={11} color="#DC2626" />
          </div>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={clientHistory} margin={{ top: 2, right: 2, left: -30, bottom: 0 }}>
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 9, fontFamily: 'JetBrains Mono' }} />
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
