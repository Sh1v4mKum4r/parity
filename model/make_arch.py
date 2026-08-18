"""System architecture diagram for the review deck."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

INK, MUT, LINE, BLUE, AMB, GRN = "#16181a", "#6b7178", "#d8dce0", "#2a78d6", "#eb6834", "#1baf7a"
fig, ax = plt.subplots(figsize=(11, 5.6))
fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
ax.set_xlim(-1, 101); ax.set_ylim(0, 52); ax.axis("off")

def box(x, y, w, h, title, sub, edge=LINE, fill="#ffffff", tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=0.6",
                                linewidth=1.4, edgecolor=edge, facecolor=fill, zorder=3))
    ax.text(x + w/2, y + h*0.62, title, ha="center", va="center", fontsize=10.5,
            fontweight="bold", color=tc, zorder=4)
    ax.text(x + w/2, y + h*0.26, sub, ha="center", va="center", fontsize=7.6, color=MUT, zorder=4)

def arrow(x1, y1, x2, y2, col=MUT, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=13,
                                 linewidth=1.3, color=col, zorder=2,
                                 connectionstyle="arc3,rad=0"))

# group frame: simulation core
ax.add_patch(FancyBboxPatch((3, 30.5), 94, 18, boxstyle="round,pad=0.4,rounding_size=0.6",
                            linewidth=1.1, edgecolor="#c9ced4", facecolor="#f4f6f8", zorder=1))
ax.text(4.6, 46.4, "SIMULATION CORE  ·  headless, unit-tested, no rendering dependency",
        fontsize=8, color=MUT, fontweight="bold", zorder=4)

box(6,  33, 25, 10, "Facility",  "room graph · mutation ops")
box(37, 33, 25, 10, "Cipher",    "codebooks · register · send")
box(68, 33, 25, 10, "Sabotage",  "the ONLY mutator of state", edge=AMB)

# agent chain
box(6,  15, 25, 10, "Telemetry", "routes · dwell · verify time")
box(37, 15, 25, 10, "Predictor", "VOMM · persists across runs", edge=BLUE)
box(68, 15, 25, 10, "Director",  "scores counter-moves", edge=BLUE)

# embodiment
box(37, 2, 25, 9.5, "Entity", "patrol · hunt · ambush")
box(68, 2, 25, 9.5, "Notebook", "player's vector editor", edge=GRN)

arrow(31, 20, 37, 20); arrow(62, 20, 68, 20)
arrow(80.5, 25, 80.5, 30.5, col=AMB)              # director -> sabotage
arrow(74, 15, 58, 11.5)                            # director -> entity
ax.text(2.2, 20, "player\nactions", fontsize=8, color=MUT, ha="center", va="center")
arrow(0.5, 20, 6, 20)

ax.text(80.5, 0.2, "outside the loop — the Director cannot touch it",
        fontsize=7.6, color=GRN, ha="center", style="italic")
ax.text(50, 49.6, "PARITY — module architecture", fontsize=12.5, fontweight="bold",
        color=INK, ha="center")

fig.tight_layout()
out = Path(__file__).parent.parent / "out" / "fig_arch.png"
fig.savefig(out, dpi=200, facecolor="#fcfcfb"); print("wrote", out.name)
