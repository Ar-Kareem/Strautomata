
import time
import numpy as np

FULL = (1 << 64) - 1
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F

A1 = 1 << 0
H1 = 1 << 7
A8 = 1 << 56
H8 = 1 << 63

B1 = 1 << 1
G1 = 1 << 6
A2 = 1 << 8
B2 = 1 << 9
G2 = 1 << 14
H2 = 1 << 15

A7 = 1 << 48
B7 = 1 << 49
G7 = 1 << 54
H7 = 1 << 55
B8 = 1 << 57
G8 = 1 << 62

CORNERS = A1 | H1 | A8 | H8

INF = 10**18

WEIGHTS = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -60,  -5,  -5,  -5,  -5, -60, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -60,  -5,  -5,  -5,  -5, -60, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
]

IDX_TO_STR = [chr(ord("a") + (i % 8)) + str((i // 8) + 1) for i in range(64)]

TT = {}
DEADLINE = 0.0
NODE_COUNT = 0


class SearchTimeout(Exception):
    pass


def bitboard_from_array(arr: np.ndarray) -> int:
    b = 0
    flat = arr.ravel()
    for i in range(64):
        if int(flat[i]):
            b |= 1 << i
    return b


def bit_to_str(bit: int) -> str:
    return IDX_TO_STR[bit.bit_length() - 1]


def neighbors(x: int) -> int:
    return (
        ((x & NOT_H) << 1) |
        ((x & NOT_A) >> 1) |
        (((x << 8) & FULL)) |
        (x >> 8) |
        ((((x & NOT_H) << 9) & FULL)) |
        ((((x & NOT_A) << 7) & FULL)) |
        ((x & NOT_H) >> 7) |
        ((x & NOT_A) >> 9)
    ) & FULL


def legal_moves(player: int, opp: int) -> int:
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

    x = ((player << 8) & FULL) & opp
    x |= ((x << 8) & FULL) & opp
    x |= ((x << 8) & FULL) & opp
    x |= ((x << 8) & FULL) & opp
    x |= ((x << 8) & FULL) & opp
    x |= ((x << 8) & FULL) & opp
    moves |= ((x << 8) & FULL) & empty

    x = (player >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    moves |= (x >> 8) & empty

    x = (((player & NOT_H) << 9) & FULL) & opp
    x |= (((x & NOT_H) << 9) & FULL) & opp
    x |= (((x & NOT_H) << 9) & FULL) & opp
    x |= (((x & NOT_H) << 9) & FULL) & opp
    x |= (((x & NOT_H) << 9) & FULL) & opp
    x |= (((x & NOT_H) << 9) & FULL) & opp
    moves |= (((x & NOT_H) << 9) & FULL) & empty

    x = (((player & NOT_A) << 7) & FULL) & opp
    x |= (((x & NOT_A) << 7) & FULL) & opp
    x |= (((x & NOT_A) << 7) & FULL) & opp
    x |= (((x & NOT_A) << 7) & FULL) & opp
    x |= (((x & NOT_A) << 7) & FULL) & opp
    x |= (((x & NOT_A) << 7) & FULL) & opp
    moves |= (((x & NOT_A) << 7) & FULL) & empty

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

    return moves & FULL


def do_move(player: int, opp: int, move: int):
    flips = 0

    x = 0
    cur = (move & NOT_H) << 1
    while cur and (cur & opp):
        x |= cur
        cur = (cur & NOT_H) << 1
    if cur & player:
        flips |= x

    x = 0
    cur = (move & NOT_A) >> 1
    while cur and (cur & opp):
        x |= cur
        cur = (cur & NOT_A) >> 1
    if cur & player:
        flips |= x

    x = 0
    cur = (move << 8) & FULL
    while cur and (cur & opp):
        x |= cur
        cur = (cur << 8) & FULL
    if cur & player:
        flips |= x

    x = 0
    cur = move >> 8
    while cur and (cur & opp):
        x |= cur
        cur = cur >> 8
    if cur & player:
        flips |= x

    x = 0
    cur = ((move & NOT_H) << 9) & FULL
    while cur and (cur & opp):
        x |= cur
        cur = ((cur & NOT_H) << 9) & FULL
    if cur & player:
        flips |= x

    x = 0
    cur = ((move & NOT_A) << 7) & FULL
    while cur and (cur & opp):
        x |= cur
        cur = ((cur & NOT_A) << 7) & FULL
    if cur & player:
        flips |= x

    x = 0
    cur = (move & NOT_H) >> 7
    while cur and (cur & opp):
        x |= cur
        cur = (cur & NOT_H) >> 7
    if cur & player:
        flips |= x

    x = 0
    cur = (move & NOT_A) >> 9
    while cur and (cur & opp):
        x |= cur
        cur = (cur & NOT_A) >> 9
    if cur & player:
        flips |= x

    new_player = player | move | flips
    new_opp = opp & ~flips

    return new_opp, new_player


def weighted_sum(bb: int) -> int:
    s = 0
    while bb:
        bit = bb & -bb
        s += WEIGHTS[bit.bit_length() - 1]
        bb ^= bit
    return s


def edge_stability(player: int) -> int:
    s = 0

    if player & A1:
        b = B1
        while b and (player & b):
            s += 1
            b <<= 1
        b = A2
        while b and (player & b):
            s += 1
            b <<= 8

    if player & H1:
        b = G1
        while b and (player & b):
            s += 1
            b >>= 1
        b = H2
        while b and (player & b):
            s += 1
            b <<= 8

    if player & A8:
        b = B8
        while b and (player & b):
            s += 1
            b <<= 1
        b = A7
        while b and (player & b):
            s += 1
            b >>= 8

    if player & H8:
        b = G8
        while b and (player & b):
            s += 1
            b >>= 1
        b = H7
        while b and (player & b):
            s += 1
            b >>= 8

    return s


def corner_risk(player: int, opp: int) -> int:
    occ = player | opp
    score = 0

    if not (occ & A1):
        self_bad = ((player & B2) != 0) + ((player & A2) != 0) + ((player & B1) != 0)
        opp_bad = ((opp & B2) != 0) + ((opp & A2) != 0) + ((opp & B1) != 0)
        score += opp_bad - self_bad

    if not (occ & H1):
        self_bad = ((player & G2) != 0) + ((player & H2) != 0) + ((player & G1) != 0)
        opp_bad = ((opp & G2) != 0) + ((opp & H2) != 0) + ((opp & G1) != 0)
        score += opp_bad - self_bad

    if not (occ & A8):
        self_bad = ((player & B7) != 0) + ((player & A7) != 0) + ((player & B8) != 0)
        opp_bad = ((opp & B7) != 0) + ((opp & A7) != 0) + ((opp & B8) != 0)
        score += opp_bad - self_bad

    if not (occ & H8):
        self_bad = ((player & G7) != 0) + ((player & H7) != 0) + ((player & G8) != 0)
        opp_bad = ((opp & G7) != 0) + ((opp & H7) != 0) + ((opp & G8) != 0)
        score += opp_bad - self_bad

    return int(score)


def terminal_score(player: int, opp: int) -> int:
    return (player.bit_count() - opp.bit_count()) * 10000


def evaluate(player: int, opp: int) -> int:
    occupied = player | opp
    empty = FULL ^ occupied
    empties = 64 - occupied.bit_count()

    my_moves = legal_moves(player, opp).bit_count()
    opp_moves = legal_moves(opp, player).bit_count()
    mobility = my_moves - opp_moves

    corners = (player & CORNERS).bit_count() - (opp & CORNERS).bit_count()
    stable = edge_stability(player) - edge_stability(opp)
    risk = corner_risk(player, opp)
    disc = player.bit_count() - opp.bit_count()
    pos = weighted_sum(player) - weighted_sum(opp)

    potential = (neighbors(opp) & empty).bit_count() - (neighbors(player) & empty).bit_count()
    frontier = (neighbors(empty) & player).bit_count() - (neighbors(empty) & opp).bit_count()

    if empties > 40:
        return (
            2 * pos +
            14 * mobility +
            5 * potential +
            70 * corners +
            18 * risk +
            10 * stable -
            8 * frontier -
            1 * disc
        )
    elif empties > 18:
        return (
            2 * pos +
            12 * mobility +
            3 * potential +
            85 * corners +
            14 * risk +
            12 * stable -
            6 * frontier +
            2 * disc
        )
    else:
        return (
            1 * pos +
            8 * mobility +
            2 * potential +
            100 * corners +
            8 * risk +
            14 * stable -
            3 * frontier +
            12 * disc
        )


def move_order_score(move: int, player: int, opp: int, tt_move: int, depth: int) -> int:
    occ = player | opp
    idx = move.bit_length() - 1
    score = WEIGHTS[idx]

    if move & CORNERS:
        score += 100000

    if move == B2 and not (occ & A1):
        score -= 50000
    elif move == G2 and not (occ & H1):
        score -= 50000
    elif move == B7 and not (occ & A8):
        score -= 50000
    elif move == G7 and not (occ & H8):
        score -= 50000

    if move == A2 and not (occ & A1):
        score -= 18000
    elif move == B1 and not (occ & A1):
        score -= 18000
    elif move == H2 and not (occ & H1):
        score -= 18000
    elif move == G1 and not (occ & H1):
        score -= 18000
    elif move == A7 and not (occ & A8):
        score -= 18000
    elif move == B8 and not (occ & A8):
        score -= 18000
    elif move == H7 and not (occ & H8):
        score -= 18000
    elif move == G8 and not (occ & H8):
        score -= 18000

    if move == tt_move:
        score += 200000

    if depth >= 4:
        child_player, child_opp = do_move(player, opp, move)
        score -= 12 * legal_moves(child_player, child_opp).bit_count()

    return score


def order_moves(moves: int, player: int, opp: int, tt_move: int = 0, depth: int = 0):
    lst = []
    bb = moves
    while bb:
        move = bb & -bb
        bb ^= move
        lst.append((move_order_score(move, player, opp, tt_move, depth), move))
    lst.sort(reverse=True)
    return [m for _, m in lst]


def negamax(player: int, opp: int, depth: int, alpha: int, beta: int, passed: bool) -> int:
    global NODE_COUNT, TT, DEADLINE

    NODE_COUNT += 1
    if (NODE_COUNT & 511) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    alpha_in = alpha
    beta_in = beta
    key = (player, opp, passed)
    tt_move = 0

    entry = TT.get(key)
    if entry is not None:
        e_depth, e_val, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            elif e_flag == 1:
                if e_val > alpha:
                    alpha = e_val
            else:
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    moves = legal_moves(player, opp)

    if moves == 0:
        opp_moves = legal_moves(opp, player)
        if opp_moves == 0:
            val = terminal_score(player, opp)
            TT[key] = (depth, val, 0, 0)
            return val
        val = -negamax(opp, player, depth, -beta, -alpha, True)
        TT[key] = (depth, val, 0, 0)
        return val

    if depth == 0:
        val = evaluate(player, opp)
        TT[key] = (depth, val, 0, 0)
        return val

    best = -INF
    best_move = 0

    for move in order_moves(moves, player, opp, tt_move, depth):
        child_player, child_opp = do_move(player, opp, move)
        val = -negamax(child_player, child_opp, depth - 1, -beta, -alpha, False)

        if val > best:
            best = val
            best_move = move
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha_in:
        flag = 2  # upper bound
    elif best >= beta_in:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    TT[key] = (depth, best, flag, best_move)
    return best


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global TT, DEADLINE, NODE_COUNT

    player = bitboard_from_array(you)
    opp = bitboard_from_array(opponent)

    moves = legal_moves(player, opp)
    if moves == 0:
        return "pass"

    if (moves & (moves - 1)) == 0:
        return bit_to_str(moves)

    TT = {}
    NODE_COUNT = 0
    DEADLINE = time.perf_counter() + 0.93

    ordered = order_moves(moves, player, opp, 0, 4)
    best_move = ordered[0]
    best_score = -INF

    empties = 64 - (player | opp).bit_count()
    if empties <= 10:
        max_depth = empties + 2
    elif empties <= 16:
        max_depth = 12
    elif empties <= 24:
        max_depth = 8
    else:
        max_depth = 6

    try:
        for depth in range(2, max_depth + 1):
            alpha = -INF
            beta = INF
            current_best = best_move
            current_score = -INF

            root_moves = [best_move] + [m for m in order_moves(moves, player, opp, best_move, depth) if m != best_move]

            for move in root_moves:
                child_player, child_opp = do_move(player, opp, move)
                val = -negamax(child_player, child_opp, depth - 1, -beta, -alpha, False)

                if val > current_score:
                    current_score = val
                    current_best = move
                if val > alpha:
                    alpha = val

            best_move = current_best
            best_score = current_score

            if time.perf_counter() >= DEADLINE:
                break

            if abs(best_score) >= 300000 and depth >= empties:
                break

    except SearchTimeout:
        pass

    legal = legal_moves(player, opp)
    if best_move & legal:
        return bit_to_str(best_move)

    fallback = legal & -legal
    return bit_to_str(fallback)
