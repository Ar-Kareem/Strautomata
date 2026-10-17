#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

from matplotlib import colors
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


GS = [
    ("tic_tac_toe_3d", "world1", "3D TTT", None),
    ("tic_tac_toe", "world1", "3x3 TTT", None),
    ("tic_tac_toe", "world2", "4x4 TTT", None),
    ("battleships", "world1", "Battleships", None),
    ("connect4", "world1", "Connect4", None),
    ("lines_of_action", "world1", "LoA", None),
    ("mancala", "world1", "Mancala", None),
    ("clobber", "world1", "Clobber", None),
    ("pentago", "world1", "Pentago", None),
    ("amazons", "world1", "Amazons", None),
    ("backgammon", "world1", "Backgammon", None),
    ("nim", "world1", "Nim", None),
    ("othello", "world1", "Othello", None),
    ("dots_and_boxes", "world1", "Dots&B", None),
    ("breakthrough", "world1", "Breakthrough", None),
    ("hex", "world1", "Hex", None),
    ("havannah", "world1", "Havannah", None),
    ("go", "world1", "Go", None),
    ("checkers", "world1", "Checkers", None),
    ("chess", "worlduci1", "Chess UCI", None),
]

CSV_COL_TO_GAME_WORLD = {csv_col: (game, world) for game, world, csv_col, _ in GS}
ARENA_PURPLE = "#6c4ca8"
ARENA_PURPLE_DARK = "#2b164f"
ARENA_PURPLE_MID = "#a586d1"
ARENA_PURPLE_LIGHT = "#ddd0f2"
ELO_CMAP = colors.LinearSegmentedColormap.from_list(
    "arena_elo",
    [ARENA_PURPLE_LIGHT, ARENA_PURPLE_MID, ARENA_PURPLE],
)
RANK_CMAP = colors.LinearSegmentedColormap.from_list(
    "arena_rank",
    [ARENA_PURPLE_DARK, "#9f82cb", "#d8c8f0"],
)


@dataclass(frozen=True)
class BotRef:
    bot_id: str
    game: str
    world: str
    model_name: str


@dataclass(frozen=True)
class BotMetadata:
    actual_cost: float | None
    output_len: int | None


@dataclass(frozen=True)
class CellValue:
    ref: BotRef
    column_name: str
    value: float


@dataclass(frozen=True)
class PlotPoint:
    ref: BotRef
    column_name: str
    cost: float
    value: float
    cost_source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot per-bot generation cost vs per-game ELO and rank for every non-empty cell in an ELO CSV."
    )
    parser.add_argument(
        "--elos-csv",
        type=Path,
        required=True,
        help="Path to an ELO CSV such as analysis_2/elos_all_bots.csv.",
    )
    parser.add_argument(
        "--ranking-csv",
        type=Path,
        default=Path("analysis_2/ranking_all_bots.csv"),
        help="Path to a ranking CSV such as analysis_2/ranking_all_bots.csv.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Optional explicit output directory. Default: analysis_2/cost under the repo root.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root. Defaults to the repo root.",
    )
    return parser.parse_args()


def _resolve_input_path(root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    cwd_candidate = (Path.cwd() / path).resolve()
    if cwd_candidate.exists():
        return cwd_candidate
    return (root / path).resolve()


def _resolve_output_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else (root / path).resolve()


def _infer_default_out_dir(root: Path) -> Path:
    return root / "analysis_2" / "cost"


def _extract_cost(payload: dict[str, Any]) -> float | None:
    usage = payload.get("usage")
    if isinstance(usage, dict):
        for key in ("cost", "total_cost", "cost_total"):
            value = usage.get(key)
            if value is None:
                continue
            try:
                cost = float(value)
            except (TypeError, ValueError):
                continue
            if np.isfinite(cost):
                return cost
    for key in ("cost", "total_cost", "cost_total"):
        value = payload.get(key)
        if value is None:
            continue
        try:
            cost = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(cost):
            return cost
    return None


def _make_bot_ref(game: str, world: str, bot_id: str) -> BotRef:
    model_name = bot_id.split("/", 1)[0] if "/" in bot_id else bot_id
    return BotRef(bot_id=bot_id, game=game, world=world, model_name=model_name)


def _bot_dir(root: Path, ref: BotRef) -> Path | None:
    if "/" not in ref.bot_id:
        return None
    model_name, run_id = ref.bot_id.split("/", 1)
    return root / "src" / "game_arena" / ref.game / "examples" / ref.world / model_name / run_id


def _extract_output_len_from_json(raw_text: str) -> int:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return len(raw_text)
    if isinstance(payload, dict):
        for key in ("output", "response", "text", "completion", "content"):
            value = payload.get(key)
            if isinstance(value, str):
                return len(value)
    return len(raw_text)


def _load_bot_metadata(
    root: Path,
    ref: BotRef,
    cache: dict[BotRef, BotMetadata],
) -> BotMetadata:
    if ref in cache:
        return cache[ref]

    bot_dir = _bot_dir(root, ref)
    if bot_dir is None:
        metadata = BotMetadata(actual_cost=None, output_len=None)
        cache[ref] = metadata
        return metadata

    info_path = bot_dir / "0.info.json"
    actual_cost = None
    if info_path.exists():
        try:
            payload = json.loads(info_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            actual_cost = _extract_cost(payload)

    output_len = None
    output_txt_path = bot_dir / "1.output.txt"
    output_json_path = bot_dir / "1.output.json"
    if output_txt_path.exists():
        try:
            output_len = len(output_txt_path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            output_len = None
    elif output_json_path.exists():
        try:
            output_len = _extract_output_len_from_json(output_json_path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            output_len = None

    metadata = BotMetadata(actual_cost=actual_cost, output_len=output_len)
    cache[ref] = metadata
    return metadata


def _load_cells(csv_path: Path, *, skip_columns: set[str] | None = None) -> tuple[list[CellValue], int]:
    skip_columns = skip_columns or set()
    cells: list[CellValue] = []
    unmapped_columns = 0

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            raise ValueError(f"CSV is empty: {csv_path}")
        rows = list(reader)

        for column_index, column_name in enumerate(header[1:], start=1):
            if column_name in skip_columns:
                continue
            if column_name not in CSV_COL_TO_GAME_WORLD:
                for row in rows:
                    if column_index < len(row) and row[column_index].strip():
                        unmapped_columns += 1
                continue
            game, world = CSV_COL_TO_GAME_WORLD[column_name]
            for row in rows:
                if not row:
                    continue
                bot_id = row[0].strip()
                if not bot_id or column_index >= len(row):
                    continue
                value_text = row[column_index].strip()
                if not value_text:
                    continue
                try:
                    value = float(value_text)
                except ValueError:
                    continue
                cells.append(
                    CellValue(
                        ref=_make_bot_ref(game, world, bot_id),
                        column_name=column_name,
                        value=value,
                    )
                )
    return cells, unmapped_columns


def _build_metadata_cache(root: Path, refs: Iterable[BotRef]) -> dict[BotRef, BotMetadata]:
    metadata_cache: dict[BotRef, BotMetadata] = {}
    for ref in refs:
        _load_bot_metadata(root, ref, metadata_cache)
    return metadata_cache


def _build_model_rate_stats(
    metadata_cache: dict[BotRef, BotMetadata],
) -> tuple[dict[str, float], dict[str, int]]:
    rate_sum_by_model: dict[str, float] = {}
    rate_count_by_model: dict[str, int] = {}
    for ref, metadata in metadata_cache.items():
        if metadata.actual_cost is None or metadata.output_len is None or metadata.output_len <= 0:
            continue
        rate = metadata.actual_cost / float(metadata.output_len)
        if not np.isfinite(rate):
            continue
        rate_sum_by_model[ref.model_name] = rate_sum_by_model.get(ref.model_name, 0.0) + rate
        rate_count_by_model[ref.model_name] = rate_count_by_model.get(ref.model_name, 0) + 1
    return rate_sum_by_model, rate_count_by_model


def _predict_cost(
    ref: BotRef,
    metadata_cache: dict[BotRef, BotMetadata],
    rate_sum_by_model: dict[str, float],
    rate_count_by_model: dict[str, int],
    *,
    leave_one_out: bool = False,
) -> float | None:
    metadata = metadata_cache.get(ref)
    if metadata is None or metadata.output_len is None or metadata.output_len <= 0:
        return None

    rate_sum = rate_sum_by_model.get(ref.model_name, 0.0)
    rate_count = rate_count_by_model.get(ref.model_name, 0)

    if leave_one_out and metadata.actual_cost is not None:
        own_rate = metadata.actual_cost / float(metadata.output_len)
        if np.isfinite(own_rate):
            rate_sum -= own_rate
            rate_count -= 1

    if rate_count <= 0:
        return None

    predicted_cost = float(metadata.output_len) * (rate_sum / float(rate_count))
    if not np.isfinite(predicted_cost):
        return None
    return predicted_cost


def _build_plot_points(
    cells: Iterable[CellValue],
    metadata_cache: dict[BotRef, BotMetadata],
    rate_sum_by_model: dict[str, float],
    rate_count_by_model: dict[str, int],
) -> tuple[list[PlotPoint], int, int, int]:
    points: list[PlotPoint] = []
    actual_count = 0
    predicted_count = 0
    missing_count = 0

    for cell in cells:
        metadata = metadata_cache.get(cell.ref)
        if metadata is None:
            missing_count += 1
            continue

        if metadata.actual_cost is not None and np.isfinite(metadata.actual_cost):
            points.append(
                PlotPoint(
                    ref=cell.ref,
                    column_name=cell.column_name,
                    cost=float(metadata.actual_cost),
                    value=cell.value,
                    cost_source="actual",
                )
            )
            actual_count += 1
            continue

        predicted_cost = _predict_cost(cell.ref, metadata_cache, rate_sum_by_model, rate_count_by_model)
        if predicted_cost is None:
            missing_count += 1
            continue
        points.append(
            PlotPoint(
                ref=cell.ref,
                column_name=cell.column_name,
                cost=predicted_cost,
                value=cell.value,
                cost_source="predicted",
            )
        )
        predicted_count += 1

    return points, actual_count, predicted_count, missing_count


def _build_cost_errors(
    metadata_cache: dict[BotRef, BotMetadata],
    rate_sum_by_model: dict[str, float],
    rate_count_by_model: dict[str, int],
) -> tuple[np.ndarray, int, int]:
    errors: list[float] = []
    with_actual_cost = 0
    without_prediction = 0

    for ref, metadata in metadata_cache.items():
        if metadata.actual_cost is None:
            continue
        with_actual_cost += 1
        predicted_cost = _predict_cost(
            ref,
            metadata_cache,
            rate_sum_by_model,
            rate_count_by_model,
            leave_one_out=True,
        )
        if predicted_cost is None:
            without_prediction += 1
            continue
        error_value = float(metadata.actual_cost) - predicted_cost
        if np.isfinite(error_value):
            errors.append(error_value)

    return np.array(errors, dtype=float), with_actual_cost, without_prediction


def _plot(
    x: np.ndarray,
    y: np.ndarray,
    out_pdf: Path,
    *,
    title: str,
    y_label: str,
    x_label: str = "Automata Cost ($)",
    cmap: str | colors.Colormap = ELO_CMAP,
    invert_y: bool = False,
    color_center: float | None = None,
    annotations: list[tuple[float, float, str, float, float, str]] | None = None,
    figsize: tuple[float, float] = (8, 6),
) -> None:
    fig, ax = plt.subplots(figsize=figsize)
    finite_mask = np.isfinite(x) & np.isfinite(y) & (x > 0)
    x_plot = x[finite_mask]
    y_plot = y[finite_mask]
    norm = None
    if color_center is not None and len(y_plot) > 0:
        y_min = float(np.min(y_plot))
        y_max = float(np.max(y_plot))
        if y_min < color_center < y_max:
            norm = colors.TwoSlopeNorm(vmin=y_min, vcenter=color_center, vmax=y_max)
    scatter = ax.scatter(
        x_plot,
        y_plot,
        c=y_plot,
        cmap=cmap,
        norm=norm,
        s=30,
        alpha=0.84,
        edgecolor="black",
        linewidth=0.35,
    )

    if len(x_plot) >= 2:
        log_x = np.log10(x_plot)
        slope, intercept = np.polyfit(log_x, y_plot, 1)
        x_line = np.geomspace(x_plot.min(), x_plot.max(), 200)
        y_line = slope * np.log10(x_line) + intercept
        r_value = float(np.corrcoef(log_x, y_plot)[0, 1])
        ax.plot(x_line, y_line, color="black", linestyle="--", linewidth=1.2)
        if np.isfinite(r_value):
            ax.text(
                0.02,
                0.98,
                f"r={r_value:.3f}",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=10,
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
            )

    x_min = float(np.min(x_plot)) if len(x_plot) > 0 else 0.01
    x_max = float(np.max(x_plot)) if len(x_plot) > 0 else 1.0
    y_min = float(np.min(y_plot)) if len(y_plot) > 0 else 0.0
    y_max = float(np.max(y_plot)) if len(y_plot) > 0 else 1.0
    x_pad_factor = 1.18
    y_pad = max((y_max - y_min) * 0.08, 10.0)

    if annotations:
        for x_val, y_val, label, dx, dy, ha in annotations:
            ax.annotate(
                "",
                (x_val, y_val),
                xytext=(dx, dy),
                textcoords="offset points",
                ha=ha,
                va="center",
                arrowprops={
                    "arrowstyle": "-",
                    "color": "black",
                    "lw": 0.45,
                    "alpha": 0.5,
                    "shrinkA": 0,
                    "shrinkB": 2,
                },
            )
            text_artist = ax.annotate(
                label,
                (x_val, y_val),
                xytext=(dx, dy),
                textcoords="offset points",
                ha=ha,
                va="center",
                fontsize=8,
            )
            text_artist.set_path_effects(
                [
                    pe.withStroke(linewidth=2.8, foreground="white", alpha=0.9),
                ]
            )

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xscale("log")
    ax.grid(axis="y", alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if invert_y:
        if len(y_plot) > 0:
            ax.set_ylim(float(np.max(y_plot)) + 0.5, -5.0)
            ax.set_yticks([tick for tick in ax.get_yticks() if tick >= 0])
        else:
            ax.invert_yaxis()
    else:
        ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_xlim(x_min / x_pad_factor, x_max * x_pad_factor)
    fig.tight_layout()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf)
    plt.close(fig)


def _plot_cost_error_histogram(errors: np.ndarray, out_pdf: Path, *, bin_width: float = 0.05) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    data_min = float(np.min(errors))
    data_max = float(np.max(errors))
    start = bin_width * np.floor(data_min / bin_width)
    stop = bin_width * np.ceil(data_max / bin_width)
    if np.isclose(start, stop):
        start -= bin_width
        stop += bin_width
    bins = np.arange(start, stop + bin_width, bin_width)
    if len(bins) < 2:
        bins = np.array([start, start + bin_width], dtype=float)

    ax.hist(errors, bins=bins, color=ARENA_PURPLE, alpha=0.85, edgecolor="black", linewidth=0.6)
    ax.axvline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_xlabel("Actual Cost - Predicted Cost")
    ax.set_ylabel("Bot Count")
    ax.set_title("Cost Prediction Error Histogram")
    ax.grid(axis="y", alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    elos_csv = _resolve_input_path(root, args.elos_csv)
    ranking_csv = _resolve_input_path(root, args.ranking_csv)
    out_dir = _resolve_output_path(root, args.out_dir) if args.out_dir is not None else _infer_default_out_dir(root)

    elo_cells, elo_unmapped_columns = _load_cells(elos_csv, skip_columns={"Median ELO"})
    rank_cells, rank_unmapped_columns = _load_cells(ranking_csv)

    unique_refs = {cell.ref for cell in elo_cells}
    unique_refs.update(cell.ref for cell in rank_cells)
    metadata_cache = _build_metadata_cache(root, unique_refs)
    rate_sum_by_model, rate_count_by_model = _build_model_rate_stats(metadata_cache)

    elo_points, elo_actual_cost, elo_predicted_cost, elo_without_cost = _build_plot_points(
        elo_cells,
        metadata_cache,
        rate_sum_by_model,
        rate_count_by_model,
    )
    rank_points, rank_actual_cost, rank_predicted_cost, rank_without_cost = _build_plot_points(
        rank_cells,
        metadata_cache,
        rate_sum_by_model,
        rate_count_by_model,
    )
    cost_errors, cost_error_actual_bots, cost_error_without_prediction = _build_cost_errors(
        metadata_cache,
        rate_sum_by_model,
        rate_count_by_model,
    )

    print(f"models_with_cost_rate={len(rate_count_by_model)}")
    print(f"elo_points_total={len(elo_cells)}")
    print(f"elo_points_actual_cost={elo_actual_cost}")
    print(f"elo_points_predicted_cost={elo_predicted_cost}")
    print(f"elo_points_without_cost={elo_without_cost}")
    print(f"elo_unmapped_column_cells={elo_unmapped_columns}")
    print(f"rank_points_total={len(rank_cells)}")
    print(f"rank_points_actual_cost={rank_actual_cost}")
    print(f"rank_points_predicted_cost={rank_predicted_cost}")
    print(f"rank_points_without_cost={rank_without_cost}")
    print(f"rank_unmapped_column_cells={rank_unmapped_columns}")
    print(f"cost_error_actual_bots={cost_error_actual_bots}")
    print(f"cost_error_points={len(cost_errors)}")
    print(f"cost_error_without_prediction={cost_error_without_prediction}")

    if not elo_points:
        raise ValueError("No per-cell bot entries had both a cost and an ELO value; nothing to plot for ELO.")
    if not rank_points:
        raise ValueError("No per-cell bot entries had both a cost and a rank value; nothing to plot for rank.")
    if len(cost_errors) == 0:
        raise ValueError("No bots had both an actual cost and a leave-one-out predicted cost; nothing to plot for cost error.")

    elo_points_only_real = [point for point in elo_points if point.cost_source == "actual"]
    rank_points_only_real = [point for point in rank_points if point.cost_source == "actual"]
    chess_uci_elo_points = [point for point in elo_points if point.column_name == "Chess UCI"]

    print(f"elo_points_only_real={len(elo_points_only_real)}")
    print(f"rank_points_only_real={len(rank_points_only_real)}")
    print(f"chess_uci_elo_points={len(chess_uci_elo_points)}")

    x_cost_elo = np.array([point.cost for point in elo_points], dtype=float)
    y_elo = np.array([point.value for point in elo_points], dtype=float)
    x_cost_rank = np.array([point.cost for point in rank_points], dtype=float)
    y_rank = np.array([point.value for point in rank_points], dtype=float)
    x_cost_elo_only_real = np.array([point.cost for point in elo_points_only_real], dtype=float)
    y_elo_only_real = np.array([point.value for point in elo_points_only_real], dtype=float)
    x_cost_rank_only_real = np.array([point.cost for point in rank_points_only_real], dtype=float)
    y_rank_only_real = np.array([point.value for point in rank_points_only_real], dtype=float)
    x_cost_chess_uci_elo = np.array([point.cost for point in chess_uci_elo_points], dtype=float)
    y_chess_uci_elo = np.array([point.value for point in chess_uci_elo_points], dtype=float)
    global_elo_mean = float(np.mean([cell.value for cell in elo_cells]))

    out_dir.mkdir(parents=True, exist_ok=True)
    elo_pdf = out_dir / f"{elos_csv.stem}_cost_vs_elo.pdf"
    rank_pdf = out_dir / f"{ranking_csv.stem}_cost_vs_rank.pdf"
    elo_only_real_pdf = out_dir / f"{elos_csv.stem}_cost_vs_elo_only_real.pdf"
    rank_only_real_pdf = out_dir / f"{ranking_csv.stem}_cost_vs_rank_only_real.pdf"
    chess_uci_elo_pdf = out_dir / f"{elos_csv.stem}_cost_vs_elo_chess_uci_only.pdf"
    cost_error_pdf = out_dir / "cost_error_histogram.pdf"

    _plot(
        x_cost_elo,
        y_elo,
        elo_pdf,
        title="Automata Cost vs ELO",
        y_label="ELO",
        cmap=ELO_CMAP,
        color_center=global_elo_mean,
    )
    _plot(
        x_cost_rank,
        y_rank,
        rank_pdf,
        title="Automata Cost vs Rank",
        y_label="ELO Rank per game",
        cmap=RANK_CMAP,
        invert_y=True,
    )
    _plot(
        x_cost_elo_only_real,
        y_elo_only_real,
        elo_only_real_pdf,
        title="Automata Cost vs ELO",
        y_label="ELO",
        cmap=ELO_CMAP,
        color_center=global_elo_mean,
    )
    _plot(
        x_cost_rank_only_real,
        y_rank_only_real,
        rank_only_real_pdf,
        title="Automata Cost vs Rank",
        y_label="ELO Rank per game",
        cmap=RANK_CMAP,
        invert_y=True,
    )
    if len(chess_uci_elo_points) > 0:
        # Label bots on the cost/ELO Pareto frontier (no other bot is both cheaper-or-equal and
        # stronger-or-equal with at least one strict improvement) that also reach >= 2000 ELO.
        def _is_pareto_dominated(candidate) -> bool:
            for other in chess_uci_elo_points:
                if other is candidate:
                    continue
                if other.cost <= candidate.cost and other.value >= candidate.value and (
                    other.cost < candidate.cost or other.value > candidate.value
                ):
                    return True
            return False

        selected_chess_uci = sorted(
            [
                point
                for point in chess_uci_elo_points
                if float(point.value) >= 2000.0 and not _is_pareto_dominated(point)
            ],
            key=lambda point: point.cost,
        )
        chess_y_min = min(float(point.value) for point in chess_uci_elo_points)
        chess_y_max = max(float(point.value) for point in chess_uci_elo_points)
        chess_y_span = max(chess_y_max - chess_y_min, 1.0)
        # Per-bot label placement: (dx points, dy points, horizontal alignment).
        chess_uci_label_offsets = {
            'muse_spark_1.3/005': (-8, 8, 'right'),
            'muse_spark_1.3/004': (-8, 10, 'right'),
            'gpt_5.4_medium/003': (8, -10, 'left'),
            'gpt_5.4_high/002': (-8, 8, 'right'),
            'gpt_6_astra_high/004': (-8, 0, 'right'),
            'gpt_6_astra_high/001': (-6, 12, 'right'),
        }
        chess_uci_annotations = [
            (
                float(point.cost),
                float(point.value),
                point.ref.bot_id,
                *chess_uci_label_offsets.get(point.ref.bot_id, (8, 0, 'left')),
            )
            for point in selected_chess_uci
        ]
        for point in selected_chess_uci:
            print(f"chess_uci_label={point.ref.bot_id} cost={float(point.cost):.4f} elo={float(point.value):.0f}")
        _plot(
            x_cost_chess_uci_elo,
            y_chess_uci_elo,
            chess_uci_elo_pdf,
            title="Chess Automata Cost vs ELO",
            y_label="ELO",
            x_label="Chess Automata Cost ($)",
            cmap=ELO_CMAP,
            color_center=global_elo_mean,
            annotations=chess_uci_annotations,
            figsize=(7.1, 5.2),
        )
    _plot_cost_error_histogram(cost_errors, cost_error_pdf, bin_width=0.05)
    print(f"wrote_pdf={elo_pdf}")
    print(f"wrote_pdf={rank_pdf}")
    print(f"wrote_pdf={elo_only_real_pdf}")
    print(f"wrote_pdf={rank_only_real_pdf}")
    if len(chess_uci_elo_points) > 0:
        print(f"wrote_pdf={chess_uci_elo_pdf}")
    print(f"wrote_pdf={cost_error_pdf}")


if __name__ == "__main__":
    main()
