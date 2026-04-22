import React from 'react';
import { Activity, Users, Target, Zap } from 'lucide-react';
import { useFLStore } from '../store/useFLStore';
import { MetricCard } from '../components/common/MetricCard';
import { NetworkGraph } from '../components/graph/NetworkGraph';
import { NodeDetailPanel } from '../components/graph/NodeDetailPanel';
import { AccuracyChart } from '../components/charts/AccuracyChart';
import { LossChart } from '../components/charts/LossChart';
import { LatencyChart } from '../components/charts/LatencyChart';
import { LogPanel } from '../components/logs/LogPanel';

export function Dashboard() {
  const { roundHistory, clients, currentRound, selectedClientId } = useFLStore();

  const latest = roundHistory[roundHistory.length - 1];
  const prev   = roundHistory[roundHistory.length - 2];
  const activeClients = clients.filter((c) => c.status !== 'disconnected').length;
  const avgAcc = clients.reduce((s, c) => s + c.accuracy, 0) / clients.length;

  const accTrend  = latest && prev ? latest.globalAccuracy > prev.globalAccuracy ? 'up' : 'down' : undefined;
  const lossTrend = latest && prev ? latest.globalLoss < prev.globalLoss ? 'up' : 'down' : undefined;

  return (
    <div className="flex flex-col h-full gap-0 overflow-hidden page-enter">
      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-3 p-3 pb-0 shrink-0 stagger">
        <MetricCard
          label="Global Accuracy"
          value={latest ? `${(latest.globalAccuracy * 100).toFixed(2)}%` : '—'}
          sub={accTrend === 'up' ? '+improving' : accTrend === 'down' ? 'slight drop' : 'no data yet'}
          icon={<Target size={14} />}
          accent="green"
          trend={accTrend}
          trendValue={prev && latest ? `${Math.abs((latest.globalAccuracy - prev.globalAccuracy) * 100).toFixed(2)}%` : undefined}
        />
        <MetricCard
          label="Global Loss"
          value={latest ? latest.globalLoss.toFixed(4) : '—'}
          sub="cross-entropy"
          icon={<Activity size={14} />}
          accent="danger"
          trend={lossTrend}
          trendValue={prev && latest ? Math.abs(latest.globalLoss - prev.globalLoss).toFixed(4) : undefined}
        />
        <MetricCard
          label="Active Clients"
          value={`${activeClients} / ${clients.length}`}
          sub={`avg accuracy ${(avgAcc * 100).toFixed(1)}%`}
          icon={<Users size={14} />}
          accent="primary"
        />
        <MetricCard
          label="Training Round"
          value={`${currentRound}`}
          sub={latest ? `${latest.participatingClients} participants` : 'not started'}
          icon={<Zap size={14} />}
          accent="accent"
        />
      </div>

      {/* Main grid: graph + charts */}
      <div className="flex flex-1 min-h-0 gap-3 p-3 pb-0">
        {/* Network graph */}
        <div className="flex-1 min-w-0 panel relative overflow-hidden">
          <div className="panel-header shrink-0 absolute top-0 left-0 right-0 z-10 bg-fl-panel/90 backdrop-blur-sm">
            <span className="panel-header-title">
              <span className="w-1.5 h-1.5 rounded-full bg-fl-primary" />
              Federation Network
            </span>
            <span className="text-[10px] text-fl-subtle">{clients.length} nodes · click to inspect</span>
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
      <div className="p-3 shrink-0" style={{ height: 200 }}>
        <LogPanel compact maxHeight={165} />
      </div>
    </div>
  );
}
