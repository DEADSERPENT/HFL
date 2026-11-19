# Glossary

| Term | Plain-language meaning |
|---|---|
| **Federated learning (FL)** | Training a shared model where the data lives; only model updates are exchanged. |
| **Hierarchical FL (HFL)** | FL with an edge tier between clients and cloud; edges aggregate locally for several rounds. |
| **Client** | A data holder: a hospital (eICU), a surgical specialty (VitalDB) or a wearable participant (WEAR). |
| **Edge aggregator** | A nearby server that averages its clients' updates before reporting to the cloud. |
| **FedAvg** | Weighted averaging of client models into a global model. |
| **Differential privacy (DP)** | A guarantee that the output barely changes whether or not one unit's data is used. |
| **ε (epsilon)** | Privacy-loss budget; smaller is stronger. ε ≤ 1 is considered strong. |
| **δ (delta)** | Small probability that the ε bound fails; here 10⁻⁵. |
| **DP-SGD** | Private training: clip each unit's gradient, add Gaussian noise. |
| **Clipping norm C** | Maximum size allowed for a unit's gradient (C = 1). |
| **Noise multiplier σ** | Noise standard deviation relative to C. |
| **Privacy unit** | What the guarantee protects: one record, one patient, or one client. |
| **Record-level DP** | Protects one window/record. |
| **Patient-level (user-level) DP** | Protects all records of one patient together. |
| **Group privacy** | Converting a record-level guarantee to a group; ε grows with group size. |
| **Poisson sampling** | Each unit is included independently with probability q. |
| **Parallel composition** | Mechanisms on disjoint people do not add up their budgets. |
| **Adaptive composition** | Budgets of sequential steps add up (tracked by an accountant). |
| **Post-processing** | Any computation on a DP output stays DP at no extra cost. |
| **PLD accountant** | Privacy-loss-distribution accountant; a tight budget calculator. |
| **Rényi (RDP) accountant** | Another, looser budget calculator; used as a cross-check. |
| **Transcript** | Everything the system releases: client updates, edge/cloud models, chosen checkpoint. |
| **End to end** | The guarantee also covers encoders and normalization constants. |
| **Disjoint encoders** | Encoders pretrained on people who are not in any client's data. |
| **Oracle encoders** | Encoders pretrained on the client training data; results are upper bounds. |
| **Fusion head** | The small network that combines both modality embeddings and predicts. |
| **Multimodal** | Using two or more kinds of data (e.g., waveforms + clinical variables). |
| **Paired at source** | Both modalities come from the same person and time, not matched by a rule. |
| **k** | Number of records per individual. |
| **A(1 − 1/k)** | The scaling law for the cost of patient-level vs. record-level privacy. |
| **Top-κ sparsification** | Sending only the largest 20 % of update values. |
| **Quantization** | Representing values with fewer bits (8 bits). |
| **Error feedback** | Keeping the unsent residual locally and adding it to the next update. |
| **AUROC** | Area under the ROC curve; ranking quality (0.5 = chance, 1 = perfect). |
| **AUPRC** | Area under the precision–recall curve; informative for rare outcomes. |
| **Balanced accuracy** | Mean of sensitivity and specificity; robust to imbalance. |
| **Youden's index** | Threshold choice maximizing sensitivity + specificity − 1. |
| **Paired seeds** | Comparing two configurations run with the same random seeds. |
| **Resolved** | The 95 % interval of a difference excludes zero. |
| **Inconclusive** | The interval spans the target threshold. |
| **Membership inference (MIA)** | An attack that guesses whether someone was in the training set. |
| **LiRA** | Likelihood-ratio attack using shadow models; a strong MIA. |
| **Shadow models** | Models trained on random halves of the population to calibrate the attack. |
| **Positive control** | A setting known to leak (no DP), proving the attack works. |
| **Difficulty floor** | Attack AUC from per-patient difficulty alone, without the target model. |
| **Conformal prediction** | Produces prediction sets with a coverage guarantee; tested privately and removed. |
| **ns-3** | Packet-level network simulator (v3.46) used for delivery and round latency. |
| **CloudSim Plus** | Edge–cloud resource and energy simulator (v8.5). |
| **ONNX Runtime** | Inference engine used to time model latency. |
| **P95 latency** | The latency below which 95 % of requests complete. |
| **HED-FL** | Prior hierarchical, energy-efficient FL system without DP. |
| **FL2DP** | Prior DP + shuffling FL system without hierarchy. |
| **VitalDB** | Open surgical dataset (intraoperative vitals + pre-op variables). |
| **eICU** | Multi-centre ICU database (PhysioNet, credentialed). |
| **WEAR** | Wearable inertial + egocentric video activity dataset. |
| **APACHE score** | Clinician-computed ICU severity score. |
