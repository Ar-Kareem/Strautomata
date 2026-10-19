
import time
import numpy as np

FULL = (1 << 64) - 1
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
INF = 10 ** 15
TERMINAL_SCALE = 100000

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
DELTA = []
SRC_MASK = []
OPP_DIR = [0] * 8
for i, (dr, dc) in enumerate(DIRS):
    d = dr * 8 + dc
    mask = 0
    for r in range(8):
        for c in range(8):
            rr = r + dr
            cc = c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                mask |= 1 << (r * 8 + c)
    DELTA.append(d)
    SRC_MASK.append(mask)
    for j, (dr2, dc2) in enumerate(DIRS):
        if dr2 == -dr and dc2 == -dc:
            OPP_DIR[i] = j

try:
    (1).bit_count()
    def popcnt(x):
        return x.bit_count()
except AttributeError:
    def popcnt(x):
        return bin(x).count("1")

POS = [0] * 64
for r in range(8):
    for c in range(8):
        idx = r * 8 + c
        if r in (0, 7) and c in (0, 7):
            v = 0
        elif r in (0, 7) or c in (0, 7):
            v = 12
        elif r in (1, 6) or c in (1, 6):
            v = -6
        else:
            v = 1
        POS[idx] = v

# corner_bit, ortho_adjacent_C_squares, diagonal_X_square, edge_line_1, edge_line_2
CORNER_DATA = [
    (1 << 0,  (1 << 1) | (1 << 8),   (1 << 9),  (0, 1, 2, 3, 4, 5, 6, 7),      (0, 8, 16, 24, 32, 40, 48, 56)),
    (1 << 7,  (1 << 6) | (1 << 15),  (1 << 14), (7, 6, 5, 4, 3, 2, 1, 0),      (7, 15, 23, 31, 39, 47, 55, 63)),
    (1 << 56, (1 << 57) | (1 << 48), (1 << 49), (56, 57, 58, 59, 60, 61, 62, 63), (56, 48, 40, 32, 24, 16, 8, 0)),
    (1 << 63, (1 << 62) | (1 << 55), (1 << 54), (63, 62, 61, 60, 59, 58, 57, 56), (63, 55, 47, 39, 31, 23, 15, 7)),
]

class SearchTimeout(Exception):
    pass

def shift_dir(b, i):
    d = DELTA[i]
    if d > 0:
        return ((b & SRC_MASK[i]) << d) & FULL
    return (b & SRC_MASK[i]) >> (-d)

def neighbor_mask(b):
    x = 0
    for i in range(8):
        x |= shift_dir(b, i)
    return x & FULL

def legal_bits(P, O):
    empty = ~(P | O) & FULL
    moves = 0
    for i in range(8):
        oi = OPP_DIR[i]
        w = shift_dir(P, oi) & O
        while w:
            moves |= shift_dir(w, oi) & empty
            w = shift_dir(w, oi) & O
    return moves

def apply_move(P, O, mbit):
    flips = 0
    for i in range(8):
        x = shift_dir(mbit, i)
        run = 0
        while x & O:
            run |= x
            x = shift_dir(x, i)
        if run and (x & P):
            flips |= run
    return (P | mbit | flips), (O ^ flips)

def bits_to_list(bits):
    out = []
    while bits:
        lb = bits & -bits
        out.append(lb)
        bits ^= lb
    return out

def move_to_str(mbit):
    idx = mbit.bit_length() - 1
    return chr(97 + (idx & 7)) + str((idx >> 3) + 1)

def evaluate(P, O, movesP_bits=None):
    empty = ~(P | O) & FULL
    empties = popcnt(empty)
    if movesP_bits is None:
        movesP_bits = legal_bits(P, O)
    my_mob = popcnt(movesP_bits)
    opp_mob = popcnt(legal_bits(O, P))
    mobility = my_mob - opp_mob

    pos = 0
    x = P
    while x:
        lb = x & -x
        x ^= lb
        pos += POS[lb.bit_length() - 1]
    x = O
    while x:
        lb = x & -x
        x ^= lb
        pos -= POS[lb.bit_length() - 1]

    n_opp = neighbor_mask(O) & empty
    n_me = neighbor_mask(P) & empty
    potential = popcnt(n_opp) - popcnt(n_me)

    corner_diff = popcnt(P & CORNERS) - popcnt(O & CORNERS)
    danger = 0
    stable_diff = 0
    occupied = P | O
    for cbit, ortho, diag, line1, line2 in CORNER_DATA:
        if occupied & cbit:
            if P & cbit:
                b = P
                sign = 1
            else:
                b = O
                sign = -1
            stable_diff += sign
            for line in (line1, line2):
                for idx in line[1:]:
                    if (b >> idx) & 1:
                        stable_diff += sign
                    else:
                        break
        else:
            danger += 2 * (popcnt(P & ortho) - popcnt(O & ortho))
            danger += 3 * (popcnt(P & diag) - popcnt(O & diag))

    coin = popcnt(P) - popcnt(O)
    if empties > 40:
        return (4 * pos + 75 * mobility + 8 * potential + 1300 * corner_diff
                - 70 * danger + 25 * stable_diff)
    if empties > 18:
        return (coin + 3 * pos + 38 * mobility + 4 * potential + 1300 * corner_diff
                - 60 * danger + 22 * stable_diff)
    return (35 * coin + pos + 12 * mobility + 1300 * corner_diff
            - 35 * danger + 18 * stable_diff)

def move_order_score(mbit, P, O):
    idx = mbit.bit_length() - 1
    score = POS[idx] * 8
    if mbit & CORNERS:
        return 1000000 + score
    r = idx >> 3
    c = idx & 7
    if r == 0 or r == 7 or c == 0 or c == 7:
        score += 80
    occupied = P | O
    for cbit, ortho, diag, line1, line2 in CORNER_DATA:
        adj = ortho | diag
        if mbit & adj:
            if not (occupied & cbit):
                score -= 9000 if (mbit & diag) else 6000
            elif P & cbit:
                score += 300
            else:
                score -= 100
    return score

def _board_to_bits(a):
    flat = np.asarray(a, dtype=np.uint8).ravel()
    return int.from_bytes(np.packbits(flat, bitorder="little").tobytes(), "little")

def policy(you, opponent):
    P = _board_to_bits(you)
    O = _board_to_bits(opponent)

    moves_bits = legal_bits(P, O)
    if moves_bits == 0:
        return "pass"

    moves = bits_to_list(moves_bits)
    if len(moves) == 1:
        return move_to_str(moves[0])

    moves.sort(key=lambda m: move_order_score(m, P, O), reverse=True)
    best_move = moves[0]

    tt = {}
    nodes = 0
    start = time.perf_counter()
    deadline = start + 0.92
    empties = popcnt(~(P | O) & FULL)
    max_depth = empties + 8 if empties <= 18 else 14

    def search(P, O, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 511) == 0 and time.perf_counter() > deadline:
            raise SearchTimeout()

        key = (P, O)
        entry = tt.get(key)
        tt_move = 0
        if entry is not None:
            ed, ev, ef, eb = entry
            tt_move = eb
            if ed >= depth:
                if ef == 0:
                    return ev
                if ef == 1:
                    if ev > alpha:
                        alpha = ev
                else:
                    if ev < beta:
                        beta = ev
                if alpha >= beta:
                    return ev

        alpha_orig = alpha
        beta_orig = beta

        mb = legal_bits(P, O)
        if mb == 0:
            if legal_bits(O, P) == 0:
                return (popcnt(P) - popcnt(O)) * TERMINAL_SCALE
            if depth <= 0:
                return evaluate(P, O, 0)
            return -search(O, P, depth - 1, -beta, -alpha)

        if depth <= 0:
            return evaluate(P, O, mb)

        best = -INF
        bestmove = 0
        ms = bits_to_list(mb)
        ms.sort(key=lambda m: (m == tt_move, move_order_score(m, P, O)), reverse=True)

        for m in ms:
            P2, O2 = apply_move(P, O, m)
            val = -search(O2, P2, depth - 1, -beta, -alpha)
            if val > best:
                best = val
                bestmove = m
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break

        if best <= alpha_orig:
            flag = 2
        elif best >= beta_orig:
            flag = 1
        else:
            flag = 0
        old = tt.get(key)
        if old is None or old[0] <= depth:
            tt[key] = (depth, best, flag, bestmove)
        return best

    for depth in range(1, max_depth + 1):
        try:
            val = search(P, O, depth, -INF, INF)
        except SearchTimeout:
            break
        entry = tt.get((P, O))
        if entry is not None and entry[3] and (entry[3] & moves_bits):
            best_move = entry[3]
        if abs(val) >= TERMINAL_SCALE:
            break

    return move_to_str(best_move)
