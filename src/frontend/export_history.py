#!/usr/bin/env python3
"""Export historical match data for the "Match Viewer" page of the static frontend.

Run from ``src/``::

    python -m frontend.export_history --out frontend/arena_fe/public/

The pickle defaults to ``WEBSITE_PKL`` in the repo's ``.env`` (path relative to the repo root);
``--pkl`` overrides it.

Inputs
------
* The experiment pickle (``results_models`` / ``results_bots`` leaderboards, one
  entry per game).  Its ``config.results_dir`` points at the tourney JSON files;
  the qualification JSON files are read from the sibling ``quals`` directory.
* ``results_current/<run>/tourney/matches_<game>_<world>.json``  (qualified bots only)
* ``results_current/<run>/quals/matches_quals_<game>_<world>.json`` (bots of the
  same model fight each other)

Output  (everything under ``<out>/history/``)
-------
index.json                                   games, models, families, stage counts
games/<game>_<world>/summary.json            leaderboards, per-bot records, pairwise table
games/<game>_<world>/<stage>/matches.json    every match of that stage, compact columnar form
replays/<game>_<world>/<stage>/...           move lists and think times of every match, binary
                                             (gitignored, see frontend/replay_format.py)
replays.lock.json                            content hash of replays/ (committed)
sources.json                                 size/mtime/sha256 of every input file, so
                                             scripts/check_history.cjs can tell when the
                                             website is behind the results on disk

Every file is designed to stay well under 10 MB so the page can fetch on demand.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import pickle
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # src/

from dotenv import load_dotenv  # noqa: E402

from game_arena import utils  # noqa: E402
from game_arena.utils import set_seed  # noqa: E402
from frontend import replay_format  # noqa: E402

STAGES = ("quals", "tourney")
GAME_LABELS: dict[tuple[str, str], str] = {
    ("amazons", "world1"): "Amazons",
    ("backgammon", "world1"): "Backgammon",
    ("battleships", "world1"): "Battleships",
    ("breakthrough", "world1"): "Breakthrough",
    ("checkers", "world1"): "Checkers",
    ("chess", "worlduci1"): "Chess",
    ("clobber", "world1"): "Clobber",
    ("connect4", "world1"): "Connect 4",
    ("dots_and_boxes", "world1"): "Dots and Boxes",
    ("go", "world1"): "Go",
    ("havannah", "world1"): "Havannah",
    ("hex", "world1"): "Hex",
    ("lines_of_action", "world1"): "Lines of Action",
    ("mancala", "world1"): "Mancala",
    ("nim", "world1"): "Nim",
    ("othello", "world1"): "Othello",
    ("pentago", "world1"): "Pentago",
    ("tic_tac_toe", "world1"): "Tic Tac Toe (3x3)",
    ("tic_tac_toe", "world2"): "Tic Tac Toe (4x4)",
    ("tic_tac_toe_3d", "world1"): "Tic Tac Toe 3D",
}
# Replayability is detected per game by re-running a sample of decisive matches through the
# engine and checking that the recorded winner comes out (see detect_replayable).  Games whose
# engine drew unseeded random numbers at the time of the run (backgammon dice and battleships
# ship placement before the fix in game.py) fail that check and are exported as move lists only.
NON_REPLAYABLE_GAMES: set[str] = set()  # filled at runtime (detection or --non_replayable)
REPLAY_CHECK_SAMPLE = 20
REPLAY_CHECK_MIN_OK = 0.9
# Keys of the fixed observation that are derived data and bloat the export.
STRIP_OBS_KEYS = {"legal_moves"}

FAMILY_RULES: list[tuple[str, str]] = [
    (r"^claude", "Claude"),
    (r"^(gpt|o\d|chatgpt)", "GPT"),
    (r"^gemini", "Gemini"),
    (r"^deepseek", "DeepSeek"),
    (r"^tng", "DeepSeek"),
    (r"^(devstral|ministral|mistral|magistral|codestral)", "Mistral"),
    (r"^glm", "GLM"),
    (r"^grok", "Grok"),
    (r"^kat_", "KAT"),
    (r"^kimi", "Kimi"),
    (r"^mimo", "MiMo"),
    (r"^minimax", "MiniMax"),
    (r"^nemotron", "Nemotron"),
    (r"^qwen", "Qwen"),
    (r"^solar", "Solar"),
    (r"^trinity", "Trinity"),
    (r"^llama", "Llama"),
    (r"^muse", "Meta"),
    (r"^random$", "Baseline"),
]

RESULT_CODES = {
    # per-player outcome codes used in matches.json (small ints keep files compact)
    "win": 0,
    "loss": 1,
    "draw": 2,
    "error": 3,          # this player crashed / illegal move
    "enemy_error": 4,
    "timeout": 5,        # this player exceeded the time limit
    "enemy_timeout": 6,
    "unknown": 7,
}
REASON_CODES = {"win": 0, "draw": 1, "error": 2, "timeout": 3, "unknown": 4}


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------
def log(msg: str) -> None:
    print(f"[export_history {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def family_of(model: str) -> str:
    for pattern, family in FAMILY_RULES:
        if re.match(pattern, model):
            return family
    return "Other"


def model_of(bot: str) -> str:
    return bot.split("/")[0]


def safe_name(bot: str) -> str:
    return bot.replace("/", "__")


def to_jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    if hasattr(obj, "tolist"):
        return to_jsonable(obj.tolist())
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            return obj.item()
        except Exception:  # pragma: no cover
            pass
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (str, int, bool)) or obj is None:
        return obj
    return str(obj)


def dump_json(path: Path, payload: Any) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(to_jsonable(payload), separators=(",", ":"), ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def round_or_none(v: Any, nd: int = 2) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, nd)


def match_outcome(m: dict[str, Any]) -> tuple[str, Optional[int]]:
    """Return (reason, winner) mirroring ``game_arena.utils.get_match_result`` but
    never raising: reason in win/draw/error/timeout/unknown, winner in {0,1,None}."""
    winner = m.get("winner")
    done = bool(m.get("done"))
    if done and winner in (0, 1):
        return "win", int(winner)
    if done and winner is None:
        return "draw", None
    r = m.get("r") if isinstance(m.get("r"), dict) else {}
    if winner == "error":
        counts = r.get("player_err_counts")
        if isinstance(counts, list) and len(counts) == 2 and set(counts) == {0, 1}:
            return "error", counts.index(0)
        return "error", None
    if winner == "timeout":
        hit = m.get("timeout_hit")
        if isinstance(hit, (list, tuple)) and hit and str(hit[0]) in ("0", "1"):
            return "timeout", 1 - int(hit[0])
        exc = str(m.get("exception", ""))
        found = re.search(r"\('([01])'", exc)
        if found:
            return "timeout", 1 - int(found.group(1))
        return "timeout", None
    if winner in (0, 1):  # not done but winner recorded (legacy)
        return "win", int(winner)
    return "unknown", None


def player_result(reason: str, winner: Optional[int], idx: int) -> str:
    if reason == "win":
        return "win" if winner == idx else "loss"
    if reason == "draw":
        return "draw"
    if reason == "error":
        if winner is None:
            return "error"
        return "enemy_error" if winner == idx else "error"
    if reason == "timeout":
        if winner is None:
            return "timeout"
        return "enemy_timeout" if winner == idx else "timeout"
    return "unknown"


def parse_history(raw: Any) -> list[list[Any]]:
    """action_history is stored as the repr of a list of (player, action, seconds)."""
    if isinstance(raw, list):
        hist = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            hist = json.loads(raw)
        except Exception:
            try:
                hist = ast.literal_eval(raw)
            except Exception:
                return []
    else:
        return []
    out = []
    for item in hist:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            player = item[0]
            action = item[1]
            secs = item[2] if len(item) > 2 else None
            out.append([player, action, secs])
    return out


def truncate(text: Any, limit: int = 600) -> Optional[str]:
    if text is None:
        return None
    s = str(text)
    return s if len(s) <= limit else s[: limit - 3] + "..."


# --------------------------------------------------------------------------------------
# board-state replay (pre-rendered per-turn observations)
# --------------------------------------------------------------------------------------
def _listify(v: Any) -> Any:
    if isinstance(v, (list, tuple)):
        return tuple(_listify(x) for x in v)
    return v


def _clean_obs(obs: Any) -> dict[str, Any]:
    obs = to_jsonable(obs)
    if not isinstance(obs, dict):
        return {"value": obs}
    return {k: v for k, v in obs.items() if k not in STRIP_OBS_KEYS}


def _coerce_move(game: Any, action: Any) -> Any:
    """Try the engine's own parser with the recorded action in the most likely shapes."""
    candidates = [action]
    if isinstance(action, list):
        candidates.insert(0, _listify(action))
    last_err: Optional[Exception] = None
    for cand in candidates:
        try:
            return game.get_move(cand)
        except Exception as exc:  # pragma: no cover - engine specific
            last_err = exc
    raise ValueError(f"cannot parse move {action!r}: {last_err}")


# --------------------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------------------
def load_pickle(path: Path) -> dict[str, Any]:
    log(f"loading pickle {path} ({path.stat().st_size / 1e9:.2f} GB)")
    t = time.time()
    with open(path, "rb") as f:
        payload = pickle.load(f)
    log(f"pickle loaded in {time.time() - t:.0f}s")
    return payload


def leaderboard_rows(df: Any) -> dict[str, dict[str, Any]]:
    """leaderboard_table_df -> {name: {rating, q975, q025, n, rank}}"""
    out: dict[str, dict[str, Any]] = {}
    if df is None or not hasattr(df, "iterrows"):
        return out
    for name, row in df.iterrows():
        out[str(name)] = {
            "rating": round_or_none(row.get("rating")),
            "q975": round_or_none(row.get("rating_q975")),
            "q025": round_or_none(row.get("rating_q025")),
            "variance": round_or_none(row.get("variance")),
            "n": int(row.get("num_battles", 0) or 0),
            "rank": int(row.get("final_ranking", 0) or 0),
        }
    return out


def top_bot_per_model(bot_rows: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Same rule as analysis/exp_plotting: highest tourney rating per model, ties by name."""
    best: dict[str, tuple[float, str]] = {}
    for bot, row in bot_rows.items():
        rating = row.get("rating")
        if rating is None:
            continue
        model = model_of(bot)
        cand = (-float(rating), bot)
        if model not in best or cand < best[model]:
            best[model] = cand
    return {model: bot for model, (_r, bot) in best.items()}


def fingerprint(path: Path, root: Path) -> dict[str, Any]:
    st = path.stat()
    with open(path, "rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    rel = path.resolve().relative_to(root) if path.resolve().is_relative_to(root) else path.resolve()
    # mtime as a string: nanoseconds exceed the integer precision of JavaScript numbers
    return {"path": rel.as_posix(), "size": st.st_size, "mtime_ns": str(st.st_mtime_ns), "sha256": digest}


def load_stage_json(path: Path) -> dict[str, Any]:
    log(f"reading {path.name} ({path.stat().st_size / 1e6:.0f} MB)")
    with open(path) as f:
        return json.load(f)


# --------------------------------------------------------------------------------------
# per game export
# --------------------------------------------------------------------------------------
def new_record() -> dict[str, Any]:
    return {"n": 0, "win": 0, "loss": 0, "draw": 0, "error": 0, "enemy_error": 0,
            "timeout": 0, "enemy_timeout": 0, "unknown": 0, "moves": 0, "secs": 0.0}


def finish_record(rec: dict[str, Any]) -> dict[str, Any]:
    n = rec["n"] or 1
    rec["avg_moves"] = round(rec["moves"] / n, 1)
    rec["avg_secs"] = round(rec["secs"] / n, 2)
    del rec["moves"]
    del rec["secs"]
    return rec


def export_stage(
    game_id: str,
    world_id: str,
    stage: str,
    data: dict[str, Any],
    out_dir: Path,
    replay_dir: Path,
    stats: dict[str, Any],
) -> dict[str, Any]:
    matches = data.get("match_results") or []
    bots = sorted({m["name0"] for m in matches} | {m["name1"] for m in matches})
    bot_index = {b: i for i, b in enumerate(bots)}
    records: dict[str, dict[str, Any]] = {b: new_record() for b in bots}
    pair_stats: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0, 0])
    # pair_stats[(a,b)] with a<b: [n, a_wins, b_wins, draws, a_err, b_err, a_timeout, b_timeout]

    rows: list[list[Any]] = []
    vocab = replay_format.Vocab()
    writers: dict[str, replay_format.ReplayFileWriter] = {}

    for m in matches:
        a, b = m["name0"], m["name1"]
        reason, winner = match_outcome(m)
        res0 = player_result(reason, winner, 0)
        res1 = player_result(reason, winner, 1)
        r = m.get("r") if isinstance(m.get("r"), dict) else {}
        move_count = r.get("move_count")
        if move_count is None:
            hist_len = None
            raw = m.get("action_history")
            if isinstance(raw, str):
                hist_len = raw.count("], [") + (1 if raw.strip("[] ") else 0)
            move_count = hist_len
        secs = round_or_none(m.get("time_elapsed"), 2)
        seed = m.get("seed")

        for bot, res in ((a, res0), (b, res1)):
            rec = records[bot]
            rec["n"] += 1
            rec[res] += 1
            rec["moves"] += move_count or 0
            rec["secs"] += secs or 0.0

        lo, hi = (a, b) if a <= b else (b, a)
        ps = pair_stats[(lo, hi)]
        ps[0] += 1
        a_is_lo = a == lo
        if reason == "win" and winner is not None:
            w_is_a = winner == 0
            ps[1 if (w_is_a == a_is_lo) else 2] += 1
        elif reason == "draw":
            ps[3] += 1
        elif reason == "error":
            if winner is None:
                ps[4] += 1
                ps[5] += 1
            else:
                culprit_is_a = winner == 1
                ps[4 if (culprit_is_a == a_is_lo) else 5] += 1
        elif reason == "timeout":
            if winner is None:
                ps[6] += 1
                ps[7] += 1
            else:
                culprit_is_a = winner == 1
                ps[6 if (culprit_is_a == a_is_lo) else 7] += 1

        hist = [h for h in parse_history(m.get("action_history")) if h[1] is not None]
        writer = writers.get(lo) or writers.setdefault(lo, replay_format.ReplayFileWriter(lo, vocab))
        extras = {k: v for k, v in (
            ("exception", truncate(m.get("exception") or r.get("exception"))),
            ("timeout_hit", to_jsonable(m.get("timeout_hit"))),
            ("returns", to_jsonable(r.get("returns"))),
            ("other", to_jsonable(r.get("other"))),
        ) if v is not None}
        detail_slot = writer.add(
            hi,
            [int(p) if isinstance(p, int) or str(p).isdigit() else 0 for p, _a, _s in hist],
            [to_jsonable(act) for _p, act, _s in hist],
            [round_or_none(sec, 3) for _p, _a, sec in hist],
            extras,
        )

        rows.append([
            bot_index[a], bot_index[b],
            RESULT_CODES[res0], RESULT_CODES[res1], REASON_CODES[reason],
            winner if winner is not None else -1,
            move_count if move_count is not None else -1,
            secs if secs is not None else -1,
            seed if seed is not None else -1,
            detail_slot,
        ])

    stage_dir = out_dir / stage
    matches_bytes = dump_json(stage_dir / "matches.json", {
        "game": game_id,
        "world": world_id,
        "stage": stage,
        "bots": bots,
        "columns": ["a", "b", "res_a", "res_b", "reason", "winner", "move_count", "secs", "seed", "detail"],
        "result_codes": RESULT_CODES,
        "reason_codes": REASON_CODES,
        "rows": rows,
    })
    shutil.rmtree(stage_dir / "pairs", ignore_errors=True)  # JSON detail files of older exports
    replay_stage = replay_dir / stage
    shutil.rmtree(replay_stage, ignore_errors=True)
    pair_bytes = replay_format.write_vocab(replay_stage / "vocab.json", vocab)
    pair_files = 0
    max_pair_bytes = 0
    for lo, writer in writers.items():
        n = writer.write(replay_stage / f"{safe_name(lo)}.rpl")
        pair_bytes += n
        pair_files += 1
        max_pair_bytes = max(max_pair_bytes, n)

    stats.update({
        f"{stage}_matches": len(matches),
        f"{stage}_bots": len(bots),
        f"{stage}_matches_bytes": matches_bytes,
        f"{stage}_pair_files": pair_files,
        f"{stage}_pair_bytes": pair_bytes,
        f"{stage}_max_pair_bytes": max_pair_bytes,
    })

    return {
        "bots": bots,
        "records": {b: finish_record(rec) for b, rec in records.items()},
        "pairwise": {f"{lo}|{hi}": v for (lo, hi), v in pair_stats.items()},
        "n_matches": len(matches),
    }


def detect_replayable(game_id: str, world_id: str, matches: list[dict[str, Any]]) -> tuple[bool, str]:
    """Replay a sample of decisive matches; the game is replayable when the engine reproduces
    the recorded winner for (almost) all of them."""
    # one match per pairing: a pairing's repeats are often identical games, so taking the first
    # N matches can sample a single pairing and let one odd game decide for the whole game
    sample: list[dict[str, Any]] = []
    seen_pairs: set[tuple[Any, Any]] = set()
    for m in matches:
        reason, winner = match_outcome(m)
        pair = (m.get("name0"), m.get("name1"))
        if reason == "win" and winner is not None and m.get("action_history") and pair not in seen_pairs:
            seen_pairs.add(pair)
            sample.append(m)
            if len(sample) >= REPLAY_CHECK_SAMPLE:
                break
    if not sample:
        return True, "no decisive matches to check"
    try:
        cfg = utils.get_config_file(game_id, world_id)
        game_cls = utils.get_game(game_id)
    except Exception as exc:
        return False, f"engine unavailable: {exc}"
    ok = 0
    for m in sample:
        try:
            set_seed(m.get("seed"))
            game = game_cls(cfg)
            # some engines initialise derived attributes lazily in the observation call
            (game.get_fixed_observation() if hasattr(game, "get_fixed_observation") else game.get_observation())
            for player, action, _secs in parse_history(m.get("action_history")):
                if action is None or game.is_done():
                    break
                game.game_step(_coerce_move(game, action))
            try:
                final = game.get_final_stats() or {}
            except Exception:
                final = {}
            if final.get("winner") == m.get("winner"):
                ok += 1
        except Exception:
            pass
    share = ok / len(sample)
    return share >= REPLAY_CHECK_MIN_OK, f"{ok}/{len(sample)} sampled matches reproduce the recorded winner"


def export_game(
    game_id: str,
    world_id: str,
    colname: str,
    payload: dict[str, Any],
    tourney_dir: Path,
    quals_dir: Path,
    out_root: Path,
    args: argparse.Namespace,
) -> Optional[dict[str, Any]]:
    key = f"{game_id}_{world_id}"
    out_dir = out_root / "games" / key
    replay_dir = out_root / replay_format.REPLAYS_DIR / key
    label = GAME_LABELS.get((game_id, world_id), colname)
    log(f"== {key} ({label})")
    stats: dict[str, Any] = {}

    models_res = (payload.get("results_models") or {}).get(colname) or {}
    bots_res = (payload.get("results_bots") or {}).get(colname) or {}
    model_rows = leaderboard_rows(models_res.get("leaderboard_table_df"))
    bot_rows = leaderboard_rows(bots_res.get("leaderboard_table_df"))
    top_bot = top_bot_per_model(bot_rows)

    summary: dict[str, Any] = {
        "game": game_id,
        "world": world_id,
        "label": label,
        "column": colname,
        "replayable": game_id not in NON_REPLAYABLE_GAMES,
        "rating_system": bots_res.get("rating_system") or models_res.get("rating_system"),
        "models": {m: {**row, "top_bot": top_bot.get(m), "family": family_of(m)} for m, row in model_rows.items()},
        "bots": {b: {**row, "model": model_of(b), "family": family_of(model_of(b))} for b, row in bot_rows.items()},
        "stages": {},
    }

    # ---- tourney -----------------------------------------------------------------
    tpath = tourney_dir / f"matches_{game_id}_{world_id}.json"
    qualified: list[str] = []
    if tpath.exists() and "tourney" in args.stages:
        data = load_stage_json(tpath)
        if not args.no_detect and game_id not in args.forced_non_replayable:
            ok, why = detect_replayable(game_id, world_id, data.get("match_results") or [])
            log(f"  replayable={ok} ({why})")
            if not ok:
                NON_REPLAYABLE_GAMES.add(game_id)
        qualified = sorted(data.get("qual_bot_names") or [])
        stage = export_stage(game_id, world_id, "tourney", data, out_dir, replay_dir, stats)
        stage["config"] = data.get("config")
        stage["qualified"] = qualified
        summary["stages"]["tourney"] = stage
        del data
    else:
        log(f"  no tourney file {tpath}")

    # ---- quals -------------------------------------------------------------------
    qpath = quals_dir / f"matches_quals_{game_id}_{world_id}.json"
    if qpath.exists() and "quals" in args.stages:
        data = load_stage_json(qpath)
        ci = data.get("ci_rankings") or {}
        qual_set = set(qualified)
        quals_rank: dict[str, list[dict[str, Any]]] = {}
        for model, entries in ci.items():
            rows = []
            for e in entries or []:
                bot = str(e.get("bot"))
                rows.append({
                    "bot": bot,
                    "rating": round_or_none(e.get("rating")),
                    "q975": round_or_none(e.get("rating_qupper")),
                    "q025": round_or_none(e.get("rating_qlower")),
                    "n": int(e.get("num_battles") or 0),
                    "rank": int(e.get("final_ranking") or 0),
                    "qualified": bot in qual_set,
                })
            quals_rank[model] = sorted(rows, key=lambda r: (r["rank"], -(r["rating"] or -1e9)))
        stage = export_stage(game_id, world_id, "quals", data, out_dir, replay_dir, stats)
        stage["config"] = data.get("config")
        stage["rankings"] = quals_rank
        summary["stages"]["quals"] = stage
        del data
    else:
        log(f"  no quals file {qpath}")

    stats["summary_bytes"] = dump_json(out_dir / "summary.json", summary)
    log(f"  done: " + ", ".join(f"{k}={v}" for k, v in stats.items()))
    return {
        "id": key,
        "game": game_id,
        "world": world_id,
        "label": label,
        "column": colname,
        "replayable": game_id not in NON_REPLAYABLE_GAMES,
        "stages": {s: {"matches": stats.get(f"{s}_matches", 0), "bots": stats.get(f"{s}_bots", 0)} for s in STAGES if f"{s}_matches" in stats},
        "qualified": len(qualified),
        "models": len(model_rows),
        "bytes": {k: v for k, v in stats.items() if k.endswith("bytes")},
    }


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pkl", type=Path, default=None, help="experiment results pickle (default: WEBSITE_PKL in .env)")
    p.add_argument("--out", type=Path, required=True, help="frontend public/ directory (history/ is created inside)")
    p.add_argument("--tourney_dir", type=Path, default=None, help="override tourney JSON dir (default: pickle config.results_dir)")
    p.add_argument("--quals_dir", type=Path, default=None, help="override quals JSON dir (default: sibling 'quals' of tourney dir)")
    p.add_argument("--games", type=str, default=None, help="comma separated game ids to export (default all)")
    p.add_argument("--stages", type=str, default="quals,tourney", help="comma separated subset of quals,tourney")
    p.add_argument("--clean", action="store_true", help="delete <out>/history before writing")
    p.add_argument("--non_replayable", type=str, default="",
                   help="comma separated game ids to export as move lists only (skips detection for them)")
    p.add_argument("--no_detect", action="store_true", help="skip the replayability check (treat every game as replayable)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    args.forced_non_replayable = {g.strip() for g in args.non_replayable.split(",") if g.strip()}
    NON_REPLAYABLE_GAMES.update(args.forced_non_replayable)
    root = utils.get_root_path().resolve()
    if args.pkl is None:
        load_dotenv(root / ".env")
        if not os.environ.get("WEBSITE_PKL"):
            raise SystemExit("no --pkl given and WEBSITE_PKL is not set in .env")
        args.pkl = root / os.environ["WEBSITE_PKL"]
    payload = load_pickle(args.pkl)

    results_dir = Path(payload.get("config", {}).get("results_dir", ""))
    tourney_dir = args.tourney_dir or (results_dir if results_dir.is_absolute() else root / results_dir)
    quals_dir = args.quals_dir or (tourney_dir.parent / "quals")
    log(f"tourney dir: {tourney_dir}")
    log(f"quals dir:   {quals_dir}")

    out_root = args.out / "history"
    if args.clean and out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    runs = payload.get("runs") or []
    wanted = {g.strip() for g in args.games.split(",")} if args.games else None
    specs = [(g, w, c) for g, w, c in runs if wanted is None or g in wanted or f"{g}_{w}" in wanted]
    if not specs:
        raise SystemExit(f"no games selected from runs={runs}")

    games_index: list[dict[str, Any]] = []
    models: dict[str, dict[str, Any]] = {}
    sources: dict[str, Any] = {"pkl": fingerprint(args.pkl, root), "games": {}}
    t0 = time.time()
    for game_id, world_id, colname in specs:
        entry = export_game(game_id, world_id, colname, payload, tourney_dir, quals_dir, out_root, args)
        if entry:
            games_index.append(entry)
        inputs = [tourney_dir / f"matches_{game_id}_{world_id}.json", quals_dir / f"matches_quals_{game_id}_{world_id}.json"]
        sources["games"][f"{game_id}_{world_id}"] = [
            fingerprint(path, root) for path, stage in zip(inputs, ("tourney", "quals")) if path.exists() and stage in args.stages
        ]
        bots_res = (payload.get("results_bots") or {}).get(colname) or {}
        for bot in leaderboard_rows(bots_res.get("leaderboard_table_df")):
            m = model_of(bot)
            models.setdefault(m, {"id": m, "family": family_of(m), "bots": set()})["bots"].add(bot)
        qpath = quals_dir / f"matches_quals_{game_id}_{world_id}.json"
        if qpath.exists() and "quals" in args.stages:
            # cheap: read only the ci_rankings keys via the already exported summary
            summ = json.loads((out_root / "games" / f"{game_id}_{world_id}" / "summary.json").read_text())
            for m, rows in (summ.get("stages", {}).get("quals", {}).get("rankings") or {}).items():
                entry_m = models.setdefault(m, {"id": m, "family": family_of(m), "bots": set()})
                entry_m["bots"].update(r["bot"] for r in rows)

    families: dict[str, list[str]] = defaultdict(list)
    for m in sorted(models):
        families[models[m]["family"]].append(m)
    index = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": {"pkl": str(args.pkl), "tourney_dir": str(tourney_dir), "quals_dir": str(quals_dir)},
        "stages": {"quals": "Qualification: bots of the same model play each other; the top bots advance.",
                   "tourney": "Tournament: qualified bots from every model play each other."},
        "games": games_index,
        "models": [{**models[m], "bots": sorted(models[m]["bots"])} for m in sorted(models)],
        "families": [{"id": f, "models": ms} for f, ms in sorted(families.items())],
    }
    n = dump_json(out_root / "index.json", index)
    lock = replay_format.write_lock(out_root)
    (out_root / "sources.json").write_text(json.dumps(sources, indent=1) + "\n")
    files = [p for p in out_root.rglob("*") if p.is_file()]
    log(f"index.json {n} bytes; total export {sum(p.stat().st_size for p in files) / 1e6:.1f} MB in {len(files)} files; "
        f"replays {lock['bytes'] / 1e6:.1f} MB (hash {lock['hash']}); {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
