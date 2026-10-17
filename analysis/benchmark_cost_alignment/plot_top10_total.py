"""Export the saved top-10 total-cost panel without recomputing benchmark data.

Run: env3.12/bin/python analysis/benchmark_cost_alignment/plot_top10_total.py
Rendering matches alignment_plot.py; the legend is inside the bottom left.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--tall", action="store_true", help="Export a narrow portrait version.")
parser.add_argument("--wide", action="store_true", help="Export the tall version's styling in a landscape figure.")
parser.add_argument("--no-ids", action="store_true", help="Hide point ID numbers while keeping all other text and labeling our point 'Strautomata (Ours)'.")
parser.add_argument("--dir", default=None, help="Directory holding benchmark_table_top10.csv; outputs go there too "
                    "(e.g. max_vs_mean2/top2_board/out for the top-2 board version). Default: this script's directory.")
args = parser.parse_args()
OUT_DIR = Path(args.dir).resolve() if args.dir else Path(__file__).resolve().parent
TOP_K = 10
SUFFIX = "_top10_total_tall" if args.tall else ("_top10_total_wide" if args.wide else "_top10_total")
if args.no_ids:
    SUFFIX += "_no_ids"
STYLED = args.tall or args.wide  # frontier-cost title, two-line x label, "(Ours)" label bottom-right
_a = SimpleNamespace(show_ci=False)
plot_all = pd.read_csv(OUT_DIR / "benchmark_table_top10.csv")

# Match plot_median_elo in src/experimental/exp_plotting.py: plain seaborn whitegrid, no custom colours/weights.
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"pdf.fonttype": 42})

ARENA_TYPE = {"game_arena", "agent_arena", "aa_briefcase", "aa_gdpval", "lmarena_text", "lmarena_webdev", "designarena_gamedev",
              "designarena_3d", "lech_debate", "snakebench", "chessbench", "threejs_eval", "duellab"}       # head-to-head / pairwise-judged (Elo, BT, TrueSkill)
TYPE_MARKER = {"arena": "^", "individual": "o"}
def btype(b): return "arena" if b in ARENA_TYPE else "individual"
def family(b): return "ours" if b == "game_arena" else ("aa" if b.startswith("aa_") else ("vals" if b.startswith("vals_") else "other"))
# Keep Strautomata orange; match the other points to the engine chess purple.
FCOL = {"ours": "#e66b00", "aa": "#6c4ca8", "vals": "#6c4ca8", "other": "#6c4ca8"}
DISPLAY = {"game_arena": "Strautomata", "threejs_eval": "Three.js Eval", "normal_cad_arena": "Normal CAD Arena", "duellab": "DuelLab", "pinnacle": "PINNACLE"}
def disp(b): return DISPLAY.get(b, b)

fig, ax = plt.subplots(figsize=(5, 6) if args.tall else ((9, 4.5) if args.wide else (10, 4)))
axes = [ax]
panels = [("pair_total", "GPT-6 Astra + Claude Fable 5.1 (USD total cost, log)", "Total Cost")]
for ax, (col, xl, ttl) in zip(axes, panels):
    plot = plot_all.dropna(subset=[col])
    for _, r in plot.iterrows():
        b = r["benchmark"]; fam = family(b); ours = fam == "ours"; mk = TYPE_MARKER[btype(b)]; sat = bool(r["saturated"])
        size = (100 if mk == "^" else 70) * (0.25 if sat else 1)
        if ours:
            size = 150
            # Soft halo plus a white rim keeps the orange triangle clear over the frontier.
            for halo_size, halo_alpha in [(340, 0.06)]:
                ax.scatter(r[col], r["kendall_tau"], s=halo_size, marker=mk, color=FCOL[fam],
                           edgecolor="none", alpha=halo_alpha, zorder=3)
            ax.scatter(r[col], r["kendall_tau"], s=size + 40, marker=mk,
                       color="white", edgecolor="none", zorder=4)
        if _a.show_ci and not np.isnan(r["tau_lo"]):
            ax.errorbar(r[col], r["kendall_tau"], yerr=[[r["kendall_tau"] - r["tau_lo"]], [r["tau_hi"] - r["kendall_tau"]]],
                        fmt="none", ecolor=FCOL[fam], elinewidth=1.0, capsize=2, alpha=0.15 if sat else 0.45, zorder=1)
        ax.scatter(r[col], r["kendall_tau"], s=size, marker=mk, color=FCOL[fam], alpha=0.3 if sat else (1 if ours else 0.95),
                   edgecolor="#713600" if ours else "#555555", linewidth=0.9 if ours else 0.5,
                   zorder=5 if ours else (2 if sat else 3))
        # Separate the near-coincident labels and keep the rightmost ID inside.
        label_offset, label_align = {
            25: ((-8, 6), "right"),
            34: ((8, -10), "left"),
            38: ((-8, -10), "right"),
            33: ((-8, 5), "right"),
        }.get(int(r["benchmark_id"]), ((7, 4), "left"))
        if args.tall:  # portrait layout packs points tighter; spread the colliding IDs
            label_offset, label_align = {
                26: ((-8, -10), "right"),
                36: ((8, -10), "left"),
                40: ((8, -10), "left"),
                33: ((-8, 5), "right"),
                35: ((-8, 5), "right"),
            }.get(int(r["benchmark_id"]), (label_offset, label_align))
        if args.wide:  # top-2 board IDs are shifted by one; separate the pair near $2k and the pair near $8k
            label_offset, label_align = {
                26: ((-8, 6), "right"),
                36: ((8, -10), "left"),
                40: ((8, -10), "left"),
            }.get(int(r["benchmark_id"]), (label_offset, label_align))
        if ours and STYLED:
            label_offset, label_align = (7, -7), "left"  # bottom-right of the marker
        point_label = ("Strautomata (Ours)" if ours else "") if args.no_ids else (f'{r["benchmark_id"]} (Ours)' if ours else str(r["benchmark_id"]))
        ax.annotate(point_label, (r[col], r["kendall_tau"]),
                    xytext=label_offset, ha=label_align, va="top" if (ours and STYLED) else "baseline",
                    textcoords="offset points", fontsize=8 if ours else 7,
                    color=FCOL[fam], fontweight="bold" if ours else "normal",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.92) if ours else None,
                    alpha=0.65 if sat else 1, zorder=6)
    # Pareto frontier (cheaper and more aligned dominates); saturated boards excluded
    cand = plot[~plot["saturated"].astype(bool)].sort_values([col, "kendall_tau"], ascending=[True, False])
    front, best = [], -np.inf
    for _, r in cand.iterrows():
        if r["kendall_tau"] > best: front.append((r[col], r["kendall_tau"])); best = r["kendall_tau"]
    if len(front) > 1:
        fx, fy = zip(*front)
        ax.plot(fx, fy, ls=":", color="black", lw=1.6, alpha=0.95, zorder=2, label="Non-saturated Pareto Fronteir")
    # keep the y range set by the point estimates; a few tiny-n boards have CIs wide enough to
    # rescale the whole panel, so let those bars clip instead.
    ax.set_ylim(0.35, plot["kendall_tau"].max() + 0.05)
    ax.set_xscale("log"); ax.set_xlabel(xl)
    if TOP_K == 10 and col == "pair_total":
        from matplotlib.patches import Rectangle
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        ax.add_patch(Rectangle((xmin, 0.6), 200 - xmin, ymax - 0.6,
                               facecolor=(76 / 255, 175 / 255, 80 / 255, 0.18),
                               edgecolor="none", zorder=0))
        ax.set_xlim(xmin, xmax)
        ax.text(np.sqrt(xmin * 200), 0.6 + (0.84 if args.tall else 0.72) * (ymax - 0.6),
                "high quality\nbenchmark\nfor <$200" if args.tall else "high quality benchmark\nfor <$200", ha="center", va="center",
                fontsize=12, fontweight="bold", fontfamily="DejaVu Sans",
                linespacing=1.0, color="#229b25", alpha=1.0, zorder=4)
    ax.grid(False, which="minor")
    ax.grid(axis="both", which="major", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", length=0)
    ax.set_title("Benchmark Alignment vs Cost Per Task/Unit" if col == "pair_per_unit" else "Benchmark Alignment vs Total Cost", pad=10)
for ax in axes:
    ax.set_ylabel("Alignment (Kendall τ)")
    if STYLED:
        ax.set_title("Benchmark Alignment vs Frontier Cost", pad=10)
        ax.set_xlabel("GPT-6 Astra + Claude Fable 5.1\n(USD total cost, log)")
# marker legend
from matplotlib.lines import Line2D
handles = [Line2D([], [], marker="^", ls="", ms=9, color=FCOL["other"], label="arena (pairwise)"),
           Line2D([], [], marker="o", ls="", ms=9, color=FCOL["other"], label="individual"),
           Line2D([], [], marker="o", ls="", ms=4, color=FCOL["other"], alpha=0.3, label="saturated"),
           Line2D([], [], ls=":", color="black", lw=1.5, label="Non-saturated\nPareto frontier")]
if _a.show_ci:
    handles.insert(4, Line2D([], [], ls="-", color="gray", lw=1.0, label="95% CI on τ (bootstrap over shared models)"))
axes[0].legend(handles=handles, loc="lower left", fontsize=7 if args.tall else 8.5, frameon=True, framealpha=0.9, edgecolor="none", ncol=1,
               markerscale=0.6, labelspacing=0.7, handletextpad=0.65, borderaxespad=0.7)
fig.tight_layout(pad=1.0, h_pad=1.5)
if TOP_K == 10:
    # Separate outline inset by two pixels at the PNG's 160 dpi export size.
    ax = axes[0]
    lower = ax.transAxes.inverted().transform(ax.transData.transform((ax.get_xlim()[0], 0.6)))
    upper = ax.transAxes.inverted().transform(ax.transData.transform((200, ax.get_ylim()[1])))
    inset_x = 2 / (ax.get_position().width * fig.get_figwidth() * 160)
    inset_y = 2 / (ax.get_position().height * fig.get_figheight() * 160)
    ax.add_patch(Rectangle((lower[0] + inset_x, lower[1] + inset_y),
                           upper[0] - lower[0] - 2 * inset_x,
                           upper[1] - lower[1] - 2 * inset_y,
                           transform=ax.transAxes, facecolor="none",
                           edgecolor=(76 / 255, 175 / 255, 80 / 255, 0.32),
                           linewidth=0.8, linestyle="-", zorder=1))
fig.savefig(OUT_DIR / f"cost_vs_alignment{SUFFIX}.png", dpi=160, bbox_inches="tight")
fig.savefig(OUT_DIR / f"cost_vs_alignment{SUFFIX}.pdf", bbox_inches="tight")
print("\nsaved", OUT_DIR / f"cost_vs_alignment{SUFFIX}.png")
