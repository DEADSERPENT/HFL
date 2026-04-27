import { useEffect, useRef } from 'react';
import { useFLStore } from '../store/useFLStore';
import { ClientNode, EdgeServer, LogEntry, RoundMetrics } from '../types';

let logCounter = 0;
function uid() { return `log-${Date.now()}-${++logCounter}`; }

// Expected accuracy trajectory for P1 HFL-MM-HC over 15 rounds
const ACC_TARGETS = [
  0.643, 0.668, 0.688, 0.704, 0.718, 0.730, 0.742, 0.754,
  0.764, 0.774, 0.783, 0.793, 0.803, 0.815, 0.832,
];

function buildRoundLogs(
  round: number, clients: ClientNode[],
  globalAcc: number, globalLoss: number, epsSpent: number
): LogEntry[] {
  const now = Date.now();
  const entries: LogEntry[] = [];

  entries.push({
    id: uid(), timestamp: now - 3600, type: 'info', source: 'Cloud', round,
    message: `Round ${round} — broadcasting global HFL-MM-HC model to Edge-A + Edge-B (τ_e=3)`,
  });

  entries.push({
    id: uid(), timestamp: now - 3100, type: 'debug', source: 'Edge-A', round,
    message: 'Relaying global model to HC-A1 (device_00) · HC-A2 (device_01) · HC-A3 (device_02)',
  });
  entries.push({
    id: uid(), timestamp: now - 3000, type: 'debug', source: 'Edge-B', round,
    message: 'Relaying global model to HC-B1 (device_03) · HC-B2 (device_04) · HC-B3 (device_05)',
  });

  clients.forEach((c, i) => {
    const edgeName = c.edgeId === 0 ? 'Edge-A' : 'Edge-B';
    const compBytes = Math.round(c.datasetSize * 820 * 0.2);
    entries.push({
      id: uid(), timestamp: now - 2400 + i * 80, source: c.name, round,
      type: c.status === 'disconnected' ? 'warning' : 'success',
      message: `[${edgeName}] acc ${(c.accuracy * 100).toFixed(2)}%  loss ${c.loss.toFixed(4)}  ‖∇‖ ${c.gradientNorm.toFixed(3)}  ε ${epsSpent.toFixed(3)}  → ${compBytes.toLocaleString()}B (compressed)`,
    });
  });

  const edge0 = clients.filter((c) => c.edgeId === 0);
  const edge1 = clients.filter((c) => c.edgeId === 1);
  const e0data = edge0.reduce((s, c) => s + c.datasetSize, 0);
  const e1data = edge1.reduce((s, c) => s + c.datasetSize, 0);
  const e0acc = edge0.reduce((s, c) => s + c.accuracy * c.datasetSize, 0) / e0data;
  const e1acc = edge1.reduce((s, c) => s + c.accuracy * c.datasetSize, 0) / e1data;

  entries.push({
    id: uid(), timestamp: now - 1400, type: 'info', source: 'Edge-A', round,
    message: `Edge-A agg done — 3 updates · FedProx μ=0.01 · edge_acc ${(e0acc * 100).toFixed(2)}% · FedConform-HC recalibrated (${e0data} samples)`,
  });
  entries.push({
    id: uid(), timestamp: now - 1350, type: 'info', source: 'Edge-B', round,
    message: `Edge-B agg done — 3 updates · FedProx μ=0.01 · edge_acc ${(e1acc * 100).toFixed(2)}% · FedConform-HC recalibrated (${e1data} samples)`,
  });

  entries.push({
    id: uid(), timestamp: now - 700, type: 'info', source: 'Cloud', round,
    message: `Cloud agg: Edge-A (${e0data} samples) + Edge-B (${e1data} samples) → global model updated`,
  });

  entries.push({
    id: uid(), timestamp: now, type: 'success', source: 'Cloud', round,
    message: `Round ${round} done — global_acc ${(globalAcc * 100).toFixed(3)}%  loss ${globalLoss.toFixed(5)}  ε ${epsSpent.toFixed(4)}/1.0`,
  });

  if (round % 5 === 0) {
    entries.push({
      id: uid(), timestamp: now + 50, type: 'info', source: 'System', round,
      message: `Checkpoint → SIMULATORS/checkpoints/best_model_hc.pt (round ${round})`,
    });
  }

  if (round >= 8) {
    const hist = useFLStore.getState().roundHistory;
    const prev = hist[hist.length - 1];
    if (!prev || globalAcc > prev.globalAccuracy + 0.004) {
      entries.push({
        id: uid(), timestamp: now + 100, type: 'success', source: 'Monitor', round,
        message: `★ New best acc ${(globalAcc * 100).toFixed(3)}% — hfl_mm_hc_results.csv updated`,
      });
    }
  }

  if (epsSpent >= 0.93) {
    entries.push({
      id: uid(), timestamp: now + 120, type: 'warning', source: 'DP-Engine', round,
      message: `Privacy budget near limit — ε_spent ${epsSpent.toFixed(4)} / 1.0 (δ=1e-5, σ=1.1, C=1.0)`,
    });
  }

  if (Math.random() < 0.1) {
    const c = clients[Math.floor(Math.random() * clients.length)];
    entries.push({
      id: uid(), timestamp: now + 160, type: 'warning', source: 'Network', round,
      message: `High latency — ${c.name} (device_0${clients.indexOf(c)}) ${(70 + Math.random() * 55).toFixed(0)}ms · edge: ${c.edgeId === 0 ? 'Edge-A' : 'Edge-B'}`,
    });
  }

  return entries;
}

export function useSimulation() {
  const store = useFLStore;
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const phaseRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isRoundRunning = useRef(false);

  const runOneRound = () => {
    if (isRoundRunning.current) return;
    const state = store.getState();
    if (!state.isTraining) return;
    if (state.currentRound >= state.maxRounds) {
      state.stopTraining();
      state.addLogs([{
        id: uid(), timestamp: Date.now(), type: 'success', source: 'System',
        message: `Training complete — 15 rounds finished · results → SIMULATORS/results/phase5/hfl_mm_hc_results.csv`,
      }]);
      return;
    }

    isRoundRunning.current = true;
    const round = state.currentRound + 1;

    // Phase 1: local training
    state.setTrainingPhase('local-training');
    state.setSystemStatus('training');
    state.setActiveClients(state.clients.map((c) => c.id));
    state.setActiveEdges([]);

    phaseRef.current = setTimeout(() => {
      // Phase 2: edge aggregation
      state.setTrainingPhase('edge-agg');
      state.setSystemStatus('edge-agg');
      state.setActiveClients([]);
      state.setActiveEdges([0, 1]);

      setTimeout(() => {
        // Phase 3: cloud aggregation
        state.setTrainingPhase('cloud-agg');
        state.setSystemStatus('cloud-agg');
        state.setActiveEdges([]);

        setTimeout(() => {
          const current = store.getState().clients;
          const accTarget = ACC_TARGETS[Math.min(round - 1, ACC_TARGETS.length - 1)];
          const totalData = current.reduce((s, c) => s + c.datasetSize, 0);

          const updated: ClientNode[] = current.map((c) => {
            const targetLocal = accTarget * (0.93 + Math.random() * 0.1);
            const gap = targetLocal - c.accuracy;
            const newAcc = Math.min(0.962, Math.max(0.35, c.accuracy + gap * 0.22 + (Math.random() - 0.48) * 0.008));
            const lossRed = 0.014 + Math.random() * 0.016;
            const newLoss = Math.max(0.055, c.loss * (1 - lossRed) + (Math.random() - 0.5) * 0.006);
            return {
              ...c,
              accuracy: newAcc,
              loss: newLoss,
              latency: 20 + Math.random() * 85,
              lastUpdate: Date.now(),
              status: (Math.random() > 0.05 ? 'active' : 'idle') as ClientNode['status'],
              localRounds: c.localRounds + 1,
              gradientNorm: 0.08 + Math.random() * 0.28,
              epsilonSpent: Math.min(1.0, c.epsilonSpent + 1.0 / 15),
            };
          });

          const globalAcc = updated.reduce((s, c) => s + c.accuracy * c.datasetSize, 0) / totalData;
          const globalLoss = updated.reduce((s, c) => s + c.loss * c.datasetSize, 0) / totalData;
          const avgLat = updated.reduce((s, c) => s + c.latency, 0) / updated.length;
          const epsSpent = Math.min(1.0, round / 15);
          const compRatio = (1 - 0.2) * (8 / 32); // sparsity + INT8
          const uncompressed = 820000;
          const compressed = uncompressed * compRatio;
          const commReduction = ((uncompressed - compressed) / uncompressed) * 100;

          const updatedEdges: EdgeServer[] = state.edges.map((edge) => {
            const devs = updated.filter((c) => c.edgeId === edge.id);
            const data = devs.reduce((s, c) => s + c.datasetSize, 0);
            return {
              ...edge,
              accuracy: devs.reduce((s, c) => s + c.accuracy * c.datasetSize, 0) / data,
              latency: devs.reduce((s, c) => s + c.latency, 0) / devs.length,
              status: 'idle' as const,
            };
          });

          const metrics: RoundMetrics = {
            round, globalAccuracy: globalAcc, globalLoss,
            macroAuc: globalAcc * 0.987 + 0.009,
            epsilonSpent: epsSpent,
            timestamp: Date.now(),
            participatingClients: updated.filter((c) => c.status !== 'disconnected').length,
            avgLatency: avgLat,
            communicationBytes: Math.round(compressed + Math.random() * 40000),
            commReduction,
            avgSetSize: 1.1 + Math.random() * 0.85,
          };

          const logs = buildRoundLogs(round, updated, globalAcc, globalLoss, epsSpent);
          store.getState().advanceRound(metrics, updated, updatedEdges, logs);
          isRoundRunning.current = false;
        }, 600);
      }, 800);
    }, 1400);
  };

  useEffect(() => {
    const boot = setTimeout(() => useFLStore.getState().startTraining(), 900);
    return () => clearTimeout(boot);
  }, []);

  useEffect(() => {
    const unsub = useFLStore.subscribe((state) => {
      if (state.isTraining && !intervalRef.current) {
        phaseRef.current = setTimeout(runOneRound, 1200);
        intervalRef.current = setInterval(runOneRound, 3500);
      }
      if (!state.isTraining && intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
        if (phaseRef.current) clearTimeout(phaseRef.current);
        isRoundRunning.current = false;
      }
    });
    return () => {
      unsub();
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (phaseRef.current) clearTimeout(phaseRef.current);
      isRoundRunning.current = false;
    };
  }, []);
}
