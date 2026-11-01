"""fig09_system_cost.py — Fig. 9: system cost per deployment (paper/figs.md, Fig. 9).

(a) uplink per cloud round, measured from the deployed compressor
    (results/phase5/uplink_measured_<ds>.json);
(b) round latency, communication + compute, packet-level NS-3
    (results/ns3/ns3_results_<ds>.csv, mean over rounds);
(c) energy per round by tier, CloudSim (results/cloudsim/cloudsim_results_<ds>.csv),
    shown as a share of the centralized total with the absolute value printed.

A deployment appears in a panel only when its result file exists, so eICU
fills in by itself once its NS-3 run has written ns3_results_eicu.csv."""
import csv
import json
from collections import defaultdict
import numpy as np
from _figstyle import plt, RES, DOUBLE, C, NAME, panel, ygrid, save

DS = ("vitaldb", "wear", "eicu")
SHORT = dict(vitaldb="VitalDB", wear="WEAR", eicu="eICU")
ARM = dict(CentralizedFL="Centralized", HierarchicalFL_NoDP="Hierarchy only",
           HFL_Proposed="PP-HFM")
ARM_C = dict(CentralizedFL=C["ctrl"], HierarchicalFL_NoDP=C["record"],
             HFL_Proposed=C["indiv"])


def means(path, cols):
    acc = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(path)):
        for c in cols:
            acc[r["scenario"]][c].append(float(r[c]))
    return {s: {c: float(np.mean(v)) for c, v in d.items()} for s, d in acc.items()}


def uplink(ax):
    rows = []
    for ds in DS:
        p = RES / "phase5" / f"uplink_measured_{ds}.json"
        if p.exists():
            u = json.load(open(p))
            rows.append((ds, [u["centralized_mb_per_round"],
                              u["system"]["full_model"]["mb_per_round"],
                              u["system"]["head_only"]["mb_per_round"]],
                         u["system"]["head_only"]["reduction_pct"]))
    w = 0.26
    for i, (ds, v, red) in enumerate(rows):
        for j, arm in enumerate(ARM):
            ax.bar(i + (j - 1) * w, v[j], w, color=ARM_C[arm],
                   label=ARM[arm] if i == 0 else None)
        ax.text(i + w, v[2] * 1.15, f"$-${red:.1f} %", ha="center", va="bottom",
                fontsize=6.3, color=C["indiv"], rotation=90)
    ax.set_yscale("log")
    ax.set_xticks(range(len(rows)), [SHORT[d] for d, *_ in rows])
    ax.set_ylabel("Uplink per cloud round [MB]")
    ax.set_title("Uplink (measured payload)", fontsize=8)
    ygrid(ax)


def latency(ax):
    rows = []
    for ds in DS:
        p = RES / "ns3" / f"ns3_results_{ds}.csv"
        if p.exists():
            m = means(p, ("L_comm_ms", "L_total_ms"))
            rows.append((ds, m))
    y, labels = 0, []
    for ds, m in rows:
        for arm in ("CentralizedFL", "HFL_Proposed"):
            comm, tot = m[arm]["L_comm_ms"], m[arm]["L_total_ms"]
            ax.barh(y, comm, 0.7, color=ARM_C[arm])
            ax.barh(y, tot - comm, 0.7, left=comm, color=ARM_C[arm], alpha=0.35)
            ax.text(tot + 1.5, y, f"{tot:.1f}", va="center", fontsize=6.3)
            labels.append(f"{SHORT[ds]}, {ARM[arm]}")
            y += 1
        y += 0.5
    ax.set_yticks([i + 0.5 * (i // 2) for i in range(len(labels))], labels)
    ax.invert_yaxis()
    ax.set_xlabel("Round latency [ms]")
    ax.set_title("Round latency (NS-3)", fontsize=8)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc="#555555", label="communication"),
                       Patch(fc="#555555", alpha=0.35, label="computation")],
              loc="upper right", fontsize=6.3, handlelength=1.2)
    ax.xaxis.grid(True, lw=0.3, color="#DDDDDD"); ax.set_axisbelow(True)
    if rows:
        ax.set_xlim(0, max(m[a]["L_total_ms"] for _, m in rows for a in m) * 1.18)
    if len(rows) < len(DS):
        miss = ", ".join(SHORT[d] for d in DS if d not in dict(rows))
        ax.text(0.98, 0.02, f"{miss}: pending", transform=ax.transAxes, ha="right",
                fontsize=6, style="italic", color=C["ctrl"])


def energy(ax):
    tiers = (("iot_energy_J", "device", 1.0, None), ("edge_energy_J", "edge", 0.55, "////"),
             ("cloud_energy_J", "cloud", 0.25, "...."))
    rows = []
    for ds in DS:
        p = RES / "cloudsim" / f"cloudsim_results_{ds}.csv"
        if p.exists():
            rows.append((ds, means(p, [t[0] for t in tiers] + ["total_energy_J"])))
    w = 0.26
    for i, (ds, m) in enumerate(rows):
        base = m["CentralizedFL"]["total_energy_J"]
        for j, arm in enumerate(ARM):
            x, bot = i + (j - 1) * w, 0.0
            for col, tier, a, hat in tiers:
                h = 100 * m[arm][col] / base
                ax.bar(x, h, w, bottom=bot, color=ARM_C[arm], alpha=a, lw=0,
                       hatch=hat, edgecolor="white")
                bot += h
            ax.text(x, bot + 2, f"{m[arm]['total_energy_J']:.0f}", ha="center",
                    va="bottom", fontsize=5.4, rotation=90)
    ax.axhline(100, color="#444444", lw=0.4, ls=":")
    ax.set_xticks(range(len(rows)), [SHORT[d] for d, _ in rows])
    ax.set_ylim(0, 165)
    ax.set_yticks(range(0, 121, 20))
    ax.set_ylabel("Energy per round [% of centralized]")
    ax.set_title("Energy per round by tier", fontsize=8)
    ygrid(ax)
    # tier key, in grey so it does not compete with the arm colours
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc="#555555", alpha=a, hatch=hat, ec="white",
                             label=f"{tier}") for _, tier, a, hat in tiers],
              loc="upper center", ncol=3, fontsize=6.3, handlelength=1.2,
              columnspacing=0.8, title="stacked by tier; label = total J",
              title_fontsize=6.0)


def main():
    fig, axs = plt.subplots(1, 3, figsize=(DOUBLE, 2.6),
                            gridspec_kw=dict(width_ratios=(1, 1.15, 1)))
    uplink(axs[0]); latency(axs[1]); energy(axs[2])
    h0, l0 = axs[0].get_legend_handles_labels()
    fig.legend(h0, l0, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.01),
               title="Configuration (color in every panel)", title_fontsize=7,
               alignment="left")
    for ax, L in zip(axs, "abc"):
        panel(ax, L, x=-0.22)
    fig.tight_layout(w_pad=1.2, rect=(0, 0.07, 1, 1))
    save(fig, "fig09_system_cost")


if __name__ == "__main__":
    main()
