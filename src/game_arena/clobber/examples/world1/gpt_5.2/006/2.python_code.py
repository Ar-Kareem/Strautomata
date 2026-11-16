
# clobber_policy.py
# 5x6 Clobber policy(you, opponent) -> "row,col,dir"
from __future__ import annotations

import time
from typing import List, Tuple, Optional, Dict

ROWS, COLS = 5, 6
N = ROWS * COLS

DIRS = {
    "U": (-1, 0),
    "R": (0, 1),
    "D": (1, 0),
    "L": (0, -1),
}

# Precompute adjacency for each square: list of (to_idx, dir_char)
ADJ: List[List[Tuple[int, str]]] = [[] for _ in range(N)]
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dch, (dr, dc) in DIRS.items():
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                ADJ[i].append((j, dch))

# Large constants for mate scores
MATE = 10_000_000
INF = 10_000_000_000

# Transposition table entry flags
EXACT, LOWER, UPPER = 0, 1, 2

class _Timeout(Exception):
    pass


def _to_bitboard(arr) -> int:
    """
    Robustly convert input (nested list, flat list length 30, numpy array, etc.) into 30-bit int.
    Bit i corresponds to cell (i//6, i%6).
    """
    # Try numpy-like flatten if present
    try:
        flat = list(arr.ravel())
    except Exception:
        # If nested list, flatten
        if isinstance(arr, list) and arr and isinstance(arr[0], list):
            flat = [v for row in arr for v in row]
        else:
            flat = list(arr)

    # If somehow provided as 5x6 but not nested, still fine if length 30
    bb = 0
    # Only consider first 30 entries; ignore extras if any
    for i, v in enumerate(flat[:N]):
        if v:
            bb |= (1 << i)
    return bb


def _legal_moves(you: int, opp: int) -> List[Tuple[int, int, str]]:
    """Return list of legal moves (from_idx, to_idx, dir_char)."""
    moves: List[Tuple[int, int, str]] = []
    y = you
    while y:
        lsb = y & -y
        i = (lsb.bit_length() - 1)
        y ^= lsb
        for j, dch in ADJ[i]:
            if (opp >> j) & 1:
                moves.append((i, j, dch))
    return moves


def _legal_count(you: int, opp: int) -> int:
    """Count legal moves without allocating a big list."""
    cnt = 0
    y = you
    while y:
        lsb = y & -y
        i = (lsb.bit_length() - 1)
        y ^= lsb
        for j, _dch in ADJ[i]:
            if (opp >> j) & 1:
                cnt += 1
    return cnt


def _apply_move(you: int, opp: int, frm: int, to: int) -> Tuple[int, int]:
    """Apply capture move for current player: move frm -> to capturing opponent at to."""
    frm_bit = 1 << frm
    to_bit = 1 << to
    # you loses frm, gains to; opp loses to
    you2 = (you ^ frm_bit) | to_bit
    opp2 = opp ^ to_bit
    return you2, opp2


def _evaluate(you: int, opp: int, moves_len: int) -> int:
    """
    Static evaluation (current player perspective).
    Mobility dominates in Clobber; pieces term is a small tiebreak.
    """
    # If no moves, it's losing (should be handled earlier, but keep safe)
    if moves_len == 0:
        return -MATE

    my_mob = moves_len
    opp_mob = _legal_count(opp, you)
    my_pieces = you.bit_count()
    opp_pieces = opp.bit_count()

    # Mobility difference is crucial; piece count is mild.
    return 120 * (my_mob - opp_mob) + 3 * (my_pieces - opp_pieces)


def _key(you: int, opp: int) -> int:
    """Pack into one integer key for TT."""
    return you | (opp << N)


def _negamax(
    you: int,
    opp: int,
    depth: int,
    alpha: int,
    beta: int,
    ply: int,
    deadline: float,
    tt: Dict[int, Tuple[int, int, int, Optional[Tuple[int, int, str]]]],
) -> Tuple[int, Optional[Tuple[int, int, str]]]:
    """
    Returns (value, best_move) from perspective of side to move (you).
    Negamax: value is good for current player.
    """
    if time.perf_counter() > deadline:
        raise _Timeout

    k = _key(you, opp)
    entry = tt.get(k)
    if entry is not None:
        edepth, evalv, flag, bestm = entry
        if edepth >= depth:
            if flag == EXACT:
                return evalv, bestm
            if flag == LOWER:
                alpha = max(alpha, evalv)
            elif flag == UPPER:
                beta = min(beta, evalv)
            if alpha >= beta:
                return evalv, bestm

    moves = _legal_moves(you, opp)
    if not moves:
        # No legal move: current player loses. Prefer quicker mates.
        return -MATE + ply, None

    if depth == 0:
        return _evaluate(you, opp, len(moves)), None

    # Move ordering:
    # 1) immediate wins (opponent has no reply)
    # 2) otherwise, reduce opponent mobility (after our move)
    scored_moves: List[Tuple[int, Tuple[int, int, str]]] = []
    for m in moves:
        frm, to, dch = m
        you2, opp2 = _apply_move(you, opp, frm, to)
        # Next player is opponent: state (opp2, you2)
        opp_reply_cnt = _legal_count(opp2, you2)
        if opp_reply_cnt == 0:
            # Winning move; prioritize heavily
            score = 10_000_000
        else:
            # Smaller opponent mobility is better
            score = 10_000_0 - opp_reply_cnt * 100
        scored_moves.append((score, m))
    scored_moves.sort(reverse=True, key=lambda x: x[0])

    best_move: Optional[Tuple[int, int, str]] = None
    orig_alpha = alpha
    best_val = -INF

    for _score, m in scored_moves:
        if time.perf_counter() > deadline:
            raise _Timeout
        frm, to, dch = m
        you2, opp2 = _apply_move(you, opp, frm, to)
        # Swap roles for negamax
        val_child, _ = _negamax(opp2, you2, depth - 1, -beta, -alpha, ply + 1, deadline, tt)
        val = -val_child

        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    # Store in TT
    flag = EXACT
    if best_val <= orig_alpha:
        flag = UPPER
    elif best_val >= beta:
        flag = LOWER
    tt[k] = (depth, best_val, flag, best_move)
    return best_val, best_move


def _move_to_str(m: Tuple[int, int, str]) -> str:
    frm, _to, dch = m
    r, c = divmod(frm, COLS)
    return f"{r},{c},{dch}"


def policy(you: list[int], opponent: list[int]) -> str:
    yb = _to_bitboard(you)
    ob = _to_bitboard(opponent)

    moves = _legal_moves(yb, ob)
    if not moves:
        # Should not be called in terminal states; unavoidable fallback.
        return "0,0,U"

    # If any immediate winning move exists, play it.
    for m in moves:
        frm, to, dch = m
        y2, o2 = _apply_move(yb, ob, frm, to)
        if _legal_count(o2, y2) == 0:
            return _move_to_str(m)

    # Iterative deepening alpha-beta with TT under time budget
    start = time.perf_counter()
    deadline = start + 0.93  # keep margin for overhead
    tt: Dict[int, Tuple[int, int, int, Optional[Tuple[int, int, str]]]] = {}

    # Seed best move with something legal (ordered by low opponent mobility)
    def root_order_key(m):
        frm, to, _d = m
        y2, o2 = _apply_move(yb, ob, frm, to)
        return _legal_count(o2, y2)

    moves_sorted = sorted(moves, key=root_order_key)
    best = moves_sorted[0]

    # Depth schedule: increase until timeout.
    # Practical cap to avoid spending too long in deep searches in worst cases.
    max_depth = 14
    alpha, beta = -INF, INF

    for depth in range(1, max_depth + 1):
        try:
            val, bm = _negamax(yb, ob, depth, alpha, beta, 0, deadline, tt)
            if bm is not None:
                best = bm
            # Light aspiration: narrow around last value (helps speed)
            window = 250
            alpha, beta = val - window, val + window
        except _Timeout:
            break
        except Exception:
            # Safety: never crash; fall back to current best legal move.
            break

        if time.perf_counter() > deadline:
            break

    return _move_to_str(best)
