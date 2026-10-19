
import time

WIN = 100000
INF = 10 ** 9
FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H
ROWS = [0xFF << (8 * r) for r in range(8)]

try:
    (0).bit_count()
    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')

BONUS = [0, 2, 5, 9, 15, 25, 45, 0]
FREE_BONUS = [1, 3, 7, 15, 30, 60, 0, 0]

CONE_UP = [0] * 64
CONE_DOWN = [0] * 64
for _sq in range(64):
    _r, _c = divmod(_sq, 8)
    _m = 0
    for _r2 in range(_r + 1, 8):
        _d = _r2 - _r
        for _c2 in range(max(0, _c - _d), min(7, _c + _d) + 1):
            _m |= 1 << (_r2 * 8 + _c2)
    CONE_UP[_sq] = _m
    _m = 0
    for _r2 in range(0, _r):
        _d = _r - _r2
        for _c2 in range(max(0, _c - _d), min(7, _c + _d) + 1):
            _m |= 1 << (_r2 * 8 + _c2)
    CONE_DOWN[_sq] = _m


class TimeUp(Exception):
    pass


TT = {}
KILLERS = [None] * 128
HISTORY = {}
nodes = 0
deadline = 0.0
current_best = None


def attacks(bb, up):
    if up:
        return (((bb & NOT_A) << 7) | ((bb & NOT_H) << 9)) & FULL
    else:
        return ((bb & NOT_A) >> 9) | ((bb & NOT_H) >> 7)


def gen_moves(me, opp, up):
    empty = FULL ^ (me | opp)
    notme = FULL ^ me
    moves = []
    if up:
        t = (me << 8) & empty
        while t:
            b = t & -t
            t ^= b
            i = b.bit_length() - 1
            moves.append((i - 8, i, 0))
        t = ((me & NOT_A) << 7) & notme
        while t:
            b = t & -t
            t ^= b
            i = b.bit_length() - 1
            moves.append((i - 7, i, 1 if (b & opp) else 0))
        t = ((me & NOT_H) << 9) & notme
        while t:
            b = t & -t
            t ^= b
            i = b.bit_length() - 1
            moves.append((i - 9, i, 1 if (b & opp) else 0))
    else:
        t = (me >> 8) & empty
        while t:
            b = t & -t
            t ^= b
            i = b.bit_length() - 1
            moves.append((i + 8, i, 0))
        t = ((me & NOT_A) >> 9) & notme
        while t:
            b = t & -t
            t ^= b
            i = b.bit_length() - 1
            moves.append((i + 9, i, 1 if (b & opp) else 0))
        t = ((me & NOT_H) >> 7) & notme
        while t:
            b = t & -t
            t ^= b
            i = b.bit_length() - 1
            moves.append((i + 7, i, 1 if (b & opp) else 0))
    return moves


def evaluate(me, opp, up, ply):
    my_att = attacks(me, up)
    opp_att = attacks(opp, not up)
    if up:
        if me & ROWS[6]:
            return WIN - ply - 1
        danger = opp & ROWS[1]
        home_me = ROWS[0]
        home_opp = ROWS[7]
    else:
        if me & ROWS[1]:
            return WIN - ply - 1
        danger = opp & ROWS[6]
        home_me = ROWS[7]
        home_opp = ROWS[0]
    if danger:
        if (danger & (danger - 1)) or not (danger & my_att):
            return -WIN + ply + 2
    score = 0
    for r in range(8):
        c1 = popcount(me & ROWS[r])
        c2 = popcount(opp & ROWS[r])
        if up:
            rm = r
            ro = 7 - r
        else:
            rm = 7 - r
            ro = r
        score += c1 * (100 + BONUS[rm]) - c2 * (100 + BONUS[ro])
    score -= 25 * popcount(me & opp_att & ~my_att)
    score += 35 * popcount(opp & my_att & ~opp_att)
    score -= 4 * popcount(me & opp_att & my_att)
    score += 4 * popcount(opp & my_att & opp_att)
    # free runners
    b = me
    cone_me = CONE_UP if up else CONE_DOWN
    cone_opp = CONE_DOWN if up else CONE_UP
    while b:
        x = b & -b
        b ^= x
        sq = x.bit_length() - 1
        r = sq >> 3
        rel = r if up else 7 - r
        if not (opp & cone_me[sq]):
            score += FREE_BONUS[rel]
    b = opp
    while b:
        x = b & -b
        b ^= x
        sq = x.bit_length() - 1
        r = sq >> 3
        rel = 7 - r if up else r
        if not (me & cone_opp[sq]):
            score -= FREE_BONUS[rel]
    score += 4 * popcount(me & home_me) - 4 * popcount(opp & home_opp)
    return score


def quiesce(me, opp, up, alpha, beta, ply, qd):
    global nodes
    nodes += 1
    if (nodes & 255) == 0 and time.time() > deadline:
        raise TimeUp()
    stand = evaluate(me, opp, up, ply)
    if qd >= 3 or stand >= beta or stand <= -WIN + 200 or stand >= WIN - 200:
        return stand
    if stand > alpha:
        alpha = stand
    moves = gen_moves(me, opp, up)
    goal_mask = ROWS[7] if up else ROWS[0]
    near_mask = ROWS[6] if up else ROWS[1]
    cand = []
    for mv in moves:
        f, t, cap = mv
        tb = 1 << t
        if tb & goal_mask:
            return WIN - ply
        if cap:
            if (opp & ~tb) == 0:
                return WIN - ply
            rel = (t >> 3) if up else 7 - (t >> 3)
            cand.append((20000 + (7 - rel) * 10, mv))
        elif tb & near_mask:
            cand.append((100, mv))
    cand.sort(reverse=True)
    best = stand
    for _, mv in cand:
        f, t, cap = mv
        tb = 1 << t
        nme = (me ^ (1 << f)) | tb
        nopp = opp & ~tb
        v = -quiesce(nopp, nme, not up, -beta, -alpha, ply + 1, qd + 1)
        if v > best:
            best = v
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    return best


def negamax(me, opp, up, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 255) == 0 and time.time() > deadline:
        raise TimeUp()
    if depth <= 0:
        return quiesce(me, opp, up, alpha, beta, ply, 0)
    key = (me, opp, up)
    entry = TT.get(key)
    tt_move = None
    if entry is not None:
        edepth, evalue, eflag, emove = entry
        if edepth >= depth:
            if eflag == 0:
                return evalue
            if eflag == 1 and evalue >= beta:
                return evalue
            if eflag == 2 and evalue <= alpha:
                return evalue
        tt_move = emove
    moves = gen_moves(me, opp, up)
    if not moves:
        return evaluate(me, opp, up, ply)
    goal_mask = ROWS[7] if up else ROWS[0]
    killer = KILLERS[ply]
    scored = []
    for mv in moves:
        f, t, cap = mv
        tb = 1 << t
        if tb & goal_mask:
            return WIN - ply
        if cap and (opp & ~tb) == 0:
            return WIN - ply
        rel = (t >> 3) if up else 7 - (t >> 3)
        if mv == tt_move:
            s = 1000000
        elif cap:
            s = 20000 + (7 - rel) * 10
        elif mv == killer:
            s = 15000
        else:
            s = rel * 10 + HISTORY.get(f * 64 + t, 0)
        scored.append((s, mv))
    scored.sort(reverse=True)
    best = -INF
    best_move = None
    a = alpha
    for _, mv in scored:
        f, t, cap = mv
        tb = 1 << t
        nme = (me ^ (1 << f)) | tb
        nopp = opp & ~tb
        v = -negamax(nopp, nme, not up, depth - 1, -beta, -a, ply + 1)
        if v > best:
            best = v
            best_move = mv
        if v > a:
            a = v
        if a >= beta:
            KILLERS[ply] = mv
            if not cap:
                k = f * 64 + t
                HISTORY[k] = HISTORY.get(k, 0) + depth * depth
            break
    if best <= alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best, flag, best_move)
    return best


def search_root(me, opp, up, ordered, depth):
    global current_best
    alpha = -INF
    best = None
    results = []
    goal_mask = ROWS[7] if up else ROWS[0]
    for mv in ordered:
        f, t, cap = mv
        tb = 1 << t
        nme = (me ^ (1 << f)) | tb
        nopp = opp & ~tb
        if (tb & goal_mask) or nopp == 0:
            current_best = mv
            return WIN, mv, [(WIN, mv)] + results
        v = -negamax(nopp, nme, not up, depth - 1, -INF, -alpha, 1)
        results.append((v, mv))
        if v > alpha:
            alpha = v
            best = mv
            current_best = mv
    results.sort(key=lambda x: x[0], reverse=True)
    return alpha, best, results


def heuristic_fallback(me, opp, up, moves):
    goal_mask = ROWS[7] if up else ROWS[0]
    best = None
    best_s = -INF
    opp_att = attacks(opp, not up)
    for mv in moves:
        f, t, cap = mv
        tb = 1 << t
        s = 0
        if tb & goal_mask:
            return mv
        rel = (t >> 3) if up else 7 - (t >> 3)
        if cap:
            s += 100 + (7 - rel) * 10
        s += rel * 3
        if tb & opp_att:
            s -= 40
        if s > best_s:
            best_s = s
            best = mv
    return best


def policy(me, opp, color):
    global deadline, nodes, current_best, TT, HISTORY, KILLERS
    start = time.time()
    up = (color == 'w')
    me_bb = 0
    for r, c in me:
        me_bb |= 1 << (r * 8 + c)
    opp_bb = 0
    for r, c in opp:
        opp_bb |= 1 << (r * 8 + c)
    moves = gen_moves(me_bb, opp_bb, up)
    if not moves:
        # No legal moves (should not happen); return something
        r, c = me[0]
        return ((r, c), (r + (1 if up else -1), c))
    try:
        fallback = heuristic_fallback(me_bb, opp_bb, up, moves)
    except Exception:
        fallback = moves[0]
    best_move = fallback
    deadline = start + 0.6
    nodes = 0
    TT = {}
    HISTORY = {}
    KILLERS = [None] * 128
    current_best = None
    ordered = list(moves)
    # initial ordering: captures / advancement
    def init_key(mv):
        f, t, cap = mv
        rel = (t >> 3) if up else 7 - (t >> 3)
        return (20000 + (7 - rel) * 10) if cap else rel * 10
    ordered.sort(key=init_key, reverse=True)
    try:
        depth = 1
        while depth < 40:
            current_best = None
            val, mv, results = search_root(me_bb, opp_bb, up, ordered, depth)
            if mv is not None:
                best_move = mv
            ordered = [m for _, m in results]
            if val >= WIN - 200 or val <= -WIN + 200:
                break
            if time.time() - start > 0.3:
                break
            depth += 1
    except TimeUp:
        if current_best is not None:
            best_move = current_best
    except Exception:
        pass
    # validate
    legal = set((f, t) for f, t, _ in moves)
    if best_move is None or (best_move[0], best_move[1]) not in legal:
        best_move = fallback if fallback is not None else moves[0]
    f, t = best_move[0], best_move[1]
    return ((f >> 3, f & 7), (t >> 3, t & 7))
