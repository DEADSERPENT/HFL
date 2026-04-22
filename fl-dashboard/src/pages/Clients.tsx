import React, { useState, useMemo } from 'react';
import { ArrowUpDown, Search, Database, Wifi, WifiOff } from 'lucide-react';
import clsx from 'clsx';
import { useFLStore } from '../store/useFLStore';
import { StatusBadge } from '../components/common/StatusBadge';
import { ClientNode } from '../types';

type SortKey = keyof Pick<ClientNode, 'name' | 'accuracy' | 'loss' | 'datasetSize' | 'latency' | 'localRounds'>;

function AccBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="acc-bar-bg w-16">
        <div className="acc-bar-fill" style={{ width: `${value * 100}%`, background: color }} />
      </div>
      <span className="font-mono text-[11px]">{(value * 100).toFixed(2)}%</span>
    </div>
  );
}

export function Clients() {
  const { clients, selectedClientId, selectClient, setPage } = useFLStore();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('accuracy');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const filtered = useMemo(() => {
    let arr = [...clients];
    if (search.trim()) {
      const q = search.toLowerCase();
      arr = arr.filter((c) =>
        c.name.toLowerCase().includes(q) ||
        c.hospitalType.toLowerCase().includes(q) ||
        c.location.toLowerCase().includes(q)
      );
    }
    arr.sort((a, b) => {
      const av = a[sortKey] as number | string;
      const bv = b[sortKey] as number | string;
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return arr;
  }, [clients, search, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('desc'); }
  };

  const SortHeader = ({ k, label }: { k: SortKey; label: string }) => (
    <th className="cursor-pointer select-none" onClick={() => handleSort(k)}>
      <div className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-fl-muted p-3">
        {label}
        <ArrowUpDown size={10} className={clsx(sortKey === k ? 'text-fl-primary' : 'text-fl-subtle')} />
      </div>
    </th>
  );

  const totalData = clients.reduce((s, c) => s + c.datasetSize, 0);
  const avgAcc = clients.reduce((s, c) => s + c.accuracy, 0) / clients.length;
  const avgLat = clients.reduce((s, c) => s + c.latency, 0) / clients.length;

  return (
    <div className="flex flex-col h-full overflow-hidden p-4 gap-4 page-enter">
      {/* Summary bar */}
      <div className="grid grid-cols-4 gap-3 shrink-0 stagger">
        {[
          { label: 'Total Clients', value: `${clients.length}`, sub: `${clients.filter(c => c.status === 'active' || c.status === 'training').length} active` },
          { label: 'Total Samples', value: totalData.toLocaleString(), sub: 'across federation' },
          { label: 'Avg Accuracy',  value: `${(avgAcc * 100).toFixed(2)}%`, sub: 'weighted mean' },
          { label: 'Avg Latency',   value: `${avgLat.toFixed(0)}ms`, sub: 'round-trip' },
        ].map((s) => (
          <div key={s.label} className="panel px-4 py-3">
            <p className="text-[9px] uppercase tracking-widest text-fl-muted font-semibold">{s.label}</p>
            <p className="font-mono text-xl font-medium mt-0.5 text-fl-text">{s.value}</p>
            <p className="text-[10px] text-fl-subtle mt-0.5">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="panel flex-1 min-h-0 flex flex-col overflow-hidden">
        <div className="panel-header shrink-0">
          <span className="panel-header-title">
            <Database size={11} />
            Client Registry
          </span>
          <div className="relative">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-fl-subtle" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search clients…"
              className="fl-input pl-7 py-1 text-xs h-7 w-52"
            />
          </div>
        </div>

        <div className="overflow-auto flex-1">
          <table className="fl-table">
            <thead className="sticky top-0 z-10">
              <tr>
                <SortHeader k="name" label="Client" />
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide text-fl-muted bg-fl-secondary">Type</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide text-fl-muted bg-fl-secondary">Status</th>
                <SortHeader k="accuracy" label="Accuracy" />
                <SortHeader k="loss" label="Loss" />
                <SortHeader k="datasetSize" label="Samples" />
                <SortHeader k="latency" label="Latency" />
                <SortHeader k="localRounds" label="Rounds" />
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide text-fl-muted bg-fl-secondary">‖∇‖</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => {
                const accColor = c.accuracy >= 0.85 ? '#059669' : c.accuracy >= 0.70 ? '#D97706' : '#DC2626';
                const isSelected = selectedClientId === c.id;
                return (
                  <tr
                    key={c.id}
                    onClick={() => { selectClient(isSelected ? null : c.id); setPage('dashboard'); }}
                    className={clsx('cursor-pointer transition-colors', isSelected && 'bg-blue-50')}
                  >
                    <td className="px-3 py-2.5">
                      <div className="flex flex-col">
                        <span className="font-medium text-[12px]">{c.name}</span>
                        <span className="text-[10px] text-fl-subtle font-mono">{c.id} · {c.location}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-[11px] text-fl-muted">{c.hospitalType}</td>
                    <td className="px-3 py-2.5"><StatusBadge variant={c.status} size="xs" /></td>
                    <td className="px-3 py-2.5"><AccBar value={c.accuracy} color={accColor} /></td>
                    <td className="px-3 py-2.5 font-mono text-[11px]">{c.loss.toFixed(4)}</td>
                    <td className="px-3 py-2.5 font-mono text-[11px]">{c.datasetSize.toLocaleString()}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1.5">
                        {c.status === 'disconnected'
                          ? <WifiOff size={11} className="text-fl-danger" />
                          : <Wifi size={11} className="text-fl-green" />
                        }
                        <span className="font-mono text-[11px]">{c.latency.toFixed(0)}ms</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 font-mono text-[11px]">{c.localRounds}</td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-fl-accent">{c.gradientNorm.toFixed(3)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
