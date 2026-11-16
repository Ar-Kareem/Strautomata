
import time
from collections import deque

N = 6
DIRS = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
INF = 99
WIN = 1 << 30
TIE = 6  # tempo bonus per contested square (awarded to side to move)


def _bfs(b, side):
    dist = [INF] * 36
    dq = deque()
    bb = b
    for i, v in enumerate(bb):
        if v != side:
            continue
        r, c = divmod(i, 6)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                j = nr * 6 + nc
                if bb[j] != 0:
                    break
                if dist[j] > 1:
                    dist[j] = 1
                    dq.append(j)
                nr += dr
                nc += dc
    pop = dq.popleft
    app = dq.append
    while dq:
        i = pop()
        d = dist[i]
        nd = d + 1
        r, c = divmod(i, 6)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                j = nr * 6 + nc
                if bb[j] != 0:
                    break
                if dist[j] > nd:
                    dist[j] = nd
                    app(j)
                nr += dr
                nc += dc
    return dist


def _eval_base(b):
    """Return (score_for_player1, contested_count)."""
    d1 = _bfs(b, 1)
    d2 = _bfs(b, 2)
    s = 0
    cont = 0
    for i in range(36):
        if b[i] != 0:
            continue
        a = d1[i]
        c = d2[i]
        if a >= INF and c >= INF:
            continue
        if a < c:
            s += 16 + (min(c, 8) - min(a, 8))
        elif c < a:
            s -= 16 + (min(a, 8) - min(c, 8))
        else:
            cont += 1
    return s, cont


def _eval_full(b, stm):
    """Player-1 perspective value, contested squares awarded to side-to-move."""
    s, cont = _eval_base(b)
    return s + (TIE * cont if stm == 1 else -TIE * cont)


def _has_move(b, side):
    for i, v in enumerate(b):
        if v != side:
            continue
        r, c = divmod(i, 6)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 6 and 0 <= nc < 6 and b[nr * 6 + nc] == 0:
                return True
    return False


def _root_candidates(b, soft_deadline):
    """One entry per (amazon,destination): the eval-best arrow. Returns
    (entries sorted desc, total_full_moves, truncated)."""
    t0 = time.perf_counter()
    entries = []
    total = 0
    trunc = False
    for i, v in enumerate(b):
        if v != 1:
            continue
        r, c = divmod(i, 6)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                j = nr * 6 + nc
                if b[j] != 0:
                    break
                nb = list(b)
                nb[i] = 0
                nb[j] = 1
                rr, cc = divmod(j, 6)
                bestV = None
                bestA = -1
                for dr2, dc2 in DIRS:
                    r2, c2 = rr + dr2, cc + dc2
                    while 0 <= r2 < 6 and 0 <= c2 < 6:
                        k = r2 * 6 + c2
                        if nb[k] != 0:
                            break
                        total += 1
                        nb[k] = -1
                        V = _eval_full(nb, 2)
                        nb[k] = 0
                        if bestV is None or V > bestV:
                            bestV = V
                            bestA = k
                        r2 += dr2
                        c2 += dc2
                if bestA >= 0:
                    entries.append((bestV, i, j, bestA))
                if time.perf_counter() - t0 > soft_deadline:
                    trunc = True
                    break
                nr += dr
                nc += dc
            if trunc:
                break
        if trunc:
            break
    entries.sort(key=lambda x: -x[0])
    return entries, total, trunc


def _catastrophe(entries, b, deadline):
    """Penalize top moves that let one opponent arrow swing the eval a lot."""
    cand = entries[:14] if len(entries) > 14 else entries
    best = cand[0]
    best_final = None
    for (V, p, t, a) in cand:
        child = list(b)
        child[p] = 0
        child[t] = 1
        child[a] = -1
        dmg = 0
        for e in range(36):
            if child[e] != 0:
                continue
            child[e] = -1
            V2 = _eval_full(child, 2)
            child[e] = 0
            d = V - V2
            if d > dmg:
                dmg = d
        final = V - (dmg >> 1)
        if best_final is None or final > best_final:
            best_final = final
            best = (V, p, t, a)
        if time.perf_counter() > deadline:
            break
    return best


def _gen_moves(b, side):
    res = []
    for i, v in enumerate(b):
        if v != side:
            continue
        r, c = divmod(i, 6)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                j = nr * 6 + nc
                if b[j] != 0:
                    break
                nb = list(b)
                nb[i] = 0
                nb[j] = side
                rr, cc = divmod(j, 6)
                for dr2, dc2 in DIRS:
                    r2, c2 = rr + dr2, cc + dc2
                    while 0 <= r2 < 6 and 0 <= c2 < 6:
                        k = r2 * 6 + c2
                        if nb[k] != 0:
                            break
                        res.append((i, j, k))
                        r2 += dr2
                        c2 += dc2
                nr += dr
                nc += dc
    return res


def _negamax(b, depth, alpha, beta, side, ctx):
    if ctx['stop']:
        return 0
    ctx['nodes'] += 1
    if (ctx['nodes'] & 127) == 0 and time.perf_counter() > ctx['deadline']:
        ctx['stop'] = True
        return 0
    if not _has_move(b, side):
        return -(WIN + depth)
    if depth <= 0:
        v = _eval_full(b, side)
        return v if side == 1 else -v
    best = -WIN
    for (p, t, a) in _gen_moves(b, side):
        child = list(b)
        child[p] = 0
        child[t] = side
        child[a] = -1
        val = -_negamax(child, depth - 1, -beta, -alpha, 3 - side, ctx)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
        if ctx['stop']:
            break
    return best


def _deepen(b, deadline):
    Lfull = []
    for i, v in enumerate(b):
        if v != 1:
            continue
        r, c = divmod(i, 6)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                j = nr * 6 + nc
                if b[j] != 0:
                    break
                nb = list(b)
                nb[i] = 0
                nb[j] = 1
                rr, cc = divmod(j, 6)
                for dr2, dc2 in DIRS:
                    r2, c2 = rr + dr2, cc + dc2
                    while 0 <= r2 < 6 and 0 <= c2 < 6:
                        k = r2 * 6 + c2
                        if nb[k] != 0:
                            break
                        nb[k] = -1
                        V = _eval_full(nb, 2)
                        nb[k] = 0
                        Lfull.append((V, i, j, k))
                        r2 += dr2
                        c2 += dc2
                nr += dr
                nc += dc
    if not Lfull:
        return None
    tm = len(Lfull)
    if tm <= 25:
        md = 6
    elif tm <= 50:
        md = 5
    elif tm <= 90:
        md = 4
    else:
        md = 3
    order = sorted(Lfull, key=lambda x: -x[0])
    best = (order[0][1], order[0][2], order[0][3])
    for depth in range(2, md + 1):
        ctx = {'deadline': deadline, 'stop': False, 'nodes': 0}
        alpha = -WIN
        beta = WIN
        iter_best = None
        iter_bestV = -WIN
        newvals = []
        completed = True
        for (V0, p, t, a) in order:
            child = list(b)
            child[p] = 0
            child[t] = 1
            child[a] = -1
            val = -_negamax(child, depth - 1, -beta, -alpha, 2, ctx)
            if ctx['stop']:
                completed = False
                break
            newvals.append((val, p, t, a))
            if val > iter_bestV:
                iter_bestV = val
                iter_best = (p, t, a)
            if val > alpha:
                alpha = val
        if completed and iter_best is not None:
            best = iter_best
            order = sorted(newvals, key=lambda x: -x[0])
        else:
            break
        if time.perf_counter() > deadline - 0.04:
            break
    return best


def policy(board) -> str:
    t0 = time.perf_counter()
    b = [int(x) for x in board.ravel()]

    if not _has_move(b, 1):
        return "0,0:0,0:0,0"  # environment should never call in this state

    entries, total_moves, trunc = _root_candidates(b, 0.50)
    if not entries:
        return "0,0:0,0:0,0"

    best = entries[0]  # (V,p,t,a), always legal

    if time.perf_counter() - t0 < 0.62:
        best = _catastrophe(entries, b, t0 + 0.74)

    if (not trunc) and total_moves <= 120 and (time.perf_counter() - t0) < 0.55:
        mv = _deepen(b, t0 + 0.90)
        if mv is not None:
            best = (0, mv[0], mv[1], mv[2])

    _, p, t, a = best

    def s(idx):
        return "{},{}".format(idx // 6, idx % 6)

    return "{}:{}:{}".format(s(p), s(t), s(a))
