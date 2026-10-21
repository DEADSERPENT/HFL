# Phase 5 Results — HFL for Healthcare IoT
# Generated:,2026-09-06 10:59:39

## SECTION 1: Accuracy Comparison (B0–B5 vs P1)
system,accuracy,macro_auc,epsilon,rounds,source_file
B0 Centralized,0.7764945652173914,0.861175893605332,N/A,N/A,baseline_b0.csv
B1 Local Only,0.8157388986064373,0.78725984535602,N/A,N/A,baseline_b1.csv
B2 FedAvg,0.7972826086956522,0.8173120945409745,N/A,10,baseline_b2.csv
B3 FedProx,0.7857336956521739,0.8153841120181432,N/A,10,baseline_b3.csv
B4 DP-FedAvg,0.8005434782608696,0.7364005320103368,0.963441782468697,10,baseline_b4.csv
B5 MOON,0.7639945652173913,0.8430724429374518,N/A,10,baseline_b5.csv
HFL-MM-HC (P1),0.8233,0.8429,0.7705,10,proposed_vitaldb.csv
HFL-MM-HC DP-off (ε=1000),0.6437,0.8731,1033.9038,20,eps1000_headonly_nodp.csv
HFL-MM-HC ε=inf,0.5653,0.8199,inf,N/A,epsilon_sweep_summary.csv

## SECTION 2: Inference Latency (source: latency_vitaldb.json)
metric,value
latency_p50_ms,4.366
latency_p95_ms,4.582
latency_p99_ms,5.139
latency_mean_ms,4.401

## SECTION 3: QoS Target Validation
qos_target,value,status,basis
Comm reduction ≥ 50%,N/A,N/A,
Energy saving ≥ 20%,N/A,N/A,
Update reliability > 99%,98.894,FAIL,
Inference P95 < 100ms,4.582,PASS,
Accuracy loss ≤ 2% at ε=1,3.46%,FAIL,vs DP-off same-arch comparator (valid); single seed — 3-seed stats in RESULTS.md
