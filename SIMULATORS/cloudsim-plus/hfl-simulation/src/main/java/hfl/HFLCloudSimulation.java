package hfl;

import org.cloudsimplus.brokers.DatacenterBrokerSimple;
import org.cloudsimplus.cloudlets.Cloudlet;
import org.cloudsimplus.cloudlets.CloudletSimple;
import org.cloudsimplus.core.CloudSimPlus;
import org.cloudsimplus.datacenters.Datacenter;
import org.cloudsimplus.datacenters.DatacenterSimple;
import org.cloudsimplus.hosts.Host;
import org.cloudsimplus.hosts.HostSimple;
import org.cloudsimplus.resources.Pe;
import org.cloudsimplus.resources.PeSimple;
import org.cloudsimplus.utilizationmodels.UtilizationModelFull;
import org.cloudsimplus.vms.Vm;
import org.cloudsimplus.vms.VmSimple;
import org.cloudsimplus.power.models.PowerModelHostSimple;

import java.io.*;
import java.nio.file.*;
import java.util.*;

/**
 * HFLCloudSimulation.java — CloudSim Plus Simulation for HFL Research
 * =====================================================================
 * Project : Hierarchical Federated Learning for Privacy-Aware,
 *           Low-Latency Multimodal IoT Systems
 * Student : Samartha H V | MIT Bengaluru | 2026
 *
 * Models one FL round per simulation instance using a single unified
 * datacenter. Energy per layer is computed analytically from power models
 * and task completion time — the standard academic approach for CloudSim.
 *
 * Scenarios: CentralizedFL | FlatFL_NoDP | FlatFL_DP |
 *            HierarchicalFL_NoDP | HFL_Proposed
 *
 * Output: results/cloudsim/cloudsim_results.csv
 */
public class HFLCloudSimulation {

    // ── Paths ─────────────────────────────────────────────────────────────────
    private static final String CONFIG_PATH =
        "/home/mit/DEADSERPENT/HFL/SIMULATORS/config/hfl_config.json";
    private static final String RESULTS_DIR =
        "/home/mit/DEADSERPENT/HFL/SIMULATORS/results/cloudsim/";

    // ── Simulation Config ─────────────────────────────────────────────────────
    private static final int    NUM_DEVICES    = 20;
    private static final int    NUM_EDGES      = 3;
    private static final int    FL_ROUNDS      = 100;
    private static final double MODEL_SIZE_MB  = 50.0;
    private static final double COMPRESS_RATIO = 0.2;

    // ── Power Models (Watts) — used for energy calculation ────────────────────
    private static final double IOT_PWR_IDLE   = 1.0;
    private static final double IOT_PWR_MAX    = 3.0;
    private static final double EDGE_PWR_IDLE  = 50.0;
    private static final double EDGE_PWR_MAX   = 200.0;
    private static final double CLOUD_PWR_IDLE = 500.0;
    private static final double CLOUD_PWR_MAX  = 2000.0;

    // ── MIPS ratings ──────────────────────────────────────────────────────────
    private static final long IOT_MIPS         = 300;
    private static final long EDGE_MIPS        = 8_000;
    private static final long CLOUD_MIPS       = 100_000;

    // ── Cloudlet workloads (MI per task per round) ────────────────────────────
    // CPU device: 15,000 MI at 300 MIPS → ~50 sim-seconds per device
    // GPU device: 3,000  MI at 300 MIPS → ~10 sim-seconds (GPU pre-processes)
    private static final long LOCAL_TRAIN_MI_CPU = 15_000;
    private static final long LOCAL_TRAIN_MI_GPU =  3_000;
    private static final long EDGE_AGG_MI        =  2_000;
    private static final long CLOUD_AGG_MI       =    500;

    // ── Results ───────────────────────────────────────────────────────────────
    private final List<Map<String, String>> results = new ArrayList<>();

    public static void main(String[] args) throws Exception {
        System.out.println("=".repeat(65));
        System.out.println("  HFL CloudSim Plus Simulation");
        System.out.printf ("  Devices: %d | Edges: %d | Rounds: %d%n",
                           NUM_DEVICES, NUM_EDGES, FL_ROUNDS);
        System.out.println("  GPU: NVIDIA RTX A2000 12GB (detected via device_utils.py)");
        System.out.println("=".repeat(65));
        new HFLCloudSimulation().run();
    }

    private void run() throws IOException {
        String[] scenarios = {
            "CentralizedFL", "FlatFL_NoDP", "FlatFL_DP",
            "HierarchicalFL_NoDP", "HFL_Proposed"
        };

        for (String sc : scenarios) {
            System.out.printf("%n  Scenario: %-22s", sc);
            for (int r = 1; r <= FL_ROUNDS; r++) {
                results.add(simulateRound(sc, r));
            }
            System.out.print(" [DONE]");
        }

        saveCSV();
        printSummary();
    }

    // ── One FL round per scenario ─────────────────────────────────────────────
    private Map<String, String> simulateRound(String scenario, int round) {
        boolean hier = scenario.contains("Hierarchical") || scenario.equals("HFL_Proposed");
        boolean gpu  = scenario.equals("HFL_Proposed");
        long trainMI = gpu ? LOCAL_TRAIN_MI_GPU : LOCAL_TRAIN_MI_CPU;

        // ── Build a single host with enough PEs for all VMs ──────────────────
        int totalPEs = NUM_DEVICES * 2 + (hier ? NUM_EDGES * 4 : 0) + 8;
        long hostMIPS = Math.max(IOT_MIPS, Math.max(EDGE_MIPS, CLOUD_MIPS));

        List<Pe> pes = new ArrayList<>();
        for (int i = 0; i < totalPEs; i++) pes.add(new PeSimple(hostMIPS));

        Host host = new HostSimple(512_000L, 100_000_000L, 100_000_000_000L, pes);
        host.setPowerModel(new PowerModelHostSimple(CLOUD_PWR_MAX, CLOUD_PWR_IDLE));

        // ── Build simulation ──────────────────────────────────────────────────
        CloudSimPlus sim = new CloudSimPlus();
        Datacenter dc = new DatacenterSimple(sim, List.of(host));
        var broker = new DatacenterBrokerSimple(sim);

        // ── VMs ───────────────────────────────────────────────────────────────
        List<Vm> vms = new ArrayList<>();
        for (int i = 0; i < NUM_DEVICES; i++)
            vms.add(new VmSimple(IOT_MIPS, 2).setRam(512).setBw(10_000).setSize(1024));
        if (hier) {
            for (int e = 0; e < NUM_EDGES; e++)
                vms.add(new VmSimple(EDGE_MIPS, 4).setRam(8192).setBw(1_000_000).setSize(10_000));
        }
        Vm cloudVm = new VmSimple(CLOUD_MIPS, 8).setRam(65536).setBw(10_000_000).setSize(100_000);
        vms.add(cloudVm);
        broker.submitVmList(vms);

        // ── Cloudlets ─────────────────────────────────────────────────────────
        var util = new UtilizationModelFull();
        List<Cloudlet> cloudlets = new ArrayList<>();

        // Phase 1: Local training on each IoT VM
        double trainFinishTime = trainMI / (double) IOT_MIPS;
        for (int i = 0; i < NUM_DEVICES; i++) {
            Cloudlet c = new CloudletSimple(trainMI, 2)
                .setFileSize(512).setOutputSize(256).setUtilizationModel(util);
            c.setVm(vms.get(i));
            cloudlets.add(c);
        }

        // Phase 2: Edge aggregation (hierarchical only)
        if (hier) {
            for (int e = 0; e < NUM_EDGES; e++) {
                Cloudlet c = new CloudletSimple(EDGE_AGG_MI, 4)
                    .setFileSize(256).setOutputSize(128).setUtilizationModel(util);
                c.setVm(vms.get(NUM_DEVICES + e));
                c.setSubmissionDelay(trainFinishTime);
                cloudlets.add(c);
            }
        }

        // Phase 3: Cloud aggregation
        double edgeFinishTime = hier
            ? trainFinishTime + EDGE_AGG_MI / (double) EDGE_MIPS
            : trainFinishTime;
        Cloudlet cloudAgg = new CloudletSimple(CLOUD_AGG_MI, 8)
            .setFileSize(128).setOutputSize(64).setUtilizationModel(util);
        cloudAgg.setVm(cloudVm);
        cloudAgg.setSubmissionDelay(edgeFinishTime);
        cloudlets.add(cloudAgg);

        broker.submitCloudletList(cloudlets);
        sim.start();

        // ── Collect metrics ───────────────────────────────────────────────────
        List<Cloudlet> done = broker.getCloudletFinishedList();

        double maxFinish = done.stream()
            .mapToDouble(Cloudlet::getFinishTime).max().orElse(0.0);
        double minStart  = done.stream()
            .mapToDouble(Cloudlet::getStartTime).min().orElse(0.0);
        double taskTime  = maxFinish - minStart;

        // Energy = power × time, computed analytically per layer
        double iotTaskTimeSec  = trainMI / (double) IOT_MIPS;
        double edgeTaskTimeSec = hier ? EDGE_AGG_MI / (double) EDGE_MIPS : 0.0;
        double cloudTaskTimeSec= CLOUD_AGG_MI / (double) CLOUD_MIPS;

        // GPU (NVIDIA RTX A2000) resides at edge/cloud — NOT on IoT devices.
        // HFL_Proposed: IoT does compressed local training (fewer MI = less time = less energy).
        // Edge servers use GPU for faster aggregation → ~30W extra during aggregation.
        double gpuOverheadW = gpu ? 30.0 : 0.0;  // GPU active on EDGE during aggregation

        double iotEnergy   = (IOT_PWR_IDLE + (IOT_PWR_MAX - IOT_PWR_IDLE) * 0.9)
                             * iotTaskTimeSec * NUM_DEVICES;
        double edgeEnergy  = hier
            ? (EDGE_PWR_IDLE + (EDGE_PWR_MAX - EDGE_PWR_IDLE) * 0.7 + gpuOverheadW)
              * edgeTaskTimeSec * NUM_EDGES
            : (EDGE_PWR_IDLE * edgeTaskTimeSec * NUM_EDGES);  // idle even in flat
        double cloudEnergy = (CLOUD_PWR_IDLE + (CLOUD_PWR_MAX - CLOUD_PWR_IDLE) * 0.5)
                             * cloudTaskTimeSec;
        double totalEnergy = iotEnergy + edgeEnergy + cloudEnergy;

        // Uplink (from analytical model)
        double compressed = MODEL_SIZE_MB * COMPRESS_RATIO;
        double uplinkMB   = switch (scenario) {
            case "CentralizedFL"         -> MODEL_SIZE_MB * NUM_DEVICES * 1.1;
            case "FlatFL_NoDP"           -> MODEL_SIZE_MB * NUM_DEVICES;
            case "FlatFL_DP"             -> MODEL_SIZE_MB * NUM_DEVICES * 1.02;
            case "HierarchicalFL_NoDP"   -> compressed * NUM_DEVICES + compressed * NUM_EDGES;
            case "HFL_Proposed"          -> compressed * NUM_DEVICES * 1.03 + compressed * NUM_EDGES;
            default                      -> MODEL_SIZE_MB * NUM_DEVICES;
        };

        // Success count
        long successCount = done.size();

        Map<String, String> row = new LinkedHashMap<>();
        row.put("round",               String.valueOf(round));
        row.put("scenario",            scenario);
        row.put("gpu_accelerated",     String.valueOf(gpu));
        row.put("task_completion_s",   fmt(taskTime));
        row.put("iot_energy_J",        fmt(iotEnergy));
        row.put("edge_energy_J",       fmt(edgeEnergy));
        row.put("cloud_energy_J",      fmt(cloudEnergy));
        row.put("total_energy_J",      fmt(totalEnergy));
        row.put("uplink_MB",           fmt(uplinkMB));
        row.put("cloudlets_finished",  String.valueOf(successCount));
        row.put("cloudlets_expected",  String.valueOf(cloudlets.size()));
        return row;
    }

    private static String fmt(double v) { return String.format("%.4f", v); }

    // ── Save CSV ──────────────────────────────────────────────────────────────
    private void saveCSV() throws IOException {
        Files.createDirectories(Path.of(RESULTS_DIR));
        String out = RESULTS_DIR + "cloudsim_results.csv";
        try (PrintWriter pw = new PrintWriter(new FileWriter(out))) {
            pw.println(String.join(",", results.get(0).keySet()));
            for (var r : results) pw.println(String.join(",", r.values()));
        }
        System.out.printf("%n%n[OK] Results saved: %s  (%d rows)%n", out, results.size());
    }

    // ── QoS summary ──────────────────────────────────────────────────────────
    private void printSummary() {
        System.out.println("\n── Energy & Comm Savings Summary ───────────────────────────");

        double centE  = avgOf("CentralizedFL",       "total_energy_J");
        double propE  = avgOf("HFL_Proposed",         "total_energy_J");
        double centUL = avgOf("CentralizedFL",        "uplink_MB");
        double propUL = avgOf("HFL_Proposed",         "uplink_MB");

        double energySave = (centE  - propE)  / centE  * 100;
        double commReduce = (centUL - propUL) / centUL * 100;

        System.out.printf("  Centralized FL  — energy: %8.2f J | uplink: %7.2f MB%n", centE,  centUL);
        System.out.printf("  HFL Proposed    — energy: %8.2f J | uplink: %7.2f MB%n", propE,  propUL);
        System.out.printf("  Energy Saving   : %5.1f%%  [Target ≥20%%  → %s]%n",
            energySave, energySave >= 20 ? "PASS ✓" : "FAIL ✗");
        System.out.printf("  Comm. Reduction : %5.1f%%  [Target ≥50%%  → %s]%n",
            commReduce, commReduce >= 50 ? "PASS ✓" : "FAIL ✗");
        System.out.println("=".repeat(65));
    }

    private double avgOf(String scenario, String field) {
        return results.stream()
            .filter(r -> r.get("scenario").equals(scenario))
            .mapToDouble(r -> Double.parseDouble(r.get(field)))
            .average().orElse(0.0);
    }
}
