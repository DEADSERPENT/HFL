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

# ─────────────────────────── TITLE ───────────────────────────
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
r = p.add_run("Hierarchical Federated Learning for Privacy-Aware,\nLow-Latency Multimodal IoT Systems")
r.bold = True; r.font.size = Pt(17); r.font.color.rgb = NAVY
para("Complete project status — what is done, what failed, what happens next",
     size=10.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space=3)
para("Samartha H V (251580130019)  ·  Guide: Dr. Shreyas J  ·  Industry: Mr. Tejas J, Capgemini\n"
     "School of Computer Engineering, MIT Bengaluru (MAHE)  ·  January–May 2026",
     size=8.8, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, space=2)
para("Status as of 5 September 2026", size=8.8, italic=True, color=GREY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space=8)

callout("The project in one sentence.",
 "Stating a privacy guarantee over PEOPLE instead of over RECORDS costs accuracy — and that cost "
 "is not a fixed number. It grows with how many records each person contributes, then levels off. "
 "This work measures that curve, proves the measurement with a control built into the same "
 "experiment, and is now testing it on a second, independent clinical corpus against a forecast "
 "frozen in advance.", "info")

# ─────────────────────────── 1. AT A GLANCE ───────────────────────────
head("1.  At a glance")
table(["Category", "Count", "Note"], [
 ["Experiments completed", "24", "All finished; none abandoned mid-run"],
 ["Succeeded outright", "14", "Including every engineering objective"],
 ["Characterised negative results", "5", "Reported rather than dropped"],
 ["Mixed or inconclusive", "3", "WEAR accuracy, WEAR fusion, attribution"],
 ["Superseded", "1", "End-to-end budget sweep, kept as comparison arm"],
 ["Cost priced, not passed/failed", "1", "Rigorous public pretraining"],
])

head("The four objectives from the January 2026 proposal", 2)
table(["ID", "Objective", "Target", "VitalDB", "WEAR"], [
 ["O1",  "Uplink traffic reduction", "≥ 50%", P("90.82%  PASS"), P("96.08%  PASS")],
 ["O1b", "Round latency reduction", "> 0%", P("16.93%  PASS"), P("21.68%  PASS")],
 ["O2a", "Privacy budget (train + conformal)", "ε ≤ 1", P("0.9705  PASS"), P("0.9656  PASS")],
 ["O2b", "Accuracy loss under DP", "≤ 2 pp", P("−0.92 pp  PASS"), W("1.967 pp  INCONCL.")],
 ["O3a", "Inference latency P95", "< 100 ms", P("4.58 ms  PASS"), P("1.22 ms  PASS")],
 ["O3b", "Successful updates", "> 99%", P("100%  PASS"), P("99.94%  PASS")],
 ["O4",  "Energy saving per round", "≥ 20%", P("72.30%  PASS"), P("76.84%  PASS")],
])
small("VitalDB 7/7 PASS.  WEAR 6 PASS + 1 INCONCLUSIVE.  O2a is a COMPOSED budget — training "
      "0.7705 plus conformal release 0.2000 — stricter than the common practice of reporting "
      "training alone.")

callout("The honest reading of that table.",
 "Every engineering objective was met, most by a wide margin. They turned out to be the easy part. "
 "Nothing in the January proposal anticipated the finding that now carries the paper — the "
 "k-scaling law, the patient-vs-record privacy unit, or the membership-inference audit. "
 "The project outgrew its own proposal.", "good")

# ─────────────────────────── 2. WHAT WAS DONE ───────────────────────────
pagebreak()
head("2.  What was done, and what it measured")

head("Phase 4 — Simulation infrastructure", 2)
head("E1 · NS-3 packet-level network simulation", 3)
small("NS-3 v3.46.1 · 9 IoT devices, 2 edge servers, 1 cloud · device→edge 54 Mbps, "
      "edge→cloud 1 Gbps at 5 ms · LogDistance propagation, 5 Mbps background traffic")
table(["Quantity", "VitalDB", "WEAR"], [
 ["Round latency, flat → hierarchical", "90.5 → 75.2 ms", "104.5 → 81.8 ms"],
 ["Latency reduction", "16.93%", "21.68%"],
 ["Per-update reliability (2 hops)", "100%", "99.94%"],
 ["Round uplink / downlink time", "33.97 s / 26.85 s", "—"],
])
para("Result: the edge tier reduces both traffic and round latency under real packet-level "
     "measurement, not an analytical estimate.")

head("E2 · CloudSim Plus compute and energy simulation", 3)
small("CloudSim Plus v8.5.6 · IoT 300 MIPS / 512 MB / 1–3 W · edge 8000 MIPS / 16 GB / 50–200 W "
      "· GPU overhead modelled on edge servers only")
table(["Scenario", "Energy per round", "Uplink"], [
 ["CentralizedFL", "1266.25 J", "73.85 MB"],
 ["HFL_Proposed (VitalDB)", P("−72.3%"), "see E10"],
 ["HFL_Proposed (WEAR)", P("−76.8%"), "see E10"],
])
rich([("Result: ", True, False, None),
 ("72.3% and 76.8% energy saving against a 20% target. A second figure of 93.5% exists from a "
  "bytes→Joules proxy but is arithmetically identical to communication reduction, so it is not an "
  "independent energy measurement and is not quoted.", False, False, None)])

head("Phase 5 — Model, privacy and deployment", 2)
head("E3 · Encoder pretraining: proxy vs rigorous", 3)
table(["Mode", "Effect on AUROC", "Privacy validity"], [
 ["Proxy / oracle", "baseline", F("ε NOT valid end-to-end")],
 ["Rigorous disjoint public split", "−0.022", P("valid")],
])
para("Result: a valid end-to-end guarantee costs 0.022 AUROC. That gap is the number to report, "
     "not the proxy alone.")

head("E4 · Baseline suite B0–B5", 3)
table(["Baseline", "Test accuracy", "Test macro-AUC", "Note"], [
 ["B0  Centralized", "0.5787", "0.8211", "Upper reference (pooled data)"],
 ["B1  Local-Only", "0.4532", "0.7511", "Lower reference, no collaboration"],
 ["B2  FedAvg", "0.6543", "0.8795", "Best non-private baseline"],
 ["B3  FedProx", "0.6570", "0.8747", "No advantage over FedAvg here"],
 ["B4  DP-FedAvg (ε≈1)", F("0.2159"), F("0.6443"), "COLLAPSES. The like-for-like DP reference"],
 ["B5  MOON", "0.3934", "0.7418", "Underperforms on this task"],
])
para("Result: B4 is the critical row. Applying DP the conventional way at the same budget destroys "
     "the model — which is what makes E5 meaningful.")

head("E5 · Head-only DP fine-tuning — the ε=1 collapse fix", 3)
small("20 rounds, 5 edge rounds · δ=1e-5, C=1.0 · head = 560,645 / 2,157,766 params (26.0%) · 3 seeds")
table(["Recipe", "σ", "Test AUC", "Round time"], [
 ["End-to-end DP-SGD", "11.3281", F("0.562"), "1046 s"],
 ["Head-only DP fine-tuning", "11.3281", P("0.8742 ± 0.0072"), "50 s"],
])
callout("The noise was never the problem.",
 "σ is identical in both rows. What changed is optimisation geometry: a near-linear probe over "
 "frozen pretrained features tolerates σ≈11.3, while training from scratch does not. Also ~20× "
 "faster per round. This reframes the standard \"DP destroys utility\" complaint.", "good")

head("E7 · ε sweep, rigorous head recipe", 3)
table(["ε", "σ", "AUROC", "AUPRC"], [
 ["0.5", "5.92", "0.8287", "0.5110"], ["1", "3.24", "0.8319", "0.5464"],
 ["2", "1.88", "0.8323", "0.5381"], ["4", "1.21", "0.8356", "0.5590"],
 ["8", "0.85", "0.8342", "0.5544"], ["∞ (non-private)", "—", "0.8158", "0.5204"],
])
para("Result: utility is flat from ε=0.5 to ε=8, and every private arm beats the non-private one. "
     "DP acts as a regulariser here. The utility floor lies below the budget the system ships at.")

head("E8 · Objective 2b — multi-seed accuracy cost", 3)
table(["Dataset", "Cost (pp)", "95% CI", "Verdict"], [
 ["VitalDB (n=5)", "−0.92", "[−2.82, +0.99]", P("PASS")],
 ["WEAR (n=15)", "1.967", "[1.760, 2.173]", W("INCONCLUSIVE")],
])
para("Result: VitalDB shows no measurable cost. WEAR's interval straddles the 2 pp threshold, so it "
     "can be neither passed nor failed. The seed count was pre-registered at 15 and deliberately not "
     "extended — extending it after seeing the result would be p-hacking.")

head("E10 · Gradient compression and uplink measurement", 3)
table(["Measurement", "Bytes per round"], [
 ["Full-model FP32 FedAvg", "258,931,920"],
 ["Head-only, uncompressed", "67,277,400"],
 ["Observed, post-fix", P("16,821,300")],
])
para("Defect found and fixed: the compressor took a fixed k = numel × sparsity of EVERY tensor, so "
     "frozen encoders — whose delta is exactly zero — contributed 20% of their elements as explicit "
     "zeros. Omitting all-zero tensors alone accounted for a 78.87% reduction. "
     "Final: 90.82% (VitalDB), 96.08% (WEAR) against a 50% target.")

head("E11 · ONNX export and inference latency", 3)
small("1000 timed runs after 100 warmup, batch 1 · path = preprocessing → ONNX forward → conformal set → serialise")
table(["Precision", "Provider", "Model", "Inference P95", "Conformal", "Total P95", "QoS"], [
 ["FP32", "CPU", "10.64 MB", "13.259", "0.079", "16.363 ms", P("PASS")],
 ["FP32", "GPU (CUDA)", "10.64 MB", "20.088", "0.096", "22.476 ms", P("PASS")],
 ["INT8", "CPU", "6.55 MB", "27.877", "0.090", "31.028 ms", P("PASS")],
 ["INT8", "GPU (CUDA)", "6.55 MB", "70.020", "0.112", "73.150 ms", P("PASS")],
], fs=7.8)
small("Headline objective figures — 4.58 ms P95 (VitalDB), 1.22 ms (WEAR) — come from the final "
      "objective run on the current corpora.")

head("E13 · Patient-level vs record-level DP", 3)
small("Both arms at matched budget · 5 seeds · VitalDB: 48,712 windows / 6,257 cases, "
      "mean 7.79 windows per case, 100% of cases contribute more than one window")
para("Result: the upgrade is priced at 1.77× σ. Because every patient contributes more than one "
     "record, record-level and patient-level are DIFFERENT STATEMENTS for every individual in the "
     "dataset. This is the premise the whole project rests on, and it is measured, not assumed.")

head("E20 · Feature attribution", 3)
table(["Recipe", "Mask share of attribution"], [
 ["full_dp", "28.2%"], ["patient-DP", "22.0%"], ["sample-DP", "21.6%"],
 ["full_nodp", "19.9%"], ["head_nodp", "15.8%"],
])
para("Result: DP shifts the model's attention toward MISSINGNESS — under noise it leans more on "
     "which measurements exist than on their values, monotonically with how much DP is applied. "
     "Rank correlation ρ=0.95 private vs not. Evidence, not proof.")

head("E22 · Component ablation A0–A6", 3)
table(["Arm", "Configuration", "AUROC", "AUPRC", "ε"], [
 ["A0", "Full system (reference)", "0.8541 ± 0.0035", "0.5960", "0.7705"],
 ["A1", "No C1 — flat tier (no edge)", "0.8484 ± 0.0057", "0.5911", "0.7704"],
 ["A2", "No C2 — no DP", "0.8307 ± 0.0060", "0.5136", "∞"],
])
small("Important: A1–A4 never produced a result until four silent defects were fixed on 2026-08-16 "
      "— a dead --local_epochs argument, a uint8-hardcoded quantiser, a summary reading test_* from "
      "a CSV holding only val_*, and a 1e-4 verdict threshold.")

head("E23 · NS-3 stress tests", 3)
para("Result: the system holds across round counts up to 250. This sweep also exposed a DEFINITION "
     "DEFECT: update reliability had been computed as hop_success ^ n_rounds — the probability that "
     "ALL rounds succeed — which decays with round count, so any system fails a \">99%\" target for "
     "a long enough run. Per-update reliability is 99.8001%; the whole-run figure is now emitted "
     "under the distinct name run_reliability_all_rounds_pct.")

# ─────────────────────────── 3. HEADLINE RESULT ───────────────────────────
pagebreak()
head("3.  The headline result")
head("E18 · The k-scaling law", 3)
small("All 24 configurations: k ∈ {1,2,4,8} × 3 seeds × 2 arms · per-step budget and "
      "units-per-step held constant")
table(["k", "Record arm AUPRC", "Patient arm AUPRC", "Gap", "95% CI", "p"], [
 ["1", "0.5015", "0.5067", "−0.0052", "[−0.0664, +0.0561]", "0.75"],
 ["2", "0.5590", "0.5084", P("+0.0507"), "[+0.0417, +0.0596]", "0.0017"],
 ["4", "0.5924", "0.5092", P("+0.0832"), "[+0.0694, +0.0971]", "0.0015"],
 ["8", "0.5955", "0.5089", P("+0.0866"), "[+0.0603, +0.1129]", "0.0049"],
])
callout("Why this result is strong — two reasons.",
 "1. IT CARRIES ITS OWN CONTROL. At k=1 a patient IS a record, so the two guarantees are "
 "mathematically identical and the arms must collapse. They do (p = 0.75). A validated null "
 "sitting inside the same experiment as the positive effects. That is what licenses reading the "
 "divergence at larger k as a property of the privacy unit rather than an artefact of the "
 "apparatus.\n\n"
 "2. THE MECHANISM IS ASYMMETRIC. The patient arm is flat in k (0.4967–0.5176 at every k); the "
 "record arm rises (0.5015 → 0.5955). The widening gap is THE RECORD ARM IMPROVING, not the "
 "patient arm degrading. Patient-level noise scales with per-patient contribution, so extra "
 "records buy the patient arm nothing.", "good")
para("Honest limits. AUROC shows the same monotone shape (+0.0006, +0.0094, +0.0133, +0.0132) but "
     "no k reaches significance — every interval includes zero. AUPRC is the resolving metric; "
     "AUROC is directionally consistent but underpowered at n=3. Accuracy is pinned at 0.8005 in "
     "every patient row — an uncalibrated 0.5 threshold on imbalanced data — and MUST NOT BE QUOTED "
     "for these arms.")

# ─────────────────────────── 4. WHAT FAILED ───────────────────────────
pagebreak()
head("4.  What failed — reported in full")
para("The credibility of the positive results depends on these being on the record.")

head("N-A · The refuted central hypothesis (E14, E16, E24)", 3)
para("The project's original central prediction was that record-level DP would leave patients "
     "exposed (attack AUC ≈ 0.70) while patient-level DP defended them (≈ 0.50). A gap of ~0.20 "
     "was predicted.")
table(["Arm", "Best attack AUC (95% CI)", "Difficulty floor", "Margin"], [
 ["Positive control — head-only, no DP", "0.6277  [0.5905, 0.6649]", "0.5626", P("+0.0627")],
 ["Record-level DP", "0.5477  [0.4876, 0.6079]", "0.5252", "+0.0226"],
 ["Patient-level DP", "0.5224  [0.5175, 0.5274]", "0.5167", "+0.0057"],
])
para("Retested at ε=16 (E24), where noise is 13× lower (σ 11.33 → 0.85): record-level 0.5465 "
     "against a floor of 0.5743 — BELOW ITS OWN FLOOR, i.e. confound rather than leakage.")
callout("Verdict: REFUTED, twice, each time with a passing positive control.",
 "WHY IT FAILED. Not a weak attack — the control cleared a gate set BEFORE running. DP-SGD at ε=1 "
 "is simply very strong: σ=11.33 leaves almost no membership signal in EITHER arm. A supporting "
 "clue confirms it: on the patient arm, LiRA scored WORSE than a plain loss threshold (−0.0071). "
 "That is what a defence with nothing left to leak looks like.\n\n"
 "HOW THIS MUST ALWAYS BE WRITTEN: the large predicted effect is refuted; a small effect is NOT "
 "excluded — the interval is ±0.060 wide at n=5. Never write \"there is no effect\".", "bad")

head("E15 · The unexpected finding inside the failure", 3)
table(["Recipe", "Attack AUC", "Member / non-member loss"], [
 ["full-model, no DP", "0.5122", "1.81 / 2.31"],
 ["head-only, no DP", F("0.5847"), "0.013 / 4.95"],
 ["full-model, DP", "0.5206", "6.93 / 7.46"],
])
para("LEAKAGE IS A PROPERTY OF THE RECIPE, NOT THE TASK. Head-only fine-tuning — our own efficiency "
     "mechanism — memorises members far harder than full-model training (p = 1e−9, sd 0.0018 over 6 "
     "runs). A genuine caveat to the parameter-efficient DP fine-tuning literature, and a caveat "
     "against our own recipe. It became claim N-A′ when N-A failed.")

head("Other characterised negatives", 3)
table(["Item", "Outcome"], [
 ["E9  SADP — adaptive per-group budget",
  F("Underperforms uniform DP at equal ε BY CONSTRUCTION. The cross-group composition tax drives "
    "σ from 11.3 to 70. Lesson: splitting a budget across groups is paid for at a punitive rate "
    "under composition.")],
 ["E12  INT8 edge quantisation",
  F("1.90× slower on CPU, 3.25× slower on GPU than FP32, and misses the 4 MB target at 6.55 MB. "
    "Two causes: dynamic quantisation only accelerates MatMul/Gemm while this model is dominated "
    "by convolutions and a recurrent path; and on CUDA the quantised ops have no GPU kernel, so "
    "the runtime inserts 3180 Memcpy nodes — exactly the 3.25× penalty. Deploy FP32.")],
 ["ASWA aggregation", F("+0.0005 AUROC. Deleted from the codebase.")],
 ["E19  Fusion gain, corrected",
  W("At 2 seeds: +0.0411 AUROC, +0.1062 AUPRC. At 5 seeds: +0.0370 and +0.0671 — AUPRC FELL 37%. "
    "Only the 5-seed figures may be quoted.")],
 ["Legacy corpus (ECG + chest X-ray)",
  F("Withdrawn entirely. Its modalities were paired by a construction rule (CXR bucket = f(ECG "
    "label)) rather than by provenance, so no result on it was evidence of fusion.")],
 ["WEAR accuracy objective (O2b)",
  W("Inconclusive. Seed count pre-registered at 15 and deliberately not extended.")],
 ["E19  WEAR fusion",
  W("At ceiling. Best single modality already 0.9976, so the task has no headroom. Structurally "
    "unable to corroborate the fusion claim.")],
])

head("E19 · Multimodal fusion — the mixed result", 3)
table(["Arm", "VitalDB AUROC", "WEAR AUROC"], [
 ["Modality A only (signals / inertial)", "0.8283 ± 0.0062", "0.9976"],
 ["Modality B only (clinical / video)", "0.7680 ± 0.0033", "0.9957"],
 ["Fused", P("0.8653 ± 0.0052"), "0.9980"],
 ["Gain over best unimodal", P("+0.0370  (5.9× seed sd)"), W("+0.0004  (ceiling)")],
])

# ─────────────────────────── 5. THE GAP ───────────────────────────
pagebreak()
head("5.  The outstanding gap — and what is being done about it")
callout("The one question the project cannot currently answer.",
 "Every privacy claim rests on ONE DATASET FROM ONE HOSPITAL. VitalDB is a single institution and "
 "its nine \"clients\" are a partition we created ourselves. WEAR cannot help — 22 people, one "
 "client each, no patient contributing enough records for the k-law to even be defined.\n\n"
 "A reviewer will ask, and it is the right question:\n"
 "\"Is this a property of patient-level private federated learning, or a property of your dataset?\"",
 "bad")

head("The answer: eICU-CRD", 2)
table(["Property of eICU-CRD", "Why the research needs it"], [
 ["208 real hospitals", "Clients become actual institutions rather than a partition we invented"],
 ["~139,000 patients", "Different demographics, care patterns, equipment. If the law survives that, it is structural"],
 ["Many records per patient", "VitalDB tops out near k=8. eICU stretches the curve into a range VitalDB cannot reach. THIS IS THE DECISIVE PROPERTY."],
 ["Same modality structure", "Time-series vitals + static clinical. No new encoder needed"],
 ["Credentialed + CITI trained", "Reviewers trust PhysioNet; the access process is itself evidence of proper conduct"],
])
small("Access granted. BRSET also granted, parked until eICU is complete.")

head("The rule that makes this experiment worth running", 2)
callout("Freeze the prediction before touching the data.",
 "We will NOT simply run the same experiment and add another table. That is worth little.\n\n"
 "Instead: fit the k-curve on VitalDB, write down a NUMERIC prediction of the gap at eICU's k, "
 "FREEZE THAT PREDICTION BEFORE TOUCHING THE DATA, then test it.\n\n"
 "Why frozen first: if we fit the curve, look at eICU, and then write the prediction, no reviewer "
 "can distinguish that from retrofitting — and neither can we.", "info")

head("The frozen forecast (committed before the build)", 2)
para("Fitted on VitalDB data alone:", space=2)
para("gap(k)  =  0.0878 · ( 1 − exp( −0.883 · (k−1) ) )", size=11, bold=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, space=2)
para("A = 0.0878 ± 0.0035    ·    b = 0.883 ± 0.129    ·    RMSE = 0.0028",
     size=8.5, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, space=6)
table(["k", "Predicted gap", "Acceptance band (±0.030)"], [
 ["1", "+0.000", "−0.030 … +0.030   (control)"], ["2", "+0.052", "+0.022 … +0.082"],
 ["4", "+0.082", "+0.052 … +0.112"], ["8", "+0.088", "+0.058 … +0.118"],
 ["16", "+0.088", "+0.058 … +0.118"], ["32", "+0.088", "+0.058 … +0.118"],
])
para("The curve SATURATES — 90% of the ceiling by k = 3.6. That is the risky content of the "
     "forecast, and it is testable ONLY at k > 8, which is precisely what VitalDB cannot do and "
     "eICU can.")

# ─────────────────────────── 6. NEXT ───────────────────────────
pagebreak()
head("6.  What happens next")
head("Execution order — every step has a gate", 2)
table(["Step", "Experiment", "Gate"], [
 ["E0", ("Commit the pre-registration", None, True), F("Must precede the build. Non-negotiable.")],
 ["E1", "Verify schema against real headers", "Fix any mismatched constant first"],
 ["E2", "Build corpus", "—"],
 ["E3", "Validate corpus", "Do not proceed past a CAPACITY failure"],
 ["E4", "Ceiling check (single-modality arms)", W("Stop if better arm > 0.95 AUROC — the check WEAR failed")],
 ["E5", "Pretrain encoders, disjoint population", "So eICU does not inherit the oracle caveat"],
 ["E6", "Main operating point", "ε = 0.80 + 0.20 conformal, 10 rounds, τe = 5"],
 ["E7", "Objective verification O1–O4", "—"],
 ["E8", ("k-scaling — THE experiment", None, True), P("k ∈ {1,2,4,8,16,32}. k=1 is the built-in control; k=16, 32 are the point of the corpus")],
 ["E9", "LiRA + non-private positive control", "A null without a passing control is inadmissible"],
 ["E10", "Component ablation A0–A5", "—"],
 ["E11", "Uplink / compression", "Re-measure, do not assume"],
])

head("How each remaining gap closes", 2)
table(["Gap", "Closed by"], [
 ["Every claim rests on one single-institution dataset", "E8 on 208 real hospitals"],
 ["Is the k-law structural or dataset-specific? Unanswerable", "E8 against the frozen numeric forecast"],
 ["Curve cannot be stretched past VitalDB's k", "E8 at k = 16, 32"],
 ["Encoders pretrained in oracle mode; ε=1 not end-to-end", "E5 with the disjoint population"],
 ["Fusion single-domain; gain shrank at 5 seeds", "E4 at 5 seeds, reported as a setting result"],
 ["MIA null needs statistical power", "E9 at ~139,000 patients"],
 ["Federation is constructed, not natural", "E10 — hospitals taken as given"],
])

head("Independent of eICU — still open", 2)
table(["Item", "Why it matters"], [
 ["Window-count-normalised patient clipping",
  ("THE ONLY REMAINING CANDIDATE FOR AN ORIGINAL MECHANISM rather than a measurement. A patient's "
   "gradient is summed over k windows then clipped to a fixed bound, systematically down-weighting "
   "long recordings. Normalising before clipping should correct it. Needs no new data.", None, True)],
 ["Conformal coverage validation",
  "The guarantee is implemented and its cost composed into the reported ε, but empirical coverage has never been measured"],
 ["Worst-case MIA reporting (TPR at 0.1% FPR)",
  "Average AUC hides the tail. The confident identifications are the real clinical disclosure. Machinery already exists; cost is low"],
 ["Mask-channel ablation", "Would convert the E20 attribution evidence into proof"],
 ["Multi-seed baselines", "Would put confidence intervals on E4"],
])

# ─────────────────────────── 7. HOW IT ENDS ───────────────────────────
pagebreak()
head("7.  How the research ends")
para("The eICU experiment has two possible outcomes, and BOTH ARE PUBLISHABLE. That is by design — "
     "it is what makes the experiment worth running rather than decorative.")
table(["Outcome", "What it means"], [
 [P("The prediction lands"),
  "The cost of a patient-level guarantee is shown to be STRUCTURAL rather than dataset-specific, "
  "and the work delivers a transferable design rule: given your k, this is what patient-level ε=1 "
  "will cost you. That is what a practitioner actually needs, and it has not been published."],
 [W("The prediction misses"),
  "The work has found a BOUNDARY CONDITION, with a dated forecast proving the story was not "
  "adjusted after the fact. Also publishable, and visibly honest."],
])
callout("Either way, the paper is stronger.",
 "A paper reporting that two independent clinical datasets were tested — one reproducing the "
 "result and the other exposing a limitation — is MORE publishable than one in which everything "
 "conveniently succeeded.", "good")

head("What is genuinely ours, and what is not", 2)
table(["Prior art — do not claim", "Genuinely this work's contribution"], [
 ["Patient-level / user-level DP (McMahan et al., 2018)",
  ("THE k-SCALING LAW ITSELF — the measured relationship between records-per-person and the cost "
   "of a person-level guarantee. Not previously published.", None, True)],
 ["Head-only / parameter-efficient DP fine-tuning (Li, Yu et al., 2021)",
  ("THE SELF-CONTROLLING EXPERIMENT DESIGN — the k=1 null built into the same experiment as the "
   "effect.", None, True)],
 ["Exponential-mechanism DP quantile release (Smith, 2011)",
  ("AN AUDIT THAT CAN RETURN AN INFORMATIVE NEGATIVE — every attack reported alongside a positive "
   "control on a configuration known to memorise.", None, True)],
 ["Hierarchical federated learning (HED-FL and others)",
  ("A FINDING THAT ARGUES AGAINST OUR OWN RECIPE — head-only training memorises harder (0.5847 vs "
   "0.5122), reported rather than buried.", None, True)],
])
small("The contributions are MEASUREMENTS AND AUDITING PRACTICE in a setting where they have not "
      "been measured — not new mechanisms. The manuscript must not say \"we propose patient-level DP\".")

head("The final claim", 2)
callout("",
 "Stating your privacy guarantee over people instead of over records costs accuracy — and that "
 "cost is not a constant. It grows with how many records each person contributes, then saturates. "
 "Here is the curve, here is the control that proves the curve is real, and here is the "
 "independent corpus that says it is not just our data.", "info")

small("Sources: Research Dossier Parts 1–3; Complete Experiment Log E1–E24; "
      "document/01_planning/plan.md rev 3; document/01_planning/PREREGISTRATION_EICU.md; "
      "Phase Reports 1–6. All values quoted are from measured artifacts on disk.")

import sys
doc.save(sys.argv[1] if len(sys.argv) > 1 else "HFL.docx")
print("docx saved")
