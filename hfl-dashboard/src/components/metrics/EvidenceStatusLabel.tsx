import { CircleCheck, CircleDashed, CircleHelp, CircleSlash, CircleX, Cpu } from "lucide-react";
import { STATUS_META } from "@/lib/metric-status";
import type { EvidenceStatus } from "@/lib/types";

/**
 * Each status has a distinct icon, text and outline style, so status is never
 * conveyed by colour alone and the labels never read as interchangeable
 * success badges.
 */
const STYLE: Record<EvidenceStatus, { cls: string; Icon: typeof CircleCheck }> = {
  measured: { cls: "border-sage/50 text-sage bg-sage/[0.06]", Icon: CircleCheck },
  modelled: { cls: "border-model/50 text-model bg-model/[0.06] border-dashed", Icon: Cpu },
  inconclusive: { cls: "border-caution/60 text-caution bg-caution/[0.08]", Icon: CircleHelp },
  "target-not-met": { cls: "border-miss/60 text-miss bg-miss/[0.08]", Icon: CircleX },
  "not-evaluated": { cls: "border-line-strong text-subtle", Icon: CircleSlash },
  illustrative: { cls: "border-line-strong text-muted border-dotted", Icon: CircleDashed },
};

export function EvidenceStatusLabel({
  status,
  size = "md",
  withDescription = false,
}: {
  status: EvidenceStatus;
  size?: "sm" | "md";
  withDescription?: boolean;
}) {
  const meta = STATUS_META[status];
  const { cls, Icon } = STYLE[status];
  return (
    <span className="inline-flex flex-col gap-1">
      <span
        className={`inline-flex w-fit items-center gap-1.5 rounded-full border font-medium ${cls} ${
          size === "sm" ? "px-2 py-0.5 text-[0.72rem]" : "px-2.5 py-1 text-xs"
        }`}
        data-status={status}
      >
        <Icon size={size === "sm" ? 12 : 14} aria-hidden />
        <span>
          <span className="sr-only">Evidence status: </span>
          {meta.label}
        </span>
      </span>
      {withDescription && <span className="text-xs text-subtle">{meta.description}</span>}
    </span>
  );
}

export function StatusLegend() {
  return (
    <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {(Object.keys(STATUS_META) as EvidenceStatus[]).map((s) => (
        <div key={s} className="card p-4">
          <dt>
            <EvidenceStatusLabel status={s} />
          </dt>
          <dd className="mt-2 text-sm text-muted">{STATUS_META[s].description}</dd>
        </div>
      ))}
    </dl>
  );
}
