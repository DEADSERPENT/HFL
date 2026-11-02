"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { GUIDED_STEPS, LAYERS } from "@/content/architecture";
import { EvidenceStatusLabel } from "@/components/metrics/EvidenceStatusLabel";

export function GuidedStepPanel({ index, onChange, onExit }: { index: number; onChange: (i: number) => void; onExit: () => void }) {
  const step = GUIDED_STEPS[index]!;
  const layer = LAYERS.find((l) => l.id === step.layer)!;
  return (
    <section aria-label="Guided story" className="clay p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="eyebrow">
          Step {index + 1} of {GUIDED_STEPS.length}
        </p>
        <button type="button" className="text-sm text-muted underline-offset-2 hover:text-ink hover:underline" onClick={onExit}>
          Exit story
        </button>
      </div>
      <div aria-live="polite">
        <h3 className="mt-2 text-xl font-medium text-ink">{step.title}</h3>
        <p className="mt-1 text-xs text-subtle">Current layer: {layer.name}</p>
        <p className="mt-3 text-[0.95rem] leading-relaxed text-muted">{step.body}</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <EvidenceStatusLabel status={step.evidenceStatus} size="sm" />
          <span className="text-xs text-subtle">{step.evidenceNote}</span>
        </div>
        {step.notMeaning && (
          <p className="mt-4 rounded-md border border-caution/30 bg-caution/5 px-3 py-2 text-sm text-caution">
            <span className="font-semibold">What this does not mean: </span>
            {step.notMeaning}
          </p>
        )}
      </div>
      <div className="mt-5 flex items-center justify-between gap-2">
        <button type="button" className="btn btn-ghost btn-sm" disabled={index === 0} onClick={() => onChange(index - 1)} aria-label="Previous step">
          <ChevronLeft size={15} aria-hidden /> Back
        </button>
        <ol className="flex gap-1.5" aria-label="Steps">
          {GUIDED_STEPS.map((s, i) => (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => onChange(i)}
                aria-label={`Step ${i + 1}: ${s.title}`}
                aria-current={i === index ? "step" : undefined}
                className={`block h-2.5 w-2.5 rounded-full ${i === index ? "bg-accent" : "bg-line-strong hover:bg-muted"}`}
              />
            </li>
          ))}
        </ol>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={index === GUIDED_STEPS.length - 1}
          onClick={() => onChange(index + 1)}
          aria-label="Next step"
        >
          Next <ChevronRight size={15} aria-hidden />
        </button>
      </div>
    </section>
  );
}
