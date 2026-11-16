
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

INF = 10**9
MATE = 100000

EXACT = 0
LOWER = 1
UPPER = 2

BIT = [1 << i for i in range(N)]
NEIGHBORS = [[] for _ in range(N)]
ADJ_MASK = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        mask = 0
        if r > 0:
            NEIGHBORS[i].append((i - COLS, 'U'))
            mask |= BIT[i - COLS]
        if c < COLS - 1:
            NEIGHBORS[i].append((i + 1, 'R'))
            mask |= BIT[i + 1]
        if r < ROWS - 1:
            NEIGHBORS[i].append((i + COLS, 'D'))
            mask |= BIT[i + COLS]
        if c > 0:
            NEIGHBORS[i].append((i - 1, 'L'))
            mask |= BIT[i - 1]
        ADJ_MASK[i] = mask

TT = {}
HISTORY = [0] * (N * N)
KILLERS = [[-1, -1] for _ in range(64)]

SEARCH_END = 0.0
NODE_COUNT = 0


class SearchTimeout(Exception):
    pass


try:
    (1).bit_count

    def popcount(x: int) -> int:
        return x.bit_count()
except Exception:
    def popcount(x: int) -> int:
        return bin(x).count("1")


def to_bitboard(arr) -> int:
    b = 0
    try:
        if len(arr) == N and not hasattr(arr[0], "__len__"):
            for i, v in enumerate(arr):
                if int(v):
                    b |= BIT[i]
            return b
    except Exception:
        pass

    for r in range(ROWS):
        for c in range(COLS):
            try:
                v = arr[r][c]
            except Exception:
                try:
                    v = arr[r, c]
                except Exception:
                    v = arr[r * COLS + c]
            if int(v):
                b |= BIT[r * COLS + c]
    return b


def generate_moves(me: int, opp: int):
    moves = []
    bits = me
    while bits:
        lsb = bits & -bits
        frm = lsb.bit_length() - 1
        if ADJ_MASK[frm] & opp:
            for to, d in NEIGHBORS[frm]:
                if opp & BIT[to]:
                    moves.append((frm, to, d))
        bits ^= lsb
    return moves


def has_move(me: int, opp: int) -> bool:
    bits = me
    while bits:
        lsb = bits & -bits
        frm = lsb.bit_length() - 1
        if ADJ_MASK[frm] & opp:
            return True
        bits ^= lsb
    return False


def active_count(me: int, opp: int) -> int:
    cnt = 0
    bits = me
    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        if ADJ_MASK[idx] & opp:
            cnt += 1
        bits ^= lsb
    return cnt


def side_stats(me: int, opp: int, moves):
    active_from = {}
    safe = 0
    exposure_total = 0
    for frm, to, _ in moves:
        active_from[frm] = 1
        exposure = popcount(ADJ_MASK[to] & (opp ^ BIT[to]))
        exposure_total += exposure
        if exposure == 0:
            safe += 1
    return len(active_from), safe, exposure_total


def eval_state(me: int, opp: int, moves) -> int:
    active_me, safe_me, exp_me = side_stats(me, opp, moves)
    opp_moves = generate_moves(opp, me)
    if opp_moves:
        active_opp, safe_opp, exp_opp = side_stats(opp, me, opp_moves)
    else:
        active_opp = 0
        safe_opp = 0
        exp_opp = 0

    return (
        60 * (safe_me - safe_opp)
        + 18 * (active_me - active_opp)
        + 5 * (popcount(me) - popcount(opp))
        + 2 * (exp_opp - exp_me)
        + 4
    )


def apply_swapped(me: int, opp: int, frm: int, to: int):
    opp_after = opp ^ BIT[to]
    me_after = (me ^ BIT[frm]) | BIT[to]
    return opp_after, me_after


def move_id(frm: int, to: int) -> int:
    return frm * N + to


def move_from_id(mid: int, moves):
    if mid < 0:
        return None
    frm = mid // N
    to = mid % N
    for m in moves:
        if m[0] == frm and m[1] == to:
            return m
    return None


def order_moves(moves, me: int, opp: int, tt_move: int, ply: int):
    if len(moves) <= 1:
        return moves

    k0, k1 = KILLERS[ply]
    scored = []

    for frm, to, d in moves:
        mid = move_id(frm, to)
        score = HISTORY[mid]

        if mid == tt_move:
            score += 3_000_000
        if mid == k0:
            score += 2_000_000
        elif mid == k1:
            score += 1_500_000

        opp_after = opp ^ BIT[to]
        exposure = popcount(ADJ_MASK[to] & opp_after)

        score += (4 - exposure) * 200
        score += popcount(ADJ_MASK[to] & me) * 30
        score += popcount(ADJ_MASK[frm] & opp) * 10

        if ply < 2:
            me_after = (me ^ BIT[frm]) | BIT[to]
            if not has_move(opp_after, me_after):
                score += 2_500_000
            else:
                score += 40 * (active_count(me_after, opp_after) - active_count(opp_after, me_after))

        scored.append((score, (frm, to, d)))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def search(me: int, opp: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    global NODE_COUNT

    NODE_COUNT += 1
    if (NODE_COUNT & 511) == 0 and time.perf_counter() >= SEARCH_END:
        raise SearchTimeout

    orig_alpha = alpha
    orig_beta = beta

    key = (me << N) | opp
    tt_move = -1
    entry = TT.get(key)
    if entry is not None:
        edepth, escore, eflag, emove = entry
        tt_move = emove
        if edepth >= depth:
            if eflag == EXACT:
                return escore
            if eflag == LOWER:
                if escore > alpha:
                    alpha = escore
            else:
                if escore < beta:
                    beta = escore
            if alpha >= beta:
                return escore

    moves = generate_moves(me, opp)
    if not moves:
        return -MATE - popcount(me | opp)

    if depth == 0:
        return eval_state(me, opp, moves)

    ordered = order_moves(moves, me, opp, tt_move, ply)

    best_score = -INF
    best_mid = move_id(ordered[0][0], ordered[0][1])
    first = True

    for i, move in enumerate(ordered):
        frm, to, _ = move
        opp_after = opp ^ BIT[to]
        me_after = (me ^ BIT[frm]) | BIT[to]
        child_me = opp_after
        child_opp = me_after

        reduced = False
        new_depth = depth - 1
        if (not first) and depth >= 4 and i >= 4 and popcount(ADJ_MASK[to] & opp_after) > 0:
            reduced = True
            new_depth = depth - 2

        if first:
            score = -search(child_me, child_opp, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            score = -search(child_me, child_opp, new_depth, -alpha - 1, -alpha, ply + 1)
            if score > alpha and reduced:
                score = -search(child_me, child_opp, depth - 1, -alpha - 1, -alpha, ply + 1)
            if score > alpha and score < beta:
                score = -search(child_me, child_opp, depth - 1, -beta, -alpha, ply + 1)

        if score > best_score:
            best_score = score
            best_mid = move_id(frm, to)

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if best_mid != KILLERS[ply][0]:
                KILLERS[ply][1] = KILLERS[ply][0]
                KILLERS[ply][0] = best_mid
            HISTORY[best_mid] += depth * depth
            break

    if best_score <= orig_alpha:
        flag = UPPER
    elif best_score >= orig_beta:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best_score, flag, best_mid)
    return best_score


def root_search(me: int, opp: int, depth: int, alpha: int, beta: int):
    orig_alpha = alpha
    orig_beta = beta

    moves = generate_moves(me, opp)
    if not moves:
        return -MATE - popcount(me | opp), None

    key = (me << N) | opp
    tt_move = -1
    entry = TT.get(key)
    if entry is not None:
        edepth, escore, eflag, emove = entry
        tt_move = emove
        if edepth >= depth:
            if eflag == EXACT:
                mv = move_from_id(emove, moves)
                return escore, (mv if mv is not None else moves[0])
            if eflag == LOWER:
                if escore > alpha:
                    alpha = escore
            else:
                if escore < beta:
                    beta = escore
            if alpha >= beta:
                mv = move_from_id(emove, moves)
                return escore, (mv if mv is not None else moves[0])

    ordered = order_moves(moves, me, opp, tt_move, 0)

    best_score = -INF
    best_move = ordered[0]
    first = True

    for move in ordered:
        frm, to, _ = move
        child_me, child_opp = apply_swapped(me, opp, frm, to)

        if first:
            score = -search(child_me, child_opp, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            score = -search(child_me, child_opp, depth - 1, -alpha - 1, -alpha, 1)
            if score > alpha and score < beta:
                score = -search(child_me, child_opp, depth - 1, -beta, -alpha, 1)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    best_mid = move_id(best_move[0], best_move[1])
    if best_score <= orig_alpha:
        flag = UPPER
    elif best_score >= orig_beta:
        flag = LOWER
    else:
        flag = EXACT
    TT[key] = (depth, best_score, flag, best_mid)

    return best_score, best_move


def move_to_str(move) -> str:
    frm, _, d = move
    return f"{frm // COLS},{frm % COLS},{d}"


def policy(you, opponent) -> str:
    global SEARCH_END, NODE_COUNT

    if len(TT) > 350000:
        TT.clear()

    if max(HISTORY) > 1_000_000:
        for i in range(len(HISTORY)):
            HISTORY[i] //= 2

    for k in KILLERS:
        k[0] = -1
        k[1] = -1

    me = to_bitboard(you)
    opp = to_bitboard(opponent)

    moves = generate_moves(me, opp)
    if not moves:
        return "0,0,U"

    if len(moves) == 1:
        return move_to_str(moves[0])

    for m in moves:
        child_me, child_opp = apply_swapped(me, opp, m[0], m[1])
        if not has_move(child_me, child_opp):
            return move_to_str(m)

    root_key = (me << N) | opp
    tt_move = TT[root_key][3] if root_key in TT else -1
    best_move = order_moves(moves, me, opp, tt_move, 0)[0]

    SEARCH_END = time.perf_counter() + 0.92
    NODE_COUNT = 0

    max_depth = popcount(me | opp) - 1
    last_score = 0

    for depth in range(1, max_depth + 1):
        try:
            if depth == 1:
                score, move = root_search(me, opp, depth, -INF, INF)
            else:
                window = 120
                alpha = last_score - window
                beta = last_score + window
                while True:
                    score, move = root_search(me, opp, depth, alpha, beta)
                    if score <= alpha:
                        alpha -= window
                        window *= 2
                    elif score >= beta:
                        beta += window
                        window *= 2
                    else:
                        break

            if move is not None:
                best_move = move
                last_score = score

            if depth >= max_depth:
                break
        except SearchTimeout:
            break

    return move_to_str(best_move)
