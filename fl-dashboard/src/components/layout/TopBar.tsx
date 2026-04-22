import React from 'react';
import clsx from 'clsx';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { useFLStore } from '../../store/useFLStore';

function Divider() {
  return <div className="w-px h-6 bg-fl-border mx-3" />;
}

function Stat({ label, value, mono = true, color }: {
  label: string; value: string; mono?: boolean; color?: string;
}) {
  return (
    <div className="flex flex-col items-end leading-none">
      <span className="text-[9px] uppercase tracking-widest text-fl-subtle font-medium mb-1">{label}</span>
      <span className={clsx(
        'text-sm font-medium',
        mono && 'font-mono',
        color ?? 'text-fl-text',
      )}>
        {value}
      </span>
    </div>
  );
}

export function TopBar() {
  const { currentRound, maxRounds, roundHistory, systemStatus, trainingPhase, isTraining } = useFLStore();

  const latest = roundHistory[roundHistory.length - 1];
  const accuracy = latest ? `${(latest.globalAccuracy * 100).toFixed(2)}%` : '—';
  const loss     = latest ? latest.globalLoss.toFixed(4) : '—';
  const avgLat   = latest ? `${latest.avgLatency.toFixed(0)}ms` : '—';

  const statusLabel = !isTraining
    ? 'Idle'
    : trainingPhase === 'local-training' ? 'Local Training'
    : trainingPhase === 'aggregating'    ? 'Aggregating'
    : 'Training';

  const statusColor = !isTraining
    ? 'text-fl-muted'
    : trainingPhase === 'aggregating'
      ? 'text-fl-accent'
      : 'text-fl-green';

  const progress = maxRounds > 0 ? (currentRound / maxRounds) * 100 : 0;

  return (
    <header className="h-14 shrink-0 border-b border-fl-border bg-fl-panel flex items-center px-5 gap-0 z-10">
      {/* Page title area */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h1 className="text-[13px] font-semibold text-fl-text truncate">Federated Learning Monitor</h1>
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-fl-secondary text-fl-subtle uppercase tracking-wider font-mono">
            PHANTOM-FL / HFL-MM
          </span>
        </div>
        {/* Round progress bar */}
        <div className="flex items-center gap-2 mt-1">
          <div className="h-1 w-32 bg-fl-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-fl-primary rounded-full transition-all duration-700"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-[10px] font-mono text-fl-muted">
            Round {currentRound} / {maxRounds}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center">
        <Stat label="Global Accuracy" value={accuracy} color={latest && latest.globalAccuracy >= 0.85 ? 'text-fl-green' : 'text-fl-text'} />
        <Divider />
        <Stat label="Global Loss" value={loss} color={latest && latest.globalLoss < 0.15 ? 'text-fl-green' : 'text-fl-text'} />
        <Divider />
        <Stat label="Avg Latency" value={avgLat} />
        <Divider />

        {/* System Status */}
        <div className="flex flex-col items-end leading-none">
          <span className="text-[9px] uppercase tracking-widest text-fl-subtle font-medium mb-1">Status</span>
          <span className={clsx('text-[11px] font-semibold uppercase tracking-wide flex items-center gap-1.5', statusColor)}>
            {isTraining && <span className="w-1.5 h-1.5 rounded-full bg-current training-dot" />}
            {!isTraining && <WifiOff size={11} />}
            {statusLabel}
          </span>
        </div>
      </div>
    </header>
  );
}
