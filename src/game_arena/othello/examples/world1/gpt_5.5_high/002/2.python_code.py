
import time
import numpy as np

ALL = (1 << 64) - 1
NOT_A = 0xfefefefefefefefe
NOT_H = 0x7f7f7f7f7f7f7f7f

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

INF = 10 ** 9
TIME_LIMIT = 0.88

TT = {}
TT_LIMIT = 250000
END_TIME = 0.0
NODES = 0

FILES = "abcdefgh"

# Positional table: corners are excellent, X-squares dangerous, edges valuable.
SQ_WEIGHTS = (
    120, -25,  20,   5,   5,  20, -25, 120,
    -25, -50,  -5,  -5,  -5,  -5, -50, -25,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -25, -50,  -5,  -5,  -5,  -5, -50, -25,
    120, -25,  20,   5,   5,  20, -25, 120,
)

ORDER_WEIGHTS = (
    10000, -3000,  800, 200, 200,  800, -3000, 10000,
    -3000, -6000, -400,-300,-300, -400, -6000, -3000,
      800,  -400,  500, 100, 100,  500,  -400,   800,
      200,  -300,  100,  50,  50,  100,  -300,   200,
      200,  -300,  100,  50,  50,  100,  -300,   200,
      800,  -400,  500, 100, 100,  500,  -400,   800,
    -3000, -6000, -400,-300,-300, -400, -6000, -3000,
    10000, -3000,  800, 200, 200,  800, -3000, 10000,
)

ROW_TABLE = []
for r in range(8):
    row = []
    for b in range(256):
        s = 0
        for c in range(8):
            if b & (1 << c):
                s += SQ_WEIGHTS[r * 8 + c]
        row.append(s)
    ROW_TABLE.append(tuple(row))
ROW_TABLE = tuple(ROW_TABLE)


def arrays_to_bits(you, opponent):
    me = 0
    opp = 0
    for r in range(8):
        base = r * 8
        for c in range(8):
            bit = 1 << (base + c)
            if int(you[r][c]):
                me |= bit
            elif int(opponent[r][c]):
                opp |= bit
    return me, opp


def bit_to_str(move):
    i = move.bit_length() - 1
    return FILES[i & 7] + str((i >> 3) + 1)


def legal_moves(me, opp):
    empty = (~(me | opp)) & ALL
    moves = 0

    x = ((me << 1) & NOT_A) & opp
    x |= ((x << 1) & NOT_A) & opp
    x |= ((x << 1) & NOT_A) & opp
    x |= ((x << 1) & NOT_A) & opp
    x |= ((x << 1) & NOT_A) & opp
    x |= ((x << 1) & NOT_A) & opp
    moves |= ((x << 1) & NOT_A) & empty

    x = ((me >> 1) & NOT_H) & opp
    x |= ((x >> 1) & NOT_H) & opp
    x |= ((x >> 1) & NOT_H) & opp
    x |= ((x >> 1) & NOT_H) & opp
    x |= ((x >> 1) & NOT_H) & opp
    x |= ((x >> 1) & NOT_H) & opp
    moves |= ((x >> 1) & NOT_H) & empty

    x = (me << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    moves |= (x << 8) & empty

    x = (me >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    moves |= (x >> 8) & empty

    x = ((me << 9) & NOT_A) & opp
    x |= ((x << 9) & NOT_A) & opp
    x |= ((x << 9) & NOT_A) & opp
    x |= ((x << 9) & NOT_A) & opp
    x |= ((x << 9) & NOT_A) & opp
    x |= ((x << 9) & NOT_A) & opp
    moves |= ((x << 9) & NOT_A) & empty

    x = ((me << 7) & NOT_H) & opp
    x |= ((x << 7) & NOT_H) & opp
    x |= ((x << 7) & NOT_H) & opp
    x |= ((x << 7) & NOT_H) & opp
    x |= ((x << 7) & NOT_H) & opp
    x |= ((x << 7) & NOT_H) & opp
    moves |= ((x << 7) & NOT_H) & empty

    x = ((me >> 7) & NOT_A) & opp
    x |= ((x >> 7) & NOT_A) & opp
    x |= ((x >> 7) & NOT_A) & opp
    x |= ((x >> 7) & NOT_A) & opp
    x |= ((x >> 7) & NOT_A) & opp
    x |= ((x >> 7) & NOT_A) & opp
    moves |= ((x >> 7) & NOT_A) & empty

    x = ((me >> 9) & NOT_H) & opp
    x |= ((x >> 9) & NOT_H) & opp
    x |= ((x >> 9) & NOT_H) & opp
    x |= ((x >> 9) & NOT_H) & opp
    x |= ((x >> 9) & NOT_H) & opp
    x |= ((x >> 9) & NOT_H) & opp
    moves |= ((x >> 9) & NOT_H) & empty

    return moves & ALL


def sh_e(x): return (x << 1) & NOT_A
def sh_w(x): return (x >> 1) & NOT_H
def sh_s(x): return x << 8
def sh_n(x): return x >> 8
def sh_se(x): return (x << 9) & NOT_A
def sh_sw(x): return (x << 7) & NOT_H
def sh_ne(x): return (x >> 7) & NOT_A
def sh_nw(x): return (x >> 9) & NOT_H

SHIFTS = (sh_e, sh_w, sh_s, sh_n, sh_se, sh_sw, sh_ne, sh_nw)


def apply_move(move, me, opp):
    flips = 0
    for sh in SHIFTS:
        x = sh(move) & opp
        captured = 0
        while x:
            captured |= x
            y = sh(x)
            if y & me:
                flips |= captured
                break
            x = y & opp
    return me | move | flips, opp & ~flips


def adjacent(bb):
    return (
        ((bb << 1) & NOT_A) |
        ((bb >> 1) & NOT_H) |
        (bb << 8) |
        (bb >> 8) |
        ((bb << 9) & NOT_A) |
        ((bb << 7) & NOT_H) |
        ((bb >> 7) & NOT_A) |
        ((bb >> 9) & NOT_H)
    ) & ALL


def weighted_sum(bb):
    return (
        ROW_TABLE[0][bb & 255] +
        ROW_TABLE[1][(bb >> 8) & 255] +
        ROW_TABLE[2][(bb >> 16) & 255] +
        ROW_TABLE[3][(bb >> 24) & 255] +
        ROW_TABLE[4][(bb >> 32) & 255] +
        ROW_TABLE[5][(bb >> 40) & 255] +
        ROW_TABLE[6][(bb >> 48) & 255] +
        ROW_TABLE[7][(bb >> 56) & 255]
    )


def bad_corner_masks(occupied):
    xbad = 0
    cbad = 0

    if not (occupied & (1 << 0)):
        xbad |= 1 << 9
        cbad |= (1 << 1) | (1 << 8)

    if not (occupied & (1 << 7)):
        xbad |= 1 << 14
        cbad |= (1 << 6) | (1 << 15)

    if not (occupied & (1 << 56)):
        xbad |= 1 << 49
        cbad |= (1 << 48) | (1 << 57)

    if not (occupied & (1 << 63)):
        xbad |= 1 << 54
        cbad |= (1 << 55) | (1 << 62)

    return xbad, cbad


def stable_edge_count(bb):
    n = 0

    if bb & (1 << 0):
        for i in range(1, 8):
            if bb & (1 << i):
                n += 1
            else:
                break
        for i in range(8, 64, 8):
            if bb & (1 << i):
                n += 1
            else:
                break

    if bb & (1 << 7):
        for i in range(6, -1, -1):
            if bb & (1 << i):
                n += 1
            else:
                break
        for i in range(15, 64, 8):
            if bb & (1 << i):
                n += 1
            else:
                break

    if bb & (1 << 56):
        for i in range(57, 64):
            if bb & (1 << i):
                n += 1
            else:
                break
        for i in range(48, -1, -8):
            if bb & (1 << i):
                n += 1
            else:
                break

    if bb & (1 << 63):
        for i in range(62, 55, -1):
            if bb & (1 << i):
                n += 1
            else:
                break
        for i in range(55, -1, -8):
            if bb & (1 << i):
                n += 1
            else:
                break

    return n


def terminal_score(me, opp):
    diff = me.bit_count() - opp.bit_count()
    return diff * 100000


def evaluate(me, opp):
    occupied = me | opp
    empty = (~occupied) & ALL
    empties = empty.bit_count()

    my_moves_bb = legal_moves(me, opp)
    opp_moves_bb = legal_moves(opp, me)
    my_mob = my_moves_bb.bit_count()
    opp_mob = opp_moves_bb.bit_count()

    if my_mob == 0 and opp_mob == 0:
        return terminal_score(me, opp)

    my_discs = me.bit_count()
    opp_discs = opp.bit_count()
    disc_diff = my_discs - opp_discs

    score = 0

    # Actual mobility is one of the strongest midgame features.
    score += 80 * (my_mob - opp_mob)

    # Potential mobility: empty squares adjacent to opponent discs.
    score += 12 * (((adjacent(opp) & empty).bit_count()) -
                   ((adjacent(me) & empty).bit_count()))

    # Corners dominate Othello strategy.
    score += 1000 * ((me & CORNERS).bit_count() - (opp & CORNERS).bit_count())

    # Penalize discs next to empty corners.
    xbad, cbad = bad_corner_masks(occupied)
    score -= 450 * ((me & xbad).bit_count() - (opp & xbad).bit_count())
    score -= 250 * ((me & cbad).bit_count() - (opp & cbad).bit_count())

    # Stable-looking edge discs connected to owned corners.
    score += 120 * (stable_edge_count(me) - stable_edge_count(opp))

    # Frontier discs are vulnerable.
    adj_empty = adjacent(empty)
    score -= 14 * ((adj_empty & me).bit_count() - (adj_empty & opp).bit_count())

    # Square table.
    score += weighted_sum(me) - weighted_sum(opp)

    # Disc count matters mostly late; early, having fewer discs can be better.
    if empties > 44:
        score -= 4 * disc_diff
    elif empties > 18:
        score -= 2 * disc_diff
    else:
        score += (28 - empties) * disc_diff

    # Slight parity preference in very late positions.
    if empties <= 12:
        score += 15 if (empties % 2 == 1) else -15

    return score


def move_order_score(move, me, opp, tt_move=0):
    if move == tt_move:
        return 10 ** 8

    idx = move.bit_length() - 1
    s = ORDER_WEIGHTS[idx]

    if move & CORNERS:
        s += 1000000

    occupied = me | opp
    xbad, cbad = bad_corner_masks(occupied)
    if move & xbad:
        s -= 50000
    if move & cbad:
        s -= 15000

    return s


def ordered_moves(moves, me, opp, tt_move=0):
    arr = []
    bb = moves
    while bb:
        m = bb & -bb
        bb -= m
        arr.append((move_order_score(m, me, opp, tt_move), m))
    arr.sort(reverse=True)
    return [m for _, m in arr]


def check_time():
    if time.perf_counter() > END_TIME:
        raise TimeoutError


def negamax(me, opp, depth, alpha, beta):
    global NODES, TT

    NODES += 1
    if (NODES & 1023) == 0:
        check_time()

    if depth <= 0:
        return evaluate(me, opp)

    key = (me, opp)
    original_alpha = alpha
    tt_move = 0

    entry = TT.get(key)
    if entry is not None:
        e_depth, e_score, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:
                return e_score
            if e_flag == 1:
                if e_score > alpha:
                    alpha = e_score
            elif e_flag == 2:
                if e_score < beta:
                    beta = e_score
            if alpha >= beta:
                return e_score

    moves = legal_moves(me, opp)

    if moves == 0:
        if legal_moves(opp, me) == 0:
            return terminal_score(me, opp)
        return -negamax(opp, me, depth, -beta, -alpha)

    best = -INF
    best_move = 0

    for move in ordered_moves(moves, me, opp, tt_move):
        nme, nopp = apply_move(move, me, opp)
        val = -negamax(nopp, nme, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = move
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= original_alpha:
        flag = 2  # upper bound
    elif best >= beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    TT[key] = (depth, best, flag, best_move)
    return best


def root_search(me, opp, depth, preferred=0):
    moves = legal_moves(me, opp)
    order = ordered_moves(moves, me, opp, preferred)

    best_move = order[0]
    best_score = -INF
    alpha = -INF
    beta = INF

    for move in order:
        check_time()
        nme, nopp = apply_move(move, me, opp)
        val = -negamax(nopp, nme, depth - 1, -beta, -alpha)

        if val > best_score:
            best_score = val
            best_move = move
        if val > alpha:
            alpha = val

    return best_move, best_score


def choose_fallback(me, opp, moves):
    best_move = moves & -moves
    best_score = -INF

    for move in ordered_moves(moves, me, opp, 0):
        nme, nopp = apply_move(move, me, opp)
        val = -evaluate(nopp, nme)
        if val > best_score:
            best_score = val
            best_move = move

    return best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global END_TIME, NODES, TT

    me, opp = arrays_to_bits(you, opponent)
    moves = legal_moves(me, opp)

    if moves == 0:
        return "pass"

    # Forced move: immediately return it.
    if moves & (moves - 1) == 0:
        return bit_to_str(moves)

    fallback = choose_fallback(me, opp, moves)
    best_move = fallback

    try:
        if len(TT) > TT_LIMIT:
            TT.clear()

        NODES = 0
        END_TIME = time.perf_counter() + TIME_LIMIT

        occupied = me | opp
        empties = 64 - occupied.bit_count()

        # Iterative deepening. Near the end, this attempts an exact solve.
        max_depth = empties
        preferred = best_move
        last_score = 0

        for depth in range(1, max_depth + 1):
            move, score = root_search(me, opp, depth, preferred)
            best_move = move
            preferred = move
            last_score = score

            # If a full-width endgame solve completed, no need to search deeper.
            if depth >= empties:
                break

            # If the result is a proven terminal win/loss and sufficiently deep,
            # avoid wasting time.
            if depth >= 8 and abs(last_score) >= 100000:
                break

    except TimeoutError:
        pass
    except Exception:
        # Absolute safety: fallback was generated from the legal move list.
        pass

    return bit_to_str(best_move)
