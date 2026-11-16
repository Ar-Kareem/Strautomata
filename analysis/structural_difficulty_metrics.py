#!/usr/bin/env python3
"""Compute prompt, state, branching, and horizon metrics from replayed matches."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from dataclasses import asdict, astuple, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from game_arena import utils  # noqa: E402
from game_arena.base import to_jsonable  # noqa: E402


DEFAULT_PICKLE = ROOT / "analysis/results_tmp/exp_results_somerset_may_5.pkl"
DEFAULT_OUTPUT_DIR = ROOT / "analysis/results_tmp/game_difficulty"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pickle", type=Path, default=DEFAULT_PICKLE)
    parser.add_argument("--matches-per-game", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def scalar_count(value: Any) -> int:
    if isinstance(value, dict):
        return sum(scalar_count(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(scalar_count(item) for item in value)
    if isinstance(value, np.ndarray):
        return int(value.size)
    return 1


def replay_move(game: Any, recorded_action: Any, legal_moves: list[Any]) -> Any:
    """Recover the engine-native move represented in a JSON action history."""
    try:
        return game.get_move(recorded_action)
    except (TypeError, ValueError, AttributeError):
        pass

    for public_move in legal_moves:
        native_move = public_move
        try:
            native_move = game.get_move(public_move)
        except (TypeError, ValueError, AttributeError):
            pass
        for candidate in (public_move, native_move):
            representations: list[Any] = []
            if is_dataclass(candidate):
                tuple_representation = to_jsonable(astuple(candidate))
                dict_representation = to_jsonable(asdict(candidate))
                representations.extend(
                    [
                        tuple_representation,
                        dict_representation,
                        *dict_representation.values(),
                    ]
                )
                if isinstance(recorded_action, list):
                    representations.append(
                        tuple_representation[: len(recorded_action)]
                    )
            else:
                try:
                    representations.append(to_jsonable(candidate))
                except TypeError:
                    pass
            if recorded_action in representations:
                return native_move
    raise ValueError(f"Recorded action is not legal in replay: {recorded_action}")


def game_specific_prompt_words(prompts: dict[str, str]) -> dict[str, int]:
    line_counts: Counter[str] = Counter()
    normalized: dict[str, list[str]] = {}
    for game, prompt in prompts.items():
        lines = [
            " ".join(line.split())
            for line in prompt.splitlines()
            if line.strip()
        ]
        normalized[game] = lines
        line_counts.update(set(lines))
    common = {
        line for line, count in line_counts.items() if count == len(prompts)
    }
    return {
        game: len(words("\n".join(line for line in lines if line not in common)))
        for game, lines in normalized.items()
    }


def analyze_game(
    game_str: str,
    world: str,
    display_name: str,
    records: list[dict[str, Any]],
    matches_per_game: int,
    sampling_seed: int,
    prompt: str,
    specific_prompt_words: int,
) -> dict[str, Any]:
    game_cls = utils.get_game(game_str)
    config = utils.get_config_file(game_str, world)
    rng = random.Random(sampling_seed)

    horizons: list[int] = []
    branching: list[int] = []
    state_scalars: list[int] = []
    state_chars: list[int] = []
    replay_failures = 0
    replayed_matches = 0

    completed_candidates = [
        record
        for record in records
        if record.get("done") and record.get("action_history")
    ]
    completed = rng.sample(
        completed_candidates, min(matches_per_game, len(completed_candidates))
    )

    for record in completed:
        try:
            history = record["action_history"]
            if isinstance(history, str):
                history = json.loads(history)
            if not isinstance(history, list):
                raise TypeError("action_history is not a list")

            horizons.append(len(history))
            if game_str == "battleships":
                # OpenSpiel exposes already-fired cells as legal, although the
                # benchmark prompt forbids repeats. Count prompt-valid unknown
                # cells while replaying each player's recorded shot history.
                seen_shots: dict[int, set[tuple[int, int]]] = {
                    0: set(),
                    1: set(),
                }
                for player, action, _elapsed in history:
                    player = int(player)
                    if not isinstance(action, (list, tuple)) or len(action) != 2:
                        raise ValueError(f"Invalid recorded shot: {action}")
                    branching.append(
                        int(config["n"]) ** 2 - len(seen_shots[player])
                    )
                    seen_shots[player].add((int(action[0]), int(action[1])))
                replayed_matches += 1
                continue

            if game_str == "backgammon":
                # The pickle does not store dice outcomes, and Backgammon's
                # private RNG was not initialized from the recorded match seed.
                replay_failures += 1
                continue

            utils.set_seed(record.get("seed"))
            game = game_cls(config)
            match_branching: list[int] = []
            match_scalars: list[int] = []
            match_chars: list[int] = []

            for player, action, _elapsed in history:
                if int(player) != game.current_player():
                    raise ValueError("recorded player does not match replay state")
                legal = game.get_legal_moves()
                match_branching.append(len(legal))
                observation = game.get_observation()
                match_scalars.append(scalar_count(observation))
                match_chars.append(
                    len(
                        json.dumps(
                            to_jsonable(observation), separators=(",", ":")
                        )
                    )
                )
                game.game_step(replay_move(game, action, legal))

            if not game.is_done():
                raise ValueError("replayed action history did not finish the game")

            branching.extend(match_branching)
            state_scalars.extend(match_scalars)
            state_chars.extend(match_chars)
            replayed_matches += 1
        except (AssertionError, TypeError, ValueError, AttributeError, IndexError):
            replay_failures += 1

    if not horizons:
        raise RuntimeError(f"No completed {display_name} matches were sampled")

    branch = pd.Series(branching, dtype=float)
    horizon = pd.Series(horizons, dtype=float)
    scalars = pd.Series(state_scalars, dtype=float)
    chars = pd.Series(state_chars, dtype=float)
    return {
        "game": display_name,
        "game_str": game_str,
        "world": world,
        "completed_match_candidates": len(completed_candidates),
        "sampled_completed_matches": len(completed),
        "replayed_matches": replayed_matches,
        "replay_failures": replay_failures,
        "full_prompt_words": len(words(prompt)),
        "game_specific_prompt_words": specific_prompt_words,
        "median_state_scalars": scalars.median(),
        "median_serialized_state_chars": chars.median(),
        "initial_legal_actions": len(game_cls(config).get_legal_moves()),
        "median_legal_actions": branch.median(),
        "p90_legal_actions": branch.quantile(0.9),
        "maximum_legal_actions_observed": branch.max(),
        "mean_match_horizon": horizon.mean(),
        "median_match_horizon": horizon.median(),
        "p90_match_horizon": horizon.quantile(0.9),
    }


def markdown(df: pd.DataFrame) -> str:
    view = df[
        [
            "game",
            "game_specific_prompt_words",
            "median_state_scalars",
            "median_legal_actions",
            "p90_legal_actions",
            "mean_match_horizon",
            "p90_match_horizon",
        ]
    ].copy()
    view.columns = [
        "Game",
        "Specification words",
        "State scalars",
        "Median legal actions",
        "P90 legal actions",
        "Mean match horizon",
        "P90 match horizon",
    ]
    for column in view.columns[1:]:
        view[column] = view[column].map(
            lambda value: "NA" if pd.isna(value) else f"{value:.1f}"
        )
    return view.to_markdown(index=False)


_ILLEGAL_RE = re.compile(r"Invalid move|illegal move|not a legal|Malformed|Could not parse|invalid action", re.IGNORECASE)


def illegal_failures_per_1k(results_bots: dict[str, Any]) -> dict[str, float]:
    """Illegal-move failures per 1,000 player-games in each game, over every tournament match and every automaton."""
    out = {}
    for game, res in results_bots.items():
        matches = res.get("raw_match_results", [])
        illegal = 0
        for m in matches:
            r = m.get("r") if isinstance(m.get("r"), dict) else {}
            counts = r.get("player_err_counts") or []
            if m.get("winner") != "error" and not any(counts):
                continue
            text = " ".join(str(r.get(k) or m.get(k) or "") for k in ("exception", "exception_traceback"))
            if _ILLEGAL_RE.search(text):
                illegal += sum(1 for c in counts[:2] if c)
        out[game] = 1000.0 * illegal / (2 * len(matches)) if matches else float("nan")
    return out


def latex(df: pd.DataFrame, illegal_per_1k: dict[str, float]) -> str:
    cols = ["game", "game_specific_prompt_words", "median_legal_actions", "p90_legal_actions", "mean_match_horizon", "p90_match_horizon"]
    ints = {"game_specific_prompt_words", "median_legal_actions", "p90_legal_actions"}
    fmt = lambda v, c: "NA" if pd.isna(v) else (f"{v:.0f}" if c in ints and float(v).is_integer() else f"{v:.1f}")  # noqa: E731
    rows = [" & ".join([str(r["game"]).replace("&", r"\&")] + [fmt(r[c], c) for c in cols[1:]]
                       + [fmt(illegal_per_1k.get(r["game"], float("nan")), "illegal")]) + r" \\" for _, r in df[cols].iterrows()]
    caption = ("Structural difficulty of each game: words in the game-specific part of the specification, median and 90th-percentile "
               "number of legal actions per turn, mean and 90th-percentile match horizon in plies (measured on replayed tournament "
               "matches), and illegal-move failures per 1,000 player-games over all tournament matches.")
    return "\n".join([r"\begin{table}[t]", r"\centering", r"\small", rf"\caption{{{caption}}}", r"\label{tab:structural-difficulty}",
                      r"\begin{tabular}{lrrrrrr}", r"\toprule",
                      r"Game & Spec. words & Median legal & P90 legal & Mean horizon & P90 horizon & Illegal / 1K \\", r"\midrule",
                      *rows, r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])


def main() -> None:
    args = parse_args()
    if args.matches_per_game < 1:
        raise ValueError("--matches-per-game must be at least 1")

    import pickle

    with args.pickle.open("rb") as handle:
        payload = pickle.load(handle)  # noqa: S301 - trusted local experiment file
    runs = payload["runs"]
    results = payload["results_bots"]
    prompts: dict[str, str] = {}
    for game_str, world, display_name in runs:
        game_cls = utils.get_game(game_str)
        config = utils.get_config_file(game_str, world)
        prompts[display_name] = game_cls.get_prompt(config=config)
    specific_counts = game_specific_prompt_words(prompts)

    rows = []
    for index, (game_str, world, display_name) in enumerate(runs):
        print(f"[{index + 1}/{len(runs)}] {display_name}", flush=True)
        rows.append(
            analyze_game(
                game_str,
                world,
                display_name,
                results[display_name]["raw_match_results"],
                args.matches_per_game,
                args.seed + index,
                prompts[display_name],
                specific_counts[display_name],
            )
        )
    df = pd.DataFrame(rows)
    text = markdown(df)
    print(df.to_string(index=False))
    print("\nMarkdown\n")
    print(text)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_dir / "structural_difficulty_metrics.csv", index=False)
    (args.output_dir / "structural_difficulty_metrics.md").write_text(
        text + "\n", encoding="utf-8"
    )
    (args.output_dir / "structural_difficulty_metrics.tex").write_text(latex(df, illegal_failures_per_1k(payload["results_bots"])))
    print(f"\nWrote outputs (CSV, Markdown, structural_difficulty_metrics.tex) to {args.output_dir}")


if __name__ == "__main__":
    main()
