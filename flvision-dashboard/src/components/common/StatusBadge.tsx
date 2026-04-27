import React from 'react';
import clsx from 'clsx';
import { ClientStatus, SystemStatus, ExperimentStatus, LogType } from '../../types';

type BadgeVariant = ClientStatus | SystemStatus | ExperimentStatus | LogType | 'default';

const styles: Record<string, string> = {
  // Client / system status
  active:       'bg-emerald-50 text-emerald-700 border border-emerald-200',
  training:     'bg-blue-50 text-blue-700 border border-blue-200',
  aggregating:  'bg-violet-50 text-violet-700 border border-violet-200',
  idle:         'bg-slate-100 text-slate-500 border border-slate-200',
  disconnected: 'bg-red-50 text-red-600 border border-red-200',
  completed:    'bg-emerald-50 text-emerald-700 border border-emerald-200',
  failed:       'bg-red-50 text-red-600 border border-red-200',
  paused:       'bg-amber-50 text-amber-700 border border-amber-200',
  running:      'bg-blue-50 text-blue-700 border border-blue-200',
  error:        'bg-red-50 text-red-600 border border-red-200',
  // Log types
  info:         'bg-blue-50 text-blue-600 border border-blue-200',
  success:      'bg-emerald-50 text-emerald-700 border border-emerald-200',
  warning:      'bg-amber-50 text-amber-700 border border-amber-200',
  debug:        'bg-slate-100 text-slate-500 border border-slate-200',
  default:      'bg-slate-100 text-slate-600 border border-slate-200',
};

const dots: Record<string, string> = {
  active: 'bg-emerald-500', training: 'bg-blue-500', aggregating: 'bg-violet-500',
  idle: 'bg-slate-400', disconnected: 'bg-red-500', running: 'bg-blue-500',
  completed: 'bg-emerald-500', failed: 'bg-red-500', paused: 'bg-amber-500',
};

interface Props {
  variant: BadgeVariant;
  label?: string;
  pulse?: boolean;
  size?: 'xs' | 'sm';
}

export function StatusBadge({ variant, label, pulse = false, size = 'sm' }: Props) {
  const cls = styles[variant] ?? styles.default;
  const dotColor = dots[variant];
  const displayLabel = label ?? variant.charAt(0).toUpperCase() + variant.slice(1);

  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 rounded font-medium uppercase tracking-wide',
      size === 'xs' ? 'text-[9px] px-1.5 py-0.5' : 'text-[10px] px-2 py-0.5',
      cls,
    )}>
      {dotColor && (
        <span className={clsx(
          'rounded-full shrink-0',
          size === 'xs' ? 'w-1 h-1' : 'w-1.5 h-1.5',
          dotColor,
          pulse && 'training-dot',
        )} />
      )}
      {displayLabel}
    </span>
  );
}
