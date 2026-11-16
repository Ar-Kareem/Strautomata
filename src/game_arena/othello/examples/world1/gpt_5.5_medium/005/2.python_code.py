
import time
from functools import lru_cache
import numpy as np

FULL = (1 << 64) - 1

COL_A = sum(1 << (r * 8) for r in range(8))
COL_H = sum(1 << (r * 8 + 7) for r in range(8))
NOT_A = FULL ^ COL_A
NOT_H = FULL ^ COL_H

DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

POS_TABLE_2D = [
    [120, -25,  20,   5,   5,  20, -25, 120],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [120, -25,  20,   5,   5,  20, -25, 120],
]
POS = [POS_TABLE_2D[r][c] for r in range(8) for c in range(8)]

CORNERS = (0, 7, 56, 63)
CORNER_MASK = sum(1 << i for i in CORNERS)

ADJACENT_TO_EMPTY_CORNER = {
    0:  (1, 8, 9),
    7:  (6, 14, 15),
    56: (48, 49, 57),
    63: (54, 55, 62),
}

X_SQUARE_TO_CORNER = {
    9: 0,
    14: 7,
    49: 56,
    54: 63,
}

C_SQUARE_TO_CORNER = {
    1: 0, 8: 0,
    6: 7, 15: 7,
    48: 56, 57: 56,
    55: 63, 62: 63,
}

INF = 10 ** 12
TIME_LIMIT = 0.90

TT = {}
DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


def _bit_index(r, c):
    return r * 8 + c


def _on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _arrays_to_bits(you, opponent):
    own = 0
    opp = 0
    y = np.asarray(you)
    o = np.asarray(opponent)
    for r in range(8):
        for c in range(8):
            bit = 1 << (r * 8 + c)
            if y[r][c]:
                own |= bit
            elif o[r][c]:
                opp |= bit
    return own, opp


def _move_to_string(idx):
    r, c = divmod(idx, 8)
    return chr(ord("a") + c) + str(r + 1)


@lru_cache(maxsize=300000)
def flips_for_move(own, opp, idx):
    bit = 1 << idx
    if (own | opp) & bit:
        return 0

    r0, c0 = divmod(idx, 8)
    flips = 0

    for dr, dc in DIRS:
        r = r0 + dr
        c = c0 + dc
        line = 0

        while _on_board(r, c):
            b = 1 << (r * 8 + c)
            if opp & b:
                line |= b
            elif own & b:
                if line:
                    flips |= line
                break
            else:
                break
            r += dr
            c += dc

    return flips


@lru_cache(maxsize=300000)
def legal_moves(own, opp):
    empty = FULL ^ (own | opp)
    moves = []

    e = empty
    while e:
        b = e & -e
        idx = b.bit_length() - 1
        if flips_for_move(own, opp, idx):
            moves.append(idx)
        e ^= b

    return tuple(moves)


def apply_move(own, opp, move):
    flips = flips_for_move(own, opp, move)
    bit = 1 << move
    return own | bit | flips, opp & ~flips


@lru_cache(maxsize=300000)
def neighbors(bb):
    n = 0
    n |= (bb & NOT_H) << 1
    n |= (bb & NOT_A) >> 1
    n |= bb << 8
    n |= bb >> 8
    n |= (bb & NOT_H) >> 7
    n |= (bb & NOT_A) >> 9
    n |= (bb & NOT_H) << 9
    n |= (bb & NOT_A) << 7
    return n & FULL


@lru_cache(maxsize=300000)
def positional_sum(bb):
    s = 0
    while bb:
        b = bb & -bb
        idx = b.bit_length() - 1
        s += POS[idx]
        bb ^= b
    return s


@lru_cache(maxsize=300000)
def edge_stable_count(bb):
    count = 0

    if bb & (1 << 0):
        for c in range(8):
            if bb & (1 << c):
                count += 1
            else:
                break
        for r in range(8):
            if bb & (1 << (r * 8)):
                count += 1
            else:
                break

    if bb & (1 << 7):
        for c in range(7, -1, -1):
            if bb & (1 << c):
                count += 1
            else:
                break
        for r in range(8):
            if bb & (1 << (r * 8 + 7)):
                count += 1
            else:
                break

    if bb & (1 << 56):
        for c in range(8):
            if bb & (1 << (56 + c)):
                count += 1
            else:
                break
        for r in range(7, -1, -1):
            if bb & (1 << (r * 8)):
                count += 1
            else:
                break

    if bb & (1 << 63):
        for c in range(7, -1, -1):
            if bb & (1 << (56 + c)):
                count += 1
            else:
                break
        for r in range(7, -1, -1):
            if bb & (1 << (r * 8 + 7)):
                count += 1
            else:
                break

    return count


@lru_cache(maxsize=300000)
def evaluate(own, opp):
    occupied = own | opp
    empty = FULL ^ occupied
    empties = 64 - occupied.bit_count()

    own_count = own.bit_count()
    opp_count = opp.bit_count()
    disc_diff = own_count - opp_count

    if empties == 0:
        return disc_diff * 100000

    my_moves = len(legal_moves(own, opp))
    op_moves = len(legal_moves(opp, own))

    if my_moves == 0 and op_moves == 0:
        return disc_diff * 100000

    phase = 64 - empties

    if empties > 44:
        disc_w = -4
        mobility_w = 95
        potential_w = 28
        frontier_w = 35
        pos_w = 7
    elif empties > 18:
        disc_w = 2
        mobility_w = 80
        potential_w = 20
        frontier_w = 28
        pos_w = 5
    else:
        disc_w = 16
        mobility_w = 45
        potential_w = 8
        frontier_w = 12
        pos_w = 2

    score = 0

    score += disc_w * disc_diff

    mobility_diff = my_moves - op_moves
    score += mobility_w * mobility_diff

    my_potential = (neighbors(opp) & empty).bit_count()
    op_potential = (neighbors(own) & empty).bit_count()
    score += potential_w * (my_potential - op_potential)

    my_frontier = (neighbors(empty) & own).bit_count()
    op_frontier = (neighbors(empty) & opp).bit_count()
    score += frontier_w * (op_frontier - my_frontier)

    my_corners = (own & CORNER_MASK).bit_count()
    op_corners = (opp & CORNER_MASK).bit_count()
    score += 900 * (my_corners - op_corners)

    for corner, adj in ADJACENT_TO_EMPTY_CORNER.items():
        cb = 1 << corner
        if not (occupied & cb):
            my_bad = 0
            op_bad = 0
            for a in adj:
                ab = 1 << a
                if own & ab:
                    my_bad += 1
                elif opp & ab:
                    op_bad += 1
            score += 85 * (op_bad - my_bad)

    score += pos_w * (positional_sum(own) - positional_sum(opp))

    score += 75 * (edge_stable_count(own) - edge_stable_count(opp))

    if empties <= 12:
        score += 30 * disc_diff

    return int(score)


def static_move_score(own, opp, move):
    occupied = own | opp
    bit = 1 << move
    flips = flips_for_move(own, opp, move)

    score = POS[move] * 12 + flips.bit_count() * 3

    if bit & CORNER_MASK:
        score += 100000

    if move in X_SQUARE_TO_CORNER:
        corner = X_SQUARE_TO_CORNER[move]
        if not (occupied & (1 << corner)):
            score -= 12000

    if move in C_SQUARE_TO_CORNER:
        corner = C_SQUARE_TO_CORNER[move]
        if not (occupied & (1 << corner)):
            score -= 3500

    nown, nopp = apply_move(own, opp, move)
    opp_corner_moves = legal_moves(nopp, nown)
    for m in opp_corner_moves:
        if (1 << m) & CORNER_MASK:
            score -= 25000

    return score


def order_moves(own, opp, moves, preferred=-1):
    scored = []
    for m in moves:
        if m == preferred:
            scored.append((10 ** 9, m))
        else:
            scored.append((static_move_score(own, opp, m), m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def check_time():
    global NODES
    NODES += 1
    if (NODES & 2047) == 0:
        if time.perf_counter() > DEADLINE:
            raise SearchTimeout()


def negamax(own, opp, depth, alpha, beta):
    check_time()

    alpha_orig = alpha
    key = (own, opp)
    entry = TT.get(key)
    tt_best = -1

    if entry is not None:
        e_depth, e_value, e_flag, e_best = entry
        tt_best = e_best
        if e_depth >= depth:
            if e_flag == 0:
                return e_value
            elif e_flag == 1:
                alpha = max(alpha, e_value)
            else:
                beta = min(beta, e_value)
            if alpha >= beta:
                return e_value

    moves = legal_moves(own, opp)

    if not moves:
        opp_moves = legal_moves(opp, own)
        if not opp_moves:
            value = (own.bit_count() - opp.bit_count()) * 100000
            TT[key] = (depth, value, 0, -1)
            return value

        value = -negamax(opp, own, depth, -beta, -alpha)
        TT[key] = (depth, value, 0, -1)
        return value

    if depth <= 0:
        value = evaluate(own, opp)
        TT[key] = (depth, value, 0, -1)
        return value

    best_value = -INF
    best_move = moves[0]

    for move in order_moves(own, opp, moves, tt_best):
        nown, nopp = apply_move(own, opp, move)
        value = -negamax(nopp, nown, depth - 1, -beta, -alpha)

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

    TT[key] = (depth, int(best_value), flag, best_move)
    return int(best_value)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global DEADLINE, NODES, TT

    start = time.perf_counter()
    DEADLINE = start + TIME_LIMIT
    NODES = 0

    if len(TT) > 500000:
        TT.clear()

    own, opp = _arrays_to_bits(you, opponent)
    moves = legal_moves(own, opp)

    if not moves:
        return "pass"

    if len(moves) == 1:
        return _move_to_string(moves[0])

    ordered = order_moves(own, opp, moves)
    best_move = ordered[0]

    occupied = own | opp
    empties = 64 - occupied.bit_count()

    if empties <= 10:
        max_depth = 64
    elif empties <= 16:
        max_depth = 18
    elif empties <= 26:
        max_depth = 10
    else:
        max_depth = 8

    try:
        for depth in range(1, max_depth + 1):
            alpha = -INF
            beta = INF
            local_best = best_move
            local_best_value = -INF

            root_order = order_moves(own, opp, moves, best_move)

            for move in root_order:
                if time.perf_counter() > DEADLINE:
                    raise SearchTimeout()

                nown, nopp = apply_move(own, opp, move)
                value = -negamax(nopp, nown, depth - 1, -beta, -alpha)

                if value > local_best_value:
                    local_best_value = value
                    local_best = move

                if value > alpha:
                    alpha = value

            best_move = local_best

    except SearchTimeout:
        pass
    except Exception:
        best_move = ordered[0]

    if best_move not in moves:
        best_move = moves[0]

    return _move_to_string(best_move)
