"""fig10_ablation_mia.py — Fig. 10: (a) component ablation on VitalDB, delta
AUROC against the full system paired by seed, beside total uplink; (b)
patient-level membership-inference audit (paper/figs.md, Fig. 10).

Arm map (ablation_runner): A0 full, A1 -C1 hierarchy, A2 -C2 privacy,
A3 -C3 sparsification, A4 -C4 quantization, A6 +C6 loss-aware weighting.
Seeds 42-44, the set Table tab:ablation reports."""
import csv
import json
from collections import defaultdict
import numpy as np
from _figstyle import plt, RES, DOUBLE, C, tci, panel, save

ABL = RES / "phase6" / "vitaldb"
SEEDS = (42, 43, 44)
ARMS = ((1, "$-$C1 hierarchy"), (2, "$-$C2 privacy"), (3, "$-$C3 sparsification"),
        (4, "$-$C4 quantization"), (6, "+C6 loss-aware weighting"))
# audit on the person-level partition; the ablation stays case-level
MIA_DS = "vitaldb_person"
MIA = RES / "phase5" / "lira" / MIA_DS
CONFIGS = (("head_nodp", "Control (non-private)", C["ctrl"]),
           ("sample", "Record-level DP", C["record"]),
           ("patient", "Patient-level DP", C["indiv"]))
ATTACKS = (("loss", "loss threshold", "o", "none"), ("lira_offline", "LiRA (offline)", "o", None))


def abl(a, sd):
    d = json.load(open(ABL / f"ablation_A{a}_seed{sd}_final.json"))
    return d["test"]["macro_auc"], d["uplink_bytes_total"] / 1e6


def main():
    fig = plt.figure(figsize=(DOUBLE, 2.6))
    # a blank spacer column separates the two panels
    gs = fig.add_gridspec(1, 4, width_ratios=[1.3, 0.55, 0.22, 1.25], wspace=0.08)
    ax, axu, axm = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[3])

    full = {sd: abl(0, sd) for sd in SEEDS}
    y = np.arange(len(ARMS))[::-1]
    for yi, (a, lab) in zip(y, ARMS):
        d = [abl(a, sd)[0] - full[sd][0] for sd in SEEDS]
        m, h = tci(d)
        sig = abs(m) > h
        col = C["indiv"] if sig else "#333333"
        ax.errorbar(m, yi, xerr=h, fmt="o", color=col, ms=4.5 if sig else 3.5,
                    elinewidth=1.1 if sig else 0.75)
        up = abl(a, SEEDS[0])[1]
        axu.barh(yi, up, color=C["ctrl"] if a != 1 else "none",
                 edgecolor=C["ctrl"], hatch="////" if a == 1 else None, lw=0.6,
                 height=0.55)
        axu.text(up * 1.15, yi, f"{up:.0f}", va="center", fontsize=6.3)
    ax.axvline(0, color="#444444", lw=0.5)
    ax.set_yticks(y, [lab for _, lab in ARMS])
    ax.set_xlabel("$\\Delta$AUROC vs full system")
    ax.text(0.02, 0.02, f"$n={len(SEEDS)}$, 95 % CI", transform=ax.transAxes, fontsize=6.3)
    panel(ax, "a", x=-0.62)
    ax.set_title("Component ablation (VitalDB, case-level)", fontsize=8, loc="left")
    fullup = full[SEEDS[0]][1]
    axu.axvline(fullup, color=C["indiv"], lw=0.6, ls=":")
    axu.set_xscale("log")
    axu.set_xlim(20, 8000)
    axu.set_yticks([])
    axu.spines["left"].set_visible(False)
    axu.set_xlabel("Uplink [MB]")
    axu.set_ylim(ax.get_ylim())

    floor = {r["arm"].split("/")[1]: float(r["floor"]) for r in
             csv.DictReader(open(RES / "phase5" / "mia_difficulty_floor_vitaldb.csv"))}
    by = defaultdict(list)
    tpr = defaultdict(list)
    for arm, _, _ in CONFIGS:
        # both DP arms are scored on identical shadow splits in one file
        joint = MIA / f"lira_{MIA_DS}_sample_patient.csv"
        src = joint if arm != "head_nodp" and joint.exists() else MIA / f"lira_{MIA_DS}_{arm}.csv"
        for r in csv.DictReader(open(src)):
            if r.get("arm", arm) != arm:
                continue
            by[(arm, r["attack"])].append(float(r["attack_auc"]))
            if r["attack"] == "difficulty":
                floor[arm] = None
            tpr[(arm, r["attack"])].append(float(r["tpr_at_1pct_fpr"]))
    for i, (arm, lab, col) in enumerate(CONFIGS):
        for j, (att, alab, mk, fc) in enumerate(ATTACKS):
            v = by[(arm, att)]
            m, h = tci(v)
            axm.errorbar(i + (j - 0.5) * 0.25, m, yerr=h, fmt=mk, color=col,
                         mfc=fc if fc else col, ms=4.5, elinewidth=0.75,
                         label=alab if i == 0 else None)
            print(f"{arm:10s} {att:13s} AUC {m:.4f}+-{h:.4f} n={len(v)} "
                  f"TPR@1%={np.mean(tpr[(arm, att)]):.4f}")
        # difficulty floor: AUC from per-patient difficulty alone, no target model
        f = np.mean(by[(arm, "difficulty")]) if floor.get(arm) is None else floor[arm]
        axm.plot([i - 0.3, i + 0.3], [f, f], color=col, lw=1.0, ls=(0, (1.5, 1)),
                 label="difficulty floor" if i == 0 else None)
    axm.axhline(0.5, color="#444444", lw=0.6, ls="--")
    axm.text(-0.45, 0.503, "chance", fontsize=6.3, ha="left", va="bottom")
    axm.set_xticks(range(3), [lab.replace(" (", "\n(").replace("-level DP", "-level\nDP") for _, lab, _ in CONFIGS])
    axm.set_xlim(-0.5, 2.5)
    axm.set_ylabel("Attack AUC")
    axm.yaxis.set_label_position("right"); axm.yaxis.tick_right()
    axm.spines["right"].set_visible(True); axm.spines["left"].set_visible(False)
    leg = axm.legend(loc="upper right", fontsize=6.3)
    for hdl in leg.legend_handles:
        hdl.set_color("#333333")
    panel(axm, "b", x=-0.14)
    axm.set_title("Membership inference (VitalDB, person-level)", fontsize=8)
    save(fig, "fig10_ablation_mia")


if __name__ == "__main__":
    main()
