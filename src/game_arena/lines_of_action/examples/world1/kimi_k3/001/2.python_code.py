
import time

# ============================================================
# Lines of Action policy:
#   iterative-deepening negamax (alpha-beta + transposition table)
#   on 64-bit bitboards, with a connectivity-based evaluation.
# ============================================================

NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
DELTAS = ((-1, -1), (-1, 0), (-1, 1),
          (0, -1),           (0, 1),
          (1, -1),  (1, 0),  (1, 1))

LINE = [[0] * 8 for _ in range(64)]   # full line mask through s in direction d
STEPS = [None] * 64                   # STEPS[s][d][k-1] = (target_bit, between_mask)
NEIGH = [0] * 64                      # 8-neighbourhood mask
ROW = [0] * 64
COL = [0] * 64
RSQ = [0] * 64
CW = [0] * 64                         # centrality weight


def _init_tables():
    for s in range(64):
        r = s >> 3
        c = s & 7
        ROW[s] = r
        COL[s] = c
        RSQ[s] = r * r + c * c
        CW[s] = 7 - int(abs(r - 3.5) + abs(c - 3.5))
        neigh = 0
        steps_all = [None] * 8
        for di in range(8):
            dr, dc = DELTAS[di]
            m = 1 << s
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
                rr += dr
                cc += dc
            rr, cc = r - dr, c - dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
                rr -= dr
                cc -= dc
            LINE[s][di] = m
            lst = []
            between = 0
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                tb = 1 << (rr * 8 + cc)
                lst.append((tb, between))
                between |= tb
                rr += dr
                cc += dc
            steps_all[di] = lst
            if 0 <= r + dr < 8 and 0 <= c + dc < 8:
                neigh |= 1 << ((r + dr) * 8 + (c + dc))
        NEIGH[s] = neigh
        STEPS[s] = steps_all


_init_tables()

if hasattr(int, "bit_count"):
    def _popcount(x):
        return x.bit_count()
else:
    _PT = [0] * 256
    for _i in range(1, 256):
        _PT[_i] = _PT[_i >> 1] + (_i & 1)

    def _popcount(x):
        return (_PT[x & 255] + _PT[(x >> 8) & 255] + _PT[(x >> 16) & 255] +
                _PT[(x >> 24) & 255] + _PT[(x >> 32) & 255] + _PT[(x >> 40) & 255] +
                _PT[(x >> 48) & 255] + _PT[(x >> 56) & 255])


def _dilate(x):
    return (((x << 1) & NOT_A) | ((x >> 1) & NOT_H) |
            (x << 8) | (x >> 8) |
            ((x << 9) & NOT_A) | ((x << 7) & NOT_H) |
            ((x >> 7) & NOT_A) | ((x >> 9) & NOT_H))


def _flood(bb):
    # 8-connected region containing the lowest piece of bb
    r = bb & -bb
    while True:
        nr = (r | _dilate(r)) & bb
        if nr == r:
            return r
        r = nr


def _components(bb):
    n = 0
    while bb:
        bb &= ~_flood(bb)
        n += 1
    return n


def _features(me):
    # (piece count, components, variance about centroid, isolated pieces, centrality)
    n = 0
    sr = 0
    sc = 0
    sq = 0
    cw = 0
    iso = 0
    m = me
    while m:
        lb = m & -m
        s = lb.bit_length() - 1
        m ^= lb
        n += 1
        sr += ROW[s]
        sc += COL[s]
        sq += RSQ[s]
        cw += CW[s]
        if not (NEIGH[s] & me):
            iso += 1
    comps = _components(me)
    var = sq - (sr * sr + sc * sc) / n
    return n, comps, var, iso, cw


def _evaluate(me, opp):
    # score from the perspective of the side to move (me)
    n1, c1, v1, i1, w1 = _features(me)
    n2, c2, v2, i2, w2 = _features(opp)
    return (1000.0 * (c2 - c1) +
            8.0 * (v2 - v1) +
            40.0 * (i2 - i1) +
            4.0 * (w1 - w2))


def _ordered_moves(me, opp, ttm=None):
    occ = me | opp
    out = []
    pc = _popcount
    m = me
    while m:
        lb = m & -m
        s = lb.bit_length() - 1
        m ^= lb
        Ls = LINE[s]
        Ss = STEPS[s]
        for d in range(8):
            cnt = pc(Ls[d] & occ)
            st = Ss[d]
            if cnt <= len(st):
                tb, bm = st[cnt - 1]
                if tb & me:        # cannot land on own piece
                    continue
                if bm & opp:       # cannot jump over enemy pieces
                    continue
                t = tb.bit_length() - 1
                sc = CW[t] + 14 * pc(NEIGH[t] & me)
                if tb & opp:
                    sc += 60
                if ttm is not None and s == ttm[0] and tb == ttm[1]:
                    sc += 100000
                out.append((-sc, s, tb))
    out.sort()
    return [(s, tb) for _, s, tb in out]


WIN = 10 ** 7
TT = {}
nodes = 0
deadline = 0.0
TIME_LIMIT = 0.85


class _Timeout(Exception):
    pass


def _negamax(me, opp, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 1023) == 0 and time.perf_counter() > deadline:
        raise _Timeout
    # previous mover connected? (covers simultaneous connection: mover wins)
    if _flood(opp) == opp:
        return -WIN + ply
    # side to move already connected (e.g. reduced to a single piece)
    if _flood(me) == me:
        return WIN - ply
    if depth <= 0:
        return _evaluate(me, opp)
    key = (me, opp)
    ent = TT.get(key)
    ttm = None
    if ent is not None:
        d, val, flag, bm = ent
        if d >= depth:
            if flag == 0:
                return val
            if flag == 1:                    # lower bound
                if val >= beta:
                    return val
                if val > alpha:
                    alpha = val
            else:                            # upper bound
                if val <= alpha:
                    return val
                if val < beta:
                    beta = val
        ttm = bm
    moves = _ordered_moves(me, opp, ttm)
    if not moves:
        return -WIN + ply                    # no legal moves: treated as a loss
    a0 = alpha
    best = -WIN - 1
    bestm = None
    for s, tb in moves:
        val = -_negamax(opp & ~tb, (me ^ (1 << s)) | tb,
                        depth - 1, -beta, -alpha, ply + 1)
        if val > best:
            best = val
            bestm = (s, tb)
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    break
    if best <= a0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best, flag, bestm)
    return best


def _fmt(s, tb):
    t = tb.bit_length() - 1
    return "%d,%d:%d,%d" % (s >> 3, s & 7, t >> 3, t & 7)


def _to_bitboards(board):
    me = 0
    opp = 0
    bit = 1
    for r in range(8):
        rowv = board[r]
        for c in range(8):
            v = rowv[c]
            if v == 1:
                me |= bit
            elif v == -1:
                opp |= bit
            bit <<= 1
    return me, opp


def policy(board) -> str:
    global deadline, nodes
    try:
        me, opp = _to_bitboards(board)
        moves = _ordered_moves(me, opp)
        if not moves:
            return "0,0:0,0"          # no legal move; game is over anyway
        if len(moves) == 1:
            return _fmt(moves[0][0], moves[0][1])

        if len(TT) > 400000:
            TT.clear()
        deadline = time.perf_counter() + TIME_LIMIT
        nodes = 0

        # immediate-win shortcut
        for s, tb in moves:
            nme = (me ^ (1 << s)) | tb
            if _flood(nme) == nme:
                return _fmt(s, tb)

        best = moves[0]
        try:
            depth = 1
            while depth <= 10:
                cur = None
                curv = -WIN - 1
                alpha = -WIN
                for s, tb in moves:
                    nme = (me ^ (1 << s)) | tb
                    nopp = opp & ~tb
                    val = -_negamax(nopp, nme, depth - 1, -WIN, -alpha, 1)
                    if val > curv:
                        curv = val
                        cur = (s, tb)
                        if val > alpha:
                            alpha = val
                best = cur
                moves.remove(best)
                moves.insert(0, best)
                if curv >= WIN - 100:        # forced win found
                    break
                if time.perf_counter() > deadline:
                    break
                depth += 1
        except _Timeout:
            pass
        return _fmt(best[0], best[1])
    except Exception:
        # absolute fallback: return any legal move
        try:
            me, opp = _to_bitboards(board)
            mv = _ordered_moves(me, opp)
            if mv:
                return _fmt(mv[0][0], mv[0][1])
        except Exception:
            pass
        return "0,0:0,0"
