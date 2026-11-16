
import time

# ---------------- precomputation ----------------
if hasattr(int, "bit_count"):
    def pc(x):
        return x.bit_count()
else:
    def pc(x):
        return bin(x).count("1")

WIN = 100000
INF = 10 ** 9
BUDGET = 0.75
W = [0, 1, 4, 12, 50, 200]

LINES = []
for r in range(6):
    for c in range(2):
        m = 0
        for k in range(5):
            m |= 1 << (r * 6 + c + k)
        LINES.append(m)
for c in range(6):
    for r in range(2):
        m = 0
        for k in range(5):
            m |= 1 << ((r + k) * 6 + c)
        LINES.append(m)
for r in range(2):
    for c in range(2):
        m = 0
        for k in range(5):
            m |= 1 << ((r + k) * 6 + c + k)
        LINES.append(m)
        m = 0
        for k in range(5):
            m |= 1 << ((r + k) * 6 + (5 - c - k))
        LINES.append(m)

CENTERS = (1 << 7) | (1 << 10) | (1 << 25) | (1 << 28)

MH = sum(1 << (r * 6 + c) for r in range(6) for c in range(2))
MV = sum(1 << (r * 6 + c) for r in range(2) for c in range(6))
MD = sum(1 << (r * 6 + c) for r in range(2) for c in range(2))
MA = sum(1 << (r * 6 + c) for r in range(2) for c in range(4, 6))

S0 = [0, 3, 18, 21]
QMASK = []
for q in range(4):
    br, bc = 3 * (q >> 1), 3 * (q & 1)
    m = 0
    for lr in range(3):
        for lc in range(3):
            m |= 1 << ((br + lr) * 6 + bc + lc)
    QMASK.append(m)
FULL = (1 << 36) - 1
NOTQ = [FULL ^ m for m in QMASK]

DEST = [[0] * 36 for _ in range(8)]
for q in range(4):
    br, bc = 3 * (q >> 1), 3 * (q & 1)
    for d in range(2):  # 0 = L (anticlockwise), 1 = R (clockwise)
        qd = 2 * q + d
        for i in range(36):
            r, c = divmod(i, 6)
            if br <= r < br + 3 and bc <= c < bc + 3:
                lr, lc = r - br, c - bc
                if d == 1:
                    nr, nc = lc, 2 - lr
                else:
                    nr, nc = 2 - lc, lr
                j = (br + nr) * 6 + (bc + nc)
            else:
                j = i
            DEST[qd][i] = 1 << j

RTAB = []
for qd in range(8):
    q = qd >> 1
    br, bc = 3 * (q >> 1), 3 * (q & 1)
    tab = [0] * 512
    for k in range(512):
        v = 0
        for lr in range(3):
            for lc in range(3):
                if (k >> (lr * 3 + lc)) & 1:
                    v |= DEST[qd][(br + lr) * 6 + bc + lc]
        tab[k] = v
    RTAB.append(tab)


def rotate(b, qd):
    q = qd >> 1
    s0 = S0[q]
    k = ((b >> s0) & 7) | (((b >> (s0 + 6)) & 7) << 3) | (((b >> (s0 + 12)) & 7) << 6)
    return (b & NOTQ[q]) | RTAB[qd][k]


def has5(b):
    if (b & (b >> 1) & (b >> 2) & (b >> 3) & (b >> 4)) & MH:
        return True
    if (b & (b >> 6) & (b >> 12) & (b >> 18) & (b >> 24)) & MV:
        return True
    if (b & (b >> 7) & (b >> 14) & (b >> 21) & (b >> 28)) & MD:
        return True
    if (b & (b >> 5) & (b >> 10) & (b >> 15) & (b >> 20)) & MA:
        return True
    return False


def evaluate(a, b):
    s = 0
    for m in LINES:
        x = a & m
        if x:
            if not (b & m):
                s += W[pc(x)]
        else:
            y = b & m
            if y:
                s -= W[pc(y)]
    return s + 3 * (pc(a & CENTERS) - pc(b & CENTERS))


class Timeout(Exception):
    pass


def search(my, op, depth, alpha, beta, ply, deadline):
    if time.perf_counter() > deadline:
        raise Timeout()
    occ = my | op
    empties = [i for i in range(36) if not (occ >> i) & 1]
    full = len(empties) == 1
    check_win = pc(my) >= 4
    best = -INF
    seen = set()
    children = []
    for qd in range(8):
        mr = rotate(my, qd)
        orr = rotate(op, qd)
        ow = has5(orr)
        dest = DEST[qd]
        for i in empties:
            m2 = mr | dest[i]
            key = (m2, orr)
            if key in seen:
                continue
            seen.add(key)
            mw = has5(m2) if check_win else False
            if mw:
                v = 0 if ow else WIN - ply
            elif ow:
                v = -WIN + ply
            elif full:
                v = 0
            elif depth <= 1:
                v = evaluate(m2, orr)
            else:
                children.append((evaluate(m2, orr), m2, orr))
                continue
            if v > best:
                best = v
                if best > alpha:
                    alpha = best
                    if alpha >= beta:
                        return best
    if children:
        children.sort(reverse=True)
        for e, m2, o2 in children:
            v = -search(o2, m2, depth - 1, -beta, -alpha, ply + 1, deadline)
            if v > best:
                best = v
                if best > alpha:
                    alpha = best
                    if alpha >= beta:
                        return best
    return best


def move_str(i, qd):
    return "%d,%d,%d,%s" % (i // 6 + 1, i % 6 + 1, qd >> 1, "L" if (qd & 1) == 0 else "R")


def choose(my, op, empties, t0):
    deadline = t0 + BUDGET
    seen = set()
    roots = []
    full = len(empties) == 1
    for qd in range(8):
        mr = rotate(my, qd)
        orr = rotate(op, qd)
        ow = has5(orr)
        dest = DEST[qd]
        for i in empties:
            m2 = mr | dest[i]
            key = (m2, orr)
            if key in seen:
                continue
            seen.add(key)
            mw = has5(m2)
            if mw and not ow:
                return move_str(i, qd)
            if mw and ow:
                term = 0
            elif ow:
                term = -WIN
            elif full:
                term = 0
            else:
                term = None
            roots.append([0, m2, orr, i, qd, term])
    for rt in roots:
        rt[0] = rt[5] if rt[5] is not None else evaluate(rt[1], rt[2])
    roots.sort(key=lambda x: -x[0])
    best_move = move_str(roots[0][3], roots[0][4])
    if abs(roots[0][0]) >= WIN - 100:
        return best_move
    depth = 2
    while depth <= len(empties):
        alpha = -INF
        beta = INF
        cur_best = None
        try:
            for rt in roots:
                if rt[5] is not None:
                    v = rt[5]
                else:
                    v = -search(rt[2], rt[1], depth - 1, -beta, -alpha, 1, deadline)
                rt[0] = v
                if v > alpha:
                    alpha = v
                    cur_best = rt
        except Timeout:
            if cur_best is not None:
                best_move = move_str(cur_best[3], cur_best[4])
            break
        roots.sort(key=lambda x: -x[0])
        best_move = move_str(roots[0][3], roots[0][4])
        if abs(roots[0][0]) >= WIN - 100:
            break
        depth += 1
    return best_move


def policy(you, opponent):
    t0 = time.perf_counter()
    my = 0
    op = 0
    for r in range(6):
        for c in range(6):
            if int(you[r][c]) == 1:
                my |= 1 << (r * 6 + c)
            elif int(opponent[r][c]) == 1:
                op |= 1 << (r * 6 + c)
    occ = my | op
    empties = [i for i in range(36) if not (occ >> i) & 1]
    if not empties:
        return "1,1,0,R"
    fallback = move_str(empties[0], 1)
    try:
        mv = choose(my, op, empties, t0)
        if mv:
            parts = mv.split(",")
            r, c = int(parts[0]) - 1, int(parts[1]) - 1
            if 0 <= r < 6 and 0 <= c < 6 and not (occ >> (r * 6 + c)) & 1:
                return mv
    except Exception:
        pass
    return fallback
