
import numpy as np
from time import perf_counter

FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

EXACT = 0
LOWER = 1
UPPER = 2
INF = 10**9

DEADLINE = 0.0
TT = {}
NODES = 0


class Timeout(Exception):
    pass


def sh_n(x):
    return x >> 8


def sh_s(x):
    return (x << 8) & FULL


def sh_e(x):
    return ((x & NOT_H) << 1) & FULL


def sh_w(x):
    return (x & NOT_A) >> 1


def sh_ne(x):
    return (x & NOT_H) >> 7


def sh_nw(x):
    return (x & NOT_A) >> 9


def sh_se(x):
    return ((x & NOT_H) << 9) & FULL


def sh_sw(x):
    return ((x & NOT_A) << 7) & FULL


SHIFTS = (sh_n, sh_s, sh_e, sh_w, sh_ne, sh_nw, sh_se, sh_sw)

WEIGHTS = [
    [120, -20, 20, 5, 5, 20, -20, 120],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [20, -5, 15, 3, 3, 15, -5, 20],
    [5, -5, 3, 3, 3, 3, -5, 5],
    [5, -5, 3, 3, 3, 3, -5, 5],
    [20, -5, 15, 3, 3, 15, -5, 20],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [120, -20, 20, 5, 5, 20, -20, 120],
]

ORDER_WEIGHTS = [w * 10 for row in WEIGHTS for w in row]

POS_TABLE = [[0] * 256 for _ in range(8)]
for r in range(8):
    row = WEIGHTS[r]
    for b in range(256):
        s = 0
        x = b
        while x:
            lsb = x & -x
            c = lsb.bit_length() - 1
            s += row[c]
            x -= lsb
        POS_TABLE[r][b] = s

CORNER_ADJ = (
    ((1 << 0), (1 << 1) | (1 << 8) | (1 << 9)),         # a1: b1, a2, b2
    ((1 << 7), (1 << 6) | (1 << 14) | (1 << 15)),       # h1: g1, g2, h2
    ((1 << 56), (1 << 48) | (1 << 49) | (1 << 57)),     # a8: a7, b7, b8
    ((1 << 63), (1 << 54) | (1 << 55) | (1 << 62)),     # h8: g7, h7, g8
)


def array_to_bb(arr):
    bb = 0
    for i in np.flatnonzero(arr):
        bb |= 1 << int(i)
    return bb


def move_to_str(move):
    idx = move.bit_length() - 1
    return "abcdefgh"[idx & 7] + str((idx >> 3) + 1)


def neighbors(bb):
    return (
        sh_n(bb) | sh_s(bb) | sh_e(bb) | sh_w(bb) |
        sh_ne(bb) | sh_nw(bb) | sh_se(bb) | sh_sw(bb)
    )


def legal_moves(player, opp):
    empty = FULL ^ (player | opp)
    moves = 0
    for sh in SHIFTS:
        x = sh(player) & opp
        x |= sh(x) & opp
        x |= sh(x) & opp
        x |= sh(x) & opp
        x |= sh(x) & opp
        x |= sh(x) & opp
        moves |= sh(x) & empty
    return moves


def play(player, opp, move):
    flips = 0
    for sh in SHIFTS:
        x = sh(move)
        captured = 0
        while x and (x & opp):
            captured |= x
            x = sh(x)
        if x & player:
            flips |= captured
    return player | move | flips, opp & ~flips, flips.bit_count()


def positional_score(bb):
    return (
        POS_TABLE[0][bb & 255] +
        POS_TABLE[1][(bb >> 8) & 255] +
        POS_TABLE[2][(bb >> 16) & 255] +
        POS_TABLE[3][(bb >> 24) & 255] +
        POS_TABLE[4][(bb >> 32) & 255] +
        POS_TABLE[5][(bb >> 40) & 255] +
        POS_TABLE[6][(bb >> 48) & 255] +
        POS_TABLE[7][(bb >> 56) & 255]
    )


def stable_edge_count(bb):
    mask = 0

    if bb & (1 << 0):
        for c in range(8):
            bit = 1 << c
            if bb & bit:
                mask |= bit
            else:
                break
        for r in range(8):
            bit = 1 << (8 * r)
            if bb & bit:
                mask |= bit
            else:
                break

    if bb & (1 << 7):
        for c in range(7, -1, -1):
            bit = 1 << c
            if bb & bit:
                mask |= bit
            else:
                break
        for r in range(8):
            bit = 1 << (8 * r + 7)
            if bb & bit:
                mask |= bit
            else:
                break

    if bb & (1 << 56):
        for c in range(8):
            bit = 1 << (56 + c)
            if bb & bit:
                mask |= bit
            else:
                break
        for r in range(7, -1, -1):
            bit = 1 << (8 * r)
            if bb & bit:
                mask |= bit
            else:
                break

    if bb & (1 << 63):
        for c in range(7, -1, -1):
            bit = 1 << (56 + c)
            if bb & bit:
                mask |= bit
            else:
                break
        for r in range(7, -1, -1):
            bit = 1 << (8 * r + 7)
            if bb & bit:
                mask |= bit
            else:
                break

    return mask.bit_count()


def corner_closeness(player, opp):
    occupied = player | opp
    s = 0
    for corner, adj in CORNER_ADJ:
        if not (occupied & corner):
            s += (opp & adj).bit_count() - (player & adj).bit_count()
    return s


def norm(a, b):
    t = a + b
    if t == 0:
        return 0
    return (100 * (a - b)) // t


def terminal_value(player, opp):
    diff = player.bit_count() - opp.bit_count()
    if diff > 0:
        return 1_000_000 + diff
    if diff < 0:
        return -1_000_000 + diff
    return 0


def evaluate(player, opp, empties, my_moves_bb=None):
    empty = FULL ^ (player | opp)

    if my_moves_bb is None:
        my_moves_bb = legal_moves(player, opp)
    opp_moves_bb = legal_moves(opp, player)

    my_moves = my_moves_bb.bit_count()
    opp_moves = opp_moves_bb.bit_count()
    mobility = norm(my_moves, opp_moves)

    potential = norm((neighbors(opp) & empty).bit_count(), (neighbors(player) & empty).bit_count())

    adj_empty = neighbors(empty)
    frontier = norm((opp & adj_empty).bit_count(), (player & adj_empty).bit_count())

    corner_diff = (player & CORNERS).bit_count() - (opp & CORNERS).bit_count()
    corner_access = (my_moves_bb & CORNERS).bit_count() - (opp_moves_bb & CORNERS).bit_count()

    stable = stable_edge_count(player) - stable_edge_count(opp)
    pos = positional_score(player) - positional_score(opp)
    close = corner_closeness(player, opp)
    disc = norm(player.bit_count(), opp.bit_count())
    parity = 1 if (empties & 1) else -1

    if empties > 48:
        return (
            14 * mobility +
            10 * potential +
            4 * frontier +
            2 * pos +
            1600 * corner_diff +
            900 * corner_access +
            120 * close +
            80 * stable
        )
    if empties > 24:
        return (
            12 * mobility +
            8 * potential +
            6 * frontier +
            2 * pos +
            1800 * corner_diff +
            1000 * corner_access +
            120 * close +
            100 * stable +
            5 * disc
        )
    if empties > 10:
        return (
            10 * mobility +
            4 * potential +
            4 * frontier +
            2 * pos +
            2000 * corner_diff +
            1200 * corner_access +
            100 * close +
            120 * stable +
            20 * disc +
            20 * parity
        )
    return (
        4 * mobility +
        2 * pos +
        2200 * corner_diff +
        800 * corner_access +
        80 * close +
        160 * stable +
        50 * disc +
        30 * parity
    )


def first_ordered_move(moves):
    best_move = 0
    best_score = -INF
    mm = moves
    while mm:
        m = mm & -mm
        mm -= m
        idx = m.bit_length() - 1
        score = ORDER_WEIGHTS[idx]
        if m & CORNERS:
            score += 100000
        if score > best_score:
            best_score = score
            best_move = m
    return best_move


def ordered_children(player, opp, moves, tt_move=0):
    items = []
    mm = moves
    while mm:
        m = mm & -mm
        mm -= m

        p2, o2, flipc = play(player, opp, m)
        opp_legal = legal_moves(o2, p2)

        idx = m.bit_length() - 1
        pr = ORDER_WEIGHTS[idx] + 4 * flipc - 14 * opp_legal.bit_count()

        if opp_legal & CORNERS:
            pr -= 5000 * (opp_legal & CORNERS).bit_count()
        if m & CORNERS:
            pr += 200000
        if m == tt_move:
            pr += 1000000

        items.append((pr, m, p2, o2))

    items.sort(key=lambda t: t[0], reverse=True)
    return items


def negamax(player, opp, depth, alpha, beta):
    global NODES, TT, DEADLINE

    NODES += 1
    if (NODES & 511) == 0 and perf_counter() > DEADLINE:
        raise Timeout

    key = (player, opp)
    orig_alpha = alpha
    orig_beta = beta

    entry = TT.get(key)
    tt_move = 0
    if entry is not None:
        entry_depth, flag, score, best_move = entry
        tt_move = best_move
        if entry_depth >= depth:
            if flag == EXACT:
                return score
            if flag == LOWER:
                if score > alpha:
                    alpha = score
            else:
                if score < beta:
                    beta = score
            if alpha >= beta:
                return score

    moves = legal_moves(player, opp)

    if moves == 0:
        if legal_moves(opp, player) == 0:
            score = terminal_value(player, opp)
        else:
            score = -negamax(opp, player, depth, -beta, -alpha)

        old = TT.get(key)
        if old is None or depth >= old[0]:
            TT[key] = (depth, EXACT, score, 0)
        return score

    if depth == 0:
        score = evaluate(player, opp, 64 - (player | opp).bit_count(), moves)
        old = TT.get(key)
        if old is None or depth >= old[0]:
            TT[key] = (depth, EXACT, score, 0)
        return score

    children = ordered_children(player, opp, moves, tt_move)
    best_score = -INF
    best_move = children[0][1]

    for _, m, p2, o2 in children:
        score = -negamax(o2, p2, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    flag = EXACT
    if best_score <= orig_alpha:
        flag = UPPER
    elif best_score >= orig_beta:
        flag = LOWER

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, flag, best_score, best_move)

    return best_score


def root_search(player, opp, moves, max_depth, fallback):
    best_move = fallback
    best_score = -INF

    for depth in range(1, max_depth + 1):
        if perf_counter() > DEADLINE:
            break

        alpha = -INF
        beta = INF
        children = ordered_children(player, opp, moves, best_move)
        current_best_move = children[0][1]
        current_best_score = -INF

        for _, m, p2, o2 in children:
            if perf_counter() > DEADLINE:
                raise Timeout

            score = -negamax(o2, p2, depth - 1, -beta, -alpha)

            if score > current_best_score:
                current_best_score = score
                current_best_move = m
            if score > alpha:
                alpha = score

        best_move = current_best_move
        best_score = current_best_score
        TT[(player, opp)] = (depth, EXACT, best_score, best_move)

        if abs(best_score) >= 1_000_000:
            break

    return best_move


def choose_depth(player, opp, moves):
    empties = 64 - (player | opp).bit_count()
    mobility = moves.bit_count()

    if empties <= 12:
        d = empties
    elif empties <= 18:
        d = 10 if mobility <= 8 else 8
    elif empties <= 28:
        d = 7 if mobility <= 8 else 6
    elif empties <= 44:
        d = 6 if mobility <= 8 else 5
    else:
        d = 5 if mobility <= 6 else 4

    if d < 1:
        d = 1
    if d > empties:
        d = empties
    return d


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global DEADLINE, TT, NODES

    player = array_to_bb(np.asarray(you, dtype=np.uint8))
    opp = array_to_bb(np.asarray(opponent, dtype=np.uint8))

    moves = legal_moves(player, opp)
    if moves == 0:
        return "pass"

    if (moves & (moves - 1)) == 0:
        return move_to_str(moves)

    corner_moves = moves & CORNERS
    if corner_moves and (corner_moves & (corner_moves - 1)) == 0:
        return move_to_str(corner_moves)

    fallback = first_ordered_move(moves)

    TT = {}
    NODES = 0
    DEADLINE = perf_counter() + 0.93

    try:
        max_depth = choose_depth(player, opp, moves)
        move = root_search(player, opp, moves, max_depth, fallback)
        if move == 0 or not (move & moves):
            move = fallback
    except Exception:
        move = fallback

    return move_to_str(move)
