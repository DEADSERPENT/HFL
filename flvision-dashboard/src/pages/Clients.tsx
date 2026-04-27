import React, { useState, useMemo } from 'react';
import { ArrowUpDown, Search, Database, Wifi, WifiOff, Shield } from 'lucide-react';
import clsx from 'clsx';
import { useFLStore } from '../store/useFLStore';
import { StatusBadge } from '../components/common/StatusBadge';
import { ClientNode, ECGClass } from '../types';

type SortKey = keyof Pick<ClientNode, 'name' | 'accuracy' | 'loss' | 'datasetSize' | 'latency' | 'localRounds' | 'epsilonSpent'>;

const CLASS_COLORS: Record<ECGClass, string> = {
  NORM: '#059669', MI: '#DC2626', STTC: '#2563EB', CD: '#D97706', HYP: '#7C3AED',
};

function AccBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="acc-bar-bg w-14">
        <div className="acc-bar-fill" style={{ width: `${value * 100}%`, background: color }} />
      </div>
      <span className="font-mono text-[11px]">{(value * 100).toFixed(2)}%</span>
    </div>
  );
}

function ClassPills({ dist }: { dist: ClientNode['classDist'] }) {
  const total = Object.values(dist).reduce((a, b) => a + b, 0);
  const top = (Object.entries(dist) as [ECGClass, number][])
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  return (
    <div className="flex gap-1 flex-wrap">
      {top.map(([cls, count]) => (
        <span key={cls} className="text-[8px] px-1.5 py-0.5 rounded font-mono font-semibold text-white"
          style={{ background: CLASS_COLORS[cls], opacity: 0.85 + (count / total) * 0.15 }}>
          {cls} {((count / total) * 100).toFixed(0)}%
        </span>
      ))}
    </div>
  );
}

export function Clients() {
  const { clients, edges, selectedClientId, selectClient, setPage } = useFLStore();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('accuracy');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [edgeFilter, setEdgeFilter] = useState<number | null>(null);

  const filtered = useMemo(() => {
    let arr = [...clients];
    if (edgeFilter !== null) arr = arr.filter((c) => c.edgeId === edgeFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      arr = arr.filter((c) =>
        c.name.toLowerCase().includes(q) || c.id.toLowerCase().includes(q) ||
        c.dominantClass.toLowerCase().includes(q)
      );
    }
    arr.sort((a, b) => {
      const av = a[sortKey] as number | string;
      const bv = b[sortKey] as number | string;
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return arr;
  }, [clients, search, sortKey, sortDir, edgeFilter]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('desc'); }
  };

  const SortHeader = ({ k, label }: { k: SortKey; label: string }) => (
    <th className="cursor-pointer select-none bg-fl-secondary" onClick={() => handleSort(k)}>
      <div className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-fl-muted p-3 whitespace-nowrap">
        {label}
        <ArrowUpDown size={9} className={clsx(sortKey === k ? 'text-fl-primary' : 'text-fl-subtle')} />
      </div>
    </th>
  );

  const totalData = clients.reduce((s, c) => s + c.datasetSize, 0);
  const avgAcc = clients.reduce((s, c) => s + c.accuracy, 0) / clients.length;
  const avgLat = clients.reduce((s, c) => s + c.latency, 0) / clients.length;
  const avgEps = clients.reduce((s, c) => s + c.epsilonSpent, 0) / clients.length;

  return (
    <div className="flex flex-col h-full overflow-hidden p-4 gap-4 page-enter">
      {/* Summary bar */}
      <div className="grid grid-cols-4 gap-3 shrink-0 stagger">
        {[
          { label: 'Total Devices', value: `${clients.length}`, sub: `${clients.filter(c => c.status !== 'idle' && c.status !== 'disconnected').length} active` },
          { label: 'Total Samples', value: totalData.toLocaleString(), sub: 'Dirichlet α=0.5 non-IID' },
          { label: 'Avg Accuracy', value: `${(avgAcc * 100).toFixed(2)}%`, sub: 'weighted FedAvg' },
          { label: 'Avg ε Spent', value: avgEps.toFixed(3), sub: `/ 1.0 · σ=1.1 · C=1.0` },
        ].map((s) => (
          <div key={s.label} className="panel px-4 py-3">
            <p className="text-[9px] uppercase tracking-widest text-fl-muted font-semibold">{s.label}</p>
            <p className="font-mono text-xl font-medium mt-0.5 text-fl-text">{s.value}</p>
            <p className="text-[10px] text-fl-subtle mt-0.5">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Edge filter tabs */}
      <div className="flex gap-2 shrink-0">
        {[null, 0, 1].map((edgeId) => {
          const label = edgeId === null ? 'All Devices' : `Edge-${edgeId === 0 ? 'A' : 'B'} (${edges[edgeId].name})`;
          const active = edgeFilter === edgeId;
          return (
            <button key={String(edgeId)} onClick={() => setEdgeFilter(edgeId)}
              className={clsx(
                'text-[11px] px-3 py-1.5 rounded border font-medium transition-all',
                active ? 'bg-fl-primary text-white border-fl-primary' : 'bg-fl-panel text-fl-muted border-fl-border hover:border-fl-primary',
              )}>
              {label}
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div className="panel flex-1 min-h-0 flex flex-col overflow-hidden">
        <div className="panel-header shrink-0">
          <span className="panel-header-title">
            <Database size={11} />
            Device Registry — partition_meta.json
          </span>
          <div className="relative">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-fl-subtle pointer-events-none" />
            <input value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Search devices…"
              className="fl-input py-1 text-xs h-7 w-48"
              style={{ paddingLeft: '28px' }} />
          </div>
        </div>

        <div className="overflow-auto flex-1">
          <table className="fl-table">
            <thead className="sticky top-0 z-10">
              <tr>
                <SortHeader k="name" label="Device" />
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide text-fl-muted bg-fl-secondary">Edge</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide text-fl-muted bg-fl-secondary">Status</th>
                <SortHeader k="accuracy" label="Accuracy" />
                <SortHeader k="loss" label="Loss" />
                <SortHeader k="datasetSize" label="Samples" />
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide text-fl-muted bg-fl-secondary whitespace-nowrap">ECG Classes</th>
                <SortHeader k="latency" label="Latency" />
                <SortHeader k="epsilonSpent" label="ε Spent" />
                <SortHeader k="localRounds" label="Rounds" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => {
                const accColor = c.accuracy >= 0.80 ? '#059669' : c.accuracy >= 0.68 ? '#D97706' : '#DC2626';
                const isSelected = selectedClientId === c.id;
                const edge = edges[c.edgeId];
                return (
                  <tr key={c.id}
                    onClick={() => { selectClient(isSelected ? null : c.id); setPage('dashboard'); }}
                    className={clsx('cursor-pointer transition-colors', isSelected && 'bg-blue-50')}>
                    <td className="px-3 py-2.5">
                      <div className="flex flex-col">
                        <span className="font-semibold text-[12px]">{c.name}</span>
                        <span className="text-[9px] text-fl-subtle font-mono">{c.id}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold text-white"
                        style={{ background: '#7C3AED' }}>
                        {edge.name}
                      </span>
                    </td>
                    <td className="px-3 py-2.5"><StatusBadge variant={c.status} size="xs" /></td>
                    <td className="px-3 py-2.5"><AccBar value={c.accuracy} color={accColor} /></td>
                    <td className="px-3 py-2.5 font-mono text-[11px]">{c.loss.toFixed(4)}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex flex-col">
                        <span className="font-mono text-[11px]">{c.datasetSize.toLocaleString()}</span>
                        <span className="text-[9px] text-fl-subtle font-mono">{c.nTrain}/{c.nVal}/{c.nTest}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5"><ClassPills dist={c.classDist} /></td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1.5">
                        {c.status === 'disconnected'
                          ? <WifiOff size={10} className="text-fl-danger" />
                          : <Wifi size={10} className="text-fl-green" />}
                        <span className="font-mono text-[11px]">{c.latency.toFixed(0)}ms</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <Shield size={10} className={c.epsilonSpent > 0.8 ? 'text-fl-danger' : 'text-fl-green'} />
                        <span className={clsx('font-mono text-[11px]', c.epsilonSpent > 0.8 && 'text-fl-danger')}>
                          {c.epsilonSpent.toFixed(3)}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 font-mono text-[11px]">{c.localRounds}</td>
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
