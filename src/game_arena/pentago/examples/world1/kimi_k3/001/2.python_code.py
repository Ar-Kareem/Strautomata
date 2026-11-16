
import time

# ---------- constants ----------
ALL36 = (1 << 36) - 1
INF = 10 ** 9
BIG = 10 ** 7  # terminal score base (bigger than any eval)

try:
    int(1).bit_count
    def _pc(x): return x.bit_count()
except Exception:
    def _pc(x): return bin(x).count('1')

# lines of 5
def _build_lines():
    lines = []
    for r in range(6):
        for c in range(2):
            lines.append(sum(1 << (r * 6 + c + k) for k in range(5)))
    for c in range(6):
        for r in range(2):
            lines.append(sum(1 << ((r + k) * 6 + c) for k in range(5)))
    for r in range(2):
        for c in range(2):
            lines.append(sum(1 << ((r + k) * 6 + c + k) for k in range(5)))
    for r in range(2):
        for c in range(4, 6):
            lines.append(sum(1 << ((r + k) * 6 + c - k) for k in range(5)))
    return tuple(lines)

LINES = _build_lines()

# quadrant geometry
_OFFS = ((0, 0), (0, 3), (3, 0), (3, 3))
QMASK = []
ROT = []          # ROT[q][d]: list of (src_bit, dst_bit); d 0='L', 1='R'
LQ = []           # masks of win-lines touching each quadrant
DIRCH = ('L', 'R')
for (R, C) in _OFFS:
    cells = [(R + i) * 6 + (C + j) for i in range(3) for j in range(3)]
    mask = 0
    for x in cells:
        mask |= 1 << x
    QMASK.append(mask)
    q_lines = []
    for ln in LINES:
        if ln & mask:
            q_lines.append(ln)
    LQ.append(tuple(q_lines))
    dl, dr = [], []
    for i in range(3):
        for j in range(3):
            src = (R + i) * 6 + (C + j)
            # L: 90 anticlockwise (i,j)->(2-j, i);  R: clockwise (i,j)->(j,2-i)
            niL, njL = 2 - j, i
            niR, njR = j, 2 - i
            dl.append((1 << src, 1 << ((R + niL) * 6 + (C + njL))))
            dr.append((1 << src, 1 << ((R + niR) * 6 + (C + njR))))
    ROT.append((tuple(dl), tuple(dr)))

CENTER = (1 << 14) | (1 << 15) | (1 << 20) | (1 << 21)

# evaluation weights: open line containing k marbles
WT = (0, 2, 12, 90, 1200)     # ours
WO = (0, 2, 14, 110, 1400)    # theirs (defense slightly higher)

def _five(b, masks):
    for m in masks:
        if (b & m) == m:
            return True
    return False

def _evaluate(you, opp, LINES=LINES):
    s = 0
    for m in LINES:
        yb = you & m
        if yb:
            if not (opp & m):
                s += WT[_pc(yb)]
        else:
            ob = opp & m
            if ob:
                s -= WO[_pc(ob)]
    s += _pc(you & CENTER) - _pc(opp & CENTER)
    return s

class _Abort(Exception):
    pass

# ---------- move generation (with dedup, ordering, terminal classification) ----------
def _gen(you, opp, with_move):
    empty = ALL36 ^ (you | opp)
    res = []
    seen = set()
    while empty:
        bit = empty & -empty
        empty ^= bit
        pos = bit.bit_length() - 1
        yb0 = you | bit
        for q in (0, 1, 2, 3):
            qm = QMASK[q]
            nq = ~qm
            aqm = yb0 & qm
            bqm = opp & qm
            lq = LQ[q]
            for d in (0, 1):
                ny = yb0 & nq
                no = opp & nq
                for sm, dm in ROT[q][d]:
                    if aqm & sm:
                        ny |= dm
                    if bqm & sm:
                        no |= dm
                key = ny | (no << 36)
                if key in seen:
                    continue
                seen.add(key)
                yw = _five(ny, lq)
                ow = _five(no, lq)
                if yw and ow:
                    kind, score = 2, 0
                elif yw:
                    kind, score = 1, BIG * 4
                elif ow:
                    kind, score = -1, -BIG * 4
                else:
                    kind, score = 0, _evaluate(ny, no)
                mv = None
                if with_move:
                    mv = "%d,%d,%d,%s" % (pos // 6 + 1, pos % 6 + 1, q, DIRCH[d])
                res.append((score, ny, no, kind, mv))
    res.sort(key=lambda t: t[0], reverse=True)
    return res

def _negamax(you, opp, depth, alpha, beta, ctx):
    if depth == 0:
        return _evaluate(you, opp)
    ctx[1] += 1
    if (ctx[1] & 127) == 0 and time.time() > ctx[0]:
        raise _Abort
    tt = ctx[2]
    key = you | (opp << 36)
    a0 = alpha
    ent = tt.get(key)
    if ent is not None and ent[1] >= depth:
        v, d, f = ent
        if f == 0:
            return v
        if f == 1 and v <= alpha:
            return v     # upper bound
        if f == 2 and v >= beta:
            return v     # lower bound
    best = -INF
    for score, ny, no, kind, _ in _gen(you, opp, False):
        if kind == 1:
            v = BIG + depth
        elif kind == -1:
            v = -(BIG + depth)
        elif kind == 2:
            v = 0
        else:
            v = -_negamax(no, ny, depth - 1, -beta, -alpha, ctx)
        if v > best:
            best = v
        if v > alpha:
            alpha = v
            if alpha >= beta:
                break
    if best <= a0:
        tt[key] = (best, depth, 1)
    elif best >= beta:
        tt[key] = (best, depth, 2)
    else:
        tt[key] = (best, depth, 0)
    return best

def _root_once(you, opp, depth, ctx):
    alpha = -INF
    beta = INF
    best = -INF
    bmv = None
    for score, ny, no, kind, mv in _gen(you, opp, True):
        if kind == 1:
            v = BIG + depth
        elif kind == -1:
            v = -(BIG + depth)
        elif kind == 2:
            v = 0
        else:
            v = -_negamax(no, ny, depth - 1, -beta, -alpha, ctx)
        if v > best:
            best = v
            bmv = mv
        if v > alpha:
            alpha = v
    return best, bmv

def _decide(you, opp):
    empty = ALL36 ^ (you | opp)
    # guaranteed legal fallback
    b = empty & -empty
    pos = b.bit_length() - 1
    fallback = "%d,%d,0,L" % (pos // 6 + 1, pos % 6 + 1)
    if not empty:
        return fallback
    ctx = [time.time() + 0.8, 0, {}]   # deadline, node count, TT
    best_move = fallback
    try:
        depth = 1
        while depth <= 20:
            v, mv = _root_once(you, opp, depth, ctx)
            if mv is not None:
                best_move = mv
            if v >= BIG or v <= -BIG + 30:
                break
            if time.time() > ctx[0] - 0.05:
                break
            depth += 1
    except _Abort:
        pass
    except Exception:
        return fallback
    return best_move

def policy(you, opponent):
    try:
        yb = 0
        ob = 0
        for r in range(6):
            yr = you[r]
            orw = opponent[r]
            base = r * 6
            for c in range(6):
                if yr[c]:
                    yb |= 1 << (base + c)
                elif orw[c]:
                    ob |= 1 << (base + c)
        return _decide(yb, ob)
    except Exception:
        # absolute fallback: first empty cell, rotate quadrant 0 left
        try:
            for r in range(6):
                for c in range(6):
                    if not you[r][c] and not opponent[r][c]:
                        return "%d,%d,0,L" % (r + 1, c + 1)
        except Exception:
            pass
        return "1,1,0,L"
