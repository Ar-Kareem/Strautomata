"""Adaptive live play: rate one LLM against the automata of a tourney.

Each round: rate the LLM with the paper's rating pipeline (simple_example.main_results, BT, bots mode) on the tourney's
matches plus the LLM's live games, pick the not-yet-overused bots whose rating is closest to the LLM's, and play one
more game per colour against each. Stops once the 95% bootstrap CI half-width is below --target_ci (and the LLM has
both a non-loss and a non-win, so its rating is finite), at --max_games usable games, or once --max_unusable unusable
games exist in total (e.g. the free-tier daily limit was hit); it then refuses to run until they are moved out by hand.

No rating code lives here. The only live-specific logic is turning a saved live game into a match record
(live_game_to_match): finished games as is, forfeits (d['forfeit'], set by live_play) as tourney-style errors. Any other
failed game is unusable; live_play saves those to LIVE_UNSAVED_DIR, so their slot is replayed.
"""
import json
import argparse
from typing import Optional

import numpy as np

from game_arena.utils import get_root_path, get_match_result, get_bot_paths_from_world
from game_arena.live_play import (play_live_game, get_live_play_counts, resolve_model, llm_player_name, logger,
                                  LIVE_RESULTS_DIR, LIVE_UNSAVED_DIR)
from experimental.lm_arena import simple_example


def live_game_to_match(d: dict) -> Optional[dict]:
    """Match record for a saved live game (readable by utils.get_match_result), or None if the game is unusable.
    A forfeit (live_play sets d['forfeit'] when the erring player is at fault) is scored like a tourney error: the
    erring player loses. Any other unfinished game failed because of the harness / API and is unusable."""
    if d.get('done'):
        return d
    if d.get('forfeit'):
        # same shape as tourney error records: 'r' holds the game result (player_err_counts, move_count, exception)
        return {**d, 'winner': 'error', 'r': {k: d.get(k) for k in ('player_err_counts', 'done', 'move_count', 'exception')}}
    return None


def load_games(save_name: str, game_world: str) -> list[Optional[dict]]:
    """Match records of the LLM's saved games in time order, None for unusable ones (all games in LIVE_UNSAVED_DIR)."""
    files = []
    for dir_name in (LIVE_RESULTS_DIR, LIVE_UNSAVED_DIR):
        files += [(fp.name, fp, dir_name == LIVE_RESULTS_DIR) for fp in (get_root_path() / dir_name / save_name / game_world).glob('*.json')]
    return [live_game_to_match(json.loads(fp.read_text())) if in_results_dir else None for _, fp, in_results_dir in sorted(files)]


def pick_opponents(est: float, pool: dict[str, float], played: dict[str, int], n: int, max_per_bot: int) -> list[str]:
    """Closest-rated bots, one per parent model, skipping bots already played max_per_bot times."""
    picked, parents = [], set()
    for bot in sorted(pool, key=lambda b: (abs(pool[b] - est), played.get(b, 0))):
        parent = bot.split('/')[0]
        if parent in parents or played.get(bot, 0) >= max_per_bot:
            continue
        picked.append(bot)
        parents.add(parent)
        if len(picked) == n:
            break
    return picked


def run(args: argparse.Namespace) -> None:
    model = resolve_model(args.model)
    llm_name = llm_player_name(model)
    for gw in args.game_worlds.split(','):
        game_str, world = gw.split('/')
        game_world = f'{game_str}_{world}'
        tourney, base_tstamp = simple_example.get_match_results(game_str, world, None, args.tourney_dir)
        playable_bots = get_bot_paths_from_world(game_str, world)  # bots with loadable code ('random' is rated but not playable here)
        for round_idx in range(args.max_rounds):
            games = load_games(model.save_name, game_world)
            usable = [m for m in games if m is not None]
            n_unusable = len(games) - len(usable)

            # rating: the paper's pipeline (BT + bootstrap CI, bots mode) on tourney + live games
            np.random.seed(42)
            lb = simple_example.main_results(tourney + usable, base_tstamp, rating_system='bt',
                                             num_bootstrap=100, num_cpu=args.num_cpu, only_model=False)['leaderboard_table_df']
            pool = {b: float(lb.at[b, 'rating']) for b in lb.index if b in playable_bots}
            scores = [get_match_result(m, False) for m in usable]
            llm_idx = [0 if m['name0'] == llm_name else 1 for m in usable]
            draws = sum(r == 'draw' for r, _ in scores)
            wins = sum(r != 'draw' and w == i for (r, w), i in zip(scores, llm_idx))  # 'win' / 'error' both return the winner's index
            losses = len(usable) - wins - draws
            if llm_name in lb.index:
                est = float(lb.at[llm_name, 'rating'])
                half_width = float(lb.at[llm_name, 'rating_q975'] - lb.at[llm_name, 'rating_q025']) / 2
            else:
                est, half_width = float(np.median(list(pool.values()))), float('inf')
            finite = (wins + draws) > 0 and (losses + draws) > 0
            logger.info(f"ADAPTIVE {gw} round {round_idx}: {len(usable)} usable / {len(games)} saved games, W/D/L {(wins, draws, losses)}, "
                        f"rating {est:.0f} +- {half_width:.0f} (finite: {finite}), unusable {n_unusable}")
            if finite and half_width <= args.target_ci and len(usable) >= args.min_games:
                logger.info(f"ADAPTIVE {gw}: done, CI target reached")
                break
            if len(usable) >= args.max_games:
                logger.info(f"ADAPTIVE {gw}: done, max_games reached without the CI target")
                break
            if n_unusable >= args.max_unusable:
                logger.error(f"MANUAL INTERVENTION NEEDED: {gw} has {n_unusable} unusable games (--max_unusable {args.max_unusable}); move them out of {get_root_path() / LIVE_UNSAVED_DIR / model.save_name / game_world} to continue")
                break
            counts = get_live_play_counts(game_world)[llm_name]  # bot -> colour -> games saved in LIVE_RESULTS_DIR
            played = {bot: max(per_color.values()) for bot, per_color in counts.items()}
            opponents = pick_opponents(est, pool, played, args.bots_per_round, args.max_games_per_bot // 2)
            if not opponents:
                logger.warning(f"ADAPTIVE {gw}: no eligible opponents left")
                break
            logger.info(f"ADAPTIVE {gw}: next opponents {[(b, round(pool[b])) for b in opponents]}")
            if args.dry_run:
                break
            for bot in opponents:  # one more game per colour vs each
                for llm_color in ('A', 'B'):
                    play_live_game(args.model, game_str, world, bot, llm_color, history_len=args.history_len,
                                   show_legal_moves=args.show_legal_moves, request_timeout=args.request_timeout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=True)
    parser.add_argument('--game_worlds', type=str, required=True, help='e.g. connect4/world1,chess/worlduci1')
    parser.add_argument('--tourney_dir', type=str, required=True, help='tourney whose automata the LLM is rated against, e.g. results_current/results_somerset_feb_20/tourney')
    parser.add_argument('--target_ci', type=float, default=100.0, help='stop when the 95%% CI half-width (Elo) is below this')
    parser.add_argument('--min_games', type=int, default=20)
    parser.add_argument('--max_games', type=int, default=80)
    parser.add_argument('--max_rounds', type=int, default=100)
    parser.add_argument('--bots_per_round', type=int, default=3)
    parser.add_argument('--max_games_per_bot', type=int, default=4)
    parser.add_argument('--max_unusable', type=int, default=6, help='stop (and require manual cleanup) once this many unusable games exist in total')
    parser.add_argument('--num_cpu', type=int, default=8)
    parser.add_argument('--history_len', type=int, default=-1)
    parser.add_argument('--show_legal_moves', action='store_true')
    parser.add_argument('--request_timeout', type=float, default=None)
    parser.add_argument('--dry_run', action='store_true', help='print the current rating and next opponents without playing')
    run(parser.parse_args())
