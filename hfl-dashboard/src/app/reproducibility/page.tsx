import type { Metadata } from "next";
import { LongformLayout, PageHeader, Section } from "@/components/layout/Page";
import { LimitationsCallout } from "@/components/content/LimitationsCallout";
import { pageMeta } from "@/content/site";

const meta = pageMeta("/reproducibility/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

const SECTIONS = [
  { id: "protocol", label: "Protocol overview" },
  { id: "config", label: "Configuration summary" },
  { id: "access", label: "Data access" },
  { id: "splits", label: "Splits and grouping" },
  { id: "privacy", label: "Privacy accounting" },
  { id: "simulation", label: "Simulation assumptions" },
  { id: "metrics", label: "Metrics and statistics" },
  { id: "environment", label: "Environment" },
  { id: "provenance", label: "Versioning and provenance" },
  { id: "checklist", label: "Reproduction checklist" },
  { id: "variation", label: "Sources of variation" },
  { id: "limits", label: "Limitations" },
];

const CONFIG: [string, string][] = [
  ["Cloud rounds; edge rounds per cloud round", "10; 5"],
  ["Edge aggregators", "2 (eICU edge-count test: 2–16)"],
  ["Local passes per edge round", "1"],
  ["Optimizer; learning rate; weight decay", "Adam; 10⁻³; 10⁻⁴"],
  ["Expected individuals per step", "64"],
  ["Clipping norm", "1"],
  ["Training budget", "ε = 0.9 (0.766 on WEAR), δ = 10⁻⁵"],
  ["Accountant", "Privacy loss distribution, per-client noise multiplier"],
  ["Records per patient (cap)", "64"],
  ["Update encoding", "Top-20% sparsification, 8-bit quantization, error feedback"],
  ["Seeds", "5 paired; 3 for parameter grids"],
  ["Membership-inference shadow models", "16"],
  ["Latency timing", "P95 over 1,000 runs after 100 warm-up runs"],
];

const CHECKLIST: { group: string; items: string[] }[] = [
  { group: "Data access and agreements", items: ["Obtain each corpus from its provider under its terms.", "For eICU, complete credentialing and sign the data-use agreement."] },
  { group: "Split and grouping", items: ["Split by individual, never by record.", "Assign every individual to exactly one client and one split, or account for individuals held by several clients.", "Keep validation patients disjoint from training patients."] },
  { group: "Seeds and variance", items: ["Use paired seeds across private and non-private arms.", "Fix the seed count before running; do not add seeds after inspecting results."] },
  { group: "Mechanism and accounting", items: ["Group and sum each patient's gradients before clipping.", "Normalise by the expected, not the realised, batch size.", "Calibrate each client's noise from its declared size before training.", "Compose every release, including any calibration release, in the reported budget."] },
  { group: "Simulator configuration", items: ["Simulate the network at packet level for every round, not analytically for some rounds.", "Treat energy as a model output, and report its assumptions."] },
  { group: "Metrics and intervals", items: ["Report AUROC as primary and AUPRC and balanced accuracy as declared secondaries.", "Report paired t-intervals and classify targets with the interval rule."] },
  { group: "Hardware versus simulation", items: ["Label every result as measured or modelled.", "State the hardware used for latency timing."] },
];

export default function ReproducibilityPage() {
  return (
    <>
      <PageHeader
        eyebrow="Methods"
        title="Reproducibility"
        lead="What a researcher needs to understand the method and reproduce the reported evaluation, without access to any restricted artefact."
      />
      <LongformLayout sections={SECTIONS}>
        <Section id="protocol" title="Research protocol overview" intro={<p>Each run trains the fusion head of a fixed encoder backbone across the device, edge and cloud hierarchy, privately and non-privately with paired seeds, then evaluates each selected checkpoint once on its test split. System metrics are collected from the same configuration in ns-3 and CloudSim Plus.</p>} />
        <Section id="config" title="Model and system configuration summary">
          <div className="card overflow-x-auto">
            <table className="data-table">
              <caption className="sr-only">Training and evaluation parameters</caption>
              <thead>
                <tr>
                  <th scope="col">Parameter</th>
                  <th scope="col">Value</th>
                </tr>
              </thead>
              <tbody>
                {CONFIG.map(([k, v]) => (
                  <tr key={k}>
                    <th scope="row" className="font-normal normal-case tracking-normal text-[0.92rem] text-muted">{k}</th>
                    <td className="tnum text-ink">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
        <Section id="access" title="Data-access requirements" intro={<p>VitalDB and WEAR are public research datasets with provider terms. eICU is credentialed data available only under a data-use agreement. This site provides no data and grants no access.</p>} />
        <Section id="splits" title="Patient-level split and grouping principles" intro={<p>Every individual is assigned to exactly one split, and training individuals are disjoint from validation individuals, which are used only for checkpoint selection. On VitalDB, cases that would place a person in a second split or client are removed, so each person is held by one client. On eICU, where clients are hospitals, 2.9% of training individuals have stays at more than one hospital; their privacy budget is the composition of those hospitals' budgets.</p>} />
        <Section id="privacy" title="Privacy accounting assumptions" intro={<p>The guarantee assumes each patient is held by one client, that the architecture, encoder parameters, hyperparameters, edge map, standardization constants and declared client sizes are public and fixed before training, and that each record&apos;s forward pass depends on that record alone. Where encoders or standardization constants are fitted on training data, the guarantee covers the training transcript only.</p>} />
        <Section id="simulation" title="Simulation assumptions" intro={<p>Network delivery and round latency come from a packet-level ns-3 model with clients contending for a shared medium at each edge. Energy per round comes from a CloudSim Plus model of devices, edges and cloud. Neither is a measurement on physical deployment hardware.</p>} />
        <Section id="metrics" title="Evaluation metrics and statistical reporting" intro={<p>AUROC is the primary utility measure; AUPRC and balanced accuracy (at a validation-chosen threshold) were declared before the runs. Comparisons are paired by seed with t-intervals, and targets are classified by whether the whole interval meets them.</p>} />
        <Section id="environment" title="Environment and dependency summary" intro={<p>Training used PyTorch with Opacus on a single workstation GPU; inference was timed with ONNX Runtime on a workstation CPU; network and energy were simulated in ns-3 and CloudSim Plus.</p>} />
        <Section id="provenance" title="Versioning and provenance policy" intro={<p>Every number on this site is a hand-authored, curated record checked against the final manuscript, with a provenance label and review date. The site never reads research files at build or run time. Any change to a value must pass the content validation and the review checklist.</p>} />
        <Section id="checklist" title="Reproduction checklist">
          <div className="grid gap-4 md:grid-cols-2">
            {CHECKLIST.map((c) => (
              <div key={c.group} className="card p-5">
                <h3 className="font-medium text-ink">{c.group}</h3>
                <ul className="mt-2 space-y-1.5 text-sm text-muted">
                  {c.items.map((i) => (
                    <li key={i} className="flex gap-2">
                      <span aria-hidden className="mt-[3px] inline-block h-3.5 w-3.5 shrink-0 rounded-sm border border-line-strong" />
                      {i}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Section>
        <Section id="variation" title="Known sources of variation">
          <ul className="grid gap-2 text-muted">
            {[
              "Seed-to-seed variance, especially for small clients that sample every patient at every step.",
              "Partition choice: person-level and case-level partitions of VitalDB give different estimates.",
              "Encoder provenance and where standardization constants are fitted.",
              "Edge count and clients per edge, which drive simulated delivery.",
              "Latency hardware.",
            ].map((x) => (
              <li key={x} className="flex gap-3">
                <span aria-hidden className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                {x}
              </li>
            ))}
          </ul>
        </Section>
        <Section id="limits" title="Limitations of the reported setup">
          <LimitationsCallout title="Code and artefacts" tone="scope" href="/limitations/" linkLabel="All limitations">
            No public code release has been approved, and this site does not expose source files, configuration files, logs or intermediate data. A release, if approved, will be linked from the publication page after a separate review.
          </LimitationsCallout>
        </Section>
      </LongformLayout>
    </>
  );
}
