
import time
import numpy as np

FULL = (1 << 64) - 1

FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

A1 = 1 << 0
H1 = 1 << 7
A8 = 1 << 56
H8 = 1 << 63
CORNERS = A1 | H1 | A8 | H8

A1_X = 1 << 9
H1_X = 1 << 14
A8_X = 1 << 49
H8_X = 1 << 54

A1_C = (1 << 1) | (1 << 8)
H1_C = (1 << 6) | (1 << 15)
A8_C = (1 << 48) | (1 << 57)
H8_C = (1 << 55) | (1 << 62)

INF = 10 ** 9
WIN_SCORE = 10 ** 6

EXACT = 0
LOWER = 1
UPPER = 2

popcount = int.bit_count

# Classic Othello positional weights
POSITION_WEIGHTS = (
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
)

ORDER_BASE = POSITION_WEIGHTS

IDX_TO_MOVE = tuple(chr(ord("a") + (i % 8)) + str(i // 8 + 1) for i in range(64))

# Row lookup tables for fast positional-score summation.
ROW_PSQ = []
for r in range(8):
    w = POSITION_WEIGHTS[r * 8:(r + 1) * 8]
    table = [0] * 256
    for byte in range(256):
        s = 0
        for c in range(8):
            if byte & (1 << c):
                s += w[c]
        table[byte] = s
    ROW_PSQ.append(table)

TT = {}
DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


def psq_sum(bb: int) -> int:
    return (
        ROW_PSQ[0][bb & 0xFF] +
        ROW_PSQ[1][(bb >> 8) & 0xFF] +
        ROW_PSQ[2][(bb >> 16) & 0xFF] +
        ROW_PSQ[3][(bb >> 24) & 0xFF] +
        ROW_PSQ[4][(bb >> 32) & 0xFF] +
        ROW_PSQ[5][(bb >> 40) & 0xFF] +
        ROW_PSQ[6][(bb >> 48) & 0xFF] +
        ROW_PSQ[7][(bb >> 56) & 0xFF]
    )


def neighbors(bb: int) -> int:
    return (
        ((bb & NOT_H) << 1) |
        ((bb & NOT_A) >> 1) |
        ((bb << 8) & FULL) |
        (bb >> 8) |
        (((bb & NOT_H) << 9) & FULL) |
        (((bb & NOT_A) << 7) & FULL) |
        ((bb & NOT_H) >> 7) |
        ((bb & NOT_A) >> 9)
    )


def legal_moves_bb(own: int, opp: int) -> int:
    empty = FULL ^ (own | opp)
    moves = 0

    # East
    t = ((own & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    moves |= ((t & NOT_H) << 1) & empty

    # West
    t = ((own & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    moves |= ((t & NOT_A) >> 1) & empty

    # South
    t = ((own << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    moves |= ((t << 8) & FULL) & empty

    # North
    t = (own >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    moves |= (t >> 8) & empty

    # South-East
    t = (((own & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    moves |= (((t & NOT_H) << 9) & FULL) & empty

    # South-West
    t = (((own & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    moves |= (((t & NOT_A) << 7) & FULL) & empty

    # North-East
    t = ((own & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    moves |= ((t & NOT_H) >> 7) & empty

    # North-West
    t = ((own & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    moves |= ((t & NOT_A) >> 9) & empty

    return moves


def apply_move(own: int, opp: int, move_idx: int):
    move = 1 << move_idx
    flips = 0

    # East
    x = (move & NOT_H) << 1
    cap = 0
    while x & opp:
        cap |= x
        x = (x & NOT_H) << 1
    if x & own:
        flips |= cap

    # West
    x = (move & NOT_A) >> 1
    cap = 0
    while x & opp:
        cap |= x
        x = (x & NOT_A) >> 1
    if x & own:
        flips |= cap

    # South
    x = (move << 8) & FULL
    cap = 0
    while x & opp:
        cap |= x
        x = (x << 8) & FULL
    if x & own:
        flips |= cap

    # North
    x = move >> 8
    cap = 0
    while x & opp:
        cap |= x
        x >>= 8
    if x & own:
        flips |= cap

    # South-East
    x = ((move & NOT_H) << 9) & FULL
    cap = 0
    while x & opp:
        cap |= x
        x = ((x & NOT_H) << 9) & FULL
    if x & own:
        flips |= cap

    # South-West
    x = ((move & NOT_A) << 7) & FULL
    cap = 0
    while x & opp:
        cap |= x
        x = ((x & NOT_A) << 7) & FULL
    if x & own:
        flips |= cap

    # North-East
    x = (move & NOT_H) >> 7
    cap = 0
    while x & opp:
        cap |= x
        x = (x & NOT_H) >> 7
    if x & own:
        flips |= cap

    # North-West
    x = (move & NOT_A) >> 9
    cap = 0
    while x & opp:
        cap |= x
        x = (x & NOT_A) >> 9
    if x & own:
        flips |= cap

    own2 = own | move | flips
    opp2 = opp & ~flips
    return own2, opp2


def corner_adj_stats(own: int, opp: int, occ: int):
    x_adj = 0
    c_adj = 0

    if not (occ & A1):
        x_adj += popcount(own & A1_X) - popcount(opp & A1_X)
        c_adj += popcount(own & A1_C) - popcount(opp & A1_C)

    if not (occ & H1):
        x_adj += popcount(own & H1_X) - popcount(opp & H1_X)
        c_adj += popcount(own & H1_C) - popcount(opp & H1_C)

    if not (occ & A8):
        x_adj += popcount(own & A8_X) - popcount(opp & A8_X)
        c_adj += popcount(own & A8_C) - popcount(opp & A8_C)

    if not (occ & H8):
        x_adj += popcount(own & H8_X) - popcount(opp & H8_X)
        c_adj += popcount(own & H8_C) - popcount(opp & H8_C)

    return x_adj, c_adj


def evaluate(own: int, opp: int) -> int:
    occ = own | opp
    empties = 64 - popcount(occ)

    own_moves = legal_moves_bb(own, opp)
    opp_moves = legal_moves_bb(opp, own)
    mobility = popcount(own_moves) - popcount(opp_moves)

    corners = popcount(own & CORNERS) - popcount(opp & CORNERS)
    x_adj, c_adj = corner_adj_stats(own, opp, occ)

    empty = FULL ^ occ
    frontier_mask = neighbors(empty)
    frontier = popcount(own & frontier_mask) - popcount(opp & frontier_mask)

    psq = psq_sum(own) - psq_sum(opp)
    discs = popcount(own) - popcount(opp)

    if empties > 44:
        return (
            180 * corners
            - 100 * x_adj
            - 45 * c_adj
            + 14 * mobility
            - 8 * frontier
            + 2 * psq
        )
    elif empties > 20:
        return (
            220 * corners
            - 80 * x_adj
            - 35 * c_adj
            + 12 * mobility
            - 6 * frontier
            + 2 * psq
            + 2 * discs
        )
    else:
        parity = 1 if (empties & 1) else -1
        return (
            260 * corners
            - 50 * x_adj
            - 20 * c_adj
            + 8 * mobility
            - 4 * frontier
            + 2 * psq
            + 12 * discs
            + 6 * parity
        )


def terminal_score(own: int, opp: int) -> int:
    diff = popcount(own) - popcount(opp)
    if diff > 0:
        return WIN_SCORE + diff
    if diff < 0:
        return -WIN_SCORE + diff
    return 0


def move_order_score(idx: int, occ: int, tt_move: int) -> int:
    s = ORDER_BASE[idx]

    if idx == tt_move:
        s += 1_000_000

    # Strongly penalize moves next to empty corners.
    if not (occ & A1):
        if idx == 9:
            s -= 15000
        elif idx == 1 or idx == 8:
            s -= 5000

    if not (occ & H1):
        if idx == 14:
            s -= 15000
        elif idx == 6 or idx == 15:
            s -= 5000

    if not (occ & A8):
        if idx == 49:
            s -= 15000
        elif idx == 48 or idx == 57:
            s -= 5000

    if not (occ & H8):
        if idx == 54:
            s -= 15000
        elif idx == 55 or idx == 62:
            s -= 5000

    return s


def ordered_moves(moves_bb: int, occ: int, tt_move: int = -1):
    scored = []
    bb = moves_bb
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        scored.append((move_order_score(idx, occ, tt_move), idx))
        bb ^= lsb
    scored.sort(reverse=True)
    return [idx for _, idx in scored]


def check_timeout():
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout


def negamax(own: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    check_timeout()

    if depth == 0:
        return evaluate(own, opp)

    key = (own, opp)
    alpha_orig = alpha
    beta_orig = beta

    entry = TT.get(key)
    tt_move = -1
    if entry is not None:
        edepth, eflag, eval_, emove = entry
        tt_move = emove
        if edepth >= depth:
            if eflag == EXACT:
                return eval_
            if eflag == LOWER:
                if eval_ > alpha:
                    alpha = eval_
            else:
                if eval_ < beta:
                    beta = eval_
            if alpha >= beta:
                return eval_

    moves_bb = legal_moves_bb(own, opp)
    if not moves_bb:
        opp_moves = legal_moves_bb(opp, own)
        if not opp_moves:
            val = terminal_score(own, opp)
        else:
            val = -negamax(opp, own, depth, -beta, -alpha)
        old = TT.get(key)
        if old is None or depth >= old[0]:
            TT[key] = (depth, EXACT, val, -1)
        return val

    occ = own | opp
    best_val = -INF
    best_move = tt_move

    for m in ordered_moves(moves_bb, occ, tt_move):
        own2, opp2 = apply_move(own, opp, m)
        val = -negamax(opp2, own2, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = UPPER
    elif best_val >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, flag, best_val, best_move)

    return best_val


def root_search(own: int, opp: int, depth: int):
    key = (own, opp)
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else -1

    moves_bb = legal_moves_bb(own, opp)
    if not moves_bb:
        return terminal_score(own, opp), -1

    occ = own | opp
    moves = ordered_moves(moves_bb, occ, tt_move)

    best_move = moves[0]
    best_val = -INF
    alpha = -INF
    beta = INF

    for m in moves:
        if time.perf_counter() >= DEADLINE:
            raise SearchTimeout

        own2, opp2 = apply_move(own, opp, m)
        val = -negamax(opp2, own2, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if best_val > alpha:
            alpha = best_val

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, EXACT, best_val, best_move)

    return best_val, best_move


def arrays_to_bitboards(you: np.ndarray, opponent: np.ndarray):
    own = 0
    opp = 0

    for i in np.flatnonzero(you.ravel()):
        own |= 1 << int(i)
    for i in np.flatnonzero(opponent.ravel()):
        opp |= 1 << int(i)

    return own, opp


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global DEADLINE, NODES, TT

    if len(TT) > 300000:
        TT.clear()

    own, opp = arrays_to_bitboards(you, opponent)
    moves_bb = legal_moves_bb(own, opp)

    if not moves_bb:
        return "pass"

    # Only one legal move.
    if (moves_bb & (moves_bb - 1)) == 0:
        idx = moves_bb.bit_length() - 1
        return IDX_TO_MOVE[idx]

    empties = 64 - popcount(own | opp)

    # Conservative time budget to stay under the limit.
    if empties > 50:
        budget = 0.60
    elif empties > 40:
        budget = 0.75
    elif empties > 20:
        budget = 0.90
    else:
        budget = 0.97

    DEADLINE = time.perf_counter() + budget
    NODES = 0

    entry = TT.get((own, opp))
    tt_move = entry[3] if entry is not None else -1
    initial_moves = ordered_moves(moves_bb, own | opp, tt_move)
    best_move = initial_moves[0]

    move_count = popcount(moves_bb)
    if empties <= 10:
        start_depth = 4
    elif move_count <= 6:
        start_depth = 3
    else:
        start_depth = 2

    max_depth = empties if empties <= 14 else 64
    if start_depth > max_depth:
        start_depth = max_depth
    if start_depth < 1:
        start_depth = 1

    try:
        for depth in range(start_depth, max_depth + 1):
            _, move = root_search(own, opp, depth)
            if move != -1:
                best_move = move
            if depth >= empties:
                break
    except SearchTimeout:
        pass

    # Final safety check: always return a legal move.
    if not (moves_bb & (1 << best_move)):
        lsb = moves_bb & -moves_bb
        best_move = lsb.bit_length() - 1

    return IDX_TO_MOVE[best_move]
