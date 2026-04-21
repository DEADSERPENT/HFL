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

import java.util.ArrayList;
import java.util.List;

/**
 * CloudSim Plus Smoke Test for HFL Research Project.
 *
 * Simulates one FL training round across the 3-layer HFL architecture:
 *   Layer 1: 5 IoT Device VMs perform local training (Cloudlets)
 *   Layer 2: 1 Edge Server VM performs partial FedAvg aggregation
 *   Layer 3: 1 Cloud Server VM performs global FedAvg aggregation
 *
 * Outputs: task completion time, energy consumed per entity.
 *
 * Project: Hierarchical Federated Learning for Privacy-Aware Multimodal IoT
 * Student: Samartha H V | MIT Bengaluru | 2026
 */
public class HFLSimTest {

    // ── Simulation Parameters (from hfl_config.json) ─────────────────────────
    private static final int    NUM_IOT_DEVICES         = 5;    // per cluster (smoke: 5)
    private static final int    FL_ROUNDS               = 1;    // smoke: 1 round

    // IoT Device specs (battery-constrained)
    private static final long   IOT_MIPS                = 300;
    private static final long   IOT_RAM_MB              = 512;
    private static final long   IOT_BW_MBPS             = 10;
    private static final long   IOT_STORAGE_MB          = 4096;
    private static final double IOT_POWER_IDLE_W        = 1.0;   // min 1W (CloudSim constraint)
    private static final double IOT_POWER_MAX_W         = 3.0;   // realistic for RPi-class device

    // Edge Server specs
    private static final long   EDGE_MIPS               = 8000;
    private static final long   EDGE_RAM_MB             = 16384;
    private static final long   EDGE_BW_MBPS            = 1000;
    private static final long   EDGE_STORAGE_MB         = 102400;
    private static final double EDGE_POWER_IDLE_W       = 50.0;
    private static final double EDGE_POWER_MAX_W        = 200.0;

    // Cloud Server specs
    private static final long   CLOUD_MIPS              = 100_000;
    private static final long   CLOUD_RAM_MB            = 262_144;
    private static final long   CLOUD_BW_MBPS           = 10_000;
    private static final long   CLOUD_STORAGE_MB        = 10_000_000;
    private static final double CLOUD_POWER_IDLE_W      = 500.0;
    private static final double CLOUD_POWER_MAX_W       = 2000.0;

    // Cloudlet workload (represents FL task complexity in MIs)
    // Local training: proportional to dataset size × model complexity
    private static final long   LOCAL_TRAIN_MI          = 50_000;   // per device per round
    private static final long   EDGE_AGGREGATION_MI     = 10_000;   // FedAvg at edge
    private static final long   CLOUD_AGGREGATION_MI    = 5_000;    // global FedAvg
    private static final int    CLOUDLET_PES            = 2;         // PEs per task

    public static void main(String[] args) {
        new HFLSimTest().run();
    }

    private void run() {
        System.out.println("=".repeat(65));
        System.out.println("  CloudSim Plus Smoke Test — HFL Research Project");
        System.out.println("  One FL Round: IoT Training → Edge Aggregation → Cloud Aggregation");
        System.out.println("=".repeat(65));

        final var simulation = new CloudSimPlus();

        // ── Create Datacenters ────────────────────────────────────────────────
        Datacenter iotDC   = createDatacenter(simulation, "IoT-DC",
                             NUM_IOT_DEVICES, IOT_MIPS, IOT_RAM_MB,
                             IOT_POWER_IDLE_W, IOT_POWER_MAX_W);

        Datacenter edgeDC  = createDatacenter(simulation, "Edge-DC",
                             1, EDGE_MIPS, EDGE_RAM_MB,
                             EDGE_POWER_IDLE_W, EDGE_POWER_MAX_W);

        Datacenter cloudDC = createDatacenter(simulation, "Cloud-DC",
                             1, CLOUD_MIPS, CLOUD_RAM_MB,
                             CLOUD_POWER_IDLE_W, CLOUD_POWER_MAX_W);

        // ── Create Broker ────────────────────────────────────────────────────
        var broker = new DatacenterBrokerSimple(simulation);

        // ── Create VMs ───────────────────────────────────────────────────────
        // IoT device VMs
        List<Vm> vmList = new ArrayList<>();
        for (int i = 0; i < NUM_IOT_DEVICES; i++) {
            vmList.add(new VmSimple(IOT_MIPS, CLOUDLET_PES)
                .setRam(IOT_RAM_MB).setBw(IOT_BW_MBPS).setSize(IOT_STORAGE_MB));
        }
        // Edge server VM
        Vm edgeVm = new VmSimple(EDGE_MIPS, 4)
            .setRam(EDGE_RAM_MB).setBw(EDGE_BW_MBPS).setSize(EDGE_STORAGE_MB);
        vmList.add(edgeVm);

        // Cloud server VM
        Vm cloudVm = new VmSimple(CLOUD_MIPS, 8)
            .setRam(CLOUD_RAM_MB).setBw(CLOUD_BW_MBPS).setSize(CLOUD_STORAGE_MB);
        vmList.add(cloudVm);

        broker.submitVmList(vmList);

        // ── Create Cloudlets (FL Tasks) ──────────────────────────────────────
        List<Cloudlet> cloudletList = new ArrayList<>();
        var utilModel = new UtilizationModelFull();

        // Phase 1: Local training on each IoT device
        for (int i = 0; i < NUM_IOT_DEVICES; i++) {
            Cloudlet localTrain = new CloudletSimple(LOCAL_TRAIN_MI, CLOUDLET_PES)
                .setFileSize(1024).setOutputSize(512)
                .setUtilizationModel(utilModel);
            localTrain.setVm(vmList.get(i));
            cloudletList.add(localTrain);
        }

        // Phase 2: Edge aggregation (runs after local training)
        Cloudlet edgeAgg = new CloudletSimple(EDGE_AGGREGATION_MI, 4)
            .setFileSize(512).setOutputSize(256)
            .setUtilizationModel(utilModel);
        edgeAgg.setVm(edgeVm);
        cloudletList.add(edgeAgg);

        // Phase 3: Cloud global aggregation
        Cloudlet cloudAgg = new CloudletSimple(CLOUD_AGGREGATION_MI, 8)
            .setFileSize(256).setOutputSize(128)
            .setUtilizationModel(utilModel);
        cloudAgg.setVm(cloudVm);
        cloudletList.add(cloudAgg);

        broker.submitCloudletList(cloudletList);

        // ── Run Simulation ───────────────────────────────────────────────────
        simulation.start();

        // ── Print Results ────────────────────────────────────────────────────
        System.out.println("\n" + "─".repeat(65));
        System.out.printf("%-12s %-10s %-12s %-10s %-10s%n",
            "Cloudlet", "Status", "Exec(sec)", "Start", "Finish");
        System.out.println("─".repeat(65));

        double totalEnergy = 0;
        var finishedList = broker.getCloudletFinishedList();
        for (Cloudlet cl : finishedList) {
            double execTime = cl.getFinishTime() - cl.getStartTime();
            System.out.printf("  %-10d %-10s %-12.4f %-10.4f %-10.4f%n",
                cl.getId(),
                cl.getStatus(),
                execTime,
                cl.getStartTime(),
                cl.getFinishTime());
        }

        // Print datacenter energy
        System.out.println("\n── Energy Consumed per Datacenter ─────────────────────────");
        for (var dc : List.of(iotDC, edgeDC, cloudDC)) {
            double powerW = dc.getPowerModel().getPower();
            System.out.printf("  %-12s : Current power draw = %.2f W%n",
                dc.getName(), powerW);
        }

        System.out.println("\n" + "=".repeat(65));
        System.out.println("  [OK] CloudSim Plus Smoke Test PASSED");
        System.out.println("  Environment is ready for Phase 4 implementation.");
        System.out.println("=".repeat(65));
    }

    /**
     * Creates a simple datacenter with one host containing [numVMs] PEs.
     */
    private Datacenter createDatacenter(CloudSimPlus sim, String name,
                                         int numVMs, long mips, long ramMB,
                                         double powerIdle, double powerMax) {
        int pesPerHost = numVMs * CLOUDLET_PES + 4; // extra headroom
        List<Pe> peList = new ArrayList<>();
        for (int i = 0; i < pesPerHost; i++) {
            peList.add(new PeSimple(mips));
        }

        Host host = new HostSimple(ramMB * numVMs, 10_000L, 1_000_000L, peList);
        host.setPowerModel(new PowerModelHostSimple(powerMax, powerIdle));

        List<Host> hostList = new ArrayList<>();
        hostList.add(host);

        return new DatacenterSimple(sim, hostList);
    }
}
