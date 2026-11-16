
import time
import numpy as np

FULL = (1 << 64) - 1
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

INF = 10 ** 9
WIN = 1_000_000

EXACT = 0
LOWER = 1
UPPER = 2

WEIGHTS = (
    120, -30,  20,   5,   5,  20, -30, 120,
    -30, -55,  -5,  -5,  -5,  -5, -55, -30,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -30, -55,  -5,  -5,  -5,  -5, -55, -30,
    120, -30,  20,   5,   5,  20, -30, 120,
)

ORDER_WEIGHTS = (
    2000, -350, 120, 50, 50, 120, -350, 2000,
    -350, -700, -30, -30, -30, -30, -700, -350,
     120,  -30,  80, 20, 20,  80,  -30,  120,
      50,  -30,  20, 10, 10,  20,  -30,   50,
      50,  -30,  20, 10, 10,  20,  -30,   50,
     120,  -30,  80, 20, 20,  80,  -30,  120,
    -350, -700, -30, -30, -30, -30, -700, -350,
    2000, -350, 120, 50, 50, 120, -350, 2000,
)

CORNER_NEIGHBORS = (
    (1 << 0, (1 << 1) | (1 << 8) | (1 << 9)),
    (1 << 7, (1 << 6) | (1 << 14) | (1 << 15)),
    (1 << 56, (1 << 48) | (1 << 49) | (1 << 57)),
    (1 << 63, (1 << 54) | (1 << 55) | (1 << 62)),
)

ROW_VALUE = []
for r in range(8):
    table = [0] * 256
    base = r * 8
    for mask in range(256):
        value = 0
        x = mask
        while x:
            b = x & -x
            c = b.bit_length() - 1
            value += WEIGHTS[base + c]
            x ^= b
        table[mask] = value
    ROW_VALUE.append(table)

_deadline = 0.0
_nodes = 0
_tt = {}
_history = [0] * 64


class SearchTimeout(Exception):
    pass


def _legal(p, o):
    empty = FULL ^ (p | o)
    moves = 0

    t = ((p & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    moves |= ((t & NOT_H) << 1) & empty

    t = ((p & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    moves |= ((t & NOT_A) >> 1) & empty

    t = (p << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    moves |= (t << 8) & empty

    t = (p >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    moves |= (t >> 8) & empty

    t = ((p & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    moves |= ((t & NOT_H) << 9) & empty

    t = ((p & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    moves |= ((t & NOT_A) << 7) & empty

    t = ((p & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    moves |= ((t & NOT_H) >> 7) & empty

    t = ((p & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    moves |= ((t & NOT_A) >> 9) & empty

    return moves & FULL


def _flips(p, o, move):
    flips = 0

    x = (move & NOT_H) << 1
    captured = 0
    while x & o:
        captured |= x
        x = (x & NOT_H) << 1
    if x & p:
        flips |= captured

    x = (move & NOT_A) >> 1
    captured = 0
    while x & o:
        captured |= x
        x = (x & NOT_A) >> 1
    if x & p:
        flips |= captured

    x = move << 8
    captured = 0
    while x & o:
        captured |= x
        x <<= 8
    if x & p:
        flips |= captured

    x = move >> 8
    captured = 0
    while x & o:
        captured |= x
        x >>= 8
    if x & p:
        flips |= captured

    x = (move & NOT_H) << 9
    captured = 0
    while x & o:
        captured |= x
        x = (x & NOT_H) << 9
    if x & p:
        flips |= captured

    x = (move & NOT_A) << 7
    captured = 0
    while x & o:
        captured |= x
        x = (x & NOT_A) << 7
    if x & p:
        flips |= captured

    x = (move & NOT_H) >> 7
    captured = 0
    while x & o:
        captured |= x
        x = (x & NOT_H) >> 7
    if x & p:
        flips |= captured

    x = (move & NOT_A) >> 9
    captured = 0
    while x & o:
        captured |= x
        x = (x & NOT_A) >> 9
    if x & p:
        flips |= captured

    return flips


def _adjacent(x):
    return (
        ((x & NOT_H) << 1)
        | ((x & NOT_A) >> 1)
        | (x << 8)
        | (x >> 8)
        | ((x & NOT_H) << 9)
        | ((x & NOT_A) << 7)
        | ((x & NOT_H) >> 7)
        | ((x & NOT_A) >> 9)
    ) & FULL


def _orthogonal(x):
    return (
        ((x & NOT_H) << 1)
        | ((x & NOT_A) >> 1)
        | (x << 8)
        | (x >> 8)
    ) & FULL


def _positional_value(bits):
    total = 0
    for r in range(8):
        total += ROW_VALUE[r][(bits >> (8 * r)) & 255]
    return total


def _stable_edge_count(bits):
    stable = 0
    configurations = (
        (0, 1, 8),
        (7, -1, 8),
        (56, 1, -8),
        (63, -1, -8),
    )

    for corner, row_step, col_step in configurations:
        corner_bit = 1 << corner
        if not (bits & corner_bit):
            continue

        stable |= corner_bit

        for k in range(1, 8):
            idx = corner + row_step * k
            b = 1 << idx
            if bits & b:
                stable |= b
            else:
                break

        for k in range(1, 8):
            idx = corner + col_step * k
            b = 1 << idx
            if bits & b:
                stable |= b
            else:
                break

    return stable.bit_count()


def _terminal_value(p, o):
    diff = p.bit_count() - o.bit_count()
    if diff > 0:
        return WIN + diff
    if diff < 0:
        return -WIN + diff
    return 0


def _evaluate(p, o, my_moves=None):
    occupied = p | o
    empty = FULL ^ occupied
    empties = empty.bit_count()

    if my_moves is None:
        my_moves = _legal(p, o)
    opp_moves = _legal(o, p)

    my_count = p.bit_count()
    opp_count = o.bit_count()
    disc_diff = my_count - opp_count

    mobility_diff = my_moves.bit_count() - opp_moves.bit_count()

    adjacent_empty = _adjacent(empty)
    frontier_diff = (
        (p & adjacent_empty).bit_count()
        - (o & adjacent_empty).bit_count()
    )

    potential_diff = (
        (empty & _adjacent(o)).bit_count()
        - (empty & _adjacent(p)).bit_count()
    )

    positional = _positional_value(p) - _positional_value(o)
    corner_diff = (p & CORNERS).bit_count() - (o & CORNERS).bit_count()

    corner_closeness = 0
    for corner, neighbors in CORNER_NEIGHBORS:
        if not (occupied & corner):
            corner_closeness += (
                (p & neighbors).bit_count()
                - (o & neighbors).bit_count()
            )

    stable_diff = _stable_edge_count(p) - _stable_edge_count(o)

    if empties > 44:
        disc_weight = -2
        mobility_weight = 68
        frontier_weight = 22
        potential_weight = 12
    elif empties > 20:
        disc_weight = 1
        mobility_weight = 76
        frontier_weight = 28
        potential_weight = 10
    else:
        disc_weight = 4 + 3 * (20 - empties)
        mobility_weight = 42
        frontier_weight = 10
        potential_weight = 5

    return (
        4 * positional
        + 700 * corner_diff
        + 95 * stable_diff
        - 110 * corner_closeness
        + mobility_weight * mobility_diff
        - frontier_weight * frontier_diff
        + potential_weight * potential_diff
        + disc_weight * disc_diff
    )


def _odd_region_mask(empty):
    remaining = empty
    odd = 0

    while remaining:
        seed = remaining & -remaining
        region = 0
        frontier = seed

        while frontier:
            region |= frontier
            remaining &= ~frontier
            frontier = _orthogonal(frontier) & remaining

        if region.bit_count() & 1:
            odd |= region

    return odd


def _store_tt(key, depth, value, flag, best):
    old = _tt.get(key)
    if old is None or depth >= old[0]:
        if len(_tt) < 350000 or old is not None:
            _tt[key] = (depth, value, flag, best)


def _ordered_moves(p, o, moves, depth, tt_move=0):
    occupied = p | o
    empties = 64 - occupied.bit_count()
    odd_mask = _odd_region_mask(FULL ^ occupied) if empties <= 18 else 0
    calculate_mobility = depth >= 2

    result = []
    remaining = moves

    while remaining:
        move = remaining & -remaining
        remaining ^= move
        idx = move.bit_length() - 1

        flips = _flips(p, o, move)
        p_after = p | move | flips
        o_after = o & ~flips

        score = 8 * ORDER_WEIGHTS[idx] + min(_history[idx], 2500)

        if move == tt_move:
            score += 2_000_000

        if move & CORNERS:
            score += 500_000

        if odd_mask & move:
            score += 180

        if empties < 18:
            score += 5 * flips.bit_count()
        else:
            score -= flips.bit_count()

        next_moves = None
        if calculate_mobility:
            next_moves = _legal(o_after, p_after)
            next_count = next_moves.bit_count()
            score -= 65 * next_count

            if next_moves & CORNERS:
                score -= 150_000

            if next_count == 0:
                score += 1200

        result.append((score, move, p_after, o_after, next_moves))

    result.sort(key=lambda item: item[0], reverse=True)
    return result


def _search(p, o, depth, alpha, beta, moves_hint=None):
    global _nodes

    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() >= _deadline:
        raise SearchTimeout

    key = (p, o)
    alpha_original = alpha
    beta_original = beta

    entry = _tt.get(key)
    tt_move = 0
    if entry is not None:
        stored_depth, stored_value, stored_flag, tt_move = entry
        if stored_depth >= depth:
            if stored_flag == EXACT:
                return stored_value
            if stored_flag == LOWER:
                if stored_value > alpha:
                    alpha = stored_value
            else:
                if stored_value < beta:
                    beta = stored_value
            if alpha >= beta:
                return stored_value

    moves = moves_hint if moves_hint is not None else _legal(p, o)

    if not moves:
        opponent_moves = _legal(o, p)
        if not opponent_moves:
            value = _terminal_value(p, o)
            _store_tt(key, 99, value, EXACT, 0)
            return value

        return -_search(o, p, depth, -beta, -alpha, opponent_moves)

    if depth <= 0:
        value = _evaluate(p, o, moves)
        _store_tt(key, 0, value, EXACT, 0)
        return value

    ordered = _ordered_moves(p, o, moves, depth, tt_move)
    best_value = -INF
    best_move = ordered[0][1]
    first = True

    for _, move, p_after, o_after, next_moves in ordered:
        if first:
            value = -_search(
                o_after, p_after, depth - 1,
                -beta, -alpha, next_moves
            )
            first = False
        else:
            value = -_search(
                o_after, p_after, depth - 1,
                -alpha - 1, -alpha, next_moves
            )
            if alpha < value < beta:
                value = -_search(
                    o_after, p_after, depth - 1,
                    -beta, -alpha, next_moves
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            idx = move.bit_length() - 1
            _history[idx] += depth * depth
            break

    if best_value <= alpha_original:
        flag = UPPER
    elif best_value >= beta_original:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(key, depth, best_value, flag, best_move)
    return best_value


def _root_search(p, o, moves, depth, pv_move):
    ordered = _ordered_moves(p, o, moves, depth, pv_move)

    alpha = -INF
    beta = INF
    best_value = -INF
    best_move = ordered[0][1]
    first = True

    for _, move, p_after, o_after, next_moves in ordered:
        if time.perf_counter() >= _deadline:
            raise SearchTimeout

        if first:
            value = -_search(
                o_after, p_after, depth - 1,
                -beta, -alpha, next_moves
            )
            first = False
        else:
            value = -_search(
                o_after, p_after, depth - 1,
                -alpha - 1, -alpha, next_moves
            )
            if value > alpha:
                value = -_search(
                    o_after, p_after, depth - 1,
                    -beta, -alpha, next_moves
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    return best_move, best_value


def _to_bitboard(array):
    bits = 0
    for i, value in enumerate(array.flat):
        if int(value):
            bits |= 1 << i
    return bits


def _move_string(move):
    idx = move.bit_length() - 1
    row, col = divmod(idx, 8)
    return chr(ord("a") + col) + str(row + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _deadline, _nodes, _tt, _history

    p = _to_bitboard(you)
    o = _to_bitboard(opponent)
    moves = _legal(p, o)

    if not moves:
        return "pass"

    if moves & (moves - 1) == 0:
        return _move_string(moves)

    start = time.perf_counter()
    _deadline = start + 0.92
    _nodes = 0
    _tt = {}
    _history = [0] * 64

    empties = 64 - (p | o).bit_count()

    # Establish a legal, strategically ordered fallback before searching.
    fallback_order = _ordered_moves(p, o, moves, 2, 0)
    best_move = fallback_order[0][1]
    pv_move = best_move

    if empties <= 16:
        depths = list(range(3, empties + 1, 2))
        if not depths:
            depths = [empties]
        elif depths[-1] != empties:
            depths.append(empties)
    else:
        depths = range(1, empties + 1)

    try:
        for depth in depths:
            move, _ = _root_search(p, o, moves, depth, pv_move)
            best_move = move
            pv_move = move

            if depth >= empties:
                break

            if time.perf_counter() >= _deadline:
                break
    except SearchTimeout:
        pass
    except Exception:
        # The precomputed fallback is always legal.
        pass

    return _move_string(best_move)
