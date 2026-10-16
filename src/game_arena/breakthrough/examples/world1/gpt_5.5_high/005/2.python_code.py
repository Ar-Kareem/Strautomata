
import time

# Bitboard square index: row * 8 + col
# Color index: 0 = black, 1 = white
BLACK = 0
WHITE = 1
COLOR_TO_CI = {"b": BLACK, "w": WHITE}
OPP_CI = [WHITE, BLACK]

ALL_MASK = (1 << 64) - 1
MASKS = tuple(1 << i for i in range(64))
ROW_MASKS = tuple(sum(1 << (r * 8 + c) for c in range(8)) for r in range(8))

GOAL_MASK = [ROW_MASKS[0], ROW_MASKS[7]]
BEFORE_GOAL_MASK = [ROW_MASKS[1], ROW_MASKS[6]]

COL0 = sum(1 << (r * 8) for r in range(8))
COL7 = sum(1 << (r * 8 + 7) for r in range(8))
NOT_COL0 = ALL_MASK ^ COL0
NOT_COL7 = ALL_MASK ^ COL7

FWD = [[-1] * 64 for _ in range(2)]
DIAGS = [[() for _ in range(64)] for _ in range(2)]

for sq in range(64):
    r, c = divmod(sq, 8)

    # Black moves toward lower rows.
    if r > 0:
        FWD[BLACK][sq] = sq - 8
        ds = []
        if c > 0:
            ds.append(sq - 9)
        if c < 7:
            ds.append(sq - 7)
        DIAGS[BLACK][sq] = tuple(ds)

    # White moves toward higher rows.
    if r < 7:
        FWD[WHITE][sq] = sq + 8
        ds = []
        if c > 0:
            ds.append(sq + 7)
        if c < 7:
            ds.append(sq + 9)
        DIAGS[WHITE][sq] = tuple(ds)

CENTER_BONUS = [0, 2, 4, 5, 5, 4, 2, 0]

PROGRESS = [[0] * 64 for _ in range(2)]
ADV_VALUE = [[0] * 64 for _ in range(2)]
PASSED_MASK = [[0] * 64 for _ in range(2)]

for sq in range(64):
    r, c = divmod(sq, 8)

    bp = 7 - r
    wp = r
    PROGRESS[BLACK][sq] = bp
    PROGRESS[WHITE][sq] = wp

    ADV_VALUE[BLACK][sq] = bp * 16 + bp * bp * 7 + CENTER_BONUS[c] * (bp + 2)
    ADV_VALUE[WHITE][sq] = wp * 16 + wp * wp * 7 + CENTER_BONUS[c] * (wp + 2)

    for ci, step in ((BLACK, -1), (WHITE, 1)):
        mask = 0
        rr = r + step
        while 0 <= rr < 8:
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < 8:
                    mask |= 1 << (rr * 8 + cc)
            rr += step
        PASSED_MASK[ci][sq] = mask

PASSED_BONUS = [0, 5, 15, 45, 110, 260, 650, 0]
FRONT_BONUS = [0, 0, 10, 30, 75, 170, 360, 0]

INF = 10**9
WIN = 100_000_000
THREAT_WIN = 900_000
THREAT_LOSS = 700_000

EXACT = 0
LOWER = 1
UPPER = 2

TT = {}
KILLERS = [[-1, -1] for _ in range(64)]
HISTORY = [[0] * 4096 for _ in range(2)]
DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


def _bits_from_list(pieces):
    b = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            b |= 1 << (r * 8 + c)
    return b


def _decode_move(m):
    fr = m >> 6
    to = m & 63
    return ((fr >> 3, fr & 7), (to >> 3, to & 7))


def _attack_map(bits, ci):
    if ci == WHITE:
        return (((bits & NOT_COL0) << 7) | ((bits & NOT_COL7) << 9)) & ALL_MASK
    return ((bits & NOT_COL0) >> 9) | ((bits & NOT_COL7) >> 7)


def _generate_moves(me, opp, ci):
    moves = []
    occ = me | opp
    b = me
    fwd = FWD[ci]
    diags = DIAGS[ci]
    masks = MASKS

    while b:
        lsb = b & -b
        fr = lsb.bit_length() - 1
        b ^= lsb

        to = fwd[fr]
        if to >= 0 and not (occ & masks[to]):
            moves.append((fr << 6) | to)

        for to in diags[fr]:
            if not (me & masks[to]):
                moves.append((fr << 6) | to)

    return moves


def _mobility_count(me, opp, ci):
    cnt = 0
    occ = me | opp
    b = me
    fwd = FWD[ci]
    diags = DIAGS[ci]
    masks = MASKS

    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb

        to = fwd[sq]
        if to >= 0 and not (occ & masks[to]):
            cnt += 1

        for to in diags[sq]:
            if not (me & masks[to]):
                cnt += 1

    return cnt


def _has_immediate_win(me, opp, ci):
    candidates = me & BEFORE_GOAL_MASK[ci]
    if not candidates:
        return False

    occ = me | opp
    b = candidates
    fwd = FWD[ci]
    diags = DIAGS[ci]
    masks = MASKS

    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb

        to = fwd[sq]
        if to >= 0 and not (occ & masks[to]):
            return True

        for to in diags[sq]:
            if not (me & masks[to]):
                return True

    return False


def _raw_score(me, opp, ci):
    if me == 0:
        return -WIN // 4

    oppci = OPP_CI[ci]
    score = me.bit_count() * 130

    my_attacks = _attack_map(me, ci)
    opp_attacks = _attack_map(opp, oppci)

    protected = me & my_attacks
    attacked = me & opp_attacks
    hanging = attacked & ~my_attacks
    targets = my_attacks & opp

    score += protected.bit_count() * 10
    score -= attacked.bit_count() * 18
    score -= hanging.bit_count() * 24

    t = targets
    while t:
        lsb = t & -t
        sq = lsb.bit_length() - 1
        t ^= lsb
        score += 28 + PROGRESS[oppci][sq] * 8

    front = 0
    b = me
    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb

        p = PROGRESS[ci][sq]
        if p > front:
            front = p

        score += ADV_VALUE[ci][sq]

        if not (opp & PASSED_MASK[ci][sq]):
            score += PASSED_BONUS[p]
            if p >= 5:
                score += 80 * (p - 4)

    score += FRONT_BONUS[front]
    score += _mobility_count(me, opp, ci) * 3

    return score


def _evaluate(me, opp, ci):
    oppci = OPP_CI[ci]

    if opp == 0 or (me & GOAL_MASK[ci]):
        return WIN // 2
    if me == 0 or (opp & GOAL_MASK[oppci]):
        return -WIN // 2

    if _has_immediate_win(me, opp, ci):
        return THREAT_WIN
    if _has_immediate_win(opp, me, oppci):
        return -THREAT_LOSS

    return _raw_score(me, opp, ci) - _raw_score(opp, me, oppci) + 5


def _move_sort_score(m, me, opp, ci, tt_move, ply, own_attacks, opp_attacks):
    fr = m >> 6
    to = m & 63
    tm = MASKS[to]

    score = HISTORY[ci][m]

    if m == tt_move:
        score += 10_000_000

    if ply < len(KILLERS):
        if m == KILLERS[ply][0]:
            score += 850_000
        elif m == KILLERS[ply][1]:
            score += 650_000

    if tm & GOAL_MASK[ci]:
        score += 5_000_000

    if opp & tm:
        oppci = OPP_CI[ci]
        score += 120_000 + PROGRESS[oppci][to] * 2_000

    score += (ADV_VALUE[ci][to] - ADV_VALUE[ci][fr]) * 8

    if own_attacks & tm:
        score += 600
    if opp_attacks & tm:
        score -= 700

    p = PROGRESS[ci][to]
    if not (opp & PASSED_MASK[ci][to]):
        score += PASSED_BONUS[p] * 5

    return score


def _ordered_moves(me, opp, ci, tt_move=None, ply=0):
    moves = _generate_moves(me, opp, ci)
    if len(moves) <= 1:
        return moves

    own_attacks = _attack_map(me, ci)
    opp_attacks = _attack_map(opp, OPP_CI[ci])

    moves.sort(
        key=lambda m: _move_sort_score(
            m, me, opp, ci, tt_move, ply, own_attacks, opp_attacks
        ),
        reverse=True,
    )
    return moves


def _negamax(me, opp, ci, depth, alpha, beta, ply):
    global NODES

    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()

    oppci = OPP_CI[ci]

    if opp & GOAL_MASK[oppci]:
        return -WIN - depth
    if me & GOAL_MASK[ci]:
        return WIN + depth
    if opp == 0:
        return WIN + depth
    if me == 0:
        return -WIN - depth

    if depth <= 0:
        return _evaluate(me, opp, ci)

    alpha_orig = alpha
    beta_orig = beta
    key = (me, opp, ci)
    tt_move = None

    entry = TT.get(key)
    if entry is not None:
        ent_depth, ent_val, ent_flag, ent_best = entry
        tt_move = ent_best
        if ent_depth >= depth:
            if ent_flag == EXACT:
                return ent_val
            if ent_flag == LOWER:
                alpha = max(alpha, ent_val)
            elif ent_flag == UPPER:
                beta = min(beta, ent_val)
            if alpha >= beta:
                return ent_val

    moves = _ordered_moves(me, opp, ci, tt_move, ply)
    if not moves:
        return -WIN // 3 - depth

    best_val = -INF
    best_move = moves[0]
    next_ci = oppci

    for m in moves:
        fr = m >> 6
        to = m & 63
        fm = MASKS[fr]
        tm = MASKS[to]
        capture = bool(opp & tm)

        new_me = (me & ~fm) | tm
        new_opp = opp & ~tm

        val = -_negamax(new_opp, new_me, next_ci, depth - 1, -beta, -alpha, ply + 1)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            if not capture and ply < len(KILLERS):
                if KILLERS[ply][0] != m:
                    KILLERS[ply][1] = KILLERS[ply][0]
                    KILLERS[ply][0] = m
                HISTORY[ci][m] += depth * depth
            break

    if best_val <= alpha_orig:
        flag = UPPER
    elif best_val >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best_val, flag, best_move)
    return best_val


def _search_root(me, opp, ci, depth, best_hint):
    if time.perf_counter() > DEADLINE:
        raise SearchTimeout()

    moves = _ordered_moves(me, opp, ci, best_hint, 0)
    if not moves:
        return None, -INF

    best_move = moves[0]
    best_score = -INF
    alpha = -INF
    beta = INF
    next_ci = OPP_CI[ci]

    for m in moves:
        if time.perf_counter() > DEADLINE:
            raise SearchTimeout()

        fr = m >> 6
        to = m & 63
        fm = MASKS[fr]
        tm = MASKS[to]

        new_me = (me & ~fm) | tm
        new_opp = opp & ~tm

        score = -_negamax(new_opp, new_me, next_ci, depth - 1, -beta, -alpha, 1)

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

        if best_score > WIN // 2:
            break

    return best_move, best_score


def _choose_fallback(me, opp, ci):
    moves = _ordered_moves(me, opp, ci, None, 0)
    if not moves:
        return None

    best = moves[0]
    best_val = -INF
    next_ci = OPP_CI[ci]

    for m in moves:
        fr = m >> 6
        to = m & 63
        fm = MASKS[fr]
        tm = MASKS[to]

        new_me = (me & ~fm) | tm
        new_opp = opp & ~tm

        if (tm & GOAL_MASK[ci]) or new_opp == 0:
            val = WIN
        else:
            val = -_evaluate(new_opp, new_me, next_ci)

        if val > best_val:
            best_val = val
            best = m

    return best


def _emergency_move(me_list, color):
    if me_list:
        r, c = me_list[0]
        dr = -1 if color == "b" else 1
        nr = max(0, min(7, r + dr))
        return ((r, c), (nr, c))
    return ((0, 0), (0, 0))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global TT, KILLERS, HISTORY, DEADLINE, NODES

    ci = COLOR_TO_CI.get(color, BLACK)

    me_bits = _bits_from_list(me)
    opp_bits = _bits_from_list(opp) & ~me_bits

    root_moves = _generate_moves(me_bits, opp_bits, ci)
    if not root_moves:
        return _emergency_move(me, color)

    # Always take an immediate goal-row win.
    for m in root_moves:
        if MASKS[m & 63] & GOAL_MASK[ci]:
            return _decode_move(m)

    # Also immediately take the last opposing piece if possible.
    for m in root_moves:
        to_mask = MASKS[m & 63]
        if (opp_bits & to_mask) and ((opp_bits & ~to_mask) == 0):
            return _decode_move(m)

    TT = {}
    KILLERS = [[-1, -1] for _ in range(64)]
    HISTORY = [[0] * 4096 for _ in range(2)]
    NODES = 0
    DEADLINE = time.perf_counter() + 0.86

    best_move = _choose_fallback(me_bits, opp_bits, ci)
    if best_move is None:
        best_move = root_moves[0]

    total_pieces = (me_bits | opp_bits).bit_count()
    if total_pieces > 26:
        max_depth = 5
    elif total_pieces > 20:
        max_depth = 6
    elif total_pieces > 14:
        max_depth = 7
    elif total_pieces > 8:
        max_depth = 9
    else:
        max_depth = 13

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > DEADLINE:
                break

            bm, score = _search_root(me_bits, opp_bits, ci, depth, best_move)
            if bm is not None:
                best_move = bm

            if score > WIN // 2:
                break

    except SearchTimeout:
        pass

    if best_move not in root_moves:
        best_move = root_moves[0]

    return _decode_move(best_move)
