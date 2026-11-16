
import time
import numpy as np

BOARD_N = 8
FULL_MASK = (1 << 64) - 1
INF = 10**18
FILES = "abcdefgh"

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

# Strong static square table. Corners are excellent; X-squares/C-squares are dangerous.
_POS_TABLE_2D = [
    [120, -25,  25,   8,   8,  25, -25, 120],
    [-25, -55, -10, -10, -10, -10, -55, -25],
    [ 25, -10,  18,   4,   4,  18, -10,  25],
    [  8, -10,   4,   1,   1,   4, -10,   8],
    [  8, -10,   4,   1,   1,   4, -10,   8],
    [ 25, -10,  18,   4,   4,  18, -10,  25],
    [-25, -55, -10, -10, -10, -10, -55, -25],
    [120, -25,  25,   8,   8,  25, -25, 120],
]
POS_WEIGHTS = []
for _r in range(8):
    for _c in range(8):
        POS_WEIGHTS.append(_POS_TABLE_2D[_r][_c])

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

CORNER_ADJACENT = {
    0:  (1 << 1) | (1 << 8) | (1 << 9),
    7:  (1 << 6) | (1 << 14) | (1 << 15),
    56: (1 << 48) | (1 << 49) | (1 << 57),
    63: (1 << 54) | (1 << 55) | (1 << 62),
}

# Precomputed rays from every square in each direction.
RAYS = [[] for _ in range(64)]
for r in range(8):
    for c in range(8):
        sq = r * 8 + c
        rays = []
        for dr, dc in DIRECTIONS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                ray.append(rr * 8 + cc)
                rr += dr
                cc += dc
            rays.append(ray)
        RAYS[sq] = rays

# Neighbor masks for frontier-disc evaluation.
NEIGH_MASK = [0] * 64
for r in range(8):
    for c in range(8):
        sq = r * 8 + c
        m = 0
        for dr, dc in DIRECTIONS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
        NEIGH_MASK[sq] = m


class _Timeout(Exception):
    pass


def _bit_count(x: int) -> int:
    return x.bit_count()


def _arrays_to_bits(you: np.ndarray, opponent: np.ndarray):
    my = 0
    opp = 0
    for r in range(8):
        for c in range(8):
            bit = 1 << (r * 8 + c)
            if you[r][c]:
                my |= bit
            elif opponent[r][c]:
                opp |= bit
    return my, opp


def _move_to_str(sq: int) -> str:
    return FILES[sq % 8] + str(sq // 8 + 1)


def _flips_for_move(my: int, opp: int, sq: int) -> int:
    bit = 1 << sq
    if (my | opp) & bit:
        return 0

    captured = 0
    for ray in RAYS[sq]:
        line = 0
        for s in ray:
            b = 1 << s
            if opp & b:
                line |= b
            elif my & b:
                if line:
                    captured |= line
                break
            else:
                break
    return captured


def _legal_moves_uncached(my: int, opp: int):
    empty = FULL_MASK & ~(my | opp)
    moves = []
    bb = empty
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        flips = _flips_for_move(my, opp, sq)
        if flips:
            moves.append((sq, flips))
        bb ^= lsb
    return moves


def _get_legal(my: int, opp: int, cache: dict):
    key = (my, opp)
    v = cache.get(key)
    if v is None:
        v = _legal_moves_uncached(my, opp)
        cache[key] = v
    return v


def _apply_move(my: int, opp: int, sq: int, flips: int):
    move_bit = 1 << sq
    my2 = my | move_bit | flips
    opp2 = opp & ~flips
    return my2, opp2


def _weighted_sum(bb: int) -> int:
    s = 0
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        s += POS_WEIGHTS[sq]
        bb ^= lsb
    return s


def _frontier_count(discs: int, empty: int) -> int:
    cnt = 0
    bb = discs
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        if NEIGH_MASK[sq] & empty:
            cnt += 1
        bb ^= lsb
    return cnt


def _terminal_score(my: int, opp: int) -> int:
    diff = _bit_count(my) - _bit_count(opp)
    if diff > 0:
        return 10000000 + diff * 10000
    if diff < 0:
        return -10000000 + diff * 10000
    return 0


def _evaluate(my: int, opp: int, cache: dict) -> int:
    occupied = my | opp
    empty = FULL_MASK & ~occupied
    empties = 64 - _bit_count(occupied)

    if empties == 0:
        return _terminal_score(my, opp)

    my_count = _bit_count(my)
    opp_count = _bit_count(opp)
    total_discs = my_count + opp_count

    # Disc parity: bad to over-emphasize early, crucial late.
    disc_score = 100 * (my_count - opp_count) / max(1, total_discs)

    my_moves = len(_get_legal(my, opp, cache))
    opp_moves = len(_get_legal(opp, my, cache))
    if my_moves + opp_moves:
        mobility_score = 100 * (my_moves - opp_moves) / (my_moves + opp_moves)
    else:
        return _terminal_score(my, opp)

    my_corners = _bit_count(my & CORNERS)
    opp_corners = _bit_count(opp & CORNERS)
    corner_score = 100 * (my_corners - opp_corners)

    # Penalize occupying squares adjacent to empty corners.
    close_score = 0
    for corner_sq, adj_mask in CORNER_ADJACENT.items():
        if not (occupied & (1 << corner_sq)):
            close_score -= 30 * _bit_count(my & adj_mask)
            close_score += 30 * _bit_count(opp & adj_mask)

    pos_score = _weighted_sum(my) - _weighted_sum(opp)

    my_frontier = _frontier_count(my, empty)
    opp_frontier = _frontier_count(opp, empty)
    if my_frontier + opp_frontier:
        frontier_score = 100 * (opp_frontier - my_frontier) / (my_frontier + opp_frontier)
    else:
        frontier_score = 0

    # Phase-dependent weighting.
    if empties > 44:
        return int(
            8.0 * mobility_score
            + 10.0 * corner_score
            + 2.0 * pos_score
            + 4.0 * close_score
            + 3.0 * frontier_score
            - 2.0 * disc_score
        )
    elif empties > 16:
        return int(
            7.0 * mobility_score
            + 12.0 * corner_score
            + 2.0 * pos_score
            + 4.0 * close_score
            + 2.0 * frontier_score
            + 2.0 * disc_score
        )
    else:
        return int(
            3.0 * mobility_score
            + 15.0 * corner_score
            + 1.0 * pos_score
            + 2.0 * close_score
            + 1.0 * frontier_score
            + 12.0 * disc_score
        )


def _move_order_score(my: int, opp: int, sq: int, flips: int) -> int:
    score = POS_WEIGHTS[sq] * 10 + 3 * _bit_count(flips)

    # Corners first.
    if (1 << sq) & CORNERS:
        score += 100000

    # If a corner is empty, adjacent moves are usually tactically dangerous.
    occupied = my | opp
    for corner_sq, adj_mask in CORNER_ADJACENT.items():
        if not (occupied & (1 << corner_sq)) and ((1 << sq) & adj_mask):
            score -= 2500

    return score


def _ordered_moves(my: int, opp: int, moves, tt_best=None):
    return sorted(
        moves,
        key=lambda mv: (10000000 if mv[0] == tt_best else 0) + _move_order_score(my, opp, mv[0], mv[1]),
        reverse=True,
    )


def _negamax(my: int, opp: int, depth: int, alpha: int, beta: int,
             deadline: float, nodes: list, tt: dict, cache: dict) -> int:
    nodes[0] += 1
    if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
        raise _Timeout()

    occupied = my | opp
    if depth <= 0 or occupied == FULL_MASK:
        return _evaluate(my, opp, cache)

    key = (my, opp)
    entry = tt.get(key)
    tt_best = None
    alpha_orig = alpha
    beta_orig = beta

    if entry is not None:
        e_depth, e_val, e_flag, e_best = entry
        tt_best = e_best
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            elif e_flag > 0:
                alpha = max(alpha, e_val)
            else:
                beta = min(beta, e_val)
            if alpha >= beta:
                return e_val

    moves = _get_legal(my, opp, cache)

    if not moves:
        opp_moves = _get_legal(opp, my, cache)
        if not opp_moves:
            return _terminal_score(my, opp)
        # Pass: same depth because no disc was placed.
        return -_negamax(opp, my, depth, -beta, -alpha, deadline, nodes, tt, cache)

    best_val = -INF
    best_sq = moves[0][0]

    for sq, flips in _ordered_moves(my, opp, moves, tt_best):
        my2, opp2 = _apply_move(my, opp, sq, flips)
        val = -_negamax(opp2, my2, depth - 1, -beta, -alpha, deadline, nodes, tt, cache)

        if val > best_val:
            best_val = val
            best_sq = sq

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = -1  # upper bound
    elif best_val >= beta_orig:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    tt[key] = (depth, best_val, flag, best_sq)
    return best_val


def _root_search(my: int, opp: int, depth: int, deadline: float, tt: dict, cache: dict):
    moves = _get_legal(my, opp, cache)
    if not moves:
        return None, 0

    entry = tt.get((my, opp))
    tt_best = entry[3] if entry is not None else None

    best_sq = moves[0][0]
    best_val = -INF
    alpha = -INF
    beta = INF
    nodes = [0]

    for sq, flips in _ordered_moves(my, opp, moves, tt_best):
        if time.perf_counter() > deadline:
            raise _Timeout()

        my2, opp2 = _apply_move(my, opp, sq, flips)
        val = -_negamax(opp2, my2, depth - 1, -beta, -alpha, deadline, nodes, tt, cache)

        if val > best_val:
            best_val = val
            best_sq = sq

        if val > alpha:
            alpha = val

    return best_sq, best_val


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    my, opp = _arrays_to_bits(you, opponent)

    cache = {}
    legal = _get_legal(my, opp, cache)

    if not legal:
        return "pass"

    # Always keep a legal fallback before doing any expensive search.
    fallback_sq = _ordered_moves(my, opp, legal)[0][0]
    best_sq = fallback_sq

    empties = 64 - _bit_count(my | opp)

    # Iterative deepening with conservative time budget.
    deadline = time.perf_counter() + 0.87
    tt = {}

    if empties <= 10:
        max_depth = empties + 2
    elif empties <= 14:
        max_depth = 12
    elif empties <= 22:
        max_depth = 8
    elif empties <= 40:
        max_depth = 6
    else:
        max_depth = 5

    # If only one legal move exists, return it immediately.
    if len(legal) == 1:
        return _move_to_str(legal[0][0])

    try:
        for depth in range(1, max_depth + 1):
            sq, _ = _root_search(my, opp, depth, deadline, tt, cache)
            if sq is not None:
                best_sq = sq
            if time.perf_counter() > deadline:
                break
    except _Timeout:
        pass
    except Exception:
        # Safety: never allow an unexpected issue to cause an illegal/no return.
        best_sq = fallback_sq

    # Final legality guard.
    legal_squares = {sq for sq, _ in legal}
    if best_sq not in legal_squares:
        best_sq = fallback_sq

    return _move_to_str(best_sq)
