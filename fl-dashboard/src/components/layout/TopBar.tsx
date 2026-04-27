import React from 'react';
import clsx from 'clsx';
import { WifiOff, Shield } from 'lucide-react';
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
      <span className={clsx('text-sm font-medium', mono && 'font-mono', color ?? 'text-fl-text')}>
        {value}
      </span>
    </div>
  );
}

export function TopBar() {
  const { currentRound, maxRounds, roundHistory, trainingPhase, isTraining } = useFLStore();

  const latest = roundHistory[roundHistory.length - 1];
  const accuracy = latest ? `${(latest.globalAccuracy * 100).toFixed(2)}%` : '—';
  const loss     = latest ? latest.globalLoss.toFixed(4) : '—';
  const eps      = latest ? latest.epsilonSpent.toFixed(3) : '—';

  const statusLabel = !isTraining
    ? 'Idle'
    : trainingPhase === 'local-training' ? 'Local Train'
    : trainingPhase === 'edge-agg'       ? 'Edge Agg'
    : trainingPhase === 'cloud-agg'      ? 'Cloud Agg'
    : trainingPhase === 'complete'       ? 'DP Certify'
    : 'Training';

  const statusColor = !isTraining
    ? 'text-fl-muted'
    : trainingPhase === 'edge-agg'  ? 'text-fl-accent'
    : trainingPhase === 'cloud-agg' ? 'text-fl-primary'
    : trainingPhase === 'complete'  ? 'text-fl-green'
    : 'text-fl-green';

  const progress = maxRounds > 0 ? (currentRound / maxRounds) * 100 : 0;
  const epsOver  = latest && latest.epsilonSpent > 0.8;

  return (
    <header className="h-14 shrink-0 border-b border-fl-border bg-fl-panel flex items-center px-5 gap-0 z-10">
      {/* Page title */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h1 className="text-[13px] font-semibold text-fl-text truncate">HFL-MM-HC Monitor</h1>
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-fl-secondary text-fl-subtle uppercase tracking-wider font-mono">
            PHANTOM-FL · PTB-XL
          </span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="h-1 w-32 bg-fl-secondary rounded-full overflow-hidden">
            <div className="h-full bg-fl-primary rounded-full transition-all duration-700" style={{ width: `${progress}%` }} />
          </div>
          <span className="text-[10px] font-mono text-fl-muted">
            Round {currentRound} / {maxRounds} · target ≥83%
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center">
        <Stat label="Global Accuracy" value={accuracy}
          color={latest && latest.globalAccuracy >= 0.83 ? 'text-fl-green' : 'text-fl-text'} />
        <Divider />
        <Stat label="Global Loss" value={loss}
          color={latest && latest.globalLoss < 0.15 ? 'text-fl-green' : 'text-fl-text'} />
        <Divider />
        {/* ε budget with mini bar */}
        <div className="flex flex-col items-end leading-none gap-1">
          <div className="flex items-center gap-1">
            <Shield size={9} className={epsOver ? 'text-fl-danger' : 'text-fl-green'} />
            <span className="text-[9px] uppercase tracking-widest text-fl-subtle font-medium">ε / 1.0</span>
          </div>
          <span className={clsx('text-sm font-medium font-mono', epsOver ? 'text-fl-danger' : 'text-fl-text')}>
            {eps}
          </span>
          {latest && (
            <div className="h-0.5 w-16 bg-fl-secondary rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700"
                style={{ width: `${latest.epsilonSpent * 100}%`, background: epsOver ? '#DC2626' : '#059669' }} />
            </div>
          )}
        </div>
        <Divider />
        {/* Status */}
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
