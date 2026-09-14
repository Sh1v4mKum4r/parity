"""Figures for the review deck. Light mode, projector-legible.

Palette: dataviz categorical slots 1-3 (blue/orange/aqua), validated for
adjacent-pair CVD separation before use. Colour follows the MODEL, not its
rank, and stays fixed across every figure.
"""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent
M = json.loads((ROOT / "out" / "metrics.json").read_text())

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e2e1dd"
COLOR = {"vomm": "#2a78d6", "markov-1": "#eb6834", "uniform": "#1baf7a"}
LABEL = {"vomm": "VOMM (proposed)", "markov-1": "Order-1 Markov", "uniform": "Uniform (no model)"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
})


def _finish(ax, title, sub=None):
    ax.set_title(title, loc="left", fontsize=11.5, fontweight="bold", color=INK, pad=20 if sub else 8)
    if sub:
        ax.text(0, 1.015, sub, transform=ax.transAxes, fontsize=8.5, color=INK2, va="bottom")


def fig_accuracy(out):
    bots = ["habitual", "explorer", "evasive", "random"]
    names = ["Habitual\n(follows routes)", "Explorer\n(systematic sweep)",
             "Evasive\n(waits to break pattern)", "Random\n(control)"]
    models = ["uniform", "markov-1", "vomm"]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    w, xs = 0.24, range(len(bots))
    for i, mk in enumerate(models):
        vals = [M["e1_accuracy"][f"{b}|{mk}"]["top1"] * 100 for b in bots]
        pos = [x + (i - 1) * w for x in xs]
        ax.bar(pos, vals, width=w - 0.02, color=COLOR[mk], label=LABEL[mk], zorder=3)
        for p, v in zip(pos, vals):
            ax.text(p, v + 1.6, f"{v:.0f}%", ha="center", fontsize=8.5, color=INK2)
    ax.set_xticks(list(xs)); ax.set_xticklabels(names, fontsize=8.5)
    ax.set_ylabel("Top-1 next-room accuracy"); ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper right", ncol=1)
    _finish(ax, "The model learns habits — and correctly learns nothing from noise",
            "Prequential top-1 accuracy over {door, door, ..., stay}. 10 rooms, 1200 windows x 12 seeds")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


def fig_learning(out):
    cur = M["e2_learning"]["curves"]; win = M["e2_learning"]["window"]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    LIMIT = 20
    for mk in ["uniform", "markov-1", "vomm"]:
        ys = [v * 100 for v in cur[mk]][:LIMIT]
        xs = [(i + 1) * win for i in range(len(ys))]
        ax.plot(xs, ys, color=COLOR[mk], lw=2, zorder=3)
        ax.text(xs[-1] + 12, ys[-1], LABEL[mk], color=COLOR[mk], fontsize=9, va="center")
    ax.set_xlabel("Player moves observed"); ax.set_ylabel("Top-1 accuracy (rolling)")
    ax.set_ylim(0, 105); ax.set_xlim(0, max(xs) * 1.34)
    ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    _finish(ax, "It learns you inside the first minute of play",
            "Rolling top-1 accuracy (20-move window), habitual player, mean of 12 seeds")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


def fig_capture(out):
    order = ["random-walk", "hub-camp", "markov-1", "vomm", "vomm-intercept"]
    nice = {"random-walk": "Random walk (control)", "hub-camp": "Camp the busiest junction",
            "markov-1": "Order-1 Markov director", "vomm": "VOMM, one-step targeting",
            "vomm-intercept": "VOMM interceptor (proposed)"}
    vals = [M["e4_pursuit"][k]["per_1000"] for k in order]
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    ypos = range(len(order))
    cols = ["#2a78d6"] * len(order)
    cols[order.index("vomm")] = "#8fb9e8"          # the naive variant, same hue, lighter
    ax.barh(list(ypos), vals, height=0.55, color=cols, zorder=3)
    for y, v in zip(ypos, vals):
        ax.text(v + 6, y, f"{v:.0f}", va="center", fontsize=9.5, color=INK)
    ax.set_yticks(list(ypos)); ax.set_yticklabels([nice[k] for k in order], fontsize=9.5)
    ax.invert_yaxis(); ax.set_xlabel("Captures per 1000 player moves"); ax.set_xlim(0, max(vals) * 1.22)
    ax.grid(axis="x", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    _finish(ax, "Better prediction becomes a measurably more dangerous entity",
            "Embodied pursuit: the entity occupies a room and moves one room per step")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


def fig_disruption(out):
    d = M["e5_disruption"]
    labels = ["Facility left alone", "Director sealing and\nrewiring ahead of you"]
    vals = [d["no-director"]["moves_per_lap"], d["full-director"]["moves_per_lap"]]
    errs = [d["no-director"]["sd"], d["full-director"]["sd"]]
    fig, ax = plt.subplots(figsize=(8.2, 3.9))
    ax.bar([0, 1], vals, width=0.42, color=["#9aa3ab", "#2a78d6"], zorder=3,
           yerr=errs, ecolor="#6b7178", capsize=5)
    for x, v in zip([0, 1], vals):
        ax.text(x, v + 1.4, f"{v:.1f}", ha="center", fontsize=12, fontweight="bold", color=INK)
    ax.set_xticks([0, 1]); ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Moves per objective lap"); ax.set_ylim(0, max(vals) * 1.32)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    ax.annotate(f"+{d['full-director']['overhead_pct']:.0f}%",
                xy=(1, vals[1]), xytext=(1.34, vals[1] * 0.72),
                fontsize=15, fontweight="bold", color="#2a78d6")
    a = d["full-director"]["actions"]
    _finish(ax, "World edits impose a real navigation cost",
            f"No entity — mutation only. {a['rewire']} rewires, {a['seal']} seals, "
            f"{a['poison']} poisons across 12 seeds x 1500 moves")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


def fig_scaling(out):
    E = M["e7_scaling"]
    sizes = sorted(int(k) for k in E)
    series = [
        ("vomm-intercept", "VOMM interceptor", "#2a78d6"),
        ("markov-1",       "Order-1 Markov",   "#eb6834"),
        ("hub-camp",       "Camp the hub",     "#1baf7a"),
        ("random-walk",    "Random (control)", "#9aa3ab"),
    ]
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    for key, label, col in series:
        ys = [E[str(n)][key] for n in sizes]
        ax.plot(sizes, ys, color=col, lw=2, marker="o", ms=5, zorder=3)
        ax.text(sizes[-1] + 0.8, ys[-1], label, color=col, fontsize=9, va="center")
    ax.set_xlabel("Rooms in the facility"); ax.set_ylabel("Captures per 1000 player moves")
    ax.set_xticks(sizes); ax.set_xlim(sizes[0] - 1, sizes[-1] + 11)
    ax.set_ylim(0, max(E[str(sizes[0])].values()) * 1.12)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    lo = E[str(sizes[0])]["advantage_vs_hub"]; hi = E[str(sizes[-1])]["advantage_vs_hub"]
    _finish(ax, "Prediction matters more as the facility grows",
            f"Advantage over hub-camping widens from {lo:.2f}x to {hi:.2f}x. "
            "Habitual player, 1200 moves x 8 seeds per point")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


def fig_dwell(out):
    E = M["e10_dwell_learned"]
    labels = ["Assume they\nalways move", "VOMM\n(all rooms)",
              "VOMM in rooms\nwith nothing to record", "VOMM in rooms\nwith a codebook"]
    vals = [E["baseline_accuracy"], E["vomm_accuracy"], E["vomm_plain_rooms"], E["vomm_task_rooms"]]
    cols = ["#9aa3ab", "#2a78d6", "#2a78d6", "#2a78d6"]
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    ax.bar(range(len(vals)), [x * 100 for x in vals], width=0.5, color=cols, zorder=3)
    for i, x in enumerate(vals):
        ax.text(i, x * 100 + 1.8, f"{x*100:.0f}%", ha="center", fontsize=11,
                fontweight="bold", color=INK)
    ax.set_xticks(range(len(vals))); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Accuracy predicting 'will they stay?'"); ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    _finish(ax, "It learned where you stop to write",
            f"Dwell as a binary prediction task. Actual dwell rate {E['actual_dwell_rate']*100:.0f}%; "
            "pages take 1-4 windows")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


def fig_localisation(out):
    E = M["e11_localisation"]
    covs = sorted(E["uniform"], key=float)
    fig, ax = plt.subplots(figsize=(8.2, 4.1))
    for key, label, col in (("uniform", "Uniform prior", "#eb6834"),
                            ("learned", "Learned transition prior", "#2a78d6")):
        ys = [E[key][c]["localisation"] * 100 for c in covs]
        xs = [float(c) * 100 for c in covs]
        ax.plot(xs, ys, color=col, lw=2, marker="o", ms=5, zorder=3)
        ax.text(xs[0] - 3, ys[0], label, color=col, fontsize=9, ha="right", va="center")
    ax.set_xlabel("Doors carrying a live sensor"); ax.set_ylabel("Antagonist locates the player")
    ax.set_xlim(-22, 108); ax.set_ylim(0, 108)
    ax.set_xticks([20, 40, 60, 80, 100]); ax.set_xticklabels(["20%", "40%", "60%", "80%", "100%"])
    ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    _finish(ax, "Full sensor coverage is still perfect tracking",
            "Silence tells it you stayed, so a fully wired facility leaks everything. "
            "Belief filter over door events, 1200 windows x 12 seeds")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


def fig_counterplay(out):
    E = M["e12_counterplay"]
    covs = sorted(E, key=float, reverse=True)
    strats = [("habitual", "Habitual (baseline)", "#9aa3ab"),
              ("evasive", "Waits at random", "#eb6834"),
              ("route_around", "Routes around sensors", "#1baf7a"),
              ("disable_3", "Disables 3 sensors on its route", "#2a78d6")]
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    w, xs = 0.2, range(len(covs))
    for i, (key, label, col) in enumerate(strats):
        vals = [E[c][key]["per_lap"] for c in covs]
        pos = [x + (i - 1.5) * w for x in xs]
        ax.bar(pos, vals, width=w - 0.02, color=col, label=label, zorder=3)
        for px, v in zip(pos, vals):
            ax.text(px, v + 0.09, f"{v:.1f}", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{float(c):.0%} of doors wired" for c in covs], fontsize=9.5)
    ax.set_ylabel("Captures per completed objective")
    ax.set_ylim(0, max(E[c][k]["per_lap"] for c in covs for k, _, _ in strats) * 1.22)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", ncol=2)
    _finish(ax, "Killing a sensor beats avoiding one — and waiting is worse than useless",
            "Per objective completed, not per window: all four strategies pay the same notebook cost")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


if __name__ == "__main__":
    out = ROOT / "out"; out.mkdir(exist_ok=True)
    fig_accuracy(out / "fig_accuracy.png")
    fig_learning(out / "fig_learning.png")
    fig_capture(out / "fig_capture.png")
    fig_disruption(out / "fig_disruption.png")
    fig_scaling(out / "fig_scaling.png")
    fig_dwell(out / "fig_dwell.png")
    fig_localisation(out / "fig_localisation.png")
    fig_counterplay(out / "fig_counterplay.png")
    print("figures written:", *[p.name for p in sorted(out.glob("*.png"))])
