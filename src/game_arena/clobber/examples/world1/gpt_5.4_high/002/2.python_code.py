
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

FULL = (1 << N) - 1
WIN = 1_000_000
INF = 2_000_000

TIME_LIMIT = 0.90
ENDGAME_PIECES = 10

BITS = [1 << i for i in range(N)]

COL0 = sum(1 << (r * COLS) for r in range(ROWS))
COL5 = sum(1 << (r * COLS + COLS - 1) for r in range(ROWS))
NOT_COL0 = FULL ^ COL0
NOT_COL5 = FULL ^ COL5

INNER_MASK = 0
CORE_MASK = 0
POS_BONUS = [0] * N
ADJ_MASK = [0] * N

for r in range(1, ROWS - 1):
    for c in range(1, COLS - 1):
        INNER_MASK |= 1 << (r * COLS + c)

for r in range(1, ROWS - 1):
    for c in range(2, 4):
        CORE_MASK |= 1 << (r * COLS + c)

for idx in range(N):
    bit = 1 << idx
    bonus = 0
    if bit & INNER_MASK:
        bonus += 1
    if bit & CORE_MASK:
        bonus += 2
    POS_BONUS[idx] = bonus

    r, c = divmod(idx, COLS)
    m = 0
    if r > 0:
        m |= 1 << (idx - COLS)
    if r < ROWS - 1:
        m |= 1 << (idx + COLS)
    if c > 0:
        m |= 1 << (idx - 1)
    if c < COLS - 1:
        m |= 1 << (idx + 1)
    ADJ_MASK[idx] = m

EXACT = 0
LOWER = 1
UPPER = 2

TT = {}
DEADLINE = 0.0
NODE_COUNT = 0


class SearchTimeout(Exception):
    pass


def flatten_board(arr):
    out = []

    def rec(x):
        if len(out) >= N:
            return
        if isinstance(x, (str, bytes)):
            try:
                out.append(1 if int(x) else 0)
            except Exception:
                out.append(0)
            return
        try:
            it = iter(x)
        except TypeError:
            try:
                out.append(1 if int(x) else 0)
            except Exception:
                out.append(0)
        else:
            for y in it:
                rec(y)

    rec(arr)
    if len(out) < N:
        out.extend([0] * (N - len(out)))
    return out[:N]


def bits_from_flat(flat):
    bits = 0
    for i, v in enumerate(flat):
        if v:
            bits |= 1 << i
    return bits


def source_union(my, opp):
    return (
        (my & ((opp << COLS) & FULL))
        | (my & (opp >> COLS))
        | (my & ((opp << 1) & FULL) & NOT_COL0)
        | (my & (opp >> 1) & NOT_COL5)
    )


def dest_union(my, opp):
    return (
        (((my << COLS) & FULL) & opp)
        | ((my >> COLS) & opp)
        | ((((my << 1) & FULL) & NOT_COL0) & opp)
        | (((my >> 1) & NOT_COL5) & opp)
    )


def mobility(my, opp):
    return (
        (my & ((opp << COLS) & FULL)).bit_count()
        + (my & (opp >> COLS)).bit_count()
        + (my & ((opp << 1) & FULL) & NOT_COL0).bit_count()
        + (my & (opp >> 1) & NOT_COL5).bit_count()
    )


def gen_moves(my, opp):
    moves = []

    srcs = my & ((opp << COLS) & FULL)
    while srcs:
        b = srcs & -srcs
        s = b.bit_length() - 1
        moves.append((s, s - COLS, "U"))
        srcs ^= b

    srcs = my & (opp >> 1) & NOT_COL5
    while srcs:
        b = srcs & -srcs
        s = b.bit_length() - 1
        moves.append((s, s + 1, "R"))
        srcs ^= b

    srcs = my & (opp >> COLS)
    while srcs:
        b = srcs & -srcs
        s = b.bit_length() - 1
        moves.append((s, s + COLS, "D"))
        srcs ^= b

    srcs = my & ((opp << 1) & FULL) & NOT_COL0
    while srcs:
        b = srcs & -srcs
        s = b.bit_length() - 1
        moves.append((s, s - 1, "L"))
        srcs ^= b

    return moves


def child_state(my, opp, move):
    s, d, _ = move
    bs = BITS[s]
    bd = BITS[d]
    my2 = (my ^ bs) | bd
    opp2 = opp ^ bd
    # Next turn is from the opponent's perspective.
    return opp2, my2


def evaluate(my, opp, cur_mob=None):
    if cur_mob is None:
        cur_mob = mobility(my, opp)
    opp_mob = mobility(opp, my)

    cur_active = source_union(my, opp).bit_count()
    opp_active = source_union(opp, my).bit_count()

    cur_threats = dest_union(my, opp).bit_count()
    opp_threats = dest_union(opp, my).bit_count()

    piece_diff = my.bit_count() - opp.bit_count()
    inner_diff = (my & INNER_MASK).bit_count() - (opp & INNER_MASK).bit_count()
    core_diff = (my & CORE_MASK).bit_count() - (opp & CORE_MASK).bit_count()

    return (
        82 * (cur_mob - opp_mob)
        + 22 * (cur_active - opp_active)
        + 14 * (cur_threats - opp_threats)
        + 6 * piece_diff
        + 3 * inner_diff
        + 2 * core_diff
    )


def order_children(my, opp, moves, tt_move=None):
    if len(moves) == 1:
        mv = moves[0]
        cmy, copp = child_state(my, opp, mv)
        return [(mv, cmy, copp)]

    scored = []
    for mv in moves:
        cmy, copp = child_state(my, opp, mv)
        child_mob = mobility(cmy, copp)
        if child_mob == 0:
            score = 10_000_000
        else:
            future_mob = mobility(copp, cmy)
            danger = (ADJ_MASK[mv[1]] & cmy).bit_count()
            score = -64 * child_mob + 14 * future_mob - 5 * danger + 4 * POS_BONUS[mv[1]]
        if mv == tt_move:
            score += 5_000_000
        scored.append((score, mv, cmy, copp))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(mv, cmy, copp) for _, mv, cmy, copp in scored]


def search(my, opp, depth, alpha, beta, ply):
    global NODE_COUNT

    NODE_COUNT += 1
    if (NODE_COUNT & 511) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    alpha_orig = alpha
    beta_orig = beta

    key = my | (opp << N)
    tt_move = None
    entry = TT.get(key)
    if entry is not None:
        e_depth, e_flag, e_score, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_score
            if e_flag == LOWER:
                if e_score > alpha:
                    alpha = e_score
            else:
                if e_score < beta:
                    beta = e_score
            if alpha >= beta:
                return e_score

    moves = gen_moves(my, opp)
    if not moves:
        return -(WIN - ply)

    if depth <= 0:
        pieces = (my | opp).bit_count()
        if pieces > ENDGAME_PIECES:
            return evaluate(my, opp, cur_mob=len(moves))
        depth = pieces

    ordered = order_children(my, opp, moves, tt_move)

    best = -INF
    best_move = ordered[0][0]
    first = True

    for mv, cmy, copp in ordered:
        if first:
            score = -search(cmy, copp, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            score = -search(cmy, copp, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -search(cmy, copp, depth - 1, -beta, -alpha, ply + 1)

        if score > best:
            best = score
            best_move = mv
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    flag = EXACT
    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER

    TT[key] = (depth, flag, best, best_move)
    return best


def root_search(my, opp, moves, depth, hint_move=None):
    if time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    key = my | (opp << N)
    tt_move = hint_move
    entry = TT.get(key)
    if entry is not None and entry[3] is not None:
        tt_move = entry[3]

    ordered = order_children(my, opp, moves, tt_move)

    alpha = -INF
    beta = INF
    best = -INF
    best_move = ordered[0][0]
    first = True

    for mv, cmy, copp in ordered:
        if first:
            score = -search(cmy, copp, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            score = -search(cmy, copp, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < score < beta:
                score = -search(cmy, copp, depth - 1, -beta, -alpha, 1)

        if score > best:
            best = score
            best_move = mv
        if score > alpha:
            alpha = score

    TT[key] = (depth, EXACT, best, best_move)
    return best, best_move


def move_to_str(move):
    s, _, d = move
    return f"{s // COLS},{s % COLS},{d}"


def brute_fallback(flat_you, flat_opp):
    for r in range(ROWS):
        for c in range(COLS):
            i = r * COLS + c
            if not flat_you[i]:
                continue
            if r > 0 and flat_opp[(r - 1) * COLS + c]:
                return f"{r},{c},U"
            if c < COLS - 1 and flat_opp[r * COLS + (c + 1)]:
                return f"{r},{c},R"
            if r < ROWS - 1 and flat_opp[(r + 1) * COLS + c]:
                return f"{r},{c},D"
            if c > 0 and flat_opp[r * COLS + (c - 1)]:
                return f"{r},{c},L"
    return "0,0,U"


def policy(you, opponent) -> str:
    flat_you = flatten_board(you)
    flat_opp = flatten_board(opponent)
    fallback = brute_fallback(flat_you, flat_opp)

    try:
        my = bits_from_flat(flat_you)
        opp = bits_from_flat(flat_opp)

        moves = gen_moves(my, opp)
        if not moves:
            return fallback
        if len(moves) == 1:
            return move_to_str(moves[0])

        ordered = order_children(my, opp, moves)
        best_move = ordered[0][0]

        for mv, cmy, copp in ordered:
            if mobility(cmy, copp) == 0:
                return move_to_str(mv)

        global TT, DEADLINE, NODE_COUNT
        TT = {}
        NODE_COUNT = 0
        DEADLINE = time.perf_counter() + TIME_LIMIT

        max_depth = (my | opp).bit_count() - 1
        depth = 1

        try:
            while depth <= max_depth:
                if time.perf_counter() >= DEADLINE:
                    break
                score, mv = root_search(my, opp, moves, depth, best_move)
                best_move = mv
                if abs(score) >= WIN // 2:
                    break
                depth += 1
        except SearchTimeout:
            pass

        return move_to_str(best_move)
    except Exception:
        return fallback
