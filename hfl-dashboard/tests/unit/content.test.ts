import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { METRICS, METRIC_DEFINITIONS } from "@/content/metrics";
import { PUBLICATION } from "@/content/publication";
import { FORBIDDEN_PUBLIC_PATTERNS, validateMetrics, validatePublication } from "@/lib/validation";
import type { MetricRecord } from "@/lib/types";

const clone = (id: string): MetricRecord => structuredClone(METRICS.find((m) => m.id === id)!);

describe("curated content validation", () => {
  it("all curated metrics pass", () => {
    expect(validateMetrics(METRICS)).toEqual([]);
  });

  it("every metric has status, unit, context, interpretation and caveat", () => {
    for (const m of METRICS) {
      expect(m.evidenceStatus, m.id).toBeTruthy();
      expect(m.unit, m.id).toBeTruthy();
      expect(m.evaluationContext.length, m.id).toBeGreaterThan(10);
      expect(m.interpretation.length, m.id).toBeGreaterThan(10);
      expect(m.caveat.length, m.id).toBeGreaterThan(10);
      expect(METRIC_DEFINITIONS[m.kind]).toBeDefined();
    }
  });

  it("fails an inconclusive result labelled as measured", () => {
    const r = clone("utility-eicu-headline");
    r.evidenceStatus = "measured";
    expect(validateMetrics([r]).join()).toMatch(/imply "inconclusive"/);
  });

  it("fails a missed target labelled as met", () => {
    const r = clone("update-delivery-eicu");
    r.evidenceStatus = "modelled";
    expect(validateMetrics([r]).join()).toMatch(/target-not-met/);
  });

  it("fails a modelled result without a modelling caveat", () => {
    const r = clone("round-latency-wear");
    r.caveat = "Looks fine.";
    expect(validateMetrics([r]).join()).toMatch(/modelling caveat/);
  });

  it("fails an energy result without the CloudSim Plus caveat", () => {
    const r = clone("energy-eicu");
    r.caveat = "A simulation estimate.";
    expect(validateMetrics([r]).join()).toMatch(/CloudSim Plus/);
  });

  it("fails malformed confidence intervals", () => {
    const r = clone("utility-vitaldb");
    r.confidenceInterval = { ...r.confidenceInterval!, lower: 1, upper: 0 };
    expect(validateMetrics([r]).length).toBeGreaterThan(0);
  });

  it("fails privacy totals that do not add up", () => {
    const r = clone("privacy-wear");
    r.value = 1.0;
    expect(validateMetrics([r]).join()).toMatch(/training \+ conformal/);
  });

  it("privacy totals match the published values", () => {
    const t = (id: string) => METRICS.find((m) => m.id === id)!;
    expect(t("privacy-vitaldb").privacy!.training + t("privacy-vitaldb").privacy!.conformal).toBeCloseTo(1.0, 9);
    expect(t("privacy-wear").privacy!.training + t("privacy-wear").privacy!.conformal).toBeCloseTo(0.966, 9);
    expect(t("privacy-eicu").privacy!.training + t("privacy-eicu").privacy!.conformal).toBeCloseTo(1.0, 9);
  });

  it("publication metadata contains no unverified citation fields", () => {
    expect(validatePublication(PUBLICATION)).toEqual([]);
    expect(validatePublication({ ...PUBLICATION, doi: "10.1234/fake" }).join()).toMatch(/not confirmed/);
    expect(validatePublication({ ...PUBLICATION, status: "Accepted" }).join()).toMatch(/publication status/);
  });
});

describe("public assets", () => {
  const pub = path.resolve(__dirname, "../../public");
  const walk = (d: string): string[] =>
    fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]));

  it("contains no restricted artefacts", () => {
    for (const f of walk(pub)) {
      expect(f).not.toMatch(/\.(py|tex|ipynb|npy|npz|pt|ckpt|log|csv|parquet|pkl|env)$/i);
      if (/\.(svg|txt|json|html)$/.test(f)) {
        const text = fs.readFileSync(f, "utf8");
        for (const re of FORBIDDEN_PUBLIC_PATTERNS) expect(re.test(text), `${f} ${re}`).toBe(false);
      }
    }
  });

  it("source never calls GitHub or raw repository URLs", () => {
    const src = path.resolve(__dirname, "../../src");
    for (const f of walk(src)) {
      if (f.endsWith("validation.ts")) continue;
      const text = fs.readFileSync(f, "utf8");
      expect(/api\.github|raw\.githubusercontent|github\.com/i.test(text), f).toBe(false);
    }
  });
});
