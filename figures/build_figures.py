#!/usr/bin/env python3
"""Build figures 2-4 from results/analysis.json only. Each figure function
returns the numbers it drew, printed for checking against the source."""

import json
import pathlib
import sys

import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import style as S  # noqa: E402

A = json.loads((HERE.parent / "results" / "analysis.json").read_text())
ASSETS = HERE.parent / "paper" / "iclr" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

MODELS = ["gemini-3.6-flash", "gemini-3.1-pro-preview", "openai/gpt-5.6-luna", "modal-qwen2.5-7b"]
CONDS = ["A", "B_strict", "C", "D", "E"]
COND_LABEL = {"A": "v1 baseline", "B_strict": "silent drift", "C": "+ diff",
              "D": "+ full v2 schema", "E": "+ error retry"}
CLASSES = ["rename", "enum_tighten", "required", "type_change", "default_change"]
CLASS_LABEL = {"rename": "rename", "enum_tighten": "enum-tighten", "required": "newly-required",
               "type_change": "type-change", "default_change": "default-change"}


def fig2():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.3, 2.9),
                                   gridspec_kw={"wspace": 0.34})
    drawn = {}
    x = np.arange(len(CONDS))
    for m in MODELS:
        sr = A["models"][m]["success_rate"]
        ys = [sr[c] for c in CONDS]
        drawn[m] = ys
        ax1.plot(x, ys, color=S.FAMILY_COLOR[m], lw=2.2, solid_capstyle="round", zorder=3)
        ax1.scatter(x, ys, s=52, color=S.FAMILY_COLOR[m], edgecolor=S.SURFACE,
                    linewidth=1.4, zorder=4)
    # direct labels at line ends, nudged apart
    ends = sorted([(drawn[m][-1], m) for m in MODELS])
    slots = np.linspace(0.18, 0.62, len(ends))
    for slot, (yv, m) in zip(slots, ends):
        ax1.annotate(S.FAMILY_LABEL[m], xy=(x[-1] + 0.06, yv), xytext=(x[-1] + 0.55, slot),
                     fontsize=8, color=S.FAMILY_COLOR[m], va="center",
                     arrowprops=dict(arrowstyle="-", color=S.FAINT, lw=0.7))
    ax1.set_xticks(x, [COND_LABEL[c] for c in CONDS], rotation=25, fontsize=7.8)
    ax1.set_ylim(0, 1.04)
    ax1.set_ylabel("task success")
    ax1.set_xlim(-0.3, len(CONDS) + 1.5)
    S.frame(ax1)
    S.eyebrow(ax1, "Success by condition")

    levers = ["C", "D", "E"]
    ypos = np.arange(len(levers))[::-1]
    off = {"gemini-3.6-flash": 0.27, "gemini-3.1-pro-preview": 0.09,
           "openai/gpt-5.6-luna": -0.09, "modal-qwen2.5-7b": -0.27}
    rec = {}
    for m in MODELS:
        rf = A["models"][m]["levers"]
        for i, lv in enumerate(levers):
            r = rf[lv]["recovery_fraction"].get("overall")
            if not r:
                continue
            rec[(m, lv)] = r
            y = ypos[i] + off[m]
            ax2.plot(r["ci95"], [y, y], color=S.FAMILY_COLOR[m], lw=1.6, zorder=3)
            ax2.scatter([r["point"]], [y], s=48, color=S.FAMILY_COLOR[m],
                        edgecolor=S.SURFACE, linewidth=1.3, zorder=4)
    ax2.axvline(0, color=S.MUTED, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax2.text(0.015, ypos[-1] - 0.58, "no recovery", fontsize=8, color=S.MUTED)
    ax2.axvline(1, color=S.FAINT, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax2.text(0.985, ypos[-1] - 0.58, "full recovery", fontsize=8, color=S.MUTED, ha="right")
    ax2.set_yticks(ypos, ["structured diff", "full v2 schema", "raw-error retry"])
    ax2.set_xlabel("recovery fraction of the drift-induced drop")
    ax2.set_xlim(-0.35, 1.12)
    S.frame(ax2, grid_y=False)
    ax2.grid(axis="x", color=S.RULE, linewidth=0.6, zorder=0)
    S.eyebrow(ax2, "Recovery by lever")
    ax2.annotate("diff on GPT-5.6-luna: below zero",
                 xy=(rec[("openai/gpt-5.6-luna", "C")]["point"] - 0.01, ypos[0] - 0.09),
                 xytext=(-0.32, ypos[0] - 0.62), fontsize=8, color=S.HOT,
                 arrowprops=dict(arrowstyle="-", color=S.FAINT, lw=0.8))
    ax2.set_ylim(ypos[-1] - 0.75, ypos[0] + 0.55)
    fig.savefig(ASSETS / "fig2_conditions_recovery.pdf")
    plt.close(fig)
    return {"success": drawn, "recovery": {f"{m}:{lv}": v["point"] for (m, lv), v in rec.items()}}


def fig3():
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.7), gridspec_kw={"wspace": 0.30})
    drawn = {}
    for ax, prof, title in [(axes[0], "B_strict", "Strict executor"),
                            (axes[1], "B_lenient", "Lenient executor")]:
        lg = A["models"]["gemini-3.6-flash"]["ledger"][prof]
        x = np.arange(len(CLASSES))
        wrong = [lg[c]["accepted_wrong"] for c in CLASSES]
        err = [lg[c]["error_surfaced"] for c in CLASSES]
        ok = [lg[c]["accepted_correct"] for c in CLASSES]
        drawn[prof] = {"wrong": wrong, "err": err, "ok": ok}
        ax.bar(x, err, width=0.62, color=S.SLATE, zorder=3)
        ax.bar(x, wrong, width=0.62, bottom=err, color=S.HOT, zorder=3)
        ax.bar(x, ok, width=0.62, bottom=[e + w for e, w in zip(err, wrong)],
               color=S.GOOD, zorder=3, alpha=0.55)
        ax.set_xticks(x, [CLASS_LABEL[c] for c in CLASSES], rotation=22, fontsize=8)
        ax.set_ylim(0, 1.34)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        S.frame(ax)
        S.eyebrow(ax, title, y=1.02)
        if prof == "B_strict":
            ax.set_ylabel("share of drifted calls")
            ax.annotate("default-change is silent even\nunder a strict validator",
                        xy=(3.85, 0.20), xytext=(0.6, 1.12), fontsize=8, color=S.INK2,
                        arrowprops=dict(arrowstyle="-", color=S.FAINT, lw=0.8))
        else:
            ax.annotate("a tolerant API converts rename and\ntype drift into silent wrong calls",
                        xy=(0.28, 1.02), xytext=(0.75, 1.12), fontsize=8, color=S.INK2,
                        arrowprops=dict(arrowstyle="-", color=S.FAINT, lw=0.8))
    # key (color dots + ink text, no legend box)
    for xx, col, lab in [(0.02, S.SLATE, "error surfaced"), (0.42, S.HOT, "accepted, wrong semantics"),
                         (1.12, S.GOOD, "accepted, correct")]:
        axes[0].scatter([xx], [-0.40], transform=axes[0].transAxes, s=26, color=col, clip_on=False)
        axes[0].text(xx + 0.035, -0.405, lab, transform=axes[0].transAxes, fontsize=8,
                     color=S.INK2, va="center")
    fig.savefig(ASSETS / "fig3_ledger.pdf")
    plt.close(fig)
    return drawn


def fig4():
    fig, ax = plt.subplots(figsize=(6.3, 2.5))
    drawn = {}
    for m in MODELS:
        st = A["models"][m]["arg_style"]
        xv, yv = st["optional_fill_rate"], st["b_strict_success_immune_classes"]
        drawn[m] = (xv, yv)
        ax.scatter([xv], [yv], s=110, color=S.FAMILY_COLOR[m], edgecolor=S.SURFACE,
                   linewidth=1.6, zorder=4)
    # labels
    lab_off = {"gemini-3.6-flash": (-0.015, 0.09), "gemini-3.1-pro-preview": (-0.015, -0.10),
               "openai/gpt-5.6-luna": (-0.30, -0.01), "modal-qwen2.5-7b": (0.015, 0.07)}
    for m, (xv, yv) in drawn.items():
        dx, dy = lab_off[m]
        ha = "left" if dx >= 0 else "left"
        ax.text(xv + dx, yv + dy, S.FAMILY_LABEL[m], fontsize=8.5,
                color=S.FAMILY_COLOR[m], ha=ha, va="center")
    xs = np.array([drawn[m][0] for m in MODELS])
    ys = np.array([drawn[m][1] for m in MODELS])
    b, a = np.polyfit(xs, ys, 1)
    xx = np.linspace(0.40, 1.02, 10)
    ax.plot(xx, a + b * xx, color=S.FAINT, lw=1.2, ls=(0, (4, 3)), zorder=2)
    ax.set_xlabel("share of optional parameters passed explicitly (baseline calls)")
    ax.set_ylabel("survival on required +\ndefault-change drift")
    ax.set_xlim(0.40, 1.06)
    ax.set_ylim(0, 1.05)
    S.frame(ax)
    S.eyebrow(ax, "Calling style buys mechanical immunity", y=1.10)
    ax.annotate("a model that always fills defaults itself\ncannot be hit by default-change or\nnewly-required drift",
                xy=(drawn["openai/gpt-5.6-luna"][0] - 0.005, drawn["openai/gpt-5.6-luna"][1] - 0.03),
                xytext=(0.42, 0.62), fontsize=8.5, color=S.INK2,
                arrowprops=dict(arrowstyle="-", color=S.FAINT, lw=0.8))
    fig.savefig(ASSETS / "fig4_argstyle.pdf")
    plt.close(fig)
    return drawn


if __name__ == "__main__":
    print("fig2:", json.dumps(fig2(), default=float)[:400])
    print("fig3:", json.dumps(fig3())[:300])
    print("fig4:", json.dumps(fig4()))
    print("saved to", ASSETS)
