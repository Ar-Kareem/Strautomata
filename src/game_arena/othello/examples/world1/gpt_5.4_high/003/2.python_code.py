
import time
from functools import lru_cache
import numpy as np

FULL = 0xFFFFFFFFFFFFFFFF
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
INF = 10**9

# Standard Othello positional weights.
BASE_WEIGHTS = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
]

IDX_TO_STR = [chr(ord("a") + (i % 8)) + str(i // 8 + 1) for i in range(64)]

# Danger-square metadata:
# kind 1 = C-square, kind 2 = X-square
DANGER_CORNER = [0] * 64
DANGER_KIND = [0] * 64

for idx in (1, 8):
    DANGER_CORNER[idx] = 1 << 0
    DANGER_KIND[idx] = 1
DANGER_CORNER[9] = 1 << 0
DANGER_KIND[9] = 2

for idx in (6, 15):
    DANGER_CORNER[idx] = 1 << 7
    DANGER_KIND[idx] = 1
DANGER_CORNER[14] = 1 << 7
DANGER_KIND[14] = 2

for idx in (48, 57):
    DANGER_CORNER[idx] = 1 << 56
    DANGER_KIND[idx] = 1
DANGER_CORNER[49] = 1 << 56
DANGER_KIND[49] = 2

for idx in (55, 62):
    DANGER_CORNER[idx] = 1 << 63
    DANGER_KIND[idx] = 1
DANGER_CORNER[54] = 1 << 63
DANGER_KIND[54] = 2

CORNER_DATA = [
    (1 << 0,  1 << 9,  (1 << 1)  | (1 << 8)),
    (1 << 7,  1 << 14, (1 << 6)  | (1 << 15)),
    (1 << 56, 1 << 49, (1 << 48) | (1 << 57)),
    (1 << 63, 1 << 54, (1 << 55) | (1 << 62)),
]


class Timeout(Exception):
    pass


def bit_to_str(move_bit: int) -> str:
    return IDX_TO_STR[move_bit.bit_length() - 1]


def array_to_bitboard(arr: np.ndarray) -> int:
    bb = 0
    for i in np.flatnonzero(arr):
        bb |= 1 << int(i)
    return bb


def ratio(a: int, b: int) -> int:
    s = a + b
    if s == 0:
        return 0
    return int(100 * (a - b) / s)


@lru_cache(maxsize=131072)
def gen_moves(player: int, opp: int) -> int:
    empty = FULL ^ (player | opp)
    moves = 0

    x = ((player & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    moves |= ((x & NOT_H) << 1) & empty

    x = ((player & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    moves |= ((x & NOT_A) >> 1) & empty

    x = (player << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    moves |= (x << 8) & empty

    x = (player >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    moves |= (x >> 8) & empty

    x = ((player & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    moves |= ((x & NOT_H) << 9) & empty

    x = ((player & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    moves |= ((x & NOT_A) << 7) & empty

    x = ((player & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    moves |= ((x & NOT_H) >> 7) & empty

    x = ((player & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    moves |= ((x & NOT_A) >> 9) & empty

    return moves


def calc_flips(player: int, opp: int, move: int) -> int:
    flips = 0

    x = (move & NOT_H) << 1
    captured = 0
    while x and (x & opp):
        captured |= x
        x = (x & NOT_H) << 1
    if x & player:
        flips |= captured

    x = (move & NOT_A) >> 1
    captured = 0
    while x and (x & opp):
        captured |= x
        x = (x & NOT_A) >> 1
    if x & player:
        flips |= captured

    x = move << 8
    captured = 0
    while x and (x & opp):
        captured |= x
        x <<= 8
    if x & player:
        flips |= captured

    x = move >> 8
    captured = 0
    while x and (x & opp):
        captured |= x
        x >>= 8
    if x & player:
        flips |= captured

    x = (move & NOT_H) << 9
    captured = 0
    while x and (x & opp):
        captured |= x
        x = (x & NOT_H) << 9
    if x & player:
        flips |= captured

    x = (move & NOT_A) << 7
    captured = 0
    while x and (x & opp):
        captured |= x
        x = (x & NOT_A) << 7
    if x & player:
        flips |= captured

    x = (move & NOT_H) >> 7
    captured = 0
    while x and (x & opp):
        captured |= x
        x = (x & NOT_H) >> 7
    if x & player:
        flips |= captured

    x = (move & NOT_A) >> 9
    captured = 0
    while x and (x & opp):
        captured |= x
        x = (x & NOT_A) >> 9
    if x & player:
        flips |= captured

    return flips


@lru_cache(maxsize=65536)
def expand_neighbors(bb: int) -> int:
    return (
        (((bb & NOT_H) << 1) |
         ((bb & NOT_A) >> 1) |
         (bb << 8) |
         (bb >> 8) |
         ((bb & NOT_H) << 9) |
         ((bb & NOT_A) << 7) |
         ((bb & NOT_H) >> 7) |
         ((bb & NOT_A) >> 9))
        & FULL
    )


@lru_cache(maxsize=65536)
def weighted_sum(bb: int) -> int:
    s = 0
    while bb:
        lsb = bb & -bb
        s += BASE_WEIGHTS[lsb.bit_length() - 1]
        bb ^= lsb
    return s


@lru_cache(maxsize=65536)
def edge_stable_mask(p: int) -> int:
    stable = 0

    if p & (1 << 0):
        x = 1 << 0
        while x and (p & x):
            stable |= x
            x = (x & NOT_H) << 1
        x = 1 << 8
        while x and (p & x):
            stable |= x
            x <<= 8

    if p & (1 << 7):
        x = 1 << 7
        while x and (p & x):
            stable |= x
            x = (x & NOT_A) >> 1
        x = 1 << 15
        while x and (p & x):
            stable |= x
            x <<= 8

    if p & (1 << 56):
        x = 1 << 56
        while x and (p & x):
            stable |= x
            x = (x & NOT_H) << 1
        x = 1 << 48
        while x and (p & x):
            stable |= x
            x >>= 8

    if p & (1 << 63):
        x = 1 << 63
        while x and (p & x):
            stable |= x
            x = (x & NOT_A) >> 1
        x = 1 << 55
        while x and (p & x):
            stable |= x
            x >>= 8

    return stable


def corner_adj_score(player: int, opp: int) -> int:
    board = player | opp
    score = 0
    for corner, xmask, cmask in CORNER_DATA:
        adjmask = xmask | cmask
        if not (board & corner):
            score -= 40 * ((player & xmask).bit_count())
            score += 40 * ((opp & xmask).bit_count())
            score -= 14 * ((player & cmask).bit_count())
            score += 14 * ((opp & cmask).bit_count())
        elif player & corner:
            score += 6 * ((player & adjmask).bit_count())
            score -= 6 * ((opp & adjmask).bit_count())
        else:
            score -= 6 * ((player & adjmask).bit_count())
            score += 6 * ((opp & adjmask).bit_count())
    return score


def evaluate(player: int, opp: int, empty_count: int, my_moves_bb: int | None = None) -> int:
    my_discs = player.bit_count()
    opp_discs = opp.bit_count()

    if my_moves_bb is None:
        my_moves_bb = gen_moves(player, opp)
    opp_moves_bb = gen_moves(opp, player)

    mobility = ratio(my_moves_bb.bit_count(), opp_moves_bb.bit_count())

    empty = FULL ^ (player | opp)
    my_potential = (expand_neighbors(opp) & empty).bit_count()
    opp_potential = (expand_neighbors(player) & empty).bit_count()
    potential = ratio(my_potential, opp_potential)

    adj_empty = expand_neighbors(empty)
    my_frontier = (player & adj_empty).bit_count()
    opp_frontier = (opp & adj_empty).bit_count()
    frontier = ratio(opp_frontier, my_frontier)  # fewer frontier discs is better

    corner_diff = (player & CORNERS).bit_count() - (opp & CORNERS).bit_count()
    stable_diff = edge_stable_mask(player).bit_count() - edge_stable_mask(opp).bit_count()
    pos = weighted_sum(player) - weighted_sum(opp)
    disc = ratio(my_discs, opp_discs)
    c_adj = corner_adj_score(player, opp)
    parity = 8 if (empty_count & 1) else -8

    if empty_count > 44:
        score = (
            12 * mobility +
             6 * potential +
             3 * frontier +
             2 * pos +
           180 * corner_diff +
            10 * stable_diff -
             4 * disc +
             c_adj
        )
    elif empty_count > 20:
        score = (
            10 * mobility +
             4 * potential +
             2 * frontier +
             2 * pos +
           220 * corner_diff +
            14 * stable_diff +
             2 * disc +
             c_adj
        )
    else:
        score = (
             6 * mobility +
             2 * potential +
             2 * frontier +
                 pos +
           260 * corner_diff +
            20 * stable_diff +
            12 * disc +
             parity +
             c_adj
        )

    return int(score)


def gen_move_list(player: int, opp: int, moves_bb: int, tt_move: int = 0):
    board = player | opp
    out = []
    while moves_bb:
        move = moves_bb & -moves_bb
        moves_bb ^= move
        flips = calc_flips(player, opp, move)
        idx = move.bit_length() - 1

        score = BASE_WEIGHTS[idx] * 4 + flips.bit_count() * 8

        if move & CORNERS:
            score += 100000
        if tt_move and move == tt_move:
            score += 200000

        danger_corner = DANGER_CORNER[idx]
        if danger_corner and not (board & danger_corner):
            if DANGER_KIND[idx] == 2:
                score -= 5000
            else:
                score -= 2000

        out.append((score, move, flips))

    out.sort(key=lambda t: t[0], reverse=True)
    return out


def search(player: int, opp: int, depth: int, alpha: int, beta: int, ctx) -> tuple[int, int]:
    ctx["nodes"] += 1
    if (ctx["nodes"] & 511) == 0 and time.perf_counter() >= ctx["end"]:
        raise Timeout

    moves = gen_moves(player, opp)

    if not moves:
        opp_moves = gen_moves(opp, player)
        if not opp_moves:
            diff = player.bit_count() - opp.bit_count()
            return diff * 1000, 0
        score, _ = search(opp, player, depth, -beta, -alpha, ctx)
        return -score, 0

    if depth <= 0:
        empty_count = 64 - (player | opp).bit_count()
        return evaluate(player, opp, empty_count, moves), 0

    tt = ctx["tt"]
    key = (player, opp)
    alpha0, beta0 = alpha, beta
    tt_best = 0

    entry = tt.get(key)
    if entry is not None:
        stored_depth, flag, val, best = entry
        tt_best = best
        if stored_depth >= depth:
            if flag == 0:  # exact
                return val, best
            elif flag == 1:  # lower
                if val > alpha:
                    alpha = val
            else:  # upper
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val, best

    best_score = -INF
    best_move = 0
    ordered = gen_move_list(player, opp, moves, tt_best)

    first = True
    for _, move, flips in ordered:
        next_player = opp & ~flips
        next_opp = player | move | flips

        if first:
            score, _ = search(next_player, next_opp, depth - 1, -beta, -alpha, ctx)
            score = -score
            first = False
        else:
            score, _ = search(next_player, next_opp, depth - 1, -alpha - 1, -alpha, ctx)
            score = -score
            if alpha < score < beta:
                score, _ = search(next_player, next_opp, depth - 1, -beta, -alpha, ctx)
                score = -score

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best_score <= alpha0:
        flag = 2  # upper
    elif best_score >= beta0:
        flag = 1  # lower
    else:
        flag = 0  # exact
    tt[key] = (depth, flag, best_score, best_move)

    return best_score, best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    player = array_to_bitboard(you)
    opp = array_to_bitboard(opponent)

    moves = gen_moves(player, opp)
    if moves == 0:
        return "pass"

    # One legal move only: play it immediately.
    if (moves & (moves - 1)) == 0:
        return bit_to_str(moves)

    # If there is exactly one corner available, take it immediately.
    corner_moves = moves & CORNERS
    if corner_moves and (corner_moves & (corner_moves - 1)) == 0:
        return bit_to_str(corner_moves)

    deadline = time.perf_counter() + 0.95
    ctx = {"end": deadline, "nodes": 0, "tt": {}}

    root_moves = gen_move_list(player, opp, moves)
    best_move = root_moves[0][1] if root_moves else (moves & -moves)

    empties = 64 - (player | opp).bit_count()
    legal_count = moves.bit_count()

    if empties <= 12:
        max_depth = empties  # exact search
    elif empties <= 16:
        max_depth = 14
    elif empties <= 24:
        max_depth = 10
    elif empties <= 36:
        max_depth = 8
    else:
        max_depth = 7

    if legal_count <= 4 and max_depth < empties:
        max_depth += 1
    if max_depth > empties:
        max_depth = empties

    prev_score = 0

    try:
        for depth in range(1, max_depth + 1):
            if depth >= 4:
                window = 120
                a = max(-INF, prev_score - window)
                b = min(INF, prev_score + window)
                score, move = search(player, opp, depth, a, b, ctx)
                if score <= a or score >= b:
                    score, move = search(player, opp, depth, -INF, INF, ctx)
            else:
                score, move = search(player, opp, depth, -INF, INF, ctx)

            prev_score = score
            if move:
                best_move = move

            if time.perf_counter() >= deadline:
                break

    except Timeout:
        pass

    if not best_move or not (best_move & moves):
        best_move = root_moves[0][1] if root_moves else (moves & -moves)

    return bit_to_str(best_move)
