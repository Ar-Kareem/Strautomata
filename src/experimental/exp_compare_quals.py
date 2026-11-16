#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from game_arena import utils as arena_utils


ROOT_DIR = arena_utils.get_root_path()


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="High-level comparison for two quals match JSON files.")
    parser.add_argument("--json_a", type=str, required=True, help="Path to first quals json.")
    parser.add_argument("--json_b", type=str, required=True, help="Path to second quals json.")
    parser.add_argument("--top_n", type=int, default=50, help="How many non-zero-distance pairs to print (<=0 prints all).")
    parser.add_argument(
        "--focus-single",
        action="store_true",
        default=False,
        help="Only consider pairs where either A or B is 100%% in a single bucket among {win0, win1, draw, timeout, error}.",
    )
    return parser.parse_args()


def _pair_key(name0: str, name1: str) -> tuple[str, str]:
    return name0, name1


def _classify_match(match: dict[str, Any]) -> str:
    winner = match.get("winner")
    if isinstance(winner, str):
        winner_l = winner.lower().strip()
        if winner_l == "timeout":
            return "timeout"
        if winner_l in {"error", "exception"}:
            return "error"
        if winner_l in {"draw", "tie"}:
            return "draw"
    if winner == "timeout" or match.get("timeout_hit") is not None:
        return "timeout"
    if match.get("exception"):
        return "error"
    if winner is None:
        return "draw"
    if winner in (0, 0.0):
        return "win0"
    if winner in (1, 1.0):
        return "win1"
    return f"other:{winner}"


@dataclass
class QualsStats:
    path: Path
    n_matches: int
    n_bots: int
    n_pairs: int
    pair_counts: Counter[tuple[str, str]]
    outcome_counts: Counter[str]
    pair_outcomes: dict[tuple[str, str], Counter[str]]


def _load_stats(path: Path) -> QualsStats:
    with path.open("r") as f:
        payload = json.load(f)

    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON payload in {path}: expected dict.")
    match_results = payload.get("match_results")
    if not isinstance(match_results, list):
        raise ValueError(f"Invalid JSON payload in {path}: missing list key 'match_results'.")

    pair_counts: Counter[tuple[str, str]] = Counter()
    outcome_counts: Counter[str] = Counter()
    pair_outcomes: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    bots = set()

    for match in match_results:
        if not isinstance(match, dict):
            continue
        name0 = str(match.get("name0"))
        name1 = str(match.get("name1"))
        bots.add(name0)
        bots.add(name1)
        pair = _pair_key(name0, name1)
        pair_counts[pair] += 1
        outcome = _classify_match(match)
        outcome_counts[outcome] += 1
        pair_outcomes[pair][outcome] += 1

    return QualsStats(
        path=path,
        n_matches=len(match_results),
        n_bots=len(bots),
        n_pairs=len(pair_counts),
        pair_counts=pair_counts,
        outcome_counts=outcome_counts,
        pair_outcomes=dict(pair_outcomes),
    )


def _fmt_counter(counter: Counter[str], *, top_n: int = 20) -> str:
    if not counter:
        return "{}"
    items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))[:top_n]
    return "{ " + ", ".join(f"{k}: {v}" for k, v in items) + " }"


def _print_summary(label: str, stats: QualsStats) -> None:
    print(f"\n=== {label} ===")
    print(f"path: {stats.path}")
    print(f"matches={stats.n_matches}, bots={stats.n_bots}, ordered_pairs={stats.n_pairs}")
    print(f"outcomes(top): {_fmt_counter(stats.outcome_counts)}")


def _has_single_bucket_100(counter: Counter[str], total: int, stat_keys: list[str]) -> bool:
    if total <= 0:
        return False
    return any(int(counter.get(k, 0)) == total for k in stat_keys)


def _pair_is_focus_single(pair: tuple[str, str], a: QualsStats, b: QualsStats, stat_keys: list[str]) -> bool:
    oa = a.pair_outcomes.get(pair, Counter())
    ob = b.pair_outcomes.get(pair, Counter())
    ca = a.pair_counts.get(pair, 0)
    cb = b.pair_counts.get(pair, 0)
    return _has_single_bucket_100(oa, ca, stat_keys) or _has_single_bucket_100(ob, cb, stat_keys)


def _print_pair_coverage(a: QualsStats, b: QualsStats, top_n: int, focus_single: bool) -> None:
    stat_keys = ["win0", "win1", "draw", "timeout", "error"]
    pairs_a = set(a.pair_counts.keys())
    pairs_b = set(b.pair_counts.keys())
    if focus_single:
        pairs_a = {p for p in pairs_a if _pair_is_focus_single(p, a, b, stat_keys)}
        pairs_b = {p for p in pairs_b if _pair_is_focus_single(p, a, b, stat_keys)}
    common = pairs_a & pairs_b
    only_a = pairs_a - pairs_b
    only_b = pairs_b - pairs_a

    print("\n=== Pair Coverage ===")
    if focus_single:
        print("focus: single-bucket-100 pairs only")
    print(
        f"common_pairs={len(common)}, only_in_a={len(only_a)}, only_in_b={len(only_b)}"
    )
    if only_a:
        print("only_in_a:")
        for p in sorted(only_a)[:top_n if top_n > 0 else None]:
            print(f"  {p[0]}  <->  {p[1]}  (count_a={a.pair_counts[p]})")
    if only_b:
        print("only_in_b:")
        for p in sorted(only_b)[:top_n if top_n > 0 else None]:
            print(f"  {p[0]}  <->  {p[1]}  (count_b={b.pair_counts[p]})")

    diffs: list[tuple[int, tuple[str, str], int, int]] = []
    for pair in common:
        ca = a.pair_counts[pair]
        cb = b.pair_counts[pair]
        if ca != cb:
            diffs.append((abs(ca - cb), pair, ca, cb))
    diffs.sort(key=lambda x: (-x[0], x[1]))

    print(
        f"common_pairs_with_same_count={len(common) - len(diffs)}, "
        f"common_pairs_with_count_diff={len(diffs)}"
    )
    if diffs:
        print("pair-count diffs:")
        for _, pair, ca, cb in diffs[:top_n if top_n > 0 else None]:
            print(f"  {pair[0]}  <->  {pair[1]}: A={ca}, B={cb}, delta={ca - cb:+d}")


def _pair_stat_value(counter: Counter[str], total: int, key: str) -> float:
    if total <= 0:
        return 0.0
    return 100.0 * float(counter.get(key, 0)) / float(total)


def _print_pair_stat_comparison(a: QualsStats, b: QualsStats, top_n: int, focus_single: bool) -> None:
    print("\n=== Per-Pair Stats (ordered: name0,name1, mode=raw) ===")
    all_pairs = sorted(set(a.pair_counts.keys()) | set(b.pair_counts.keys()))
    stat_keys = ["win0", "win1", "draw", "timeout", "error"]
    if focus_single:
        all_pairs = [p for p in all_pairs if _pair_is_focus_single(p, a, b, stat_keys)]
        print("focus: single-bucket-100 pairs only")
    pct_zero_pairs = 0
    nonzero_rows: list[tuple[int, tuple[str, str], int, int, list[str], Counter[str], Counter[str]]] = []
    for pair in all_pairs:
        oa = a.pair_outcomes.get(pair, Counter())
        ob = b.pair_outcomes.get(pair, Counter())
        ca = a.pair_counts.get(pair, 0)
        cb = b.pair_counts.get(pair, 0)
        all_keys = sorted(set(stat_keys) | set(oa.keys()) | set(ob.keys()))
        raw_deltas = {k: int(oa.get(k, 0)) - int(ob.get(k, 0)) for k in all_keys}
        delta_l1 = sum(abs(raw_deltas[k]) for k in all_keys)

        pct_zero = True
        for k in stat_keys:
            da = _pair_stat_value(oa, ca, k)
            db = _pair_stat_value(ob, cb, k)
            if abs(da - db) >= 1e-12:
                pct_zero = False
                break
        if pct_zero:
            pct_zero_pairs += 1
            continue
        nonzero_rows.append((delta_l1, pair, ca, cb, all_keys, oa, ob))

    nonzero_rows.sort(key=lambda x: (-x[0], x[1]))
    rows_to_print = nonzero_rows[:top_n if top_n > 0 else None]
    for delta_l1, pair, ca, cb, all_keys, oa, ob in rows_to_print:
        print(
            f"\nPAIR {pair[0]}  vs  {pair[1]} | "
            f"count: A={ca}, B={cb}, delta={ca-cb:+d}, stat_distance={delta_l1}"
        )
        for k in all_keys:
            va = int(oa.get(k, 0))
            vb = int(ob.get(k, 0))
            delta = va - vb
            print(f"  {k}: A={va}, B={vb}, delta={delta:+d}")

    hist_keys = [int(round(distance)) for distance, *_ in nonzero_rows]
    hist = Counter(hist_keys)
    print("\n=== Distance Histogram ===")
    if hist:
        max_count = max(hist.values())
        max_bar = 40
        count_width = max(len(str(v)) for v in hist.values())
        for distance in sorted(hist.keys(), reverse=True):
            count = hist[distance]
            bar_len = max(1, round((count / max_count) * max_bar))
            bar = "#" * bar_len
            dist_label = f"{int(distance):>3}"
            print(f"{dist_label}: {bar:<{max_bar}} {count:>{count_width}}")
    else:
        print("(empty)")
    print(f"\nignored pairs (percentage deltas for win0/win1/draw/timeout/error are all 0): {pct_zero_pairs}")
    if focus_single:
        print(f"focus-single candidate pairs: {len(all_pairs)}")
    print(f"non-zero-distance pairs total: {len(nonzero_rows)}")
    print(f"printed pairs: {len(rows_to_print)}")


def main() -> None:
    args = _parse_args()
    path_a = _resolve_path(args.json_a)
    path_b = _resolve_path(args.json_b)
    if not path_a.exists():
        raise FileNotFoundError(f"--json_a not found: {path_a}")
    if not path_b.exists():
        raise FileNotFoundError(f"--json_b not found: {path_b}")

    stats_a = _load_stats(path_a)
    stats_b = _load_stats(path_b)

    _print_summary("A", stats_a)
    _print_summary("B", stats_b)
    _print_pair_coverage(stats_a, stats_b, args.top_n, args.focus_single)
    _print_pair_stat_comparison(stats_a, stats_b, args.top_n, args.focus_single)


if __name__ == "__main__":
    main()
