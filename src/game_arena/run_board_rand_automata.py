"""Adaptive model-level tournament with random automata (no qualifier round).

Loop:
  1. Fit model-level Bradley-Terry Elo (all automata of a model pooled under the model name) with bootstrap CIs.
  2. A model is "wide" if it has fewer than --min_games games or its CI width (upper - lower) exceeds --ci_width.
  3. Pick two distinct wide models uniformly at random, pick one random automaton from each, random sides, play ONE game.
  4. Repeat until no model is wide or --max_matches total games is reached.

Runtime: games run in a streaming thread pool that always keeps --max_workers games in flight (no batch barrier
waiting on the slowest game). CIs are refit in the main thread every --refresh_every completed games, so pairs
are chosen from CIs that are at most ~refresh_every + max_workers games stale.

Output: {save_results_dir}/matches_{game}_{world}.json in the same format as run_leaderboard (config, qual_bot_names,
match_results) plus a 'ci_status' snapshot. Resuming from an existing file continues where it left off.

Example:
  PYTHONHASHSEED=0 python -m game_arena.run_board_rand_automata --game connect4 --world world1 \
      --timeout 1 --seed 0 --max_workers 50 --ci_width 100 --max_matches 20000 \
      --model_blacklist_file experimental/model_ignore.json \
      --save_results_dir results_current/results_akimiski_nov_11_randomautomata/tourney
"""
import argparse
import json
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from game_arena import base, utils
from game_arena.run_leaderboard import get_model_blacklist_whitelist
from game_arena.typing import BotPath, MatchResults
from experimental.lm_arena.rating_systems import fit_bt, preprocess_for_bt, scale_and_offset
from experimental.lm_arena.simple_example import _build_battles

logger = utils.setup_logging("run_board_rand_automata.log", "run_board_rand_automata", to_stdout=True)
ModelToBots = dict[str, list[BotPath]]


def model_of(bot_name: str) -> str:
    return bot_name.split('/')[0]


def compute_model_ci(match_results: list[MatchResults], num_bootstrap: int, confidence_level: float, rng_seed: int = 0) -> dict[str, dict[str, float]]:
    """Model-level BT ratings + bootstrap CI. Runs sequentially in-process (no mp.Pool: we are inside a thread pool,
    and with tens of models each fit is a few ms so pool startup would dominate)."""
    if len(match_results) == 0:
        return {}
    battles = pd.DataFrame(_build_battles(match_results, "base", 0.0))  # type: ignore[arg-type]
    matchups, outcomes, models, weights = preprocess_for_bt(battles)
    alpha_log = np.log(10.0)
    point = scale_and_offset(fit_bt(matchups, outcomes, weights, len(models), alpha_log), models)
    rng = np.random.default_rng(rng_seed)
    boot_w = rng.multinomial(n=len(battles), pvals=weights / weights.sum(), size=num_bootstrap).astype(np.float64) / len(battles)
    boot = np.array([fit_bt(matchups, outcomes, w, len(models), alpha_log) for w in boot_w])
    boot = scale_and_offset(boot, models)
    a = 1 - confidence_level
    lower = np.quantile(boot, a / 2, axis=0)
    upper = np.quantile(boot, 1 - a / 2, axis=0)
    n_games = battles["model_a"].value_counts().add(battles["model_b"].value_counts(), fill_value=0)
    return {
        m: {'rating': float(point[i]), 'lower': float(lower[i]), 'upper': float(upper[i]),
            'width': float(upper[i] - lower[i]), 'n_games': int(n_games.get(m, 0))}
        for i, m in enumerate(models)
    }


def get_wide_models(models: list[str], ci: dict[str, dict[str, float]], game_counts: Counter[str], ci_width: float, min_games: int, max_games_per_model: Optional[int]) -> list[str]:
    wide = []
    for m in models:
        if max_games_per_model is not None and game_counts[m] >= max_games_per_model:
            continue  # capped: a model with a perfect record never narrows, don't let it eat the budget
        if game_counts[m] < min_games or m not in ci or ci[m]['width'] > ci_width:
            wide.append(m)
    return wide


def pick_pair(rng: random.Random, wide: list[str], all_models: list[str], model_to_bots: ModelToBots) -> tuple[BotPath, BotPath]:
    if len(wide) >= 2:
        m1, m2 = rng.sample(wide, 2)
    else:  # a single wide model left: its opponent can be any other model
        m1 = wide[0]
        m2 = rng.choice([m for m in all_models if m != m1])
    b1, b2 = rng.choice(model_to_bots[m1]), rng.choice(model_to_bots[m2])
    return (b1, b2) if rng.random() < 0.5 else (b2, b1)


def _load_previous(path: Path, run_config: dict[str, Any]) -> list[MatchResults]:
    if not path.exists():
        return []
    with open(path, 'r') as f:
        data = json.load(f)
    assert data.get('config') == run_config, f'config mismatch: {data.get("config")} != {run_config}'
    logger.info(f'resuming with {len(data["match_results"])} previous matches from {path}')
    return data['match_results']


def _save(path: Path, run_config: dict[str, Any], match_results: list[MatchResults], ci: dict[str, Any], wide: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.json.tmp')
    with open(tmp, 'w') as f:
        json.dump({'config': run_config, 'qual_bot_names': None, 'ci_status': {'wide_models': sorted(wide), 'models': ci}, 'match_results': match_results}, f, indent=2)
    tmp.replace(path)  # atomic: an interrupt mid-dump never corrupts the results file


def _log_status(ci: dict[str, dict[str, float]], wide: list[str], n_done: int, max_matches: int, elapsed: float, ci_width: float) -> None:
    rows = sorted(ci.items(), key=lambda kv: -kv[1]['rating'])
    table = ' | '.join(f"{m}:{v['rating']:.0f} w={v['width']:.0f}(n={v['n_games']})" for m, v in rows)
    logger.info(f'[{n_done}/{max_matches} games, {elapsed / 60:.1f}m] wide (CI width > {ci_width:g})={len(wide)}/{len(ci)} :: {table}')


def main_rand_automata(
        game_str: str,
        world: str,
        timeout: int,
        save_results_dir: str,
        max_workers: int,
        max_matches: int,
        ci_width: float,
        confidence_level: float = 0.95,
        min_games: int = 10,
        max_games_per_model: Optional[int] = None,
        refresh_every: Optional[int] = None,
        num_bootstrap: int = 100,
        save_every_s: float = 120.0,
        seed: Optional[int] = None,
        include_random: bool = True,
        allowed_bot_nums: Optional[str] = None,
        model_blacklist: Optional[list[str]] = None,
        model_whitelist: Optional[list[str]] = None,
    ):
    t0 = time.time()
    game = utils.get_game(game_name=game_str)
    config = utils.get_config_file(game_str, world)
    bots: list[BotPath] = list(utils.get_bot_paths_from_world(game_str, world, add_random=include_random, allowed_bot_nums=allowed_bot_nums).items())
    if model_blacklist is not None:
        bots = [b for b in bots if model_of(b[0]) not in model_blacklist]
    if model_whitelist is not None:
        bots = [b for b in bots if model_of(b[0]) in model_whitelist]
    model_to_bots: ModelToBots = defaultdict(list)
    for b in bots:
        model_to_bots[model_of(b[0])].append(b)
    all_models = sorted(model_to_bots)
    assert len(all_models) >= 2, f'need >= 2 models, got {all_models}'
    logger.info(f'game={game_str} world={world}: {len(all_models)} models, {len(bots)} automata, ci_width={ci_width}, conf={confidence_level}, min_games={min_games}, max_matches={max_matches}, max_workers={max_workers}')

    refresh_every = refresh_every or max_workers
    run_config = {'game_str': game_str, 'world': world, 'timeout': timeout, 'seed': seed, 'mode': 'rand_automata'}
    out_path = utils.get_root_path() / Path(save_results_dir) / f'matches_{game_str}_{world}.json'
    match_results = _load_previous(out_path, run_config)
    known_bots = {b[0] for b in bots}
    match_results = [m for m in match_results if m['name0'] in known_bots and m['name1'] in known_bots]
    game_counts: Counter[str] = Counter()
    for m in match_results:
        game_counts[model_of(m['name0'])] += 1
        game_counts[model_of(m['name1'])] += 1

    # seed=None -> nondeterministic pair choice; otherwise deterministic stream offset by #resumed matches
    rng = random.Random(None if seed is None else seed * 1_000_003 + len(match_results))

    def refresh() -> tuple[dict[str, dict[str, float]], list[str]]:
        ci = compute_model_ci(match_results, num_bootstrap, confidence_level)
        return ci, get_wide_models(all_models, ci, game_counts, ci_width, min_games, max_games_per_model)

    ci, wide = refresh()
    n_submitted = len(match_results)
    since_refresh = 0
    last_save = time.time()
    in_flight: set[Future[MatchResults]] = set()

    def submit(executor: ThreadPoolExecutor) -> bool:
        nonlocal n_submitted
        if n_submitted >= max_matches or len(wide) == 0:
            return False
        p0, p1 = pick_pair(rng, wide, all_models, model_to_bots)
        game_seed = None if seed is None else seed + rng.randrange(2**16)
        in_flight.add(executor.submit(base.play_game_with_timeout, game, config, [p0, p1], game_seed, timeout))
        n_submitted += 1
        return True

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while len(in_flight) < max_workers and submit(executor):
                pass
            while in_flight:
                done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
                for fut in done:
                    in_flight.discard(fut)
                    try:
                        res = fut.result()
                    except Exception as e:  # play_game_with_timeout already converts bot errors/timeouts to results
                        logger.error(f'unexpected game failure, dropping: {e!r}')
                        continue
                    match_results.append(res)
                    game_counts[model_of(res['name0'])] += 1
                    game_counts[model_of(res['name1'])] += 1
                    since_refresh += 1
                if since_refresh >= refresh_every:
                    ci, wide = refresh()
                    since_refresh = 0
                    _log_status(ci, wide, len(match_results), max_matches, time.time() - t0, ci_width)
                if time.time() - last_save > save_every_s:
                    _save(out_path, run_config, match_results, ci, wide)
                    last_save = time.time()
                while len(in_flight) < max_workers and submit(executor):
                    pass
    finally:  # also on Ctrl-C: keep every finished game
        ci, wide = refresh()
        _save(out_path, run_config, match_results, ci, wide)
        _log_status(ci, wide, len(match_results), max_matches, time.time() - t0, ci_width)
        reason = 'all CIs narrow' if len(wide) == 0 else f'match limit ({max_matches})' if len(match_results) >= max_matches else 'interrupted'
        logger.info(f'finished game={game_str} world={world}: {len(match_results)} games, stop reason: {reason}, still wide: {sorted(wide)}, elapsed_m={(time.time() - t0) / 60:.2f}')


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Adaptive tournament: random automata from models with wide Elo CIs play single games.")
    p.add_argument("--game", required=True)
    p.add_argument("--world", required=True)
    p.add_argument("--timeout", type=int, required=True)
    p.add_argument("--save_results_dir", type=str, required=True)
    p.add_argument("--max_matches", type=int, required=True, help="total games limit for this game/world (including resumed ones)")
    p.add_argument("--ci_width", type=float, required=True, help="a model is done when its CI upper-lower Elo width is <= this")
    p.add_argument("--conf", type=float, default=0.95, help="CI confidence level")
    p.add_argument("--min_games", type=int, default=10, help="models with fewer games are always considered wide")
    p.add_argument("--max_games_per_model", type=int, default=None, help="stop selecting a model after this many games (guards perfect-record models whose CI never narrows)")
    p.add_argument("--refresh_every", type=int, default=None, help="refit CIs every N completed games (default: max_workers)")
    p.add_argument("--num_bootstrap", type=int, default=100)
    p.add_argument("--save_every_s", type=float, default=120.0)
    p.add_argument("--max_workers", type=int, default=12)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--no_random", action='store_true', help="exclude the built-in random bot")
    p.add_argument("--allowed_bot_nums", type=str, default=None)
    p.add_argument("--model_blacklist_file", type=str, nargs='+', default=None)
    p.add_argument("--model_whitelist_file", type=str, nargs='+', default=None)
    p.add_argument("--model_blacklist", type=str, nargs='+', default=None)
    p.add_argument("--model_whitelist", type=str, nargs='+', default=None)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    model_blacklist, model_whitelist = get_model_blacklist_whitelist(args.model_blacklist_file, args.model_whitelist_file, args.model_blacklist, args.model_whitelist)
    main_rand_automata(
        game_str=args.game,
        world=args.world,
        timeout=args.timeout,
        save_results_dir=args.save_results_dir,
        max_workers=args.max_workers,
        max_matches=args.max_matches,
        ci_width=args.ci_width,
        confidence_level=args.conf,
        min_games=args.min_games,
        max_games_per_model=args.max_games_per_model,
        refresh_every=args.refresh_every,
        num_bootstrap=args.num_bootstrap,
        save_every_s=args.save_every_s,
        seed=args.seed,
        include_random=not args.no_random,
        allowed_bot_nums=args.allowed_bot_nums,
        model_blacklist=model_blacklist,
        model_whitelist=model_whitelist,
    )
