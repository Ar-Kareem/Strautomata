"""Sparse O(N) tournament over ALL automata (no qualifier round).

Every automaton (plus the built-in random bot) is a node in a random K-regular graph: it plays exactly K distinct
opponents, never an automaton of its own model (sibling pairings are excluded). Each edge is played 2 * n_games
times, n_games from each seating (n_games=1 -> r=2 games per pairing).

Total games per game/world = n_bots * K / 2 * 2 * n_games  (e.g. 261 bots, K=20, n_games=1 -> 5,220).

The pairing graph is built deterministically from --seed and stored in the results file, so a resumed run plays
exactly the same pairings and only the games still missing.

Output: {save_results_dir}/matches_{game}_{world}.json in the run_leaderboard format (config, qual_bot_names=None,
match_results) plus 'pairings'.

Example:
  PYTHONHASHSEED=0 python -m game_arena.run_board_all_automata --game connect4 --world world1 \
      --k 20 --n_games 1 --timeout 1 --seed 0 --max_workers 50 \
      --model_blacklist_file experimental/model_ignore.json \
      --save_results_dir results_current/results_all_automata_k20r2/tourney
"""
import argparse
import json
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from game_arena import base, utils
from game_arena.run_leaderboard import _build_todo_with_resume, get_model_blacklist_whitelist
from game_arena.typing import BotPath

logger = utils.setup_logging("run_board_all_automata.log", "run_board_all_automata", to_stdout=True)


def model_of(bot_name: str) -> str:
    return bot_name.split('/')[0]


def random_regular_pairings(names: list[str], k: int, rng: random.Random, swaps_per_edge: int = 50) -> list[tuple[str, str]]:
    """Random K-regular simple graph over `names` with no edge between two automata of the same model.

    Start from a circulant graph on an order that interleaves models (siblings far apart), repair any sibling edge,
    then randomize with degree-preserving double edge swaps that never create a sibling or duplicate edge.
    Every node has degree k (one node k-1 when len(names) * k is odd)."""
    n = len(names)
    models = [model_of(x) for x in names]
    max_siblings = max(models.count(m) for m in set(models))
    assert k <= n - max_siblings, f'k={k} too large: some automaton has only {n - max_siblings} non-sibling opponents'

    # interleave: one automaton per model per round, models in random order
    by_model: dict[str, list[int]] = defaultdict(list)
    for i in rng.sample(range(n), n):
        by_model[models[i]].append(i)
    order: list[int] = []
    while any(by_model.values()):
        for m in rng.sample(sorted(by_model), len(by_model)):
            if by_model[m]:
                order.append(by_model[m].pop())

    edges: list[tuple[int, int]] = []
    for pos in range(n):
        for d in range(1, k // 2 + 1):
            edges.append((order[pos], order[(pos + d) % n]))
    if k % 2:
        edges.extend((order[pos], order[pos + n // 2]) for pos in range(n // 2))
    adj: dict[int, set[int]] = {i: set() for i in range(n)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)

    def ok(u: int, v: int) -> bool:
        return u != v and models[u] != models[v] and v not in adj[u]

    def try_swap(i: int, j: int) -> bool:
        (a, b), (c, d) = edges[i], edges[j]
        if rng.random() < 0.5:
            c, d = d, c
        if len({a, b, c, d}) < 4 or not ok(a, d) or not ok(c, b):
            return False
        adj[a].discard(b); adj[b].discard(a); adj[c].discard(d); adj[d].discard(c)
        adj[a].add(d); adj[d].add(a); adj[c].add(b); adj[b].add(c)
        edges[i], edges[j] = (a, d), (c, b)
        return True

    def is_sibling(e: tuple[int, int]) -> bool:
        return models[e[0]] == models[e[1]]

    # repair: the interleaved start only has sibling edges in the tail when models have unequal automata counts
    for i in range(len(edges)):
        tries = 0
        while is_sibling(edges[i]):
            tries += 1
            assert tries < 100_000, 'could not remove a sibling pairing'
            j = rng.randrange(len(edges))
            if j != i and not is_sibling(edges[j]):
                try_swap(i, j)
    for _ in range(swaps_per_edge * len(edges)):
        try_swap(rng.randrange(len(edges)), rng.randrange(len(edges)))

    assert not any(is_sibling(e) for e in edges)
    assert len({frozenset(e) for e in edges}) == len(edges)
    return sorted(tuple(sorted((names[a], names[b]))) for a, b in edges)  # type: ignore[misc]


def main_all_automata(
        game_str: str,
        world: str,
        k: int,
        n_games: int,
        timeout: int,
        save_results_dir: str,
        max_workers: int,
        seed: int,
        include_random: bool = True,
        allowed_bot_nums: Optional[str] = None,
        model_blacklist: Optional[list[str]] = None,
        model_whitelist: Optional[list[str]] = None,
        skip_save_results: bool = False,
    ):
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
    n_models = len({model_of(x) for x in names})
    logger.info(f'game={game_str} world={world}: {n_models} models, {len(names)} automata, k={k}, n_games={n_games} per seating, seed={seed}, max_workers={max_workers}')

    run_config = {'game_str': game_str, 'world': world, 'timeout': timeout, 'seed': seed, 'mode': 'all_automata', 'k': k, 'n_games': n_games}
    out_path = utils.get_root_path() / Path(save_results_dir) / f'matches_{game_str}_{world}.json'
    if out_path.exists():
        with open(out_path, 'r') as f:
            global_results: dict[str, Any] = json.load(f)
        assert global_results.get('config') == run_config, f'config mismatch: {global_results.get("config")} != {run_config}'
        pairings = [tuple(p) for p in global_results['pairings']]
        missing = {x for p in pairings for x in p} - set(names)
        assert not missing, f'pairings reference automata that no longer exist: {sorted(missing)}'
        logger.info(f'resuming: {len(global_results["match_results"])} previous matches, {len(pairings)} stored pairings from {out_path}')
    else:
        pairings = random_regular_pairings(names, k, random.Random(seed))
        global_results = {'config': run_config, 'qual_bot_names': None, 'pairings': [list(p) for p in pairings], 'match_results': []}

    pair_set = {frozenset(p) for p in pairings}
    done = [m for m in global_results['match_results'] if frozenset((m['name0'], m['name1'])) in pair_set]
    todo_all = _build_todo_with_resume(bots, n_games, done)
    todo = [t for t in todo_all if frozenset((t[0][0], t[1][0])) in pair_set]
    n_todo_games = sum(2 * t[2] for t in todo)
    logger.info(f'{len(pairings)} pairings, {len(pairings) * 2 * n_games} games total, {n_todo_games} games to play')
    if n_todo_games == 0:
        logger.info('No games to play. Exiting.')
        return

    result = base.play_all_2p_games(game, config, todo, seed=seed, timeout=timeout, max_workers=max_workers)
    global_results['match_results'].extend(result)
    logger.info(f'done game={game_str} world={world}: played {len(result)} games, elapsed_m={(time.time() - t0) / 60:.2f}')

    if skip_save_results:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix('.json.tmp')
    with open(tmp, 'w') as f:
        json.dump(global_results, f, indent=2)
    tmp.replace(out_path)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sparse tournament: every automaton plays K random non-sibling automata.")
    p.add_argument("--game", required=True)
    p.add_argument("--world", required=True)
    p.add_argument("--k", type=int, required=True, help="opponents per automaton (degree of the random regular graph)")
    p.add_argument("--n_games", type=int, default=1, help="games per seating per pairing (r = 2 * n_games)")
    p.add_argument("--timeout", type=int, required=True)
    p.add_argument("--seed", type=int, required=True, help="seeds the pairing graph and the games")
    p.add_argument("--save_results_dir", type=str, required=True)
    p.add_argument("--max_workers", type=int, default=12)
    p.add_argument("--no_random", action='store_true', help="exclude the built-in random bot")
    p.add_argument("--allowed_bot_nums", type=str, default=None)
    p.add_argument("--model_blacklist_file", type=str, nargs='+', default=None)
    p.add_argument("--model_whitelist_file", type=str, nargs='+', default=None)
    p.add_argument("--model_blacklist", type=str, nargs='+', default=None)
    p.add_argument("--model_whitelist", type=str, nargs='+', default=None)
    p.add_argument("--skip_save_results", action='store_true')
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    model_blacklist, model_whitelist = get_model_blacklist_whitelist(args.model_blacklist_file, args.model_whitelist_file, args.model_blacklist, args.model_whitelist)
    main_all_automata(
        game_str=args.game,
        world=args.world,
        k=args.k,
        n_games=args.n_games,
        timeout=args.timeout,
        save_results_dir=args.save_results_dir,
        max_workers=args.max_workers,
        seed=args.seed,
        include_random=not args.no_random,
        allowed_bot_nums=args.allowed_bot_nums,
        model_blacklist=model_blacklist,
        model_whitelist=model_whitelist,
        skip_save_results=args.skip_save_results,
    )
