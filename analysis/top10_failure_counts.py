#!/usr/bin/env python3
"""Report attributable failures for top-ranked models' selected automata.

The model ranking is read from the same ``rating_df.csv`` used to create the
median-Elo plot. Match-level failure information comes from ``results_models``
in the experiment pickle, which contains the top-1 automaton selected for each
model/game pair.

Only load pickle files produced by a trusted source.
"""

from __future__ import annotations

import argparse
import pickle
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

try:  # pretty model names as used in the figures; fall back to raw names
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from experimental.exp_utils import model_name_map as _model_name_map  # noqa: E402
except Exception:  # pragma: no cover
    _model_name_map = lambda name: name  # noqa: E731


def _tex_escape(text: str) -> str:
    return str(text).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def latex_model_table(model_df: pd.DataFrame, player_games_note: str = "") -> str:
    """booktabs table of attributable failures per model, same layout as the NeurIPS submission table."""
    kinds = ["illegal", "timeout", "runtime", "compile"]
    rows = []
    for _, r in model_df.iterrows():
        cells = [_tex_escape(_model_name_map(str(r["model"])))] + [f"{int(r[k])}" for k in kinds]
        cells += [f"{int(r['total_failures'])}", f"{r['failure_rate_percent']:.2f}\\%"]
        rows.append(" & ".join(cells) + r" \\")
    tot = {k: int(model_df[k].sum()) for k in kinds}
    tot_all = int(model_df["total_failures"].sum()); pg = int(model_df["player_games"].sum())
    rate = 100.0 * tot_all / pg if pg else float("nan")
    total_row = " & ".join([r"\textbf{Total}"] + [rf"\textbf{{{tot[k]}}}" for k in kinds] + [rf"\textbf{{{tot_all}}}", rf"\textbf{{{rate:.2f}\%}}"]) + r" \\"
    n = len(model_df); per_model = int(model_df["player_games"].iloc[0]) if n else 0
    caption = (f"Attributable failures for the selected automata of each top-{n} model across 20 games. "
               f"Each model has {per_model:,} player-games{player_games_note}. Failure rate is the fraction of player-games "
               "ending in an attributable illegal move, timeout, runtime error, or compile error.")
    return "\n".join([r"\begin{table}[t]", r"\centering", r"\small", rf"\caption{{{caption}}}", rf"\label{{tab:top{n}-failure-counts}}",
                      r"\begin{tabular}{lrrrrrr}", r"\toprule", r"Model & Illegal & Timeout & Runtime & Compile & Total & Failure rate \\", r"\midrule",
                      *rows, r"\midrule", total_row, r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])


DEFAULT_PICKLE = Path("analysis/results_tmp/exp_results_somerset_may_5.pkl")
DEFAULT_RATINGS = Path(
    "analysis/results_tmp/plots_somerset_may_5/models_sample/rating_df.csv"
)
FAILURE_KINDS = ("illegal", "timeout", "runtime", "compile")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Count attributable illegal moves, timeouts, runtime errors, and "
            "compile errors for the top models' selected automata."
        )
    )
    parser.add_argument("--pickle", type=Path, default=DEFAULT_PICKLE)
    parser.add_argument("--ratings", type=Path, default=DEFAULT_RATINGS)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="If set, write model, game, and model-game CSV files here.",
    )
    return parser.parse_args()


def classify_failure(record: dict[str, Any]) -> tuple[str | None, list[str]]:
    """Return the failure kind and the model(s) attributable for a match."""
    names = [str(record.get("name0")), str(record.get("name1"))]

    if record.get("winner") == "timeout" or record.get("timeout_hit") is not None:
        timeout_hit = record.get("timeout_hit")
        blamed: list[str] = []
        if isinstance(timeout_hit, (list, tuple)) and timeout_hit:
            try:
                blamed = [names[int(timeout_hit[0])]]
            except (ValueError, TypeError, IndexError):
                pass

        if not blamed:
            match = re.search(r"\('([01])'", str(record.get("exception", "")))
            if match:
                blamed = [names[int(match.group(1))]]
        return "timeout", blamed

    result = record.get("r")
    error_counts: list[Any] = []
    if isinstance(result, dict):
        candidate = result.get("player_err_counts")
        if isinstance(candidate, list):
            error_counts = candidate

    if record.get("winner") != "error" and not any(error_counts):
        return None, []

    blamed = [
        names[index]
        for index, count in enumerate(error_counts[:2])
        if count
    ]
    result_dict = result if isinstance(result, dict) else {}
    exception_text = "\n".join(
        [
            str(result_dict.get("exception") or record.get("exception") or ""),
            str(
                result_dict.get("exception_traceback")
                or record.get("exception_traceback")
                or ""
            ),
        ]
    )

    if re.search(r"\b(SyntaxError|IndentationError|TabError)\b", exception_text):
        kind = "compile"
    elif re.search(
        r"Invalid move|illegal move|not a legal|Malformed|Could not parse|"
        r"invalid action",
        exception_text,
        flags=re.IGNORECASE,
    ):
        kind = "illegal"
    else:
        kind = "runtime"
    return kind, blamed


def load_inputs(
    pickle_path: Path, ratings_path: Path, top_n: int
) -> tuple[dict[str, Any], pd.DataFrame, list[str]]:
    if top_n < 1:
        raise ValueError("--top-n must be at least 1")

    with pickle_path.open("rb") as handle:
        payload = pickle.load(handle)  # noqa: S301 - input is a trusted local artifact

    results = payload.get("results_models")
    if not isinstance(results, dict) or not results:
        raise ValueError("Pickle does not contain a non-empty 'results_models' mapping")

    ratings = pd.read_csv(ratings_path, index_col=0)
    if "Median ELO" not in ratings.columns:
        raise ValueError("Ratings CSV does not contain a 'Median ELO' column")

    ratings = ratings.sort_values("Median ELO", ascending=False)
    top_models = [str(name) for name in ratings.index[:top_n]]
    if len(top_models) < top_n:
        raise ValueError(
            f"Requested top {top_n}, but ratings contain only {len(top_models)} models"
        )
    return results, ratings, top_models


def calculate(
    results: dict[str, Any],
    ratings: pd.DataFrame,
    top_models: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Counter[str]]:
    games = list(results)
    counts: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    player_games: Counter[tuple[str, str]] = Counter()
    unattributed: Counter[str] = Counter()

    top_set = set(top_models)
    for game, game_result in results.items():
        records = game_result.get("raw_match_results", [])
        for record in records:
            names = [str(record.get("name0")), str(record.get("name1"))]
            for model in names:
                if model in top_set:
                    player_games[(model, game)] += 1

            kind, blamed = classify_failure(record)
            if kind is None:
                continue
            if not blamed:
                unattributed[kind] += 1
            for model in blamed:
                if model in top_set:
                    counts[(model, game)][kind] += 1

    model_game_rows: list[dict[str, Any]] = []
    for rank, model in enumerate(top_models, start=1):
        for game in games:
            counter = counts[(model, game)]
            denominator = player_games[(model, game)]
            total = sum(counter[kind] for kind in FAILURE_KINDS)
            model_game_rows.append(
                {
                    "rank": rank,
                    "model": model,
                    "median_elo": float(ratings.loc[model, "Median ELO"]),
                    "game": game,
                    "player_games": denominator,
                    **{kind: counter[kind] for kind in FAILURE_KINDS},
                    "total_failures": total,
                    "failure_rate_percent": (
                        100.0 * total / denominator if denominator else 0.0
                    ),
                }
            )
    model_game_df = pd.DataFrame(model_game_rows)

    model_df = (
        model_game_df.groupby(
            ["rank", "model", "median_elo"], as_index=False, sort=True
        )
        .agg(
            player_games=("player_games", "sum"),
            illegal=("illegal", "sum"),
            timeout=("timeout", "sum"),
            runtime=("runtime", "sum"),
            compile=("compile", "sum"),
            total_failures=("total_failures", "sum"),
            failure_free_games=("total_failures", lambda values: int((values == 0).sum())),
        )
        .sort_values("rank")
    )
    model_df["failure_rate_percent"] = (
        100.0 * model_df["total_failures"] / model_df["player_games"]
    )

    game_df = (
        model_game_df.groupby("game", as_index=False, sort=False)
        .agg(
            player_games=("player_games", "sum"),
            illegal=("illegal", "sum"),
            timeout=("timeout", "sum"),
            runtime=("runtime", "sum"),
            compile=("compile", "sum"),
            total_failures=("total_failures", "sum"),
            affected_automata=("total_failures", lambda values: int((values > 0).sum())),
        )
    )
    game_df["failure_rate_percent"] = (
        100.0 * game_df["total_failures"] / game_df["player_games"]
    )
    return model_df, game_df, model_game_df, unattributed


def print_report(
    model_df: pd.DataFrame,
    game_df: pd.DataFrame,
    model_game_df: pd.DataFrame,
    unattributed: Counter[str],
) -> None:
    display_models = model_df.copy()
    display_models["median_elo"] = display_models["median_elo"].round(2)
    display_models["failure_rate_percent"] = display_models[
        "failure_rate_percent"
    ].round(3)

    display_games = game_df.copy()
    display_games["failure_rate_percent"] = display_games[
        "failure_rate_percent"
    ].round(3)

    print("\nFailure counts by model")
    print(display_models.to_string(index=False))
    print("\nFailure counts by game")
    print(display_games.to_string(index=False))

    totals = Counter()
    for kind in FAILURE_KINDS:
        totals[kind] = int(model_df[kind].sum())
    total_player_games = int(model_df["player_games"].sum())
    total_failures = sum(totals.values())
    failure_free = int((model_game_df["total_failures"] == 0).sum())
    total_automata = len(model_game_df)

    print("\nAggregate")
    print(f"player-games: {total_player_games:,}")
    for kind in FAILURE_KINDS:
        print(f"{kind}: {totals[kind]:,}")
    print(f"total failures: {total_failures:,}")
    print(f"failure rate: {100.0 * total_failures / total_player_games:.3f}%")
    print(
        f"failure-free model-game automata: {failure_free}/{total_automata} "
        f"({100.0 * failure_free / total_automata:.1f}%)"
    )

    if unattributed:
        print(f"unattributed failure records: {dict(unattributed)}")

    concentrated = game_df.sort_values("total_failures", ascending=False).head(2)
    top_two_failures = int(concentrated["total_failures"].sum())
    top_two_names = ", ".join(concentrated["game"].astype(str))
    print(
        f"two highest-failure games ({top_two_names}): "
        f"{top_two_failures:,}/{total_failures:,} "
        f"({100.0 * top_two_failures / total_failures:.1f}%)"
    )

    print("\nHighest-failure model-game selections")
    worst = model_game_df.sort_values("total_failures", ascending=False).head(15)
    columns = [
        "model",
        "game",
        "player_games",
        "illegal",
        "timeout",
        "runtime",
        "compile",
        "total_failures",
        "failure_rate_percent",
    ]
    print(worst[columns].round({"failure_rate_percent": 2}).to_string(index=False))


def main() -> None:
    args = parse_args()
    results, ratings, top_models = load_inputs(
        args.pickle, args.ratings, args.top_n
    )
    model_df, game_df, model_game_df, unattributed = calculate(
        results, ratings, top_models
    )
    print_report(model_df, game_df, model_game_df, unattributed)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        model_df.to_csv(args.output_dir / "failure_counts_by_model.csv", index=False)
        game_df.to_csv(args.output_dir / "failure_counts_by_game.csv", index=False)
        model_game_df.to_csv(
            args.output_dir / "failure_counts_by_model_game.csv", index=False
        )
        (args.output_dir / "failure_counts_by_model.tex").write_text(latex_model_table(model_df))
        print(f"\nWrote CSVs and failure_counts_by_model.tex to {args.output_dir}")


if __name__ == "__main__":
    main()
