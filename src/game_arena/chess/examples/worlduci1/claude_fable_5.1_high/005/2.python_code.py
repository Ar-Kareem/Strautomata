
import time
import random


class Timeout(Exception):
    pass


OFF = 7
P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6
VAL = (0, 100, 320, 330, 500, 900, 20000)
PHASE_W = (0, 0, 1, 1, 2, 4, 0)
INF = 10 ** 9
MATE = 100000
PIECE_CODE = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}

KNIGHT_D = (-21, -19, -12, -8, 8, 12, 19, 21)
BISHOP_D = (-11, -9, 9, 11)
ROOK_D = (-10, -1, 1, 10)
KING_D = (-11, -10, -9, -1, 1, 9, 10, 11)
SQUARES = [21 + r * 10 + f for r in range(8) for f in range(8)]
FILES = 'abcdefgh'


def sq_name(sq):
    r, f = divmod(sq - 21, 10)
    return FILES[f] + str(r + 1)


def name_sq(s):
    return 21 + (int(s[1]) - 1) * 10 + FILES.index(s[0])


def move_str(m):
    frm = m & 127
    to = (m >> 7) & 127
    promo = m >> 14
    return sq_name(frm) + sq_name(to) + ('q' if promo else '')


PAWN_MG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0]
PAWN_EG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    90, 90, 90, 90, 90, 90, 90, 90,
    50, 50, 50, 50, 50, 50, 50, 50,
    30, 30, 30, 30, 30, 30, 30, 30,
    15, 15, 15, 15, 15, 15, 15, 15,
    5, 5, 5, 5, 5, 5, 5, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0]
KNIGHT_T = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50]
BISHOP_T = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20]
ROOK_T = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0]
QUEEN_T = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20]
KING_MG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20]
KING_EG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50]

TABLES_MG = {P: PAWN_MG, N: KNIGHT_T, B: BISHOP_T, R: ROOK_T, Q: QUEEN_T, K: KING_MG}
TABLES_EG = {P: PAWN_EG, N: KNIGHT_T, B: BISHOP_T, R: ROOK_T, Q: QUEEN_T, K: KING_EG}
PST_MG = [[0] * 120 for _ in range(13)]
PST_EG = [[0] * 120 for _ in range(13)]
for _pt in range(1, 7):
    _mat = VAL[_pt] if _pt != K else 0
    for _sq in SQUARES:
        _r, _f = divmod(_sq - 21, 10)
        _wi = (7 - _r) * 8 + _f
        _bi = _r * 8 + _f
        PST_MG[_pt + 6][_sq] = _mat + TABLES_MG[_pt][_wi]
        PST_EG[_pt + 6][_sq] = _mat + TABLES_EG[_pt][_wi]
        PST_MG[6 - _pt][_sq] = -(_mat + TABLES_MG[_pt][_bi])
        PST_EG[6 - _pt][_sq] = -(_mat + TABLES_EG[_pt][_bi])

CENTER_DIST = [0] * 120
for _sq in SQUARES:
    _r, _f = divmod(_sq - 21, 10)
    CENTER_DIST[_sq] = (3 - min(_f, 7 - _f)) + (3 - min(_r, 7 - _r))

_rng = random.Random(20240601)
ZOB = [[_rng.getrandbits(64) for _ in range(120)] for _ in range(13)]
ZOB_SIDE = _rng.getrandbits(64)

board = [OFF] * 120
SIDE = 1
MG = 0
EG = 0
PHASE = 0
WK = 0
BK = 0
WMAT = 0
BMAT = 0
WP = 0
BP = 0
HASH = 0
NODES = 0
DEADLINE = 0.0
TT = {}
HISTORY = set()
KILLERS = [[0, 0] for _ in range(128)]
HIST_W = [0] * (1 << 17)
HIST_B = [0] * (1 << 17)
LAST_COUNT = [0]


def setup(pieces, to_play):
    global SIDE, MG, EG, PHASE, WK, BK, WMAT, BMAT, WP, BP, HASH
    for i in range(120):
        board[i] = OFF
    for sq in SQUARES:
        board[sq] = 0
    MG = EG = PHASE = WMAT = BMAT = WP = BP = 0
    HASH = 0
    WK = BK = 0
    for s, code in pieces.items():
        sq = name_sq(s.lower())
        pt = PIECE_CODE[code[1].upper()]
        white = code[0].lower() == 'w'
        p = pt if white else -pt
        board[sq] = p
        pi = p + 6
        MG += PST_MG[pi][sq]
        EG += PST_EG[pi][sq]
        HASH ^= ZOB[pi][sq]
        PHASE += PHASE_W[pt]
        if white:
            if pt == P:
                WP += 1
            elif pt == K:
                WK = sq
            else:
                WMAT += VAL[pt]
        else:
            if pt == P:
                BP += 1
            elif pt == K:
                BK = sq
            else:
                BMAT += VAL[pt]
    SIDE = 1 if str(to_play).lower().startswith('w') else -1
    if SIDE == -1:
        HASH ^= ZOB_SIDE


def attacked(sq, by):
    b = board
    if by == 1:
        if b[sq - 9] == 1 or b[sq - 11] == 1:
            return True
    else:
        if b[sq + 9] == -1 or b[sq + 11] == -1:
            return True
    kn = 2 * by
    for d in KNIGHT_D:
        if b[sq + d] == kn:
            return True
    kg = 6 * by
    for d in KING_D:
        if b[sq + d] == kg:
            return True
    bi = 3 * by
    qu = 5 * by
    for d in BISHOP_D:
        t = sq + d
        c = b[t]
        while c == 0:
            t += d
            c = b[t]
        if c == bi or c == qu:
            return True
    ro = 4 * by
    for d in ROOK_D:
        t = sq + d
        c = b[t]
        while c == 0:
            t += d
            c = b[t]
        if c == ro or c == qu:
            return True
    return False


def gen_moves(caps_only):
    b = board
    side = SIDE
    moves = []
    ap = moves.append
    hist = HIST_W if side == 1 else HIST_B
    for sq in SQUARES:
        p = b[sq]
        if p == 0:
            continue
        if side == 1:
            if p < 0:
                continue
        elif p > 0:
            continue
        pt = p if p > 0 else -p
        if pt == P:
            fwd = 10 * side
            t = sq + fwd
            if side == 1:
                prom = t >= 91
            else:
                prom = t <= 28
            if b[t] == 0:
                if prom:
                    ap((900000, sq | (t << 7) | (Q << 14)))
                elif not caps_only:
                    m = sq | (t << 7)
                    ap((hist[m], m))
                    if (side == 1 and 31 <= sq <= 38) or (side == -1 and 81 <= sq <= 88):
                        t2 = t + fwd
                        if b[t2] == 0:
                            m2 = sq | (t2 << 7)
                            ap((hist[m2], m2))
            for d in (fwd - 1, fwd + 1):
                t = sq + d
                c = b[t]
                if c != 0 and c != OFF and ((c < 0) if side == 1 else (c > 0)):
                    ct = -c if c < 0 else c
                    if prom:
                        ap((900000 + VAL[ct], sq | (t << 7) | (Q << 14)))
                    else:
                        ap((100000 + VAL[ct] * 10 - pt, sq | (t << 7)))
        elif pt == N or pt == K:
            for d in (KNIGHT_D if pt == N else KING_D):
                t = sq + d
                c = b[t]
                if c == 0:
                    if not caps_only:
                        m = sq | (t << 7)
                        ap((hist[m], m))
                elif c != OFF and ((c < 0) if side == 1 else (c > 0)):
                    ct = -c if c < 0 else c
                    ap((100000 + VAL[ct] * 10 - pt, sq | (t << 7)))
        else:
            dirs = BISHOP_D if pt == B else (ROOK_D if pt == R else KING_D)
            for d in dirs:
                t = sq + d
                while True:
                    c = b[t]
                    if c == 0:
                        if not caps_only:
                            m = sq | (t << 7)
                            ap((hist[m], m))
                        t += d
                        continue
                    if c != OFF and ((c < 0) if side == 1 else (c > 0)):
                        ct = -c if c < 0 else c
                        ap((100000 + VAL[ct] * 10 - pt, sq | (t << 7)))
                    break
    return moves


def make(m):
    global SIDE, MG, EG, PHASE, WK, BK, WMAT, BMAT, WP, BP, HASH
    frm = m & 127
    to = (m >> 7) & 127
    promo = m >> 14
    b = board
    piece = b[frm]
    cap = b[to]
    undo = (piece, cap, MG, EG, PHASE, WK, BK, WMAT, BMAT, WP, BP, HASH)
    side = SIDE
    pi = piece + 6
    HASH ^= ZOB[pi][frm]
    MG -= PST_MG[pi][frm]
    EG -= PST_EG[pi][frm]
    if cap:
        ci = cap + 6
        HASH ^= ZOB[ci][to]
        MG -= PST_MG[ci][to]
        EG -= PST_EG[ci][to]
        ct = cap if cap > 0 else -cap
        PHASE -= PHASE_W[ct]
        if cap > 0:
            if ct == P:
                WP -= 1
            elif ct != K:
                WMAT -= VAL[ct]
        else:
            if ct == P:
                BP -= 1
            elif ct != K:
                BMAT -= VAL[ct]
    if promo:
        newp = promo * side
        PHASE += PHASE_W[promo]
        if side == 1:
            WP -= 1
            WMAT += VAL[promo]
        else:
            BP -= 1
            BMAT += VAL[promo]
    else:
        newp = piece
    ni = newp + 6
    b[to] = newp
    b[frm] = 0
    HASH ^= ZOB[ni][to]
    MG += PST_MG[ni][to]
    EG += PST_EG[ni][to]
    if piece == K:
        WK = to
    elif piece == -K:
        BK = to
    SIDE = -side
    HASH ^= ZOB_SIDE
    return undo


def unmake(m, u):
    global SIDE, MG, EG, PHASE, WK, BK, WMAT, BMAT, WP, BP, HASH
    frm = m & 127
    to = (m >> 7) & 127
    board[frm] = u[0]
    board[to] = u[1]
    SIDE = -SIDE
    MG, EG, PHASE, WK, BK, WMAT, BMAT, WP, BP, HASH = u[2:]


def evaluate():
    ph = PHASE if PHASE < 24 else 24
    s = (MG * ph + EG * (24 - ph)) // 24
    if WP == 0 and BP == 0 and WMAT <= 330 and BMAT <= 330:
        return 0
    if BMAT == 0 and BP == 0 and WMAT >= 400:
        rw, fw = divmod(WK - 21, 10)
        rb, fb = divmod(BK - 21, 10)
        kd = abs(rw - rb) + abs(fw - fb)
        s += CENTER_DIST[BK] * 10 + (14 - kd) * 4
    elif WMAT == 0 and WP == 0 and BMAT >= 400:
        rw, fw = divmod(WK - 21, 10)
        rb, fb = divmod(BK - 21, 10)
        kd = abs(rw - rb) + abs(fw - fb)
        s -= CENTER_DIST[WK] * 10 + (14 - kd) * 4
    return s if SIDE == 1 else -s


def quiesce(alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() > DEADLINE:
        raise Timeout()
    stand = evaluate()
    if stand >= beta:
        return stand
    if ply >= 90:
        return stand
    if stand > alpha:
        alpha = stand
    moves = gen_moves(True)
    moves.sort(reverse=True)
    side = SIDE
    b = board
    for s, m in moves:
        if (m >> 14) == 0:
            cap = b[(m >> 7) & 127]
            if cap:
                cv = VAL[cap if cap > 0 else -cap]
                if stand + cv + 200 < alpha:
                    continue
        u = make(m)
        if attacked(WK if side == 1 else BK, -side):
            unmake(m, u)
            continue
        sc = -quiesce(-beta, -alpha, ply + 1)
        unmake(m, u)
        if sc > alpha:
            alpha = sc
            if sc >= beta:
                return sc
    return alpha


def search(depth, alpha, beta, ply, do_null):
    global NODES, SIDE, HASH
    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() > DEADLINE:
        raise Timeout()
    if HASH in HISTORY:
        return 0
    side = SIDE
    ksq = WK if side == 1 else BK
    in_check = attacked(ksq, -side)
    if in_check and ply < 60:
        depth += 1
    if depth <= 0:
        return quiesce(alpha, beta, ply)
    if ply >= 60:
        return evaluate()
    tt_move = 0
    e = TT.get(HASH)
    if e is not None:
        tdepth, tscore, tflag, tt_move = e
        if tdepth >= depth:
            if tscore > MATE - 1000:
                tscore -= ply
            elif tscore < -MATE + 1000:
                tscore += ply
            if tflag == 0:
                return tscore
            if tflag == 1 and tscore >= beta:
                return tscore
            if tflag == 2 and tscore <= alpha:
                return tscore
    if do_null and not in_check and depth >= 3 and beta < MATE - 1000:
        mat = WMAT if side == 1 else BMAT
        if mat > 0:
            SIDE = -side
            HASH ^= ZOB_SIDE
            try:
                sc = -search(depth - 3, -beta, -beta + 1, ply + 1, False)
            finally:
                SIDE = side
                HASH ^= ZOB_SIDE
            if sc >= beta:
                return beta
    moves = gen_moves(False)
    k1, k2 = KILLERS[ply]
    for i in range(len(moves)):
        s, m = moves[i]
        if m == tt_move:
            moves[i] = (10000000, m)
        elif (m == k1 or m == k2) and s < 100000:
            moves[i] = (s + 50000, m)
    moves.sort(reverse=True)
    best = -INF
    best_move = 0
    legal = 0
    flag = 2
    hist = HIST_W if side == 1 else HIST_B
    for s, m in moves:
        u = make(m)
        if attacked(WK if side == 1 else BK, -side):
            unmake(m, u)
            continue
        legal += 1
        sc = -search(depth - 1, -beta, -alpha, ply + 1, True)
        unmake(m, u)
        if sc > best:
            best = sc
            best_move = m
            if sc > alpha:
                alpha = sc
                flag = 0
                if sc >= beta:
                    if u[1] == 0 and (m >> 14) == 0:
                        if k1 != m:
                            KILLERS[ply] = [m, k1]
                        v = hist[m] + depth * depth
                        hist[m] = v if v < 90000 else 90000
                    flag = 1
                    break
    if legal == 0:
        return (-MATE + ply) if in_check else 0
    sc = best
    if sc > MATE - 1000:
        sc += ply
    elif sc < -MATE + 1000:
        sc -= ply
    TT[HASH] = (depth, sc, flag, best_move)
    return best


def root_search(depth, root_moves):
    root_moves.sort(reverse=True)
    alpha = -INF
    beta = INF
    best_move = root_moves[0][1]
    best = -INF
    for i in range(len(root_moves)):
        m = root_moves[i][1]
        u = make(m)
        try:
            sc = -search(depth - 1, -beta, -alpha, 1, True)
        finally:
            unmake(m, u)
        root_moves[i][0] = sc
        if sc > best:
            best = sc
            best_move = m
            if sc > alpha:
                alpha = sc
    return best_move, best


def policy(pieces, to_play):
    global DEADLINE, NODES
    start = time.perf_counter()
    DEADLINE = start + 0.62
    fallback = None
    try:
        setup(pieces, to_play)
        root_hash = HASH
        n = len(pieces)
        if n > LAST_COUNT[0] or len(TT) > 2000000:
            TT.clear()
            HISTORY.clear()
        LAST_COUNT[0] = n
        for k in KILLERS:
            k[0] = 0
            k[1] = 0
        HIST_W[:] = [0] * (1 << 17)
        HIST_B[:] = [0] * (1 << 17)
        NODES = 0
        side = SIDE
        root_moves = []
        for s, m in gen_moves(False):
            u = make(m)
            ok = not attacked(WK if side == 1 else BK, -side)
            unmake(m, u)
            if ok:
                root_moves.append([s, m])
        if not root_moves:
            return 'a1a1'
        root_moves.sort(reverse=True)
        best_move = root_moves[0][1]
        fallback = move_str(best_move)
        if len(root_moves) > 1:
            for depth in range(1, 40):
                try:
                    bm, sc = root_search(depth, root_moves)
                except Timeout:
                    break
                best_move = bm
                fallback = move_str(best_move)
                if sc > MATE - 1000 or sc < -MATE + 1000:
                    break
                if time.perf_counter() > DEADLINE:
                    break
        # restore clean state (a timeout may have left the board mid-line)
        setup(pieces, to_play)
        HISTORY.add(root_hash)
        u = make(best_move)
        HISTORY.add(HASH)
        unmake(best_move, u)
        return move_str(best_move)
    except Exception:
        if fallback is not None:
            return fallback
        try:
            setup(pieces, to_play)
            side = SIDE
            for s, m in gen_moves(False):
                u = make(m)
                ok = not attacked(WK if side == 1 else BK, -side)
                unmake(m, u)
                if ok:
                    return move_str(m)
        except Exception:
            pass
        return 'a1a1'
