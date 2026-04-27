import React from 'react';
import { Play, Square, RotateCcw, ChevronRight, Cpu, Server, Cloud, Shield, SlidersHorizontal } from 'lucide-react';
import clsx from 'clsx';
import { useFLStore } from '../store/useFLStore';
import { StatusBadge } from '../components/common/StatusBadge';
import { AccuracyChart } from '../components/charts/AccuracyChart';
import { LossChart } from '../components/charts/LossChart';

function ParamSlider({ label, value, min, max, step, fmt, color, onChange }: {
  label: string; value: number; min: number; max: number; step: number;
  fmt: (v: number) => string; color: string; onChange: (v: number) => void;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between">
        <span className="text-[10px] text-fl-muted font-medium">{label}</span>
        <span className="font-mono text-[13px] font-bold" style={{ color }}>{fmt(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="param-slider"
        style={{ '--pct': `${pct}%`, '--track-fill': color } as React.CSSProperties}
      />
      <div className="flex justify-between text-[9px] text-fl-subtle font-mono">
        <span>{fmt(min)}</span><span>{fmt(max)}</span>
      </div>
    </div>
  );
}

function Stepper({ label, value, min, max, step, color, onChange }: {
  label: string; value: number; min: number; max: number; step: number;
  color: string; onChange: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[10px] text-fl-muted font-medium">{label}</span>
      <div className="flex items-stretch rounded-lg border border-fl-border overflow-hidden h-8">
        <button
          onClick={() => onChange(Math.max(min, value - step))}
          disabled={value <= min}
          className="w-8 flex items-center justify-center text-fl-muted hover:bg-fl-secondary active:bg-slate-200 text-lg font-light border-r border-fl-border transition-colors disabled:opacity-30">
          −
        </button>
        <span className="flex-1 flex items-center justify-center font-mono font-bold text-[13px]" style={{ color }}>
          {value}
        </span>
        <button
          onClick={() => onChange(Math.min(max, value + step))}
          disabled={value >= max}
          className="w-8 flex items-center justify-center text-fl-muted hover:bg-fl-secondary active:bg-slate-200 text-lg font-light border-l border-fl-border transition-colors disabled:opacity-30">
          +
        </button>
      </div>
    </div>
  );
}

// Two-tier HFL pipeline: Local → Edge Agg → Cloud Agg → Done
const PIPELINE_STEPS = [
  { key: 'local-training', label: 'Local Train',  sub: '6 IoT devices', icon: Cpu },
  { key: 'edge-agg',       label: 'Edge Agg',     sub: 'Edge-A + Edge-B', icon: Server },
  { key: 'cloud-agg',      label: 'Cloud Agg',    sub: 'HFL-MM-HC global', icon: Cloud },
  { key: 'complete',       label: 'DP Certify',   sub: 'ε accounting', icon: Shield },
] as const;

export function Training() {
  const {
    isTraining, currentRound, maxRounds, clients, edges, trainingPhase,
    roundHistory, experiments, activeExperimentId,
    startTraining, stopTraining, updateActiveHyperparams,
  } = useFLStore();

  const activeExp = experiments.find((e) => e.id === activeExperimentId);
  const hp = activeExp?.hyperparams;
  const progress = maxRounds > 0 ? (currentRound / maxRounds) * 100 : 0;
  const latest = roundHistory[roundHistory.length - 1];

  const phaseIdx = PIPELINE_STEPS.findIndex((s) => s.key === trainingPhase);

  if (!hp) return null;

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 gap-4 page-enter">
      {/* Control bar */}
      <div className="panel p-4 flex items-center gap-4 shrink-0">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-sm font-semibold text-fl-text">HFL-MM-HC Training Control</h2>
            <StatusBadge
              variant={isTraining ? trainingPhase === 'edge-agg' || trainingPhase === 'cloud-agg' ? 'aggregating' : 'training' : 'idle'}
              pulse={isTraining}
            />
          </div>
          <p className="text-[11px] text-fl-muted font-mono">
            P1 · {hp.nDevices} devices · {hp.nEdges} edges · ε={hp.privacyBudget} · batch={hp.batchSize} · τ_e={hp.tauE}
          </p>
        </div>

        {/* Round progress */}
        <div className="flex flex-col items-center gap-1 min-w-[170px]">
          <div className="flex justify-between w-full text-[10px] text-fl-muted mb-0.5">
            <span>Round Progress</span>
            <span className="font-mono">{currentRound} / {maxRounds}</span>
          </div>
          <div className="h-2 w-full bg-fl-secondary rounded-full overflow-hidden">
            <div className="h-full bg-fl-primary rounded-full transition-all duration-700"
              style={{ width: `${progress}%` }} />
          </div>
          <span className="text-[10px] text-fl-subtle font-mono">{progress.toFixed(1)}% · target acc ≥83%</span>
        </div>

        {/* Privacy budget */}
        {latest && (
          <div className="flex flex-col items-center gap-1 min-w-[110px]">
            <div className="flex justify-between w-full text-[10px] text-fl-muted mb-0.5">
              <span>ε budget</span>
              <span className="font-mono">{latest.epsilonSpent.toFixed(3)} / 1.0</span>
            </div>
            <div className="h-2 w-full bg-fl-secondary rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700"
                style={{ width: `${latest.epsilonSpent * 100}%`, background: latest.epsilonSpent > 0.8 ? '#DC2626' : '#059669' }} />
            </div>
            <span className="text-[9px] text-fl-subtle">DP-SGD σ=1.1 C=1.0</span>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-2 shrink-0">
          {!isTraining ? (
            <button onClick={startTraining} className="fl-btn fl-btn-primary">
              <Play size={13} /> Start
            </button>
          ) : (
            <button onClick={stopTraining} className="fl-btn fl-btn-danger">
              <Square size={13} /> Stop
            </button>
          )}
          <button onClick={() => window.location.reload()} className="fl-btn fl-btn-secondary">
            <RotateCcw size={13} /> Reset
          </button>
        </div>
      </div>

      {/* Two-tier pipeline */}
      <div className="panel p-4 shrink-0">
        <p className="text-[10px] uppercase tracking-widest font-semibold text-fl-muted mb-3">
          HFL Two-Tier Training Pipeline — Round {currentRound}
        </p>
        <div className="flex items-center gap-0">
          {PIPELINE_STEPS.map((step, i) => {
            const done   = isTraining && phaseIdx > i;
            const active = isTraining && phaseIdx === i;
            const Icon = step.icon;
            return (
              <React.Fragment key={step.key}>
                <div className={clsx(
                  'flex flex-col items-center gap-1.5 px-4 py-2.5 rounded-md transition-all',
                  active && 'bg-blue-50 border border-blue-100',
                  done   && 'bg-emerald-50',
                )}>
                  <div className={clsx(
                    'w-9 h-9 rounded-full flex items-center justify-center',
                    active && 'bg-fl-primary text-white shadow-sm',
                    done   && 'bg-fl-green text-white',
                    !active && !done && 'bg-fl-secondary text-fl-muted',
                  )}>
                    <Icon size={15} />
                  </div>
                  <span className={clsx(
                    'text-[10px] font-semibold',
                    active && 'text-fl-primary',
                    done   && 'text-fl-green',
                    !active && !done && 'text-fl-muted',
                  )}>{step.label}</span>
                  <span className={clsx(
                    'text-[9px]',
                    active ? 'text-blue-400' : done ? 'text-emerald-400' : 'text-fl-subtle',
                  )}>{step.sub}</span>
                  {active && <span className="w-1.5 h-1.5 rounded-full bg-fl-primary training-dot" />}
                </div>
                {i < PIPELINE_STEPS.length - 1 && (
                  <ChevronRight size={14} className={clsx('shrink-0 mx-1', done ? 'text-fl-green' : 'text-fl-border')} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Device grid — split by edge */}
      <div className="panel p-4 shrink-0">
        <p className="text-[10px] uppercase tracking-widest font-semibold text-fl-muted mb-3">
          IoT Device Participation — {clients.filter(c => c.status !== 'disconnected').length}/6 online
        </p>
        <div className="grid grid-cols-2 gap-3">
          {edges.map((edge) => {
            const edgeDevs = clients.filter((c) => c.edgeId === edge.id);
            return (
              <div key={edge.id} className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-violet-500" />
                  <span className="text-[10px] font-semibold text-fl-text">{edge.name}</span>
                  {edge.accuracy > 0 && (
                    <span className="font-mono text-[10px] text-fl-muted">
                      edge_acc {(edge.accuracy * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-1.5">
                  {edgeDevs.map((c) => {
                    const isTrain = isTraining && (trainingPhase === 'local-training') && c.status !== 'disconnected';
                    const isEdgeAgg = isTraining && trainingPhase === 'edge-agg';
                    const accColor = c.accuracy >= 0.80 ? '#059669' : c.accuracy >= 0.68 ? '#D97706' : '#DC2626';
                    return (
                      <div key={c.id} className={clsx(
                        'panel p-2 flex flex-col gap-1 transition-all duration-300',
                        isTrain && 'border-fl-primary bg-blue-50/40',
                        isEdgeAgg && 'border-violet-400 bg-violet-50/30',
                      )}>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-semibold text-fl-text">{c.name}</span>
                          <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: accColor }} />
                        </div>
                        <span className="font-mono text-[11px]" style={{ color: accColor }}>
                          {(c.accuracy * 100).toFixed(1)}%
                        </span>
                        <div className="acc-bar-bg">
                          <div className="acc-bar-fill" style={{ width: `${c.accuracy * 100}%`, background: accColor }} />
                        </div>
                        <div className="flex justify-between text-[8px] text-fl-subtle font-mono">
                          <span>{c.dominantClass}</span>
                          <span>{c.latency.toFixed(0)}ms</span>
                        </div>
                        <div className="flex justify-between text-[8px] text-fl-subtle font-mono">
                          <span>ε {c.epsilonSpent.toFixed(2)}</span>
                          <span>{c.datasetSize}S</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Charts + hyperparams */}
      <div className="grid grid-cols-2 gap-4 shrink-0">
        <div className="flex flex-col gap-4">
          <div className="panel p-4" style={{ height: 200 }}>
            <AccuracyChart height={140} compact={false} />
          </div>
          <div className="panel p-4" style={{ height: 200 }}>
            <LossChart height={140} compact={false} />
          </div>
        </div>

        {/* ── Hyperparams redesign ── */}
        <div className="panel flex flex-col overflow-hidden">
          <div className="panel-header shrink-0">
            <span className="panel-header-title">
              <SlidersHorizontal size={11} />
              Config — run_phase5.py
            </span>
            <span className="text-[9px] font-mono text-fl-subtle px-1.5 py-0.5 bg-fl-secondary rounded">P1 · HFL-MM-HC</span>
          </div>

          <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2.5">
            {/* Training group */}
            <div className="rounded-md border border-blue-100 overflow-hidden">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border-b border-blue-100">
                <div className="w-1.5 h-1.5 rounded-full bg-fl-primary" />
                <span className="text-[9px] font-bold uppercase tracking-widest text-blue-700">Training</span>
              </div>
              <div className="p-3 flex flex-col gap-3">
                <ParamSlider
                  label="Learning Rate" value={hp.learningRate} min={0.0001} max={0.01} step={0.0001}
                  fmt={(v) => v.toFixed(4)} color="#2563EB"
                  onChange={(v) => updateActiveHyperparams({ learningRate: v })}
                />
                <div className="grid grid-cols-2 gap-3">
                  <Stepper
                    label="τ_e Local Epochs" value={hp.tauE} min={1} max={10} step={1}
                    color="#2563EB" onChange={(v) => updateActiveHyperparams({ tauE: v })}
                  />
                  <Stepper
                    label="Batch Size" value={hp.batchSize} min={16} max={128} step={16}
                    color="#2563EB" onChange={(v) => updateActiveHyperparams({ batchSize: v })}
                  />
                </div>
              </div>
            </div>

            {/* Privacy group */}
            <div className="rounded-md border border-amber-100 overflow-hidden">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border-b border-amber-100">
                <div className="w-1.5 h-1.5 rounded-full bg-fl-warning" />
                <span className="text-[9px] font-bold uppercase tracking-widest text-amber-700">DP Privacy · Opacus σ={hp.noiseMult.toFixed(1)} C=1.0</span>
              </div>
              <div className="p-3 grid grid-cols-2 gap-3">
                <ParamSlider
                  label="Budget ε" value={hp.privacyBudget} min={0.1} max={5.0} step={0.1}
                  fmt={(v) => v.toFixed(1)} color="#D97706"
                  onChange={(v) => updateActiveHyperparams({ privacyBudget: v })}
                />
                <ParamSlider
                  label="Noise σ" value={hp.noiseMult} min={0.5} max={3.0} step={0.1}
                  fmt={(v) => v.toFixed(1)} color="#D97706"
                  onChange={(v) => updateActiveHyperparams({ noiseMult: v })}
                />
              </div>
            </div>

            {/* Compression group */}
            <div className="rounded-md border border-violet-100 overflow-hidden">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-violet-50 border-b border-violet-100">
                <div className="w-1.5 h-1.5 rounded-full bg-fl-accent" />
                <span className="text-[9px] font-bold uppercase tracking-widest text-violet-700">Gradient Compression · INT8</span>
              </div>
              <div className="p-3">
                <ParamSlider
                  label="Top-k Sparsity (active params)" value={hp.sparsity} min={0.05} max={0.5} step={0.05}
                  fmt={(v) => `${(v * 100).toFixed(0)}%`} color="#7C3AED"
                  onChange={(v) => updateActiveHyperparams({ sparsity: v })}
                />
              </div>
            </div>

            {/* Aggregation group */}
            <div className="rounded-md border border-fl-border overflow-hidden">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-fl-secondary border-b border-fl-border">
                <div className="w-1.5 h-1.5 rounded-full bg-fl-muted" />
                <span className="text-[9px] font-bold uppercase tracking-widest text-fl-muted">Aggregation Strategy</span>
              </div>
              <div className="p-2.5 grid grid-cols-3 gap-1.5">
                {['FedAvg', 'FedProx', 'FedNova', 'SCAFFOLD', 'MOON', 'Median'].map((a) => (
                  <button key={a}
                    onClick={() => updateActiveHyperparams({ aggregation: a })}
                    className={clsx(
                      'text-[10px] font-semibold py-1.5 px-1 rounded border transition-all text-center',
                      hp.aggregation === a
                        ? 'bg-fl-primary text-white border-fl-primary shadow-sm'
                        : 'bg-fl-secondary text-fl-muted border-fl-border hover:border-fl-primary hover:text-fl-text',
                    )}>
                    {a}
                  </button>
                ))}
              </div>
            </div>

            {/* Live output metrics */}
            {latest && (
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-fl-border">
                {[
                  { label: 'Best Acc', value: `${(Math.max(...roundHistory.map(r => r.globalAccuracy)) * 100).toFixed(3)}%`, color: '#059669' },
                  { label: 'Best AUC', value: `${Math.max(...roundHistory.map(r => r.macroAuc)).toFixed(4)}`, color: '#2563EB' },
                  { label: 'Comm/Round', value: `${(latest.communicationBytes / 1e6).toFixed(2)} MB`, color: '#0F172A' },
                  { label: 'Reduction', value: `${latest.commReduction.toFixed(1)}%`, color: '#7C3AED' },
                ].map((s) => (
                  <div key={s.label} className="flex flex-col gap-0.5">
                    <p className="text-[9px] text-fl-subtle uppercase tracking-wide">{s.label}</p>
                    <p className="font-mono text-sm font-semibold" style={{ color: s.color }}>{s.value}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
