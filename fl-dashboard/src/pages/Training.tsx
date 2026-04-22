import React, { useState } from 'react';
import { Play, Square, RotateCcw, ChevronRight, Cpu, Users, Layers, Shield } from 'lucide-react';
import clsx from 'clsx';
import { useFLStore } from '../store/useFLStore';
import { StatusBadge } from '../components/common/StatusBadge';
import { AccuracyChart } from '../components/charts/AccuracyChart';
import { LossChart } from '../components/charts/LossChart';

function SliderRow({
  label, value, min, max, step, unit, onChange,
}: {
  label: string; value: number; min: number; max: number;
  step: number; unit: string; onChange: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between text-[11px]">
        <span className="text-fl-muted font-medium">{label}</span>
        <span className="font-mono text-fl-text font-medium">{value}{unit}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1 rounded appearance-none bg-fl-border accent-fl-primary cursor-pointer"
      />
      <div className="flex justify-between text-[9px] text-fl-subtle">
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  );
}

export function Training() {
  const {
    isTraining, currentRound, maxRounds, clients, trainingPhase,
    roundHistory, experiments, activeExperimentId,
    startTraining, stopTraining, updateActiveHyperparams,
  } = useFLStore();

  const activeExp = experiments.find((e) => e.id === activeExperimentId);
  const hp = activeExp?.hyperparams;

  const progress = maxRounds > 0 ? (currentRound / maxRounds) * 100 : 0;
  const latest = roundHistory[roundHistory.length - 1];

  const activeCount  = clients.filter((c) => c.status === 'active' || c.status === 'training').length;
  const trainingCount = clients.filter((c) => c.status === 'training').length;

  const phaseSteps = ['waiting', 'local-training', 'aggregating', 'complete'] as const;
  const phaseIdx = phaseSteps.indexOf(trainingPhase as typeof phaseSteps[number]);

  if (!hp) return null;

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 gap-4 page-enter">
      {/* Control bar */}
      <div className="panel p-4 flex items-center gap-4 shrink-0">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-sm font-semibold text-fl-text">Training Control</h2>
            <StatusBadge
              variant={isTraining ? trainingPhase === 'aggregating' ? 'aggregating' : 'training' : 'idle'}
              pulse={isTraining}
            />
          </div>
          <p className="text-[11px] text-fl-muted">{activeExp?.name ?? 'No active experiment'}</p>
        </div>

        {/* Round progress */}
        <div className="flex flex-col items-center gap-1 min-w-[160px]">
          <div className="flex justify-between w-full text-[10px] text-fl-muted mb-0.5">
            <span>Round Progress</span>
            <span className="font-mono">{currentRound} / {maxRounds}</span>
          </div>
          <div className="h-2 w-full bg-fl-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-fl-primary rounded-full transition-all duration-700"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-[10px] text-fl-subtle">{progress.toFixed(1)}% complete</span>
        </div>

        {/* Buttons */}
        <div className="flex gap-2">
          {!isTraining ? (
            <button onClick={startTraining} className="fl-btn fl-btn-primary">
              <Play size={13} /> Start Training
            </button>
          ) : (
            <button onClick={stopTraining} className="fl-btn fl-btn-danger">
              <Square size={13} /> Stop
            </button>
          )}
          <button
            onClick={() => window.location.reload()}
            className="fl-btn fl-btn-secondary"
          >
            <RotateCcw size={13} /> Reset
          </button>
        </div>
      </div>

      {/* Phase pipeline */}
      <div className="panel p-4 shrink-0">
        <p className="text-[10px] uppercase tracking-widest font-semibold text-fl-muted mb-3">Training Pipeline</p>
        <div className="flex items-center gap-0">
          {[
            { key: 'waiting',       label: 'Broadcast',    icon: Layers },
            { key: 'local-training',label: 'Local Train',  icon: Cpu },
            { key: 'aggregating',   label: 'Aggregate',    icon: Users },
            { key: 'complete',      label: 'Update',       icon: Shield },
          ].map((step, i) => {
            const done   = isTraining && phaseIdx > i;
            const active = isTraining && phaseIdx === i;
            const Icon   = step.icon;
            return (
              <React.Fragment key={step.key}>
                <div className={clsx(
                  'flex flex-col items-center gap-1.5 px-3 py-2 rounded-md transition-all',
                  active && 'bg-blue-50',
                  done   && 'bg-emerald-50',
                )}>
                  <div className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center',
                    active && 'bg-fl-primary text-white',
                    done   && 'bg-fl-green text-white',
                    !active && !done && 'bg-fl-secondary text-fl-muted',
                  )}>
                    <Icon size={14} />
                  </div>
                  <span className={clsx(
                    'text-[10px] font-medium',
                    active && 'text-fl-primary',
                    done   && 'text-fl-green',
                    !active && !done && 'text-fl-muted',
                  )}>
                    {step.label}
                  </span>
                  {active && <span className="w-1.5 h-1.5 rounded-full bg-fl-primary training-dot" />}
                </div>
                {i < 3 && (
                  <ChevronRight size={14} className={clsx('shrink-0', done ? 'text-fl-green' : 'text-fl-border')} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Client grid */}
      <div className="panel p-4 shrink-0">
        <p className="text-[10px] uppercase tracking-widest font-semibold text-fl-muted mb-3">
          Client Participation — {activeCount}/{clients.length} active
        </p>
        <div className="grid grid-cols-4 gap-2">
          {clients.map((c) => {
            const isTrain = isTraining && (c.status === 'training' || c.status === 'active');
            const accColor = c.accuracy >= 0.85 ? '#059669' : c.accuracy >= 0.70 ? '#D97706' : '#DC2626';
            return (
              <div
                key={c.id}
                className={clsx(
                  'panel p-3 flex flex-col gap-1.5 transition-all duration-300',
                  isTrain && trainingPhase === 'local-training' && 'border-fl-primary bg-blue-50/40',
                  isTrain && trainingPhase === 'aggregating'    && 'border-fl-accent bg-violet-50/40',
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-semibold text-fl-text truncate">{c.name.split(' ')[0]}</span>
                  <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: accColor }} />
                </div>
                <span className="font-mono text-[11px]" style={{ color: accColor }}>
                  {(c.accuracy * 100).toFixed(1)}%
                </span>
                <div className="acc-bar-bg">
                  <div className="acc-bar-fill" style={{ width: `${c.accuracy * 100}%`, background: accColor }} />
                </div>
                <span className="text-[9px] text-fl-subtle font-mono">{c.latency.toFixed(0)}ms</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Charts + hyperparams */}
      <div className="grid grid-cols-2 gap-4 shrink-0">
        {/* Charts */}
        <div className="flex flex-col gap-4">
          <div className="panel p-4" style={{ height: 200 }}>
            <AccuracyChart height={140} compact={false} />
          </div>
          <div className="panel p-4" style={{ height: 200 }}>
            <LossChart height={140} compact={false} />
          </div>
        </div>

        {/* Hyperparams */}
        <div className="panel p-4 flex flex-col gap-5">
          <p className="text-[10px] uppercase tracking-widest font-semibold text-fl-muted">Hyperparameters</p>

          <SliderRow
            label="Learning Rate" value={hp.learningRate} min={0.0001} max={0.1}
            step={0.0001} unit="" onChange={(v) => updateActiveHyperparams({ learningRate: v })}
          />
          <SliderRow
            label="Local Epochs" value={hp.localEpochs} min={1} max={20}
            step={1} unit="" onChange={(v) => updateActiveHyperparams({ localEpochs: v })}
          />
          <SliderRow
            label="Batch Size" value={hp.batchSize} min={8} max={128}
            step={8} unit="" onChange={(v) => updateActiveHyperparams({ batchSize: v })}
          />
          <SliderRow
            label="Momentum" value={hp.momentum} min={0} max={0.999}
            step={0.001} unit="" onChange={(v) => updateActiveHyperparams({ momentum: v })}
          />
          <SliderRow
            label="Privacy Budget ε" value={hp.privacyBudget} min={0.1} max={10}
            step={0.1} unit="" onChange={(v) => updateActiveHyperparams({ privacyBudget: v })}
          />
          <SliderRow
            label="Compression Ratio" value={hp.compressionRatio} min={0.1} max={1.0}
            step={0.05} unit="x" onChange={(v) => updateActiveHyperparams({ compressionRatio: v })}
          />

          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] text-fl-muted font-medium">Aggregation Strategy</label>
            <select
              value={hp.aggregation}
              onChange={(e) => updateActiveHyperparams({ aggregation: e.target.value })}
              className="fl-select"
            >
              {['FedAvg', 'FedProx', 'FedNova', 'SCAFFOLD', 'FedAdam', 'Median', 'Trimmed Mean'].map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          {/* Current stats */}
          {latest && (
            <div className="mt-auto pt-3 border-t border-fl-border grid grid-cols-2 gap-3">
              {[
                { label: 'Best Accuracy', value: `${(Math.max(...roundHistory.map(r => r.globalAccuracy)) * 100).toFixed(3)}%` },
                { label: 'Rounds Done',  value: `${currentRound}` },
                { label: 'Participants', value: `${latest.participatingClients}` },
                { label: 'Comm. Cost',   value: `${(latest.communicationBytes / 1e6).toFixed(1)}MB` },
              ].map((s) => (
                <div key={s.label}>
                  <p className="text-[9px] text-fl-subtle uppercase tracking-wide">{s.label}</p>
                  <p className="font-mono text-sm font-medium text-fl-text">{s.value}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
