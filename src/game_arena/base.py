from __future__ import annotations
import hashlib
import json
import time
import random
import inspect
import warnings
import traceback
import queue as py_queue
import multiprocessing as mp
from functools import lru_cache
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Literal, TypeAlias
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

import numpy as np

from game_arena.utils import get_policy_fn_with_memory, setup_logging, get_player_result, set_seed, callable_name
from game_arena.typing import MatchResults, PartialMatchResults, PolicyFn, Player, BotPath, init_match_results


logger = setup_logging("game.log", "game", to_stdout=True)
fatal_logger = setup_logging("game_fatal.log", "game_fatal", to_stdout=True)



WorkerEvent: TypeAlias = (
    tuple[Literal["thinking"], int, float]
    | tuple[Literal["action"], int, Any, float]
)

WorkerDoneMsg: TypeAlias = (
    tuple[Literal["ok", "err"], PartialMatchResults]
    | tuple[Literal["KeyboardInterrupt"], None]
    | tuple[Literal["???"], str]
)

class Game(ABC):
    @abstractmethod
    def get_observation(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def get_move(self, move_str: str) -> Any:
        ...

    @abstractmethod
    def get_legal_moves(self) -> list[Any]:
        ...

    @abstractmethod
    def game_step(self, move: Any) -> None:
        ...

    @abstractmethod
    def current_player(self) -> int:
        ...

    @abstractmethod
    def is_done(self) -> bool:
        ...

    @abstractmethod
    def get_final_stats(self) -> Dict[str, Any]:
        ...
    
    def live_play_legal_moves(self) -> list[Any]:
        raise NotImplementedError("live_play_legal_moves is not implemented")


class BotPolicyError(RuntimeError):
    """The bot's own code failed: it raised, exceeded its time limit, or its process died without a result."""


def run_policy_with_timeout(policy_fn: PolicyFn, inp: dict, timeout: float) -> Any:
    """THIS FUNCTION IS ONLY USED FOR LIVE PLAY. IT IS TOO SLOW FOR AUTOMATA VS AUTOMATA"""
    """Run `policy_fn(inp)` in a separate process with a time limit."""
    def _worker(fn: PolicyFn, inp: dict, q: mp.Queue) -> None:
        try:
            result = fn(**inp)  # type: ignore
            q.put(("ok", result))
        except Exception:
            q.put(("err", traceback.format_exc()))
    q: mp.Queue = mp.Queue()
    p = mp.Process(target=_worker, args=(policy_fn, inp, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        raise BotPolicyError(f"Policy execution exceeded timeout of {timeout} seconds")

    if q.empty():
        raise BotPolicyError("Policy process finished without returning a result")

    status, payload = q.get_nowait()
    if status == "ok":
        return payload
    else:
        raise BotPolicyError("Policy raised an exception: " + str(payload))


def play_game(game: Game, players: list[Player], event_q: mp.Queue) -> PartialMatchResults:
    result: PartialMatchResults = {
        'done': False,
        'winner': 'error',
        'player_err_counts': [0] * len(players),
    }
    while not game.is_done():
        kwargs = game.get_observation()
        current_player = game.current_player()
        assert current_player >= 0 and current_player < len(players), "Current player is out of range"
        policy = players[current_player][1]
        try:
            if '_debug_legal_moves' in inspect.signature(policy).parameters:  # when the policy wants to see the legal moves
                kwargs['_debug_legal_moves'] = game.get_legal_moves()
            policy_start_s = time.time()
            event_q.put(("thinking", current_player, policy_start_s))
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=r"(overflow|divide by zero|invalid value) encountered", category=RuntimeWarning)
                action_str = policy(**kwargs)  # type: ignore
            policy_end_s = time.time()
            event_q.put(("action", current_player, action_str, policy_end_s - policy_start_s))
            action = game.get_move(action_str)
            game.game_step(action)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            result['player_err_counts'][current_player] += 1
            result['exception'] = str(e)
            result['exception_traceback'] = traceback.format_exc()
            break
    final_stats = game.get_final_stats()
    result['done'] = final_stats.pop('done')
    result['winner'] = final_stats.pop('winner', 'error')
    result['other'] = final_stats
    return result


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {to_jsonable(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()  # np.int64 -> int, etc.
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    raise TypeError(f'cannot dump {type(obj).__name__} to json')


def dumps_json(obj):
    return json.dumps(to_jsonable(obj))


_MP_WARNING_PRINTED_COUNT = 0
def _get_isolated_mp_context() -> Any:
    try:
        return mp.get_context('forkserver')
    except ValueError:
        global _MP_WARNING_PRINTED_COUNT
        if _MP_WARNING_PRINTED_COUNT < 10:
            _MP_WARNING_PRINTED_COUNT += 1
            print("Warning: mp.get_context('forkserver') failed, using mp.get_context()")
        return mp.get_context()


def _play_game_timeout_worker(game_cls: type[Game], game_config: dict[str, Any], bot_paths: list[BotPath], seed: Optional[int], event_q: mp.Queue[WorkerEvent], done_q: mp.Queue[WorkerDoneMsg]) -> None:
    try:
        set_seed(seed)
        game = game_cls(game_config)  # type: ignore
        players = [get_policy_fn_with_memory(name, path) for name, path in bot_paths]
        result = play_game(game, players, event_q=event_q)
        if 'exception' not in result:
            done_q.put(("ok", result))
        else:
            done_q.put(("err", result))
    except KeyboardInterrupt:
        done_q.put(("KeyboardInterrupt", None))
    except Exception:
        done_q.put(("???", traceback.format_exc()))


def _drain_play_game_queue(q: mp.Queue[WorkerEvent], action_history: list[tuple[Any, Any, Any]], thinking_status: Optional[tuple[int, float]], timeout: int) -> tuple[Optional[tuple[int, float]], Optional[tuple[str, float]]]:
    timeout_hit = None
    while True:
        try:
            msg = q.get_nowait()
        except py_queue.Empty:
            break
        assert isinstance(msg, tuple) and len(msg) > 0, f"invalid message: {msg}"
        tag = msg[0]
        if tag == "thinking":
            assert len(msg) == 3, "thinking message must have 3 elements, (current_player, policy_start_s)"
            thinking_status = (int(msg[1]), float(msg[2]))  # (current_player, policy_start_s)
        elif tag == "action":
            assert len(msg) == 4, "action message must have 4 elements, (current_player, action, action_end_s - action_start_s)"
            # msg is (current_player, action, action_end_s - action_start_s)
            player_idx = int(msg[1])
            action_dt = float(msg[3])
            action_history.append((player_idx, msg[2], round(action_dt, 2)))
            if action_dt > timeout:
                return None, (str(player_idx), round(action_dt, 2))
            thinking_status = None
        else:
            raise ValueError(f"Unknown message tag: {tag}")
    if thinking_status is not None:
        active_player, policy_start_s = thinking_status
        action_dt = time.time() - policy_start_s
        if action_dt > timeout:
            action_history.append((None, None, None))
            timeout_hit = (str(active_player), round(action_dt, 2))
    return thinking_status, timeout_hit


def _debug_print(match_results: MatchResults, start_time: float, _debug_last_print_s: Optional[float], thinking_status: Optional[tuple[int, float]], action_history: list[tuple[Any, Any, Any]]) -> Optional[float]:
    _PERIODIC_DEBUG_PRINT_INTERVAL = 30
    _START_DEBUG_PRINT_TIME = 60
    debug_overtime = time.time() - start_time
    if debug_overtime > _START_DEBUG_PRINT_TIME and (_debug_last_print_s is None or debug_overtime - _debug_last_print_s > _PERIODIC_DEBUG_PRINT_INTERVAL):
        _debug_last_print_s = debug_overtime
        name0, name1 = match_results['name0'], match_results['name1']
        seed = match_results['seed']
        logger.info(f"Game execution took {debug_overtime:.1f}s for players {name0} and {name1}; seed {seed}; last action history: {action_history[-1] if len(action_history) > 0 else None} (len: {len(action_history)}) (thinking_status: {thinking_status})")
    return _debug_last_print_s


def play_game_with_timeout(game_cls: type[Game], game_config: dict[str, Any], bot_paths: list[BotPath], seed: Optional[int], timeout: int) -> MatchResults:
    set_seed(seed)
    start_time = time.time()
    results: MatchResults = init_match_results([p[0] for p in bot_paths], seed)
    action_history: list[tuple[Any, Any, Any]] = []
    thinking_status: Optional[tuple[int, float]] = None
    timeout_hit: Optional[tuple[str, float]] = None
    p: Optional[mp.Process] = None
    _debug_last_print_s: Optional[float] = None
    try:
        ctx = _get_isolated_mp_context()
        event_q: mp.Queue[WorkerEvent] = ctx.Queue()
        done_q: mp.Queue[WorkerDoneMsg] = ctx.Queue()
        p = ctx.Process(target=_play_game_timeout_worker, args=(game_cls, game_config, bot_paths, seed, event_q, done_q))
        assert p is not None, "p is not populated"
        p.start()
        while p.is_alive() and done_q.empty():
            thinking_status, timeout_hit = _drain_play_game_queue(event_q, action_history, thinking_status, timeout)
            if timeout_hit is not None:
                raise TimeoutError(f"Game execution exceeded timeout of {timeout} seconds: {timeout_hit}")
            p.join(timeout)
            _debug_last_print_s = _debug_print(results, start_time, _debug_last_print_s, thinking_status, action_history)  # DEBUG: print periodically if match > 60s
        thinking_status, timeout_hit = _drain_play_game_queue(event_q, action_history, thinking_status, timeout)
        if timeout_hit is not None:
            raise TimeoutError(f"Game execution exceeded timeout of {timeout} seconds: {timeout_hit}")
        if done_q.empty():
            raise RuntimeError("Game process finished without returning a result")
        tag, payload = done_q.get_nowait()
        assert payload is not None, "final payload is not populated"
        if tag == "ok" and not isinstance(payload, str):
            results['winner'] = payload['winner']
            results['done'] = payload['done']
        elif tag == "err" and not isinstance(payload, str):
            results['winner'] = 'error'
            results['done'] = False
        elif tag == "KeyboardInterrupt":
            raise KeyboardInterrupt
        else:
            raise RuntimeError(f"play_game status {tag} raised an exception in the worker process:\n" + str(payload))
        results['r'] = payload
        results['action_history'] = dumps_json(action_history)
        results['time_elapsed'] = round(time.time() - start_time, 2)
        return results
    except TimeoutError as e:
        logger.info(f"Timeout in play_game_with_timeout. Game: {callable_name(game_cls)} Players: {', '.join([p[0] for p in bot_paths])} Timeout: {timeout} seconds")
        assert timeout_hit is not None, f"timeout_hit is not populated: {timeout_hit}"
        results['winner'] = 'timeout'
        results['done'] = False
        results['r'] = None
        results['action_history'] = dumps_json(action_history)
        results['time_elapsed'] = round(time.time() - start_time, 2)
        results['exception'] = str(e)
        results['exception_traceback'] = traceback.format_exc()
        results['timeout_hit'] = timeout_hit
        return results
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        fatal_logger.error(f"Something very wrong happened and game data dropped: {traceback.format_exc()}")
        raise
    finally:
        if p is not None:
            if p.is_alive():
                p.kill()
            if p.pid is not None:
                p.join(timeout=3)


def update_scores(all_scores: dict[str, list[int]], res: MatchResults):
    # wins, draws, losses, total
    for p in (0, 1):
        player_result = get_player_result(res, p, verbose=False)  # type: ignore
        name = res[f'name{p}']
        all_scores[name][3] += 1
        if player_result in ('win', 'enemy_error', 'enemy_timeout'):
            all_scores[name][0] += 1
        elif player_result == 'draw':
            all_scores[name][1] += 1
        elif player_result in ('loss', 'error', 'timeout'):
            all_scores[name][2] += 1
        else:
            assert False, f"Unknown player result: {player_result}"


@lru_cache(maxsize=1)
def _get_bt_deps():
    from experimental.lm_arena.rating_systems import compute_bt
    from experimental.lm_arena.simple_example import _build_battles
    return compute_bt, _build_battles


def get_bt_elo_ratings(all_matches: list[MatchResults]) -> dict[str, float]:
    compute_bt, _build_battles = _get_bt_deps()
    battles = _build_battles(all_matches, "full", 0.0)  # type: ignore
    elo_ratings = compute_bt(battles)
    return elo_ratings


def _build_scores_table(all_scores: dict[str, list[int]], names: set[str], *, max_rows: int = 25, bt_elo_ratings: Optional[dict[str, float]] = None):  # "wd_pct" | "done_pct" | "total" | "wins"
    from rich.table import Table
    sort_by = "elo,wins"
    rows: list[tuple[str, float, float, float, int, float]] = []
    for name in names:
        if name not in all_scores:
            continue
        wins, draws, losses, total = all_scores[name]
        if total > 0:
            w_pct = wins / total * 100.0
            l_pct = losses / total * 100.0
            d_pct = draws / total * 100.0
        else:
            w_pct = float("-inf")
            l_pct = float("-inf")
            d_pct = float("-inf")
        elo = bt_elo_ratings.get(name, float("-inf")) if bt_elo_ratings is not None else float("-inf")
        rows.append((name, w_pct, d_pct, l_pct, total, elo))

    if sort_by == "elo,wins":
        rows.sort(key=lambda r: (r[5], r[1] + r[2]/2), reverse=True)  # elo then wins+draws/2
    else:
        raise ValueError(f"Invalid sort_by: {sort_by}")

    table = Table(title="Scores", expand=True)
    table.add_column("Name", no_wrap=True)
    table.add_column("W%", justify="right")
    table.add_column("D%", justify="right")
    table.add_column("L%", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("ELO", justify="right")
    for name, w_pct, d_pct, l_pct, total, elo in rows[:max_rows]:
        table.add_row(
            name,
            f"{w_pct:5.1f}",
            f"{d_pct:5.1f}",
            f"{l_pct:5.1f}",
            str(total),
            f"{elo:5.1f}",
        )
    if len(rows) > max_rows:
        table.caption = f"Showing top {max_rows} of {len(rows)} (sort: {sort_by})."
    return table


def get_seed(name1: str, name2: str, iter_i: int) -> int:
    # get deterministic hash from name1+name2+iter_i % 2**16
    full_str = hashlib.sha256(f"{name1}{name2}{iter_i}".encode()).digest()
    return int.from_bytes(full_str, 'little') % 2**16


def play_all_2p_games(game_cls: type[Game], game_config: dict[str, Any], todo: list[tuple[BotPath, BotPath, int]], seed: Optional[int] = None, timeout: int = 5, max_workers: int = 32) -> list[MatchResults]:
    from rich.console import Console, Group
    from rich.live import Live
    from rich.progress import (
        Progress,
        BarColumn,
        MofNCompleteColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
        SpinnerColumn,
        TextColumn,
        TransferSpeedColumn,
    )
    from tqdm import tqdm
    if len(todo) == 0:
        return []
    if seed is not None:
        random.seed(seed+123)
        np.random.seed(seed+123)
    todo = list(todo)
    random.shuffle(todo)
    total_games = sum(2 * pair_n_games for _, _, pair_n_games in todo)
    logger.info(f'Playing a total of {total_games} games of {game_cls.__name__} for {len(todo)} pairs (single big multithreaded loop)')
    all_data: list[MatchResults] = []
    names: set[str] = set([p1[0] for p1, p2, _ in todo] + [p2[0] for p1, p2, _ in todo])
    # score row: [wins (+1), losses (0), draws (1/2), total]
    all_scores: dict[str, list[int]] = {name: [0, 0, 0, 0] for name in names}

    console = Console()
    # UI tuning knobs
    table_refresh_every = 50   # update the table every N completed games
    table_max_rows = 25        # show top N players
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("{task.percentage:>6.2f}%"),
        TransferSpeedColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,  # keep final state visible
        expand=True,
    )
    task_id = progress.add_task(f"Playing a total of {total_games} games of {game_cls.__name__} for {len(todo)} pairs", total=total_games)
    scores_table = _build_scores_table(
        all_scores,
        names,
        max_rows=table_max_rows,
    )
    layout = Group(progress, scores_table)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: list[Future[MatchResults]] = []
        pbar = tqdm(total=total_games, desc="Creating futures, this should only take a few seconds")
        for p1, p2, pair_n_games in todo:
            for i in range(2 * pair_n_games):
                game_seed = None
                if seed is not None:
                    game_seed = get_seed(p1[0], p2[0], i) + seed
                if i % 2 == 0:
                    p1x, p2x = p1, p2
                else:
                    p1x, p2x = p2, p1
                fut = executor.submit(
                    play_game_with_timeout,
                    game_cls,
                    game_config,
                    [p1x, p2x],
                    game_seed,
                    timeout,
                )
                futures.append(fut)
                pbar.update(1)
        pbar.close()
        bt_elo_ratings = None
        table_refresh_elo_every = max(total_games // 100, table_refresh_every)
        with Live(layout, console=console, refresh_per_second=2) as live:
            for i, fut in enumerate(as_completed(futures), start=1):
                try:
                    res = fut.result()
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:
                    print(f'UNKNOWN ERROR {traceback.format_exc()}')
                    continue
                all_data.append(res)
                update_scores(all_scores, res)

                progress.advance(task_id, 1)

                # calculate ELO every table_refresh_elo_every
                if i % table_refresh_elo_every == 0 or (i == total_games):
                    bt_elo_ratings = get_bt_elo_ratings(all_data)
                # Update table periodically (and more frequently early on)
                if i < 300 or (i % table_refresh_every == 0) or (i == total_games):
                    scores_table = _build_scores_table(
                        all_scores,
                        names,
                        max_rows=table_max_rows,
                        bt_elo_ratings=bt_elo_ratings,
                    )
                    live.update(Group(progress, scores_table))
    live.refresh()
    live.stop()
    all_data.sort(key=lambda x: (x['name0'], x['name1'], x['seed']))  # sort by (name0, name1, seed)

    return all_data
