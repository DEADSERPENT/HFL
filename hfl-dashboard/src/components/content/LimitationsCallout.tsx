import Link from "next/link";
import { AlertTriangle, Info } from "lucide-react";
import type { ReactNode } from "react";

export function LimitationsCallout({
  title,
  children,
  tone = "unresolved",
  href,
  linkLabel,
}: {
  title: string;
  children: ReactNode;
  tone?: "unresolved" | "scope";
  href?: string;
  linkLabel?: string;
}) {
  const Icon = tone === "unresolved" ? AlertTriangle : Info;
  return (
    <aside
      aria-label={`${tone === "unresolved" ? "Unresolved result" : "Caveat"}: ${title}`}
      className={`flex gap-3 rounded-[var(--radius-md)] border p-4 ${
        tone === "unresolved" ? "border-caution/40 bg-caution/[0.06]" : "border-line bg-surface/60"
      }`}
    >
      <Icon size={18} aria-hidden className={`mt-0.5 shrink-0 ${tone === "unresolved" ? "text-caution" : "text-model"}`} />
      <div className="min-w-0">
        <p className="text-[0.8125rem] font-semibold text-subtle">
          {tone === "unresolved" ? "Unresolved" : "Scope"}
        </p>
        <p className="mt-0.5 font-medium text-ink">{title}</p>
        <div className="mt-1 text-sm leading-relaxed text-muted">{children}</div>
        {href && (
          <Link href={href} className="mt-2 inline-block text-sm font-medium text-accent hover:underline">
            {linkLabel ?? "Read more"}
          </Link>
        )}
      </div>
    </aside>
  );
}
