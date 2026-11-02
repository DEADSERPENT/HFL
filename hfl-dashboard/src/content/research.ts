export const RESEARCH = {
  problem:
    "Federated learning keeps medical data at the institution that holds it, and a hierarchy of edge aggregators makes it cheaper to run across many devices and sites. Differential privacy is the usual way to bound what the shared updates reveal. But most federated privacy guarantees protect a single record, while a hospital holds many records per patient. A record-level guarantee can leave a patient with many records far less protected than the stated budget suggests.",
  whyHierarchy:
    "In a device → edge → cloud hierarchy, clients send updates to a nearby edge aggregator that averages them over several rounds before reporting to the cloud. Fewer, smaller messages cross the expensive uplink, rounds get shorter and devices spend less energy. With one edge round per cloud round the design collapses to ordinary single-tier federated averaging.",
  patientVsRecord:
    "Record-level privacy hides whether one row was used. Patient-level privacy hides whether any of a patient's rows were used. The two coincide when each patient has one record, and diverge as records per patient grow: in the evaluation, the utility cost of moving from the record to the patient grows with the number of records per patient.",
  multimodal:
    "Medical IoT data arrives as several streams at once: high-rate physiological time series alongside static clinical context. Each stream needs its own encoder, the streams must be fused, and privacy must be applied at a point where the gradient accounting stays valid. PP-HFM freezes pretrained encoders and privatizes only the compact fusion head.",
  questions: [
    "How can hierarchical device–edge–cloud coordination reduce communication overhead?",
    "What utility costs arise when enforcing patient-level differential privacy under the stated accounting method?",
    "How do latency, update delivery and modelled energy consumption behave across the evaluated datasets and topologies?",
    "How do privacy-audit outcomes vary across the evaluated comparison methods?",
  ],
  contributions: [
    {
      title: "A hierarchical FL design for multimodal medical IoT",
      body: "Clients train a fusion head over frozen, pretrained encoders; edges and the cloud average sparsified, quantized updates.",
    },
    {
      title: "A patient-level privacy mechanism and accounting protocol",
      body: "Per-patient gradient grouping and clipping, per-client noise calibration from each client's population, and accounting of every hierarchical release, evaluated under stated assumptions.",
    },
    {
      title: "A cross-dataset evaluation",
      body: "Communication, round latency, inference latency, update delivery, modelled energy and utility on two clinical corpora and one wearable corpus.",
    },
    {
      title: "A bounded membership-inference audit",
      body: "A patient-adapted likelihood-ratio attack with a positive control and explicit uncertainty, scoped to one corpus and one attack family.",
    },
    {
      title: "A reproducibility-oriented presentation",
      body: "Every result is reported with its interval, evaluation path and limitations, including the targets that were not met.",
    },
  ],
  notClaimed: [
    "No claim of zero privacy leakage.",
    "No claim of clinical deployment readiness.",
    "No claim that simulator outputs equal real-device measurements.",
    "No claim that all targets are met across all datasets.",
    "No claim that results generalize to every institution, device or patient population.",
  ],
  scope: [
    "Three corpora: VitalDB and eICU (clinical) and WEAR (wearable, non-clinical).",
    "Network behaviour simulated in ns-3; energy modelled in CloudSim Plus; inference timed on a workstation CPU.",
    "Two edge aggregators in the headline configuration; an edge-count sensitivity test on eICU.",
    "Five paired seeds for headline comparisons; three for parameter grids.",
  ],
};

export const RESEARCH_QUESTION_CARDS = [
  {
    title: "Communication",
    body: "Reduce uplink traffic by compressing updates and coordinating at the edge.",
  },
  {
    title: "Privacy",
    body: "Apply patient-level privacy accounting and evaluate the utility it costs.",
  },
  {
    title: "Deployment constraints",
    body: "Study latency, energy and update delivery in a hierarchical simulation and evaluation setting.",
  },
];
