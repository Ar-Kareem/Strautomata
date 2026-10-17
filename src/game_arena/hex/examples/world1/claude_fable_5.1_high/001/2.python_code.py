
import math
import time
import numpy as np

N = 11
NN = N * N
EPS = 1e-3
GB = 20.0
BIG = 1e9
TIME_BUDGET = 0.72

DIRS = ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0))
BDIRS = ((-2, 1), (-1, 2), (1, 1), (2, -1), (1, -2), (-1, -1))


def _in(r, c):
    return 0 <= r < N and 0 <= c < N


NEIGH = []
BRIDGE = []
_ea = []
_eb = []
for r in range(N):
    for c in range(N):
        i = r * N + c
        nb = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if _in(rr, cc):
                j = rr * N + cc
                nb.append(j)
                if i < j:
                    _ea.append(i)
                    _eb.append(j)
        NEIGH.append(nb)
        br = []
        for dr, dc in BDIRS:
            rr, cc = r + dr, c + dc
            if _in(rr, cc):
                br.append(rr * N + cc)
        BRIDGE.append(br)
EA = np.array(_ea)
EB = np.array(_eb)
DI = np.arange(NN)

_ba = []
_bb = []
_bc1 = []
_bc2 = []
BR_T = (((-2, 1), (-1, 0), (-1, 1)), ((-1, 2), (-1, 1), (0, 1)), ((1, 1), (0, 1), (1, 0)))
for r in range(N):
    for c in range(N):
        i = r * N + c
        for d, c1, c2 in BR_T:
            rr, cc = r + d[0], c + d[1]
            if _in(rr, cc):
                _ba.append(i)
                _bb.append(rr * N + cc)
                _bc1.append((r + c1[0]) * N + (c + c1[1]))
                _bc2.append((r + c2[0]) * N + (c + c2[1]))
BA = np.array(_ba)
BB = np.array(_bb)
BC1 = np.array(_bc1)
BC2 = np.array(_bc2)

TEMPL = {}
IS_SRC = {}
IS_SNK = {}


def _idx(r, c):
    return r * N + c


# black: top (row 0) -> bottom (row 10)
_src = np.array([_idx(0, c) for c in range(N)])
_snk = np.array([_idx(N - 1, c) for c in range(N)])
_ets = (np.array([_idx(1, c) for c in range(N - 1)]),
        np.array([_idx(0, c) for c in range(N - 1)]),
        np.array([_idx(0, c + 1) for c in range(N - 1)]))
_etk = (np.array([_idx(N - 2, c) for c in range(1, N)]),
        np.array([_idx(N - 1, c - 1) for c in range(1, N)]),
        np.array([_idx(N - 1, c) for c in range(1, N)]))
TEMPL['b'] = (_src, _snk, _ets, _etk)
IS_SRC['b'] = [(i // N) == 0 for i in range(NN)]
IS_SNK['b'] = [(i // N) == N - 1 for i in range(NN)]
# white: left (col 0) -> right (col 10)
_src = np.array([_idx(r, 0) for r in range(N)])
_snk = np.array([_idx(r, N - 1) for r in range(N)])
_ets = (np.array([_idx(r, 1) for r in range(N - 1)]),
        np.array([_idx(r, 0) for r in range(N - 1)]),
        np.array([_idx(r + 1, 0) for r in range(N - 1)]))
_etk = (np.array([_idx(r, N - 2) for r in range(1, N)]),
        np.array([_idx(r, N - 1) for r in range(1, N)]),
        np.array([_idx(r - 1, N - 1) for r in range(1, N)]))
TEMPL['w'] = (_src, _snk, _ets, _etk)
IS_SRC['w'] = [(i % N) == 0 for i in range(NN)]
IS_SNK['w'] = [(i % N) == N - 1 for i in range(NN)]


def _resistance(board, p, col):
    src, snk, ets, etk = TEMPL[col]
    q = 3 - p
    r = np.where(board == p, EPS, np.where(board == 0, 1.0, np.inf))
    g = 1.0 / (r[EA] + r[EB])
    L = np.zeros((NN, NN))
    L[EA, EB] = -g
    L[EB, EA] = -g
    diag = np.bincount(EA, g, NN) + np.bincount(EB, g, NN)
    gs = 1.0 / r[src]
    gk = 1.0 / r[snk]
    diag[src] += gs
    diag[snk] += gk
    b = np.zeros(NN)
    b[src] += gs
    m = (board[BA] == p) & (board[BB] == p) & (board[BC1] == 0) & (board[BC2] == 0)
    if m.any():
        a = BA[m]
        bb = BB[m]
        L[a, bb] -= GB
        L[bb, a] -= GB
        np.add.at(diag, a, GB)
        np.add.at(diag, bb, GB)
    st, c1, c2 = ets
    ms = (board[st] == p) & (board[c1] == 0) & (board[c2] == 0)
    src_t = st[ms]
    if src_t.size:
        diag[src_t] += GB
        b[src_t] += GB
    st, c1, c2 = etk
    mk = (board[st] == p) & (board[c1] == 0) & (board[c2] == 0)
    snk_t = st[mk]
    if snk_t.size:
        diag[snk_t] += GB
    diag[board == q] += 1.0
    L[DI, DI] += diag
    try:
        v = np.linalg.solve(L, b)
    except Exception:
        return 1e6
    I = float(np.sum(gs * (1.0 - v[src])))
    if src_t.size:
        I += GB * float(np.sum(1.0 - v[src_t]))
    if not (I > 1e-9):
        return 1e6
    R = 1.0 / I
    if R < 1e-6:
        R = 1e-6
    if R > 1e6:
        R = 1e6
    return R


def _score(board, my_col, op_col):
    rm = _resistance(board, 1, my_col)
    ro = _resistance(board, 2, op_col)
    return math.log(ro) - math.log(rm)


def _winning_cells(bl, p, col):
    is_src = IS_SRC[col]
    is_snk = IS_SNK[col]
    comp = [-1] * NN
    tsrc = []
    tsnk = []
    nc = 0
    for i in range(NN):
        if bl[i] == p and comp[i] == -1:
            stack = [i]
            comp[i] = nc
            ts = False
            tk = False
            while stack:
                x = stack.pop()
                if is_src[x]:
                    ts = True
                if is_snk[x]:
                    tk = True
                for y in NEIGH[x]:
                    if bl[y] == p and comp[y] == -1:
                        comp[y] = nc
                        stack.append(y)
            tsrc.append(ts)
            tsnk.append(tk)
            nc += 1
    res = []
    for i in range(NN):
        if bl[i] == 0:
            ts = is_src[i]
            tk = is_snk[i]
            for y in NEIGH[i]:
                if bl[y] == p:
                    cc = comp[y]
                    if tsrc[cc]:
                        ts = True
                    if tsnk[cc]:
                        tk = True
            if ts and tk:
                res.append(i)
    return res


def _tup(i):
    return (i // N, i % N)


def _search(board, empties, color, deadline):
    my_col = color
    op_col = 'w' if color == 'b' else 'b'
    bl = board.tolist()
    wins = _winning_cells(bl, 1, my_col)
    if wins:
        return _tup(wins[0])
    thr = _winning_cells(bl, 2, op_col)
    if thr:
        return _tup(thr[0])
    if len(empties) == 1:
        return _tup(empties[0])

    # root 1-ply for me
    my_s = {}
    best_e = empties[0]
    best_v = -float('inf')
    for e in empties:
        board[e] = 1
        s = _score(board, my_col, op_col)
        board[e] = 0
        my_s[e] = s
        if s > best_v:
            best_v = s
            best_e = e
        if time.time() > deadline:
            return _tup(best_e)
    order_me = sorted(empties, key=lambda x: -my_s[x])

    # root 1-ply for opponent
    op_s = {}
    for e in empties:
        board[e] = 2
        s = _score(board, my_col, op_col)
        board[e] = 0
        op_s[e] = s
        if time.time() > deadline:
            return _tup(order_me[0])
    order_op = sorted(empties, key=lambda x: op_s[x])

    cands = []
    seen = set()
    for e in order_me[:12]:
        if e not in seen:
            seen.add(e)
            cands.append(e)
    for e in order_op[:6]:
        if e not in seen:
            seen.add(e)
            cands.append(e)

    top_op = order_op[:8]
    top_me = order_me[:6]

    best_val = -float('inf')
    best_move = order_me[0]
    v2 = {}
    reply_vals = {}
    complete = {}
    timed_out = False
    for c in cands:
        if time.time() > deadline:
            timed_out = True
            break
        board[c] = 1
        bl = board.tolist()
        mw = _winning_cells(bl, 1, my_col)
        if len(mw) >= 2:
            board[c] = 0
            return _tup(c)
        if len(mw) == 1:
            D = [mw[0]]
        else:
            D = []
            ds = set()
            for lst in (top_op, top_me, NEIGH[c], BRIDGE[c]):
                for d in lst:
                    if d != c and board[d] == 0 and d not in ds:
                        ds.add(d)
                        D.append(d)
        val = float('inf')
        vals = {}
        comp = True
        for d in D:
            board[d] = 2
            s = _score(board, my_col, op_col)
            board[d] = 0
            vals[d] = s
            if s < val:
                val = s
            if val < best_val:
                comp = False
                break
            if time.time() > deadline:
                comp = False
                timed_out = True
                break
        board[c] = 0
        v2[c] = val
        reply_vals[c] = vals
        complete[c] = comp
        if val > best_val:
            best_val = val
            best_move = c
        if timed_out:
            break

    if timed_out:
        return _tup(best_move)

    comp_cands = [c for c in cands if c in complete and complete[c]]
    if not comp_cands:
        return _tup(best_move)

    top_me8 = order_me[:8]

    def my_best_response(c, d):
        bl2 = board.tolist()
        mw2 = _winning_cells(bl2, 1, my_col)
        if mw2:
            return BIG
        ow2 = _winning_cells(bl2, 2, op_col)
        if len(ow2) >= 2:
            return -BIG
        if len(ow2) == 1:
            E = [ow2[0]]
        else:
            E = []
            es = set()
            for lst in (top_me8, NEIGH[d], BRIDGE[d], NEIGH[c]):
                for e in lst:
                    if board[e] == 0 and e not in es:
                        es.add(e)
                        E.append(e)
        bv = -float('inf')
        for e in E:
            if time.time() > deadline:
                return None
            board[e] = 1
            s = _score(board, my_col, op_col)
            board[e] = 0
            if s > bv:
                bv = s
        if bv == -float('inf'):
            return None
        return bv

    v3 = {}
    deepened = set()
    while time.time() < deadline:
        cur = max(comp_cands, key=lambda x: v3.get(x, v2[x]))
        if cur in deepened:
            break
        vals = reply_vals[cur]
        ds = sorted(vals, key=lambda x: vals[x])
        cur_min = float('inf')
        ok = True
        board[cur] = 1
        for d in ds:
            if vals[d] >= cur_min:
                break
            board[d] = 2
            val3 = my_best_response(cur, d)
            board[d] = 0
            if val3 is None:
                ok = False
                if vals[d] < cur_min:
                    cur_min = vals[d]
                break
            if val3 < cur_min:
                cur_min = val3
        board[cur] = 0
        if cur_min == float('inf'):
            cur_min = v2[cur]
        v3[cur] = cur_min
        deepened.add(cur)
        if not ok:
            break

    final = max(comp_cands, key=lambda x: v3.get(x, v2[x]))
    return _tup(final)


def policy(me, opp, color):
    t0 = time.time()
    deadline = t0 + TIME_BUDGET
    board = np.zeros(NN, dtype=np.int8)
    occupied = set()
    for (r, c) in me:
        board[r * N + c] = 1
        occupied.add((r, c))
    for (r, c) in opp:
        board[r * N + c] = 2
        occupied.add((r, c))
    empties = [i for i in range(NN) if board[i] == 0]
    if not empties:
        return (0, 0)
    fallback = _tup(empties[0])
    if (5, 5) not in occupied:
        fallback = (5, 5)
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)
    try:
        mv = _search(board, empties, color, deadline)
        if mv is None or mv in occupied or not (0 <= mv[0] < N and 0 <= mv[1] < N):
            return fallback
        return (int(mv[0]), int(mv[1]))
    except Exception:
        return fallback
