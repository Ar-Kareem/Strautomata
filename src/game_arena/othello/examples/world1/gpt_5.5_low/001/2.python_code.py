
import time
import numpy as np

# 8 directions on the board
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

# Positional weights: corners are excellent, squares adjacent to empty corners are dangerous.
POS_W = [
    120, -25,  20,   5,   5,  20, -25, 120,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
    120, -25,  20,   5,   5,  20, -25, 120,
]

CORNERS = (0, 7, 56, 63)
INF = 10 ** 9


class Timeout(Exception):
    pass


def _bit_count(x: int) -> int:
    return x.bit_count()


def _to_mask(arr: np.ndarray) -> int:
    m = 0
    # row-major bit index: r * 8 + c
    for r in range(8):
        row = arr[r]
        for c in range(8):
            if int(row[c]):
                m |= 1 << (r * 8 + c)
    return m


def _inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def _flips_for_move(me: int, opp: int, idx: int) -> int:
    """Return mask of opponent discs flipped by playing idx, or 0 if illegal."""
    bit = 1 << idx
    if (me | opp) & bit:
        return 0

    r0, c0 = divmod(idx, 8)
    flips = 0

    for dr, dc in DIRS:
        r, c = r0 + dr, c0 + dc
        line = 0
        seen_opp = False

        while _inside(r, c):
            j = r * 8 + c
            b = 1 << j
            if opp & b:
                line |= b
                seen_opp = True
            elif me & b:
                if seen_opp:
                    flips |= line
                break
            else:
                break
            r += dr
            c += dc

    return flips


def _legal_moves(me: int, opp: int):
    empty = ~(me | opp) & ((1 << 64) - 1)
    moves = []
    e = empty
    while e:
        lsb = e & -e
        idx = lsb.bit_length() - 1
        flips = _flips_for_move(me, opp, idx)
        if flips:
            moves.append((idx, flips))
        e ^= lsb
    return moves


def _apply_move(me: int, opp: int, idx: int, flips: int):
    move_bit = 1 << idx
    new_me = me | move_bit | flips
    new_opp = opp & ~flips
    return new_me, new_opp


def _frontier_count(me: int, empty: int) -> int:
    cnt = 0
    x = me
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        r, c = divmod(idx, 8)
        is_frontier = False
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if _inside(rr, cc) and (empty & (1 << (rr * 8 + cc))):
                is_frontier = True
                break
        if is_frontier:
            cnt += 1
        x ^= lsb
    return cnt


def _corner_score(me: int, opp: int) -> int:
    s = 0
    for idx in CORNERS:
        b = 1 << idx
        if me & b:
            s += 1
        elif opp & b:
            s -= 1
    return s


def _positional_score(me: int, opp: int) -> int:
    s = 0
    x = me
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        s += POS_W[idx]
        x ^= lsb

    x = opp
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        s -= POS_W[idx]
        x ^= lsb

    return s


def _evaluate(me: int, opp: int) -> int:
    occupied = _bit_count(me | opp)
    empty = ((1 << 64) - 1) & ~(me | opp)

    my_discs = _bit_count(me)
    op_discs = _bit_count(opp)
    disc_diff = my_discs - op_discs

    # Terminal-like late game: disc count matters much more.
    if occupied >= 58:
        return 1000 * disc_diff

    my_moves = len(_legal_moves(me, opp))
    op_moves = len(_legal_moves(opp, me))
    mobility = my_moves - op_moves

    corners = _corner_score(me, opp)
    pos = _positional_score(me, opp)

    my_frontier = _frontier_count(me, empty)
    op_frontier = _frontier_count(opp, empty)
    frontier = op_frontier - my_frontier  # fewer frontier discs is better

    # Disc parity is often misleading early; increase its weight late.
    if occupied < 20:
        disc_weight = -2
    elif occupied < 50:
        disc_weight = 1
    else:
        disc_weight = 8

    return (
        800 * corners +
        75 * mobility +
        25 * frontier +
        4 * pos +
        disc_weight * disc_diff
    )


def _move_order_score(idx: int, flips: int) -> int:
    # Prefer corners, then positional value, then more flips as a small tiebreaker.
    score = POS_W[idx] * 10 + _bit_count(flips)
    if idx in CORNERS:
        score += 10000
    return score


def _negamax(me: int, opp: int, depth: int, alpha: int, beta: int,
             start_time: float, limit: float) -> int:
    if time.perf_counter() - start_time > limit:
        raise Timeout()

    moves = _legal_moves(me, opp)

    if not moves:
        opp_moves = _legal_moves(opp, me)
        if not opp_moves:
            diff = _bit_count(me) - _bit_count(opp)
            if diff > 0:
                return 1000000 + diff
            if diff < 0:
                return -1000000 + diff
            return 0
        # Pass turn.
        return -_negamax(opp, me, depth, -beta, -alpha, start_time, limit)

    if depth <= 0:
        return _evaluate(me, opp)

    moves.sort(key=lambda mf: _move_order_score(mf[0], mf[1]), reverse=True)

    best = -INF
    for idx, flips in moves:
        nme, nopp = _apply_move(me, opp, idx, flips)
        val = -_negamax(nopp, nme, depth - 1, -beta, -alpha, start_time, limit)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _idx_to_move(idx: int) -> str:
    r, c = divmod(idx, 8)
    return chr(ord('a') + c) + str(r + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start = time.perf_counter()
    limit = 0.90

    me = _to_mask(you)
    opp = _to_mask(opponent)

    legal = _legal_moves(me, opp)
    if not legal:
        return "pass"

    # Safe fallback: best static ordered move.
    legal.sort(key=lambda mf: _move_order_score(mf[0], mf[1]), reverse=True)
    best_idx = legal[0][0]

    occupied = _bit_count(me | opp)
    empties = 64 - occupied

    # Search deeper in endgames.
    if empties <= 10:
        max_depth = empties
    elif empties <= 16:
        max_depth = 8
    elif empties <= 24:
        max_depth = 7
    else:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() - start > limit:
                break

            alpha = -INF
            beta = INF
            current_best_idx = best_idx
            current_best_val = -INF

            ordered = list(legal)
            ordered.sort(key=lambda mf: _move_order_score(mf[0], mf[1]), reverse=True)

            for idx, flips in ordered:
                if time.perf_counter() - start > limit:
                    raise Timeout()

                nme, nopp = _apply_move(me, opp, idx, flips)
                val = -_negamax(nopp, nme, depth - 1, -beta, -alpha, start, limit)

                if val > current_best_val:
                    current_best_val = val
                    current_best_idx = idx

                if val > alpha:
                    alpha = val

            # Only commit a depth after it completes.
            best_idx = current_best_idx

    except Timeout:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        best_idx = legal[0][0]

    return _idx_to_move(best_idx)
