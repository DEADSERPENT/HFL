from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY = RGBColor(0x1A, 0x3A, 0x5C); GREEN = RGBColor(0x0A, 0x6B, 0x2E)
RED = RGBColor(0x9C, 0x20, 0x20); AMBER = RGBColor(0x8A, 0x5A, 0x00)
GREY = RGBColor(0x55, 0x55, 0x55)

doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = Cm(1.7); s.left_margin = s.right_margin = Cm(1.6)
n = doc.styles['Normal']; n.font.name = 'Calibri'; n.font.size = Pt(9.5)
n.paragraph_format.space_after = Pt(4); n.paragraph_format.line_spacing = 1.08

def shade(cell, hexcolor):
    el = OxmlElement('w:shd'); el.set(qn('w:val'), 'clear'); el.set(qn('w:fill'), hexcolor)
    cell._tc.get_or_add_tcPr().append(el)

def para(text="", size=9.5, bold=False, italic=False, color=None, space=4, align=None):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(space)
    if align: p.alignment = align
    r = p.add_run(text); r.font.size = Pt(size); r.bold = bold; r.italic = italic
    if color: r.font.color.rgb = color
    return p

def rich(parts, size=9.5, space=4):
    """parts = [(text, bold, italic, color), ...]"""
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(space)
    for t, b, i, c in parts:
        r = p.add_run(t); r.font.size = Pt(size); r.bold = b; r.italic = i
        if c: r.font.color.rgb = c
    return p

def head(text, level=1):
    sizes = {1: 15, 2: 11.5, 3: 10}
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12 if level == 1 else 9)
    p.paragraph_format.space_after = Pt(4); p.paragraph_format.keep_with_next = True
    r = p.add_run(text); r.bold = True; r.font.size = Pt(sizes[level]); r.font.color.rgb = NAVY
    if level == 1:
        pPr = p._p.get_or_add_pPr(); bd = OxmlElement('w:pBdr'); bt = OxmlElement('w:bottom')
        bt.set(qn('w:val'), 'single'); bt.set(qn('w:sz'), '8'); bt.set(qn('w:color'), '1A3A5C')
        bt.set(qn('w:space'), '2'); bd.append(bt); pPr.append(bd)
    return p

def callout(label, text, kind="info"):
    fill = {"info": "EEF3F8", "good": "EDF6EF", "bad": "FBEEEE"}[kind]
    col  = {"info": NAVY, "good": GREEN, "bad": RED}[kind]
    t = doc.add_table(rows=1, cols=1); t.style = 'Table Grid'
    c = t.rows[0].cells[0]; shade(c, fill)
    p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(2)
    r = p.add_run(label); r.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = col
    p2 = c.add_paragraph(); p2.paragraph_format.space_after = Pt(1)
    r2 = p2.add_run(text); r2.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(3)
    return t

def table(headers, rows, widths=None, fs=8.3):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; shade(c, "1A3A5C")
        p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(1)
        r = p.add_run(str(h)); r.bold = True; r.font.size = Pt(fs); r.font.color.rgb = RGBColor(255,255,255)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            if ri % 2 == 1: shade(cells[i], "F2F6FA")
            p = cells[i].paragraphs[0]; p.paragraph_format.space_after = Pt(1)
            txt, col, bold = (val if isinstance(val, tuple) else (val, None, False))
            r = p.add_run(str(txt)); r.font.size = Pt(fs); r.bold = bold
            if col: r.font.color.rgb = col
    doc.add_paragraph().paragraph_format.space_after = Pt(3)
    return t

def small(text): para(text, size=8.2, color=GREY, space=6)
def pagebreak(): doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

P = (lambda s: (s, GREEN, True)); F = (lambda s: (s, RED, True)); W = (lambda s: (s, AMBER, True))

from docx.enum.section import WD_SECTION

def mono(text, size=7.6):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text); r.font.name = 'Consolas'; r.font.size = Pt(size)
    return p

def parthead(text):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8); p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=1); t.style = 'Table Grid'
    c = t.rows[0].cells[0]; shade(c, "1A3A5C")
    pp = c.paragraphs[0]; pp.paragraph_format.space_after = Pt(2)
    r = pp.add_run(text); r.bold = True; r.font.size = Pt(12.5)
    r.font.color.rgb = RGBColor(255, 255, 255)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ══════════════════════════ TITLE ══════════════════════════
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
r = p.add_run("Hierarchical Federated Learning for Privacy-Aware,\nLow-Latency Multimodal IoT Systems")
r.bold = True; r.font.size = Pt(17); r.font.color.rgb = NAVY
para("DETAILED TECHNICAL REPORT", size=11, bold=True, color=NAVY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space=3)
para("Complete record: what was built, what was measured, what failed, and what remains",
     size=10, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space=6)
para("Samartha H V (251580130019)  ·  Guide: Dr. Shreyas J  ·  Industry: Mr. Tejas J, Capgemini\n"
     "School of Computer Engineering, MIT Bengaluru (MAHE)  ·  January–May 2026",
     size=8.8, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, space=2)
para("Status as of 5 September 2026", size=8.8, italic=True, color=GREY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space=10)

callout("How to read this document.",
 "HFL.pdf is the 11-page executive summary of the same project. THIS document is the full "
 "record: every experiment with its configuration and measured values, the algorithms and why "
 "each was chosen, theory against practice, the complete findings register, and the "
 "objective-by-objective achievement status. Where the two disagree on wording, the numbers here "
 "are the authority — all are read from measured artifacts on disk.", "info")

# ══════════════════════════ PART I ══════════════════════════
parthead("PART I — WHAT THIS RESEARCH IS")

head("1.  The problem, in plain terms")
para("Hospitals hold data that would train good clinical models, but consent regimes and "
     "data-protection law forbid pooling it. Federated learning removes that obstacle: each site "
     "trains locally and transmits model updates rather than records. A hierarchical organisation "
     "— device → edge → cloud — further relieves the wide-area link that otherwise "
     "constrains such systems.")
para("Neither, however, supplies a privacy guarantee. And the guarantee such systems conventionally "
     "report is stated over training RECORDS, while the guarantee a clinical setting actually "
     "requires concerns INDIVIDUALS. Where a single episode of care yields many records, those two "
     "statements differ for every participant in the dataset.")

head("2.  The single central idea")
callout("The claim the whole project rests on.",
 "The unit of privacy is a first-class design parameter of federated learning, and its utility "
 "cost is predictable from the structure of the data — specifically from k, the number of "
 "records each individual contributes.", "good")
para("Almost every private federated learning paper reports a single number for the price of "
     "privacy: \"ε = 1 costs us 3% accuracy.\" That number is treated as a property of the method. "
     "This research shows it is not. It is a property of the method APPLIED TO A PARTICULAR DATA "
     "STRUCTURE, and the governing variable of that structure is how many records each protected "
     "individual contributes. Change k and the price changes — systematically, and in a "
     "direction that can be predicted in advance.")

head("3.  The architecture")
mono(
"+---------------------------------------------------------------+\n"
"|  LAYER 3 — CLOUD                                              |\n"
"|  Global aggregation · model distribution · privacy accounting |\n"
"+------------------------------^--------------------------------+\n"
"                               |  wide-area link, exercised ONCE\n"
"                               |  per several local rounds\n"
"+------------------------------+--------------------------------+\n"
"|  LAYER 2 — EDGE SERVERS  (x2)                                 |\n"
"|  Partial FedAvg · gradient compression · filtering            |\n"
"|  (the tier that relieves the uplink)                          |\n"
"+------^---------------------------------------^----------------+\n"
"       |                                       |\n"
"+------+-------------+                +--------+---------------+\n"
"| LAYER 1 — DEVICE   |                | LAYER 1 — DEVICE       |\n"
"| Multimodal sensing |      . . .     | Multimodal sensing     |\n"
"| Local DP training  |                | Local DP training      |\n"
"| PATIENT-grouped    |                | PATIENT-grouped        |\n"
"| gradient clipping  |                | gradient clipping      |\n"
"+--------------------+                +------------------------+")
small("Fig. 1 — The three-tier topology. The distinguishing feature sits at LAYER 1: gradients "
      "are grouped by individual BEFORE the clipping bound is applied, so the guarantee is a "
      "statement about people from the outset rather than something recovered afterwards by a "
      "ruinous group-privacy conversion.")

head("4.  The datasets")
table(["Property", "VitalDB (primary)", "WEAR (secondary)"], [
 ["Domain", "Intraoperative clinical", "Wearable IoT"],
 ["Modality A", "9 intraop numeric trends + 9 observed-masks, 10 min @ 0.5 Hz",
  "12-ch accelerometer (4 sensors × 3 axes), 2 s @ 50 Hz"],
 ["Modality B", "34-d preoperative clinical + laboratory vector",
  "2048-d two-stream I3D egocentric video features, same 2 s"],
 ["How paired", "Same patient, same second (Vital Recorder, one operation)",
  "Hardware-synchronised (same person, same instant)"],
 ["Train / test windows", "34,044 / 7,360", "26,424 / 5,969"],
 ["Individuals", "6,257 patients across 48,712 windows", "22 participants"],
 ["Records per individual (k)", ("mean 7.79, median 8, max 8 — 100% contribute >1 window", None, True),
  "one client per participant"],
 ["Federated clients", "9 clients over 2 edge servers", "22 clients"],
 ["Role in the study", "Headline results; all privacy claims", "Fast iteration; systems generalisation"],
])
callout("Why the k row is the premise of the whole programme.",
 "Not one patient in VitalDB contributes only a single record. So for EVERY individual in the "
 "dataset, a record-level guarantee and a patient-level guarantee are different statements. WEAR "
 "cannot support any patient-level claim: 22 individuals, one client each, so the client-level "
 "and individual-level units coincide and the privacy unit is degenerate.", "info")

head("5.  What was designed that is genuinely ours")
head("5.1  Patient-level guarantee by construction", 3)
para("The gradients of one individual's records are accumulated BEFORE the clipping bound is "
     "applied. That individual's influence on the released model is therefore bounded irrespective "
     "of how many records they contributed, and accounting performed at the same granularity "
     "yields a budget that is a statement about people by construction — not one recovered "
     "afterwards through a group-privacy conversion that would be unusable at k ≈ 8.")
head("5.2  Accounting practices specified to be checkable", 3)
para("Two practices are specified in enough detail to be verified from outside, because each "
     "corresponds to a failure mode that is invisible in a training log:")
para("(a) The noise scale is calibrated to satisfy the budget for EVERY CLIENT SIMULTANEOUSLY, "
     "rather than for a representative one, so that interposing the edge tier is reflected in the "
     "reported figure.", space=2)
para("(b) The cost of releasing the conformal calibration quantile is COMPOSED INTO the budget "
     "rather than omitted from it. Measured: ε = 0.7705 (training) + 0.2000 (conformal) = 0.9705.")
head("5.3  Separation of representation from private adaptation", 3)
para("Encoders are pretrained on a population disjoint from every client and then frozen; only a "
     "compact fusion head is privatised. This is what makes ε ≤ 1 viable at all.")
head("5.4  An audit that can return an informative negative", 3)
para("The guarantee is audited by mounting membership inference AT THE LEVEL OF THE INDIVIDUAL, "
     "under both a threshold attack and a likelihood-ratio attack (LiRA), with every attack "
     "reported alongside a positive control on a configuration known to memorise. The control is "
     "what makes a null attributable to the defence rather than to an inadequate adversary. This "
     "discipline is one of the most defensible things the project produced — it is what "
     "allowed a refuted hypothesis to remain publishable.")
head("5.5  The k-scaling law", 3)
para("The price of the individual-level guarantee is shown to be a function of individual "
     "contribution, with a built-in control at k = 1. This is the headline finding; see Part II §8.")

head("6.  Algorithms used, and why")
table(["Algorithm", "Where used", "Why this one"], [
 ["FedAvg", "Aggregation at edge and cloud",
  "The standard. Simple, well understood, the correct baseline. Anything more exotic must justify itself against it."],
 ["DP-SGD (Opacus)", "Private training of the fusion head",
  "The only mechanism giving a formal, composable guarantee. Everything else is heuristic."],
 [("Patient-level DP-SGD (our variant)", None, True), "The core privacy mechanism",
  ("Standard DP-SGD clips PER SAMPLE. Our sample is a 10-minute window and every patient gives "
   "about 8 of them. Clipping per window protects windows, not people. We group by patient first, "
   "then clip.", None, True)],
 ["Top-k sparsification (20%)", "Gradient compression", "Sends only the 20% largest updates. 5× reduction."],
 ["8-bit quantisation", "Gradient compression", "Another 4× on top of sparsification. Combined 20×."],
 ["Error feedback", "Compression accumulator",
  "Compression discards information. Error feedback stores what was dropped and adds it back next round, so accuracy is not lost."],
 ["Head-only DP fine-tuning", "The training recipe",
  "Freeze encoders, privatise only the fusion head (26% of parameters). This is what made ε ≤ 1 work at all."],
 ["Multi-scale 1D-CNN + BiGRU + attention", "Signal encoder (modality A)",
  "Captures patterns at several time scales. Uses DP-compatible layers — no BatchNorm, which breaks DP-SGD."],
 ["Conformal prediction + DP quantile release", "Coverage guarantee",
  "Gives P(true label ∈ predicted set) ≥ 1−α, and the release cost is charged to the same budget."],
])

head("7.  What was built")
table(["Component", "File", "What it does"], [
 [("Patient-level DP engine", None, True), "privacy/patient_dp.py",
  ("THE CORE CONTRIBUTION. Groups gradients by patient before clipping.", None, True)],
 ["DP-SGD engine", "privacy/dp_engine.py", "Opacus wrapper with extended RDP orders so tight budgets are reachable"],
 ["Adaptive DP engine", "privacy/sadp_engine.py", "Per-group budget split. Retained as a negative result"],
 ["HFL training engine", "training/hfl_trainer.py", "The three-tier training loop: device → edge → cloud"],
 ["Encoder pretraining", "training/pretrain_encoders.py", "Non-private pretraining, deterministic mode and public-data mode"],
 ["Baseline suite B0–B5", "training/baselines.py", "Centralised, local-only, FedAvg, FedProx, DP-FedAvg, MOON"],
 ["Multimodal model", "architecture/hfl_mm_model.py", "Two encoders plus a fusion head"],
 ["Signal encoder", "architecture/fedmamba_hc.py", "Multi-scale CNN + BiGRU + attention, DP-compatible"],
 ["Gradient compressor", "utils/compression.py", "Top-k + 8-bit + error feedback. 20× compression"],
 ["Conformal prediction", "utils/fedconform_hc.py", "Coverage guarantee with DP quantile release"],
 ["LiRA attack suite", "scripts/lira_attack.py", "Four attack variants, shadow models, per-patient Gaussians. The audit instrument"],
 ["k-scaling driver", "scripts/k_scaling.py", "Runs the headline experiment across k and both arms"],
 ["Attribution", "scripts/attribution.py", "Integrated gradients, with a separate seed-stability check"],
 ["ONNX export + benchmark", "deploy/", "Edge deployment artifact and timed serving path"],
])

# ══════════════════════════ PART II ══════════════════════════
pagebreak()
parthead("PART II — WHAT SUCCEEDED, AND HOW")

head("8.  The k-scaling law — the headline result")
head("E18 · Configuration", 3)
small("All 24 configurations: k ∈ {1,2,4,8} × 3 seeds × 2 arms · per-step budget and "
      "units-per-step held constant · artifact: k_scaling/vitaldb/k_scaling_vitaldb.csv")
table(["k", "Record arm AUPRC", "Patient arm AUPRC", "Gap", "95% CI", "p"], [
 ["1", "0.5015", "0.5067", "−0.0052", "[−0.0664, +0.0561]", "0.75"],
 ["2", "0.5590", "0.5084", P("+0.0507"), "[+0.0417, +0.0596]", "0.0017"],
 ["4", "0.5924", "0.5092", P("+0.0832"), "[+0.0694, +0.0971]", "0.0015"],
 ["8", "0.5955", "0.5089", P("+0.0866"), "[+0.0603, +0.1129]", "0.0049"],
])
callout("Why this result is strong — two reasons.",
 "1. IT CARRIES ITS OWN POSITIVE CONTROL. At k=1 a patient IS a record, so the two guarantees are "
 "mathematically identical and the arms MUST collapse. They do (p = 0.75). A validated null "
 "sitting inside the same experiment as the positive effects — exactly the design property "
 "the earlier membership-inference work initially lacked. It is what licenses reading the "
 "divergence at larger k as a property of the privacy unit rather than an artefact of the "
 "apparatus.\n\n"
 "2. THE MECHANISM IS ASYMMETRIC, and must be stated that way. The patient arm is essentially "
 "flat in k (AUPRC 0.4967–0.5176 at every k) while the record arm rises (0.5015 → 0.5955). "
 "The widening gap is THE RECORD ARM IMPROVING, not the patient arm degrading. Patient-level "
 "noise scales with the per-patient contribution, so extra records per patient buy the patient "
 "arm nothing.", "good")
head("The honest limits of it", 3)
para("AUROC shows the same monotone shape (+0.0006, +0.0094, +0.0133, +0.0132) but no k reaches "
     "significance — every interval includes zero. AUPRC is reported as the RESOLVING metric "
     "and AUROC as directionally consistent but underpowered at n = 3.")
para("Accuracy is pinned at 0.8005 in every patient row. That is an uncalibrated 0.5 threshold on "
     "imbalanced data, not a degenerate model (AUROC ≈ 0.835 rules out majority-class "
     "prediction). ACCURACY MUST NOT BE QUOTED for these arms.")

head("9.  Complete objective status")
table(["Objective", "Status", "How far achieved, and the explanation"], [
 ["O1 — Uplink reduction ≥ 50%", P("FULLY ACHIEVED"),
  "90.82% (VitalDB) and 96.08% (WEAR) — roughly 1.8–1.9× the target. Measured on the real "
  "compressor payload with indices included, not estimated from parameter counts. Deterministic "
  "and seed-independent, so a single run suffices as evidence. No caveat."],
 ["O1b — Round latency reduction", P("FULLY ACHIEVED"),
  "16.93% and 21.68%, measured packet-level in NS-3 on rounds where the payload actually traversed "
  "the topology. Added as an objective mid-project once packet-level measurement became available."],
 ["O2a — Privacy budget ε ≤ 1", P("FULLY ACHIEVED"),
  "ε = 0.9705 and 0.9656, and these are COMPOSED totals (training 0.7705 + conformal 0.2000), not "
  "training-only figures. Composing the conformal release is stricter than standard practice, "
  "where it is usually omitted. Caveat: end-to-end validity depends on the pretraining-disjointness "
  "issue in §17."],
 ["O2b — Accuracy loss ≤ 2 pp", W("VitalDB PASS / WEAR INCONCLUSIVE"),
  "VitalDB: −0.92 pp, CI [−2.82, +0.99] over 5 paired seeds — the point estimate is "
  "NEGATIVE, i.e. the private arm was marginally better. The defensible statement is \"no "
  "measurable cost, bounded by the interval\", not \"zero cost\". WEAR: 1.967 pp, CI [1.760, "
  "2.173] straddles the threshold; seed count pre-registered at 15 and deliberately not extended."],
 ["O3a — Latency P95 < 100 ms", P("EXCEEDED >20×"),
  "4.58 ms (VitalDB) and 1.22 ms (WEAR) over 1000 timed runs after 100 warmup, across the full "
  "serving path."],
 ["O3b — Successful updates > 99%", P("FULLY ACHIEVED"), "100% and 99.94% per-update, measured at packet level."],
 ["O4 — Energy saving ≥ 20%", P("EXCEEDED 3.6×"), "72.30% and 76.84% under the CloudSim Plus power model."],
])

head("10.  Phase 4 — simulation infrastructure")
head("E1 · NS-3 packet-level network simulation", 3)
small("NS-3 v3.46.1 · 9 IoT devices, 2 edge servers, 1 cloud · device→edge 54 Mbps, "
      "edge→cloud 1 Gbps at 5 ms · LogDistance propagation, 5 Mbps background traffic · "
      "artifacts ns3_results_{vitaldb,wear}.csv, ns3_phase5_{vitaldb,wear}.csv")
table(["Quantity", "VitalDB", "WEAR"], [
 ["Round uplink time", "33.97 s", "—"], ["Round downlink time", "26.85 s", "—"],
 ["Round latency, flat → hierarchical", "90.5 → 75.2 ms", "104.5 → 81.8 ms"],
 ["Latency reduction", "16.93%", "21.68%"],
 ["Per-update reliability (2 hops)", "100%", "99.94%"],
])
head("E2 · CloudSim Plus compute and energy simulation", 3)
small("CloudSim Plus v8.5.6 · IoT 300 MIPS / 512 MB / 1–3 W · edge 8000 MIPS / 16 GB / "
      "50–200 W · GPU overhead modelled on edge servers only")
table(["Scenario", "Energy per round", "Uplink"], [
 ["CentralizedFL", "1266.25 J", "73.85 MB"],
 ["HFL_Proposed (VitalDB)", P("−72.3%"), "see E10"],
 ["HFL_Proposed (WEAR)", P("−76.8%"), "see E10"],
])
para("A second figure of 93.5% exists from a linear bytes→Joules proxy, but under that model it is "
     "arithmetically identical to communication reduction and is NOT an independent energy "
     "measurement. Quote 72.3% / 76.8%.")

head("11.  Phase 5 — model, privacy and deployment")
head("E3 · Encoder pretraining — proxy vs rigorous", 3)
small("30 epochs, --deterministic · proxy mode = pooled FL train indices; rigorous mode = "
      "disjoint public split via --public_data")
table(["Mode", "Effect on AUROC", "Privacy validity"], [
 ["Proxy / oracle", "baseline", F("ε NOT valid end-to-end")],
 ["Rigorous disjoint public split", "−0.022", P("valid")],
])
para("A valid end-to-end guarantee costs 0.022 AUROC. That GAP is the quantity to report, not the "
     "proxy number alone. Determinism was verified: with the flag, two runs of a seed are "
     "byte-identical; without it they diverge (epoch-1 loss 1.5699 vs 1.5713) and checkpoint "
     "selection can land on a different round.")

head("E4 · Baseline suite B0–B5", 3)
small("No frozen encoders, trained from scratch · baselines/baselines_summary.csv")
table(["Baseline", "Test accuracy", "Test macro-AUC", "Note"], [
 ["B0  Centralized", "0.5787", "0.8211", "Upper reference for pooled data"],
 ["B1  Local-Only", "0.4532", "0.7511", "Lower reference, no collaboration"],
 ["B2  FedAvg", "0.6543", "0.8795", "Best non-private baseline"],
 ["B3  FedProx", "0.6570", "0.8747", "No advantage over FedAvg here"],
 ["B4  DP-FedAvg (ε≈1)", F("0.2159"), F("0.6443"), ("COLLAPSES. The like-for-like DP reference", None, True)],
 ["B5  MOON", "0.3934", "0.7418", "Underperforms on this task"],
])

head("E5 · Head-only DP fine-tuning — the ε=1 collapse fix", 3)
small("20 rounds, 5 edge rounds · δ=1e-5, C=1.0 · head = 560,645 / 2,157,766 params (26.0%) · 3 seeds")
table(["Recipe", "σ", "Test AUC", "Round time"], [
 ["End-to-end DP-SGD", "11.3281", F("0.562"), "1046 s"],
 ["Head-only DP fine-tuning", "11.3281", P("0.8742 ± 0.0072"), "50 s"],
])
callout("Methodological turning point.",
 "For roughly three weeks the project was blocked: at ε = 1 the model collapsed to near-random "
 "and Objective 2 was unreachable. The resolution was head-only DP fine-tuning.\n\n"
 "THE NOISE WAS NEVER THE REDUCIBLE QUANTITY. σ = 11.3281 is identical in both rows. What "
 "changed is the OPTIMISATION GEOMETRY — a near-linear probe over frozen pretrained "
 "features tolerates σ ≈ 11.3; end-to-end training from scratch does not. Test AUC moved "
 "0.562 → 0.8742, and each round ran ~20× faster.\n\n"
 "PROVENANCE NOTE: the specific AUC figures here were obtained on the legacy dataset later "
 "withdrawn. The MECHANISM transferred intact and is confirmed on VitalDB by O2b = −0.92 pp. "
 "Cite the mechanism here, and cite O2b for the number.", "good")

head("E6 · ε sweep, end-to-end recipe (SUPERSEDED)", 3)
para("Characterises the BROKEN recipe. Retained only as the \"without our fix\" arm. Must not be "
     "presented as the proposed method.")

head("E7 · ε sweep, rigorous head recipe", 3)
small("ε ∈ {0.5, 1, 2, 4, 8, ∞} · 10 rounds, head recipe · epsilon_sweep_rigorous/vitaldb/")
table(["ε", "σ", "AUROC", "AUPRC"], [
 ["0.5", "5.92", "0.8287", "0.5110"], ["1", "3.24", "0.8319", "0.5464"],
 ["2", "1.88", "0.8323", "0.5381"], ["4", "1.21", "0.8356", "0.5590"],
 ["8", "0.85", "0.8342", "0.5544"], ["∞ (non-private)", "—", "0.8158", "0.5204"],
])
para("Utility is FLAT from ε=0.5 to ε=8, and every private arm beats the non-private one. DP is "
     "acting as a regulariser on this task. The utility floor is below ε=0.5 — lower than the "
     "budget the system actually ships at.")

head("E8 · Objective 2b — multi-seed accuracy cost", 3)
small("30 rounds, head recipe, paired seeds · VitalDB n=5, WEAR n=15 (both pre-registered)")
table(["Dataset", "Cost (pp)", "95% CI", "Verdict"], [
 ["VitalDB", "−0.92", "[−2.82, +0.99]", P("PASS")],
 ["WEAR", "1.967", "[1.760, 2.173]", W("INCONCLUSIVE")],
])

head("E9 · SADP — adaptive per-group privacy budget", 3)
para("Tests whether splitting the budget across groups beats a uniform allocation at equal total ε.")
callout("NEGATIVE RESULT.",
 "It runs correctly and UNDERPERFORMS UNIFORM DP BY CONSTRUCTION. The cross-group composition tax "
 "drives σ from 11.3 to 70. Retained as a characterised negative result, not a claimed "
 "contribution. The transferable lesson: splitting a budget across groups is paid for at a "
 "punitive rate under composition.", "bad")

head("E10 · Gradient compression and uplink measurement", 3)
small("top-20% sparsity × 8-bit → 20× nominal · error-feedback accumulator · uplink_measured_*.json")
table(["Measurement", "Bytes per round"], [
 ["Full-model FP32 FedAvg", "258,931,920"],
 ["Head-only, uncompressed", "67,277,400"],
 ["Observed, post-fix", P("16,821,300")],
])
para("DEFECT FOUND AND FIXED: the compressor took a fixed k = numel × sparsity of EVERY float "
     "tensor, so frozen encoders — whose delta is exactly zero — still contributed 20% of "
     "their elements to every payload as explicit zeros. Omitting all-zero tensors and capping k at "
     "the nonzero count accounted for a 78.87% reduction on its own.")
para("The fix was PROVEN not to alter learning: the dense path is bit-identical to the previous "
     "implementation — indices, quantised values, bounds and the error-feedback accumulator "
     "all match exactly over five rounds against a verbatim copy of the old code. A seed re-run "
     "against an existing checkpoint isolated the compressor as the only change, moving AUC by 0.0001.")

head("E11 · ONNX export and inference latency", 3)
small("1000 timed runs after 100 warmup, batch 1 · path = preprocessing → ONNX forward → "
      "conformal set → serialise · inference_latency/latency_summary.csv")
table(["Precision", "Provider", "Model", "Inference P95", "Conformal", "Total P95", "QoS"], [
 ["FP32", "CPU", "10.64 MB", "13.259", "0.079", "16.363 ms", P("PASS")],
 ["FP32", "GPU (CUDA)", "10.64 MB", "20.088", "0.096", "22.476 ms", P("PASS")],
 ["INT8", "CPU", "6.55 MB", "27.877", "0.090", "31.028 ms", P("PASS")],
 ["INT8", "GPU (CUDA)", "6.55 MB", "70.020", "0.112", "73.150 ms", P("PASS")],
], fs=7.8)
callout("The result that matters for the paper's argument.",
 "THE PRIVACY APPARATUS COSTS NOTHING AT SERVING TIME. The conformal set construction that carries "
 "the coverage guarantee occupies 0.68% of the inference path, and the private mechanism occupies "
 "NONE of it — its noise is applied to gradients during training and adds no operation to "
 "serving. The standing objection that a privacy apparatus is too heavy for a latency-bound "
 "deployment is therefore answered by measurement rather than by argument.\n\n"
 "CAVEAT RETAINED FOR HONESTY: the preprocessing stage synthesises tensors rather than reading "
 "real sensors and disks, so that figure is a FLOOR. Describe the end-to-end number as \"compute "
 "latency\", not \"glass-to-glass latency\". With a >20× margin the verdict is not endangered.", "info")

head("E12 · INT8 quantisation for edge deployment", 3)
callout("NEGATIVE RESULT.",
 "INT8 is 1.90× SLOWER on CPU and 3.25× SLOWER on GPU than FP32, and misses the 4 MB size target "
 "at 6.55 MB. Two independent causes were identified: dynamic quantisation only accelerates "
 "MatMul/Gemm, while this model's cost is dominated by convolutions and a recurrent path; and on "
 "CUDA the quantised ops have no GPU kernel and fall back to CPU — the runtime reports 3180 "
 "Memcpy nodes inserted, which is exactly the 3.25× penalty.\n\n"
 "DEPLOY THE FP32 ARTIFACT. If size later matters more than latency, the correct lever is "
 "static/QDQ quantisation or quantisation-aware training.", "bad")

head("E13 · Patient-level vs record-level DP", 3)
small("Both arms at matched budget · 5 seeds · patient_dp/vitaldb/ · VitalDB: 48,712 windows "
      "/ 6,257 cases, mean 7.79 windows per case, 100% of cases contribute more than one window")
para("The upgrade is priced at 1.77× σ. Because every patient contributes more than one record, a "
     "record-level and a patient-level guarantee are DIFFERENT STATEMENTS for every individual in "
     "the dataset. This is the premise the whole project rests on, and it is measured, not assumed.")

head("E20 · Feature attribution — what the model uses", 3)
small("Integrated gradients, midpoint rule, 64 steps, completeness 6.06% · 20 runs across 5 "
      "recipes × 2 baselines, plus a separate seed-stability check")
table(["Recipe", "Mask share of attribution"], [
 ["full_dp", "28.2%"], ["patient-DP", "22.0%"], ["sample-DP", "21.6%"],
 ["full_nodp", "19.9%"], ["head_nodp", "15.8%"],
])
para("DP shifts the model's attention toward MISSINGNESS. Under noise the model leans more on WHICH "
     "measurements exist than on their values, monotonically with how much DP is applied. Rank "
     "correlation stays ρ = 0.95 head-only private vs not. Evidence, not proof, for claim N-7: "
     "masks carry 22.0% of attribution mass over 5 seeds, and ART_MBP_observed alone is 4.99%.")

head("E21 · Objective verification O1–O4", 3)
para("All quantified objectives resolved from measured artifacts with no hardcoded values. Results "
     "in §9 above. VitalDB 7/7 PASS; WEAR 6 PASS + 1 INCONCLUSIVE.")

head("E22 · Component ablation A0–A6", 3)
small("3 seeds per arm · VitalDB · phase6/vitaldb/ablation.csv")
table(["Arm", "Configuration", "AUROC", "AUPRC", "ε", "Uplink"], [
 ["A0", "Full system", "0.8541 ± 0.0035", "0.5960", "0.7705", "251.97 MB"],
 ["A1", "No C1 — flat tier (no edge)", "0.8484 ± 0.0057", "0.5911", "0.7704", "50.40 MB"],
 ["A2", "No C2 — no DP", "0.8307 ± 0.0060", "0.5136", "∞", "251.97 MB"],
], fs=8.0)
para("A1's uplink is not comparable — a flat topology counts traffic differently. A2 is "
     "instructive: removing DP makes the model WORSE on AUPRC (0.5136 vs 0.5960), consistent with "
     "the E7 finding that DP regularises this task.")
callout("A defect that invalidated four arms until 2026-08-16.",
 "A1–A4 had never produced a result until four silent defects were fixed: a dead --local_epochs "
 "argument, a uint8-hardcoded quantiser, a summary reading test_* from a CSV holding only val_*, "
 "and a 1e-4 verdict threshold. The 8-bit path was bit-identical after the fix, so Phase 5 results "
 "stand unchanged.", "bad")

head("E23 · NS-3 stress tests", 3)
small("Round sweeps r30 / r50 / r70 / r90 / r105 / r120 / r250, plus packet-error sweeps · both "
      "datasets · ns3/stress*.csv, 17 files")
para("The system holds across round counts up to 250. This sweep also exposed a DEFINITION DEFECT: "
     "update reliability had been computed as hop_success ^ n_rounds — the probability that ALL "
     "rounds succeed — which decays with round count, so any system fails a \">99%\" target "
     "for a long enough run. Per-update reliability is 99.8001%; the whole-run figure is still "
     "emitted under the distinct name run_reliability_all_rounds_pct.")

head("12.  Multimodal fusion")
head("E19 · Modality ablation", 3)
small("8 epochs · VitalDB 5 seeds (34,044 train / 7,360 test), WEAR 2 seeds · ablation_{vitaldb,wear}.json")
table(["Dataset", "Modality A", "Modality B", "A only", "B only", "Fused", "Gain"], [
 ["VitalDB", "Intraop signals", "Preop clinical + labs", "0.8283", "0.7680", P("0.8653"), P("+0.0370")],
 ["WEAR", "Accelerometer", "Egocentric video features", "0.9976", "0.9957", "0.9980", W("+0.0004")],
], fs=8.0)
callout("Why the multimodal design matters to the privacy question.",
 "This is the part that is easy to miss. Two modalities mean the model has TWO SOURCES OF EVIDENCE "
 "ABOUT THE SAME PATIENT. That makes the patient — not the window — the natural unit of "
 "both learning and disclosure. A single patient's identity is carried by the COMBINATION of their "
 "signals and their clinical record. Protecting one window of one modality protects almost nothing "
 "about that person.\n\n"
 "So multimodality is not decoration here. It is the reason the unit-of-privacy question has teeth "
 "in the first place.", "info")
para("HONEST LIMITATION: the fusion claim rests on ONE dataset. WEAR structurally cannot "
     "corroborate it — its better single modality already reaches 0.9976 and the script's own "
     "verdict reads \"CEILING\". Reported as a finding rather than hidden: on some IoT tasks a "
     "single modality suffices, so multimodal federated learning is not universally motivated.")

head("13.  The privacy audit machinery")
para("A full LiRA implementation was built with four attack variants, per-patient IN/OUT Gaussians "
     "fitted from 16 shadow models per arm, and TPR reported at 1% and 0.1% FPR alongside AUC "
     "— because average AUC hides the confident identification tail that is the clinical "
     "disclosure.")
callout("The single decision that saved the negative result.",
 "A PRE-REGISTERED GATE was set BEFORE running: the attack had to exceed 0.5847 on a configuration "
 "known to memorise, or its nulls would be inadmissible. It reached 0.6277 [0.5905, 0.6649]. The "
 "gate cleared. That decision is what converted the subsequent negative result from a hole in the "
 "paper into a reportable finding.", "good")

# ══════════════════════════ PART III ══════════════════════════
pagebreak()
parthead("PART III — WHAT FAILED, AND HOW")

head("14.  The refuted central hypothesis (N-A)")
para("The project's original central prediction was that record-level DP would leave patients "
     "exposed (attack AUC ≈ 0.70) while patient-level DP defended them (≈ 0.50). A gap of "
     "roughly 0.20 was predicted.")

head("E14 · Membership inference — loss threshold sweep", 3)
small("Patient-aggregated loss threshold · ε ∈ {1, 4, 8} · mia_vitaldb*.csv")
table(["ε", "record-DP", "patient-DP", "gap"], [
 ["1", "0.5461", "0.5374", "+0.0087"], ["4", "0.5512", "0.5417", "+0.0095"],
 ["8", "0.5459", "0.5430", "+0.0030"],
])
para("Against a predicted gap of ≈0.20, the measured gap is under 0.01 at every budget. But a loss "
     "threshold is the WEAKEST attack in the literature and its AUC is only a lower bound on "
     "leakage, so this null was NOT REPORTABLE ON ITS OWN. That is what motivated E16.")

head("E16 · LiRA — likelihood-ratio attack at ε = 1", 3)
small("3 arms × 16 shadow models · per-patient IN/OUT Gaussians · identical splits "
      "(--split_seed 7) · 5 paired seeds · 600 members + 600 non-members")
table(["Arm", "Best attack AUC (95% CI)", "Via", "Difficulty floor", "Margin"], [
 ["Positive control — head-only, no DP", "0.6277 [0.5905, 0.6649]", "lira_offline", "0.5626", P("+0.0627")],
 ["Record-level DP", "0.5477 [0.4876, 0.6079]", "lira_offline", "0.5252", "+0.0226"],
 ["Patient-level DP", "0.5224 [0.5175, 0.5274]", "loss threshold", "0.5167", "+0.0057"],
], fs=8.0)

head("E17 · Difficulty floor — confound control", 3)
small("Added 2026-08-20 · computed from shadow scores already on disk, no retraining · "
      "mia_difficulty_floor.py")
para("Ranks patients by shadow-model difficulty alone, using NO TARGET MODEL AT ALL. Shadow "
     "membership is randomised over the whole patient universe, so a balanced split must score 0.5.")
table(["Arm", "Floor", "Attack", "Margin"], [
 ["head_nodp (control)", "0.5626", "0.6254", P("+0.0627")],
 ["record-DP, ε=1", "0.5252", "0.5477", "+0.0226"],
 ["patient-DP, ε=1", "0.5167", "0.5224", "+0.0057"],
 ["record-DP, ε=16", "0.5743", "0.5465", F("−0.0278")],
])
para("METHODOLOGICAL FINDING: members are drawn from released TRAIN patients and non-members from "
     "released TEST patients, and those pools differ in intrinsic difficulty. Any attack AUC must "
     "therefore be read against this floor, not against 0.5. The ε=16 record arm scores BELOW its "
     "own floor — that is confound, not leakage.")

head("E24 · LiRA at ε = 16 — N-A's last chance", 3)
small("Run 2026-08-19/20 · 6 targets + 32 shadows, 3 seeds · lira_eps/vitaldb/eps16.0/")
para("Tests whether N-A failed because ε=1 crushed both arms to chance, leaving no room for a gap. "
     "At ε=16 the noise is 13× lower (σ 11.33 → 0.85), so a membership signal should survive if "
     "one exists.")
table(["Arm", "Best attack", "Floor", "Margin"], [
 ["Record-level DP", "0.5465 (loss)", "0.5743", F("−0.0278")],
 ["Patient-level DP", "0.5630 (lira_offline)", "0.5259", "+0.0371"],
])
callout("Verdict: REFUTED, twice, each time with a passing positive control.",
 "WHY IT FAILED — the real reason. Not because the attack was weak: the positive control, on "
 "a model known to memorise, reached 0.6277 and cleared a gate set BEFORE running.\n\n"
 "DP-SGD at ε = 1 is already very strong. The noise (σ = 11.33) is large enough that even "
 "record-level DP leaves almost no membership signal to find. The theoretical gap between "
 "record-level and patient-level protection is real, but at this budget BOTH arms are pushed so "
 "close to chance that the difference is smaller than we can measure with 5 seeds.\n\n"
 "A supporting clue confirms this: on the patient arm, LiRA performed WORSE than a plain loss "
 "threshold (−0.0071). That is what a defence with nothing left to leak looks like — not a "
 "failing attack.\n\n"
 "SAY IT THIS WAY, ALWAYS: the large predicted effect is refuted. A small effect is NOT excluded "
 "— the interval is ±0.060 wide at n = 5. NEVER write \"there is no effect\".", "bad")

head("15.  The unexpected finding inside the failure (N-A′)")
head("E15 · MIA factorial — leakage by recipe", 3)
table(["Recipe", "Attack AUC", "Member / non-member loss"], [
 ["Full-model, no DP", "0.5122", "1.81 / 2.31"],
 [("Head-only, no DP — OUR OWN RECIPE", None, True), F("0.5847"), "0.013 / 4.95"],
 ["Full-model, DP", "0.5206", "6.93 / 7.46"],
])
para("p = 1×10⁻⁹, sd 0.0018 over 6 runs. Under LiRA the head-only figure rises to 0.6277.")
callout("Leakage is a property of the RECIPE, not of the task.",
 "Head-only fine-tuning — the very recipe this project adopted to make ε ≤ 1 viable "
 "— memorises its members far harder than full-model training. This is a genuine caveat to "
 "the parameter-efficient DP fine-tuning literature, and to our own method. Li et al. (2021) and "
 "Yu et al. (2021) propose head-only DP fine-tuning for efficiency; neither measures whether it "
 "leaks more. Retained as a contribution in its own right.", "bad")

head("16.  What routes remain to revive N-A")
table(["#", "What to change", "Why it would help", "Cost"], [
 ["1", "Attack at a weaker budget — ε = 4, 8, 16",
  "At ε=1 both arms are near chance, so there is no room for a gap. Weaker DP leaves signal.",
  W("DONE — also refuted")],
 ["2", "Increase seeds from 5 to 20–30",
  "The interval half-width is ±0.060; the measured gap is +0.0325. More seeds would resolve whether that small gap is real.", "Medium"],
 ["3", ("Use a dataset with higher k", None, True),
  ("VitalDB gives ~8 windows per patient. The more records a patient contributes, the bigger the "
   "theoretical gap. A dataset with 50–100 records per patient should show it more clearly.", None, True),
  P("NEEDS eICU")],
 ["4", "Attack the worst-case patient, not the average",
  "Average AUC hides the tail. Report TPR at 0.1% FPR — the confident identifications that are the real clinical disclosure. Machinery already computes it.", P("Low — not yet run")],
 ["5", "Attack the head-only recipe directly",
  "We already know head-only training memorises harder (0.6277 vs 0.5122). That is where leakage lives.", "DONE — this is N-A′"],
])
para("Route 3 is why eICU matters for this claim specifically, and why BRSET cannot serve it: BRSET "
     "gives 1.91 records per patient and mBRSET 4.0, both BELOW VitalDB's ~8. The theoretical gap "
     "would be smaller there, not larger.")

head("17.  The outstanding validity gap")
callout("UNRESOLVED — affects the ε claim.",
 "A substantial portion of results ran in PROXY / ORACLE MODE: the encoders were pretrained on the "
 "pooled federated training indices. The encoders therefore saw private data non-privately, which "
 "means ε = 1 DOES NOT HOLD END-TO-END for that version of the pipeline, and Objective 2 as "
 "reported there is an UPPER BOUND.\n\n"
 "The cost of a valid guarantee has since been priced at −0.022 AUROC versus the oracle, which is "
 "the quantity to report — the proxy-versus-public gap, not the proxy alone. Closing this "
 "fully requires pretraining on an external public corpus or carving a disjoint public index "
 "split.", "bad")

head("18.  Other characterised negatives")
table(["Item", "Outcome"], [
 ["ASWA aggregation", F("+0.0005 AUROC. Deleted from the codebase.")],
 ["FedKD-E", F("Not freeze-aware; dropped.")],
 ["CMGA / PHANTOM-FL branding", F("Unbuilt and abandoned. Cross-modal attention entangles the modality "
   "streams, leaving no small separable head to DP-train — building it would have DESTROYED "
   "head-only DP, the project's own enabling mechanism.")],
 ["Fusion gain at two seeds", W("Corrected downward at five seeds: +0.0411 → +0.0370 AUROC, and "
   "AUPRC +0.1062 → +0.0671, a 37% fall. Only five-seed figures may be quoted.")],
 ["Legacy corpus (ECG + chest X-ray)", F("Withdrawn entirely. Its two modalities were paired by a "
   "RULE (CXR bucket = f(ECG label)) rather than by provenance, so no result computed on it was "
   "evidence of multimodal fusion. Removed from code and disk 2026-08-15.")],
 ["WEAR accuracy objective (O2b)", W("Inconclusive; seed count pre-registered at 15 and deliberately "
   "not extended, because extending after seeing the result would be p-hacking.")],
 ["WEAR fusion", W("At ceiling (0.9976). Structurally unable to corroborate the fusion claim.")],
])

# ══════════════════════════ PART IV ══════════════════════════
pagebreak()
parthead("PART IV — THEORY, PRACTICE AND STANDING")

head("19.  What was achieved in theory")
table(["Theoretical result", "Status", "Meaning in one line"], [
 ["Patient-level guarantee holds by construction", P("PROVEN"),
  "Grouping gradients before clipping bounds one patient's influence, whatever number of records they contribute."],
 ["Record-level ε ≠ patient-level ε", P("PROVEN"),
  "The two are different guarantees. Analytic, and survives the failed attack."],
 ["Price of upgrading the unit = 1.77× σ", P("DERIVED"),
  "Making the guarantee patient-level costs 1.77× more noise at the same budget."],
 ["Group privacy conversion is unusable here", P("SHOWN"),
  "At 8 records per patient, converting a record-level ε = 1 gives a number that guarantees nothing."],
 ["Composed budget = training + calibration", P("CORRECT"),
  "ε = 0.7705 + 0.2000 = 0.9705. Most papers report only the first term."],
 ["Conformal coverage guarantee", P("HOLDS"),
  "P(true label ∈ predicted set) ≥ 1 − α, and its release cost is paid for."],
 ["Cost is a function of k, zero at k = 1", P("PREDICTED & CONFIRMED"),
  "Theory says the two units coincide at k = 1. Measurement agrees (p = 0.75). Theory and experiment match."],
 ["Record-level DP is exploitable by patient MIA", F("PREDICTED, NOT OBSERVED"),
  "The theory is sound; the effect is not measurable at ε = 1."],
])

head("20.  What was achieved in practice")
table(["Practical result", "Measured", "Verdict"], [
 ["Uplink reduction (VitalDB / WEAR)", "90.82% / 96.08%", P("WORKS")],
 ["Energy saving", "72.30% / 76.84%", P("WORKS")],
 ["Inference latency P95", "4.58 ms / 1.22 ms", P("WORKS")],
 ["Update reliability", "100% / 99.94%", P("WORKS")],
 ["Privacy budget achieved", "ε = 0.9705 / 0.9656", P("WORKS")],
 ["Accuracy cost at ε = 1 (VitalDB)", "−0.92 pp", P("WORKS")],
 ["Multimodal fusion gain (VitalDB)", "+0.0370 AUROC", P("WORKS")],
 ["k-scaling law measured", "24/24 configs", P("WORKS")],
 ["Accuracy cost at ε = 1 (WEAR)", "1.967 pp, CI [1.76, 2.17]", W("UNRESOLVED")],
 ["Patient MIA vulnerability", "Δ CI includes zero", F("FAILED")],
 ["Adaptive DP (SADP)", "σ 11.3 → 70", F("FAILED")],
 ["INT8 edge quantisation", "1.9× slower on CPU", F("FAILED")],
 ["Fusion gain on WEAR", "+0.0004 (ceiling)", W("NO HEADROOM")],
 ["ASWA aggregation", "+0.0005 AUROC", F("USELESS")],
 ["End-to-end valid ε (public pretraining)", "priced at −0.022 AUROC", W("NOT CLOSED")],
])
callout("The short version.",
 "THEORY: almost everything held. The one thing that did not was a prediction about what an "
 "ATTACKER could do, not about the mechanism itself.\n\n"
 "PRACTICE: every system objective passed with a wide margin. The failures were all in the "
 "OPTIONAL EXTRAS — adaptive privacy, INT8, a fancy aggregator — none of which the "
 "framework depends on.", "good")

head("21.  Success rate")
table(["Category", "Achieved", "Rate", "Note"], [
 ["Engineering objectives (both datasets)", "13 of 14", "93%", "Only WEAR O2b unresolved, deliberately"],
 ["Original four objectives (O1–O4)", "4 of 4", P("100%"), "All exceeded, most by a wide margin"],
 ["Project phases", "5 of 6", "83%", "Phase 6 code-complete, runs partly pending"],
 ["Phase 5 deliverables", "17 of 17", P("100%"), ""],
 ["Scientific claims measured", "8 of 12", "67%", "1 refuted, 2 never run, 1 evidence-only"],
 ["Major hypotheses", "1 of 2", "50%", "k-law succeeded; patient MIA refuted"],
 ["Optional mechanisms we designed", "0 of 3", F("0%"), "SADP, ASWA, FedKD-E all dropped"],
 ["External validation", "0 of 1", F("0%"), "The eICU experiment, now unblocked"],
])
para("HONESTLY: engineering ~95% successful — the system does everything it was supposed to "
     "do, with margins of 2× to 20× on the targets. Science ~60% successful — one hypothesis "
     "died, one succeeded on a single dataset, one original mechanism has still not been tested. "
     "A fair combined figure is 75–80%, and the remaining 20–25% is almost entirely the "
     "external validation that eICU supplies.")

head("22.  What does not exist anywhere else")
para("The list of things not found in any paper studied. This is the answer to \"what is new?\"")
table(["#", "Does not exist in the literature", "Closest existing work, and what it stops short of"], [
 ["1", ("The privacy cost measured as a CURVE in records-per-individual.", None, True),
  "User-level DP papers (McMahan 2018) report one number for one dataset. The controlling variable has never been isolated."],
 ["2", "A hierarchical FL system carrying a formal patient-level guarantee.",
  "HED-FL, HCEF and Mhaisen et al. are hierarchical with NO privacy guarantee. FL2DP and RoPPFL have privacy but are NOT hierarchical. The two lines have never met."],
 ["3", "Conformal calibration cost composed into the privacy budget.",
  "Conformal FL papers release the calibration quantile for free. Smith (2011) gives the DP quantile mechanism, but nobody charges it to the same budget as training. We do: 0.7705 + 0.2000."],
 ["4", "Patient-level MIA audit with a passing positive control.",
  "MIA audits in FL are conducted at RECORD level — the quantity a record-level guarantee already protects, so the least informative test. Almost none report a positive control, so their nulls cannot be trusted."],
 ["5", "The finding that parameter-efficient DP fine-tuning INCREASES memorisation.",
  "Li et al. (2021) and Yu et al. (2021) propose head-only DP fine-tuning for efficiency. Neither measures whether it leaks more."],
])

head("23.  Complete findings register")
table(["ID", "Claim", "/10", "State", "Evidence"], [
 ["N-B", "Cost of the guarantee scales with records per patient", P("8"), P("MEASURED"),
  "24/24 configs; gap 0 → +0.0507 → +0.0832 → +0.0866 AUPRC; control at k=1 (p=0.75)"],
 ["N-D", "Normalised patient clipping beats fixed-C", "8", W("NOT RUN"), "—"],
 ["N-A′", "Head-only DP fine-tuning memorises members", "7", P("MEASURED"),
  "0.6277 LiRA vs 0.5122 full-model; p = 1e−9, sd 0.0018 over 6 runs"],
 ["N-1", "Genuinely paired multimodal benchmark shows fusion gain", "7.5", W("ONE DATASET"),
  "+0.0370 AUROC / +0.0671 AUPRC, 5 seeds, 5.9× sd (VitalDB); WEAR at ceiling"],
 ["N-2", "Patient-level DP cost measured", "7.5", P("DONE"), "Superseded in importance by N-B, which generalises it"],
 ["N-3", "Cost of a valid guarantee (disjoint pretraining)", "6.5", P("MEASURED"), "−0.022 AUROC versus oracle pretraining"],
 ["N-4", "Head-only DP viable in hierarchical multimodal FL", "6", P("MEASURED"), "Gap widens as budget tightens; holds on both datasets"],
 ["N-5", "Adaptive-DP composition tax", "5.5", F("NEGATIVE"), "Cross-group split drives σ 11.3 → 70; worse than uniform at equal ε"],
 ["—", "DP shifts model attention toward missingness", "5", P("MEASURED"),
  "Mask attribution: full_dp 28.2% > patient 22.0% ≈ sample 21.6% > full_nodp 19.9% > head_nodp 15.8%; ρ = 0.95"],
 ["N-6", "Specialty-derived non-IID partitioning", "4", P("MEASURED"), "3.2–50.7% ICU base rate across clients"],
 ["N-A", "Record-level DP exploitable by patient-level MIA", "—", F("REFUTED"),
  "ε=1 and ε=16, both with passing positive controls"],
])

# ══════════════════════════ PART V ══════════════════════════
pagebreak()
parthead("PART V — WHAT HAPPENS NEXT, AND HOW IT ENDS")

head("24.  The one question the project cannot yet answer")
callout("The reviewer's question — and it is the right one.",
 "Every privacy claim rests on ONE DATASET FROM ONE HOSPITAL. VitalDB is a single institution, and "
 "its nine \"clients\" are a partition we created ourselves. WEAR cannot help: 22 people, one "
 "client each, no patient contributing enough records for the k-law to even be defined.\n\n"
 "\"Is this a property of patient-level private federated learning, or a property of your dataset?\"\n\n"
 "Right now the project cannot answer it. That is the entire remaining gap.", "bad")
para("Exactly ONE work item is blocked on data access — running the eICU arms. Everything else "
     "— the pre-registration, the manuscript restructuring, the eICU pipeline itself — "
     "was always doable and is now done.")

head("25.  Why eICU-CRD specifically")
table(["Property of eICU-CRD", "Why the research needs it"], [
 [("208 real hospitals", None, True), "Clients become ACTUAL INSTITUTIONS rather than a partition we invented. This is what federated learning is supposed to model; we currently only simulate it."],
 [("~139,000 patients", None, True), "Different demographics, care patterns, equipment. If the k-law survives that, it is structural."],
 [("Many records per patient", None, True), ("THE DECISIVE PROPERTY. VitalDB tops out near k=8; eICU stretches the curve into a range VitalDB cannot reach — which is the only place the saturation prediction can be falsified.", None, True)],
 ["Same modality structure", "Time-series vitals + static clinical. modality_b=\"features\" applies, NO NEW ENCODER. Weeks, not months."],
 ["Credentialed access + CITI training", "Reviewers trust PhysioNet, and the access process is itself evidence the work was conducted properly."],
 ["Widely used benchmark", "Results on eICU can be compared against other published work. Results on a private partition cannot."],
])
small("Rejected alternatives: MIMIC-IV + MIMIC-CXR (4.7 TB, needs a new encoder — better as the "
      "next paper); HiRID (same structure as VitalDB, corroborates little); PTB-XL (largely "
      "single-modality, fails the pairing and headroom tests); BRSET / mBRSET (1.91 and 4.00 "
      "records per patient — BELOW VitalDB's ~8, so they would weaken the k-law test, not "
      "strengthen it).")

head("26.  The rule that makes this experiment worth running")
callout("Freeze the prediction before touching the data.",
 "We will NOT simply run the same experiment and add another table. That is worth little.\n\n"
 "Instead: fit the k-curve on VitalDB, write down a NUMERIC prediction of what the gap should be "
 "at eICU's k, FREEZE THAT PREDICTION BEFORE TOUCHING THE DATA, then test it.\n\n"
 "WHY FROZEN FIRST: the value of this experiment is that IT COULD FAIL. If we fit the curve, look "
 "at eICU, and then write the prediction, no reviewer can tell that apart from retrofitting "
 "— and neither can we.", "info")

head("27.  The frozen forecast")
para("Fitted on VitalDB measurements alone, before any eICU array existed:", space=2)
mono("gap(k)  =  A · ( 1 − exp( −b · (k − 1) ) )\n\n"
     "  A = 0.0878 ± 0.0035     (asymptotic ceiling)\n"
     "  b = 0.8827 ± 0.1286     (approach rate)\n"
     "  RMSE = 0.0028            residuals: −0.0052, −0.0008, +0.0016, −0.0010", size=8.5)
table(["k", "Fitted", "Observed (VitalDB)", "Predicted for eICU", "Acceptance band (±0.030)"], [
 ["1", "+0.0000", "−0.0052", "+0.000", "−0.030 … +0.030   (control)"],
 ["2", "+0.0515", "+0.0507", "+0.052", "+0.022 … +0.082"],
 ["4", "+0.0816", "+0.0832", "+0.082", "+0.052 … +0.112"],
 ["8", "+0.0876", "+0.0866", "+0.088", "+0.058 … +0.118"],
 ["16", "—", ("not reachable", None, True), "+0.088", "+0.058 … +0.118"],
 ["32", "—", ("not reachable", None, True), "+0.088", "+0.058 … +0.118"],
], fs=8.0)
callout("The risky content of the forecast.",
 "THE CURVE SATURATES — 90% of the ceiling is reached by k = 3.6. The prediction is therefore "
 "that the gap at k=32 exceeds the gap at k=8 by LESS THAN 0.015: the cost of a patient-level "
 "guarantee is BOUNDED, not unbounded, in records per patient.\n\n"
 "This is testable only at k > 8 — precisely what VitalDB cannot do and eICU can.", "good")

head("28.  What refutes the forecast")
table(["Outcome", "Reading"], [
 ["k=1 gap outside ±0.020", F("Harness fault. NOT a finding. Fix before reporting anything.")],
 ["Gap flat or negative at k ≥ 2, k=1 control passing", W("The law is VitalDB-specific. Report as a boundary condition.")],
 ["Gap still climbing steeply past k=8", W("Saturation model refuted; the ceiling is not bounded as forecast.")],
 ["Ceiling far from 0.0878 but shape preserved", W("Shape is structural, magnitude is corpus-dependent. Report both.")],
])

head("29.  Execution order — every step has a gate")
table(["Step", "Experiment", "Gate"], [
 ["E0", ("Commit the pre-registration", None, True), F("Must precede the build. Non-negotiable.")],
 ["E1", "Verify SCHEMA against real headers", "Headers only, no data values. Fix any mismatch first."],
 ["E2", "Build corpus", "--max_stays for a fast first pass"],
 ["E3", "Validate corpus", "Do not proceed past a CAPACITY failure"],
 ["E4", "Ceiling check (single-modality arms)", W("Stop if the better arm > 0.95 AUROC — the check WEAR failed")],
 ["E5", "Pretrain encoders, disjoint population", "So eICU does not inherit the §17 validity gap"],
 ["E6", "Main operating point", "ε = 0.80 + 0.20 conformal, 10 rounds, τe = 5"],
 ["E7", "Objective verification O1–O4", "—"],
 ["E8", ("k-scaling — THE experiment", None, True), P("k ∈ {1,2,4,8,16,32}. k=1 is the control; k=16, 32 are the point of the corpus")],
 ["E9", "LiRA + non-private positive control", "A null without a passing control is inadmissible"],
 ["E10", "Component ablation A0–A5", "—"],
 ["E11", "Uplink / compression", "Re-measure, do not assume"],
])

head("30.  How each remaining gap closes")
table(["Gap", "Closed by"], [
 ["Every claim rests on one single-institution dataset", "E8 on 208 real hospitals"],
 ["Is the k-law structural or dataset-specific? Unanswerable", "E8 against the frozen numeric forecast"],
 ["Curve cannot be stretched past VitalDB's k", "E8 at k = 16, 32"],
 ["Encoders pretrained in oracle mode; ε=1 not end-to-end", "E5 with the disjoint population"],
 ["Fusion single-domain; gain shrank at 5 seeds", "E4 at 5 seeds, reported as a setting result"],
 ["MIA null needs statistical power", "E9 at ~139,000 patients"],
 ["Federation is constructed, not natural", "E10 — hospitals taken as given"],
])

head("31.  Open regardless of eICU")
table(["Item", "Why it matters"], [
 [("Window-count-normalised patient clipping (N-D)", None, True),
  ("THE ONLY REMAINING CANDIDATE FOR AN ORIGINAL MECHANISM rather than a measurement. A patient's "
   "gradient is summed over k windows and then clipped to a fixed bound, so long recordings are "
   "systematically down-weighted; normalising before clipping should correct it. Rated 8/10, "
   "NEVER RUN, and needs no new data.", None, True)],
 ["Conformal coverage validation",
  "The coverage guarantee is implemented and its budget cost composed into the reported ε, but empirical coverage has NEVER been measured."],
 ["Worst-case MIA reporting (TPR at 0.1% FPR)",
  "Average AUC hides the confident-identification tail that is the real clinical disclosure. Machinery already exists; cost is low."],
 ["Mask-channel ablation", "Would convert the E20 attribution evidence into proof."],
 ["Hierarchical arm without DP", "Completes the topology axis alongside the existing ablation arms."],
 ["Multi-seed baselines", "Would place confidence intervals on E4."],
])

head("32.  How the research ends")
para("The eICU experiment has two possible outcomes, and BOTH ARE PUBLISHABLE. That is by design "
     "— it is what makes the experiment worth running rather than decorative.")
table(["Outcome", "What it means"], [
 [P("The prediction lands"),
  "The cost of a patient-level guarantee is shown to be STRUCTURAL rather than dataset-specific, "
  "and the work delivers a transferable design rule: given your k, this is what patient-level "
  "ε = 1 will cost you. That is what a practitioner actually needs, and it has not been published."],
 [W("The prediction misses"),
  "The work has found a BOUNDARY CONDITION, with a registered forecast proving the story was not "
  "retrofitted. Also publishable, and visibly honest."],
])
callout("Either way the paper is stronger.",
 "A paper reporting that two independent clinical datasets were tested — one reproducing the "
 "result and the other exposing a limitation — is MORE publishable than one in which "
 "everything conveniently succeeded.", "good")

head("33.  What is genuinely ours, and what is not")
para("Be precise about this, because a reviewer will be. The positioning rule stands: the "
     "manuscript must NOT say \"we propose patient-level DP\".")
table(["Prior art — do not claim", "This work's actual contribution"], [
 ["Patient-level / user-level DP — McMahan et al., 2018",
  ("THE k-SCALING LAW — the measured relationship between records-per-person and the cost of "
   "a person-level guarantee. Not previously published.", None, True)],
 ["Head-only / parameter-efficient DP fine-tuning — Li et al., Yu et al., 2021",
  ("THE SELF-CONTROLLING EXPERIMENT DESIGN — the k=1 null built into the same experiment as "
   "the effect, which is what licenses reading the rest.", None, True)],
 ["Exponential-mechanism DP quantile release — Smith, 2011",
  ("AN AUDIT THAT CAN RETURN AN INFORMATIVE NEGATIVE — every attack reported alongside a "
   "positive control on a configuration known to memorise.", None, True)],
 ["Hierarchical federated learning — HED-FL, HCEF, Mhaisen et al.",
  ("A FINDING THAT ARGUES AGAINST OUR OWN RECIPE — head-only training memorises harder "
   "(0.5847 vs 0.5122), reported rather than buried.", None, True)],
])
para("The contributions are MEASUREMENTS AND AUDITING PRACTICE in a setting where they have not "
     "been measured — not new mechanisms. That is a defensible position; \"we integrated four "
     "existing things\" is not.")

head("34.  The final claim")
callout("",
 "Stating your privacy guarantee over PEOPLE instead of over RECORDS costs accuracy — and "
 "that cost is not a constant. It grows with how many records each person contributes, then "
 "saturates. Here is the curve, here is the control that proves the curve is real, and here is the "
 "independent corpus that says it is not just our data.", "info")

small("Sources: RESEARCH DOSSIER Parts 1–3 (HFL_Research_Dossier, HFL_Dossier_Part2_Technical, "
      "HFL_Dossier_Part3_Experiments); Complete Experiment Log E1–E24; "
      "document/01_planning/plan.md rev 3; document/01_planning/PREREGISTRATION_EICU.md; "
      "document/01_planning/EICU_INTEGRATION_SPEC.md; Phase Reports 1–6. Every value quoted is "
      "read from a measured artifact on disk; none is estimated.")

import sys
doc.save(sys.argv[1] if len(sys.argv) > 1 else "HFL_Detailed.docx")
print("docx saved")
