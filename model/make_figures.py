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
    bots = ["habitual", "explorer", "random"]
    names = ["Habitual player\n(follows routes)", "Explorer\n(systematic sweep)", "Random\n(control)"]
    models = ["uniform", "markov-1", "vomm"]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    w, xs = 0.26, range(len(bots))
    for i, mk in enumerate(models):
        vals = [M["e1_accuracy"][f"{b}|{mk}"]["top1"] * 100 for b in bots]
        pos = [x + (i - 1) * w for x in xs]
        ax.bar(pos, vals, width=w - 0.02, color=COLOR[mk], label=LABEL[mk], zorder=3)
        for p, v in zip(pos, vals):
            ax.text(p, v + 1.6, f"{v:.0f}%", ha="center", fontsize=8.5, color=INK2)
    ax.set_xticks(list(xs)); ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("Top-1 next-room accuracy"); ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper right", ncol=1)
    _finish(ax, "The model learns habits — and correctly learns nothing from noise",
            "Prequential top-1 accuracy, 10-room facility, 1200 steps x 12 seeds")
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
    order = ["random-walk", "hub-camp", "markov-1", "vomm"]
    nice = {"random-walk": "Random walk (control)", "hub-camp": "Camp the busiest junction",
            "markov-1": "Order-1 Markov director", "vomm": "VOMM director (proposed)"}
    vals = [M["e4_pursuit"][k]["per_1000"] for k in order]
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    ypos = range(len(order))
    ax.barh(list(ypos), vals, height=0.55, color="#2a78d6", zorder=3)
    for y, v in zip(ypos, vals):
        ax.text(v + 6, y, f"{v:.0f}", va="center", fontsize=9.5, color=INK)
    ax.set_yticks(list(ypos)); ax.set_yticklabels([nice[k] for k in order], fontsize=9.5)
    ax.invert_yaxis(); ax.set_xlabel("Captures per 1000 player moves"); ax.set_xlim(0, max(vals) * 1.22)
    ax.grid(axis="x", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    _finish(ax, "Better prediction becomes a measurably more dangerous entity",
            "Embodied pursuit: the entity occupies a room and moves one room per step")
    fig.tight_layout(); fig.savefig(out, dpi=200); plt.close(fig)


if __name__ == "__main__":
    out = ROOT / "out"; out.mkdir(exist_ok=True)
    fig_accuracy(out / "fig_accuracy.png")
    fig_learning(out / "fig_learning.png")
    fig_capture(out / "fig_capture.png")
    print("figures written:", *[p.name for p in sorted(out.glob("*.png"))])
