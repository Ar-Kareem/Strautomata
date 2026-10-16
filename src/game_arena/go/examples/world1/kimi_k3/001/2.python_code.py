
import time

W = 21
POS = []
RC = {}
NEI = {}
LINE = {}
OFF2 = []
for dr in (-2, -1, 0, 1, 2):
    for dc in (-2, -1, 0, 1, 2):
        if dr or dc:
            OFF2.append((dr * W + dc, max(abs(dr), abs(dc))))
for r in range(1, 20):
    for c in range(1, 20):
        p = r * W + c
        POS.append(p)
        RC[p] = (r, c)
        NEI[p] = (p - 1, p + 1, p - W, p + W)
        LINE[p] = min(r - 1, 19 - r, c - 1, 19 - c)
BIT = {}
for p in POS:
    r, c = RC[p]
    BIT[p] = 1 << ((r - 1) * 19 + (c - 1))
STAR = set(r * W + c for r in (4, 10, 16) for c in (4, 10, 16))
CORNER = set(r * W + c for r in (3, 4, 16, 17) for c in (3, 4, 16, 17))
STRAT = STAR | CORNER
LB_EARLY = (-6.0, -3.0, 2.0, 2.5, 1.0, 0, 0, 0, 0, 0)
LB_LATE = (-2.0, -0.5, 0, 0, 0, 0, 0, 0, 0, 0)

gmark = [0] * 441
lmark = [0] * 441
amark = [0] * 441
emark = [0] * 441
tmark = [0] * 441
gstamp = 0
astamp = 0
estamp = 0
tstamp = 0
HIST = set()
PREV_TOTAL = 0
START = 0.0


def get_group(board, pos):
    global gstamp
    gstamp += 1
    gs = gstamp
    col = board[pos]
    stack = [pos]
    gmark[pos] = gs
    stones = []
    libs = []
    while stack:
        p = stack.pop()
        stones.append(p)
        for q in NEI[p]:
            v = board[q]
            if v == col:
                if gmark[q] != gs:
                    gmark[q] = gs
                    stack.append(q)
            elif v == 0:
                if lmark[q] != gs:
                    lmark[q] = gs
                    libs.append(q)
    return stones, libs


def analyze(board, pos, color):
    """Simulate move; return feature tuple or None if illegal (suicide)."""
    global astamp
    if board[pos] != 0:
        return None
    astamp += 1
    ast = astamp
    enemy = color ^ 3
    friendly = []
    enemyg = []
    for q in NEI[pos]:
        v = board[q]
        if v == color and amark[q] != ast:
            st, lb = get_group(board, q)
            for s in st:
                amark[s] = ast
            friendly.append((st, lb))
        elif v == enemy and amark[q] != ast:
            st, lb = get_group(board, q)
            for s in st:
                amark[s] = ast
            enemyg.append((st, lb))
    captured = []
    for st, lb in enemyg:
        if len(lb) == 1:
            captured.extend(st)
    nb2 = board.copy()
    nb2[pos] = color
    for s in captured:
        nb2[s] = 0
    mst, mlb = get_group(nb2, pos)
    if not mlb:
        return None
    own_libs = len(mlb)
    saved = 0
    if own_libs >= 2:
        for st, lb in friendly:
            if len(lb) == 1:
                saved += len(st)
    weak = 0
    if own_libs >= 3:
        for st, lb in friendly:
            if len(lb) == 2:
                weak += len(st)
    ag = 0
    asz = 0
    for st, lb in enemyg:
        if len(lb) == 2:
            ag += 1
            asz += len(st)
    return (nb2, captured, own_libs, saved, weak, ag, asz,
            len(friendly), len(enemyg))


def evaluate(board):
    """Area score: stones + empty regions touching only one color."""
    global estamp
    estamp += 1
    es = estamp
    my = 0
    opp = 0
    for p in POS:
        v = board[p]
        if v == 1:
            my += 1
        elif v == 2:
            opp += 1
        elif emark[p] != es:
            stack = [p]
            emark[p] = es
            size = 0
            mask = 0
            while stack:
                x = stack.pop()
                size += 1
                for q in NEI[x]:
                    vq = board[q]
                    if vq == 0:
                        if emark[q] != es:
                            emark[q] = es
                            stack.append(q)
                    elif vq == 1:
                        mask |= 1
                    elif vq == 2:
                        mask |= 2
            if mask == 1:
                my += size
            elif mask == 2:
                opp += size
    return my - opp


def gen_candidates(board, total):
    cand = {}
    for p in POS:
        v = board[p]
        if v == 1 or v == 2:
            for off, d in OFF2:
                q = p + off
                if 0 <= q < 441 and board[q] == 0:
                    e = cand.get(q)
                    if e is None:
                        e = [99, 99]
                        cand[q] = e
                    if v == 1:
                        if d < e[0]:
                            e[0] = d
                    else:
                        if d < e[1]:
                            e[1] = d
    if total < 14:
        for p in STRAT:
            if board[p] == 0 and p not in cand:
                cand[p] = [99, 99]
    return cand


def prior(pos, d1, d2, total):
    line = LINE[pos]
    p = LB_EARLY[line] if total < 30 else LB_LATE[line]
    if d1 == 1:
        p += 1.0
    elif d1 == 2:
        p += 1.5
    if d2 == 1:
        p += 0.3
    elif d2 == 2:
        p += 1.2
    elif d2 == 3:
        p += 0.8
    if total < 40 and pos in STAR:
        p += 1.5
    return p


def move_score(f, pos, d1, d2, total):
    nb2, captured, own_libs, saved, weak, ag, asz, nf, ne = f
    s = prior(pos, d1, d2, total)
    nc = len(captured)
    if nc:
        s += 12 * nc + 4
    if saved:
        s += 11 * saved
    if weak:
        s += min(1.0 * weak, 5)
    if ag:
        s += min(3 * ag + 1.5 * asz, 15)
    if own_libs == 1:
        s += -18 if nc == 0 else -3
    elif own_libs == 2 and nc == 0:
        s -= 2.5
    if nf >= 2:
        s += 2.5 * (nf - 1)
    if ne >= 2 and own_libs >= 2:
        s += 3.0
    # isolated weak invasion deep in enemy zone without support
    if d1 > 2 and d2 <= 2 and own_libs <= 3 and nc == 0:
        s -= 4.0
    return s


def tactical_points(board, color):
    """Liberties of enemy groups with <=2 liberties (capture/atari points)."""
    global tstamp
    tstamp += 1
    ts = tstamp
    enemy = color ^ 3
    pts = set()
    for p in POS:
        if board[p] == enemy and tmark[p] != ts:
            st, lb = get_group(board, p)
            for s in st:
                tmark[s] = ts
            if len(lb) <= 2:
                pts.update(lb)
    return pts


def tactical_score(f):
    nc = len(f[1])
    rs = 0.0
    if nc:
        rs += 12 * nc + 4
    if f[5]:
        rs += min(3 * f[5] + 1.5 * f[6], 15)
    return rs


def best_tactical(board, color, limit=28):
    tp = tactical_points(board, color)
    best = 0.0
    for i, p in enumerate(tp):
        if i >= limit:
            break
        f = analyze(board, p, color)
        if f is None:
            continue
        rs = tactical_score(f)
        if rs > best:
            best = rs
    return best


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    global START
    START = time.perf_counter()
    try:
        return _policy(me, opponent)
    except Exception:
        try:
            board = [3] * 441
            for p in POS:
                board[p] = 0
            for (r, c) in me:
                board[int(r) * W + int(c)] = 1
            for (r, c) in opponent:
                board[int(r) * W + int(c)] = 2
            for p in POS:
                if board[p] == 0 and analyze(board, p, 1) is not None:
                    return RC[p]
        except Exception:
            pass
        return (0, 0)


def _policy(me, opponent):
    global HIST, PREV_TOTAL
    board = [3] * 441
    for p in POS:
        board[p] = 0
    my_bits = 0
    opp_bits = 0
    for (r, c) in me:
        r = int(r); c = int(c)
        p = r * W + c
        board[p] = 1
        my_bits |= BIT[p]
    for (r, c) in opponent:
        r = int(r); c = int(c)
        p = r * W + c
        board[p] = 2
        opp_bits |= BIT[p]
    total = len(me) + len(opponent)
    if total <= 1 or total < PREV_TOTAL - 12:
        HIST = set()
    HIST.add((my_bits, opp_bits))

    cand = gen_candidates(board, total)
    if not cand:
        PREV_TOTAL = total
        return (0, 0)

    eval0 = evaluate(board)
    scores = []
    for i, (pos, dd) in enumerate(cand.items()):
        if (i & 15) == 15 and time.perf_counter() - START > 0.80:
            break
        f = analyze(board, pos, 1)
        if f is None:
            continue
        mb = my_bits | BIT[pos]
        ob = opp_bits
        if f[1]:
            for s in f[1]:
                ob &= ~BIT[s]
        if (mb, ob) in HIST:
            continue  # superko / simple-ko safety
        s = move_score(f, pos, dd[0], dd[1], total)
        scores.append((s, pos, f, mb, ob))

    if not scores:
        PREV_TOTAL = total
        return (0, 0)

    scores.sort(key=lambda x: -x[0])
    empty_count = 361 - total
    best_final = -1e18
    best_item = None
    best_ev = 0
    limit = min(len(scores), 24)
    for i in range(limit):
        if i > 0:
            t = time.perf_counter() - START
            if t > 0.85:
                break
            if i >= 14 and t > 0.55:
                break
        s, pos, f, mb, ob = scores[i]
        b1 = f[0]
        e1 = evaluate(b1)
        opp_best = 0.0
        tp = tactical_points(b1, 2)
        for j, p2 in enumerate(tp):
            if j >= 24:
                break
            if (j & 7) == 7 and time.perf_counter() - START > 0.85:
                break
            f2 = analyze(b1, p2, 2)
            if f2 is None:
                continue
            rs = tactical_score(f2)
            e2 = evaluate(f2[0])
            val = rs + 1.2 * (e1 - e2)
            if rs > 0:
                val -= 0.75 * best_tactical(f2[0], 1)
            if val > opp_best:
                opp_best = val
        final = s + 1.2 * (e1 - eval0) - 0.9 * opp_best
        if final > best_final:
            best_final = final
            best_item = (s, pos, f, mb, ob)
            best_ev = e1

    if best_item is None:
        s, pos, f, mb, ob = scores[0]
        best_item = (s, pos, f, mb, ob)
        best_ev = evaluate(f[0])

    s, pos, f, mb, ob = best_item
    quiet = (len(f[1]) == 0 and f[3] == 0 and f[5] == 0)
    if (quiet and eval0 > 0 and (best_ev - eval0) <= 0
            and empty_count < 70 and total >= 120):
        PREV_TOTAL = total
        return (0, 0)

    HIST.add((mb, ob))
    PREV_TOTAL = total + 1 - len(f[1])
    return RC[pos]
