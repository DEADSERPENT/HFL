"use client";

import { useRef } from "react";
import { DATASETS, type DatasetId } from "@/lib/types";

/** Keyboard-accessible radio group: arrow keys move the selection. */
export function DatasetSelector({
  value,
  onChange,
  label,
  includeAll = false,
}: {
  value: DatasetId | "all";
  onChange: (d: DatasetId | "all") => void;
  label: string;
  includeAll?: boolean;
}) {
  const options: (DatasetId | "all")[] = includeAll ? ["all", ...DATASETS] : [...DATASETS];
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const onKey = (e: React.KeyboardEvent, i: number) => {
    let n: number | null = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") n = (i + 1) % options.length;
    if (e.key === "ArrowLeft" || e.key === "ArrowUp") n = (i - 1 + options.length) % options.length;
    if (n === null) return;
    e.preventDefault();
    onChange(options[n]!);
    refs.current[n]?.focus();
  };
  return (
    <div role="radiogroup" aria-label={label} className="flex flex-wrap gap-1.5">
      {options.map((o, i) => (
        <button
          key={o}
          ref={(el) => {
            refs.current[i] = el;
          }}
          type="button"
          role="radio"
          aria-checked={value === o}
          tabIndex={value === o ? 0 : -1}
          className="chip"
          onClick={() => onChange(o)}
          onKeyDown={(e) => onKey(e, i)}
        >
          {o === "all" ? "All" : o}
        </button>
      ))}
    </div>
  );
}
