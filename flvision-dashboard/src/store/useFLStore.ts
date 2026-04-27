import { create } from 'zustand';
import {
  ClientNode, EdgeServer, RoundMetrics, LogEntry, ExperimentRun,
  Page, SystemStatus, TrainingPhase, Hyperparams,
} from '../types';

// ── Real device data from partition_meta.json (6 devices, 2 edges, 5000 samples) ──
const initialClients: ClientNode[] = [
  {
    id: 'device_00', name: 'HC-A1', edgeId: 0,
    accuracy: 0.611, loss: 0.921, datasetSize: 573, nTrain: 401, nVal: 85, nTest: 87,
    lastUpdate: Date.now(), status: 'active', latency: 43, localRounds: 0,
    classDist: { NORM: 58, MI: 151, STTC: 75, CD: 127, HYP: 162 },
    dominantClass: 'HYP', gradientNorm: 0.241, epsilonSpent: 0,
  },
  {
    id: 'device_01', name: 'HC-A2', edgeId: 0,
    accuracy: 0.578, loss: 0.963, datasetSize: 594, nTrain: 415, nVal: 89, nTest: 90,
    lastUpdate: Date.now(), status: 'active', latency: 61, localRounds: 0,
    classDist: { NORM: 55, MI: 91, STTC: 233, CD: 98, HYP: 117 },
    dominantClass: 'STTC', gradientNorm: 0.298, epsilonSpent: 0,
  },
  {
    id: 'device_02', name: 'HC-A3', edgeId: 0,
    accuracy: 0.633, loss: 0.856, datasetSize: 896, nTrain: 627, nVal: 134, nTest: 135,
    lastUpdate: Date.now(), status: 'active', latency: 37, localRounds: 0,
    classDist: { NORM: 212, MI: 149, STTC: 111, CD: 207, HYP: 217 },
    dominantClass: 'HYP', gradientNorm: 0.204, epsilonSpent: 0,
  },
  {
    id: 'device_03', name: 'HC-B1', edgeId: 1,
    accuracy: 0.604, loss: 0.934, datasetSize: 689, nTrain: 482, nVal: 103, nTest: 104,
    lastUpdate: Date.now(), status: 'active', latency: 55, localRounds: 0,
    classDist: { NORM: 186, MI: 132, STTC: 107, CD: 173, HYP: 91 },
    dominantClass: 'NORM', gradientNorm: 0.263, epsilonSpent: 0,
  },
  {
    id: 'device_04', name: 'HC-B2', edgeId: 1,
    accuracy: 0.619, loss: 0.899, datasetSize: 919, nTrain: 643, nVal: 137, nTest: 139,
    lastUpdate: Date.now(), status: 'idle', latency: 72, localRounds: 0,
    classDist: { NORM: 213, MI: 199, STTC: 245, CD: 124, HYP: 138 },
    dominantClass: 'STTC', gradientNorm: 0.237, epsilonSpent: 0,
  },
  {
    id: 'device_05', name: 'HC-B3', edgeId: 1,
    accuracy: 0.641, loss: 0.844, datasetSize: 1329, nTrain: 930, nVal: 199, nTest: 200,
    lastUpdate: Date.now(), status: 'active', latency: 48, localRounds: 0,
    classDist: { NORM: 276, MI: 278, STTC: 229, CD: 271, HYP: 275 },
    dominantClass: 'MI', gradientNorm: 0.219, epsilonSpent: 0,
  },
];

const initialEdges: EdgeServer[] = [
  { id: 0, name: 'Edge-A', deviceIds: ['device_00', 'device_01', 'device_02'], status: 'idle', accuracy: 0, latency: 0 },
  { id: 1, name: 'Edge-B', deviceIds: ['device_03', 'device_04', 'device_05'], status: 'idle', accuracy: 0, latency: 0 },
];

// ── Synthetic completed experiment generator ──────────────────────────────────
function makeCompletedExp(
  id: string, name: string, shortName: string, desc: string,
  targetAcc: number, nRounds: number, tags: string[],
  privacyEnabled: boolean, hp: Partial<Hyperparams> = {}
): ExperimentRun {
  const metrics: RoundMetrics[] = [];
  let acc = 0.50 + Math.random() * 0.04;
  let loss = 1.05 + Math.random() * 0.15;
  let epsSpent = 0;
  const epsBudget = hp.privacyBudget ?? 0;
  const epsPerRound = privacyEnabled && epsBudget > 0 ? epsBudget / nRounds : 0;
  const sparsity = hp.sparsity ?? 0;

  for (let r = 1; r <= nRounds; r++) {
    const gap = targetAcc - acc;
    acc = Math.min(targetAcc + 0.003, acc + 0.008 * gap * (0.85 + Math.random() * 0.3));
    loss = Math.max(0.055, loss * (0.972 + (Math.random() - 0.5) * 0.01));
    epsSpent = Math.min(epsBudget, epsSpent + epsPerRound);
    const compRatio = sparsity > 0 ? (1 - sparsity) : 1.0;
    metrics.push({
      round: r, globalAccuracy: acc, globalLoss: loss,
      macroAuc: acc * 0.987 + 0.009,
      epsilonSpent: epsSpent,
      timestamp: Date.now() - (nRounds - r) * 3200 - 400000,
      participatingClients: 6,
      avgLatency: 32 + Math.random() * 52,
      communicationBytes: Math.round(820000 * compRatio + Math.random() * 300000),
      commReduction: sparsity > 0 ? (1 - compRatio) * 100 + Math.random() * 3 : 0,
      avgSetSize: 1.15 + Math.random() * 0.9,
    });
  }

  const baseHp: Hyperparams = {
    learningRate: 1e-3, rounds: nRounds, tauE: 3, clientsPerRound: 6,
    aggregation: 'FedAvg', localEpochs: 5, batchSize: 64,
    momentum: 0.9, weightDecay: 1e-4, privacyBudget: 0, privacyDelta: 1e-5,
    noiseMult: 1.1, maxGradNorm: 1.0, sparsity: 0, quantBits: 8,
    nDevices: 6, nEdges: 2, nClasses: 5, ...hp,
  };

  return {
    id, name, shortName, description: desc, status: 'completed', tags, privacyEnabled,
    startTime: Date.now() - nRounds * 3200 - 480000,
    endTime: Date.now() - 180000,
    hyperparams: baseHp,
    metrics,
    bestAccuracy: metrics[metrics.length - 1]?.globalAccuracy ?? targetAcc,
    targetAccuracy: targetAcc,
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
  activeEdgeIds: number[];
  clients: ClientNode[];
  edges: EdgeServer[];
  selectedClientId: string | null;
  roundHistory: RoundMetrics[];
  logs: LogEntry[];
  experiments: ExperimentRun[];
  activeExperimentId: string | null;

  setPage: (page: Page) => void;
  toggleSidebar: () => void;
  selectClient: (id: string | null) => void;
  startTraining: () => void;
  stopTraining: () => void;
  advanceRound: (metrics: RoundMetrics, clients: ClientNode[], edges: EdgeServer[], newLogs: LogEntry[]) => void;
  setSystemStatus: (status: SystemStatus) => void;
  setTrainingPhase: (phase: TrainingPhase) => void;
  setActiveClients: (ids: string[]) => void;
  setActiveEdges: (ids: number[]) => void;
  addLogs: (logs: LogEntry[]) => void;
  clearLogs: () => void;
  updateActiveHyperparams: (params: Partial<Hyperparams>) => void;
}

export const useFLStore = create<FLState>((set) => ({
  currentPage: 'dashboard',
  sidebarCollapsed: false,
  currentRound: 0,
  maxRounds: 20,
  isTraining: false,
  systemStatus: 'idle',
  trainingPhase: 'waiting',
  activeClientIds: [],
  activeEdgeIds: [],
  clients: initialClients,
  edges: initialEdges,
  selectedClientId: null,
  roundHistory: [],

  logs: [
    { id: 'b1', timestamp: Date.now() - 8000, type: 'info',    source: 'System',    message: 'HFL-MM-HC runtime initialized — PTB-XL + CheXpert pipeline ready' },
    { id: 'b2', timestamp: Date.now() - 7000, type: 'info',    source: 'System',    message: '6 IoT devices registered: Edge-A (HC-A1/A2/A3) · Edge-B (HC-B1/B2/B3)' },
    { id: 'b3', timestamp: Date.now() - 6000, type: 'info',    source: 'Data',      message: 'Partition loaded — 5,000 samples · Dirichlet α=5.0 · 5 ECG classes (NORM/MI/STTC/CD/HYP)' },
    { id: 'b4', timestamp: Date.now() - 5000, type: 'success', source: 'DP-Engine', message: 'Opacus DP-SGD ready — ε=1.0 δ=1e-5 σ=1.1 C=1.0 (Gaussian mechanism)' },
    { id: 'b5', timestamp: Date.now() - 4000, type: 'info',    source: 'Compress',  message: 'Gradient compression: Top-20% sparsification + INT8 quantization → 20× reduction' },
    { id: 'b6', timestamp: Date.now() - 3000, type: 'success', source: 'FedConform', message: 'FedConform-HC (IP-9) calibration sets initialized per edge cluster' },
    { id: 'b7', timestamp: Date.now() - 2000, type: 'debug',   source: 'FedMamba',  message: 'FedMamba-HC ECG encoder (IP-1): Mamba SSM blocks ready on device' },
    { id: 'b8', timestamp: Date.now() - 1000, type: 'success', source: 'System',    message: 'HFL topology live: 6 devices → 2 edges → 1 cloud | Awaiting training start' },
  ],

  experiments: [
    makeCompletedExp('b0', 'B0 — Centralized', 'B0',
      'Upper bound: all 5,000 samples pooled, centralized training on 1 node. No FL, no DP, no hierarchy. Serves as accuracy ceiling.',
      0.850, 10, ['centralized', 'upper-bound', 'no-fl', 'no-dp'], false,
      { aggregation: 'Centralized', localEpochs: 10, sparsity: 0, privacyBudget: 0 }),
    makeCompletedExp('b1', 'B1 — Local Only', 'B1',
      'Lower bound: each device trains independently on its own data only. No federation. Severe non-IID (α=0.5) causes model drift.',
      0.710, 5, ['local', 'lower-bound', 'no-fl', 'no-dp'], false,
      { aggregation: 'Local', localEpochs: 5, sparsity: 0, privacyBudget: 0 }),
    makeCompletedExp('b2', 'B2 — FedAvg', 'B2',
      'Standard FedAvg (McMahan 2017): global weighted averaging every round. Flat FL, all 6 devices participate. No DP, no hierarchy.',
      0.840, 15, ['fedavg', 'flat-fl', 'no-dp', 'baseline'], false,
      { aggregation: 'FedAvg', sparsity: 0, privacyBudget: 0 }),
    makeCompletedExp('b3', 'B3 — FedProx', 'B3',
      'FedProx (Li 2020) μ=0.01: proximal regularization prevents local divergence under non-IID. Flat FL with better convergence than FedAvg.',
      0.845, 15, ['fedprox', 'flat-fl', 'no-dp', 'baseline'], false,
      { aggregation: 'FedProx', sparsity: 0, privacyBudget: 0 }),
    makeCompletedExp('b4', 'B4 — DP-FedAvg', 'B4',
      'Flat DP-FedAvg (Geyer 2017) ε=1.0: DP-SGD on each device with single-tier aggregation. Privacy protected but no hierarchical structure.',
      0.820, 15, ['dp-fedavg', 'flat-fl', 'privacy', 'baseline'], true,
      { aggregation: 'FedAvg', privacyBudget: 1.0, sparsity: 0 }),
    makeCompletedExp('b5', 'B5 — MOON', 'B5',
      'MOON (Li 2021) μ=5.0: model-contrastive FL — positive/negative pairs reduce representation divergence under non-IID. No DP.',
      0.835, 15, ['moon', 'contrastive', 'flat-fl', 'no-dp', 'baseline'], false,
      { aggregation: 'MOON', sparsity: 0, privacyBudget: 0 }),
    {
      id: 'p1',
      name: 'P1 — HFL-MM-HC (Ours)',
      shortName: 'P1',
      status: 'running' as const,
      startTime: Date.now(),
      hyperparams: {
        learningRate: 1e-3, rounds: 20, tauE: 5, clientsPerRound: 6,
        aggregation: 'FedAvg', localEpochs: 5, batchSize: 32,
        momentum: 0.9, weightDecay: 1e-4, privacyBudget: 1.0, privacyDelta: 1e-5,
        noiseMult: 1.1, maxGradNorm: 1.0, sparsity: 0.2, quantBits: 8,
        nDevices: 6, nEdges: 2, nClasses: 5,
      },
      metrics: [],
      bestAccuracy: 0,
      targetAccuracy: 0.850,
      description: 'Our novel model: FedMamba-HC ECG encoder (IP-1) + MobileNetV3 CheXpert + FedConform-HC (IP-9) conformal prediction. Two-tier HFL: 6 devices → 2 edges → 1 cloud. DP-SGD ε=1.0 + Top-20% sparsification + INT8 (20× compression). QoS target: Acc ≥80%, AUC ≥0.83, ε≤1.0, P95 latency <100ms.',
      tags: ['hfl-mm-hc', 'phantom-fl', 'fedmamba', 'fedconform', 'two-tier', 'dp', 'active', 'compression'],
      privacyEnabled: true,
    },
  ],
  activeExperimentId: 'p1',

  setPage: (page) => set({ currentPage: page }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  selectClient: (id) => set({ selectedClientId: id }),
  startTraining: () => set({ isTraining: true, systemStatus: 'training' }),
  stopTraining: () => set({
    isTraining: false, systemStatus: 'idle',
    trainingPhase: 'waiting', activeClientIds: [], activeEdgeIds: [],
  }),
  advanceRound: (metrics, clients, edges, newLogs) => set((s) => ({
    currentRound: metrics.round,
    clients,
    edges,
    roundHistory: [...s.roundHistory, metrics],
    logs: [...newLogs, ...s.logs].slice(0, 800),
    experiments: s.experiments.map((exp) =>
      exp.id === s.activeExperimentId
        ? { ...exp, metrics: [...exp.metrics, metrics], bestAccuracy: Math.max(exp.bestAccuracy, metrics.globalAccuracy) }
        : exp
    ),
    trainingPhase: 'waiting',
    activeClientIds: [],
    activeEdgeIds: [],
  })),
  setSystemStatus: (status) => set({ systemStatus: status }),
  setTrainingPhase: (phase) => set({ trainingPhase: phase }),
  setActiveClients: (ids) => set({ activeClientIds: ids }),
  setActiveEdges: (ids) => set({ activeEdgeIds: ids }),
  addLogs: (logs) => set((s) => ({ logs: [...logs, ...s.logs].slice(0, 800) })),
  clearLogs: () => set({ logs: [] }),
  updateActiveHyperparams: (params) => set((s) => ({
    experiments: s.experiments.map((exp) =>
      exp.id === s.activeExperimentId
        ? { ...exp, hyperparams: { ...exp.hyperparams, ...params } }
        : exp
    ),
  })),
}));
