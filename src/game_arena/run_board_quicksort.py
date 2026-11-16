"""Quicksort tournament over ALL automata (no qualifier round): "Just Sort It!" (Maystre & Grossglauser, ICML 2017).

--sorts independent randomized Quicksorts over all automata. In each partition a uniformly random pivot plays every other
member once (one game, random seat); members that beat the pivot form one sub-partition, members that lost to it the
other, and each sub-partition is sorted the same way until it has fewer than 2 members. A draw is decided by a coin flip
(the paper's model has no draws). Siblings may meet and pairs may repeat across sorts, as in the paper. Ratings are the
usual Bradley-Terry fit on all games; the sorted orders themselves are not used.

Expected games per sort: 2(n+1)H_n - 4n (261 automata -> ~2,175; Swiss with 20 rounds ~5,200).

Scheduling: a partition splits as soon as its own pivot games are finished, and all sorts run at the same time, so
workers only idle once fewer than max_workers games are left in the whole tournament (no round barriers).
Every pivot, seat, game seed and coin flip is derived from --seed and the partition, so the schedule depends only on game
outcomes, never on which game finished first; a resume replays the stored comparisons and plays only what is missing.

Results are saved every --save_every_s seconds and on exit (including Ctrl-C).

Output: {save_results_dir}/matches_{game}_{world}.json in the run_leaderboard format (config, qual_bot_names=None,
match_results) plus 'comparisons' ({comparison id "sort:path:automaton": index into match_results}).

Example:
  PYTHONHASHSEED=0 python -m game_arena.run_board_quicksort --game connect4 --world world1 \
      --sorts 3 --timeout 1 --seed 0 --max_workers 32 --allowed_bot_nums 1,2,3,4,5 \
      --model_blacklist_file experimental/model_ignore.json \
      --save_results_dir results_current/results_quicksort_s3/tourney
"""
import argparse
import json
import logging
import random
import sys
import time
from collections import deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from game_arena import base, utils
from game_arena.run_leaderboard import get_model_blacklist_whitelist
from game_arena.typing import BotPath, MatchResults

logger = utils.setup_logging("run_board_quicksort.log", "run_board_quicksort", to_stdout=True)
for _h in logging.getLogger("game").handlers:  # per-game timeout / slow-game lines: keep them in logs/game.log only
    if isinstance(_h, logging.StreamHandler) and not isinstance(_h, logging.FileHandler):
        _h.setLevel(logging.WARNING)


def model_of(bot_name: str) -> str:
    return bot_name.split('/')[0]


def expected_games_per_sort(n: int) -> int:
    return round(2 * (n + 1) * sum(1 / k for k in range(1, n + 1)) - 4 * n)


@dataclass
class Partition:
    sort: int
    path: str  # '' for the root, then 'W' (beat the pivot) / 'L' (lost to the pivot) per level
    pivot: str
    left: int  # pivot games not finished yet
    won: list[str] = field(default_factory=list)
    lost: list[str] = field(default_factory=list)


@dataclass
class Comparison:
    cmp_id: str
    part: Partition
    other: str
    p0: str
    p1: str
    game_seed: int


def _save(path: Path, global_results: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.json.tmp')
    with open(tmp, 'w') as f:
        json.dump(global_results, f, indent=2)
    tmp.replace(path)  # atomic: an interrupt mid-dump never corrupts the results file


def main_quicksort(
        game_str: str,
        world: str,
        sorts: int,
        timeout: int,
        save_results_dir: str,
        max_workers: int,
        seed: int,
        save_every_s: float = 120.0,
        include_random: bool = True,
        allowed_bot_nums: Optional[str] = None,
        model_blacklist: Optional[list[str]] = None,
        model_whitelist: Optional[list[str]] = None,
    ):
    assert sorts >= 1, f'need sorts >= 1, got {sorts}'
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
    expected_total = sorts * expected_games_per_sort(len(names))
    logger.info(f'game={game_str} world={world}: {len({model_of(x) for x in names})} models, {len(names)} automata, sorts={sorts} '
                f'(~{expected_total} games expected), seed={seed}, max_workers={max_workers}')

    run_config = {'game_str': game_str, 'world': world, 'timeout': timeout, 'seed': seed, 'mode': 'quicksort', 'sorts': sorts}
    out_path = utils.get_root_path() / Path(save_results_dir) / f'matches_{game_str}_{world}.json'
    if out_path.exists():
        with open(out_path, 'r') as f:
            global_results: dict[str, Any] = json.load(f)
        old_config = global_results.get('config') or {}
        # sorts are independent (all randomness keyed by seed:sort:path), so a finished run can be extended with more sorts
        assert {k: v for k, v in old_config.items() if k != 'sorts'} == {k: v for k, v in run_config.items() if k != 'sorts'} \
            and sorts >= old_config.get('sorts', 0), f'config mismatch: {old_config} != {run_config}'
        global_results['config'] = run_config
        logger.info(f'resuming: {len(global_results["comparisons"])} stored comparisons, {len(global_results["match_results"])} matches from {out_path}')
    else:
        global_results = {'config': run_config, 'qual_bot_names': None, 'comparisons': {}, 'match_results': []}

    match_results: list[MatchResults] = global_results['match_results']
    stored: dict[str, int] = global_results['comparisons']
    pending: deque[Comparison] = deque()
    ready: deque[tuple[Comparison, Optional[MatchResults]]] = deque()  # finished comparisons waiting to be applied

    def open_partition(sort: int, path: str, members: list[str]) -> None:
        if len(members) < 2:
            return
        rng = random.Random(f'{seed}:{sort}:{path}')
        part = Partition(sort, path, rng.choice(members), len(members) - 1)
        for x in members:
            if x == part.pivot:
                continue
            p0, p1 = (part.pivot, x) if rng.random() < 0.5 else (x, part.pivot)
            c = Comparison(f'{sort}:{path}:{x}', part, x, p0, p1, base.get_seed(p0, p1, sort) + seed)
            if c.cmp_id in stored:  # resume: already played
                ready.append((c, match_results[stored[c.cmp_id]]))
            else:
                pending.append(c)

    def apply(c: Comparison, res: Optional[MatchResults]) -> None:
        """Send c.other to the side of the pivot it belongs on; split the partition once all its pivot games are in."""
        winner = utils.get_match_result(res, verbose=False)[1] if res is not None else 0.5  # type: ignore[arg-type]
        pivot_seat = 0 if c.p0 == c.part.pivot else 1
        if winner == 0.5:
            pivot_won = random.Random(f'{seed}:{c.cmp_id}:draw').random() < 0.5
        else:
            pivot_won = winner == pivot_seat
        (c.part.lost if pivot_won else c.part.won).append(c.other)
        c.part.left -= 1
        if c.part.left == 0:
            open_partition(c.part.sort, c.part.path + 'W', sorted(c.part.won))
            open_partition(c.part.sort, c.part.path + 'L', sorted(c.part.lost))

    def drain_ready() -> None:
        while ready:
            apply(*ready.popleft())

    for s in range(sorts):
        open_partition(s, '', names)
    drain_ready()
    if stored:
        logger.info(f'replayed stored comparisons, {len(pending)} games ready to play')

    # live board: progress bar + scores/Elo table (same widgets as play_all_2p_games)
    from rich.console import Console, Group
    from rich.live import Live
    from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, TransferSpeedColumn
    all_scores: dict[str, list[int]] = {name: [0, 0, 0, 0] for name in names}
    for m in match_results:
        base.update_scores(all_scores, m)
    progress = Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), MofNCompleteColumn(),
                        TextColumn("{task.percentage:>6.2f}%"), TransferSpeedColumn(), TimeElapsedColumn(), TimeRemainingColumn(),
                        console=Console(), transient=False, expand=True)
    task_id = progress.add_task(f"{game_str} {world} quicksort, {sorts} sorts (total is the expectation)", total=expected_total, completed=len(match_results))
    elo = base.get_bt_elo_ratings(match_results) if match_results else None
    elo_every = max(expected_total // 100, 50)

    def board():
        progress.update(task_id, description=f"{game_str} {world} quicksort: {len(pending)} games queued")
        return Group(progress, base._build_scores_table(all_scores, set(names), max_rows=25, bt_elo_ratings=elo))

    in_flight: dict[Future[MatchResults], Comparison] = {}
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
                while pending and len(in_flight) < max_workers:
                    c = pending.popleft()
                    fut = executor.submit(base.play_game_with_timeout, game, config, [(c.p0, bot_by_name[c.p0]), (c.p1, bot_by_name[c.p1])], c.game_seed, timeout)
                    in_flight[fut] = c
                if not in_flight:
                    elo = base.get_bt_elo_ratings(match_results) if match_results else None
                    live.update(board())
                    break
                done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
                for fut in done:
                    c = in_flight.pop(fut)
                    res: Optional[MatchResults] = None
                    try:
                        res = fut.result()
                        stored[c.cmp_id] = len(match_results)
                        match_results.append(res)
                        base.update_scores(all_scores, res)
                        progress.advance(task_id, 1)
                        n_since_elo += 1
                    except Exception as e:  # play_game_with_timeout already turns bot errors/timeouts into results
                        logger.error(f'unexpected game failure in comparison {c.cmp_id}, deciding it by coin flip: {e!r}')
                    ready.append((c, res))
                drain_ready()
                if n_since_elo >= elo_every:
                    elo = base.get_bt_elo_ratings(match_results)
                    n_since_elo = 0
                live.update(board())
                if time.time() - last_save > save_every_s:
                    _save(out_path, global_results)
                    last_save = time.time()
    finally:  # also on Ctrl-C: keep every finished game
        for h, stream in zip(console_handlers, old_streams):
            if stream is not None:  # setStream returns None when the stream did not change
                h.setStream(stream)
        _save(out_path, global_results)

    logger.info(f'finished game={game_str} world={world}: {len(match_results)} games, elapsed_m={(time.time() - t0) / 60:.2f}')


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Quicksort tournament over all automata (Maystre & Grossglauser 2017).")
    p.add_argument("--game", required=True)
    p.add_argument("--world", required=True)
    p.add_argument("--sorts", type=int, required=True, help="independent Quicksorts (~2,175 games each for 261 automata)")
    p.add_argument("--timeout", type=int, required=True)
    p.add_argument("--seed", type=int, required=True, help="seeds pivots, seats, games and draw coin flips")
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
    main_quicksort(
        game_str=args.game,
        world=args.world,
        sorts=args.sorts,
        timeout=args.timeout,
        save_results_dir=args.save_results_dir,
        max_workers=args.max_workers,
        seed=args.seed,
        save_every_s=args.save_every_s,
        include_random=not args.no_random,
        allowed_bot_nums=args.allowed_bot_nums,
        model_blacklist=model_blacklist,
        model_whitelist=model_whitelist,
    )
