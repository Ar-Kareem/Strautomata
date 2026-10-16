#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import io
import json
import keyword
import math
import os
import pickle
import re
import shutil
import sys
import time
import tokenize
import urllib.error
import urllib.request
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2
from dotenv import load_dotenv
from game_arena.utils import get_root_path

assert load_dotenv(get_root_path() / '.env')

SRC_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SRC_ROOT.parent
GAME_ARENA_ROOT = SRC_ROOT / "game_arena"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

OPENROUTER_PROVIDER = "openrouter"
MODEL_DEFAULT = "openai/text-embedding-3-small"
OPENROUTER_MODEL_ALIASES = {
    "text-embedding-3-small": "openai/text-embedding-3-small",
    "text-embedding-3-large": "openai/text-embedding-3-large",
    "text-embedding-ada-002": "openai/text-embedding-ada-002",
}
EMBEDDING_PRICE_PER_1M_TOKENS_USD_BY_MODEL = {
    "text-embedding-3-small": 0.02,
    "openai/text-embedding-3-small": 0.02,
    "text-embedding-3-large": 0.13,
    "openai/text-embedding-3-large": 0.13,
    "text-embedding-ada-002": 0.10,
    "openai/text-embedding-ada-002": 0.10,
}
OPENROUTER_CACHE_HEADER_VALUE = "true"
RETRYABLE_API_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
OPENROUTER_EMBEDDING_INPUT_TOKEN_LIMIT = 8192
OVERSIZE_RETRY_TOKEN_FRACTION = 0.67
FORCED_RESPLIT_CHARS_PER_TOKEN = 3.0
MIN_FORCED_RESPLIT_TOKENS = 512

EMBEDDING_CHECKPOINT_FILENAME = "openrouter_chunk_embedding_checkpoint.npz"
EMBEDDING_PROGRESS_FILENAME = "openrouter_chunk_embedding_progress.json"

DEFAULT_K_MIN = 2
DEFAULT_K_MAX = 12
DEFAULT_RANDOM_SEED = 0
DEFAULT_TOP_THEME_TERMS = 3
DEFAULT_PAIRWISE_PLOT_LIMIT = 20000
DEFAULT_CHARS_PER_TOKEN = 4.0
DEFAULT_BATCH_SIZE = 64
DEFAULT_MAX_BATCH_ESTIMATED_TOKENS = 24000
DEFAULT_MAX_INPUT_TOKENS = 7000
DEFAULT_CHUNK_OVERLAP_TOKENS = 256
DEFAULT_RETRY_LIMIT = 6
DEFAULT_RETRY_BASE_SECONDS = 2.0

IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PY_IDENTIFIER_EXACT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
OPENROUTER_INPUT_LIMIT_RE = re.compile(
    r"input\[(?P<input_index>\d+)\].*maximum input length is (?P<max_tokens>\d+) tokens",
    flags=re.IGNORECASE | re.DOTALL,
)

PROTECTED_NAMES = (
    set(keyword.kwlist)
    | set(getattr(keyword, "softkwlist", ()))
    | {"True", "False", "None"}
    | set(dir(builtins))
)
ALLOWED_LIBRARY_ATTRIBUTES = {
    "abs",
    "acos",
    "append",
    "array",
    "asarray",
    "asin",
    "atan",
    "atan2",
    "astype",
    "ceil",
    "choice",
    "clip",
    "copy",
    "copysign",
    "cos",
    "cross",
    "dot",
    "e",
    "exp",
    "extend",
    "fabs",
    "floor",
    "get",
    "hypot",
    "isfinite",
    "items",
    "keys",
    "linalg",
    "log",
    "maximum",
    "mean",
    "minimum",
    "nan_to_num",
    "normal",
    "norm",
    "ones",
    "pi",
    "pop",
    "rand",
    "randn",
    "random",
    "reshape",
    "setdefault",
    "sign",
    "sin",
    "sqrt",
    "std",
    "sum",
    "tan",
    "tolist",
    "uniform",
    "update",
    "values",
    "where",
    "zeros",
}
THEME_STOPWORDS = set(keyword.kwlist) | {
    "action",
    "actions",
    "agent",
    "all",
    "and",
    "array",
    "arrays",
    "axis",
    "board",
    "bot",
    "break",
    "candidate",
    "code",
    "col",
    "cols",
    "count",
    "current",
    "data",
    "dict",
    "done",
    "draw",
    "else",
    "empty",
    "enemy",
    "false",
    "float",
    "from",
    "game",
    "if",
    "import",
    "index",
    "int",
    "is",
    "item",
    "items",
    "key",
    "keys",
    "len",
    "list",
    "logic",
    "loss",
    "math",
    "max",
    "min",
    "move",
    "moves",
    "none",
    "np",
    "numpy",
    "obs",
    "opponent",
    "out",
    "player",
    "players",
    "policy",
    "position",
    "positions",
    "print",
    "python",
    "random",
    "range",
    "result",
    "return",
    "row",
    "rows",
    "score",
    "self",
    "set",
    "shape",
    "state",
    "str",
    "sum",
    "target",
    "temp",
    "tensor",
    "text",
    "theta",
    "torch",
    "true",
    "tuple",
    "type",
    "value",
    "values",
    "vec",
    "vector",
    "vectors",
    "win",
    "winner",
}


@dataclass(frozen=True)
class SampleRecord:
    sample_name: str
    bot_name: str
    parent_name: str
    code_path: str
    raw_code_sha256: str
    raw_code_text: str
    obfuscated_code_sha256: str
    obfuscated_code_text: str
    elo: float
    rank: float
    num_bytes: int
    num_chars: int
    obfuscated_num_chars: int
    obfuscation_stats: dict[str, int]


@dataclass(frozen=True)
class UniqueCodeRecord:
    obfuscated_code_sha256: str
    representative_sample_name: str
    representative_bot_name: str
    representative_parent_name: str
    representative_code_path: str
    representative_raw_code_sha256: str
    representative_raw_code_text: str
    obfuscated_code_text: str
    num_bytes: int
    num_chars: int
    obfuscated_num_chars: int
    duplicate_group_size: int
    sample_names: list[str]
    bot_names: list[str]
    parent_names: list[str]


@dataclass(frozen=True)
class ChunkInstance:
    parent_obfuscated_code_sha256: str
    representative_sample_name: str
    chunk_index: int
    chunk_sha256: str
    text: str
    token_count: int
    num_chars: int


@dataclass(frozen=True)
class AnalysisInput:
    label: str
    game: str
    world: str
    mode: str
    rating_system: str
    sample_rows: list[dict[str, Any]]


class OpenRouterAPIError(RuntimeError):
    def __init__(
        self,
        *,
        code: int | None,
        message: str,
        metadata: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.metadata = metadata
        self.payload = payload
        self.retryable = code in RETRYABLE_API_STATUS_CODES or code is None
        prefix = f"OpenRouter API error {code}" if code is not None else "OpenRouter API error"
        if metadata:
            super().__init__(f"{prefix}: {message} | metadata={json.dumps(metadata, sort_keys=True)}")
        else:
            super().__init__(f"{prefix}: {message}")


class ChunkResplitRequired(RuntimeError):
    def __init__(self, *, resplit_targets: dict[str, int], message: str) -> None:
        super().__init__(message)
        self.resplit_targets = resplit_targets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Obfuscate code, embed via OpenRouter with chunking, cluster it, and compare clusters/embeddings against Elo."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--in-pkl", type=str, help="Pickle produced by experimental/exp_plotting.py gen_pkl.")
    source.add_argument("--match-json", type=str, help="Match JSON file with a top-level 'match_results' list.")

    parser.add_argument("--result-key", type=str, default=None, help="Result key / game label inside the pickle, e.g. '3D TTT'. Required for --in-pkl unless the pickle contains exactly one result.")
    parser.add_argument("--game", type=str, default=None, help="Game id. Required with --match-json.")
    parser.add_argument("--world", type=str, default=None, help="World id. Required with --match-json.")
    parser.add_argument("--mode", choices=["bots", "models"], default="bots", help="Analyze all rated bots or best-per-model entries.")
    parser.add_argument("--rating-system", choices=["bt", "elo"], default="bt", help="Only used with --match-json.")
    parser.add_argument("--out-dir", type=str, default=None, help="Output directory. Default depends on the input source.")

    parser.add_argument("--model", type=str, default=MODEL_DEFAULT, help=f"OpenRouter embedding model to use. Default: {MODEL_DEFAULT}")
    parser.add_argument("--estimate-only", action="store_true", help="Print size/cost estimates and exit before any embedding API calls.")
    parser.add_argument("--chars-per-token", type=float, default=DEFAULT_CHARS_PER_TOKEN, help=f"Fallback chars/token heuristic when tiktoken is unavailable. Default: {DEFAULT_CHARS_PER_TOKEN}")
    parser.add_argument("--max-input-tokens", type=int, default=DEFAULT_MAX_INPUT_TOKENS, help=f"Maximum tokens per embedding chunk. Default: {DEFAULT_MAX_INPUT_TOKENS}")
    parser.add_argument("--chunk-overlap-tokens", type=int, default=DEFAULT_CHUNK_OVERLAP_TOKENS, help=f"Chunk overlap in tokens for long files. Default: {DEFAULT_CHUNK_OVERLAP_TOKENS}")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"Maximum number of chunks per embedding request. Default: {DEFAULT_BATCH_SIZE}")
    parser.add_argument("--max-batch-estimated-tokens", type=int, default=DEFAULT_MAX_BATCH_ESTIMATED_TOKENS, help=f"Upper bound on estimated tokens per embedding request. Default: {DEFAULT_MAX_BATCH_ESTIMATED_TOKENS}")
    parser.add_argument("--retry-limit", type=int, default=DEFAULT_RETRY_LIMIT, help=f"Maximum retries for embedding API calls. Default: {DEFAULT_RETRY_LIMIT}")
    parser.add_argument("--retry-base-seconds", type=float, default=DEFAULT_RETRY_BASE_SECONDS, help=f"Base delay for exponential backoff on retriable API failures. Default: {DEFAULT_RETRY_BASE_SECONDS}")

    parser.add_argument("--n-clusters", type=int, default=None, help="If set, use this many clusters instead of silhouette-based auto selection.")
    parser.add_argument("--k-min", type=int, default=DEFAULT_K_MIN, help=f"Minimum k considered for auto cluster selection. Default: {DEFAULT_K_MIN}")
    parser.add_argument("--k-max", type=int, default=DEFAULT_K_MAX, help=f"Maximum k considered for auto cluster selection. Default: {DEFAULT_K_MAX}")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help=f"Random seed for clustering and plotting. Default: {DEFAULT_RANDOM_SEED}")
    parser.add_argument("--top-theme-terms", type=int, default=DEFAULT_TOP_THEME_TERMS, help=f"Top raw-code identifier terms used to label a cluster. Default: {DEFAULT_TOP_THEME_TERMS}")
    parser.add_argument("--pairwise-plot-limit", type=int, default=DEFAULT_PAIRWISE_PLOT_LIMIT, help=f"Maximum number of pairwise points to render in the scatter plot. Default: {DEFAULT_PAIRWISE_PLOT_LIMIT}")
    parser.add_argument("--cluster-labels-json", type=str, default=None, help="Optional JSON mapping cluster ids to {'name', 'detail'} entries for plots.")
    parser.add_argument("--legend-panel", action="store_true", help="Draw a right-side legend panel in the model-colored cluster plot.")
    parser.add_argument("--clear-out-dir", action="store_true", help="Delete the output directory before running. Use carefully; this also clears embedding checkpoints.")

    args = parser.parse_args()
    if args.in_pkl is None and (not args.game or not args.world):
        parser.error("--game and --world are required with --match-json.")
    if args.chars_per_token <= 0:
        parser.error("--chars-per-token must be positive.")
    if args.max_input_tokens <= 0:
        parser.error("--max-input-tokens must be positive.")
    if args.chunk_overlap_tokens < 0:
        parser.error("--chunk-overlap-tokens cannot be negative.")
    if args.chunk_overlap_tokens >= args.max_input_tokens:
        parser.error("--chunk-overlap-tokens must be smaller than --max-input-tokens.")
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive.")
    if args.max_batch_estimated_tokens <= 0:
        parser.error("--max-batch-estimated-tokens must be positive.")
    if args.retry_limit <= 0:
        parser.error("--retry-limit must be positive.")
    if args.retry_base_seconds <= 0:
        parser.error("--retry-base-seconds must be positive.")
    if args.n_clusters is not None and args.n_clusters <= 0:
        parser.error("--n-clusters must be positive.")
    if args.k_min <= 0 or args.k_max <= 0:
        parser.error("--k-min and --k-max must be positive.")
    if args.k_min > args.k_max:
        parser.error("--k-min cannot exceed --k-max.")
    if args.top_theme_terms <= 0:
        parser.error("--top-theme-terms must be positive.")
    if args.pairwise_plot_limit <= 0:
        parser.error("--pairwise-plot-limit must be positive.")
    return args


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if path.is_absolute():
        return path
    candidates = [Path.cwd() / path, REPO_ROOT / path, SRC_ROOT / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (Path.cwd() / path).resolve()


def _sanitize_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return slug.strip("._-") or "analysis"


def _default_out_dir(args: argparse.Namespace, analysis_input: AnalysisInput) -> Path:
    stem = _sanitize_slug(f"{analysis_input.label}_{analysis_input.mode}")
    if args.in_pkl is not None:
        pkl_path = _resolve_path(args.in_pkl)
        return pkl_path.parent / f"{pkl_path.stem}_cluster_code" / stem
    match_path = _resolve_path(args.match_json)
    return match_path.parent / f"{match_path.stem}_cluster_code" / stem


def _normalize_openrouter_model(model: str) -> str:
    return OPENROUTER_MODEL_ALIASES.get(model, model)


def _tiktoken_model_name(model: str) -> str:
    if model.startswith("openai/"):
        return model.split("/", 1)[1]
    return model


def _load_tiktoken_encoder(model: str) -> Any | None:
    try:
        import tiktoken
    except ImportError:
        return None
    model_name = _tiktoken_model_name(model)
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def _estimate_tokens(text: str, encoder: Any | None, chars_per_token: float) -> int:
    if encoder is not None:
        return len(encoder.encode(text))
    return max(1, int(math.ceil(len(text) / chars_per_token)))


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, float) and math.isfinite(value):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None
    if isinstance(value, str):
        try:
            numeric = float(value.strip())
        except ValueError:
            return None
        return numeric if math.isfinite(numeric) else None
    return None


def _load_json_bytes(raw_bytes: bytes) -> dict[str, Any] | None:
    if not raw_bytes:
        return None
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _openrouter_error_from_payload(
    payload: dict[str, Any],
    *,
    fallback_status_code: int | None = None,
) -> OpenRouterAPIError | None:
    error = payload.get("error")
    if not isinstance(error, dict):
        return None
    return OpenRouterAPIError(
        code=_int_or_none(error.get("code")) or fallback_status_code,
        message=str(error.get("message") or "Unknown OpenRouter error"),
        metadata=error.get("metadata") if isinstance(error.get("metadata"), dict) else None,
        payload=payload,
    )


def _estimate_provider_costs(model: str, token_count: int) -> tuple[float | None, float | None]:
    normalized_model = _normalize_openrouter_model(model)
    price = EMBEDDING_PRICE_PER_1M_TOKENS_USD_BY_MODEL.get(normalized_model)
    if price is None:
        return None, None
    return price, (token_count / 1_000_000.0) * price


def _load_pickle_payload(pkl_path: Path) -> dict[str, Any]:
    with pkl_path.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pickle payload in {pkl_path}: expected dict.")
    return payload


def _ratings_from_leaderboard_df(leaderboard_df: Any) -> pd.Series:
    if not isinstance(leaderboard_df, pd.DataFrame) or "rating" not in leaderboard_df.columns:
        raise ValueError("Result is missing leaderboard_table_df['rating'].")
    ratings = pd.to_numeric(leaderboard_df["rating"], errors="coerce").dropna()
    if ratings.empty:
        raise ValueError("Leaderboard rating series is empty.")
    return ratings.sort_values(ascending=False)


def _top_bot_map_from_ratings(ratings: pd.Series) -> dict[str, str]:
    rows: list[tuple[str, str, float]] = []
    for name, rating in ratings.items():
        if not isinstance(name, str):
            continue
        rows.append((name.split("/")[0], name, float(rating)))
    rows.sort(key=lambda row: (row[0], -row[2], row[1]))
    top_map: dict[str, str] = {}
    for parent_name, bot_name, _ in rows:
        top_map.setdefault(parent_name, bot_name)
    return top_map


def _load_from_pkl(pkl_path: Path, result_key: str | None, mode: str) -> AnalysisInput:
    payload = _load_pickle_payload(pkl_path)
    results_key = "results_bots" if mode == "bots" else "results_models"
    results = payload.get(results_key)
    if not isinstance(results, dict) or not results:
        raise ValueError(f"Pickle does not contain a non-empty '{results_key}' mapping.")

    if result_key is None:
        if len(results) == 1:
            result_key = next(iter(results))
        else:
            available = ", ".join(sorted(map(str, results.keys())))
            raise ValueError(f"--result-key is required. Available keys: {available}")
    if result_key not in results:
        available = ", ".join(sorted(map(str, results.keys())))
        raise KeyError(f"Result key '{result_key}' not found in '{results_key}'. Available keys: {available}")

    run_map: dict[str, tuple[str, str]] = {}
    for item in payload.get("runs", []):
        if isinstance(item, (tuple, list)) and len(item) >= 3:
            run_map[str(item[2])] = (str(item[0]), str(item[1]))
    if result_key not in run_map:
        raise KeyError(f"Could not resolve game/world metadata for result key '{result_key}'.")

    result = results[result_key]
    if not isinstance(result, dict):
        raise ValueError(f"Result '{result_key}' has invalid type {type(result).__name__}; expected dict.")

    ratings = _ratings_from_leaderboard_df(result.get("leaderboard_table_df"))
    ranks = ratings.rank(ascending=False, method="average")

    sample_rows: list[dict[str, Any]] = []
    if mode == "bots":
        for sample_name, elo in ratings.items():
            sample_name = str(sample_name)
            sample_rows.append(
                {
                    "sample_name": sample_name,
                    "bot_name": sample_name,
                    "parent_name": sample_name.split("/")[0],
                    "elo": float(elo),
                    "rank": float(ranks.loc[sample_name]),
                }
            )
    else:
        top_map = result.get("top_bots_per_model")
        if not isinstance(top_map, dict) or not top_map:
            bots_result = payload.get("results_bots", {}).get(result_key, {})
            bots_ratings = _ratings_from_leaderboard_df(bots_result.get("leaderboard_table_df"))
            top_map = _top_bot_map_from_ratings(bots_ratings)
        for sample_name, elo in ratings.items():
            sample_name = str(sample_name)
            bot_name = top_map.get(sample_name)
            if not isinstance(bot_name, str) or not bot_name:
                warnings.warn(f"Skipping model '{sample_name}': missing top bot mapping.")
                continue
            sample_rows.append(
                {
                    "sample_name": sample_name,
                    "bot_name": bot_name,
                    "parent_name": sample_name,
                    "elo": float(elo),
                    "rank": float(ranks.loc[sample_name]),
                }
            )

    config = payload.get("config", {})
    game, world = run_map[result_key]
    return AnalysisInput(
        label=str(result_key),
        game=game,
        world=world,
        mode=mode,
        rating_system=str(config.get("rating_system", "unknown")),
        sample_rows=sample_rows,
    )


def _timeout_winner_from_time_analysis(time_analysis: dict[str, Any]) -> int:
    for key in ("winner", "winner_idx", "winner_index"):
        value = time_analysis.get(key)
        if value in (0, 1):
            return int(value)
    raise ValueError(f"Could not infer timeout winner from time_analysis keys: {list(time_analysis.keys())}")


def _winner_label_from_match(match: dict[str, Any]) -> str:
    done = bool(match.get("done"))
    winner = match.get("winner")
    match_r = match.get("r")
    if done and winner is not None:
        if winner == 0:
            return "model_a"
        if winner == 1:
            return "model_b"
        raise ValueError(f"Unexpected finished winner value: {winner!r}")
    if done and winner is None:
        return "tie"
    if winner == "error" and isinstance(match_r, dict):
        err_counts = match_r.get("player_err_counts")
        if isinstance(err_counts, list) and set(err_counts) == {0, 1}:
            winner_idx = err_counts.index(0)
            return "model_a" if winner_idx == 0 else "model_b"
    if winner == "timeout":
        timeout_hit = match.get("timeout_hit")
        if isinstance(timeout_hit, (list, tuple)) and timeout_hit:
            loser_idx = int(timeout_hit[0])
            winner_idx = 1 - loser_idx
            return "model_a" if winner_idx == 0 else "model_b"
        time_analysis = match.get("time_analysis")
        if isinstance(time_analysis, dict):
            winner_idx = _timeout_winner_from_time_analysis(time_analysis)
            return "model_a" if winner_idx == 0 else "model_b"
    raise ValueError(f"Could not infer match outcome for entry: {match}")


def _build_battles(
    match_results: list[dict[str, Any]],
    *,
    collapse_to_parent: bool,
    allowed_bots: set[str] | None = None,
) -> list[dict[str, Any]]:
    battles: list[dict[str, Any]] = []
    for match in match_results:
        if not isinstance(match, dict):
            continue
        bot_a = str(match.get("name0"))
        bot_b = str(match.get("name1"))
        if allowed_bots is not None and (bot_a not in allowed_bots or bot_b not in allowed_bots):
            continue
        model_a = bot_a.split("/")[0] if collapse_to_parent else bot_a
        model_b = bot_b.split("/")[0] if collapse_to_parent else bot_b
        battles.append(
            {
                "model_a": model_a,
                "model_b": model_b,
                "winner": _winner_label_from_match(match),
            }
        )
    return battles


def _compute_ratings_from_battles(battles: list[dict[str, Any]], rating_system: str) -> pd.Series:
    if not battles:
        raise ValueError("No battles available after filtering.")
    from experimental.lm_arena.rating_systems import compute_bt, compute_elo

    frame = pd.DataFrame(battles)
    if rating_system == "bt":
        ratings = compute_bt(frame)
    elif rating_system == "elo":
        ratings = pd.Series(compute_elo(frame)).sort_values(ascending=False)
    else:
        raise ValueError(f"Unsupported rating system: {rating_system}")
    return pd.to_numeric(ratings, errors="coerce").dropna().sort_values(ascending=False)


def _load_from_match_json(match_json_path: Path, game: str, world: str, mode: str, rating_system: str) -> AnalysisInput:
    with match_json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid match JSON in {match_json_path}: expected dict.")
    match_results = payload.get("match_results")
    if not isinstance(match_results, list):
        raise ValueError(f"Invalid match JSON in {match_json_path}: missing list key 'match_results'.")

    bot_battles = _build_battles(match_results, collapse_to_parent=False)
    bot_ratings = _compute_ratings_from_battles(bot_battles, rating_system)

    if mode == "bots":
        ratings = bot_ratings
        ranks = ratings.rank(ascending=False, method="average")
        sample_rows = [
            {
                "sample_name": str(bot_name),
                "bot_name": str(bot_name),
                "parent_name": str(bot_name).split("/")[0],
                "elo": float(elo),
                "rank": float(ranks.loc[bot_name]),
            }
            for bot_name, elo in ratings.items()
        ]
    else:
        top_map = _top_bot_map_from_ratings(bot_ratings)
        filtered = _build_battles(match_results, collapse_to_parent=True, allowed_bots=set(top_map.values()))
        ratings = _compute_ratings_from_battles(filtered, rating_system)
        ranks = ratings.rank(ascending=False, method="average")
        sample_rows = []
        for model_name, elo in ratings.items():
            model_name = str(model_name)
            bot_name = top_map.get(model_name)
            if bot_name is None:
                continue
            sample_rows.append(
                {
                    "sample_name": model_name,
                    "bot_name": bot_name,
                    "parent_name": model_name,
                    "elo": float(elo),
                    "rank": float(ranks.loc[model_name]),
                }
            )

    return AnalysisInput(
        label=f"{game}_{world}",
        game=game,
        world=world,
        mode=mode,
        rating_system=rating_system,
        sample_rows=sample_rows,
    )


def _code_path_for_bot(game: str, world: str, bot_name: str) -> Path:
    return GAME_ARENA_ROOT / game / "examples" / world / bot_name / "2.python_code.py"


def _docstring_starts(source: str) -> set[tuple[int, int]]:
    starts: set[tuple[int, int]] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return starts
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(getattr(first, "value", None), ast.Constant)
            and isinstance(first.value.value, str)
        ):
            starts.add((first.lineno, first.col_offset))
    return starts


def _should_remember_as_significant(token_type: int) -> bool:
    return token_type not in {
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }


def _obfuscate_python(source: str) -> tuple[str, dict[str, int]]:
    doc_starts = _docstring_starts(source)
    name_map: dict[str, str] = {}
    string_map: dict[str, str] = {}
    attr_map: dict[str, str] = {}
    counters = {
        "comments_removed": 0,
        "docstrings_removed": 0,
        "names_obfuscated": 0,
        "strings_obfuscated": 0,
        "attributes_obfuscated": 0,
    }
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return source, counters

    result: list[tokenize.TokenInfo] = []
    prev_significant: tokenize.TokenInfo | None = None
    for token in tokens:
        token_type, text, start, end, line = token
        if token_type == tokenize.COMMENT:
            counters["comments_removed"] += 1
            continue
        if token_type == tokenize.STRING and start in doc_starts:
            counters["docstrings_removed"] += 1
            continue

        new_text = text
        prev_text = prev_significant.string if prev_significant else ""
        if token_type == tokenize.NAME and text not in PROTECTED_NAMES:
            if prev_text == ".":
                if text not in ALLOWED_LIBRARY_ATTRIBUTES:
                    if text not in attr_map:
                        attr_map[text] = f"a{len(attr_map)}"
                    new_text = attr_map[text]
            else:
                if text not in name_map:
                    name_map[text] = f"n{len(name_map)}"
                new_text = name_map[text]
        elif token_type == tokenize.STRING:
            try:
                value = ast.literal_eval(text)
            except Exception:
                value = None
            if isinstance(value, str) and value:
                if value not in string_map:
                    string_map[value] = f"s{len(string_map)}"
                new_text = repr(string_map[value])

        new_token = tokenize.TokenInfo(token_type, new_text, start, end, line)
        result.append(new_token)
        if _should_remember_as_significant(token_type):
            prev_significant = new_token

    counters["names_obfuscated"] = len(name_map)
    counters["strings_obfuscated"] = len(string_map)
    counters["attributes_obfuscated"] = len(attr_map)
    return tokenize.untokenize(result), counters


def _load_sample_records(analysis_input: AnalysisInput) -> list[SampleRecord]:
    sample_records: list[SampleRecord] = []
    missing_code: list[str] = []
    for row in analysis_input.sample_rows:
        sample_name = str(row["sample_name"])
        bot_name = str(row["bot_name"])
        code_path = _code_path_for_bot(analysis_input.game, analysis_input.world, bot_name)
        if not code_path.exists():
            missing_code.append(f"{sample_name} -> {code_path}")
            continue
        payload = code_path.read_bytes()
        raw_text = payload.decode("utf-8", errors="replace")
        obfuscated_text, obfuscation_stats = _obfuscate_python(raw_text)
        sample_records.append(
            SampleRecord(
                sample_name=sample_name,
                bot_name=bot_name,
                parent_name=str(row["parent_name"]),
                code_path=str(code_path),
                raw_code_sha256=hashlib.sha256(payload).hexdigest(),
                raw_code_text=raw_text,
                obfuscated_code_sha256=hashlib.sha256(obfuscated_text.encode("utf-8")).hexdigest(),
                obfuscated_code_text=obfuscated_text,
                elo=float(row["elo"]),
                rank=float(row["rank"]),
                num_bytes=len(payload),
                num_chars=len(raw_text),
                obfuscated_num_chars=len(obfuscated_text),
                obfuscation_stats=obfuscation_stats,
            )
        )
    for item in missing_code[:10]:
        warnings.warn(f"Missing code file; skipping sample: {item}")
    if len(missing_code) > 10:
        warnings.warn(f"Skipped {len(missing_code) - 10} additional samples with missing code files.")
    if not sample_records:
        raise ValueError("No rated samples had readable code files.")
    return sample_records


def _build_unique_records(sample_records: list[SampleRecord]) -> list[UniqueCodeRecord]:
    groups: dict[str, list[SampleRecord]] = defaultdict(list)
    for record in sample_records:
        groups[record.obfuscated_code_sha256].append(record)

    unique_records: list[UniqueCodeRecord] = []
    for obfuscated_code_sha256, members in groups.items():
        members_sorted = sorted(members, key=lambda record: (record.sample_name, record.bot_name))
        rep = members_sorted[0]
        unique_records.append(
            UniqueCodeRecord(
                obfuscated_code_sha256=obfuscated_code_sha256,
                representative_sample_name=rep.sample_name,
                representative_bot_name=rep.bot_name,
                representative_parent_name=rep.parent_name,
                representative_code_path=rep.code_path,
                representative_raw_code_sha256=rep.raw_code_sha256,
                representative_raw_code_text=rep.raw_code_text,
                obfuscated_code_text=rep.obfuscated_code_text,
                num_bytes=rep.num_bytes,
                num_chars=rep.num_chars,
                obfuscated_num_chars=rep.obfuscated_num_chars,
                duplicate_group_size=len(members_sorted),
                sample_names=[record.sample_name for record in members_sorted],
                bot_names=[record.bot_name for record in members_sorted],
                parent_names=sorted({record.parent_name for record in members_sorted}),
            )
        )
    unique_records.sort(key=lambda record: record.representative_sample_name)
    return unique_records


def _chunk_text_exact_tokens(
    text: str,
    *,
    encoder: Any,
    max_input_tokens: int,
    chunk_overlap_tokens: int,
) -> list[tuple[str, int]]:
    token_ids = encoder.encode(text)
    if not token_ids:
        return [("", 1)]
    if len(token_ids) <= max_input_tokens:
        return [(text, len(token_ids))]
    chunks: list[tuple[str, int]] = []
    step = max_input_tokens - chunk_overlap_tokens
    start = 0
    while start < len(token_ids):
        end = min(len(token_ids), start + max_input_tokens)
        chunk_ids = token_ids[start:end]
        chunks.append((encoder.decode(chunk_ids), len(chunk_ids)))
        if end >= len(token_ids):
            break
        start += step
    return chunks


def _chunk_text_fallback_chars(
    text: str,
    *,
    chars_per_token: float,
    max_input_tokens: int,
    chunk_overlap_tokens: int,
) -> list[tuple[str, int]]:
    max_chars = max(1, int(max_input_tokens * chars_per_token))
    overlap_chars = max(0, int(chunk_overlap_tokens * chars_per_token))
    if len(text) <= max_chars:
        return [(text, max(1, int(math.ceil(len(text) / chars_per_token))))]
    step = max(1, max_chars - overlap_chars)
    chunks: list[tuple[str, int]] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunk_text = text[start:end]
        token_count = max(1, int(math.ceil(len(chunk_text) / chars_per_token)))
        chunks.append((chunk_text, token_count))
        if end >= len(text):
            break
        start += step
    return chunks


def _forced_resplit_target_max_tokens(
    *,
    max_input_tokens: int,
    provider_limit_tokens: int,
) -> int:
    candidate = int(math.floor(provider_limit_tokens * OVERSIZE_RETRY_TOKEN_FRACTION))
    return max(MIN_FORCED_RESPLIT_TOKENS, min(max_input_tokens - 1, candidate))


def _parse_openrouter_input_limit_error(message: str) -> tuple[int | None, int | None] | None:
    match = OPENROUTER_INPUT_LIMIT_RE.search(message)
    if not match:
        return None
    input_index = _int_or_none(match.group("input_index"))
    max_tokens = _int_or_none(match.group("max_tokens"))
    return input_index, max_tokens


def _resplit_chunk_payloads(
    chunk_text: str,
    *,
    chunk_overlap_tokens: int,
    target_max_tokens: int,
) -> list[tuple[str, int]]:
    overlap = min(chunk_overlap_tokens, max(0, target_max_tokens // 4))
    return _chunk_text_fallback_chars(
        chunk_text,
        chars_per_token=FORCED_RESPLIT_CHARS_PER_TOKEN,
        max_input_tokens=target_max_tokens,
        chunk_overlap_tokens=overlap,
    )


def _build_chunk_instances(
    unique_records: list[UniqueCodeRecord],
    *,
    encoder: Any | None,
    chars_per_token: float,
    max_input_tokens: int,
    chunk_overlap_tokens: int,
    forced_resplit_targets: dict[str, int] | None = None,
) -> tuple[list[ChunkInstance], dict[str, list[ChunkInstance]], dict[str, int]]:
    chunk_instances: list[ChunkInstance] = []
    chunks_by_code_sha: dict[str, list[ChunkInstance]] = {}
    estimated_tokens_by_chunk_sha: dict[str, int] = {}
    forced_resplit_targets = forced_resplit_targets or {}

    for record in unique_records:
        if encoder is not None:
            chunk_payloads = _chunk_text_exact_tokens(
                record.obfuscated_code_text,
                encoder=encoder,
                max_input_tokens=max_input_tokens,
                chunk_overlap_tokens=chunk_overlap_tokens,
            )
        else:
            chunk_payloads = _chunk_text_fallback_chars(
                record.obfuscated_code_text,
                chars_per_token=chars_per_token,
                max_input_tokens=max_input_tokens,
                chunk_overlap_tokens=chunk_overlap_tokens,
            )

        normalized_chunk_payloads: list[tuple[str, int]] = []
        for chunk_text, token_count in chunk_payloads:
            chunk_sha256 = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            forced_target = forced_resplit_targets.get(chunk_sha256)
            if forced_target is None:
                normalized_chunk_payloads.append((chunk_text, int(token_count)))
                continue
            child_payloads = _resplit_chunk_payloads(
                chunk_text,
                chunk_overlap_tokens=chunk_overlap_tokens,
                target_max_tokens=forced_target,
            )
            if len(child_payloads) <= 1:
                normalized_chunk_payloads.append((chunk_text, int(token_count)))
                continue
            normalized_chunk_payloads.extend(child_payloads)

        per_doc_chunks: list[ChunkInstance] = []
        for chunk_index, (chunk_text, token_count) in enumerate(normalized_chunk_payloads):
            chunk_sha256 = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            estimated_tokens_by_chunk_sha.setdefault(chunk_sha256, int(token_count))
            instance = ChunkInstance(
                parent_obfuscated_code_sha256=record.obfuscated_code_sha256,
                representative_sample_name=record.representative_sample_name,
                chunk_index=chunk_index,
                chunk_sha256=chunk_sha256,
                text=chunk_text,
                token_count=int(token_count),
                num_chars=len(chunk_text),
            )
            chunk_instances.append(instance)
            per_doc_chunks.append(instance)
        chunks_by_code_sha[record.obfuscated_code_sha256] = per_doc_chunks

    return chunk_instances, chunks_by_code_sha, estimated_tokens_by_chunk_sha


def _summarize_corpus(
    sample_records: list[SampleRecord],
    unique_records: list[UniqueCodeRecord],
    chunk_instances: list[ChunkInstance],
    estimated_tokens_by_chunk_sha: dict[str, int],
    *,
    model: str,
    out_dir: Path,
) -> dict[str, Any]:
    unique_chunk_instances: dict[str, ChunkInstance] = {}
    for instance in chunk_instances:
        unique_chunk_instances.setdefault(instance.chunk_sha256, instance)

    total_sample_raw_chars = int(sum(record.num_chars for record in sample_records))
    total_sample_obfuscated_chars = int(sum(record.obfuscated_num_chars for record in sample_records))
    total_unique_raw_chars = int(sum(record.num_chars for record in unique_records))
    total_unique_obfuscated_chars = int(sum(record.obfuscated_num_chars for record in unique_records))

    total_unique_chunk_tokens = int(sum(estimated_tokens_by_chunk_sha.values()))
    price_per_million, estimated_cost = _estimate_provider_costs(model, total_unique_chunk_tokens)
    largest_code = max(unique_records, key=lambda record: record.obfuscated_num_chars)
    largest_chunk = max(unique_chunk_instances.values(), key=lambda item: item.token_count)

    return {
        "output_dir": str(out_dir),
        "embedding_provider": OPENROUTER_PROVIDER,
        "embedding_model": model,
        "sample_count": len(sample_records),
        "unique_code_count": len(unique_records),
        "duplicate_sample_count": len(sample_records) - len(unique_records),
        "chunk_count": len(chunk_instances),
        "unique_chunk_count": len(unique_chunk_instances),
        "total_sample_raw_chars": total_sample_raw_chars,
        "total_sample_obfuscated_chars": total_sample_obfuscated_chars,
        "total_unique_raw_chars": total_unique_raw_chars,
        "total_unique_obfuscated_chars": total_unique_obfuscated_chars,
        "total_unique_chunk_estimated_tokens": total_unique_chunk_tokens,
        "price_per_1m_tokens_usd": price_per_million,
        "estimated_cost_usd": estimated_cost,
        "largest_unique_code": {
            "sample_name": largest_code.representative_sample_name,
            "obfuscated_chars": int(largest_code.obfuscated_num_chars),
            "raw_chars": int(largest_code.num_chars),
            "chunk_count": int(sum(1 for item in chunk_instances if item.parent_obfuscated_code_sha256 == largest_code.obfuscated_code_sha256)),
        },
        "largest_chunk": {
            "sample_name": largest_chunk.representative_sample_name,
            "estimated_tokens": int(largest_chunk.token_count),
            "num_chars": int(largest_chunk.num_chars),
        },
        "obfuscation_totals": {
            "comments_removed": int(sum(record.obfuscation_stats.get("comments_removed", 0) for record in sample_records)),
            "docstrings_removed": int(sum(record.obfuscation_stats.get("docstrings_removed", 0) for record in sample_records)),
            "names_obfuscated": int(sum(record.obfuscation_stats.get("names_obfuscated", 0) for record in sample_records)),
            "strings_obfuscated": int(sum(record.obfuscation_stats.get("strings_obfuscated", 0) for record in sample_records)),
            "attributes_obfuscated": int(sum(record.obfuscation_stats.get("attributes_obfuscated", 0) for record in sample_records)),
        },
    }


def _print_corpus_summary(summary: dict[str, Any]) -> None:
    print(f"Embedding provider: {summary['embedding_provider']}")
    print(f"Embedding model: {summary['embedding_model']}")
    print(
        "Samples: "
        f"{summary['sample_count']} rated entries, "
        f"{summary['unique_code_count']} unique obfuscated code blobs, "
        f"{summary['duplicate_sample_count']} duplicates"
    )
    print(
        "Chunks: "
        f"{summary['chunk_count']} total chunks, "
        f"{summary['unique_chunk_count']} unique chunks"
    )
    print(
        "Corpus size: "
        f"{summary['total_sample_raw_chars']:,} raw chars -> "
        f"{summary['total_sample_obfuscated_chars']:,} obfuscated chars across rated entries"
    )
    print(
        "Unique size: "
        f"{summary['total_unique_raw_chars']:,} raw chars -> "
        f"{summary['total_unique_obfuscated_chars']:,} obfuscated chars after exact-obfuscated dedupe"
    )
    print(
        "Estimated tokens: "
        f"{summary['total_unique_chunk_estimated_tokens']:,} unique chunk tokens"
    )
    if summary["estimated_cost_usd"] is not None:
        print(
            "Estimated embedding cost: "
            f"${summary['estimated_cost_usd']:.6f} "
            f"(@ ${summary['price_per_1m_tokens_usd']:.2f} / 1M tokens)"
        )
    else:
        print("Estimated embedding cost: unavailable for this model.")
    largest_code = summary["largest_unique_code"]
    print(
        "Largest unique obfuscated code: "
        f"{largest_code['obfuscated_chars']:,} chars, "
        f"{largest_code['chunk_count']} chunks, "
        f"{largest_code['sample_name']}"
    )
    largest_chunk = summary["largest_chunk"]
    print(
        "Largest chunk: "
        f"{largest_chunk['estimated_tokens']:,} est. tokens, "
        f"{largest_chunk['num_chars']:,} chars, "
        f"{largest_chunk['sample_name']}"
    )


def _embedding_checkpoint_paths(out_dir: Path) -> tuple[Path, Path]:
    return out_dir / EMBEDDING_CHECKPOINT_FILENAME, out_dir / EMBEDDING_PROGRESS_FILENAME


def _save_embedding_checkpoint(
    out_dir: Path,
    *,
    model: str,
    chunk_order: list[str],
    embeddings_by_chunk_sha: dict[str, np.ndarray],
) -> None:
    checkpoint_path, _ = _embedding_checkpoint_paths(out_dir)
    ordered_chunk_shas = [chunk_sha for chunk_sha in chunk_order if chunk_sha in embeddings_by_chunk_sha]
    if not ordered_chunk_shas:
        return
    tmp_path = checkpoint_path.with_suffix(".tmp.npz")
    np.savez_compressed(
        tmp_path,
        model=np.asarray(model),
        chunk_sha256=np.asarray(ordered_chunk_shas, dtype=str),
        embeddings=np.vstack(
            [np.asarray(embeddings_by_chunk_sha[chunk_sha], dtype=np.float32) for chunk_sha in ordered_chunk_shas]
        ).astype(np.float32, copy=False),
    )
    tmp_path.replace(checkpoint_path)


def _load_embedding_checkpoint(out_dir: Path, *, model: str) -> dict[str, np.ndarray]:
    checkpoint_path, _ = _embedding_checkpoint_paths(out_dir)
    if not checkpoint_path.exists():
        return {}
    try:
        with np.load(checkpoint_path, allow_pickle=False) as payload:
            checkpoint_model = str(payload["model"].item()) if "model" in payload.files else None
            if checkpoint_model not in {None, model}:
                warnings.warn(
                    f"Ignoring embedding checkpoint for model {checkpoint_model!r}; current model is {model!r}."
                )
                return {}
            if "chunk_sha256" not in payload.files or "embeddings" not in payload.files:
                warnings.warn(f"Ignoring invalid embedding checkpoint: {checkpoint_path}")
                return {}
            chunk_shas = [str(item) for item in payload["chunk_sha256"].tolist()]
            embeddings = np.asarray(payload["embeddings"], dtype=np.float32)
    except Exception as exc:
        warnings.warn(f"Could not load embedding checkpoint {checkpoint_path}: {exc}")
        return {}
    if embeddings.ndim != 2 or embeddings.shape[0] != len(chunk_shas):
        warnings.warn(f"Ignoring malformed embedding checkpoint: {checkpoint_path}")
        return {}
    return {
        chunk_sha: embeddings[idx].astype(np.float32, copy=False)
        for idx, chunk_sha in enumerate(chunk_shas)
    }


def _load_embedding_usage_progress(out_dir: Path, *, model: str) -> list[dict[str, Any]]:
    _, progress_path = _embedding_checkpoint_paths(out_dir)
    if not progress_path.exists():
        return []
    try:
        with progress_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        warnings.warn(f"Could not load embedding progress {progress_path}: {exc}")
        return []
    if not isinstance(payload, dict):
        return []
    progress_model = payload.get("model")
    if progress_model not in {None, model}:
        return []
    usage_rows = payload.get("usage_by_batch")
    if not isinstance(usage_rows, list):
        return []
    return [row for row in usage_rows if isinstance(row, dict)]


def _load_forced_resplit_targets_from_progress(
    out_dir: Path,
    *,
    model: str,
    max_input_tokens: int,
) -> dict[str, int]:
    _, progress_path = _embedding_checkpoint_paths(out_dir)
    if not progress_path.exists():
        return {}
    try:
        with progress_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("model") not in {None, model}:
        return {}
    last_error = payload.get("last_error")
    if not isinstance(last_error, dict):
        return {}
    parsed = _parse_openrouter_input_limit_error(str(last_error.get("message", "")))
    if parsed is None:
        return {}
    input_index, provider_limit = parsed
    chunk_sha256 = last_error.get("chunk_sha256")
    if not isinstance(chunk_sha256, list):
        return {}
    if input_index is None or input_index < 0 or input_index >= len(chunk_sha256):
        return {}
    offending_chunk_sha = str(chunk_sha256[input_index])
    if provider_limit is None:
        provider_limit = OPENROUTER_EMBEDDING_INPUT_TOKEN_LIMIT
    return {
        offending_chunk_sha: _forced_resplit_target_max_tokens(
            max_input_tokens=max_input_tokens,
            provider_limit_tokens=provider_limit,
        )
    }


def _write_embedding_progress(
    out_dir: Path,
    *,
    model: str,
    unique_chunk_shas: list[str],
    estimated_tokens_by_chunk_sha: dict[str, int],
    embeddings_by_chunk_sha: dict[str, np.ndarray],
    usage_by_batch: list[dict[str, Any]],
    last_error: dict[str, Any] | None = None,
) -> None:
    _, progress_path = _embedding_checkpoint_paths(out_dir)
    completed_shas = [chunk_sha for chunk_sha in unique_chunk_shas if chunk_sha in embeddings_by_chunk_sha]
    completed_estimated_tokens = int(sum(estimated_tokens_by_chunk_sha.get(chunk_sha, 0) for chunk_sha in completed_shas))
    total_estimated_tokens = int(sum(estimated_tokens_by_chunk_sha.get(chunk_sha, 0) for chunk_sha in unique_chunk_shas))

    prompt_tokens_total = 0
    total_tokens_total = 0
    cost_total = 0.0
    has_prompt_tokens = False
    has_total_tokens = False
    has_cost = False
    for row in usage_by_batch:
        prompt_tokens = _int_or_none(row.get("prompt_tokens"))
        total_tokens = _int_or_none(row.get("total_tokens"))
        cost = _float_or_none(row.get("cost"))
        if prompt_tokens is not None:
            prompt_tokens_total += prompt_tokens
            has_prompt_tokens = True
        if total_tokens is not None:
            total_tokens_total += total_tokens
            has_total_tokens = True
        if cost is not None:
            cost_total += cost
            has_cost = True

    payload = {
        "provider": OPENROUTER_PROVIDER,
        "model": model,
        "total_unique_chunk_count": len(unique_chunk_shas),
        "completed_unique_chunk_count": len(completed_shas),
        "remaining_unique_chunk_count": len(unique_chunk_shas) - len(completed_shas),
        "total_estimated_tokens": total_estimated_tokens,
        "completed_estimated_tokens": completed_estimated_tokens,
        "remaining_estimated_tokens": total_estimated_tokens - completed_estimated_tokens,
        "completed_chunk_sha256": completed_shas,
        "usage_by_batch": usage_by_batch,
        "usage_totals": {
            "prompt_tokens": prompt_tokens_total if has_prompt_tokens else None,
            "total_tokens": total_tokens_total if has_total_tokens else None,
            "cost": cost_total if has_cost else None,
        },
        "last_error": last_error,
        "checkpoint_file": str(_embedding_checkpoint_paths(out_dir)[0]),
    }
    tmp_path = progress_path.with_suffix(".tmp.json")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    tmp_path.replace(progress_path)


def _embedding_error_payload(
    exc: Exception,
    *,
    batch_index: int,
    batch_count: int,
    token_total: int,
    batch_instances: list[ChunkInstance],
) -> dict[str, Any]:
    payload = {
        "batch_index": int(batch_index),
        "batch_count": int(batch_count),
        "estimated_tokens": int(token_total),
        "sample_names": [instance.representative_sample_name for instance in batch_instances],
        "chunk_sha256": [instance.chunk_sha256 for instance in batch_instances],
        "exception_type": exc.__class__.__name__,
        "message": str(exc),
    }
    if isinstance(exc, OpenRouterAPIError):
        payload["openrouter_code"] = exc.code
        if exc.metadata:
            payload["openrouter_metadata"] = exc.metadata
    elif isinstance(exc, urllib.error.HTTPError):
        payload["http_status"] = int(exc.code)
    return payload


def _is_retryable_http_error(exc: Exception) -> bool:
    if isinstance(exc, OpenRouterAPIError):
        return exc.retryable
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in RETRYABLE_API_STATUS_CODES
    return isinstance(exc, (urllib.error.URLError, TimeoutError))


def _iter_batches(
    chunk_instances: list[ChunkInstance],
    estimated_tokens_by_chunk_sha: dict[str, int],
    *,
    batch_size: int,
    max_batch_estimated_tokens: int,
) -> list[list[ChunkInstance]]:
    batches: list[list[ChunkInstance]] = []
    batch: list[ChunkInstance] = []
    batch_token_total = 0
    for instance in chunk_instances:
        estimated_tokens = int(estimated_tokens_by_chunk_sha[instance.chunk_sha256])
        would_overflow = bool(
            batch
            and (
                len(batch) >= batch_size
                or batch_token_total + estimated_tokens > max_batch_estimated_tokens
            )
        )
        if would_overflow:
            batches.append(batch)
            batch = []
            batch_token_total = 0
        batch.append(instance)
        batch_token_total += estimated_tokens
    if batch:
        batches.append(batch)
    return batches


def _openrouter_embed_batch(
    *,
    api_key: str,
    model: str,
    texts: list[str],
) -> tuple[list[list[float]], dict[str, Any] | None]:
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/embeddings",
        data=json.dumps(
            {
                "input": texts,
                "model": model,
                "encoding_format": "float",
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Cache": OPENROUTER_CACHE_HEADER_VALUE,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw_payload = response.read()
    except urllib.error.HTTPError as exc:
        payload = _load_json_bytes(exc.read())
        if payload is not None:
            openrouter_error = _openrouter_error_from_payload(payload, fallback_status_code=int(exc.code))
            if openrouter_error is not None:
                raise openrouter_error from exc
        raise

    payload = _load_json_bytes(raw_payload)
    if payload is None:
        raise RuntimeError("OpenRouter embedding response was not valid JSON.")
    openrouter_error = _openrouter_error_from_payload(payload)
    if openrouter_error is not None:
        raise openrouter_error
    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError(f"OpenRouter embedding response missing data list: {payload.keys()}")

    rows = sorted(data, key=lambda item: int(item.get("index", 0)))
    embeddings: list[list[float]] = []
    for row in rows:
        embedding = row.get("embedding")
        if not isinstance(embedding, list):
            raise RuntimeError("OpenRouter embedding response row missing embedding vector.")
        embeddings.append(embedding)
    usage = payload.get("usage")
    if isinstance(usage, dict) and "id" not in usage and payload.get("id") is not None:
        usage = dict(usage)
        usage["id"] = payload.get("id")
    return embeddings, usage if isinstance(usage, dict) else None


def _l2_normalize_dense(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


def _embed_unique_chunks(
    chunk_instances: list[ChunkInstance],
    estimated_tokens_by_chunk_sha: dict[str, int],
    *,
    out_dir: Path,
    model: str,
    max_input_tokens: int,
    batch_size: int,
    max_batch_estimated_tokens: int,
    retry_limit: int,
    retry_base_seconds: float,
) -> dict[str, np.ndarray]:
    normalized_model = _normalize_openrouter_model(model)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is not set.")

    unique_chunk_by_sha: dict[str, ChunkInstance] = {}
    for instance in chunk_instances:
        unique_chunk_by_sha.setdefault(instance.chunk_sha256, instance)
    unique_chunk_shas = sorted(unique_chunk_by_sha)

    embeddings_by_chunk_sha = _load_embedding_checkpoint(out_dir, model=normalized_model)
    usage_by_batch = _load_embedding_usage_progress(out_dir, model=normalized_model)
    _write_embedding_progress(
        out_dir,
        model=normalized_model,
        unique_chunk_shas=unique_chunk_shas,
        estimated_tokens_by_chunk_sha=estimated_tokens_by_chunk_sha,
        embeddings_by_chunk_sha=embeddings_by_chunk_sha,
        usage_by_batch=usage_by_batch,
    )

    if embeddings_by_chunk_sha:
        print(
            f"Resuming from checkpoint: {len(embeddings_by_chunk_sha)}/{len(unique_chunk_shas)} "
            "unique chunk embeddings already saved"
        )

    pending_instances = [
        unique_chunk_by_sha[chunk_sha]
        for chunk_sha in unique_chunk_shas
        if chunk_sha not in embeddings_by_chunk_sha
    ]
    if not pending_instances:
        print("All unique chunk embeddings already exist in the local checkpoint; skipping API calls.")
        return embeddings_by_chunk_sha

    batches = _iter_batches(
        pending_instances,
        estimated_tokens_by_chunk_sha,
        batch_size=batch_size,
        max_batch_estimated_tokens=max_batch_estimated_tokens,
    )
    for batch_index, batch in enumerate(batches, start=1):
        input_texts = [instance.text for instance in batch]
        token_total = int(sum(estimated_tokens_by_chunk_sha[instance.chunk_sha256] for instance in batch))
        print(
            f"Embedding chunk batch {batch_index}/{len(batches)}: "
            f"{len(batch)} chunks, ~{token_total:,} tokens"
        )
        for attempt in range(1, retry_limit + 1):
            try:
                batch_embeddings, batch_usage = _openrouter_embed_batch(
                    api_key=api_key,
                    model=normalized_model,
                    texts=input_texts,
                )
                break
            except Exception as exc:
                if isinstance(exc, OpenRouterAPIError):
                    parsed_limit_error = _parse_openrouter_input_limit_error(str(exc))
                    if parsed_limit_error is not None:
                        input_index, provider_limit = parsed_limit_error
                        if input_index is None:
                            input_index = 0
                        if 0 <= input_index < len(batch):
                            if provider_limit is None:
                                provider_limit = OPENROUTER_EMBEDDING_INPUT_TOKEN_LIMIT
                            offending_chunk = batch[input_index]
                            resplit_target = _forced_resplit_target_max_tokens(
                                max_input_tokens=max_input_tokens,
                                provider_limit_tokens=provider_limit,
                            )
                            _write_embedding_progress(
                                out_dir,
                                model=normalized_model,
                                unique_chunk_shas=unique_chunk_shas,
                                estimated_tokens_by_chunk_sha=estimated_tokens_by_chunk_sha,
                                embeddings_by_chunk_sha=embeddings_by_chunk_sha,
                                usage_by_batch=usage_by_batch,
                                last_error=_embedding_error_payload(
                                    exc,
                                    batch_index=batch_index,
                                    batch_count=len(batches),
                                    token_total=token_total,
                                    batch_instances=batch,
                                ),
                            )
                            raise ChunkResplitRequired(
                                resplit_targets={offending_chunk.chunk_sha256: resplit_target},
                                message=(
                                    "OpenRouter rejected an input chunk as too long. "
                                    f"Will resplit chunk {offending_chunk.chunk_sha256[:12]} "
                                    f"to ~{resplit_target} tokens and retry."
                                ),
                            ) from exc
                if attempt >= retry_limit or not _is_retryable_http_error(exc):
                    _write_embedding_progress(
                        out_dir,
                        model=normalized_model,
                        unique_chunk_shas=unique_chunk_shas,
                        estimated_tokens_by_chunk_sha=estimated_tokens_by_chunk_sha,
                        embeddings_by_chunk_sha=embeddings_by_chunk_sha,
                        usage_by_batch=usage_by_batch,
                        last_error=_embedding_error_payload(
                            exc,
                            batch_index=batch_index,
                            batch_count=len(batches),
                            token_total=token_total,
                            batch_instances=batch,
                        ),
                    )
                    raise
                sleep_seconds = retry_base_seconds * (2 ** (attempt - 1))
                print(
                    f"  retry {attempt}/{retry_limit - 1} after "
                    f"{exc}: sleeping {sleep_seconds:.1f}s"
                )
                time.sleep(sleep_seconds)
        else:
            raise RuntimeError("Unreachable retry loop termination.")

        if len(batch_embeddings) != len(batch):
            raise RuntimeError(f"Expected {len(batch)} embeddings, received {len(batch_embeddings)}.")

        for instance, embedding in zip(batch, batch_embeddings, strict=True):
            embeddings_by_chunk_sha[instance.chunk_sha256] = np.asarray(embedding, dtype=np.float32)

        usage_row: dict[str, Any] = {
            "batch_index": int(batch_index),
            "chunk_count": len(batch),
            "estimated_tokens": token_total,
            "sample_names": [instance.representative_sample_name for instance in batch],
            "chunk_sha256": [instance.chunk_sha256 for instance in batch],
        }
        if batch_usage is not None:
            prompt_tokens = _int_or_none(batch_usage.get("prompt_tokens"))
            total_tokens = _int_or_none(batch_usage.get("total_tokens"))
            cost = _float_or_none(batch_usage.get("cost"))
            response_id = batch_usage.get("id")
            if prompt_tokens is not None:
                usage_row["prompt_tokens"] = prompt_tokens
            if total_tokens is not None:
                usage_row["total_tokens"] = total_tokens
            if cost is not None:
                usage_row["cost"] = cost
            if response_id is not None:
                usage_row["response_id"] = str(response_id)
        usage_by_batch.append(usage_row)

        _save_embedding_checkpoint(
            out_dir,
            model=normalized_model,
            chunk_order=unique_chunk_shas,
            embeddings_by_chunk_sha=embeddings_by_chunk_sha,
        )
        _write_embedding_progress(
            out_dir,
            model=normalized_model,
            unique_chunk_shas=unique_chunk_shas,
            estimated_tokens_by_chunk_sha=estimated_tokens_by_chunk_sha,
            embeddings_by_chunk_sha=embeddings_by_chunk_sha,
            usage_by_batch=usage_by_batch,
        )
        print(
            f"  checkpointed {len(embeddings_by_chunk_sha)}/{len(unique_chunk_shas)} unique chunk embeddings"
        )

    return embeddings_by_chunk_sha


def _pooled_document_embeddings(
    unique_records: list[UniqueCodeRecord],
    chunks_by_code_sha: dict[str, list[ChunkInstance]],
    embeddings_by_chunk_sha: dict[str, np.ndarray],
) -> np.ndarray:
    vectors: list[np.ndarray] = []
    for record in unique_records:
        chunks = chunks_by_code_sha.get(record.obfuscated_code_sha256)
        if not chunks:
            raise ValueError(f"No chunks for code {record.obfuscated_code_sha256}")
        chunk_vectors: list[np.ndarray] = []
        weights: list[float] = []
        for chunk in chunks:
            embedding = embeddings_by_chunk_sha.get(chunk.chunk_sha256)
            if embedding is None:
                raise ValueError(f"Missing embedding for chunk {chunk.chunk_sha256}")
            chunk_vectors.append(np.asarray(embedding, dtype=np.float32))
            weights.append(float(max(chunk.token_count, 1)))
        matrix = np.vstack(chunk_vectors).astype(np.float32, copy=False)
        weight_array = np.asarray(weights, dtype=np.float32)
        pooled = np.average(matrix, axis=0, weights=weight_array).astype(np.float32, copy=False)
        vectors.append(pooled)
    return _l2_normalize_dense(np.vstack(vectors).astype(np.float32, copy=False))


def _cluster_distances(embeddings: np.ndarray, labels: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    return np.linalg.norm(embeddings - centroids[labels], axis=1)


def _projection_2d(embeddings: np.ndarray) -> np.ndarray:
    if embeddings.shape[0] == 0:
        return np.zeros((0, 2), dtype=np.float32)
    if embeddings.shape[0] == 1:
        return np.zeros((1, 2), dtype=np.float32)
    centered = embeddings.astype(np.float64) - embeddings.astype(np.float64).mean(axis=0, keepdims=True)
    try:
        u, singular_values, _ = np.linalg.svd(centered, full_matrices=False)
        if singular_values.size >= 2:
            return (u[:, :2] * singular_values[:2]).astype(np.float32)
        if singular_values.size == 1:
            first = (u[:, :1] * singular_values[:1]).astype(np.float32)
            return np.hstack([first, np.zeros((embeddings.shape[0], 1), dtype=np.float32)])
    except np.linalg.LinAlgError:
        pass
    if embeddings.shape[1] >= 2:
        return embeddings[:, :2].astype(np.float32)
    if embeddings.shape[1] == 1:
        return np.hstack([embeddings.astype(np.float32), np.zeros((embeddings.shape[0], 1), dtype=np.float32)])
    return np.zeros((embeddings.shape[0], 2), dtype=np.float32)


def _cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    return np.clip(embeddings @ embeddings.T, -1.0, 1.0).astype(np.float32)


def _silhouette_score_from_similarity(similarity: np.ndarray, labels: np.ndarray) -> float:
    unique_labels = np.unique(labels)
    if unique_labels.size <= 1:
        return float("nan")
    distances = 1.0 - similarity
    scores = np.zeros(labels.shape[0], dtype=np.float64)
    for idx in range(labels.shape[0]):
        same_mask = labels == labels[idx]
        same_mask[idx] = False
        if np.any(same_mask):
            a = float(distances[idx, same_mask].mean())
        else:
            scores[idx] = 0.0
            continue
        b = float("inf")
        for other_label in unique_labels:
            if other_label == labels[idx]:
                continue
            other_mask = labels == other_label
            if np.any(other_mask):
                b = min(b, float(distances[idx, other_mask].mean()))
        if not math.isfinite(b):
            scores[idx] = 0.0
            continue
        denom = max(a, b)
        scores[idx] = 0.0 if denom <= 0.0 else (b - a) / denom
    return float(scores.mean())


def _run_kmeans(embeddings: np.ndarray, n_clusters: int, random_seed: int) -> tuple[np.ndarray, np.ndarray]:
    if n_clusters <= 0:
        raise ValueError("n_clusters must be positive.")
    if embeddings.shape[0] < n_clusters:
        raise ValueError(f"Cannot fit {n_clusters} clusters with only {embeddings.shape[0]} samples.")
    rng = np.random.default_rng(random_seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        centroids, labels = kmeans2(
            embeddings,
            n_clusters,
            minit="++",
            iter=50,
            missing="warn",
            check_finite=True,
            rng=rng,
        )
    return np.asarray(centroids, dtype=np.float32), np.asarray(labels, dtype=np.int32)


def _choose_cluster_count(embeddings: np.ndarray, similarity: np.ndarray, k_min: int, k_max: int, random_seed: int) -> tuple[int, dict[str, float]]:
    n_samples = embeddings.shape[0]
    if n_samples <= 2:
        return n_samples, {}
    max_candidate = min(k_max, n_samples - 1)
    min_candidate = min(max(k_min, 2), max_candidate)
    if max_candidate < 2:
        return 1, {}
    scores: dict[str, float] = {}
    best_k = min_candidate
    best_score = -float("inf")
    for n_clusters in range(min_candidate, max_candidate + 1):
        _, labels = _run_kmeans(embeddings, n_clusters, random_seed)
        score = _silhouette_score_from_similarity(similarity, labels)
        scores[str(n_clusters)] = float(score)
        if not math.isnan(score) and score > best_score:
            best_score = score
            best_k = n_clusters
    return best_k, scores


def _identifier_terms(text: str) -> list[str]:
    terms: list[str] = []
    for match in IDENTIFIER_RE.findall(text):
        pieces = CAMEL_BOUNDARY_RE.sub(" ", match).replace("_", " ").split()
        for piece in pieces:
            piece = piece.lower()
            if len(piece) < 3 or piece in THEME_STOPWORDS:
                continue
            terms.append(piece)
    return terms


def _build_cluster_themes(unique_records: list[UniqueCodeRecord], labels: np.ndarray, top_n: int) -> dict[int, str]:
    counts_by_cluster: dict[int, Counter[str]] = defaultdict(Counter)
    for record, cluster_id in zip(unique_records, labels, strict=True):
        counts_by_cluster[int(cluster_id)].update(_identifier_terms(record.representative_raw_code_text))
    themes: dict[int, str] = {}
    for cluster_id, counter in counts_by_cluster.items():
        top_terms = [term for term, _ in counter.most_common(top_n)]
        themes[cluster_id] = ", ".join(top_terms) if top_terms else f"cluster_{cluster_id}"
    return themes


def _cluster_label_overrides(path_str: str | None) -> dict[int, dict[str, str]]:
    if not path_str:
        return {}
    path = _resolve_path(path_str)
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels: dict[int, dict[str, str]] = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if not isinstance(value, dict):
                continue
            labels[int(key)] = {
                "name": str(value.get("name", f"Cluster {key}")),
                "detail": str(value.get("detail", "")),
            }
    return labels


def _cluster_display_label(cluster_id: int, cluster_themes: dict[int, str], overrides: dict[int, dict[str, str]]) -> tuple[str, str]:
    override = overrides.get(int(cluster_id))
    if override:
        return override.get("name", f"Cluster {cluster_id}"), override.get("detail", "")
    return cluster_themes.get(int(cluster_id), f"cluster_{cluster_id}"), ""


def _correlation_triplet(df: pd.DataFrame, left: str, right: str) -> dict[str, float]:
    lhs = pd.to_numeric(df[left], errors="coerce")
    rhs = pd.to_numeric(df[right], errors="coerce")
    valid = lhs.notna() & rhs.notna()
    if int(valid.sum()) < 2:
        return {"pearson": float("nan"), "spearman": float("nan"), "kendall": float("nan")}
    lhs = lhs[valid]
    rhs = rhs[valid]
    return {
        "pearson": float(lhs.corr(rhs, method="pearson")),
        "spearman": float(lhs.corr(rhs, method="spearman")),
        "kendall": float(lhs.corr(rhs, method="kendall")),
    }


def _pairwise_dataframe(
    sample_records: list[SampleRecord],
    sample_embeddings: np.ndarray,
    sample_labels: np.ndarray,
) -> pd.DataFrame:
    n_samples = len(sample_records)
    if n_samples < 2:
        raise ValueError("Need at least two samples to build pairwise comparisons.")
    elo = np.asarray([record.elo for record in sample_records], dtype=np.float64)
    rank = np.asarray([record.rank for record in sample_records], dtype=np.float64)
    similarity = _cosine_similarity_matrix(sample_embeddings)
    idx_i, idx_j = np.triu_indices(n_samples, k=1)
    sample_names = np.asarray([record.sample_name for record in sample_records], dtype=object)
    parent_names = np.asarray([record.parent_name for record in sample_records], dtype=object)
    frame = pd.DataFrame(
        {
            "sample_a": sample_names[idx_i],
            "sample_b": sample_names[idx_j],
            "parent_a": parent_names[idx_i],
            "parent_b": parent_names[idx_j],
            "cosine_similarity": similarity[idx_i, idx_j].astype(np.float64),
            "elo_gap": np.abs(elo[idx_i] - elo[idx_j]),
            "rank_gap": np.abs(rank[idx_i] - rank[idx_j]),
            "same_cluster": (sample_labels[idx_i] == sample_labels[idx_j]).astype(np.int64),
            "cluster_a": sample_labels[idx_i].astype(np.int64),
            "cluster_b": sample_labels[idx_j].astype(np.int64),
        }
    )
    frame["neg_elo_gap"] = -frame["elo_gap"]
    frame["neg_rank_gap"] = -frame["rank_gap"]
    return frame


def _cluster_summary_dataframe(
    sample_records: list[SampleRecord],
    sample_labels: np.ndarray,
    sample_distances: np.ndarray,
    cluster_themes: dict[int, str],
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "sample_name": [record.sample_name for record in sample_records],
            "parent_name": [record.parent_name for record in sample_records],
            "elo": [record.elo for record in sample_records],
            "cluster_id": sample_labels.astype(np.int64),
            "distance_to_centroid": sample_distances.astype(np.float64),
        }
    )
    rows: list[dict[str, Any]] = []
    for cluster_id, group in frame.groupby("cluster_id", sort=True):
        ordered = group.sort_values(by=["distance_to_centroid", "elo"], ascending=[True, False])
        rows.append(
            {
                "cluster_id": int(cluster_id),
                "cluster_theme": cluster_themes.get(int(cluster_id), f"cluster_{cluster_id}"),
                "sample_count": int(len(group)),
                "mean_elo": float(group["elo"].mean()),
                "median_elo": float(group["elo"].median()),
                "min_elo": float(group["elo"].min()),
                "max_elo": float(group["elo"].max()),
                "representative_samples": json.dumps(ordered["sample_name"].head(5).tolist()),
            }
        )
    return pd.DataFrame(rows).sort_values("cluster_id").reset_index(drop=True)


def _summary_metrics(
    sample_records: list[SampleRecord],
    unique_records: list[UniqueCodeRecord],
    pairwise_df: pd.DataFrame,
    sample_labels: np.ndarray,
) -> dict[str, Any]:
    elo = np.asarray([record.elo for record in sample_records], dtype=np.float64)
    same_cluster = pairwise_df["same_cluster"] == 1
    within_gap = pairwise_df.loc[same_cluster, "elo_gap"]
    between_gap = pairwise_df.loc[~same_cluster, "elo_gap"]
    within_similarity = pairwise_df.loc[same_cluster, "cosine_similarity"]
    between_similarity = pairwise_df.loc[~same_cluster, "cosine_similarity"]

    cluster_means: dict[int, float] = {}
    for cluster_id in np.unique(sample_labels):
        mask = sample_labels == cluster_id
        cluster_means[int(cluster_id)] = float(np.mean(elo[mask]))

    if elo.size >= 2 and np.var(elo) > 0:
        fitted = np.asarray([cluster_means[int(cluster_id)] for cluster_id in sample_labels], dtype=np.float64)
        sse = float(np.sum((elo - fitted) ** 2))
        sst = float(np.sum((elo - np.mean(elo)) ** 2))
        cluster_r2 = float(1.0 - (sse / sst))
    else:
        cluster_r2 = float("nan")

    return {
        "sample_count": len(sample_records),
        "unique_code_count": len(unique_records),
        "duplicate_sample_count": len(sample_records) - len(unique_records),
        "pair_count": int(len(pairwise_df)),
        "within_cluster_mean_abs_elo_gap": float(within_gap.mean()) if not within_gap.empty else float("nan"),
        "between_cluster_mean_abs_elo_gap": float(between_gap.mean()) if not between_gap.empty else float("nan"),
        "within_cluster_mean_cosine_similarity": float(within_similarity.mean()) if not within_similarity.empty else float("nan"),
        "between_cluster_mean_cosine_similarity": float(between_similarity.mean()) if not between_similarity.empty else float("nan"),
        "cluster_mean_elo_r2": cluster_r2,
    }


def _prepare_plot_env() -> None:
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-codex")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache-codex")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)


def _truncate_label(text: str, max_len: int = 28) -> str:
    text = str(text)
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _cluster_color_map(cluster_ids: list[int]) -> dict[int, Any]:
    _prepare_plot_env()
    import matplotlib.pyplot as plt

    unique_cluster_ids = sorted(set(int(cluster_id) for cluster_id in cluster_ids))
    cmap = plt.get_cmap("tab20", max(3, len(unique_cluster_ids)))
    return {cluster_id: cmap(idx) for idx, cluster_id in enumerate(unique_cluster_ids)}


def _model_colors(models: list[str]) -> dict[str, Any]:
    _prepare_plot_env()
    import matplotlib.pyplot as plt

    base_colors = list(plt.get_cmap("tab20").colors)
    order = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    return {model: base_colors[order[index % len(order)]] for index, model in enumerate(models)}


def _plot_cluster_projection(
    out_path: Path,
    unique_records: list[UniqueCodeRecord],
    projection_2d: np.ndarray,
    unique_labels: np.ndarray,
    cluster_themes: dict[int, str],
    cluster_label_overrides: dict[int, dict[str, str]],
) -> None:
    _prepare_plot_env()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    label_values = np.asarray(unique_labels, dtype=np.int64)
    unique_cluster_ids = sorted(set(label_values.tolist()))
    cmap = plt.get_cmap("tab20", max(3, len(unique_cluster_ids)))
    fig, ax = plt.subplots(figsize=(13, 9), constrained_layout=True)
    for color_idx, cluster_id in enumerate(unique_cluster_ids):
        mask = label_values == cluster_id
        cluster_points = projection_2d[mask]
        sizes = np.asarray(
            [unique_records[idx].duplicate_group_size for idx, is_member in enumerate(mask) if is_member],
            dtype=np.float32,
        )
        point_sizes = 34.0 + 10.0 * np.sqrt(np.maximum(sizes, 1.0))
        color = cmap(color_idx)
        ax.scatter(
            cluster_points[:, 0],
            cluster_points[:, 1],
            s=point_sizes,
            alpha=0.78,
            color=color,
            edgecolors="white",
            linewidths=0.5,
        )
        centroid = cluster_points.mean(axis=0)
        label_name, label_detail = _cluster_display_label(int(cluster_id), cluster_themes, cluster_label_overrides)
        detail_line = f"\n{label_detail}" if label_detail else ""
        ax.annotate(
            f"C{cluster_id}: {label_name}{detail_line}\n(n={int(mask.sum())})",
            xy=(float(centroid[0]), float(centroid[1])),
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "white",
                "edgecolor": color,
                "linewidth": 1.2,
                "alpha": 0.92,
            },
        )
    ax.set_title("Obfuscated Code Clusters (unique code only)")
    ax.set_xlabel("Projection component 1")
    ax.set_ylabel("Projection component 2")
    ax.grid(alpha=0.2)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_cluster_projection_by_elo(
    out_path: Path,
    unique_records: list[UniqueCodeRecord],
    projection_2d: np.ndarray,
    unique_labels: np.ndarray,
    unique_mean_elo: np.ndarray,
    cluster_themes: dict[int, str],
    cluster_label_overrides: dict[int, dict[str, str]],
) -> None:
    _prepare_plot_env()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    label_values = np.asarray(unique_labels, dtype=np.int64)
    fig, ax = plt.subplots(figsize=(13, 9), constrained_layout=True)
    sizes = np.asarray([record.duplicate_group_size for record in unique_records], dtype=np.float32)
    point_sizes = 34.0 + 10.0 * np.sqrt(np.maximum(sizes, 1.0))
    scatter = ax.scatter(
        projection_2d[:, 0],
        projection_2d[:, 1],
        c=unique_mean_elo.astype(np.float64),
        cmap="viridis",
        s=point_sizes,
        alpha=0.82,
        edgecolors="white",
        linewidths=0.6,
    )
    color_lookup = _cluster_color_map(label_values.tolist())
    for cluster_id in sorted(set(label_values.tolist())):
        mask = label_values == cluster_id
        cluster_points = projection_2d[mask]
        centroid = cluster_points.mean(axis=0)
        color = color_lookup[int(cluster_id)]
        label_name, _ = _cluster_display_label(int(cluster_id), cluster_themes, cluster_label_overrides)
        ax.scatter([float(centroid[0])], [float(centroid[1])], s=180, marker="x", color=color, linewidths=2.2, zorder=3)
        ax.annotate(
            f"C{cluster_id}: {_truncate_label(label_name, 22)}",
            xy=(float(centroid[0]), float(centroid[1])),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
            color="black",
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": color,
                "linewidth": 1.1,
                "alpha": 0.9,
            },
        )
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    colorbar.set_label("Mean Elo of samples sharing this code")
    ax.set_title("Embedding Projection Colored by ELO")
    ax.set_xlabel("Projection component 1")
    ax.set_ylabel("Projection component 2")
    ax.grid(alpha=0.2)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _draw_model_cluster_legends(
    ax: Any,
    models: list[str],
    clusters: list[int],
    colors: dict[str, Any],
    markers: list[str],
    cluster_themes: dict[int, str],
    cluster_label_overrides: dict[int, dict[str, str]],
) -> None:
    from matplotlib.lines import Line2D

    model_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            color=colors[model],
            markeredgecolor="black",
            markersize=8,
            label=model,
        )
        for model in models
    ]
    cluster_handles = []
    for cluster_id in clusters:
        label_name, _ = _cluster_display_label(int(cluster_id), cluster_themes, cluster_label_overrides)
        cluster_handles.append(
            Line2D(
                [0],
                [0],
                marker=markers[cluster_id % len(markers)],
                linestyle="",
                color="white",
                markeredgecolor="black",
                markersize=8,
                label=f"C{cluster_id}: {label_name}",
            )
        )
    model_legend = ax.legend(
        handles=model_handles,
        title="Color = model",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        title_fontsize=10,
        frameon=True,
    )
    ax.add_artist(model_legend)
    ax.legend(
        handles=cluster_handles,
        title="Marker = cluster",
        loc="upper left",
        fontsize=8,
        title_fontsize=10,
        frameon=True,
    )


def _draw_embedded_legend_panel(
    legend_ax: Any,
    models: list[str],
    clusters: list[int],
    colors: dict[str, Any],
    markers: list[str],
    cluster_themes: dict[int, str],
    cluster_label_overrides: dict[int, dict[str, str]],
) -> None:
    legend_ax.text(0.0, 0.98, "Color Legend: Model", fontsize=15, fontweight="bold", va="top")
    y = 0.92
    for model in models:
        legend_ax.scatter([0.035], [y], s=145, color=colors[model], edgecolors="black", linewidths=0.6)
        legend_ax.text(0.085, y, _truncate_label(model, 30), fontsize=10.5, va="center")
        y -= 0.055
    legend_ax.text(0.0, y - 0.02, "Marker Legend: Cluster", fontsize=15, fontweight="bold", va="top")
    y -= 0.085
    for cluster_id in clusters:
        label_name, _ = _cluster_display_label(int(cluster_id), cluster_themes, cluster_label_overrides)
        legend_ax.scatter(
            [0.035],
            [y],
            s=145,
            marker=markers[cluster_id % len(markers)],
            color="white",
            edgecolors="black",
            linewidths=1.0,
        )
        legend_ax.text(0.085, y, f"C{cluster_id}: {_truncate_label(label_name, 28)}", fontsize=10.5, va="center")
        y -= 0.058
    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis("off")


def _plot_cluster_projection_by_model(
    out_path: Path,
    sample_records: list[SampleRecord],
    sample_projection: np.ndarray,
    sample_labels: np.ndarray,
    cluster_themes: dict[int, str],
    cluster_label_overrides: dict[int, dict[str, str]],
    *,
    legend_panel: bool,
) -> None:
    _prepare_plot_env()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = sorted({record.parent_name for record in sample_records})
    clusters = sorted(set(sample_labels.astype(int).tolist()))
    colors = _model_colors(models)
    markers = ["o", "s", "^", "D", "P", "X", "v", "<", ">", "*"]
    if legend_panel:
        fig = plt.figure(figsize=(22, 11), constrained_layout=True)
        grid = fig.add_gridspec(1, 2, width_ratios=[4.8, 1.65])
        ax = fig.add_subplot(grid[0, 0])
        legend_ax = fig.add_subplot(grid[0, 1])
    else:
        fig, ax = plt.subplots(figsize=(18, 10), constrained_layout=True)
        legend_ax = None

    cluster_points: dict[int, list[np.ndarray]] = defaultdict(list)
    for cluster_id in clusters:
        for model in models:
            indices = [
                index
                for index, record in enumerate(sample_records)
                if int(sample_labels[index]) == cluster_id and record.parent_name == model
            ]
            if not indices:
                continue
            points = sample_projection[indices]
            ax.scatter(
                points[:, 0],
                points[:, 1],
                s=74,
                marker=markers[cluster_id % len(markers)],
                color=colors[model],
                edgecolors="black",
                linewidths=0.5,
                alpha=0.86,
            )
            cluster_points[cluster_id].extend(points.tolist())

    for cluster_id, points in sorted(cluster_points.items()):
        centroid = np.asarray(points, dtype=np.float64).mean(axis=0)
        label_name, label_detail = _cluster_display_label(int(cluster_id), cluster_themes, cluster_label_overrides)
        detail_line = f"\n{label_detail}" if label_detail else ""
        ax.annotate(
            f"C{cluster_id}: {label_name}{detail_line}\nn={len(points)}",
            xy=(float(centroid[0]), float(centroid[1])),
            ha="center",
            va="center",
            fontsize=10,
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": "white",
                "edgecolor": "black",
                "linewidth": 1.0,
                "alpha": 0.84,
            },
        )

    ax.set_title("Obfuscated Code Clusters\nColor = model; marker = cluster", fontsize=17)
    ax.set_xlabel("Projection component 1", fontsize=12)
    ax.set_ylabel("Projection component 2", fontsize=12)
    ax.grid(alpha=0.18)

    if legend_ax is None:
        _draw_model_cluster_legends(ax, models, clusters, colors, markers, cluster_themes, cluster_label_overrides)
    else:
        _draw_embedded_legend_panel(legend_ax, models, clusters, colors, markers, cluster_themes, cluster_label_overrides)

    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_similarity_vs_elo_gap(
    out_path: Path,
    pairwise_df: pd.DataFrame,
    correlation_summary: dict[str, float],
    plot_limit: int,
    random_seed: int,
) -> None:
    _prepare_plot_env()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_df = pairwise_df
    if len(plot_df) > plot_limit:
        plot_df = plot_df.sample(n=plot_limit, random_state=random_seed)
    same_cluster = plot_df["same_cluster"] == 1
    fig, ax = plt.subplots(figsize=(11, 7), constrained_layout=True)
    ax.scatter(
        plot_df.loc[~same_cluster, "cosine_similarity"],
        plot_df.loc[~same_cluster, "elo_gap"],
        s=12,
        alpha=0.28,
        label="Different cluster",
    )
    ax.scatter(
        plot_df.loc[same_cluster, "cosine_similarity"],
        plot_df.loc[same_cluster, "elo_gap"],
        s=14,
        alpha=0.52,
        label="Same cluster",
    )
    ax.set_xlabel("Code cosine similarity")
    ax.set_ylabel("Absolute Elo gap")
    ax.set_title(
        "Pairwise Code Similarity vs Elo Gap\n"
        f"pearson={correlation_summary['pearson']:.3f}, "
        f"spearman={correlation_summary['spearman']:.3f}, "
        f"kendall={correlation_summary['kendall']:.3f}"
    )
    ax.grid(alpha=0.2)
    ax.legend(loc="upper right")
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_elo_by_cluster(
    out_path: Path,
    sample_records: list[SampleRecord],
    sample_labels: np.ndarray,
    cluster_themes: dict[int, str],
    cluster_mean_elo_r2: float,
    cluster_label_overrides: dict[int, dict[str, str]],
) -> None:
    _prepare_plot_env()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frame = pd.DataFrame(
        {
            "sample_name": [record.sample_name for record in sample_records],
            "elo": [record.elo for record in sample_records],
            "cluster_id": sample_labels.astype(np.int64),
        }
    )
    cluster_order = frame.groupby("cluster_id", sort=True)["elo"].mean().sort_values(ascending=False).index.tolist()
    color_lookup = _cluster_color_map(cluster_order)
    groups = [frame.loc[frame["cluster_id"] == cluster_id, "elo"].to_numpy(dtype=float) for cluster_id in cluster_order]
    labels = []
    for cluster_id in cluster_order:
        label_name, _ = _cluster_display_label(int(cluster_id), cluster_themes, cluster_label_overrides)
        labels.append(_truncate_label(f"C{cluster_id}: {label_name}", 24))

    fig, ax = plt.subplots(figsize=(max(9.5, 1.35 * len(cluster_order)), 7.2), constrained_layout=True)
    boxplot = ax.boxplot(
        groups,
        positions=np.arange(len(cluster_order), dtype=float),
        widths=0.58,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "black", "linewidth": 1.6},
        whiskerprops={"linewidth": 1.1},
        capprops={"linewidth": 1.1},
    )
    for patch, cluster_id in zip(boxplot["boxes"], cluster_order, strict=True):
        patch.set_facecolor(color_lookup[int(cluster_id)])
        patch.set_alpha(0.32)
        patch.set_edgecolor(color_lookup[int(cluster_id)])
        patch.set_linewidth(1.2)

    rng = np.random.default_rng(DEFAULT_RANDOM_SEED)
    for x_pos, cluster_id in enumerate(cluster_order):
        ys = frame.loc[frame["cluster_id"] == cluster_id, "elo"].to_numpy(dtype=float)
        xs = x_pos + rng.uniform(-0.16, 0.16, size=ys.shape[0])
        ax.scatter(xs, ys, s=26, alpha=0.78, color=color_lookup[int(cluster_id)], edgecolors="none")
        ax.scatter([x_pos], [float(np.mean(ys))], s=70, color="black", marker="D", zorder=3)
        ax.text(x_pos, float(np.max(ys)) + 8.0, f"n={len(ys)}", ha="center", va="bottom", fontsize=8, color="black")

    title = "ELO Distribution by Cluster"
    if math.isfinite(cluster_mean_elo_r2):
        title += f"\ncluster-mean ELO R²={cluster_mean_elo_r2:.3f}"
    ax.set_title(title)
    ax.set_xlabel("Cluster (ordered by mean ELO)")
    ax.set_ylabel("ELO")
    ax.set_xticks(np.arange(len(cluster_order), dtype=float))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.2)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_latent_dimensions_vs_elo(
    out_path: Path,
    sample_records: list[SampleRecord],
    sample_projection: np.ndarray,
    sample_labels: np.ndarray,
) -> dict[str, dict[str, float]]:
    _prepare_plot_env()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    elo = np.asarray([record.elo for record in sample_records], dtype=np.float64)
    x_dim = sample_projection[:, 0].astype(np.float64)
    y_dim = sample_projection[:, 1].astype(np.float64)
    frame = pd.DataFrame({"elo": elo, "projection_x": x_dim, "projection_y": y_dim})
    x_corr = _correlation_triplet(frame, "projection_x", "elo")
    y_corr = _correlation_triplet(frame, "projection_y", "elo")

    color_lookup = _cluster_color_map(sample_labels.astype(int).tolist())
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8), constrained_layout=True, sharey=True)
    dims = [
        ("projection_x", "Projection component 1", x_corr),
        ("projection_y", "Projection component 2", y_corr),
    ]
    for ax, (col_name, axis_label, corr) in zip(axes, dims, strict=True):
        xs = frame[col_name].to_numpy(dtype=float)
        for cluster_id in sorted(set(sample_labels.astype(int).tolist())):
            mask = sample_labels == cluster_id
            ax.scatter(
                xs[mask],
                elo[mask],
                s=24,
                alpha=0.78,
                color=color_lookup[int(cluster_id)],
                label=f"C{int(cluster_id)}",
                edgecolors="none",
            )
        if np.nanstd(xs) > 0:
            slope, intercept = np.polyfit(xs, elo, 1)
            line_x = np.linspace(float(np.min(xs)), float(np.max(xs)), 100)
            ax.plot(line_x, slope * line_x + intercept, color="black", linewidth=1.6, alpha=0.85)
        ax.set_xlabel(f"{axis_label} (sign arbitrary)")
        ax.set_title(f"{axis_label} vs ELO\npearson={corr['pearson']:.3f}, spearman={corr['spearman']:.3f}")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("ELO")
    handles, labels = axes[0].get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    axes[1].legend(unique.values(), unique.keys(), loc="best", fontsize=8, title="Cluster")
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return {"projection_x_vs_elo": x_corr, "projection_y_vs_elo": y_corr}


def _plot_similarity_heatmap(
    out_path: Path,
    sample_records: list[SampleRecord],
    sample_embeddings: np.ndarray,
    sample_labels: np.ndarray,
    order_mode: str,
) -> None:
    _prepare_plot_env()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    similarity = _cosine_similarity_matrix(sample_embeddings).astype(np.float64)
    sample_names = np.asarray([record.sample_name for record in sample_records], dtype=object)
    elo = np.asarray([record.elo for record in sample_records], dtype=np.float64)
    cluster_ids = sample_labels.astype(np.int64)
    base_indices = np.arange(len(sample_records), dtype=np.int64)

    if order_mode == "cluster_then_elo":
        order = sorted(base_indices.tolist(), key=lambda idx: (int(cluster_ids[idx]), -float(elo[idx]), str(sample_names[idx])))
        title = "Code Cosine Similarity Ordered by Cluster, Then ELO"
    elif order_mode == "elo":
        order = sorted(base_indices.tolist(), key=lambda idx: (-float(elo[idx]), int(cluster_ids[idx]), str(sample_names[idx])))
        title = "Code Cosine Similarity Ordered by ELO"
    else:
        raise ValueError(f"Unknown heatmap order_mode: {order_mode}")

    ordered_similarity = similarity[np.ix_(order, order)]
    ordered_names = sample_names[order]
    ordered_clusters = cluster_ids[order]

    fig, ax = plt.subplots(figsize=(10.8, 9.5), constrained_layout=True)
    image = ax.imshow(ordered_similarity, vmin=-1.0, vmax=1.0, cmap="RdYlGn", interpolation="nearest", aspect="auto")
    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label("Cosine similarity")
    ax.set_title(title)
    if len(order) <= 60:
        labels = [_truncate_label(name, 18) for name in ordered_names.tolist()]
        ax.set_xticks(np.arange(len(order)))
        ax.set_yticks(np.arange(len(order)))
        ax.set_xticklabels(labels, rotation=90, fontsize=7)
        ax.set_yticklabels(labels, fontsize=7)
    else:
        ax.set_xticks([])
        ax.set_yticks([])
    change_points = np.where(np.diff(ordered_clusters) != 0)[0]
    for idx in change_points:
        pos = idx + 0.5
        ax.axhline(pos, color="white", linewidth=1.0, alpha=0.9)
        ax.axvline(pos, color="white", linewidth=1.0, alpha=0.9)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _write_obfuscated_sources(out_dir: Path, unique_records: list[UniqueCodeRecord]) -> None:
    source_dir = out_dir / "obfuscated_sources"
    if source_dir.exists():
        shutil.rmtree(source_dir)
    source_dir.mkdir(parents=True, exist_ok=True)
    for record in unique_records:
        filename = f"{_sanitize_slug(record.representative_sample_name)}_{record.obfuscated_code_sha256[:12]}.py"
        (source_dir / filename).write_text(record.obfuscated_code_text, encoding="utf-8")


def _write_outputs(
    out_dir: Path,
    *,
    analysis_input: AnalysisInput,
    sample_records: list[SampleRecord],
    unique_records: list[UniqueCodeRecord],
    chunk_instances: list[ChunkInstance],
    estimated_tokens_by_chunk_sha: dict[str, int],
    chunk_embeddings_by_sha: dict[str, np.ndarray],
    unique_embeddings: np.ndarray,
    sample_embeddings: np.ndarray,
    unique_labels: np.ndarray,
    sample_labels: np.ndarray,
    unique_distances: np.ndarray,
    sample_distances: np.ndarray,
    unique_projection: np.ndarray,
    sample_projection: np.ndarray,
    cluster_themes: dict[int, str],
    cluster_label_overrides: dict[int, dict[str, str]],
    cluster_summary_df: pd.DataFrame,
    pairwise_df: pd.DataFrame,
    summary: dict[str, Any],
    pairwise_elo_corr: dict[str, float],
    legend_panel: bool,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    theme_lookup = {int(cluster_id): theme for cluster_id, theme in cluster_themes.items()}

    chunks_by_code_sha: dict[str, list[ChunkInstance]] = defaultdict(list)
    unique_chunk_occurrences: dict[str, list[ChunkInstance]] = defaultdict(list)
    for instance in chunk_instances:
        chunks_by_code_sha[instance.parent_obfuscated_code_sha256].append(instance)
        unique_chunk_occurrences[instance.chunk_sha256].append(instance)

    sample_manifest = pd.DataFrame(
        {
            "sample_name": [record.sample_name for record in sample_records],
            "bot_name": [record.bot_name for record in sample_records],
            "parent_name": [record.parent_name for record in sample_records],
            "elo": [record.elo for record in sample_records],
            "rank": [record.rank for record in sample_records],
            "raw_code_sha256": [record.raw_code_sha256 for record in sample_records],
            "obfuscated_code_sha256": [record.obfuscated_code_sha256 for record in sample_records],
            "raw_num_bytes": [record.num_bytes for record in sample_records],
            "raw_num_chars": [record.num_chars for record in sample_records],
            "obfuscated_num_chars": [record.obfuscated_num_chars for record in sample_records],
            "code_path": [record.code_path for record in sample_records],
            "chunk_count": [len(chunks_by_code_sha[record.obfuscated_code_sha256]) for record in sample_records],
            "chunk_sha256s_json": [json.dumps([item.chunk_sha256 for item in chunks_by_code_sha[record.obfuscated_code_sha256]]) for record in sample_records],
            "estimated_chunk_tokens": [int(sum(item.token_count for item in chunks_by_code_sha[record.obfuscated_code_sha256])) for record in sample_records],
            "cluster_id": sample_labels.astype(np.int64),
            "cluster_theme": [theme_lookup.get(int(cluster_id), "") for cluster_id in sample_labels],
            "distance_to_centroid": sample_distances.astype(np.float64),
            "projection_x": sample_projection[:, 0].astype(np.float64),
            "projection_y": sample_projection[:, 1].astype(np.float64),
        }
    ).sort_values(by=["cluster_id", "distance_to_centroid", "elo"], ascending=[True, True, False])
    sample_manifest.to_csv(out_dir / "sample_manifest.csv", index=False)

    unique_manifest = pd.DataFrame(
        {
            "obfuscated_code_sha256": [record.obfuscated_code_sha256 for record in unique_records],
            "representative_sample_name": [record.representative_sample_name for record in unique_records],
            "representative_bot_name": [record.representative_bot_name for record in unique_records],
            "representative_parent_name": [record.representative_parent_name for record in unique_records],
            "representative_code_path": [record.representative_code_path for record in unique_records],
            "representative_raw_code_sha256": [record.representative_raw_code_sha256 for record in unique_records],
            "raw_num_bytes": [record.num_bytes for record in unique_records],
            "raw_num_chars": [record.num_chars for record in unique_records],
            "obfuscated_num_chars": [record.obfuscated_num_chars for record in unique_records],
            "duplicate_group_size": [record.duplicate_group_size for record in unique_records],
            "sample_names_json": [json.dumps(record.sample_names) for record in unique_records],
            "bot_names_json": [json.dumps(record.bot_names) for record in unique_records],
            "parent_names_json": [json.dumps(record.parent_names) for record in unique_records],
            "chunk_count": [len(chunks_by_code_sha[record.obfuscated_code_sha256]) for record in unique_records],
            "chunk_sha256s_json": [json.dumps([item.chunk_sha256 for item in chunks_by_code_sha[record.obfuscated_code_sha256]]) for record in unique_records],
            "estimated_chunk_tokens": [int(sum(item.token_count for item in chunks_by_code_sha[record.obfuscated_code_sha256])) for record in unique_records],
            "cluster_id": unique_labels.astype(np.int64),
            "cluster_theme": [theme_lookup.get(int(cluster_id), "") for cluster_id in unique_labels],
            "distance_to_centroid": unique_distances.astype(np.float64),
            "projection_x": unique_projection[:, 0].astype(np.float64),
            "projection_y": unique_projection[:, 1].astype(np.float64),
        }
    ).sort_values(by=["cluster_id", "distance_to_centroid", "duplicate_group_size"], ascending=[True, True, False])
    unique_manifest.to_csv(out_dir / "unique_code_manifest.csv", index=False)

    chunk_manifest_rows: list[dict[str, Any]] = []
    for chunk_sha256, occurrences in sorted(unique_chunk_occurrences.items()):
        representative = occurrences[0]
        chunk_manifest_rows.append(
            {
                "chunk_sha256": chunk_sha256,
                "representative_sample_name": representative.representative_sample_name,
                "token_count": int(estimated_tokens_by_chunk_sha[chunk_sha256]),
                "num_chars": int(representative.num_chars),
                "occurrence_count": len(occurrences),
                "parent_obfuscated_code_sha256s_json": json.dumps(sorted({item.parent_obfuscated_code_sha256 for item in occurrences})),
                "sample_names_json": json.dumps(sorted({item.representative_sample_name for item in occurrences})),
            }
        )
    pd.DataFrame(chunk_manifest_rows).to_csv(out_dir / "chunk_manifest.csv", index=False)

    cluster_summary_df.to_csv(out_dir / "cluster_summary.csv", index=False)
    pairwise_df.to_csv(out_dir / "pairwise_similarity_vs_elo.csv", index=False)

    chunk_sha_order = sorted(chunk_embeddings_by_sha)
    np.savez_compressed(
        out_dir / "chunk_embeddings.npz",
        embeddings=np.vstack([np.asarray(chunk_embeddings_by_sha[chunk_sha], dtype=np.float32) for chunk_sha in chunk_sha_order]).astype(np.float32, copy=False),
        chunk_sha256=np.asarray(chunk_sha_order, dtype=object),
    )
    np.savez_compressed(
        out_dir / "unique_code_embeddings.npz",
        embeddings=unique_embeddings.astype(np.float32),
        obfuscated_code_sha256=np.asarray([record.obfuscated_code_sha256 for record in unique_records], dtype=object),
        cluster_id=unique_labels.astype(np.int32),
    )
    np.savez_compressed(
        out_dir / "sample_code_embeddings.npz",
        embeddings=sample_embeddings.astype(np.float32),
        sample_name=np.asarray([record.sample_name for record in sample_records], dtype=object),
        cluster_id=sample_labels.astype(np.int32),
    )

    with (out_dir / "cluster_themes.json").open("w", encoding="utf-8") as handle:
        json.dump(
            [
                {"cluster_id": int(cluster_id), "theme_label": theme}
                for cluster_id, theme in sorted(cluster_themes.items())
            ],
            handle,
            indent=2,
            sort_keys=True,
        )
    with (out_dir / "run_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)

    _write_obfuscated_sources(out_dir, unique_records)

    sha_to_elo: dict[str, list[float]] = defaultdict(list)
    for record in sample_records:
        sha_to_elo[record.obfuscated_code_sha256].append(float(record.elo))
    unique_mean_elo = np.asarray([float(np.mean(sha_to_elo[record.obfuscated_code_sha256])) for record in unique_records], dtype=np.float64)

    _plot_cluster_projection(
        out_dir / "cluster_projection.png",
        unique_records=unique_records,
        projection_2d=unique_projection,
        unique_labels=unique_labels,
        cluster_themes=cluster_themes,
        cluster_label_overrides=cluster_label_overrides,
    )
    _plot_cluster_projection_by_elo(
        out_dir / "cluster_projection_by_elo.png",
        unique_records=unique_records,
        projection_2d=unique_projection,
        unique_labels=unique_labels,
        unique_mean_elo=unique_mean_elo,
        cluster_themes=cluster_themes,
        cluster_label_overrides=cluster_label_overrides,
    )
    _plot_cluster_projection_by_model(
        out_dir / "cluster_projection_by_model.png",
        sample_records=sample_records,
        sample_projection=sample_projection,
        sample_labels=sample_labels,
        cluster_themes=cluster_themes,
        cluster_label_overrides=cluster_label_overrides,
        legend_panel=legend_panel,
    )
    _plot_similarity_vs_elo_gap(
        out_dir / "code_similarity_vs_elo_gap.png",
        pairwise_df=pairwise_df,
        correlation_summary=pairwise_elo_corr,
        plot_limit=summary["config"]["pairwise_plot_limit"],
        random_seed=summary["config"]["random_seed"],
    )
    _plot_elo_by_cluster(
        out_dir / "elo_by_cluster_boxplot.png",
        sample_records=sample_records,
        sample_labels=sample_labels,
        cluster_themes=cluster_themes,
        cluster_mean_elo_r2=summary["metrics"]["cluster_mean_elo_r2"],
        cluster_label_overrides=cluster_label_overrides,
    )
    _plot_similarity_heatmap(
        out_dir / "code_similarity_heatmap_cluster_order.png",
        sample_records=sample_records,
        sample_embeddings=sample_embeddings,
        sample_labels=sample_labels,
        order_mode="cluster_then_elo",
    )
    _plot_similarity_heatmap(
        out_dir / "code_similarity_heatmap_elo_order.png",
        sample_records=sample_records,
        sample_embeddings=sample_embeddings,
        sample_labels=sample_labels,
        order_mode="elo",
    )


def main() -> None:
    args = parse_args()
    resolved_model = _normalize_openrouter_model(args.model)
    if args.in_pkl is not None:
        analysis_input = _load_from_pkl(_resolve_path(args.in_pkl), args.result_key, args.mode)
    else:
        analysis_input = _load_from_match_json(
            _resolve_path(args.match_json),
            game=str(args.game),
            world=str(args.world),
            mode=args.mode,
            rating_system=args.rating_system,
        )

    out_dir = _resolve_path(args.out_dir) if args.out_dir else _default_out_dir(args, analysis_input)
    if args.clear_out_dir and out_dir.exists():
        shutil.rmtree(out_dir)

    sample_records = _load_sample_records(analysis_input)
    unique_records = _build_unique_records(sample_records)
    if len(unique_records) < 2:
        raise ValueError("Need at least two distinct obfuscated code blobs to cluster.")

    encoder = _load_tiktoken_encoder(resolved_model)
    out_dir.mkdir(parents=True, exist_ok=True)
    forced_resplit_targets = _load_forced_resplit_targets_from_progress(
        out_dir,
        model=resolved_model,
        max_input_tokens=args.max_input_tokens,
    )
    if forced_resplit_targets:
        print(
            f"Detected prior oversize chunk failure; forcing smaller resplit for "
            f"{len(forced_resplit_targets)} chunk(s) before retry"
        )

    while True:
        chunk_instances, chunks_by_code_sha, estimated_tokens_by_chunk_sha = _build_chunk_instances(
            unique_records,
            encoder=encoder,
            chars_per_token=args.chars_per_token,
            max_input_tokens=args.max_input_tokens,
            chunk_overlap_tokens=args.chunk_overlap_tokens,
            forced_resplit_targets=forced_resplit_targets,
        )
        corpus_summary = _summarize_corpus(
            sample_records,
            unique_records,
            chunk_instances,
            estimated_tokens_by_chunk_sha,
            model=resolved_model,
            out_dir=out_dir,
        )
        _print_corpus_summary(corpus_summary)
        if args.estimate_only:
            return

        try:
            chunk_embeddings_by_sha = _embed_unique_chunks(
                chunk_instances,
                estimated_tokens_by_chunk_sha,
                out_dir=out_dir,
                model=resolved_model,
                max_input_tokens=args.max_input_tokens,
                batch_size=args.batch_size,
                max_batch_estimated_tokens=args.max_batch_estimated_tokens,
                retry_limit=args.retry_limit,
                retry_base_seconds=args.retry_base_seconds,
            )
            break
        except ChunkResplitRequired as exc:
            forced_resplit_targets.update(exc.resplit_targets)
            print(str(exc))
            continue

    cluster_label_overrides = _cluster_label_overrides(args.cluster_labels_json)
    unique_embeddings = _pooled_document_embeddings(unique_records, chunks_by_code_sha, chunk_embeddings_by_sha)
    embedding_dimension = int(unique_embeddings.shape[1])
    similarity_unique = _cosine_similarity_matrix(unique_embeddings)

    if args.n_clusters is None:
        selected_n_clusters, silhouette_by_k = _choose_cluster_count(
            unique_embeddings,
            similarity_unique,
            args.k_min,
            args.k_max,
            args.random_seed,
        )
    else:
        selected_n_clusters = args.n_clusters
        silhouette_by_k = {}

    unique_centroids, unique_labels = _run_kmeans(unique_embeddings, selected_n_clusters, args.random_seed)
    unique_distances = _cluster_distances(unique_embeddings, unique_labels, unique_centroids)
    unique_projection = _projection_2d(unique_embeddings)
    silhouette = _silhouette_score_from_similarity(similarity_unique, unique_labels)
    cluster_themes = _build_cluster_themes(unique_records, unique_labels, args.top_theme_terms)

    sample_index_by_sha = {record.obfuscated_code_sha256: idx for idx, record in enumerate(unique_records)}
    sample_unique_indices = np.asarray(
        [sample_index_by_sha[record.obfuscated_code_sha256] for record in sample_records],
        dtype=np.int32,
    )
    sample_embeddings = unique_embeddings[sample_unique_indices]
    sample_labels = unique_labels[sample_unique_indices]
    sample_distances = unique_distances[sample_unique_indices]
    sample_projection = unique_projection[sample_unique_indices]

    latent_projection_corr = _plot_latent_dimensions_vs_elo(
        out_dir / "latent_dimensions_vs_elo.png",
        sample_records=sample_records,
        sample_projection=sample_projection,
        sample_labels=sample_labels,
    )

    pairwise_df = _pairwise_dataframe(sample_records, sample_embeddings, sample_labels)
    pairwise_elo_corr = _correlation_triplet(pairwise_df, "cosine_similarity", "neg_elo_gap")
    pairwise_rank_corr = _correlation_triplet(pairwise_df, "cosine_similarity", "neg_rank_gap")
    same_cluster_elo_corr = _correlation_triplet(pairwise_df, "same_cluster", "neg_elo_gap")
    cluster_summary_df = _cluster_summary_dataframe(sample_records, sample_labels, sample_distances, cluster_themes)
    summary_metrics = _summary_metrics(sample_records, unique_records, pairwise_df, sample_labels)

    summary = {
        "config": {
            "input_label": analysis_input.label,
            "game": analysis_input.game,
            "world": analysis_input.world,
            "mode": analysis_input.mode,
            "rating_system": analysis_input.rating_system,
            "embedding_provider": OPENROUTER_PROVIDER,
            "embedding_model": resolved_model,
            "embedding_model_requested": args.model,
            "embedding_dimension": embedding_dimension,
            "out_dir": str(out_dir),
            "chars_per_token": args.chars_per_token,
            "max_input_tokens": args.max_input_tokens,
            "chunk_overlap_tokens": args.chunk_overlap_tokens,
            "batch_size": args.batch_size,
            "max_batch_estimated_tokens": args.max_batch_estimated_tokens,
            "selected_n_clusters": int(selected_n_clusters),
            "k_min": args.k_min,
            "k_max": args.k_max,
            "random_seed": args.random_seed,
            "pairwise_plot_limit": args.pairwise_plot_limit,
        },
        "corpus": corpus_summary,
        "cluster_quality": {
            "silhouette": float(silhouette),
            "silhouette_by_k": silhouette_by_k,
        },
        "correlations": {
            "code_similarity_vs_negative_elo_gap": pairwise_elo_corr,
            "code_similarity_vs_negative_rank_gap": pairwise_rank_corr,
            "same_cluster_vs_negative_elo_gap": same_cluster_elo_corr,
            "latent_projection_vs_elo": latent_projection_corr,
        },
        "metrics": summary_metrics,
        "cluster_themes": [
            {"cluster_id": int(cluster_id), "theme_label": theme}
            for cluster_id, theme in sorted(cluster_themes.items())
        ],
        "cluster_label_overrides": cluster_label_overrides,
    }

    _write_outputs(
        out_dir,
        analysis_input=analysis_input,
        sample_records=sample_records,
        unique_records=unique_records,
        chunk_instances=chunk_instances,
        estimated_tokens_by_chunk_sha=estimated_tokens_by_chunk_sha,
        chunk_embeddings_by_sha=chunk_embeddings_by_sha,
        unique_embeddings=unique_embeddings,
        sample_embeddings=sample_embeddings,
        unique_labels=unique_labels,
        sample_labels=sample_labels,
        unique_distances=unique_distances,
        sample_distances=sample_distances,
        unique_projection=unique_projection,
        sample_projection=sample_projection,
        cluster_themes=cluster_themes,
        cluster_label_overrides=cluster_label_overrides,
        cluster_summary_df=cluster_summary_df,
        pairwise_df=pairwise_df,
        summary=summary,
        pairwise_elo_corr=pairwise_elo_corr,
        legend_panel=args.legend_panel,
    )

    print(
        f"Loaded {len(sample_records)} {analysis_input.mode} samples "
        f"({len(unique_records)} unique obfuscated code blobs) for {analysis_input.label} "
        f"[{analysis_input.game} {analysis_input.world}]"
    )
    print(f"Selected {selected_n_clusters} clusters | silhouette={summary['cluster_quality']['silhouette']:.3f}")
    print(
        "Code similarity vs -Elo gap: "
        f"pearson={pairwise_elo_corr['pearson']:.3f}, "
        f"spearman={pairwise_elo_corr['spearman']:.3f}, "
        f"kendall={pairwise_elo_corr['kendall']:.3f}"
    )
    print(f"Wrote outputs to {out_dir}")


if __name__ == "__main__":
    main()
