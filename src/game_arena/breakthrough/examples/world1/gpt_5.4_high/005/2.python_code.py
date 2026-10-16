
from __future__ import annotations

import time

FULL = (1 << 64) - 1

FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_FILE_A = FULL ^ FILE_A
NOT_FILE_H = FULL ^ FILE_H

RANK_0 = 0x00000000000000FF
RANK_1 = 0x000000000000FF00
RANK_2 = 0x0000000000FF0000
RANK_5 = 0x0000FF0000000000
RANK_6 = 0x00FF000000000000
RANK_7 = 0xFF00000000000000

CENTER_COL = (0, 2, 4, 6, 6, 4, 2, 0)
PROGRESS = (0, 8, 18, 32, 50, 72, 98, 128)

WIN = 1_000_000
INF = 1_000_000_000

EXACT = 0
LOWER = 1
UPPER = 2

TT = {}
HISTORY = [0] * 4096
DEADLINE = 0.0
NODE_COUNT = 0


class _Timeout(Exception):
    pass


ROW = [sq >> 3 for sq in range(64)]
COL = [sq & 7 for sq in range(64)]
ADV_W = [ROW[sq] for sq in range(64)]
ADV_B = [7 - ROW[sq] for sq in range(64)]
SQVAL_W = [PROGRESS[ADV_W[sq]] + 3 * CENTER_COL[COL[sq]] for sq in range(64)]
SQVAL_B = [PROGRESS[ADV_B[sq]] + 3 * CENTER_COL[COL[sq]] for sq in range(64)]


def _build_cones():
    cone_w = [0] * 64
    cone_b = [0] * 64
    for sq in range(64):
        r = sq >> 3
        c = sq & 7

        mw = 0
        for rr in range(r + 1, 8):
            d = rr - r
            lo = max(0, c - d)
            hi = min(7, c + d)
            for cc in range(lo, hi + 1):
                mw |= 1 << (rr * 8 + cc)
        cone_w[sq] = mw

        mb = 0
        for rr in range(0, r):
            d = r - rr
            lo = max(0, c - d)
            hi = min(7, c + d)
            for cc in range(lo, hi + 1):
                mb |= 1 << (rr * 8 + cc)
        cone_b[sq] = mb
    return cone_w, cone_b


CONE_W, CONE_B = _build_cones()


def list_to_bb(pieces):
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def decode_move(mv):
    frm = mv >> 6
    to = mv & 63
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))


def apply_move(my, opp, mv):
    frm = mv >> 6
    to = mv & 63
    from_mask = 1 << frm
    to_mask = 1 << to
    my2 = (my ^ from_mask) | to_mask
    opp2 = opp & ~to_mask
    return my2, opp2


def attacks(bb, color):
    if color == 'w':
        return ((((bb & NOT_FILE_A) << 7) | ((bb & NOT_FILE_H) << 9)) & FULL)
    return (((bb & NOT_FILE_A) >> 9) | ((bb & NOT_FILE_H) >> 7))


def move_count(bb, opp, color):
    occ = bb | opp
    empty = FULL ^ occ
    not_my = FULL ^ bb
    if color == 'w':
        fwd = (((bb << 8) & FULL) & empty).bit_count()
        dl = ((((bb & NOT_FILE_A) << 7) & FULL) & not_my).bit_count()
        dr = ((((bb & NOT_FILE_H) << 9) & FULL) & not_my).bit_count()
        return fwd + dl + dr
    fwd = ((bb >> 8) & empty).bit_count()
    dl = (((bb & NOT_FILE_A) >> 9) & not_my).bit_count()
    dr = (((bb & NOT_FILE_H) >> 7) & not_my).bit_count()
    return fwd + dl + dr


def immediate_win_moves_count(bb, opp, color):
    occ = bb | opp
    empty = FULL ^ occ
    not_my = FULL ^ bb

    if color == 'w':
        p = bb & RANK_6
        if not p:
            return 0
        return (
            ((((p << 8) & FULL) & empty & RANK_7).bit_count()) +
            (((((p & NOT_FILE_A) << 7) & FULL) & not_my & RANK_7).bit_count()) +
            (((((p & NOT_FILE_H) << 9) & FULL) & not_my & RANK_7).bit_count())
        )

    p = bb & RANK_1
    if not p:
        return 0
    return (
        (((p >> 8) & empty & RANK_0).bit_count()) +
        ((((p & NOT_FILE_A) >> 9) & not_my & RANK_0).bit_count()) +
        ((((p & NOT_FILE_H) >> 7) & not_my & RANK_0).bit_count())
    )


def terminal_score(my, opp, color):
    if color == 'w':
        white = my
        black = opp
    else:
        white = opp
        black = my

    if (white & RANK_7) or black == 0:
        return WIN if color == 'w' else -WIN
    if (black & RANK_0) or white == 0:
        return WIN if color == 'b' else -WIN
    return None


def side_features(bb, opp, color):
    count = bb.bit_count()
    if count == 0:
        return -50_000

    opp_color = 'b' if color == 'w' else 'w'
    my_attacks = attacks(bb, color)
    def_mask = my_attacks & bb
    opp_attacks = attacks(opp, opp_color)
    attacked_mask = opp_attacks & bb

    defended = def_mask.bit_count()
    attacked = attacked_mask.bit_count()
    undefended_attacked = (attacked_mask & ~def_mask).bit_count()
    mobility = move_count(bb, opp, color)
    phalanx = (bb & ((((bb & NOT_FILE_H) << 1) & FULL))).bit_count()

    score = 120 * count
    score += 3 * mobility
    score += 10 * defended
    score -= 8 * attacked
    score -= 18 * undefended_attacked
    score += 7 * phalanx

    front = 0
    tmp = bb
    if color == 'w':
        sqvals = SQVAL_W
        advs = ADV_W
        cones = CONE_W
        prep_rank = RANK_5
    else:
        sqvals = SQVAL_B
        advs = ADV_B
        cones = CONE_B
        prep_rank = RANK_2

    while tmp:
        lsb = tmp & -tmp
        sq = lsb.bit_length() - 1
        tmp ^= lsb

        adv = advs[sq]
        score += sqvals[sq]
        if adv > front:
            front = adv

        if (opp & cones[sq]) == 0:
            score += 20 + 8 * adv
            if def_mask & lsb:
                score += 8

    score += 30 * front
    score += 15 * (bb & prep_rank).bit_count()
    return score


def evaluate(my, opp, color):
    opp_color = 'b' if color == 'w' else 'w'

    my_immediate = immediate_win_moves_count(my, opp, color)
    if my_immediate:
        return 250_000 + 1000 * my_immediate

    opp_immediate = immediate_win_moves_count(opp, my, opp_color)
    if opp_immediate:
        return -220_000 - 1000 * opp_immediate

    return side_features(my, opp, color) - side_features(opp, my, opp_color)


def gen_moves_ordered(my, opp, color, tt_move=-1):
    moves = []
    occ = my | opp
    empty = FULL ^ occ
    not_my = FULL ^ my
    opp_count = opp.bit_count()
    hist = HISTORY

    if color == 'w':
        dests = (((my << 8) & FULL) & empty)
        while dests:
            lsb = dests & -dests
            to = lsb.bit_length() - 1
            frm = to - 8
            mv = (frm << 6) | to
            row = to >> 3
            col = to & 7
            score = hist[mv] + row * 60 + CENTER_COL[col] * 12
            if mv == tt_move:
                score += 2_000_000
            if lsb & RANK_7:
                score += 1_500_000
            elif row == 6:
                score += 6_000
            elif row == 5:
                score += 1_500
            moves.append((score, mv))
            dests ^= lsb

        dests = ((((my & NOT_FILE_A) << 7) & FULL) & not_my)
        while dests:
            lsb = dests & -dests
            to = lsb.bit_length() - 1
            frm = to - 7
            mv = (frm << 6) | to
            row = to >> 3
            col = to & 7
            score = hist[mv] + row * 60 + CENTER_COL[col] * 12
            if mv == tt_move:
                score += 2_000_000
            if opp & lsb:
                score += 50_000
                if opp_count == 1:
                    score += 1_000_000
            if lsb & RANK_7:
                score += 1_500_000
            elif row == 6:
                score += 6_000
            elif row == 5:
                score += 1_500
            moves.append((score, mv))
            dests ^= lsb

        dests = ((((my & NOT_FILE_H) << 9) & FULL) & not_my)
        while dests:
            lsb = dests & -dests
            to = lsb.bit_length() - 1
            frm = to - 9
            mv = (frm << 6) | to
            row = to >> 3
            col = to & 7
            score = hist[mv] + row * 60 + CENTER_COL[col] * 12
            if mv == tt_move:
                score += 2_000_000
            if opp & lsb:
                score += 50_000
                if opp_count == 1:
                    score += 1_000_000
            if lsb & RANK_7:
                score += 1_500_000
            elif row == 6:
                score += 6_000
            elif row == 5:
                score += 1_500
            moves.append((score, mv))
            dests ^= lsb

    else:
        dests = ((my >> 8) & empty)
        while dests:
            lsb = dests & -dests
            to = lsb.bit_length() - 1
            frm = to + 8
            mv = (frm << 6) | to
            row = to >> 3
            col = to & 7
            adv = 7 - row
            score = hist[mv] + adv * 60 + CENTER_COL[col] * 12
            if mv == tt_move:
                score += 2_000_000
            if lsb & RANK_0:
                score += 1_500_000
            elif row == 1:
                score += 6_000
            elif row == 2:
                score += 1_500
            moves.append((score, mv))
            dests ^= lsb

        dests = (((my & NOT_FILE_A) >> 9) & not_my)
        while dests:
            lsb = dests & -dests
            to = lsb.bit_length() - 1
            frm = to + 9
            mv = (frm << 6) | to
            row = to >> 3
            col = to & 7
            adv = 7 - row
            score = hist[mv] + adv * 60 + CENTER_COL[col] * 12
            if mv == tt_move:
                score += 2_000_000
            if opp & lsb:
                score += 50_000
                if opp_count == 1:
                    score += 1_000_000
            if lsb & RANK_0:
                score += 1_500_000
            elif row == 1:
                score += 6_000
            elif row == 2:
                score += 1_500
            moves.append((score, mv))
            dests ^= lsb

        dests = (((my & NOT_FILE_H) >> 7) & not_my)
        while dests:
            lsb = dests & -dests
            to = lsb.bit_length() - 1
            frm = to + 7
            mv = (frm << 6) | to
            row = to >> 3
            col = to & 7
            adv = 7 - row
            score = hist[mv] + adv * 60 + CENTER_COL[col] * 12
            if mv == tt_move:
                score += 2_000_000
            if opp & lsb:
                score += 50_000
                if opp_count == 1:
                    score += 1_000_000
            if lsb & RANK_0:
                score += 1_500_000
            elif row == 1:
                score += 6_000
            elif row == 2:
                score += 1_500
            moves.append((score, mv))
            dests ^= lsb

    moves.sort(reverse=True)
    return [mv for _, mv in moves]


def negamax(my, opp, color, depth, alpha, beta):
    global NODE_COUNT

    NODE_COUNT += 1
    if (NODE_COUNT & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise _Timeout

    term = terminal_score(my, opp, color)
    if term is not None:
        return term

    if depth <= 0:
        return evaluate(my, opp, color)

    key = (my, opp, 0 if color == 'w' else 1)
    entry = TT.get(key)
    alpha_orig = alpha
    beta_orig = beta
    tt_move = -1

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

    moves = gen_moves_ordered(my, opp, color, tt_move)
    if not moves:
        return -WIN

    best = -INF
    best_move = moves[0]
    opp_color = 'b' if color == 'w' else 'w'

    for mv in moves:
        my2, opp2 = apply_move(my, opp, mv)
        score = -negamax(opp2, my2, opp_color, depth - 1, -beta, -alpha)

        if score > best:
            best = score
            best_move = mv
        if score > alpha:
            alpha = score
        if alpha >= beta:
            HISTORY[mv] += depth * depth
            break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT
    TT[key] = (depth, flag, best, best_move)
    return best


def root_search(my, opp, color, depth):
    key = (my, opp, 0 if color == 'w' else 1)
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else -1
    moves = gen_moves_ordered(my, opp, color, tt_move)

    best_score = -INF
    best_move = moves[0]
    alpha = -INF
    beta = INF
    opp_color = 'b' if color == 'w' else 'w'

    for mv in moves:
        if time.perf_counter() >= DEADLINE:
            raise _Timeout
        my2, opp2 = apply_move(my, opp, mv)
        score = -negamax(opp2, my2, opp_color, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    TT[key] = (depth, EXACT, best_score, best_move)
    return best_score, best_move


def is_legal_encoded(mv, my, opp, color):
    frm = mv >> 6
    to = mv & 63
    from_mask = 1 << frm
    to_mask = 1 << to

    if (my & from_mask) == 0:
        return False
    if my & to_mask:
        return False

    fr = frm >> 3
    fc = frm & 7
    tr = to >> 3
    tc = to & 7

    step = 1 if color == 'w' else -1
    if tr - fr != step:
        return False
    if abs(tc - fc) > 1:
        return False

    if tc == fc:
        return (opp & to_mask) == 0
    return True


def brute_force_legal(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    step = 1 if color == 'w' else -1

    out = []
    for r, c in me:
        nr = r + step
        if not (0 <= nr < 8):
            continue

        if (nr, c) not in me_set and (nr, c) not in opp_set:
            out.append(((r, c), (nr, c)))

        nc = c - 1
        if 0 <= nc < 8 and (nr, nc) not in me_set:
            out.append(((r, c), (nr, nc)))

        nc = c + 1
        if 0 <= nc < 8 and (nr, nc) not in me_set:
            out.append(((r, c), (nr, nc)))

    return out


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global TT, HISTORY, DEADLINE, NODE_COUNT

    my = list_to_bb(me)
    op = list_to_bb(opp)

    TT = {}
    HISTORY = [0] * 4096
    NODE_COUNT = 0
    DEADLINE = time.perf_counter() + 0.93

    moves = gen_moves_ordered(my, op, color, -1)
    if not moves:
        brute = brute_force_legal(me, opp, color)
        if brute:
            return brute[0]
        p = me[0] if me else (0, 0)
        return (p, p)

    opp_color = 'b' if color == 'w' else 'w'

    # Immediate win if available.
    for mv in moves:
        my2, op2 = apply_move(my, op, mv)
        term = terminal_score(op2, my2, opp_color)
        if term == -WIN:
            move = decode_move(mv)
            if is_legal_encoded(mv, my, op, color):
                return move

    # Safe shallow fallback (effectively a depth-1 search).
    best_move = moves[0]
    best_score = -INF
    for mv in moves:
        my2, op2 = apply_move(my, op, mv)
        term = terminal_score(op2, my2, opp_color)
        score = -term if term is not None else -evaluate(op2, my2, opp_color)
        if score > best_score:
            best_score = score
            best_move = mv

    TT[(my, op, 0 if color == 'w' else 1)] = (1, EXACT, best_score, best_move)
    last_best = best_move

    total_pieces = my.bit_count() + op.bit_count()
    if total_pieces > 24:
        max_depth = 6
    elif total_pieces > 16:
        max_depth = 8
    elif total_pieces > 8:
        max_depth = 10
    else:
        max_depth = 12

    depth = 2
    while depth <= max_depth:
        try:
            score, mv = root_search(my, op, color, depth)
            if is_legal_encoded(mv, my, op, color):
                last_best = mv
            if abs(score) >= WIN:
                break
            depth += 1
        except _Timeout:
            break

    if is_legal_encoded(last_best, my, op, color):
        return decode_move(last_best)

    brute = brute_force_legal(me, opp, color)
    if brute:
        return brute[0]

    p = me[0] if me else (0, 0)
    return (p, p)
