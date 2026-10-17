
import numpy as np
import time

TIME_LIMIT = 0.70
WIN = 10_000_000
INF = 10 ** 9

# ---------------- static tables ----------------
def _lines():
    L = []
    for r in range(6):
        L.append([r * 6 + c for c in range(6)])
    for c in range(6):
        L.append([r * 6 + c for r in range(6)])
    L.append([i * 6 + i for i in range(6)])
    L.append([i * 6 + (5 - i) for i in range(6)])
    L.append([i * 6 + (i + 1) for i in range(5)])
    L.append([(i + 1) * 6 + i for i in range(5)])
    L.append([i * 6 + (4 - i) for i in range(5)])
    L.append([(i + 1) * 6 + (5 - i) for i in range(5)])
    return L

LINES = _lines()
NL = len(LINES)
LINE_IDX = np.array([ln + [36] * (6 - len(ln)) for ln in LINES], dtype=np.intp)
LINE_FLAT = LINE_IDX.reshape(-1)
POW3_6 = np.array([3 ** k for k in range(6)], dtype=np.int64)
POW3_37 = np.array([3 ** k for k in range(36)] + [0], dtype=np.int64)
LID = np.arange(NL)[None, :]
SWAP = np.array([0, 2, 1], dtype=np.int8)

def _perms():
    perms = []
    for q in range(4):
        r0, c0 = 3 * (q // 2), 3 * (q % 2)
        for d in ('L', 'R'):
            p = np.arange(37, dtype=np.intp)
            for i in range(3):
                for j in range(3):
                    if d == 'R':
                        oi, oj = 2 - j, i
                    else:
                        oi, oj = j, 2 - i
                    p[(r0 + i) * 6 + c0 + j] = (r0 + oi) * 6 + c0 + oj
            perms.append(p)
    return perms

PERMS = _perms()

M_W = [0, 1, 4, 15, 150, 0]
O_W = [0, 1, 5, 18, 20000, 0]
POS = [0] * 36
for (r, c) in [(1, 1), (1, 4), (4, 1), (4, 4)]:
    POS[r * 6 + c] = 3
for (r, c) in [(2, 2), (2, 3), (3, 2), (3, 3)]:
    POS[r * 6 + c] = 2

OFF = 1 << 24
MASK30 = (1 << 30) - 1

def _build_packed():
    P = np.full((NL, 729), OFF, dtype=np.int64)
    for l, cells in enumerate(LINES):
        L = len(cells)
        for idx in range(3 ** L):
            d = []
            x = idx
            for k in range(L):
                d.append(x % 3)
                x //= 3
            s = 0
            w1 = 0
            w2 = 0
            t4 = 0
            for st in range(L - 4):
                w = d[st:st + 5]
                c1 = w.count(1)
                c2 = w.count(2)
                if c1 and c2:
                    continue
                if c1 == 5:
                    w1 = 1
                elif c2 == 5:
                    w2 = 1
                elif c1:
                    s += M_W[c1]
                    if c1 == 4:
                        t4 += 1
                elif c2:
                    s -= O_W[c2]
            if l < 6:
                for k in range(L):
                    if d[k] == 1:
                        s += POS[cells[k]]
                    elif d[k] == 2:
                        s -= POS[cells[k]]
            P[l, idx] = (s + OFF) + (w1 << 30) + (w2 << 36) + (t4 << 42)
    return P

PACKED = _build_packed()

class _Timeout(Exception):
    pass

_deadline = 0.0

# ---------------- vectorized expansion ----------------
def expand(board, ply, dedupe):
    empties = np.flatnonzero(board[:36] == 0)
    n = empties.size
    base = np.repeat(board[None, :], n, axis=0)
    base[np.arange(n), empties] = 1
    ch = np.concatenate([base[:, p] for p in PERMS], axis=0)
    lines = ch[:, LINE_FLAT].astype(np.int64).reshape(-1, NL, 6)
    idx = lines @ POW3_6
    tot = PACKED[LID, idx].sum(axis=1)
    score = (tot & MASK30) - NL * OFF
    w1 = ((tot >> 30) & 63) > 0
    w2 = ((tot >> 36) & 63) > 0
    t4 = (tot >> 42) & 63
    score = score + (t4 >= 2) * 600
    wv = WIN - ply
    val = np.where(w1 & w2, 0, np.where(w1, wv, np.where(w2, -wv, score)))
    term = w1 | w2
    if n == 1:
        val = np.where(term, val, 0)
        term = np.ones_like(term)
    if dedupe:
        keys = ch @ POW3_37
        _, ui = np.unique(keys, return_index=True)
        return ch[ui], val[ui], term[ui], ui, empties, n
    return ch, val, term, None, empties, n

# ---------------- search ----------------
def search(board, depth, alpha, beta, ply):
    if time.perf_counter() > _deadline:
        raise _Timeout()
    ch, val, term, _, _, _ = expand(board, ply, depth > 1)
    if depth == 1:
        return int(val.max())
    order = np.argsort(-val, kind='stable')
    best = -INF
    for j in order:
        j = int(j)
        if term[j]:
            v = int(val[j])
        else:
            v = -search(SWAP[ch[j]], depth - 1, -beta, -alpha, ply + 1)
        if v > best:
            best = v
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break
    return best

# ---------------- fallback ----------------
def _fallback(you, opponent):
    for r in range(6):
        for c in range(6):
            try:
                y = int(you[r][c])
                o = int(opponent[r][c])
            except Exception:
                y, o = 0, 0
            if y == 0 and o == 0:
                return f"{r + 1},{c + 1},0,L"
    return "1,1,0,L"

# ---------------- policy ----------------
def policy(you, opponent):
    global _deadline
    t0 = time.perf_counter()
    _deadline = t0 + TIME_LIMIT
    try:
        yf = np.asarray(you).reshape(-1)[:36]
        of = np.asarray(opponent).reshape(-1)[:36]
        b36 = np.zeros(36, dtype=np.int8)
        b36[yf != 0] = 1
        b36[of != 0] = 2
        board = np.concatenate([b36, np.zeros(1, dtype=np.int8)])

        ch, val, term, ui, empties, n = expand(board, 0, True)
        nc = len(ch)

        def mv(k):
            j = int(ui[k])
            rot = j // n
            p = j % n
            cell = int(empties[p])
            return f"{cell // 6 + 1},{cell % 6 + 1},{rot // 2},{'L' if rot % 2 == 0 else 'R'}"

        vals = val.astype(np.int64)
        order = np.argsort(-vals, kind='stable')
        best = int(order[0])
        if vals[best] >= WIN - 1:
            return mv(best)

        depth = 2
        while depth <= n and depth <= 40:
            new_vals = np.full(nc, -INF, dtype=np.int64)
            alpha = -INF
            it_best = -1
            it_val = -INF
            done = 0
            try:
                for k in order:
                    k = int(k)
                    if term[k]:
                        v = int(val[k])
                    else:
                        v = -search(SWAP[ch[k]], depth - 1, -INF, -alpha, 1)
                    new_vals[k] = v
                    done += 1
                    if v > it_val:
                        it_val = v
                        it_best = k
                    if v > alpha:
                        alpha = v
            except _Timeout:
                if done > 0 and it_best >= 0:
                    best = it_best
                break
            best = it_best
            order = np.argsort(-new_vals, kind='stable')
            if it_val >= WIN - 100 or it_val <= -WIN + 100:
                break
            depth += 1

        move = mv(best)
        # legality sanity check
        r, c, q, d = move.split(',')
        r, c = int(r) - 1, int(c) - 1
        if b36[r * 6 + c] != 0:
            return _fallback(you, opponent)
        return move
    except Exception:
        return _fallback(you, opponent)
