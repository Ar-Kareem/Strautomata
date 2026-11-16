from __future__ import annotations

import argparse
import ast
import csv
import difflib
import re
from pathlib import Path
from typing import Any


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def _to_int(value: Any) -> int:
    if value is None:
        return 0
    s = str(value).strip()
    if not s:
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate OpenRouter CSV usage by model_permaslug.")
    parser.add_argument(
        "--in-dir",
        type=str,
        default="openrouter_csv",
        help="Directory containing OpenRouter CSV files.",
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        default="openrouter_csv/model_permaslug_summary.csv",
        help="Output CSV path for aggregated results.",
    )
    parser.add_argument(
        "--out-latex-model-table",
        type=str,
        default=None,
        help="Output .tex path for the 5-column model metadata table. Default: alongside --out-csv.",
    )
    parser.add_argument(
        "--out-latex-name-map",
        type=str,
        default=None,
        help="Output .tex path for the 2-column short-name to save-name table. Default: alongside --out-csv.",
    )
    parser.add_argument(
        "--ignore-human-names",
        nargs="+",
        default=None,
        help="Optional list of human-readable short model names to omit from the LaTeX tables.",
    )
    return parser.parse_args()


def _collect_csv_files(in_dir: Path) -> list[Path]:
    files = sorted(p for p in in_dir.glob("*.csv") if p.is_file())
    if not files:
        raise FileNotFoundError(f"No CSV files found in {in_dir}")
    return files


def _load_dict_literal_from_exp_utils(marker: str) -> dict[Any, Any]:
    exp_utils_path = Path(__file__).resolve().parent / "exp_utils.py"
    if not exp_utils_path.exists():
        return {}
    text = exp_utils_path.read_text()
    idx = text.find(marker)
    if idx < 0:
        return {}
    eq_idx = text.find("=", idx)
    if eq_idx < 0:
        return {}
    brace_start = text.find("{", eq_idx)
    if brace_start < 0:
        return {}

    depth = 0
    brace_end = -1
    for i in range(brace_start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                brace_end = i
                break
    if brace_end < 0:
        return {}

    dict_src = text[brace_start:brace_end + 1]
    try:
        raw: Any = ast.literal_eval(dict_src)
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    return raw


def _load_model_name_map_from_exp_utils() -> dict[str, str]:
    raw = _load_dict_literal_from_exp_utils("MODEL_NAME_MAP")
    out: dict[str, str] = {}
    for k, v in raw.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def _load_model_tuple_map_from_exp_utils() -> dict[str, tuple[Any, ...]]:
    raw = _load_dict_literal_from_exp_utils("MODEL_NAME_TUPLE_MAP")
    out: dict[str, tuple[Any, ...]] = {}
    for k, v in raw.items():
        if isinstance(k, str) and isinstance(v, tuple):
            out[k] = v
    return out


def _slug_core_from_permaslug(permaslug: str) -> str:
    if "/" not in permaslug:
        return permaslug.strip()
    return permaslug.split("/", 1)[1].strip()


def _normalize_for_match(s: str) -> str:
    s = s.lower()
    s = s.replace(".", "")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def _tokens_for_match(s: str) -> list[str]:
    norm = _normalize_for_match(s)
    if not norm:
        return []
    return [tok for tok in norm.split() if tok]


def _match_score(slug_core: str, model_key: str) -> float:
    a = _normalize_for_match(slug_core)
    b = _normalize_for_match(model_key)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0

    # char-level closeness
    ratio = difflib.SequenceMatcher(None, a.replace(" ", ""), b.replace(" ", "")).ratio()

    # token overlap helps for versioned slugs like "...-20260211"
    ta = set(_tokens_for_match(slug_core))
    tb = set(_tokens_for_match(model_key))
    tok_overlap = 0.0
    if ta and tb:
        tok_overlap = len(ta & tb) / max(len(ta), len(tb))

    # containment bonus for near-prefix forms
    compact_a = a.replace(" ", "")
    compact_b = b.replace(" ", "")
    contain_bonus = 0.0
    if compact_a in compact_b or compact_b in compact_a:
        contain_bonus = 0.15

    return min(1.0, 0.6 * ratio + 0.4 * tok_overlap + contain_bonus)


# Minimum fuzzy-match score for a slug -> human name assignment. Without this,
# the greedy assignment pairs leftover slugs with leftover human names no matter
# how dissimilar (e.g. qwen3.5-flash -> "Claude Haiku 4.5").
_MIN_MATCH_SCORE = 0.5


def _build_high_use_human_names(rows: list[dict[str, Any]], model_name_map: dict[str, str]) -> dict[str, str]:
    # Map unique high-use slug cores to unique MODEL_NAME_MAP human names.
    high_use_cores = sorted(
        {
            _slug_core_from_permaslug(str(r["model_permaslug"]))
            for r in rows
            if bool(r.get("high_use"))
        }
    )
    if not high_use_cores or not model_name_map:
        return {}

    candidates: list[tuple[float, str, str, str]] = []
    for core in high_use_cores:
        for key, human in model_name_map.items():
            score = _match_score(core, key)
            candidates.append((score, core, key, human))

    # Global greedy assignment with uniqueness on core and human_name.
    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    assigned_core: set[str] = set()
    assigned_human: set[str] = set()
    out: dict[str, str] = {}
    for score, core, _key, human in candidates:
        if core in assigned_core or human in assigned_human:
            continue
        if score < _MIN_MATCH_SCORE:
            continue
        out[core] = human
        assigned_core.add(core)
        assigned_human.add(human)
    print('mapping found')
    print(out)
    return out


def _aggregate(csv_files: list[Path]) -> list[dict[str, Any]]:
    by_slug: dict[str, dict[str, Any]] = {}
    for csv_path in csv_files:
        with csv_path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                slug = str(row.get("model_permaslug", "")).strip()
                if not slug:
                    continue
                entry = by_slug.setdefault(
                    slug,
                    {
                        "model_permaslug": slug,
                        "n_rows": 0,
                        "total_cost": 0.0,
                        "total_tokens_completion": 0,
                        "total_tokens_reasoning": 0,
                        "providers": set(),
                    },
                )
                entry["n_rows"] += 1
                entry["total_cost"] += _to_float(row.get("cost_total"))
                entry["total_tokens_completion"] += _to_int(row.get("tokens_completion"))
                entry["total_tokens_reasoning"] += _to_int(row.get("tokens_reasoning"))
                provider = str(row.get("provider_name", "")).strip()
                if provider:
                    entry["providers"].add(provider)

    rows: list[dict[str, Any]] = []
    for slug, entry in by_slug.items():
        n = max(1, int(entry["n_rows"]))
        provider_list = sorted(str(p) for p in entry["providers"] if str(p))
        rows.append(
            {
                "model_permaslug": slug,
                "n_rows": int(entry["n_rows"]),
                "high_use": int(entry["n_rows"]) >= 100,
                "provider": ",".join(provider_list),
                "total_cost": float(entry["total_cost"]),
                "avg_cost": float(entry["total_cost"]) / n,
                "total_tokens_completion": int(entry["total_tokens_completion"]),
                "avg_tokens_completion": int(entry["total_tokens_completion"]) / n,
                "total_tokens_reasoning": int(entry["total_tokens_reasoning"]),
                "avg_tokens_reasoning": int(entry["total_tokens_reasoning"]) / n,
                "human_name": "",
            }
        )

    model_name_map = _load_model_name_map_from_exp_utils()
    high_use_name_map = _build_high_use_human_names(rows, model_name_map)
    for row in rows:
        if bool(row.get("high_use")):
            core = _slug_core_from_permaslug(str(row["model_permaslug"]))
            row["human_name"] = high_use_name_map.get(core, core)
    model_tuple_map = _load_model_tuple_map_from_exp_utils()
    for row in rows:
        is_open_source: bool | str = ""
        param_count_b: float | str = ""
        param_text: str = ""
        candidate_name = str(row.get("human_name", "")).strip()
        if not candidate_name:
            core = _slug_core_from_permaslug(str(row["model_permaslug"]))
            candidate_name = str(model_name_map.get(core, "")).strip()
        meta = model_tuple_map.get(candidate_name)
        if isinstance(meta, tuple):
            if len(meta) >= 1 and isinstance(meta[0], bool):
                is_open_source = bool(meta[0])
            if len(meta) >= 2 and isinstance(meta[1], (int, float)):
                param_count_b = float(meta[1])
            if len(meta) >= 3 and isinstance(meta[2], str):
                param_text = meta[2]
        row["is_open_source"] = is_open_source
        row["param_count_b"] = param_count_b
        row["param_text"] = param_text
        row["openrouter_url"] = f"https://openrouter.ai/{row['model_permaslug']}"

    rows.sort(
        key=lambda r: (
            0 if bool(r.get("high_use")) else 1,
            _split_permaslug(str(r.get("model_permaslug", "")))[0].lower(),
            str(r.get("human_name", "")),
        )
    )
    return rows


def _write_csv(rows: list[dict[str, Any]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model_permaslug",
        "openrouter_url",
        "human_name",
        "is_open_source",
        "param_count_b",
        "param_text",
        "n_rows",
        "high_use",
        "provider",
        "total_cost",
        "avg_cost",
        "total_tokens_completion",
        "avg_tokens_completion",
        "total_tokens_reasoning",
        "avg_tokens_reasoning",
    ]
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            open_source_value = row.get("is_open_source", "")
            if isinstance(open_source_value, bool):
                open_source_value = str(open_source_value)
            param_count_value = row.get("param_count_b", "")
            if isinstance(param_count_value, (int, float)):
                param_count_value = f"{float(param_count_value):.1f}"
            writer.writerow(
                {
                    "model_permaslug": row["model_permaslug"],
                    "openrouter_url": row.get("openrouter_url", ""),
                    "human_name": row["human_name"],
                    "is_open_source": open_source_value,
                    "param_count_b": param_count_value,
                    "param_text": row.get("param_text", ""),
                    "n_rows": row["n_rows"],
                    "high_use": str(bool(row["high_use"])),
                    "provider": row["provider"],
                    "total_cost": f"{row['total_cost']:.6f}",
                    "avg_cost": f"{row['avg_cost']:.6f}",
                    "total_tokens_completion": row["total_tokens_completion"],
                    "avg_tokens_completion": f"{row['avg_tokens_completion']:.2f}",
                    "total_tokens_reasoning": row["total_tokens_reasoning"],
                    "avg_tokens_reasoning": f"{row['avg_tokens_reasoning']:.2f}",
                }
            )


def _split_permaslug(permaslug: str) -> tuple[str, str]:
    if "/" not in permaslug:
        return "", permaslug
    left, right = permaslug.split("/", 1)
    return left.strip(), right.strip()


def _latex_escape(s: str) -> str:
    return (
        s.replace("\\", r"\textbackslash{}")
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


def _latex_short_name(short_name: str) -> str:
    rename_map = {
        "Claude Opus 4.6 (instant)": "Claude Opus 4.6",
        "Claude Opus 4.7 High": "Claude Opus 4.7",
        "GPT-5.2 (Adaptive)": "GPT-5.2",
        "GPT-5.5 Low": "GPT-5.5",
    }
    return rename_map.get(short_name, short_name)


def _iter_filtered_latex_rows(
    rows: list[dict[str, Any]],
    *,
    ignore_human_names: list[str] | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    ignored = {str(name).strip().casefold() for name in (ignore_human_names or []) if str(name).strip()}
    table_rows: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        if not bool(row.get("high_use")):
            continue
        short_name = str(row.get("human_name", "")).strip()
        if not short_name:
            short_name = _slug_core_from_permaslug(str(row.get("model_permaslug", "")))
        display_short_name = _latex_short_name(short_name)
        if short_name.strip().casefold() in ignored or display_short_name.strip().casefold() in ignored:
            continue
        table_rows.append((display_short_name, row))
    table_rows.sort(key=lambda item: item[0].casefold())
    return table_rows


def _render_latex_table(
    rows: list[dict[str, Any]],
    *,
    ignore_human_names: list[str] | None = None,
) -> str:
    table_rows = _iter_filtered_latex_rows(rows, ignore_human_names=ignore_human_names)
    table_rows = sorted(
        table_rows,
        key=lambda item: (
            _split_permaslug(str(item[1].get("model_permaslug", "")))[0].casefold(),
            item[0].casefold(),
        ),
    )
    lines: list[str] = [
        r"\begin{tabular}{lllll}",
        r"\hline",
        r"Short model name & Publisher & Full model name & \#parameters & Open source \\",
        r"\hline",
    ]
    for short_name, row in table_rows:
        prime_slug, full_model_name = _split_permaslug(str(row.get("model_permaslug", "")))
        publisher = prime_slug.capitalize()
        open_source = row.get("is_open_source", "")
        if isinstance(open_source, bool):
            open_source_txt = "True" if open_source else "False"
        else:
            open_source_txt = ""
        param_text = str(row.get("param_text", "")).strip()
        if short_name == "DeepSeek TNG R1T" and open_source_txt == "False":
            open_source_txt = "False*"
        lines.append(
            f"{_latex_escape(short_name)} & "
            f"{_latex_escape(publisher)} & "
            f"{_latex_escape(full_model_name)} & "
            f"{_latex_escape(param_text)} & "
            f"{_latex_escape(open_source_txt)} \\\\"
        )
    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
        ]
    )
    return "\n".join(lines) + "\n"


def _save_name_preference_key(save_name: str) -> tuple[int, int, str]:
    # Prefer the explicit free alias when multiple arena save-names collapse to
    # the same human-readable label (e.g. MiMo/Devstral). Then prefer shorter,
    # simpler keys for stable output.
    return (
        0 if save_name.endswith("_free") else 1,
        len(save_name),
        save_name,
    )


def _build_short_name_to_save_name_map() -> dict[str, str]:
    model_name_map = _load_model_name_map_from_exp_utils()
    by_short_name: dict[str, list[str]] = {}
    for save_name, human_name in model_name_map.items():
        if save_name == "random":
            continue
        display_short_name = _latex_short_name(str(human_name).strip())
        by_short_name.setdefault(display_short_name, []).append(str(save_name))

    out: dict[str, str] = {}
    for short_name, save_names in by_short_name.items():
        ordered = sorted(set(save_names), key=_save_name_preference_key)
        if ordered:
            out[short_name] = ordered[0]
    return out


def _render_short_name_save_name_table(
    rows: list[dict[str, Any]],
    *,
    ignore_human_names: list[str] | None = None,
) -> str:
    table_rows = _iter_filtered_latex_rows(rows, ignore_human_names=ignore_human_names)
    short_name_to_save_name = _build_short_name_to_save_name_map()
    lines: list[str] = [
        r"\begin{tabular}{ll}",
        r"\toprule",
        r"Short model name & Full model name \\",
        r"\midrule",
    ]
    for short_name, _row in table_rows:
        save_name = short_name_to_save_name.get(short_name)
        if save_name is None:
            continue
        lines.append(f"{_latex_escape(short_name)} & {_latex_escape(save_name)} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines) + "\n"


def main() -> None:
    args = _parse_args()
    in_dir = Path(args.in_dir)
    if not in_dir.exists() or not in_dir.is_dir():
        raise FileNotFoundError(f"--in-dir must be an existing directory: {in_dir}")
    csv_files = _collect_csv_files(in_dir)
    rows = _aggregate(csv_files)
    out_csv = Path(args.out_csv)
    out_latex_model_table = (
        Path(args.out_latex_model_table)
        if args.out_latex_model_table
        else out_csv.parent / "openrouter_model_metadata_table.tex"
    )
    out_latex_name_map = (
        Path(args.out_latex_name_map)
        if args.out_latex_name_map
        else out_csv.parent / "openrouter_short_name_mapping_table.tex"
    )
    _write_csv(rows, out_csv)
    out_latex_model_table.parent.mkdir(parents=True, exist_ok=True)
    out_latex_name_map.parent.mkdir(parents=True, exist_ok=True)
    out_latex_model_table.write_text(
        _render_latex_table(rows, ignore_human_names=args.ignore_human_names),
        encoding="utf-8",
    )
    out_latex_name_map.write_text(
        _render_short_name_save_name_table(rows, ignore_human_names=args.ignore_human_names),
        encoding="utf-8",
    )
    print(f"saved_summary_csv={out_csv}")
    print(f"saved_model_table_tex={out_latex_model_table}")
    print(f"saved_name_map_tex={out_latex_name_map}")


if __name__ == "__main__":
    main()
