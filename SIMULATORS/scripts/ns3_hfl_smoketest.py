#!/usr/bin/env python3
"""
NS-3 Smoke Test for HFL Research Project
Verifies NS-3 Python bindings work and simulates a minimal
3-node (Device → Edge → Cloud) point-to-point topology.

Run from inside the ns-3-dev directory:
    python3 ../../scripts/ns3_hfl_smoketest.py
OR via ns3 runner:
    ./ns3 run "python3 ../../scripts/ns3_hfl_smoketest.py"
"""

try:
    import ns.core
    import ns.network
    import ns.internet
    import ns.point_to_point
    import ns.applications
    import ns.flow_monitor
    print("[OK] NS-3 Python bindings imported successfully.")
except ImportError as e:
    print(f"[ERROR] NS-3 Python bindings not found: {e}")
    print("  Ensure you are running from inside the ns-3-dev directory.")
    print("  Or set: export PYTHONPATH=/path/to/ns-3-dev/build/bindings/python")
    raise SystemExit(1)

import json
import csv
import os

# ── Load shared config ────────────────────────────────────────────────────────
CONFIG_PATH = "/home/mit/DEADSERPENT/HFL/SIMULATORS/config/hfl_config.json"
with open(CONFIG_PATH) as f:
    cfg = json.load(f)

RESULTS_DIR = cfg["output"]["ns3_results_path"]
os.makedirs(RESULTS_DIR, exist_ok=True)

# ── Simulation Parameters ────────────────────────────────────────────────────
MODEL_SIZE_MB = cfg["model"]["model_size_MB"]
PACKET_SIZE   = 1024          # bytes
SIM_DURATION  = 10.0          # seconds
LINK_DELAY    = "5ms"
LINK_BW       = "54Mbps"

print(f"[INFO] Smoke test: 3-node (Device→Edge→Cloud) topology")
print(f"[INFO] Model size: {MODEL_SIZE_MB} MB | Duration: {SIM_DURATION}s")

# ── Build topology ───────────────────────────────────────────────────────────
nodes = ns.network.NodeContainer()
nodes.Create(3)  # node[0]=Device, node[1]=Edge, node[2]=Cloud

# Link 1: Device → Edge (WiFi simulated as P2P for smoke test)
p2p_de = ns.point_to_point.PointToPointHelper()
p2p_de.SetDeviceAttribute("DataRate", ns.core.StringValue(LINK_BW))
p2p_de.SetChannelAttribute("Delay", ns.core.StringValue(LINK_DELAY))
devices_de = p2p_de.Install(nodes.Get(0), nodes.Get(1))

# Link 2: Edge → Cloud (1 Gbps fiber)
p2p_ec = ns.point_to_point.PointToPointHelper()
p2p_ec.SetDeviceAttribute("DataRate", ns.core.StringValue("1Gbps"))
p2p_ec.SetChannelAttribute("Delay", ns.core.StringValue("5ms"))
devices_ec = p2p_ec.Install(nodes.Get(1), nodes.Get(2))

# Install Internet stack and assign IPs
stack = ns.internet.InternetStackHelper()
stack.InstallAll()

address = ns.internet.Ipv4AddressHelper()
address.SetBase(
    ns.network.Ipv4Address("10.1.1.0"),
    ns.network.Ipv4Mask("255.255.255.0")
)
ifaces_de = address.Assign(devices_de)

address.SetBase(
    ns.network.Ipv4Address("10.1.2.0"),
    ns.network.Ipv4Mask("255.255.255.0")
)
ifaces_ec = address.Assign(devices_ec)

ns.internet.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

# ── Install Applications (BulkSend: Device→Cloud via Edge) ──────────────────
cloud_addr = ifaces_ec.GetAddress(1)
port = 9

# Sink on Cloud node
sink_helper = ns.applications.PacketSinkHelper(
    "ns3::TcpSocketFactory",
    ns.network.InetSocketAddress(ns.network.Ipv4Address.GetAny(), port)
)
sink_apps = sink_helper.Install(nodes.Get(2))
sink_apps.Start(ns.core.Seconds(0.0))
sink_apps.Stop(ns.core.Seconds(SIM_DURATION))

# BulkSend on Device node (simulating gradient upload)
bulk = ns.applications.BulkSendHelper(
    "ns3::TcpSocketFactory",
    ns.network.InetSocketAddress(cloud_addr, port)
)
bulk.SetAttribute("MaxBytes", ns.core.UintegerValue(MODEL_SIZE_MB * 1024 * 1024))
source_apps = bulk.Install(nodes.Get(0))
source_apps.Start(ns.core.Seconds(1.0))
source_apps.Stop(ns.core.Seconds(SIM_DURATION))

# ── Flow Monitor ─────────────────────────────────────────────────────────────
flow_helper = ns.flow_monitor.FlowMonitorHelper()
monitor = flow_helper.InstallAll()

# ── Run ──────────────────────────────────────────────────────────────────────
ns.core.Simulator.Stop(ns.core.Seconds(SIM_DURATION))
ns.core.Simulator.Run()

# ── Collect Results ──────────────────────────────────────────────────────────
monitor.CheckForLostPackets()
classifier = flow_helper.GetClassifier()
stats = monitor.GetFlowStats()

results = []
for flow_id, flow_stat in stats.items():
    c = classifier.FindFlow(flow_id)
    rx_bytes_MB = flow_stat.rxBytes / (1024 * 1024)
    tx_bytes_MB = flow_stat.txBytes / (1024 * 1024)
    delay_ms    = (flow_stat.delaySum.GetSeconds() / max(flow_stat.rxPackets, 1)) * 1000
    loss_rate   = 1 - (flow_stat.rxPackets / max(flow_stat.txPackets, 1))
    results.append({
        "flow_id":      flow_id,
        "rx_bytes_MB":  round(rx_bytes_MB, 4),
        "tx_bytes_MB":  round(tx_bytes_MB, 4),
        "delay_ms":     round(delay_ms, 4),
        "loss_rate":    round(loss_rate, 4),
        "rx_packets":   flow_stat.rxPackets,
        "tx_packets":   flow_stat.txPackets,
    })
    print(f"  Flow {flow_id}: TX={tx_bytes_MB:.2f}MB "
          f"RX={rx_bytes_MB:.2f}MB "
          f"Delay={delay_ms:.2f}ms "
          f"Loss={loss_rate*100:.1f}%")

ns.core.Simulator.Destroy()

# ── Save results to CSV ──────────────────────────────────────────────────────
out_path = os.path.join(RESULTS_DIR, "smoketest_results.csv")
with open(out_path, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=results[0].keys() if results else [])
    writer.writeheader()
    writer.writerows(results)

print(f"\n[OK] Smoke test complete. Results saved to: {out_path}")
print("[OK] NS-3 Python interface: FULLY FUNCTIONAL")
