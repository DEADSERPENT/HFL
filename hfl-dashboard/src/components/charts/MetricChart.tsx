"use client";

import { METRIC_DEFINITIONS } from "@/content/metrics";
import { formatInterval, formatNumber, formatTarget, formatValue } from "@/lib/format";
import { STATUS_META, OUTCOME_LABEL, targetOutcomeOf } from "@/lib/metric-status";
import type { MetricKind, MetricRecord } from "@/lib/types";
import { AccessibleChartFrame, type TableColumn } from "./AccessibleChartFrame";
import { RowChart, type ChartRow, type ReferenceLine, type Scale } from "./RowChart";

type ChartSpec = {
  mode: "bar" | "dot" | "interval" | "stack";
  scale: Scale;
  axisLabel: string;
  disclosure?: string;
  references: ReferenceLine[];
  persistentLabel?: string;
  caveat?: string;
};

const pctFmt = (v: number) => `${v}%`;

export function chartSpec(kind: MetricKind, unit?: string): ChartSpec {
  switch (kind) {
    case "communication":
      return {
        mode: "bar",
        scale: { min: 0, max: 100, type: "linear", ticks: [0, 25, 50, 75, 100], format: pctFmt },
        axisLabel: "Uplink traffic reduction (%)",
        references: [{ value: 50, label: "Target ≥ 50%", kind: "target" }],
      };
    case "round-latency":
      return {
        mode: "bar",
        scale: { min: 0, max: 50, type: "linear", ticks: [0, 10, 20, 30, 40, 50], format: pctFmt },
        axisLabel: "Round-latency reduction (%)",
        disclosure: "the axis runs from 0% to 50% (it starts at zero; the target is any reduction above 0%).",
        references: [],
        persistentLabel: "Simulated in ns-3",
        caveat: "Simulated at packet level in ns-3; not measured on a physical network. Not the same quantity as inference latency.",
      };
    case "energy":
      return {
        mode: "bar",
        scale: { min: 0, max: 100, type: "linear", ticks: [0, 25, 50, 75, 100], format: pctFmt },
        axisLabel: "Modelled energy saving per FL round (%)",
        references: [{ value: 20, label: "Target ≥ 20%", kind: "target" }],
        persistentLabel: "Simulation estimate from CloudSim Plus",
        caveat: "Estimated by CloudSim Plus simulation; not a physical hardware energy measurement.",
      };
    case "inference-latency":
      return {
        mode: "dot",
        scale: { min: 0.1, max: 200, type: "log", ticks: [0.1, 1, 10, 100], format: (v) => `${v} ms` },
        axisLabel: "P95 inference latency (ms, logarithmic scale)",
        disclosure: "logarithmic scale from 0.1 ms to 200 ms, so that millisecond values and the 100 ms budget are both legible.",
        references: [{ value: 100, label: "Budget < 100 ms", kind: "target" }],
        caveat: "Timed on a workstation CPU, not on edge or medical-device hardware.",
      };
    case "update-delivery":
      return {
        mode: "dot",
        scale: { min: 95, max: 100, type: "linear", ticks: [95, 96, 97, 98, 99, 100], format: pctFmt },
        axisLabel: "Updates delivered (%)",
        disclosure: "the axis starts at 95%, not 0%, to make differences around the 99% target visible.",
        references: [{ value: 99, label: "Target > 99%", kind: "target" }],
        persistentLabel: "Simulated in ns-3",
        caveat: "Simulated in ns-3. The eICU value is for the reported two-edge configuration and is below target.",
      };
    case "privacy":
      return {
        mode: "stack",
        scale: { min: 0, max: 1.2, type: "linear", ticks: [0, 0.2, 0.4, 0.6, 0.8, 1, 1.2], format: (v) => v.toFixed(1) },
        axisLabel: "Privacy budget ε (δ = 10⁻⁵)",
        references: [{ value: 1, label: "Target ε ≤ 1", kind: "target" }],
        caveat: "Accounting results under stated assumptions, not measurements of leakage. WEAR is record-level; VitalDB and eICU are patient-level.",
      };
    case "utility":
      if (unit === "accuracy pp")
        return {
          mode: "interval",
          scale: { min: 0, max: 4, type: "linear", ticks: [0, 1, 2, 3, 4], format: (v) => `${v}` },
          axisLabel: "Accuracy loss (percentage points; positive = cost)",
          references: [{ value: 2, label: "Target ≤ 2 points", kind: "target" }],
          caveat: "Record-level guarantee; accuracy points are not comparable with AUROC points.",
        };
      return {
        mode: "interval",
        scale: { min: -3, max: 6, type: "linear", ticks: [-2, 0, 2, 4, 6], format: (v) => formatNumber(v, 0) },
        axisLabel: "AUROC cost (points; positive = cost, negative = private model scored higher)",
        references: [
          { value: 0, label: "No difference", kind: "zero" },
          { value: 2, label: "Target ≤ 2 points", kind: "target" },
        ],
        caveat: "The two eICU rows are separate evaluation paths and must not be combined.",
      };
  }
}

function toRow(r: MetricRecord): ChartRow {
  const def = METRIC_DEFINITIONS[r.kind];
  const ci = r.confidenceInterval;
  const outcome = targetOutcomeOf(r);
  return {
    key: r.id,
    label: r.dataset,
    sublabel: r.variant,
    value: r.value,
    display: formatValue(r),
    status: r.evidenceStatus,
    interval: ci ? { lower: ci.lower, upper: ci.upper, display: formatInterval(ci, r.decimals) } : undefined,
    segments: r.privacy
      ? [
          { value: r.privacy.training, label: "Training", tone: "a" },
          { value: r.privacy.conformal, label: "Conformal", tone: "b" },
        ]
      : undefined,
    ariaLabel: [
      `${def.name}, ${r.dataset}${r.variant ? `, ${r.variant}` : ""}: ${formatValue(r)}`,
      ci ? `95% interval ${formatInterval(ci, r.decimals)}` : "",
      r.privacy ? `training ${formatNumber(r.privacy.training, 3)} plus conformal ${formatNumber(r.privacy.conformal, 3)}` : "",
      r.target ? `target ${formatTarget(r.target, r.kind)}, ${OUTCOME_LABEL[outcome].toLowerCase()}` : "",
      `status ${STATUS_META[r.evidenceStatus].label}. Open details.`,
    ]
      .filter(Boolean)
      .join("; "),
  };
}

/** Generated from the same records as the chart, so the text always matches the filter. */
export function chartSummary(kind: MetricKind, records: MetricRecord[]): string {
  const def = METRIC_DEFINITIONS[kind];
  if (records.length === 0) return `No ${def.name.toLowerCase()} results match the current filters.`;
  const parts = records.map((r) => {
    const ci = r.confidenceInterval ? ` ${formatInterval(r.confidenceInterval, r.decimals)}` : "";
    const name = r.variant ? `${r.dataset} (${r.variant.toLowerCase()})` : r.dataset;
    return `${name} ${formatValue(r)}${ci}, ${STATUS_META[r.evidenceStatus].label.toLowerCase()}`;
  });
  return `${def.name}: ${parts.join("; ")}.`;
}

export function MetricChart({
  kind,
  records,
  showTargets = true,
  showIntervals = true,
  showInterpretation = false,
  onSelect,
  headingLevel = 3,
}: {
  kind: MetricKind;
  records: MetricRecord[];
  showTargets?: boolean;
  showIntervals?: boolean;
  showInterpretation?: boolean;
  onSelect?: (r: MetricRecord, trigger: HTMLElement) => void;
  headingLevel?: 2 | 3;
}) {
  // Never put incompatible units on one axis: utility splits into AUROC and accuracy panels.
  const groups =
    kind === "utility"
      ? (["AUROC points", "accuracy pp"] as const)
          .map((u) => records.filter((r) => r.unit === u))
          .filter((g) => g.length > 0)
      : [records];

  const def = METRIC_DEFINITIONS[kind];
  const columns: TableColumn[] = [
    { key: "dataset", label: "Dataset" },
    { key: "value", label: "Result", numeric: true },
    ...(kind === "privacy"
      ? [
          { key: "training", label: "Training ε", numeric: true },
          { key: "conformal", label: "Conformal ε", numeric: true },
        ]
      : []),
    ...(records.some((r) => r.confidenceInterval) ? [{ key: "ci", label: "95% CI", numeric: true }] : []),
    { key: "target", label: "Target" },
    { key: "status", label: "Evidence status" },
  ];

  return (
    <div className="space-y-5">
      {groups.map((g, i) => {
        const spec = chartSpec(kind, g[0]?.unit);
        const title =
          kind === "utility"
            ? g[0]?.unit === "accuracy pp"
              ? "Utility cost — accuracy points (WEAR)"
              : "Utility cost — AUROC points (clinical corpora)"
            : def.name;
        return (
          <AccessibleChartFrame
            key={i}
            title={title}
            headingLevel={headingLevel}
            summary={chartSummary(kind, g)}
            disclosure={spec.disclosure}
            caveat={spec.caveat}
            persistentLabel={spec.persistentLabel}
            columns={columns}
            rows={g.map((r) => ({
              dataset: `${r.dataset}${r.variant ? ` — ${r.variant}` : ""}`,
              value: formatValue(r),
              training: r.privacy ? formatNumber(r.privacy.training, 3) : "",
              conformal: r.privacy ? formatNumber(r.privacy.conformal, 3) : "",
              ci: r.confidenceInterval ? formatInterval(r.confidenceInterval, r.decimals) : "—",
              target: r.target ? formatTarget(r.target, r.kind) : "—",
              status: STATUS_META[r.evidenceStatus].label,
            }))}
          >
            <RowChart
              rows={g.map(toRow)}
              scale={spec.scale}
              mode={spec.mode}
              references={spec.references}
              showReferences={showTargets}
              showIntervals={showIntervals}
              axisLabel={spec.axisLabel}
              onSelect={
                onSelect
                  ? (key, el) => {
                      const r = g.find((x) => x.id === key);
                      if (r) onSelect(r, el);
                    }
                  : undefined
              }
            />
            {showInterpretation && (
              <ul className="mt-4 space-y-1.5 border-t border-line pt-4 text-sm text-muted">
                {g.map((r) => (
                  <li key={r.id}>
                    <span className="font-medium text-ink">
                      {r.dataset}
                      {r.variant ? ` (${r.variant})` : ""}:
                    </span>{" "}
                    {r.interpretation}
                  </li>
                ))}
              </ul>
            )}
          </AccessibleChartFrame>
        );
      })}
    </div>
  );
}
