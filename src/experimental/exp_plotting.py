#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Rectangle
from matplotlib.colors import TwoSlopeNorm, ListedColormap, BoundaryNorm
from matplotlib.lines import Line2D

from game_arena import utils as arena_utils


plt.style.use("seaborn-v0_8-whitegrid")


ROOT_DIR = arena_utils.get_root_path()
RANDOM_HIGHLIGHT_GOLD = "#f2b705"
_THINKING_LEVEL_SPECS: list[tuple[str, str, int, str]] = [
    ("_instant", "instant", 0, "Instant"),
    ("_low", "low", 1, "Low"),
    ("_medium", "medium", 2, "Medium"),
    ("_high", "high", 3, "High"),
    ("_thinking", "thinking", 4, "Thinking"),
    ("_xhigh", "xhigh", 5, "XHigh"),
]
_EXP_UTILS_MODULE = None


def _exp_utils_module():
    global _EXP_UTILS_MODULE
    if _EXP_UTILS_MODULE is None:
        from experimental import exp_utils as _exp_utils

        _EXP_UTILS_MODULE = _exp_utils
    return _EXP_UTILS_MODULE


def _main_games_world_columns():
    return _exp_utils_module().MAIN_GAMES_WORLD_COLUMNS


def model_name_map(model_name: str):
    return _exp_utils_module().model_name_map(model_name)


def get_logo(name: str, size: int = 96) -> np.ndarray:
    return _exp_utils_module().get_logo(name, size=size)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate lm_arena result pickle, or plot artifacts from an existing pickle.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("gen_pkl", help="Run ratings for configured games and save a pickle.")
    gen_parser.add_argument("--results-dir", type=str, required=True)
    gen_parser.add_argument("--num-bootstrap", type=int, default=100)
    gen_parser.add_argument("--rating-system", choices=["elo", "bt"], default="bt")
    gen_parser.add_argument("--exclude-tie", action="store_true", default=False)
    gen_parser.add_argument("--num-cpu", type=int, default=1, help="num_cpu passed to simple_example.main_results")
    gen_parser.add_argument("--seed", type=int, default=42)
    gen_parser.add_argument("--out-pkl", type=str, required=True)
    gen_parser.add_argument("--games", nargs="+", default=None, help="Optional game filter list, e.g. --games chess go")
    gen_parser.add_argument("--worlds", nargs="+", default=None, help="Optional world filter list, e.g. --worlds world1 worlduci1")
    gen_parser.add_argument(
        "--game-names",
        nargs="+",
        default=None,
        help="Explicit per-results game names to load, bypassing MAIN_GAMES_WORLD_COLUMNS. "
             "For Stanford tourneys, names like `albuquerque alquerque` map to "
             "`matches_stanford_gamemaster_w_<name>.json` and use `<name>` as the column label.",
    )
    gen_parser.add_argument("--match-file", type=str, default=None, help="Optional explicit match file path/name override.")
    gen_parser.add_argument("--stop-on-error", action="store_true", default=False, help="If set, raise on first game error. Default: continue and collect errors.")
    gen_parser.add_argument("--model-repr", choices=["top1", "top2mean"], default="top1", help="models mode: which automata represent an LLM. top1 = best bot; top2mean = mean rating of the two best bots (their games are pooled for win rates / done rates).")

    plot_parser = subparsers.add_parser("plot_pkl", help="Load a pickle produced by gen_pkl and generate plots/csv files.")
    plot_parser.add_argument("--in-pkl", type=str, required=True, help="Input pickle path.")
    plot_parser.add_argument("--out-dir", type=str, default=None, help="Output directory (default: pickle parent).")
    plot_parser.add_argument("--mode", choices=["models", "bots"], default="models", help="Which results set to plot from gen_pkl output.")
    plot_parser.add_argument(
        "--focus-on",
        nargs="+",
        default=None,
        help="Optional model focus list. Non-heatmap outputs are filtered to these models. "
             "Heatmaps keep all models, but cells where both models are unfocused are masked to NaN.",
    )
    plot_parser.add_argument(
        "--ignore",
        nargs="+",
        default=None,
        help="Optional model ignore list. Matching models are excluded from all plot/csv outputs, "
             "including heatmaps.",
    )

    thinking_plot_parser = subparsers.add_parser("thinking_plot", help="Plot median ELO against thinking level from a gen_pkl pickle.")
    thinking_plot_parser.add_argument("--in-pkl", type=str, required=True, help="Input pickle path from gen_pkl.")
    thinking_plot_parser.add_argument("--out-dir", type=str, default=None, help="Output directory (default: pickle parent).")

    quals_plot_parser = subparsers.add_parser(
        "quals-plot",
        help="For each game, pick each parent's best-ELO bot from results and plot its quals rank.",
    )
    quals_plot_parser.add_argument("--in-pkl", type=str, required=True, help="Input pickle path from gen_pkl.")
    quals_plot_parser.add_argument("--quals-dir", type=str, default="results_quals")
    quals_plot_parser.add_argument("--out-dir", type=str, default=None, help="Output directory (default: quals-dir).")
    quals_plot_parser.add_argument("--hide-yellow", action="store_true", default=False, help="Hide yellow warning markers in CI subplot figure.")

    return parser.parse_args()


def _candidate_match_files_for_game_name(results_path: Path, game_name: str) -> list[Path]:
    label = game_name.strip()
    if not label:
        return []
    label = label[2:] if label.startswith("w_") else label

    exact_candidates = [
        results_path / f"matches_stanford_gamemaster_w_{label}.json",
        results_path / f"matches_stanford_gamemaster_{label}.json",
    ]
    matches = [path for path in exact_candidates if path.exists()]
    if matches:
        return matches

    suffixes = (label, f"w_{label}")
    matches = []
    for path in sorted(results_path.glob("matches_*.json")):
        stem = path.stem
        if any(stem.endswith(f"_{suffix}") for suffix in suffixes):
            matches.append(path)
    return matches


def _load_match_identity(match_path: Path) -> tuple[str, str]:
    with match_path.open("r") as handle:
        match_json = json.load(handle)
    config = match_json.get("config", {})
    game = config.get("game_str")
    world = config.get("world")
    if not isinstance(game, str) or not game:
        raise ValueError(f"Match file is missing config.game_str: {match_path}")
    if not isinstance(world, str) or not world:
        raise ValueError(f"Match file is missing config.world: {match_path}")
    return game, world


def _resolve_named_run_specs(results_dir: str, game_names: list[str]) -> list[tuple[str, str, str, str]]:
    results_path = ROOT_DIR / results_dir
    if not results_path.exists():
        raise FileNotFoundError(f"Results directory not found: {results_path}")

    specs: list[tuple[str, str, str, str]] = []
    for raw_name in game_names:
        label = raw_name.strip()
        if not label:
            continue
        colname = label[2:] if label.startswith("w_") else label
        candidates = _candidate_match_files_for_game_name(results_path, label)
        if not candidates:
            raise FileNotFoundError(
                f"No match file found for game name {label!r} in {results_path}"
            )
        if len(candidates) > 1:
            raise FileExistsError(
                f"Multiple match files found for game name {label!r}: {candidates}"
            )
        match_path = candidates[0]
        game, world = _load_match_identity(match_path)
        specs.append((game, world, colname, str(match_path)))
    return specs


def run_gen_pkl(args: argparse.Namespace) -> Path:
    from experimental.lm_arena import simple_example

    if args.game_names and args.match_file:
        raise ValueError("--game-names cannot be combined with --match-file")

    games_filter = set(args.games) if args.games else None
    worlds_filter = set(args.worlds) if args.worlds else None
    match_file = getattr(args, "match_file", None)

    mode_to_only_model = {
        "models": True,
        "bots": False,
    }
    results_by_mode: dict[str, dict[str, dict[str, Any]]] = {mode: {} for mode in mode_to_only_model}
    errors_by_mode: dict[str, dict[str, str]] = {mode: {} for mode in mode_to_only_model}
    ran_specs: list[tuple[str, str, str]] = []

    if args.game_names:
        run_specs: list[tuple[str, str, str, Optional[str]]] = _resolve_named_run_specs(
            args.results_dir,
            list(args.game_names),
        )
    else:
        run_specs = []
        for game, world, colname, _ in _main_games_world_columns():
            if games_filter is not None and game not in games_filter:
                continue
            if worlds_filter is not None and world not in worlds_filter:
                continue
            run_specs.append((game, world, colname, match_file))

    for game, world, colname, spec_match_file in run_specs:
        is_any_success = False
        for mode, only_model in mode_to_only_model.items():
            print(f"Running {game} {world} {colname} mode={mode}")
            np.random.seed(args.seed)
            try:
                match_results_all, base_tstamp = simple_example.get_match_results(
                    game,
                    world,
                    spec_match_file,
                    args.results_dir,
                )
                result = simple_example.main_results(
                    match_results_all,
                    base_tstamp,
                    rating_system=args.rating_system,
                    num_bootstrap=args.num_bootstrap,
                    exclude_tie=args.exclude_tie,
                    num_cpu=args.num_cpu,
                    only_model=only_model,
                    model_repr=getattr(args, "model_repr", "top1"),
                )
                is_any_success = True
                results_by_mode[mode][colname] = result
            except Exception as exc:
                msg = f"{type(exc).__name__}: {exc}"
                errors_by_mode[mode][colname] = msg
                print(f"Error running {game} {world} {colname} mode={mode}: {msg}")
                if args.stop_on_error:
                    raise
        if is_any_success:
            ran_specs.append((game, world, colname))

    payload = {
        "config": {
            "results_dir": args.results_dir,
            "num_bootstrap": args.num_bootstrap,
            "rating_system": args.rating_system,
            "exclude_tie": args.exclude_tie,
            "num_cpu": args.num_cpu,
            "seed": args.seed,
            "modes": mode_to_only_model,
            "model_repr": getattr(args, "model_repr", "top1"),
            "games_filter": sorted(games_filter) if games_filter is not None else None,
            "worlds_filter": sorted(worlds_filter) if worlds_filter is not None else None,
            "game_names": list(args.game_names) if args.game_names is not None else None,
        },
        "runs": ran_specs,
        # Full outputs for both modes.
        "results_models": results_by_mode["models"],
        "errors_models": errors_by_mode["models"],
        "results_bots": results_by_mode["bots"],
        "errors_bots": errors_by_mode["bots"],
    }

    out_pkl = args.out_pkl.replace("{date}", datetime.now().strftime("%m%d_%H%M%S"))
    out_pkl = ROOT_DIR / out_pkl
    out_pkl.parent.mkdir(parents=True, exist_ok=True)
    with out_pkl.open("wb") as handle:
        pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print(
        f"Saved pickle to {out_pkl} "
        f"(runs={len(ran_specs)}, "
        f"models_success={len(results_by_mode['models'])}, "
        f"bots_success={len(results_by_mode['bots'])}, "
        f"models_errors={len(errors_by_mode['models'])}, "
        f"bots_errors={len(errors_by_mode['bots'])})"
    )
    return out_pkl

def fmt_err_timeout(xs, timeout_count):
    xs_missing = (xs is None or not xs)
    timeout_missing = (timeout_count is None or timeout_count == 0)
    if xs_missing and timeout_missing:
        return f""
    if timeout_missing:
        timeout_count = '0'
    if xs_missing:
        return f"(0/{timeout_count})"
    x = np.asarray(xs, dtype=float)
    n = int(x.size)
    mean = x.mean()
    std = x.std(ddof=1) if n >= 2 else 0.0
    return f"{mean:.2f} ± {std:.2f} ({n}/{timeout_count})"


def plot_median_elo(rating_df, rating_system, out_dir):
    plot_df = rating_df.copy()
    plot_df['Median ELO'] = plot_df.median(axis=1, skipna=True)
    plot_df = plot_df.sort_values(by='Median ELO', ascending=False)
    n_games = len(plot_df.columns) - 1
    print('n_games', n_games, '\n', plot_df.columns)
    elo_series = plot_df["Median ELO"].dropna()
    if elo_series.empty:
        print("Skipping median ELO plot: no finite values.")
        return

    lower_bound = 800.0
    bar_upper = max(2200.0, float(np.ceil((float(elo_series.max()) + 25.0) / 50.0) * 50.0))
    axis_upper = bar_upper + 240.0
    x_step = 0.48
    x_positions = np.arange(len(elo_series), dtype=float) * x_step

    fig_width = max(8.8, 0.34 * len(elo_series) + 1.8)
    fig, ax = plt.subplots(figsize=(fig_width, 6.2))
    text_nudge_transform = mtransforms.offset_copy(ax.transData, fig=fig, x=0.0, y=4.0, units="dots")
    logo_nudge_transform = mtransforms.offset_copy(ax.transData, fig=fig, x=0.0, y=10.0, units="dots")

    bar_color = "#6c4ca8"
    random_color = RANDOM_HIGHLIGHT_GOLD
    value_color = "#2f2149"
    bar_lw = 15

    label_positions: list[tuple[float, float, str, float]] = []
    for x, (name, elo) in zip(x_positions, elo_series.items()):
        color = random_color if str(name) == "random" else bar_color
        bar = ax.vlines(x, lower_bound, float(elo), color=color, linewidth=bar_lw, zorder=3)
        bar.set_capstyle("round")
        label_y = min(float(elo) + 42.0, axis_upper - 96.0)
        ax.text(
            x,
            label_y,
            f"{float(elo):.0f}",
            transform=text_nudge_transform,
            va="bottom",
            ha="center",
            fontsize=9,
            color=value_color,
            fontweight="semibold",
        )
        label_positions.append((x, float(elo), str(name), label_y))

    ax.set_xticks(x_positions)
    ax.set_xticklabels([model_name_map(str(name)) for name in elo_series.index.astype(str)], rotation=45, ha="right", fontsize=10.5)
    ax.tick_params(axis="x", length=0, pad=12)
    ax.set_xlim(-0.28, (len(x_positions) - 1) * x_step + 0.20)
    ax.set_ylim(lower_bound - 28.0, axis_upper)
    ax.set_xlabel("")
    ax.set_ylabel("Median ELO")
    ax.set_title(f"Median ELO across {n_games} games", pad=10)
    ax.grid(axis="y", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    logo_zoom = 0.142
    for x, elo, name, label_y in label_positions:
        if name == "random":
            continue
        try:
            arr = get_logo(name)
            logo_y = min(label_y + 84.0, axis_upper - 40.0)
            ax.add_artist(
                AnnotationBbox(
                    OffsetImage(arr, zoom=logo_zoom),
                    (x, logo_y),
                    xycoords=logo_nudge_transform,
                    frameon=False,
                    box_alignment=(0.5, 0.5),
                    pad=0.0,
                    zorder=5,
                    clip_on=False,
                )
            )
        except Exception as exc:
            print(f"Warning: logo fetch failed for {name}: {type(exc).__name__}: {exc}")

    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.24)
    fig.savefig(out_dir / 'median_elo.pdf', bbox_inches="tight")
    plt.close(fig)


def plot_bot_elo_scatter(
    rating_df: pd.DataFrame,
    out_dir: Path,
    *,
    results: dict[str, dict[str, Any]],
    focus_models: Optional[set[str]] = None,
) -> None:
    if rating_df.empty:
        print("Skipping bot ELO scatter: empty ratings dataframe.")
        return
    bot_median_elo = rating_df.median(axis=1, skipna=True)
    plot_df = pd.DataFrame(
        {
            "bot": rating_df.index.astype(str),
            "elo": pd.to_numeric(bot_median_elo, errors="coerce"),
        }
    ).dropna(subset=["elo"])
    if plot_df.empty:
        print("Skipping bot ELO scatter: all bot ELO values are NaN.")
        return

    plot_df["model"] = plot_df["bot"].map(lambda name: name.split("/")[0] if "/" in name else name)
    if focus_models:
        plot_df = plot_df[plot_df["model"].isin(focus_models)].copy()
        if plot_df.empty:
            print("Skipping bot ELO scatter: no focused models present.")
            return
    done_rates = _aggregate_bot_done_rates(results)
    if done_rates is None:
        print("Skipping bot ELO scatter: input pickle is missing stored done-rate stats. Regenerate with `gen_pkl` to enable this plot.")
        return
    plot_df["done_rate"] = plot_df["bot"].map(done_rates)
    plot_df["color"] = "C0"
    plot_df.loc[plot_df["done_rate"].fillna(1.0).eq(0.0), "color"] = "#d62728"

    model_order = (
        plot_df.groupby("model", sort=False)["elo"]
        .max()
        .sort_values(ascending=False)
        .index.tolist()
    )
    x_step = 0.84
    x_centers = np.arange(len(model_order), dtype=float) * x_step
    x_pos = {model: x_centers[idx] for idx, model in enumerate(model_order)}
    rng = np.random.default_rng(42)
    jitter = rng.uniform(-0.14, 0.14, size=len(plot_df))
    xs = np.array([x_pos[model] for model in plot_df["model"]], dtype=float) + jitter

    fig_w = max(6.2, 0.48 * len(model_order) + 1.2)
    fig, ax = plt.subplots(figsize=(fig_w, 5.2))
    ax.scatter(xs, plot_df["elo"], s=22, alpha=0.72, c=plot_df["color"], edgecolors="none")

    ax.set_xticks(x_centers)
    ax.set_xticklabels([model_name_map(model) for model in model_order], rotation=45, ha="right")
    ax.margins(x=0.0)
    ax.set_xlim(x_centers[0] - 0.20, x_centers[-1] + 0.20)
    ax.set_xlabel("Model")
    ax.set_ylabel("ELO")
    ax.set_title("ELO Scatter by Model")
    ax.grid(axis="x", alpha=0.18, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    legend_handles = [
        Line2D([0], [0], marker="o", linestyle="", markersize=6, markerfacecolor="#d62728", markeredgecolor="none", label="no completed game"),
    ]
    ax.legend(handles=legend_handles, loc="best", frameon=False)
    plt.tight_layout()
    fig.savefig(out_dir / "bot_elo_scatter.pdf")
    fig.savefig(out_dir / "bot_elo_scatter.png", dpi=200)
    plt.close(fig)

    completed_df = plot_df[plot_df["done_rate"].fillna(0.0) > 0.0].copy()
    std_by_model = completed_df.groupby("model")["elo"].agg(
        lambda s: float(np.std(s.to_numpy(dtype=float), ddof=0)) if len(s) > 1 else np.nan
    )
    valid_models = [model for model in model_order if np.isfinite(std_by_model.get(model, np.nan))]
    std_heights = [float(std_by_model[model]) for model in valid_models]

    fig_std, ax_std = plt.subplots(figsize=(fig_w, 4.8))
    if valid_models:
        ax_std.bar(
            [x_pos[model] for model in valid_models],
            std_heights,
            width=0.52,
            color="#4c78a8",
            edgecolor="black",
            linewidth=0.5,
        )
    ax_std.set_xticks(x_centers)
    ax_std.set_xticklabels([model_name_map(model) for model in model_order], rotation=45, ha="right")
    ax_std.set_xlabel("Model")
    ax_std.set_ylabel("ELO Std")
    ax_std.set_title("ELO Std by Model (done_rate > 0)")
    ax_std.grid(axis="y", alpha=0.2, linewidth=0.8)
    ax_std.set_axisbelow(True)
    ax_std.spines["top"].set_visible(False)
    ax_std.spines["right"].set_visible(False)
    plt.tight_layout()
    fig_std.savefig(out_dir / "elo_std_by_model_completed.pdf")
    fig_std.savefig(out_dir / "elo_std_by_model_completed.png", dpi=200)
    plt.close(fig_std)


def _ordered_models_by_mean_rank(rank_df: pd.DataFrame, base_models: list[str]) -> list[str]:
    mean_rank = rank_df.mean(axis=1, skipna=True)
    base = [m for m in base_models if m in rank_df.index]
    base_pos = {m: i for i, m in enumerate(base)}
    return sorted(
        base,
        key=lambda m: (
            float(mean_rank.get(m)) if np.isfinite(mean_rank.get(m, np.nan)) else float("inf"),
            base_pos.get(m, 10**9),
        ),
    )


def plot_ranking_scatter(
    rankings_df,
    model_order_by_median_elo,
    out_dir,
    *,
    sort_by_mean_rank: bool = False,
    filename: str = "per_game_rank_scatter.pdf",
):
    # 2) Coerce values to numeric (safe if you have strings / missing values)
    rank_df = rankings_df.apply(pd.to_numeric, errors="coerce")
    # 3) mean ranks + ordering (lower mean = better)
    med = rank_df.mean(axis=1, skipna=True)
    models = (
        _ordered_models_by_mean_rank(rank_df, model_order_by_median_elo)
        if sort_by_mean_rank
        else [m for m in model_order_by_median_elo if m in rank_df.index]
    )
    # 4) Plot: scatter (strip) with jitter + mean trend line + legend
    x = np.arange(len(models))

    jitter = 0.18
    alpha = 0.75
    size = 18

    plt.figure(figsize=(max(10, 0.5 * len(models)), 6))
    ax = plt.gca()

    ax.grid(axis="y", which="major", linestyle="-", linewidth=0.6, alpha=0.25)
    ax.grid(axis="x", visible=False)

    cmap = plt.get_cmap("Dark2")
    colors = [cmap(i % cmap.N) for i in range(len(models))]

    for i, m in enumerate(models):
        # row = all game ranks for model m
        y = rank_df.loc[m].dropna().to_numpy(dtype=float)
        xj = i + np.random.uniform(-jitter, jitter, size=len(y))
        ax.scatter(
            xj, y,
            s=size,
            alpha=alpha,
            color=colors[i],
            edgecolors="black",
            linewidths=0.3,
            zorder=2,
        )

    mean_y = med.loc[models].to_numpy(dtype=float)
    mean_line, = ax.plot(x, mean_y, linestyle="-", linewidth=2.0, color="red", zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels([model_name_map(m) for m in models], rotation=45, ha="right")

    # Logos (unchanged; uses your get_logo + model_name_map)
    logo_zoom = 0.18
    x_offset = -10  # px left of label
    y_offset = 0

    for i, m in enumerate(models):
        if m == "random":
            continue
        arr = get_logo(m)  # uint8 HxWx3
        ax.add_artist(AnnotationBbox(
            OffsetImage(arr, zoom=logo_zoom),
            (i+0.5, 0.01),
            xycoords=("data", "axes fraction"),
            xybox=(x_offset, y_offset),
            boxcoords="offset points",
            frameon=False,
            box_alignment=(1.0, 0.0),
            pad=0.0,
            zorder=4,
            clip_on=False,
        ))

    plt.subplots_adjust(bottom=0.30)

    ax.set_xlabel("Model (sorted by mean rank)")
    ax.set_ylabel("Rank for each game (1 = best)")
    ax.set_title("Per-game Rank by Model")

    ymin, ymax = ax.get_ylim()
    pad = 1.8
    ax.set_ylim(ymin, ymax + pad)

    ax.invert_yaxis()

    text_blend = 0.45
    grey = np.array([0.25, 0.25, 0.25, 1.0])
    for tick, c in zip(ax.get_xticklabels(), colors):
        rgba = np.array(c)
        muted = (1 - text_blend) * rgba + text_blend * grey
        tick.set_color(tuple(muted))
        tick.set_fontweight("semibold")

    ax.legend([mean_line], ["Mean rank"], frameon=False, loc="upper right")

    plt.tight_layout()
    plt.savefig(out_dir / filename)
    plt.close()


def plot_mean_rank_bar(rankings_df, model_order_by_median_elo, out_dir):
    rank_df = rankings_df.apply(pd.to_numeric, errors="coerce")
    mean_rank = rank_df.mean(axis=1, skipna=True).rename("Mean Rank")
    base_models = [m for m in model_order_by_median_elo if m in mean_rank.index]
    order = _ordered_models_by_mean_rank(rank_df, base_models)
    plot_df = mean_rank.reindex(order).dropna()
    if plot_df.empty:
        print("Skipping mean-rank bar plot: no finite rank values.")
        return

    max_rank = float(np.nanmax(plot_df.to_numpy(dtype=float)))
    rank_upper = max(1, int(np.ceil(max_rank)))
    inv_df = (rank_upper + 1 - plot_df).rename("Mean Rank (Inverted)")

    lower_bound = 0.0
    axis_upper = float(np.ceil((float(inv_df.max()) + 0.5) * 2.0) / 2.0) + 3.5
    axis_lower = lower_bound - 0.25
    axis_span = axis_upper - axis_lower
    # Match the median-ELO plot's label/logo stack using the same relative
    # vertical geometry rather than separate hand-tuned rank-specific offsets.
    label_gap = axis_span * (42.0 / 1668.0)
    label_top_margin = axis_span * (96.0 / 1668.0)
    logo_gap = axis_span * (84.0 / 1668.0)
    logo_top_margin = axis_span * (40.0 / 1668.0)
    x_step = 0.48
    x_positions = np.arange(len(inv_df), dtype=float) * x_step

    fig_width = max(8.8, 0.34 * len(inv_df) + 1.8)
    fig, ax = plt.subplots(figsize=(fig_width, 6.2))
    text_nudge_transform = mtransforms.offset_copy(ax.transData, fig=fig, x=0.0, y=4.0, units="dots")
    logo_nudge_transform = mtransforms.offset_copy(ax.transData, fig=fig, x=0.0, y=10.0, units="dots")

    bar_color = "#4f7f95"
    random_color = RANDOM_HIGHLIGHT_GOLD
    value_color = "#2f2149"
    bar_lw = 15

    label_positions: list[tuple[float, str, float]] = []
    for x, (name, inv_rank) in zip(x_positions, inv_df.items()):
        color = random_color if str(name) == "random" else bar_color
        bar = ax.vlines(x, lower_bound, float(inv_rank), color=color, linewidth=bar_lw, zorder=3)
        bar.set_capstyle("round")
        label_y = min(float(inv_rank) + label_gap, axis_upper - label_top_margin)
        actual_rank = float(plot_df.loc[name])
        label_text = f"{actual_rank:.1f}".rstrip("0").rstrip(".")
        ax.text(
            x,
            label_y,
            label_text,
            transform=text_nudge_transform,
            va="bottom",
            ha="center",
            fontsize=9,
            color=value_color,
            fontweight="semibold",
        )
        label_positions.append((x, str(name), label_y))

    ax.set_xticks(x_positions)
    ax.set_xticklabels([model_name_map(str(name)) for name in inv_df.index.astype(str)], rotation=45, ha="right", fontsize=10.5)
    ax.tick_params(axis="x", length=0, pad=12)
    ax.set_xlim(-0.20, (len(x_positions) - 1) * x_step + 0.20)
    ax.set_ylim(axis_lower, axis_upper)
    ax.set_xlabel("")
    ax.set_ylabel("Mean Rank (1 is the best)")
    ax.set_title("Mean Rank across Games", pad=10)
    ax.grid(axis="y", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    max_ticks = 10
    step = max(1, int(np.ceil(rank_upper / max_ticks)))
    ranks_to_show = list(range(1, rank_upper + 1, step))
    if ranks_to_show[-1] != rank_upper:
        if (rank_upper - ranks_to_show[-1]) <= max(1, step // 2):
            ranks_to_show[-1] = rank_upper
        else:
            ranks_to_show.append(rank_upper)
    tick_pos = np.array([rank_upper + 1 - r for r in ranks_to_show], dtype=float)
    tick_labels = [str(r) for r in ranks_to_show]
    tick_order = np.argsort(tick_pos)
    ax.set_yticks(tick_pos[tick_order])
    ax.set_yticklabels([tick_labels[i] for i in tick_order])

    logo_zoom = 0.142
    for x, name, label_y in label_positions:
        if name == "random":
            continue
        try:
            arr = get_logo(name)
            logo_y = min(label_y + logo_gap, axis_upper - logo_top_margin)
            ax.add_artist(
                AnnotationBbox(
                    OffsetImage(arr, zoom=logo_zoom),
                    (x, logo_y),
                    xycoords=logo_nudge_transform,
                    frameon=False,
                    box_alignment=(0.5, 0.5),
                    pad=0.0,
                    zorder=5,
                    clip_on=False,
                )
            )
        except Exception as exc:
            print(f"Warning: logo fetch failed for {name}: {type(exc).__name__}: {exc}")

    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.24)
    fig.savefig(out_dir / "mean_rank_bar.pdf", bbox_inches="tight")
    plt.close(fig)


def get_row_beats(results):
    def my_heatmap(battles, models):
        total_ab = pd.pivot_table(
            battles, index="model_a", columns="model_b", aggfunc="size", fill_value=0
        ).reindex(index=models, columns=models, fill_value=0)
        total = total_ab + total_ab.T

        wins_as_a = pd.pivot_table(
            battles[battles["winner"] == "model_a"],
            index="model_a", columns="model_b", aggfunc="size", fill_value=0
        ).reindex(index=models, columns=models, fill_value=0)

        wins_as_b = pd.pivot_table(
            battles[battles["winner"] == "model_b"],
            index="model_b", columns="model_a", aggfunc="size", fill_value=0
        ).reindex(index=models, columns=models, fill_value=0)

        ties_ab = pd.pivot_table(
            battles[battles["winner"] == "tie"],
            index="model_a", columns="model_b", aggfunc="size", fill_value=0
        ).reindex(index=models, columns=models, fill_value=0)

        win_counts = wins_as_a + wins_as_b + 0.5 * (ties_ab + ties_ab.T)
        A = win_counts.div(total).where(total != 0)
        return A
    row_beats: dict[str, pd.DataFrame] = {}
    for col in results.keys():
        battles = results[col]["battles"]
        all_models = set(battles["model_a"]) | set(battles["model_b"])
        row_beats[col] = my_heatmap(battles, all_models)
    return row_beats


def _heatmap_vis_params(n_items: int, scale: float) -> tuple[float, float, int, bool, float]:
    n = max(1, int(n_items))
    # Give each row/column more physical space, especially for all-bots matrices.
    cell_in = 0.12 * float(scale)
    fig_size = max(10.0, min(160.0, n * cell_in))
    # Always show every row/column label.
    tick_step = 1
    tick_fontsize = max(0.75, min(7.0, (205.0 / n) * (float(scale) / 1.9)))
    annotate_cells = n <= 200
    # Keep annotations present but compact for dense bot-vs-bot matrices.
    annotate_fontsize = max(1.1, min(4.5, (255.0 / max(1, n)) * (float(scale) / 1.9)))
    return fig_size, tick_fontsize, tick_step, annotate_cells, annotate_fontsize


def _average_row_beats_matrices(
    row_beats: dict[str, pd.DataFrame],
    model_order: list[str],
) -> pd.DataFrame:
    if not row_beats:
        return pd.DataFrame(index=model_order, columns=model_order, dtype=float)
    matrices = [
        df.reindex(index=model_order, columns=model_order).to_numpy(dtype=float)
        for df in row_beats.values()
    ]
    stacked = np.stack(matrices, axis=0)
    finite_mask = np.isfinite(stacked)
    counts = finite_mask.sum(axis=0)
    summed = np.nansum(stacked, axis=0)
    averaged = np.divide(
        summed,
        counts,
        out=np.full_like(summed, np.nan, dtype=float),
        where=counts > 0,
    )
    return pd.DataFrame(averaged, index=model_order, columns=model_order)


def _format_combined_heatmap_fraction(value: float) -> str:
    if not np.isfinite(value):
        return ""
    if value >= (1.0 - 1e-12):
        return "1.0"
    clipped = min(max(float(value), 0.0), np.nextafter(1.0, 0.0))
    tenths = int(np.floor(clipped * 10.0 + 1e-12))
    return f".{tenths}"


def _resolve_model_tokens(
    tokens: Optional[list[str]],
    available_models: list[str],
    *,
    flag_name: str,
) -> set[str]:
    if not tokens:
        return set()
    searchable: list[tuple[str, str, str]] = []
    for raw in available_models:
        raw_str = str(raw)
        searchable.append((raw_str, raw_str.lower(), str(model_name_map(raw_str)).lower()))
    resolved: set[str] = set()
    unresolved: list[str] = []
    for token in tokens:
        token_l = str(token).strip().lower()
        if not token_l:
            continue
        matches = [
            raw
            for raw, raw_l, label_l in searchable
            if (token_l in raw_l) or (token_l in label_l)
        ]
        if matches:
            resolved.update(matches)
            continue
        unresolved.append(token)
    if unresolved:
        print(f"Warning: unresolved {flag_name} entries: {unresolved}")
    return resolved


def _mask_unfocused_pairs(df: pd.DataFrame, focus_models: Optional[set[str]]) -> pd.DataFrame:
    if not focus_models:
        return df
    row_focus = np.asarray(df.index.isin(focus_models), dtype=bool)
    col_focus = np.asarray(df.columns.isin(focus_models), dtype=bool)
    keep_mask = np.logical_or(row_focus[:, None], col_focus[None, :])
    return df.where(keep_mask)


def _keep_only_focused_rows(df: pd.DataFrame, focus_models: Optional[set[str]]) -> pd.DataFrame:
    if not focus_models:
        return df
    focused_rows = [name for name in df.index if name in focus_models]
    return df.loc[focused_rows, :]


def _style_focused_columns(
    ax,
    *,
    raw_col_names: list[str],
    x_ticks: list[int],
    n_rows: int,
    focus_models: Optional[set[str]],
) -> None:
    if not focus_models:
        return
    # Outline focused columns across the full heatmap height.
    for j, raw_name in enumerate(raw_col_names):
        if raw_name not in focus_models:
            continue
        ax.add_patch(
            Rectangle(
                (j - 0.5, -0.5),
                1.0,
                float(n_rows),
                fill=False,
                edgecolor="limegreen",
                linewidth=1.1,
                zorder=6,
            )
        )
    # Emphasize focused x-axis labels.
    tick_labels = ax.get_xticklabels()
    for tick_i, label in zip(x_ticks, tick_labels):
        if 0 <= tick_i < len(raw_col_names) and raw_col_names[tick_i] in focus_models:
            label.set_fontweight("bold")
            label.set_color("#111111")


def _order_names_for_game_heatmap(
    *,
    col: str,
    base_df: pd.DataFrame,
    results: dict[str, Any],
    default_order: list[str],
    use_per_game_elo_order: bool,
) -> list[str]:
    names = list(dict.fromkeys(list(base_df.index) + list(base_df.columns)))
    default_ranked = [n for n in default_order if n in names]
    default_ranked.extend([n for n in names if n not in default_ranked])
    if not use_per_game_elo_order:
        return default_ranked

    result = results.get(col, {})
    if not isinstance(result, dict):
        return default_ranked
    leaderboard_df = result.get("leaderboard_table_df")
    if not isinstance(leaderboard_df, pd.DataFrame) or "rating" not in leaderboard_df.columns:
        return default_ranked

    rating_series = pd.to_numeric(leaderboard_df["rating"], errors="coerce").dropna().sort_values(ascending=False)
    game_ranked = [n for n in rating_series.index.tolist() if n in names]
    game_ranked.extend([n for n in default_ranked if n not in game_ranked])
    return game_ranked


def _build_per_game_stats_csv_df(game_result: dict[str, Any]) -> pd.DataFrame:
    battles = game_result.get("battles")
    if isinstance(battles, pd.DataFrame):
        battles_df = battles.copy()
    elif isinstance(battles, list):
        battles_df = pd.DataFrame(battles)
    else:
        battles_df = pd.DataFrame()

    required_cols = {"model_a", "model_b", "winner"}
    if battles_df.empty or not required_cols.issubset(set(battles_df.columns)):
        return pd.DataFrame(
            columns=[
                "ELO",
                "win",
                "loss",
                "draw",
                "error",
                "timeout",
                "done",
                "Total",
                "Timeout_Percent",
                "Done_Percent",
                "No_Blame_Score",
            ]
        )

    all_models = sorted(set(battles_df["model_a"]).union(set(battles_df["model_b"])))
    counts_df = pd.DataFrame(0, index=all_models, columns=["win", "loss", "draw"], dtype=int)

    winner_a = battles_df["winner"] == "model_a"
    winner_b = battles_df["winner"] == "model_b"
    winner_tie = battles_df["winner"] == "tie"

    wins_a = battles_df.loc[winner_a, "model_a"].value_counts()
    losses_b = battles_df.loc[winner_a, "model_b"].value_counts()
    wins_b = battles_df.loc[winner_b, "model_b"].value_counts()
    losses_a = battles_df.loc[winner_b, "model_a"].value_counts()
    ties_a = battles_df.loc[winner_tie, "model_a"].value_counts()
    ties_b = battles_df.loc[winner_tie, "model_b"].value_counts()

    counts_df.loc[wins_a.index, "win"] += wins_a.to_numpy()
    counts_df.loc[wins_b.index, "win"] += wins_b.to_numpy()
    counts_df.loc[losses_a.index, "loss"] += losses_a.to_numpy()
    counts_df.loc[losses_b.index, "loss"] += losses_b.to_numpy()
    counts_df.loc[ties_a.index, "draw"] += ties_a.to_numpy()
    counts_df.loc[ties_b.index, "draw"] += ties_b.to_numpy()

    err_counts_s = pd.Series(dtype=float)
    timeout_counts_s = pd.Series(dtype=float)
    error_turn_count = game_result.get("error_turn_count")
    if isinstance(error_turn_count, tuple) and len(error_turn_count) == 2:
        err_turns_d, timeout_d = error_turn_count
        if isinstance(err_turns_d, dict):
            err_counts_s = pd.Series({k: len(v) for k, v in err_turns_d.items()}, dtype=float)
        if isinstance(timeout_d, dict):
            timeout_counts_s = pd.Series(timeout_d, dtype=float)

    out_df = counts_df.copy()
    out_df["error"] = err_counts_s.reindex(out_df.index).fillna(0).astype(int)
    out_df["timeout"] = timeout_counts_s.reindex(out_df.index).fillna(0).astype(int)
    out_df["loss"] = (out_df["loss"] - out_df["error"] - out_df["timeout"]).clip(lower=0).astype(int)

    done_counts_s = pd.Series(dtype=float)
    done_rate_stats = game_result.get("done_rate_stats")
    if isinstance(done_rate_stats, dict):
        done_counts_s = pd.Series(
            {
                str(bot_name): float(bot_stats.get("done", 0.0) or 0.0)
                for bot_name, bot_stats in done_rate_stats.items()
                if isinstance(bot_stats, dict)
            },
            dtype=float,
        )

    out_df["done"] = done_counts_s.reindex(out_df.index).fillna(0).astype(int)
    out_df["Total"] = out_df[["win", "loss", "draw", "error", "timeout"]].sum(axis=1)
    timeout_pct = np.where(out_df["Total"] > 0, (out_df["timeout"] / out_df["Total"]) * 100, 0.0)
    out_df["Timeout_Percent"] = [f"{x:.1f}%" for x in timeout_pct]
    done_pct = np.where(out_df["Total"] > 0, (out_df["done"] / out_df["Total"]) * 100, 0.0)
    out_df["Done_Percent"] = [f"{x:.1f}%" for x in done_pct]
    no_blame_denom = out_df["done"] + out_df["error"]
    no_blame_score = np.where(no_blame_denom > 0, out_df["done"] / no_blame_denom, 1.0)
    out_df["No_Blame_Score"] = np.round(no_blame_score, 3)

    leaderboard_df = game_result.get("leaderboard_table_df")
    if isinstance(leaderboard_df, pd.DataFrame) and "rating" in leaderboard_df.columns:
        elo_s = pd.to_numeric(leaderboard_df["rating"], errors="coerce").round().astype("Int64").rename("ELO")
    else:
        elo_s = pd.Series(dtype="Int64", name="ELO")

    out_df = pd.concat([elo_s, out_df], axis=1)
    if "ELO" in out_df.columns:
        out_df = out_df.sort_values("ELO", ascending=False, na_position="last")
    return out_df


def _aggregate_bot_done_rates(results: dict[str, dict[str, Any]]) -> Optional[pd.Series]:
    total_counts: dict[str, float] = {}
    done_counts: dict[str, float] = {}
    for colname, game_result in results.items():
        done_rate_stats = game_result.get("done_rate_stats")
        if not isinstance(done_rate_stats, dict):
            return None
        for bot_name, bot_stats in done_rate_stats.items():
            if not isinstance(bot_stats, dict):
                continue
            total = float(bot_stats.get("total", 0.0) or 0.0)
            done = float(bot_stats.get("done", 0.0) or 0.0)
            total_counts[str(bot_name)] = total_counts.get(str(bot_name), 0.0) + total
            done_counts[str(bot_name)] = done_counts.get(str(bot_name), 0.0) + done

    if not total_counts:
        return pd.Series(dtype=float)
    return pd.Series(
        {
            bot_name: (done_counts.get(bot_name, 0.0) / total)
            for bot_name, total in total_counts.items()
            if total > 0
        },
        dtype=float,
    )


def plot_heatmap_combined(
    results,
    model_order_by_median_elo,
    out_dir,
    scale = 1.9,
    focus_models: Optional[set[str]] = None,
    return_plot: bool = False,
    cell_fontsize: Optional[float] = None,
):
    row_beats = get_row_beats(results)
    row_beats_col = _average_row_beats_matrices(row_beats, model_order_by_median_elo)
    row_beats_col = row_beats_col.reindex(model_order_by_median_elo, columns=model_order_by_median_elo)
    row_beats_col = _mask_unfocused_pairs(row_beats_col, focus_models)
    row_beats_col = _keep_only_focused_rows(row_beats_col, focus_models)
    if row_beats_col.shape[0] == 0 or row_beats_col.shape[1] == 0:
        print("Skipping combined heatmap: no rows/columns to plot after focus filter.")
        return
    raw_col_names = list(row_beats_col.columns)
    row_beats_col = row_beats_col.rename(index=model_name_map, columns=model_name_map)

    data = row_beats_col.to_numpy(dtype=float).copy()
    np.fill_diagonal(data, np.nan)
    n_items = len(row_beats_col.index)
    fig_size, tick_fontsize, tick_step, annotate_cells, annotate_fontsize = _heatmap_vis_params(n_items, scale)
    fig_size = max(6.0, min(18.0, fig_size * 0.55))
    tick_fontsize = max(0.7, tick_fontsize * 0.9)
    annotate_fontsize = max(1.0, annotate_fontsize * 0.9)
    if cell_fontsize is not None:
        annotate_fontsize = cell_fontsize

    dpi = 100
    fig, ax = plt.subplots(figsize=(fig_size, fig_size), dpi=dpi, constrained_layout=True)

    norm = TwoSlopeNorm(vmin=0, vcenter=0.5, vmax=1.0)

    cmap = plt.get_cmap("RdBu").copy()
    cmap.set_bad(alpha=0.0)

    im = ax.imshow(data, cmap=cmap, norm=norm, interpolation="nearest", aspect="equal")
    ax.grid(False)

    if annotate_cells:
        nrows, ncols = data.shape
        for i in range(nrows):
            for j in range(ncols):
                v = data[i, j]
                if np.isfinite(v):
                    ax.text(
                        j,
                        i,
                        _format_combined_heatmap_fraction(v),
                        ha="center",
                        va="center",
                        fontsize=annotate_fontsize,
                    )

    ax.set_xlabel("Model B")
    ax.set_ylabel("Model A")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    x_labels = list(row_beats_col.columns)
    y_labels = list(row_beats_col.index)
    x_ticks = list(range(0, len(x_labels), tick_step))
    y_ticks = list(range(0, len(y_labels), tick_step))
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.set_xticklabels([x_labels[i] for i in x_ticks], rotation=45, ha="left", rotation_mode="anchor", fontsize=tick_fontsize)
    ax.set_yticklabels([y_labels[i] for i in y_ticks], fontsize=tick_fontsize)
    _style_focused_columns(
        ax,
        raw_col_names=raw_col_names,
        x_ticks=x_ticks,
        n_rows=len(y_labels),
        focus_models=focus_models,
    )

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Fraction of A Wins")

    fig.savefig(out_dir / "model_matchups_heatmap.pdf", bbox_inches="tight")
    plt.close()
    if return_plot:
        return fig


def plot_heatmap_subplots(
    results,
    model_order_by_median_elo,
    out_dir,
    scale = 1.9,
    ncols = 3,
    use_per_game_elo_order: bool = False,
    focus_models: Optional[set[str]] = None,
):
    dpi = 100

    def _cell_text(Z):
        text = np.full(Z.shape, "", dtype=object)
        m0 = np.isfinite(Z) & (Z == 0)
        m1 = np.isfinite(Z) & (Z == 1)
        m = np.isfinite(Z) & ~(m0 | m1)
        text[m0] = "0"
        text[m1] = "1"
        text[m] = np.char.lstrip(np.char.mod("%.1f", Z[m]), "0")  # "0.3" -> ".3"
        return text

    # ncols is kept for backward compatibility; plots are now emitted individually.
    _ = ncols
    keys = list(results.keys())
    row_beats = get_row_beats(results)
    heatmaps_dir = Path(out_dir) / "heatmaps"
    heatmaps_dir.mkdir(parents=True, exist_ok=True)

    norm = TwoSlopeNorm(vmin=0, vcenter=0.5, vmax=1)
    cmap = plt.get_cmap("RdBu").copy()
    cmap.set_bad(alpha=0.0)

    for col in keys:
        print(f"doing {col}")
        base_df = row_beats[col]
        stats_csv_df = _build_per_game_stats_csv_df(results[col])
        safe_col = "".join(ch if (ch.isalnum() or ch in "-_.") else "_" for ch in str(col))
        stats_csv_df.to_csv(heatmaps_dir / f"model_stats_{safe_col}.csv")
        ordered_names = _order_names_for_game_heatmap(
            col=col,
            base_df=base_df,
            results=results,
            default_order=model_order_by_median_elo,
            use_per_game_elo_order=use_per_game_elo_order,
        )
        df = (
            base_df
            .reindex(ordered_names, columns=ordered_names)
        )
        df = _mask_unfocused_pairs(df, focus_models)
        df = _keep_only_focused_rows(df, focus_models)
        if df.shape[0] == 0 or df.shape[1] == 0:
            print(f"Skipping heatmap for {col}: no rows/columns to plot after focus filter.")
            continue
        # Keep prior cleanup behavior only when no focus masking is requested.
        if not focus_models:
            df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
            keep = df.index.intersection(df.columns)
            if len(keep) > 0:
                df = df.loc[keep, keep]
        raw_col_names = list(df.columns)
        df = df.rename(index=model_name_map, columns=model_name_map)
        n_items = len(df.index)
        fig_size, tick_fontsize, tick_step, annotate_cells, annotate_fontsize = _heatmap_vis_params(n_items, scale)
        fig, ax = plt.subplots(1, 1, figsize=(fig_size, fig_size), dpi=dpi, constrained_layout=True)
        data = df.to_numpy(dtype=float).copy()
        np.fill_diagonal(data, np.nan)
        im = ax.imshow(data, cmap=cmap, norm=norm, interpolation="nearest", aspect="equal")

        if annotate_cells:
            text = _cell_text(data)
            nrows, ncols_data = data.shape
            for i in range(nrows):
                for j in range(ncols_data):
                    s = text[i, j]
                    if s != "":
                        ax.text(j, i, s, ha="center", va="center", fontsize=annotate_fontsize)

        ax.set_xlabel("Model B")
        ax.set_ylabel("Model A")
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        x_labels = list(df.columns)
        y_labels = list(df.index)
        x_ticks = list(range(0, len(x_labels), tick_step))
        y_ticks = list(range(0, len(y_labels), tick_step))
        ax.set_xticks(x_ticks)
        ax.set_yticks(y_ticks)
        ax.set_xticklabels([x_labels[i] for i in x_ticks], rotation=45, ha="left", rotation_mode="anchor", fontsize=tick_fontsize)
        ax.set_yticklabels([y_labels[i] for i in y_ticks], fontsize=tick_fontsize)
        _style_focused_columns(
            ax,
            raw_col_names=raw_col_names,
            x_ticks=x_ticks,
            n_rows=len(y_labels),
            focus_models=focus_models,
        )
        ax.grid(False)
        ax.set_title(f"Battle Heatmap for {col.upper()}", pad=20)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Fraction of A Wins")

        fig.savefig(heatmaps_dir / f"model_matchups_heatmap_{safe_col}.pdf", bbox_inches="tight")
        csv_df = df.copy()
        csv_df.index = [f"{i}:{name}" for i, name in enumerate(df.index)]
        csv_df.columns = [str(i) for i in range(len(df.columns))]
        csv_df.to_csv(heatmaps_dir / f"model_matchups_{safe_col}.csv")
        plt.close(fig)


def plot_elo_of_random(rankings_df, out_dir):
    if "random" not in rankings_df.index:
        print("Skipping random_rank plot: 'random' not present after filtering.")
        return
    random_rank_df = rankings_df.loc["random"]
    sorted_rank = random_rank_df.sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    xs = np.arange(len(sorted_rank), dtype=float)
    ax.plot(
        xs,
        sorted_rank.to_numpy(dtype=float),
        linestyle="-",
        linewidth=1.6,
        color=RANDOM_HIGHLIGHT_GOLD,
        marker="o",
        markersize=4.2,
        markerfacecolor=RANDOM_HIGHLIGHT_GOLD,
        markeredgecolor="#2f2149",
        markeredgewidth=0.45,
        solid_capstyle="round",
        alpha=0.96,
    )
    ax.set_xlabel("Game" if sorted_rank.index.name is None else sorted_rank.index.name)
    ax.set_ylabel("Random Policy Rank")
    ax.set_title("Random Policy Rank per Game")
    ax.set_xticks(xs)
    ax.set_xticklabels(sorted_rank.index, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.2, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig.savefig(out_dir / "random_rank.pdf")
    plt.close(fig)


def plot_rank_correlation_heatmap(rankings_df, out_dir, method: str = "spearman"):
    _cols = rankings_df.columns.tolist()
    if len(_cols) < 2:
        print(f"Not enough columns to plot rank correlation heatmap: {_cols}")
        return
    if method not in ("spearman", "kendall"):
        raise ValueError(f"Unsupported rank correlation method: {method}")
    rankings_df = rankings_df.copy()
    rankings_df["Median rank"] = rankings_df.fillna(-9999).median(axis=1, skipna=False).round(1)
    ranks = rankings_df.rank(axis=0, method="average", na_option="keep")
    # Spearman = Pearson on ranks; Kendall tau-b is rank-based so it is unaffected by the rank transform.
    corr = ranks.corr(method="pearson" if method == "spearman" else "kendall")

    C = corr.loc[_cols, _cols].copy()
    if C.isna().all().all():
        print(f"Skipping {method} rank correlation heatmap: correlation matrix is all-NaN.")
        return
    # Put games closest to the median ranking first; undefined correlations go last.
    ordered_games = corr.loc[_cols, "Median rank"].sort_values(
        ascending=False, kind="stable", na_position="last"
    ).index.tolist()
    ordered = ["Median rank"] + ordered_games
    corr = corr.reindex(index=ordered, columns=ordered)

    if method == "spearman":
        cbar_label, title, out_name = "Spearman rank correlation (ρ)", "Spearman rank-correlation heatmap", "rank_correlation_heatmap.pdf"
    else:
        cbar_label, title, out_name = "Kendall rank correlation (τ)", "Kendall rank-correlation heatmap", "rank_correlation_heatmap_kendall.pdf"

    fig, ax = plt.subplots(figsize=(8.6, 6.8))
    im = ax.imshow( corr.to_numpy(), vmin=-1, vmax=1, cmap="RdYlGn", interpolation="nearest", aspect="auto" )
    ax.grid(False)
    ax.set_xticks(np.arange(corr.shape[1]))
    ax.set_yticks(np.arange(corr.shape[0]))
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xticklabels(corr.columns, rotation=90)
    ax.set_yticklabels(corr.index)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    ax.set_title(title)
    plt.tight_layout()
    fig.savefig(out_dir / out_name)
    plt.close(fig)


def save_csv_top_bots(results, out_dir, model_order_by_median_elo):
    top_bots = {}
    for game_col, value in results.items():
        if value.get("top_bots_per_model") is None:
            continue
        per_parent: dict[str, list[str]] = {}
        for bot_name in sorted(value["top_bots_per_model"]):
            per_parent.setdefault(bot_name.split("/")[0], []).append(bot_name.split("/")[-1])
        top_bots[game_col] = {parent: ",".join(nums) for parent, nums in per_parent.items()}
    if not top_bots:
        return
    top_bots_df = pd.DataFrame(top_bots)
    top_bots_df = top_bots_df.reindex(index=model_order_by_median_elo)
    top_bots_df.to_csv(out_dir / "bots_df_top.csv")
    all_bots = {}
    for game_col, value in results.items():
        all_bots[game_col] = {name: ','.join([r.split('/')[-1] for r in ranks]) for name, ranks in value["all_bots"].items()}
    all_bots_df = pd.DataFrame(all_bots)
    all_bots_df = all_bots_df.reindex(index=model_order_by_median_elo)
    all_bots_df.to_csv(out_dir / "bots_df_all.csv")


def save_csv_error_turn_count(results, out_dir, model_order_by_median_elo):
    error_turn_count_df = pd.DataFrame(index=model_order_by_median_elo, columns=list(results.keys()), dtype=object)
    total_timeout: dict[str, str] = {}
    for game_col, value in results.items():
        error_d, timeout_d = value["error_turn_count"]
        leaderboard_df = value["leaderboard_table_df"]
        for model_name in model_order_by_median_elo:
            error_turn_count_df.loc[model_name, game_col] = fmt_err_timeout(error_d.get(model_name), timeout_d.get(model_name))

        num_battles = float(leaderboard_df["num_battles"].sum())
        timeout_sum = float(sum(timeout_d.values()))
        perc = (2.0 * timeout_sum / num_battles) * 100
        total_timeout[game_col] = f"{int(timeout_sum)} ({perc:.1f}%)"

    error_turn_count_df.loc["Total"] = total_timeout
    error_turn_count_df = error_turn_count_df.reindex(index=model_order_by_median_elo + ["Total"])
    error_turn_count_df.to_csv(out_dir / "error_turn_count_df.csv")
    return error_turn_count_df


def _escape_latex_text(value: Any) -> str:
    text = str(value)
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _to_latex_with_bold_best(
    numeric_df: pd.DataFrame,
    *,
    best_mode: str,
    index_name_map: Optional[dict[str, str]] = None,
    decimals: int = 1,
    starred_rows: Optional[set[str]] = None,
    starred_cells: Optional[set[tuple[str, str]]] = None,
) -> str:
    if best_mode not in {"max", "min"}:
        raise ValueError(f"Unsupported best_mode: {best_mode}")
    if decimals < 0:
        raise ValueError(f"Unsupported decimals: {decimals}")

    display_df = pd.DataFrame(index=numeric_df.index, columns=numeric_df.columns, dtype=object)
    starred_cells = starred_cells or set()
    for col in numeric_df.columns:
        series = pd.to_numeric(numeric_df[col], errors="coerce")
        finite = series[np.isfinite(series.to_numpy(dtype=float, na_value=np.nan))]
        if finite.empty:
            best_mask = pd.Series(False, index=series.index)
        else:
            best_value = finite.max() if best_mode == "max" else finite.min()
            best_mask = series.eq(best_value) & series.notna()
        for idx, value in series.items():
            if pd.isna(value):
                display_df.loc[idx, col] = ""
                continue
            cell_text = f"{float(value):.{decimals}f}"
            if bool(best_mask.loc[idx]):
                cell_text = rf"\textbf{{{cell_text}}}"
            if (str(idx), str(col)) in starred_cells:
                cell_text += "*"
            display_df.loc[idx, col] = cell_text

    raw_index_labels = display_df.index.astype(str)
    starred_rows = starred_rows or set()
    index_labels = raw_index_labels
    if index_name_map:
        index_labels = index_labels.map(lambda x: index_name_map.get(x, x))
    display_df.index = [
        _escape_latex_text(label.replace("_", " ").title().replace(" Free", ""))
        + ("*" if raw_name in starred_rows else "")
        for raw_name, label in zip(raw_index_labels, index_labels)
    ]
    display_df.columns = [_escape_latex_text(col) for col in display_df.columns]
    return display_df.to_latex(
        index=True,
        escape=False,
        column_format="l" + "r" * display_df.shape[1],
    )


def _build_unfinished_rating_cells(
    rating_df_median: pd.DataFrame,
    results: dict[str, dict[str, Any]],
) -> set[tuple[str, str]]:
    unfinished_cells: set[tuple[str, str]] = set()
    row_names = [str(name) for name in rating_df_median.index]
    game_columns = [str(col) for col in rating_df_median.columns if str(col) != "Median ELO"]
    for col in game_columns:
        game_result = results.get(col)
        if not isinstance(game_result, dict):
            continue
        done_rate_stats = game_result.get("done_rate_stats")
        if not isinstance(done_rate_stats, dict):
            continue
        for row_name in row_names:
            bot_stats = done_rate_stats.get(row_name)
            if not isinstance(bot_stats, dict):
                continue
            total = float(bot_stats.get("total", 0.0) or 0.0)
            done = float(bot_stats.get("done", 0.0) or 0.0)
            if total > 0.0 and done <= 0.0:
                unfinished_cells.add((row_name, col))
    return unfinished_cells


def _save_ratings_outputs(
    rating_df_median: pd.DataFrame,
    out_dir: Path,
    *,
    results: Optional[dict[str, dict[str, Any]]] = None,
) -> None:
    rating_df_median.to_csv(out_dir / "rating_df.csv")
    starred_rows: set[str] = set()
    starred_cells: set[tuple[str, str]] = set()
    if results is not None:
        starred_cells = _build_unfinished_rating_cells(rating_df_median, results)
    latex_str = _to_latex_with_bold_best(
        rating_df_median,
        best_mode="max",
        index_name_map={"random": "Random Legal Move"},
        decimals=0,
        starred_rows=starred_rows,
        starred_cells=starred_cells,
    )
    (out_dir / "rating_df.latex").write_text(latex_str, encoding="utf-8")


def save_csv_ratings(results, out_dir: Optional[Path] = None) -> tuple[pd.DataFrame, list[str]]:
    l = [v['leaderboard_table_df']['rating'].rename(k) for k, v in results.items()]
    if len(l) > 1:
        rating_df = pd.concat(l, axis=1)
    elif len(l) == 1:
        rating_df = pd.DataFrame(l[0])
    else:
        raise ValueError(f"Expected 1 or more leaderboard table dataframes, got {len(l)}")
    rating_df_median = rating_df.copy()
    rating_df_median["Median ELO"] = rating_df_median.median(axis=1, skipna=True)
    rating_df_median = rating_df_median.round(2)
    rating_df_median = rating_df_median.sort_values(by="Median ELO", ascending=False)
    model_order_by_median_elo = rating_df_median.index.tolist()
    if out_dir is not None:
        _save_ratings_outputs(rating_df_median, out_dir, results=results)
    return rating_df, model_order_by_median_elo


def save_csv_rankings(results, out_dir, model_order_by_median_elo) -> pd.DataFrame:
    rankings_df = pd.concat([v['leaderboard_table_df']['final_ranking'].rename(k) for k, v in results.items()], axis=1)
    rankings_df = rankings_df.reindex(index=model_order_by_median_elo)
    rankings_df.to_csv(out_dir / "rankings_df.csv")

    latex_df = rankings_df.copy()
    if "Mean ELO" in latex_df.columns:
        latex_df = latex_df.drop(columns=["Mean ELO"])
    latex_str = _to_latex_with_bold_best(
        latex_df,
        best_mode="min",
        index_name_map={"random": "Random Legal Move"},
    )
    (out_dir / "rankings_df.latex").write_text(latex_str, encoding="utf-8")
    return rankings_df


def _split_thinking_variant(model_name: str) -> Optional[tuple[str, str, int, str]]:
    for suffix, level_key, order, level_label in _THINKING_LEVEL_SPECS:
        if model_name.endswith(suffix):
            return model_name[: -len(suffix)], level_key, order, level_label
    return None


def _thinking_family_label(family: str, family_df: pd.DataFrame) -> str:
    if family.startswith("gpt_"):
        return family.replace("gpt_", "GPT-")
    if family.startswith("claude_"):
        return family.replace("claude_", "Claude ").replace("_", " ").title()
    if family.startswith("gemini_"):
        return family.replace("gemini_", "Gemini ").replace("_", " ").title()
    return family.replace("_", " ").title()


def _build_thinking_plot_df(results_models: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rating_df, _ = save_csv_ratings(results_models, out_dir=None)
    median_elo = rating_df.median(axis=1, skipna=True)

    rows: list[dict[str, Any]] = []
    for model_name, elo in median_elo.items():
        model_name = str(model_name)
        parsed = _split_thinking_variant(model_name)
        if parsed is None or not np.isfinite(float(elo)):
            continue
        family, thinking_key, thinking_order, thinking_label = parsed
        rows.append(
            {
                "model": model_name,
                "family": family,
                "thinking_key": thinking_key,
                "thinking_order": thinking_order,
                "thinking_label": thinking_label,
                "median_elo": float(elo),
            }
        )

    thinking_df = pd.DataFrame(rows)
    if thinking_df.empty:
        raise ValueError("No thinking-level model variants found in results_models.")

    family_counts = thinking_df.groupby("family")["thinking_key"].nunique()
    keep_families = family_counts[family_counts >= 2].index.tolist()
    thinking_df = thinking_df[thinking_df["family"].isin(keep_families)].copy()
    if thinking_df.empty:
        raise ValueError("Found thinking-level variants, but no family has at least two thinking levels to plot.")

    family_label_map = {
        family: _thinking_family_label(family, family_df)
        for family, family_df in thinking_df.groupby("family", sort=False)
    }
    thinking_df["family_label"] = thinking_df["family"].map(family_label_map)
    thinking_df = thinking_df.sort_values(
        by=["family_label", "thinking_order", "model"],
        ascending=[True, True, True],
    ).reset_index(drop=True)
    return thinking_df


def plot_thinking_levels(thinking_df: pd.DataFrame, out_dir: Path) -> None:
    marker_cycle = ["o", "s", "^", "D", "P", "X", "v", "*", "<", ">"]
    color_cycle = [
        "#6c4ca8",  # automata purple, as in the engine plots
        "#E69F00",  # engine orange, as in the engine plots
        "#117733",
        "#AA4499",
        "#DDCC77",
        "#CC6677",
        "#332288",
        "#88CCEE",
    ]
    family_scores = (
        thinking_df.groupby(["family", "family_label"], sort=False)["median_elo"]
        .max()
        .sort_values(ascending=False)
    )
    family_order = [family for family, _ in family_scores.index.tolist()]
    family_to_label = {
        family: label for family, label in family_scores.index.tolist()
    }
    family_to_marker = {
        family: marker_cycle[idx % len(marker_cycle)] for idx, family in enumerate(family_order)
    }
    family_to_color = {
        family: color_cycle[idx % len(color_cycle)] for idx, family in enumerate(family_order)
    }

    tick_pairs = sorted(
        {(int(row["thinking_order"]), str(row["thinking_label"])) for _, row in thinking_df.iterrows()},
        key=lambda pair: pair[0],
    )
    x_ticks = [pair[0] for pair in tick_pairs]
    x_labels = [pair[1] for pair in tick_pairs]

    fig, ax = plt.subplots(figsize=(6.6, 3.1))
    for family in family_order:
        group = thinking_df[thinking_df["family"] == family].sort_values("thinking_order")
        xs = group["thinking_order"].to_numpy(dtype=float)
        ys = group["median_elo"].to_numpy(dtype=float)
        color = family_to_color[family]
        marker = family_to_marker[family]

        ax.plot(xs, ys, linestyle=":", linewidth=1.6, color=color, alpha=0.95, zorder=2)
        ax.scatter(
            xs,
            ys,
            s=58,
            marker=marker,
            color=color,
            edgecolors="black",
            linewidths=0.5,
            label=family_to_label[family],
            zorder=3,
        )

    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels)
    ax.set_xlim(min(x_ticks) - 0.25, max(x_ticks) + 0.25)
    ax.set_xlabel("Thinking")
    ax.set_ylabel("Median ELO")
    ax.set_title("Median ELO by Thinking Level", pad=6)
    ax.grid(axis="y", alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(title="Model", frameon=False, loc="best", fontsize=8.5, title_fontsize=9)
    plt.tight_layout()
    fig.savefig(out_dir / "thinking_plot.pdf")
    plt.close(fig)


def run_thinking_plot(args: argparse.Namespace) -> None:
    in_pkl = Path(args.in_pkl)
    if not in_pkl.is_absolute():
        in_pkl = ROOT_DIR / in_pkl
    if not in_pkl.exists():
        raise FileNotFoundError(f"Input pickle not found: {in_pkl}")
    with in_pkl.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pickle payload type: expected dict, got {type(payload).__name__}")
    results_models = payload.get("results_models")
    if not isinstance(results_models, dict) or not results_models:
        raise ValueError("Input pickle missing non-empty 'results_models' dictionary")

    out_dir = Path(args.out_dir) if args.out_dir else in_pkl.parent
    if not out_dir.is_absolute():
        out_dir = ROOT_DIR / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    thinking_df = _build_thinking_plot_df(results_models)
    plot_thinking_levels(thinking_df, out_dir)
    print(f"Saved thinking plot artifacts to {out_dir}")


def run_plot_pkl(args: argparse.Namespace):
    in_pkl = Path(args.in_pkl)
    if not in_pkl.is_absolute():
        in_pkl = ROOT_DIR / in_pkl
    if not in_pkl.exists():
        raise FileNotFoundError(f"Input pickle not found: {in_pkl}")
    with in_pkl.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pickle payload type: expected dict, got {type(payload).__name__}")
    results = payload[f"results_{args.mode}"]
    config = payload["config"]
    out_dir = Path(args.out_dir) if args.out_dir else in_pkl.parent
    if not out_dir.is_absolute():
        out_dir = ROOT_DIR / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Using results key: results_{args.mode}")
    rating_system = config["rating_system"]
    heatmap_scale = 2.6 if args.mode == "bots" else 1.9
    rating_df_full, model_order_by_median_elo_full = save_csv_ratings(results, out_dir=None)
    focus_models = _resolve_model_tokens(
        args.focus_on,
        model_order_by_median_elo_full,
        flag_name="--focus-on",
    )
    if args.focus_on is not None and not focus_models:
        raise ValueError("No models matched --focus-on entries.")
    ignored_models = _resolve_model_tokens(
        args.ignore,
        model_order_by_median_elo_full,
        flag_name="--ignore",
    )
    filtered_model_order_full = [m for m in model_order_by_median_elo_full if m not in ignored_models]
    if args.ignore is not None and not filtered_model_order_full:
        raise ValueError("All models were excluded by --ignore.")
    if focus_models:
        focus_models = {m for m in focus_models if m not in ignored_models}
        if args.focus_on is not None and not focus_models:
            raise ValueError("No models remain after applying both --focus-on and --ignore.")
    model_order_for_outputs = (
        [m for m in filtered_model_order_full if m in focus_models]
        if focus_models
        else list(filtered_model_order_full)
    )
    rating_df = rating_df_full.reindex(index=model_order_for_outputs)
    rating_df_median = rating_df.copy()
    rating_df_median["Median ELO"] = rating_df_median.median(axis=1, skipna=True)
    rating_df_median = rating_df_median.round(2)
    rating_df_median = rating_df_median.sort_values(by="Median ELO", ascending=False)
    _save_ratings_outputs(rating_df_median, out_dir, results=results)
    rankings_df = save_csv_rankings(results, out_dir, model_order_for_outputs)
    save_csv_top_bots(results, out_dir, model_order_for_outputs)
    save_csv_error_turn_count(results, out_dir, model_order_for_outputs)
    plot_median_elo(rating_df, rating_system, out_dir)
    if args.mode == "bots":
        plot_bot_elo_scatter(
            rating_df,
            out_dir,
            results=results,
            focus_models=focus_models if focus_models else None,
        )
    plot_ranking_scatter(rankings_df, model_order_for_outputs, out_dir)
    plot_ranking_scatter(
        rankings_df,
        model_order_for_outputs,
        out_dir,
        sort_by_mean_rank=True,
        filename="per_game_rank_scatter_sorted.pdf",
    )
    plot_mean_rank_bar(rankings_df, model_order_for_outputs, out_dir)
    plot_elo_of_random(rankings_df, out_dir)
    plot_heatmap_combined(
        results,
        filtered_model_order_full,
        out_dir,
        scale=heatmap_scale,
        focus_models=focus_models if focus_models else None,
    )
    plot_heatmap_subplots(
        results,
        filtered_model_order_full,
        out_dir,
        scale=heatmap_scale,
        use_per_game_elo_order=(args.mode == "bots"),
        focus_models=focus_models if focus_models else None,
    )
    plot_rank_correlation_heatmap(rankings_df, out_dir, method="spearman")
    plot_rank_correlation_heatmap(rankings_df, out_dir, method="kendall")
    print(f"Saved plot/csv artifacts to {out_dir}")


def _best_bot_per_parent_from_leaderboard_df(leaderboard_df: pd.DataFrame) -> dict[str, str]:
    top2 = _top_bots_per_parent_from_leaderboard_df(leaderboard_df, n=1)
    return {parent: bots[0] for parent, bots in top2.items() if bots}


def _top_bots_per_parent_from_leaderboard_df(leaderboard_df: pd.DataFrame, n: int = 2) -> dict[str, list[str]]:
    if not isinstance(leaderboard_df, pd.DataFrame) or "rating" not in leaderboard_df.columns:
        return {}
    if n <= 0:
        return {}
    ratings = pd.to_numeric(leaderboard_df["rating"], errors="coerce").dropna()
    rows: list[tuple[str, str, float]] = []
    for bot_name, rating in ratings.items():
        if not isinstance(bot_name, str):
            continue
        rows.append((bot_name.split("/")[0], bot_name, float(rating)))
    rows.sort(key=lambda x: (x[0], -x[2], x[1]))
    per_parent: dict[str, list[str]] = {}
    for parent, bot_name, _ in rows:
        bucket = per_parent.setdefault(parent, [])
        if len(bucket) < n:
            bucket.append(bot_name)
    return per_parent


def _bot_ratings_from_leaderboard_df(leaderboard_df: pd.DataFrame) -> dict[str, float]:
    if not isinstance(leaderboard_df, pd.DataFrame) or "rating" not in leaderboard_df.columns:
        return {}
    ratings = pd.to_numeric(leaderboard_df["rating"], errors="coerce").dropna()
    return {str(bot): float(rating) for bot, rating in ratings.items() if isinstance(bot, str)}


def _quals_rank_for_bot(ci_rankings: dict[str, Any], parent: str, bot: str) -> float:
    for row in ci_rankings.get(parent, []):
        if row.get("bot") == bot:
            v = row.get("final_ranking")
            if v is None:
                return np.nan
            return float(v)
    return np.nan


def _sorted_quals_rows_by_point(ci_rankings: dict[str, Any], parent: str) -> list[dict[str, Any]]:
    rows = ci_rankings.get(parent, [])
    if not rows:
        return []

    def _key(row: dict[str, Any]) -> tuple[float, float, str]:
        try:
            rating = float(row.get("rating"))
        except Exception:
            rating = float("-inf")
        try:
            final_ranking = float(row.get("final_ranking"))
        except Exception:
            final_ranking = float("inf")
        bot_name = str(row.get("bot", ""))
        return (-rating, final_ranking, bot_name)

    return sorted(rows, key=_key)


def _quals_point_rank_for_bot(ci_rankings: dict[str, Any], parent: str, bot: str) -> float:
    sorted_rows = _sorted_quals_rows_by_point(ci_rankings, parent)
    for i, row in enumerate(sorted_rows, start=1):
        if row.get("bot") == bot:
            return float(i)
    return np.nan


def _quals_best_row(ci_rankings: dict[str, Any], parent: str) -> Optional[dict[str, Any]]:
    rows = ci_rankings.get(parent, [])
    if not rows:
        return None

    def _key(row: dict[str, Any]) -> tuple[float, float]:
        try:
            rank = float(row.get("final_ranking"))
        except Exception:
            rank = float("inf")
        try:
            rating = float(row.get("rating"))
        except Exception:
            rating = float("-inf")
        return (rank, -rating)

    return min(rows, key=_key)


def _quals_rating_for_bot(ci_rankings: dict[str, Any], parent: str, bot: str) -> float:
    for row in ci_rankings.get(parent, []):
        if row.get("bot") == bot:
            try:
                return float(row.get("rating"))
            except Exception:
                return np.nan
    return np.nan


def _first_finite_float(row_like: Any, keys: list[str]) -> float:
    for key in keys:
        try:
            value = float(row_like.get(key, np.nan))
        except Exception:
            continue
        if np.isfinite(value):
            return value
    return np.nan


def plot_quals_rank_heatmap(
    df: pd.DataFrame,
    out_dir: Path,
    *,
    title: str = "Quals Rank of Best Final-ELO Bot",
    filename: str = "quals_best_elo_rank_heatmap.pdf",
) -> None:
    if df.empty:
        print("Skipping quals heatmap: no data.")
        return
    data = df.to_numpy(dtype=float, copy=True)
    n_rows, n_cols = data.shape
    cell = 0.24
    fig_w = max(8.0, cell * n_cols + 2.5)
    fig_h = max(8.0, cell * n_rows + 2.5)
    finite = data[np.isfinite(data)]
    if finite.size == 0:
        print("Skipping quals heatmap: all cells are NaN.")
        return
    max_rank = max(1, int(np.nanmax(finite)))
    colors: list[Any] = []
    for rank in range(1, max_rank + 1):
        if rank == 1:
            colors.append("#2ca02c")  # green
        elif rank == 2:
            colors.append("#ffd84d")  # yellow
        else:
            t = (rank - 3) / max(1, max_rank - 3)
            colors.append(plt.cm.OrRd(0.45 + 0.45 * t))
    cmap = ListedColormap(colors)
    cmap.set_bad("#f0f0f0")
    bounds = np.arange(0.5, max_rank + 1.5, 1.0)
    norm = BoundaryNorm(bounds, cmap.N)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=120, constrained_layout=True)
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect="equal", interpolation="nearest")
    ax.grid(False)

    # annotate cells with quals rank when matrix is not huge
    if n_rows * n_cols <= 2500:
        ann_fs = max(4.0, min(8.0, 300.0 / max(n_rows, n_cols)))
        for i in range(n_rows):
            for j in range(n_cols):
                v = data[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f"{int(v)}", ha="center", va="center", fontsize=ann_fs)

    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(df.columns, rotation=45, ha="right")
    ax.set_yticklabels([model_name_map(m) for m in df.index.astype(str)])
    ax.set_xlabel("Game")
    ax.set_ylabel("Model")
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("Quals Rank (lower is better)")
    cbar.ax.invert_yaxis()

    fig.savefig(out_dir / filename, bbox_inches="tight")
    plt.close(fig)


def plot_quals_final_elo_delta_heatmap(
    df: pd.DataFrame,
    out_dir: Path,
    *,
    title: str = "Final ELO Delta: Top Quals Bot - Best Finalist",
    filename: str = "quals_top_qual_minus_best_final_elo_heatmap.pdf",
) -> None:
    if df.empty:
        print("Skipping quals final-ELO-delta heatmap: no data.")
        return
    data = df.to_numpy(dtype=float, copy=True)
    finite = data[np.isfinite(data)]
    if finite.size == 0:
        print("Skipping quals final-ELO-delta heatmap: all cells are NaN.")
        return

    n_rows, n_cols = data.shape
    cell = 0.24
    fig_w = max(8.0, cell * n_cols + 2.5)
    fig_h = max(8.0, cell * n_rows + 2.5)
    max_abs = max(abs(float(np.nanmin(finite))), abs(float(np.nanmax(finite))), 1.0)
    norm = TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)
    cmap = plt.cm.RdYlGn.copy()
    cmap.set_bad("#f0f0f0")

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=120, constrained_layout=True)
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect="equal", interpolation="nearest")
    ax.grid(False)

    if n_rows * n_cols <= 2500:
        ann_fs = max(4.0, min(8.0, 300.0 / max(n_rows, n_cols)))
        for i in range(n_rows):
            for j in range(n_cols):
                v = data[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f"{int(round(v))}", ha="center", va="center", fontsize=ann_fs)

    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(df.columns, rotation=45, ha="right")
    ax.set_yticklabels([model_name_map(m) for m in df.index.astype(str)])
    ax.set_xlabel("Game")
    ax.set_ylabel("Model")
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("Final ELO Delta (Top Quals - Best Finalist)")

    fig.savefig(out_dir / filename, bbox_inches="tight")
    plt.close(fig)


def plot_quals_point_top2_ci_by_model(
    ci_plot: dict[str, dict[str, list[dict[str, float | str]]]],
    models: list[str],
    games: list[str],
    out_dir: Path,
    hide_yellow: bool = False,
) -> None:
    models = [m for m in models if m in ci_plot]
    if not models:
        print("Skipping CI subplot plot: no models with CI data.")
        return
    if not games:
        print("Skipping CI subplot plot: no games.")
        return

    n_models = len(models)
    ncols = 4
    nrows = int(np.ceil(n_models / ncols))
    fig_w = 4.2 * ncols
    fig_h = 2.6 * nrows
    fig, axes = plt.subplots(nrows, ncols, figsize=(fig_w, fig_h), dpi=170, constrained_layout=False)
    if isinstance(axes, np.ndarray):
        axes_flat = axes.ravel()
    else:
        axes_flat = np.asarray([axes])

    for ax_i, model in enumerate(models):
        ax = axes_flat[ax_i]
        per_game = ci_plot.get(model, {})
        has_lines = False
        model_bounds: list[float] = []
        warning_games: dict[int, str] = {}
        for j, game in enumerate(games):
            entries = per_game.get(game, [])
            if len(entries) < 2:
                continue
            # Always put the higher quals point-estimate bot on the left.
            entries = sorted(
                entries[:2],
                key=lambda e: (
                    -float(e.get("point_rating", float("-inf"))),
                    str(e.get("bot", "")),
                ),
            )
            r0 = float(entries[0].get("final_rating", np.nan))
            r1 = float(entries[1].get("final_rating", np.nan))
            if np.isfinite(r0) and np.isfinite(r1):
                green_idx = 0 if r0 >= r1 else 1
            elif np.isfinite(r0):
                green_idx = 0
            elif np.isfinite(r1):
                green_idx = 1
            else:
                green_idx = 0
            green_quals_rank = float(entries[green_idx].get("quals_rank", np.nan))
            if green_idx == 1:
                if np.isfinite(green_quals_rank) and green_quals_rank == 1.0:
                    if not hide_yellow:
                        warning_games[j] = "#ffd84d"
                else:
                    warning_games[j] = "#d62728"

            for k, entry in enumerate(entries[:2]):
                lo = float(entry.get("qlower", np.nan))
                hi = float(entry.get("qupper", np.nan))
                if not np.isfinite(lo) or not np.isfinite(hi):
                    continue
                x = j + (-0.12 if k == 0 else 0.12)
                color = "#2ca02c" if k == green_idx else "#d62728"
                ax.vlines(x, lo, hi, color=color, linewidth=1.8, alpha=0.95)
                has_lines = True
                model_bounds.extend([lo, hi])

        ax.set_title(str(model_name_map(model)), fontsize=8)
        ax.set_xticks(np.arange(len(games)))
        ax.set_xticklabels(games, rotation=90, fontsize=5)
        ax.tick_params(axis="y", labelsize=6)
        ax.grid(axis="y", alpha=0.2, linewidth=0.5)
        if ax_i % ncols == 0:
            ax.set_ylabel("Quals ELO CI", fontsize=7)
        ax.set_xlim(-0.5, len(games) - 0.5)
        marker_y: Optional[float] = None
        if model_bounds:
            y_min = float(np.min(model_bounds))
            y_max = float(np.max(model_bounds))
            span = max(1.0, y_max - y_min)
            lower_pad = 0.16 * span
            upper_pad = 0.03 * span
            marker_y = y_min - 0.08 * span
            ax.set_ylim(y_min - lower_pad, y_max + upper_pad)
        for j in sorted(warning_games):
            if marker_y is None:
                continue
            face_color = warning_games[j]
            text_color = "black" if face_color == "#ffd84d" else "white"
            ax.text(
                j,
                marker_y,
                "!",
                ha="center",
                va="center",
                fontsize=5,
                fontweight="bold",
                color=text_color,
                bbox={
                    "boxstyle": "circle,pad=0.14",
                    "facecolor": face_color,
                    "edgecolor": face_color,
                    "linewidth": 0.5,
                },
            )
        if not has_lines:
            ax.text(0.5, 0.5, "no CI data", transform=ax.transAxes, ha="center", va="center", fontsize=6, color="0.4")

    for i in range(n_models, len(axes_flat)):
        axes_flat[i].axis("off")

    legend_handles = [
        Line2D([0], [0], color="#2ca02c", lw=2.0, label="#1 tournament ranking"),
        Line2D([0], [0], color="#d62728", lw=2.0, label="#2 tournament ranking"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=2, frameon=False, fontsize=8, bbox_to_anchor=(0.5, 0.945))
    fig.suptitle("Top-2 Quals Bots CI", fontsize=10, y=0.958)
    fig.subplots_adjust(top=0.91, hspace=0.55, wspace=0.28)
    fig.savefig(out_dir / "quals_point_top2_ci_by_model.jpg", bbox_inches="tight", format="jpg")
    plt.close(fig)


def run_quals_plot(args: argparse.Namespace) -> None:
    in_pkl = Path(args.in_pkl)
    if not in_pkl.is_absolute():
        in_pkl = ROOT_DIR / in_pkl
    if not in_pkl.exists():
        raise FileNotFoundError(f"Input pickle not found: {in_pkl}")
    with in_pkl.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pickle payload type: expected dict, got {type(payload).__name__}")
    results_bots = payload.get("results_bots")
    if not isinstance(results_bots, dict):
        raise ValueError("Input pickle missing 'results_bots' dictionary")
    results_models = payload.get("results_models")

    quals_dir = Path(args.quals_dir)
    if not quals_dir.is_absolute():
        quals_dir = ROOT_DIR / quals_dir
    out_dir = Path(args.out_dir) if args.out_dir else quals_dir
    if not out_dir.is_absolute():
        out_dir = ROOT_DIR / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    game_to_parent_rank: dict[str, dict[str, float]] = {}
    game_to_parent_point_rank: dict[str, dict[str, float]] = {}
    game_to_parent_final_elo_delta: dict[str, dict[str, float]] = {}
    ci_by_model_game: dict[str, dict[str, list[dict[str, float | str]]]] = {}
    for game, world, colname, _ in MAIN_GAMES_WORLD_COLUMNS:
        print(f"running quals-plot for {game} {world} ({colname})")
        game_result = results_bots.get(colname)
        if not isinstance(game_result, dict):
            print(f"Warning: missing results_bots entry for {colname}, skipping.")
            continue
        leaderboard_df = game_result.get("leaderboard_table_df")
        top2_by_parent = _top_bots_per_parent_from_leaderboard_df(leaderboard_df, n=2)
        best_by_parent = {parent: bots[0] for parent, bots in top2_by_parent.items() if bots}
        final_bot_ratings = _bot_ratings_from_leaderboard_df(leaderboard_df)
        quals_path = quals_dir / f"matches_quals_{game}_{world}.json"
        if not quals_path.exists():
            print(f"Warning: missing quals file {quals_path}, filling NaN.")
            game_to_parent_rank[colname] = {parent: np.nan for parent in best_by_parent}
            game_to_parent_point_rank[colname] = {parent: np.nan for parent in best_by_parent}
            game_to_parent_final_elo_delta[colname] = {parent: np.nan for parent in best_by_parent}
            continue
        with quals_path.open("r") as f:
            quals_data = json.load(f)
        ci_rankings = quals_data.get("ci_rankings", {})
        per_parent_rank: dict[str, float] = {}
        per_parent_point_rank: dict[str, float] = {}
        per_parent_final_elo_delta: dict[str, float] = {}
        for parent, bot_name in best_by_parent.items():
            rank = _quals_rank_for_bot(ci_rankings, parent, bot_name)
            other_rank = np.nan
            top2_bots = top2_by_parent.get(parent, [])
            if len(top2_bots) >= 2:
                other_rank = _quals_rank_for_bot(ci_rankings, parent, top2_bots[1])

            # First heatmap display rule:
            # 1: best bot rank is 1 and other bot rank is 2
            # 2: best bot rank is 2
            # NaN: both bots rank 1 (or anything outside the two explicit rules)
            display_rank = np.nan
            if np.isfinite(rank) and rank == 2.0:
                display_rank = 2.0
            elif np.isfinite(rank) and rank == 1.0 and np.isfinite(other_rank) and other_rank == 2.0:
                display_rank = 1.0
            point_rank = _quals_point_rank_for_bot(ci_rankings, parent, bot_name)
            per_parent_rank[parent] = display_rank
            per_parent_point_rank[parent] = point_rank
            quals_best = _quals_best_row(ci_rankings, parent)
            quals_best_bot = str(quals_best.get("bot", "")) if isinstance(quals_best, dict) else ""
            final_best_rating = final_bot_ratings.get(bot_name, np.nan)
            quals_best_final_rating = final_bot_ratings.get(quals_best_bot, np.nan) if quals_best_bot else np.nan
            if np.isfinite(quals_best_final_rating) and np.isfinite(final_best_rating):
                per_parent_final_elo_delta[parent] = quals_best_final_rating - final_best_rating
            else:
                per_parent_final_elo_delta[parent] = np.nan
            if np.isfinite(rank) and rank > 1:
                if not quals_best:
                    continue
                this_quals_rating = _quals_rating_for_bot(ci_rankings, parent, bot_name)
                try:
                    quals_best_quals_rating = float(quals_best.get("rating"))
                except Exception:
                    quals_best_quals_rating = np.nan
                delta_final = final_best_rating - quals_best_final_rating
                delta_quals = this_quals_rating - quals_best_quals_rating
                print(
                    f"{delta_final:8.2f} / {delta_quals:8.2f} | {int(rank):2d} | {colname} | {parent}"
                )

            # Third plot payload: top-2 quals bots by point estimate with quals CIs.
            point_rows = _sorted_quals_rows_by_point(ci_rankings, parent)[:2]
            if len(point_rows) == 2 and isinstance(leaderboard_df, pd.DataFrame):
                bot_entries: list[dict[str, float | str]] = []
                for row in point_rows:
                    bot_cur = str(row.get("bot", ""))
                    if bot_cur not in leaderboard_df.index:
                        continue
                    row_final = leaderboard_df.loc[bot_cur]
                    if isinstance(row_final, pd.DataFrame):
                        row_final = row_final.iloc[0]
                    qlower = _first_finite_float(row, ["rating_qlower", "rating_q025"])
                    qupper = _first_finite_float(row, ["rating_qupper", "rating_q975"])
                    if np.isfinite(qlower) and np.isfinite(qupper) and qlower > qupper:
                        qlower, qupper = qupper, qlower
                    final_rank = _first_finite_float(row_final, ["final_ranking"])
                    final_rating = _first_finite_float(row_final, ["rating"])
                    bot_entries.append(
                        {
                            "bot": bot_cur,
                            "point_rating": _first_finite_float(row, ["rating"]),
                            "quals_rank": _first_finite_float(row, ["final_ranking"]),
                            "qlower": qlower,
                            "qupper": qupper,
                            "final_rank": final_rank,
                            "final_rating": final_rating,
                        }
                    )
                if len(bot_entries) == 2:
                    ci_by_model_game.setdefault(parent, {})[colname] = bot_entries
        game_to_parent_rank[colname] = per_parent_rank
        game_to_parent_point_rank[colname] = per_parent_point_rank
        game_to_parent_final_elo_delta[colname] = per_parent_final_elo_delta

    df = pd.DataFrame(game_to_parent_rank)
    df_point = pd.DataFrame(game_to_parent_point_rank)
    df_final_elo_delta = pd.DataFrame(game_to_parent_final_elo_delta)
    ordered_cols = [colname for _, _, colname, _ in MAIN_GAMES_WORLD_COLUMNS if colname in df.columns]
    df = df.reindex(columns=ordered_cols)
    df_point = df_point.reindex(columns=ordered_cols)
    df_final_elo_delta = df_final_elo_delta.reindex(columns=ordered_cols)
    df = df.apply(pd.to_numeric, errors="coerce")
    df_point = df_point.apply(pd.to_numeric, errors="coerce")
    df_final_elo_delta = df_final_elo_delta.apply(pd.to_numeric, errors="coerce")
    if df.empty:
        print("No data produced for quals-plot.")
        return

    # Keep row order consistent with other plots: median-ELO order from results_models.
    ordered_models: list[str] = []
    if isinstance(results_models, dict) and results_models:
        _, model_order_by_median_elo = save_csv_ratings(results_models, out_dir=None)
        ordered_models.extend([m for m in model_order_by_median_elo if m in df.index])
    if not ordered_models:
        med = df.median(axis=1, skipna=True)
        ordered_models = med.sort_values().index.tolist()
    ordered_models.extend(sorted([m for m in df.index if m not in ordered_models]))
    ordered_models = [m for m in ordered_models if str(m).lower() != "random"]
    keep_index = [m for m in df.index if str(m).lower() != "random"]
    df = df.reindex(index=keep_index)
    df_point = df_point.reindex(index=keep_index)
    df_final_elo_delta = df_final_elo_delta.reindex(index=keep_index)
    df = df.reindex(index=ordered_models)
    df_point = df_point.reindex(index=ordered_models)
    df_final_elo_delta = df_final_elo_delta.reindex(index=ordered_models)

    arr = df.to_numpy(dtype=float)
    finite = np.isfinite(arr)
    total = int(finite.sum())
    non_1 = int(np.logical_and(finite, arr != 1).sum())
    print(f"non-1 cells: {non_1}/{total}")
    arr_point = df_point.to_numpy(dtype=float)
    finite_point = np.isfinite(arr_point)
    total_point = int(finite_point.sum())
    non_1_point = int(np.logical_and(finite_point, arr_point != 1).sum())
    print(f"non-1 empirical-point cells: {non_1_point}/{total_point}")

    df.to_csv(out_dir / "quals_best_elo_rank.csv")
    plot_quals_rank_heatmap(
        df,
        out_dir,
        title="Quals Rank of Best Final-ELO Bot",
        filename="quals_best_elo_rank_heatmap.pdf",
    )
    df_point.to_csv(out_dir / "quals_best_elo_point_rank.csv")
    plot_quals_rank_heatmap(
        df_point,
        out_dir,
        title="Quals Point-Estimate Rank of Best Final-ELO Bot",
        filename="quals_best_elo_point_rank_heatmap.pdf",
    )
    df_final_elo_delta.to_csv(out_dir / "quals_top_qual_minus_best_final_elo.csv")
    plot_quals_final_elo_delta_heatmap(
        df_final_elo_delta,
        out_dir,
        title="Top Quals Bot Final ELO - Best Finalist ELO",
        filename="quals_top_qual_minus_best_final_elo_heatmap.pdf",
    )
    plot_quals_point_top2_ci_by_model(
        ci_by_model_game,
        ordered_models,
        ordered_cols,
        out_dir,
        hide_yellow=args.hide_yellow,
    )
    print(f"Saved quals plot artifacts to {out_dir}")


def main() -> None:
    args = parse_args()
    if args.command == "gen_pkl":
        run_gen_pkl(args)
    elif args.command == "plot_pkl":
        run_plot_pkl(args)
    elif args.command == "thinking_plot":
        run_thinking_plot(args)
    elif args.command == "quals-plot":
        run_quals_plot(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
