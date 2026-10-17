#!/usr/bin/env python3
"""Compute per-game empirical difficulty metrics from a results pickle."""

from __future__ import annotations

import argparse
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.top10_failure_counts import FAILURE_KINDS, classify_failure  # noqa: E402


DEFAULT_PICKLE = ROOT / "analysis/results_tmp/exp_results_somerset_may_5.pkl"
DEFAULT_OUTPUT_DIR = ROOT / "analysis/results_tmp/game_difficulty"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pickle", type=Path, default=DEFAULT_PICKLE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def move_count(record: dict[str, Any]) -> int | None:
    result = record.get("r")
    if not isinstance(result, dict):
        return None
    value = result.get("move_count")
    if value is None and isinstance(result.get("other"), dict):
        value = result["other"].get("move_count")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def is_generated(name: str) -> bool:
    return name != "random" and not name.startswith("heuristic")


def analyze(payload: dict[str, Any]) -> pd.DataFrame:
    results = payload["results_bots"]
    rows: list[dict[str, Any]] = []

    for game, game_result in results.items():
        records = game_result["raw_match_results"]
        failures: Counter[str] = Counter()
        failures_by_bot: defaultdict[str, Counter[str]] = defaultdict(Counter)
        player_games = 0
        completed_lengths: list[int] = []

        participants = {
            str(name)
            for record in records
            for name in (record.get("name0"), record.get("name1"))
            if is_generated(str(name))
        }

        for record in records:
            names = [str(record.get("name0")), str(record.get("name1"))]
            player_games += sum(is_generated(name) for name in names)

            if record.get("done"):
                length = move_count(record)
                if length is not None:
                    completed_lengths.append(length)

            kind, blamed = classify_failure(record)
            if kind is None:
                continue
            for bot in blamed:
                if is_generated(bot):
                    failures[kind] += 1
                    failures_by_bot[bot][kind] += 1

        ratings = pd.to_numeric(
            game_result["leaderboard_table_df"]["rating"], errors="coerce"
        )
        generated_ratings = ratings.reindex(sorted(participants)).dropna()
        failure_free = [
            bot for bot in generated_ratings.index if not failures_by_bot[bot]
        ]
        failure_free_ratings = generated_ratings.reindex(failure_free).dropna()

        length_series = pd.Series(completed_lengths, dtype=float)
        total_failures = sum(failures[kind] for kind in FAILURE_KINDS)
        bots_with_failure = sum(
            bool(sum(failures_by_bot[bot].values())) for bot in participants
        )
        rows.append(
            {
                "game": game,
                "generated_automata": len(participants),
                "player_games": player_games,
                "completed_matches": len(completed_lengths),
                "completion_rate_percent": (
                    100.0 * len(completed_lengths) / len(records) if records else 0.0
                ),
                "median_horizon_moves": length_series.median(),
                "p90_horizon_moves": length_series.quantile(0.9),
                "illegal_failures": failures["illegal"],
                "timeout_failures": failures["timeout"],
                "runtime_failures": failures["runtime"],
                "compile_failures": failures["compile"],
                "total_failures": total_failures,
                "failures_per_1000_player_games": (
                    1000.0 * total_failures / player_games if player_games else 0.0
                ),
                "automata_with_failure": bots_with_failure,
                "automata_with_failure_percent": (
                    100.0 * bots_with_failure / len(participants)
                    if participants
                    else 0.0
                ),
                "failure_free_automata": len(failure_free_ratings),
                "all_automata_elo_iqr": (
                    generated_ratings.quantile(0.75)
                    - generated_ratings.quantile(0.25)
                ),
                "failure_free_elo_iqr": (
                    failure_free_ratings.quantile(0.75)
                    - failure_free_ratings.quantile(0.25)
                    if len(failure_free_ratings) >= 2
                    else float("nan")
                ),
                "failure_free_elo_range": (
                    failure_free_ratings.max() - failure_free_ratings.min()
                    if len(failure_free_ratings) >= 2
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def markdown(df: pd.DataFrame) -> str:
    view = df[
        [
            "game",
            "median_horizon_moves",
            "p90_horizon_moves",
            "failures_per_1000_player_games",
            "automata_with_failure_percent",
            "failure_free_elo_iqr",
        ]
    ].copy()
    view.columns = [
        "Game",
        "Median moves",
        "P90 moves",
        "Failures/1K player-games",
        "Automata with failure",
        "Failure-free Elo IQR",
    ]
    for column in ["Median moves", "P90 moves", "Failures/1K player-games"]:
        view[column] = view[column].map(lambda value: f"{value:.1f}")
    view["Automata with failure"] = view["Automata with failure"].map(
        lambda value: f"{value:.1f}%"
    )
    view["Failure-free Elo IQR"] = view["Failure-free Elo IQR"].map(
        lambda value: "NA" if pd.isna(value) else f"{value:.0f}"
    )
    return view.to_markdown(index=False)


def main() -> None:
    args = parse_args()
    with args.pickle.open("rb") as handle:
        payload = pickle.load(handle)  # noqa: S301 - trusted local experiment file
    df = analyze(payload)
    text = markdown(df)
    print(df.to_string(index=False))
    print("\nMarkdown\n")
    print(text)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_dir / "tournament_difficulty_metrics.csv", index=False)
    (args.output_dir / "tournament_difficulty_metrics.md").write_text(
        text + "\n", encoding="utf-8"
    )
    print(f"\nWrote outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
