# PP-HFM Research Observatory
## Complete Product, Design, Interaction, Animation, Three.js, Content, and Implementation Specification

**Document type:** Product requirements + UX/UI specification + technical implementation brief  
**Project:** PP-HFM Research Observatory  
**Research title:** *Patient-Level Differential Privacy in Hierarchical Federated Learning for Multimodal Medical IoT*  
**Delivery model:** Pure web-based public-facing research experience  
**Primary goal:** Explain the research, system architecture, privacy design, experiments, evidence, limitations, and reproducibility in a polished, interactive, animated scientific website.  
**Non-negotiable constraint:** The website must never expose or display the underlying GitHub repository, its source code, internal directory structure, private logs, raw experiment outputs, credentials, restricted datasets, patient-level records, or other repository artifacts. All public content must be intentionally curated for the website.

---

# 1. Product Vision

Build a premium, browser-based scientific experience—not a generic admin dashboard and not a GitHub viewer. Visitors should be able to understand the research problem, explore the Device → Edge → Cloud learning design, inspect approved aggregate results, understand the privacy mechanism, compare evaluation datasets, and read the limitations without needing to inspect code.

The site should feel like an interactive research exhibit: precise, restrained, technically credible, visual, and easy to navigate. Use motion to explain concepts, not merely decorate the page.

## 1.1 Core outcomes

1. Explain the research problem and motivation in under one minute.
2. Make hierarchical federated learning understandable through an interactive 3D system model.
3. Explain patient-level differential privacy and its accounting boundary without implying that a single privacy metric proves zero leakage.
4. Present results with clear labels, confidence intervals where available, targets, and caveats.
5. Distinguish measured results from simulated/modelled results and inconclusive findings.
6. Explain the datasets at a safe, aggregate level without exposing individual records or restricted source data.
7. Provide a transparent limitations and reproducibility section.
8. Work entirely in the browser for the public research experience; no live connection to the research repository is required.
9. Remain usable on mobile, reduced-motion devices, and devices without WebGL.
10. Keep every public-facing metric traceable to an approved, curated content record—not to a live repository file.

## 1.2 Non-goals

- Not a hospital information system or clinical decision-support tool.
- Not a production FL orchestration console.
- Not a live experiment launcher.
- Not a repository browser, code explorer, file tree, or CI dashboard.
- Not a patient-data viewer.
- Not a public download area for raw datasets, patient-level arrays, per-hospital counts, scratch files, credentials, or internal logs.
- Not a claim of clinical validation or deployment readiness.
- Not a claim that privacy risk is zero.
- Not an API for unrestricted access to internal research artefacts.

---

# 2. Product Principles

### 2.1 Evidence before spectacle
Use 3D and animation to explain the system. Use restrained charts and annotations to communicate results. Every numeric result must have a definition, unit, evaluation context, and appropriate status label.

### 2.2 Public narrative, not repository exposure
The website is a separately authored product. It must not fetch, render, enumerate, or mirror the GitHub repository. Do not display source paths, code snippets copied from the repository, branch names, commit hashes, raw log text, internal filenames, directory trees, or private scratch paths.

### 2.3 Explicit evidence labels
Every result must be classified as one of:
- **Measured** — directly measured in the described experiment or evaluation.
- **Modelled** — produced by a simulator or analytical model, not measured on physical deployment hardware.
- **Inconclusive** — evidence does not resolve the prespecified decision rule.
- **Target not met** — a target was not reached.
- **Not evaluated** — no evidence is being claimed.
- **Illustrative** — a conceptual visual or example, not experimental evidence.

Never style these labels as interchangeable success badges.

### 2.4 Privacy-aware by design
Only publish approved aggregate results. Never publish row-level patient records, patient identifiers, raw medical time series, image samples, per-hospital small-cell counts, membership-audit examples tied to individuals, restricted dataset extracts, or secrets.

### 2.5 Accessibility is part of the design
Support keyboard navigation, visible focus, screen-reader labels, high contrast, captions/alternative text, and reduced-motion preferences. Never rely on animation, colour, or 3D alone to convey meaning.

---

# 3. Brand and Visual Direction

## 3.1 Brand name
**PP-HFM Research Observatory**

Subtitle:
**Patient-Level Differential Privacy in Hierarchical Federated Learning for Multimodal Medical IoT**

Short descriptor:
*A browser-based exploration of privacy-aware learning across device, edge, and cloud.*

## 3.2 Art direction
- Premium scientific editorial aesthetic.
- Deep ink / charcoal backgrounds with subtle blue undertones.
- Soft off-white text and restrained cyan/teal highlights.
- Occasional warm amber for caveats and warnings.
- Large editorial headings balanced with compact technical labels.
- Fine grid lines, thin borders, generous whitespace, and purposeful negative space.
- 3D scenes should resemble a scientific visualization or network observatory, not a game.
- Charts should be legible and sober, with no misleading 3D chart effects.

## 3.3 Suggested design tokens

```css
:root {
  --color-bg: #071018;
  --color-bg-elevated: #0c1822;
  --color-surface: #101f2b;
  --color-surface-raised: #142735;
  --color-border: rgba(173, 207, 221, 0.16);
  --color-text: #eef6f8;
  --color-text-muted: #a4b7c1;
  --color-text-subtle: #718995;
  --color-cyan: #67dce7;
  --color-teal: #56cbb4;
  --color-blue: #78a9ff;
  --color-amber: #f2bd73;
  --color-red: #f18b8b;
  --color-success: #77d6ae;
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 22px;
  --shadow-soft: 0 16px 48px rgba(0, 0, 0, 0.24);
  --content-width: 1240px;
}
```

These values are initial design tokens and can be tuned during implementation. Maintain contrast when adjusting them.

## 3.4 Typography
- Interface and body: Inter, Geist Sans, or another highly legible sans-serif.
- Research/editorial headings: a restrained serif such as Newsreader or Instrument Serif, used sparingly.
- Metrics and technical values: tabular numerals.
- Avoid overly small body text. Aim for 16–18 px desktop body text and comfortable line height.
- Technical labels may be compact but must remain readable.

## 3.5 Layout
- Desktop content width: approximately 1160–1280 px.
- Large editorial sections with alternating text and visual compositions.
- Use a persistent top navigation with a compact scroll state.
- Use a left-side section index only on long-form desktop pages where it improves orientation.
- Mobile: single-column layout, collapsible navigation, simplified 3D scenes, and no horizontal overflow.

---

# 4. Recommended Technology Stack

## 4.1 Frontend
- **Next.js** with the App Router.
- **TypeScript** with strict type checking.
- **React** for component structure and interactions.
- **Tailwind CSS** for styling and responsive layout.
- **shadcn/ui** or equivalent accessible primitives for menus, dialogs, tabs, tooltips, and accordions.
- **Three.js** with **React Three Fiber** for interactive 3D scenes.
- **Drei** for common 3D helpers where useful.
- **Framer Motion** for UI transitions and scroll-triggered motion.
- **Recharts** or **Visx** for evidence-based 2D charts.
- **Zod** for validation of curated local content data.
- **Vitest** and **React Testing Library** for unit/component tests.
- **Playwright** for end-to-end and accessibility-oriented interaction checks.

Equivalent libraries are acceptable if the implementation preserves the behavior, accessibility, and privacy requirements.

## 4.2 Pure web-based requirement
The public website must work as a normal browser application. The visitor should not need Python, notebooks, a local model, a research runtime, or repository access.

Recommended public experience:
- Static-first rendering and curated content data.
- No backend required for the first release.
- No live experiment execution.
- No repository API calls.
- No hidden connection to internal project services.
- Optional future analytics only if privacy-preserving, disclosed, and approved.

A static deployment on a suitable web host is sufficient. The website can be deployed independently from the research repository.

## 4.3 Three.js implementation
- Use Three.js only where spatial interaction adds explanatory value.
- Load 3D scenes lazily when their section becomes visible or the user opens them.
- Use instancing for repeated nodes and particles.
- Limit device pixel ratio on mobile.
- Pause animation when a scene is offscreen or the tab is hidden.
- Provide a static SVG/canvas/HTML fallback when WebGL is unavailable.
- Respect `prefers-reduced-motion`.
- Keep text, labels, metrics, and controls in semantic HTML, not baked into the 3D canvas.
- Do not use 3D charts for numeric comparisons.

---

# 5. Information Architecture and Routes

Required public pages:

1. `/` — Overview
2. `/research` — Research question and contributions
3. `/architecture` — Interactive hierarchical FL architecture
4. `/datasets` — Dataset and evaluation overview
5. `/privacy` — Privacy mechanism and threat model
6. `/results` — Results explorer
7. `/experiments` — Experiment design and evaluation protocol
8. `/reproducibility` — Methods, assumptions, provenance, and reproducibility guidance
9. `/limitations` — Limitations, unresolved targets, and interpretation
10. `/publication` — Publication information and approved public resources
11. `/accessibility` — Accessibility statement and interaction alternatives
12. Custom 404 page — Clear route back to the public research experience

The navigation may group pages under “Research”, “System”, “Evidence”, and “Methods”, but all required pages must remain discoverable.

Do not include a route named `/repository`, `/source`, `/files`, `/logs`, or `/internal`. Do not add a source-code panel or a GitHub repository browser.

---

# 6. Global Shell and Interactions

## 6.1 Header
Elements:
- Wordmark: PP-HFM.
- Small descriptor: Research Observatory.
- Navigation links: Research, Architecture, Datasets, Privacy, Results, Methods.
- Primary action: “Explore the system”.
- Mobile menu button with accessible name and expanded state.

Behavior:
- Transparent or subtly translucent header at the top of the page.
- On scroll, transition to a solid elevated background with a fine border.
- Active page link updates based on the current route.
- Keyboard focus remains clearly visible.
- No hidden auto-opening menus.

## 6.2 Global progress / section navigation
Long pages may include a thin reading-progress indicator and an optional section index. These must not obstruct content or interfere with screen readers.

## 6.3 Global interaction patterns
- Hover states are subtle and also have keyboard-focus equivalents.
- Tooltips are not the sole location for essential information.
- Clickable cards must be semantic links or buttons.
- Tabs must support keyboard interaction.
- Modals must trap focus, close on Escape, and return focus to the trigger.
- Charts must have an accessible textual summary and data table alternative.
- Motion must never be required to understand a claim.

## 6.4 Search
Optional site-wide search can search only the website’s curated public content index. It must not query GitHub, source files, logs, or connected drives. Search results must be limited to approved public page content.

---

# 7. Homepage Specification

The homepage is a guided narrative rather than a dense KPI wall.

## Section 1 — Hero

**Eyebrow:** PRIVACY-AWARE COLLABORATIVE LEARNING  
**Headline:** Learning across the edge. Privacy at the patient level.  
**Supporting copy:** PP-HFM explores a hierarchical federated learning design for multimodal medical IoT, combining device-level learning, edge coordination, cloud aggregation, and patient-level differential privacy. The Observatory presents its design, evaluation evidence, and limitations in an interactive format.

Primary CTA: **Explore the architecture**  
Secondary CTA: **Read the results**

Visual:
- A restrained Three.js network scene.
- Three spatial layers labelled Device, Edge, Cloud.
- Device nodes emit small, slow-moving signal particles toward edge nodes; edge nodes aggregate visual signals toward a cloud layer.
- Use neutral particles rather than representations of real patient data.
- Label all signals as **conceptual model**, not a live network trace.
- Provide “Pause motion” and “Use static view” controls.

Animation:
- Intro fade and short vertical reveal.
- Node paths draw in over time.
- No long blocking intro, forced scroll, or animation that delays access to content.
- Hero content remains readable when WebGL fails.

## Section 2 — Research question

Headline: **Can hierarchical collaboration reduce communication and energy costs while maintaining a bounded privacy budget?**

Three short cards:
1. **Communication:** Reduce uplink traffic by compressing updates and coordinating at the edge.
2. **Privacy:** Apply patient-level privacy accounting and evaluate utility costs.
3. **Deployment constraints:** Study latency, energy, and update delivery in a hierarchical simulation/evaluation setting.

Add a concise disclaimer: this is a research evaluation, not a validated clinical system.

## Section 3 — System at a glance

Use three linked cards:
- **Device layer:** Local data processing and client-side model updates.
- **Edge layer:** Local coordination, update reduction, and regional aggregation.
- **Cloud layer:** Higher-level aggregation, global coordination, and evaluation.

Interaction:
- Selecting a card highlights its layer in the architecture preview.
- A “Trace an update” button animates a conceptual update path.
- A “Trace a model broadcast” button reverses the direction.
- The user can step through one layer at a time.
- Provide a static textual explanation adjacent to the visual.

## Section 4 — Evaluation datasets

Display high-level dataset cards for:
- VitalDB
- WEAR
- eICU

Each card includes:
- Dataset role in the evaluation.
- Broad data modality or task description only when verified.
- Public/credentialed access note where applicable.
- What is evaluated.
- Link to the website’s dataset page.

Important:
- eICU is credentialed data under a data-use agreement. Do not provide raw records, extracts, patient-level samples, or per-hospital small-cell counts.
- Do not show actual medical images or time-series samples unless the license and publication approval explicitly permit them.
- Any dataset size or cohort count shown publicly must be reviewed for disclosure risk and approved before publication.

## Section 5 — Evidence snapshot

Use a small set of evidence cards, not an overwhelming wall of numbers.

Approved headline values to include only with context:
- Uplink reduction: VitalDB 90.8%, WEAR 96.1%, eICU 92.3%.
- Round-latency reduction: VitalDB 16.9%, WEAR 21.7%, eICU 33.4%.
- Modelled energy saving per FL round: VitalDB 72.3%, WEAR 76.8%, eICU 79.6%.
- P95 inference latency: VitalDB 2.30 ms, WEAR 0.75 ms, eICU 0.24 ms.
- Update delivery: VitalDB 100.00%, WEAR 99.94%, eICU 97.83% at the reported two-edge configuration.

Every card must display:
- Dataset.
- Metric name and unit.
- Evaluation setting.
- Status label.
- One-line interpretation.
- Link to detailed result and limitations.

Energy savings must be labelled **modelled in CloudSim Plus**, not physical hardware measurements. Update delivery for eICU at two edges must be marked **target not met** against a >99% target.

## Section 6 — Privacy in context

Explain that privacy is a defined mechanism and accounting claim, not a guarantee that all attacks are impossible.

Show the training privacy budget and conformal calibration budget separately:
- VitalDB: training ε = 0.900; conformal ε = 0.1; total ε = 1.000.
- WEAR: training ε = 0.766; conformal ε = 0.2; total ε = 0.966.
- eICU: training ε = 0.900; conformal ε = 0.1; total ε = 1.000.

State δ = 10⁻⁵ where applicable and explain that privacy guarantees depend on the stated adjacency definition, sampling/accounting assumptions, and implemented mechanism. The page must not imply that epsilon alone captures every real-world risk.

## Section 7 — What the evidence does and does not show

Use two columns: **Evidence supports** and **Still unresolved**.

Evidence supports:
- Strong uplink reductions in the reported evaluation.
- Low reported inference latency under the stated evaluation conditions.
- Modelled energy savings in the simulator.
- A person-level VitalDB rerun with a favourable utility result under the reported protocol.

Still unresolved:
- eICU privacy utility cost remains above the two-point point-estimate target, with the headline interval classified as inconclusive by the prespecified rule.
- eICU end-to-end AUROC cost is a clear miss against the target.
- eICU update delivery at two edge servers is below the >99% target.
- Simulator estimates are not physical deployment measurements.
- Membership-inference audit results do not prove zero leakage.
- Clinical usefulness and production readiness have not been established by these experiments.

## Section 8 — Methods preview
Links to:
- Architecture
- Privacy laboratory
- Experiments
- Reproducibility
- Limitations

## Section 9 — Publication and credits
Show the approved paper title and author list only after the final author metadata and publication status are confirmed. Do not fabricate a DOI, conference acceptance, publication date, journal, or publication status. Until confirmed, label the paper “Manuscript / research project” and provide no invented citation metadata.

## Section 10 — Footer
- Research title.
- Navigation links.
- Accessibility.
- Data and privacy statement.
- Disclaimer: research prototype; not for clinical decision-making.
- “All public figures are curated research summaries; this site does not expose the underlying repository or raw research data.”

---

# 8. Research Page (`/research`)

Purpose: explain the scientific problem, research gap, aims, and contributions without requiring code inspection.

Sections:
1. Problem statement.
2. Why hierarchical federated learning.
3. Why patient-level privacy differs from record-level privacy.
4. Why multimodal medical IoT is challenging.
5. Research questions.
6. Claimed contributions.
7. Evaluation overview.
8. Scope boundaries.

Suggested research questions:
- How can hierarchical device–edge–cloud coordination reduce communication overhead?
- What utility costs arise when enforcing patient-level differential privacy under the stated accounting method?
- How do latency, update delivery, and modelled energy consumption behave across the evaluated datasets and topologies?
- How do privacy-audit outcomes vary across the evaluated comparison methods?

Contributions must be phrased as design/evaluation contributions, not as universal proof:
- A hierarchical federated learning design for multimodal medical IoT.
- A patient-level privacy mechanism and accounting protocol evaluated under stated assumptions.
- A cross-dataset evaluation of communication, latency, energy modelling, utility, and update delivery.
- A bounded membership-inference audit with explicit uncertainty and scope limitations.
- A reproducibility-oriented presentation of results and limitations.

Add a “What this work does not claim” block:
- No claim of zero privacy leakage.
- No claim of clinical deployment readiness.
- No claim that simulator outputs equal real-device measurements.
- No claim that all targets are met across all datasets.
- No claim that results generalize to every institution, device, or patient population.

---

# 9. Interactive Architecture Page (`/architecture`)

This is the main Three.js experience.

## 9.1 Three.js scene composition

Create a layered spatial scene with three horizontal bands:
- **Device tier** — a set of small client nodes.
- **Edge tier** — two or more aggregation nodes, with the currently selected topology explicitly labelled.
- **Cloud tier** — a global aggregation/coordinator node.

Do not imply that the rendered node count is the actual number of patients or a faithful count of physical devices. If a count is used, label it as a schematic or the specific evaluated configuration.

Visual language:
- Devices: small geometric nodes with subtle glow.
- Edge servers: larger translucent geometric hubs.
- Cloud: a restrained central node or layered ring.
- Links: thin lines with low-opacity flow particles.
- Privacy boundary: a clearly marked boundary around the client update mechanism, accompanied by text explaining what is and is not protected.
- Compression step: a visual narrowing of an abstract update stream, not a claim that every packet follows the exact animation.

## 9.2 Controls
- Rotate: pointer drag and keyboard-accessible equivalent controls.
- Zoom: scroll/pinch with limits.
- Pan: optional, with reset control.
- “Show data flow” toggle.
- “Show privacy boundary” toggle.
- “Show compression” toggle.
- “Show edge aggregation” toggle.
- “Reset view” button.
- “Play flow” / “Pause flow” controls.
- Step selector: Device → Edge → Cloud.
- Layer selector: Device / Edge / Cloud.
- Topology selector only for configurations that have verified result data.
- “Switch to 2D diagram” link.

Do not rely on drag-only controls. Every core action must also be possible through buttons or a linear stepper.

## 9.3 Guided story mode
A short, optional sequence:
1. **Local computation:** Explain that local processing happens at clients.
2. **Privacy mechanism:** Explain clipping/noise/accounting at the correct mechanism boundary.
3. **Update reduction:** Explain the reported compression or sparsification strategy only as verified by the approved methods description.
4. **Edge coordination:** Explain local aggregation.
5. **Cloud aggregation:** Explain global coordination.
6. **Evaluation:** Show where metrics are measured or modelled.

Each step updates:
- Highlighted scene elements.
- A side panel with a short explanation.
- A small “Evidence status” label.
- A “What this does not mean” caveat when necessary.

## 9.4 Three.js technical requirements
- Use React Three Fiber with a clean scene/component boundary.
- Use `Canvas` with accessible fallback handling.
- Use `InstancedMesh` for repeated nodes where appropriate.
- Use a small, fixed number of particles and deterministic animation parameters.
- Avoid expensive post-processing by default.
- Cap device pixel ratio to avoid overheating laptops and phones.
- Pause rendering when offscreen and when the document is hidden.
- Respect `prefers-reduced-motion`; default to a static diagram or only user-triggered animation.
- Ensure server rendering does not attempt to access browser-only WebGL APIs.
- Dynamically import the 3D component.
- If WebGL initialization fails, render the 2D diagram with the same controls and labels.
- Do not put the only copy of a scientific explanation inside a WebGL canvas.
- Do not use a Three.js scene as a source of scientific truth; use curated data objects for labels and metrics.

## 9.5 2D fallback
Use an accessible SVG diagram with the same three layers, arrows, privacy boundary, and explanatory labels. It must be functionally sufficient, not a decorative placeholder.

---

# 10. Dataset Explorer (`/datasets`)

## 10.1 Dataset comparison view
Use accessible tabs or cards for VitalDB, WEAR, and eICU.

Each dataset detail panel includes:
- Evaluation role.
- Broad modality/task summary.
- Split and client-partitioning description at a safe aggregate level.
- Relevant metrics.
- Privacy budget.
- Communication result.
- Utility result.
- Latency and update delivery.
- Energy result with modelling caveat.
- Access/licensing caveat.
- Dataset-specific limitations.

Only include values whose provenance and disclosure have been reviewed and approved.

## 10.2 Public content rules
- Do not display patient records, individual time series, medical images, row-level features, identifiers, or sample payloads.
- Do not expose restricted dataset extracts or downloadable intermediate data.
- Do not show per-hospital small-cell counts or any statistic that could disclose sensitive cohort information.
- For credentialed eICU, state that access is governed by the dataset provider’s terms and data-use agreement.
- Do not imply that the website itself grants access to any dataset.
- If dataset size figures are included, use official/publicly documented counts and verify their license and suitability for this context.

## 10.3 Comparison controls
- Metric selector: Communication, Utility, Latency, Energy, Update delivery, Privacy budget.
- Dataset selector.
- Target line toggle.
- “Show confidence intervals” toggle where intervals exist.
- “Show interpretation” toggle.
- Export only the current approved summary table as CSV or JSON if explicitly implemented; never export underlying records or private arrays.

---

# 11. Privacy Laboratory (`/privacy`)

Purpose: explain the mechanism and audit findings accurately and cautiously.

## 11.1 Page structure
1. Privacy goal.
2. Unit of privacy and adjacency definition.
3. Mechanism overview.
4. Clipping and noise.
5. Accounting and budget composition.
6. Utility trade-off.
7. Membership-inference audit.
8. Threat model and assumptions.
9. Limitations.

## 11.2 Interactive privacy budget explorer
A visual budget composition component shows:
- Training budget.
- Conformal calibration budget.
- Total reported budget.
- Target threshold ε ≤ 1.
- δ where applicable.

Values:
- VitalDB: 0.900 + 0.100 = 1.000.
- WEAR: 0.766 + 0.200 = 0.966.
- eICU: 0.900 + 0.100 = 1.000.

Interaction:
- Select a dataset.
- Hover or focus each budget component for a definition.
- Toggle “Explain the accounting”.
- Show a formula/definition panel in accessible HTML.
- Provide a plain-language explanation of what the budget does and does not guarantee.

Do not allow users to change epsilon and have the UI pretend to recompute an actual privacy guarantee unless a valid, tested accounting implementation is provided. A hypothetical slider may be included only if it is explicitly labelled **illustrative scenario—not a recomputed guarantee**.

## 11.3 Membership-inference audit
Use a chart with a clearly explained AUC scale and uncertainty intervals. Show only approved aggregate results.

Selected patient-level VitalDB result:
- Patient-level DP offline LiRA AUC: 0.503 [0.475, 0.531].
- Reference/floor value: 0.508.
- Difference from the stated floor: −0.005.

Interpretation:
- This result is close to the reference level under the reported audit protocol.
- It does **not** establish zero leakage.
- It does **not** prove resistance to all attacks.
- Its meaning is limited by the evaluated attack, model, dataset, sampling, and uncertainty.

Other comparator values may be displayed only after their exact definitions, intervals, and comparability are checked. Do not compare values from different audit setups as though they were a single perfectly controlled ranking.

## 11.4 Threat model
Describe in plain language:
- Protected unit: patient-level contribution, as defined by the research protocol.
- Adversary scope: only the adversaries and attacks actually evaluated.
- Trusted components and assumptions.
- Potential leakage channels outside the mechanism.
- Why model outputs, metadata, repeated participation, preprocessing, and deployment operations require separate scrutiny.

Do not invent a threat-model guarantee absent from the approved research description.

---

# 12. Results Explorer (`/results`)

This page is a core research feature. It should make evidence understandable and auditable, not merely visually impressive.

## 12.1 Top-level controls
- Dataset: All / VitalDB / WEAR / eICU.
- Metric: Communication / Round latency / Utility / P95 inference latency / Update delivery / Energy / Privacy.
- View: Cards / Charts / Table.
- Confidence intervals: show/hide where available.
- Targets: show/hide.
- Evidence status: measured / modelled / inconclusive / target not met.
- “Explain this metric” panel.

Every filter must update the visible chart, table, caption, and status text together. Avoid a UI where the chart changes but the interpretation does not.

## 12.2 Approved aggregate result values

Use the following values as the initial curated content set, subject to final verification against the approved final results record before publication.

### Communication reduction
| Dataset | Result | Target | Status |
|---|---:|---:|---|
| VitalDB | 90.8% | ≥50% | Target met |
| WEAR | 96.1% | ≥50% | Target met |
| eICU | 92.3% | ≥50% | Target met |

Label the metric precisely: **uplink traffic reduction**. Define the baseline and comparison method in the metric detail panel.

### Round latency reduction
| Dataset | Result | Status |
|---|---:|---|
| VitalDB | 16.9% | Reported result |
| WEAR | 21.7% | Reported result |
| eICU | 33.4% | Reported result |

Clearly define which latency is measured and which baseline is used. Do not conflate this with inference latency.

### Modelled energy savings per FL round
| Dataset | Result | Target | Status |
|---|---:|---:|---|
| VitalDB | 72.3% | ≥20% | Modelled; target met |
| WEAR | 76.8% | ≥20% | Modelled; target met |
| eICU | 79.6% | ≥20% | Modelled; target met |

Required caption: **Estimated by CloudSim Plus simulation; not a physical hardware energy measurement.** This caveat must remain visible in chart, table, and exported summary.

### P95 inference latency
| Dataset | Result | Target | Status |
|---|---:|---:|---|
| VitalDB | 2.30 ms | <100 ms | Reported result |
| WEAR | 0.75 ms | <100 ms | Reported result |
| eICU | 0.24 ms | <100 ms | Reported result |

Display the evaluation context and hardware/simulation context if relevant and verified. Do not imply that the numbers are universal deployment guarantees.

### Update delivery
| Dataset | Result | Target | Status |
|---|---:|---:|---|
| VitalDB | 100.00% | >99% | Target met |
| WEAR | 99.94% | >99% | Target met |
| eICU, two-edge configuration | 97.83% | >99% | Target not met |

State that the eICU result was below target for the reported two-edge configuration. The claim that delivery meets the target from eight edges may be included only if the corresponding experiment and exact setup are validated and clearly scoped.

### Privacy budgets
| Dataset | Training ε | Conformal ε | Total ε | Target |
|---|---:|---:|---:|---:|
| VitalDB | 0.900 | 0.100 | 1.000 | ≤1 |
| WEAR | 0.766 | 0.200 | 0.966 | ≤1 |
| eICU | 0.900 | 0.100 | 1.000 | ≤1 |

Explain that the totals are valid only under the stated accounting protocol and assumptions.

### Utility cost under privacy
| Dataset / evaluation | Result | Interval | Interpretation |
|---|---:|---|---|
| VitalDB, person-level rerun | −1.18 AUROC points | [−1.63, −0.73] points | Favourable reported result under this protocol |
| WEAR | 1.97 percentage points accuracy loss | Show interval only if verified in final record | Near the two-point target; preserve exact metric definition |
| eICU, headline/training-fitted | 3.09 AUROC points | [1.37, 4.81] points | Inconclusive under the prespecified interval rule; point estimate exceeds the two-point target |
| eICU, end-to-end/pool-fitted | 3.91 AUROC points | [2.40, 5.42] points | Target not met |

For VitalDB, the raw AUROC difference is −0.0118, equivalent to −1.18 AUROC points. Explain that a negative cost here indicates the private model scored higher in this evaluation; do not generalize it to a guarantee that privacy improves utility.

Do not collapse the two eICU results into one. Label the training-fitted and end-to-end evaluation paths separately.

## 12.3 Required chart types
- Horizontal bar chart for communication reduction.
- Horizontal bar chart for round-latency reduction.
- Point-and-interval plot for utility cost where confidence intervals are available.
- Dot plot for P95 inference latency with target reference line.
- Dot/bar plot for update delivery with a 99% reference line.
- Stacked budget bar for privacy accounting.
- Modelled energy chart with a persistent “simulation estimate” label.
- Optional small multiples to compare datasets without mixing incompatible units.

Do not use a shared axis for incompatible metrics. Avoid 3D bars, perspective distortion, truncated axes without disclosure, and decorative motion that changes apparent values.

## 12.4 Result detail drawer
Selecting any metric opens a detail panel with:
- Exact definition.
- Unit.
- Dataset and evaluation setting.
- Result.
- Target.
- Evidence status.
- Confidence interval if available.
- Baseline/comparator.
- Interpretation.
- Caveat.
- Public provenance label, such as “Curated from the approved final evaluation record”.
- Date of last review, if known.

Do not expose internal file paths, repository commit hashes, raw logs, or a direct link to internal files.

---

# 13. Experiments Page (`/experiments`)

Describe the evaluation programme as an organized scientific plan.

Suggested sections:
1. Evaluation objectives.
2. Baselines and comparison systems.
3. Datasets and partitioning.
4. Communication experiments.
5. Privacy and utility experiments.
6. Latency and update-delivery experiments.
7. Energy simulation.
8. Membership-inference audit.
9. Sensitivity and ablation experiments.
10. Statistical reporting.

Objectives:
- **O1:** Uplink reduction, with target ≥50%.
- **O1b:** Round-latency reduction.
- **O2a:** Total privacy budget, target ε ≤1 under the stated accounting protocol.
- **O2b:** Utility cost, with a two-point target where defined.
- **O3a:** P95 inference latency target <100 ms.
- **O3b:** Update-delivery reliability target >99%.
- **O4:** Energy saving per round target ≥20%, explicitly modelled in CloudSim Plus.

Interactive experiment matrix:
- Rows: objectives or experiment families.
- Columns: datasets.
- Cell: status, result summary, and link to the results detail.
- Selecting a cell opens a side panel with scope, metric, and caveats.

Only include baselines, ablations, and exact experiment counts that are verified in the approved manuscript and results. Do not fabricate a completed experiment because a section exists in the site design.

---

# 14. Reproducibility Page (`/reproducibility`)

Goal: help a researcher understand the method and the requirements for reproducing the reported evaluation without exposing restricted artefacts.

Sections:
- Research protocol overview.
- Model and system configuration summary.
- Data-access requirements.
- Patient-level split and grouping principles.
- Privacy accounting assumptions.
- Simulation assumptions.
- Evaluation metrics and statistical reporting.
- Environment and dependency summary at a high level.
- Versioning and provenance policy.
- Reproduction checklist.
- Known sources of variation.
- Limitations of the reported setup.

Do not expose:
- Internal source files or raw configuration files.
- Secrets, API keys, tokens, credentials, or private endpoints.
- Raw patient-level data, arrays, intermediate feature files, or restricted extracts.
- Internal logs or scratch directories.
- Private hostnames or machine paths.
- Internal repository structure or source browsing.

Provide only an intentionally written method summary, approved public artifacts, and legitimate public publication links. If a public code release is later approved, link to it only after a separate release review; the default website must not expose the repository.

Reproduction checklist should distinguish:
- Required data access and agreements.
- Exact data split and grouping assumptions.
- Random seeds and reported variance, where verified.
- Mechanism and privacy-accounting settings.
- Simulator configuration and calibration assumptions.
- Metric definitions and statistical intervals.
- Hardware versus simulated measurements.

---

# 15. Limitations Page (`/limitations`)

This page is mandatory and should be easy to find.

## 15.1 Key limitations to disclose
- The results are tied to the stated datasets, partitions, model choices, privacy mechanism, and evaluation protocol.
- eICU headline utility cost: 3.09 AUROC points with interval [1.37, 4.81], classified as inconclusive under the prespecified interval rule; its point estimate exceeds the two-point target.
- eICU end-to-end utility cost: 3.91 points with interval [2.40, 5.42], a clear miss against the two-point target.
- eICU update delivery at the reported two-edge configuration: 97.83%, below the >99% target.
- Energy savings are simulator estimates from CloudSim Plus, not physical energy measurements.
- A membership-inference AUC close to a reference value does not prove zero leakage or universal attack resistance.
- Low reported inference latency does not establish a real-world clinical deployment SLA.
- Clinical validity, generalization, regulatory readiness, and operational safety require separate evaluation.
- The website’s 3D architecture is explanatory and not a live telemetry view.

## 15.2 Presentation
Use a calm, transparent editorial tone. Avoid hiding limitations behind a tiny footer or a collapsible disclosure that users are unlikely to open.

---

# 16. Publication Page (`/publication`)

Display:
- Full research title.
- Confirmed author names and affiliations only.
- Abstract written for public readers.
- Keywords.
- Current publication status.
- Approved citations and public links.
- Approved figures or supplementary materials.
- A short statement of data-access restrictions and code availability policy.

Never invent:
- DOI.
- Venue.
- Acceptance status.
- Publication date.
- Author list or affiliations.
- Dataset permissions.
- License for source code or figures.

If publication status is not finalized, state that clearly. Keep repository and raw data links out of the default public experience unless an explicit release review approves a specific public resource.

---

# 17. Motion and Animation System

## 17.1 Motion principles
- Purposeful, short, and calm.
- Motion must communicate hierarchy, direction, or state.
- Avoid excessive parallax, continuous page-wide movement, cursor trails, flashing, or scroll hijacking.
- Essential content must render without waiting for animation.
- Keep text readable while animation runs.

## 17.2 Recommended animation patterns
- Page transition: short opacity/position transition.
- Section reveal: subtle fade-up when entering viewport.
- Cards: slight border/highlight transition.
- Charts: animate from a neutral baseline once, then stop.
- Architecture: animate flow only when visible or user-triggered.
- Navigation: small underline or background transition.
- Number values: count-up only once and only when it does not obscure exact values; provide the exact number in accessible text immediately.
- Tabs: quick content crossfade without moving layout unexpectedly.
- Dialog/drawer: brief fade and small translation.

## 17.3 Reduced motion
When `prefers-reduced-motion: reduce`:
- Disable automatic parallax and scroll-linked movement.
- Stop particle drift.
- Replace animated scene transitions with instant state changes.
- Do not auto-play the architecture flow.
- Use static charts or minimal nonessential transitions.
- Keep all controls and explanations functional.

Provide a visible motion toggle that allows users to pause decorative motion. Do not use the toggle as a replacement for honoring OS preferences.

---

# 18. Interactive Components Catalogue

Implement the following reusable components.

1. **ResearchMetricCard**
   - Metric, value, unit, dataset, status, target, caveat, detail action.

2. **EvidenceStatusLabel**
   - Measured, Modelled, Inconclusive, Target not met, Not evaluated, Illustrative.

3. **MetricDefinitionPanel**
   - Definition, unit, baseline, evaluation context, limitations.

4. **DatasetSelector**
   - Keyboard-accessible selection for VitalDB, WEAR, eICU.

5. **MetricFilterBar**
   - Metric, dataset, evidence status, target and interval filters.

6. **AccessibleChartFrame**
   - Chart title, text summary, caveat, accessible data table.

7. **PrivacyBudgetStack**
   - Training budget, calibration budget, total, threshold, explanation.

8. **ArchitectureCanvas3D**
   - Three.js view with layer selection, flow playback, reset, pause, fallback.

9. **ArchitectureDiagram2D**
   - Accessible SVG fallback and alternative view.

10. **GuidedStepPanel**
    - Step title, explanation, current layer, next/back, evidence status.

11. **ResultDetailDrawer**
    - Metric details and caveats.

12. **ExperimentMatrix**
    - Objective/dataset matrix linked to result details.

13. **LimitationsCallout**
    - Clearly visible unresolved result or caveat.

14. **CitationPanel**
    - Approved bibliographic metadata only.

15. **MotionPreferenceControl**
    - Pause motion and respect system preferences.

16. **PublicContentSearch**
    - Searches only curated site content.

---

# 19. Curated Content Model

All website metrics and claims should be stored in a dedicated public content layer, separate from research implementation files.

Example TypeScript types:

```ts
type EvidenceStatus =
  | "measured"
  | "modelled"
  | "inconclusive"
  | "target-not-met"
  | "not-evaluated"
  | "illustrative";

type MetricRecord = {
  id: string;
  title: string;
  dataset: "VitalDB" | "WEAR" | "eICU";
  value: number;
  unit: string;
  target?: {
    operator: "<" | "<=" | ">" | ">=";
    value: number;
    unit: string;
  };
  evidenceStatus: EvidenceStatus;
  evaluationContext: string;
  baseline?: string;
  confidenceInterval?: {
    lower: number;
    upper: number;
    unit: string;
  };
  interpretation: string;
  caveat: string;
  publicProvenanceLabel: string;
  reviewedAt?: string;
};
```

Data-handling rules:
- Do not ingest arbitrary repository files into this content layer.
- Do not use a GitHub API client to populate pages.
- Do not fetch `raw.githubusercontent.com`.
- Do not mirror internal file trees or logs.
- Validate curated data with Zod during build/test.
- Keep all metric definitions and caveats beside the metric.
- Add a review checklist before any public content update.
- Do not place secrets or restricted data in client-side bundles.
- Do not assume that data is safe merely because it is JSON.

---

# 20. Privacy and Repository Non-Exposure Requirements

These are hard requirements.

## 20.1 Prohibited content
Never display or expose:
- GitHub repository contents, source files, source code, directory trees, branches, commits, issues, or internal file names.
- Raw experiment logs, terminal output, scratch paths, private notes, or environment details.
- Patient-level records, identifiers, feature arrays, raw medical signals/images, or row-level predictions.
- Per-hospital small-cell counts or sensitive cohort breakdowns.
- Credentials, tokens, API keys, private endpoints, or machine-specific paths.
- Unreviewed paper drafts or unreleased supplementary material.
- Any restricted dataset extract or artifact covered by a data-use agreement.

## 20.2 Technical controls
- No GitHub SDK or GitHub API request from the public client.
- No runtime repository scraping.
- No automatic repository-backed search.
- No hidden iframe or embedded repository view.
- No raw-source or log viewer.
- No public static folder copied wholesale from the research repository.
- No service that returns internal files to the browser.
- Use an allowlist of approved public pages, figures, and curated metric records.
- Inspect the production build output for accidental inclusion of restricted files.
- Check network requests in browser dev tools before launch.
- Use secret scanning and dependency checks in the deployment workflow.
- Do not treat obfuscation as a security control.

## 20.3 Public provenance without internal leakage
A metric may have a provenance label such as:
“Source: approved final evaluation summary; reviewed for public release.”

Do not display internal paths or private repository metadata. If a public paper or officially released supplementary document is approved, link directly to that specific public resource after review.

---

# 21. Accessibility Requirements

Target WCAG 2.2 AA where feasible and test the final experience.

- Semantic landmarks and heading hierarchy.
- Keyboard navigation for every control.
- Visible focus indicator.
- Accessible names for icon-only controls.
- Correct tab, dialog, accordion, and menu behavior.
- Text contrast suitable for dark backgrounds.
- No information communicated by colour alone.
- Chart descriptions and tabular alternatives.
- Captions or text summaries for animated concepts.
- 3D interactions with non-drag alternatives.
- Reduced-motion support.
- No flashing or rapid repeated movement.
- Touch targets sized for mobile use.
- Correct language metadata.
- Error states described in text.
- Screen-reader announcements for filter changes without excessive chatter.

---

# 22. Responsive and Performance Requirements

## 22.1 Responsive behavior
- Desktop: full 3D architecture and multi-column research layout.
- Tablet: simplified 3D scene, fewer decorative details, stacked side panels.
- Mobile: static/low-cost 3D mode by default where appropriate, accessible 2D alternative, vertically stacked metrics, horizontally scrollable tables only when necessary and with clear affordance.
- Keep chart labels readable.
- No essential hover-only content.

## 22.2 Performance targets
Targets are engineering goals, not claims to publish:
- Avoid loading Three.js on pages that do not need it.
- Lazy-load the 3D scene.
- Keep the initial route lightweight.
- Use optimized local images and compressed approved figures.
- Avoid large video backgrounds.
- Pause offscreen animation.
- Minimize layout shift.
- Aim for good Core Web Vitals on mid-range mobile hardware.
- Provide a stable fallback if WebGL or GPU acceleration is unavailable.

## 22.3 SEO and sharing
- Unique title and description per route.
- Open Graph metadata with an approved static preview image.
- Structured metadata only where accurate.
- Sitemap and robots configuration appropriate for public pages.
- No metadata exposing internal project paths or private artifact names.
- Public page URLs should remain stable.

---

# 23. Testing and Quality Assurance

## 23.1 Unit tests
- Metric target classification.
- Evidence-status labels.
- Privacy budget total calculations.
- Unit conversion and rounding.
- Confidence interval display.
- Dataset and metric filters.
- Data schema validation.
- Interpretation/caveat presence for every result.

## 23.2 Component tests
- Metric card renders value, unit, status, target, and caveat.
- Filters update chart and summary consistently.
- Drawer opens, closes, and restores focus.
- Tabs work by keyboard.
- 3D fallback appears when WebGL is unavailable.
- Reduced-motion preference stops automatic animation.
- CSV/JSON export, if implemented, contains only approved aggregate summaries.

## 23.3 End-to-end tests
- Navigate all public pages.
- Use the architecture with keyboard and pointer.
- Pause and resume motion.
- Switch between 3D and 2D.
- Filter results by dataset and metric.
- Open and close result details.
- Check mobile viewport layouts.
- Check that no horizontal overflow or inaccessible control occurs.
- Verify that the site makes no requests to GitHub APIs or raw repository URLs.
- Inspect network traffic for accidental calls to internal services.
- Inspect built assets for restricted data or source files.

## 23.4 Content validation tests
Fail the build if:
- A metric lacks an evidence status.
- A modelled result lacks a modelling caveat.
- An inconclusive result is rendered as a success.
- A target-not-met result is presented as achieved.
- A confidence interval is malformed.
- A metric has no unit or evaluation context.
- A restricted artifact is placed in the public assets directory.
- A citation contains unverified publication metadata.

---

# 24. Suggested Project Structure

This is the structure of the **new website project only**. It is not a mirror of the research repository.

```text
pp-hfm-observatory/
├── public/
│   ├── brand/
│   ├── approved-figures/
│   └── social-preview/
├── src/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── research/
│   │   ├── architecture/
│   │   ├── datasets/
│   │   ├── privacy/
│   │   ├── results/
│   │   ├── experiments/
│   │   ├── reproducibility/
│   │   ├── limitations/
│   │   ├── publication/
│   │   ├── accessibility/
│   │   └── not-found.tsx
│   ├── components/
│   │   ├── layout/
│   │   ├── motion/
│   │   ├── three/
│   │   ├── architecture/
│   │   ├── charts/
│   │   ├── metrics/
│   │   ├── privacy/
│   │   └── content/
│   ├── content/
│   │   ├── research.ts
│   │   ├── datasets.ts
│   │   ├── metrics.ts
│   │   ├── privacy.ts
│   │   ├── experiments.ts
│   │   ├── limitations.ts
│   │   └── publication.ts
│   ├── lib/
│   │   ├── validation.ts
│   │   ├── metric-status.ts
│   │   ├── accessibility.ts
│   │   └── format.ts
│   └── styles/
├── tests/
│   ├── unit/
│   ├── components/
│   └── e2e/
├── README.md
└── package.json
```

Do not copy the research repository into this folder. Only add assets that have been individually reviewed and approved for public release.

---

# 25. Implementation Roadmap

## Phase 1 — Content and design foundation
- Create the standalone web application.
- Define typography, colours, spacing, and responsive shell.
- Create the curated content model.
- Validate all approved metrics and wording.
- Build navigation, footer, cards, and evidence labels.
- No repository integration.

## Phase 2 — Research narrative
- Build the homepage.
- Build research, datasets, privacy, and limitations pages.
- Add approved aggregate data and caveats.
- Add publication page with verified metadata only.

## Phase 3 — Results explorer
- Build charts, filters, metric definitions, target lines, and confidence intervals.
- Add accessible data-table alternatives.
- Add result detail drawer.
- Add tests for all classifications and values.

## Phase 4 — Three.js architecture
- Build the device–edge–cloud scene.
- Add layer selection, guided steps, flow controls, reset, and pause.
- Add a 2D SVG fallback.
- Implement reduced motion and lazy loading.
- Test on mobile and low-performance hardware.

## Phase 5 — Polish and validation
- Add restrained page transitions and section reveals.
- Add SEO and social preview.
- Run accessibility, responsive, performance, content, and privacy checks.
- Inspect network traffic and production bundle.
- Confirm no repository content or restricted data is present.

## Phase 6 — Release review
- Verify all numeric values against the approved final evaluation record.
- Confirm paper metadata and permissions.
- Confirm that every figure is approved for public use.
- Run the repository non-exposure checklist.
- Publish the website independently.

---

# 26. Definition of Done

The project is complete only when all of the following are true:

- [ ] The site is a standalone browser-based website.
- [ ] The website has all required routes.
- [ ] The visual design is consistent and responsive.
- [ ] The architecture page includes an interactive Three.js scene.
- [ ] A fully usable 2D fallback exists.
- [ ] Motion respects reduced-motion preferences.
- [ ] Results filters update the charts, tables, and interpretations consistently.
- [ ] Every displayed result includes a unit, context, status, and caveat.
- [ ] Modelled energy results are visibly identified as simulator estimates.
- [ ] eICU utility findings preserve their inconclusive/target-miss distinctions.
- [ ] eICU update delivery at the two-edge configuration is not misrepresented as meeting target.
- [ ] Membership-inference results are not described as proof of zero leakage.
- [ ] No patient-level or restricted dataset data is exposed.
- [ ] No repository source, file tree, branch, commit, log, or internal artifact is displayed.
- [ ] The client makes no requests to GitHub or raw repository URLs.
- [ ] No secrets or private endpoints are in the public bundle.
- [ ] All claims and publication metadata are verified.
- [ ] Keyboard, screen-reader, reduced-motion, and mobile behavior are tested.
- [ ] Production assets and network requests have been inspected.
- [ ] The limitations page is easy to discover.
- [ ] The website does not claim clinical readiness without independent evidence.

---

# 27. Final Product Summary

Build **PP-HFM Research Observatory** as an independent, public-facing scientific website. It combines a clear research narrative, interactive results explorer, privacy budget visualizer, dataset comparison, limitations, reproducibility guidance, and a Three.js device–edge–cloud architecture experience.

The 3D experience should make the system easier to understand, while accessible text and 2D diagrams preserve the same meaning. Charts should communicate evidence honestly. Simulated results, inconclusive findings, and unmet targets must remain clearly distinguished.

**Most important constraint:** the website is not a frontend for the research repository. It is a separately curated public research presentation. It must never display or fetch repository contents, source code, raw logs, restricted data, patient-level records, internal paths, or unreleased artifacts. Only reviewed, approved, aggregate research summaries and approved public assets may be included.
