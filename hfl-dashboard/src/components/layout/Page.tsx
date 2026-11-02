import type { ReactNode } from "react";
import { SectionIndex } from "./SectionIndex";

export function PageHeader({
  eyebrow,
  title,
  lead,
  children,
}: {
  eyebrow: string;
  title: ReactNode;
  lead?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="relative overflow-hidden border-b border-line">
      <div className="container-site relative pb-14 pt-16 md:pb-20 md:pt-24">
        <p className="eyebrow hero-in">{eyebrow}</p>
        <h1 className="font-display hero-in t-72 mt-4 max-w-[20ch] text-ink">{title}</h1>
        {lead && <div className="hero-in t-21 mt-6 max-w-[58ch] font-normal text-muted">{lead}</div>}
        {children && <div className="mt-8">{children}</div>}
      </div>
    </div>
  );
}

export function Section({
  id,
  title,
  eyebrow,
  intro,
  children,
  className = "",
}: {
  id: string;
  title: string;
  eyebrow?: string;
  intro?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className={`scroll-mt-24 py-14 md:py-16 ${className}`}>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2 id={`${id}-title`} className="font-display t-36 mt-2 max-w-[28ch] text-ink">
        {title}
      </h2>
      {intro && <div className="prose-site mt-4 text-[1.05rem]">{intro}</div>}
      {children && <div className="mt-8">{children}</div>}
    </section>
  );
}

/** Long-form layout with an optional sticky section index on wide screens. */
export function LongformLayout({
  sections,
  children,
}: {
  sections: { id: string; label: string }[];
  children: ReactNode;
}) {
  return (
    <div className="container-site grid grid-cols-[minmax(0,1fr)] gap-10 xl:grid-cols-[220px_minmax(0,1fr)]">
      <SectionIndex sections={sections} />
      <div className="min-w-0 divide-y divide-line">{children}</div>
    </div>
  );
}
