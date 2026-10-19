
import time
import numpy as np

FULL = (1 << 64) - 1
INF = 10**9

NOT_A_FILE = 0xFEFEFEFEFEFEFEFE
NOT_H_FILE = 0x7F7F7F7F7F7F7F7F

EXACT = 0
LOWER = 1
UPPER = 2

# Globals used by search
DEADLINE = 0.0
NODE_COUNT = 0
TT = {}


class Timeout(Exception):
    pass


def shift_n(x):
    return x >> 8


def shift_s(x):
    return (x << 8) & FULL


def shift_e(x):
    return ((x & NOT_H_FILE) << 1) & FULL


def shift_w(x):
    return (x & NOT_A_FILE) >> 1


def shift_ne(x):
    return (x & NOT_H_FILE) >> 7


def shift_nw(x):
    return (x & NOT_A_FILE) >> 9


def shift_se(x):
    return ((x & NOT_H_FILE) << 9) & FULL


def shift_sw(x):
    return ((x & NOT_A_FILE) << 7) & FULL


SHIFTS = (shift_n, shift_s, shift_e, shift_w, shift_ne, shift_nw, shift_se, shift_sw)

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

POS_WEIGHTS = [
    120, -20, 20, 5, 5, 20, -20, 120,
    -20, -40, -5, -5, -5, -5, -40, -20,
    20, -5, 15, 3, 3, 15, -5, 20,
    5, -5, 3, 3, 3, 3, -5, 5,
    5, -5, 3, 3, 3, 3, -5, 5,
    20, -5, 15, 3, 3, 15, -5, 20,
    -20, -40, -5, -5, -5, -5, -40, -20,
    120, -20, 20, 5, 5, 20, -20, 120,
]

BIT_TO_WEIGHT = {1 << i: POS_WEIGHTS[i] for i in range(64)}
BIT_TO_COORD = {1 << i: f"{chr(97 + (i % 8))}{(i // 8) + 1}" for i in range(64)}

# Dangerous squares near empty corners
X_TO_CORNER = {
    1 << 9: 1 << 0,     # b2 -> a1
    1 << 14: 1 << 7,    # g2 -> h1
    1 << 49: 1 << 56,   # b7 -> a8
    1 << 54: 1 << 63,   # g7 -> h8
}

C_TO_CORNER = {
    1 << 1: 1 << 0,     # b1 -> a1
    1 << 8: 1 << 0,     # a2 -> a1
    1 << 6: 1 << 7,     # g1 -> h1
    1 << 15: 1 << 7,    # h2 -> h1
    1 << 48: 1 << 56,   # a7 -> a8
    1 << 57: 1 << 56,   # b8 -> a8
    1 << 55: 1 << 63,   # h7 -> h8
    1 << 62: 1 << 63,   # g8 -> h8
}

CORNER_INFO = [
    (1 << 0,  (1 << 1) | (1 << 8) | (1 << 9)),
    (1 << 7,  (1 << 6) | (1 << 14) | (1 << 15)),
    (1 << 56, (1 << 48) | (1 << 49) | (1 << 57)),
    (1 << 63, (1 << 54) | (1 << 55) | (1 << 62)),
]

CORNER_RAYS = [
    ([0, 1, 2, 3, 4, 5, 6, 7], [0, 8, 16, 24, 32, 40, 48, 56]),
    ([7, 6, 5, 4, 3, 2, 1, 0], [7, 15, 23, 31, 39, 47, 55, 63]),
    ([56, 57, 58, 59, 60, 61, 62, 63], [56, 48, 40, 32, 24, 16, 8, 0]),
    ([63, 62, 61, 60, 59, 58, 57, 56], [63, 55, 47, 39, 31, 23, 15, 7]),
]


def iter_bits(bb):
    while bb:
        lsb = bb & -bb
        yield lsb
        bb ^= lsb


def adjacent(bits):
    return (
        shift_n(bits) | shift_s(bits) | shift_e(bits) | shift_w(bits) |
        shift_ne(bits) | shift_nw(bits) | shift_se(bits) | shift_sw(bits)
    )


def legal_moves(player, opp):
    empty = FULL ^ (player | opp)
    moves = 0
    for shift in SHIFTS:
        t = shift(player) & opp
        t |= shift(t) & opp
        t |= shift(t) & opp
        t |= shift(t) & opp
        t |= shift(t) & opp
        t |= shift(t) & opp
        moves |= shift(t) & empty
    return moves


def apply_move(player, opp, move):
    flips = 0
    for shift in SHIFTS:
        x = shift(move)
        captured = 0
        while x and (x & opp):
            captured |= x
            x = shift(x)
        if x & player:
            flips |= captured
    new_player = player | move | flips
    new_opp = opp & ~flips
    return new_player, new_opp


def weighted_sum(bits):
    s = 0
    while bits:
        lsb = bits & -bits
        s += BIT_TO_WEIGHT[lsb]
        bits ^= lsb
    return s


def corner_run_count(bits):
    total = 0
    for row_seq, col_seq in CORNER_RAYS:
        corner_bit = 1 << row_seq[0]
        if bits & corner_bit:
            a = 0
            for idx in row_seq:
                if bits & (1 << idx):
                    a += 1
                else:
                    break
            b = 0
            for idx in col_seq:
                if bits & (1 << idx):
                    b += 1
                else:
                    break
            total += a + b - 1
    return total


def terminal_value(player, opp):
    diff = player.bit_count() - opp.bit_count()
    if diff > 0:
        return 100000 + diff
    if diff < 0:
        return -100000 + diff
    return 0


def evaluate(player, opp):
    my_discs = player.bit_count()
    opp_discs = opp.bit_count()
    empties = 64 - my_discs - opp_discs

    my_moves_bb = legal_moves(player, opp)
    opp_moves_bb = legal_moves(opp, player)
    my_moves = my_moves_bb.bit_count()
    opp_moves = opp_moves_bb.bit_count()

    corner_diff = (player & CORNERS).bit_count() - (opp & CORNERS).bit_count()

    corner_adj_diff = 0
    for corner, adjmask in CORNER_INFO:
        if ((player | opp) & corner) == 0:
            corner_adj_diff += (player & adjmask).bit_count()
            corner_adj_diff -= (opp & adjmask).bit_count()

    empty = FULL ^ (player | opp)
    front_mask = adjacent(empty)
    frontier_diff = (player & front_mask).bit_count() - (opp & front_mask).bit_count()

    pot_my = (adjacent(opp) & empty).bit_count()
    pot_opp = (adjacent(player) & empty).bit_count()
    potential_diff = pot_my - pot_opp

    positional = weighted_sum(player) - weighted_sum(opp)
    edge_stability = corner_run_count(player) - corner_run_count(opp)
    disc_diff = my_discs - opp_discs

    if empties > 44:
        return (
            125 * corner_diff
            - 35 * corner_adj_diff
            + 10 * (my_moves - opp_moves)
            + 6 * potential_diff
            - 6 * frontier_diff
            + 2 * positional
            + 8 * edge_stability
        )
    elif empties > 20:
        return (
            150 * corner_diff
            - 30 * corner_adj_diff
            + 12 * (my_moves - opp_moves)
            + 4 * potential_diff
            - 8 * frontier_diff
            + 2 * positional
            + 12 * edge_stability
            + 2 * disc_diff
        )
    else:
        return (
            200 * corner_diff
            - 20 * corner_adj_diff
            + 10 * (my_moves - opp_moves)
            - 6 * frontier_diff
            + 2 * positional
            + 15 * edge_stability
            + 15 * disc_diff
        )


def order_moves(player, opp, moves, tt_move=0, deep=False):
    board = player | opp
    ordered = []

    for move in iter_bits(moves):
        score = 0

        if move == tt_move:
            score += 200000

        score += 20 * BIT_TO_WEIGHT[move]

        if move & CORNERS:
            score += 100000

        corner = X_TO_CORNER.get(move, 0)
        if corner and not (board & corner):
            score -= 45000

        corner = C_TO_CORNER.get(move, 0)
        if corner and not (board & corner):
            score -= 15000

        if deep:
            new_player, new_opp = apply_move(player, opp, move)
            opp_legal = legal_moves(new_opp, new_player)
            opp_count = opp_legal.bit_count()
            score -= 250 * opp_count
            if opp_legal & CORNERS:
                score -= 40000
            if opp_count == 0:
                score += 6000

        ordered.append((score, move))

    ordered.sort(reverse=True)
    return [m for _, m in ordered]


def negamax(player, opp, depth, alpha, beta, passed):
    global NODE_COUNT, TT, DEADLINE

    NODE_COUNT += 1
    if (NODE_COUNT & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise Timeout

    key = (player, opp, passed)
    alpha_orig = alpha
    beta_orig = beta

    entry = TT.get(key)
    tt_move = 0
    if entry is not None:
        e_depth, e_val, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_val
            elif e_flag == LOWER:
                alpha = max(alpha, e_val)
            else:
                beta = min(beta, e_val)
            if alpha >= beta:
                return e_val

    moves = legal_moves(player, opp)

    if moves == 0:
        if passed:
            return terminal_value(player, opp)
        val = -negamax(opp, player, depth, -beta, -alpha, True)
        TT[key] = (depth, val, EXACT, 0)
        return val

    if depth <= 0:
        return evaluate(player, opp)

    best = -INF
    best_move = 0

    ordered = order_moves(player, opp, moves, tt_move=tt_move, deep=(depth >= 4))

    for move in ordered:
        new_player, new_opp = apply_move(player, opp, move)
        val = -negamax(new_opp, new_player, depth - 1, -beta, -alpha, False)

        if val > best:
            best = val
            best_move = move

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best, flag, best_move)
    return best


def search_root(player, opp, depth):
    entry = TT.get((player, opp, False))
    tt_move = entry[3] if entry is not None else 0

    moves = legal_moves(player, opp)
    ordered = order_moves(player, opp, moves, tt_move=tt_move, deep=True)

    alpha = -INF
    beta = INF
    best = -INF
    best_move = 0

    for move in ordered:
        if time.perf_counter() > DEADLINE:
            raise Timeout

        new_player, new_opp = apply_move(player, opp, move)
        val = -negamax(new_opp, new_player, depth - 1, -beta, -alpha, False)

        if val > best:
            best = val
            best_move = move

        if val > alpha:
            alpha = val

    TT[(player, opp, False)] = (depth, best, EXACT, best_move)
    return best, best_move


def arrays_to_bitboards(you, opponent):
    player = 0
    opp = 0
    for r in range(8):
        for c in range(8):
            idx = r * 8 + c
            if you[r, c]:
                player |= 1 << idx
            elif opponent[r, c]:
                opp |= 1 << idx
    return player, opp


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global DEADLINE, NODE_COUNT, TT

    player, opp = arrays_to_bitboards(you, opponent)
    moves = legal_moves(player, opp)

    if moves == 0:
        return "pass"

    fallback = moves & -moves
    best_move = fallback

    NODE_COUNT = 0
    TT = {}
    start = time.perf_counter()
    DEADLINE = start + 0.94

    empties = 64 - (player | opp).bit_count()
    if empties > 52:
        max_depth = 5
    elif empties > 44:
        max_depth = 6
    elif empties > 32:
        max_depth = 7
    elif empties > 20:
        max_depth = 8
    else:
        max_depth = 64

    try:
        depth = 1
        while depth <= max_depth:
            val, move = search_root(player, opp, depth)
            if move:
                best_move = move
            if abs(val) >= 100000 and depth >= empties:
                break
            depth += 1
    except Timeout:
        pass

    if not (best_move & moves):
        best_move = fallback

    return BIT_TO_COORD[best_move]
