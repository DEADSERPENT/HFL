import { METRICS } from "./metrics";
import { PUBLICATION } from "./publication";
import { validateMetrics, validatePublication } from "@/lib/validation";

/**
 * Imported by the root layout, which is rendered during `next build`. Any
 * content-rule violation therefore fails the build instead of shipping.
 */
export function assertContentValid(): void {
  const errors = [...validateMetrics(METRICS), ...validatePublication(PUBLICATION)];
  if (errors.length) throw new Error(`Curated content failed validation:\n- ${errors.join("\n- ")}`);
}
