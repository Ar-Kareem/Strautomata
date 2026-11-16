#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import pickle
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from experimental.lm_arena.rating_systems import compute_bt
from game_arena import utils as arena_utils


ROOT_DIR = arena_utils.get_root_path()
EPS = 1e-12
OUTCOME_LABELS = ("a", "b", "draw")
PRED_BT_SYNTHETIC_MATCHES_PER_PAIR = 100
ARENA_PURPLE = "#6c4ca8"
ARENA_PURPLE_SOFT = "#9f89cf"
ARENA_TEXT = "#2f2149"
ARENA_GRID = "#ddd6ef"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare guessing-model predictions against empirical arena results.")
    parser.add_argument("--pred-dir", required=True, help="Directory containing guessing prediction JSON files.")
    parser.add_argument("--in-pkl", required=True, help="Arena results pickle to compare against.")
    parser.add_argument("--out-dir", required=True, help="Directory to write comparison outputs.")
    return parser.parse_args()


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _load_payload(in_pkl: Path) -> dict[str, Any]:
    with in_pkl.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pickle payload type: expected dict, got {type(payload).__name__}")
    return payload


def _build_battles_via_simple_example(all_matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    log_dir = Path("/tmp/codex_game_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    arena_utils.get_logs_dir = lambda: log_dir
    simple_example = importlib.import_module("experimental.lm_arena.simple_example")
    return simple_example._build_battles(all_matches, "full", 0.0)  # type: ignore[attr-defined]


def _load_predictions(pred_dir: Path) -> list[dict[str, Any]]:
    all_predictions = pred_dir / "all_predictions.json"
    if all_predictions.exists():
        rows = json.loads(all_predictions.read_text(encoding="utf-8"))
    else:
        rows = []
        for path in sorted(pred_dir.glob("*.json")):
            if path.name == "run_info.json":
                continue
            rows.append(json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(rows, list):
        raise ValueError(f"Expected a JSON list in {all_predictions}, got {type(rows).__name__}")
    return rows


def _game_world_key(game: str, world: str) -> str:
    return f"{game}/{world}"

def _infer_game_worlds(rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    ordered: list[tuple[str, str]] = []
    for row in rows:
        game = row.get("game")
        world = row.get("world")
        if not isinstance(game, str) or not isinstance(world, str):
            raise ValueError(f"Prediction row {row.get('id')} is missing string game/world metadata")
        pair = (game, world)
        if pair not in seen:
            seen.add(pair)
            ordered.append(pair)
    if not ordered:
        raise ValueError("Could not infer game/worlds from prediction rows")
    return ordered


def _build_run_label_map(payload: dict[str, Any]) -> dict[tuple[str, str], str]:
    mapping: dict[tuple[str, str], str] = {}
    for item in payload.get("runs", []):
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue
        key = (str(item[0]), str(item[1]))
        label = str(item[2])
        if key in mapping and mapping[key] != label:
            raise ValueError(f"Duplicate pickle run mapping for {_game_world_key(*key)}: {mapping[key]!r} vs {label!r}")
        mapping[key] = label
    if not mapping:
        raise ValueError("Could not infer any run mappings from pickle payload")
    return mapping


def _model_name(bot_name: str) -> str:
    return bot_name.split("/", 1)[0]


def _extract_probs(row: dict[str, Any]) -> tuple[float, float, float]:
    parsed = row.get("parsed")
    if not isinstance(parsed, dict):
        raise ValueError(f"Prediction row {row.get('id')} missing parsed probabilities")
    return float(parsed["p_a"]), float(parsed["p_b"]), float(parsed["p_draw"])


def _expected_score(p_a: float, p_b: float, p_draw: float) -> float:
    return p_a + 0.5 * p_draw


def _top_outcome_label(p_a: float, p_b: float, p_draw: float, tol: float = 1e-12) -> str:
    values = {"a": p_a, "b": p_b, "draw": p_draw}
    max_value = max(values.values())
    winners = [label for label, value in values.items() if abs(value - max_value) <= tol]
    return winners[0] if len(winners) == 1 else "tie"


def _pair_direction_label(score_a: float, tol: float = 1e-12) -> str:
    if score_a > 0.5 + tol:
        return "a"
    if score_a < 0.5 - tol:
        return "b"
    return "tie"


def _empirical_counts_for_pair(battles: pd.DataFrame, bot_a: str, bot_b: str) -> dict[str, int]:
    direct = battles[(battles["model_a"] == bot_a) & (battles["model_b"] == bot_b)]
    reverse = battles[(battles["model_a"] == bot_b) & (battles["model_b"] == bot_a)]
    a_wins = int((direct["winner"] == "model_a").sum() + (reverse["winner"] == "model_b").sum())
    b_wins = int((direct["winner"] == "model_b").sum() + (reverse["winner"] == "model_a").sum())
    draws = int((direct["winner"] == "tie").sum() + (reverse["winner"] == "tie").sum())
    return {"a_wins": a_wins, "b_wins": b_wins, "draws": draws, "n_games": a_wins + b_wins + draws}


def _multiclass_brier(pred: np.ndarray, emp: np.ndarray) -> float:
    return float(np.square(pred - emp).sum())


def _cross_entropy(pred: np.ndarray, emp: np.ndarray) -> float:
    return float(-(emp * np.log(np.clip(pred, EPS, 1.0))).sum())


def _js_divergence(pred: np.ndarray, emp: np.ndarray) -> float:
    mid = 0.5 * (pred + emp)
    kl_emp = float((emp * (np.log(np.clip(emp, EPS, 1.0)) - np.log(np.clip(mid, EPS, 1.0)))).sum())
    kl_pred = float((pred * (np.log(np.clip(pred, EPS, 1.0)) - np.log(np.clip(mid, EPS, 1.0)))).sum())
    return 0.5 * (kl_emp + kl_pred)


def _build_pairwise_table(rows: list[dict[str, Any]], battles: pd.DataFrame, empirical_bots: set[str]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in rows:
        record = {
            "id": row.get("id"),
            "status": row.get("status"),
            "game": row.get("game"),
            "world": row.get("world"),
            "bot_a": row.get("bot_a"),
            "bot_b": row.get("bot_b"),
        }
        if row.get("status") != "ok":
            record["compare_status"] = "prediction_not_ok"
            records.append(record)
            continue

        bot_a = str(row["bot_a"])
        bot_b = str(row["bot_b"])
        record["model_a_name"] = _model_name(bot_a)
        record["model_b_name"] = _model_name(bot_b)
        pred_p_a, pred_p_b, pred_p_draw = _extract_probs(row)
        record.update(
            {
                "pred_p_a": pred_p_a,
                "pred_p_b": pred_p_b,
                "pred_p_draw": pred_p_draw,
                "pred_score_a": _expected_score(pred_p_a, pred_p_b, pred_p_draw),
                "pred_top_outcome": _top_outcome_label(pred_p_a, pred_p_b, pred_p_draw),
            }
        )

        if bot_a not in empirical_bots or bot_b not in empirical_bots:
            record["compare_status"] = "missing_bot_in_empirical"
            record["bot_a_in_empirical"] = bot_a in empirical_bots
            record["bot_b_in_empirical"] = bot_b in empirical_bots
            records.append(record)
            continue

        counts = _empirical_counts_for_pair(battles, bot_a, bot_b)
        record.update(counts)
        if counts["n_games"] == 0:
            record["compare_status"] = "missing_pair_games"
            records.append(record)
            continue

        emp_p_a = counts["a_wins"] / counts["n_games"]
        emp_p_b = counts["b_wins"] / counts["n_games"]
        emp_p_draw = counts["draws"] / counts["n_games"]
        emp_score_a = _expected_score(emp_p_a, emp_p_b, emp_p_draw)
        pred = np.array([pred_p_a, pred_p_b, pred_p_draw], dtype=np.float64)
        emp = np.array([emp_p_a, emp_p_b, emp_p_draw], dtype=np.float64)
        record.update(
            {
                "compare_status": "ok",
                "emp_p_a": emp_p_a,
                "emp_p_b": emp_p_b,
                "emp_p_draw": emp_p_draw,
                "emp_score_a": emp_score_a,
                "emp_top_outcome": _top_outcome_label(emp_p_a, emp_p_b, emp_p_draw),
                "pred_vs_emp_score_error": record["pred_score_a"] - emp_score_a,
                "pred_vs_emp_draw_error": pred_p_draw - emp_p_draw,
                "multiclass_brier": _multiclass_brier(pred, emp),
                "cross_entropy": _cross_entropy(pred, emp),
                "js_divergence": _js_divergence(pred, emp),
            }
        )
        record["top_outcome_correct"] = record["pred_top_outcome"] == record["emp_top_outcome"]
        record["pred_side"] = _pair_direction_label(record["pred_score_a"])
        record["emp_side"] = _pair_direction_label(emp_score_a)
        record["side_correct_tie_aware"] = record["pred_side"] == record["emp_side"]
        record["side_correct_no_emp_ties"] = (
            record["emp_side"] != "tie" and record["pred_side"] == record["emp_side"]
        )
        records.append(record)
    return pd.DataFrame.from_records(records)


def _compute_usage_summary(rows: list[dict[str, Any]]) -> dict[str, float | int | None]:
    usage_rows = [row.get("usage") for row in rows if isinstance(row.get("usage"), dict)]
    if not usage_rows:
        return {
            "rows_with_usage": 0,
            "total_prompt_tokens": None,
            "total_completion_tokens": None,
            "total_tokens": None,
            "total_cost": None,
        }
    def _sum_key(key: str) -> float:
        return float(sum(float(row.get(key, 0) or 0) for row in usage_rows))
    return {
        "rows_with_usage": len(usage_rows),
        "total_prompt_tokens": int(_sum_key("prompt_tokens")),
        "total_completion_tokens": int(_sum_key("completion_tokens")),
        "total_tokens": int(_sum_key("total_tokens")),
        "total_cost": _sum_key("cost"),
    }


def _compute_calibration_table(df: pd.DataFrame, pred_col: str, emp_col: str, n_bins: int = 5) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["bin", "n", "pred_mean", "emp_mean"])
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    out = df[[pred_col, emp_col]].copy()
    out["bin"] = pd.cut(out[pred_col], bins=bins, include_lowest=True, duplicates="drop")
    grouped = (
        out.groupby("bin", observed=False)
        .agg(n=(pred_col, "size"), pred_mean=(pred_col, "mean"), emp_mean=(emp_col, "mean"))
        .reset_index()
    )
    grouped["bin"] = grouped["bin"].astype(str)
    return grouped


def _compute_top_outcome_confusion(df: pd.DataFrame) -> pd.DataFrame:
    labels = ["a", "b", "draw", "tie"]
    confusion = pd.DataFrame(0, index=labels, columns=labels, dtype=int)
    for _, row in df.iterrows():
        confusion.loc[str(row["emp_top_outcome"]), str(row["pred_top_outcome"])] += 1
    return confusion


def _make_synthetic_match(name0: str, name1: str, winner: int | None) -> dict[str, Any]:
    return {
        "name0": name0,
        "name1": name1,
        "done": True,
        "winner": winner,
        "r": None,
    }


def _probs_to_counts(p_a: float, p_b: float, p_draw: float, total: int) -> tuple[int, int, int]:
    raw = np.array([p_a, p_b, p_draw], dtype=float) * float(total)
    base = np.floor(raw).astype(int)
    remainder = total - int(base.sum())
    if remainder > 0:
        order = np.argsort(-(raw - base))
        for idx in order[:remainder]:
            base[idx] += 1
    return int(base[0]), int(base[1]), int(base[2])


def _pair_rows_to_bt_series(pair_df: pd.DataFrame) -> pd.Series:
    ok_df = pair_df[pair_df["status"] == "ok"]
    if ok_df.empty:
        return pd.Series(dtype=float)
    all_matches: list[dict[str, Any]] = []
    for _, row in ok_df.iterrows():
        bot_a = str(row["bot_a"])
        bot_b = str(row["bot_b"])
        count_a, count_b, count_draw = _probs_to_counts(
            float(row["pred_p_a"]),
            float(row["pred_p_b"]),
            float(row["pred_p_draw"]),
            total=PRED_BT_SYNTHETIC_MATCHES_PER_PAIR,
        )
        all_matches.extend(_make_synthetic_match(bot_a, bot_b, 0) for _ in range(count_a))
        all_matches.extend(_make_synthetic_match(bot_a, bot_b, 1) for _ in range(count_b))
        all_matches.extend(_make_synthetic_match(bot_a, bot_b, None) for _ in range(count_draw))
    battles = _build_battles_via_simple_example(all_matches)
    return compute_bt(battles)


def _pairwise_order_accuracy(series_a: pd.Series, series_b: pd.Series, tol: float = 1e-9) -> float | None:
    shared = [bot for bot in series_a.index if bot in series_b.index]
    if len(shared) < 2:
        return None
    correct = 0
    total = 0
    for bot_x, bot_y in combinations(shared, 2):
        dx = float(series_a[bot_x] - series_a[bot_y])
        dy = float(series_b[bot_x] - series_b[bot_y])
        sx = 0 if abs(dx) <= tol else (1 if dx > 0 else -1)
        sy = 0 if abs(dy) <= tol else (1 if dy > 0 else -1)
        total += 1
        if sx == sy:
            correct += 1
    return correct / total if total else None


def _summarize_rating_alignment(
    rating_df: pd.DataFrame,
    *,
    count_key: str,
    include_synthetic_match_count: bool,
) -> dict[str, float | int | None]:
    if rating_df.empty:
        summary: dict[str, float | int | None] = {count_key: 0}
        if include_synthetic_match_count:
            summary["pred_bt_synthetic_matches_per_pair"] = int(PRED_BT_SYNTHETIC_MATCHES_PER_PAIR)
        for col in ("emp_bt_subset", "emp_rating_full"):
            summary[f"pairwise_order_accuracy_vs_{col}"] = None
            summary[f"pearson_vs_{col}"] = None
            summary[f"spearman_vs_{col}"] = None
            summary[f"kendall_vs_{col}"] = None
        return summary

    summary = {
        count_key: int(len(rating_df)),
        "pairwise_order_accuracy_vs_emp_bt_subset": _pairwise_order_accuracy(rating_df["pred_bt"], rating_df["emp_bt_subset"]),
        "pairwise_order_accuracy_vs_emp_rating_full": _pairwise_order_accuracy(rating_df["pred_bt"], rating_df["emp_rating_full"]),
    }
    if include_synthetic_match_count:
        summary["pred_bt_synthetic_matches_per_pair"] = int(PRED_BT_SYNTHETIC_MATCHES_PER_PAIR)
    for col in ("emp_bt_subset", "emp_rating_full"):
        valid = rating_df[["pred_bt", col]].dropna()
        summary[f"pearson_vs_{col}"] = float(valid["pred_bt"].corr(valid[col], method="pearson")) if len(valid) >= 2 else None
        summary[f"spearman_vs_{col}"] = float(valid["pred_bt"].corr(valid[col], method="spearman")) if len(valid) >= 2 else None
        summary[f"kendall_vs_{col}"] = float(valid["pred_bt"].corr(valid[col], method="kendall")) if len(valid) >= 2 else None
    return summary


def _compute_rating_compare(
    pair_df: pd.DataFrame,
    battles: pd.DataFrame,
    full_leaderboard: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float | int | None]]:
    pred_bt = _pair_rows_to_bt_series(pair_df)
    if pred_bt.empty:
        empty = pd.DataFrame(columns=["pred_bt", "emp_bt_subset", "emp_rating_full", "pred_rank", "emp_bt_subset_rank", "emp_rating_full_rank"])
        return empty, _summarize_rating_alignment(empty, count_key="n_overlap_bots", include_synthetic_match_count=True)

    overlap_bots = pred_bt.index.tolist()
    subset_battles = battles[battles["model_a"].isin(overlap_bots) & battles["model_b"].isin(overlap_bots)].copy()
    emp_bt_subset = compute_bt(subset_battles[["model_a", "model_b", "winner"]]) if not subset_battles.empty else pd.Series(dtype=float)
    emp_full = full_leaderboard["rating"].copy()

    rating_df = pd.DataFrame(index=pred_bt.index)
    rating_df["pred_bt"] = pred_bt
    rating_df["emp_bt_subset"] = emp_bt_subset.reindex(rating_df.index)
    rating_df["emp_rating_full"] = emp_full.reindex(rating_df.index)
    rating_df["pred_rank"] = rating_df["pred_bt"].rank(ascending=False, method="min")
    rating_df["emp_bt_subset_rank"] = rating_df["emp_bt_subset"].rank(ascending=False, method="min")
    rating_df["emp_rating_full_rank"] = rating_df["emp_rating_full"].rank(ascending=False, method="min")
    summary = _summarize_rating_alignment(rating_df, count_key="n_overlap_bots", include_synthetic_match_count=True)
    return rating_df.sort_values("pred_bt", ascending=False), summary


def _aggregate_model_rating_compare(per_game_rating_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float | int | None]]:
    if per_game_rating_df.empty:
        empty = pd.DataFrame(
            columns=[
                "n_game_worlds",
                "pred_bt",
                "pred_bt_median",
                "emp_bt_subset",
                "emp_rating_full",
                "emp_rating_full_median",
                "pred_rank",
                "pred_bt_median_rank",
                "emp_bt_subset_rank",
                "emp_rating_full_rank",
                "emp_rating_full_median_rank",
                "game_worlds",
                "bot_variants",
            ]
        )
        summary = _summarize_rating_alignment(empty, count_key="n_models", include_synthetic_match_count=False)
        summary["pairwise_order_accuracy_vs_emp_rating_full_median"] = None
        summary["pearson_vs_emp_rating_full_median"] = None
        summary["spearman_vs_emp_rating_full_median"] = None
        summary["kendall_vs_emp_rating_full_median"] = None
        return empty, summary

    grouped = per_game_rating_df.groupby("model_id", sort=True)
    model_df = grouped.agg(
        n_game_worlds=("game_world", "nunique"),
        pred_bt=("pred_bt", "mean"),
        pred_bt_median=("pred_bt", "median"),
        emp_bt_subset=("emp_bt_subset", "mean"),
        emp_rating_full=("emp_rating_full", "mean"),
        emp_rating_full_median=("emp_rating_full", "median"),
        pred_rank=("pred_rank", "mean"),
        emp_bt_subset_rank=("emp_bt_subset_rank", "mean"),
        emp_rating_full_rank=("emp_rating_full_rank", "mean"),
    )
    model_df["pred_bt_median_rank"] = model_df["pred_bt_median"].rank(ascending=False, method="min")
    model_df["emp_rating_full_median_rank"] = model_df["emp_rating_full_median"].rank(ascending=False, method="min")
    model_df["game_worlds"] = grouped["game_world"].agg(lambda s: "|".join(sorted(set(str(x) for x in s))))
    model_df["bot_variants"] = grouped["bot"].agg(lambda s: "|".join(sorted(set(str(x) for x in s))))
    summary = _summarize_rating_alignment(model_df, count_key="n_models", include_synthetic_match_count=False)
    summary["pairwise_order_accuracy_vs_emp_rating_full_median"] = _pairwise_order_accuracy(
        model_df["pred_bt_median"],
        model_df["emp_rating_full_median"],
    )
    valid = model_df[["pred_bt_median", "emp_rating_full_median"]].dropna()
    summary["pearson_vs_emp_rating_full_median"] = (
        float(valid["pred_bt_median"].corr(valid["emp_rating_full_median"], method="pearson")) if len(valid) >= 2 else None
    )
    summary["spearman_vs_emp_rating_full_median"] = (
        float(valid["pred_bt_median"].corr(valid["emp_rating_full_median"], method="spearman")) if len(valid) >= 2 else None
    )
    summary["kendall_vs_emp_rating_full_median"] = (
        float(valid["pred_bt_median"].corr(valid["emp_rating_full_median"], method="kendall")) if len(valid) >= 2 else None
    )
    return model_df.sort_values("pred_bt", ascending=False), summary


def _coverage_summary(
    rows: list[dict[str, Any]],
    pair_df: pd.DataFrame,
    empirical_bot_keys: set[tuple[str, str, str]],
) -> dict[str, Any]:
    predicted_bot_keys = sorted(
        {
            (str(row["game"]), str(row["world"]), str(row["bot_a"]))
            for row in rows
        }
        | {
            (str(row["game"]), str(row["world"]), str(row["bot_b"]))
            for row in rows
        }
    )
    overlapping_bot_keys = sorted(bot_key for bot_key in predicted_bot_keys if bot_key in empirical_bot_keys)
    missing_bot_keys = sorted(bot_key for bot_key in predicted_bot_keys if bot_key not in empirical_bot_keys)
    ok_predictions = int((pair_df["status"] == "ok").sum()) if not pair_df.empty else 0
    compare_status_counts = pair_df["compare_status"].value_counts(dropna=False).to_dict() if not pair_df.empty else {}
    missing_bots = [_game_world_key(game, world) + f":{bot}" for game, world, bot in missing_bot_keys]
    return {
        "predicted_pairs_total": len(rows),
        "predicted_pairs_status_ok": ok_predictions,
        "predicted_unique_bots_total": len(predicted_bot_keys),
        "predicted_unique_bots_in_empirical": len(overlapping_bot_keys),
        "predicted_unique_bots_missing_from_empirical": len(missing_bot_keys),
        "predicted_unique_bot_entries_total": len(predicted_bot_keys),
        "predicted_unique_bot_entries_in_empirical": len(overlapping_bot_keys),
        "predicted_unique_bot_entries_missing_from_empirical": len(missing_bot_keys),
        "missing_bots": missing_bots,
        "missing_bot_entries": missing_bots,
        "compare_status_counts": compare_status_counts,
    }


def _pair_metrics_summary(ok_pair_df: pd.DataFrame) -> dict[str, float | int | None]:
    if ok_pair_df.empty:
        return {
            "n_pairs": 0,
            "mean_multiclass_brier": None,
            "mean_cross_entropy": None,
            "mean_js_divergence": None,
            "mae_score_a": None,
            "rmse_score_a": None,
            "mae_draw": None,
            "rmse_draw": None,
            "top_outcome_accuracy": None,
            "side_accuracy_tie_aware": None,
            "side_accuracy_excluding_empirical_ties": None,
            "pearson_pred_vs_emp_score": None,
            "spearman_pred_vs_emp_score": None,
        }
    score_err = ok_pair_df["pred_vs_emp_score_error"].astype(float)
    draw_err = ok_pair_df["pred_vs_emp_draw_error"].astype(float)
    no_emp_ties = ok_pair_df[ok_pair_df["emp_side"] != "tie"]
    return {
        "n_pairs": int(len(ok_pair_df)),
        "mean_multiclass_brier": float(ok_pair_df["multiclass_brier"].mean()),
        "mean_cross_entropy": float(ok_pair_df["cross_entropy"].mean()),
        "mean_js_divergence": float(ok_pair_df["js_divergence"].mean()),
        "mae_score_a": float(score_err.abs().mean()),
        "rmse_score_a": float(np.sqrt(np.square(score_err).mean())),
        "mae_draw": float(draw_err.abs().mean()),
        "rmse_draw": float(np.sqrt(np.square(draw_err).mean())),
        "top_outcome_accuracy": float(ok_pair_df["top_outcome_correct"].mean()),
        "side_accuracy_tie_aware": float(ok_pair_df["side_correct_tie_aware"].mean()),
        "side_accuracy_excluding_empirical_ties": (
            float((no_emp_ties["pred_side"] == no_emp_ties["emp_side"]).mean()) if len(no_emp_ties) > 0 else None
        ),
        "pearson_pred_vs_emp_score": float(ok_pair_df["pred_score_a"].corr(ok_pair_df["emp_score_a"], method="pearson")),
        "spearman_pred_vs_emp_score": float(ok_pair_df["pred_score_a"].corr(ok_pair_df["emp_score_a"], method="spearman")),
    }


def _load_empirical_run(
    payload: dict[str, Any],
    run_label_map: dict[tuple[str, str], str],
    game: str,
    world: str,
) -> tuple[str, pd.DataFrame, pd.DataFrame, set[str]]:
    run_key = (game, world)
    if run_key not in run_label_map:
        raise ValueError(f"Could not find empirical run for {_game_world_key(game, world)!r} in pickle runs")
    run_label = run_label_map[run_key]
    run_result = payload["results_bots"][run_label]
    full_leaderboard = run_result["leaderboard_table_df"].copy()
    full_leaderboard.index = full_leaderboard.index.astype(str)
    battles = run_result["battles"].copy()
    battles["model_a"] = battles["model_a"].astype(str)
    battles["model_b"] = battles["model_b"].astype(str)
    battles["winner"] = battles["winner"].astype(str)
    empirical_bots = set(full_leaderboard.index.astype(str))
    return run_label, full_leaderboard, battles, empirical_bots


def _save_figure(fig: plt.Figure, out_dir: Path, stem: str) -> None:
    fig.savefig(out_dir / f"{stem}.png", dpi=180, bbox_inches="tight")
    fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def _style_axes(ax: plt.Axes) -> None:
    ax.grid(True, axis="y", alpha=0.25, linewidth=0.8, color=ARENA_GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(ARENA_TEXT)
    ax.spines["bottom"].set_color(ARENA_TEXT)
    ax.tick_params(colors=ARENA_TEXT)
    ax.xaxis.label.set_color(ARENA_TEXT)
    ax.yaxis.label.set_color(ARENA_TEXT)
    ax.title.set_color(ARENA_TEXT)
    ax.set_axisbelow(True)


def _add_best_fit_line(ax: plt.Axes, x: pd.Series, y: pd.Series, lo: float, hi: float) -> None:
    x_vals = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float)
    y_vals = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(x_vals) & np.isfinite(y_vals)
    if mask.sum() < 2:
        return
    slope, intercept = np.polyfit(x_vals[mask], y_vals[mask], deg=1)
    r_value = float(np.corrcoef(x_vals[mask], y_vals[mask])[0, 1])
    x_line = np.array([lo, hi], dtype=float)
    y_line = slope * x_line + intercept
    ax.plot(
        x_line,
        y_line,
        linestyle="--",
        color=ARENA_PURPLE_SOFT,
        linewidth=1.4,
        alpha=0.95,
        label=f"Best Fit (r={r_value:.3f})",
    )
    ax.legend(frameon=False, loc="best")



def _plot_rank_scatter(
    rating_df: pd.DataFrame,
    out_dir: Path,
    *,
    x_rank_col: str,
    y_rank_col: str,
    stem: str,
    title: str,
    x_label: str,
    y_label: str,
) -> None:
    plot_df = rating_df[[x_rank_col, y_rank_col]].dropna().copy()
    if plot_df.empty:
        return
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    ax.scatter(
        plot_df[x_rank_col],
        plot_df[y_rank_col],
        s=58,
        c=ARENA_PURPLE,
        edgecolors=ARENA_TEXT,
        linewidths=0.45,
        alpha=0.86,
    )
    max_rank = float(max(plot_df[x_rank_col].max(), plot_df[y_rank_col].max()))
    ax.plot(
        [0.5, max_rank + 0.5],
        [0.5, max_rank + 0.5],
        linestyle="--",
        color="black",
        linewidth=1.0,
        alpha=0.7,
        label="Identity",
    )
    _add_best_fit_line(ax, plot_df[x_rank_col], plot_df[y_rank_col], 0.5, max_rank + 0.5)
    for bot_name, row in plot_df.iterrows():
        ax.annotate(
            bot_name,
            (row[x_rank_col], row[y_rank_col]),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=8,
            color=ARENA_TEXT,
        )
    ax.set_xlim(max_rank + 0.5, 0.5)
    ax.set_ylim(max_rank + 0.5, 0.5)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    _style_axes(ax)
    _save_figure(fig, out_dir, stem)


def _plot_rank_slopegraph(
    rating_df: pd.DataFrame,
    out_dir: Path,
    *,
    left_rank_col: str,
    right_rank_col: str,
    stem: str,
    title: str,
    left_label: str,
    right_label: str,
) -> None:
    plot_df = rating_df[[left_rank_col, right_rank_col]].dropna().copy()
    if plot_df.empty:
        return
    fig, ax = plt.subplots(figsize=(8.0, 0.55 * len(plot_df) + 2.0))
    x_left = 0.0
    x_right = 1.0
    max_rank = float(max(plot_df[left_rank_col].max(), plot_df[right_rank_col].max()))
    for bot_name, row in plot_df.iterrows():
        color = "#54a24b" if row[right_rank_col] < row[left_rank_col] else "#e45756" if row[right_rank_col] > row[left_rank_col] else "#4c78a8"
        ax.plot([x_left, x_right], [row[left_rank_col], row[right_rank_col]], color=color, linewidth=1.8, alpha=0.9)
        ax.scatter([x_left, x_right], [row[left_rank_col], row[right_rank_col]], s=36, color=color, edgecolors="black", linewidths=0.4, zorder=3)
        ax.text(x_left - 0.04, row[left_rank_col], bot_name, ha="right", va="center", fontsize=8)
        ax.text(x_right + 0.04, row[right_rank_col], bot_name, ha="left", va="center", fontsize=8)
    ax.set_xlim(-0.35, 1.35)
    ax.set_ylim(max_rank + 0.5, 0.5)
    ax.set_xticks([x_left, x_right])
    ax.set_xticklabels([left_label, right_label])
    ax.set_ylabel("Rank (1 is best)")
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.2, linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    _save_figure(fig, out_dir, stem)


def _plot_rank_delta_bar(
    rating_df: pd.DataFrame,
    out_dir: Path,
    *,
    empirical_rank_col: str,
    predicted_rank_col: str,
    stem: str,
    title: str,
) -> None:
    plot_df = rating_df[[empirical_rank_col, predicted_rank_col]].dropna().copy()
    if plot_df.empty:
        return
    plot_df["rank_delta"] = plot_df[predicted_rank_col] - plot_df[empirical_rank_col]
    plot_df = plot_df.sort_values(empirical_rank_col, ascending=True)
    fig, ax = plt.subplots(figsize=(8.0, 0.5 * len(plot_df) + 2.2))
    colors = ["#e45756" if x > 0 else "#54a24b" if x < 0 else "#4c78a8" for x in plot_df["rank_delta"]]
    ax.barh(plot_df.index.tolist(), plot_df["rank_delta"], color=colors, edgecolor="black", linewidth=0.4)
    ax.axvline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("Predicted Rank - Empirical Rank")
    ax.set_ylabel("Bot")
    _style_axes(ax)
    _save_figure(fig, out_dir, stem)


def _plot_value_scatter(
    rating_df: pd.DataFrame,
    out_dir: Path,
    *,
    x_col: str,
    y_col: str,
    stem: str,
    title: str,
    x_label: str,
    y_label: str,
) -> None:
    plot_df = rating_df[[x_col, y_col]].dropna().copy()
    if plot_df.empty:
        return
    fig, ax = plt.subplots(figsize=(7.0, 5.4))
    ax.scatter(plot_df[x_col], plot_df[y_col], s=64, c="#4c78a8", edgecolors="black", linewidths=0.5, alpha=0.9)
    x_min = float(plot_df[x_col].min())
    x_max = float(plot_df[x_col].max())
    y_min = float(plot_df[y_col].min())
    y_max = float(plot_df[y_col].max())
    x_pad = max((x_max - x_min) * 0.06, 1.0)
    y_pad = max((y_max - y_min) * 0.06, 1.0)
    _add_best_fit_line(ax, plot_df[x_col], plot_df[y_col], x_min - x_pad, x_max + x_pad)
    for label, row in plot_df.iterrows():
        ax.annotate(label, (row[x_col], row[y_col]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    _style_axes(ax)
    _save_figure(fig, out_dir, stem)


def _series_equal_on_shared_index(series_a: pd.Series, series_b: pd.Series) -> bool:
    a = pd.to_numeric(series_a, errors="coerce")
    b = pd.to_numeric(series_b, errors="coerce")
    valid = a.notna() & b.notna()
    if not bool(valid.any()):
        return False
    return a[valid].equals(b[valid])


def _make_plots(
    out_dir: Path,
    rating_df: pd.DataFrame,
    context_label: str,
) -> None:
    game_suffix = f" ({context_label})" if context_label else ""
    _plot_rank_scatter(
        rating_df,
        out_dir,
        x_rank_col="emp_rating_full_rank",
        y_rank_col="pred_rank",
        stem="rank_scatter_full_predicted_vs_empirical",
        title="Empirical Rank vs Predicted Rank",
        x_label="Empirical Rank",
        y_label="Predicted Rank",
    )
    _plot_rank_slopegraph(
        rating_df,
        out_dir,
        left_rank_col="emp_rating_full_rank",
        right_rank_col="pred_rank",
        stem="rank_slope_full_predicted_vs_empirical",
        title=f"Rank Changes: Empirical Full Pool to Predicted BT{game_suffix}",
        left_label="Empirical Full",
        right_label="Predicted",
    )
    _plot_rank_delta_bar(
        rating_df,
        out_dir,
        empirical_rank_col="emp_rating_full_rank",
        predicted_rank_col="pred_rank",
        stem="rank_delta_full_predicted_minus_empirical",
        title=f"Rank Delta: Predicted Minus Empirical Full-Pool Rank{game_suffix}",
    )
    if not _series_equal_on_shared_index(rating_df["emp_bt_subset_rank"], rating_df["emp_rating_full_rank"]):
        _plot_rank_scatter(
            rating_df,
            out_dir,
            x_rank_col="emp_bt_subset_rank",
            y_rank_col="pred_rank",
            stem="rank_scatter_bt_subset_predicted_vs_empirical",
            title="Empirical Rank vs Predicted Rank",
            x_label="Empirical Rank",
            y_label="Predicted Rank",
        )
        _plot_rank_slopegraph(
            rating_df,
            out_dir,
            left_rank_col="emp_bt_subset_rank",
            right_rank_col="pred_rank",
            stem="rank_slope_bt_subset_predicted_vs_empirical",
            title=f"Rank Changes: Empirical BT Subset to Predicted BT{game_suffix}",
            left_label="Empirical Subset",
            right_label="Predicted",
        )
    if "emp_rating_full_median_rank" in rating_df.columns:
        _plot_rank_scatter(
            rating_df,
            out_dir,
            x_rank_col="emp_rating_full_median_rank",
            y_rank_col="pred_bt_median_rank",
            stem="rank_scatter_median_elo_predicted_vs_empirical",
            title=f"Ranks: Empirical Median Elo vs Predicted Median BT{game_suffix}",
            x_label="Empirical Rank by Median Elo Across Games",
            y_label="Predicted Rank by Median BT Across Games",
        )
    if "emp_rating_full_median" in rating_df.columns and "pred_bt_median" in rating_df.columns:
        _plot_value_scatter(
            rating_df,
            out_dir,
            x_col="emp_rating_full_median",
            y_col="pred_bt_median",
            stem="scatter_median_elo_predicted_vs_empirical",
            title=f"Median Empirical Elo vs Median Predicted BT{game_suffix}",
            x_label="Empirical Median Elo Across Games",
            y_label="Predicted Median BT Across Games",
        )


def _write_summary_md(
    out_path: Path,
    pred_dir: Path,
    in_pkl: Path,
    dataset_label: str,
    coverage: dict[str, Any],
    usage: dict[str, Any],
    pair_metrics: dict[str, Any],
    rating_metrics: dict[str, Any],
) -> None:
    lines = [
        f"# Guessing Comparison Report",
        "",
        f"- Predictions: `{pred_dir}`",
        f"- Empirical pickle: `{in_pkl}`",
        f"- Dataset: `{dataset_label}`",
        "",
        "## Coverage",
        "",
        f"- Predicted pairs: {coverage['predicted_pairs_total']}",
        f"- Prediction rows with `status=ok`: {coverage['predicted_pairs_status_ok']}",
        f"- Predicted unique bot entries: {coverage['predicted_unique_bot_entries_total']}",
        f"- Bot entries present in empirical results: {coverage['predicted_unique_bot_entries_in_empirical']}",
        f"- Bot entries missing from empirical results: {coverage['predicted_unique_bot_entries_missing_from_empirical']}",
        f"- Compare status counts: `{coverage['compare_status_counts']}`",
        "",
        "## Pairwise Metrics",
        "",
    ]
    for key, value in pair_metrics.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Rating Metrics", ""])
    for key, value in rating_metrics.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Usage", ""])
    for key, value in usage.items():
        lines.append(f"- {key}: {value}")
    if coverage["missing_bots"]:
        lines.extend(["", "## Missing Bots", ""])
        for bot in coverage["missing_bots"]:
            lines.append(f"- {bot}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    pred_dir = _resolve_path(args.pred_dir)
    in_pkl = _resolve_path(args.in_pkl)
    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_predictions(pred_dir)
    if not rows:
        raise ValueError(f"No prediction rows found in {pred_dir}")
    payload = _load_payload(in_pkl)
    game_worlds = _infer_game_worlds(rows)
    run_label_map = _build_run_label_map(payload)
    multi_game = len(game_worlds) > 1

    rows_by_game_world: dict[tuple[str, str], list[dict[str, Any]]] = {(game, world): [] for game, world in game_worlds}
    for row in rows:
        rows_by_game_world[(str(row["game"]), str(row["world"]))].append(row)

    pair_frames: list[pd.DataFrame] = []
    ok_pair_frames: list[pd.DataFrame] = []
    per_game_rating_tables: list[pd.DataFrame] = []
    per_game_summaries: list[dict[str, Any]] = []
    empirical_bot_keys_all: set[tuple[str, str, str]] = set()

    for game, world in game_worlds:
        run_label, full_leaderboard, battles, empirical_bots = _load_empirical_run(payload, run_label_map, game, world)
        group_rows = rows_by_game_world[(game, world)]
        group_empirical_bot_keys = {(game, world, bot) for bot in empirical_bots}
        empirical_bot_keys_all.update(group_empirical_bot_keys)

        pair_df_group = _build_pairwise_table(group_rows, battles, empirical_bots)
        pair_frames.append(pair_df_group)
        ok_pair_df_group = pair_df_group[pair_df_group["compare_status"] == "ok"].copy()
        ok_pair_frames.append(ok_pair_df_group)

        coverage_group = _coverage_summary(group_rows, pair_df_group, group_empirical_bot_keys)
        pair_metrics_group = _pair_metrics_summary(ok_pair_df_group)
        rating_df_group, rating_metrics_group = _compute_rating_compare(ok_pair_df_group, battles, full_leaderboard)

        game_world_label = _game_world_key(game, world)
        if not rating_df_group.empty:
            per_game_rating_df = rating_df_group.rename_axis("bot").reset_index()
            per_game_rating_df.insert(0, "game_world", game_world_label)
            per_game_rating_df.insert(1, "game", game)
            per_game_rating_df.insert(2, "world", world)
            per_game_rating_df.insert(3, "run_label", run_label)
            per_game_rating_df.insert(5, "model_id", per_game_rating_df["bot"].map(_model_name))
            per_game_rating_tables.append(per_game_rating_df)

        per_game_summaries.append(
            {
                "game": game,
                "world": world,
                "game_world": game_world_label,
                "run_label": run_label,
                "coverage": coverage_group,
                "pair_metrics": pair_metrics_group,
                "rating_metrics": rating_metrics_group,
            }
        )

        if multi_game:
            per_game_dir = out_dir / "per_game" / game_world_label.replace("/", "__")
            per_game_dir.mkdir(parents=True, exist_ok=True)
            calibration_score_group = _compute_calibration_table(ok_pair_df_group, pred_col="pred_score_a", emp_col="emp_score_a")
            calibration_draw_group = _compute_calibration_table(ok_pair_df_group, pred_col="pred_p_draw", emp_col="emp_p_draw")
            confusion_group = _compute_top_outcome_confusion(ok_pair_df_group) if not ok_pair_df_group.empty else pd.DataFrame()
            pair_df_group.to_csv(per_game_dir / "pairwise_compare.csv", index=False)
            rating_df_group.to_csv(per_game_dir / "rating_compare.csv")
            calibration_score_group.to_csv(per_game_dir / "calibration_score.csv", index=False)
            calibration_draw_group.to_csv(per_game_dir / "calibration_draw.csv", index=False)
            if not confusion_group.empty:
                confusion_group.to_csv(per_game_dir / "top_outcome_confusion.csv")
            _make_plots(per_game_dir, rating_df_group, game_world_label)
            with (per_game_dir / "summary.json").open("w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "pred_dir": str(pred_dir),
                        "in_pkl": str(in_pkl),
                        "dataset": game_world_label,
                        "coverage": coverage_group,
                        "pair_metrics": pair_metrics_group,
                        "rating_metrics": rating_metrics_group,
                    },
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
                handle.write("\n")
            _write_summary_md(
                per_game_dir / "summary.md",
                pred_dir=pred_dir,
                in_pkl=in_pkl,
                dataset_label=game_world_label,
                coverage=coverage_group,
                usage={},
                pair_metrics=pair_metrics_group,
                rating_metrics=rating_metrics_group,
            )

    pair_df = pd.concat(pair_frames, ignore_index=True) if pair_frames else pd.DataFrame()
    ok_pair_df = pd.concat(ok_pair_frames, ignore_index=True) if ok_pair_frames else pd.DataFrame()
    usage_summary = _compute_usage_summary(rows)
    coverage = _coverage_summary(rows, pair_df, empirical_bot_keys_all)
    pair_metrics = _pair_metrics_summary(ok_pair_df)
    calibration_score = _compute_calibration_table(ok_pair_df, pred_col="pred_score_a", emp_col="emp_score_a")
    calibration_draw = _compute_calibration_table(ok_pair_df, pred_col="pred_p_draw", emp_col="emp_p_draw")
    confusion = _compute_top_outcome_confusion(ok_pair_df) if not ok_pair_df.empty else pd.DataFrame()

    per_game_summary_df = pd.DataFrame.from_records(
        [
            {
                "game": item["game"],
                "world": item["world"],
                "game_world": item["game_world"],
                "run_label": item["run_label"],
                "predicted_pairs_total": item["coverage"]["predicted_pairs_total"],
                "pairs_compared": item["pair_metrics"]["n_pairs"],
                "predicted_unique_bots_in_empirical": item["coverage"]["predicted_unique_bots_in_empirical"],
                "predicted_unique_bots_missing_from_empirical": item["coverage"]["predicted_unique_bots_missing_from_empirical"],
                "mean_multiclass_brier": item["pair_metrics"]["mean_multiclass_brier"],
                "spearman_pred_vs_emp_score": item["pair_metrics"]["spearman_pred_vs_emp_score"],
                "spearman_vs_emp_bt_subset": item["rating_metrics"].get("spearman_vs_emp_bt_subset"),
                "spearman_vs_emp_rating_full": item["rating_metrics"].get("spearman_vs_emp_rating_full"),
            }
            for item in per_game_summaries
        ]
    )

    if len(game_worlds) == 1:
        rating_df = (
            per_game_rating_tables[0]
            .set_index("bot")[
                ["pred_bt", "emp_bt_subset", "emp_rating_full", "pred_rank", "emp_bt_subset_rank", "emp_rating_full_rank"]
            ]
            if per_game_rating_tables
            else pd.DataFrame(columns=["pred_bt", "emp_bt_subset", "emp_rating_full", "pred_rank", "emp_bt_subset_rank", "emp_rating_full_rank"])
        )
        rating_metrics = per_game_summaries[0]["rating_metrics"]
        dataset_label = _game_world_key(*game_worlds[0])
        rating_metrics_scope = "single_game_bot_level"
    else:
        per_game_rating_df = pd.concat(per_game_rating_tables, ignore_index=True) if per_game_rating_tables else pd.DataFrame(
            columns=["game_world", "game", "world", "run_label", "bot", "model_id", "pred_bt", "emp_bt_subset", "emp_rating_full", "pred_rank", "emp_bt_subset_rank", "emp_rating_full_rank"]
        )
        rating_df, rating_metrics = _aggregate_model_rating_compare(per_game_rating_df)
        rating_df.index.name = "model_id"
        dataset_label = f"{len(game_worlds)} game/worlds"
        rating_metrics_scope = "cross_game_model_aggregate"
        per_game_rating_df.to_csv(out_dir / "rating_compare_per_game_bot.csv", index=False)

    pair_df.to_csv(out_dir / "pairwise_compare.csv", index=False)
    rating_df.to_csv(out_dir / "rating_compare.csv")
    if not per_game_summary_df.empty:
        per_game_summary_df.to_csv(out_dir / "per_game_summary.csv", index=False)
    calibration_score.to_csv(out_dir / "calibration_score.csv", index=False)
    calibration_draw.to_csv(out_dir / "calibration_draw.csv", index=False)
    if not confusion.empty:
        confusion.to_csv(out_dir / "top_outcome_confusion.csv")
    _make_plots(out_dir, rating_df, dataset_label if not multi_game else f"Mean Across {len(game_worlds)} Game/Worlds")

    summary = {
        "pred_dir": str(pred_dir),
        "in_pkl": str(in_pkl),
        "games": sorted({game for game, _ in game_worlds}),
        "game_worlds": [_game_world_key(game, world) for game, world in game_worlds],
        "n_game_worlds": len(game_worlds),
        "coverage": coverage,
        "pair_metrics": pair_metrics,
        "rating_metrics": rating_metrics,
        "rating_metrics_scope": rating_metrics_scope,
        "usage": usage_summary,
        "per_game": per_game_summaries,
    }
    with (out_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    _write_summary_md(
        out_dir / "summary.md",
        pred_dir=pred_dir,
        in_pkl=in_pkl,
        dataset_label=dataset_label,
        coverage=coverage,
        usage=usage_summary,
        pair_metrics=pair_metrics,
        rating_metrics=rating_metrics,
    )

    print(f"saved_dir={out_dir}")
    print(f"dataset={dataset_label}")
    print(f"n_game_worlds={len(game_worlds)}")
    print(f"predicted_pairs_total={coverage['predicted_pairs_total']}")
    print(f"pairs_compared={pair_metrics['n_pairs']}")
    print(f"overlap_bots={coverage['predicted_unique_bots_in_empirical']}")
    print(f"missing_bots={coverage['predicted_unique_bots_missing_from_empirical']}")
    print(f"mean_multiclass_brier={pair_metrics['mean_multiclass_brier']}")
    print(f"spearman_pred_vs_emp_bt_subset={rating_metrics.get('spearman_vs_emp_bt_subset')}")


if __name__ == "__main__":
    main()
