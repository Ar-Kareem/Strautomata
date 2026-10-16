
import numpy as np
import time

# ---------- Precomputed board geometry ----------

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

RAYS = []
for r in range(8):
    for c in range(8):
        rays = []
        for dr, dc in DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                ray.append(rr * 8 + cc)
                rr += dr
                cc += dc
            rays.append(ray)
        RAYS.append(rays)

CORNERS = [0, 7, 56, 63]
CORNER_MASK = sum(1 << i for i in CORNERS)
FULL_MASK = (1 << 64) - 1

# Squares adjacent to each corner, used as danger squares when corner is empty.
CORNER_ADJ = {
    0:  [1, 8, 9],
    7:  [6, 14, 15],
    56: [48, 49, 57],
    63: [54, 55, 62],
}

# A standard-ish Othello positional table.
PST = [
    120, -25,  20,   5,   5,  20, -25, 120,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
    120, -25,  20,   5,   5,  20, -25, 120,
]

NEIGHBOR_MASKS = []
for i in range(64):
    r, c = divmod(i, 8)
    m = 0
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < 8 and 0 <= cc < 8:
            m |= 1 << (rr * 8 + cc)
    NEIGHBOR_MASKS.append(m)


class SearchTimeout(Exception):
    pass


_deadline = 0.0
_nodes = 0


def _bit_count(x):
    return int(x.bit_count())


def _arrays_to_bits(you, opponent):
    me = 0
    op = 0
    # np arrays are tiny; explicit loops are reliable and fast enough.
    for r in range(8):
        for c in range(8):
            bit = 1 << (r * 8 + c)
            if int(you[r][c]):
                me |= bit
            elif int(opponent[r][c]):
                op |= bit
    return me, op


def _flips_for_move(me, op, idx):
    bit = 1 << idx
    if (me | op) & bit:
        return 0

    flips = 0
    for ray in RAYS[idx]:
        captured = 0
        seen_opponent = False
        for j in ray:
            b = 1 << j
            if op & b:
                captured |= b
                seen_opponent = True
            elif me & b:
                if seen_opponent:
                    flips |= captured
                break
            else:
                break
    return flips


def _legal_moves(me, op):
    occupied = me | op
    empties = (~occupied) & FULL_MASK
    moves = []

    # Only empty squares adjacent to opponent discs can be legal.
    candidates = 0
    temp = op
    while temp:
        lsb = temp & -temp
        idx = lsb.bit_length() - 1
        candidates |= NEIGHBOR_MASKS[idx]
        temp ^= lsb
    candidates &= empties

    temp = candidates
    while temp:
        lsb = temp & -temp
        idx = lsb.bit_length() - 1
        flips = _flips_for_move(me, op, idx)
        if flips:
            moves.append((idx, flips))
        temp ^= lsb
    return moves


def _apply_move(me, op, idx, flips):
    bit = 1 << idx
    new_me = me | bit | flips
    new_op = op & ~flips
    return new_me, new_op


def _positional_score(me, op):
    score = 0
    x = me
    while x:
        lsb = x & -x
        score += PST[lsb.bit_length() - 1]
        x ^= lsb
    x = op
    while x:
        lsb = x & -x
        score -= PST[lsb.bit_length() - 1]
        x ^= lsb
    return score


def _frontier_count(bits, empty):
    n = 0
    x = bits
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        if NEIGHBOR_MASKS[idx] & empty:
            n += 1
        x ^= lsb
    return n


def _corner_danger(me, op):
    penalty = 0
    for corner, adj in CORNER_ADJ.items():
        cb = 1 << corner
        if not ((me | op) & cb):
            for sq in adj:
                b = 1 << sq
                if me & b:
                    penalty -= 18
                elif op & b:
                    penalty += 18
    return penalty


def _evaluate(me, op):
    occupied = me | op
    empty = (~occupied) & FULL_MASK
    empties = 64 - _bit_count(occupied)

    my_discs = _bit_count(me)
    op_discs = _bit_count(op)
    disc_diff = my_discs - op_discs

    my_moves = len(_legal_moves(me, op))
    op_moves = len(_legal_moves(op, me))
    mobility = 0
    if my_moves + op_moves:
        mobility = 100 * (my_moves - op_moves) // (my_moves + op_moves)

    my_corners = _bit_count(me & CORNER_MASK)
    op_corners = _bit_count(op & CORNER_MASK)
    corner_score = 260 * (my_corners - op_corners)

    frontier = _frontier_count(op, empty) - _frontier_count(me, empty)

    # Disc count matters mostly near the end; early disc greed is often bad.
    if empties > 44:
        disc_weight = -2
    elif empties > 18:
        disc_weight = 2
    else:
        disc_weight = 12

    parity = 0
    if empties <= 16:
        parity = 18 if empties % 2 == 1 else -18

    return (
        8 * mobility
        + corner_score
        + 3 * _positional_score(me, op)
        + 9 * frontier
        + disc_weight * disc_diff
        + _corner_danger(me, op)
        + parity
    )


def _terminal_score(me, op):
    diff = _bit_count(me) - _bit_count(op)
    if diff > 0:
        return 100000 + diff
    if diff < 0:
        return -100000 + diff
    return 0


def _move_order_key(move):
    idx, flips = move
    if idx in CORNERS:
        return 100000
    r, c = divmod(idx, 8)
    edge = 1 if r in (0, 7) or c in (0, 7) else 0
    return PST[idx] * 100 + edge * 400 + _bit_count(flips)


def _negamax(me, op, depth, alpha, beta, table):
    global _nodes

    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > _deadline:
        raise SearchTimeout()

    key = (me, op, depth)
    cached = table.get(key)
    if cached is not None:
        return cached

    moves = _legal_moves(me, op)
    opp_has = None

    if not moves:
        opp_moves = _legal_moves(op, me)
        opp_has = bool(opp_moves)
        if not opp_has:
            val = _terminal_score(me, op)
            table[key] = val
            return val
        if depth <= 0:
            val = _evaluate(me, op)
            table[key] = val
            return val
        val = -_negamax(op, me, depth - 1, -beta, -alpha, table)
        table[key] = val
        return val

    if depth <= 0:
        return _evaluate(me, op)

    moves.sort(key=_move_order_key, reverse=True)

    best = -10**12
    for idx, flips in moves:
        nme, nop = _apply_move(me, op, idx, flips)
        val = -_negamax(nop, nme, depth - 1, -beta, -alpha, table)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    table[key] = best
    return best


def _choose_depth(empties):
    # Iterative deepening will stop early if needed.
    if empties <= 10:
        return empties + 2
    if empties <= 14:
        return 8
    if empties <= 22:
        return 7
    if empties <= 42:
        return 5
    return 4


def _idx_to_move(idx):
    r, c = divmod(idx, 8)
    return chr(ord("a") + c) + str(r + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal Othello move such as 'd3', or 'pass' only if no legal move exists.
    """
    global _deadline, _nodes

    me, op = _arrays_to_bits(you, opponent)
    moves = _legal_moves(me, op)

    if not moves:
        return "pass"

    # Safe fallback: best-looking legal move by static ordering.
    moves.sort(key=_move_order_key, reverse=True)
    best_idx = moves[0][0]

    occupied = me | op
    empties = 64 - _bit_count(occupied)
    max_depth = _choose_depth(empties)

    _deadline = time.perf_counter() + 0.88
    _nodes = 0

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _deadline:
                break

            table = {}
            alpha = -10**12
            beta = 10**12
            depth_best_idx = best_idx
            depth_best_val = -10**12

            ordered = list(moves)
            ordered.sort(key=_move_order_key, reverse=True)

            for idx, flips in ordered:
                if time.perf_counter() > _deadline:
                    raise SearchTimeout()

                nme, nop = _apply_move(me, op, idx, flips)
                val = -_negamax(nop, nme, depth - 1, -beta, -alpha, table)

                if val > depth_best_val:
                    depth_best_val = val
                    depth_best_idx = idx

                if val > alpha:
                    alpha = val

            best_idx = depth_best_idx

    except SearchTimeout:
        pass
    except Exception:
        # Never risk returning an illegal/non-move due to an unexpected issue.
        pass

    return _idx_to_move(best_idx)
