import { useEffect, useRef } from 'react';
import { useFLStore } from '../store/useFLStore';
import { ClientNode, LogEntry, RoundMetrics } from '../types';

let logCounter = 0;
function uid() { return `log-${Date.now()}-${++logCounter}`; }

function buildRoundLogs(
  round: number, clients: ClientNode[], globalAcc: number, globalLoss: number
): LogEntry[] {
  const now = Date.now();
  const entries: LogEntry[] = [];

  entries.push({
    id: uid(), timestamp: now - 2800, type: 'info', source: 'Server', round,
    message: `Round ${round} started — broadcasting global model to ${clients.length} participants`,
  });

  clients.forEach((c, i) => {
    entries.push({
      id: uid(), timestamp: now - 2000 + i * 90, source: c.name, round,
      type: c.status === 'disconnected' ? 'warning' : 'success',
      message: `Local update submitted — acc: ${(c.accuracy * 100).toFixed(2)}%  loss: ${c.loss.toFixed(4)}  Δ‖g‖: ${c.gradientNorm.toFixed(3)}  latency: ${c.latency.toFixed(0)}ms`,
    });
  });

  entries.push({
    id: uid(), timestamp: now - 600, type: 'info', source: 'Aggregator', round,
    message: `Aggregating ${clients.length} updates via FedProx  μ=0.01`,
  });

  entries.push({
    id: uid(), timestamp: now, type: 'success', source: 'Server', round,
    message: `Round ${round} complete — global accuracy: ${(globalAcc * 100).toFixed(3)}%  loss: ${globalLoss.toFixed(5)}`,
  });

  if (round % 5 === 0) {
    entries.push({
      id: uid(), timestamp: now + 50, type: 'info', source: 'System', round,
      message: `Checkpoint saved — weights serialized at round ${round}`,
    });
  }

  if (globalAcc > 0.88 && round > 5) {
    const hist = useFLStore.getState().roundHistory;
    const prev = hist[hist.length - 1];
    if (prev && globalAcc > prev.globalAccuracy + 0.003) {
      entries.push({
        id: uid(), timestamp: now + 100, type: 'success', source: 'Monitor', round,
        message: `★ New best accuracy: ${(globalAcc * 100).toFixed(3)}% — convergence milestone`,
      });
    }
  }

  if (Math.random() < 0.08) {
    entries.push({
      id: uid(), timestamp: now + 150, type: 'warning', source: 'Network', round,
      message: `High latency detected — client "${clients[Math.floor(Math.random() * clients.length)].name}" (${(80 + Math.random() * 60).toFixed(0)}ms)`,
    });
  }

  return entries;
}

export function useSimulation() {
  const store = useFLStore;
  const intervalRef    = useRef<ReturnType<typeof setInterval> | null>(null);
  const phaseRef       = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Guards against overlapping rounds: interval (3200ms) < round duration (2100ms)
  // would cause duplicate round execution without this flag.
  const isRoundRunning = useRef(false);

  const runOneRound = () => {
    if (isRoundRunning.current) return;

    const state = store.getState();
    if (!state.isTraining) return;
    if (state.currentRound >= state.maxRounds) {
      state.stopTraining();
      state.addLogs([{
        id: uid(), timestamp: Date.now(), type: 'success', source: 'System',
        message: `Training complete — ${state.maxRounds} rounds finished. Best accuracy: ${(Math.max(...state.roundHistory.map(r => r.globalAccuracy)) * 100).toFixed(2)}%`,
      }]);
      return;
    }

    isRoundRunning.current = true;
    const round = state.currentRound + 1;

    // Phase 1: broadcast → local training (1200ms)
    state.setTrainingPhase('local-training');
    state.setSystemStatus('training');
    state.setActiveClients(state.clients.map((c) => c.id));

    phaseRef.current = setTimeout(() => {
      // Phase 2: aggregating (900ms)
      state.setTrainingPhase('aggregating');
      state.setSystemStatus('aggregating');
      state.setActiveClients([]);

      setTimeout(() => {
        const current = store.getState().clients;

        const updated: ClientNode[] = current.map((c) => {
          const gain  = 0.0045 * (1 - c.accuracy) * (0.7 + Math.random() * 0.6);
          const noise = (Math.random() - 0.46) * 0.006;
          const newAcc  = Math.min(0.972, Math.max(0.35, c.accuracy + gain + noise));
          const lossRed = 0.012 + Math.random() * 0.018;
          const newLoss = Math.max(0.055, c.loss * (1 - lossRed) + (Math.random() - 0.5) * 0.008);
          return {
            ...c,
            accuracy: newAcc,
            loss: newLoss,
            latency: 18 + Math.random() * 92,
            lastUpdate: Date.now(),
            status: Math.random() > 0.06 ? 'active' : 'idle',
            localRounds: c.localRounds + 1,
            gradientNorm: 0.08 + Math.random() * 0.32,
          } as ClientNode;
        });

        const totalData  = updated.reduce((s, c) => s + c.datasetSize, 0);
        const globalAcc  = updated.reduce((s, c) => s + c.accuracy  * c.datasetSize, 0) / totalData;
        const globalLoss = updated.reduce((s, c) => s + c.loss      * c.datasetSize, 0) / totalData;
        const avgLat     = updated.reduce((s, c) => s + c.latency, 0) / updated.length;

        const metrics: RoundMetrics = {
          round, globalAccuracy: globalAcc, globalLoss,
          timestamp: Date.now(),
          participatingClients: updated.filter((c) => c.status !== 'disconnected').length,
          avgLatency: avgLat,
          communicationBytes: 800000 + Math.random() * 700000,
        };

        const logs = buildRoundLogs(round, updated, globalAcc, globalLoss);
        store.getState().advanceRound(metrics, updated, logs);

        // Release lock — next interval tick can now run
        isRoundRunning.current = false;
      }, 900);
    }, 1200);
  };

  // Auto-start simulation on mount
  useEffect(() => {
    const boot = setTimeout(() => {
      useFLStore.getState().startTraining();
    }, 800);
    return () => clearTimeout(boot);
  }, []);

  // Manage interval based on isTraining state
  useEffect(() => {
    const unsub = useFLStore.subscribe((state) => {
      if (state.isTraining && !intervalRef.current) {
        // Kick off first round, then tick every 3200ms
        const first = setTimeout(runOneRound, 1200);
        intervalRef.current = setInterval(runOneRound, 3200);
        // Store first-timeout id so cleanup can cancel it
        phaseRef.current = first;
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
      if (phaseRef.current)    clearTimeout(phaseRef.current);
      isRoundRunning.current = false;
    };
  }, []);
}
