import { z } from "zod";
import { DATASETS, EVIDENCE_STATUSES, METRIC_KINDS, type MetricRecord } from "./types";
import { expectedEvidenceStatus, roundTo, targetOutcomeOf } from "./metric-status";
import type { PublicationRecord } from "@/content/publication";

const nonEmpty = z.string().trim().min(1);

/** Words that must never appear in public copy (internal paths, repo metadata). */
export const FORBIDDEN_PUBLIC_PATTERNS: RegExp[] = [
  /github\.com/i,
  /raw\.githubusercontent/i,
  /api\.github/i,
  /\/home\//i,
  /DEADSERPENT/,
  /SIMULATORS\//,
  /\.(py|tex|ipynb|npy|npz|pt|ckpt|log)\b/i,
  /\b[0-9a-f]{40}\b/, // commit hashes
];

export const TargetSchema = z.object({
  operator: z.enum(["<", "<=", ">", ">="]),
  value: z.number().finite(),
  unit: nonEmpty,
});

export const IntervalSchema = z.object({
  lower: z.number().finite(),
  upper: z.number().finite(),
  unit: nonEmpty,
  method: nonEmpty,
});

export const MetricRecordSchema = z
  .object({
    id: z.string().regex(/^[a-z0-9-]+$/),
    kind: z.enum(METRIC_KINDS),
    objective: z.enum(["O1", "O1b", "O2a", "O2b", "O3a", "O3b", "O4"]),
    title: nonEmpty,
    dataset: z.enum(DATASETS),
    variant: nonEmpty.optional(),
    value: z.number().finite(),
    unit: nonEmpty,
    decimals: z.number().int().min(0).max(4),
    target: TargetSchema.optional(),
    basis: z.enum(["measured", "modelled"]),
    evidenceStatus: z.enum(EVIDENCE_STATUSES),
    evaluationContext: nonEmpty,
    baseline: nonEmpty.optional(),
    confidenceInterval: IntervalSchema.optional(),
    interpretation: nonEmpty,
    caveat: nonEmpty,
    publicProvenanceLabel: nonEmpty,
    reviewedAt: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
    privacy: z
      .object({
        training: z.number().positive(),
        conformal: z.number().min(0),
        delta: z.number().positive().lt(1),
        unit: nonEmpty,
      })
      .optional(),
    headline: z.boolean(),
  })
  .superRefine((m, ctx) => {
    const rec = m as MetricRecord;
    const issue = (message: string) => ctx.addIssue({ code: "custom", message: `${m.id}: ${message}` });

    // A confidence interval must be well formed and contain its point estimate.
    if (m.confidenceInterval) {
      const ci = m.confidenceInterval;
      if (!(ci.lower < ci.upper)) issue("interval lower bound must be below upper bound");
      if (m.value < ci.lower || m.value > ci.upper) issue("point estimate lies outside its interval");
      if (ci.unit !== m.unit) issue("interval unit differs from the record unit");
    }
    if (m.target && m.target.unit !== m.unit) issue("target unit differs from the record unit");

    // Status must follow from basis + target outcome. This is what stops an
    // inconclusive or missed result from being published as a success.
    const expected = expectedEvidenceStatus(rec);
    if (m.evidenceStatus !== expected)
      issue(`evidenceStatus is "${m.evidenceStatus}" but the data imply "${expected}"`);

    // Modelled results must say so in their caveat.
    if (m.basis === "modelled" && !/simulat|model/i.test(m.caveat))
      issue("modelled result lacks a modelling caveat");

    // Energy is always a CloudSim Plus estimate.
    if (m.kind === "energy") {
      if (m.basis !== "modelled") issue("energy results must be modelled");
      if (!/CloudSim Plus/.test(m.caveat) || !/not a physical/i.test(m.caveat))
        issue("energy caveat must name CloudSim Plus and state it is not a physical measurement");
    }

    // Privacy totals must equal training + conformal.
    if (m.kind === "privacy") {
      if (!m.privacy) issue("privacy record lacks budget components");
      else if (roundTo(m.privacy.training + m.privacy.conformal, 6) !== roundTo(m.value, 6))
        issue("privacy total does not equal training + conformal");
    } else if (m.privacy) issue("only privacy records may carry budget components");

    // A missed target must never be headed as achieved.
    if (targetOutcomeOf(rec) === "not-met" && /\b(meets|met|achiev)/i.test(m.interpretation) && !/miss|below|not met/i.test(m.interpretation))
      issue("target-not-met result is described as achieved");

    for (const field of [m.title, m.interpretation, m.caveat, m.evaluationContext, m.baseline ?? ""])
      for (const re of FORBIDDEN_PUBLIC_PATTERNS) if (re.test(field)) issue(`public text matches forbidden pattern ${re}`);
  });

export function validateMetrics(records: MetricRecord[]): string[] {
  const errors: string[] = [];
  const seen = new Set<string>();
  for (const r of records) {
    if (seen.has(r.id)) errors.push(`duplicate metric id ${r.id}`);
    seen.add(r.id);
    const res = MetricRecordSchema.safeParse(r);
    if (!res.success) for (const i of res.error.issues) errors.push(i.message);
  }
  return errors;
}

export const PublicationSchema = z
  .object({
    title: nonEmpty,
    status: nonEmpty,
    confirmed: z.boolean(),
    authors: z.array(z.object({ name: nonEmpty, affiliation: nonEmpty })).optional(),
    venue: nonEmpty.optional(),
    doi: z.string().regex(/^10\.\d{4,9}\/\S+$/).optional(),
    date: z.string().regex(/^\d{4}-\d{2}(-\d{2})?$/).optional(),
    keywords: z.array(nonEmpty).min(1),
    publicAbstract: z.array(nonEmpty).min(1),
    dataAccess: nonEmpty,
    codeAvailability: nonEmpty,
    approvedLinks: z.array(z.object({ label: nonEmpty, href: z.string().url() })),
  })
  .superRefine((p, ctx) => {
    if (!p.confirmed) {
      for (const k of ["authors", "venue", "doi", "date"] as const)
        if (p[k] !== undefined)
          ctx.addIssue({ code: "custom", message: `publication.${k} is set but metadata is not confirmed` });
      if (/accepted|published|in press/i.test(p.status))
        ctx.addIssue({ code: "custom", message: "unconfirmed publication must not claim a publication status" });
    }
    for (const l of p.approvedLinks)
      for (const re of FORBIDDEN_PUBLIC_PATTERNS)
        if (re.test(l.href)) ctx.addIssue({ code: "custom", message: `link ${l.href} is not allowed` });
  });

export function validatePublication(p: PublicationRecord): string[] {
  const res = PublicationSchema.safeParse(p);
  return res.success ? [] : res.error.issues.map((i) => i.message);
}
