#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import pickle
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from game_arena import utils as arena_utils


ROOT_DIR = arena_utils.get_root_path()
MODULE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build prompt datasets and bot lists for winner-guessing experiments.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build_dataset", help="Build prompt-only JSON from explicit bot identities, a top-bots JSON list, or directly from a gen_pkl plus selected game/worlds.")
    build_parser.add_argument("--game", default=None, help="Game id, e.g. chess, checkers, go. Required with --bots; optional filter with --in-json.")
    build_parser.add_argument("--world", default=None, help="World id, e.g. worlduci1, world1. Required with --bots; optional filter with --in-json.")
    build_parser.add_argument("--bots", default=None, help="Bot names as CSV or JSON list, e.g. 'a/001,b/002' or '[\"a/001\",\"b/002\"]'.")
    build_parser.add_argument("--in-json", default=None, help="Input JSON list produced by top_bots_from_pkl.")
    build_parser.add_argument("--in-pkl", default=None, help="Input exp_plotting gen_pkl results file. Use with --game_worlds to select runs directly.")
    build_parser.add_argument("--game_worlds", "--game-worlds", default=None, help="Comma-separated list like 'tic_tac_toe/world1,chess/worlduci1'. Supported with --in-json or --in-pkl.")
    build_parser.add_argument("--top-k", type=int, default=None, help="Optional max number of bots to use from each selected entry when --in-json or --in-pkl is provided.")
    build_parser.add_argument("--out-json", required=True, help="Output JSON path.")

    top_parser = subparsers.add_parser("top_bots_from_pkl", help="Return bots sorted by ELO for every game in a gen_pkl payload, with optional filtering/truncation.")
    top_parser.add_argument("--in-pkl", required=True, help="Input exp_plotting gen_pkl results file.")
    top_parser.add_argument("--game", default=None, help="Optional game id filter, e.g. chess, checkers, go.")
    top_parser.add_argument("--top-k", type=int, default=None, help="Optional max number of bots to keep per game after sorting by rating.")
    top_parser.add_argument("--out-json", default=None, help="Optional output JSON path. Default: next to --in-pkl.")
    return parser.parse_args()


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _load_payload(in_pkl: Path) -> dict[str, Any]:
    with in_pkl.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pickle payload type: expected dict, got {type(payload).__name__}")
    return payload


def _find_run(payload: dict[str, Any], game: str) -> tuple[str, str]:
    matches = []
    for item in payload.get("runs", []):
        if isinstance(item, (list, tuple)) and len(item) >= 3 and item[0] == game:
            matches.append((str(item[1]), str(item[2])))
    if not matches:
        raise ValueError(f"Game {game!r} not found in payload runs")
    if len(matches) > 1:
        raise ValueError(f"Game {game!r} matched multiple runs: {matches}")
    return matches[0]


def _iter_runs(payload: dict[str, Any]) -> list[tuple[str, str, str]]:
    runs: list[tuple[str, str, str]] = []
    for item in payload.get("runs", []):
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            runs.append((str(item[0]), str(item[1]), str(item[2])))
    return runs


def _read_rules(game: str) -> str:
    prompt_path = arena_utils.get_game_dir(game) / "prompt_example.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt rules file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _ratings_df(results: dict[str, dict[str, Any]]) -> pd.DataFrame:
    cols = []
    for key, value in results.items():
        leaderboard_df = value.get("leaderboard_table_df")
        if not isinstance(leaderboard_df, pd.DataFrame) or "rating" not in leaderboard_df:
            raise ValueError(f"Expected leaderboard_table_df with a 'rating' column for {key!r}")
        cols.append(leaderboard_df["rating"].rename(key))
    if not cols:
        raise ValueError("Expected at least one results table")
    return pd.concat(cols, axis=1)


def _top_names_by_median_elo(results: dict[str, dict[str, Any]], top_k: int | None) -> list[str]:
    rating_df = _ratings_df(results)
    median_elo = rating_df.median(axis=1, skipna=True).sort_values(ascending=False)
    ordered = median_elo.index.astype(str).tolist()
    ordered = [name for name in ordered if name != "random"]
    return ordered if top_k is None else ordered[:top_k]


def _best_bot_per_model_in_game(leaderboard_df: pd.DataFrame, top_models: list[str]) -> list[str]:
    if not isinstance(leaderboard_df, pd.DataFrame) or "rating" not in leaderboard_df:
        raise ValueError("Expected leaderboard_table_df with a 'rating' column")
    ratings = leaderboard_df.sort_values("rating", ascending=False)
    best: dict[str, str] = {}
    for bot_name in ratings.index.astype(str).tolist():
        if bot_name == "random":
            continue
        model_name = bot_name.split("/", 1)[0]
        if model_name in top_models and model_name not in best:
            best[model_name] = bot_name
    missing = [model for model in top_models if model not in best]
    if missing:
        raise ValueError(f"Could not find top bot for models: {missing}")
    return [best[model] for model in top_models]


def _sorted_bot_names_for_game(leaderboard_df: pd.DataFrame, top_k: int | None = None) -> list[str]:
    if not isinstance(leaderboard_df, pd.DataFrame) or "rating" not in leaderboard_df:
        raise ValueError("Expected leaderboard_table_df with a 'rating' column")
    ordered = leaderboard_df.sort_values("rating", ascending=False).index.astype(str).tolist()
    return ordered if top_k is None else ordered[:top_k]


def _default_top_bots_out_json(in_pkl: Path, game: str | None, top_k: int | None) -> Path:
    stem = in_pkl.stem
    suffix = "all_games" if game is None else game
    out_dir = MODULE_DIR / "generated"
    if top_k is None:
        return out_dir / f"{stem}_top_bots_{suffix}.json"
    return out_dir / f"{stem}_top_bots_{suffix}_top{top_k}.json"


def _load_bot_code_map(game: str, world: str, bot_names: list[str]) -> dict[str, str]:
    bot_paths = arena_utils.get_bot_paths_from_world(game, world)
    out: dict[str, str] = {}
    for bot_name in bot_names:
        bot_dir = bot_paths.get(bot_name)
        if bot_dir is None:
            raise KeyError(f"Bot path not found for {bot_name}")
        py_code = bot_dir / "2.python_code.py"
        out[bot_name] = py_code.read_text(encoding="utf-8")
    return out


def _load_top_bot_entries(in_json: Path) -> list[dict[str, Any]]:
    payload = json.loads(in_json.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list in {in_json}, got {type(payload).__name__}")
    entries: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Entry {index} in {in_json} is not an object")
        if not isinstance(item.get("game"), str):
            raise ValueError(f"Entry {index} missing string field 'game'")
        if not isinstance(item.get("world"), str):
            raise ValueError(f"Entry {index} missing string field 'world'")
        botlist = item.get("botlist")
        if not isinstance(botlist, list) or not all(isinstance(bot, str) for bot in botlist):
            raise ValueError(f"Entry {index} missing string-list field 'botlist'")
        entries.append(
            {
                "game": str(item["game"]),
                "world": str(item["world"]),
                "botlist": [str(bot) for bot in botlist],
            }
        )
    return entries


def _parse_game_worlds(game_worlds: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw_item in game_worlds.split(","):
        item = raw_item.strip()
        if not item:
            continue
        if "/" not in item:
            raise ValueError(f"Invalid --game_worlds entry {item!r}; expected 'game/world'")
        game, world = item.split("/", 1)
        game = game.strip()
        world = world.strip()
        if not game or not world:
            raise ValueError(f"Invalid --game_worlds entry {item!r}; expected non-empty game/world")
        pair = (game, world)
        if pair not in seen:
            seen.add(pair)
            pairs.append(pair)
    if not pairs:
        raise ValueError("--game_worlds must contain at least one 'game/world' entry")
    return pairs


def _parse_bots_json(bots_json: str) -> list[str]:
    text = bots_json.strip()
    if text.startswith("["):
        parsed = json.loads(text)
        if not isinstance(parsed, list) or not parsed or not all(isinstance(x, str) for x in parsed):
            raise ValueError("--bots JSON input must be a non-empty list of strings")
        return [str(x) for x in parsed]
    bots = [part.strip() for part in text.split(",") if part.strip()]
    if not bots:
        raise ValueError("--bots CSV input must contain at least one bot name")
    return bots


def _row_for_pair(game: str, world: str, rules: str, bot_code_map: dict[str, str], bot_a: str, bot_b: str) -> dict[str, Any]:
    return {
        "id": f"{game}:{world}:{bot_a}__vs__{bot_b}",
        "game": game,
        "world": world,
        "bot_a": bot_a,
        "bot_b": bot_b,
        "rules": rules,
        "bot_a_code": bot_code_map[bot_a],
        "bot_b_code": bot_code_map[bot_b],
    }


def _assign_anon_order(bot_x: str, bot_y: str) -> tuple[str, str]:
    ordered = tuple(sorted((bot_x, bot_y)))
    digest = hashlib.sha256("||".join(ordered).encode("utf-8")).digest()
    return ordered if (digest[0] & 1) == 0 else (ordered[1], ordered[0])


def build_rows(game: str, world: str, bot_names: list[str]) -> list[dict[str, Any]]:
    if len(bot_names) < 2:
        raise ValueError("Need at least two bots to build a dataset")
    rules = _read_rules(game)
    bot_code_map = _load_bot_code_map(game, world, bot_names)
    rows = []
    for bot_x, bot_y in itertools.combinations(bot_names, 2):
        bot_a, bot_b = _assign_anon_order(bot_x, bot_y)
        rows.append(_row_for_pair(game, world, rules, bot_code_map, bot_a, bot_b))
    return rows


def _build_rows_from_top_bot_entries(
    entries: list[dict[str, Any]],
    *,
    game: str | None,
    world: str | None,
    top_k: int | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    matched = 0
    for entry in entries:
        if game is not None and entry["game"] != game:
            continue
        if world is not None and entry["world"] != world:
            continue
        matched += 1
        botlist = entry["botlist"] if top_k is None else entry["botlist"][:top_k]
        rows.extend(build_rows(entry["game"], entry["world"], botlist))
    if (game is not None or world is not None) and matched == 0:
        raise ValueError(f"No entries matched game={game!r}, world={world!r}")
    if not rows:
        raise ValueError("No dataset rows were built from the provided JSON/top-k selection")
    return rows


def _select_top_bot_entries_by_game_worlds(
    entries: list[dict[str, Any]],
    game_worlds: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    entry_map: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        key = (entry["game"], entry["world"])
        if key in entry_map:
            raise ValueError(f"Duplicate top-bots entry for game/world {key[0]!r}/{key[1]!r}")
        entry_map[key] = entry

    missing = [f"{game}/{world}" for game, world in game_worlds if (game, world) not in entry_map]
    if missing:
        raise ValueError(f"Missing top-bots entries for requested game/worlds: {missing}")

    return [entry_map[(game, world)] for game, world in game_worlds]


def top_bots_from_pkl(payload: dict[str, Any], game: str | None = None, top_k: int | None = None) -> list[dict[str, Any]]:
    results_models = payload.get("results_models")
    results_bots = payload.get("results_bots")
    if not isinstance(results_models, dict) or not isinstance(results_bots, dict):
        raise ValueError("Payload is missing results_models/results_bots")

    top_models = _top_names_by_median_elo(results_models, top_k=top_k)

    out: list[dict[str, Any]] = []
    matched = 0
    for run_game, world, label in _iter_runs(payload):
        if game is not None and run_game != game:
            continue
        matched += 1
        if label not in results_bots:
            raise KeyError(f"Missing run label {label!r} in results_bots")
        bot_leaderboard = results_bots[label].get("leaderboard_table_df")
        out.append(
            {
            "game": run_game,
            "world": world,
            "botlist": _best_bot_per_model_in_game(bot_leaderboard, top_models),
            }
        )
    if game is not None and matched == 0:
        raise ValueError(f"Game {game!r} not found in payload runs")
    if not out:
        raise ValueError("No game runs found in payload")
    return out


def run_build_dataset(args: argparse.Namespace) -> None:
    out_json = _resolve_path(args.out_json)
    if args.top_k is not None and args.top_k <= 0:
        raise ValueError("--top-k must be positive")

    if args.in_pkl is not None:
        if args.in_json is not None or args.bots is not None or args.game is not None or args.world is not None:
            raise ValueError("--in-pkl/--game_worlds is a separate mode; do not combine it with --in-json or explicit --game/--world/--bots")
        if args.game_worlds is None:
            raise ValueError("--game_worlds is required with --in-pkl")
        payload = _load_payload(_resolve_path(args.in_pkl))
        entries = top_bots_from_pkl(payload, top_k=args.top_k)
        selected_entries = _select_top_bot_entries_by_game_worlds(entries, _parse_game_worlds(args.game_worlds))
        rows = _build_rows_from_top_bot_entries(selected_entries, game=None, world=None, top_k=args.top_k)
    elif args.in_json is not None:
        entries = _load_top_bot_entries(_resolve_path(args.in_json))
        if args.game_worlds is not None:
            if args.game is not None or args.world is not None:
                raise ValueError("Use either --game_worlds or --game/--world filters with --in-json, not both")
            selected_entries = _select_top_bot_entries_by_game_worlds(entries, _parse_game_worlds(args.game_worlds))
            rows = _build_rows_from_top_bot_entries(selected_entries, game=None, world=None, top_k=args.top_k)
        else:
            rows = _build_rows_from_top_bot_entries(
                entries,
                game=args.game,
                world=args.world,
                top_k=args.top_k,
            )
    else:
        if args.game is None or args.world is None or args.bots is None:
            raise ValueError("--game, --world, and --bots are required unless --in-json is provided")
        rows = build_rows(args.game, args.world, _parse_bots_json(args.bots))
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"saved_json={out_json}")
    print(f"n_rows={len(rows)}")


def run_top_bots_from_pkl(args: argparse.Namespace) -> None:
    in_pkl = _resolve_path(args.in_pkl)
    if not in_pkl.exists():
        raise FileNotFoundError(f"Input pickle not found: {in_pkl}")
    payload = _load_payload(in_pkl)
    out_json = _resolve_path(args.out_json) if args.out_json else _default_top_bots_out_json(in_pkl, args.game, args.top_k)
    top_bots = top_bots_from_pkl(payload, game=args.game, top_k=args.top_k)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as handle:
        json.dump(top_bots, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(top_bots, ensure_ascii=False, indent=2))
    print(f"saved_json={out_json}", file=sys.stderr)


def main() -> None:
    args = parse_args()
    if args.command == "build_dataset":
        run_build_dataset(args)
    elif args.command == "top_bots_from_pkl":
        run_top_bots_from_pkl(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
