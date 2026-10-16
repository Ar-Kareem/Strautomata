
import time
import random

WIN = 100000
INF = 10 ** 9
TIME_LIMIT = 0.65
QDEPTH = 4
MAXPLY = 128
MAXDEPTH = 40

GOAL = [0, 7, 0]
PENULT = [0, 6, 1]
ADV = [0, 2, 4, 7, 11, 17, 26, 0]
RUN = [0, 260, 210, 170, 140, 115, 100, 90]

FWD = [None, [-1] * 64, [-1] * 64]
DIAG = [None, [[] for _ in range(64)], [[] for _ in range(64)]]
ATT = [None, [[] for _ in range(64)], [[] for _ in range(64)]]
for _sq in range(64):
    _r, _c = divmod(_sq, 8)
    if _r < 7:
        FWD[1][_sq] = _sq + 8
        if _c > 0:
            DIAG[1][_sq].append(_sq + 7)
        if _c < 7:
            DIAG[1][_sq].append(_sq + 9)
    if _r > 0:
        FWD[2][_sq] = _sq - 8
        if _c > 0:
            DIAG[2][_sq].append(_sq - 9)
        if _c < 7:
            DIAG[2][_sq].append(_sq - 7)
for _s in (1, 2):
    for _sq in range(64):
        for _t in DIAG[_s][_sq]:
            ATT[_s][_t].append(_sq)

_rng = random.Random(20240607)
Z = [None, [_rng.getrandbits(64) for _ in range(64)], [_rng.getrandbits(64) for _ in range(64)]]
ZSIDE = _rng.getrandbits(64)


class Timeout(Exception):
    pass


_deadline = 0.0
_nodes = 0
_TT = {}
_cnt = [0, 0, 0]
_HIST = [None, [0] * 4096, [0] * 4096]
_KILL = [[None, None] for _ in range(MAXPLY + 2)]


def _gen_moves(board, side):
    moves = []
    fwd = FWD[side]
    dg = DIAG[side]
    for sq in range(64):
        if board[sq] == side:
            t = fwd[sq]
            if t >= 0 and board[t] == 0:
                moves.append((sq, t))
            for t in dg[sq]:
                if board[t] != side:
                    moves.append((sq, t))
    return moves


def _can_win_now(board, side):
    base = PENULT[side] * 8
    for sq in range(base, base + 8):
        if board[sq] == side:
            return True
    return False


def _threats(board, side):
    opp = 3 - side
    base = PENULT[opp] * 8
    return [sq for sq in range(base, base + 8) if board[sq] == opp]


def _evaluate(board, side):
    whites = []
    blacks = []
    for sq in range(64):
        v = board[sq]
        if v == 1:
            whites.append(sq)
        elif v == 2:
            blacks.append(sq)
    score = 0
    wrun = 99
    brun = 99
    wmin = 99
    bmin = 99
    A1 = ATT[1]
    A2 = ATT[2]
    for sq in whites:
        r = sq >> 3
        c = sq & 7
        v = 100 + ADV[r]
        att = False
        for s in A2[sq]:
            if board[s] == 2:
                att = True
                break
        if att:
            dfd = False
            for s in A1[sq]:
                if board[s] == 1:
                    dfd = True
                    break
            if dfd:
                v -= 6
            else:
                v -= 20 if side == 1 else 45
        d = 7 - r
        if d < wmin:
            wmin = d
        run = True
        for b in blacks:
            br = b >> 3
            if br > r:
                dc = (b & 7) - c
                if dc < 0:
                    dc = -dc
                if dc <= br - r:
                    run = False
                    break
        if run:
            if d < wrun:
                wrun = d
            v += RUN[d]
        if r == 0:
            v += 4
        score += v
    for sq in blacks:
        r = sq >> 3
        c = sq & 7
        v = 100 + ADV[7 - r]
        att = False
        for s in A1[sq]:
            if board[s] == 1:
                att = True
                break
        if att:
            dfd = False
            for s in A2[sq]:
                if board[s] == 2:
                    dfd = True
                    break
            if dfd:
                v -= 6
            else:
                v -= 20 if side == 2 else 45
        d = r
        if d < bmin:
            bmin = d
        run = True
        for w in whites:
            wr = w >> 3
            if wr < r:
                dc = (w & 7) - c
                if dc < 0:
                    dc = -dc
                if dc <= r - wr:
                    run = False
                    break
        if run:
            if d < brun:
                brun = d
            v += RUN[d]
        if r == 7:
            v += 4
        score -= v
    if wrun < 99:
        if (side == 1 and wrun <= bmin) or (side == 2 and wrun < bmin):
            score += 2000
    if brun < 99:
        if (side == 2 and brun <= wmin) or (side == 1 and brun < wmin):
            score -= 2000
    return score if side == 1 else -score


def _quiesce(board, side, alpha, beta, ply, qd):
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.time() > _deadline:
        raise Timeout()
    if _can_win_now(board, side):
        return WIN - ply - 1
    opp = 3 - side
    thr = _threats(board, side)
    if thr:
        if len(thr) > 1:
            return -WIN + ply + 2
        t = thr[0]
        best = -INF
        for s in ATT[side][t]:
            if board[s] == side:
                board[t] = side
                board[s] = 0
                _cnt[opp] -= 1
                if _cnt[opp] == 0:
                    sc = WIN - ply - 1
                else:
                    sc = -_quiesce(board, opp, -beta, -alpha, ply + 1, qd)
                board[s] = side
                board[t] = opp
                _cnt[opp] += 1
                if sc > best:
                    best = sc
                if sc > alpha:
                    alpha = sc
                if alpha >= beta:
                    break
        if best == -INF:
            return -WIN + ply + 2
        return best
    stand = _evaluate(board, side)
    if qd <= 0 or stand >= beta:
        return stand
    if stand > alpha:
        alpha = stand
    best = stand
    dg = DIAG[side]
    goal = GOAL[side]
    for sq in range(64):
        if board[sq] == side:
            for t in dg[sq]:
                if board[t] == opp:
                    board[t] = side
                    board[sq] = 0
                    _cnt[opp] -= 1
                    if _cnt[opp] == 0 or (t >> 3) == goal:
                        sc = WIN - ply - 1
                    else:
                        sc = -_quiesce(board, opp, -beta, -alpha, ply + 1, qd - 1)
                    board[sq] = side
                    board[t] = opp
                    _cnt[opp] += 1
                    if sc > best:
                        best = sc
                    if sc > alpha:
                        alpha = sc
                    if alpha >= beta:
                        return best
    return best


def _negamax(board, side, depth, alpha, beta, ply, h):
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.time() > _deadline:
        raise Timeout()
    if _can_win_now(board, side):
        return WIN - ply - 1
    opp = 3 - side
    thr = _threats(board, side)
    nthr = len(thr)
    if nthr > 1:
        return -WIN + ply + 2
    if depth <= 0 and nthr == 0:
        return _quiesce(board, side, alpha, beta, ply, QDEPTH)
    alpha0 = alpha
    ttmove = None
    e = _TT.get(h)
    if e is not None:
        tdepth, tscore, tflag, ttmove = e
        if tdepth >= depth:
            if tscore > WIN - 1000:
                tscore -= ply
            elif tscore < -WIN + 1000:
                tscore += ply
            if tflag == 0:
                return tscore
            if tflag == 1:
                if tscore >= beta:
                    return tscore
                if tscore > alpha:
                    alpha = tscore
            else:
                if tscore <= alpha:
                    return tscore
                if tscore < beta:
                    beta = tscore
    if nthr == 1:
        t = thr[0]
        moves = [(s, t) for s in ATT[side][t] if board[s] == side]
        if not moves:
            return -WIN + ply + 2
    else:
        moves = _gen_moves(board, side)
        if not moves:
            return _evaluate(board, side)
    if len(moves) > 1:
        hist = _HIST[side]
        k = _KILL[ply]
        k1 = k[0]
        k2 = k[1]
        keyed = []
        aopp = ATT[opp]
        for m in moves:
            frm, to = m
            if m == ttmove:
                s = 10000000
            else:
                cap = board[to]
                if cap:
                    tr = to >> 3
                    adv = (7 - tr) if side == 1 else tr
                    s = 500000 + 1000 * adv
                    for a in aopp[to]:
                        if board[a] == opp:
                            s -= 400
                            break
                elif m == k1 or m == k2:
                    s = 400000
                else:
                    tr = to >> 3
                    s = hist[frm * 64 + to] + (tr if side == 1 else 7 - tr) * 4
            keyed.append((s, m))
        keyed.sort(reverse=True)
        moves = [m for _, m in keyed]
    best = -INF
    bestm = moves[0]
    goal = GOAL[side]
    zs = Z[side]
    for m in moves:
        frm, to = m
        cap = board[to]
        board[to] = side
        board[frm] = 0
        nh = h ^ zs[frm] ^ zs[to] ^ ZSIDE
        if cap:
            nh ^= Z[cap][to]
            _cnt[cap] -= 1
            if _cnt[cap] == 0 or (to >> 3) == goal:
                sc = WIN - ply - 1
            else:
                sc = -_negamax(board, opp, depth - 1, -beta, -alpha, ply + 1, nh)
            _cnt[cap] += 1
        else:
            if (to >> 3) == goal:
                sc = WIN - ply - 1
            else:
                sc = -_negamax(board, opp, depth - 1, -beta, -alpha, ply + 1, nh)
        board[frm] = side
        board[to] = cap
        if sc > best:
            best = sc
            bestm = m
            if sc > alpha:
                alpha = sc
                if alpha >= beta:
                    if not cap:
                        k = _KILL[ply]
                        if k[0] != m:
                            k[1] = k[0]
                            k[0] = m
                        _HIST[side][frm * 64 + to] += depth * depth
                    break
    st = best
    if st > WIN - 1000:
        st += ply
    elif st < -WIN + 1000:
        st -= ply
    if best <= alpha0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _TT[h] = (max(depth, 0), st, flag, bestm)
    return best


def _conv(m):
    frm, to = m
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))


def policy(me, opp, color):
    global _deadline, _nodes, _TT, _HIST, _KILL
    start = time.time()
    _deadline = start + TIME_LIMIT
    _nodes = 0
    _TT = {}
    _HIST = [None, [0] * 4096, [0] * 4096]
    _KILL = [[None, None] for _ in range(MAXPLY + 2)]

    side = 1 if color == 'w' else 2
    o = 3 - side
    board = [0] * 64
    for r, c in me:
        board[r * 8 + c] = side
    for r, c in opp:
        board[r * 8 + c] = o
    _cnt[side] = len(me)
    _cnt[o] = len(opp)

    moves = _gen_moves(board, side)
    if not moves:
        if me:
            return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))
        return ((0, 0), (0, 0))
    goal = GOAL[side]
    for m in moves:
        if (m[1] >> 3) == goal:
            return _conv(m)
    legal_set = set(moves)

    thr = _threats(board, side)
    if len(thr) == 1:
        caps = [m for m in moves if m[1] == thr[0]]
        if caps:
            moves = caps

    # static ordering
    def skey(m):
        frm, to = m
        cap = board[to]
        tr = to >> 3
        adv = tr if side == 1 else 7 - tr
        s = adv * 4
        if cap:
            s += 500000 + 1000 * ((7 - tr) if side == 1 else tr)
            for a in ATT[o][to]:
                if board[a] == o:
                    s -= 400
                    break
        return -s

    order = sorted(moves, key=skey)
    best_move = order[0]

    h = 0
    for sq in range(64):
        v = board[sq]
        if v:
            h ^= Z[v][sq]
    if side == 2:
        h ^= ZSIDE

    root_scores = {m: 0 for m in order}
    cur_best = None
    zs = Z[side]
    try:
        depth = 1
        while depth <= MAXDEPTH:
            alpha = -INF
            beta = INF
            cur_best = None
            cur_score = -INF
            for m in order:
                frm, to = m
                cap = board[to]
                board[to] = side
                board[frm] = 0
                nh = h ^ zs[frm] ^ zs[to] ^ ZSIDE
                if cap:
                    nh ^= Z[cap][to]
                    _cnt[cap] -= 1
                if (cap and _cnt[cap] == 0) or (to >> 3) == goal:
                    sc = WIN - 1
                else:
                    try:
                        sc = -_negamax(board, o, depth - 1, -beta, -alpha, 1, nh)
                    except Timeout:
                        raise
                board[frm] = side
                board[to] = cap
                if cap:
                    _cnt[cap] += 1
                root_scores[m] = sc
                if sc > cur_score:
                    cur_score = sc
                    cur_best = m
                if sc > alpha:
                    alpha = sc
            best_move = cur_best
            order.sort(key=lambda mm: -root_scores[mm])
            if cur_score > WIN - 1000 or cur_score < -WIN + 1000:
                break
            if time.time() - start > TIME_LIMIT * 0.6:
                break
            depth += 1
    except Timeout:
        if cur_best is not None:
            best_move = cur_best
    except Exception:
        pass

    if best_move not in legal_set:
        best_move = order[0] if order[0] in legal_set else next(iter(legal_set))
    return _conv(best_move)
