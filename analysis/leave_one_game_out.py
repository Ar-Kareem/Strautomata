#!/usr/bin/env python3
"""Measure leaderboard sensitivity to leaving out one game.

The input is the per-game ``rating_df.csv`` produced by ``exp_plotting.py``.
For each game, this script recomputes model scores as the median Elo across all
remaining games and compares the resulting ranking with the full leaderboard.

It prints pandas DataFrames and OpenReview-compatible Markdown tables. When an
output directory is provided, it also writes the underlying CSVs and Markdown.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr


DEFAULT_RATINGS = Path(
    "analysis/results_tmp/plots_somerset_may_5/models_sample/rating_df.csv"
)
DEFAULT_OUTPUT_DIR = Path("analysis/results_tmp/leave_one_game_out")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recompute median-Elo rankings after removing each game."
    )
    parser.add_argument("--ratings", type=Path, default=DEFAULT_RATINGS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-k", type=int, default=10)
    return parser.parse_args()


def rank_scores(scores: pd.Series) -> pd.Series:
    """Assign deterministic ordinal ranks after sorting by score and model."""
    ordered = scores.rename("score").reset_index()
    ordered = ordered.rename(columns={ordered.columns[0]: "model"})
    ordered = ordered.sort_values(["score", "model"], ascending=[False, True])
    ordered["rank"] = range(1, len(ordered) + 1)
    return ordered.set_index("model")["rank"].reindex(scores.index)


def analyze(
    ratings: pd.DataFrame, top_k: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if top_k < 1:
        raise ValueError("--top-k must be at least 1")

    games = [column for column in ratings.columns if column != "Median ELO"]
    if len(games) < 2:
        raise ValueError("Ratings CSV must contain at least two game columns")

    per_game = ratings[games].apply(pd.to_numeric, errors="coerce")
    full_scores = per_game.median(axis=1, skipna=True)
    full_ranks = rank_scores(full_scores)
    full_order = full_ranks.sort_values().index.tolist()
    full_top_k = set(full_order[:top_k])

    summary_rows: list[dict[str, object]] = []
    rank_rows: list[dict[str, object]] = []

    for omitted_game in games:
        loo_scores = per_game.drop(columns=omitted_game).median(axis=1, skipna=True)
        loo_ranks = rank_scores(loo_scores)
        rank_delta = loo_ranks - full_ranks
        loo_order = loo_ranks.sort_values().index.tolist()

        rho = float(spearmanr(full_ranks, loo_ranks).statistic)
        largest_model = rank_delta.abs().idxmax()
        summary_rows.append(
            {
                "removed_game": omitted_game,
                "spearman_rho": rho,
                "mean_absolute_rank_shift": float(rank_delta.abs().mean()),
                "median_absolute_rank_shift": float(rank_delta.abs().median()),
                "maximum_absolute_rank_shift": int(rank_delta.abs().max()),
                f"top_{top_k}_overlap": len(
                    full_top_k.intersection(loo_order[:top_k])
                ),
                "top_5_overlap": len(
                    set(full_order[:5]).intersection(loo_order[:5])
                ),
                "top_1_unchanged": loo_order[0] == full_order[0],
                "largest_shift_model": largest_model,
                "largest_shift_from": int(full_ranks[largest_model]),
                "largest_shift_to": int(loo_ranks[largest_model]),
            }
        )

        for model in ratings.index:
            rank_rows.append(
                {
                    "removed_game": omitted_game,
                    "model": model,
                    "full_median_elo": float(full_scores[model]),
                    "leave_one_out_median_elo": float(loo_scores[model]),
                    "full_rank": int(full_ranks[model]),
                    "leave_one_out_rank": int(loo_ranks[model]),
                    "rank_shift": int(rank_delta[model]),
                    "absolute_rank_shift": int(abs(rank_delta[model])),
                }
            )

    summary_df = pd.DataFrame(summary_rows).sort_values(
        "spearman_rho", ascending=True
    )
    ranks_df = pd.DataFrame(rank_rows)

    top_rows: list[dict[str, object]] = []
    for model in full_order[:top_k]:
        model_ranks = ranks_df.loc[ranks_df["model"] == model, "leave_one_out_rank"]
        model_shifts = ranks_df.loc[ranks_df["model"] == model, "absolute_rank_shift"]
        top_rows.append(
            {
                "model": model,
                "full_rank": int(full_ranks[model]),
                "minimum_leave_one_out_rank": int(model_ranks.min()),
                "maximum_leave_one_out_rank": int(model_ranks.max()),
                "mean_absolute_rank_shift": float(model_shifts.mean()),
            }
        )
    top_models_df = pd.DataFrame(top_rows)
    return summary_df, ranks_df, top_models_df


def markdown_tables(
    summary_df: pd.DataFrame, top_models_df: pd.DataFrame, top_k: int
) -> str:
    summary_md = summary_df[
        [
            "removed_game",
            "spearman_rho",
            "mean_absolute_rank_shift",
            "maximum_absolute_rank_shift",
            f"top_{top_k}_overlap",
        ]
    ].copy()
    summary_md.columns = [
        "Removed game",
        "Spearman rho",
        "Mean absolute shift",
        "Maximum shift",
        f"Top-{top_k} overlap",
    ]
    summary_md["Spearman rho"] = summary_md["Spearman rho"].map(lambda x: f"{x:.3f}")
    summary_md["Mean absolute shift"] = summary_md[
        "Mean absolute shift"
    ].map(lambda x: f"{x:.2f}")
    summary_md[f"Top-{top_k} overlap"] = summary_md[
        f"Top-{top_k} overlap"
    ].map(lambda x: f"{x}/{top_k}")

    top_md = top_models_df.copy()
    top_md.columns = [
        "Model",
        "Full rank",
        "Best leave-one-out rank",
        "Worst leave-one-out rank",
        "Mean absolute shift",
    ]
    top_md["Mean absolute shift"] = top_md["Mean absolute shift"].map(
        lambda x: f"{x:.2f}"
    )

    return "\n".join(
        [
            "### Leave-one-game-out stability",
            "",
            summary_md.to_markdown(index=False),
            "",
            f"### Original top-{top_k} rank ranges",
            "",
            top_md.to_markdown(index=False),
            "",
        ]
    )


def print_aggregate(summary_df: pd.DataFrame, top_k: int) -> None:
    overlap_column = f"top_{top_k}_overlap"
    print("\nAggregate statistics")
    print(f"leave-one-out runs: {len(summary_df)}")
    print(
        "Spearman rho range: "
        f"{summary_df['spearman_rho'].min():.4f}--"
        f"{summary_df['spearman_rho'].max():.4f}"
    )
    print(f"Mean Spearman rho: {summary_df['spearman_rho'].mean():.4f}")
    print(
        "Mean absolute rank shift: "
        f"{summary_df['mean_absolute_rank_shift'].mean():.3f}"
    )
    print(
        "Largest rank shift: "
        f"{summary_df['maximum_absolute_rank_shift'].max()}"
    )
    print(
        f"Top-{top_k} overlap range: "
        f"{summary_df[overlap_column].min()}/{top_k}--"
        f"{summary_df[overlap_column].max()}/{top_k}"
    )
    print(
        "Top-1 unchanged: "
        f"{int(summary_df['top_1_unchanged'].sum())}/{len(summary_df)}"
    )


def latex_tables(summary_df: pd.DataFrame, top_k: int) -> str:
    esc = lambda t: str(t).replace("&", r"\&").replace("_", r"\_")  # noqa: E731
    rows = [f"{esc(r['removed_game'])} & {r['spearman_rho']:.3f} & {r['mean_absolute_rank_shift']:.2f} & "
            f"{int(r[f'top_{top_k}_overlap'])}/{top_k} \\\\" for _, r in summary_df.iterrows()]
    caption = (f"Leaderboard sensitivity to omitting one game. For each omitted game the model score is recomputed as the median "
               f"Elo over the remaining games and compared with the full leaderboard: Spearman $\\rho$ between the two rankings, "
               f"the mean absolute rank shift, and how many of the original top-{top_k} models remain in the top {top_k}.")
    return "\n".join([r"\begin{table}[t]", r"\centering", r"\small", rf"\caption{{{caption}}}", r"\label{tab:leave-one-game-out}",
                      r"\begin{tabular}{lrrr}", r"\toprule",
                      rf"Omitted game & Spearman $\rho$ & Mean abs. rank shift & Top-{top_k} overlap \\", r"\midrule",
                      *rows, r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])


def main() -> None:
    args = parse_args()
    ratings = pd.read_csv(args.ratings, index_col=0)
    summary_df, ranks_df, top_models_df = analyze(ratings, args.top_k)
    markdown = markdown_tables(summary_df, top_models_df, args.top_k)

    print("Leave-one-game-out summary DataFrame")
    print(summary_df.to_string(index=False))
    print("\nTop-model stability DataFrame")
    print(top_models_df.to_string(index=False))
    print_aggregate(summary_df, args.top_k)
    print("\nOpenReview Markdown\n")
    print(markdown)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(args.output_dir / "leave_one_game_out_summary.csv", index=False)
    ranks_df.to_csv(args.output_dir / "leave_one_game_out_all_ranks.csv", index=False)
    top_models_df.to_csv(
        args.output_dir / "leave_one_game_out_top_models.csv", index=False
    )
    (args.output_dir / "leave_one_game_out_tables.md").write_text(
        markdown, encoding="utf-8"
    )
    (args.output_dir / "leave_one_game_out_table.tex").write_text(latex_tables(summary_df, args.top_k))
    print(f"Wrote outputs (CSV, Markdown, leave_one_game_out_table.tex) to {args.output_dir}")


if __name__ == "__main__":
    main()
