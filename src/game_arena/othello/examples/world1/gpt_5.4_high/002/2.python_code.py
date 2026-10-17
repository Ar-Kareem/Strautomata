
import time
import numpy as np

FULL = (1 << 64) - 1
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F

A1 = 1 << 0
H1 = 1 << 7
A8 = 1 << 56
H8 = 1 << 63

CORNERS = A1 | H1 | A8 | H8
EDGE_MASK = 0xFF818181818181FF
NONCORNER_EDGE = EDGE_MASK & ~CORNERS

X_TO_CORNER = {
    1 << 9: A1,    # b2
    1 << 14: H1,   # g2
    1 << 49: A8,   # b7
    1 << 54: H8,   # g7
}

C_TO_CORNER = {
    1 << 1: A1,    # b1
    1 << 8: A1,    # a2
    1 << 6: H1,    # g1
    1 << 15: H1,   # h2
    1 << 48: A8,   # a7
    1 << 57: A8,   # b8
    1 << 55: H8,   # h7
    1 << 62: H8,   # g8
}

CORNER_DATA = [
    (A1, 1 << 9, (1 << 1) | (1 << 8)),
    (H1, 1 << 14, (1 << 6) | (1 << 15)),
    (A8, 1 << 49, (1 << 48) | (1 << 57)),
    (H8, 1 << 54, (1 << 55) | (1 << 62)),
]

MOVE_STR = [chr(ord("a") + c) + str(r + 1) for r in range(8) for c in range(8)]

PSQ = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
]

EXACT, LOWER, UPPER = 0, 1, 2
INF = 10**18

TT = {}
DEADLINE = 0.0
NODE_COUNT = 0


class SearchTimeout(Exception):
    pass


def shift_e(x: int) -> int:
    return ((x & NOT_H) << 1) & FULL


def shift_w(x: int) -> int:
    return (x & NOT_A) >> 1


def shift_n(x: int) -> int:
    return (x << 8) & FULL


def shift_s(x: int) -> int:
    return x >> 8


def shift_ne(x: int) -> int:
    return ((x & NOT_H) << 9) & FULL


def shift_nw(x: int) -> int:
    return ((x & NOT_A) << 7) & FULL


def shift_se(x: int) -> int:
    return (x & NOT_H) >> 7


def shift_sw(x: int) -> int:
    return (x & NOT_A) >> 9


def adjacency(x: int) -> int:
    return (
        shift_e(x) | shift_w(x) | shift_n(x) | shift_s(x) |
        shift_ne(x) | shift_nw(x) | shift_se(x) | shift_sw(x)
    )


def legal_moves(P: int, O: int) -> int:
    empty = FULL ^ (P | O)
    moves = 0

    x = shift_e(P) & O
    x |= shift_e(x) & O
    x |= shift_e(x) & O
    x |= shift_e(x) & O
    x |= shift_e(x) & O
    x |= shift_e(x) & O
    moves |= shift_e(x) & empty

    x = shift_w(P) & O
    x |= shift_w(x) & O
    x |= shift_w(x) & O
    x |= shift_w(x) & O
    x |= shift_w(x) & O
    x |= shift_w(x) & O
    moves |= shift_w(x) & empty

    x = shift_n(P) & O
    x |= shift_n(x) & O
    x |= shift_n(x) & O
    x |= shift_n(x) & O
    x |= shift_n(x) & O
    x |= shift_n(x) & O
    moves |= shift_n(x) & empty

    x = shift_s(P) & O
    x |= shift_s(x) & O
    x |= shift_s(x) & O
    x |= shift_s(x) & O
    x |= shift_s(x) & O
    x |= shift_s(x) & O
    moves |= shift_s(x) & empty

    x = shift_ne(P) & O
    x |= shift_ne(x) & O
    x |= shift_ne(x) & O
    x |= shift_ne(x) & O
    x |= shift_ne(x) & O
    x |= shift_ne(x) & O
    moves |= shift_ne(x) & empty

    x = shift_nw(P) & O
    x |= shift_nw(x) & O
    x |= shift_nw(x) & O
    x |= shift_nw(x) & O
    x |= shift_nw(x) & O
    x |= shift_nw(x) & O
    moves |= shift_nw(x) & empty

    x = shift_se(P) & O
    x |= shift_se(x) & O
    x |= shift_se(x) & O
    x |= shift_se(x) & O
    x |= shift_se(x) & O
    x |= shift_se(x) & O
    moves |= shift_se(x) & empty

    x = shift_sw(P) & O
    x |= shift_sw(x) & O
    x |= shift_sw(x) & O
    x |= shift_sw(x) & O
    x |= shift_sw(x) & O
    x |= shift_sw(x) & O
    moves |= shift_sw(x) & empty

    return moves


def apply_move(P: int, O: int, m: int):
    flips = 0

    x = shift_e(m)
    cap = 0
    while x and (x & O):
        cap |= x
        x = shift_e(x)
    if x & P:
        flips |= cap

    x = shift_w(m)
    cap = 0
    while x and (x & O):
        cap |= x
        x = shift_w(x)
    if x & P:
        flips |= cap

    x = shift_n(m)
    cap = 0
    while x and (x & O):
        cap |= x
        x = shift_n(x)
    if x & P:
        flips |= cap

    x = shift_s(m)
    cap = 0
    while x and (x & O):
        cap |= x
        x = shift_s(x)
    if x & P:
        flips |= cap

    x = shift_ne(m)
    cap = 0
    while x and (x & O):
        cap |= x
        x = shift_ne(x)
    if x & P:
        flips |= cap

    x = shift_nw(m)
    cap = 0
    while x and (x & O):
        cap |= x
        x = shift_nw(x)
    if x & P:
        flips |= cap

    x = shift_se(m)
    cap = 0
    while x and (x & O):
        cap |= x
        x = shift_se(x)
    if x & P:
        flips |= cap

    x = shift_sw(m)
    cap = 0
    while x and (x & O):
        cap |= x
        x = shift_sw(x)
    if x & P:
        flips |= cap

    return P | m | flips, O & (FULL ^ flips)


def terminal_score(P: int, O: int) -> int:
    return (P.bit_count() - O.bit_count()) * 10000


def piece_square_score(B: int) -> int:
    s = 0
    while B:
        b = B & -B
        s += PSQ[b.bit_length() - 1]
        B ^= b
    return s


def corner_closeness(P: int, O: int, occupied: int) -> int:
    score = 0
    for corner, xmask, cmask in CORNER_DATA:
        if not (occupied & corner):
            if P & xmask:
                score -= 35
            if O & xmask:
                score += 35
            score += 12 * ((O & cmask).bit_count() - (P & cmask).bit_count())
    return score


def anchored_edge_diff(P: int, O: int) -> int:
    s = 0

    # a1
    if P & A1:
        i = 1
        while i < 8 and (P & (1 << i)):
            s += 1
            i += 1
        i = 1
        while i < 8 and (P & (1 << (8 * i))):
            s += 1
            i += 1
    elif O & A1:
        i = 1
        while i < 8 and (O & (1 << i)):
            s -= 1
            i += 1
        i = 1
        while i < 8 and (O & (1 << (8 * i))):
            s -= 1
            i += 1

    # h1
    if P & H1:
        i = 1
        while i < 8 and (P & (1 << (7 - i))):
            s += 1
            i += 1
        i = 1
        while i < 8 and (P & (1 << (7 + 8 * i))):
            s += 1
            i += 1
    elif O & H1:
        i = 1
        while i < 8 and (O & (1 << (7 - i))):
            s -= 1
            i += 1
        i = 1
        while i < 8 and (O & (1 << (7 + 8 * i))):
            s -= 1
            i += 1

    # a8
    if P & A8:
        i = 1
        while i < 8 and (P & (1 << (56 + i))):
            s += 1
            i += 1
        i = 1
        while i < 8 and (P & (1 << (56 - 8 * i))):
            s += 1
            i += 1
    elif O & A8:
        i = 1
        while i < 8 and (O & (1 << (56 + i))):
            s -= 1
            i += 1
        i = 1
        while i < 8 and (O & (1 << (56 - 8 * i))):
            s -= 1
            i += 1

    # h8
    if P & H8:
        i = 1
        while i < 8 and (P & (1 << (63 - i))):
            s += 1
            i += 1
        i = 1
        while i < 8 and (P & (1 << (63 - 8 * i))):
            s += 1
            i += 1
    elif O & H8:
        i = 1
        while i < 8 and (O & (1 << (63 - i))):
            s -= 1
            i += 1
        i = 1
        while i < 8 and (O & (1 << (63 - 8 * i))):
            s -= 1
            i += 1

    return s


def evaluate(P: int, O: int) -> int:
    occupied = P | O
    if occupied == FULL:
        return terminal_score(P, O)

    my_moves = legal_moves(P, O)
    opp_moves = legal_moves(O, P)

    if not my_moves and not opp_moves:
        return terminal_score(P, O)

    empty = FULL ^ occupied
    empties = 64 - occupied.bit_count()

    pc = P.bit_count()
    oc = O.bit_count()

    mobility_diff = my_moves.bit_count() - opp_moves.bit_count()
    potential_diff = (empty & adjacency(O)).bit_count() - (empty & adjacency(P)).bit_count()
    frontier_diff = (O & adjacency(empty)).bit_count() - (P & adjacency(empty)).bit_count()
    corner_diff = (P & CORNERS).bit_count() - (O & CORNERS).bit_count()
    pos = piece_square_score(P) - piece_square_score(O)
    close = corner_closeness(P, O, occupied)
    edge = anchored_edge_diff(P, O)
    disc_diff = pc - oc

    if empties > 44:
        return (
            pos
            + 14 * mobility_diff
            + 3 * potential_diff
            + 8 * frontier_diff
            + 110 * corner_diff
            + 6 * edge
            + close
        )
    elif empties > 20:
        return (
            pos
            + 11 * mobility_diff
            + 2 * potential_diff
            + 5 * frontier_diff
            + 130 * corner_diff
            + 7 * edge
            + close
            + 2 * disc_diff
        )
    else:
        parity = 4 if (empties & 1) else -4
        return (
            pos
            + 8 * mobility_diff
            + potential_diff
            + 3 * frontier_diff
            + 150 * corner_diff
            + 8 * edge
            + close
            + 22 * disc_diff
            + parity
        )


def order_moves(P: int, O: int, moves: int, tt_move: int = 0, empties: int = 64):
    occupied = P | O
    late = empties <= 12
    scored = []

    while moves:
        m = moves & -moves
        moves ^= m

        idx = m.bit_length() - 1
        s = PSQ[idx] * 10

        if m == tt_move:
            s += 1_000_000

        if m & CORNERS:
            s += 200_000
        elif m & NONCORNER_EDGE:
            s += 4_000

        c = X_TO_CORNER.get(m, 0)
        if c and not (occupied & c):
            s -= 60_000

        c = C_TO_CORNER.get(m, 0)
        if c and not (occupied & c):
            s -= 25_000

        if late:
            nP, nO = apply_move(P, O, m)
            s -= 200 * legal_moves(nO, nP).bit_count()
            s += 20 * (nP.bit_count() - P.bit_count())

        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def search(P: int, O: int, depth: int, alpha: int, beta: int, passed: bool) -> int:
    global NODE_COUNT, DEADLINE, TT

    NODE_COUNT += 1
    if (NODE_COUNT & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    occupied = P | O
    if occupied == FULL:
        return terminal_score(P, O)

    moves = legal_moves(P, O)
    if not moves:
        if passed:
            return terminal_score(P, O)
        return -search(O, P, depth, -beta, -alpha, True)

    if depth <= 0:
        return evaluate(P, O)

    key = (P, O, passed)
    tt = TT.get(key)
    if tt is not None and tt[0] >= depth:
        _, flag, val, _ = tt
        if flag == EXACT:
            return val
        if flag == LOWER:
            alpha = max(alpha, val)
        elif flag == UPPER:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    alpha_orig = alpha
    best = -INF
    best_move = 0
    tt_move = tt[3] if tt is not None else 0
    empties = 64 - occupied.bit_count()

    for m in order_moves(P, O, moves, tt_move, empties):
        nP, nO = apply_move(P, O, m)
        val = -search(nO, nP, depth - 1, -beta, -alpha, False)

        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    flag = EXACT
    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta:
        flag = LOWER

    TT[key] = (depth, flag, best, best_move)
    return best


def search_root(P: int, O: int, depth: int):
    moves = legal_moves(P, O)
    if not moves:
        return terminal_score(P, O), 0

    key = (P, O, False)
    tt = TT.get(key)
    tt_move = tt[3] if tt is not None else 0

    occupied = P | O
    empties = 64 - occupied.bit_count()

    ordered = order_moves(P, O, moves, tt_move, empties)
    best = -INF
    best_move = ordered[0]
    alpha = -INF
    beta = INF

    for m in ordered:
        nP, nO = apply_move(P, O, m)
        val = -search(nO, nP, depth - 1, -beta, -alpha, False)

        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val

    TT[key] = (depth, EXACT, best, best_move)
    return best, best_move


def arrays_to_bitboards(you: np.ndarray, opponent: np.ndarray):
    P = 0
    O = 0
    for i in np.flatnonzero(you):
        P |= 1 << int(i)
    for i in np.flatnonzero(opponent):
        O |= 1 << int(i)
    return P, O


def depth_schedule(empties: int):
    if empties <= 12:
        ds = [d for d in (4, 6, 8, 10) if d < empties]
        ds.append(empties)
        return ds
    if empties <= 20:
        return [4, 5, 6, 7, 8]
    if empties <= 32:
        return [3, 4, 5, 6, 7]
    if empties <= 44:
        return [2, 3, 4, 5, 6]
    if empties <= 52:
        return [2, 3, 4, 5]
    return [2, 3, 4]


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global DEADLINE, NODE_COUNT, TT

    try:
        if len(TT) > 400000:
            TT.clear()

        DEADLINE = time.perf_counter() + 0.94
        NODE_COUNT = 0

        P, O = arrays_to_bitboards(you, opponent)
        moves = legal_moves(P, O)

        if not moves:
            return "pass"

        if moves & (moves - 1) == 0:
            return MOVE_STR[moves.bit_length() - 1]

        empties = 64 - (P | O).bit_count()
        ordered = order_moves(P, O, moves, 0, empties)

        # Safe fallback: best 1-ply evaluated move.
        best_move = ordered[0]
        best_val = -INF
        for m in ordered:
            if time.perf_counter() >= DEADLINE:
                break
            nP, nO = apply_move(P, O, m)
            val = -evaluate(nO, nP)
            if val > best_val:
                best_val = val
                best_move = m

        # Iterative deepening.
        for depth in depth_schedule(empties):
            if time.perf_counter() >= DEADLINE:
                break
            try:
                val, move = search_root(P, O, depth)
                if move:
                    best_val = val
                    best_move = move
            except SearchTimeout:
                break

        return MOVE_STR[best_move.bit_length() - 1]

    except Exception:
        # Final safety net: always return a legal move string.
        try:
            P, O = arrays_to_bitboards(you, opponent)
            moves = legal_moves(P, O)
            if not moves:
                return "pass"
            m = moves & -moves
            return MOVE_STR[m.bit_length() - 1]
        except Exception:
            return "pass"
