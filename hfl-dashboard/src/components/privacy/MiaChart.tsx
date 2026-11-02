"use client";

import { MIA_AUDIT } from "@/content/privacy";
import { formatNumber } from "@/lib/format";
import { AccessibleChartFrame } from "@/components/charts/AccessibleChartFrame";
import { RowChart } from "@/components/charts/RowChart";

export function MiaChart() {
  const a = MIA_AUDIT;
  const ci = `[${a.interval.lower.toFixed(3)}, ${a.interval.upper.toFixed(3)}]`;
  return (
    <AccessibleChartFrame
      title="Membership-inference audit (VitalDB)"
      summary={`${a.title}: attack AUC ${a.auc.toFixed(3)} ${ci} against a difficulty floor of ${a.floor.toFixed(3)} (difference ${formatNumber(
        a.margin,
        3,
      )}). An AUC of 0.5 means the attack cannot tell members from non-members better than chance.`}
      disclosure="the AUC axis runs from 0.45 to 0.60, not 0 to 1, so the interval is visible."
      caveat="Close to the floor under this audit protocol. This does not establish zero leakage or resistance to all attacks."
      columns={[
        { key: "arm", label: "Audit arm" },
        { key: "auc", label: "Attack AUC", numeric: true },
        { key: "ci", label: "95% interval", numeric: true },
        { key: "floor", label: "Difficulty floor", numeric: true },
        { key: "margin", label: "Difference from floor", numeric: true },
      ]}
      rows={[{ arm: a.title, auc: a.auc.toFixed(3), ci, floor: a.floor.toFixed(3), margin: formatNumber(a.margin, 3) }]}
    >
      <RowChart
        mode="interval"
        axisLabel="Attack AUC (0.5 = chance)"
        scale={{ min: 0.45, max: 0.6, type: "linear", ticks: [0.45, 0.5, 0.55, 0.6], format: (v) => v.toFixed(2) }}
        references={[
          { value: 0.5, label: "Chance (0.5)", kind: "chance" },
          { value: a.floor, label: `Difficulty floor (${a.floor.toFixed(3)})`, kind: "floor" },
        ]}
        rows={[
          {
            key: a.id,
            label: "Patient-level DP",
            sublabel: "Offline LiRA",
            value: a.auc,
            display: a.auc.toFixed(3),
            status: a.evidenceStatus,
            interval: { lower: a.interval.lower, upper: a.interval.upper, display: ci },
            ariaLabel: `${a.title}: AUC ${a.auc.toFixed(3)}, interval ${ci}, floor ${a.floor.toFixed(3)}`,
          },
        ]}
      />
    </AccessibleChartFrame>
  );
}
