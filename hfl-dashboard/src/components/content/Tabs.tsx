"use client";

import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";

export type TabItem<T extends string> = { id: T; label: ReactNode };

/**
 * WAI-ARIA tabs with automatic activation: Left/Right (and Up/Down) move and
 * select, Home/End jump to the ends.
 */
export function Tabs<T extends string>({
  items,
  value,
  onChange,
  label,
  children,
  idBase,
}: {
  items: TabItem<T>[];
  value: T;
  onChange: (id: T) => void;
  label: string;
  children: ReactNode;
  idBase?: string;
}) {
  const auto = useId();
  const base = idBase ?? auto;
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const onKey = (e: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const n = items.length;
    let next: number | null = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") next = (index + 1) % n;
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") next = (index - 1 + n) % n;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = n - 1;
    if (next === null) return;
    e.preventDefault();
    const item = items[next];
    if (!item) return;
    onChange(item.id);
    refs.current[next]?.focus();
  };

  return (
    <div>
      <div role="tablist" aria-label={label} className="flex flex-wrap gap-2">
        {items.map((it, i) => {
          const selected = it.id === value;
          return (
            <button
              key={it.id}
              ref={(el) => {
                refs.current[i] = el;
              }}
              role="tab"
              type="button"
              id={`${base}-tab-${it.id}`}
              aria-selected={selected}
              aria-controls={`${base}-panel`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(it.id)}
              onKeyDown={(e) => onKey(e, i)}
              className="chip"
            >
              {it.label}
            </button>
          );
        })}
      </div>
      <div
        role="tabpanel"
        id={`${base}-panel`}
        aria-labelledby={`${base}-tab-${value}`}
        tabIndex={0}
        className="mt-6 rounded-[var(--radius-md)] focus-visible:outline-offset-4"
      >
        {children}
      </div>
    </div>
  );
}
