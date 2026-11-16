import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd

from game_arena import utils as arena_utils
from game_arena import run_leaderboard
from experimental.lm_arena.elo_analysis import report_elo_analysis_results, pretty_print_elo_rating
from experimental.lm_arena.rating_systems import compute_bt
from experimental.exp_utils import NAME_DELETE, NAME_FIX_MAP

def _find_match_file(game: str, world: str, results_dir: str, match_file: Optional[str]) -> Path:
    results_path = arena_utils.get_root_path() / results_dir
    if match_file:
        candidate = Path(match_file)
        path = candidate if candidate.is_absolute() else results_path / candidate
        if not path.exists():
            raise FileNotFoundError(f"Match file not found: {path}")
        return path
    pattern = f"matches_{game}_{world}*.json"
    matches = list(results_path.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No match files found for {game} {world} in {results_path}")
    if len(matches) > 1:
        raise FileExistsError(f"Multiple match files found for {game} {world}: {matches}")
    return matches[0]


def _normalize_name(name: str, name_mode: str) -> str:
    if name_mode == "base":
        return name.split("/")[0]
    return name


def _build_battles(match_results: List[Dict], name_mode: str, base_tstamp: float) -> List[Dict]:
    battles: List[Dict] = []
    for idx, match in enumerate(match_results):
        reason, winner = arena_utils.get_match_result(match, verbose=False)
        if reason == "draw" or winner == 0.5:
            winner_label = "tie"
        elif winner == 0:
            winner_label = "model_a"
        elif winner == 1:
            winner_label = "model_b"
        else:
            raise ValueError(f"Unknown match result: {match}")
        battles.append(
            {
                "model_a": _normalize_name(match["name0"], name_mode),
                "model_b": _normalize_name(match["name1"], name_mode),
                "winner": winner_label,
                "tstamp": base_tstamp + idx,
                "anony": True,
                "language": "English",
            }
        )
    return battles


def _build_done_rate_stats(match_results: List[Dict], name_mode: str) -> Dict[str, Dict[str, float]]:
    done_counts: dict[str, int] = defaultdict(int)
    total_counts: dict[str, int] = defaultdict(int)
    for match in match_results:
        bot_names = (
            _normalize_name(match["name0"], name_mode),
            _normalize_name(match["name1"], name_mode),
        )
        is_done = bool(match.get("done", False))
        for bot_name in bot_names:
            total_counts[bot_name] += 1
            if is_done:
                done_counts[bot_name] += 1
    return {
        bot_name: {
            "done": float(done_counts.get(bot_name, 0)),
            "total": float(total_count),
            "done_rate": float(done_counts.get(bot_name, 0) / total_count) if total_count > 0 else 0.0,
        }
        for bot_name, total_count in total_counts.items()
    }


def _print_rating(rating: Dict[str, float], top_n: Optional[int]) -> None:
    if top_n is None:
        pretty_print_elo_rating(rating)
        return
    ordered = sorted(rating.items(), key=lambda item: -item[1])[:top_n]
    for idx, (name, score) in enumerate(ordered, start=1):
        print(f"{idx:2d}, {name:25s}, {score:.0f}")


def get_top_bot_per_model(match_results: List[Dict], rating_system: str = "elo", n: int = 1) -> set[str]:
    """Top-n bots (by a single BT fit over all bots) for every parent model."""
    if rating_system == "elo":
        raise NotImplementedError("should be easy to implement")
    elif rating_system == "bt":
        all_battles = _build_battles(match_results, 'full', 0.0)
        elo_ratings = compute_bt(pd.DataFrame(all_battles))
    else:
        raise ValueError(f"Unknown rating system: {rating_system}")
    per_model: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for model, elo in elo_ratings.items():
        per_model[model.split('/')[0]].append((float(elo), model))
    top_bots: set[str] = set()
    for bots in per_model.values():
        bots.sort(key=lambda x: (-x[0], x[1]))
        top_bots.update(bot for _, bot in bots[:n])
    return top_bots


def _aggregate_bots_to_models(results: Dict, parent_battles: pd.DataFrame) -> Dict:
    """Turn a bot-level rating result into a model-level one where each model's rating is the MEAN of its bots'
    ratings (averaged per bootstrap sample so the CIs are those of the mean). Battle-based fields use parent names."""
    bootstrap_df: pd.DataFrame = results["bootstrap_df"]
    parents = bootstrap_df.columns.map(lambda c: str(c).split("/")[0])
    model_bootstrap_df = bootstrap_df.T.groupby(parents).mean().T
    final = pd.Series(results["elo_rating_final"], dtype=float)
    model_final = final.groupby(final.index.map(lambda c: str(c).split("/")[0])).mean()
    q025, q975 = model_bootstrap_df.quantile(0.025), model_bootstrap_df.quantile(0.975)
    ranking = {}
    for a in model_final.index:
        ranking[a] = 1 + sum(1 for b in model_final.index if b != a and q025[b] > q975[a])
    leaderboard_table_df = pd.DataFrame(
        {
            "rating": model_final,
            "variance": model_bootstrap_df.var(),
            "rating_q975": q975,
            "rating_q025": q025,
            "num_battles": parent_battles["model_a"].value_counts().add(parent_battles["model_b"].value_counts(), fill_value=0),
            "final_ranking": pd.Series(ranking),
        }
    )
    out = dict(results)
    out.update(
        {
            "elo_rating_final": model_final.to_dict(),
            "elo_rating_online": model_final.to_dict(),
            "bootstrap_df": model_bootstrap_df,
            "leaderboard_table_df": leaderboard_table_df,
            "battles": parent_battles,
            "bot_level_results": {k: results[k] for k in ("elo_rating_final", "bootstrap_df", "leaderboard_table_df")},
        }
    )
    return out


def get_match_results(game: str, world: str, match_file: Optional[str] = None, results_dir: str = "results"):
    match_path = _find_match_file(game, world, results_dir, match_file)
    with match_path.open("r") as f:
        match_json = json.load(f)
    match_results = run_leaderboard.filter_matches_to_qual_bots(match_json["match_results"], match_json.get("qual_bot_names"), label=f"{match_path.name}: ")
    return match_results, match_json.get("now", 0.0)

def main_results(match_results_all: List[Dict], base_tstamp = 0.0, rating_system: str = "elo", num_bootstrap: int = 100, exclude_tie: bool = False, num_cpu: int = 12, top: Optional[int] = None, seed: int = 42, only_model: bool = True, model_repr: str = "top1"):
    """model_repr (only_model=True): "top1" = the best bot stands in for the model; "top2mean" = the model's rating is the
    mean of its two best bots' ratings and its battles/done rates pool both bots' games."""
    all_bots = run_leaderboard.get_all_bots(match_results_all)
    if model_repr not in ("top1", "top2mean"):
        raise ValueError(f"Unknown model_repr: {model_repr}")
    n_top = 2 if model_repr == "top2mean" else 1
    if only_model:
        top_bots_per_model = get_top_bot_per_model(match_results_all, rating_system, n=n_top)
        match_results = run_leaderboard.filter_matches_by_bot_names(match_results_all, top_bots_per_model, remove_bot_number=(n_top == 1))
        name_mode = "base" if n_top == 1 else "full"
    else:
        match_results = match_results_all
        name_mode = "full"
    parent_level = only_model and n_top > 1  # rate bots individually, then report per parent model
    if parent_level:  # names are still "parent/NNN" here: apply the parent-level ignore/fix maps to the parent part
        match_results = [m for m in match_results if m['name0'].split('/')[0] not in NAME_DELETE and m['name1'].split('/')[0] not in NAME_DELETE]
        for m in match_results:
            for k in ('name0', 'name1'):
                parent, _, num = m[k].partition('/')
                m[k] = NAME_FIX_MAP.get(parent, parent) + '/' + num
    else:
        match_results = [m for m in match_results if m['name0'] not in NAME_DELETE and m['name1'] not in NAME_DELETE]
        for m in match_results:
            m['name0'] = NAME_FIX_MAP.get(m['name0'], m['name0'])
            m['name1'] = NAME_FIX_MAP.get(m['name1'], m['name1'])
    stats_matches = match_results
    if parent_level:
        stats_matches = run_leaderboard.filter_matches_by_bot_names(match_results, {m[k] for m in match_results for k in ("name0", "name1")}, remove_bot_number=True)
    error_turn_count = run_leaderboard.get_error_turn_count(stats_matches)
    done_rate_stats = _build_done_rate_stats(stats_matches, "base" if only_model else "full")
    print(f"Filtered {len(match_results_all)} matches to {len(match_results)} matches")

    battles = _build_battles(match_results, name_mode, base_tstamp)    
    if not battles:
        raise RuntimeError("No valid battles to rate after filtering/skipping.")

    results = report_elo_analysis_results(
        battles,
        rating_system=rating_system,
        num_bootstrap=num_bootstrap,
        exclude_models=[],
        langs=[],
        exclude_tie=exclude_tie,
        exclude_unknown_lang=False,
        daily_vote_per_user=None,
        run_outlier_detect=False,
        scale=1,
        filter_func=lambda x: True,
        style_control=False,
        num_cpu=num_cpu,
    )
    if parent_level:
        results = _aggregate_bots_to_models(results, pd.DataFrame(_build_battles(stats_matches, "base", base_tstamp)))
    results['model_repr'] = model_repr if only_model else None
    results['error_turn_count'] = error_turn_count
    results['done_rate_stats'] = done_rate_stats
    results['top_bots_per_model'] = top_bots_per_model if only_model else None
    results['all_bots'] = all_bots
    results['raw_match_results'] = stats_matches
    return results


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=str, help="Game id, e.g. amazons")
    parser.add_argument("--world", type=str, help="World id, e.g. world1")
    parser.add_argument("--match-file", type=str, help="Override match file path or name in results dir")
    parser.add_argument("--results-dir", type=str, default="results")
    parser.add_argument("--name-mode", choices=["base", "full"], default="base")
    parser.add_argument("--rating-system", choices=["elo", "bt"], default="elo")
    parser.add_argument("--num-bootstrap", type=int, default=100)
    parser.add_argument("--exclude-tie", action="store_true", default=False)
    parser.add_argument("--num-cpu", type=int, default=12)
    parser.add_argument("--top", type=int, default=None, help="Show only top N ratings")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    # Example: python src/experimental/lm_arena/simple_example.py --game amazons --world world1
    args = parse_args()
    np.random.seed(args.seed)
    match_results_all, base_tstamp = get_match_results(args.game, args.world, args.match_file, args.results_dir)
    results = main_results(match_results_all, base_tstamp, args.rating_system, args.num_bootstrap, args.exclude_tie, args.num_cpu, args.top, args.seed, args.only_model)
    print(f"Game: {args.game} | World: {args.world} | File: {args.match_file}")
    print("# Online Elo")
    _print_rating(results["elo_rating_online"], args.top)
    print("# Median Elo")
    _print_rating(results["elo_rating_final"], args.top)
