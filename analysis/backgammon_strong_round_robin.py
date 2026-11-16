#!/usr/bin/env python3
"""Run a seeded Backgammon round robin across four strong model families."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from game_arena import base, utils  # noqa: E402


AUTOMATA = {
    "GPT": "gpt_5.4_high/005",
    "Claude": "claude_opus_4.7_high/004",
    "Gemini": "gemini_3_pro_preview/004",
    "GLM": "glm_5/004",
}
DEFAULT_OUTPUT_DIR = ROOT / "analysis/results_tmp/backgammon_strong_round_robin"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-per-seat", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026072700)
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def play_one(
    game_cls: type[Any],
    config: dict[str, Any],
    bot_paths: dict[str, Path],
    name0: str,
    name1: str,
    seed: int,
    timeout: int,
) -> dict[str, Any]:
    seeded_game = functools.partial(game_cls, seed=seed)
    result = base.play_game_with_timeout(
        seeded_game,
        config,
        [(name0, bot_paths[name0]), (name1, bot_paths[name1])],
        seed=seed,
        timeout=timeout,
    )
    payload = result.get("r") or {}
    other = payload.get("other") or {}
    horizon = payload.get("move_count", other.get("move_count"))
    action_history = result.get("action_history") or "[]"
    if isinstance(action_history, str):
        action_history = json.loads(action_history)

    replay = game_cls(config, seed=seed)
    legal_action_counts: list[int] = []
    for player, action, _elapsed in action_history:
        if int(player) != replay.current_player():
            raise ValueError("Recorded player does not match seeded replay")
        replay.get_observation()
        legal_action_counts.append(len(replay.get_legal_moves()))
        replay.game_step(replay.get_move(action))
    if result.get("done") and not replay.is_done():
        raise ValueError("Seeded action replay did not reach the recorded terminal state")

    return {
        "seed": seed,
        "name0": name0,
        "name1": name1,
        "family0": next(k for k, v in AUTOMATA.items() if v == name0),
        "family1": next(k for k, v in AUTOMATA.items() if v == name1),
        "done": bool(result.get("done")),
        "winner": result.get("winner"),
        "horizon": horizon,
        "median_legal_actions": statistics.median(legal_action_counts),
        "legal_action_counts": json.dumps(legal_action_counts),
        "time_elapsed": result.get("time_elapsed"),
        "exception": result.get("exception"),
    }


def main() -> None:
    args = parse_args()
    if args.games_per_seat < 1:
        raise ValueError("--games-per-seat must be at least 1")

    game_cls = utils.get_game("backgammon")
    config = utils.get_config_file("backgammon", "world1")
    all_paths = utils.get_bot_paths_from_world(
        "backgammon", "world1", add_random=False
    )
    bot_paths = {name: all_paths[name] for name in AUTOMATA.values()}

    jobs: list[tuple[str, str, int]] = []
    seed_offset = 0
    for family_a, family_b in combinations(AUTOMATA, 2):
        for name0, name1 in (
            (AUTOMATA[family_a], AUTOMATA[family_b]),
            (AUTOMATA[family_b], AUTOMATA[family_a]),
        ):
            for _ in range(args.games_per_seat):
                jobs.append((name0, name1, args.seed + seed_offset))
                seed_offset += 1

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(
                play_one,
                game_cls,
                config,
                bot_paths,
                name0,
                name1,
                seed,
                args.timeout,
            )
            for name0, name1, seed in jobs
        ]
        for completed, future in enumerate(as_completed(futures), 1):
            row = future.result()
            rows.append(row)
            print(
                f"[{completed}/{len(futures)}] "
                f"{row['family0']} vs {row['family1']}: "
                f"horizon={row['horizon']}",
                flush=True,
            )

    rows.sort(key=lambda row: int(row["seed"]))
    horizons = [
        int(row["horizon"])
        for row in rows
        if row["done"] and row["horizon"] is not None
    ]
    if not horizons:
        raise RuntimeError("No matches completed successfully")
    legal_action_counts = [
        count
        for row in rows
        if row["done"]
        for count in json.loads(str(row["legal_action_counts"]))
    ]

    pair_rows = []
    for family_a, family_b in combinations(AUTOMATA, 2):
        pair_horizons = [
            int(row["horizon"])
            for row in rows
            if row["done"]
            and row["horizon"] is not None
            and {row["family0"], row["family1"]} == {family_a, family_b}
        ]
        pair_legal_counts = [
            count
            for row in rows
            if row["done"]
            and {row["family0"], row["family1"]} == {family_a, family_b}
            for count in json.loads(str(row["legal_action_counts"]))
        ]
        pair_rows.append(
            {
                "pair": f"{family_a} vs {family_b}",
                "completed": len(pair_horizons),
                "mean_horizon": statistics.fmean(pair_horizons),
                "median_horizon": statistics.median(pair_horizons),
                "minimum_horizon": min(pair_horizons),
                "maximum_horizon": max(pair_horizons),
                "median_legal_actions": statistics.median(pair_legal_counts),
            }
        )

    summary = {
        "automata": AUTOMATA,
        "requested_matches": len(rows),
        "completed_matches": len(horizons),
        "mean_horizon": statistics.fmean(horizons),
        "median_horizon": statistics.median(horizons),
        "minimum_horizon": min(horizons),
        "maximum_horizon": max(horizons),
        "legal_action_observations": len(legal_action_counts),
        "median_legal_actions": statistics.median(legal_action_counts),
        "pair_summaries": pair_rows,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "matches.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("\n" + json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
