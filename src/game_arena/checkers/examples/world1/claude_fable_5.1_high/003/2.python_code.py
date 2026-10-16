
import time

INF = 10 ** 9
MATE = 100000
TIME_BUDGET = 0.75

FWD = {1: 1, -1: -1}
PROMO = {1: 7, -1: 0}
PST = {}
DIRS_ALL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
MAN_DIRS = {1: ((1, -1), (1, 1)), -1: ((-1, -1), (-1, 1))}


class Timeout(Exception):
    pass


_nodes = 0
_deadline = 0.0
_killers = [None] * 128
LAST = {'boards': None, 'to': -1, 'dead': ()}


def setup(color):
    myf = -1 if color == 'b' else 1
    FWD[1] = myf
    FWD[-1] = -myf
    PROMO[1] = 0 if myf == -1 else 7
    PROMO[-1] = 7 if myf == -1 else 0
    for side in (1, -1):
        f = FWD[side]
        man = [0] * 64
        king = [0] * 64
        for sq in range(64):
            r = sq >> 3
            c = sq & 7
            adv = r if f == 1 else 7 - r
            v = 100 + adv * 3
            if adv >= 5:
                v += (adv - 4) * 4
            if adv == 0:
                v += 6
            if 2 <= c <= 5 and 2 <= r <= 5:
                v += 3
            man[sq] = v
            kv = 160
            if c == 0 or c == 7 or r == 0 or r == 7:
                kv -= 6
            if 2 <= c <= 5 and 2 <= r <= 5:
                kv += 4
            king[sq] = kv
        PST[side] = man
        PST[2 * side] = king


def build_board(my_men, my_kings, opp_men, opp_kings):
    b = [0] * 64
    for r, c in my_men:
        b[r * 8 + c] = 1
    for r, c in my_kings:
        b[r * 8 + c] = 2
    for r, c in opp_men:
        b[r * 8 + c] = -1
    for r, c in opp_kings:
        b[r * 8 + c] = -2
    return b


def _jumps(board, side, sq, is_king, dirs, path, caps, out, promo):
    found = False
    r = sq >> 3
    c = sq & 7
    for dr, dc in dirs:
        r2 = r + 2 * dr
        c2 = c + 2 * dc
        if 0 <= r2 < 8 and 0 <= c2 < 8:
            m = (r + dr) * 8 + (c + dc)
            t = r2 * 8 + c2
            q = board[m]
            if q != 0 and q * side < 0 and m not in caps and board[t] == 0:
                found = True
                npath = path + (t,)
                ncaps = caps + (m,)
                if (not is_king) and r2 == promo:
                    out.append((npath, ncaps))
                else:
                    _jumps(board, side, t, is_king, dirs, npath, ncaps, out, promo)
    if not found and len(caps) > 0 and len(path) > 1:
        out.append((path, caps))


def gen_moves(board, side):
    fwd = FWD[side]
    promo = PROMO[side]
    mdirs = MAN_DIRS[fwd]
    caps = []
    quiet = []
    for sq in range(64):
        p = board[sq]
        if p == 0 or p * side < 0:
            continue
        if p == side:
            dirs = mdirs
            is_king = False
        else:
            dirs = DIRS_ALL
            is_king = True
        board[sq] = 0
        _jumps(board, side, sq, is_king, dirs, (sq,), (), caps, promo)
        board[sq] = p
        if not caps:
            r = sq >> 3
            c = sq & 7
            for dr, dc in dirs:
                r1 = r + dr
                c1 = c + dc
                if 0 <= r1 < 8 and 0 <= c1 < 8 and board[r1 * 8 + c1] == 0:
                    quiet.append(((sq, r1 * 8 + c1), ()))
    return caps if caps else quiet


def apply(board, mv, side):
    path, caps = mv
    b = board[:]
    p = b[path[0]]
    b[path[0]] = 0
    for m in caps:
        b[m] = 0
    dest = path[-1]
    if p == side and (dest >> 3) == PROMO[side]:
        p = 2 * side
    b[dest] = p
    return b


def evaluate(board, side):
    my = 0
    op = 0
    mymat = 0
    opmat = 0
    my_k = []
    op_k = []
    my_sqs = []
    op_sqs = []
    for sq in range(64):
        p = board[sq]
        if p == 0:
            continue
        if p > 0:
            my += PST[p][sq]
            my_sqs.append(sq)
            if p == 1:
                mymat += 100
            else:
                mymat += 160
                my_k.append(sq)
        else:
            op += PST[p][sq]
            op_sqs.append(sq)
            if p == -1:
                opmat += 100
            else:
                opmat += 160
                op_k.append(sq)
    total = len(my_sqs) + len(op_sqs)
    if total == 0:
        return 0
    score = my - op
    score += (mymat - opmat) * 6 // total
    if total <= 8:
        if mymat > opmat and my_k and op_sqs:
            for k in my_k:
                kr = k >> 3
                kc = k & 7
                d = 8
                for s in op_sqs:
                    dd = max(abs(kr - (s >> 3)), abs(kc - (s & 7)))
                    if dd < d:
                        d = dd
                score -= 4 * d
        elif opmat > mymat and op_k and my_sqs:
            for k in op_k:
                kr = k >> 3
                kc = k & 7
                d = 8
                for s in my_sqs:
                    dd = max(abs(kr - (s >> 3)), abs(kc - (s & 7)))
                    if dd < d:
                        d = dd
                score += 4 * d
    return score * side


def search(board, side, depth, alpha, beta, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.time() > _deadline:
        raise Timeout()
    moves = gen_moves(board, side)
    if not moves:
        return -MATE + ply
    if moves[0][1]:
        if ply >= 60:
            return evaluate(board, side)
    else:
        if depth <= 0:
            return evaluate(board, side)
        k = _killers[ply] if ply < 128 else None
        if k is not None and k in moves:
            moves.remove(k)
            moves.insert(0, k)
    best = -INF
    for mv in moves:
        sc = -search(apply(board, mv, side), -side, depth - 1, -beta, -alpha, ply + 1)
        if sc > best:
            best = sc
            if sc > alpha:
                alpha = sc
                if alpha >= beta:
                    if not mv[1] and ply < 128:
                        _killers[ply] = mv
                    break
    return best


def root_search(board, moves, deadline):
    global _deadline, _nodes
    best = moves[0]
    if len(moves) == 1:
        return best
    _deadline = deadline
    _nodes = 0
    for i in range(128):
        _killers[i] = None
    order = list(moves)
    depth = 1
    while depth <= 60:
        try:
            scores = []
            alpha = -INF
            bestmv = None
            for mv in order:
                nb = apply(board, mv, 1)
                sc = -search(nb, -1, depth - 1, -INF, -alpha, 1)
                scores.append((sc, mv))
                if sc > alpha:
                    alpha = sc
                    bestmv = mv
            if bestmv is not None:
                best = bestmv
            scores.sort(key=lambda x: -x[0])
            order = [m for s, m in scores]
            if alpha >= MATE - 200 or alpha <= -MATE + 200:
                break
        except Timeout:
            break
        depth += 1
    return best


def finish(board, mv, dead_prev):
    path, caps = mv
    frm = path[0]
    to = path[1]
    if caps:
        mid = (frm + to) // 2
        dead = tuple(dead_prev) + (mid,)
        p = board[frm]
        np_ = 2 if (p == 1 and (to >> 3) == PROMO[1]) else p
        ba = board[:]
        ba[frm] = 0
        ba[to] = np_
        ba[mid] = 0
        bb = board[:]
        bb[frm] = 0
        bb[to] = np_
        LAST['boards'] = (ba, bb)
        LAST['to'] = to
        LAST['dead'] = dead
    else:
        LAST['boards'] = None
        LAST['dead'] = ()
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))


def policy(my_men, my_kings, opp_men, opp_kings, color):
    start = time.time()
    deadline = start + TIME_BUDGET
    setup(color)
    board = build_board(my_men, my_kings, opp_men, opp_kings)

    # Mid multi-jump continuation detection
    try:
        if LAST['boards'] is not None:
            to = LAST['to']
            if 0 <= to < 64 and board[to] > 0:
                for eb in LAST['boards']:
                    match = True
                    for i in range(64):
                        if i != to and board[i] != eb[i]:
                            match = False
                            break
                    if match:
                        p = board[to]
                        is_king = (p == 2)
                        dirs = DIRS_ALL if is_king else MAN_DIRS[FWD[1]]
                        dead = tuple(LAST['dead'])
                        board[to] = 0
                        out = []
                        _jumps(board, 1, to, is_king, dirs, (to,), dead, out, PROMO[1])
                        board[to] = p
                        if out:
                            mv = root_search(board, out, deadline)
                            return finish(board, mv, dead)
                        break
    except Exception:
        pass

    LAST['boards'] = None
    LAST['dead'] = ()
    moves = gen_moves(board, 1)
    if not moves:
        # No legal moves (game should be over); return a formally shaped tuple.
        pieces = list(my_men) + list(my_kings)
        if pieces:
            r, c = pieces[0]
            return ((r, c), (r, c))
        return ((0, 0), (1, 1))
    try:
        mv = root_search(board, moves, deadline)
    except Exception:
        mv = moves[0]
    return finish(board, mv, ())
