export type Page = 'dashboard' | 'clients' | 'training' | 'experiments' | 'logs' | 'settings';

export type ClientStatus = 'active' | 'idle' | 'training' | 'aggregating' | 'disconnected';
export type SystemStatus = 'idle' | 'training' | 'aggregating' | 'completed' | 'error';
export type LogType = 'info' | 'success' | 'warning' | 'error' | 'debug';
export type ExperimentStatus = 'running' | 'completed' | 'failed' | 'paused';
export type TrainingPhase = 'waiting' | 'local-training' | 'aggregating' | 'complete';

export interface ClientNode {
  id: string;
  name: string;
  accuracy: number;
  loss: number;
  datasetSize: number;
  lastUpdate: number;
  status: ClientStatus;
  latency: number;
  localRounds: number;
  hospitalType: string;
  location: string;
  gradientNorm: number;
}

export interface RoundMetrics {
  round: number;
  globalAccuracy: number;
  globalLoss: number;
  timestamp: number;
  participatingClients: number;
  avgLatency: number;
  communicationBytes: number;
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
  clientsPerRound: number;
  aggregation: string;
  localEpochs: number;
  batchSize: number;
  momentum: number;
  weightDecay: number;
  privacyBudget: number;
  compressionRatio: number;
}

export interface ExperimentRun {
  id: string;
  name: string;
  status: ExperimentStatus;
  startTime: number;
  endTime?: number;
  hyperparams: Hyperparams;
  metrics: RoundMetrics[];
  bestAccuracy: number;
  description: string;
  tags: string[];
}
