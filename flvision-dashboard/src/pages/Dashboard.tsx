import React from 'react';
import { Activity, Users, Target, Zap, Shield, Network } from 'lucide-react';
import { useFLStore } from '../store/useFLStore';
import { MetricCard } from '../components/common/MetricCard';
import { NetworkGraph } from '../components/graph/NetworkGraph';
import { NodeDetailPanel } from '../components/graph/NodeDetailPanel';
import { AccuracyChart } from '../components/charts/AccuracyChart';
import { LossChart } from '../components/charts/LossChart';
import { LatencyChart } from '../components/charts/LatencyChart';
import { LogPanel } from '../components/logs/LogPanel';

export function Dashboard() {
  const { roundHistory, clients, edges, currentRound, selectedClientId } = useFLStore();

  const latest = roundHistory[roundHistory.length - 1];
  const prev   = roundHistory[roundHistory.length - 2];
  const totalSamples = clients.reduce((s, c) => s + c.datasetSize, 0);

  const accTrend  = latest && prev ? latest.globalAccuracy > prev.globalAccuracy ? 'up' : 'down' : undefined;
  const lossTrend = latest && prev ? latest.globalLoss < prev.globalLoss ? 'up' : 'down' : undefined;

  const epsColor = latest && latest.epsilonSpent > 0.85
    ? 'danger' : latest && latest.epsilonSpent > 0.6 ? 'accent' : 'green';

  return (
    <div className="flex flex-col h-full gap-0 overflow-hidden page-enter">
      {/* Metric cards — 6 cards showing real project metrics */}
      <div className="grid grid-cols-6 gap-2 p-3 pb-0 shrink-0 stagger">
        <MetricCard
          label="Global Accuracy"
          value={latest ? `${(latest.globalAccuracy * 100).toFixed(2)}%` : '—'}
          sub={accTrend === 'up' ? '↑ improving' : accTrend === 'down' ? '↓ slight drop' : 'awaiting round 1'}
          icon={<Target size={13} />}
          accent="green"
          trend={accTrend}
          trendValue={prev && latest ? `${Math.abs((latest.globalAccuracy - prev.globalAccuracy) * 100).toFixed(2)}%` : undefined}
        />
        <MetricCard
          label="Macro AUC"
          value={latest ? latest.macroAuc.toFixed(4) : '—'}
          sub="5-class ECG (PTB-XL)"
          icon={<Activity size={13} />}
          accent="primary"
        />
        <MetricCard
          label="Global Loss"
          value={latest ? latest.globalLoss.toFixed(4) : '—'}
          sub="cross-entropy"
          icon={<Activity size={13} />}
          accent="danger"
          trend={lossTrend}
          trendValue={prev && latest ? Math.abs(latest.globalLoss - prev.globalLoss).toFixed(4) : undefined}
        />
        <MetricCard
          label="Privacy ε"
          value={latest ? `${latest.epsilonSpent.toFixed(3)} / 1.0` : '— / 1.0'}
          sub="DP-SGD · δ=1e-5 · σ=1.1"
          icon={<Shield size={13} />}
          accent={epsColor}
        />
        <MetricCard
          label="Comm Reduction"
          value={latest ? `${latest.commReduction.toFixed(1)}%` : '—'}
          sub="Top-20% + INT8 (20×)"
          icon={<Network size={13} />}
          accent="accent"
        />
        <MetricCard
          label="Round / Devices"
          value={`${currentRound} / 15`}
          sub={`${clients.filter(c => c.status !== 'disconnected').length}/6 active · ${totalSamples.toLocaleString()} samples`}
          icon={<Zap size={13} />}
          accent="primary"
        />
      </div>

      {/* Edge server status bar */}
      <div className="px-3 pt-2 pb-0 flex gap-2 shrink-0">
        {edges.map((edge) => {
          const devs = clients.filter((c) => c.edgeId === edge.id);
          const edgeSamples = devs.reduce((s, c) => s + c.datasetSize, 0);
          return (
            <div key={edge.id} className="flex-1 panel px-3 py-1.5 flex items-center gap-3">
              <div className="w-2 h-2 rounded-full shrink-0" style={{ background: '#7C3AED' }} />
              <div className="flex-1 min-w-0">
                <p className="text-[10px] font-semibold text-fl-text">{edge.name}</p>
                <p className="text-[9px] text-fl-subtle font-mono">
                  {devs.map(d => d.name).join(' · ')} · {edgeSamples.toLocaleString()} samples
                </p>
              </div>
              <div className="text-right shrink-0">
                <p className="font-mono text-[11px] font-medium text-fl-text">
                  {edge.accuracy > 0 ? `${(edge.accuracy * 100).toFixed(1)}%` : '—'}
                </p>
                <p className="text-[9px] text-fl-subtle">edge acc</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main grid: graph + charts */}
      <div className="flex flex-1 min-h-0 gap-3 p-3 pb-0">
        {/* HFL Network graph */}
        <div className="flex-1 min-w-0 panel relative overflow-hidden">
          <div className="panel-header shrink-0 absolute top-0 left-0 right-0 z-10 bg-fl-panel/90 backdrop-blur-sm">
            <span className="panel-header-title">
              <span className="w-1.5 h-1.5 rounded-full bg-fl-accent" />
              HFL Topology — 6 devices → 2 edges → 1 cloud
            </span>
            <span className="text-[10px] text-fl-subtle">click node to inspect</span>
          </div>
          <div className="absolute inset-0 pt-10">
            <NetworkGraph />
          </div>
          {selectedClientId && <NodeDetailPanel />}
        </div>

        {/* Right charts panel */}
        <div className="w-72 flex flex-col gap-3 shrink-0 overflow-y-auto">
          <div className="panel p-3 flex flex-col" style={{ minHeight: 160 }}>
            <AccuracyChart height={115} />
          </div>
          <div className="panel p-3 flex flex-col" style={{ minHeight: 160 }}>
            <LossChart height={115} />
          </div>
          <div className="panel p-3 flex flex-col" style={{ minHeight: 160 }}>
            <LatencyChart height={115} />
          </div>
        </div>
      </div>

      {/* Log panel */}
      <div className="p-3 shrink-0" style={{ height: 190 }}>
        <LogPanel compact maxHeight={155} />
      </div>
    </div>
  );
}
