
export type Page = 'dashboard' | 'clients' | 'training' | 'experiments' | 'logs' | 'settings';

export type ClientStatus = 'active' | 'idle' | 'training' | 'aggregating' | 'disconnected';
export type SystemStatus = 'idle' | 'training' | 'edge-agg' | 'cloud-agg' | 'completed' | 'error';
export type LogType = 'info' | 'success' | 'warning' | 'error' | 'debug';
export type ExperimentStatus = 'running' | 'completed' | 'failed' | 'paused';
export type TrainingPhase = 'waiting' | 'local-training' | 'edge-agg' | 'cloud-agg' | 'complete';

export type ECGClass = 'NORM' | 'MI' | 'STTC' | 'CD' | 'HYP';

export interface ClassDist { NORM: number; MI: number; STTC: number; CD: number; HYP: number; }

export interface ClientNode {
  id: string;
  name: string;
  edgeId: number;
  accuracy: number;
  loss: number;
  datasetSize: number;
  nTrain: number; nVal: number; nTest: number;
  lastUpdate: number;
  status: ClientStatus;
  latency: number;
  localRounds: number;
  dominantClass: ECGClass;
  classDist: ClassDist;
  gradientNorm: number;
  epsilonSpent: number;
}

export interface EdgeServer {
  id: number;
  name: string;
  deviceIds: string[];
  status: 'idle' | 'aggregating' | 'broadcasting';
  accuracy: number;
  latency: number;
}

export interface RoundMetrics {
  round: number;
  globalAccuracy: number;
  globalLoss: number;
  macroAuc: number;
  epsilonSpent: number;
  timestamp: number;
  participatingClients: number;
  avgLatency: number;
  communicationBytes: number;
  commReduction: number;
  avgSetSize: number;
}

export interface LogEntry {
  id: string;
  timestamp: number;
  type: LogType;
  message: string;
  source: string;
  round?: number;
}

export interface Hyperparams {
  learningRate: number;
  rounds: number;
  tauE: number;
  clientsPerRound: number;
  aggregation: string;
  localEpochs: number;
  batchSize: number;
  momentum: number;
  weightDecay: number;
  privacyBudget: number;
  privacyDelta: number;
  noiseMult: number;
  maxGradNorm: number;
  sparsity: number;
  quantBits: number;
  nDevices: number;
  nEdges: number;
  nClasses: number;
}

export interface ExperimentRun {
  id: string;
  name: string;
  shortName: string;
  status: ExperimentStatus;
  startTime: number;
  endTime?: number;
  hyperparams: Hyperparams;
  metrics: RoundMetrics[];
  bestAccuracy: number;
  targetAccuracy: number;
  description: string;
  tags: string[];
  privacyEnabled: boolean;
}
