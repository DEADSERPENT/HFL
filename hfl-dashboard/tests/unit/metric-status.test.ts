import { describe, expect, it } from "vitest";
import { classifyTarget, expectedEvidenceStatus, targetOutcomeOf } from "@/lib/metric-status";
import { METRICS, metricById } from "@/content/metrics";

describe("classifyTarget", () => {
  it("compares point estimates without an interval", () => {
    expect(classifyTarget(90.8, { operator: ">=", value: 50, unit: "%" })).toBe("met");
    expect(classifyTarget(97.83, { operator: ">", value: 99, unit: "%" })).toBe("not-met");
    expect(classifyTarget(100, { operator: ">", value: 99, unit: "%" })).toBe("met");
    expect(classifyTarget(1, { operator: "<=", value: 1, unit: "e" })).toBe("met");
    expect(classifyTarget(5, undefined)).toBe("no-target");
  });

  it("applies the prespecified interval rule", () => {
    const t = { operator: "<=" as const, value: 2, unit: "pts" };
    expect(classifyTarget(-1.18, t, { lower: -1.63, upper: -0.73 })).toBe("met");
    expect(classifyTarget(3.09, t, { lower: 1.37, upper: 4.81 })).toBe("inconclusive");
    expect(classifyTarget(3.91, t, { lower: 2.4, upper: 5.42 })).toBe("not-met");
    expect(classifyTarget(1.97, t, { lower: 1.76, upper: 2.17 })).toBe("inconclusive");
  });
});

describe("curated results keep their required classifications", () => {
  it.each([
    ["utility-vitaldb", "measured"],
    ["utility-wear", "inconclusive"],
    ["utility-eicu-headline", "inconclusive"],
    ["utility-eicu-end-to-end", "target-not-met"],
    ["update-delivery-eicu", "target-not-met"],
    ["energy-vitaldb", "modelled"],
    ["round-latency-eicu", "modelled"],
    ["inference-latency-vitaldb", "measured"],
  ])("%s is %s", (id, status) => {
    const r = metricById(id)!;
    expect(r.evidenceStatus).toBe(status);
    expect(expectedEvidenceStatus(r)).toBe(status);
  });

  it("never labels an inconclusive or missed result as a success", () => {
    for (const r of METRICS) {
      const o = targetOutcomeOf(r);
      if (o === "inconclusive") expect(r.evidenceStatus).toBe("inconclusive");
      if (o === "not-met") expect(r.evidenceStatus).toBe("target-not-met");
    }
  });

  it("keeps the two eICU utility paths separate", () => {
    const eicu = METRICS.filter((m) => m.kind === "utility" && m.dataset === "eICU");
    expect(eicu.map((m) => m.value).sort()).toEqual([3.09, 3.91]);
    expect(new Set(eicu.map((m) => m.variant)).size).toBe(2);
  });
});
