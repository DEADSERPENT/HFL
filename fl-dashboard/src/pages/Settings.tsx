import React, { useState } from 'react';
import { Server, Shield, Network, Database, Bell, Info, Check } from 'lucide-react';
import clsx from 'clsx';
import { useFLStore } from '../store/useFLStore';

function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="panel overflow-hidden">
      <div className="panel-header">
        <span className="panel-header-title">
          <Icon size={11} />
          {title}
        </span>
      </div>
      <div className="p-4 flex flex-col gap-4">{children}</div>
    </div>
  );
}

function Field({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-8">
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-[12px] font-medium text-fl-text">{label}</span>
        {description && <span className="text-[10px] text-fl-muted">{description}</span>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={clsx(
        'w-9 h-5 rounded-full relative transition-colors duration-200 shrink-0',
        checked ? 'bg-fl-primary' : 'bg-fl-border',
      )}
    >
      <span className={clsx(
        'absolute top-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200',
        checked ? 'translate-x-4' : 'translate-x-0.5',
      )} />
    </button>
  );
}

export function Settings() {
  const { experiments, activeExperimentId, clearLogs } = useFLStore();
  const activeExp = experiments.find((e) => e.id === activeExperimentId);

  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState({
    serverHost: '0.0.0.0',
    serverPort: 8080,
    wsPort: 8081,
    maxClients: 20,
    roundTimeout: 30,
    minParticipants: 3,
    // Privacy
    dpEnabled: false,
    dpEpsilon: 1.0,
    dpDelta: 1e-5,
    secureAgg: true,
    // Network
    compressionEnabled: true,
    maxBandwidth: 100,
    reconnectAttempts: 3,
    // Monitoring
    metricsInterval: 1,
    logLevel: 'info',
    alertOnDrop: true,
    alertThreshold: 5,
    // Data
    checkpointInterval: 10,
    checkpointPath: './checkpoints',
    maxCheckpoints: 5,
  });

  const set = (key: string, value: unknown) => setSettings((s) => ({ ...s, [key]: value }));

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 gap-4 page-enter">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-sm font-semibold text-fl-text">System Configuration</h2>
          <p className="text-[11px] text-fl-muted mt-0.5">
            FedVision server · PHANTOM-FL / HFL-MM runtime
          </p>
        </div>
        <button
          onClick={handleSave}
          className={clsx('fl-btn transition-all', saved ? 'fl-btn-secondary text-fl-green' : 'fl-btn-primary')}
        >
          {saved ? <><Check size={13} /> Saved</> : 'Save Changes'}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Server */}
        <Section title="Server Configuration" icon={Server}>
          <Field label="Host Address" description="IP address to bind the FL server">
            <input
              value={settings.serverHost}
              onChange={(e) => set('serverHost', e.target.value)}
              className="fl-input w-40 text-right font-mono text-xs"
            />
          </Field>
          <Field label="HTTP Port">
            <input
              type="number" value={settings.serverPort}
              onChange={(e) => set('serverPort', +e.target.value)}
              className="fl-input w-24 text-right font-mono text-xs"
            />
          </Field>
          <Field label="WebSocket Port">
            <input
              type="number" value={settings.wsPort}
              onChange={(e) => set('wsPort', +e.target.value)}
              className="fl-input w-24 text-right font-mono text-xs"
            />
          </Field>
          <Field label="Max Clients" description="Maximum number of concurrent client connections">
            <input
              type="number" value={settings.maxClients}
              onChange={(e) => set('maxClients', +e.target.value)}
              className="fl-input w-24 text-right font-mono text-xs"
            />
          </Field>
          <Field label="Round Timeout (s)" description="Seconds before a round is forcibly aggregated">
            <input
              type="number" value={settings.roundTimeout}
              onChange={(e) => set('roundTimeout', +e.target.value)}
              className="fl-input w-24 text-right font-mono text-xs"
            />
          </Field>
          <Field label="Min Participants" description="Minimum clients required to start aggregation">
            <input
              type="number" value={settings.minParticipants}
              onChange={(e) => set('minParticipants', +e.target.value)}
              className="fl-input w-24 text-right font-mono text-xs"
            />
          </Field>
        </Section>

        {/* Privacy & Security */}
        <Section title="Privacy & Security" icon={Shield}>
          <Field label="Differential Privacy" description="Add calibrated noise to protect client gradients">
            <Toggle checked={settings.dpEnabled} onChange={(v) => set('dpEnabled', v)} />
          </Field>
          {settings.dpEnabled && (
            <>
              <Field label="Privacy Budget ε" description="Lower = more privacy, less accuracy">
                <input
                  type="number" step="0.1" value={settings.dpEpsilon}
                  onChange={(e) => set('dpEpsilon', +e.target.value)}
                  className="fl-input w-28 text-right font-mono text-xs"
                />
              </Field>
              <Field label="Privacy Delta δ">
                <input
                  value={settings.dpDelta.toExponential(0)}
                  onChange={() => {}}
                  className="fl-input w-28 text-right font-mono text-xs"
                  readOnly
                />
              </Field>
            </>
          )}
          <Field label="Secure Aggregation" description="Encrypt client updates during aggregation">
            <Toggle checked={settings.secureAgg} onChange={(v) => set('secureAgg', v)} />
          </Field>
          <div className="pt-2 border-t border-fl-border">
            <div className="flex items-start gap-2 text-[11px] text-fl-muted p-2 bg-fl-secondary rounded">
              <Info size={12} className="mt-0.5 shrink-0 text-fl-primary" />
              <span>Secure aggregation uses threshold secret sharing. Requires all clients to agree before any update is revealed.</span>
            </div>
          </div>
        </Section>

        {/* Network */}
        <Section title="Network & Communication" icon={Network}>
          <Field label="Gradient Compression" description="Reduce communication cost via sparsification">
            <Toggle checked={settings.compressionEnabled} onChange={(v) => set('compressionEnabled', v)} />
          </Field>
          <Field label="Max Bandwidth (MB/s)" description="Per-client bandwidth cap">
            <input
              type="number" value={settings.maxBandwidth}
              onChange={(e) => set('maxBandwidth', +e.target.value)}
              className="fl-input w-28 text-right font-mono text-xs"
            />
          </Field>
          <Field label="Reconnect Attempts" description="Times to retry a failed client connection">
            <input
              type="number" value={settings.reconnectAttempts}
              onChange={(e) => set('reconnectAttempts', +e.target.value)}
              className="fl-input w-24 text-right font-mono text-xs"
            />
          </Field>
        </Section>

        {/* Data & Checkpoints */}
        <Section title="Data & Checkpointing" icon={Database}>
          <Field label="Checkpoint Interval" description="Save model every N rounds">
            <input
              type="number" value={settings.checkpointInterval}
              onChange={(e) => set('checkpointInterval', +e.target.value)}
              className="fl-input w-28 text-right font-mono text-xs"
            />
          </Field>
          <Field label="Checkpoint Path">
            <input
              value={settings.checkpointPath}
              onChange={(e) => set('checkpointPath', e.target.value)}
              className="fl-input w-48 text-right font-mono text-xs"
            />
          </Field>
          <Field label="Max Checkpoints" description="Older checkpoints are pruned">
            <input
              type="number" value={settings.maxCheckpoints}
              onChange={(e) => set('maxCheckpoints', +e.target.value)}
              className="fl-input w-24 text-right font-mono text-xs"
            />
          </Field>
          <Field label="Log Level">
            <select
              value={settings.logLevel}
              onChange={(e) => set('logLevel', e.target.value)}
              className="fl-select"
            >
              {['debug', 'info', 'warning', 'error'].map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </Field>
          <div className="pt-2 border-t border-fl-border">
            <button onClick={clearLogs} className="fl-btn fl-btn-secondary text-[11px] w-full justify-center text-fl-danger">
              Clear All Logs
            </button>
          </div>
        </Section>

        {/* Monitoring */}
        <Section title="Monitoring & Alerts" icon={Bell}>
          <Field label="Metrics Interval (s)" description="How often live metrics are sampled">
            <input
              type="number" value={settings.metricsInterval}
              onChange={(e) => set('metricsInterval', +e.target.value)}
              className="fl-input w-28 text-right font-mono text-xs"
            />
          </Field>
          <Field label="Alert on Accuracy Drop" description="Notify when global accuracy drops">
            <Toggle checked={settings.alertOnDrop} onChange={(v) => set('alertOnDrop', v)} />
          </Field>
          {settings.alertOnDrop && (
            <Field label="Alert Threshold (%)" description="Trigger when drop exceeds this value">
              <input
                type="number" value={settings.alertThreshold}
                onChange={(e) => set('alertThreshold', +e.target.value)}
                className="fl-input w-24 text-right font-mono text-xs"
              />
            </Field>
          )}
        </Section>

        {/* System info */}
        <Section title="System Info" icon={Info}>
          {[
            { label: 'Runtime',      value: 'PHANTOM-FL v2.4.1' },
            { label: 'Model',        value: activeExp?.name ?? 'HFL-MM v2' },
            { label: 'Aggregation',  value: activeExp?.hyperparams.aggregation ?? 'FedProx' },
            { label: 'FL Framework', value: 'FedVision 1.0.0' },
            { label: 'React',        value: '18.2.0' },
            { label: 'Node Env',     value: 'development' },
          ].map((r) => (
            <div key={r.label} className="flex justify-between text-[11px]">
              <span className="text-fl-muted">{r.label}</span>
              <span className="font-mono text-fl-text">{r.value}</span>
            </div>
          ))}
        </Section>
      </div>
    </div>
  );
}
