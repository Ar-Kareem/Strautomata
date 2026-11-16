
import time

if hasattr(int, "bit_count"):
    pc = int.bit_count
else:
    def pc(x):
        return bin(x).count("1")

# ---------- Board layout: bit index = quad*9 + localrow*3 + localcol ----------
BITIDX = [[0] * 6 for _ in range(6)]
for r in range(6):
    for c in range(6):
        q = (r // 3) * 2 + (c // 3)
        BITIDX[r][c] = q * 9 + (r % 3) * 3 + (c % 3)
BIT = [[1 << BITIDX[r][c] for c in range(6)] for r in range(6)]
QMASK = [0x1FF << (9 * q) for q in range(4)]
FULL = (1 << 36) - 1


def _rot_local(v, cw):
    out = 0
    for r in range(3):
        for c in range(3):
            if cw:
                sr, sc = 2 - c, r
            else:
                sr, sc = c, 2 - r
            if (v >> (sr * 3 + sc)) & 1:
                out |= 1 << (r * 3 + c)
    return out


ROT_L = [_rot_local(v, False) for v in range(512)]
ROT_R = [_rot_local(v, True) for v in range(512)]
DIRCH = ("L", "R")

# ---------- Lines ----------
LINES = []
for r in range(6):
    for c0 in range(2):
        m = 0
        for k in range(5):
            m |= BIT[r][c0 + k]
        LINES.append(m)
for c in range(6):
    for r0 in range(2):
        m = 0
        for k in range(5):
            m |= BIT[r0 + k][c]
        LINES.append(m)
for r0 in range(2):
    for c0 in range(2):
        m = 0
        for k in range(5):
            m |= BIT[r0 + k][c0 + k]
        LINES.append(m)
for r0 in range(2):
    for c0 in range(4, 6):
        m = 0
        for k in range(5):
            m |= BIT[r0 + k][c0 - k]
        LINES.append(m)

LINES_FOR = []
for q in range(4):
    for bi in range(36):
        b = 1 << bi
        LINES_FOR.append([L for L in LINES if (L & QMASK[q]) or (L & b)])

CENTERS = 0
for q in range(4):
    CENTERS |= 1 << (q * 9 + 4)

W = (0, 1, 4, 16, 80, 400)
WIN = 1000000
INF = 10 ** 9


class Timeout(Exception):
    pass


DEADLINE = [0.0]


def has5(b, lines):
    for L in lines:
        if b & L == L:
            return True
    return False


def has5_all(b):
    return has5(b, LINES)


def evaluate(me, opp):
    s = 0
    for L in LINES:
        mm = me & L
        oo = opp & L
        if oo == 0:
            if mm:
                s += W[pc(mm)]
        elif mm == 0:
            s -= W[pc(oo)]
    s += 3 * (pc(me & CENTERS) - pc(opp & CENTERS))
    return s


def gen(me, opp):
    occ = me | opp
    rotm = []
    roto = []
    basem = []
    for q in range(4):
        sh = 9 * q
        bm = me & ~QMASK[q]
        bo = opp & ~QMASK[q]
        vm = (me >> sh) & 511
        vo = (opp >> sh) & 511
        rotm.append((bm | (ROT_L[vm] << sh), bm | (ROT_R[vm] << sh)))
        roto.append((bo | (ROT_L[vo] << sh), bo | (ROT_R[vo] << sh)))
        basem.append(bm)
    res = []
    seen = set()
    for bi in range(36):
        b = 1 << bi
        if occ & b:
            continue
        qp = bi // 9
        for q in range(4):
            no_pair = roto[q]
            if q == qp:
                sh = 9 * q
                vm = ((me | b) >> sh) & 511
                bm = basem[q]
                nm_pair = (bm | (ROT_L[vm] << sh), bm | (ROT_R[vm] << sh))
            else:
                rp = rotm[q]
                nm_pair = (rp[0] | b, rp[1] | b)
            lidx = q * 36 + bi
            for di in (0, 1):
                nm = nm_pair[di]
                no = no_pair[di]
                key = nm | (no << 36)
                if key in seen:
                    continue
                seen.add(key)
                res.append((nm, no, (bi * 4 + q) * 2 + di, lidx))
    return res


def decode(code):
    di = code & 1
    code >>= 1
    q = code & 3
    bi = code >> 2
    qp = bi // 9
    li = bi % 9
    r = (qp // 2) * 3 + li // 3 + 1
    c = (qp % 2) * 3 + li % 3 + 1
    return "%d,%d,%d,%s" % (r, c, q, DIRCH[di])


def search(me, opp, depth, alpha, beta):
    if time.perf_counter() > DEADLINE[0]:
        raise Timeout
    best = -INF
    pending = []
    for nm, no, code, lidx in gen(me, opp):
        lines = LINES_FOR[lidx]
        wm = has5(nm, lines)
        wo = has5(no, lines)
        if wm:
            if wo:
                v = 0
            else:
                return WIN + depth
        elif wo:
            v = -WIN - depth
        elif (nm | no) == FULL:
            v = 0
        elif depth <= 1:
            v = evaluate(nm, no)
        else:
            pending.append((evaluate(nm, no), nm, no))
            continue
        if v > best:
            best = v
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    return best
    if pending:
        pending.sort(reverse=True)
        for _, nm, no in pending:
            v = -search(no, nm, depth - 1, -beta, -alpha)
            if v > best:
                best = v
                if v > alpha:
                    alpha = v
                    if alpha >= beta:
                        return best
    return best


def _fallback(you, opponent):
    for r in range(6):
        for c in range(6):
            if not you[r][c] and not opponent[r][c]:
                return "%d,%d,0,R" % (r + 1, c + 1)
    return "1,1,0,R"


def policy(you, opponent):
    start = time.perf_counter()
    DEADLINE[0] = start + 0.7
    try:
        me = 0
        opp = 0
        for r in range(6):
            for c in range(6):
                if you[r][c]:
                    me |= BIT[r][c]
                elif opponent[r][c]:
                    opp |= BIT[r][c]

        children = gen(me, opp)
        if not children:
            return _fallback(you, opponent)

        root = []
        for nm, no, code, lidx in children:
            lines = LINES_FOR[lidx]
            wm = has5(nm, lines)
            wo = has5(no, lines)
            if wm and not wo:
                return decode(code)
            if wm and wo:
                v = 0
                term = True
            elif wo:
                v = -WIN
                term = True
            elif (nm | no) == FULL:
                v = 0
                term = True
            else:
                v = evaluate(nm, no)
                term = False
            root.append([v, nm, no, code, term])

        root.sort(key=lambda x: -x[0])
        best_code = root[0][3]
        if len(root) == 1:
            return decode(best_code)

        depth = 2
        while depth <= 8:
            alpha = -INF
            cur_best = None
            cur_best_v = -INF
            completed = 0
            try:
                for item in root:
                    v, nm, no, code, term = item
                    if term:
                        val = v
                    else:
                        val = -search(no, nm, depth - 1, -INF, -alpha)
                    item[0] = val
                    if val > cur_best_v:
                        cur_best_v = val
                        cur_best = code
                        if val > alpha:
                            alpha = val
                    completed += 1
            except Timeout:
                if completed >= 1 and cur_best is not None:
                    if cur_best_v > -WIN // 2 or completed == len(root):
                        best_code = cur_best
                    else:
                        chosen = None
                        for item in root[completed:]:
                            if not item[4]:
                                chosen = item[3]
                                break
                        best_code = chosen if chosen is not None else cur_best
                break
            best_code = cur_best
            root.sort(key=lambda x: -x[0])
            if cur_best_v >= WIN // 2 or cur_best_v <= -WIN // 2:
                break
            if time.perf_counter() > DEADLINE[0]:
                break
            depth += 1

        return decode(best_code)
    except Exception:
        return _fallback(you, opponent)
