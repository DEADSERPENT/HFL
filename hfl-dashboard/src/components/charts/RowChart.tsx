"use client";

import type { EvidenceStatus } from "@/lib/types";
import { EvidenceStatusLabel } from "@/components/metrics/EvidenceStatusLabel";

export type Scale = {
  min: number;
  max: number;
  type: "linear" | "log";
  ticks: number[];
  format: (v: number) => string;
};

export type ReferenceLine = { value: number; label: string; kind: "target" | "zero" | "floor" | "chance" };

export type ChartRow = {
  key: string;
  label: string;
  sublabel?: string;
  value: number;
  display: string;
  status: EvidenceStatus;
  interval?: { lower: number; upper: number; display: string };
  /** For stacked bars: segments summing to `value`. */
  segments?: { value: number; label: string; tone: "a" | "b" }[];
  ariaLabel: string;
};

export function scalePos(scale: Scale, v: number): number {
  const clamp = (x: number) => Math.max(0, Math.min(1, x));
  if (scale.type === "log") {
    const lv = Math.log10(Math.max(v, scale.min));
    return clamp((lv - Math.log10(scale.min)) / (Math.log10(scale.max) - Math.log10(scale.min)));
  }
  return clamp((v - scale.min) / (scale.max - scale.min));
}

const pct = (x: number) => `${(x * 100).toFixed(3)}%`;

const MARK_TONE: Record<EvidenceStatus, string> = {
  measured: "bg-sage",
  modelled: "bg-model",
  inconclusive: "bg-caution",
  "target-not-met": "bg-miss",
  "not-evaluated": "bg-subtle",
  illustrative: "bg-muted",
};

const REF_STYLE: Record<ReferenceLine["kind"], string> = {
  target: "border-caution/80",
  zero: "border-line-strong",
  floor: "border-accent/80",
  chance: "border-line-strong",
};

/**
 * Horizontal row chart in HTML: bars, dots, point-and-interval or stacked
 * bars on one explicit axis. Every row is a real button with an accessible
 * label, so the chart is usable with keyboard and screen readers.
 */
export function RowChart({
  rows,
  scale,
  mode,
  references = [],
  showReferences = true,
  showIntervals = true,
  onSelect,
  axisLabel,
}: {
  rows: ChartRow[];
  scale: Scale;
  mode: "bar" | "dot" | "interval" | "stack";
  references?: ReferenceLine[];
  showReferences?: boolean;
  showIntervals?: boolean;
  onSelect?: (key: string, trigger: HTMLElement) => void;
  axisLabel: string;
}) {
  const refs = showReferences ? references : references.filter((r) => r.kind === "zero");
  const zeroPos = scalePos(scale, scale.type === "log" ? scale.min : Math.max(scale.min, 0));

  return (
    <div className="chart-animate">
      <ul className="space-y-2">
        {rows.map((r) => {
          const p = scalePos(scale, r.value);
          const Row = onSelect ? "button" : "div";
          return (
            <li key={r.key}>
              <Row
                {...(onSelect
                  ? { type: "button" as const, onClick: (e: React.MouseEvent<HTMLElement>) => onSelect(r.key, e.currentTarget), "aria-label": r.ariaLabel }
                  : { "aria-label": r.ariaLabel, role: "group" })}
                className="group grid w-full grid-cols-1 items-center gap-x-4 gap-y-1.5 rounded-lg px-2 py-2 text-left transition-colors hover:bg-white/70 focus-visible:bg-white/70 sm:grid-cols-[minmax(8rem,13rem)_minmax(0,1fr)_7.5rem]"
              >
                <span className="min-w-0">
                  <span className="block text-sm font-medium text-ink">{r.label}</span>
                  {r.sublabel && <span className="block text-xs text-subtle">{r.sublabel}</span>}
                </span>

                <span aria-hidden className="relative block h-7">
                  {/* track */}
                  <span className="absolute inset-y-[9px] left-0 right-0 rounded-full bg-surface shadow-[var(--clay-inset-sm)]" />
                  {/* reference lines */}
                  {refs.map((ref) => (
                    <span
                      key={ref.label}
                      className={`absolute -top-1 -bottom-1 border-l border-dashed ${REF_STYLE[ref.kind]}`}
                      style={{ left: pct(scalePos(scale, ref.value)) }}
                    />
                  ))}
                  {mode === "bar" && (
                    <span
                      className={`bar-grow absolute inset-y-[8px] rounded-full ${MARK_TONE[r.status]} ${r.status === "modelled" ? "bg-[repeating-linear-gradient(135deg,var(--color-model)_0_6px,#6f88a6_6px_10px)]" : ""}`}
                      style={{ left: pct(zeroPos), width: pct(Math.max(0, p - zeroPos)) }}
                    />
                  )}
                  {mode === "stack" && r.segments && (
                    <span className="bar-grow absolute inset-y-[7px] left-0 flex overflow-hidden rounded-full" style={{ width: pct(p) }}>
                      {r.segments.map((s) => (
                        <span
                          key={s.label}
                          className={s.tone === "a" ? "h-full bg-sage" : "h-full bg-[repeating-linear-gradient(135deg,var(--color-accent)_0_5px,#ffa58c_5px_9px)]"}
                          style={{ width: pct(s.value / r.value) }}
                        />
                      ))}
                    </span>
                  )}
                  {(mode === "interval" || mode === "dot") && showIntervals && r.interval && (
                    <span
                      className="absolute top-1/2 h-[3px] -translate-y-1/2 rounded-full bg-ink/60"
                      style={{
                        left: pct(scalePos(scale, r.interval.lower)),
                        width: pct(scalePos(scale, r.interval.upper) - scalePos(scale, r.interval.lower)),
                      }}
                    >
                      <span className="absolute -top-[5px] left-0 h-[13px] w-[2px] bg-ink/70" />
                      <span className="absolute -top-[5px] right-0 h-[13px] w-[2px] bg-ink/70" />
                    </span>
                  )}
                  {(mode === "interval" || mode === "dot") && (
                    <span
                      className={`absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-bg ${MARK_TONE[r.status]} ${
                        r.status === "target-not-met" ? "rotate-45 rounded-[2px]" : ""
                      } ${r.status === "inconclusive" ? "rounded-[2px]" : ""}`}
                      style={{ left: pct(p) }}
                    />
                  )}
                </span>

                <span className="flex items-center justify-between gap-2 sm:flex-col sm:items-end sm:justify-center sm:gap-1">
                  <span className="tnum text-sm font-semibold text-ink">{r.display}</span>
                  {showIntervals && r.interval && <span className="tnum text-xs text-subtle">{r.interval.display}</span>}
                  <span className="sm:hidden">
                    <EvidenceStatusLabel status={r.status} size="sm" />
                  </span>
                </span>
              </Row>
            </li>
          );
        })}
      </ul>

      {/* axis */}
      <div aria-hidden className="mt-1 grid grid-cols-1 gap-x-4 px-2 sm:grid-cols-[minmax(8rem,13rem)_minmax(0,1fr)_7.5rem]">
        <span className="hidden sm:block" />
        <span className="relative block h-6 border-t border-line">
          {scale.ticks.map((t) => (
            <span
              key={t}
              className="tnum absolute top-1 -translate-x-1/2 text-[0.7rem] text-subtle"
              style={{ left: pct(scalePos(scale, t)) }}
            >
              {scale.format(t)}
            </span>
          ))}
        </span>
      </div>
      <p className="mt-1 px-2 text-xs text-subtle sm:pl-[calc(13rem+1.5rem)]">{axisLabel}</p>

      {refs.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1 px-2 text-xs text-muted">
          {refs.map((ref) => (
            <li key={ref.label} className="flex items-center gap-2">
              <span aria-hidden className={`inline-block h-3 border-l border-dashed ${REF_STYLE[ref.kind]}`} />
              {ref.label}
            </li>
          ))}
          {mode === "stack" && (
            <>
              <li className="flex items-center gap-2">
                <span aria-hidden className="inline-block h-2.5 w-4 rounded-sm bg-sage" /> Training ε
              </li>
              <li className="flex items-center gap-2">
                <span aria-hidden className="inline-block h-2.5 w-4 rounded-sm bg-[repeating-linear-gradient(135deg,var(--color-accent)_0_3px,#ffa58c_3px_6px)]" />{" "}
                Conformal ε
              </li>
            </>
          )}
        </ul>
      )}
    </div>
  );
}
