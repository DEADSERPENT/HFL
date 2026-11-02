import Link from "next/link";
import { PAGES, SITE } from "@/content/site";

const GROUPS = ["Research", "System", "Evidence", "Methods", "About"] as const;

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-line bg-bg-elevated/60">
      <div className="container-site grid gap-10 py-14 md:grid-cols-[1.3fr_2fr]">
        <div>
          <p className="font-display text-2xl text-ink">{SITE.wordmark}</p>
          <p className="mt-1 text-sm text-subtle">{SITE.descriptor}</p>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted">{SITE.title}</p>
          <p className="mt-6 inline-flex items-start gap-2 rounded-md border border-caution/30 bg-caution/5 px-3 py-2 text-sm text-caution">
            <span aria-hidden>!</span>
            <span>{SITE.disclaimer}</span>
          </p>
        </div>
        <nav aria-label="Footer" className="grid grid-cols-2 gap-8 sm:grid-cols-3 lg:grid-cols-5">
          {GROUPS.map((g) => (
            <div key={g}>
              <p className="text-[0.8125rem] font-semibold text-subtle">{g}</p>
              <ul className="mt-3 space-y-2 text-sm">
                {PAGES.filter((p) => p.group === g).map((p) => (
                  <li key={p.href}>
                    <Link href={p.href} className="text-muted hover:text-ink">
                      {p.title}
                    </Link>
                  </li>
                ))}
                {g === "About" && (
                  <li>
                    <Link href="/publication/#data-and-privacy" className="text-muted hover:text-ink">
                      Data and privacy statement
                    </Link>
                  </li>
                )}
              </ul>
            </div>
          ))}
        </nav>
      </div>
      <div className="border-t border-line">
        <p className="container-site py-6 text-xs leading-relaxed text-subtle">{SITE.curation}</p>
      </div>
    </footer>
  );
}
