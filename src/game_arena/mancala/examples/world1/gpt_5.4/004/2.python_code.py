
from __future__ import annotations

import time
from typing import List, Tuple

INF = 10**18

# Precomputed opposite house mapping for captures
OPP = [5, 4, 3, 2, 1, 0]


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal move index 0..5 for standard 6-house Kalah.
    `you` and `opponent` are length-7 lists, with index 6 the store.
    """
    # Always keep a legal fallback
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0  # should never happen by problem statement
    fallback = _greedy_fallback(you, opponent, legal)

    start = time.perf_counter()
    # Conservative time budget
    time_limit = 0.92

    best_move = fallback
    best_val = -INF

    # Iterative deepening
    depth = 1
    try:
        while True:
            if time.perf_counter() - start > time_limit:
                break
            val, move = _search_root(you, opponent, depth, start, time_limit, fallback)
            if move is not None:
                best_move = move
                best_val = val
            depth += 1
            # Late-game positions are smaller; allow deeper naturally by time.
    except TimeoutError:
        pass

    # Guarantee legality
    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return fallback


def _greedy_fallback(you: List[int], opp: List[int], legal: List[int]) -> int:
    """
    Very fast legal fallback: prefer immediate extra turn, then biggest tactical gain.
    """
    best_score = -10**18
    best_move = legal[0]
    for m in legal:
        ny, no, extra = _apply_move(you, opp, m)
        score = (ny[6] - no[6]) * 100 + (1 if extra else 0) * 80
        # Small bias toward leaving opponent fewer tactical resources
        score += sum(ny[:6]) - sum(no[:6])
        if score > best_score:
            best_score = score
            best_move = m
    return best_move


def _search_root(you: List[int], opp: List[int], depth: int, start: float, time_limit: float, fallback: int) -> Tuple[int, int | None]:
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return -INF, fallback

    ordered = _ordered_moves(you, opp, legal, maximizing=True)

    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = ordered[0]

    for m in ordered:
        _check_time(start, time_limit)
        ny, no, extra = _apply_move(you, opp, m)
        if _is_terminal(ny, no):
            val = _terminal_value(ny, no)
        else:
            if extra:
                val = _alphabeta(ny, no, depth - 1, alpha, beta, True, start, time_limit)
            else:
                val = _alphabeta(no, ny, depth - 1, alpha, beta, False, start, time_limit)
        if val > best_val:
            best_val = val
            best_move = m
        if best_val > alpha:
            alpha = best_val

    return best_val, best_move


def _alphabeta(you: List[int], opp: List[int], depth: int, alpha: int, beta: int, maximizing: bool,
               start: float, time_limit: float) -> int:
    _check_time(start, time_limit)

    if _is_terminal(you, opp):
        return _terminal_value(you, opp)

    if depth <= 0:
        return _evaluate(you, opp, maximizing)

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return _terminal_value(you, opp)

    ordered = _ordered_moves(you, opp, legal, maximizing)

    if maximizing:
        value = -INF
        for m in ordered:
            ny, no, extra = _apply_move(you, opp, m)
            if _is_terminal(ny, no):
                v = _terminal_value(ny, no)
            else:
                if extra:
                    v = _alphabeta(ny, no, depth - 1, alpha, beta, True, start, time_limit)
                else:
                    v = _alphabeta(no, ny, depth - 1, alpha, beta, False, start, time_limit)
            if v > value:
                value = v
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value
    else:
        value = INF
        for m in ordered:
            ny, no, extra = _apply_move(you, opp, m)
            if _is_terminal(ny, no):
                v = _terminal_value(no, ny) if False else _terminal_value(ny, no)
            else:
                if extra:
                    v = _alphabeta(ny, no, depth - 1, alpha, beta, False, start, time_limit)
                else:
                    v = _alphabeta(no, ny, depth - 1, alpha, beta, True, start, time_limit)
            if v < value:
                value = v
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return value


def _ordered_moves(you: List[int], opp: List[int], legal: List[int], maximizing: bool) -> List[int]:
    scored = []
    for m in legal:
        ny, no, extra = _apply_move(you, opp, m)
        # Tactical move ordering: extra turns, store gain, captures, endgame effects
        store_gain = ny[6] - you[6]
        opp_store_gain = no[6] - opp[6]
        score = 0
        score += 1000 if extra else 0
        score += 60 * store_gain
        score -= 20 * opp_store_gain

        # Estimate capture occurrence by gained seeds beyond sow/store baseline
        score += 5 * (sum(you[:6]) + you[6] + sum(opp[:6]) + opp[6] - (sum(ny[:6]) + ny[6] + sum(no[:6]) + no[6]))
        # Small positional heuristic
        score += (ny[6] - no[6]) * 10
        score += sum(ny[:6]) - sum(no[:6])

        # For minimizing side, reverse preference so ordering still helps pruning
        if not maximizing:
            score = -score
        scored.append((score, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def _apply_move(you: List[int], opp: List[int], move: int) -> Tuple[List[int], List[int], bool]:
    """
    Apply a move for current player `you` against `opp`.
    Returns (new_you, new_opp, extra_turn).
    End-of-game sweep is applied if triggered.
    """
    ny = you[:]
    no = opp[:]

    seeds = ny[move]
    ny[move] = 0
    side = 0  # 0 => your side incl store, 1 => opponent houses only
    idx = move + 1
    last_side = None
    last_idx = None

    while seeds > 0:
        if side == 0:
            while idx <= 6 and seeds > 0:
                ny[idx] += 1
                seeds -= 1
                last_side = 0
                last_idx = idx
                idx += 1
            if seeds == 0:
                break
            side = 1
            idx = 0
        else:
            while idx <= 5 and seeds > 0:
                no[idx] += 1
                seeds -= 1
                last_side = 1
                last_idx = idx
                idx += 1
            if seeds == 0:
                break
            side = 0
            idx = 0

    extra = (last_side == 0 and last_idx == 6)

    # Capture: last seed in your empty house, opposite has seeds
    if last_side == 0 and last_idx is not None and 0 <= last_idx <= 5:
        if ny[last_idx] == 1 and no[OPP[last_idx]] > 0:
            ny[6] += 1 + no[OPP[last_idx]]
            ny[last_idx] = 0
            no[OPP[last_idx]] = 0

    # Endgame sweep
    if sum(ny[:6]) == 0:
        no[6] += sum(no[:6])
        for i in range(6):
            no[i] = 0
    elif sum(no[:6]) == 0:
        ny[6] += sum(ny[:6])
        for i in range(6):
            ny[i] = 0

    return ny, no, extra


def _is_terminal(you: List[int], opp: List[int]) -> bool:
    return sum(you[:6]) == 0 or sum(opp[:6]) == 0


def _terminal_value(you: List[int], opp: List[int]) -> int:
    """
    Absolute terminal value from the perspective of the original maximizing player
    is represented by current orientation only through store differential.
    Since swaps happen in recursion, callers preserve minimax semantics.
    """
    # Very large margin prioritizing win/loss over all heuristic details
    return (you[6] - opp[6]) * 1_000_000


def _evaluate(you: List[int], opp: List[int], maximizing: bool) -> int:
    """
    Heuristic evaluation in current orientation.
    If maximizing=True, positive is good for `you`.
    If maximizing=False, positive is still good for the original root player,
    so we negate the current-side evaluation.
    """
    cur = _static_eval_current(you, opp)
    return cur if maximizing else -cur


def _static_eval_current(you: List[int], opp: List[int]) -> int:
    # Immediate store lead dominates
    store_diff = you[6] - opp[6]
    board_diff = sum(you[:6]) - sum(opp[:6])

    # Extra-turn opportunities
    extra_count = 0
    for i in range(6):
        s = you[i]
        if s > 0 and (i + s) % 13 == 6:
            extra_count += 1

    opp_extra_count = 0
    for i in range(6):
        s = opp[i]
        if s > 0 and (i + s) % 13 == 6:
            opp_extra_count += 1

    # Capture opportunities estimate
    cap_potential = 0
    for i in range(6):
        s = you[i]
        if s <= 0:
            continue
        landing = _landing_pos_from_house(i, s)
        if landing is not None:
            side, idx = landing
            if side == 0 and 0 <= idx <= 5 and you[idx] == 0 and opp[OPP[idx]] > 0:
                cap_potential += 1 + opp[OPP[idx]]

    opp_cap_potential = 0
    for i in range(6):
        s = opp[i]
        if s <= 0:
            continue
        landing = _landing_pos_from_house(i, s)
        if landing is not None:
            side, idx = landing
            if side == 0 and 0 <= idx <= 5 and opp[idx] == 0 and you[OPP[idx]] > 0:
                opp_cap_potential += 1 + you[OPP[idx]]

    # Endgame pressure: when one side is sparse, store advantage matters even more
    your_side = sum(you[:6])
    opp_side = sum(opp[:6])
    low_seed_phase = 48 - (your_side + opp_side)

    val = 0
    val += 120 * store_diff
    val += 8 * board_diff
    val += 35 * extra_count
    val -= 35 * opp_extra_count
    val += 12 * cap_potential
    val -= 12 * opp_cap_potential

    # Prefer keeping playable seeds on our side and denying large opponent pits
    val += 2 * sum(1 for x in you[:6] if x > 0)
    val -= 2 * sum(1 for x in opp[:6] if x > 0)
    val -= sum(max(0, x - 6) for x in opp[:6])
    val += sum(max(0, x - 6) for x in you[:6]) // 2

    # Late-game store lead amplification
    val += low_seed_phase * store_diff * 3

    return val


def _landing_pos_from_house(i: int, seeds: int):
    """
    Return landing position (side, idx) for sowing `seeds` from your house i
    in the current player's orientation, skipping opponent store.
    side 0 = your side incl store 0..6, side 1 = opponent houses 0..5.
    """
    pos = i
    side = 0
    s = seeds
    while s > 0:
        if side == 0:
            pos += 1
            if pos == 7:
                side = 1
                pos = 0
            else:
                s -= 1
        else:
            if pos == 6:
                side = 0
                pos = 0
                continue
            pos += 1
            if pos == 6:
                side = 0
                pos = 0
            s -= 1
    return side, pos


def _check_time(start: float, time_limit: float):
    if time.perf_counter() - start > time_limit:
        raise TimeoutError
