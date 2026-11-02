import { describe, expect, it } from "vitest";
import { formatDelta, formatInterval, formatNumber, formatTarget, formatValue } from "@/lib/format";
import { describeFilters, filterMetrics } from "@/lib/filters";
import { toCsv, toJson, EXPORT_COLUMNS } from "@/lib/export";
import { METRICS, metricById } from "@/content/metrics";

describe("format", () => {
  it("uses a true minus sign and fixed decimals", () => {
    expect(formatNumber(-1.18, 2)).toBe("−1.18");
    expect(formatNumber(-0.0001, 2)).toBe("0.00");
    expect(formatNumber(2.3, 2)).toBe("2.30");
  });
  it("formats values, intervals, targets and delta", () => {
    expect(formatValue(metricById("communication-vitaldb")!)).toBe("90.8%");
    expect(formatValue(metricById("inference-latency-vitaldb")!)).toBe("2.30 ms");
    expect(formatValue(metricById("update-delivery-vitaldb")!)).toBe("100.00%");
    expect(formatValue(metricById("privacy-wear")!)).toBe("ε = 0.966");
    expect(formatInterval(metricById("utility-vitaldb")!.confidenceInterval!, 2)).toBe("[−1.63, −0.73]");
    expect(formatTarget({ operator: ">=", value: 50, unit: "%" })).toBe("≥ 50%");
    expect(formatDelta(1e-5)).toBe("10⁻⁵");
  });
});

describe("filters", () => {
  it("filters by dataset, metric and status", () => {
    expect(filterMetrics(METRICS, { dataset: "eICU", metric: "all", statuses: [] }).every((m) => m.dataset === "eICU")).toBe(true);
    expect(filterMetrics(METRICS, { dataset: "all", metric: "energy", statuses: [] })).toHaveLength(3);
    const missed = filterMetrics(METRICS, { dataset: "all", metric: "all", statuses: ["target-not-met"] });
    expect(missed.map((m) => m.id).sort()).toEqual(["update-delivery-eicu", "utility-eicu-end-to-end"]);
    expect(describeFilters({ dataset: "WEAR", metric: "all", statuses: [] }, 7)).toBe("Showing 7 results for all metrics, WEAR.");
  });
});

describe("export", () => {
  it("contains only the approved summary columns, with caveats", () => {
    const energy = METRICS.filter((m) => m.kind === "energy");
    const csv = toCsv(energy);
    expect(csv.split("\n")[0]).toBe(EXPORT_COLUMNS.join(","));
    expect(csv).toMatch(/CloudSim Plus simulation; not a physical hardware energy measurement/);
    const json = JSON.parse(toJson(energy));
    expect(Object.keys(json.results[0]).sort()).toEqual([...EXPORT_COLUMNS].sort());
    expect(json.results).toHaveLength(3);
  });
});
