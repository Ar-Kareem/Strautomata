"""Swiss tournament over ALL automata (no qualifier round).

--rounds rounds in total. In every round each automaton plays one opponent, 2 games (one from each seat):
  rounds 1..--random_rounds : random opponent
  later rounds              : refit Bradley-Terry ratings on all games so far, then pair each automaton (from the top of
                              the rating order down) with the nearest-rated automaton it has not played yet
Automata of the same model are never paired, and no pairing repeats. With an odd number of entries (or when no valid
opponent is left) an automaton sits out that round.

Rounds are pipelined: as soon as every game of the current round has been handed to a worker, the next round is
paired from the games finished so far and queued, so workers never sit idle waiting for a round's slowest games.
Automata keep no state between games, so an automaton may already start its next-round game while a game of the
previous round is still running. Pairing therefore ignores at most ~max_workers in-flight results, and depends slightly
on which games finished first (a rerun with the same seed may pair differently; a resume replays the stored rounds).

Results are saved every --save_every_s seconds and on exit (including Ctrl-C); a rerun with the same config replays the
stored rounds, plays any games still missing, and continues.

Output: {save_results_dir}/matches_{game}_{world}.json in the run_leaderboard format (config, qual_bot_names=None,
match_results) plus 'rounds' (the list of pairings of each round).

Example:
  PYTHONHASHSEED=0 python -m game_arena.run_board_swiss --game connect4 --world world1 \
      --rounds 20 --random_rounds 2 --timeout 1 --seed 0 --max_workers 32 --allowed_bot_nums 1,2,3,4,5 \
      --model_blacklist_file experimental/model_ignore.json \
      --save_results_dir results_current/results_swiss_d20/tourney
"""
import argparse
import json
import logging
import random
import sys
import time
from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from game_arena import base, utils
from game_arena.run_leaderboard import get_model_blacklist_whitelist
from game_arena.typing import BotPath, MatchResults
from experimental.lm_arena.rating_systems import bt_loss_and_grad, preprocess_for_bt
from experimental.lm_arena.simple_example import _build_battles

logger = utils.setup_logging("run_board_swiss.log", "run_board_swiss", to_stdout=True)
for _h in logging.getLogger("game").handlers:  # per-game timeout / slow-game lines: keep them in logs/game.log only
    if isinstance(_h, logging.StreamHandler) and not isinstance(_h, logging.FileHandler):
        _h.setLevel(logging.WARNING)
Pair = tuple[str, str]


def model_of(bot_name: str) -> str:
    return bot_name.split('/')[0]


def fit_ratings(match_results: list[MatchResults], prior: float) -> pd.Series:
    """Bradley-Terry Elo with a small L2 prior so perfect records stay finite (only used to choose pairings)."""
    battles = pd.DataFrame(_build_battles(match_results, "full", 0.0))  # type: ignore[arg-type]
    matchups, outcomes, models, weights = preprocess_for_bt(battles)
    alpha = np.log(10.0)

    def loss(x):
        l, g = bt_loss_and_grad(x, matchups, outcomes, weights, alpha)
        return l + prior * x @ x, g + 2 * prior * x

    x = minimize(loss, np.zeros(len(models)), jac=True, method="L-BFGS-B").x
    return pd.Series(x * 400 + 1500, index=models)


def can_pair(a: str, b: str, played: set[frozenset[str]]) -> bool:
    return model_of(a) != model_of(b) and frozenset((a, b)) not in played


def random_round(names: list[str], played: set[frozenset[str]], rng: random.Random) -> list[Pair]:
    free = rng.sample(names, len(names))
    out: list[Pair] = []
    while len(free) > 1:
        a = free.pop()
        for j in range(len(free) - 1, -1, -1):
            if can_pair(a, free[j], played):
                out.append((a, free.pop(j)))
                break
    return out


def swiss_round(names: list[str], ratings: pd.Series, played: set[frozenset[str]]) -> list[Pair]:
    free = list(ratings.reindex(names).fillna(ratings.median()).sort_values(ascending=False, kind='stable').index)
    out: list[Pair] = []
    while len(free) > 1:
        a = free.pop(0)
        for j, b in enumerate(free):  # nearest below in rating order first
            if can_pair(a, b, played):
                out.append((a, free.pop(j)))
                break
    return out


def _save(path: Path, global_results: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.json.tmp')
    with open(tmp, 'w') as f:
        json.dump(global_results, f, indent=2)
    tmp.replace(path)  # atomic: an interrupt mid-dump never corrupts the results file


def main_swiss(
        game_str: str,
        world: str,
        rounds: int,
        random_rounds: int,
        timeout: int,
        save_results_dir: str,
        max_workers: int,
        seed: int,
        prior: float = 1e-3,
        save_every_s: float = 120.0,
        include_random: bool = True,
        allowed_bot_nums: Optional[str] = None,
        model_blacklist: Optional[list[str]] = None,
        model_whitelist: Optional[list[str]] = None,
    ):
    assert 1 <= random_rounds <= rounds, f'need 1 <= random_rounds ({random_rounds}) <= rounds ({rounds})'
    t0 = time.time()
    game = utils.get_game(game_name=game_str)
    config = utils.get_config_file(game_str, world)
    bots: list[BotPath] = list(utils.get_bot_paths_from_world(game_str, world, add_random=include_random, allowed_bot_nums=allowed_bot_nums).items())
    if model_blacklist is not None:
        bots = [b for b in bots if model_of(b[0]) not in model_blacklist]
    if model_whitelist is not None:
        bots = [b for b in bots if model_of(b[0]) in model_whitelist]
    bots = sorted(bots, key=lambda b: b[0])
    bot_by_name = dict(bots)
    names = list(bot_by_name)
    logger.info(f'game={game_str} world={world}: {len({model_of(x) for x in names})} models, {len(names)} automata, rounds={rounds} ({random_rounds} random), seed={seed}, max_workers={max_workers}')

    run_config = {'game_str': game_str, 'world': world, 'timeout': timeout, 'seed': seed, 'mode': 'swiss',
                  'rounds': rounds, 'random_rounds': random_rounds, 'prior': prior}
    out_path = utils.get_root_path() / Path(save_results_dir) / f'matches_{game_str}_{world}.json'
    if out_path.exists():
        with open(out_path, 'r') as f:
            global_results: dict[str, Any] = json.load(f)
        assert global_results.get('config') == run_config, f'config mismatch: {global_results.get("config")} != {run_config}'
        missing = {x for rnd in global_results['rounds'] for p in rnd for x in p} - set(names)
        assert not missing, f'stored rounds reference automata that no longer exist: {sorted(missing)}'
        logger.info(f'resuming: {len(global_results["rounds"])} stored rounds, {len(global_results["match_results"])} matches from {out_path}')
    else:
        global_results = {'config': run_config, 'qual_bot_names': None, 'rounds': [], 'match_results': []}

    match_results: list[MatchResults] = global_results['match_results']
    played: set[frozenset[str]] = set()  # every pairing scheduled so far, finished or not
    seat_done = Counter((m['name0'], m['name1']) for m in match_results)
    pending: deque[tuple[int, str, str, int]] = deque()  # (round, first player, second player, game seed)
    round_left: dict[int, int] = {}  # games of each round not finished yet

    def enqueue(rnd: int, pairs: list[Pair]) -> None:
        played.update(frozenset(p) for p in pairs)
        round_left[rnd] = 0
        for a, b in pairs:
            for i, (p0, p1) in enumerate(((a, b), (b, a))):  # one game from each seat, seeds as in play_all_2p_games
                if seat_done[(p0, p1)] > 0:
                    seat_done[(p0, p1)] -= 1
                    continue
                pending.append((rnd, p0, p1, base.get_seed(a, b, i) + seed))
                round_left[rnd] += 1

    for rnd, stored in enumerate(global_results['rounds']):
        enqueue(rnd, [tuple(p) for p in stored])  # type: ignore[misc]
    if global_results['rounds']:
        logger.info(f'{len(pending)} games of the stored rounds still to play')

    def next_round() -> None:
        """Pair the next round from the games finished so far (in-flight games are not waited for)."""
        rnd = len(global_results['rounds'])
        if rnd < random_rounds:
            pairs = random_round(names, played, random.Random(seed * 1_000_003 + rnd))
        else:
            pairs = swiss_round(names, fit_ratings(match_results, prior), played)
        global_results['rounds'].append([list(p) for p in pairs])
        enqueue(rnd, pairs)
        _save(out_path, global_results)  # store the pairing before playing so a resume replays the same round
        logger.info(f'round {rnd + 1}/{rounds} ({"random" if rnd < random_rounds else "swiss"}) paired: {len(pairs)} pairings, '
                    f'{len(match_results)} games finished so far, elapsed {(time.time() - t0) / 60:.1f}m')

    # live board: progress bar + scores/Elo table (same widgets as play_all_2p_games)
    from rich.console import Console, Group
    from rich.live import Live
    from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, TransferSpeedColumn
    all_scores: dict[str, list[int]] = {name: [0, 0, 0, 0] for name in names}
    for m in match_results:
        base.update_scores(all_scores, m)
    expected_total = rounds * (len(names) // 2) * 2  # upper bound: a few automata may sit out late rounds
    progress = Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), MofNCompleteColumn(),
                        TextColumn("{task.percentage:>6.2f}%"), TransferSpeedColumn(), TimeElapsedColumn(), TimeRemainingColumn(),
                        console=Console(), transient=False, expand=True)
    task_id = progress.add_task(f"{game_str} {world} swiss, {rounds} rounds", total=expected_total, completed=len(match_results))
    elo = base.get_bt_elo_ratings(match_results) if match_results else None
    elo_every = max(expected_total // 100, 50)

    def board():
        desc = f"{game_str} {world} swiss: round {len(global_results['rounds'])}/{rounds} paired"
        progress.update(task_id, description=desc)
        return Group(progress, base._build_scores_table(all_scores, set(names), max_rows=25, bt_elo_ratings=elo))

    in_flight: dict[Future[MatchResults], int] = {}
    last_save = time.time()
    n_since_elo = 0
    console_handlers: list[logging.StreamHandler] = []
    old_streams: list[Any] = []
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor, Live(board(), refresh_per_second=2) as live:
            # Live swaps sys.stdout for a proxy that prints above the board; point our console log handler at it
            console_handlers[:] = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
            old_streams[:] = [h.setStream(sys.stdout) for h in console_handlers]
            while True:
                # the queue ran dry: start the next round now instead of letting workers idle until this round ends
                if not pending and len(global_results['rounds']) < rounds:
                    next_round()
                while pending and len(in_flight) < max_workers:
                    rnd, p0, p1, game_seed = pending.popleft()
                    fut = executor.submit(base.play_game_with_timeout, game, config, [(p0, bot_by_name[p0]), (p1, bot_by_name[p1])], game_seed, timeout)
                    in_flight[fut] = rnd
                if not in_flight:
                    elo = base.get_bt_elo_ratings(match_results) if match_results else None
                    live.update(board())
                    break
                done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
                for fut in done:
                    rnd = in_flight.pop(fut)
                    try:
                        res = fut.result()
                        match_results.append(res)
                        base.update_scores(all_scores, res)
                        progress.advance(task_id, 1)
                        n_since_elo += 1
                    except Exception as e:  # play_game_with_timeout already turns bot errors/timeouts into results
                        logger.error(f'unexpected game failure in round {rnd + 1}, dropping: {e!r}')
                    round_left[rnd] -= 1
                    if round_left[rnd] == 0:
                        logger.info(f'round {rnd + 1}/{rounds} finished: {len(match_results)} games total, elapsed {(time.time() - t0) / 60:.1f}m')
                if n_since_elo >= elo_every:
                    elo = base.get_bt_elo_ratings(match_results)
                    n_since_elo = 0
                live.update(board())
                if time.time() - last_save > save_every_s:
                    _save(out_path, global_results)
                    last_save = time.time()
    finally:  # also on Ctrl-C: keep every finished game
        for h, stream in zip(console_handlers, old_streams):
            h.setStream(stream)
        _save(out_path, global_results)

    logger.info(f'finished game={game_str} world={world}: {len(match_results)} games, elapsed_m={(time.time() - t0) / 60:.2f}')


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Swiss tournament over all automata: random warm-up rounds, then nearest-rating pairings.")
    p.add_argument("--game", required=True)
    p.add_argument("--world", required=True)
    p.add_argument("--rounds", type=int, required=True, help="total rounds = opponents per automaton (2 games each)")
    p.add_argument("--random_rounds", type=int, default=2, help="warm-up rounds with random opponents")
    p.add_argument("--timeout", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--prior", type=float, default=1e-3, help="L2 prior on natural-scale ratings, used only for choosing Swiss pairings")
    p.add_argument("--save_results_dir", type=str, required=True)
    p.add_argument("--max_workers", type=int, default=12)
    p.add_argument("--save_every_s", type=float, default=120.0)
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
    main_swiss(
        game_str=args.game,
        world=args.world,
        rounds=args.rounds,
        random_rounds=args.random_rounds,
        timeout=args.timeout,
        save_results_dir=args.save_results_dir,
        max_workers=args.max_workers,
        seed=args.seed,
        prior=args.prior,
        save_every_s=args.save_every_s,
        include_random=not args.no_random,
        allowed_bot_nums=args.allowed_bot_nums,
        model_blacklist=model_blacklist,
        model_whitelist=model_whitelist,
    )
