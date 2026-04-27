import React, { useEffect, useRef, useState, useMemo } from 'react';
import clsx from 'clsx';
import { Filter, Trash2, ChevronDown } from 'lucide-react';
import { useFLStore } from '../../store/useFLStore';
import { LogType } from '../../types';

const TYPE_COLORS: Record<LogType, { bg: string; text: string; dot: string }> = {
  info:    { bg: 'bg-blue-50',    text: 'text-blue-700',    dot: 'bg-blue-500' },
  success: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' },
  warning: { bg: 'bg-amber-50',   text: 'text-amber-700',   dot: 'bg-amber-500' },
  error:   { bg: 'bg-red-50',     text: 'text-red-700',     dot: 'bg-red-500' },
  debug:   { bg: 'bg-slate-100',  text: 'text-slate-500',   dot: 'bg-slate-400' },
};

const ALL_TYPES: LogType[] = ['info', 'success', 'warning', 'error', 'debug'];

function fmtTs(ts: number) {
  return new Date(ts).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

interface Props {
  maxHeight?: number;
  compact?: boolean;
}

export function LogPanel({ maxHeight = 200, compact = false }: Props) {
  const { logs, clearLogs } = useFLStore();
  const [activeFilters, setActiveFilters] = useState<Set<LogType>>(new Set(ALL_TYPES));
  const [search, setSearch] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevCountRef = useRef(0);

  const filtered = useMemo(() => {
    let result = logs.filter((l) => activeFilters.has(l.type));
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (l) => l.message.toLowerCase().includes(q) || l.source.toLowerCase().includes(q)
      );
    }
    return result;
  }, [logs, activeFilters, search]);

  // Auto-scroll
  useEffect(() => {
    if (!autoScroll) return;
    if (logs.length !== prevCountRef.current) {
      prevCountRef.current = logs.length;
      scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [logs.length, autoScroll]);

  const toggleFilter = (t: LogType) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(t)) { next.delete(t); } else { next.add(t); }
      if (next.size === 0) return new Set(ALL_TYPES);
      return next;
    });
  };

  return (
    <div className="panel flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="panel-header shrink-0">
        <div className="flex items-center gap-3">
          <span className="panel-header-title">
            <span className="w-1.5 h-1.5 rounded-full bg-fl-green training-dot" />
            System Logs
          </span>
          <span className="text-[10px] font-mono text-fl-subtle">{logs.length} entries</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Search */}
          {!compact && (
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter logs…"
              className="fl-input text-[11px] py-1 px-2 w-36 h-6"
            />
          )}
          {/* Type filters */}
          <div className="flex items-center gap-1">
            {ALL_TYPES.map((t) => {
              const c = TYPE_COLORS[t];
              const active = activeFilters.has(t);
              return (
                <button
                  key={t}
                  onClick={() => toggleFilter(t)}
                  className={clsx(
                    'text-[9px] uppercase tracking-wide px-1.5 py-0.5 rounded border transition-all',
                    active ? `${c.bg} ${c.text} border-current` : 'bg-transparent text-fl-subtle border-fl-border'
                  )}
                >
                  {t}
                </button>
              );
            })}
          </div>
          <button onClick={clearLogs} className="fl-btn-ghost p-1 rounded" title="Clear logs">
            <Trash2 size={12} />
          </button>
          <button
            onClick={() => setAutoScroll((a) => !a)}
            className={clsx('fl-btn-ghost p-1 rounded', autoScroll && 'text-fl-primary')}
            title="Auto-scroll"
          >
            <ChevronDown size={12} />
          </button>
        </div>
      </div>

      {/* Log entries */}
      <div
        ref={scrollRef}
        className="overflow-y-auto flex-1 divide-y divide-fl-border"
        style={{ maxHeight: compact ? maxHeight : undefined }}
      >
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center h-16 text-[11px] text-fl-subtle">
            No log entries match filters.
          </div>
        ) : (
          filtered.map((entry) => {
            const c = TYPE_COLORS[entry.type];
            return (
              <div
                key={entry.id}
                className="flex items-start gap-3 px-3 py-2 hover:bg-fl-secondary/40 transition-colors"
              >
                {/* Timestamp */}
                <span className="font-mono text-[10px] text-fl-subtle shrink-0 mt-0.5 w-16">
                  {fmtTs(entry.timestamp)}
                </span>

                {/* Type badge */}
                <span className={clsx(
                  'text-[9px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded shrink-0 mt-0.5',
                  c.bg, c.text,
                )}>
                  {entry.type}
                </span>

                {/* Source */}
                <span className="text-[10px] font-medium text-fl-muted shrink-0 w-28 mt-0.5 truncate">
                  {entry.source}
                </span>

                {/* Message */}
                <span className="text-[11px] text-fl-text font-mono leading-relaxed flex-1 min-w-0">
                  {entry.message}
                </span>

                {/* Round */}
                {entry.round !== undefined && (
                  <span className="text-[9px] font-mono text-fl-subtle shrink-0 mt-0.5">
                    R{entry.round}
                  </span>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
