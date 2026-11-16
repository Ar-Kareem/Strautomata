#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
import pickle

import matplotlib.pyplot as plt
import numpy as np


GS = [
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

ELO_GAME_MAP = {(game, world): col for game, world, col, _ in GS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot code length vs per-game ELO from CSV and example code files."
    )
    parser.add_argument("--game", required=True, help="Game id (e.g., chess, go) or ALL.")
    parser.add_argument("--world", required=True, help="World id (e.g., world1, worlduci1). Ignored when --game ALL.")
    parser.add_argument(
        "--x-axis",
        choices=["code", "thinking"],
        default="code",
        help="X-axis metric: code length or thinking length (output length minus code length).",
    )
    parser.add_argument(
        "--remove-comments",
        action="store_true",
        help="Exclude lines starting with optional whitespace then # from code length.",
    )
    parser.add_argument(
        "--ignore-corr",
        action="store_true",
        help="Hide correlation regression line and r value in the plot.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root (defaults to repo root).",
    )
    parser.add_argument(
        "--elos-csv",
        type=Path,
        default=None,
        help="Path to elos_all_bots.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("analysis_2"),
        help="Output directory for the plot.",
    )
    parser.add_argument(
        "--extension",
        type=str,
        default="png",
        help="Extension for the output plot.",
    )
    return parser.parse_args()


def map_game_to_elo(game: str, world: str) -> str | None:
    return ELO_GAME_MAP.get((game, world))

def format_game_title(game: str) -> str:
    return game.replace("_", " ").title()


def load_elo_csv(path: Path) -> dict[str, dict[str, float]]:
    data: dict[str, dict[str, float]] = {}
    if not path.exists():
        return data
    # print(f"reading {path}")
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
            per_game: dict[str, float] = {}
            for game, cell in zip(games, row[1:]):
                try:
                    per_game[game] = float(cell)
                except ValueError:
                    continue
            data[bot] = per_game
    return data


def collect_points(
    root: Path,
    game: str,
    world: str,
    elo_data: dict[str, dict[str, float]],
    elo_game: str,
    x_axis: str,
    remove_comments: bool,
) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    base = root / "src" / "game_arena" / game / "examples" / world
    if not base.exists():
        return points
    for code_path in base.rglob("2.python_code.py"):
        parts = code_path.parts
        try:
            idx = parts.index("examples")
            model = parts[idx + 2]
            run_id = parts[idx + 3]
        except (ValueError, IndexError):
            continue
        bot = f"{model}/{run_id}"
        per_game = elo_data.get(bot)
        if not per_game or elo_game not in per_game:
            continue
        try:
            # print(f"reading {code_path}")
            code_text = code_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if remove_comments:
            filtered_lines = [line for line in code_text.splitlines() if not line.lstrip().startswith("#")]
            code_text = "\n".join(filtered_lines)
        code_len = len(code_text)
        if code_len <= 0:
            continue
        x_value = float(code_len)
        if x_axis == "thinking":
            output_path_txt = code_path.parent / "1.output.txt"
            output_path_json = code_path.parent / "1.output.json"
            output_path = output_path_txt if output_path_txt.exists() else output_path_json
            if not output_path.exists():
                continue
            try:
                # print(f"reading {output_path}")
                output_text = output_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            thinking_len = max(0, len(output_text) - code_len)
            x_value = float(thinking_len)
        count = float(len(per_game))
        points.append((x_value, float(per_game[elo_game]), count))
    return points


def plot(
    points: list[tuple[float, float, float]],
    out_path: Path,
    title: str,
    x_label: str,
    show_corr: bool,
) -> tuple[float, int, Path]:
    if not points:
        return float("nan"), 0, out_path.with_suffix(".pkl")
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    sizes = np.array([p[2] for p in points])
    sizes = 20 + (sizes / sizes.max()) * 180
    r_value = float(np.corrcoef(x, y)[0, 1]) if len(points) > 1 else float("nan")

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(x, y, s=sizes, c=y, cmap="viridis", alpha=0.75, edgecolor="k", linewidth=0.4)
    if show_corr and len(points) > 1:
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 200)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color="black", linewidth=1.2, linestyle="--")
    ax.set_xlabel(x_label)
    ax.set_ylabel("ELO")
    ax.set_title(title)
    if show_corr and np.isfinite(r_value):
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
    fig.colorbar(scatter, ax=ax, label="ELO")

    fig.tight_layout()
    fig.savefig(out_path)
    pkl_path = out_path.with_suffix(".pkl")
    with pkl_path.open("wb") as handle:
        pickle.dump(fig, handle, protocol=pickle.HIGHEST_PROTOCOL)
    plt.close(fig)
    return r_value, len(points), pkl_path


def run_once(
    root: Path,
    out_dir: Path,
    game: str,
    world: str,
    elos_csv: Path,
    x_axis: str,
    remove_comments: bool,
    ignore_corr: bool,
    extension: str,
) -> None:
    elo_game = map_game_to_elo(game, world)
    if not elo_game:
        print(f"skipping {game}/{world}: no ELO column mapping")
        return
    elo_data = load_elo_csv(root / elos_csv)
    # print('ELO DATA', elo_data)
    points = collect_points(root, game, world, elo_data, elo_game, x_axis, remove_comments)
    prefix = "code_length" if x_axis == "code" else "thinking_length"
    out_path = out_dir / f"{prefix}_vs_elo_{game}_{world}.{extension}"
    if x_axis == "code":
        x_label = "Code Length"
        if remove_comments:
            x_label = "Code Length (Excluding Comments)"
    else:
        x_label = "Thinking Length (chars)"
    title = format_game_title(game)
    r_value, n_points, pkl_path = plot(points, out_path, title, x_label, show_corr=not ignore_corr)
    log_path = out_dir / "viz_len_vs_elo.log"
    corr_str = "nan" if not np.isfinite(r_value) else f"{r_value:.2f}"
    timestamp = datetime.now().isoformat(timespec="seconds")
    log_line = (
        f"[{timestamp}] [viz_len_vs_elo] game={game} world={world} x_axis={x_axis} "
        f"elo_column={elo_game} points={n_points} corr={corr_str} "
        f"out={out_path} pkl={pkl_path}\n"
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(log_line)
    print(f"Wrote {out_path} and {pkl_path} ({n_points} points)")


def main() -> None:
    args = parse_args()
    root = args.root
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.game.upper() == "ALL":
        for game, world, _, _ in GS:
            run_once(
                root,
                out_dir,
                game,
                world,
                args.elos_csv,
                args.x_axis,
                args.remove_comments,
                args.ignore_corr,
                args.extension,
            )
    else:
        run_once(
            root,
            out_dir,
            args.game,
            args.world,
            args.elos_csv,
            args.x_axis,
            args.remove_comments,
            args.ignore_corr,
            args.extension,
        )


if __name__ == "__main__":
    main()
