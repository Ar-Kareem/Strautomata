
import time
import random

# ===================== board constants (0x88) =====================
KNIGHT_D = (31, 33, 14, 18, -31, -33, -14, -18)
KING_D   = (15, 16, 17, 1, -15, -16, -17, -1)
BISHOP_D = (15, 17, -15, -17)
ROOK_D   = (16, -16, 1, -1)

VALS   = (0, 100, 320, 330, 500, 900, 0)
MAG    = (0, 100, 320, 330, 500, 900, 1500)
PHASEW = (0, 0, 1, 1, 2, 4, 0)
PT     = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}
PROMO_CH = (None, None, 'n', 'b', 'r', 'q')

MATE = 1000000
INF  = 10 ** 9
MAXD = 40

def _flip(t8):
    out = [0] * 64
    for r in range(8):
        b = (7 - r) * 8
        for f in range(8):
            out[r * 8 + f] = t8[b + f]
    return out

_PAWN = _flip([
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0])
_KNIGHT = _flip([
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50])
_BISHOP = _flip([
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20])
_ROOK = _flip([
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0])
_QUEEN = _flip([
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20])
KING_MG = _flip([
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20])
KING_EG = _flip([
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50])
PST = (None, _PAWN, _KNIGHT, _BISHOP, _ROOK, _QUEEN)

# ===================== zobrist =====================
_rng = random.Random(20240501)
ZOB = [[0] * 128 for _ in range(13)]
for _pi in range(13):
    if _pi == 6:
        continue
    _row = ZOB[_pi]
    for _s in range(128):
        if _s & 0x88:
            continue
        _row[_s] = _rng.getrandbits(64)
ZOB_SIDE = _rng.getrandbits(64)

# ===================== globals =====================
_TT = {}
_KILLERS = [[0, 0] for _ in range(140)]
_HISTORY = {}
_NODES = 0
_DEADLINE = 0.0

class _Timeout(Exception):
    pass

# ===================== board helpers =====================
def is_attacked(bd, sq, by_white):
    if by_white:
        s = sq - 15
        if not (s & 0x88) and bd[s] == 1:
            return True
        s = sq - 17
        if not (s & 0x88) and bd[s] == 1:
            return True
        n, b, r, q, k = 2, 3, 4, 5, 6
    else:
        s = sq + 15
        if not (s & 0x88) and bd[s] == -1:
            return True
        s = sq + 17
        if not (s & 0x88) and bd[s] == -1:
            return True
        n, b, r, q, k = -2, -3, -4, -5, -6
    for d in KNIGHT_D:
        s = sq + d
        if not (s & 0x88) and bd[s] == n:
            return True
    for d in KING_D:
        s = sq + d
        if not (s & 0x88) and bd[s] == k:
            return True
    for d in BISHOP_D:
        s = sq + d
        while not (s & 0x88):
            p = bd[s]
            if p:
                if p == b or p == q:
                    return True
                break
            s += d
    for d in ROOK_D:
        s = sq + d
        while not (s & 0x88):
            p = bd[s]
            if p:
                if p == r or p == q:
                    return True
                break
            s += d
    return False

def gen_moves(bd, white, capsonly):
    moves = []
    ap = moves.append
    if white:
        up, start, last, c1, c2 = 16, 1, 7, 15, 17
    else:
        up, start, last, c1, c2 = -16, 6, 0, -15, -17
    for i in range(64):
        sq = ((i >> 3) << 4) | (i & 7)
        p = bd[sq]
        if p == 0 or (p > 0) != white:
            continue
        t = p if p > 0 else -p
        if t == 1:  # pawn
            r = sq >> 4
            t1 = sq + up
            if not (t1 & 0x88) and bd[t1] == 0:
                if (t1 >> 4) == last:
                    ap(sq | (t1 << 7) | (5 << 14)); ap(sq | (t1 << 7) | (4 << 14))
                    ap(sq | (t1 << 7) | (3 << 14)); ap(sq | (t1 << 7) | (2 << 14))
                elif not capsonly:
                    ap(sq | (t1 << 7))
                    if r == start:
                        t2 = t1 + up
                        if not (t2 & 0x88) and bd[t2] == 0:
                            ap(sq | (t2 << 7))
            for d in (c1, c2):
                t1 = sq + d
                if t1 & 0x88:
                    continue
                qq = bd[t1]
                if qq and (qq > 0) != white:
                    if (t1 >> 4) == last:
                        ap(sq | (t1 << 7) | (5 << 14)); ap(sq | (t1 << 7) | (4 << 14))
                        ap(sq | (t1 << 7) | (3 << 14)); ap(sq | (t1 << 7) | (2 << 14))
                    else:
                        ap(sq | (t1 << 7))
        elif t == 2:  # knight
            for d in KNIGHT_D:
                t1 = sq + d
                if t1 & 0x88:
                    continue
                qq = bd[t1]
                if qq == 0:
                    if not capsonly:
                        ap(sq | (t1 << 7))
                elif (qq > 0) != white:
                    ap(sq | (t1 << 7))
        elif t == 6:  # king (no castling: rights unknowable from input)
            for d in KING_D:
                t1 = sq + d
                if t1 & 0x88:
                    continue
                qq = bd[t1]
                if qq == 0:
                    if not capsonly:
                        ap(sq | (t1 << 7))
                elif (qq > 0) != white:
                    ap(sq | (t1 << 7))
        else:  # sliders
            dirs = BISHOP_D if t == 3 else (ROOK_D if t == 4 else KING_D)
            for d in dirs:
                t1 = sq + d
                while not (t1 & 0x88):
                    qq = bd[t1]
                    if qq == 0:
                        if not capsonly:
                            ap(sq | (t1 << 7))
                    else:
                        if (qq > 0) != white:
                            ap(sq | (t1 << 7))
                        break
                    t1 += d
    return moves

def do_move(bd, ks, mv, white):
    frm = mv & 127
    to = (mv >> 7) & 127
    pr = mv >> 14
    p = bd[frm]
    c = bd[to]
    placed = (pr if white else -pr) if pr else p
    bd[frm] = 0
    bd[to] = placed
    k0, k1 = ks[0], ks[1]
    if p == 6:
        ks[0] = to
    elif p == -6:
        ks[1] = to
    dh = ZOB[p + 6][frm] ^ ZOB[placed + 6][to] ^ ZOB_SIDE
    if c:
        dh ^= ZOB[c + 6][to]
    return c, k0, k1, dh

def undo_move(bd, ks, mv, white, c, k0, k1):
    frm = mv & 127
    to = (mv >> 7) & 127
    pr = mv >> 14
    bd[frm] = (1 if white else -1) if pr else bd[to]
    bd[to] = c
    ks[0] = k0
    ks[1] = k1

def evaluate(bd):
    s = 0
    phase = 0
    wk = bk = 0
    wb = bb = 0
    for i in range(64):
        p = bd[((i >> 3) << 4) | (i & 7)]
        if p == 0:
            continue
        if p > 0:
            if p == 6:
                wk = i
                continue
            if p == 3:
                wb += 1
            s += VALS[p] + PST[p][i]
            phase += PHASEW[p]
        else:
            t = -p
            if t == 6:
                bk = i
                continue
            if t == 3:
                bb += 1
            s -= VALS[t] + PST[t][i ^ 56]
            phase += PHASEW[t]
    if wb >= 2:
        s += 30
    if bb >= 2:
        s -= 30
    if phase > 16:
        phase = 16
    s += ((KING_MG[wk] - KING_MG[bk ^ 56]) * phase +
          (KING_EG[wk] - KING_EG[bk ^ 56]) * (16 - phase)) >> 4
    return s

def _order(bd, moves, tt_mv, ply, white):
    k0, k1 = _KILLERS[ply]
    res = []
    for mv in moves:
        if mv == tt_mv:
            res.append((30000000, mv))
            continue
        frm = mv & 127
        to = (mv >> 7) & 127
        pr = mv >> 14
        v = bd[to]
        if v:
            a = bd[frm]
            s = 1000000 + 10 * MAG[v if v > 0 else -v] - MAG[a if a > 0 else -a]
            if pr:
                s += 2000000 + MAG[pr]
        elif pr:
            s = 2000000 + MAG[pr]
        else:
            if mv == k0:
                s = 900000
            elif mv == k1:
                s = 800000
            else:
                s = _HISTORY.get((white, frm, to), 0)
                if s > 700000:
                    s = 700000
        res.append((s, mv))
    res.sort(reverse=True)
    return res

# ===================== search =====================
def qsearch(bd, ks, h, alpha, beta, white, ply):
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.time() >= _DEADLINE:
        raise _Timeout()
    if ply >= 120:
        e = evaluate(bd)
        return e if white else -e
    ksq = ks[0] if white else ks[1]
    in_check = is_attacked(bd, ksq, not white)
    stand = 0
    if not in_check:
        stand = evaluate(bd)
        if not white:
            stand = -stand
        if stand >= beta:
            return stand
        if stand > alpha:
            alpha = stand
        moves = gen_moves(bd, white, True)
    else:
        moves = gen_moves(bd, white, False)
    scored = []
    for mv in moves:
        to = (mv >> 7) & 127
        v = bd[to]
        pr = mv >> 14
        s = 0
        if v:
            a = bd[mv & 127]
            s = 1000000 + 10 * MAG[v if v > 0 else -v] - MAG[a if a > 0 else -a]
        if pr:
            s += 2000000 + MAG[pr]
        scored.append((s, mv))
    scored.sort(reverse=True)
    legal = 0
    for s, mv in scored:
        if not in_check:
            v = bd[(mv >> 7) & 127]
            gain = (MAG[v if v > 0 else -v] if v else 0) + (900 if (mv >> 14) else 0)
            if stand + gain + 200 < alpha:
                continue
        c, k0, k1, dh = do_move(bd, ks, mv, white)
        kk = ks[0] if white else ks[1]
        if is_attacked(bd, kk, not white):
            undo_move(bd, ks, mv, white, c, k0, k1)
            continue
        legal += 1
        h ^= dh
        val = -qsearch(bd, ks, h, -beta, -alpha, not white, ply + 1)
        h ^= dh
        undo_move(bd, ks, mv, white, c, k0, k1)
        if val >= beta:
            return val
        if val > alpha:
            alpha = val
    if in_check and legal == 0:
        return -MATE + ply
    return alpha

def search(bd, ks, h, depth, alpha, beta, white, ply):
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.time() >= _DEADLINE:
        raise _Timeout()
    if ply >= 120:
        e = evaluate(bd)
        return e if white else -e
    ksq = ks[0] if white else ks[1]
    in_check = is_attacked(bd, ksq, not white)
    if in_check:
        depth += 1
    if depth <= 0:
        return qsearch(bd, ks, h, alpha, beta, white, ply)
    tt_mv = 0
    ent = _TT.get(h)
    if ent is not None:
        ed, ef, es, em = ent
        if ed >= depth:
            if ef == 0:
                return es
            if ef == 1 and es <= alpha:
                return alpha
            if ef == 2 and es >= beta:
                return beta
        tt_mv = em
    a0 = alpha
    best = -INF
    best_mv = 0
    legal = 0
    for s, mv in _order(bd, gen_moves(bd, white, False), tt_mv, ply, white):
        c, k0, k1, dh = do_move(bd, ks, mv, white)
        kk = ks[0] if white else ks[1]
        if is_attacked(bd, kk, not white):
            undo_move(bd, ks, mv, white, c, k0, k1)
            continue
        legal += 1
        h ^= dh
        val = -search(bd, ks, h, depth - 1, -beta, -alpha, not white, ply + 1)
        h ^= dh
        undo_move(bd, ks, mv, white, c, k0, k1)
        if val > best:
            best = val
            best_mv = mv
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    if c == 0 and (mv >> 14) == 0:
                        kl = _KILLERS[ply]
                        if kl[0] != mv:
                            kl[1] = kl[0]
                            kl[0] = mv
                        hk = (white, mv & 127, (mv >> 7) & 127)
                        _HISTORY[hk] = _HISTORY.get(hk, 0) + depth * depth
                    break
    if legal == 0:
        return (-MATE + ply) if in_check else 0
    if best <= a0:
        flag = 1
    elif best >= beta:
        flag = 2
    else:
        flag = 0
    _TT[h] = (depth, flag, best, best_mv)
    return best

# ===================== root / API =====================
def _setup(pieces, to_play):
    bd = [0] * 128
    for name, code in pieces.items():
        f = ord(name[0]) - 97
        r = ord(name[1]) - 49
        v = PT[code[1]]
        bd[(r << 4) | f] = v if code[0] == 'w' else -v
    ks = [0, 0]
    for i in range(64):
        sq = ((i >> 3) << 4) | (i & 7)
        p = bd[sq]
        if p == 6:
            ks[0] = sq
        elif p == -6:
            ks[1] = sq
    return bd, ks, (to_play[0] == 'w')

def _hash(bd, white):
    h = 0
    for i in range(64):
        sq = ((i >> 3) << 4) | (i & 7)
        p = bd[sq]
        if p:
            h ^= ZOB[p + 6][sq]
    if white:
        h ^= ZOB_SIDE
    return h

def _legal_moves(bd, ks, white):
    res = []
    for mv in gen_moves(bd, white, False):
        c, k0, k1, dh = do_move(bd, ks, mv, white)
        kk = ks[0] if white else ks[1]
        if not is_attacked(bd, kk, not white):
            res.append(mv)
        undo_move(bd, ks, mv, white, c, k0, k1)
    return res

def _uci(mv):
    frm = mv & 127
    to = (mv >> 7) & 127
    pr = mv >> 14
    s = chr(97 + (frm & 7)) + chr(49 + (frm >> 4)) + chr(97 + (to & 7)) + chr(49 + (to >> 4))
    if pr:
        s += PROMO_CH[pr]
    return s

def _policy(pieces, to_play):
    global _DEADLINE, _NODES, _KILLERS, _HISTORY
    bd, ks, white = _setup(pieces, to_play)
    legal = _legal_moves(bd, ks, white)
    if not legal:
        return 'a1a1'  # unreachable in a real game (no legal moves = game over)
    if len(legal) == 1:
        return _uci(legal[0])
    h = _hash(bd, white)
    start = time.time()
    _DEADLINE = start + 0.85
    _NODES = 0
    _KILLERS = [[0, 0] for _ in range(140)]
    _HISTORY = {}
    if len(_TT) > 250000:
        _TT.clear()
    prev_best = legal[0]
    depth = 1
    while depth <= MAXD:
        if time.time() > start + 0.55:
            break
        alpha = -INF
        try:
            for s, mv in _order(bd, legal, prev_best, 0, white):
                c, k0, k1, dh = do_move(bd, ks, mv, white)
                h ^= dh
                val = -search(bd, ks, h, depth - 1, -INF, -alpha, not white, 1)
                h ^= dh
                undo_move(bd, ks, mv, white, c, k0, k1)
                if val > alpha:
                    alpha = val
                    prev_best = mv
        except _Timeout:
            break
        if alpha > MATE - 2000:
            break
        depth += 1
    return _uci(prev_best)

def policy(pieces, to_play):
    try:
        return _policy(pieces, to_play)
    except Exception:
        pass
    # emergency fallback: return the first fully legal move we can find
    try:
        bd, ks, white = _setup(pieces, to_play)
        for mv in gen_moves(bd, white, False):
            c, k0, k1, dh = do_move(bd, ks, mv, white)
            kk = ks[0] if white else ks[1]
            ok = not is_attacked(bd, kk, not white)
            undo_move(bd, ks, mv, white, c, k0, k1)
            if ok:
                return _uci(mv)
    except Exception:
        pass
    return 'a1a1'
