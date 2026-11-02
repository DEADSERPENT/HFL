import { PAGES } from "./site";
import { METRICS, METRIC_DEFINITIONS } from "./metrics";
import { LIMITATIONS } from "./limitations";
import { DATASETS } from "./datasets";
import { formatValue } from "@/lib/format";

/** Search runs only over this curated, in-bundle index of public site content. */
export type SearchEntry = { title: string; href: string; text: string; section: string };

export const SEARCH_INDEX: SearchEntry[] = [
  ...PAGES.map((p) => ({ title: p.title, href: p.href, text: p.description, section: "Page" })),
  ...METRICS.map((m) => ({
    title: `${METRIC_DEFINITIONS[m.kind].name} — ${m.dataset}${m.variant ? ` (${m.variant})` : ""}`,
    href: `/results/?detail=${m.id}`,
    text: `${formatValue(m)}. ${m.interpretation} ${m.caveat}`,
    section: "Result",
  })),
  ...LIMITATIONS.map((l) => ({ title: l.title, href: `/limitations/#${l.id}`, text: l.body, section: "Limitation" })),
  ...DATASETS.map((d) => ({ title: d.name, href: `/datasets/?dataset=${d.id}`, text: `${d.tagline}. ${d.role} ${d.task}`, section: "Dataset" })),
];

export function searchContent(query: string, limit = 8): SearchEntry[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (terms.length === 0) return [];
  return SEARCH_INDEX.map((e) => {
    const title = e.title.toLowerCase();
    const body = e.text.toLowerCase();
    let score = 0;
    for (const t of terms) {
      if (title.includes(t)) score += 3;
      else if (body.includes(t)) score += 1;
      else return { e, score: -1 };
    }
    return { e, score };
  })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((x) => x.e);
}
