"""House figure style for the SchemaDrift-120 paper. Import from every build
script; never style inline. Palette identical to the website."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SLATE = "#155e8c"
HOT = "#b3006b"
SHELF = "#c0641a"
GOOD = "#1c7a55"
INK = "#16130d"
INK2 = "#3a352b"
MUTED = "#6d665a"
FAINT = "#a49c8c"
RULE = "#e7e2d5"
SURFACE = "#ffffff"

FAMILY_COLOR = {
    "gemini-3.6-flash": SLATE,
    "gemini-3.1-pro-preview": GOOD,
    "openai/gpt-5.6-luna": HOT,
    "modal-qwen2.5-7b": SHELF,
}
FAMILY_LABEL = {
    "gemini-3.6-flash": "Gemini 3.6 Flash",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "openai/gpt-5.6-luna": "GPT-5.6-luna",
    "modal-qwen2.5-7b": "Qwen2.5-7B",
}

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 10,
    "axes.labelsize": 9.5,
    "axes.labelcolor": MUTED,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": RULE,
    "axes.linewidth": 0.8,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def frame(ax, grid_y=True):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    if grid_y:
        ax.grid(axis="y", color=RULE, linewidth=0.6, zorder=0)
    ax.tick_params(length=0)


def eyebrow(ax, text, y=1.06):
    spaced = " ".join(text.upper())  # emulate letter-spacing
    ax.text(0, y, spaced, transform=ax.transAxes, ha="left",
            fontsize=8.5, color=MUTED, fontweight="bold")


def annotate(ax, text, xy, xytext, color=INK2, fs=8.5):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, color=color,
                arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8),
                ha="left", va="center")
