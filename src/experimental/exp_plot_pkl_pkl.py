#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

from experimental.exp_utils import model_name_map


matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare exp-results PKLs with scatter plots or correlation heatmaps."
    )
    parser.add_argument("--pkl-a", type=str, default=None, help="First input PKL path (scatter mode).")
    parser.add_argument("--pkl-b", type=str, default=None, help="Second input PKL path (scatter mode).")
    parser.add_argument("--mode", choices=["models", "bots", "corr-heatmap"], default="models")
    parser.add_argument(
        "--corr-granularity",
        choices=["models", "bots"],
        default="models",
        help="Granularity to use for corr-heatmap mode.",
    )
    parser.add_argument("--pkls", nargs="+", default=None, help="Input PKLs for corr-heatmap mode.")
    parser.add_argument("--names", nargs="+", default=None, help="Display names for corr-heatmap rows/cols.")
    parser.add_argument("--corr-method", choices=["pearson", "spearman", "kendall"], default="spearman")
    parser.add_argument("--corr-metric", choices=["median_elo", "mean_rank"], default="median_elo")
    parser.add_argument("--corr-out-pdf", type=str, default="pkl_corr_heatmap.pdf")
    parser.add_argument("--corr-out-png", type=str, default="pkl_corr_heatmap.png")
    parser.add_argument("--corr-csv-name", type=str, default="pkl_corr_heatmap.csv")
    parser.add_argument("--out-dir", type=str, default=None, help="Output directory (default: pkl-a parent).")
    parser.add_argument("--out-pdf", type=str, default="pkl_compare_scatter.pdf")
    parser.add_argument("--out-png", type=str, default="pkl_compare_scatter.png")
    parser.add_argument("--csv-name", type=str, default="pkl_compare_metrics.csv")
    parser.add_argument("--label-a", type=str, default=None, help="Custom label for PKL A in axis labels.")
    parser.add_argument("--label-b", type=str, default=None, help="Custom label for PKL B in axis labels.")
    parser.add_argument("--x-axis", type=str, default=None, help="Override x-axis label for both subplots.")
    parser.add_argument("--y-axis", type=str, default=None, help="Override y-axis label for both subplots.")
    parser.add_argument(
        "--game",
        type=str,
        default=None,
        help="Optional game selector (e.g. checkers, Checkers, chess:worlduci1). When set, compares per-game ELO/rank instead of global median/mean.",
    )
    parser.add_argument("--annotate", action="store_true", default=False, help="Annotate points with model names.")
    return parser.parse_args()


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str).resolve()
    return path


def _load_payload(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        payload = pickle.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid payload in {path}: expected dict, got {type(payload).__name__}")
    return payload


def _extract_results(payload: dict[str, Any], mode: str) -> dict[str, Any]:
    key = f"results_{mode}"
    results = payload.get(key)
    if isinstance(results, dict):
        return results

    # Backward compatibility with older PKLs that only had "results".
    if mode == "models" and isinstance(payload.get("results"), dict):
        return payload["results"]

    raise KeyError(f"Could not find '{key}' in payload.")


def _normalize_key(value: str) -> str:
    return str(value).strip().lower()


def _resolve_game_column(payload: dict[str, Any], results: dict[str, Any], game_selector: str) -> str:
    keys = [str(k) for k in results.keys()]
    selector = _normalize_key(game_selector)

    exact = [k for k in keys if _normalize_key(k) == selector]
    if exact:
        return exact[0]

    run_cols: list[str] = []
    runs = payload.get("runs")
    if isinstance(runs, list):
        for item in runs:
            if not isinstance(item, (list, tuple)) or len(item) < 3:
                continue
            game, world, colname = str(item[0]), str(item[1]), str(item[2])
            if selector in {
                _normalize_key(game),
                _normalize_key(colname),
                _normalize_key(f"{game}:{world}"),
                _normalize_key(f"{game}/{world}"),
            }:
                run_cols.append(colname)
    if run_cols:
        run_col_keys = {_normalize_key(c) for c in run_cols}
        run_matches = [k for k in keys if _normalize_key(k) in run_col_keys]
        run_matches = list(dict.fromkeys(run_matches))
        if len(run_matches) == 1:
            return run_matches[0]
        if len(run_matches) > 1:
            raise ValueError(
                f"Ambiguous --game '{game_selector}'. Matched multiple game columns: {run_matches}. "
                "Use a more specific selector."
            )

    partial = [k for k in keys if selector in _normalize_key(k)]
    partial = list(dict.fromkeys(partial))
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        raise ValueError(
            f"Ambiguous --game '{game_selector}'. Partial matches: {partial}. Use a more specific selector."
        )

    raise ValueError(
        f"Could not resolve --game '{game_selector}'. Available game columns: {keys}"
    )


def _metrics_from_results(results: dict[str, Any], selected_game: str | None = None) -> pd.DataFrame:
    ratings: list[pd.Series] = []
    ranks: list[pd.Series] = []

    for game_key, result in results.items():
        game_col_str = str(game_key)
        if selected_game is not None and game_col_str != selected_game:
            continue
        if not isinstance(result, dict):
            continue
        leaderboard_df = result.get("leaderboard_table_df")
        if not isinstance(leaderboard_df, pd.DataFrame):
            continue
        assert isinstance(leaderboard_df, pd.DataFrame), f"leaderboard_df is not a pandas DataFrame: {type(leaderboard_df)}"
        if "rating" in leaderboard_df.columns:
            ratings.append(pd.to_numeric(leaderboard_df["rating"], errors="coerce").rename(game_col_str))
        else:
            print(f"No rating column found for {game_col_str}: columns={leaderboard_df.columns}")
        if "final_ranking" in leaderboard_df.columns:
            ranks.append(pd.to_numeric(leaderboard_df["final_ranking"], errors="coerce").rename(game_col_str))

    if not ratings:
        if selected_game is not None:
            raise ValueError(f"No rating columns found for selected game '{selected_game}'.")
        raise ValueError("No rating columns found in PKL results.")
    if not ranks:
        if selected_game is not None:
            raise ValueError(f"No final_ranking columns found for selected game '{selected_game}'.")
        raise ValueError("No final_ranking columns found in PKL results.")

    rating_df = pd.concat(ratings, axis=1)
    rank_df = pd.concat(ranks, axis=1)
    if selected_game is not None:
        out = pd.DataFrame(
            {
                "median_elo": rating_df.iloc[:, 0],
                "mean_rank": rank_df.iloc[:, 0],
            }
        )
    else:
        out = pd.DataFrame(
            {
                "median_elo": rating_df.median(axis=1, skipna=True),
                "mean_rank": rank_df.mean(axis=1, skipna=True),
            }
        )
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def _scatter_with_diag(
    ax: plt.Axes,
    x: pd.Series,
    y: pd.Series,
    *,
    title: str,
    xlabel: str,
    ylabel: str,
    annotate: bool,
    names: pd.Series,
) -> None:
    mask = x.notna() & y.notna()
    x_f = x[mask]
    y_f = y[mask]

    ax.scatter(x_f, y_f, s=26, alpha=0.9, color="#1f77b4", edgecolors="white", linewidths=0.4)
    if len(x_f) > 0:
        lo = float(min(x_f.min(), y_f.min()))
        hi = float(max(x_f.max(), y_f.max()))
        if np.isfinite(lo) and np.isfinite(hi):
            pad = 0.03 * (hi - lo if hi > lo else 1.0)
            lo -= pad
            hi += pad
            ax.plot([lo, hi], [lo, hi], linestyle="--", linewidth=1.0, color="#666666")
            ax.set_xlim(lo, hi)
            ax.set_ylim(lo, hi)

    if annotate:
        for idx in x_f.index:
            label = str(names.get(idx, idx))
            ax.annotate(label, (float(x_f.loc[idx]), float(y_f.loc[idx])), fontsize=6, alpha=0.85)

    corr_txt = "rho=n/a, tau=n/a"
    if len(x_f) >= 2:
        spearman = x_f.corr(y_f, method="spearman")
        kendall = x_f.corr(y_f, method="kendall")
        if np.isfinite(spearman) and np.isfinite(kendall):
            corr_txt = f"rho={spearman:.3f}, tau={kendall:.3f}"
        elif np.isfinite(spearman):
            corr_txt = f"rho={spearman:.3f}, tau=n/a"
        elif np.isfinite(kendall):
            corr_txt = f"rho=n/a, tau={kendall:.3f}"
    ax.set_title(f"{title} ({corr_txt})")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25, linewidth=0.8)


def _plot_compare(
    merged: pd.DataFrame,
    *,
    label_a: str,
    label_b: str,
    x_axis: str | None,
    y_axis: str | None,
    annotate: bool,
    out_pdf_path: Path,
    out_png_path: Path,
    game_label: str | None,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.8), constrained_layout=True)
    x_label = x_axis or label_a
    y_label = y_axis or label_b
    elo_title = "Median ELO" if game_label is None else f"{game_label} ELO"
    rank_title = "Mean Rank (lower is better)" if game_label is None else f"{game_label} Rank (lower is better)"

    _scatter_with_diag(
        axes[0],
        merged["median_elo_a"],
        merged["median_elo_b"],
        title=elo_title,
        xlabel=x_label,
        ylabel=y_label,
        annotate=annotate,
        names=merged["human_name"],
    )
    _scatter_with_diag(
        axes[1],
        merged["mean_rank_a"],
        merged["mean_rank_b"],
        title=rank_title,
        xlabel=x_label,
        ylabel=y_label,
        annotate=annotate,
        names=merged["human_name"],
    )

    fig.suptitle(
        "PKL vs PKL Comparison" if game_label is None else f"PKL vs PKL Comparison: {game_label}",
        fontsize=12,
    )
    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf_path, bbox_inches="tight")
    out_png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png_path, bbox_inches="tight")
    plt.close(fig)


def _series_from_pkl(path: Path, *, mode: str, game_selector: str | None, metric: str) -> pd.Series:
    payload = _load_payload(path)
    results = _extract_results(payload, mode)
    selected_game = _resolve_game_column(payload, results, game_selector) if game_selector else None
    metrics = _metrics_from_results(results, selected_game=selected_game)
    if metric not in metrics.columns:
        raise KeyError(f"Metric '{metric}' not found in metrics columns: {list(metrics.columns)}")
    s = pd.to_numeric(metrics[metric], errors="coerce")
    s.index = s.index.map(str)
    return s


def _pairwise_corr_and_overlap(wide: pd.DataFrame, method: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    names = list(wide.columns)
    corr = pd.DataFrame(np.nan, index=names, columns=names, dtype=float)
    overlap = pd.DataFrame(0, index=names, columns=names, dtype=int)
    for a in names:
        s1 = pd.to_numeric(wide[a], errors="coerce")
        for b in names:
            s2 = pd.to_numeric(wide[b], errors="coerce")
            mask = s1.notna() & s2.notna()
            n = int(mask.sum())
            overlap.loc[a, b] = n
            if n < 2:
                continue
            c = s1[mask].corr(s2[mask], method=method)
            corr.loc[a, b] = float(c) if c is not None and np.isfinite(c) else np.nan
    for a in names:
        if overlap.loc[a, a] >= 1:
            corr.loc[a, a] = 1.0
    return corr, overlap


def _plot_corr_heatmap(
    corr: pd.DataFrame,
    *,
    metric: str,
    method: str,
    out_pdf_path: Path,
    out_png_path: Path,
) -> None:
    n = len(corr.index)
    side = max(6.0, 0.95 * n + 2.0)
    fig, ax = plt.subplots(figsize=(side, side), constrained_layout=True)
    vals = corr.to_numpy(dtype=float)
    masked = np.ma.masked_invalid(vals)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "white_blue",
        [
            (0.00, "#ffffff"),
            (1.00, "#2166ac"),
        ],
    )
    cmap.set_bad(color="#f2f2f2")
    im = ax.imshow(masked, vmin=0.75, vmax=1.0, cmap=cmap, aspect="equal")

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(corr.columns)
    ax.set_yticklabels(corr.index)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.tick_params(axis="x", top=True, labeltop=True, bottom=False, labelbottom=False, pad=4)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="left", rotation_mode="anchor")

    for i in range(n):
        for j in range(n):
            v = vals[i, j]
            txt = "NA" if not np.isfinite(v) else f"{v:.2f}"
            if not np.isfinite(v):
                color = "black"
            else:
                rgba = im.cmap(im.norm(v))
                r, g, b = float(rgba[0]), float(rgba[1]), float(rgba[2])
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                color = "black" if luminance >= 0.5 else "white"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8, color=color)

    title_metric = "Median ELO" if metric == "median_elo" else "Mean Rank"
    ax.set_title(f"Correlation Heatmap ({title_metric}, {method})")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf_path, bbox_inches="tight")
    out_png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png_path, bbox_inches="tight")
    plt.close(fig)


def _run_corr_heatmap(args: argparse.Namespace) -> None:
    if not args.pkls or len(args.pkls) < 2:
        raise ValueError("--pkls must provide at least 2 PKL paths for --mode corr-heatmap")
    pkl_paths = [_resolve_path(p) for p in args.pkls]
    for p in pkl_paths:
        if not p.exists():
            raise FileNotFoundError(f"PKL not found: {p}")

    if args.names is not None:
        if len(args.names) != len(pkl_paths):
            raise ValueError(f"--names length ({len(args.names)}) must match --pkls length ({len(pkl_paths)})")
        names = [str(n) for n in args.names]
    else:
        names = [p.stem for p in pkl_paths]

    series_by_name: dict[str, pd.Series] = {}
    for name, path in zip(names, pkl_paths):
        series_by_name[name] = _series_from_pkl(
            path,
            mode=args.corr_granularity,
            game_selector=args.game,
            metric=args.corr_metric,
        )

    wide = pd.concat(series_by_name, axis=1)
    corr, overlap = _pairwise_corr_and_overlap(wide, method=args.corr_method)

    out_dir = _resolve_path(args.out_dir) if args.out_dir else pkl_paths[0].parent
    out_dir.mkdir(parents=True, exist_ok=True)
    corr_csv_path = out_dir / args.corr_csv_name
    overlap_csv_path = out_dir / f"{Path(args.corr_csv_name).stem}_overlap.csv"
    corr_pdf_path = out_dir / args.corr_out_pdf
    corr_png_path = out_dir / args.corr_out_png

    corr.to_csv(corr_csv_path, index_label="name")
    overlap.to_csv(overlap_csv_path, index_label="name")
    _plot_corr_heatmap(
        corr,
        metric=args.corr_metric,
        method=args.corr_method,
        out_pdf_path=corr_pdf_path,
        out_png_path=corr_png_path,
    )
    print(f"saved_corr_plot={corr_pdf_path}")
    print(f"saved_corr_csv={corr_csv_path}")
    print(f"saved_overlap_csv={overlap_csv_path}")
    print(f"n_pkls={len(pkl_paths)}")


def main() -> None:
    args = _parse_args()
    if args.mode == "corr-heatmap":
        _run_corr_heatmap(args)
        return

    if args.pkl_a is None or args.pkl_b is None:
        raise ValueError("--pkl-a and --pkl-b are required unless --mode corr-heatmap is used.")
    pkl_a = _resolve_path(args.pkl_a)
    pkl_b = _resolve_path(args.pkl_b)
    if not pkl_a.exists():
        raise FileNotFoundError(f"PKL A not found: {pkl_a}")
    if not pkl_b.exists():
        raise FileNotFoundError(f"PKL B not found: {pkl_b}")

    payload_a = _load_payload(pkl_a)
    payload_b = _load_payload(pkl_b)
    results_a = _extract_results(payload_a, args.mode)
    results_b = _extract_results(payload_b, args.mode)
    selected_game_a = _resolve_game_column(payload_a, results_a, args.game) if args.game else None
    selected_game_b = _resolve_game_column(payload_b, results_b, args.game) if args.game else None
    print('metrics from pkl a', args.pkl_a)
    metrics_a = _metrics_from_results(results_a, selected_game=selected_game_a).rename(
        columns={"median_elo": "median_elo_a", "mean_rank": "mean_rank_a"}
    )
    print('metrics from pkl b', args.pkl_b)
    metrics_b = _metrics_from_results(results_b, selected_game=selected_game_b).rename(
        columns={"median_elo": "median_elo_b", "mean_rank": "mean_rank_b"}
    )
    if selected_game_a is not None:
        print(f"using_game_a={selected_game_a}")
    if selected_game_b is not None:
        print(f"using_game_b={selected_game_b}")
    plot_game_label = selected_game_a if selected_game_a == selected_game_b else selected_game_a or selected_game_b

    merged = metrics_a.join(metrics_b, how="outer")
    merged.index = merged.index.map(str)
    merged["human_name"] = merged.index.map(model_name_map)
    merged = merged[
        ["human_name", "median_elo_a", "median_elo_b", "mean_rank_a", "mean_rank_b"]
    ].sort_values(by=["human_name", "median_elo_a"], ascending=[True, False])

    out_dir = _resolve_path(args.out_dir) if args.out_dir else pkl_a.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / args.csv_name
    pdf_path = out_dir / args.out_pdf
    png_path = out_dir / args.out_png

    merged.to_csv(csv_path, index_label="model")
    _plot_compare(
        merged,
        label_a=args.label_a or pkl_a.stem,
        label_b=args.label_b or pkl_b.stem,
        x_axis=args.x_axis,
        y_axis=args.y_axis,
        annotate=args.annotate,
        out_pdf_path=pdf_path,
        out_png_path=png_path,
        game_label=plot_game_label,
    )

    overlap = int(
        (
            merged["median_elo_a"].notna()
            & merged["median_elo_b"].notna()
            & merged["mean_rank_a"].notna()
            & merged["mean_rank_b"].notna()
        ).sum()
    )
    print(f"saved_plot={pdf_path}")
    print(f"saved_csv={csv_path}")
    print(f"models_total={len(merged)}, models_with_all_metrics={overlap}")


if __name__ == "__main__":
    main()
