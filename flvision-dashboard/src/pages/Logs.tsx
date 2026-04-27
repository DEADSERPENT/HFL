import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Search, Download, Trash2, ChevronDown } from 'lucide-react';
import clsx from 'clsx';
import { useFLStore } from '../store/useFLStore';
import { LogType } from '../types';

const TYPE_STYLES: Record<LogType, { dot: string; badge: string; row: string }> = {
  info:    { dot: 'bg-blue-500',     badge: 'bg-blue-50 text-blue-700 border-blue-200',       row: '' },
  success: { dot: 'bg-emerald-500',  badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', row: 'bg-emerald-50/30' },
  warning: { dot: 'bg-amber-500',    badge: 'bg-amber-50 text-amber-700 border-amber-200',    row: 'bg-amber-50/30' },
  error:   { dot: 'bg-red-500',      badge: 'bg-red-50 text-red-700 border-red-200',          row: 'bg-red-50/30' },
  debug:   { dot: 'bg-slate-400',    badge: 'bg-slate-100 text-slate-500 border-slate-200',   row: '' },
};

const ALL_TYPES: LogType[] = ['info', 'success', 'warning', 'error', 'debug'];

function fmtFull(ts: number) {
  return new Date(ts).toLocaleString('en-US', {
    month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  });
}

export function Logs() {
  const { logs, clearLogs } = useFLStore();
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<Set<LogType>>(new Set(ALL_TYPES));
  const [sourceFilter, setSourceFilter] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const topRef = useRef<HTMLDivElement>(null);

  const sources = useMemo(() => Array.from(new Set(logs.map((l) => l.source))).sort(), [logs]);

  const filtered = useMemo(() => {
    return logs.filter((l) => {
      if (!filters.has(l.type)) return false;
      if (sourceFilter && l.source !== sourceFilter) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        if (!l.message.toLowerCase().includes(q) && !l.source.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [logs, filters, search, sourceFilter]);

  useEffect(() => {
    if (autoScroll) topRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs.length, autoScroll]);

  const toggleFilter = (t: LogType) => {
    setFilters((prev) => {
      const next = new Set(prev);
      next.has(t) ? next.delete(t) : next.add(t);
      return next.size === 0 ? new Set(ALL_TYPES) : next;
    });
  };

  const downloadLogs = () => {
    const text = filtered.map((l) =>
      `[${fmtFull(l.timestamp)}] [${l.type.toUpperCase().padEnd(7)}] [${l.source.padEnd(20)}] ${l.message}`
    ).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `fedvision-logs-${Date.now()}.txt`;
    a.click();
  };

  const counts = useMemo(() => {
    const c: Partial<Record<LogType, number>> = {};
    logs.forEach((l) => { c[l.type] = (c[l.type] ?? 0) + 1; });
    return c;
  }, [logs]);

  return (
    <div className="flex flex-col h-full overflow-hidden p-4 gap-4 page-enter">
      {/* Summary stats */}
      <div className="grid grid-cols-5 gap-3 shrink-0 stagger">
        {ALL_TYPES.map((t) => {
          const s = TYPE_STYLES[t];
          return (
            <button
              key={t}
              onClick={() => toggleFilter(t)}
              className={clsx(
                'panel px-3 py-2.5 flex items-center gap-2.5 text-left transition-all',
                !filters.has(t) && 'opacity-40',
              )}
            >
              <span className={clsx('w-2.5 h-2.5 rounded-full shrink-0', s.dot)} />
              <div>
                <p className="text-[9px] uppercase tracking-widest text-fl-muted font-semibold">{t}</p>
                <p className="font-mono text-base font-medium text-fl-text">{counts[t] ?? 0}</p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Toolbar */}
      <div className="panel shrink-0">
        <div className="panel-header">
          <span className="panel-header-title">Event Log — {filtered.length} / {logs.length} entries</span>
          <div className="flex items-center gap-2">
            {/* Search */}
            <div className="relative">
              <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-fl-subtle" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search messages…"
                className="fl-input pl-7 h-7 w-56 text-[11px] py-1"
              />
            </div>

            {/* Source filter */}
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="fl-select h-7 text-[11px]"
            >
              <option value="">All sources</option>
              {sources.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>

            {/* Auto-scroll */}
            <button
              onClick={() => setAutoScroll((a) => !a)}
              className={clsx('fl-btn fl-btn-secondary text-[11px] h-7 px-2 py-0', autoScroll && 'border-fl-primary text-fl-primary')}
            >
              <ChevronDown size={11} /> Auto
            </button>

            <button onClick={downloadLogs} className="fl-btn fl-btn-secondary text-[11px] h-7 px-2 py-0">
              <Download size={11} /> Export
            </button>
            <button onClick={clearLogs} className="fl-btn fl-btn-secondary text-[11px] h-7 px-2 py-0 text-fl-danger">
              <Trash2 size={11} />
            </button>
          </div>
        </div>
      </div>

      {/* Log table */}
      <div className="panel flex-1 min-h-0 overflow-hidden flex flex-col">
        <div className="grid text-[9px] uppercase tracking-widest text-fl-muted font-semibold px-4 py-2 bg-fl-secondary border-b border-fl-border shrink-0"
          style={{ gridTemplateColumns: '140px 60px 140px 1fr 40px' }}>
          <span>Timestamp</span>
          <span>Type</span>
          <span>Source</span>
          <span>Message</span>
          <span>Round</span>
        </div>

        <div className="overflow-y-auto flex-1 divide-y divide-fl-border/50">
          <div ref={topRef} />
          {filtered.length === 0 ? (
            <div className="flex items-center justify-center h-24 text-[11px] text-fl-subtle">
              No log entries match the current filters.
            </div>
          ) : (
            filtered.map((entry) => {
              const s = TYPE_STYLES[entry.type];
              return (
                <div
                  key={entry.id}
                  className={clsx(
                    'grid items-start px-4 py-2 hover:bg-fl-secondary/50 transition-colors gap-3',
                    s.row,
                  )}
                  style={{ gridTemplateColumns: '140px 60px 140px 1fr 40px' }}
                >
                  <span className="font-mono text-[10px] text-fl-subtle pt-0.5">
                    {fmtFull(entry.timestamp)}
                  </span>
                  <span className={clsx(
                    'text-[9px] uppercase font-semibold tracking-wide px-1.5 py-0.5 rounded border self-start',
                    s.badge,
                  )}>
                    {entry.type}
                  </span>
                  <span className="text-[11px] font-medium text-fl-muted truncate pt-0.5">{entry.source}</span>
                  <span className="font-mono text-[11px] text-fl-text leading-relaxed">{entry.message}</span>
                  <span className="font-mono text-[10px] text-fl-subtle pt-0.5">
                    {entry.round !== undefined ? `R${entry.round}` : ''}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
