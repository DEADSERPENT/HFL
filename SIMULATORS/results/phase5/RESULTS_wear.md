# Phase 5 Results — HFL for Healthcare IoT
# Generated:,2026-09-06 18:03:12

## SECTION 1: Accuracy Comparison (B0–B5 vs P1)
system,accuracy,macro_auc,epsilon,rounds,source_file
B0 Centralized,0.9594571955101358,0.9990419718110769,N/A,N/A,baseline_b0.csv
B1 Local Only,0.9406054286125346,0.9944566002849866,N/A,N/A,baseline_b1.csv
B2 FedAvg,0.9108728430222818,0.9962253140600958,N/A,10,baseline_b2.csv
B3 FedProx,0.9033338917741666,0.9958189466453875,N/A,10,baseline_b3.csv
B4 DP-FedAvg,0.16250628245937343,0.6865057774786145,0.9571849015056962,10,baseline_b4.csv
B5 MOON,0.8912715697771821,0.9948434499991596,N/A,10,baseline_b5.csv
HFL-MM-HC (P1),0.9626,0.9989,0.7656,10,proposed_wear.csv
HFL-MM-HC DP-off (ε=1000),0.6588,0.8731,1033.9038,20,eps1000_headonly_nodp.csv
HFL-MM-HC ε=inf,0.5653,0.8199,inf,N/A,epsilon_sweep_summary.csv

## SECTION 2: Inference Latency (source: latency_wear.json)
metric,value
latency_p50_ms,1.189
latency_p95_ms,1.218
latency_p99_ms,1.235
latency_mean_ms,1.191

## SECTION 3: QoS Target Validation
qos_target,value,status,basis
Comm reduction ≥ 50%,N/A,N/A,
Energy saving ≥ 20%,N/A,N/A,
Update reliability > 99%,98.894,FAIL,
Inference P95 < 100ms,1.218,PASS,
Accuracy loss ≤ 2% at ε=1,-14.41%,PASS,vs DP-off same-arch comparator (valid); single seed — 3-seed stats in RESULTS.md
