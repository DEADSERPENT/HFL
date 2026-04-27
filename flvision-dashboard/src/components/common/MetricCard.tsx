import React from 'react';
import clsx from 'clsx';

interface Props {
  label: string;
  value: string;
  sub?: string;
  icon: React.ReactNode;
  accent?: 'primary' | 'green' | 'accent' | 'warning' | 'danger';
  trend?: 'up' | 'down' | 'flat';
  trendValue?: string;
  flash?: boolean;
}

const accentColors = {
  primary: { border: '#2563EB', icon: 'bg-blue-50 text-blue-600',  bar: '#2563EB' },
  green:   { border: '#059669', icon: 'bg-emerald-50 text-emerald-600', bar: '#059669' },
  accent:  { border: '#7C3AED', icon: 'bg-violet-50 text-violet-600', bar: '#7C3AED' },
  warning: { border: '#D97706', icon: 'bg-amber-50 text-amber-600',  bar: '#D97706' },
  danger:  { border: '#DC2626', icon: 'bg-red-50 text-red-600',    bar: '#DC2626' },
};

export function MetricCard({ label, value, sub, icon, accent = 'primary', trend, trendValue, flash }: Props) {
  const colors = accentColors[accent];

  return (
    <div
      className="panel relative overflow-hidden flex flex-col gap-3 p-4 transition-all duration-200 hover:shadow-sm"
      style={{ borderLeft: `3px solid ${colors.bar}` }}
    >
      {/* Top row */}
      <div className="flex items-start justify-between">
        <div className={clsx('w-8 h-8 rounded-md flex items-center justify-center shrink-0', colors.icon)}>
          {icon}
        </div>
        {trend && trendValue && (
          <span className={clsx(
            'text-xs font-mono font-medium px-1.5 py-0.5 rounded',
            trend === 'up'   && 'bg-emerald-50 text-emerald-600',
            trend === 'down' && 'bg-red-50 text-red-600',
            trend === 'flat' && 'bg-slate-100 text-slate-500',
          )}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </span>
        )}
      </div>

      {/* Value */}
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-widest text-fl-muted mb-1">{label}</p>
        <p className={clsx('font-mono text-2xl font-medium text-fl-text leading-none', flash && 'value-flash')}>
          {value}
        </p>
        {sub && <p className="text-xs text-fl-subtle mt-1">{sub}</p>}
      </div>

      {/* Accent line at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5" style={{ background: `${colors.bar}18` }} />
    </div>
  );
}
