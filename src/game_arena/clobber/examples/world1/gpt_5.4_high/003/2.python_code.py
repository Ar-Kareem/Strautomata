
import sys
from time import perf_counter

sys.setrecursionlimit(10000)

ROWS = 5
COLS = 6
N = ROWS * COLS

ALL_MASK = (1 << N) - 1
COL0_MASK = sum(1 << (r * COLS) for r in range(ROWS))
COL5_MASK = sum(1 << (r * COLS + (COLS - 1)) for r in range(ROWS))
NOT_COL0 = ALL_MASK ^ COL0_MASK
NOT_COL5 = ALL_MASK ^ COL5_MASK

WIN_SCORE = 100000
INF = 10**9

FLAG_UPPER = -1
FLAG_EXACT = 0
FLAG_LOWER = 1

TIME_LIMIT = 0.93
EXACT_PIECES = 14
EXACT_TOTAL_MOBILITY = 7

MAX_TT = 400000
MAX_EXACT_TT = 300000

CELL_WEIGHT = [
    0, 1, 1, 1, 1, 0,
    1, 2, 3, 3, 2, 1,
    1, 3, 4, 4, 3, 1,
    1, 2, 3, 3, 2, 1,
    0, 1, 1, 1, 1, 0,
]

NEIGH_MASK = [0] * N
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        m = 0
        if r > 0:
            m |= 1 << ((r - 1) * COLS + c)
        if r + 1 < ROWS:
            m |= 1 << ((r + 1) * COLS + c)
        if c > 0:
            m |= 1 << (r * COLS + (c - 1))
        if c + 1 < COLS:
            m |= 1 << (r * COLS + (c + 1))
        NEIGH_MASK[i] = m

TT = {}
EXACT_TT = {}
EXACT_BEST = {}
HISTORY = [0] * (N * N)

END_TIME = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def check_time():
    global NODE_COUNTER
    NODE_COUNTER += 1
    if (NODE_COUNTER & 255) == 0 and perf_counter() >= END_TIME:
        raise SearchTimeout


def to_mask(board):
    try:
        flat = board.ravel()
    except Exception:
        try:
            first = board[0]
        except Exception:
            first = None

        if first is not None:
            try:
                iter(first)
                flat = [v for row in board for v in row]
            except TypeError:
                flat = board
        else:
            flat = board

    mask = 0
    for i, v in enumerate(flat):
        if int(v):
            mask |= 1 << i
    return mask


def move_to_str(move):
    src, _, dch = move
    return f"{src // COLS},{src % COLS},{dch}"


def count_moves(side, opp):
    return (
        (side & ((opp << COLS) & ALL_MASK)).bit_count()
        + (side & (opp >> COLS)).bit_count()
        + (side & (((opp << 1) & ALL_MASK) & NOT_COL0)).bit_count()
        + (side & ((opp >> 1) & NOT_COL5)).bit_count()
    )


def active_pieces(side, opp):
    adj_to_opp = (
        ((opp << COLS) & ALL_MASK)
        | (opp >> COLS)
        | (((opp << 1) & ALL_MASK) & NOT_COL0)
        | ((opp >> 1) & NOT_COL5)
    )
    return (side & adj_to_opp).bit_count()


def gen_moves(side, opp):
    moves = []

    srcs = side & ((opp << COLS) & ALL_MASK)
    while srcs:
        b = srcs & -srcs
        s = b.bit_length() - 1
        moves.append((s, s - COLS, "U"))
        srcs ^= b

    srcs = side & (opp >> COLS)
    while srcs:
        b = srcs & -srcs
        s = b.bit_length() - 1
        moves.append((s, s + COLS, "D"))
        srcs ^= b

    srcs = side & (((opp << 1) & ALL_MASK) & NOT_COL0)
    while srcs:
        b = srcs & -srcs
        s = b.bit_length() - 1
        moves.append((s, s - 1, "L"))
        srcs ^= b

    srcs = side & ((opp >> 1) & NOT_COL5)
    while srcs:
        b = srcs & -srcs
        s = b.bit_length() - 1
        moves.append((s, s + 1, "R"))
        srcs ^= b

    return moves


def evaluate(side, opp, my_moves=None, opp_moves=None):
    if my_moves is None:
        my_moves = count_moves(side, opp)
    if opp_moves is None:
        opp_moves = count_moves(opp, side)

    my_active = active_pieces(side, opp)
    opp_active = active_pieces(opp, side)
    piece_diff = side.bit_count() - opp.bit_count()

    score = 30 * (my_moves - opp_moves)
    score += 10 * (my_active - opp_active)
    score += 2 * piece_diff

    if my_moves == 1:
        score -= 8
    if opp_moves == 1:
        score += 8

    return score


def move_order_score(side, opp, move):
    s, d, _ = move
    opp2 = opp ^ (1 << d)
    side2 = (side ^ (1 << s)) | (1 << d)

    opp_m = count_moves(opp2, side2)
    my_m = count_moves(side2, opp2)

    score = HISTORY[s * N + d]
    score += 20 * my_m
    score -= 24 * opp_m
    score += 4 * CELL_WEIGHT[d]

    if opp_m == 0:
        score += 1000000

    if NEIGH_MASK[d] & opp2:
        score += 6
    else:
        score -= 6

    return score


def order_moves(side, opp, moves, hint=None):
    if len(moves) <= 1:
        return moves

    scored = []
    for m in moves:
        if hint is not None and m == hint:
            scored.append((10**18, m))
        else:
            scored.append((move_order_score(side, opp, m), m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def solve(side, opp):
    check_time()
    key = (side, opp)

    cached = EXACT_TT.get(key)
    if cached is not None:
        return cached

    moves = gen_moves(side, opp)
    if not moves:
        EXACT_TT[key] = -1
        return -1

    hint = EXACT_BEST.get(key)
    tt_entry = TT.get(key)
    if tt_entry is not None and tt_entry[3] is not None:
        hint = tt_entry[3]

    ordered = order_moves(side, opp, moves, hint)

    for m in ordered:
        s, d, _ = m
        child = solve(opp ^ (1 << d), (side ^ (1 << s)) | (1 << d))
        if child < 0:
            EXACT_TT[key] = 1
            EXACT_BEST[key] = m
            HISTORY[s * N + d] += 32
            return 1

    EXACT_TT[key] = -1
    EXACT_BEST[key] = ordered[0]
    return -1


def negamax(side, opp, depth, alpha, beta):
    check_time()
    key = (side, opp)
    rem = (side | opp).bit_count()

    if rem <= EXACT_PIECES:
        return WIN_SCORE if solve(side, opp) > 0 else -WIN_SCORE

    orig_alpha = alpha
    orig_beta = beta

    entry = TT.get(key)
    tt_move = None
    if entry is not None:
        entry_depth, entry_val, entry_flag, entry_move = entry
        tt_move = entry_move
        if entry_depth >= depth:
            if entry_flag == FLAG_EXACT:
                return entry_val
            if entry_flag == FLAG_LOWER:
                alpha = max(alpha, entry_val)
            elif entry_flag == FLAG_UPPER:
                beta = min(beta, entry_val)
            if alpha >= beta:
                return entry_val

    moves = gen_moves(side, opp)
    if not moves:
        return -WIN_SCORE

    opp_moves = None
    if len(moves) <= EXACT_TOTAL_MOBILITY:
        opp_moves = count_moves(opp, side)
        if len(moves) + opp_moves <= EXACT_TOTAL_MOBILITY:
            return WIN_SCORE if solve(side, opp) > 0 else -WIN_SCORE

    if depth <= 0:
        if opp_moves is None:
            opp_moves = count_moves(opp, side)
        return evaluate(side, opp, len(moves), opp_moves)

    hint = tt_move if tt_move is not None else EXACT_BEST.get(key)
    ordered = order_moves(side, opp, moves, hint)

    best_val = -INF
    best_move = ordered[0]

    for m in ordered:
        s, d, _ = m
        val = -negamax(
            opp ^ (1 << d),
            (side ^ (1 << s)) | (1 << d),
            depth - 1,
            -beta,
            -alpha,
        )

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            HISTORY[s * N + d] += depth * depth
            break

    flag = FLAG_EXACT
    if best_val <= orig_alpha:
        flag = FLAG_UPPER
    elif best_val >= orig_beta:
        flag = FLAG_LOWER

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, best_val, flag, best_move)

    return best_val


def root_search(side, opp, moves, depth, hint=None):
    alpha = -INF
    beta = INF

    ordered = order_moves(side, opp, moves, hint)
    best_move = ordered[0]
    best_val = -INF

    for m in ordered:
        s, d, _ = m
        val = -negamax(
            opp ^ (1 << d),
            (side ^ (1 << s)) | (1 << d),
            depth - 1,
            -beta,
            -alpha,
        )

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if best_val >= WIN_SCORE:
            break

    TT[(side, opp)] = (depth, best_val, FLAG_EXACT, best_move)
    return best_move, best_val


def policy(you: list[int], opponent: list[int]) -> str:
    global END_TIME, NODE_COUNTER

    END_TIME = perf_counter() + TIME_LIMIT
    NODE_COUNTER = 0

    if len(TT) > MAX_TT:
        TT.clear()
    if len(EXACT_TT) > MAX_EXACT_TT:
        EXACT_TT.clear()
        EXACT_BEST.clear()
    if max(HISTORY) > 1_000_000:
        for i in range(len(HISTORY)):
            HISTORY[i] //= 2

    side = to_mask(you)
    opp = to_mask(opponent)

    moves = gen_moves(side, opp)
    if not moves:
        # Terminal positions should not be passed to the policy.
        return "0,0,U"

    hint = EXACT_BEST.get((side, opp))
    tt_entry = TT.get((side, opp))
    if tt_entry is not None and tt_entry[3] is not None:
        hint = tt_entry[3]

    ordered = order_moves(side, opp, moves, hint)
    best_move = ordered[0]

    if len(ordered) == 1:
        return move_to_str(best_move)

    # Immediate tactical win.
    for m in ordered:
        s, d, _ = m
        opp2 = opp ^ (1 << d)
        side2 = (side ^ (1 << s)) | (1 << d)
        if count_moves(opp2, side2) == 0:
            return move_to_str(m)

    try:
        rem = (side | opp).bit_count()
        do_exact_root = False

        if rem <= EXACT_PIECES:
            do_exact_root = True
        elif len(moves) <= EXACT_TOTAL_MOBILITY:
            if len(moves) + count_moves(opp, side) <= EXACT_TOTAL_MOBILITY:
                do_exact_root = True

        if do_exact_root and solve(side, opp) > 0:
            exact_move = EXACT_BEST.get((side, opp))
            if exact_move is not None:
                return move_to_str(exact_move)

        depth = 1
        best_val = -INF

        while perf_counter() < END_TIME:
            mv, val = root_search(side, opp, moves, depth, best_move)
            best_move, best_val = mv, val
            if best_val >= WIN_SCORE:
                break
            depth += 1

    except SearchTimeout:
        pass

    return move_to_str(best_move)
