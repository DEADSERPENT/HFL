import Link from "next/link";
import { CircleCheck, CircleHelp, CircleX, Cpu } from "lucide-react";
import { METRICS, METRIC_DEFINITIONS } from "@/content/metrics";
import { formatTarget, formatValue } from "@/lib/format";
import { STATUS_META } from "@/lib/metric-status";
import { DATASETS, type EvidenceStatus, type MetricKind } from "@/lib/types";

const ICON: Partial<Record<EvidenceStatus, { Icon: typeof CircleCheck; cls: string }>> = {
  measured: { Icon: CircleCheck, cls: "text-sage" },
  modelled: { Icon: Cpu, cls: "text-model" },
  inconclusive: { Icon: CircleHelp, cls: "text-caution" },
  "target-not-met": { Icon: CircleX, cls: "text-miss" },
};

/** One line per metric: how it was obtained, and what the row says. */
const ROWS: { kind: MetricKind; setting: string; reading: string }[] = [
  {
    kind: "communication",
    setting: "Measured payload of the deployed update encoding",
    reading: "All three corpora send under a tenth of the centralized baseline's uplink bytes.",
  },
  {
    kind: "round-latency",
    setting: "Simulated at packet level in ns-3",
    reading: "Rounds get shorter everywhere, most where many clients share a medium.",
  },
  {
    kind: "energy",
    setting: "Modelled in CloudSim Plus, not measured on hardware",
    reading: "The model puts the saving far above the 20% target on every corpus.",
  },
  {
    kind: "inference-latency",
    setting: "Measured on a workstation CPU, not edge hardware",
    reading: "Milliseconds against a 100 ms budget; privacy adds no inference cost.",
  },
  {
    kind: "update-delivery",
    setting: "Simulated in ns-3, two edge aggregators",
    reading: "eICU misses the target with 187 hospitals sharing two edges.",
  },
];

/**
 * The homepage evidence snapshot as a single results ledger rather than a
 * wall of cards. Each value is an inset readout linking to its full record.
 */
export function EvidenceLedger() {
  const cell = (r: (typeof METRICS)[number], name: string) => {
    const ic = ICON[r.evidenceStatus];
    return (
      <Link
        href={`/results/?metric=${r.kind}&detail=${r.id}`}
        className="group inline-flex flex-col gap-1.5 rounded-xl focus-visible:outline-offset-4"
        aria-label={`${name}, ${r.dataset}: ${formatValue(r)}, ${STATUS_META[r.evidenceStatus].label}. Open the full result.`}
      >
        <span className="readout text-[1.05rem] text-ink transition-colors group-hover:text-accent">
          {ic ? <ic.Icon size={15} aria-hidden className={ic.cls} /> : null}
          {formatValue(r)}
        </span>
        <span
          className={`text-xs ${
            r.evidenceStatus === "target-not-met" ? "font-semibold text-miss" : r.evidenceStatus === "inconclusive" ? "font-semibold text-caution" : "text-subtle"
          }`}
        >
          {STATUS_META[r.evidenceStatus].label}
        </span>
      </Link>
    );
  };

  return (
    <div>
      {/* Small screens: one block per result, datasets side by side. */}
      <ul className="divide-y divide-line border-y border-line md:hidden">
        {ROWS.map((row) => {
          const def = METRIC_DEFINITIONS[row.kind];
          const recs = DATASETS.map((d) => METRICS.find((m) => m.kind === row.kind && m.dataset === d && m.headline));
          const target = recs.find((r) => r?.target)?.target;
          return (
            <li key={row.kind} className="py-6">
              <Link href={`/results/?metric=${row.kind}`} className="font-semibold text-ink underline-offset-4 hover:text-accent hover:underline">
                {def.name}
              </Link>
              <p className="mt-1 text-sm text-subtle">
                {row.setting}. Target {target ? formatTarget(target, row.kind) : "none"}.
              </p>
              <dl className="mt-4 grid grid-cols-3 gap-3">
                {recs.map((r, i) => (
                  <div key={r?.id ?? i}>
                    <dt className="mb-1.5 text-sm text-subtle">{DATASETS[i]}</dt>
                    <dd>{r ? cell(r, def.name) : <span className="text-subtle">Not evaluated</span>}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-4 text-sm leading-relaxed text-muted">{row.reading}</p>
            </li>
          );
        })}
      </ul>

      <div className="hidden md:block">
        <table className="w-full border-collapse text-left">
          <caption className="sr-only">
            Headline system results by dataset. Each value links to its definition, evaluation setting and caveat.
          </caption>
          <thead>
            <tr className="text-sm text-subtle">
              <th scope="col" className="w-[38%] pb-4 font-medium">
                Result
              </th>
              {DATASETS.map((d) => (
                <th key={d} scope="col" className="pb-4 font-medium">
                  {d}
                </th>
              ))}
              <th scope="col" className="pb-4 font-medium">
                Target
              </th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => {
              const def = METRIC_DEFINITIONS[row.kind];
              const recs = DATASETS.map((d) => METRICS.find((m) => m.kind === row.kind && m.dataset === d && m.headline));
              const target = recs.find((r) => r?.target)?.target;
              return (
                <tr key={row.kind} className="border-t border-line align-top">
                  <th scope="row" className="py-5 pr-6 font-normal">
                    <Link href={`/results/?metric=${row.kind}`} className="font-semibold text-ink underline-offset-4 hover:text-accent hover:underline">
                      {def.name}
                    </Link>
                    <span className="mt-1 block text-sm text-subtle">{row.setting}</span>
                    <span className="mt-2 block max-w-[46ch] text-sm leading-relaxed text-muted">{row.reading}</span>
                  </th>
                  {recs.map((r, i) =>
                    r ? (
                      <td key={r.id} className="py-5 pr-4">
                        {cell(r, def.name)}
                      </td>
                    ) : (
                      <td key={i} className="py-5 text-subtle">
                        Not evaluated
                      </td>
                    ),
                  )}
                  <td className="tnum py-5 text-muted">{target ? formatTarget(target, row.kind) : "None"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-subtle">
        <span className="inline-flex items-center gap-1.5">
          <CircleCheck size={14} aria-hidden className="text-sage" /> Measured
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Cpu size={14} aria-hidden className="text-model" /> Modelled by a simulator
        </span>
        <span className="inline-flex items-center gap-1.5">
          <CircleX size={14} aria-hidden className="text-miss" /> Target not met
        </span>
      </p>
    </div>
  );
}
