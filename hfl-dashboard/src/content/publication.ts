/**
 * Publication metadata.
 *
 * Bibliographic fields (authors, venue, DOI, date) stay empty until the final
 * metadata and publication status are confirmed. Content validation fails the
 * build if any of them is set while `confirmed` is false.
 */
export type PublicationRecord = {
  title: string;
  status: string;
  confirmed: boolean;
  authors?: { name: string; affiliation: string }[];
  venue?: string;
  doi?: string;
  date?: string;
  keywords: string[];
  publicAbstract: string[];
  dataAccess: string;
  codeAvailability: string;
  approvedLinks: { label: string; href: string }[];
};

export const PUBLICATION: PublicationRecord = {
  title:
    "Patient-Level Differential Privacy in Hierarchical Federated Learning for Multimodal Medical IoT",
  status: "Manuscript / research project",
  confirmed: false,
  keywords: [
    "Federated learning",
    "Hierarchical aggregation",
    "Differential privacy",
    "Patient-level privacy",
    "Medical Internet of Things",
    "Multimodal fusion",
    "Membership inference",
  ],
  publicAbstract: [
    "Hospitals and medical devices hold data that cannot simply be pooled. Federated learning lets them train a shared model while the data stays where it is, and a hierarchy of edge servers makes that cheaper in bandwidth and energy. Differential privacy then bounds how much the shared updates can reveal.",
    "Most such guarantees protect a single record. A patient, however, often contributes many records, and a record-level budget can understate how exposed that patient is. PP-HFM moves the unit of protection to the patient: each site groups and clips each patient's contribution, sets its noise level from its own population, and accounts for every message that crosses the hierarchy.",
    "On two clinical datasets and one wearable dataset, the design cut uplink traffic by roughly 91–96% and modelled energy per round by roughly 72–80%, with millisecond-scale inference on a workstation CPU. The privacy cost depends on the data: on one surgical dataset the private model was as accurate as the non-private one, while on a large multi-hospital intensive-care dataset the cost was about three AUROC points, inconclusive or missed against the two-point target depending on the evaluation path. On the wearable dataset, protected per record, the loss was just under two accuracy points, but its uncertainty interval spans the target. One reliability target, update delivery on the intensive-care dataset at two edge servers, was also missed. These results come from simulation and offline evaluation, not from a clinical deployment.",
  ],
  dataAccess:
    "The clinical datasets are governed by their providers' terms; eICU is credentialed data available only under a data-use agreement. This website contains no records, samples or per-hospital statistics and does not grant access to any dataset.",
  codeAvailability:
    "No public code release has been approved. This website does not link to, mirror or expose the research codebase. Any future release will be linked here only after a separate release review.",
  approvedLinks: [],
};
