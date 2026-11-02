export const SITE = {
  name: "PP-HFM Research Observatory",
  wordmark: "PP-HFM",
  descriptor: "Research Observatory",
  title: "Patient-Level Differential Privacy in Hierarchical Federated Learning for Multimodal Medical IoT",
  tagline: "A browser-based exploration of privacy-aware learning across device, edge, and cloud.",
  disclaimer: "Research prototype; not for clinical decision-making.",
  curation:
    "All public figures are curated research summaries; this site does not expose the underlying repository or raw research data.",
} as const;

export type PageMeta = { href: string; title: string; description: string; group: "Research" | "System" | "Evidence" | "Methods" | "About" };

export const PAGES: PageMeta[] = [
  { href: "/", title: "Overview", description: "Learning across the edge, with privacy at the patient level: the PP-HFM research at a glance.", group: "Research" },
  { href: "/research/", title: "Research", description: "The research question, the gap between record- and patient-level privacy, and the claimed contributions.", group: "Research" },
  { href: "/architecture/", title: "Architecture", description: "An interactive device, edge and cloud model of hierarchical federated learning, with a full 2D alternative.", group: "System" },
  { href: "/datasets/", title: "Datasets", description: "The three evaluation corpora, VitalDB, WEAR and eICU, described at a safe aggregate level.", group: "System" },
  { href: "/privacy/", title: "Privacy laboratory", description: "The patient-level mechanism, its accounting boundary, budgets and the membership-inference audit.", group: "Evidence" },
  { href: "/results/", title: "Results", description: "Filter and inspect every curated result with its unit, interval, target, status and caveat.", group: "Evidence" },
  { href: "/experiments/", title: "Experiments", description: "Objectives, baselines, the experiment matrix and how results are reported statistically.", group: "Methods" },
  { href: "/reproducibility/", title: "Reproducibility", description: "Protocol, assumptions, data-access requirements and a reproduction checklist.", group: "Methods" },
  { href: "/limitations/", title: "Limitations", description: "Unresolved targets, simulated results and what the evidence does not show.", group: "Methods" },
  { href: "/publication/", title: "Publication", description: "Research title, status, public abstract and data-access and code policies.", group: "About" },
  { href: "/accessibility/", title: "Accessibility", description: "Accessibility statement and alternatives for every interactive element.", group: "About" },
];

export function pageMeta(href: string): PageMeta {
  const p = PAGES.find((x) => x.href === href);
  if (!p) throw new Error(`No page meta for ${href}`);
  return p;
}

/** Header navigation (spec §6.1) plus an always-visible Limitations link. */
export const NAV = [
  { href: "/research/", label: "Research" },
  { href: "/architecture/", label: "Architecture" },
  { href: "/datasets/", label: "Datasets" },
  { href: "/privacy/", label: "Privacy" },
  { href: "/results/", label: "Results" },
  { href: "/experiments/", label: "Methods", match: ["/experiments/", "/reproducibility/"] },
  { href: "/limitations/", label: "Limitations", caution: true },
] as const;
