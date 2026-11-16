#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.append(str(Path(__file__).parent.parent / "src"))
from experimental.exp_utils import MAIN_GAMES_WORLD_COLUMNS

GAME_WORLD_TO_COL_NAME = {f"{game}:{world}": col for game, world, col, _ in MAIN_GAMES_WORLD_COLUMNS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Metric-vs-ELO r^2 boxplots across game worlds.")
    parser.add_argument("--runs", type=Path, required=True, help="Path to strategy_runs.json")
    parser.add_argument("--elo-csv", type=Path, required=True, help="Path to elos_all_bots.csv")
    parser.add_argument("--out", type=Path, default=Path("analysis/visuals/strategy_metric_r2_boxplot.png"))
    parser.add_argument("--median-threshold", type=float, required=True)
    parser.add_argument("--corr-methods", nargs="+", choices=["pearson", "pearson_rank", "spearman", "spearman_rank", "kendall", "kendall_rank"], default=[], help="One or more correlation methods.")
    parser.add_argument("--scatter_plots", "--scatter-plots", "--scatter_plot", action="store_true", help="Also write a single combined scatter grid (3 columns) with OLS fit and r.")
    parser.add_argument("--scatter-dir", type=Path, default=None, help="Directory for scatter plots (default: alongside --out).")
    parser.add_argument("--scatter-log", type=Path, default=None, help="Path for per-scatter log lines (default: alongside --out).")
    parser.add_argument(
        "--all-games-y",
        choices=["rank", "raw"],
        default="rank",
        help="Y-axis mode for all-games scatter: per-game rank or raw ELO.",
    )
    parser.add_argument(
        "--all-games-x",
        choices=["normalized", "raw"],
        default="normalized",
        help="X-axis mode for all-games scatter: per-game normalized [0,1] or raw metric values.",
    )
    return parser.parse_args()


def to_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if np.isfinite(out) else None


def load_runs(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_elo(path: Path) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            return out
        games = header[1:]
        for row in reader:
            if not row:
                continue
            bot = row[0]
            for game_col, cell in zip(games, row[1:]):
                val = to_float(cell)
                if val is not None:
                    out[(bot, game_col)] = val
    return out


def rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        ranks[order[i : j + 1]] = avg_rank
        i = j + 1
    return ranks


def kendall_tau_b(x: np.ndarray, y: np.ndarray) -> float:
    concordant = 0
    discordant = 0
    ties_x = 0
    ties_y = 0
    n = len(x)
    for i in range(n - 1):
        dx = x[i + 1 :] - x[i]
        dy = y[i + 1 :] - y[i]
        sx = np.sign(dx)
        sy = np.sign(dy)
        concordant += int(np.sum(sx * sy > 0))
        discordant += int(np.sum(sx * sy < 0))
        ties_x += int(np.sum((sx == 0) & (sy != 0)))
        ties_y += int(np.sum((sy == 0) & (sx != 0)))
    denom = np.sqrt((concordant + discordant + ties_x) * (concordant + discordant + ties_y))
    if denom == 0:
        return float("nan")
    return float((concordant - discordant) / denom)


def corr_value(x: np.ndarray, y: np.ndarray, method: str) -> float:
    use_rank = method.endswith("_rank")
    base_method = method.replace("_rank", "")
    x_use = rankdata(x) if use_rank else x
    y_use = rankdata(y) if use_rank else y
    if base_method == "pearson":
        if np.std(x_use) == 0 or np.std(y_use) == 0:
            return float("nan")
        return float(np.corrcoef(x_use, y_use)[0, 1])
    if base_method == "spearman":
        x_rank = rankdata(x_use)
        y_rank = rankdata(y_use)
        if np.std(x_rank) == 0 or np.std(y_rank) == 0:
            return float("nan")
        return float(np.corrcoef(x_rank, y_rank)[0, 1])
    if base_method == "kendall":
        return kendall_tau_b(x_use, y_use)
    raise ValueError(f"Unsupported corr method: {method}")


def draw_2d_kde(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    gridsize: int = 60,
    levels: int = 8,
) -> None:
    if len(x) < 8 or len(y) < 8:
        return
    x_std = float(np.std(x))
    y_std = float(np.std(y))
    if x_std <= 0 or y_std <= 0:
        return

    n = len(x)
    bw_x = max(1e-6, 1.06 * x_std * (n ** (-1.0 / 5.0)))
    bw_y = max(1e-6, 1.06 * y_std * (n ** (-1.0 / 5.0)))

    x_min, x_max = float(np.min(x)), float(np.max(x))
    y_min, y_max = float(np.min(y)), float(np.max(y))
    x_pad = max(1e-6, 0.05 * max(1e-6, x_max - x_min))
    y_pad = max(1e-6, 0.05 * max(1e-6, y_max - y_min))

    gx = np.linspace(x_min - x_pad, x_max + x_pad, gridsize)
    gy = np.linspace(y_min - y_pad, y_max + y_pad, gridsize)
    xv, yv = np.meshgrid(gx, gy)

    dx = (xv[..., None] - x[None, None, :]) / bw_x
    dy = (yv[..., None] - y[None, None, :]) / bw_y
    density = np.exp(-0.5 * (dx * dx + dy * dy)).sum(axis=2)
    density /= n * 2.0 * np.pi * bw_x * bw_y

    if not np.isfinite(density).all():
        return
    d_min = float(np.min(density))
    d_max = float(np.max(density))
    if d_max <= d_min:
        return

    level_values = np.linspace(float(np.percentile(density, 35)), d_max, levels)
    level_values = np.unique(level_values)
    if len(level_values) < 2:
        level_values = np.linspace(d_min, d_max, levels)

    ax.contourf(xv, yv, density, levels=level_values, cmap="turbo", alpha=0.62, zorder=1)
    ax.contour(
        xv,
        yv,
        density,
        levels=level_values,
        colors="black",
        linewidths=0.9,
        alpha=0.7,
        zorder=2,
    )


def draw_scatter_panel(
    ax: plt.Axes,
    method: str,
    metric: str,
    game_world: str,
    panel_title: str,
    x: np.ndarray,
    y: np.ndarray,
    r: float,
    y_label: str = "ELO",
    show_kde: bool = False,
    point_alpha: float = 0.72,
    point_size: float = 26.0,
    show_ols: bool = True,
    x_label: str | None = None,
) -> None:
    if show_kde:
        draw_2d_kde(ax, x, y)

    ax.scatter(x, y, alpha=point_alpha, s=point_size, edgecolors="none")

    if show_ols and len(np.unique(x)) >= 2:
        slope, intercept = np.polyfit(x, y, 1)
        x_fit = np.linspace(float(np.min(x)), float(np.max(x)), num=120)
        y_fit = slope * x_fit + intercept
        ax.plot(x_fit, y_fit, color="tab:red", linewidth=2.0, label="OLS fit")
        ax.legend(loc="lower right", fontsize=8)

    ax.set_xlabel(x_label if x_label is not None else metric)
    ax.set_ylabel(y_label)
    ax.set_title(panel_title)
    ax.grid(alpha=0.25)
    ax.text(
        0.02,
        0.98,
        # f"r={r:.3f}\nr^2={r * r:.3f}\nn={len(x)}",
        f"r={r:.3f}\nn={len(x)}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
    )


def slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")
    return slug or "plot"


def save_metric_method_scatter_grid(
    out_path: Path,
    method: str,
    metric: str,
    game_world_order: list[str],
    by_game_world: dict[str, tuple[np.ndarray, np.ndarray, float, float]],
    ncols: int = 3,
) -> int:
    if not game_world_order:
        return 0
    n = len(game_world_order)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 5.4, nrows * 4.2), squeeze=False)

    for idx, game_world in enumerate(game_world_order):
        ax = axes[idx // ncols][idx % ncols]
        payload = by_game_world.get(game_world)
        if payload is None:
            ax.set_title(GAME_WORLD_TO_COL_NAME.get(game_world, game_world))
            ax.text(0.5, 0.5, "no data", transform=ax.transAxes, ha="center", va="center", fontsize=9)
            ax.grid(alpha=0.2)
            continue
        x, y, r, _r2 = payload
        panel_title = GAME_WORLD_TO_COL_NAME.get(game_world, game_world)
        draw_scatter_panel(ax, method, metric, game_world, panel_title, x, y, r)

    for idx in range(n, nrows * ncols):
        axes[idx // ncols][idx % ncols].set_visible(False)

    fig.suptitle(f"{metric} vs ELO | {method}", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return n


def save_metric_method_scatter_all_games(
    out_path: Path,
    method: str,
    metric: str,
    by_game_world: dict[str, tuple[np.ndarray, np.ndarray, float, float]],
    x_mode: str = "normalized",
    y_mode: str = "rank",
) -> int:
    if not by_game_world:
        return 0
    x_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    for x, y, _r, _r2 in by_game_world.values():
        if len(x) > 0 and len(y) > 0:
            if x_mode == "normalized":
                x_min = float(np.min(x))
                x_max = float(np.max(x))
                span = x_max - x_min
                if span > 0:
                    x_use = (x - x_min) / span
                else:
                    x_use = np.zeros_like(x, dtype=float)
            else:
                x_use = x

            y_use = rankdata(y) if y_mode == "rank" else y
            x_parts.append(x_use)
            y_parts.append(y_use)
    if not x_parts:
        return 0

    x_all = np.concatenate(x_parts)
    y_all = np.concatenate(y_parts)
    r_all = corr_value(x_all, y_all, method)
    r_display = float(r_all) if np.isfinite(r_all) else float("nan")

    x_label = f"{metric} (normalized 0-1)" if x_mode == "normalized" else metric
    y_label = "ELO Rank (per game)" if y_mode == "rank" else "ELO"
    title_parts = ["All Games"]
    if y_mode == "rank":
        title_parts.append("Per-Game ELO Rank")
    if x_mode == "normalized":
        title_parts.append("Per-Game X Normalized")
    panel_title = " (" + ", ".join(title_parts[1:]) + ")" if len(title_parts) > 1 else ""
    panel_title = title_parts[0] + panel_title

    fig, ax = plt.subplots(figsize=(6.8, 5.2))
    draw_scatter_panel(
        ax=ax,
        method=method,
        metric=metric,
        game_world="all_games",
        panel_title=panel_title,
        x=x_all,
        y=y_all,
        r=r_display,
        y_label=y_label,
        show_kde=True,
        point_alpha=0.2,
        point_size=6,
        show_ols=False,
        x_label=x_label,
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return len(x_all)


def write_scatter_log_lines(
    log_path: Path,
    entries: list[tuple[str, str, str, np.ndarray, np.ndarray, float, float]],
) -> None:
    logger = logging.getLogger(f"strategy_boxplots.scatter.{log_path}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)

    ordered = sorted(entries, key=lambda item: (item[0], item[1], item[2]))
    for method, metric, game_world, x, _y, r, r2 in ordered:
        logger.info(
            f"method={method} metric={metric} game_world={game_world} n={len(x)} r={r:.3f} r2={r2:.3f}"
        )
    handler.close()
    logger.removeHandler(handler)


def compute_metric_game_scores(
    runs: list[dict],
    elo_by_bot_game: dict[tuple[str, str], float],
    corr_method: str,
) -> tuple[dict[str, list[float]], list[tuple[str, str, np.ndarray, np.ndarray, float, float]]]:
    metric_game_points: dict[str, dict[str, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))

    for run in runs:
        metrics = run.get("metrics")
        if not isinstance(metrics, dict):
            continue
        game = run.get("game")
        world = run.get("world")
        model = run.get("model")
        run_id = run.get("run")
        if not all([game, world, model, run_id]):
            continue

        elo_col = [col for g, w, col, _ in MAIN_GAMES_WORLD_COLUMNS if g == game and w == world]
        assert len(elo_col) <= 1, f"Expected at most 1 game, got {len(elo_col)}: {elo_col}"
        if not elo_col:
            continue
        elo_col = elo_col[0]
        bot = f"{model}/{run_id}"
        elo = elo_by_bot_game.get((bot, elo_col))
        if elo is None:
            continue

        game_world = f"{game}:{world}"
        for metric, raw_value in metrics.items():
            metric_val = to_float(raw_value)
            if metric_val is not None:
                metric_game_points[metric][game_world].append((metric_val, elo))

    metric_to_scores: dict[str, list[float]] = defaultdict(list)
    per_game_corrs: list[tuple[str, str, np.ndarray, np.ndarray, float, float]] = []
    for metric, by_game_world in metric_game_points.items():
        for game_world, points in by_game_world.items():
            if len(points) < 2:
                continue
            x = np.array([p[0] for p in points], dtype=float)
            y = np.array([p[1] for p in points], dtype=float)
            r = corr_value(x, y, corr_method)
            if np.isfinite(r):
                r2 = float(r * r)
                metric_to_scores[metric].append(r2)
                per_game_corrs.append((metric, game_world, x, y, float(r), r2))
    return metric_to_scores, per_game_corrs


def main() -> None:
    args = parse_args()
    methods = args.corr_methods
    assert methods, "At least one method is required"
    runs = load_runs(args.runs)
    elo_by_bot_game = load_elo(args.elo_csv)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    combined: list[tuple[str, str, list[float], float]] = []
    eligible_metric_scatter_corrs: list[tuple[str, str, str, np.ndarray, np.ndarray, float, float]] = []
    eligible_metric_groups: dict[tuple[str, str], dict[str, tuple[np.ndarray, np.ndarray, float, float]]] = {}
    all_game_worlds: set[str] = set()
    scatter_dir = args.scatter_dir or (args.out.parent / f"{args.out.stem}_scatter_plots")
    scatter_log = args.scatter_log or (args.out.parent / f"{args.out.stem}_scatter.log")
    for method in methods:
        metric_to_scores, per_game_corrs = compute_metric_game_scores(runs, elo_by_bot_game, method)
        per_game_by_metric: dict[str, list[tuple[str, np.ndarray, np.ndarray, float, float]]] = defaultdict(list)
        for metric, game_world, x, y, r, r2 in per_game_corrs:
            all_game_worlds.add(game_world)
            per_game_by_metric[metric].append((game_world, x, y, r, r2))
        for metric, values in metric_to_scores.items():
            if not values:
                continue
            med = float(np.mean(values))
            if med > args.median_threshold:
                combined.append((method, metric, values, med))
                group: dict[str, tuple[np.ndarray, np.ndarray, float, float]] = {}
                for game_world, x, y, r, r2 in per_game_by_metric.get(metric, []):
                    eligible_metric_scatter_corrs.append((method, metric, game_world, x, y, r, r2))
                    group[game_world] = (x, y, r, r2)
                eligible_metric_groups[(method, metric)] = group

    if combined:
        method_order = {method: idx for idx, method in enumerate(methods)}
        combined.sort(key=lambda item: (method_order[item[0]], -item[3], item[1]))
        labels = [f"{metric} | {method}\nmed={med:.2f}" for method, metric, _, med in combined]
        data = [values for _, _, values, _ in combined]

        fig, ax = plt.subplots(figsize=(max(10, len(data) * 1.0), 6))
        ax.boxplot(
            data,
            labels=labels,
            showfliers=True,
            showmeans=True,
            meanprops={"marker": "D", "markerfacecolor": "tab:red", "markeredgecolor": "black", "markersize": 4},
        )
        rng = np.random.default_rng(0)
        jitter_width = 0.08
        for idx, values in enumerate(data, start=1):
            if not values:
                continue
            x = np.full(len(values), idx, dtype=float) + rng.uniform(
                -jitter_width, jitter_width, size=len(values)
            )
            y = np.asarray(values, dtype=float)
            ax.scatter(
                x,
                y,
                s=14,
                alpha=0.45,
                color="tab:blue",
                edgecolors="none",
                zorder=2,
            )
        ax.set_ylabel("r^2")
        ax.set_title("Metric vs ELO: r^2 Across Game Worlds (All Methods)")
        ax.grid(axis="y", alpha=0.3)
        plt.xticks(rotation=55, ha="right")
        fig.tight_layout()
        fig.savefig(args.out, dpi=200)
        plt.close(fig)
        print(f"Saved: {args.out}")
    else:
        print(f"No metrics found with median r^2 > {args.median_threshold:.2f}")

    write_scatter_log_lines(scatter_log, eligible_metric_scatter_corrs)
    print(f"Logged {len(eligible_metric_scatter_corrs)} scatter lines to: {scatter_log}")

    if args.scatter_plots:
        ordered_game_worlds = [f"{g}:{w}" for g, w, _, _ in MAIN_GAMES_WORLD_COLUMNS if f"{g}:{w}" in all_game_worlds]
        for game_world in sorted(all_game_worlds):
            if game_world not in ordered_game_worlds:
                ordered_game_worlds.append(game_world)
        base_index = {game_world: idx for idx, game_world in enumerate(ordered_game_worlds)}
        scatter_dir.mkdir(parents=True, exist_ok=True)
        saved_files = 0
        for method, metric in sorted(eligible_metric_groups.keys(), key=lambda item: (item[0], item[1])):
            group = eligible_metric_groups[(method, metric)]
            ordered_by_r = sorted(
                ordered_game_worlds,
                key=lambda game_world: (
                    0 if game_world in group else 1,
                    -group[game_world][2] if game_world in group else 0.0,
                    base_index.get(game_world, 10**9),
                ),
            )
            out_name = f"{slugify(method)}__{slugify(metric)}__scatter_grid.png"
            out_path = scatter_dir / out_name
            panels = save_metric_method_scatter_grid(
                out_path=out_path,
                method=method,
                metric=metric,
                game_world_order=ordered_by_r,
                by_game_world=group,
                ncols=3,
            )
            print(f"Saved scatter grid ({panels} panels) to: {out_path}")

            out_name_all = f"{slugify(method)}__{slugify(metric)}__scatter_all_games.png"
            out_path_all = scatter_dir / out_name_all
            n_points = save_metric_method_scatter_all_games(
                out_path=out_path_all,
                method=method,
                metric=metric,
                by_game_world=group,
                x_mode=args.all_games_x,
                y_mode=args.all_games_y,
            )
            print(f"Saved combined scatter ({n_points} points) to: {out_path_all}")
            saved_files += 2
        print(f"Saved {saved_files} scatter plot files to: {scatter_dir}")


if __name__ == "__main__":
    main()
