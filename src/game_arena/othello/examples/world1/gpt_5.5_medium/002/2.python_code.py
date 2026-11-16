
import time
import numpy as np

BOARD_SIZE = 8
N_SQUARES = 64
FULL_MASK = (1 << 64) - 1
INF = 10 ** 18
WIN_SCORE = 10 ** 10
COLS = "abcdefgh"

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

POSITION_WEIGHTS = [
    120, -25,  20,   6,   6,  20, -25, 120,
    -25, -55,  -8,  -8,  -8,  -8, -55, -25,
     20,  -8,  18,   4,   4,  18,  -8,  20,
      6,  -8,   4,   2,   2,   4,  -8,   6,
      6,  -8,   4,   2,   2,   4,  -8,   6,
     20,  -8,  18,   4,   4,  18,  -8,  20,
    -25, -55,  -8,  -8,  -8,  -8, -55, -25,
    120, -25,  20,   6,   6,  20, -25, 120,
]

CORNERS = (0, 7, 56, 63)
CORNER_SET = set(CORNERS)
X_SQUARES = {9, 14, 49, 54}
CORNER_ADJACENT = {
    0:  (1, 8, 9),
    7:  (6, 14, 15),
    56: (48, 49, 57),
    63: (54, 55, 62),
}

RAYS = [[] for _ in range(64)]
NEIGHBORS = [0 for _ in range(64)]

for r in range(8):
    for c in range(8):
        sq = r * 8 + c

        for dr, dc in DIRECTIONS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                ray.append(rr * 8 + cc)
                rr += dr
                cc += dc
            RAYS[sq].append(tuple(ray))

        mask = 0
        for dr, dc in DIRECTIONS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                mask |= 1 << (rr * 8 + cc)
        NEIGHBORS[sq] = mask

EDGE_PATHS = [
    (0,  [0, 1, 2, 3, 4, 5, 6, 7]),
    (0,  [0, 8, 16, 24, 32, 40, 48, 56]),
    (7,  [7, 6, 5, 4, 3, 2, 1, 0]),
    (7,  [7, 15, 23, 31, 39, 47, 55, 63]),
    (56, [56, 57, 58, 59, 60, 61, 62, 63]),
    (56, [56, 48, 40, 32, 24, 16, 8, 0]),
    (63, [63, 62, 61, 60, 59, 58, 57, 56]),
    (63, [63, 55, 47, 39, 31, 23, 15, 7]),
]

_tt = {}
_legal_cache = {}
_flips_cache = {}
_deadline = 0.0
_nodes = 0


def _bit_count(x: int) -> int:
    return x.bit_count()


def _array_to_bits(arr: np.ndarray) -> int:
    bits = 0
    rows, cols = np.nonzero(arr)
    for r, c in zip(rows, cols):
        bits |= 1 << (int(r) * 8 + int(c))
    return bits


def _move_to_str(sq: int) -> str:
    return COLS[sq % 8] + str(sq // 8 + 1)


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() >= _deadline:
        raise TimeoutError


def _neighbor_union(bits: int) -> int:
    out = 0
    while bits:
        b = bits & -bits
        sq = b.bit_length() - 1
        out |= NEIGHBORS[sq]
        bits ^= b
    return out


def _flips_for_move_raw(move: int, me: int, opp: int) -> int:
    bit = 1 << move
    if (me | opp) & bit:
        return 0

    flips = 0
    for ray in RAYS[move]:
        captured = 0
        for sq in ray:
            b = 1 << sq
            if opp & b:
                captured |= b
            elif me & b:
                if captured:
                    flips |= captured
                break
            else:
                break
    return flips


def _flips_for_move(move: int, me: int, opp: int) -> int:
    key = (me, opp, move)
    val = _flips_cache.get(key)
    if val is None:
        val = _flips_for_move_raw(move, me, opp)
        _flips_cache[key] = val
    return val


def _legal_moves(me: int, opp: int):
    key = (me, opp)
    cached = _legal_cache.get(key)
    if cached is not None:
        return cached

    occupied = me | opp
    empty = (~occupied) & FULL_MASK
    candidates = empty & _neighbor_union(opp)

    moves = []
    while candidates:
        b = candidates & -candidates
        sq = b.bit_length() - 1
        if _flips_for_move(sq, me, opp):
            moves.append(sq)
        candidates ^= b

    moves = tuple(moves)
    _legal_cache[key] = moves
    return moves


def _apply_move(me: int, opp: int, move: int):
    flips = _flips_for_move(move, me, opp)
    bit = 1 << move
    new_me = me | bit | flips
    new_opp = opp & ~flips
    return new_me, new_opp


def _positional_sum(bits: int) -> int:
    score = 0
    while bits:
        b = bits & -bits
        sq = b.bit_length() - 1
        score += POSITION_WEIGHTS[sq]
        bits ^= b
    return score


def _frontier_count(discs: int, empty: int) -> int:
    count = 0
    x = discs
    while x:
        b = x & -x
        sq = b.bit_length() - 1
        if NEIGHBORS[sq] & empty:
            count += 1
        x ^= b
    return count


def _stable_edge_count(discs: int) -> int:
    stable = 0
    for corner, path in EDGE_PATHS:
        if not (discs & (1 << corner)):
            continue
        for sq in path:
            b = 1 << sq
            if discs & b:
                stable |= b
            else:
                break
    return _bit_count(stable)


def _corner_adjacent_difference(me: int, opp: int, occupied: int) -> int:
    diff = 0
    for corner in CORNERS:
        if not (occupied & (1 << corner)):
            for sq in CORNER_ADJACENT[corner]:
                b = 1 << sq
                if me & b:
                    diff += 1
                elif opp & b:
                    diff -= 1
    return diff


def _evaluate(me: int, opp: int) -> int:
    occupied = me | opp
    empty = (~occupied) & FULL_MASK
    empty_count = 64 - _bit_count(occupied)
    occupied_count = 64 - empty_count

    my_count = _bit_count(me)
    opp_count = _bit_count(opp)
    disc_diff = my_count - opp_count

    my_corners = sum(1 for sq in CORNERS if me & (1 << sq))
    opp_corners = sum(1 for sq in CORNERS if opp & (1 << sq))
    corner_diff = my_corners - opp_corners

    my_moves = len(_legal_moves(me, opp))
    opp_moves = len(_legal_moves(opp, me))
    if my_moves + opp_moves:
        mobility = 100 * (my_moves - opp_moves) // (my_moves + opp_moves)
    else:
        mobility = 0

    my_potential = _bit_count(_neighbor_union(opp) & empty)
    opp_potential = _bit_count(_neighbor_union(me) & empty)
    if my_potential + opp_potential:
        potential = 100 * (my_potential - opp_potential) // (my_potential + opp_potential)
    else:
        potential = 0

    pos = _positional_sum(me) - _positional_sum(opp)

    my_frontier = _frontier_count(me, empty)
    opp_frontier = _frontier_count(opp, empty)
    frontier_diff = my_frontier - opp_frontier

    stable_diff = _stable_edge_count(me) - _stable_edge_count(opp)

    bad_corner_adj = _corner_adjacent_difference(me, opp, occupied)

    if empty_count > 36:
        disc_weight = -1
        mobility_weight = 8
        potential_weight = 4
        position_weight = 3
        frontier_weight = -10
    elif empty_count > 16:
        disc_weight = 1
        mobility_weight = 7
        potential_weight = 3
        position_weight = 2
        frontier_weight = -12
    else:
        disc_weight = 12
        mobility_weight = 3
        potential_weight = 1
        position_weight = 1
        frontier_weight = -4

    if occupied_count:
        parity = 100 * disc_diff // occupied_count
    else:
        parity = 0

    score = 0
    score += position_weight * pos
    score += 1000 * corner_diff
    score -= 260 * bad_corner_adj
    score += mobility_weight * mobility
    score += potential_weight * potential
    score += frontier_weight * frontier_diff
    score += 95 * stable_diff
    score += disc_weight * parity

    return int(score)


def _terminal_score(me: int, opp: int) -> int:
    diff = _bit_count(me) - _bit_count(opp)
    if diff > 0:
        return WIN_SCORE + diff * 1000
    if diff < 0:
        return -WIN_SCORE + diff * 1000
    return 0


def _move_order_score(move: int, me: int, opp: int) -> int:
    occupied = me | opp
    flips = _flips_for_move(move, me, opp)
    score = POSITION_WEIGHTS[move] * 10 + _bit_count(flips) * 6

    if move in CORNER_SET:
        score += 100000

    for corner in CORNERS:
        if not (occupied & (1 << corner)) and move in CORNER_ADJACENT[corner]:
            if move in X_SQUARES:
                score -= 16000
            else:
                score -= 6000

    r, c = divmod(move, 8)
    if r == 0 or r == 7 or c == 0 or c == 7:
        score += 120

    return score


def _ordered_moves(moves, me: int, opp: int, preferred=None):
    if preferred is not None and preferred in moves:
        rest = [m for m in moves if m != preferred]
        rest.sort(key=lambda m: _move_order_score(m, me, opp), reverse=True)
        return [preferred] + rest
    return sorted(moves, key=lambda m: _move_order_score(m, me, opp), reverse=True)


def _negamax(me: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    alpha_orig = alpha
    key = (me, opp, depth)
    tt_entry = _tt.get(key)
    tt_move = None

    if tt_entry is not None:
        stored_depth, flag, value, best_move = tt_entry
        tt_move = best_move
        if stored_depth >= depth:
            if flag == 0:
                return value
            if flag == 1:
                alpha = max(alpha, value)
            elif flag == 2:
                beta = min(beta, value)
            if alpha >= beta:
                return value

    moves = _legal_moves(me, opp)

    if not moves:
        opp_moves = _legal_moves(opp, me)
        if not opp_moves:
            return _terminal_score(me, opp)
        return -_negamax(opp, me, depth, -beta, -alpha)

    if depth <= 0:
        return _evaluate(me, opp)

    best_value = -INF
    best_move = moves[0]

    for move in _ordered_moves(moves, me, opp, tt_move):
        new_me, new_opp = _apply_move(me, opp, move)
        value = -_negamax(new_opp, new_me, depth - 1, -beta, -alpha)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best_value <= alpha_orig:
        flag = 2
    elif best_value >= beta:
        flag = 1
    else:
        flag = 0

    _tt[key] = (depth, flag, best_value, best_move)
    return best_value


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _tt, _legal_cache, _flips_cache, _deadline, _nodes

    start = time.perf_counter()
    _deadline = start + 0.88
    _nodes = 0
    _tt = {}
    _legal_cache = {}
    _flips_cache = {}

    me = _array_to_bits(you)
    opp = _array_to_bits(opponent)

    legal = _legal_moves(me, opp)
    if not legal:
        return "pass"

    ordered = _ordered_moves(legal, me, opp)
    best_move = ordered[0]

    if len(ordered) == 1:
        return _move_to_str(best_move)

    occupied = _bit_count(me | opp)
    empties = 64 - occupied

    if empties <= 10:
        max_depth = empties + 2
    elif empties <= 18:
        max_depth = 14
    else:
        max_depth = 10

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= _deadline:
                break

            current_best = best_move
            current_score = -INF
            alpha = -INF
            beta = INF

            root_moves = _ordered_moves(legal, me, opp, best_move)

            for move in root_moves:
                _check_time()
                new_me, new_opp = _apply_move(me, opp, move)
                score = -_negamax(new_opp, new_me, depth - 1, -beta, -alpha)

                if score > current_score:
                    current_score = score
                    current_best = move

                if score > alpha:
                    alpha = score

            best_move = current_best

            if abs(current_score) >= WIN_SCORE:
                break

    except TimeoutError:
        pass

    if best_move not in legal:
        best_move = legal[0]

    return _move_to_str(best_move)
