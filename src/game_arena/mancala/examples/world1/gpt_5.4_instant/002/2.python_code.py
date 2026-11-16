
from __future__ import annotations

from typing import List, Tuple, Dict
import time

# Kalah policy for 6 houses + store per side.
# API:
#   def policy(you: list[int], opponent: list[int]) -> int


HOUSES = 6
STORE = 6
INF = 10**18


def _legal_moves(you: List[int]) -> List[int]:
    return [i for i in range(HOUSES) if you[i] > 0]


def _terminal(you: List[int], opp: List[int]) -> bool:
    return sum(you[:HOUSES]) == 0 or sum(opp[:HOUSES]) == 0


def _finalize_if_terminal(you: List[int], opp: List[int]) -> None:
    sy = sum(you[:HOUSES])
    so = sum(opp[:HOUSES])
    if sy == 0 and so > 0:
        opp[STORE] += so
        for i in range(HOUSES):
            opp[i] = 0
    elif so == 0 and sy > 0:
        you[STORE] += sy
        for i in range(HOUSES):
            you[i] = 0


def _simulate_move(you: List[int], opp: List[int], move: int) -> Tuple[List[int], List[int], bool]:
    """
    Returns (new_you, new_opp, extra_turn), from current player's perspective.
    """
    y = you[:]
    o = opp[:]
    seeds = y[move]
    y[move] = 0

    side = 0  # 0 = you, 1 = opponent
    idx = move + 1
    last_side = None
    last_idx = None

    while seeds > 0:
        if side == 0:
            while idx <= STORE and seeds > 0:
                y[idx] += 1
                seeds -= 1
                last_side = 0
                last_idx = idx
                if seeds == 0:
                    break
                idx += 1
            if seeds == 0:
                break
            side = 1
            idx = 0
        else:
            while idx < STORE and seeds > 0:  # skip opponent store
                o[idx] += 1
                seeds -= 1
                last_side = 1
                last_idx = idx
                if seeds == 0:
                    break
                idx += 1
            if seeds == 0:
                break
            side = 0
            idx = 0

    extra = (last_side == 0 and last_idx == STORE)

    # Capture: last seed landed in your empty house and opposite had stones.
    if last_side == 0 and last_idx is not None and 0 <= last_idx < HOUSES:
        if y[last_idx] == 1 and o[HOUSES - 1 - last_idx] > 0:
            y[STORE] += 1 + o[HOUSES - 1 - last_idx]
            y[last_idx] = 0
            o[HOUSES - 1 - last_idx] = 0

    _finalize_if_terminal(y, o)
    return y, o, extra


def _count_extra_turn_moves(you: List[int]) -> int:
    c = 0
    for i in range(HOUSES):
        s = you[i]
        if s <= 0:
            continue
        # Last position index in 13-slot cycle excluding opponent store.
        # Starting from house i, after removing seeds, first drop is next slot.
        # Extra turn iff last seed lands in own store.
        # Distance to store from house i is (STORE - i).
        if s % 13 == (STORE - i) % 13:
            c += 1
    return c


def _immediate_capture_gain(you: List[int], opp: List[int], move: int) -> int:
    y = you[:]
    o = opp[:]
    seeds = y[move]
    if seeds <= 0:
        return 0
    y[move] = 0

    side = 0
    idx = move + 1
    last_side = None
    last_idx = None
    while seeds > 0:
        if side == 0:
            while idx <= STORE and seeds > 0:
                before = y[idx]
                y[idx] += 1
                seeds -= 1
                last_side = 0
                last_idx = idx
                last_before = before
                if seeds == 0:
                    break
                idx += 1
            if seeds == 0:
                break
            side = 1
            idx = 0
        else:
            while idx < STORE and seeds > 0:
                o[idx] += 1
                seeds -= 1
                last_side = 1
                last_idx = idx
                if seeds == 0:
                    break
                idx += 1
            if seeds == 0:
                break
            side = 0
            idx = 0

    if last_side == 0 and last_idx is not None and 0 <= last_idx < HOUSES:
        if y[last_idx] == 1 and o[HOUSES - 1 - last_idx] > 0:
            return 1 + o[HOUSES - 1 - last_idx]
    return 0


def _vulnerability_penalty(you: List[int], opp: List[int]) -> int:
    """
    Approximate how many stones are vulnerable to immediate opponent captures.
    Since evaluation is from current player's perspective, this penalizes our side.
    """
    pen = 0
    # Consider each opponent move and whether it can land on an empty opp house
    # in their perspective, which corresponds to our houses being capturable.
    # To reuse logic, swap sides.
    for m in range(HOUSES):
        if opp[m] <= 0:
            continue
        gain = _immediate_capture_gain(opp, you, m)
        if gain > 0:
            pen += gain
    return pen


def _evaluate(you: List[int], opp: List[int]) -> int:
    if _terminal(you, opp):
        y = you[:]
        o = opp[:]
        _finalize_if_terminal(y, o)
        diff = y[STORE] - o[STORE]
        if diff > 0:
            return 10_000_000 + diff
        if diff < 0:
            return -10_000_000 + diff
        return 0

    store_diff = 40 * (you[STORE] - opp[STORE])
    side_diff = 3 * (sum(you[:HOUSES]) - sum(opp[:HOUSES]))

    extra_me = 8 * _count_extra_turn_moves(you)
    extra_opp = 8 * _count_extra_turn_moves(opp)

    cap_me = 0
    for m in range(HOUSES):
        if you[m] > 0:
            cap_me = max(cap_me, _immediate_capture_gain(you, opp, m))
    cap_opp = 0
    for m in range(HOUSES):
        if opp[m] > 0:
            cap_opp = max(cap_opp, _immediate_capture_gain(opp, you, m))

    vuln = _vulnerability_penalty(you, opp)

    empties_me = sum(1 for x in you[:HOUSES] if x == 0)
    empties_opp = sum(1 for x in opp[:HOUSES] if x == 0)

    # Endgame emphasis.
    remaining = sum(you[:HOUSES]) + sum(opp[:HOUSES])
    endgame_weight = 1 if remaining > 18 else 2 if remaining > 10 else 4

    return (
        store_diff
        + side_diff * endgame_weight
        + extra_me
        - extra_opp
        + 12 * cap_me
        - 12 * cap_opp
        - 4 * vuln
        - 2 * empties_me
        + 1 * empties_opp
    )


def _move_order(you: List[int], opp: List[int], moves: List[int]) -> List[int]:
    scored = []
    for m in moves:
        s = 0
        seeds = you[m]
        if seeds % 13 == (STORE - m) % 13:
            s += 10_000  # extra turn
        s += 500 * _immediate_capture_gain(you, opp, m)
        # Prefer moves from right side slightly; often stronger tactically near store.
        s += 5 * m
        # Mild preference for larger sow if no tactical cue.
        s += min(seeds, 20)
        scored.append((s, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


_TT: Dict[Tuple[Tuple[int, ...], Tuple[int, ...], int, bool], Tuple[int, int]] = {}
_START = 0.0
_LIMIT = 0.92


def _time_up() -> bool:
    return (time.perf_counter() - _START) >= _LIMIT


def _negamax(you: List[int], opp: List[int], depth: int, alpha: int, beta: int) -> int:
    if _time_up():
        return _evaluate(you, opp)

    key = (tuple(you), tuple(opp), depth, True)
    if key in _TT:
        tt_depth, tt_val = _TT[key]
        if tt_depth >= depth:
            return tt_val

    if depth <= 0 or _terminal(you, opp):
        val = _evaluate(you, opp)
        _TT[key] = (depth, val)
        return val

    moves = _legal_moves(you)
    if not moves:
        val = _evaluate(you, opp)
        _TT[key] = (depth, val)
        return val

    best = -INF
    ordered = _move_order(you, opp, moves)

    for m in ordered:
        ny, no, extra = _simulate_move(you, opp, m)
        if extra:
            val = _negamax(ny, no, depth - 1, alpha, beta)
        else:
            val = -_negamax(no, ny, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta or _time_up():
            break

    _TT[key] = (depth, best)
    return best


def policy(you: list[int], opponent: list[int]) -> int:
    moves = [i for i in range(HOUSES) if you[i] > 0]
    if not moves:
        return 0  # should not happen per prompt

    # Always keep a legal fallback.
    fallback = moves[0]

    # Fast tactical checks first:
    # 1) Winning immediate store swing / terminal move.
    # 2) Extra-turn moves.
    # 3) Best capture.
    best_forced = None
    best_forced_score = -INF

    ordered = _move_order(you, opponent, moves)
    for m in ordered:
        ny, no, extra = _simulate_move(you, opponent, m)
        if _terminal(ny, no):
            val = _evaluate(ny, no)
            if val > best_forced_score:
                best_forced_score = val
                best_forced = m

    if best_forced is not None and best_forced_score > 9_000_000:
        return best_forced

    global _TT, _START, _LIMIT
    _TT = {}
    _START = time.perf_counter()

    total_seeds = sum(you[:HOUSES]) + sum(opponent[:HOUSES])

    # Dynamic time/depth.
    # Keep under 1 second.
    if total_seeds <= 10:
        max_depth = 12
        _LIMIT = 0.95
    elif total_seeds <= 18:
        max_depth = 10
        _LIMIT = 0.94
    elif total_seeds <= 30:
        max_depth = 8
        _LIMIT = 0.92
    else:
        max_depth = 7
        _LIMIT = 0.88

    best_move = fallback
    best_val = -INF

    # Iterative deepening for robustness.
    for depth in range(1, max_depth + 1):
        if _time_up():
            break

        current_best_move = best_move
        current_best_val = -INF

        # Reorder root by prior best if available.
        root_moves = ordered[:]
        if current_best_move in root_moves:
            root_moves.remove(current_best_move)
            root_moves = [current_best_move] + root_moves

        alpha = -INF
        beta = INF
        for m in root_moves:
            if _time_up():
                break
            ny, no, extra = _simulate_move(you, opponent, m)
            if extra:
                val = _negamax(ny, no, depth - 1, alpha, beta)
            else:
                val = -_negamax(no, ny, depth - 1, -beta, -alpha)

            if val > current_best_val:
                current_best_val = val
                current_best_move = m
            if val > alpha:
                alpha = val

        if not _time_up():
            best_move = current_best_move
            best_val = current_best_val

    # Safety: always legal.
    if 0 <= best_move < HOUSES and you[best_move] > 0:
        return best_move

    # Fallback tactical choice.
    best_tactical = fallback
    best_score = -INF
    for m in moves:
        score = 0
        if you[m] % 13 == (STORE - m) % 13:
            score += 1000
        score += 100 * _immediate_capture_gain(you, opponent, m)
        score += m
        if score > best_score:
            best_score = score
            best_tactical = m
    return best_tactical
