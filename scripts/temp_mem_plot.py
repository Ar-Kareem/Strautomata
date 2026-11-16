from typing import Callable
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.offsetbox import AnnotationBbox, HPacker, TextArea


PURPLE_DARK = "#6c4ca8"
PURPLE_DEEP = "#4f367a"
PURPLE_LIGHT = "#b19dd8"
PURPLE_MID = "#8d72c0"
PURPLE_SOFT = "#9f89cf"
PURPLE_TEXT = "#2f2149"
GRID_LAVENDER = "#ddd6ef"


def _top_rounded_bar_patch(x_left: float, y_bottom: float, width: float, y_top: float,
                           radius_x: float, radius_y: float, facecolor: str, edgecolor: str = "none",
                           linewidth: float = 0.0, zorder: int = 3):
    height = y_top - y_bottom
    if height <= 0:
        return None

    rx = min(radius_x, width / 2.0)
    ry = min(radius_y, height / 2.0)

    verts = [
        (x_left, y_bottom),
        (x_left, y_top - ry),
        (x_left, y_top),
        (x_left + rx, y_top),
        (x_left + width - rx, y_top),
        (x_left + width, y_top),
        (x_left + width, y_top - ry),
        (x_left + width, y_bottom),
        (x_left, y_bottom),
        (x_left, y_bottom),
    ]
    codes = [
        Path.MOVETO,
        Path.LINETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.LINETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.LINETO,
        Path.LINETO,
        Path.CLOSEPOLY,
    ]
    return PathPatch(
        Path(verts, codes),
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        zorder=zorder,
    )


def _extract_elo_and_outcome_pct(engine_data):
    if isinstance(engine_data, pd.DataFrame):
        if "ELO" not in engine_data.columns:
            raise ValueError("engine_plot DataFrame input must include an 'ELO' column")

        df = engine_data.copy()
        df.index = df.index.astype(str)
        elo_series = pd.to_numeric(df["ELO"], errors="coerce").dropna()

        outcome_pct = {"win": None, "loss": None}
        if "win" in df.columns or "loss" in df.columns:
            if "total_matches" in df.columns:
                total_matches = pd.to_numeric(df["total_matches"], errors="coerce")
            else:
                total_cols = [
                    col
                    for col in ["win", "loss", "draw", "error", "timeout", "enemy_error", "enemy_timeout"]
                    if col in df.columns
                ]
                total_matches = (
                    df[total_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
                    if total_cols
                    else None
                )

            if total_matches is not None:
                # Exclude timeouts by either player from the percentage population.
                for col in ("timeout", "enemy_timeout"):
                    if col in df.columns:
                        total_matches = total_matches - pd.to_numeric(
                            df[col], errors="coerce"
                        ).fillna(0.0)
                for outcome, extras in (
                    ("win", ("enemy_error",)),
                    ("loss", ("error",)),
                ):
                    if outcome not in df.columns:
                        continue
                    effective_count = pd.to_numeric(df[outcome], errors="coerce")
                    for col in extras:
                        if col in df.columns:
                            effective_count = effective_count.add(
                                pd.to_numeric(df[col], errors="coerce").fillna(0.0),
                                fill_value=0.0,
                            )
                    outcome_pct[outcome] = (
                        effective_count / total_matches.replace(0, np.nan) * 100.0
                    ).reindex(elo_series.index)

        return elo_series, outcome_pct["win"], outcome_pct["loss"]

    elo_series = pd.to_numeric(engine_data, errors="coerce").dropna()
    return elo_series, None, None


# game_str = 'Chess'
# title = f'Chess SAN (with legal moves) Automata Comparison'
# game_str = 'Chess UCI'
# title = f'Chess Automata Comparison'
game_str = 'Go'
title = f'Go Automata Comparison'

def mem_plot(game_str, title, elos_mem_df, model_name_map: Callable, figsize: tuple[float, float] = (8.2, 2.9)):
    df = elos_mem_df[[f'{game_str} Comparison No Memory', f'{game_str} Comparison With Memory']]
    # remove gpt 5.2 pro from rows
    df = df.loc[df.median(1).sort_values(ascending=False).index]
    df = df.rename(columns={f'{game_str} Comparison No Memory': 'No Memory', f'{game_str} Comparison With Memory': 'With Memory'})

    # rand_mean = df.loc['random'].mean()
    # df.loc['random', 'With Memory'] = rand_mean
    # df.loc['random', 'No Memory'] = rand_mean

    with plt.style.context("seaborn-v0_8-whitegrid"), plt.rc_context({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": PURPLE_TEXT,
        "axes.labelcolor": PURPLE_TEXT,
        "xtick.color": PURPLE_TEXT,
        "ytick.color": PURPLE_TEXT,
        "text.color": PURPLE_TEXT,
        "axes.linewidth": 0.8,
        "grid.color": GRID_LAVENDER,
        "grid.linewidth": 0.8,
        "grid.alpha": 0.35,
    }):
        ax = df.plot.bar(
            figsize=figsize,
            width=0.82,
            color=[PURPLE_DARK, PURPLE_LIGHT],
            edgecolor=PURPLE_TEXT,
            linewidth=0.4,
        )

        ax.set_ylim(750, 2100)
        ax.set_ylabel("ELO")
        ax.set_xlabel("")
        ax.grid(axis="y")
        ax.set_axisbelow(True)

        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)

        avg_mem = df["With Memory"].median()
        avg_nomem = df["No Memory"].median()
        print(f'With Memory = {avg_mem:.1f}, No Memory = {avg_nomem:.1f}')
        ax.axhline(
            avg_mem,
            color=PURPLE_DEEP,
            linestyle=(0, (6, 2, 1.4, 2)),
            linewidth=2.2,
            alpha=0.98,
            label="Median (With Memory)",
        )
        ax.axhline(
            avg_nomem,
            color=PURPLE_SOFT,
            linestyle=(0, (1.5, 2.2)),
            linewidth=2.2,
            alpha=1.0,
            label="Median (No Memory)",
        )

        # ax.set_title(title)
        ax.tick_params(axis="x", length=0)
        ax.set_xticklabels([model_name_map(s) for s in df.index.astype(str)], rotation=35, ha="right")
        ax.legend(frameon=False, ncols=2, loc="upper right")
        plt.tight_layout()
        plt.show()
    out_pdf = f"figures/{game_str.replace(' ', '_').lower()}_memory.pdf"
    fig = ax.get_figure()
    fig.savefig(out_pdf, bbox_inches="tight")


def live_play_plot(base, title):

    base.index = base.index.astype(str)

    live = base[base.index.str.startswith("LLM_")].copy()
    live.index = live.index.str.removeprefix("LLM_").str.removeprefix("PEEK_")

    auto = pd.to_numeric(base, errors="coerce")
    auto.index = auto.index.str.removeprefix("PEEK_")

    out = pd.DataFrame({"Automaton": auto}).join(
        pd.DataFrame({"Live Play": pd.to_numeric(live, errors="coerce")}),
        how="left"
    ).dropna(subset=["Automaton","Live Play"])

    with plt.style.context("seaborn-v0_8-whitegrid"), plt.rc_context({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": PURPLE_TEXT,
        "axes.labelcolor": PURPLE_TEXT,
        "xtick.color": PURPLE_TEXT,
        "ytick.color": PURPLE_TEXT,
        "text.color": PURPLE_TEXT,
        "axes.linewidth": 0.8,
        "grid.color": GRID_LAVENDER,
        "grid.linewidth": 0.8,
        "grid.alpha": 0.35,
    }):
        fig, ax = plt.subplots(figsize=(3.6, 3))

        ax.scatter(
            out["Automaton"],
            out["Live Play"],
            s=24,
            alpha=0.9,
            c=PURPLE_DARK,
            edgecolors=PURPLE_TEXT,
            linewidths=0.45,
        )

        mn = min(out["Automaton"].min(), out["Live Play"].min())
        mx = max(out["Automaton"].max(), out["Live Play"].max())
        ax.plot(
            [mn, mx],
            [mn, mx],
            color=PURPLE_SOFT,
            linestyle=(0, (6, 2, 1.4, 2)),
            linewidth=1,
            alpha=0.95,
        )

        ax.set_title(f"Automaton vs Live Play {title}", pad=10)
        ax.set_xlabel("Automaton ELO")
        ax.set_ylabel("Live Play ELO")
        ax.grid(True)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()
        out_pdf = f"figures/live_play_{title.replace(' ', '_')}.pdf"
        fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
        plt.show()


def cost_bar_plot(cost_df, title: str | None, fig_name: str, model_name_map: Callable):
    required_cols = {"model", "Automata", "Live"}
    missing_cols = required_cols - set(cost_df.columns)
    if missing_cols:
        raise ValueError(f"cost_df is missing required columns: {sorted(missing_cols)}")

    df = cost_df.copy()
    df["model"] = df["model"].astype(str)
    df["Automata"] = pd.to_numeric(df["Automata"], errors="coerce")
    df["Live"] = pd.to_numeric(df["Live"], errors="coerce")
    df = df.dropna(subset=["Automata", "Live"])
    if df.empty:
        raise ValueError("cost_df has no finite Automata/Live rows to plot")
    if (df["Automata"] <= 0).any() or (df["Live"] <= 0).any():
        raise ValueError("Automata and Live values must be strictly positive for a log-scale bar plot")

    if title is None:
        if "game" in df.columns and df["game"].nunique(dropna=True) == 1:
            game_label = str(df["game"].dropna().iloc[0]).replace("_", " ").title()
            title = f"{game_label} Cost Comparison"
        else:
            title = "Automata vs Live Cost Comparison"

    plot_df = (
        df.groupby("model", as_index=True)[["Automata", "Live"]]
        .median()
    )
    plot_df = plot_df.loc[plot_df["Automata"].sort_values(ascending=True).index]

    with plt.style.context("seaborn-v0_8-whitegrid"), plt.rc_context({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": PURPLE_TEXT,
        "axes.labelcolor": PURPLE_TEXT,
        "xtick.color": PURPLE_TEXT,
        "ytick.color": PURPLE_TEXT,
        "text.color": PURPLE_TEXT,
        "axes.linewidth": 0.8,
        "grid.color": GRID_LAVENDER,
        "grid.linewidth": 0.8,
        "grid.alpha": 0.35,
        "hatch.linewidth": 0.7,
    }):
        n_models = len(plot_df)
        x_positions = np.arange(n_models, dtype=float)
        bar_width = 0.38
        fig_width = max(4.1, 0.29 * n_models + 0.9)
        fig, ax = plt.subplots(figsize=(fig_width, 3.7))

        ax.bar(
            x_positions - bar_width / 2.0,
            plot_df["Automata"].to_numpy(dtype=float),
            width=bar_width,
            color=PURPLE_DARK,
            edgecolor=PURPLE_TEXT,
            linewidth=0.45,
            label="Automata",
            zorder=3,
        )
        ax.bar(
            x_positions + bar_width / 2.0,
            plot_df["Live"].to_numpy(dtype=float),
            width=bar_width,
            color="#f7d778",
            edgecolor="#8a5a00",
            linewidth=0.55,
            label="Live",
            zorder=3,
        )

        ax.set_yscale("log")
        ax.set_ylabel("Cost ($)")
        ax.set_xlabel("")
        ax.set_title(title, pad=10)
        ax.set_xticks(x_positions)
        ax.set_xticklabels([model_name_map(s) for s in plot_df.index.astype(str)], rotation=35, ha="right")
        ax.tick_params(axis="x", length=0)
        ax.grid(axis="y", which="major")
        ax.grid(axis="y", which="minor", alpha=0.14, linewidth=0.6)
        ax.set_axisbelow(True)

        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)

        ax.legend(frameon=False, loc="upper left", ncols=2)
        plt.tight_layout()
        plt.show()

    safe_title = title.replace(" ", "_").replace("/", "_").lower()
    out_pdf = f"figures/{fig_name}.pdf"
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")


def engine_plot(engine_data, title, model_name_map: Callable, save_plot: bool = True, top_k: int = 10):
    df, win_pct, loss_pct = _extract_elo_and_outcome_pct(engine_data)
    df = df.sort_values(ascending=False).head(top_k)
    if win_pct is not None:
        win_pct = win_pct.reindex(df.index)
    if loss_pct is not None:
        loss_pct = loss_pct.reindex(df.index)
    has_percentages = any(
        pct is not None and pct.notna().any() for pct in (win_pct, loss_pct)
    )

    engine_names = {"sunfish", "alpha_beta", "stockfish 18", "stockfish 9", "stockfish 3", "stockfish 2", "stockfish 1", "lc0 20"}
    display_name_map = {
        "sunfish": "Sunfish",
        "alpha_beta": "Alpha Beta",
        "stockfish 18": "Stockfish 18 (2026)",
        "stockfish 9": "Stockfish 9 (2018)",
        "stockfish 3": "Stockfish 3 (2013)",
        "stockfish 2": "Stockfish 2 (2011)",
        "stockfish 1": "Stockfish 1.0 (2008)",
        "lc0 20": "LC0 v0.20 w7170 (2019)",
    }
    # Tailwind v4 palette: 400-level fills with 600-level outlines.
    engine_color, engine_edge = "#ffb900", "#e17100"  # amber-400 / amber-600
    auto_color, auto_edge = "#a684ff", "#7f22fe"  # violet-400 / violet-600
    win_color = "#155dfc"  # blue-600
    loss_color = "#737373"  # neutral-500

    with plt.style.context("seaborn-v0_8-whitegrid"), plt.rc_context({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": PURPLE_TEXT,
        "axes.labelcolor": PURPLE_TEXT,
        "xtick.color": PURPLE_TEXT,
        "ytick.color": PURPLE_TEXT,
        "text.color": PURPLE_TEXT,
        "axes.linewidth": 0.8,
        "grid.color": GRID_LAVENDER,
        "grid.linewidth": 0.8,
        "grid.alpha": 0.35,
    }):
        y_values = df.to_numpy(dtype=float)
        y_min = float(np.min(y_values))
        y_max = float(np.max(y_values))
        axis_lower = float(np.floor((y_min - 30.0) / 50.0) * 50.0)
        axis_padding = 90.0 if has_percentages else 40.0
        axis_upper = float(np.ceil((y_max + axis_padding) / 50.0) * 50.0)
        bar_width = 0.86
        corner_radius_x = 0.12
        corner_radius_y = 24.0

        fig_width = max(5.4, 0.52 * len(df) + 0.8)
        fig, ax = plt.subplots(figsize=(fig_width, 3.0))
        x_positions = np.arange(len(df))
        colors = [
            (engine_color, engine_edge) if str(name) in engine_names else (auto_color, auto_edge)
            for name in df.index
        ]

        for x_center, value, (color, edge) in zip(x_positions, y_values, colors):
            patch = _top_rounded_bar_patch(
                x_left=float(x_center) - bar_width / 2.0,
                y_bottom=axis_lower,
                width=bar_width,
                y_top=float(value),
                radius_x=corner_radius_x,
                radius_y=corner_radius_y,
                facecolor=color,
                edgecolor=edge,
                linewidth=0.9,
            )
            if patch is not None:
                ax.add_patch(patch)

        if has_percentages:
            for x_center, (name, value) in zip(x_positions, df.items()):
                win = win_pct.loc[name] if win_pct is not None else np.nan
                loss = loss_pct.loc[name] if loss_pct is not None else np.nan
                if pd.isna(win) and pd.isna(loss):
                    continue
                textprops = {"fontsize": 7.5, "fontweight": "semibold"}
                label = HPacker(
                    children=[
                        TextArea(f"{win:.0f}" if pd.notna(win) else "—",
                                 textprops={**textprops, "color": win_color}),
                        TextArea("/", textprops={**textprops, "color": "black"}),
                        TextArea(f"{loss:.0f}" if pd.notna(loss) else "—",
                                 textprops={**textprops, "color": loss_color}),
                        TextArea("%", textprops={**textprops, "color": "black"}),
                    ],
                    align="baseline", pad=0, sep=0,
                )
                ax.add_artist(AnnotationBbox(
                    label, (float(x_center), float(value)),
                    xybox=(0, 4), boxcoords="offset points",
                    box_alignment=(0.5, 0), frameon=False,
                    annotation_clip=False,
                ))

        ax.set_ylabel("ELO")
        ax.set_xlabel("")
        ax.set_title(title, pad=10)
        ax.grid(axis="y")
        ax.set_axisbelow(True)

        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)

        ax.set_xlim(-0.5, len(df) - 0.5)
        ax.set_ylim(axis_lower, axis_upper)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(
            [display_name_map.get(str(name), model_name_map(str(name))) for name in df.index],
            rotation=35,
            ha="right",
        )
        ax.tick_params(axis="x", length=0)

        from matplotlib.patches import Patch
        ax.legend(
            handles=[
                Patch(facecolor=engine_color, edgecolor=engine_edge, label="Engine ELO"),
                Patch(facecolor=auto_color, edgecolor=auto_edge, label="Automata ELO"),
            ],
            frameon=False,
            loc="upper right",
        )

        plt.tight_layout()
        plt.show()
        if save_plot:
            out_pdf = f"figures/engine_{title}.pdf"
            fig.savefig(out_pdf, format="pdf", bbox_inches="tight")


def plot_engine_matchups_heatmap(
    matches,
    df,
    top_k: int | None = None,
    out_dir="figures/engine_matchups",
    exclude_timeouts: bool = True,
    scale: float = 1.9,
    cell_fontsize: float | None = None,
):
    """Use the analysis heatmap; cell_fontsize sets cell text size in points.

    All models are included by default, and draws count as half wins.
    """
    from pathlib import Path
    from experimental.exp_plotting import plot_heatmap_combined
    from experimental.exp_utils import NAME_FIX_MAP
    from experimental.lm_arena.simple_example import _build_battles

    names = df.sort_values("ELO", ascending=False).head(top_k).index.astype(str).tolist()
    selected_matches = [
        match for match in matches
        if not (exclude_timeouts and match["winner"] == "timeout")
    ]
    battles = pd.DataFrame(_build_battles(selected_matches, "base", 0.0))
    if battles.empty:
        raise ValueError("No matches available for the engine heatmap")
    for col in ("model_a", "model_b"):
        battles[col] = battles[col].map(lambda name: NAME_FIX_MAP.get(name, name))
    battles = battles.loc[
        battles["model_a"].isin(names)
        & battles["model_b"].isin(names)
        & battles["model_a"].ne(battles["model_b"])
    ]
    if battles.empty:
        raise ValueError("No matchups between the selected engine plot entries")

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig = plot_heatmap_combined(
        {"Engine matchups": {"battles": battles}},
        names,
        output_dir,
        scale=scale,
        return_plot=True,
        cell_fontsize=cell_fontsize,
    )
    return fig


def plot_pairwise_win_draw_matrices(matches, df, model_name_map: Callable, top_k: int = 13, save_plot: bool = True):
    from pathlib import Path
    from matplotlib.colors import LinearSegmentedColormap
    from game_arena import utils
    from experimental.exp_utils import NAME_FIX_MAP

    def _pairwise_rate_matrices(matches, names):
        names = list(names)
        name_set = set(names)
        wins = pd.DataFrame(0.0, index=names, columns=names)
        decisive_totals = pd.DataFrame(0.0, index=names, columns=names)
        draws = pd.DataFrame(0.0, index=names, columns=names)
        all_totals = pd.DataFrame(0.0, index=names, columns=names)

        def normalize_name(name):
            name = str(name).split('/')[0]
            return NAME_FIX_MAP.get(name, name)

        for match in matches:
            name0 = normalize_name(match['name0'])
            name1 = normalize_name(match['name1'])
            if name0 not in name_set or name1 not in name_set or name0 == name1:
                continue
            reason, winner = utils.get_match_result(match, verbose=False)
            all_totals.loc[name0, name1] += 1.0
            all_totals.loc[name1, name0] += 1.0
            if reason == 'timeout':
                continue
            if winner == 0.5:
                draws.loc[name0, name1] += 1.0
                draws.loc[name1, name0] += 1.0
                continue
            if winner == 0:
                score0 = 1.0
            elif winner == 1:
                score0 = 0.0
            else:
                raise ValueError(f'Unexpected winner={winner!r} for reason={reason!r}')
            score1 = 1.0 - score0
            wins.loc[name0, name1] += score0
            wins.loc[name1, name0] += score1
            decisive_totals.loc[name0, name1] += 1.0
            decisive_totals.loc[name1, name0] += 1.0

        win_rates = wins.divide(decisive_totals).mul(100.0)
        draw_rates = draws.divide(all_totals).mul(100.0)
        for name in names:
            win_rates.loc[name, name] = np.nan
            draw_rates.loc[name, name] = np.nan
        return win_rates, decisive_totals, draw_rates, all_totals


    def _draw_pairwise_heatmap(ax, matrix, totals, labels, title, cmap_name, cbar_label, *, na_if_empty=True, show_ylabel=False):
        if isinstance(cmap_name, str) and cmap_name.startswith('#'):
            cmap = LinearSegmentedColormap.from_list(f'{title} cmap', ['#fff8e1', cmap_name])
        else:
            cmap = plt.get_cmap(cmap_name).copy()
        cmap.set_bad('#f4f1f8')
        im = ax.imshow(matrix.values, vmin=0, vmax=100, cmap=cmap)

        ax.set_xticks(np.arange(len(labels)))
        ax.set_yticks(np.arange(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='left', rotation_mode='anchor')
        ax.set_yticklabels(labels if show_ylabel else [])
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        ax.set_title(title, pad=18)

        for i in range(len(labels)):
            for j in range(len(labels)):
                rate = matrix.iat[i, j]
                n = totals.iat[i, j]
                if np.isfinite(rate):
                    ax.text(j, i, f'{rate:.0f}%', ha='center', va='center', fontsize=6.5, color='white' if rate > 55 else '#24142d')
                elif i == j:
                    ax.text(j, i, '-', ha='center', va='center', fontsize=7, color='#6f6078')
                elif na_if_empty and n == 0:
                    ax.text(j, i, 'N/A', ha='center', va='center', fontsize=6.5, color='#6f6078')

        ax.set_xticks(np.arange(-0.5, len(labels), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(labels), 1), minor=True)
        ax.grid(which='minor', color='white', linestyle='-', linewidth=1.0)
        ax.tick_params(which='minor', bottom=False, left=False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(cbar_label)


    def plot_pairwise_win_draw_matrices(matches, df, model_name_map, top_k=13, title='Chess Pairwise Outcomes', save_plot=True):
        names = df.head(top_k).index.tolist()
        win_rates, decisive_totals, draw_rates, all_totals = _pairwise_rate_matrices(matches, names)
        labels = [model_name_map(name) for name in names]

        fig, axes = plt.subplots(1, 2, figsize=(17.0, 7.8), dpi=150)
        _draw_pairwise_heatmap(
            axes[0],
            win_rates,
            decisive_totals,
            labels,
            'Wins',
            'Purples',
            'Win rate, excluding draws and timeouts (%)',
            na_if_empty=True,
            show_ylabel=True,
        )
        _draw_pairwise_heatmap(
            axes[1],
            draw_rates,
            all_totals,
            labels,
            'Draws',
            '#E69F00',
            'Draw rate (%)',
            na_if_empty=True,
            show_ylabel=True,
        )
        fig.suptitle(title, y=1.03, fontsize=14)
        fig.tight_layout()
        if save_plot:
            out_path = Path('figures/engine_chess_pairwise_win_draw_matrices.pdf')
            out_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(out_path, format='pdf', bbox_inches='tight')
        plt.show()
        return win_rates, decisive_totals, draw_rates, all_totals


    return plot_pairwise_win_draw_matrices(
        matches,
        df,
        model_name_map,
        top_k=top_k,
        title='Chess Engine Pairwise Outcomes',
        save_plot=save_plot,
    )
