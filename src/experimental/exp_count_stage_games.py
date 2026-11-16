#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from game_arena import utils as arena_utils


ROOT_DIR = arena_utils.get_root_path()


def _load_games_world_columns() -> list[tuple[str, str, str, Any]]:
    exp_utils_path = Path(__file__).resolve().parent / "exp_utils.py"
    module = ast.parse(exp_utils_path.read_text(encoding="utf-8"), filename=str(exp_utils_path))
    for node in module.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        if not isinstance(node.target, ast.Name):
            continue
        if node.target.id != "MAIN_GAMES_WORLD_COLUMNS":
            continue
        return ast.literal_eval(node.value)
    raise ValueError(f"Could not find MAIN_GAMES_WORLD_COLUMNS in {exp_utils_path}")


MAIN_GAMES_WORLD_COLUMNS = _load_games_world_columns()
GAME_ALIAS_MAP = {(game, world): alias for game, world, alias, _ in MAIN_GAMES_WORLD_COLUMNS}
GAME_ORDER = [(game, world) for game, world, _, _ in MAIN_GAMES_WORLD_COLUMNS]


@dataclass(frozen=True)
class MatchFileSummary:
    game: str
    world: str
    n_matches: int
    n_automata: int

    @property
    def game_world(self) -> str:
        return f"{self.game}/{self.world}"


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count Qualifiers and Tournament match totals per game/world in a results folder."
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Results directory containing subfolders like quals/ and tourney/.",
    )
    return parser.parse_args()


def _is_automata_name(name: Any) -> bool:
    return isinstance(name, str) and bool(name)


def _count_automata_names(names: list[Any]) -> int:
    return len({str(name) for name in names if _is_automata_name(name)})


def _quals_has_random_bot(payload: dict[str, Any]) -> bool:
    ci_rankings = payload.get("ci_rankings")
    if not isinstance(ci_rankings, dict):
        return False
    for rows in ci_rankings.values():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and row.get("bot") == "random":
                return True
    return False


def _summary_from_match_json(path: Path) -> MatchFileSummary:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON payload in {path}: expected dict.")

    config = payload.get("config")
    if not isinstance(config, dict):
        raise ValueError(f"Invalid JSON payload in {path}: missing dict key 'config'.")

    match_results = payload.get("match_results")
    if not isinstance(match_results, list):
        raise ValueError(f"Invalid JSON payload in {path}: missing list key 'match_results'.")

    game = config.get("game_str")
    world = config.get("world")
    if not isinstance(game, str) or not game:
        raise ValueError(f"Invalid JSON payload in {path}: missing string config['game_str'].")
    if not isinstance(world, str) or not world:
        raise ValueError(f"Invalid JSON payload in {path}: missing string config['world'].")

    qual_bot_names = payload.get("qual_bot_names")
    if isinstance(qual_bot_names, list):
        n_automata = _count_automata_names(qual_bot_names)
        # Tournament files resumed after a qualifier change keep matches of bots that no longer qualify
        # (see agents_todo/stale_tourney_matches.md). Only count matches between qualified bots.
        allowed = {str(name) for name in qual_bot_names if _is_automata_name(name)}
        match_results = [
            m for m in match_results
            if isinstance(m, dict) and m.get("name0") in allowed and m.get("name1") in allowed
        ]
    else:
        match_bot_names: list[Any] = []
        for match in match_results:
            if not isinstance(match, dict):
                continue
            match_bot_names.append(match.get("name0"))
            match_bot_names.append(match.get("name1"))
        n_automata = _count_automata_names(match_bot_names)
        if _quals_has_random_bot(payload):
            n_automata += 1

    return MatchFileSummary(game=game, world=world, n_matches=len(match_results), n_automata=n_automata)


def _load_stage_summaries(stage_dir: Path) -> dict[tuple[str, str], MatchFileSummary]:
    summaries: dict[tuple[str, str], MatchFileSummary] = {}
    if not stage_dir.exists():
        return summaries

    for path in sorted(stage_dir.glob("*.json")):
        summary = _summary_from_match_json(path)
        key = (summary.game, summary.world)
        summaries[key] = summary
    return summaries


def _latex_escape(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
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


def _display_name(game: str, world: str) -> str:
    return GAME_ALIAS_MAP.get((game, world), f"{game}/{world}")


def _render_latex_table(
    quals_summaries: dict[tuple[str, str], MatchFileSummary],
    tourney_summaries: dict[tuple[str, str], MatchFileSummary],
) -> str:
    present_keys = set(quals_summaries) | set(tourney_summaries)
    ordered_keys = [key for key in GAME_ORDER if key in present_keys]
    extra_keys = sorted(present_keys - set(ordered_keys))
    keys = ordered_keys + extra_keys
    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"\textbf{Game} &",
        r"\makecell{\textbf{\# Automata}\\\textbf{Pre-Quals}} &",
        r"\makecell{\textbf{\# Automata}\\\textbf{in Tournament}} &",
        r"\textbf{Qualifiers} &",
        r"\textbf{Tournament} \\",
        r"\midrule",
    ]

    total_qual_automata = 0
    total_tourney_automata = 0
    total_quals = 0
    total_tourney = 0
    for game, world in keys:
        quals_summary = quals_summaries.get((game, world))
        tourney_summary = tourney_summaries.get((game, world))
        qual_automata = quals_summary.n_automata if quals_summary is not None else 0
        tourney_automata = tourney_summary.n_automata if tourney_summary is not None else 0
        quals = quals_summary.n_matches if quals_summary is not None else 0
        tourney = tourney_summary.n_matches if tourney_summary is not None else 0
        total_qual_automata += qual_automata
        total_tourney_automata += tourney_automata
        total_quals += quals
        total_tourney += tourney
        lines.append(
            f"{_latex_escape(_display_name(game, world))} & {qual_automata} & {tourney_automata} & {quals} & {tourney} \\\\"
        )

    lines.extend(
        [
            r"\midrule",
            f"Total & {total_qual_automata} & {total_tourney_automata} & {total_quals} & {total_tourney} \\\\",
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    results_dir = _resolve_path(args.results_dir)
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory does not exist: {results_dir}")
    if not results_dir.is_dir():
        raise NotADirectoryError(f"Results path is not a directory: {results_dir}")

    quals_summaries = _load_stage_summaries(results_dir / "quals")
    tourney_summaries = _load_stage_summaries(results_dir / "tourney")

    if not quals_summaries and not tourney_summaries:
        raise ValueError(
            f"No match JSON files found in {results_dir}. Expected JSON files under quals/ and/or tourney/."
        )

    print(_render_latex_table(quals_summaries, tourney_summaries))


if __name__ == "__main__":
    main()
