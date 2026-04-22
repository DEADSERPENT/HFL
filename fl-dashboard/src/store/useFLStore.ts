import { create } from 'zustand';
import {
  ClientNode, RoundMetrics, LogEntry, ExperimentRun,
  Page, SystemStatus, TrainingPhase, Hyperparams,
} from '../types';

// ── Initial client data (healthcare federation) ──────────────────────────────
const initialClients: ClientNode[] = [
  { id: 'c1', name: 'City General',      accuracy: 0.623, loss: 0.892, datasetSize: 12400, lastUpdate: Date.now(), status: 'active',       latency: 45, localRounds: 0, hospitalType: 'General',      location: 'Downtown',            gradientNorm: 0.234 },
  { id: 'c2', name: 'Metro Health',      accuracy: 0.587, loss: 0.941, datasetSize: 8900,  lastUpdate: Date.now(), status: 'active',       latency: 67, localRounds: 0, hospitalType: 'Metropolitan', location: 'Midtown',             gradientNorm: 0.287 },
  { id: 'c3', name: 'St. Andrews',       accuracy: 0.641, loss: 0.847, datasetSize: 15200, lastUpdate: Date.now(), status: 'active',       latency: 38, localRounds: 0, hospitalType: 'Specialized',  location: 'Uptown',              gradientNorm: 0.198 },
  { id: 'c4', name: 'Valley Medical',    accuracy: 0.558, loss: 0.978, datasetSize: 7300,  lastUpdate: Date.now(), status: 'training',     latency: 89, localRounds: 0, hospitalType: 'Regional',     location: 'Valley District',     gradientNorm: 0.341 },
  { id: 'c5', name: 'Harbor Clinic',     accuracy: 0.612, loss: 0.904, datasetSize: 9800,  lastUpdate: Date.now(), status: 'idle',         latency: 52, localRounds: 0, hospitalType: 'Clinic',       location: 'Harbor Point',        gradientNorm: 0.256 },
  { id: 'c6', name: 'Northside Medical', accuracy: 0.634, loss: 0.861, datasetSize: 11100, lastUpdate: Date.now(), status: 'active',       latency: 44, localRounds: 0, hospitalType: 'General',      location: 'North Quarter',       gradientNorm: 0.221 },
  { id: 'c7', name: 'Riverside Center',  accuracy: 0.571, loss: 0.963, datasetSize: 6500,  lastUpdate: Date.now(), status: 'active',       latency: 73, localRounds: 0, hospitalType: 'Research',     location: 'Riverside',           gradientNorm: 0.312 },
  { id: 'c8', name: 'University Medical',accuracy: 0.659, loss: 0.824, datasetSize: 18700, lastUpdate: Date.now(), status: 'training',     latency: 31, localRounds: 0, hospitalType: 'Academic',     location: 'University District', gradientNorm: 0.176 },
];

// ── Generate synthetic completed experiment ───────────────────────────────────
function makeCompletedExp(
  id: string, name: string, desc: string, finalAcc: number, totalRounds: number,
  tags: string[], hyperparams: Partial<Hyperparams> = {}
): ExperimentRun {
  const metrics: RoundMetrics[] = [];
  let acc = 0.50 + Math.random() * 0.05;
  let loss = 1.1 + Math.random() * 0.2;
  for (let r = 1; r <= totalRounds; r++) {
    acc = Math.min(finalAcc, acc + 0.004 * (1 - acc) * (0.8 + Math.random() * 0.4));
    loss = Math.max(0.07, loss * (0.968 + (Math.random() - 0.5) * 0.015));
    metrics.push({
      round: r,
      globalAccuracy: acc,
      globalLoss: loss,
      timestamp: Date.now() - (totalRounds - r) * 3000 - 120000,
      participatingClients: 8,
      avgLatency: 40 + Math.random() * 50,
      communicationBytes: 900000 + Math.random() * 600000,
    });
  }
  return {
    id, name, description: desc, status: 'completed', tags,
    startTime: Date.now() - totalRounds * 3000 - 180000,
    endTime: Date.now() - 120000,
    hyperparams: {
      learningRate: 0.01, rounds: totalRounds, clientsPerRound: 8,
      aggregation: 'FedAvg', localEpochs: 5, batchSize: 32,
      momentum: 0.9, weightDecay: 0.0001, privacyBudget: 1.0, compressionRatio: 1.0,
      ...hyperparams,
    },
    metrics,
    bestAccuracy: metrics[metrics.length - 1]?.globalAccuracy ?? finalAcc,
  };
}

// ── Store interface ───────────────────────────────────────────────────────────
interface FLState {
  currentPage: Page;
  sidebarCollapsed: boolean;

  currentRound: number;
  maxRounds: number;
  isTraining: boolean;
  systemStatus: SystemStatus;
  trainingPhase: TrainingPhase;
  activeClientIds: string[];

  clients: ClientNode[];
  selectedClientId: string | null;
  roundHistory: RoundMetrics[];
  logs: LogEntry[];
  experiments: ExperimentRun[];
  activeExperimentId: string | null;

  // Actions
  setPage: (page: Page) => void;
  toggleSidebar: () => void;
  selectClient: (id: string | null) => void;
  startTraining: () => void;
  stopTraining: () => void;
  advanceRound: (metrics: RoundMetrics, clients: ClientNode[], newLogs: LogEntry[]) => void;
  setSystemStatus: (status: SystemStatus) => void;
  setTrainingPhase: (phase: TrainingPhase) => void;
  setActiveClients: (ids: string[]) => void;
  addLogs: (logs: LogEntry[]) => void;
  clearLogs: () => void;
  updateActiveHyperparams: (params: Partial<Hyperparams>) => void;
}

export const useFLStore = create<FLState>((set) => ({
  currentPage: 'dashboard',
  sidebarCollapsed: false,

  currentRound: 0,
  maxRounds: 50,
  isTraining: false,
  systemStatus: 'idle',
  trainingPhase: 'waiting',
  activeClientIds: [],

  clients: initialClients,
  selectedClientId: null,
  roundHistory: [],
  logs: [
    { id: 'boot-1', timestamp: Date.now() - 6000, type: 'info',    message: 'FedVision server initialized — PHANTOM-FL runtime v2.4.1', source: 'System' },
    { id: 'boot-2', timestamp: Date.now() - 5000, type: 'info',    message: '8 client nodes registered and health-checked', source: 'Server' },
    { id: 'boot-3', timestamp: Date.now() - 4000, type: 'success', message: 'Healthcare federated learning environment ready', source: 'System' },
    { id: 'boot-4', timestamp: Date.now() - 3000, type: 'debug',   message: 'WebSocket channels established for all clients', source: 'Network' },
  ],
  experiments: [
    makeCompletedExp('exp-1', 'PHANTOM-FL Baseline', 'Standard FedAvg with baseline PHANTOM architecture', 0.847, 30, ['baseline', 'fedavg', 'phantom-fl'], { aggregation: 'FedAvg', learningRate: 0.01 }),
    makeCompletedExp('exp-2', 'HFL-MM v1', 'Hierarchical multi-modal FL — first iteration', 0.891, 50, ['hierarchical', 'multimodal', 'hfl-mm'], { aggregation: 'FedProx', learningRate: 0.005, localEpochs: 8 }),
    makeCompletedExp('exp-3', 'DP-FedAvg Privacy Test', 'Differential privacy experiment with ε=0.5', 0.812, 40, ['privacy', 'dp', 'fedavg'], { aggregation: 'FedAvg', privacyBudget: 0.5, learningRate: 0.008 }),
    {
      id: 'exp-current',
      name: 'HFL-MM v2 (Active)',
      status: 'running',
      startTime: Date.now(),
      hyperparams: {
        learningRate: 0.001, rounds: 50, clientsPerRound: 8,
        aggregation: 'FedProx', localEpochs: 5, batchSize: 32,
        momentum: 0.9, weightDecay: 0.0001, privacyBudget: 1.0, compressionRatio: 0.85,
      },
      metrics: [],
      bestAccuracy: 0,
      description: 'Current active run — HFL-MM with FedProx and gradient compression',
      tags: ['active', 'fedprox', 'hfl-mm', 'v2', 'compression'],
    },
  ],
  activeExperimentId: 'exp-current',

  setPage: (page) => set({ currentPage: page }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  selectClient: (id) => set({ selectedClientId: id }),

  startTraining: () => set({ isTraining: true, systemStatus: 'training' }),
  stopTraining: () => set({
    isTraining: false, systemStatus: 'idle',
    trainingPhase: 'waiting', activeClientIds: [],
  }),

  advanceRound: (metrics, clients, newLogs) => set((s) => {
    const updatedExps = s.experiments.map((exp) =>
      exp.id === s.activeExperimentId
        ? { ...exp, metrics: [...exp.metrics, metrics], bestAccuracy: Math.max(exp.bestAccuracy, metrics.globalAccuracy) }
        : exp
    );
    return {
      currentRound: metrics.round,
      clients,
      roundHistory: [...s.roundHistory, metrics],
      logs: [...newLogs, ...s.logs].slice(0, 600),
      experiments: updatedExps,
      trainingPhase: 'waiting',
      activeClientIds: [],
    };
  }),

  setSystemStatus: (status) => set({ systemStatus: status }),
  setTrainingPhase: (phase) => set({ trainingPhase: phase }),
  setActiveClients: (ids) => set({ activeClientIds: ids }),
  addLogs: (logs) => set((s) => ({ logs: [...logs, ...s.logs].slice(0, 600) })),
  clearLogs: () => set({ logs: [] }),

  updateActiveHyperparams: (params) => set((s) => ({
    experiments: s.experiments.map((exp) =>
      exp.id === s.activeExperimentId
        ? { ...exp, hyperparams: { ...exp.hyperparams, ...params } }
        : exp
    ),
  })),
}));
