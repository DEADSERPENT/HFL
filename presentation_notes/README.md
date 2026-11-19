# Presentation Notes — PP-HFM

Notes for presenting and explaining the research
**"Patient-Level Differential Privacy in Hierarchical Federated Learning for Multimodal Medical IoT."**
Every number comes from the final manuscript in `PLDP/` (research frozen 4 Nov 2026).

## Files

| File | Purpose | When to use |
|---|---|---|
| `01_Research_Explained.md` | The whole study explained section by section, from background to conclusion | Read fully before presenting |
| `02_Presentation_Script.md` | 21 slides: what goes on each slide, what to say, timings (~20 min) | Build the slides from it and rehearse |
| `03_Key_Numbers.md` | One-page sheet of every important number | Print it and keep it beside you |
| `04_Questions_and_Answers.md` | 30 likely questions with model answers | Viva or Q&A preparation |
| `05_Glossary.md` | Plain-language definitions of all terms | For the audience or a quick check |
| `figures/` | All paper figures (PDF for slides, PNG for preview) | Insert into slides |

## Figure Map

| Figure | Used on slide | Shows |
|---|---|---|
| `fig01_overview_core` | 6 | Client–edge–cloud architecture |
| `fig2_backbone` | 7 | Encoder–fusion model |
| `fig02_privacy_unit` | 8 | Per-window vs. per-patient clipping |
| `fig00_workflow` | 12 | Study workflow |
| `fig09_system_cost` | 13 | Uplink, round latency, energy |
| `fig05_init_vs_subset` | 15 | Initialization vs. subset effect |
| `fig03_klaw` | 16 | The A(1 − 1/k) law, VitalDB and eICU |
| `fig04_arms` | 16 (optional) | Each arm's AUPRC against k |
| `fig06_fusion_map` | 17 | Fusion gain vs. modality imbalance |
| `fig10_ablation_mia` | 17–18 | Ablation and membership-inference audit |
| `fig4_lira` | 18 (optional) | How LiRA calibrates per patient |

## Suggested Preparation

1. Read `01_Research_Explained.md` once, end to end.
2. Build slides from `02_Presentation_Script.md`; keep text on slides short.
3. Rehearse the four key slides (8, 14, 16, 18) until you can explain them without notes.
4. Go through `04_Questions_and_Answers.md` and answer each question aloud.
5. On the day, keep `03_Key_Numbers.md` printed.
