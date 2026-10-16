from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import io
import inspect
import json
import math
import multiprocessing as mp
import pickle
import random
import re
import traceback
import time
from functools import partial
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Callable

import numpy as np
from game_arena import base, utils
from game_arena.typing import BotPath, PolicyFn


logger = utils.setup_logging("exp_randomness.log", "exp_randomness", to_stdout=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return safe or "unknown_model"


def _world_results_dir(results_dir: Path, game: str, world: str) -> Path:
    world_dir = results_dir / f"{game}_{world}"
    world_dir.mkdir(parents=True, exist_ok=True)
    return world_dir


def _parent_results_path(results_dir: Path, game: str, world: str, parent_model: str) -> Path:
    world_dir = _world_results_dir(results_dir, game, world)
    return world_dir / f"{_safe_filename(parent_model)}.json"


def _load_parent_json(path: Path, game: str, world: str, parent_model: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": 1,
            "game": game,
            "world": world,
            "parent_model": parent_model,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "last_run_settings": {},
            "bot_hashes": {},
            "bots": {},
            "summary": {},
        }
    with open(path, "r") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON in {path}: expected object")
    payload.setdefault("schema_version", 1)
    payload.setdefault("created_at", _utc_now())
    payload.setdefault("updated_at", _utc_now())
    payload["game"] = game
    payload["world"] = world
    payload["parent_model"] = parent_model
    payload.setdefault("last_run_settings", {})
    payload.setdefault("bot_hashes", {})
    payload.setdefault("bots", {})
    payload.setdefault("summary", {})
    return payload


def _save_parent_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    payload["updated_at"] = _utc_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f"{path.name}.tmp"
    write_payload: dict[str, Any] = {
        "summary": payload.get("summary", {}),
        "game": payload.get("game"),
        "world": payload.get("world"),
        "parent_model": payload.get("parent_model"),
        "schema_version": payload.get("schema_version", 1),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "last_run_settings": payload.get("last_run_settings", {}),
        "bot_hashes": payload.get("bot_hashes", {}),
        "bots": payload.get("bots", {}),
    }
    for k, v in payload.items():
        if k not in write_payload:
            write_payload[k] = v
    with open(tmp_path, "w") as f:
        json.dump(write_payload, f, indent=2)
    tmp_path.replace(path)


def _hash_bot_code(examples_dir: Path, bot_name: str) -> str:
    py_code = examples_dir / bot_name / "2.python_code.py"
    if not py_code.exists():
        raise FileNotFoundError(f"Bot code not found for hashing: {py_code}")
    return hashlib.sha256(py_code.read_bytes()).hexdigest()


def _collect_bot_hashes_by_parent(examples_dir: Path, bot_names: list[str]) -> dict[str, dict[str, str]]:
    hashes: dict[str, dict[str, str]] = defaultdict(dict)
    for bot_name in sorted(bot_names):
        parent = bot_name.split("/")[0]
        hashes[parent][bot_name] = _hash_bot_code(examples_dir, bot_name)
    return {parent: dict(sorted(by_bot.items())) for parent, by_bot in sorted(hashes.items())}


def _validate_existing_hashes_or_die(
    world_dir: Path,
    expected_hashes_by_parent: dict[str, dict[str, str]],
) -> None:
    mismatches: list[str] = []
    for parent_json in sorted(world_dir.glob("*.json")):
        try:
            with open(parent_json, "r") as f:
                payload = json.load(f)
        except Exception as e:
            mismatches.append(f"{parent_json}: failed to load JSON ({type(e).__name__}: {e})")
            continue
        if not isinstance(payload, dict):
            mismatches.append(f"{parent_json}: expected JSON object at top level")
            continue
        parent_model = payload.get("parent_model")
        if not isinstance(parent_model, str) or not parent_model:
            mismatches.append(f"{parent_json}: missing/invalid top-level 'parent_model'")
            continue
        expected = expected_hashes_by_parent.get(parent_model)
        if expected is None:
            mismatches.append(
                f"{parent_json}: parent_model '{parent_model}' does not exist in current bot set"
            )
            continue
        stored_hashes = payload.get("bot_hashes")
        if not isinstance(stored_hashes, dict):
            mismatches.append(f"{parent_json}: missing/invalid top-level 'bot_hashes'")
            continue
        stored = {str(k): str(v) for k, v in stored_hashes.items()}
        # Allow keyset drift (new bots added / limit_model_bots changed). Only fail on
        # true conflicts where the same bot key has a different hash.
        differing: list[str] = []
        for bot_key in sorted(set(stored.keys()) & set(expected.keys())):
            old_v = stored.get(bot_key)
            new_v = expected.get(bot_key)
            if old_v != new_v:
                differing.append(f"{bot_key}: stored={old_v} current={new_v}")
            if len(differing) >= 5:
                break
        if differing:
            mismatches.append(
                f"{parent_json}: bot_hashes mismatch. Examples: {'; '.join(differing)}"
            )
    if mismatches:
        lines = [
            f"Found bot hash mismatches in existing results for {world_dir}.",
            "Manually delete old bot result JSON files for this game/world and rerun.",
            "Mismatches:",
        ]
        lines.extend([f"- {m}" for m in mismatches])
        raise SystemExit("\n".join(lines))


def get_model_blacklist_whitelist(
    model_blacklist_file: Optional[str],
    model_whitelist_file: Optional[str],
    model_blacklist: Optional[list[str]],
    model_whitelist: Optional[list[str]],
) -> tuple[list[str], Optional[list[str]]]:
    b_res: list[str] = []
    w_res: list[str] = []
    whitelist_loaded = False
    if model_blacklist_file is not None:
        with open(model_blacklist_file, "r") as f:
            b_res.extend(json.load(f)["model_ignore"])
    if model_whitelist_file is not None:
        with open(model_whitelist_file, "r") as f:
            w_res.extend(json.load(f)["model_whitelist"])
        whitelist_loaded = True
    if model_blacklist is not None:
        b_res.extend(model_blacklist)
    if model_whitelist is not None:
        w_res.extend(model_whitelist)
        whitelist_loaded = True
    b_res = sorted(set(b_res))
    w_res = sorted(set(w_res))
    if not whitelist_loaded:
        return b_res, None
    return b_res, w_res


class SeededRandomPolicy:
    """Pickle-safe seeded random policy for forkserver workers."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def __call__(self, _debug_legal_moves, **kwargs):
        move = self._rng.choice(_debug_legal_moves)
        if hasattr(move, "get_unparsed_str"):
            return move.get_unparsed_str()
        return move


def _make_seeded_random_policy(seed: int) -> PolicyFn:
    return SeededRandomPolicy(seed)


def _build_policy_load_error_trial(seed: int, seat: int, repeat: int, exception: Exception) -> dict[str, Any]:
    return {
        "seed": seed,
        "seat": seat,
        "repeat": repeat,
        "ok": False,
        "done": False,
        "winner": "error",
        "time_elapsed": None,
        "error_kind": "error",
        "exception": f"policy_load_error: {type(exception).__name__}: {exception}"[:500],
        "bot_action_count": 0,
        "bot_action_digest": None,
        "bot_actions_sample": "[]",
        "runner": "policy_load_error",
        "runner_fallback_reason": None,
    }


def _extract_labeled_actions(
    match_result: dict[str, Any],
    bot_player_idx: int,
    random_player_idx: int,
) -> list[Any]:
    run_payload = match_result.get("r")
    action_history: Any = None
    if isinstance(run_payload, dict):
        action_history = run_payload.get("action_history")
    if not isinstance(action_history, str):
        action_history = match_result.get("action_history")
    if not isinstance(action_history, str):
        return []
    try:
        history = json.loads(action_history)
    except json.JSONDecodeError:
        return []
    labeled_actions: list[Any] = []
    for step in history:
        if not isinstance(step, list) or len(step) < 2:
            continue
        try:
            player_idx = int(step[0])
        except (TypeError, ValueError):
            continue
        if player_idx == bot_player_idx:
            labeled_actions.append(["B", step[1]])
        elif player_idx == random_player_idx:
            labeled_actions.append(["R", step[1]])
    return labeled_actions


def _digest_actions(actions: list[Any]) -> str:
    raw = json.dumps(actions, separators=(",", ":"), sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _compact_actions_sample(actions: list[Any], limit: int = 12) -> str:
    return json.dumps(actions[:limit], separators=(",", ":"), ensure_ascii=True)


def _run_trial(
    *,
    game_cls: Callable[..., Any],
    game_config: dict[str, Any],
    bot_path: BotPath,
    seed: int,
    seed_world: bool,
    seat: int,
    repeat: int,
    timeout: int,
    temp_path: Path,
) -> dict[str, Any]:
    random_policy = _make_seeded_random_policy(seed)
    random_name = f"seeded_random_{seed}"
    if seat == 0:
        bot_paths = [bot_path, (random_name, random_policy)]
        bot_idx = 0
    else:
        bot_paths = [(random_name, random_policy), bot_path]
        bot_idx = 1
    random_idx = 1 - bot_idx

    txt_path = temp_path / f"exp_randomness_{bot_path[0].replace('/', '_')}_{seed}_{seat}_{repeat}.txt"
    fallback_reason: Optional[str] = None
    runner = "play_game_with_timeout"
    start_time = time.time()
    try:
        result = base.play_game_with_timeout(
            game_cls=game_cls,  # type: ignore[arg-type]
            game_config=game_config,
            bot_paths=bot_paths,
            seed=seed if seed_world else None,
            timeout=timeout,
        )
    except Exception as e:
        fallback_reason = f"{type(e).__name__}: {e}"
        logger.error(
            f"play_game_with_timeout raised for bot={bot_path[0]}, seed={seed}, seat={seat}, repeat={repeat}. Marking trial fatal_exception. error={fallback_reason}"
        )
        result = {
            "name0": bot_paths[0][0],
            "name1": bot_paths[1][0],
            "winner": "fatal_exception",
            "done": False,
            "r": None,
            "seed": None,
            "time_elapsed": time.time() - start_time,
            "exception": fallback_reason,
        }
    finally:
        if txt_path.exists():
            txt_path.unlink()

    actions = _extract_labeled_actions(result, bot_idx, random_idx)
    action_digest = _digest_actions(actions) if actions else None
    winner = result.get("winner")
    trial: dict[str, Any] = {
        "seed": seed,
        "seat": seat,
        "repeat": repeat,
        "ok": bool(result.get("done")) and action_digest is not None,
        "done": result.get("done"),
        "winner": winner,
        "time_elapsed": result.get("time_elapsed"),
        "error_kind": None,
        "exception": None,
        "bot_action_count": len(actions),
        "bot_action_digest": action_digest,
        "bot_actions_sample": _compact_actions_sample(actions, limit=12),
        "runner": runner,
        "runner_fallback_reason": fallback_reason,
    }
    if not trial["ok"]:
        if winner == "timeout":
            trial["error_kind"] = "timeout"
        elif winner == "error":
            trial["error_kind"] = "error"
        elif winner == "fatal_exception":
            trial["error_kind"] = "fatal_exception"
        else:
            trial["error_kind"] = "unknown_error"
        if isinstance(result.get("exception"), str):
            trial["exception"] = result["exception"][:500]
        elif isinstance(result.get("r"), dict) and isinstance(result["r"].get("exception"), str):
            trial["exception"] = result["r"]["exception"][:500]
    return trial


def _ensure_bot_entry(parent_entry: dict[str, Any], bot_name: str, n_seeds: int, repeats: int) -> dict[str, Any]:
    bots = parent_entry.setdefault("bots", {})
    bot_entry = bots.setdefault(
        bot_name,
        {
            "model_name": bot_name.split("/")[0],
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "requested_n_seeds": n_seeds,
            "requested_repeats": repeats,
            "by_seed": {},
            "summary": {},
            "status": "pending",
        },
    )
    bot_entry.setdefault("by_seed", {})
    bot_entry["requested_n_seeds"] = max(int(bot_entry.get("requested_n_seeds", 0)), n_seeds)
    bot_entry["requested_repeats"] = max(int(bot_entry.get("requested_repeats", 0)), repeats)
    return bot_entry


def _count_missing_trials(bot_entry: dict[str, Any], n_seeds: int, repeats: int) -> int:
    missing = 0
    by_seed = bot_entry.get("by_seed", {})
    for seed in range(n_seeds):
        seed_entry = by_seed.get(str(seed), {})
        for seat in (0, 1):
            seat_trials = seed_entry.get(str(seat), [])
            if not isinstance(seat_trials, list):
                seat_trials = []
            missing += max(0, repeats - len(seat_trials))
    return missing


def _summarize_bot(bot_entry: dict[str, Any], n_seeds: int, repeats: int) -> dict[str, Any]:
    by_seed = bot_entry.get("by_seed", {})
    expected_trials = n_seeds * 2 * repeats
    completed_trials = 0
    successful_trials = 0
    comparable_trials = 0
    timeout_trials = 0
    error_trials = 0
    fatal_exception_trials = 0
    unknown_trials = 0
    sequence_comparisons = 0
    sequence_diff_count = 0
    seed_seat_groups_with_diff = 0
    seeds_with_any_diff = 0
    diff_examples: list[dict[str, Any]] = []

    for seed in range(n_seeds):
        seed_has_diff = False
        seed_entry = by_seed.get(str(seed), {})
        for seat in (0, 1):
            seat_trials = seed_entry.get(str(seat), [])
            if not isinstance(seat_trials, list):
                seat_trials = []

            comparable_in_group: list[tuple[int, dict[str, Any]]] = []
            for repeat in range(repeats):
                if repeat >= len(seat_trials):
                    continue
                trial = seat_trials[repeat]
                if not isinstance(trial, dict):
                    continue
                completed_trials += 1
                if trial.get("ok") and trial.get("bot_action_digest"):
                    successful_trials += 1
                else:
                    kind = trial.get("error_kind")
                    if kind == "timeout":
                        timeout_trials += 1
                    elif kind == "error":
                        error_trials += 1
                    elif kind == "fatal_exception":
                        fatal_exception_trials += 1
                    else:
                        unknown_trials += 1
                # Include null digests as explicit values, but exclude timeout trials.
                if trial.get("winner") != "timeout" and "bot_action_digest" in trial:
                    comparable_trials += 1
                    comparable_in_group.append((repeat, trial))

            group_has_diff = False
            if len(comparable_in_group) >= 2:
                baseline_repeat, baseline = comparable_in_group[0]
                baseline_digest = baseline.get("bot_action_digest")
                for repeat, current in comparable_in_group[1:]:
                    sequence_comparisons += 1
                    if current.get("bot_action_digest") != baseline_digest:
                        sequence_diff_count += 1
                        group_has_diff = True
                        seed_has_diff = True
                        if len(diff_examples) < 5:
                            diff_examples.append(
                                {
                                    "seed": seed,
                                    "seat": seat,
                                    "baseline_repeat": baseline_repeat,
                                    "repeat": repeat,
                                    "baseline_digest": baseline_digest,
                                    "repeat_digest": current.get("bot_action_digest"),
                                    "baseline_actions_sample": baseline.get("bot_actions_sample", "[]"),
                                    "repeat_actions_sample": current.get("bot_actions_sample", "[]"),
                                }
                            )
            if group_has_diff:
                seed_seat_groups_with_diff += 1
        if seed_has_diff:
            seeds_with_any_diff += 1

    failed_trials = completed_trials - successful_trials
    complete = completed_trials == expected_trials
    if fatal_exception_trials > 0:
        status = "fatal_exception"
    elif not complete:
        status = "pending"
    elif sequence_comparisons == 0:
        status = "insufficient_data"
    elif sequence_diff_count > 0:
        status = "random"
    else:
        status = "deterministic"

    return {
        "status": status,
        "expected_trials": expected_trials,
        "completed_trials": completed_trials,
        "successful_trials": successful_trials,
        "comparable_trials": comparable_trials,
        "failed_trials": failed_trials,
        "timeout_trials": timeout_trials,
        "error_trials": error_trials,
        "fatal_exception_trials": fatal_exception_trials,
        "unknown_trials": unknown_trials,
        "sequence_comparisons": sequence_comparisons,
        "sequence_diff_count": sequence_diff_count,
        "diff_rate": (sequence_diff_count / sequence_comparisons) if sequence_comparisons > 0 else None,
        "seed_seat_groups_with_diff": seed_seat_groups_with_diff,
        "seeds_with_any_diff": seeds_with_any_diff,
        "is_random": sequence_diff_count > 0,
        "diff_examples": diff_examples,
    }


def _summarize_parent(parent_entry: dict[str, Any], n_seeds: int, repeats: int) -> dict[str, Any]:
    bots = parent_entry.get("bots", {})
    status_counts: dict[str, int] = {}
    status_by_name: dict[str, str] = {}
    by_name: dict[str, dict[str, Any]] = {}
    done_bots = 0
    for bot_name, bot_entry in bots.items():
        if not isinstance(bot_entry, dict):
            continue
        summary = _summarize_bot(bot_entry, n_seeds, repeats)
        status = summary["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        status_by_name[bot_name] = status
        bot_entry["summary"] = summary
        bot_entry["status"] = status
        bots[bot_name] = bot_entry
        if int(summary.get("completed_trials", 0)) == int(summary.get("expected_trials", 0)):
            done_bots += 1
        by_name[bot_name] = {
            "status": summary.get("status"),
            "is_random": summary.get("is_random"),
            "fatal_exception_trials": summary.get("fatal_exception_trials"),
            "sequence_diff_count": summary.get("sequence_diff_count"),
            "sequence_comparisons": summary.get("sequence_comparisons"),
            "comparable_trials": summary.get("comparable_trials"),
            "completed_trials": summary.get("completed_trials"),
            "expected_trials": summary.get("expected_trials"),
            "failed_trials": summary.get("failed_trials"),
        }

    return {
        "n_bots": len(bots),
        "done_bots": done_bots,
        "status_by_name": dict(sorted(status_by_name.items())),
        "status_counts": status_counts,
        "by_name": dict(sorted(by_name.items())),
    }


def _discover_all_game_world_pairs() -> list[tuple[str, str]]:
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from experimental import exp_utils  # type: ignore
        pairs = sorted({(g, w) for g, w, _colname, _match in exp_utils.MAIN_GAMES_WORLD_COLUMNS})
        if pairs:
            return pairs
        logger.warning("experimental.exp_utils MAIN_GAMES_WORLD_COLUMNS is empty; falling back to examples directory scan")
    except Exception as e:
        logger.warning(f"Failed to import experimental.exp_utils ({type(e).__name__}: {e}); falling back to examples directory scan")

    pairs_fallback: list[tuple[str, str]] = []
    game_arena_dir = utils.get_game_arena_dir()
    for game_dir in sorted(game_arena_dir.iterdir()):
        if not game_dir.is_dir():
            continue
        examples_dir = game_dir / "examples"
        if not examples_dir.exists() or not examples_dir.is_dir():
            continue
        for world_dir in sorted(examples_dir.iterdir()):
            if world_dir.is_dir() and world_dir.name.startswith("world"):
                pairs_fallback.append((game_dir.name, world_dir.name))
    return sorted(set(pairs_fallback))


def _load_filtered_bots(
    *,
    game_str: str,
    world: str,
    limit_model_bots: Optional[int],
    model_blacklist: Optional[list[str]],
    model_whitelist: Optional[list[str]],
) -> list[tuple[str, PolicyFn]]:
    bots = list(
        utils.get_bot_paths_from_world(
            game_str,
            world,
            add_random=False,
            allowed_bot_nums=','.join(str(i) for i in range(1, limit_model_bots + 1)) if limit_model_bots is not None else None,
        ).items()
    )
    assert len(bots) > 1, f"Need at least 2 bots to run quals. Got {len(bots)} bots. in game {game_str}, world {world}"

    if model_blacklist:
        pre_filtered_len = len(bots)
        bots = [b for b in bots if b[0].split("/")[0] not in model_blacklist]
        if len(bots) != pre_filtered_len:
            logger.info(f"pre-blacklisting #bots = {pre_filtered_len}, post-blacklisting #bots = {len(bots)}")

    if model_whitelist is not None:
        pre_filtered_len = len(bots)
        bots = [b for b in bots if b[0].split("/")[0] in model_whitelist]
        if len(bots) != pre_filtered_len:
            logger.info(f"pre-whitelisting #bots = {pre_filtered_len}, post-whitelisting #bots = {len(bots)}")

    assert len(bots) > 0, f"No bots remaining after filtering. game={game_str}, world={world}"
    loaded_bots = []
    for bot_name, bot_path in bots:
        loaded_bots.append(utils.get_policy_fn_with_memory(bot_name, bot_path))
    return sorted(loaded_bots, key=lambda x: x[0])


def _prepare_world_selection_and_hashes(
    *,
    continue_dir: Path,
    game_str: str,
    world: str,
    limit_model_bots: Optional[int],
    model_blacklist: Optional[list[str]],
    model_whitelist: Optional[list[str]],
) -> tuple[Path, dict[str, list[str]], dict[str, dict[str, str]]]:
    world_dir = _world_results_dir(continue_dir, game_str, world)
    examples_dir = utils.get_examples_dir(game_str) / world

    filtered_bots = _load_filtered_bots(
        game_str=game_str,
        world=world,
        limit_model_bots=limit_model_bots,
        model_blacklist=model_blacklist,
        model_whitelist=model_whitelist,
    )
    assert len(filtered_bots) > 1, f"Need at least 2 bots to run hash checks. Got {len(filtered_bots)} bots. in game {game_str}, world {world}"
    bot_names_for_hash = sorted(bot_name for bot_name, _policy in filtered_bots)
    expected_hashes_by_parent = _collect_bot_hashes_by_parent(examples_dir, bot_names_for_hash)
    _validate_existing_hashes_or_die(world_dir, expected_hashes_by_parent)

    bots_by_parent: dict[str, list[str]] = defaultdict(list)
    for bot_name, _unused_policy in filtered_bots:
        parent_model = bot_name.split("/")[0]
        bots_by_parent[parent_model].append(bot_name)
    for parent_model in bots_by_parent:
        bots_by_parent[parent_model] = sorted(bots_by_parent[parent_model])

    return world_dir, dict(sorted(bots_by_parent.items())), expected_hashes_by_parent


def _save_parent_summary(parent_entry: dict[str, Any], parent_path: Path, n_seeds: int, repeats: int) -> None:
    parent_entry["summary"] = _summarize_parent(parent_entry, n_seeds=n_seeds, repeats=repeats)
    _save_parent_json_atomic(parent_path, parent_entry)


def _save_bot_progress(
    parent_entry: dict[str, Any],
    parent_path: Path,
    bot_name: str,
    bot_entry: dict[str, Any],
    n_seeds: int,
    repeats: int,
) -> None:
    bot_entry["summary"] = _summarize_bot(bot_entry, n_seeds=n_seeds, repeats=repeats)
    bot_entry["status"] = bot_entry["summary"]["status"]
    bot_entry["updated_at"] = _utc_now()
    parent_entry["bots"][bot_name] = bot_entry
    _save_parent_summary(parent_entry, parent_path, n_seeds=n_seeds, repeats=repeats)


def run_parent_worker(
    *,
    game_str: str,
    world: str,
    parent_model: str,
    parent_bots: list[str],
    expected_parent_hashes: dict[str, str],
    continue_dir: Path,
    n_seeds: int,
    repeats: int,
    timeout: int,
    limit_model_bots: Optional[int],
    seed_world: bool,
) -> dict[str, Any]:
    world_dir = _world_results_dir(continue_dir, game_str, world)
    examples_dir = utils.get_examples_dir(game_str) / world

    game = utils.get_game(game_name=game_str)
    config = utils.get_config_file(game_str, world)
    try:
        game_accepts_seed = "seed" in inspect.signature(game).parameters
    except Exception:
        game_accepts_seed = False

    run_id = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    temp_path = utils.get_temp_path(f"exp_randomness_{run_id}_{_safe_filename(game_str)}_{_safe_filename(world)}_{_safe_filename(parent_model)}")

    parent_path = _parent_results_path(continue_dir, game_str, world, parent_model)
    parent_entry = _load_parent_json(parent_path, game_str, world, parent_model)
    parent_entry["bot_hashes"] = dict(sorted(expected_parent_hashes.items()))
    parent_entry["last_run_settings"] = {
        "n_seeds": n_seeds,
        "repeats": repeats,
        "timeout": timeout,
        "limit_model_bots": limit_model_bots,
        "seed_world": bool(seed_world),
        "updated_at": _utc_now(),
        "run_id": run_id,
        "world_dir": str(world_dir),
    }
    for bot_name in parent_bots:
        _ensure_bot_entry(parent_entry, bot_name, n_seeds=n_seeds, repeats=repeats)
    _save_parent_summary(parent_entry, parent_path, n_seeds=n_seeds, repeats=repeats)
    logger.info(
        f"start parent={parent_model} game={game_str} world={world} "
        f"bots={len(parent_bots)} n_seeds={n_seeds} repeats={repeats} "
        f"timeout={timeout} limit_model_bots={limit_model_bots} seed_world={bool(seed_world)} "
        f"run_id={run_id} -> {parent_path}"
    )

    for bot_i, bot_name in enumerate(parent_bots, start=1):
        bot_entry = _ensure_bot_entry(parent_entry, bot_name, n_seeds=n_seeds, repeats=repeats)
        missing_trials = _count_missing_trials(bot_entry, n_seeds=n_seeds, repeats=repeats)
        if missing_trials == 0:
            _save_bot_progress(
                parent_entry,
                parent_path,
                bot_name,
                bot_entry,
                n_seeds=n_seeds,
                repeats=repeats,
            )
            logger.info(f"  ({bot_i}/{len(parent_bots)}) {bot_name}: already complete, skipping")
            continue

        by_seed = bot_entry.setdefault("by_seed", {})
        for seed in range(n_seeds):
            seed_key = str(seed)
            seed_entry = by_seed.setdefault(seed_key, {"0": [], "1": []})
            game_cls_for_trial: Callable[..., Any]
            if game_accepts_seed and seed_world:
                game_cls_for_trial = partial(game, seed=seed)
            else:
                game_cls_for_trial = game
            for seat in (0, 1):
                seat_trials = seed_entry.setdefault(str(seat), [])
                while len(seat_trials) < repeats:
                    repeat = len(seat_trials)
                    try:
                        bot_path: BotPath = (bot_name, examples_dir / bot_name)
                    except Exception as e:
                        trial = _build_policy_load_error_trial(seed=seed, seat=seat, repeat=repeat, exception=e)
                    else:
                        trial = _run_trial(
                            game_cls=game_cls_for_trial,
                            game_config=config,
                            bot_path=bot_path,
                            seed=seed,
                            seed_world=seed_world,
                            seat=seat,
                            repeat=repeat,
                            timeout=timeout,
                            temp_path=temp_path,
                        )
                    seat_trials.append(trial)
                    _save_bot_progress(
                        parent_entry,
                        parent_path,
                        bot_name,
                        bot_entry,
                        n_seeds=n_seeds,
                        repeats=repeats,
                    )

        _save_bot_progress(
            parent_entry,
            parent_path,
            bot_name,
            bot_entry,
            n_seeds=n_seeds,
            repeats=repeats,
        )
        logger.info(
            f"  ({bot_i}/{len(parent_bots)}) {bot_name}: done status={bot_entry['status']} diff_count={bot_entry['summary']['sequence_diff_count']}"
        )

    _save_parent_summary(parent_entry, parent_path, n_seeds=n_seeds, repeats=repeats)
    return {
        "game": game_str,
        "world": world,
        "parent_model": parent_model,
        "world_dir": str(world_dir),
        "summary": parent_entry["summary"],
    }


def _run_task(task: dict[str, Any]) -> dict[str, Any]:
    return run_parent_worker(
        game_str=str(task["game"]),
        world=str(task["world"]),
        parent_model=str(task["parent_model"]),
        parent_bots=list(task["parent_bots"]),
        expected_parent_hashes=dict(task["expected_parent_hashes"]),
        continue_dir=Path(task["continue_dir"]),
        n_seeds=int(task["n_seeds"]),
        repeats=int(task["repeats"]),
        timeout=int(task["timeout"]),
        limit_model_bots=task.get("limit_model_bots"),
        seed_world=bool(task.get("seed_world", False)),
    )


def _worker_entry(task: dict[str, Any], result_path: Path) -> None:
    try:
        result = _run_task(task)
        payload = {"ok": True, "result": result}
    except Exception:
        payload = {"ok": False, "error": traceback.format_exc()}
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with open(result_path, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def _format_child_statuses(summary: dict[str, Any]) -> str:
    status_by_name = summary.get("status_by_name")
    if not isinstance(status_by_name, dict) or not status_by_name:
        return "[]"
    parts: list[str] = []
    for bot_name, status in sorted(status_by_name.items()):
        child_name = str(bot_name).split("/")[-1]
        status_word = str(status).split()[0]
        parts.append(f"{child_name}:{status_word}")
    return f"[{', '.join(parts)}]"


def _execute_tasks_with_processes(tasks: list[dict[str, Any]], max_workers: int) -> list[dict[str, Any]]:
    if not tasks:
        return []
    max_workers = max(1, int(max_workers))
    if max_workers == 1:
        out: list[dict[str, Any]] = []
        for i, task in enumerate(tasks, start=1):
            label = f"{task['game']}/{task['world']}/{task['parent_model']}"
            logger.info(f"[{i}/{len(tasks)}] running {label} in current process")
            result = _run_task(task)
            out.append(result)
            logger.info(f"done {label} (finished {i}/{len(tasks)}) {_format_child_statuses(result.get('summary', {}))}")
        return out

    tmp_dir = utils.get_temp_path(f"exp_randomness_orchestrator_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}")
    pending = list(enumerate(tasks))
    running: list[tuple[int, dict[str, Any], mp.Process, Path]] = []
    completed_results: list[dict[str, Any]] = []
    failures: list[str] = []

    while pending or running:
        while pending and len(running) < max_workers:
            task_idx, task = pending.pop(0)
            result_path = tmp_dir / f"task_{task_idx}.json"
            proc = mp.Process(target=_worker_entry, args=(task, result_path))
            proc.start()
            running.append((task_idx, task, proc, result_path))

        if not running:
            break

        time.sleep(0.1)
        next_running: list[tuple[int, dict[str, Any], mp.Process, Path]] = []
        for task_idx, task, proc, result_path in running:
            if proc.is_alive():
                next_running.append((task_idx, task, proc, result_path))
                continue
            proc.join()
            label = f"{task['game']}/{task['world']}/{task['parent_model']}"
            if not result_path.exists():
                failures.append(f"{label}: worker produced no result file (exit_code={proc.exitcode})")
                continue
            with open(result_path, "r") as f:
                payload = json.load(f)
            if not isinstance(payload, dict) or not payload.get("ok"):
                failures.append(f"{label}: {payload.get('error', 'unknown worker failure')}")
                continue
            result = payload["result"]
            completed_results.append(result)
            logger.info(f"done {label} (finished {len(completed_results)}/{len(tasks)}) {_format_child_statuses(result.get('summary', {}))}")
        running = next_running

    if failures:
        msg_lines = [f"{len(failures)}/{len(tasks)} worker tasks failed:"]
        msg_lines.extend([f"- {f}" for f in failures[:20]])
        raise SystemExit("\n".join(msg_lines))
    return completed_results


def _is_parent_task_complete(
    *,
    continue_dir: Path,
    game: str,
    world: str,
    parent_model: str,
    parent_bots: list[str],
    n_seeds: int,
    repeats: int,
) -> bool:
    parent_path = _parent_results_path(continue_dir, game, world, parent_model)
    if not parent_path.exists():
        return False
    try:
        with open(parent_path, "r") as f:
            payload = json.load(f)
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    bots = payload.get("bots")
    if not isinstance(bots, dict):
        return False
    for bot_name in parent_bots:
        bot_entry = bots.get(bot_name)
        if not isinstance(bot_entry, dict):
            return False
        if _count_missing_trials(bot_entry, n_seeds=n_seeds, repeats=repeats) > 0:
            return False
    return True


def _build_tasks(
    *,
    continue_dir: Path,
    target_pairs: list[tuple[str, str]],
    n_seeds: int,
    repeats: int,
    timeout_by_game: dict[str, int],
    limit_model_bots: Optional[int],
    seed_world: bool,
    model_blacklist: Optional[list[str]],
    model_whitelist: Optional[list[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tasks: list[dict[str, Any]] = []
    complete_parent_specs: list[dict[str, Any]] = []
    for game_str, world in target_pairs:
        timeout = int(timeout_by_game[game_str])
        world_dir, bots_by_parent, expected_hashes_by_parent = _prepare_world_selection_and_hashes(
            continue_dir=continue_dir,
            game_str=game_str,
            world=world,
            limit_model_bots=limit_model_bots,
            model_blacklist=model_blacklist,
            model_whitelist=model_whitelist,
        )
        runnable_parent_models = 0
        for parent_model, parent_bots in sorted(bots_by_parent.items()):
            parent_path = _parent_results_path(continue_dir, game_str, world, parent_model)
            if _is_parent_task_complete(
                continue_dir=continue_dir,
                game=game_str,
                world=world,
                parent_model=parent_model,
                parent_bots=parent_bots,
                n_seeds=n_seeds,
                repeats=repeats,
            ):
                complete_parent_specs.append(
                    {
                        "game": game_str,
                        "world": world,
                        "parent_model": parent_model,
                        "parent_path": str(parent_path),
                        "parent_bots": list(parent_bots),
                        "expected_parent_hashes": expected_hashes_by_parent.get(parent_model, {}),
                    }
                )
                continue
            runnable_parent_models += 1
            tasks.append(
                {
                    "game": game_str,
                    "world": world,
                    "parent_model": parent_model,
                    "parent_bots": parent_bots,
                    "expected_parent_hashes": expected_hashes_by_parent.get(parent_model, {}),
                    "continue_dir": str(continue_dir),
                    "n_seeds": n_seeds,
                    "repeats": repeats,
                    "timeout": timeout,
                    "limit_model_bots": limit_model_bots,
                    "seed_world": bool(seed_world),
                }
            )
        if runnable_parent_models > 0:
            logger.info(
                f"Prepared {game_str}/{world}: parent_models={runnable_parent_models} world_dir={world_dir}"
            )
    return tasks, complete_parent_specs


def _refresh_complete_parent_summaries(
    *,
    complete_parent_specs: list[dict[str, Any]],
    n_seeds: int,
    repeats: int,
) -> list[dict[str, Any]]:
    refreshed_results: list[dict[str, Any]] = []
    for spec in complete_parent_specs:
        game_str = str(spec["game"])
        world = str(spec["world"])
        parent_model = str(spec["parent_model"])
        parent_path = Path(str(spec["parent_path"]))
        parent_entry = _load_parent_json(parent_path, game_str, world, parent_model)
        expected_parent_hashes = spec.get("expected_parent_hashes")
        if isinstance(expected_parent_hashes, dict):
            parent_entry["bot_hashes"] = dict(sorted((str(k), str(v)) for k, v in expected_parent_hashes.items()))
        for bot_name in spec.get("parent_bots", []):
            if isinstance(bot_name, str):
                _ensure_bot_entry(parent_entry, bot_name, n_seeds=n_seeds, repeats=repeats)
        _save_parent_summary(parent_entry, parent_path, n_seeds=n_seeds, repeats=repeats)
        refreshed_results.append(
            {
                "game": game_str,
                "world": world,
                "parent_model": parent_model,
                "summary": parent_entry.get("summary", {}),
            }
        )
    return refreshed_results


def _build_aggregate_summary(task_results: list[dict[str, Any]], mode: str, continue_dir: Path) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for tr in task_results:
        s = tr.get("summary", {})
        if isinstance(s, dict):
            for k, v in s.get("status_counts", {}).items():
                status_counts[str(k)] = status_counts.get(str(k), 0) + int(v)
    return {
        "mode": mode,
        "continue_from": str(continue_dir),
        "n_tasks": len(task_results),
        "status_counts": status_counts,
    }


def _parse_positive_timeout(value: str, context: str) -> int:
    try:
        out = int(value)
    except Exception as e:
        raise ValueError(f"Invalid timeout value '{value}' in {context}: {type(e).__name__}: {e}")
    if out <= 0:
        raise ValueError(f"Timeout must be > 0 in {context}, got {out}")
    return out


def _resolve_timeout_by_game(timeout_arg: str, target_pairs: list[tuple[str, str]]) -> dict[str, int]:
    games = sorted({g for g, _w in target_pairs})
    timeout_spec = str(timeout_arg).strip()
    if not timeout_spec:
        raise ValueError("--timeout cannot be empty")

    # Simple form: single integer for all games.
    if "=" not in timeout_spec:
        t = _parse_positive_timeout(timeout_spec, "--timeout")
        return {g: t for g in games}

    # Mapping form: e.g. ALL=20;go=60;othello=60
    by_key_lower: dict[str, int] = {}
    parts = [p.strip() for p in timeout_spec.split(";") if p.strip()]
    if not parts:
        raise ValueError(f"Invalid --timeout mapping: '{timeout_spec}'")
    for part in parts:
        if "=" not in part:
            raise ValueError(f"Invalid --timeout mapping part '{part}'. Expected KEY=VALUE")
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid --timeout mapping part '{part}': empty key")
        t = _parse_positive_timeout(value, f"--timeout part '{part}'")
        by_key_lower[key.lower()] = t

    out: dict[str, int] = {}
    for game in games:
        game_key = game.lower()
        if game_key in by_key_lower:
            out[game] = by_key_lower[game_key]
        elif "all" in by_key_lower:
            out[game] = by_key_lower["all"]
        else:
            raise ValueError(
                f"Missing timeout for game '{game}' in --timeout='{timeout_spec}'. "
                "Provide ALL=<sec> or an explicit per-game entry."
            )
    return out


def _parse_game_world_dirname(name: str) -> Optional[tuple[str, str]]:
    m = re.match(r"^(?P<game>.+)_(?P<world>world.+)$", name)
    if m is None:
        return None
    return m.group("game"), m.group("world")


def _extract_status_by_name(payload: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    summary = payload.get("summary")
    if isinstance(summary, dict):
        sbn = summary.get("status_by_name")
        if isinstance(sbn, dict):
            for bot_name, status in sbn.items():
                out[str(bot_name)] = str(status)
    bots = payload.get("bots")
    if isinstance(bots, dict):
        for bot_name, bot_entry in bots.items():
            if not isinstance(bot_entry, dict):
                continue
            status = bot_entry.get("status")
            if status is None:
                bs = bot_entry.get("summary")
                if isinstance(bs, dict):
                    status = bs.get("status")
            if status is not None:
                out[str(bot_name)] = str(status)
    return out


def _collapse_statuses(statuses: list[str]) -> str:
    if not statuses:
        return "missing"
    priority = {
        "error": 9,
        "timeout": 8,
        "fatal_exception": 7,
        "pending": 6,
        "random": 5,
        "seedable_randomness": 4,
        "deterministic": 3,
        "insufficient_data": 2,
        "unknown": 1,
    }
    best = "unknown"
    best_score = -1
    for s in statuses:
        score = priority.get(s, 1)
        if score > best_score:
            best = s
            best_score = score
    return best


def _status_letter(status: str) -> str:
    mapping = {
        "error": "E",
        "timeout": "T",
        "deterministic": "D",
        "random": "R",
        "seedable_randomness": "S",
        "insufficient_data": "I",
        "pending": "P",
        "fatal_exception": "F",
        "unknown": "U",
        "missing": "N",
    }
    return mapping.get(status, "U")


def _latex_escape(s: str) -> str:
    return (
        s.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def _get_model_name_map() -> dict[str, str]:
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from experimental import exp_utils  # type: ignore
        model_map = getattr(exp_utils, "MODEL_NAME_MAP", {})
        if isinstance(model_map, dict):
            return {str(k): str(v) for k, v in model_map.items()}
    except Exception as e:
        logger.warning(f"Failed loading MODEL_NAME_MAP from experimental.exp_utils ({type(e).__name__}: {e})")
    return {}


def _get_main_game_world_col_map() -> tuple[list[tuple[str, str]], dict[tuple[str, str], str]]:
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from experimental import exp_utils  # type: ignore
        rows = getattr(exp_utils, "MAIN_GAMES_WORLD_COLUMNS", [])
        ordered: list[tuple[str, str]] = []
        col_map: dict[tuple[str, str], str] = {}
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, tuple) or len(row) < 3:
                    continue
                game, world, colname = row[0], row[1], row[2]
                key = (str(game), str(world))
                if key not in col_map:
                    ordered.append(key)
                col_map[key] = str(colname)
        return ordered, col_map
    except Exception as e:
        logger.warning(
            f"Failed loading MAIN_GAMES_WORLD_COLUMNS from experimental.exp_utils ({type(e).__name__}: {e})"
        )
    return [], {}


def _median_ignore_nan(values: list[float]) -> float:
    valid = [v for v in values if not math.isnan(v)]
    if not valid:
        return float("-inf")
    valid.sort()
    n = len(valid)
    mid = n // 2
    if n % 2 == 1:
        return valid[mid]
    return (valid[mid - 1] + valid[mid]) / 2.0


def _load_model_order_from_pkl(pkl_path: Path) -> list[str]:
    ordered, _ = _load_model_median_elo_from_pkl(pkl_path)
    return ordered


def _load_model_median_elo_from_pkl(pkl_path: Path) -> tuple[list[str], dict[str, float]]:
    if not pkl_path.exists():
        raise FileNotFoundError(f"--pkl not found: {pkl_path}")
    with open(pkl_path, "rb") as f:
        payload = pickle.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pickle top-level at {pkl_path}: expected dict")
    results = payload.get("results_models")
    if not isinstance(results, dict) or not results:
        raise ValueError(f"Invalid pickle results at {pkl_path}: expected non-empty dict under key 'results'")

    ratings_by_model: dict[str, list[float]] = defaultdict(list)
    for _colname, result in results.items():
        if not isinstance(result, dict):
            continue
        leaderboard = result.get("leaderboard_table_df")
        if leaderboard is None:
            continue
        try:
            rating_series = leaderboard["rating"]
        except Exception:
            continue
        try:
            items_iter = rating_series.items()
        except Exception:
            continue
        for model_name, rating in items_iter:
            try:
                rating_f = float(rating)
            except Exception:
                continue
            ratings_by_model[str(model_name)].append(rating_f)

    if not ratings_by_model:
        raise ValueError(f"Could not extract model ratings from {pkl_path}")

    median_by_model = {
        model_name: _median_ignore_nan(ratings)
        for model_name, ratings in ratings_by_model.items()
    }
    ordered = sorted(
        ratings_by_model.keys(),
        key=lambda m: median_by_model[m],
        reverse=True,
    )
    return ordered, median_by_model


def _split_bot_name(bot_name: str) -> tuple[str, str]:
    if "/" not in bot_name:
        return bot_name, bot_name
    parent, child = bot_name.split("/", 1)
    return parent, child


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _count_completed_trials_from_by_seed(bot_entry: dict[str, Any]) -> int:
    by_seed = bot_entry.get("by_seed")
    if not isinstance(by_seed, dict):
        return 0
    completed = 0
    for seed_entry in by_seed.values():
        if not isinstance(seed_entry, dict):
            continue
        for seat in ("0", "1"):
            trials = seed_entry.get(seat, [])
            if isinstance(trials, list):
                completed += sum(1 for trial in trials if isinstance(trial, dict))
    return completed


def _barplot_status_from_bot_entry(bot_entry: dict[str, Any]) -> str:
    summary = bot_entry.get("summary")
    if not isinstance(summary, dict):
        summary = {}

    status = bot_entry.get("status")
    if status is None:
        status = summary.get("status")
    status_str = str(status) if status is not None else ""

    completed_trials = _safe_int(summary.get("completed_trials"))
    expected_trials = _safe_int(summary.get("expected_trials"))
    if status_str == "pending" or (expected_trials > 0 and completed_trials < expected_trials):
        return "pending"

    timeout_trials = _safe_int(summary.get("timeout_trials"))
    error_trials = _safe_int(summary.get("error_trials"))
    error_like = error_trials
    timeout_like = timeout_trials

    if completed_trials <= 0:
        completed_trials = _count_completed_trials_from_by_seed(bot_entry)
    if completed_trials <= 0:
        return "pending"

    error_timeout_trials = error_like + timeout_like
    if completed_trials > 0 and (2 * error_timeout_trials >= completed_trials):
        if error_like >= timeout_like:
            return "error"
        return "timeout"

    if status_str == "random" or _safe_int(summary.get("sequence_diff_count")) > 0:
        return "random"
    return "deterministic"


def _extract_barplot_status_by_name(payload: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    bots = payload.get("bots")
    if isinstance(bots, dict):
        for bot_name, bot_entry in bots.items():
            if not isinstance(bot_entry, dict):
                continue
            out[str(bot_name)] = _barplot_status_from_bot_entry(bot_entry)
        if out:
            return out

    # Fallback for older payloads that don't carry per-bot summaries.
    fallback = _extract_status_by_name(payload)
    for bot_name, status in fallback.items():
        if status in ("error", "timeout", "pending", "deterministic", "random"):
            out[bot_name] = status
        elif status == "fatal_exception":
            out[bot_name] = "error"
        elif status == "random":
            out[bot_name] = "random"
        else:
            out[bot_name] = "deterministic"
    return out


def _status_to_barplot_letter(status: Optional[str]) -> Optional[str]:
    if status == "error":
        return "E"
    if status == "timeout":
        return "T"
    if status == "pending":
        return "P"
    if status == "deterministic":
        return "D"
    if status == "random":
        return "R"
    return None


def _barplot_status_from_letter(letter: str) -> str:
    if letter == "P":
        return "pending"
    if letter == "E":
        return "error"
    if letter == "T":
        return "timeout"
    if letter == "D":
        return "deterministic"
    if letter == "R":
        return "random"
    if letter == "S":
        return "seedable_randomness"
    raise ValueError(f"Unknown barplot letter: {letter}")


def _status_to_parsed_letter4(status: Optional[str]) -> Optional[str]:
    if status is None:
        return None
    if status == "pending":
        return "P"
    if status in ("error", "fatal_exception"):
        return "E"
    if status == "timeout":
        return "T"
    if status == "random":
        return "R"
    return "D"


def _extract_barplot_raw_and_parsed_by_name(payload: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    raw_by_name = _extract_status_by_name(payload)
    parsed_by_name: dict[str, str] = {}
    bots = payload.get("bots")
    if isinstance(bots, dict):
        for bot_name, bot_entry in bots.items():
            if not isinstance(bot_entry, dict):
                continue
            parsed_status = _barplot_status_from_bot_entry(bot_entry)
            parsed_letter = _status_to_parsed_letter4(parsed_status)
            if parsed_letter is not None:
                parsed_by_name[str(bot_name)] = parsed_letter
    for bot_name, raw_status in raw_by_name.items():
        parsed_by_name.setdefault(bot_name, _status_to_parsed_letter4(raw_status) or "D")
    return raw_by_name, parsed_by_name


def _extract_timeout_error_counts_by_name(payload: dict[str, Any]) -> dict[str, tuple[int, int, int]]:
    out: dict[str, tuple[int, int, int]] = {}
    bots = payload.get("bots")
    if not isinstance(bots, dict):
        return out
    for bot_name, bot_entry in bots.items():
        if not isinstance(bot_entry, dict):
            continue
        summary = bot_entry.get("summary")
        if not isinstance(summary, dict):
            summary = {}
        timeout_trials = _safe_int(summary.get("timeout_trials"))
        error_trials = (
            _safe_int(summary.get("error_trials"))
            + _safe_int(summary.get("fatal_exception_trials"))
            + _safe_int(summary.get("unknown_trials"))
        )
        completed_trials = _safe_int(summary.get("completed_trials"))
        if completed_trials <= 0:
            completed_trials = _count_completed_trials_from_by_seed(bot_entry)
        if completed_trials > 0 or timeout_trials > 0 or error_trials > 0:
            out[str(bot_name)] = (timeout_trials, error_trials, completed_trials)
    return out


def _combine_seeded_unseeded_statuses(
    *,
    seeded_letter: Optional[str],
    unseeded_letter: Optional[str],
) -> tuple[Optional[str], Optional[tuple[str, str, str]]]:
    if seeded_letter is None and unseeded_letter is None:
        return None, None
    if seeded_letter is None:
        return unseeded_letter, None
    if unseeded_letter is None:
        return seeded_letter, None
    assert seeded_letter is not None and unseeded_letter is not None
    if "P" in (seeded_letter, unseeded_letter):
        chosen_letter = "P"
    elif "T" in (seeded_letter, unseeded_letter):
        chosen_letter = "T"
    elif "E" in (seeded_letter, unseeded_letter):
        chosen_letter = "E"
    elif seeded_letter == "R":
        # New chaotic criterion: seeded randomness implies chaotic randomness.
        chosen_letter = "R"
    elif seeded_letter == "D" and unseeded_letter == "R":
        return "S", None
    elif seeded_letter == unseeded_letter:
        chosen_letter = seeded_letter
    else:
        chosen_letter = seeded_letter
    if seeded_letter != unseeded_letter:
        return chosen_letter, (seeded_letter, unseeded_letter, chosen_letter)
    return chosen_letter, None


def _order_parent_list(
    *,
    parents: set[str],
    model_name_map: dict[str, str],
    pkl_path: Optional[Path],
) -> list[str]:
    parent_list = sorted(parents, key=lambda p: model_name_map.get(p, p))
    if pkl_path is not None:
        pkl_order = _load_model_order_from_pkl(pkl_path)
        pkl_set = set(pkl_order)
        head = [p for p in pkl_order if p in parents]
        tail = [p for p in parent_list if p not in pkl_set]
        parent_list = head + tail
    return parent_list


def _collect_latex_status_data(
    continue_dir: Path,
    pkl_path: Optional[Path] = None,
) -> tuple[
    dict[tuple[str, str], dict[str, dict[str, list[str]]]],
    list[tuple[str, str]],
    dict[tuple[str, str], str],
    dict[str, str],
    list[str],
    dict[str, list[str]],
]:
    # (game, world) -> parent -> child -> [status...]
    statuses_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, list[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for world_dir in sorted(continue_dir.iterdir()):
        if not world_dir.is_dir():
            continue
        parsed = _parse_game_world_dirname(world_dir.name)
        if parsed is None:
            continue
        parsed_game, _parsed_world = parsed
        for parent_json in sorted(world_dir.glob("*.json")):
            try:
                with open(parent_json, "r") as f:
                    payload = json.load(f)
            except Exception as e:
                logger.warning(f"Skipping unreadable JSON {parent_json}: {type(e).__name__}: {e}")
                continue
            if not isinstance(payload, dict):
                logger.warning(f"Skipping invalid JSON top-level in {parent_json}")
                continue
            game = str(payload.get("game", parsed_game))
            world = str(payload.get("world", _parsed_world))
            col_key = (game, world)
            status_by_name = _extract_status_by_name(payload)
            for bot_name, status in status_by_name.items():
                parent, child = _split_bot_name(bot_name)
                statuses_by_col_parent_child[col_key][parent][child].append(status)

    present_cols = set(statuses_by_col_parent_child.keys())
    ordered_main_cols, main_col_map = _get_main_game_world_col_map()
    ordered_cols = [c for c in ordered_main_cols if c in present_cols]
    seen_cols = set(ordered_cols)
    ordered_cols.extend(sorted(c for c in present_cols if c not in seen_cols))

    parents: set[str] = set()
    children_by_parent: dict[str, set[str]] = defaultdict(set)
    for by_parent in statuses_by_col_parent_child.values():
        for parent, by_child in by_parent.items():
            parents.add(parent)
            children_by_parent[parent].update(by_child.keys())
    model_name_map = _get_model_name_map()
    parent_list = _order_parent_list(parents=parents, model_name_map=model_name_map, pkl_path=pkl_path)
    child_names_by_parent = {
        parent: sorted(children_by_parent.get(parent, set()))
        for parent in parent_list
    }
    return (
        statuses_by_col_parent_child,
        ordered_cols,
        main_col_map,
        model_name_map,
        parent_list,
        child_names_by_parent,
    )


def _collect_barplot_status_data(
    continue_dir: Path,
    pkl_path: Optional[Path] = None,
) -> tuple[
    dict[tuple[str, str], dict[str, dict[str, list[str]]]],
    list[tuple[str, str]],
    dict[tuple[str, str], str],
    dict[str, str],
    list[str],
    dict[str, list[str]],
]:
    statuses_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, list[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for world_dir in sorted(continue_dir.iterdir()):
        if not world_dir.is_dir():
            continue
        parsed = _parse_game_world_dirname(world_dir.name)
        if parsed is None:
            continue
        parsed_game, _parsed_world = parsed
        for parent_json in sorted(world_dir.glob("*.json")):
            try:
                with open(parent_json, "r") as f:
                    payload = json.load(f)
            except Exception as e:
                logger.warning(f"Skipping unreadable JSON {parent_json}: {type(e).__name__}: {e}")
                continue
            if not isinstance(payload, dict):
                logger.warning(f"Skipping invalid JSON top-level in {parent_json}")
                continue
            game = str(payload.get("game", parsed_game))
            world = str(payload.get("world", _parsed_world))
            col_key = (game, world)
            status_by_name = _extract_barplot_status_by_name(payload)
            for bot_name, status in status_by_name.items():
                parent, child = _split_bot_name(bot_name)
                statuses_by_col_parent_child[col_key][parent][child].append(status)

    present_cols = set(statuses_by_col_parent_child.keys())
    ordered_main_cols, main_col_map = _get_main_game_world_col_map()
    ordered_cols = [c for c in ordered_main_cols if c in present_cols]
    seen_cols = set(ordered_cols)
    ordered_cols.extend(sorted(c for c in present_cols if c not in seen_cols))

    parents: set[str] = set()
    children_by_parent: dict[str, set[str]] = defaultdict(set)
    for by_parent in statuses_by_col_parent_child.values():
        for parent, by_child in by_parent.items():
            parents.add(parent)
            children_by_parent[parent].update(by_child.keys())
    model_name_map = _get_model_name_map()
    parent_list = _order_parent_list(parents=parents, model_name_map=model_name_map, pkl_path=pkl_path)
    child_names_by_parent = {
        parent: sorted(children_by_parent.get(parent, set()))
        for parent in parent_list
    }
    return (
        statuses_by_col_parent_child,
        ordered_cols,
        main_col_map,
        model_name_map,
        parent_list,
        child_names_by_parent,
    )


def _collect_barplot_combined_source_data(
    continue_dir: Path,
) -> tuple[
    dict[tuple[str, str], dict[str, dict[str, str]]],
    dict[tuple[str, str], dict[str, dict[str, str]]],
    dict[tuple[str, str], dict[str, dict[str, tuple[int, int, int]]]],
    list[tuple[str, str]],
    dict[tuple[str, str], str],
    set[str],
]:
    raw_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    parsed_letter_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    timeout_error_counts_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, tuple[int, int, int]]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for world_dir in sorted(continue_dir.iterdir()):
        if not world_dir.is_dir():
            continue
        parsed = _parse_game_world_dirname(world_dir.name)
        if parsed is None:
            continue
        parsed_game, _parsed_world = parsed
        for parent_json in sorted(world_dir.glob("*.json")):
            try:
                with open(parent_json, "r") as f:
                    payload = json.load(f)
            except Exception as e:
                logger.warning(f"Skipping unreadable JSON {parent_json}: {type(e).__name__}: {e}")
                continue
            if not isinstance(payload, dict):
                logger.warning(f"Skipping invalid JSON top-level in {parent_json}")
                continue
            game = str(payload.get("game", parsed_game))
            world = str(payload.get("world", _parsed_world))
            col_key = (game, world)
            raw_by_name, parsed_by_name = _extract_barplot_raw_and_parsed_by_name(payload)
            timeout_error_counts_by_name = _extract_timeout_error_counts_by_name(payload)
            all_names = set(raw_by_name.keys()) | set(parsed_by_name.keys())
            for bot_name in all_names:
                parent, child = _split_bot_name(bot_name)
                raw_status = raw_by_name.get(bot_name)
                if raw_status is not None:
                    raw_by_col_parent_child[col_key][parent][child] = raw_status
                parsed_letter = parsed_by_name.get(bot_name)
                if parsed_letter is not None:
                    parsed_letter_by_col_parent_child[col_key][parent][child] = parsed_letter
                timeout_error_counts = timeout_error_counts_by_name.get(bot_name)
                if timeout_error_counts is not None:
                    timeout_error_counts_by_col_parent_child[col_key][parent][child] = timeout_error_counts

    present_cols = set(raw_by_col_parent_child.keys()) | set(parsed_letter_by_col_parent_child.keys())
    ordered_main_cols, main_col_map = _get_main_game_world_col_map()
    ordered_cols = [c for c in ordered_main_cols if c in present_cols]
    seen_cols = set(ordered_cols)
    ordered_cols.extend(sorted(c for c in present_cols if c not in seen_cols))

    parents: set[str] = set()
    for by_parent in raw_by_col_parent_child.values():
        parents.update(by_parent.keys())
    for by_parent in parsed_letter_by_col_parent_child.values():
        parents.update(by_parent.keys())

    return (
        raw_by_col_parent_child,
        parsed_letter_by_col_parent_child,
        timeout_error_counts_by_col_parent_child,
        ordered_cols,
        main_col_map,
        parents,
    )


def _build_latex_console_summary(
    statuses_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, list[str]]]],
    ordered_cols: list[tuple[str, str]],
    main_col_map: dict[tuple[str, str], str],
    model_name_map: dict[str, str],
    parent_list: list[str],
) -> str:
    lines: list[str] = []
    for col in ordered_cols:
        col_label = main_col_map.get(col, f"{col[0]}/{col[1]}")
        lines.append(f"Game: {col_label}")
        shown = 0
        for parent in parent_list:
            parent_statuses: list[str] = []
            game_parent = statuses_by_col_parent_child.get(col, {}).get(parent, {})
            for statuses in game_parent.values():
                parent_statuses.extend(statuses)
            status_letter = _status_letter(_collapse_statuses(parent_statuses))
            if status_letter in ("R", "D"):
                continue
            parent_label = model_name_map.get(parent, parent)
            lines.append(f"  {parent_label}: {status_letter}")
            shown += 1
        if shown == 0:
            lines.append("  (none)")
    return "\n".join(lines)


def _generate_latex_table(
    statuses_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, list[str]]]],
    ordered_cols: list[tuple[str, str]],
    main_col_map: dict[tuple[str, str], str],
    model_name_map: dict[str, str],
    parent_list: list[str],
    child_names_by_parent: dict[str, list[str]],
) -> str:

    lines: list[str] = []
    lines.append("% Legend: D=deterministic, R=random, I=insufficient_data, P=pending, F=fatal_exception, U=unknown, N=no_data")
    lines.append("\\begin{table*}[h]")
    lines.append("\\centering")
    lines.append("\\scriptsize")
    lines.append("\\setlength{\\tabcolsep}{2.5pt}")
    lines.append("\\renewcommand{\\arraystretch}{0.9}")
    lines.append("\\resizebox{\\textwidth}{!}{%")
    lines.append("\\begin{tabular}{" + ("cc" + ("c" * len(ordered_cols))) + "}")
    lines.append("\\toprule")
    header_cells = [
        "Model",
        "Child",
    ] + [_latex_escape(main_col_map.get(c, f"{c[0]}/{c[1]}")) for c in ordered_cols]
    lines.append(" & ".join(header_cells) + r" \\")
    lines.append("\\midrule")

    for parent in parent_list:
        parent_label = model_name_map.get(parent, parent)
        child_names = child_names_by_parent.get(parent, [])
        parent_row = [f"\\textbf{{{_latex_escape(parent_label)}}}", ""]
        for col in ordered_cols:
            parent_statuses: list[str] = []
            game_parent = statuses_by_col_parent_child.get(col, {}).get(parent, {})
            for statuses in game_parent.values():
                parent_statuses.extend(statuses)
            parent_row.append(_status_letter(_collapse_statuses(parent_statuses)))
        lines.append(" & ".join(parent_row) + r" \\")

        for child in child_names:
            row_cells = ["", _latex_escape(child)]
            for col in ordered_cols:
                statuses = statuses_by_col_parent_child.get(col, {}).get(parent, {}).get(child, [])
                row_cells.append(_status_letter(_collapse_statuses(statuses)))
            lines.append(" & ".join(row_cells) + r" \\")
        lines.append("\\addlinespace")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("}")
    lines.append("\\end{table*}")
    lines.append("")
    return "\n".join(lines)


def _aggregate_parent_statuses(
    statuses_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, list[str]]]],
    parent_list: list[str],
) -> dict[str, str]:
    out: dict[str, str] = {}
    for parent in parent_list:
        collected: list[str] = []
        for by_parent in statuses_by_col_parent_child.values():
            game_parent = by_parent.get(parent, {})
            for statuses in game_parent.values():
                collected.extend(statuses)
        out[parent] = _collapse_statuses(collected)
    return out


def _status_color(status: str) -> str:
    return {
        "error": "#d62728",
        "timeout": "#ff7f0e",
        "deterministic": "#2ca02c",
        "random": "#1f77b4",
        "seedable_randomness": "#9467bd",
        "insufficient_data": "#ff7f0e",
        "pending": "#bcbd22",
        "fatal_exception": "#d62728",
        "unknown": "#7f7f7f",
        "missing": "#c7c7c7",
    }.get(status, "#7f7f7f")


def _status_legend_label(status: str) -> str:
    return {
        "error": "Error",
        "timeout": "Timeout",
        "pending": "Pending",
        "deterministic": "Deterministic",
        "random": "Unintended Randomness",
        "seedable_randomness": "Intended Randomness",
    }.get(status, status)


def _build_combined_status_counts_by_parent(
    *,
    seeded_dir: Path,
    unseeded_dir: Path,
) -> tuple[dict[str, dict[str, int]], set[str]]:
    (
        _seeded_raw_by_col_parent_child,
        seeded_parsed_by_col_parent_child,
        _seeded_timeout_error_counts_by_col_parent_child,
        _seeded_ordered_cols,
        _seeded_main_col_map,
        seeded_parents,
    ) = _collect_barplot_combined_source_data(seeded_dir)
    (
        _unseeded_raw_by_col_parent_child,
        unseeded_parsed_by_col_parent_child,
        _unseeded_timeout_error_counts_by_col_parent_child,
        _unseeded_ordered_cols,
        _unseeded_main_col_map,
        unseeded_parents,
    ) = _collect_barplot_combined_source_data(unseeded_dir)

    parents = set(seeded_parents) | set(unseeded_parents)
    subplot_statuses = ["error", "timeout", "deterministic", "random", "seedable_randomness"]
    counts_by_parent: dict[str, dict[str, int]] = {
        parent: {status: 0 for status in subplot_statuses}
        for parent in parents
    }
    present_cols = set(seeded_parsed_by_col_parent_child.keys()) | set(unseeded_parsed_by_col_parent_child.keys())
    for col in present_cols:
        seeded_by_parent = seeded_parsed_by_col_parent_child.get(col, {})
        unseeded_by_parent = unseeded_parsed_by_col_parent_child.get(col, {})
        for parent in set(seeded_by_parent.keys()) | set(unseeded_by_parent.keys()):
            seeded_by_child = seeded_by_parent.get(parent, {})
            unseeded_by_child = unseeded_by_parent.get(parent, {})
            child_names = sorted(set(seeded_by_child.keys()) | set(unseeded_by_child.keys()))
            for child in child_names:
                final_letter, _ = _combine_seeded_unseeded_statuses(
                    seeded_letter=seeded_by_child.get(child),
                    unseeded_letter=unseeded_by_child.get(child),
                )
                if final_letter is None:
                    continue
                final_status = _barplot_status_from_letter(final_letter)
                if final_status in counts_by_parent[parent]:
                    counts_by_parent[parent][final_status] += 1
    return counts_by_parent, parents


def _run_scatter(args: argparse.Namespace) -> None:
    seeded_dir = Path(args.from_seeded)
    if not seeded_dir.exists() or not seeded_dir.is_dir():
        raise ValueError(f"--from-seeded must be an existing directory: {seeded_dir}")
    unseeded_dir = Path(args.from_unseeded)
    if not unseeded_dir.exists() or not unseeded_dir.is_dir():
        raise ValueError(f"--from-unseeded must be an existing directory: {unseeded_dir}")
    pkl_path = Path(args.pkl)
    if not pkl_path.exists():
        raise FileNotFoundError(f"--pkl not found: {pkl_path}")

    counts_by_parent, randomness_parents = _build_combined_status_counts_by_parent(
        seeded_dir=seeded_dir,
        unseeded_dir=unseeded_dir,
    )
    model_order, median_elo_by_model = _load_model_median_elo_from_pkl(pkl_path)
    parent_list = model_order + [p for p in sorted(randomness_parents) if p not in set(model_order)]
    parent_list = [p for p in parent_list if p in median_elo_by_model]
    if not parent_list:
        raise ValueError("No overlapping parent models between randomness data and pickle median ELO data")

    output_dir = Path(args.output_dir) if args.output_dir is not None else seeded_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    subplot_statuses = ["error", "timeout", "deterministic", "random", "seedable_randomness"]
    model_name_map = _get_model_name_map()
    rows: list[dict[str, str | int | float]] = []
    for parent in parent_list:
        for status in subplot_statuses:
            rows.append(
                {
                    "model": parent,
                    "model_label": model_name_map.get(parent, parent),
                    "median_elo": float(median_elo_by_model[parent]),
                    "status": status,
                    "count": int(counts_by_parent.get(parent, {}).get(status, 0)),
                }
            )

    def _linear_stats(xs: np.ndarray, ys: np.ndarray) -> Optional[dict[str, float]]:
        mask = np.isfinite(xs) & np.isfinite(ys)
        x = xs[mask]
        y = ys[mask]
        if x.size < 2:
            return None
        if float(np.max(x) - np.min(x)) <= 0.0:
            return None
        slope, intercept = np.polyfit(x, y, 1)
        y_hat = slope * x + intercept
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
        if ss_tot > 0.0:
            r_squared = max(0.0, 1.0 - (ss_res / ss_tot))
        else:
            r_squared = float("nan")
        x_std = float(np.std(x))
        y_std = float(np.std(y))
        if x_std > 0.0 and y_std > 0.0:
            pearson_r = float(np.corrcoef(x, y)[0, 1])
        else:
            pearson_r = float("nan")
        return {
            "n": float(x.size),
            "slope": float(slope),
            "intercept": float(intercept),
            "pearson_r": pearson_r,
            "r_squared": r_squared,
        }

    for status in subplot_statuses:
        xs = np.array([float(counts_by_parent.get(parent, {}).get(status, 0)) for parent in parent_list], dtype=float)
        ys = np.array([float(median_elo_by_model[parent]) for parent in parent_list], dtype=float)
        fig, ax = plt.subplots(figsize=(5.6, 4.2))
        ax.scatter(
            xs,
            ys,
            s=28,
            alpha=0.82,
            color=_status_color(status),
            edgecolors="black",
            linewidths=0.35,
        )
        fit_stats = _linear_stats(xs, ys)
        if fit_stats is not None:
            line_x = np.linspace(float(np.min(xs)), float(np.max(xs)), 200)
            line_y = fit_stats["slope"] * line_x + fit_stats["intercept"]
            ax.plot(
                line_x,
                line_y,
                color="black",
                linestyle="--",
                linewidth=1.2,
                zorder=2,
            )
            annotation_lines = [f"r = {fit_stats['pearson_r']:.2f}"]
            if np.isfinite(fit_stats["r_squared"]):
                annotation_lines.append(f"R$^2$ = {fit_stats['r_squared']:.2f}")
            ax.text(
                0.03,
                0.97,
                "\n".join(annotation_lines),
                transform=ax.transAxes,
                va="top",
                ha="left",
                fontsize=9,
                color="#2b164f",
                bbox={
                    "boxstyle": "round,pad=0.28",
                    "facecolor": "white",
                    "edgecolor": "#d8d0ea",
                    "linewidth": 0.8,
                    "alpha": 0.92,
                },
            )
        ax.set_xlabel(f"{_status_legend_label(status)} Automata Count")
        ax.set_ylabel("Median ELO")
        ax.set_title(f"{_status_legend_label(status)} Automata vs Median ELO")
        ax.grid(axis="both", alpha=0.22, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        out_path = output_dir / f"randomness_status_vs_{status}.pdf"
        fig.savefig(out_path)
        plt.close(fig)
        print(f"saved_scatter={out_path} points={len(xs)}")

    print(f"elo_models={len(model_order)} randomness_models={len(randomness_parents)} plotted_models={len(parent_list)}")


def _run_barplot(args: argparse.Namespace) -> None:
    continue_dir = Path(args.continue_from)
    if not continue_dir.exists() or not continue_dir.is_dir():
        raise ValueError(f"--continue-from must be an existing directory for barplot mode: {continue_dir}")
    pkl_path = Path(args.pkl) if args.pkl is not None else None
    if pkl_path is not None and not pkl_path.exists():
        raise FileNotFoundError(f"--pkl not found: {pkl_path}")

    (
        statuses_by_col_parent_child,
        ordered_cols,
        _main_col_map,
        model_name_map,
        parent_list,
        _child_names_by_parent,
    ) = _collect_barplot_status_data(continue_dir, pkl_path=pkl_path)
    if not parent_list:
        raise ValueError(f"No parent model data found under {continue_dir}")
    parent_status = _aggregate_parent_statuses(
        statuses_by_col_parent_child=statuses_by_col_parent_child,
        parent_list=parent_list,
    )
    ordered_main_cols, _ = _get_main_game_world_col_map()
    bar_cols = ordered_main_cols if ordered_main_cols else ordered_cols

    output_dir = Path(args.output_dir) if args.output_dir is not None else continue_dir
    output_path = output_dir / "randomness_status_barplot.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a non-interactive backend so this works in headless environments.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    labels = [model_name_map.get(parent, parent) for parent in parent_list]
    legend_order = ["error", "timeout", "pending", "deterministic", "random"]
    counts_by_parent: dict[str, dict[str, int]] = {
        parent: {s: 0 for s in legend_order} for parent in parent_list
    }
    for parent in parent_list:
        for col in bar_cols:
            by_child = statuses_by_col_parent_child.get(col, {}).get(parent, {})
            for statuses in by_child.values():
                s = _collapse_statuses(statuses)
                if s not in counts_by_parent[parent]:
                    s = "deterministic"
                counts_by_parent[parent][s] += 1

    fig_width = max(9.5, 0.34 * len(parent_list))
    fig, ax = plt.subplots(figsize=(fig_width, 5.0))
    x = list(range(len(parent_list)))
    bottoms = [0.0 for _ in parent_list]
    present_statuses: list[str] = []
    for status in legend_order:
        heights = [float(counts_by_parent[parent][status]) for parent in parent_list]
        if sum(heights) <= 0:
            continue
        present_statuses.append(status)
        ax.bar(
            x,
            heights,
            bottom=bottoms,
            color=_status_color(status),
            width=0.8,
            edgecolor="white",
            linewidth=0.5,
        )
        bottoms = [b + h for b, h in zip(bottoms, heights)]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=75, ha="right")
    # max_total = max(int(sum(counts_by_parent[parent].values())) for parent in parent_list)
    # ax.set_ylim(0, float(max_total) + 0.2)
    # tick_step = 5 if max_total > 20 else 1
    # ax.set_yticks(list(range(0, max_total + 1, tick_step)))
    ax.set_ylim(0, 100)
    ax.set_yticks(list(range(0, 101, 10)))
    ax.set_ylabel("Automata Count")
    ax.set_title(args.title if args.title is not None else "Automata Determinism by Model")

    handles = [Patch(facecolor=_status_color(s), label=_status_legend_label(s)) for s in present_statuses]
    if handles:
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0.0)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    print(f"saved_barplot={output_path}")
    for parent in parent_list:
        bits = [f"{_status_letter(s)}={counts_by_parent[parent][s]}" for s in legend_order if counts_by_parent[parent][s] > 0]
        print(f"{model_name_map.get(parent, parent)}: {', '.join(bits)} (agg={_status_letter(parent_status[parent])})")


def _run_barplot_combined(args: argparse.Namespace) -> None:
    seeded_dir = Path(args.from_seeded)
    if not seeded_dir.exists() or not seeded_dir.is_dir():
        raise ValueError(f"--from-seeded must be an existing directory: {seeded_dir}")
    unseeded_dir = Path(args.from_unseeded)
    if not unseeded_dir.exists() or not unseeded_dir.is_dir():
        raise ValueError(f"--from-unseeded must be an existing directory: {unseeded_dir}")
    pkl_path = Path(args.pkl) if args.pkl is not None else None
    if pkl_path is not None and not pkl_path.exists():
        raise FileNotFoundError(f"--pkl not found: {pkl_path}")

    (
        seeded_raw_by_col_parent_child,
        seeded_parsed_by_col_parent_child,
        seeded_timeout_error_counts_by_col_parent_child,
        seeded_ordered_cols,
        seeded_main_col_map,
        seeded_parents,
    ) = _collect_barplot_combined_source_data(seeded_dir)
    (
        unseeded_raw_by_col_parent_child,
        unseeded_parsed_by_col_parent_child,
        unseeded_timeout_error_counts_by_col_parent_child,
        unseeded_ordered_cols,
        unseeded_main_col_map,
        unseeded_parents,
    ) = _collect_barplot_combined_source_data(unseeded_dir)

    model_name_map = _get_model_name_map()
    parents = set(seeded_parents) | set(unseeded_parents)
    parent_list = _order_parent_list(parents=parents, model_name_map=model_name_map, pkl_path=pkl_path)
    if not parent_list:
        raise ValueError(f"No parent model data found under {seeded_dir} and {unseeded_dir}")

    present_cols = set(seeded_ordered_cols) | set(unseeded_ordered_cols)
    ordered_main_cols, main_col_map = _get_main_game_world_col_map()
    if not main_col_map:
        main_col_map = {**seeded_main_col_map, **unseeded_main_col_map}
    bar_cols = ordered_main_cols if ordered_main_cols else sorted(present_cols)
    if not bar_cols:
        bar_cols = sorted(set(seeded_ordered_cols) | set(unseeded_ordered_cols))
    if not bar_cols:
        raise ValueError("No game/world columns found in either source directory")

    combined_by_col_parent_child: dict[tuple[str, str], dict[str, dict[str, list[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    mismatch_grouped: dict[str, dict[str, list[tuple[str, str, str, str]]]] = defaultdict(lambda: defaultdict(list))
    csv_rows: list[dict[str, str]] = []
    timeout_pct_by_col: dict[tuple[str, str], list[float]] = defaultdict(list)
    error_pct_by_col: dict[tuple[str, str], list[float]] = defaultdict(list)

    legend_order = ["pending", "error", "timeout", "deterministic", "random", "seedable_randomness"]
    counts_by_parent: dict[str, dict[str, int]] = {
        parent: {s: 0 for s in legend_order} for parent in parent_list
    }

    for parent in parent_list:
        for col in bar_cols:
            seeded_raw_by_child = seeded_raw_by_col_parent_child.get(col, {}).get(parent, {})
            unseeded_raw_by_child = unseeded_raw_by_col_parent_child.get(col, {}).get(parent, {})
            seeded_parsed_by_child = seeded_parsed_by_col_parent_child.get(col, {}).get(parent, {})
            unseeded_parsed_by_child = unseeded_parsed_by_col_parent_child.get(col, {}).get(parent, {})
            seeded_timeout_error_counts_by_child = seeded_timeout_error_counts_by_col_parent_child.get(col, {}).get(parent, {})
            unseeded_timeout_error_counts_by_child = unseeded_timeout_error_counts_by_col_parent_child.get(col, {}).get(parent, {})
            child_names = sorted(
                set(seeded_raw_by_child.keys())
                | set(unseeded_raw_by_child.keys())
                | set(seeded_parsed_by_child.keys())
                | set(unseeded_parsed_by_child.keys())
                | set(seeded_timeout_error_counts_by_child.keys())
                | set(unseeded_timeout_error_counts_by_child.keys())
            )
            col_label = main_col_map.get(col, f"{col[0]}/{col[1]}")
            for child in child_names:
                seeded_raw_state = seeded_raw_by_child.get(child, "")
                unseeded_raw_state = unseeded_raw_by_child.get(child, "")
                seeded_letter = seeded_parsed_by_child.get(child)
                unseeded_letter = unseeded_parsed_by_child.get(child)
                seeded_timeout_trials, seeded_error_trials, seeded_completed_trials = seeded_timeout_error_counts_by_child.get(child, (0, 0, 0))
                unseeded_timeout_trials, unseeded_error_trials, unseeded_completed_trials = unseeded_timeout_error_counts_by_child.get(child, (0, 0, 0))
                total_timeout_trials = int(seeded_timeout_trials) + int(unseeded_timeout_trials)
                total_error_trials = int(seeded_error_trials) + int(unseeded_error_trials)
                total_completed_trials = int(seeded_completed_trials) + int(unseeded_completed_trials)
                timeout_pct = (
                    f"{(100.0 * total_timeout_trials / total_completed_trials):.1f}"
                    if total_completed_trials > 0
                    else ""
                )
                error_pct = (
                    f"{(100.0 * total_error_trials / total_completed_trials):.1f}"
                    if total_completed_trials > 0
                    else ""
                )
                if total_completed_trials > 0:
                    timeout_pct_by_col[col].append(100.0 * total_timeout_trials / total_completed_trials)
                    error_pct_by_col[col].append(100.0 * total_error_trials / total_completed_trials)
                final_letter, mismatch_msg = _combine_seeded_unseeded_statuses(
                    seeded_letter=seeded_letter,
                    unseeded_letter=unseeded_letter,
                )
                if final_letter is None:
                    continue
                combined_status = _barplot_status_from_letter(final_letter)
                combined_by_col_parent_child[col][parent][child].append(combined_status)
                counts_by_parent[parent][combined_status] += 1
                if mismatch_msg is not None:
                    seeded_letter, unseeded_letter, chosen_letter = mismatch_msg
                    mismatch_grouped[col_label][parent].append((child, seeded_letter, unseeded_letter, chosen_letter))
                csv_rows.append(
                    {
                        "game": col[0],
                        "world": col[1],
                        "model name": parent,
                        "bot number": child,
                        "seeded state": str(seeded_raw_state),
                        "unseeded state": str(unseeded_raw_state),
                        "seeded parsed state": str(seeded_letter or ""),
                        "unseeded parsed state": str(unseeded_letter or ""),
                        "final letter": final_letter,
                        "timeout%": timeout_pct,
                        "error%": error_pct,
                    }
                )

    mismatch_count = 0
    if mismatch_grouped:
        print("mismatches (excluding S special-case):")
        by_parent_game: dict[str, dict[str, list[tuple[str, str, str, str]]]] = defaultdict(lambda: defaultdict(list))
        for col_label, by_parent in mismatch_grouped.items():
            for parent, items in by_parent.items():
                by_parent_game[parent][col_label].extend(items)
        for parent in sorted(by_parent_game, key=lambda p: model_name_map.get(p, p)):
            parent_label = model_name_map.get(parent, parent)
            print(f"parent: {parent_label}")
            for col_label in sorted(by_parent_game[parent]):
                print(f"  game: {col_label}")
                for child, seeded_letter, unseeded_letter, chosen_letter in sorted(
                    by_parent_game[parent][col_label], key=lambda x: x[0]
                ):
                    warn = " (*****WARNING*****)" if (seeded_letter == "R" and unseeded_letter == "D") else ""
                    print(
                        f"    child {child}: seeded={seeded_letter}, unseeded={unseeded_letter} -> chosen={chosen_letter}{warn}"
                    )
                    mismatch_count += 1
        print(f"mismatch_count={mismatch_count}")

    print("avg timeout%/error% by game:")
    for col in bar_cols:
        col_label = main_col_map.get(col, f"{col[0]}/{col[1]}")
        timeout_vals = timeout_pct_by_col.get(col, [])
        error_vals = error_pct_by_col.get(col, [])
        if timeout_vals:
            avg_timeout_pct = sum(timeout_vals) / len(timeout_vals)
            avg_error_pct = sum(error_vals) / len(error_vals) if error_vals else 0.0
            print(f"  {col_label}: timeout={avg_timeout_pct:.1f}, error={avg_error_pct:.1f}")
        else:
            print(f"  {col_label}: N/A")

    output_dir = Path(args.output_dir) if args.output_dir is not None else seeded_dir
    output_path = output_dir / "randomness_status_barplot_combined.pdf"
    csv_path = output_dir / "randomness_status_barplot_combined.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "game",
        "world",
        "model name",
        "bot number",
        "seeded state",
        "unseeded state",
        "seeded parsed state",
        "unseeded parsed state",
        "final letter",
        "timeout%",
        "error%",
    ]
    csv_rows_sorted = sorted(
        csv_rows,
        key=lambda r: (
            str(r["game"]),
            str(r["world"]),
            str(r["model name"]),
            str(r["bot number"]),
        ),
    )
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_rows_sorted:
            writer.writerow(row)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [model_name_map.get(parent, parent) for parent in parent_list]
    fig_width = max(6.6, 0.20 * len(parent_list))
    x_step = 0.90
    bar_width = 0.60
    x = np.arange(len(parent_list), dtype=float) * x_step
    subplot_statuses = ["error", "timeout", "deterministic", "random", "seedable_randomness"]
    omitted_statuses = [s for s in legend_order if s not in subplot_statuses]
    omitted_counts = {
        status: sum(int(counts_by_parent[parent][status]) for parent in parent_list)
        for status in omitted_statuses
    }
    omitted_counts = {k: v for k, v in omitted_counts.items() if v > 0}
    if omitted_counts:
        print(f"barplot_combined omitted statuses from 5-subplot view: {omitted_counts}")

    fig_height = max(10.0, 2.1 * len(subplot_statuses))
    fig, axes = plt.subplots(
        len(subplot_statuses),
        1,
        figsize=(fig_width, fig_height),
        sharex=True,
    )
    if not isinstance(axes, list):
        axes = list(axes)  # type: ignore[assignment]

    for ax, status in zip(axes, subplot_statuses):
        heights = [float(counts_by_parent[parent][status]) for parent in parent_list]
        ax.bar(
            x,
            heights,
            color=_status_color(status),
            width=bar_width,
            edgecolor="white",
            linewidth=0.5,
        )
        # ymax = max(heights) if heights else 0.0
        # ax.set_ylim(0.0, (ymax + 0.2) if ymax > 0 else 1.0)
        # tick_step = 5 if ymax > 20 else 1
        # ax.set_yticks(list(range(0, int(ymax) + 1, tick_step)) if ymax > 0 else [0, 1])
        ax.set_ylim(0, 100)
        ax.set_yticks(list(range(0, 101, 10)))
        ax.set_ylabel("Count")
        ax.set_title(_status_legend_label(status), loc="left", pad=2)
        ax.grid(axis="y", alpha=0.25, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_xlim(float(x[0] - 0.36), float(x[-1] + 0.36))

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=75, ha="right")
    axes[-1].set_xlabel("Model")

    fig.suptitle(args.title if args.title is not None else "Automata Determinism by Model", y=0.995)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.985))
    fig.savefig(output_path)
    plt.close(fig)

    print(f"saved_barplot={output_path}")
    print(f"saved_csv={csv_path}")


def _run_latex(args: argparse.Namespace) -> None:
    continue_dir = Path(args.continue_from)
    if not continue_dir.exists() or not continue_dir.is_dir():
        raise ValueError(f"--continue-from must be an existing directory for latex mode: {continue_dir}")
    pkl_path = Path(args.pkl) if args.pkl is not None else None
    if pkl_path is not None and not pkl_path.exists():
        raise FileNotFoundError(f"--pkl not found: {pkl_path}")
    (
        statuses_by_col_parent_child,
        ordered_cols,
        main_col_map,
        model_name_map,
        parent_list,
        child_names_by_parent,
    ) = _collect_latex_status_data(continue_dir, pkl_path=pkl_path)
    console_summary = _build_latex_console_summary(
        statuses_by_col_parent_child,
        ordered_cols,
        main_col_map,
        model_name_map,
        parent_list,
    )
    if console_summary:
        print(console_summary)
    latex = _generate_latex_table(
        statuses_by_col_parent_child,
        ordered_cols,
        main_col_map,
        model_name_map,
        parent_list,
        child_names_by_parent,
    )
    if args.output is not None:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(latex)
        logger.info(f"Wrote LaTeX table to {output_path}")
    print(latex)


def _add_main_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("main", help="Run randomness experiment workflow")
    parser.add_argument("--game", required=True, help="Game name (e.g. chess) or ALL")
    parser.add_argument("--world", required=False, default=None, help="World name. Required unless --game ALL")
    parser.add_argument("--n_seeds", type=int, default=20, help="Number of random-opponent seeds to test")
    parser.add_argument("--repeats", type=int, default=3, help="Number of repeats per (seed, seat)")
    parser.add_argument(
        "--timeout",
        type=str,
        default="5",
        help="Timeout spec. Either single seconds (e.g. 20) or per-game mapping (e.g. ALL=20;go=60;othello=60)",
    )
    parser.add_argument("--seed_world", action="store_true", help="If set, pass trial seed into play_game_with_timeout")
    parser.add_argument("--max_workers", type=int, default=1, help="Max concurrent parent workers")
    parser.add_argument("--limit_model_bots", type=int, default=None, help="limit_model_bots")
    parser.add_argument(
        "--continue-from",
        dest="continue_from",
        type=str,
        required=True,
        help="Directory for resumable outputs. Writes <dir>/<game>_<world>/<parent_model>.json",
    )
    parser.add_argument("--model_blacklist_file", type=str, default=None, help="model_blacklist_file")
    parser.add_argument("--model_whitelist_file", type=str, default=None, help="model_whitelist_file")
    parser.add_argument("--model_blacklist", type=str, nargs="+", default=None, help="model_blacklist")
    parser.add_argument("--model_whitelist", type=str, nargs="+", default=None, help="model_whitelist")


def _add_latex_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("latex", help="Build LaTeX table of bot status letters by game")
    parser.add_argument(
        "--continue-from",
        dest="continue_from",
        type=str,
        required=True,
        help="Directory containing per-game_world parent JSON outputs",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to write the generated LaTeX table",
    )
    parser.add_argument(
        "--pkl",
        type=str,
        default=None,
        help="Optional exp results.pkl path; if provided, use its model order",
    )


def _add_barplot_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("barplot", help="Build aggregate status bar plot by model")
    parser.add_argument(
        "--continue-from",
        dest="continue_from",
        type=str,
        required=True,
        help="Directory containing per-game_world parent JSON outputs",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional directory to write the plot PDF (default: --continue-from)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Optional figure title",
    )
    parser.add_argument(
        "--pkl",
        type=str,
        default=None,
        help="Optional exp results.pkl path; if provided, use its model order",
    )


def _add_barplot_combined_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "barplot_combined",
        help="Build aggregate status bar plot by model from seeded+unseeded sources",
    )
    parser.add_argument(
        "--from-seeded",
        dest="from_seeded",
        type=str,
        required=True,
        help="Directory containing per-game_world parent JSON outputs for seeded run",
    )
    parser.add_argument(
        "--from-unseeded",
        dest="from_unseeded",
        type=str,
        required=True,
        help="Directory containing per-game_world parent JSON outputs for unseeded run",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional directory to write the combined plot PDF (default: --from-seeded)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Optional figure title",
    )
    parser.add_argument(
        "--pkl",
        type=str,
        default=None,
        help="Optional exp results.pkl path; if provided, use its model order",
    )


def _add_scatter_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "scatter",
        help="Build per-status scatter plots of automata-count vs model median ELO from seeded+unseeded sources",
    )
    parser.add_argument(
        "--from-seeded",
        dest="from_seeded",
        type=str,
        required=True,
        help="Directory containing per-game_world parent JSON outputs for seeded run",
    )
    parser.add_argument(
        "--from-unseeded",
        dest="from_unseeded",
        type=str,
        required=True,
        help="Directory containing per-game_world parent JSON outputs for unseeded run",
    )
    parser.add_argument(
        "--pkl",
        type=str,
        required=True,
        help="exp results.pkl path used to get each model's Median ELO",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional directory to write the scatter PDFs and CSV (default: --from-seeded)",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Randomness experiment utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_main_subparser(subparsers)
    _add_latex_subparser(subparsers)
    _add_barplot_subparser(subparsers)
    _add_barplot_combined_subparser(subparsers)
    _add_scatter_subparser(subparsers)
    return parser.parse_args()


def _run_main(args: argparse.Namespace) -> None:
    if args.n_seeds <= 0:
        raise ValueError("--n_seeds must be > 0")
    if args.repeats <= 0:
        raise ValueError("--repeats must be > 0")
    if args.max_workers <= 0:
        raise ValueError("--max_workers must be > 0")
    n_seeds = int(args.n_seeds)
    repeats = int(args.repeats)

    game_str = str(args.game)
    world = str(args.world) if args.world is not None else None
    continue_dir = Path(args.continue_from)
    if continue_dir.exists() and not continue_dir.is_dir():
        raise ValueError(f"--continue-from must be a directory path, got file: {continue_dir}")
    continue_dir.mkdir(parents=True, exist_ok=True)

    model_blacklist, model_whitelist = get_model_blacklist_whitelist(
        args.model_blacklist_file,
        args.model_whitelist_file,
        args.model_blacklist,
        args.model_whitelist,
    )

    target_pairs: list[tuple[str, str]]
    mode: str
    if game_str.upper() == "ALL":
        if world is not None:
            raise ValueError("--world must be omitted when --game ALL")
        target_pairs = _discover_all_game_world_pairs()
        if not target_pairs:
            raise ValueError("No game/world pairs discovered for --game ALL")
        mode = "all"
    else:
        if world is None:
            raise ValueError("--world is required unless --game ALL")
        target_pairs = [(game_str, world)]
        mode = "single"
    timeout_by_game = _resolve_timeout_by_game(str(args.timeout), target_pairs)

    logger.info(
        f"Preparing tasks for mode={mode}, target_pairs={len(target_pairs)}, continue_from={continue_dir}, "
        f"timeout_by_game={timeout_by_game}"
    )
    tasks, complete_parent_specs = _build_tasks(
        continue_dir=continue_dir,
        target_pairs=target_pairs,
        n_seeds=n_seeds,
        repeats=repeats,
        timeout_by_game=timeout_by_game,
        limit_model_bots=args.limit_model_bots,
        seed_world=bool(args.seed_world),
        model_blacklist=model_blacklist,
        model_whitelist=model_whitelist,
    )
    if not tasks:
        refreshed_results = _refresh_complete_parent_summaries(
            complete_parent_specs=complete_parent_specs,
            n_seeds=n_seeds,
            repeats=repeats,
        )
        summary = _build_aggregate_summary(refreshed_results, mode=mode, continue_dir=continue_dir)
        summary["n_tasks"] = 0
        summary["n_refreshed_parent_summaries"] = len(refreshed_results)
        logger.info(f"Finished mode={mode}. Summary: {summary}")
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    logger.info(f"Running {len(tasks)} parent tasks with max_workers={args.max_workers}")
    task_results = _execute_tasks_with_processes(tasks, max_workers=int(args.max_workers))
    refreshed_results = _refresh_complete_parent_summaries(
        complete_parent_specs=complete_parent_specs,
        n_seeds=n_seeds,
        repeats=repeats,
    )
    summary = _build_aggregate_summary(
        task_results + refreshed_results, mode=mode, continue_dir=continue_dir
    )
    summary["n_tasks"] = len(task_results)
    summary["n_refreshed_parent_summaries"] = len(refreshed_results)
    logger.info(f"Finished mode={mode}. Summary: {summary}")
    print(json.dumps(summary, indent=2, sort_keys=True))


def main() -> None:
    args = _parse_args()
    if args.command == "main":
        _run_main(args)
    elif args.command == "latex":
        _run_latex(args)
    elif args.command == "barplot":
        _run_barplot(args)
    elif args.command == "barplot_combined":
        _run_barplot_combined(args)
    elif args.command == "scatter":
        _run_scatter(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
