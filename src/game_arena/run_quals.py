import argparse
import json
import time
from pathlib import Path
from typing import Optional, Any
from collections import defaultdict, Counter

import pandas as pd

from game_arena.run_leaderboard import get_model_blacklist_whitelist
from game_arena import utils
from game_arena import base
from game_arena.typing import BotPairGames, BotPath, MatchResults
from experimental.lm_arena.elo_analysis import get_leaderboard_table_df
from experimental.lm_arena.simple_example import _build_battles


logger = utils.setup_logging("run_quals.log", "run_quals", to_stdout=True)
ParentToBots = dict[str, list[BotPath]]

def get_ci_rankings(match_results: list[MatchResults], parent: list[str], old_ci_rankings: Optional[dict[str, Any]] = None, confidence_level: float = 0.95) -> dict[str, Any]:
    """
    Compute CI rankings for a given list of match results and parent models.

    Args:
        match_results: List of match results.
        old_ci_rankings: Old CI rankings (used to augment the new CI rankings).
        parent: List of parent models.
        confidence_level: Confidence level for the CI rankings.

    Returns:
        CI rankings for the parent models.
    """
    if old_ci_rankings is None:
        old_ci_rankings = {}
    if len(match_results) == 0:
        return old_ci_rankings
    quals_grouped_results = defaultdict(list)  # model_name -> list of match_results
    error_matches = []
    for m in match_results:
        name0 = m['name0'].split('/')
        name1 = m['name1'].split('/')
        if name0[0] != name1[0]:
            error_matches.append(m)
            continue
        model_name = name0[0]
        if model_name not in parent:  # already ranked
            continue
        quals_grouped_results[model_name].append(m)
    assert len(error_matches) == 0, f"Error matches ({len(error_matches)}): {error_matches}"
    ci_rankings = {}
    logger.info(f'Computing CI rankings for {len(quals_grouped_results)} parents')
    for model_name, match_results in quals_grouped_results.items():
        battles = _build_battles(match_results, "full", 0.0)  # type: ignore
        ci_rankings[model_name] = get_leaderboard_table_df(
            battles,
            rating_system="bt",
            num_bootstrap=100,
            num_cpu=1,
            confidence_level=confidence_level,
        )
    return {**old_ci_rankings, **ci_rankings}


def _get_past_match_counts(match_results: list[MatchResults]) -> Counter[frozenset[str]]:
    past_match_counts: Counter[frozenset[str]] = Counter()
    for m in match_results:
        key = (m['name0'], m['name1'])
        if key[0].split('/')[0] != key[1].split('/')[0]:
            logger.warning(f"Unexpected matchup in quals: {m}")
        past_match_counts[frozenset(key)] += 1
    return past_match_counts


def get_parents_to_do(parent_to_bots: dict[str, Any], ci_rankings: dict[str, Any], top_k_model_bots: int) -> dict[str, Any]:
    """
    Return parents whose top-k winners are still ambiguous.

    A lower `final_ranking` is better. For each parent, this function checks whether
    the top-`top_k_model_bots` bots are uniquely determined from `final_ranking`.

    Let `r_k` be the k-th smallest rank. The top-k is considered clear only if:
        count(rank < r_k) + count(rank == r_k) == k
    If a tie crosses the k-th boundary, the parent is marked todo.

    A parent is also marked todo when:
    - no dataframe exists for that parent or it is empty or 'final_ranking' is not in the columns,
    - or fewer than `k` valid (numeric) rankings are available.

    Args:
        parent_to_bots: Mapping `parent -> list of bots` to evaluate.
        ci_rankings: Mapping `parent -> pandas.DataFrame` containing `final_ranking`.
        top_k_model_bots: Number of winners to select (`k`), must be >= 1.

    Returns:
        Mapping `parent -> list of bots` that should be re-run / reviewed because top-k is not clear.

    Example:
        For ranks [1, 1, 2, 3, 3], top-k is clear for k=2,3,5 and unclear for k=1,4.
    """
    if top_k_model_bots < 1:
        raise ValueError("top_k_model_bots must be >= 1")
    out = []
    done_parents = []
    parents = list(parent_to_bots.keys())
    _log_str = []
    for p in parents:
        if p == 'random':
            _log_str += [f'parent {p} is random (done)']
            continue
        d = ci_rankings.get(p, [])
        expected_bots = {name for name, _ in parent_to_bots[p]}
        ranked_bots = {
            e.get('bot') for e in d
            if pd.notna(pd.to_numeric(e.get('final_ranking'), errors='coerce'))
        }
        if not expected_bots.issubset(ranked_bots):
            _log_str += [f'parent {p} has unranked candidate bots (STILL)']
            out.append(p)
            continue
        final_rankings = pd.Series([e.get('final_ranking') for e in d])
        if len(final_rankings) == 0:
            _log_str += [f'parent {p} has no rankings [{d}] (STILL)']
            out.append(p)
            continue
        ranks = pd.to_numeric(final_rankings, errors="coerce").dropna().sort_values().to_numpy()
        if ranks.size < top_k_model_bots:  # done
            _log_str += [f'parent {p} [{ranks}] (done)']
            done_parents.append(p)
            continue
        k = ranks[top_k_model_bots - 1]
        if int((ranks < k).sum() + (ranks == k).sum()) != top_k_model_bots:
            _log_str += [f'parent {p} [{ranks}] (STILL)']
            out.append(p)
        else:
            _log_str += [f'parent {p} [{ranks}] (done)']
            done_parents.append(p)
    logger.info(f'Current Parent Status ({len(parents)} parents): ' + ' | '.join(_log_str))
    logger.info(f'Done parents ({len(done_parents)}) by CI: {sorted(done_parents)}')
    return {p: parent_to_bots[p] for p in out}


def _build_todo(parent_to_bots: ParentToBots, top_k_model_bots: int, n_games: int, match_limit_L: int, match_results: list[MatchResults]) -> tuple[ParentToBots, BotPairGames]:
    assert top_k_model_bots > 0, f'top_k_model_bots must be greater than 0. Got {top_k_model_bots}'
    past_match_counts = _get_past_match_counts(match_results)
    parent_count = Counter()
    terminated_parents = []
    todo = []
    for model_name, model_bots in sorted(parent_to_bots.items()):
        if len(model_bots) <= top_k_model_bots:
            continue
        for i, p1 in enumerate(model_bots):
            for p2 in model_bots[i + 1:]:
                pair_past = past_match_counts[frozenset((p1[0], p2[0]))]
                next_n_games = min((match_limit_L - pair_past) // 2, n_games)
                if next_n_games > 0:
                    todo.append((p1, p2, next_n_games))
                    parent_count[model_name] += 1
        if model_name not in parent_count:
            terminated_parents.append(model_name)

    logger.info(f'  terminated parents ({len(terminated_parents)}) by match_limit_L={match_limit_L}: {sorted(terminated_parents)}')
    logger.info(f'  parents left ({len(parent_count)}): {sorted(parent_count.items())}')
    parent_to_bots = {k: v for k, v in parent_to_bots.items() if k in parent_count}
    return parent_to_bots, todo


def _load_previous_results(final_result_path: Path, config: dict[str, Any]) -> list[MatchResults]:
    if final_result_path.exists():
        with open(final_result_path, 'r') as f:
            global_results = json.load(f)
        logger.info(f'loading existing results with {len(global_results["match_results"])} previous match results')
        assert isinstance(global_results, dict), f'global_results is not a dict: {global_results}'
        assert isinstance(global_results.get('config'), dict), f'global_results["config"] is not a dict: {global_results.get("config")}'
        assert set(config.keys()) == set(global_results['config'].keys()), f'config keys do not match: {config.keys()} != {global_results["config"].keys()}'
        assert all(config[k] == global_results['config'][k] for k in config.keys()), f'config values do not match: {config} != {global_results["config"]}'
        return global_results['match_results']
    return []


def get_to_save_ci_rankings(ci_rankings: dict[str, Any], original_parent_to_bots: ParentToBots) -> dict[str, Any]:
    """Simply copies ci_rankings and if any bots is missing from the original_parent_to_bots, it adds it with a rating of None."""
    result = {p: list(v) for p, v in ci_rankings.items()}
    for p, orig_bots in original_parent_to_bots.items():
        entries = result.setdefault(p, [])
        seen = {e["bot"] for e in entries}
        for bot in orig_bots:
            name = bot[0]
            if name not in seen:
                entries.append({"bot": name, "rating": None})
                seen.add(name)
    return dict(sorted(result.items()))


def main_pre_elimination(game_str: str, world: str, n_games: int, top_k_model_bots: int, timeout: int, max_workers: int, save_results_dir: str, confidence_level: float, match_limit_L: int, seed: Optional[int] = None, allowed_bot_nums=None, model_blacklist=None, model_whitelist=None):
    t0 = time.perf_counter()
    logger.info(f'Starting quals for game {game_str}, world {world} with confidence level={confidence_level}, timeout={timeout}, top_k_model_bots={top_k_model_bots}, match_limit_L={match_limit_L}, max_workers={max_workers}, save_results_dir={save_results_dir}, seed={seed}, allowed_bot_nums={allowed_bot_nums}, model_blacklist={model_blacklist}, model_whitelist={model_whitelist}')
    game = utils.get_game(game_name=game_str)
    config = utils.get_config_file(game_str, world)
    bots = list(utils.get_bot_paths_from_world(game_str, world, add_random=True, allowed_bot_nums=allowed_bot_nums).items())
    assert len(bots) > 1, f'Need at least 2 bots to run quals. Got {len(bots)} bots. in game {game_str}, world {world}'
    def game_creator():
        return game(config)
    game_creator.__name__ = game.__name__

    if model_blacklist is not None:
        pre_filtered_len = len(bots)
        bots = [b for b in bots if b[0].split('/')[0] not in model_blacklist]
        logger.info(f'pre-blacklisting #bots = {pre_filtered_len}, post-blacklisting #bots = {len(bots)}')

    if model_whitelist is not None:
        pre_filtered_len = len(bots)
        bots = [b for b in bots if b[0].split('/')[0] in model_whitelist]
        logger.info(f'pre-whitelisting #bots = {pre_filtered_len}, post-whitelisting #bots = {len(bots)}')

    parent_to_bots: ParentToBots = defaultdict(list)  # claude_4.5_sonnet -> [('claude_4.5_sonnet/001', FN), ('claude_4.5_sonnet/002', FN), ('claude_4.5_sonnet/003', FN), ...], mistral_14b_2512: [...
    for bot in bots:
        model_name = bot[0].split('/')[0]
        parent_to_bots[model_name].append(bot)
    logger.info(f'#parent_to_bots = {len(parent_to_bots)}, #bots = {len(bots)}, confidence_level = {confidence_level}')
    original_parent_to_bots = parent_to_bots.copy()

    final_result_path = utils.get_root_path() / Path(save_results_dir) / f'matches_quals_{game_str}_{world}.json'
    run_config = {'game_str': game_str, 'world': world, 'timeout': timeout, 'seed': seed}
    match_results = _load_previous_results(final_result_path, run_config)
    ci_rankings = get_ci_rankings(match_results, parent=list(parent_to_bots.keys()), confidence_level=confidence_level, old_ci_rankings={})
    i = 0
    while True:
        parent_to_bots = get_parents_to_do(parent_to_bots, ci_rankings, top_k_model_bots)
        parent_to_bots, todo = _build_todo(parent_to_bots, top_k_model_bots, n_games, match_limit_L, match_results)
        if len(todo) == 0:
            break
        i += 1
        logger.info(f'ITERATION {i}: running one pre-elimination round robin for {len(todo)} pairs playing a total of {sum(2 * pair_n_games for _, _, pair_n_games in todo)} games')
        single_iter = base.play_all_2p_games(
            game,
            config,
            todo,
            seed=seed,
            timeout=timeout,
            max_workers=max_workers,
        )
        if len(single_iter) > 0:
            match_results.extend(single_iter)
        ci_rankings = get_ci_rankings(match_results, parent=list(parent_to_bots.keys()), confidence_level=confidence_level, old_ci_rankings=ci_rankings)
        final_result_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f'dumping results to {final_result_path}')
        with open(final_result_path, 'w') as f:
            ci_rankings_to_save = get_to_save_ci_rankings(ci_rankings, original_parent_to_bots)
            json.dump({'config': run_config, 'ci_rankings': ci_rankings_to_save, 'match_results': match_results}, f, indent=2)

    if not final_result_path.exists():  # create empty file
        final_result_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f'dumping results to {final_result_path}')
        with open(final_result_path, 'w') as f:
            ci_rankings_to_save = get_to_save_ci_rankings(ci_rankings, original_parent_to_bots)
            json.dump({'config': run_config, 'ci_rankings': ci_rankings_to_save, 'match_results': match_results}, f, indent=2)

    logger.info(f'final ci_rankings in {i} iterations: {[(k, [(e["bot"], e["final_ranking"]) for e in v]) for k, v in ci_rankings.items()]}')
    elapsed_m = (time.perf_counter() - t0) / 60
    logger.info(f'Finished quals for game={game_str}, world={world}, elapsed_m={elapsed_m:.2f}')


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run quals calculations.")
    parser.add_argument("--game", required=True, help="Value for the Game dropdown.")
    parser.add_argument("--world", required=True, help="Value for the World dropdown.")
    parser.add_argument("--n_games", type=int, required=True, help="n_games")
    parser.add_argument("--top_k_model_bots", type=int, required=True, help="top_k_model_bots in pre-elimination games")
    parser.add_argument("--timeout", type=int, required=True, help="timeout")
    parser.add_argument("--match_limit_L", type=int, required=True, help="Maximum number of matches allowed per parent model")
    parser.add_argument("--conf", type=float, required=True, help="confidence_level")
    parser.add_argument("--max_workers", type=int, default=12, help="max_workers")
    parser.add_argument("--seed", type=int, default=None, help="seed")
    parser.add_argument("--save_results_dir", type=str, required=True, help="save_results_dir")
    parser.add_argument("--allowed_bot_nums", type=str, default=None, help="allowed_bot_nums (comma-separated list of integers)")
    parser.add_argument("--model_blacklist_file", type=str, nargs='+', default=None, help="model_blacklist_file")
    parser.add_argument("--model_whitelist_file", type=str, nargs='+', default=None, help="model_whitelist_file")
    parser.add_argument("--model_blacklist", type=str, nargs='+', default=None, help="model_blacklist")
    parser.add_argument("--model_whitelist", type=str, nargs='+', default=None, help="model_whitelist")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = _parse_args()
    model_blacklist, model_whitelist = get_model_blacklist_whitelist(args.model_blacklist_file, args.model_whitelist_file, args.model_blacklist, args.model_whitelist)
    main_pre_elimination(
        game_str=args.game,
        world=args.world,
        n_games=int(args.n_games),
        timeout=int(args.timeout),
        max_workers=int(args.max_workers),
        confidence_level=args.conf,
        save_results_dir=args.save_results_dir,
        seed=args.seed,
        top_k_model_bots=args.top_k_model_bots,
        match_limit_L=args.match_limit_L,
        allowed_bot_nums=args.allowed_bot_nums,
        model_blacklist=model_blacklist,
        model_whitelist=model_whitelist,
    )
