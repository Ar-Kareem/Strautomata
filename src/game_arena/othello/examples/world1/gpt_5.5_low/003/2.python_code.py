
import time
import math
import numpy as np
from functools import lru_cache

# Directions on an 8x8 board: N, S, W, E, NW, NE, SW, SE
_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
         (-1, -1), (-1, 1), (1, -1), (1, 1)]

# Strong positional table: corners are excellent, squares adjacent to empty
# corners are dangerous, edges are useful, center is moderate.
_POS = [
    120, -25,  20,   5,   5,  20, -25, 120,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
    120, -25,  20,   5,   5,  20, -25, 120,
]

_CORNERS = [0, 7, 56, 63]

# Squares adjacent to each corner, used to penalize risky moves while corner
# is still empty.
_CORNER_ADJ = {
    0:  [1, 8, 9],
    7:  [6, 14, 15],
    56: [48, 49, 57],
    63: [54, 55, 62],
}

_INF = 10 ** 12
_END_TIME = 0.0


class _Timeout(Exception):
    pass


def _arrays_to_bits(you, opponent):
    """Convert two 8x8 numpy arrays to two 64-bit integer bitboards."""
    p = 0
    o = 0
    for r in range(8):
        for c in range(8):
            bit = 1 << (r * 8 + c)
            if int(you[r][c]):
                p |= bit
            elif int(opponent[r][c]):
                o |= bit
    return p, o


def _idx_to_move(idx):
    return chr(ord('a') + (idx % 8)) + str(idx // 8 + 1)


def _inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


@lru_cache(maxsize=200000)
def _flips_for_move(p, o, idx):
    """Return bit mask of opponent discs flipped by playing idx, or 0."""
    occupied = p | o
    move_bit = 1 << idx
    if occupied & move_bit:
        return 0

    r0, c0 = divmod(idx, 8)
    total = 0

    for dr, dc in _DIRS:
        r = r0 + dr
        c = c0 + dc
        line = 0

        while _inside(r, c):
            j = r * 8 + c
            b = 1 << j
            if o & b:
                line |= b
            elif p & b:
                if line:
                    total |= line
                break
            else:
                break
            r += dr
            c += dc

    return total


@lru_cache(maxsize=200000)
def _legal_moves(p, o):
    """Return tuple of (move_index, flips_mask)."""
    occupied = p | o
    res = []
    empties = (~occupied) & ((1 << 64) - 1)

    while empties:
        b = empties & -empties
        idx = b.bit_length() - 1
        flips = _flips_for_move(p, o, idx)
        if flips:
            res.append((idx, flips))
        empties ^= b

    return tuple(res)


def _apply_move(p, o, idx, flips):
    bit = 1 << idx
    new_p = p | bit | flips
    new_o = o & ~flips
    return new_p, new_o


def _popcount(x):
    return int(x.bit_count())


def _terminal_score(p, o):
    diff = _popcount(p) - _popcount(o)
    if diff > 0:
        return 1000000 + diff
    if diff < 0:
        return -1000000 + diff
    return 0


@lru_cache(maxsize=200000)
def _evaluate(p, o):
    """
    Static evaluation from the perspective of player bitboard p.
    Balances corners, mobility, positional value, risky corner-adjacent discs,
    frontier discs, and disc parity mostly in the late game.
    """
    occupied = p | o
    empties_count = 64 - _popcount(occupied)

    my_moves = len(_legal_moves(p, o))
    op_moves = len(_legal_moves(o, p))

    # Terminal position or double pass.
    if my_moves == 0 and op_moves == 0:
        return _terminal_score(p, o)

    score = 0

    # Positional value.
    pp = p
    while pp:
        b = pp & -pp
        idx = b.bit_length() - 1
        score += _POS[idx]
        pp ^= b

    oo = o
    while oo:
        b = oo & -oo
        idx = b.bit_length() - 1
        score -= _POS[idx]
        oo ^= b

    # Corners are the most important strategic feature.
    my_corners = 0
    op_corners = 0
    for idx in _CORNERS:
        b = 1 << idx
        if p & b:
            my_corners += 1
        elif o & b:
            op_corners += 1
    score += 850 * (my_corners - op_corners)

    # Penalize occupying squares adjacent to an empty corner.
    for corner, adj in _CORNER_ADJ.items():
        cb = 1 << corner
        if not (occupied & cb):
            for idx in adj:
                b = 1 << idx
                if p & b:
                    score -= 120
                elif o & b:
                    score += 120

    # Mobility: very important in the opening/midgame.
    if my_moves + op_moves:
        score += 90 * (my_moves - op_moves)

    # Potential mobility: empty squares adjacent to opponent discs are
    # potential future moves.
    my_potential = 0
    op_potential = 0
    empty_mask = (~occupied) & ((1 << 64) - 1)

    e = empty_mask
    while e:
        b = e & -e
        idx = b.bit_length() - 1
        r, c = divmod(idx, 8)
        adj_my = False
        adj_op = False
        for dr, dc in _DIRS:
            rr, cc = r + dr, c + dc
            if _inside(rr, cc):
                bb = 1 << (rr * 8 + cc)
                if p & bb:
                    adj_my = True
                elif o & bb:
                    adj_op = True
        if adj_op:
            my_potential += 1
        if adj_my:
            op_potential += 1
        e ^= b

    score += 18 * (my_potential - op_potential)

    # Frontier discs are vulnerable; fewer is usually better.
    my_frontier = 0
    op_frontier = 0
    discs = occupied
    while discs:
        b = discs & -discs
        idx = b.bit_length() - 1
        r, c = divmod(idx, 8)
        is_frontier = False
        for dr, dc in _DIRS:
            rr, cc = r + dr, c + dc
            if _inside(rr, cc) and (empty_mask & (1 << (rr * 8 + cc))):
                is_frontier = True
                break
        if is_frontier:
            if p & b:
                my_frontier += 1
            else:
                op_frontier += 1
        discs ^= b

    score += 14 * (op_frontier - my_frontier)

    # Disc count matters little early, but strongly near the end.
    disc_diff = _popcount(p) - _popcount(o)
    if empties_count <= 14:
        score += 120 * disc_diff
    elif empties_count <= 24:
        score += 25 * disc_diff
    else:
        # Early in Othello, having fewer discs can be beneficial.
        score -= 6 * disc_diff

    # Parity bonus in the late game.
    if empties_count <= 18:
        score += (20 if empties_count % 2 == 1 else -20)

    return score


def _move_order_score(p, o, idx, flips):
    """Heuristic move ordering for alpha-beta efficiency."""
    score = _POS[idx] + 2 * _popcount(flips)

    if idx in _CORNERS:
        score += 10000

    occupied = p | o
    for corner, adj in _CORNER_ADJ.items():
        if idx in adj and not (occupied & (1 << corner)):
            score -= 5000

    # Prefer moves that reduce opponent mobility.
    np_, no_ = _apply_move(p, o, idx, flips)
    score -= 20 * len(_legal_moves(no_, np_))

    return score


def _ordered_moves(p, o):
    moves = list(_legal_moves(p, o))
    moves.sort(key=lambda m: _move_order_score(p, o, m[0], m[1]), reverse=True)
    return moves


@lru_cache(maxsize=300000)
def _negamax_cached(p, o, depth, alpha, beta):
    # This cached wrapper includes alpha/beta, which is not ideal for cache
    # density, but works safely and avoids re-searching many identical windows.
    return _negamax(p, o, depth, alpha, beta)


def _negamax(p, o, depth, alpha, beta):
    if time.perf_counter() > _END_TIME:
        raise _Timeout()

    moves = _legal_moves(p, o)

    if depth <= 0:
        return _evaluate(p, o)

    if not moves:
        if not _legal_moves(o, p):
            return _terminal_score(p, o)
        # Pass move.
        return -_negamax(o, p, depth - 1, -beta, -alpha)

    best = -_INF

    for idx, flips in _ordered_moves(p, o):
        np_, no_ = _apply_move(p, o, idx, flips)
        val = -_negamax(no_, np_, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return the next legal Othello move in algebraic notation, or "pass" if
    no legal move exists.
    """
    global _END_TIME

    start = time.perf_counter()
    _END_TIME = start + 0.92

    p, o = _arrays_to_bits(you, opponent)
    moves = list(_legal_moves(p, o))

    if not moves:
        return "pass"

    if len(moves) == 1:
        return _idx_to_move(moves[0][0])

    # Always keep a legal fallback.
    ordered = _ordered_moves(p, o)
    best_idx = ordered[0][0]

    occupied = p | o
    empties = 64 - _popcount(occupied)

    # Depth schedule. Iterative deepening ensures a legal result even if time
    # expires. Endgames are searched deeper.
    if empties <= 8:
        max_depth = empties
    elif empties <= 12:
        max_depth = 10
    elif empties <= 18:
        max_depth = 8
    elif empties <= 30:
        max_depth = 6
    else:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _END_TIME:
                break

            current_best_idx = best_idx
            current_best_val = -_INF
            alpha = -_INF
            beta = _INF

            for idx, flips in ordered:
                if time.perf_counter() > _END_TIME:
                    raise _Timeout()

                np_, no_ = _apply_move(p, o, idx, flips)
                val = -_negamax(no_, np_, depth - 1, -beta, -alpha)

                if val > current_best_val:
                    current_best_val = val
                    current_best_idx = idx

                if val > alpha:
                    alpha = val

            best_idx = current_best_idx

            # Reorder root moves to improve the next iteration.
            ordered.sort(
                key=lambda m: (
                    m[0] == best_idx,
                    _move_order_score(p, o, m[0], m[1])
                ),
                reverse=True
            )

    except _Timeout:
        pass
    except Exception:
        # In the unlikely event of any unexpected issue, still return a legal
        # move rather than risk disqualification.
        return _idx_to_move(best_idx)

    return _idx_to_move(best_idx)
