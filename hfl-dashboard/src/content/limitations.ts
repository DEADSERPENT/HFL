export type Limitation = {
  id: string;
  title: string;
  body: string;
  severity: "unresolved" | "scope";
  relatedMetric?: string;
};

export const LIMITATIONS: Limitation[] = [
  {
    id: "eicu-utility-headline",
    title: "eICU headline utility cost is inconclusive",
    body: "3.09 AUROC points with interval [1.37, 4.81]. The interval spans the two-point target, so it is inconclusive under the prespecified rule; the point estimate exceeds the target.",
    severity: "unresolved",
    relatedMetric: "utility-eicu-headline",
  },
  {
    id: "eicu-utility-e2e",
    title: "eICU end-to-end utility cost misses the target",
    body: "3.91 AUROC points with interval [2.40, 5.42]. The whole interval lies above the two-point target: a clear miss for the only configuration whose guarantee holds end to end.",
    severity: "unresolved",
    relatedMetric: "utility-eicu-end-to-end",
  },
  {
    id: "eicu-delivery",
    title: "eICU update delivery is below target at two edges",
    body: "97.83% at the reported two-edge configuration, against a >99% target. A separate sensitivity test reaches the target with more edges, but that is a different configuration.",
    severity: "unresolved",
    relatedMetric: "update-delivery-eicu",
  },
  {
    id: "eicu-multi-hospital",
    title: "The eICU privacy budget is not uniform",
    body: "\u03B5 = 0.9 (training) holds for individuals whose records lie at one hospital. For the 2.9% of training individuals with stays at two to four hospitals, the hospitals' mechanisms compose and the bound rises to \u03B5 \u2264 1.42, 1.77 or 2.08. Utility results are unaffected.",
    severity: "unresolved",
    relatedMetric: "privacy-eicu",
  },
  {
    id: "wear-utility",
    title: "WEAR utility cost is unresolved",
    body: "1.97 accuracy points with interval [1.76, 2.17]. The point estimate is under two points but the interval spans the target. The WEAR guarantee is record-level.",
    severity: "unresolved",
    relatedMetric: "utility-wear",
  },
  {
    id: "energy-modelled",
    title: "Energy savings are simulator estimates",
    body: "All energy figures come from a CloudSim Plus model, not from physical energy measurements on devices, edges or servers.",
    severity: "scope",
    relatedMetric: "energy-vitaldb",
  },
  {
    id: "network-simulated",
    title: "Network results are simulated",
    body: "Round latency and update delivery come from a packet-level ns-3 simulation, not from a deployed network.",
    severity: "scope",
  },
  {
    id: "audit-scope",
    title: "An audit near its floor is not proof of zero leakage",
    body: "A membership-inference AUC close to the reference value says this attack, on this model and data, did no better than its floor. It does not prove universal attack resistance.",
    severity: "scope",
  },
  {
    id: "end-to-end",
    title: "Most guarantees cover the training transcript only",
    body: "In the headline runs, standardization constants are fitted on the training cohort and, on VitalDB and WEAR, the encoders are pretrained on client data. Only the eICU rerun with disjoint encoders and pool-fitted constants holds end to end.",
    severity: "scope",
  },
  {
    id: "latency-sla",
    title: "Inference latency is not a deployment SLA",
    body: "P95 latency was timed on a workstation CPU. It does not establish latency on edge or medical-device hardware, or a clinical service level.",
    severity: "scope",
  },
  {
    id: "protocol-bound",
    title: "Results are tied to the stated protocol",
    body: "Every number depends on the stated datasets, partitions, model choices, privacy mechanism and evaluation protocol.",
    severity: "scope",
  },
  {
    id: "clinical",
    title: "Clinical validity is not established",
    body: "Clinical usefulness, generalization, regulatory readiness and operational safety require separate evaluation. This is a research prototype, not a clinical tool.",
    severity: "scope",
  },
  {
    id: "visual",
    title: "The 3D architecture is explanatory",
    body: "The animated scenes on this site are conceptual models. They are not live telemetry and their node counts are schematic.",
    severity: "scope",
  },
];
