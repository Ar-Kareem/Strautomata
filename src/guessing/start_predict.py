#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime
from json import JSONDecoder
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from game_arena import utils as arena_utils
from game_arena.prompter import OpenRouterModel, get_openrouter_models, get_response_single_msg


ROOT_DIR = arena_utils.get_root_path()
PROMPT_VERSION = "0.2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run winner-guessing predictions over a prompt dataset.")
    parser.add_argument("--in-json", required=True, help="Input JSON dataset from guessing.build_dataset.")
    parser.add_argument("--model", required=True, help="Model name or override key, following game_arena/prompter_overrides.json.")
    parser.add_argument("--out-dir", required=True, help="Output directory for saved predictions.")
    parser.add_argument("--max-workers", type=int, default=4, help="Concurrent request workers.")
    parser.add_argument("--retry-count", type=int, default=2, help="Retries per row on request failure.")
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of rows to process.")
    parser.add_argument("--no-skip", action="store_true", help="Dont skip rows with an existing saved JSON result.")
    return parser.parse_args()


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _load_rows(in_json: Path) -> list[dict[str, Any]]:
    rows = json.loads(in_json.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"Expected a JSON list in {in_json}, got {type(rows).__name__}")
    required = {"id", "game", "world", "bot_a", "bot_b", "rules", "bot_a_code", "bot_b_code"}
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Row {i} is not an object")
        missing = sorted(required - set(row))
        if missing:
            raise ValueError(f"Row {i} is missing required keys: {missing}")
    return rows


def _summarize_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    games = sorted({str(row["game"]) for row in rows})
    game_worlds = sorted({f"{row['game']}/{row['world']}" for row in rows})
    if not rows:
        raise ValueError("Input dataset has no rows")
    return {
        "games": games,
        "game_worlds": game_worlds,
        "n_games": len(games),
        "n_game_worlds": len(game_worlds),
    }


def _resolve_model(model_name: str) -> OpenRouterModel:
    models = get_openrouter_models([model_name])
    if not models:
        raise ValueError(f"Could not resolve OpenRouter model for {model_name!r}")
    if len(models) != 1:
        raise ValueError(f"Expected exactly one resolved model for {model_name!r}, got {len(models)}")
    return models[0]


def _render_prompt(row: dict[str, Any]) -> str:
    return (
        "You are evaluating two anonymous game-playing bots.\n\n"
        "Task\n"
        "- Read the game rules and both bot source files.\n"
        "- Predict the outcome distribution when Bot A and Bot B play many games.\n"
        "- Treat first-move advantage as averaged out across seat orders.\n"
        "- Ignore bot/model identities and reason only from the rules and code.\n"
        "- First give short reasoning.\n"
        "- Then output a JSON object exactly in this schema: "
        "{\"p_a\": <float>, \"p_b\": <float>, \"p_draw\": <float>}.\n\n"
        "Constraints\n"
        "- 0 <= p_a <= 1\n"
        "- 0 <= p_b <= 1\n"
        "- 0 <= p_draw <= 1\n"
        "- p_a + p_b + p_draw = 1\n\n"
        "Game Rules\n"
        "```text\n"
        f"{row['rules'].strip()}\n"
        "```\n\n"
        "Bot A Code\n"
        "```python\n"
        f"{row['bot_a_code'].rstrip()}\n"
        "```\n\n"
        "Bot B Code\n"
        "```python\n"
        f"{row['bot_b_code'].rstrip()}\n"
        "```\n\n"
        "Keep your answer verybrief."
    )


def _extract_json_object(text: str) -> dict[str, Any] | None:
    decoder = JSONDecoder()
    best: dict[str, Any] | None = None
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            best = obj
    return best


def _parse_prediction(text: str) -> tuple[dict[str, float] | None, str | None]:
    obj = _extract_json_object(text)
    if obj is None:
        return None, "No JSON object found in model response"
    if "p_a" not in obj or "p_b" not in obj or "p_draw" not in obj:
        return None, "JSON object missing p_a, p_b, or p_draw"
    try:
        p_a = float(obj["p_a"])
        p_b = float(obj["p_b"])
        p_draw = float(obj["p_draw"])
    except (TypeError, ValueError):
        return None, "p_a, p_b, or p_draw is not numeric"
    if (
        p_a < 0 or p_a > 1 or
        p_b < 0 or p_b > 1 or
        p_draw < 0 or p_draw > 1 or
        abs((p_a + p_b + p_draw) - 1.0) > 1e-6
    ):
        return None, "Probabilities are out of range"
    return {"p_a": p_a, "p_b": p_b, "p_draw": p_draw}, None


def _safe_message_field(message: dict[str, Any], key: str) -> Any:
    value = message.get(key)
    return value if value is not None else None


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return slug or "row"


def _result_stem(row_id: str) -> str:
    slug = _slugify(row_id)
    digest = hashlib.sha256(row_id.encode("utf-8")).hexdigest()[:10]
    return f"{slug}__{digest}"


def _result_path(model_dir: Path, row_id: str) -> Path:
    return model_dir / f"{_result_stem(row_id)}.json"


def _looks_like_legacy_result_path(path: Path, row_id: str) -> bool:
    parts = path.stem.split("_", 1)
    if len(parts) != 2 or not parts[0].isdigit():
        return False
    return parts[1] == _slugify(row_id)


def _result_file_id(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    row_id = payload.get("id")
    return str(row_id) if row_id is not None else None


def _find_existing_result_path(model_dir: Path, row_id: str) -> Path | None:
    preferred = _result_path(model_dir, row_id)
    if preferred.exists():
        return preferred
    for path in sorted(model_dir.glob("*.json")):
        if path.name in {"run_info.json", "all_predictions.json"}:
            continue
        if not _looks_like_legacy_result_path(path, row_id):
            continue
        if _result_file_id(path) == row_id:
            return path
    return None


def _canonicalize_existing_result_path(model_dir: Path, row_id: str) -> Path | None:
    existing = _find_existing_result_path(model_dir, row_id)
    if existing is None:
        return None
    target = _result_path(model_dir, row_id)
    if existing == target:
        return target
    if not target.exists():
        existing.rename(target)
    return target


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _predict_one(model: OpenRouterModel, row_index: int, row: dict[str, Any], retry_count: int) -> dict[str, Any]:
    prompt = _render_prompt(row)
    last_error: str | None = None
    for attempt in range(retry_count):
        try:
            response = get_response_single_msg(model, prompt)
            if response is None:
                raise RuntimeError("Model request returned no response")
            content = response.content or ""
            parsed, parse_error = _parse_prediction(content)
            return {
                "status": "ok" if parse_error is None else "parse_error",
                "id": row["id"],
                "game": row["game"],
                "world": row["world"],
                "bot_a": row["bot_a"],
                "bot_b": row["bot_b"],
                "model": asdict(model),
                "prompt_version": PROMPT_VERSION,
                "prompt": prompt,
                "response_text": content,
                "api_reasoning": response.reasoning,
                "usage": response.usage,
                "parsed": parsed,
                "parse_error": parse_error,
                "attempt_count": attempt + 1,
                "now": datetime.now().isoformat(),
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return {
        "status": "request_error",
        "id": row["id"],
        "game": row["game"],
        "world": row["world"],
        "bot_a": row["bot_a"],
        "bot_b": row["bot_b"],
        "model": asdict(model),
        "prompt_version": PROMPT_VERSION,
        "prompt": prompt,
        "response_text": None,
        "api_reasoning": None,
        "usage": None,
        "parsed": None,
        "parse_error": None,
        "request_error": last_error,
        "attempt_count": retry_count,
        "now": datetime.now().isoformat(),
    }


def _write_manifest(
    model_dir: Path,
    in_json: Path,
    model: OpenRouterModel,
    total_rows: int,
    dataset_summary: dict[str, Any],
) -> None:
    _save_json(
        model_dir / "run_info.json",
        {
            "input_json": str(in_json),
            "model": asdict(model),
            "prompt_version": PROMPT_VERSION,
            "total_rows": total_rows,
            "dataset": dataset_summary,
            "now": datetime.now().isoformat(),
        },
    )


def _write_combined(model_dir: Path) -> None:
    row_files = sorted(path for path in model_dir.glob("*.json") if path.name not in {"run_info.json", "all_predictions.json"})
    rows_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    fallback_rows: list[dict[str, Any]] = []
    for path in row_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        row_id = payload.get("id")
        if row_id is None:
            fallback_rows.append(payload)
            continue
        key = str(row_id)
        previous = rows_by_id.get(key)
        if previous is None:
            rows_by_id[key] = (path, payload)
            continue
        prev_path, _ = previous
        prev_is_legacy = _looks_like_legacy_result_path(prev_path, key)
        curr_is_legacy = _looks_like_legacy_result_path(path, key)
        if prev_is_legacy and not curr_is_legacy:
            rows_by_id[key] = (path, payload)
        elif prev_is_legacy == curr_is_legacy and path.name > prev_path.name:
            rows_by_id[key] = (path, payload)
    rows = [payload for _, payload in sorted(rows_by_id.values(), key=lambda item: item[0].name)] + fallback_rows
    _save_json(model_dir / "all_predictions.json", rows)


def main() -> None:
    args = parse_args()
    load_dotenv(ROOT_DIR / ".env")

    in_json = _resolve_path(args.in_json)
    out_dir = _resolve_path(args.out_dir)
    all_rows = _load_rows(in_json)
    dataset_summary = _summarize_dataset(all_rows)
    rows = all_rows
    if args.limit is not None:
        rows = rows[:args.limit]

    model = _resolve_model(args.model)
    model_dir = out_dir
    model_dir.mkdir(parents=True, exist_ok=True)
    _write_manifest(model_dir, in_json, model, len(rows), dataset_summary)

    todo: list[tuple[int, dict[str, Any], Path]] = []
    skipped = 0
    for i, row in enumerate(rows):
        result_path = _result_path(model_dir, row["id"])
        _canonicalize_existing_result_path(model_dir, row["id"])
        if not args.no_skip and result_path.exists():
            skipped += 1
            continue
        todo.append((i, row, result_path))

    if not todo:
        _write_combined(model_dir)
        print(f"model_dir={model_dir}")
        print("n_rows=0")
        print(f"skipped={skipped}")
        return

    success = 0
    parse_errors = 0
    request_errors = 0
    max_workers = min(max(args.max_workers, 1), len(todo))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_predict_one, model, row_index, row, args.retry_count): (row_index, row, result_path)
            for row_index, row, result_path in todo
        }
        for future in as_completed(futures):
            row_index, row, result_path = futures[future]
            result = future.result()
            _save_json(result_path, result)
            if result["status"] == "ok":
                success += 1
            elif result["status"] == "parse_error":
                parse_errors += 1
            else:
                request_errors += 1
            print(f"saved={result_path} status={result['status']} row={row_index}")

    _write_combined(model_dir)
    print(f"model_dir={model_dir}")
    print(f"n_rows={len(todo)}")
    print(f"skipped={skipped}")
    print(f"ok={success}")
    print(f"parse_error={parse_errors}")
    print(f"request_error={request_errors}")


if __name__ == "__main__":
    main()
