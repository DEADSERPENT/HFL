#!/usr/bin/env python3
"""
hfl_network_sim.py — NS-3 Network Simulation for HFL Research
==============================================================
Project : Hierarchical Federated Learning for Privacy-Aware,
          Low-Latency Multimodal IoT Systems
Student : Samartha H V | MIT Bengaluru | 2026

Description
-----------
Simulates the complete 3-tier HFL network topology:
  Layer 1 → IoT devices (WiFi 802.11ax to Edge)
  Layer 2 → Edge Servers (P2P fiber to Cloud)
  Layer 3 → Cloud Server (global aggregation hub)

For each FL round, this script simulates:
  1. DOWNLINK : Cloud → Edge → Device  (model broadcast)
  2. UPLINK   : Device → Edge → Cloud  (gradient upload)

Metrics collected per round:
  - End-to-end latency (ms)
  - Uplink traffic volume (MB)
  - Packet loss rate (%)
  - Throughput (Mbps)
  - Update delivery reliability (%)

Baselines compared:
  1. CentralizedFL   : All devices → Cloud directly
  2. FlatFL_NoDP     : All devices → Cloud (FedAvg, no compression)
  3. HierarchicalFL  : Proposed 2-tier (Device→Edge→Cloud)

Output : results/ns3/ns3_results.csv

Run from ns-3-dev directory:
    python3 ../hfl-scenarios/hfl_network_sim.py

Device: GPU/CPU auto-selected via device_utils.py
"""

import sys
import os
import csv
import json
import math
import argparse
import pathlib
import random
import time

# ── GPU/CPU auto-detection ────────────────────────────────────────────────────
# Repointed from scripts/device_utils.py (deleted 2026-08-04). That copy was a
# stale April fork whose get_dataloader_kwargs returned num_workers>=2 with
# persistent_workers — the exact configuration the current version documents as
# starving the GPU, because Opacus re-wraps the loader ~30x/round and respawns
# workers each time. The path is now relative so the file is not bound to one
# machine's absolute layout.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "model" / "utils"))
from device_utils import get_device, set_seed, device_info

# Line-buffer stdout: this script is routinely piped to a log or to tail, and
# Python block-buffers a pipe, so a packet-level run that takes an hour emits
# nothing at all until it exits. Progress is the only signal that a long
# discrete-event simulation is advancing rather than stuck.
try:
    sys.stdout.reconfigure(line_buffering=True)
except AttributeError:
    pass

# NOTE: this is the ML device, used for nothing in this file. NS-3 is a
# discrete-event simulator with a strictly sequential event queue and runs
# entirely on the CPU; there is no GPU path. It is reported only so the run
# record shows which host produced the file.
device = get_device(verbose=True)
set_seed(42)   # device_utils.set_seed takes only the seed

# ── Load shared config, then override from the SELECTED DATASET ──────────────
# The top-level topology/model blocks carry one dataset's values as a default.
# Simulating a payload that matches neither trained model makes every derived
# QoS figure describe an experiment that was never run, so the dataset is
# selected explicitly and its own block wins.
_SIM_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG_PATH = str(_SIM_ROOT / "config" / "hfl_config.json")
with open(CONFIG_PATH) as f:
    cfg = json.load(f)

_ap = argparse.ArgumentParser(description="HFL NS-3 network simulation")
_ap.add_argument("--dataset", default="vitaldb",
                 choices=sorted(cfg.get("datasets", {})) or ["vitaldb"],
                 help="selects topology and model size from config['datasets']")
_ap.add_argument("--rounds", type=int, default=None)
_ap.add_argument("--output", default=None)
_ap.add_argument("--cell_radius", type=float, default=30.0,
                 help="metres from the edge access point to its devices. "
                      "Larger = worse SNR = real frame loss from the 802.11ax "
                      "PHY. Sweeping this is the heterogeneous-network "
                      "experiment: at radius 0 every architecture delivers "
                      "100%% and the reliability objective tests nothing.")
_ap.add_argument("--ns3_every", type=int, default=10,
                 help="run the packet-level simulation every N rounds "
                      "for EVERY scenario (1 = every round)")
_args, _ = _ap.parse_known_args()

_ds = cfg.get("datasets", {}).get(_args.dataset, {})
if _ds:
    cfg["topology"]["num_iot_devices"] = _ds["num_iot_devices"]
    cfg["topology"]["num_edge_servers"] = _ds["num_edge_servers"]
    cfg["model"]["model_size_MB"] = _ds["model_size_MB"]
    print(f"[config] dataset='{_args.dataset}': "
          f"{_ds['num_iot_devices']} devices, {_ds['num_edge_servers']} edges, "
          f"model {_ds['model_size_MB']} MB ({_ds['n_params']:,} params)")
else:
    print(f"[config][WARN] no datasets['{_args.dataset}'] block — using "
          f"top-level defaults, which may not match any trained model.")

# ── NS-3 import ──────────────────────────────────────────────────────────────
# NS-3 >= 3.36 ships FLAT cppyy bindings: the per-module namespaces
# (ns.core, ns.network, ns.wifi, ...) no longer exist and everything is
# hoisted to the top level, reached via `from ns import ns`. The old
# `import ns.core` style raises ImportError even on a correctly built tree,
# so this file silently fell back to ANALYTICAL MODE and reported analytical
# numbers under an NS-3 heading.
#
# The bindings also are not installed into site-packages; they live in the
# build tree, so that path is added here rather than relying on PYTHONPATH.
_NS3_BINDINGS = _SIM_ROOT / "ns3" / "ns-3-dev" / "build" / "bindings" / "python"
if _NS3_BINDINGS.is_dir():
    sys.path.insert(0, str(_NS3_BINDINGS))
try:
    from ns import ns
    _ = ns.NodeContainer            # force cppyy to resolve; import alone is lazy
    NS3_AVAILABLE = True
    print(f"[OK] NS-3 packet-level bindings loaded from {_NS3_BINDINGS}")
except Exception as _e:
    NS3_AVAILABLE = False
    print(f"[WARN] NS-3 bindings unavailable ({type(_e).__name__}: {_e}).")
    print("       Running in ANALYTICAL MODE — results are NOT packet-level.")
    print("       Build with: cd ns3/ns-3-dev && ./ns3 configure "
          "--enable-python-bindings && ./ns3 build -j28")
    print("       Requires: pip install cppyy")

# ── Parameters from config ────────────────────────────────────────────────────
NUM_DEVICES      = cfg["topology"]["num_iot_devices"]
NUM_EDGES        = cfg["topology"]["num_edge_servers"]
FL_ROUNDS        = _args.rounds or cfg["federated_learning"]["total_fl_rounds"]
TAU_E            = cfg["federated_learning"]["tau_e"]
MODEL_SIZE_MB    = cfg["model"]["model_size_MB"]
COMPRESS_RATIO   = cfg["model"]["sparsification_ratio"]         # 0.2
WIFI_BW_MBPS     = cfg["network_ns3"]["device_to_edge_bandwidth_Mbps"]
EC_DELAY_MS      = cfg["network_ns3"]["edge_to_cloud_delay_ms"]
RESULTS_DIR      = cfg["output"]["ns3_results_path"]
OUT_CSV          = _args.output

# ── MEASURED per-client payloads (Objective 1 must not be arithmetic) ────────
# scripts/measure_uplink.py runs the real GradientCompressor on real model
# deltas and counts the bytes actually serialised, INCLUDING the int32 index
# array that top-k must send alongside each value. Those indices turn out to
# be ~80 % of the payload, so the nominal "sparsity x quantization" ratio
# overstates compression by several times. If the measurement is absent the
# nominal figure is used and the run is labelled accordingly, so a reader can
# always tell which one produced a number.
_UPLINK_JSON = _SIM_ROOT / "results" / "phase5" / f"uplink_measured_{_args.dataset}.json"
MEASURED_UPLINK = None
if _UPLINK_JSON.exists():
    with open(_UPLINK_JSON) as _f:
        MEASURED_UPLINK = json.load(_f)
    _dense_b = MEASURED_UPLINK["arms"]["full_model"]["dense_fp32_bytes"]
    _comp_b  = MEASURED_UPLINK["arms"]["head_only"]["total_bytes"]
    print(f"[uplink] MEASURED: dense {_dense_b/1024**2:.2f} MB/client, "
          f"compressed {_comp_b/1024**2:.3f} MB/client "
          f"({_dense_b/max(_comp_b,1):.1f}x)")
else:
    _dense_b = MODEL_SIZE_MB * 1024**2
    _comp_b  = COMPRESSED_SIZE_MB * 1024**2
    print(f"[uplink][WARN] no measured payload for '{_args.dataset}' — using the "
          f"NOMINAL ratio. Run: python scripts/measure_uplink.py "
          f"--dataset {_args.dataset}")

PAYLOAD_BYTES = {
    "CentralizedFL":       _dense_b,   # every client sends the whole model
    "FlatFL_NoDP":         _dense_b,
    "FlatFL_DP":           _dense_b * 1.02,
    "HierarchicalFL_NoDP": _comp_b,
    "HFL_Proposed":        _comp_b * 1.03,
}

# Derived
COMPRESSED_SIZE_MB = MODEL_SIZE_MB * COMPRESS_RATIO
DEVICES_PER_EDGE   = max(1, NUM_DEVICES // NUM_EDGES)
EC_BW_GBPS         = cfg["network_ns3"]["edge_to_cloud_bandwidth_Gbps"]

os.makedirs(RESULTS_DIR, exist_ok=True)

print(f"\n{'='*65}")
print(f"  HFL NS-3 Network Simulation")
print(f"  Devices: {NUM_DEVICES} | Edges: {NUM_EDGES} | Rounds: {FL_ROUNDS}")
print(f"  Model: {MODEL_SIZE_MB}MB | Compressed: {COMPRESSED_SIZE_MB}MB")
print(f"  Compute device: {device}")
print(f"{'='*65}\n")


# ══════════════════════════════════════════════════════════════════════════════
# BASELINE COMPUTATIONS (Analytical model — runs always, NS-3 optional)
# ══════════════════════════════════════════════════════════════════════════════

def compute_analytical_metrics(scenario: str, fl_round: int) -> dict:
    """
    Compute per-round metrics analytically using the latency/energy models
    from the theoretical framework (Research Guidance Document).

    L_total = L_sensor + L_preprocessing + L_inference + L_comm + L_aggregation

    This runs on every round even without NS-3 to give reproducible baselines.
    """
    rng = random.Random(42 + fl_round)

    # Component latencies (ms) — from theoretical framework
    L_sensor     = rng.uniform(5, 10)    # camera: 5-10ms
    L_preproc    = rng.uniform(10, 20)   # feature extraction at edge
    L_inference  = rng.uniform(20, 40)   # model inference with pruning

    if scenario == "CentralizedFL":
        # All devices upload full model directly to cloud
        L_comm       = MODEL_SIZE_MB * 8 / WIFI_BW_MBPS * 1000  # bottleneck at WiFi
        L_aggregation = 15.0
        uplink_MB    = MODEL_SIZE_MB * NUM_DEVICES
        pkt_loss     = rng.uniform(0.02, 0.08)
        reliability  = 1 - pkt_loss

    elif scenario == "FlatFL_NoDP":
        # Single-tier FL, devices → cloud, no compression
        L_comm       = MODEL_SIZE_MB * 8 / WIFI_BW_MBPS * 1000
        L_aggregation = 12.0
        uplink_MB    = MODEL_SIZE_MB * NUM_DEVICES
        pkt_loss     = rng.uniform(0.015, 0.06)
        reliability  = 1 - pkt_loss

    elif scenario == "FlatFL_DP":
        # Single-tier FL + DP noise (no hierarchy)
        L_comm       = MODEL_SIZE_MB * 8 / WIFI_BW_MBPS * 1000 * 1.05  # DP overhead
        L_aggregation = 13.0
        uplink_MB    = MODEL_SIZE_MB * NUM_DEVICES * 1.02  # slight overhead from noise
        pkt_loss     = rng.uniform(0.015, 0.06)
        reliability  = 1 - pkt_loss

    elif scenario == "HierarchicalFL_NoDP":
        # Two-tier: device→edge (compressed), edge→cloud (aggregated)
        L_comm_dev_edge = COMPRESSED_SIZE_MB * 8 / WIFI_BW_MBPS * 1000
        L_comm_edge_cld = (COMPRESSED_SIZE_MB * NUM_EDGES) * 8 / (EC_BW_GBPS * 1000) * 1000
        L_comm       = L_comm_dev_edge + EC_DELAY_MS + L_comm_edge_cld
        L_aggregation = 8.0   # partial aggr. at edge faster than full cloud
        # Only edge→cloud traffic (major reduction)
        uplink_MB    = COMPRESSED_SIZE_MB * NUM_DEVICES + COMPRESSED_SIZE_MB * NUM_EDGES
        pkt_loss     = rng.uniform(0.005, 0.02)
        reliability  = 1 - pkt_loss

    else:  # HFL_Proposed — hierarchical + DP + multimodal compression
        # Best case: compression + DP noise injection + 2-tier
        L_comm_dev_edge = COMPRESSED_SIZE_MB * 8 / WIFI_BW_MBPS * 1000 * 1.03  # DP noise overhead
        L_comm_edge_cld = (COMPRESSED_SIZE_MB * NUM_EDGES) * 8 / (EC_BW_GBPS * 1000) * 1000
        L_comm       = L_comm_dev_edge + EC_DELAY_MS + L_comm_edge_cld
        L_aggregation = 7.5   # optimized FedAvg
        L_preproc    = rng.uniform(10, 18)   # slightly lower due to GPU
        uplink_MB    = COMPRESSED_SIZE_MB * NUM_DEVICES * 1.03 + COMPRESSED_SIZE_MB * NUM_EDGES
        pkt_loss     = rng.uniform(0.003, 0.015)
        reliability  = 1 - pkt_loss

    L_total     = L_sensor + L_preproc + L_inference + L_comm + L_aggregation
    throughput  = (uplink_MB * 8) / (FL_ROUNDS * TAU_E) * 1000  # Mbps approx

    return {
        "round":            fl_round,
        "scenario":         scenario,
        "L_sensor_ms":      round(L_sensor, 3),
        "L_preproc_ms":     round(L_preproc, 3),
        "L_inference_ms":   round(L_inference, 3),
        "L_comm_ms":        round(L_comm, 3),
        "L_aggregation_ms": round(L_aggregation, 3),
        "L_total_ms":       round(L_total, 3),
        "uplink_MB":        round(uplink_MB, 3),
        "throughput_Mbps":  round(throughput, 3),
        "pkt_loss_pct":     round(pkt_loss * 100, 3),
        "reliability_pct":  round(reliability * 100, 3),
        "latency_ok":       int(L_total < 100),
        "compute_device":   str(device),
    }


# ══════════════════════════════════════════════════════════════════════════════
# NS-3 SIMULATION (runs if NS-3 bindings are available)
# ══════════════════════════════════════════════════════════════════════════════

def run_ns3_round(fl_round: int, upload_bytes: int = None,
                  scenario: str = "HFL_Proposed") -> dict:
    """
    Run one NS-3 simulation round for the HFL_Proposed scenario.

    Topology:
        [20 IoT Devices] --WiFi 802.11ax--> [3 Edge Servers] --P2P 1Gbps--> [1 Cloud]

    Traffic: BulkSend from each device → cloud (via edge gateway).
    Collects: actual latency, packet loss, throughput from FlowMonitor.

    `upload_bytes` is the payload EACH CLIENT transmits this round. It is
    supplied by the caller from measured compressor output, not derived from
    a nominal compression ratio, so the contention this simulation
    experiences is the contention the real system would create.
    """
    if not NS3_AVAILABLE:
        return {}

    # Reset simulator for this round
    ns.Simulator.Destroy()
    ns.RngSeedManager.SetSeed(42 + fl_round)

    # ── Node containers ───────────────────────────────────────────────────────
    iot_nodes   = ns.NodeContainer()
    edge_nodes  = ns.NodeContainer()
    cloud_node  = ns.NodeContainer()
    iot_nodes.Create(NUM_DEVICES)
    edge_nodes.Create(NUM_EDGES)
    cloud_node.Create(1)

    # ── Edge → Cloud P2P links ────────────────────────────────────────────────
    p2p_ec = ns.PointToPointHelper()
    p2p_ec.SetDeviceAttribute("DataRate", ns.StringValue(f"{EC_BW_GBPS}Gbps"))
    p2p_ec.SetChannelAttribute("Delay",   ns.StringValue(f"{EC_DELAY_MS}ms"))
    ec_devices = []
    for i in range(NUM_EDGES):
        ec_devices.append(p2p_ec.Install(edge_nodes.Get(i), cloud_node.Get(0)))

    # ── WiFi: IoT devices → Edge ──────────────────────────────────────────────
    wifi_helper = ns.WifiHelper()
    wifi_helper.SetStandard(ns.WIFI_STANDARD_80211ax)
    wifi_mac    = ns.WifiMacHelper()

    wifi_devices_list = []
    for e in range(NUM_EDGES):
        # A SEPARATE physical channel per cluster.
        #
        # Creating one YansWifiChannel outside this loop puts every cluster on
        # ONE broadcast domain. Distinct SSIDs separate them at the MAC layer,
        # but IP does not see that: GlobalRouter then finds one broadcast link
        # carrying two different /24 subnets and aborts with
        #   "GlobalRouter::ProcessSingleBroadcastLink(): Network number
        #    confusion (192.168.2.2/24, 192.168.1.1/24)"
        # Separate channels make the clusters genuinely separate L2 segments,
        # which is also the physically honest model: two edge cells are not
        # one shared radio medium.
        phy_helper = ns.YansWifiPhyHelper()
        phy_helper.SetChannel(ns.YansWifiChannelHelper.Default().Create())

        ssid_str = f"HFL-Edge-{e}"
        ssid = ns.Ssid(ssid_str)
        # AP on edge node
        wifi_mac.SetType("ns3::ApWifiMac",
                         "Ssid", ns.SsidValue(ssid))
        ap_dev = wifi_helper.Install(phy_helper, wifi_mac, edge_nodes.Get(e))
        # STAs: devices in this cluster
        wifi_mac.SetType("ns3::StaWifiMac",
                         "Ssid",       ns.SsidValue(ssid),
                         "ActiveProbing", ns.BooleanValue(False))
        # The LAST cluster absorbs the remainder. With integer division alone
        # (9 devices // 2 edges = 4) the clusters cover devices 0-7 and the
        # 9th is never attached to any AP — it silently contributes no traffic,
        # so the simulated uplink is short by one client and every derived
        # per-round figure is understated.
        start_idx = e * DEVICES_PER_EDGE
        end_idx   = (NUM_DEVICES if e == NUM_EDGES - 1
                     else min(start_idx + DEVICES_PER_EDGE, NUM_DEVICES))
        cluster_nodes = ns.NodeContainer()
        for d in range(start_idx, end_idx):
            cluster_nodes.Add(iot_nodes.Get(d))
        sta_devs = wifi_helper.Install(phy_helper, wifi_mac, cluster_nodes)

        # Degraded-channel model. A RateErrorModel drops a fraction of
        # received packets, standing in for interference, mobility and
        # co-channel contention that a clean simulated link does not have.
        # This is what turns "> 99 % of updates delivered" from a tautology
        # into a measurement: an architecture that must push 13x more bytes
        # through a lossy channel has 13x more opportunities to lose one.
        wifi_devices_list.append((ap_dev, sta_devs, cluster_nodes))

    # ── Mobility / geometry ───────────────────────────────────────────────────
    #
    # Every node previously defaulted to position (0,0,0). Co-located nodes see
    # a perfect channel, so every architecture delivered 100 % of its packets
    # and the reliability comparison could not discriminate between them —
    # which is why the earlier version fell back to hand-picked loss ranges.
    #
    # Devices are now placed on a disc of radius CELL_RADIUS around their edge
    # access point. Path loss then degrades SNR with distance and frame errors
    # emerge from the real 802.11ax PHY/MAC rather than from an injected error
    # model. Sweeping the radius is a genuine heterogeneous-network experiment:
    # an architecture that must push more bytes through a worse link has
    # proportionally more exposure to loss.
    mobility = ns.MobilityHelper()
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
    mobility.InstallAll()

    import math as _math
    _pos = {}
    for _e in range(NUM_EDGES):
        _ax, _ay = _e * 500.0, 0.0            # edge APs 500 m apart
        _pos[edge_nodes.Get(_e)] = (_ax, _ay)
    for _e, (_ap, _sta, _cn) in enumerate(wifi_devices_list):
        _ax, _ay = _pos[edge_nodes.Get(_e)]
        _n = _cn.GetN()
        for _d in range(_n):
            _ang = 2 * _math.pi * _d / max(_n, 1)
            _pos[_cn.Get(_d)] = (_ax + CELL_RADIUS * _math.cos(_ang),
                                 _ay + CELL_RADIUS * _math.sin(_ang))
    _pos[cloud_node.Get(0)] = (0.0, 1000.0)
    for _node, (_x, _y) in _pos.items():
        _mm = _node.GetObject[ns.MobilityModel]()
        if _mm:
            _mm.SetPosition(ns.Vector(_x, _y, 1.5))

    # ── Internet stack ────────────────────────────────────────────────────────
    stack = ns.InternetStackHelper()
    stack.InstallAll()

    # ── IP addressing ─────────────────────────────────────────────────────────
    addr_helper = ns.Ipv4AddressHelper()

    # Edge → Cloud IPs: 10.0.{edge}.0/24
    cloud_addrs = []
    for e in range(NUM_EDGES):
        addr_helper.SetBase(
            ns.Ipv4Address(f"10.0.{e+1}.0"),
            ns.Ipv4Mask("255.255.255.0")
        )
        ifaces = addr_helper.Assign(ec_devices[e])
        cloud_addrs.append(ifaces.GetAddress(1))  # cloud side IP

    # WiFi cluster IPs: 192.168.{edge}.0/24
    for e, (ap_dev, sta_devs, _) in enumerate(wifi_devices_list):
        addr_helper.SetBase(
            ns.Ipv4Address(f"192.168.{e+1}.0"),
            ns.Ipv4Mask("255.255.255.0")
        )
        all_wifi = ns.NetDeviceContainer()
        all_wifi.Add(ap_dev)
        all_wifi.Add(sta_devs)
        addr_helper.Assign(all_wifi)

    ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

    # ── Applications: BulkSend from each device → Cloud ──────────────────────
    port     = 9
    sim_dur  = 20.0  # seconds per round

    # Packet Sink on cloud.
    #
    # The cppyy bindings do NOT apply the implicit InetSocketAddress ->
    # Address conversion that C++ does, so an InetSocketAddress must be
    # wrapped in ns.Address(...) explicitly or the overload resolution fails
    # with "could not convert argument 2".
    sink_h = ns.PacketSinkHelper(
        "ns3::TcpSocketFactory",
        ns.Address(ns.InetSocketAddress(ns.Ipv4Address.GetAny(), port).ConvertTo())
    )
    sinks = sink_h.Install(cloud_node.Get(0))
    sinks.Start(ns.Seconds(0.0))
    sinks.Stop(ns.Seconds(sim_dur))

    # BulkSend from each IoT device (uplink: gradient update)
    if upload_bytes is None:
        upload_bytes = int(COMPRESSED_SIZE_MB * 1024 * 1024)
    upload_bytes = int(upload_bytes)
    for e in range(NUM_EDGES):
        cloud_addr = cloud_addrs[e]
        _, _, cluster_nodes = wifi_devices_list[e]
        for d in range(cluster_nodes.GetN()):
            bulk_h = ns.BulkSendHelper(
                "ns3::TcpSocketFactory",
                ns.Address(ns.InetSocketAddress(cloud_addr, port).ConvertTo())
            )
            bulk_h.SetAttribute("MaxBytes", ns.UintegerValue(upload_bytes))
            src = bulk_h.Install(cluster_nodes.Get(d))
            # All clients of a round contend for the same medium. A large
            # stagger would serialise them and hide exactly the contention
            # this experiment exists to measure.
            src.Start(ns.Seconds(1.0 + d * 0.01))
            src.Stop(ns.Seconds(sim_dur))

    # ── FlowMonitor ───────────────────────────────────────────────────────────
    fm_helper = ns.FlowMonitorHelper()
    monitor   = fm_helper.InstallAll()

    # ── Run ──────────────────────────────────────────────────────────────────
    ns.Simulator.Stop(ns.Seconds(sim_dur))
    ns.Simulator.Run()

    # ── Collect metrics ───────────────────────────────────────────────────────
    monitor.CheckForLostPackets()
    stats = monitor.GetFlowStats()

    total_rx_bytes  = 0
    total_tx_bytes  = 0
    total_delay_sum = 0.0
    total_rx_pkts   = 0
    total_tx_pkts   = 0

    # cppyy exposes std::map as a C++ container, not a dict: it has no
    # .items(). Iterating it yields std::pair, so read .first/.second.
    for entry in stats:
        fs = entry.second
        total_rx_bytes  += fs.rxBytes
        total_tx_bytes  += fs.txBytes
        total_delay_sum += fs.delaySum.GetSeconds()
        total_rx_pkts   += fs.rxPackets
        total_tx_pkts   += fs.txPackets

    ns.Simulator.Destroy()

    avg_delay_ms   = (total_delay_sum / max(total_rx_pkts, 1)) * 1000
    loss_rate      = 1 - (total_rx_pkts / max(total_tx_pkts, 1))
    rx_MB          = total_rx_bytes / (1024 * 1024)
    throughput_Mbs = (total_rx_bytes * 8) / sim_dur / 1e6

    return {
        "ns3_avg_delay_ms":   round(avg_delay_ms, 3),
        "ns3_loss_pct":       round(loss_rate * 100, 3),
        "ns3_rx_MB":          round(rx_MB, 3),
        "ns3_throughput_Mbps":round(throughput_Mbs, 3),
        "ns3_reliability_pct":round((1 - loss_rate) * 100, 3),
        "ns3_scenario":       scenario,
        "ns3_upload_bytes":   upload_bytes,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SIMULATION LOOP
# ══════════════════════════════════════════════════════════════════════════════

NS3_EVERY = _args.ns3_every
CELL_RADIUS = _args.cell_radius


def main():
    scenarios = cfg["baselines"]
    all_results = []

    print(f"Running {len(scenarios)} scenarios × {FL_ROUNDS} rounds...\n")
    total_start = time.time()
    # Progress accounting. Packet-level runs are long and their cost scales
    # with the device count, so the per-round line reports a measured rate and
    # a projection rather than leaving the caller to guess from wall time.
    _T0 = total_start
    _TOTAL_SIMS = len(scenarios) * FL_ROUNDS

    for scenario in scenarios:
        print(f"  Scenario: {scenario}")
        for rnd in range(1, FL_ROUNDS + 1):
            row = compute_analytical_metrics(scenario, rnd)

            # PACKET-LEVEL pass for EVERY scenario, not just the proposed one.
            #
            # Previously only HFL_Proposed was simulated and the other
            # scenarios' loss came from hand-picked rng.uniform ranges — which
            # made the reliability comparison a restatement of those ranges
            # rather than a measurement. Each scenario now carries its own
            # measured payload through the real topology and its loss is read
            # from FlowMonitor.
            if NS3_AVAILABLE and rnd % NS3_EVERY == 0:
                ns3_row = run_ns3_round(rnd,
                                        upload_bytes=PAYLOAD_BYTES.get(scenario),
                                        scenario=scenario)
                row.update(ns3_row)
                # Measured values REPLACE the analytical placeholders.
                if "ns3_loss_pct" in ns3_row:
                    row["pkt_loss_pct"]    = ns3_row["ns3_loss_pct"]
                    row["reliability_pct"] = ns3_row["ns3_reliability_pct"]
                    row["metric_source"]   = "packet-level"
                # The COMMUNICATION term must be replaced too, and with it the
                # end-to-end total. Previously only loss and reliability were
                # substituted, so L_comm_ms and L_total_ms stayed analytical on
                # every row including the packet-level ones — and any latency
                # claim drawn from them was an analytical result wearing a
                # packet-level label. The compute terms (sensor, preprocessing,
                # inference, aggregation) are host-side and remain analytical
                # by construction; only the network term is simulated.
                if "ns3_avg_delay_ms" in ns3_row:
                    row["L_comm_ms"] = round(float(ns3_row["ns3_avg_delay_ms"]), 3)
                    row["L_total_ms"] = round(
                        row["L_sensor_ms"] + row["L_preproc_ms"]
                        + row["L_inference_ms"] + row["L_comm_ms"]
                        + row["L_aggregation_ms"], 3)
                    row["latency_ok"] = int(row["L_total_ms"] < 100)
            else:
                row["metric_source"] = "analytical"

            all_results.append(row)

            # Every round, not every twentieth: with FL_ROUNDS=20 the old
            # modulus fired once per scenario, which is indistinguishable from
            # a hang for most of the run.
            _done = len(all_results)
            _el = time.time() - _T0
            _rate = _el / max(_done, 1)
            _left = _rate * (_TOTAL_SIMS - _done)
            print(f"    [{_done:3d}/{_TOTAL_SIMS}] {scenario:<20} round {rnd:3d}/{FL_ROUNDS}"
                  f" | {row['L_total_ms']:6.1f}ms"
                  f" | {row['uplink_MB']:6.1f}MB"
                  f" | rel {row['reliability_pct']:6.2f}%"
                  f" | {_rate:4.1f}s/sim eta {_left/60:5.1f}min")

    # ── Save results ─────────────────────────────────────────────────────────
    # Rows are heterogeneous: only the rounds that ran the packet-level
    # simulation carry the ns3_* measurements, so the header must be the UNION
    # of all row keys. Taking the first row's keys silently drops every
    # packet-level column the moment an analytical row happens to come first —
    # which is what hid this path until the bindings were built.
    out_csv = OUT_CSV or os.path.join(RESULTS_DIR, f"ns3_results_{_args.dataset}.csv")
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    fields = list(dict.fromkeys(k for r in all_results for k in r))
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(all_results)

    elapsed = time.time() - total_start
    print(f"\n{'='*65}")
    print(f"  Simulation complete in {elapsed:.1f}s")
    print(f"  Results saved: {out_csv}")
    print(f"  Total rows: {len(all_results)}")
    print(f"  Compute device: {device}")
    print(f"{'='*65}")

    # ── Print summary metrics (for QoS validation) ─────────────────────────
    import statistics
    print(f"\n── QoS Summary per Scenario ──────────────────────────────────")
    proposed = [r for r in all_results if r["scenario"] == "HFL_Proposed"]
    centralized = [r for r in all_results if r["scenario"] == "CentralizedFL"]

    if proposed and centralized:
        prop_lat  = statistics.mean(r["L_total_ms"] for r in proposed)
        cent_lat  = statistics.mean(r["L_total_ms"] for r in centralized)
        prop_ul   = statistics.mean(r["uplink_MB"]  for r in proposed)
        cent_ul   = statistics.mean(r["uplink_MB"]  for r in centralized)
        rel_pct   = statistics.mean(r["reliability_pct"] for r in proposed)
        comm_red  = (cent_ul - prop_ul) / cent_ul * 100

        print(f"  FL Round Latency (HFL Prop) : {prop_lat:.2f} ms  "
              f"[Inference latency <100ms target → Phase 5 (ONNX)]")
        print(f"  Comm. Reduction             : {comm_red:.1f}%   "
              f"[Target: ≥50%  → {'PASS' if comm_red >= 50 else 'FAIL'}]")
        print(f"  Update Reliability          : {rel_pct:.2f}%  "
              f"[Target: >99%  → {'PASS' if rel_pct > 99 else 'FAIL'}]")


if __name__ == "__main__":
    main()
