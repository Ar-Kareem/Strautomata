#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import csv
import matplotlib.pyplot as plt
import numpy as np

MAIN_GAMES_WORLD_COLUMNS: list[tuple[str, str, str, str | None]] = [
    ('tic_tac_toe_3d', 'world1', '3D TTT', None),
    ('tic_tac_toe', 'world1', '3x3 TTT', None),
    ('tic_tac_toe', 'world2', '4x4 TTT', None),
    # ('blackjack', 'world1', 'Blackjack', None),
    ('battleships', 'world1', 'Battleships', None),
    ('connect4', 'world1', 'Connect4', None),
    ('lines_of_action', 'world1', 'LoA', None),
    ('mancala', 'world1', 'Mancala', None),
    ('clobber', 'world1', 'Clobber', None),
    ('pentago', 'world1', 'Pentago', None),
    ('amazons', 'world1', 'Amazons', None),
    ('backgammon', 'world1', 'Backgammon', None),
    ('nim', 'world1', 'Nim', None),
    ('othello', 'world1', 'Othello', None),
    ('dots_and_boxes', 'world1', 'Dots&B', None),
    ('breakthrough', 'world1', 'Breakthrough', None),
    ('hex', 'world1', 'Hex', None),
    ('havannah', 'world1', 'Havannah', None),
    ('go', 'world1', 'Go', None),
    ('checkers', 'world1', 'Checkers', None),
    ('chess', 'worlduci1', 'Chess UCI', None),
    # ('chess', 'world1', 'Chess', None),
    # ('go', 'worldmem1', 'Go', None),
]

def map_game_to_elo(game: str | None, world: str | None) -> str | None:
    if not game:
        return None
    col = [col for g, w, col, _ in MAIN_GAMES_WORLD_COLUMNS if g == game and w == world]
    if not col:
        return None
    assert len(col) == 1, f"Expected 1 game, got {len(col)}: {col}"
    return col[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate visuals for strategy analysis summaries.")
    parser.add_argument("--runs", type=Path, default=Path("analysis/strategy_runs.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("analysis/visuals"))
    parser.add_argument("--top-models", type=int, default=30)
    parser.add_argument("--top-tags", type=int, default=12)
    parser.add_argument("--min-runs", type=int, default=1)
    parser.add_argument("--tag-source", choices=["code", "thought"], default="code")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage plots.")
    parser.add_argument("--label-all", action="store_true", help="Label every model on the scatter plot.")
    parser.add_argument("--elos-all", type=Path, default=Path("src/frontend/arena_fe/public/elos_all_bots.csv"))
    parser.add_argument("--no-elo", action="store_true", help="Skip alignment vs ELO plot.")
    parser.add_argument("--game", type=str, default="", help="Filter ELO plots to a specific game.")
    parser.add_argument(
        "--elo-require-signal",
        action="store_true",
        help="Only plot bots with non-zero alignment precision or recall.",
    )
    parser.add_argument(
        "--elo-min-tags",
        type=int,
        default=0,
        help="Minimum total unique tags (code + thought) required to plot a bot.",
    )
    parser.add_argument(
        "--elo-max-code-len",
        type=int,
        default=0,
        help="Maximum code length (chars) to include in code-length vs ELO plot. 0 means no limit.",
    )
    return parser.parse_args()


def load_runs(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def log_r_plot(log_path: Path, game_name: str, filename: str, r_value: float, points_count: int) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    r_text = f"{r_value:.2f}" if np.isfinite(r_value) else "nan"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} | {game_name or 'all'} | {filename} | n={points_count} | r={r_text}\n")


def collect_models(summary: dict[str, Any], min_runs: int) -> list[dict[str, Any]]:
    models = []
    for model, entry in summary.get("by_model", {}).items():
        runs = entry.get("runs", 0)
        if runs < min_runs:
            continue
        alignment = entry.get("alignment", {})
        models.append(
            {
                "model": model,
                "runs": runs,
                "alignment_precision": alignment.get("precision", 0.0),
                "alignment_recall": alignment.get("recall", 0.0),
                "alignment_f1": alignment.get("f1", 0.0),
                "code_tag_counts": entry.get("code_tag_counts", {}),
                "thought_tag_counts": entry.get("thought_tag_counts", {}),
            }
        )
    models.sort(key=lambda x: (-x["runs"], x["model"]))
    return models


def overall_tag_counts(models: list[dict[str, Any]], key: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for model in models:
        for tag, count in model.get(key, {}).items():
            if not count:
                continue
            totals[tag] = totals.get(tag, 0) + count
    return totals


def top_n_tags(totals: dict[str, int], top_n: int) -> list[str]:
    ordered = sorted(totals.items(), key=lambda x: (-x[1], x[0]))
    return [tag for tag, _ in ordered[:top_n]]


def draw_alignment_scatter(models: list[dict[str, Any]], out_dir: Path, label_all: bool) -> None:
    if not models:
        return
    runs = np.array([m["runs"] for m in models])
    x = np.array([m["alignment_precision"] for m in models])
    y = np.array([m["alignment_recall"] for m in models])

    fig, ax = plt.subplots(figsize=(9, 6))
    sizes = 20 + (runs / runs.max()) * 180
    scatter = ax.scatter(x, y, s=sizes, c=runs, cmap="viridis", alpha=0.8, edgecolor="k", linewidth=0.4)
    ax.set_xlabel("Alignment Precision")
    ax.set_ylabel("Alignment Recall")
    ax.set_title("Per-Model Thought↔Code Alignment")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.colorbar(scatter, ax=ax, label="Runs")

    if label_all:
        n = max(1, len(models))
        for i, model in enumerate(sorted(models, key=lambda m: m["model"])):
            angle = 2 * np.pi * (i / n)
            radius = 6 + (i % 3) * 3
            dx = radius * np.cos(angle)
            dy = radius * np.sin(angle)
            ax.annotate(
                model["model"],
                (model["alignment_precision"], model["alignment_recall"]),
                textcoords="offset points",
                xytext=(dx, dy),
                fontsize=6,
                alpha=0.8,
            )
    else:
        top_by_runs = sorted(models, key=lambda m: (-m["runs"], m["model"]))[:10]
        for model in top_by_runs:
            ax.annotate(
                model["model"],
                (model["alignment_precision"], model["alignment_recall"]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=7,
            )

    fig.tight_layout()
    fig.savefig(out_dir / "model_alignment_scatter.png", dpi=200)
    plt.close(fig)


def draw_tag_heatmap(
    models: list[dict[str, Any]],
    tags: list[str],
    tag_key: str,
    out_dir: Path,
    title: str,
    filename: str,
) -> None:
    if not models or not tags:
        return
    mat = np.zeros((len(models), len(tags)), dtype=float)
    for i, model in enumerate(models):
        runs = model["runs"] or 1
        counts = model.get(tag_key, {})
        for j, tag in enumerate(tags):
            mat[i, j] = counts.get(tag, 0) / runs

    fig, ax = plt.subplots(figsize=(max(10, len(tags) * 0.7), max(6, len(models) * 0.3)))
    im = ax.imshow(mat, aspect="auto", cmap="magma", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(tags)))
    ax.set_xticklabels(tags, rotation=45, ha="right")
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([m["model"] for m in models])
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label="Tag rate (count / runs)")
    fig.tight_layout()
    fig.savefig(out_dir / filename, dpi=200)
    plt.close(fig)


def draw_stacked_tag_bars(
    models: list[dict[str, Any]],
    tags: list[str],
    tag_key: str,
    out_dir: Path,
    title: str,
    filename: str,
) -> None:
    if not models or not tags:
        return
    fig, ax = plt.subplots(figsize=(max(10, len(models) * 0.4), 6))
    x = np.arange(len(models))
    bottom = np.zeros(len(models))
    for tag in tags:
        values = []
        for model in models:
            runs = model["runs"] or 1
            values.append(model.get(tag_key, {}).get(tag, 0) / runs)
        values = np.array(values)
        ax.bar(x, values, bottom=bottom, label=tag)
        bottom += values
    ax.set_xticks(x)
    ax.set_xticklabels([m["model"] for m in models], rotation=45, ha="right")
    ax.set_ylabel("Tag rate (count / runs)")
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / filename, dpi=200)
    plt.close(fig)


def draw_overall_tag_bars(code_totals: dict[str, int], thought_totals: dict[str, int], out_dir: Path) -> None:
    tags = sorted(set(code_totals) | set(thought_totals))
    if not tags:
        return
    code_counts = np.array([code_totals.get(tag, 0) for tag in tags])
    thought_counts = np.array([thought_totals.get(tag, 0) for tag in tags])

    fig, ax = plt.subplots(figsize=(max(10, len(tags) * 0.6), 6))
    x = np.arange(len(tags))
    width = 0.4
    ax.bar(x - width / 2, code_counts, width, label="Code tags")
    ax.bar(x + width / 2, thought_counts, width, label="Thought tags")
    ax.set_xticks(x)
    ax.set_xticklabels(tags, rotation=45, ha="right")
    ax.set_ylabel("Total tag count")
    ax.set_title("Overall Tag Counts (Code vs Thought)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "overall_tag_counts.png", dpi=200)
    plt.close(fig)


def coverage_stats(runs: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    stats: dict[str, dict[str, int]] = {}

    def add_entry(key: str, has_code: bool, has_thought: bool) -> None:
        if key not in stats:
            stats[key] = {"total": 0, "both": 0, "code_only": 0, "thought_only": 0, "none": 0}
        bucket = stats[key]
        bucket["total"] += 1
        if has_code and has_thought:
            bucket["both"] += 1
        elif has_code:
            bucket["code_only"] += 1
        elif has_thought:
            bucket["thought_only"] += 1
        else:
            bucket["none"] += 1

    for run in runs:
        has_code = bool(run.get("code_tags"))
        has_thought = bool(run.get("thought_tags"))
        add_entry("overall", has_code, has_thought)
        add_entry(run.get("source", "unknown"), has_code, has_thought)

    return stats


def draw_coverage_overall(stats: dict[str, dict[str, int]], out_dir: Path) -> None:
    overall = stats.get("overall")
    if not overall:
        return
    categories = ["both", "code_only", "thought_only", "none"]
    total = overall["total"] or 1
    values = [overall[c] / total for c in categories]

    fig, ax = plt.subplots(figsize=(6, 5))
    bottom = 0.0
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B3"]
    for val, cat, color in zip(values, categories, colors):
        ax.bar(["overall"], [val], bottom=bottom, label=cat, color=color)
        bottom += val
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share of runs")
    ax.set_title("Coverage Breakdown (Overall)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "coverage_overall.png", dpi=200)
    plt.close(fig)


def draw_coverage_by_source(stats: dict[str, dict[str, int]], out_dir: Path) -> None:
    sources = [k for k in stats.keys() if k != "overall"]
    if not sources:
        return
    categories = ["both", "code_only", "thought_only", "none"]
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B3"]

    fig, ax = plt.subplots(figsize=(max(6, len(sources) * 1.4), 5))
    x = np.arange(len(sources))
    bottom = np.zeros(len(sources))
    for cat, color in zip(categories, colors):
        vals = []
        for source in sources:
            total = stats[source]["total"] or 1
            vals.append(stats[source][cat] / total)
        vals = np.array(vals)
        ax.bar(x, vals, bottom=bottom, label=cat, color=color)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(sources)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share of runs")
    ax.set_title("Coverage Breakdown by Source")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "coverage_by_source.png", dpi=200)
    plt.close(fig)


def load_elo_all(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    data: dict[str, dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            return data
        games = header[1:]
        for row in reader:
            if not row:
                continue
            bot = row[0]
            values = []
            per_game: dict[str, float] = {}
            for game, cell in zip(games, row[1:]):
                if not cell or cell == "DNQ":
                    continue
                try:
                    val = float(cell)
                except ValueError:
                    continue
                values.append(val)
                per_game[game] = val
            if values:
                data[bot] = {
                    # "mean": float(np.mean(values)),  does not make sense
                    # "median": float(np.median(values)),  does not make sense
                    "count": float(len(values)),
                    "per_game": per_game,
                }
    return data


def draw_alignment_elo_scatter(
    runs: list[dict[str, Any]],
    elo_all: dict[str, dict[str, float]],
    out_dir: Path,
    log_path: Path,
    game_name: str,
    metric_key: str,
    metric_label: str,
    filename: str,
    require_signal: bool,
    min_tags: int,
) -> None:
    record = {}
    points: list[tuple[float, float, float]] = []
    for run in runs:
        if run.get("source") != "game_arena":
            continue
        code_tags = run.get("code_tags", []) or []
        thought_tags = run.get("thought_tags", []) or []
        if isinstance(code_tags, str):
            code_tags = [t for t in code_tags.split(";") if t]
        if isinstance(thought_tags, str):
            thought_tags = [t for t in thought_tags.split(";") if t]
        total_tags = len(set(code_tags) | set(thought_tags))
        if min_tags and total_tags < min_tags:
            continue
        if require_signal:
            precision = run.get("alignment_precision", 0.0)
            recall = run.get("alignment_recall", 0.0)
            if not (precision or recall):
                continue
        model = run.get("model")
        run_id = run.get("run")
        game = run.get("game")
        world = run.get("world")
        if not model or not run_id or not game:
            continue
        elo_game = map_game_to_elo(game, world)
        if not elo_game:
            continue
        bot = f"{model}/{run_id}"
        elo_entry = elo_all.get(bot)
        if not elo_entry:
            continue
        per_game = elo_entry.get("per_game", {})
        if elo_game not in per_game:
            continue
        record[elo_game + ":" + bot] = (float(run.get(metric_key, 0.0)), float(per_game[elo_game]), float(elo_entry.get("count", 1)))
        points.append((float(run.get(metric_key, 0.0)), float(per_game[elo_game]), float(elo_entry.get("count", 1))))

    if not points:
        return
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    sizes = np.array([p[2] for p in points])
    sizes = 20 + (sizes / sizes.max()) * 180
    r_value = float(np.corrcoef(x, y)[0, 1]) if len(points) > 1 else float("nan")

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(x, y, s=sizes, c=y, cmap="viridis", alpha=0.75, edgecolor="k", linewidth=0.4)
    if len(points) > 1:
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 200)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color="black", linewidth=1.2, linestyle="--")
    ax.set_xlabel(metric_label)
    ax.set_ylabel("ELO (per game)")
    if np.isfinite(r_value):
        ax.set_title(f"{metric_label} vs ELO (Per-Run Games)  r={r_value:.3f}  n={len(points)}")
    else:
        ax.set_title(f"{metric_label} vs ELO (Per-Run Games)  n={len(points)}")
    fig.colorbar(scatter, ax=ax, label="ELO")

    fig.tight_layout()
    fig.savefig(out_dir / filename, dpi=200)
    plt.close(fig)
    log_r_plot(log_path, game_name, filename, r_value, len(points))


def draw_tags_elo_scatter(
    runs: list[dict[str, Any]],
    elo_all: dict[str, dict[str, float]],
    out_dir: Path,
    log_path: Path,
    game_name: str,
    require_signal: bool,
    min_tags: int,
) -> None:
    points: list[tuple[float, float, float]] = []
    for run in runs:
        if run.get("source") != "game_arena":
            continue
        code_tags = run.get("code_tags", []) or []
        thought_tags = run.get("thought_tags", []) or []
        if isinstance(code_tags, str):
            code_tags = [t for t in code_tags.split(";") if t]
        if isinstance(thought_tags, str):
            thought_tags = [t for t in thought_tags.split(";") if t]
        total_tags = len(set(code_tags) | set(thought_tags))
        if min_tags and total_tags < min_tags:
            continue
        if require_signal:
            precision = run.get("alignment_precision", 0.0)
            recall = run.get("alignment_recall", 0.0)
            if not (precision or recall):
                continue
        model = run.get("model")
        run_id = run.get("run")
        game = run.get("game")
        world = run.get("world")
        if not model or not run_id or not game:
            continue
        elo_game = map_game_to_elo(game, world)
        if not elo_game:
            continue
        bot = f"{model}/{run_id}"
        elo_entry = elo_all.get(bot)
        if not elo_entry:
            continue
        per_game = elo_entry.get("per_game", {})
        if elo_game not in per_game:
            continue
        points.append((float(total_tags), float(per_game[elo_game]), float(elo_entry.get("count", 1))))

    if not points:
        return
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    sizes = np.array([p[2] for p in points])
    sizes = 20 + (sizes / sizes.max()) * 180
    r_value = float(np.corrcoef(x, y)[0, 1]) if len(points) > 1 else float("nan")

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(x, y, s=sizes, c=y, cmap="viridis", alpha=0.75, edgecolor="k", linewidth=0.4)
    if len(points) > 1:
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 200)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color="black", linewidth=1.2, linestyle="--")
    ax.set_xlabel("Total Unique Tags Parsed (Code + Thought)")
    ax.set_ylabel("ELO (per game)")
    if np.isfinite(r_value):
        ax.set_title(f"Total Tags vs ELO (Per-Run Games)  r={r_value:.3f}  n={len(points)}")
    else:
        ax.set_title(f"Total Tags vs ELO (Per-Run Games)  n={len(points)}")
    fig.colorbar(scatter, ax=ax, label="ELO")

    fig.tight_layout()
    fig.savefig(out_dir / "tags_vs_elo.png", dpi=200)
    plt.close(fig)
    log_r_plot(log_path, game_name, "tags_vs_elo.png", r_value, len(points))


def draw_codelen_elo_scatter(
    runs: list[dict[str, Any]],
    elo_all: dict[str, dict[str, float]],
    out_dir: Path,
    log_path: Path,
    game_name: str,
    require_signal: bool,
    min_tags: int,
    max_code_len: int,
) -> None:
    points: list[tuple[float, float, float]] = []
    for run in runs:
        if run.get("source") != "game_arena":
            continue
        code_len = int(run.get("code_length") or 0)
        if code_len <= 0:
            continue
        if max_code_len and code_len > max_code_len:
            continue
        code_tags = run.get("code_tags", []) or []
        thought_tags = run.get("thought_tags", []) or []
        if isinstance(code_tags, str):
            code_tags = [t for t in code_tags.split(";") if t]
        if isinstance(thought_tags, str):
            thought_tags = [t for t in thought_tags.split(";") if t]
        total_tags = len(set(code_tags) | set(thought_tags))
        if min_tags and total_tags < min_tags:
            continue
        if require_signal:
            precision = run.get("alignment_precision", 0.0)
            recall = run.get("alignment_recall", 0.0)
            if not (precision or recall):
                continue
        model = run.get("model")
        run_id = run.get("run")
        game = run.get("game")
        world = run.get("world")
        if not model or not run_id or not game:
            continue
        elo_game = map_game_to_elo(game, world)
        if not elo_game:
            continue
        bot = f"{model}/{run_id}"
        elo_entry = elo_all.get(bot)
        if not elo_entry:
            continue
        per_game = elo_entry.get("per_game", {})
        if elo_game not in per_game:
            continue
        points.append((float(code_len), float(per_game[elo_game]), float(elo_entry.get("count", 1))))

    if not points:
        return
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    sizes = np.array([p[2] for p in points])
    sizes = 20 + (sizes / sizes.max()) * 180
    r_value = float(np.corrcoef(x, y)[0, 1]) if len(points) > 1 else float("nan")

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(x, y, s=sizes, c=y, cmap="viridis", alpha=0.75, edgecolor="k", linewidth=0.4)
    if len(points) > 1:
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 200)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color="black", linewidth=1.2, linestyle="--")
    ax.set_xlabel("Code Length (chars)")
    ax.set_ylabel("ELO (per game)")
    if np.isfinite(r_value):
        ax.set_title(f"Code Length vs ELO (Per-Run Games)  r={r_value:.3f}  n={len(points)}")
    else:
        ax.set_title(f"Code Length vs ELO (Per-Run Games)  n={len(points)}")
    fig.colorbar(scatter, ax=ax, label="ELO")

    fig.tight_layout()
    fig.savefig(out_dir / "code_length_vs_elo.png", dpi=200)
    plt.close(fig)
    log_r_plot(log_path, game_name, "code_length_vs_elo.png", r_value, len(points))

def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    r_log_path = out_dir / "r_coefficient_plots.log"

    runs = load_runs(args.runs) if args.runs.exists() else []
    # models = collect_models(summary, args.min_runs)
    # top_models = models[: args.top_models]

    # code_totals = overall_tag_counts(models, "code_tag_counts")
    # thought_totals = overall_tag_counts(models, "thought_tag_counts")
    # top_tags = top_n_tags(code_totals if args.tag_source == "code" else thought_totals, args.top_tags)

    # draw_alignment_scatter(models, out_dir, args.label_all)
    # draw_overall_tag_bars(code_totals, thought_totals, out_dir)

    # draw_tag_heatmap(
    #     top_models,
    #     top_tags,
    #     "code_tag_counts" if args.tag_source == "code" else "thought_tag_counts",
    #     out_dir,
    #     f"Top {len(top_models)} Models: {args.tag_source.title()} Tag Rates",
    #     f"model_tag_heatmap_{args.tag_source}.png",
    # )

    # draw_stacked_tag_bars(
    #     top_models[: min(15, len(top_models))],
    #     top_tags,
    #     "code_tag_counts" if args.tag_source == "code" else "thought_tag_counts",
    #     out_dir,
    #     f"Top {min(15, len(top_models))} Models: {args.tag_source.title()} Tag Mix",
    #     f"model_tag_stacked_{args.tag_source}.png",
    # )

    if not args.no_coverage and runs:
        stats = coverage_stats(runs)
        draw_coverage_overall(stats, out_dir)
        draw_coverage_by_source(stats, out_dir)

    if not args.no_elo and runs:
        runs_for_elo = runs
        if args.game:
            runs_for_elo = [r for r in runs if r.get("game") == args.game]
        elo_all = load_elo_all(args.elos_all)
        draw_alignment_elo_scatter(
            runs_for_elo,
            elo_all,
            out_dir,
            r_log_path,
            args.game,
            "alignment_precision",
            "Alignment Precision",
            "alignment_vs_elo_precision.png",
            args.elo_require_signal,
            args.elo_min_tags,
        )
        draw_alignment_elo_scatter(
            runs_for_elo,
            elo_all,
            out_dir,
            r_log_path,
            args.game,
            "alignment_recall",
            "Alignment Recall",
            "alignment_vs_elo_recall.png",
            args.elo_require_signal,
            args.elo_min_tags,
        )
        draw_alignment_elo_scatter(
            runs_for_elo,
            elo_all,
            out_dir,
            r_log_path,
            args.game,
            "alignment_f1",
            "Alignment F1",
            "alignment_vs_elo_f1.png",
            args.elo_require_signal,
            args.elo_min_tags,
        )
        draw_tags_elo_scatter(
            runs_for_elo,
            elo_all,
            out_dir,
            r_log_path,
            args.game,
            args.elo_require_signal,
            args.elo_min_tags,
        )
        draw_codelen_elo_scatter(
            runs_for_elo,
            elo_all,
            out_dir,
            r_log_path,
            args.game,
            args.elo_require_signal,
            args.elo_min_tags,
            args.elo_max_code_len,
        )


if __name__ == "__main__":
    main()
