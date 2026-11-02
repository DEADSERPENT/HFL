"use client";

import { useEffect, useState } from "react";

export function SectionIndex({ sections }: { sections: { id: string; label: string }[] }) {
  const [active, setActive] = useState<string | null>(sections[0]?.id ?? null);

  useEffect(() => {
    const els = sections.map((s) => document.getElementById(s.id)).filter((e): e is HTMLElement => !!e);
    if (!("IntersectionObserver" in window) || els.length === 0) return;
    const obs = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-20% 0px -65% 0px" },
    );
    els.forEach((e) => obs.observe(e));
    return () => obs.disconnect();
  }, [sections]);

  return (
    <nav aria-label="On this page" className="hidden xl:block">
      <div className="sticky top-24 pt-12">
        <p className="text-[0.8125rem] font-semibold text-subtle">On this page</p>
        <ol className="mt-4 space-y-1 border-l border-line">
          {sections.map((s) => (
            <li key={s.id}>
              <a
                href={`#${s.id}`}
                aria-current={active === s.id ? "location" : undefined}
                className={`-ml-px block border-l py-1.5 pl-4 text-sm transition-colors ${
                  active === s.id ? "border-accent text-ink" : "border-transparent text-subtle hover:text-muted"
                }`}
              >
                {s.label}
              </a>
            </li>
          ))}
        </ol>
      </div>
    </nav>
  );
}
