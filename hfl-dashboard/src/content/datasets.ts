import type { DatasetId } from "@/lib/types";

/**
 * Aggregate, public-safe dataset descriptions. No records, samples, per-hospital
 * counts or cohort breakdowns. Client counts are the number of federated
 * clients in the evaluated configuration, as stated in the manuscript.
 */
export type DatasetRecord = {
  id: DatasetId;
  name: string;
  tagline: string;
  role: string;
  clinical: boolean;
  modality: string[];
  task: string;
  clients: string;
  partitioning: string;
  privacyUnit: string;
  access: string;
  accessKind: "public" | "credentialed";
  limitations: string[];
};

export const DATASETS: DatasetRecord[] = [
  {
    id: "VitalDB",
    name: "VitalDB",
    tagline: "Surgical vital signs with preoperative context",
    role: "Primary clinical corpus. Clients hold many individuals, the regime in which patient-level privacy differs most from record-level privacy.",
    clinical: true,
    modality: [
      "Time series: ten minutes of nine intraoperative vital-sign trends at 0.5 Hz, with indicators of whether each trend was recorded.",
      "Static: a preoperative vector of clinical and laboratory variables.",
    ],
    task: "Prediction of postoperative intensive-care admission after non-cardiac surgery.",
    clients:
      "Nine clients, one per surgical specialty. They differ naturally in size and outcome rate, because of how care is organized rather than an imposed skew.",
    partitioning:
      "Person-level partition for the privacy and utility results: every person appears in exactly one split and one client. Some system results use an earlier case-level partition and are labelled as such in the manuscript.",
    privacyUnit: "Person (all surgical cases of one person).",
    access:
      "A publicly available research database. Use is governed by the provider's data-use terms; this website does not provide or grant access to any data.",
    accessKind: "public",
    limitations: [
      "The headline encoders are pretrained on pooled client training data, so the guarantee covers the training transcript, not the full pipeline.",
      "A single-centre surgical population; results may not generalize to other institutions.",
    ],
  },
  {
    id: "WEAR",
    name: "WEAR",
    tagline: "Wearable inertial sensing with egocentric video features",
    role: "A non-clinical wearable IoT workload. It tests the system objectives outside medicine; its privacy results are record-level.",
    clinical: false,
    modality: [
      "Body-worn inertial sensing.",
      "Egocentric video features, synchronized with the inertial stream in hardware.",
    ],
    task: "Human activity recognition.",
    clients: "Twenty-two clients, each one participant.",
    partitioning: "Splits are made by individual.",
    privacyUnit: "Record. Each client holds one individual, so the evaluation is record-level.",
    access:
      "A publicly released research dataset. Use is governed by its provider's terms; this website does not provide or grant access to any data.",
    accessKind: "public",
    limitations: [
      "Not a medical dataset; it does not support any clinical claim.",
      "Record-level privacy results are not comparable one-to-one with the patient-level results.",
    ],
  },
  {
    id: "eICU",
    name: "eICU",
    tagline: "Multi-centre intensive-care data, hospitals as clients",
    role: "External clinical corpus and the strictest test. It is the only configuration in which the guarantee is shown to hold end to end.",
    clinical: true,
    modality: [
      "Time series: the first 24 hours after unit admission in 60-minute windows of six vital signs and six observation indicators.",
      "Static: age, sex, admission weight and height, and the APACHE severity score.",
    ],
    task: "Prediction of in-unit mortality at hour 24. Individuals who die within the first 24 hours are excluded, so the inputs are available at prediction time.",
    clients:
      "187 hospital clients. Hospitals too small to train on, or without a positive outcome, are pooled into combined clients.",
    partitioning:
      "Splits are made by individual. Each hospital is a client; 2.9% of training individuals have stays at more than one hospital, which affects their privacy accounting (see the privacy laboratory).",
    privacyUnit: "Patient (all records of one patient).",
    access:
      "Credentialed data distributed through PhysioNet under a data-use agreement. No records, extracts or per-hospital statistics are shown here, and this website does not grant access.",
    accessKind: "credentialed",
    limitations: [
      "The headline utility cost (3.09 AUROC points) is inconclusive against the two-point target; the end-to-end cost (3.91 points) misses it.",
      "Update delivery at two edge aggregators (97.83%) is below the >99% target.",
      "The \u03B5 = 0.9 training budget applies to individuals at one hospital; for the 2.9% at several hospitals the composed bound is up to \u03B5 \u2264 2.08.",
      "The APACHE score is a clinician-computed summary, not an independent sensor stream.",
    ],
  },
];

export function datasetById(id: DatasetId): DatasetRecord {
  const d = DATASETS.find((x) => x.id === id);
  if (!d) throw new Error(`Unknown dataset ${id}`);
  return d;
}
