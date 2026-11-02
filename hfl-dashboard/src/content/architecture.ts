import type { EvidenceStatus } from "@/lib/types";

export type LayerId = "device" | "edge" | "cloud";

export const LAYERS: { id: LayerId; name: string; summary: string; detail: string }[] = [
  {
    id: "device",
    name: "Device layer",
    summary: "Local data processing and client-side model updates.",
    detail:
      "Each client (a hospital, specialty or wearable participant) keeps its records local, encodes each modality with a frozen pretrained encoder, and trains only the fusion head under patient-level differential privacy.",
  },
  {
    id: "edge",
    name: "Edge layer",
    summary: "Local coordination, update reduction and regional aggregation.",
    detail:
      "Each edge aggregator serves a group of clients. It averages their compressed, already-noised updates with public weights for several edge rounds before reporting upward.",
  },
  {
    id: "cloud",
    name: "Cloud layer",
    summary: "Higher-level aggregation, global coordination and evaluation.",
    detail:
      "The cloud averages the edge models with public weights and broadcasts the global model back down the hierarchy.",
  },
];

export type GuidedStep = {
  id: string;
  title: string;
  layer: LayerId;
  body: string;
  evidenceStatus: EvidenceStatus;
  evidenceNote: string;
  notMeaning?: string;
  highlight: { privacy?: boolean; compression?: boolean; edgeAggregation?: boolean; direction?: "up" | "down" };
};

export const GUIDED_STEPS: GuidedStep[] = [
  {
    id: "local",
    title: "Local computation",
    layer: "device",
    body: "Records never leave the client. Two frozen encoders turn the time series and the static context into embeddings; only the compact fusion head is trained.",
    evidenceStatus: "illustrative",
    evidenceNote: "Conceptual view of the method.",
    notMeaning: "Node counts are schematic; they are not patients or physical devices.",
    highlight: {},
  },
  {
    id: "privacy",
    title: "Privacy mechanism",
    layer: "device",
    body: "Inside the client, each patient's gradients are summed, clipped to norm 1 and noised with a client-specific multiplier. The privacy boundary sits here: everything that leaves the client is already privatized.",
    evidenceStatus: "illustrative",
    evidenceNote: "The bound is an accounting result; see the privacy laboratory.",
    notMeaning:
      "The boundary does not cover metadata, preprocessing fitted on training data, or deployment operations.",
    highlight: { privacy: true },
  },
  {
    id: "compression",
    title: "Update reduction",
    layer: "device",
    body: "Each update keeps its 20% largest-magnitude coordinates, quantized to 8 bits, with the suppressed residual carried into the next round. This acts on the already-noised update, so it is post-processing.",
    evidenceStatus: "measured",
    evidenceNote: "Uplink reduction 90.8–96.1% is a measured payload result.",
    notMeaning: "The narrowing stream is a visual metaphor, not a trace of real packets.",
    highlight: { privacy: true, compression: true },
  },
  {
    id: "edge",
    title: "Edge coordination",
    layer: "edge",
    body: "Each edge averages its clients' updates for five edge rounds with public weights, then reports to the cloud. Shorter, local hops replace long uplinks.",
    evidenceStatus: "modelled",
    evidenceNote: "Round latency and delivery are simulated in ns-3.",
    notMeaning: "Simulated network behaviour is not a field measurement.",
    highlight: { compression: true, edgeAggregation: true },
  },
  {
    id: "cloud",
    title: "Cloud aggregation",
    layer: "cloud",
    body: "The cloud averages the edge models over ten cloud rounds and broadcasts the global model back to every client.",
    evidenceStatus: "illustrative",
    evidenceNote: "Conceptual view of the method.",
    highlight: { edgeAggregation: true, direction: "down" },
  },
  {
    id: "evaluation",
    title: "Evaluation",
    layer: "cloud",
    body: "Utility, communication payload and inference latency are measured; round latency and delivery are simulated in ns-3; energy is modelled in CloudSim Plus.",
    evidenceStatus: "modelled",
    evidenceNote: "Mixed: each metric carries its own label on the results page.",
    notMeaning: "No part of this system has been evaluated in a clinical deployment.",
    highlight: {},
  },
];

/** Topologies with verified result data only. */
export const TOPOLOGIES = [
  {
    id: "edges-2",
    edges: 2,
    label: "2 edges",
    description: "Headline configuration for all three datasets.",
    fact: "eICU delivery at two edges: 97.83% (target not met). VitalDB 100.00%, WEAR 99.94%.",
  },
  {
    id: "edges-8",
    edges: 8,
    label: "8 edges",
    description: "eICU edge-count sensitivity test.",
    fact: "At eight edges (about 23 clients per edge) eICU delivery met the >99% target in every simulated round (minimum 99.49%).",
  },
  {
    id: "edges-16",
    edges: 16,
    label: "16 edges",
    description: "eICU edge-count sensitivity test.",
    fact: "At sixteen edges eICU delivery reached 99.94% in the simulation.",
  },
] as const;

export type TopologyId = (typeof TOPOLOGIES)[number]["id"];
