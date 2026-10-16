#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from experimental.exp_utils import MAIN_GAMES_WORLD_COLUMNS, NAME_DELETE  # noqa: E402
from game_arena import utils  # noqa: E402


@dataclass
class ModelInfoAggregate:
    bot_count: int = 0
    info_json_count: int = 0
    games: set[str] = field(default_factory=set)
    game_worlds: set[str] = field(default_factory=set)
    model_dir_names: set[str] = field(default_factory=set)
    now_values: list[datetime] = field(default_factory=list)
    prompt_versions: Counter[str] = field(default_factory=Counter)
    numeric_fields: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    bool_fields: dict[str, list[bool]] = field(default_factory=lambda: defaultdict(list))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze current bots in repo and export CSV summaries.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("analysis/current_bots"),
        help="Directory where CSV files are written.",
    )
    parser.add_argument(
        "--elos-csv",
        type=Path,
        default=None,
        help="Optional ratings CSV containing a 'Median ELO' column (e.g. rating_df.csv).",
    )
    return parser.parse_args()


def _flatten_dict(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_str = str(key)
            new_prefix = f"{prefix}.{key_str}" if prefix else key_str
            out.extend(_flatten_dict(value, new_prefix))
    else:
        out.append((prefix, obj))
    return out


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _as_model_name(model_dir_name: str, info_data: dict[str, Any] | None) -> str:
    if not info_data:
        return model_dir_name
    model_obj = info_data.get("model")
    if isinstance(model_obj, dict):
        save_name = model_obj.get("save_name")
        if isinstance(save_name, str) and save_name.strip():
            return save_name
    if isinstance(model_obj, str) and model_obj.strip():
        return model_obj
    return model_dir_name


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, dict):
        return data
    return None


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return False


def _sanitize_col_name(name: str) -> str:
    return (
        name.strip()
        .replace(" ", "_")
        .replace(".", "__")
        .replace("/", "_")
        .replace("-", "_")
        .replace(":", "_")
    )


def _format_bot_count_cell(value: Any) -> str:
    if pd.isna(value):
        return ""

    count = int(value)
    if count > 6:
        icon = "🔵"
    elif count == 6:
        icon = "🟢"
    else:
        icon = "🟡"
    return f"{count} ({icon})"


def _load_median_elo(elo_csv: Path | None) -> pd.Series | None:
    if elo_csv is None:
        return None
    path = elo_csv if elo_csv.is_absolute() else ROOT_DIR / elo_csv
    if not path.exists():
        print(f"Warning: --elos-csv not found: {path}")
        return None
    try:
        df = pd.read_csv(path, index_col=0)
    except Exception as exc:
        print(f"Warning: failed to read --elos-csv ({path}): {type(exc).__name__}: {exc}")
        return None
    if "Median ELO" not in df.columns:
        print(f"Warning: --elos-csv missing 'Median ELO' column: {path}")
        return None
    return pd.to_numeric(df["Median ELO"], errors="coerce")


def _write_table_outputs(
    df: pd.DataFrame,
    csv_path: Path,
    *,
    index: bool,
    index_label: str | None = None,
) -> tuple[Path, Path]:
    if index:
        df.to_csv(csv_path, index=True, index_label=index_label)
        json_df = df.rename_axis(index_label).reset_index() if index_label else df.reset_index()
    else:
        df.to_csv(csv_path, index=False)
        json_df = df

    json_path = csv_path.with_suffix(".json")
    records = json.loads(json_df.to_json(orient="records", force_ascii=False))
    json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return csv_path, json_path


def collect_bot_data() -> tuple[dict[str, dict[str, int]], dict[str, ModelInfoAggregate]]:
    counts_by_col: dict[str, dict[str, int]] = {}
    info_aggs: dict[str, ModelInfoAggregate] = {}

    for game_str, world, col_name, _match_json in MAIN_GAMES_WORLD_COLUMNS:
        ex_dir = utils.get_examples_dir(game_str) / world
        counts_for_col: dict[str, int] = defaultdict(int)
        if not ex_dir.exists():
            counts_by_col[col_name] = {}
            continue

        for model_dir in sorted(ex_dir.iterdir()):
            if not model_dir.is_dir():
                continue
            model_dir_name = model_dir.name
            if model_dir_name in NAME_DELETE:
                continue

            for bot_dir in sorted(model_dir.iterdir()):
                if not bot_dir.is_dir():
                    continue
                if not (bot_dir / "2.python_code.py").exists():
                    continue

                counts_for_col[model_dir_name] += 1

                info_path = bot_dir / "0.info.json"
                info_data = _safe_read_json(info_path) if info_path.exists() else None
                model_name = _as_model_name(model_dir_name, info_data)
                if model_name in NAME_DELETE:
                    continue

                agg = info_aggs.setdefault(model_name, ModelInfoAggregate())
                agg.bot_count += 1
                agg.games.add(col_name)
                agg.game_worlds.add(f"{game_str}:{world}")
                agg.model_dir_names.add(model_dir_name)

                if info_data is None:
                    continue

                agg.info_json_count += 1

                dt = _parse_dt(info_data.get("now"))
                if dt is not None:
                    agg.now_values.append(dt)

                prompt_version = info_data.get("prompt_version")
                if isinstance(prompt_version, str) and prompt_version.strip():
                    agg.prompt_versions[prompt_version] += 1

                prompt_text = info_data.get("prompt")
                if isinstance(prompt_text, str):
                    agg.numeric_fields["prompt_char_len"].append(float(len(prompt_text)))

                reasoning = info_data.get("reasoning")
                if isinstance(reasoning, str):
                    agg.numeric_fields["reasoning_char_len"].append(float(len(reasoning)))

                for key, value in _flatten_dict(info_data):
                    if not key or key in {"prompt", "reasoning"}:
                        continue
                    if _is_finite_number(value):
                        agg.numeric_fields[key].append(float(value))
                    elif isinstance(value, bool):
                        agg.bool_fields[key].append(bool(value))

        counts_by_col[col_name] = dict(counts_for_col)

    return counts_by_col, info_aggs


def build_bot_counts_df(
    counts_by_col: dict[str, dict[str, int]],
    median_elo: pd.Series | None,
) -> pd.DataFrame:
    ordered_cols = [col for _game, _world, col, _match_json in MAIN_GAMES_WORLD_COLUMNS]
    out_df = pd.DataFrame({col: counts_by_col.get(col, {}) for col in ordered_cols})
    numeric_counts_df = out_df.apply(pd.to_numeric, errors="coerce")

    out_df["total_bots"] = out_df.sum(axis=1, skipna=True)
    out_df["missing_count"] = (6 - numeric_counts_df.fillna(0).clip(upper=6)).sum(axis=1)
    out_df["nan_count"] = out_df.isna().sum(axis=1)
    if median_elo is not None:
        out_df["Median ELO"] = median_elo.reindex(out_df.index).round()
    else:
        out_df["Median ELO"] = pd.NA

    out_df["total_bots"] = pd.to_numeric(out_df["total_bots"], errors="coerce").astype("Int64")
    out_df["missing_count"] = pd.to_numeric(out_df["missing_count"], errors="coerce").astype("Int64")
    out_df["nan_count"] = pd.to_numeric(out_df["nan_count"], errors="coerce").astype("Int64")
    out_df["Median ELO"] = pd.to_numeric(out_df["Median ELO"], errors="coerce").round().astype("Int64")
    out_df = out_df.sort_values(
        by=["missing_count", "total_bots", "Median ELO"],
        ascending=[False, True, False],
        na_position="last",
    )

    out_df.insert(0, "Model#", range(1, len(out_df) + 1))

    for col in ordered_cols:
        out_df[col] = pd.to_numeric(out_df[col], errors="coerce").astype("Int64")
        out_df[col] = out_df[col].map(_format_bot_count_cell)

    return out_df


def build_info_aggregate_df(info_aggs: dict[str, ModelInfoAggregate]) -> pd.DataFrame:
    all_num_fields = sorted({field_name for agg in info_aggs.values() for field_name in agg.numeric_fields})
    all_bool_fields = sorted({field_name for agg in info_aggs.values() for field_name in agg.bool_fields})

    rows: list[dict[str, Any]] = []
    for model_name in sorted(info_aggs):
        agg = info_aggs[model_name]
        row: dict[str, Any] = {
            "model": model_name,
            "model_folder_name": ", ".join(sorted(agg.model_dir_names)) if agg.model_dir_names else pd.NA,
            "bot_count": agg.bot_count,
            "info_json_count": agg.info_json_count,
            "info_coverage": (agg.info_json_count / agg.bot_count) if agg.bot_count else 0.0,
            "games_count": len(agg.games),
            "game_worlds_count": len(agg.game_worlds),
            "prompt_version_mode": agg.prompt_versions.most_common(1)[0][0] if agg.prompt_versions else pd.NA,
            "prompt_version_unique_count": len(agg.prompt_versions),
            "first_now": min(agg.now_values).isoformat() if agg.now_values else pd.NA,
            "last_now": max(agg.now_values).isoformat() if agg.now_values else pd.NA,
        }

        for field_name in all_num_fields:
            safe = _sanitize_col_name(field_name)
            values = agg.numeric_fields.get(field_name, [])
            if not values:
                row[f"{safe}__count"] = 0
                row[f"{safe}__sum"] = pd.NA
                row[f"{safe}__mean"] = pd.NA
                row[f"{safe}__min"] = pd.NA
                row[f"{safe}__max"] = pd.NA
                continue
            arr = np.asarray(values, dtype=float)
            row[f"{safe}__count"] = int(arr.size)
            row[f"{safe}__sum"] = float(arr.sum())
            row[f"{safe}__mean"] = float(arr.mean())
            row[f"{safe}__min"] = float(arr.min())
            row[f"{safe}__max"] = float(arr.max())

        for field_name in all_bool_fields:
            safe = _sanitize_col_name(field_name)
            values = agg.bool_fields.get(field_name, [])
            true_count = int(sum(1 for v in values if v))
            false_count = int(sum(1 for v in values if not v))
            count = true_count + false_count
            row[f"{safe}__count"] = count
            row[f"{safe}__true_count"] = true_count
            row[f"{safe}__false_count"] = false_count
            row[f"{safe}__true_rate"] = (true_count / count) if count else pd.NA

        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(by=["info_json_count", "bot_count", "model"], ascending=[False, False, True], na_position="last")


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT_DIR / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    counts_by_col, info_aggs = collect_bot_data()
    median_elo = _load_median_elo(args.elos_csv)

    counts_df = build_bot_counts_df(
        counts_by_col=counts_by_col,
        median_elo=median_elo,
    )
    counts_path = out_dir / "bot_counts.csv"
    counts_csv_path, counts_json_path = _write_table_outputs(counts_df, counts_path, index=True, index_label="model")

    info_df = build_info_aggregate_df(info_aggs)
    info_path = out_dir / "model_info_aggregates.csv"
    info_csv_path, info_json_path = _write_table_outputs(info_df, info_path, index=False)

    print(f"Wrote bot count summaries: {counts_csv_path} and {counts_json_path}")
    print(f"Wrote info.json aggregate summaries: {info_csv_path} and {info_json_path}")


if __name__ == "__main__":
    main()
