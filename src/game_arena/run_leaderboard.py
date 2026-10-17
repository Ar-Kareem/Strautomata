import os
from pathlib import Path
import time
import json
import copy
import warnings
import argparse
from typing import Any, Optional
from datetime import datetime
from collections import defaultdict, Counter

import numpy as np
import pandas as pd

from game_arena import base
from game_arena import utils
from game_arena.typing import BotPath
from game_arena.utils import setup_logging, get_match_result, get_player_result

logger = setup_logging("run_leaderboard.log", "run_leaderboard", to_stdout=True)
failure_log = setup_logging("failure_log.log", "failure_log")


def sum_array(l1, l2):
    if l1 is None or np.isnan(l1).all() or l2 is None or np.isnan(l2).all():
        return l2
    return [a + b for a, b in zip(l1, l2)]

def get_scores_from_match_data(all_data, verbose: bool = False):
    d = defaultdict(list)
    for m in all_data:
        d[m['name0']].append(get_player_result(m, 0, verbose))
        d[m['name1']].append(get_player_result(m, 1, verbose))
    counts = {k: Counter(v) for k, v in d.items()}
    df = pd.DataFrame.from_dict(counts, orient="index").fillna(0).astype(int)
    df = df.reindex(columns=['win', 'loss', 'draw', 'error', 'timeout', 'enemy_error', 'enemy_timeout'], fill_value=0)
    return df

def get_all_bots(all_data):
    bots = set([m['name0'] for m in all_data] + [m['name1'] for m in all_data])
    bots_dict = defaultdict(list)
    for bot in bots:
        bots_dict[bot.split('/')[0]].append(bot)
    return bots_dict

def filter_matches_by_bot_names(all_data, bot_names: set[str], remove_bot_number: bool = False):
    results = [m for m in all_data if m['name0'] in bot_names and m['name1'] in bot_names]
    if remove_bot_number:
        results = copy.deepcopy(results)
        for m in results:
            m['name0'] = m['name0'].split('/')[0]
            m['name1'] = m['name1'].split('/')[0]
    return results


def filter_matches_to_qual_bots(match_results: list[dict], qual_bot_names: Optional[list[str]], label: str = "") -> list[dict]:
    """Drop matches involving bots that are not in the file's qualifier list.

    Tournament files are resumed in place: if the qualifier set changes between launches, matches of bots that
    no longer qualify stay in the file (see agents_todo/stale_tourney_matches.md). Those bots must not be
    candidates for top-k selection or rating, so we keep only matches where both players qualified.
    """
    if qual_bot_names is None:
        return match_results
    allowed = set(qual_bot_names)
    kept = [m for m in match_results if m["name0"] in allowed and m["name1"] in allowed]
    if len(kept) != len(match_results):
        stale = sorted({m[k] for m in match_results for k in ("name0", "name1")} - allowed)
        print(f"{label}dropped {len(match_results) - len(kept)} of {len(match_results)} matches involving {len(stale)} non-qualified (stale) bots: {stale}")
    return kept


def get_error_turn_count(all_data):
    error_turn_count = defaultdict(list)
    timeout_count = defaultdict(int)
    for m in all_data:
        m_results = get_match_result(m, verbose=False)
        if m_results[0] == 'win' or m_results[0] == 'draw':  # match finished
            continue
        winner = m_results[1]
        loser_name = m['name0'] if winner == 1 else m['name1']
        if m_results[0] == 'timeout':  # timeout doesnt have count
            timeout_count[loser_name] += 1
            continue
        elif m_results[0] == 'error':
            turn_count = m['r'].get('move_count', None)
            if turn_count is None:
                turn_count = m['r'].get('other', {}).get('move_count', None)
            assert turn_count is not None, f"turn_count is None for match: {m}"
            error_turn_count[loser_name].append(turn_count)
        else:
            assert False, f"Unknown match result: {m_results}"
    return error_turn_count, timeout_count


def get_elo_df(all_data, correct_names, verbose: bool = True, iters: int = 20, learning_rate: float = 32):
    for m in all_data:
        m['name0'] = correct_names[m['name0']]
        m['name1'] = correct_names[m['name1']]
    all_names = set(correct_names.values())
    games = [(m['name0'], m['name1'], 1 - get_match_result(m, verbose)[1]) for m in all_data]  # 1 - winner; because ELO is defined to be "0" means player_0 LOST while "1" means player_0 WON. draw stays 0.5
    ratings = utils.infer_elo(games, iters=iters, K=learning_rate)
    ratings_all = {n: -9999 for n in all_names} | ratings
    elo_df = pd.DataFrame(ratings_all, index=['ELO']).T.round(2).sort_values('ELO', ascending=False)
    return elo_df


def display_data(all_data, game_str, world, config, combine_method: str = 'none', verbose: bool = True):
    if len(all_data) == 0:
        return None, None, None
    all_names = set([m['name0'] for m in all_data] + [m['name1'] for m in all_data])
    correct_names = {k: v for k, v in zip(all_names, all_names)}
    top_n = None
    n_top_models = None
    if combine_method == 'combine':
        for k in correct_names:
            if '/' in k:
                correct_names[k] = k[:k.rfind('/')]
    elif combine_method == 'top_1':
        top_n = 1
    elif combine_method == 'none':
        top_n = None
    else:
        assert False, f"Unknown combine method: {combine_method}"
    elo_df = get_elo_df(all_data, correct_names, verbose=verbose)
    if top_n == 1:
        elo_df['model'] = elo_df.index.str.split('/').str[0]
        elo_df = elo_df.groupby('model', group_keys=False).apply(lambda x: x.nlargest(top_n, 'ELO'))
        elo_df = elo_df.sort_values('ELO', ascending=False)
        n_top_models = elo_df.index
        elo_df = elo_df.reset_index(drop=True).set_index('model')

    df = get_scores_from_match_data(all_data, verbose=verbose)
    df_index = df.index
    if n_top_models is not None:
        df = df.loc[n_top_models]
    summary_perc_df = (df.div(df.sum(axis=1), axis=0) * 100).round(2).sort_values(['win', 'loss'], ascending=[False, True])
    summary_df = df.sort_values(['win', 'loss'], ascending=[False, True])

    pairs = {(matchup['name0'], matchup['name1']): [0, 0, 0, 0] for matchup in all_data}
    for matchup in all_data:
        p = (matchup['name0'], matchup['name1'])
        if not matchup['done']:
            pairs[p][3] += 1
        elif matchup['winner'] == 0:
            pairs[p][0] += 1
        elif matchup['winner'] == 1:
            pairs[p][1] += 1
        else:
            pairs[p][2] += 1
    name_to_idx = {n: f'b{i}' for i, n in enumerate(df_index)}
    df = pd.DataFrame(index=list(name_to_idx.keys()), columns=list(name_to_idx.values()), dtype=object)
    for idx in df.index:
        for col in df.columns:
            df.at[idx, col] = np.nan
    for (p, q), v in pairs.items():
        df.loc[p, name_to_idx[q]] = sum_array(df.loc[p, name_to_idx[q]], v)
        v_t = (v[1], v[0], v[2], v[3])
        df.loc[q, name_to_idx[p]] = sum_array(df.loc[q, name_to_idx[p]], v_t)
    bot_bot_df = df.copy()

    if verbose:
        print('Game:', game_str, '| world#:', world, '| config:', config)
        print('ELO:')
        print(elo_df)
        # print('summary per bot (percentage):')
        # display(summary_perc_df)
        # print('summary per bot:')
        # display(summary_df)
        # print('bot/bot stats:')
        # for name, i in name_to_idx.items():
        #     print(i, name)
        # print()
        # print('Notation: (#wins, #losses, #draws, #errors)')
        # display(bot_bot_df)

    return summary_perc_df, bot_bot_df, elo_df


def get_elo_df_combined(all_data, combine_method: str, verbose: bool = True, iters: int = 20, learning_rate: float = 32):
    all_names = set([m['name0'] for m in all_data] + [m['name1'] for m in all_data])
    correct_names = {k: v for k, v in zip(all_names, all_names)}
    top_n = None
    n_top_models = None
    if combine_method == 'combine':
        for k in correct_names:
            if '/' in k:
                correct_names[k] = k[:k.rfind('/')]
    elif combine_method == 'top_1':
        top_n = 1
    elif combine_method == 'none':
        top_n = None
    else:
        assert False, f"Unknown combine method: {combine_method}"
    elo_df = get_elo_df(all_data, correct_names, verbose=verbose, iters=iters, learning_rate=learning_rate)
    if top_n == 1:
        _top_model_df = elo_df.copy()
        _top_model_df['model'] = _top_model_df.index.str.split('/').str[0]
        with warnings.catch_warnings():
            warnings.simplefilter(action="ignore", category=FutureWarning)
            _top_model_df = _top_model_df.groupby('model', group_keys=False).apply(lambda x: x.nlargest(top_n, 'ELO'))
        n_top_models = _top_model_df.index
    return elo_df, n_top_models


def display_world(game_str: str, world: str, match_json: str, combine_method: str, verbose: bool = True):
    world_dir = utils.get_examples_dir(game_str) / world
    config = utils.get_config_file(game_str, world)
    if os.path.exists(world_dir / match_json):
        with open(world_dir / match_json, 'r') as f:
            match_json_data = json.load(f)
    elif os.path.exists(utils.get_root_path() / 'results' / match_json):
        with open(utils.get_root_path() / 'results' / match_json, 'r') as f:
            match_json_data = json.load(f)
    else:
        assert False, f"Match JSON file not found {match_json}: does not exist at {world_dir / match_json} or {utils.get_root_path() / 'results' / match_json}"
    all_data = filter_matches_to_qual_bots(match_json_data['match_results'], match_json_data.get('qual_bot_names'))
    result = display_data(all_data, game_str, world, config, combine_method=combine_method, verbose=verbose)
    return result

def print_failures(results):
    failed_matches = [m for m in results['match_results'] if not m['done']]
    short_reason = defaultdict(list)
    long_reason = defaultdict(list)
    for m in failed_matches:
        r = m.get('r', None)
        if r is None:
            continue
        player_err_counts = r.get('player_err_counts', None)
        if player_err_counts is None:
            continue
        name = m['name0'] if player_err_counts[0] == 1 else m['name1']
        exception = r.get('exception', None)
        long_exception = r.get('exception_traceback', None)
        if exception not in short_reason[name]:
            short_reason[name].append(exception)
        if long_exception not in long_reason[name]:
            long_reason[name].append(long_exception)
    print('Qualifier Round Failures:')
    for name, reasons in sorted(short_reason.items()):
        print(f"Player {name} failed {len(reasons)} times:", end=' ')
        if len(reasons) == 1:
            print(f"  {reasons[0]}")
        else:
            print()
            for reason in reasons:
                print(f"  {reason}")
        new_line_reason = '\n'.join(reasons)
        failure_log.info(f"Player {name} failed {len(reasons)} times: {new_line_reason}")
    for name, reasons in sorted(long_reason.items()):
        new_line_long_reason = '\n'.join(reasons)
        failure_log.info(f"Player {name} long exception: \n{new_line_long_reason}")
    failure_log.info('--------------------------------')


def _load_previous_results(final_result_path: Path, config: dict, qual_bot_names: Optional[set[str]] = None) -> dict:
    
    if final_result_path.exists():
        with open(final_result_path, 'r') as f:
            global_results = json.load(f)
        logger.info(f'loading existing results with {len(global_results["match_results"])} previous match results from {final_result_path}')
        assert isinstance(global_results, dict), f'global_results is not a dict: {global_results}'
        # assert config is the same
        assert isinstance(global_results.get('config'), dict), f'global_results["config"] is not a dict: {global_results["config"]}'
        assert set(config.keys()) == set(global_results['config'].keys()), f'config keys do not match: {config.keys()} != {global_results["config"].keys()}'
        assert all(config[k] == global_results['config'][k] for k in config.keys()), f'config values do not match: {config} != {global_results["config"]}'
        # assert qual_bot_names is compatible when quals filtering is enabled
        assert (global_results.get('qual_bot_names') is None) == (qual_bot_names is None), f'qual_bot_names does not match: {global_results.get("qual_bot_names")} != {qual_bot_names}'
        if qual_bot_names is not None:  # its okay for qual bots to have new bots. Not okay the other way around.
            if not set(qual_bot_names).issuperset(set(global_results['qual_bot_names'])):
                logger.warning(f'qual_bot_names does not match: extra bots {set(global_results['qual_bot_names']) - set(qual_bot_names)}')
            global_results['qual_bot_names'] = sorted(list(qual_bot_names))
        return global_results
    else:
        logger.info(f'no previous results found at {final_result_path}. Creating new results file.')
        global_results = {
            'config': config,
            'qual_bot_names': sorted(list(qual_bot_names)) if qual_bot_names is not None else None,
            'match_results': [],
        }
        return global_results


def _build_todo_with_resume(bots: list[BotPath], n_games: int, past_match_results: list[dict[str, Any]]) -> list[tuple[BotPath, BotPath, int]]:
    past_counts: Counter[frozenset[str]] = Counter()
    for m in past_match_results:
        past_counts[frozenset((m['name0'], m['name1']))] += 1

    todo: list[tuple[BotPath, BotPath, int]] = []
    for i, p1 in enumerate(bots):
        for p2 in bots[i + 1:]:
            key = frozenset((p1[0], p2[0]))
            already_done_n_games = past_counts[key] // 2
            remaining_n_games = n_games - already_done_n_games
            if remaining_n_games > 0:
                todo.append((p1, p2, remaining_n_games))
    return todo

def _build_todo_with_resume_A_vs_B(bots1: list[BotPath], bots2: list[BotPath], n_games: int, past_match_results: list[dict[str, Any]]) -> list[tuple[BotPath, BotPath, int]]:
    past_counts: Counter[frozenset[str]] = Counter()
    for m in past_match_results:
        past_counts[frozenset((m['name0'], m['name1']))] += 1

    todo: list[tuple[BotPath, BotPath, int]] = []
    for i, p1 in enumerate(bots1):
        for p2 in bots2:
            key = frozenset((p1[0], p2[0]))
            already_done_n_games = past_counts[key] // 2
            remaining_n_games = n_games - already_done_n_games
            if remaining_n_games > 0:
                todo.append((p1, p2, remaining_n_games))
    return todo


def main_leaderboard(
        game_str: str,
        world: str,
        n_games: int,
        timeout: int,
        save_results_dir: str,
        max_workers: int,
        seed: Optional[int] = None,
        quals_dir: Optional[str] = None,
        top_k_model_bots: Optional[int] = None,
        skip_save_results: bool = False,
        model_blacklist: Optional[list[str]] = None,
        model_whitelist: Optional[list[str]] = None,
        allowed_bot_nums: Optional[str] = None,
    ):
    logger.info(f'Starting leaderboard for game {game_str}, world {world}: n_games = {n_games}, timeout = {timeout}, save_results_dir = {save_results_dir}, max_workers = {max_workers}, seed = {seed}, quals_dir = {quals_dir}, top_k_model_bots = {top_k_model_bots}, skip_save_results = {skip_save_results}, model_blacklist = {model_blacklist}, model_whitelist = {model_whitelist}, allowed_bot_nums = {allowed_bot_nums}')
    assert not (quals_dir is not None and allowed_bot_nums is not None), \
        "--allowed_bot_nums cannot be combined with --quals_dir: the qualifiers already decide which bots advance"
    game = utils.get_game(game_name=game_str)
    main_world = world
    if '&' in world:
        main_world = world.split('&')[0]
    config = utils.get_config_file(game_str, main_world)
    if '&' not in world:
        bots: list[BotPath] = list(utils.get_bot_paths_from_world(game_str, world, add_random=True, allowed_bot_nums=allowed_bot_nums).items())
    else:
        bots = []
        for world_part in world.split('&'):
            cur = list(utils.get_bot_paths_from_world(game_str, world_part, add_random=True, allowed_bot_nums=allowed_bot_nums).items())
            cur = [(f'{world_part}:{bot_name}', bot_path) for bot_name, bot_path in cur]
            bots.extend(cur)
    print(f'n bots = {len(bots)}')
    assert len(bots) > 1, f'Need at least 2 bots to run a leaderboard. Got {len(bots)} bots. in game {game_str}, world {world}'
    def game_creator():
        return game(config)
    game_creator.__name__ = game.__name__

    if model_blacklist is not None:
        pre_filtered_len = len(bots)
        bots = [b for b in bots if b[0].split('/')[0] not in model_blacklist]
        print(f'pre-blacklisting #bots = {pre_filtered_len}, post-blacklisting #bots = {len(bots)}')

    if model_whitelist is not None:
        pre_filtered_len = len(bots)
        bots = [b for b in bots if b[0].split('/')[0] in model_whitelist]
        print(f'pre-whitelisting #bots = {pre_filtered_len}, post-whitelisting #bots = {len(bots)}')

    pre_filtered_len = len(bots)
    qual_bot_names = None
    if quals_dir is not None:
        assert top_k_model_bots is not None, "top_k_model_bots is required when quals_json is provided"
        quals_json = utils.get_root_path() / Path(quals_dir) / f'matches_quals_{game_str}_{world}.json'
        assert quals_json.exists(), f"Quals JSON file not found {quals_json}"
        with open(quals_json, 'r') as f:
            quals_data = json.load(f)
        ci_rankings = quals_data['ci_rankings']
        qual_bot_names = set(['random'])
        for model_name, rankings in ci_rankings.items():
            qual_bots_sorted = sorted(rankings, key=lambda x: x['rating'] if x.get('rating') is not None else 0, reverse=True)
            top_k_bot_names = [e['bot'] for e in qual_bots_sorted[:top_k_model_bots]]
            qual_bot_names.update(top_k_bot_names)
        bots = [b for b in bots if b[0] in qual_bot_names]
        del quals_data
    post_filtered_len = len(bots)
    print(f'pre-filtered #bots = {pre_filtered_len}, post-filtered #bots = {post_filtered_len}')

    run_config = {'game_str': game_str, 'world': world, 'timeout': timeout, 'seed': seed}
    final_result_path = utils.get_root_path() / Path(save_results_dir) / f'matches_{game_str}_{world}.json'
    global_results = _load_previous_results(final_result_path, run_config, qual_bot_names)
    todo = _build_todo_with_resume(bots, n_games, global_results.get('match_results', []))
    print(f'game = {game_str}, world = {world}, len(todo) = {len(todo)}')
    if len(todo) == 0:
        print('No games to play. Exiting.')
        return
    cur_id = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    start_time = time.time()
    logger.info(f'game = {game_str}, world = {world}, #pre-filtered bots = {pre_filtered_len}, #post-filtered bots = {post_filtered_len}, #todo = {len(todo)}, n_games = {n_games}, timeout = {timeout}, max_workers = {max_workers}. start time: {start_time}. {cur_id}')
    print('TRUE TOURNAMENT:')

    result = base.play_all_2p_games(
        game,
        config,
        todo,
        seed=seed,
        timeout=timeout,
        max_workers=max_workers,
    )
    global_results['match_results'].extend(result)

    elapsed_time = time.time() - start_time
    logger.info(f'done playing all games {game_str}, world = {world}. elapsed minutes: {elapsed_time / 60:.2f}. {cur_id}')

    if skip_save_results:
        print('skipping saving results')
        return
    final_result_path.parent.mkdir(parents=True, exist_ok=True)
    with open(final_result_path, 'w') as f:
        json.dump(global_results, f, indent=2)


def get_model_blacklist_whitelist(model_blacklist_file: str, model_whitelist_file: str, model_blacklist: list[str], model_whitelist: list[str]) -> tuple[list[str], Optional[list[str]]]:
    b_res = []
    w_res = []
    if isinstance(model_blacklist_file, str):
        model_blacklist_file = [model_blacklist_file]
    if isinstance(model_whitelist_file, str):
        model_whitelist_file = [model_whitelist_file]
    whitelist_loaded = False
    if model_blacklist_file is not None:
        for file in model_blacklist_file:
            with open(file, 'r') as f:
                b_res.extend(json.load(f)['model_ignore'])
    if model_whitelist_file is not None:
        for file in model_whitelist_file:
            with open(file, 'r') as f:
                w_res.extend(json.load(f)['model_whitelist'])
        whitelist_loaded = True
    if model_blacklist is not None:
        b_res.extend(model_blacklist)
    if model_whitelist is not None:
        w_res.extend(model_whitelist)
        whitelist_loaded = True
    b_res = list(set(b_res))
    w_res = list(set(w_res))
    if not whitelist_loaded:
        w_res = None
    return b_res, w_res


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run leaderboard calculations or display leaderboard results.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_main = subparsers.add_parser("main", help="Run all leaderboard match pairs.")
    parser_main.add_argument("--game", required=True, help="Value for the Game dropdown.")
    parser_main.add_argument("--world", required=True, help="Value for the World dropdown.")
    parser_main.add_argument("--quals_dir", type=str, default=None, help="The directory containing the qualifiers results.")
    parser_main.add_argument("--top_k_model_bots", type=int, default=None, help="top_k_model_bots in qualifiers")
    parser_main.add_argument("--n_games", type=int, required=True, help="n_games")
    parser_main.add_argument("--save_results_dir", type=str, required=True, help="save_results_dir")
    parser_main.add_argument("--max_workers", type=int, default=12, help="max_workers")
    parser_main.add_argument("--timeout", type=int, default=5, help="timeout")
    parser_main.add_argument("--seed", type=int, default=None, help="seed")
    parser_main.add_argument("--skip_save_results", action='store_true', help="skip_save_results")
    parser_main.add_argument("--model_blacklist_file", type=str, nargs='+', default=None, help="model_blacklist_file")
    parser_main.add_argument("--model_whitelist_file", type=str, nargs='+', default=None, help="model_whitelist_file")
    parser_main.add_argument("--model_blacklist", type=str, nargs='+', default=None, help="model_blacklist")
    parser_main.add_argument("--model_whitelist", type=str, nargs='+', default=None, help="model_whitelist")
    parser_main.add_argument("--allowed_bot_nums", type=str, default=None, help="comma-separated bot numbers to include per model, e.g. '1' or '1,2' (same as run_quals)")

    parser_display = subparsers.add_parser("display", help="Display leaderboard results for a world.")
    parser_display.add_argument("--game", required=True, help="Value for the Game dropdown.")
    parser_display.add_argument("--world", required=True, help="Value for the World dropdown.")
    parser_display.add_argument("--match_json", required=True, help="Value for the Match JSON dropdown.")
    parser_display.add_argument("--combine_method", required=True, help="Value for the Combine Method dropdown.")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = _parse_args()
    if args.command == "main":
        model_blacklist, model_whitelist = get_model_blacklist_whitelist(args.model_blacklist_file, args.model_whitelist_file, args.model_blacklist, args.model_whitelist)
        main_leaderboard(
            game_str=args.game,
            world=args.world,
            quals_dir=args.quals_dir,
            top_k_model_bots=args.top_k_model_bots,
            n_games=int(args.n_games),
            timeout=int(args.timeout),
            seed=args.seed,
            max_workers=int(args.max_workers),
            skip_save_results=args.skip_save_results,
            save_results_dir=args.save_results_dir,
            model_blacklist=model_blacklist,
            model_whitelist=model_whitelist,
            allowed_bot_nums=args.allowed_bot_nums,
        )
    elif args.command == "display":
        # python -m game_arena.run_leaderboard display --game lines_of_action --world world1 --match_json matches_lines_of_action_world1_36_2.json --combine_method combine
        summary_df, bot_bot_stats, elo_df = display_world(
            game_str=args.game,
            world=args.world,
            match_json=args.match_json,
            combine_method=args.combine_method,
        )
        if summary_df is not None and bot_bot_stats is not None and elo_df is not None:
            summary_df.to_csv('summary_df.csv')
            bot_bot_stats.to_csv('bot_bot_stats.csv')
            elo_df.to_csv('elo_df.csv')
        else:
            print('No summary data to save')
