#!/usr/bin/env python3
"""Export short looping board previews for the game cards of the static frontend.

Run from ``src/`` after ``export_history``::

    python -m frontend.export_previews --out frontend/arena_fe/public/

For every game in ``history/index.json`` a decisive tourney match between two of the
top-rated bots is replayed through the engine and its per-turn observations are written to
``previews/<game>_<world>.json`` as ``{"frames": [{"state": ..., "player": ...}, ...]}``.
Games whose recorded moves cannot be replayed (unseeded randomness) fall back to a seeded
random self-play game.  Long games are subsampled so each file stays small.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # src/

from game_arena import utils  # noqa: E402
from game_arena.utils import set_seed  # noqa: E402
from frontend.export_history import REASON_CODES, _clean_obs, _coerce_move, dump_json, log, safe_name  # noqa: E402
from frontend.replay_format import REPLAYS_DIR, read_replay_file  # noqa: E402

MAX_FRAMES = 90
MIN_MOVES = 5
TOP_BOTS = 6


def _observe(game: Any) -> dict[str, Any]:
    obs = game.get_fixed_observation() if hasattr(game, "get_fixed_observation") else game.get_observation()
    try:
        player = int(game.current_player())
    except Exception:
        player = None
    return {"state": _clean_obs(obs), "player": player}


def replay(game_id: str, world_id: str, seed: Optional[int], moves: list[list[Any]]) -> Optional[list[dict[str, Any]]]:
    cfg = utils.get_config_file(game_id, world_id)
    set_seed(seed)
    game = utils.get_game(game_id)(cfg)
    frames = [_observe(game)]
    for _player, action in moves:
        if game.is_done():
            break
        try:
            game.game_step(_coerce_move(game, action))
        except Exception:
            return None
        frames.append(_observe(game))
    return frames if game.is_done() else None


def self_play(game_id: str, world_id: str, seed: int, max_moves: int = 400) -> list[dict[str, Any]]:
    cfg = utils.get_config_file(game_id, world_id)
    set_seed(seed)
    rng = random.Random(seed)
    game = utils.get_game(game_id)(cfg)
    frames = [_observe(game)]
    while not game.is_done() and len(frames) <= max_moves:
        move = rng.choice(list(game.get_legal_moves()))
        game.game_step(game.get_move(move) if isinstance(move, str) else move)
        frames.append(_observe(game))
    return frames


def candidate_matches(history: Path, key: str) -> list[dict[str, Any]]:
    """Finished tourney matches between the top-rated bots, decisive and longest games first."""
    summary = json.loads((history / "games" / key / "summary.json").read_text())
    bots = summary.get("stages", {}).get("tourney", {}).get("bots", [])
    ratings = summary.get("bots", {})
    top = sorted(bots, key=lambda b: -(ratings.get(b, {}).get("rating") or -1e9))[:TOP_BOTS]
    top_set = set(top)
    table = json.loads((history / "games" / key / "tourney" / "matches.json").read_text())
    col = {c: i for i, c in enumerate(table["columns"])}
    replays = history / REPLAYS_DIR / key / "tourney"
    vocab = json.loads((replays / "vocab.json").read_text())
    decisive = {REASON_CODES["win"]: False, REASON_CODES["draw"]: True}
    files: dict[str, dict[str, list[dict[str, Any]]]] = {}
    out: list[dict[str, Any]] = []
    for row in table["rows"]:
        a, b = table["bots"][row[col["a"]]], table["bots"][row[col["b"]]]
        lo, hi = min(a, b), max(a, b)
        if lo not in top_set or hi not in top_set or row[col["reason"]] not in decisive or row[col["detail"]] < 0:
            continue
        if lo not in files:
            files[lo] = read_replay_file(replays / f"{safe_name(lo)}.rpl", vocab)
        moves = files[lo][hi][row[col["detail"]]]["moves"]
        if len(moves) >= MIN_MOVES:
            seed = row[col["seed"]]
            out.append({"seed": seed if seed >= 0 else None, "moves": moves, "draw": decisive[row[col["reason"]]]})
    # prefer decisive games, then games that fit in the frame budget without subsampling, then the longest
    out.sort(key=lambda m: (m["draw"], len(m["moves"]) > MAX_FRAMES,
                            -len(m["moves"]) if len(m["moves"]) <= MAX_FRAMES else len(m["moves"])))
    return out


def subsample(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(frames) <= MAX_FRAMES:
        return frames
    step = (len(frames) - 1) / (MAX_FRAMES - 1)
    return [frames[round(i * step)] for i in range(MAX_FRAMES)]


def export_game(history: Path, out_dir: Path, game: dict[str, Any]) -> None:
    key, game_id, world_id = game["id"], game["game"], game["world"]
    frames = None
    source = "self-play"
    if game.get("replayable", True):
        for m in candidate_matches(history, key)[:10]:
            try:
                frames = replay(game_id, world_id, m["seed"], m["moves"])
            except Exception:
                frames = None
            if frames:
                source = "tourney"
                break
    if not frames:
        frames = self_play(game_id, world_id, seed=7)
    frames = subsample(frames)
    size = dump_json(out_dir / f"{key}.json", {"game": game_id, "world": world_id, "source": source, "frames": frames})
    log(f"{key}: {len(frames)} frames from {source} ({size / 1024:.0f} KB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="frontend/arena_fe/public/", help="public/ dir holding history/")
    args = parser.parse_args()
    public = Path(args.out)
    history = public / "history"
    index = json.loads((history / "index.json").read_text())
    for game in index["games"]:
        try:
            export_game(history, public / "previews", game)
        except Exception as exc:
            log(f"{game['id']}: FAILED {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
