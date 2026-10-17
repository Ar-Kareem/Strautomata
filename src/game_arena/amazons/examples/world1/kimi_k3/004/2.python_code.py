
import time
from collections import deque
import numpy as np

N = 6
NSQ = 36
_INF = 99
_WIN = 10_000_000
_DIRS = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))

def _build():
    ray = []
    cent = [0]*36
    for s in range(36):
        r, c = divmod(s, 6)
        lines = []
        for dr, dc in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            line = []
            rr, cc = r+dr, c+dc
            while 0 <= rr < 6 and 0 <= cc < 6:
                line.append(rr*6+cc)
                rr += dr; cc += dc
            lines.append(tuple(line))
        ray.append(tuple(lines))
    cent = [sum(len(l) for l in ray[s]) for s in range(36)]
    return ray, cent

RAY, CENT = _build()
_INF = 99

def _bfs(cells, side):
    dist = [99]*36
    dq = deque()
    for s, v in enumerate(cells):
        if v == side:
            dist[s] = 0
            dq.append(s)
    R = RAY
    C = cells
    ap = dq.append
    while dq:
        u = dq.popleft()
        nd = dist[u] + 1
        for line in R[u]:
            for q in line:
                if C[q] != 0:
                    break
                if dist[q] == 99:
                    dist[q] = nd
                    dq.append(q)
    return dist

def _count(cells, side):
    total = 0
    R = RAY
    C = cells
    for s, v in enumerate(C):
        if v == side:
            for line in R[s]:
                for q in line:
                    if C[q] == 0:
                        total += 1
                    else:
                        break
    return total

def _evaluate(cells):
    d1 = _bfs(cells, 1)
    d2 = _bfs(cells, 2)
    my = _count(cells, 1)
    op = _count(cells, 2)
    if op == 0:
        return _WIN + my
    terr = 0
    r1 = 0
    r2 = 0
    for e in range(36):
        if cells[e] == 0:
            a = d1[e]; b = d2[e]
            if a < b:
                terr += 1
            elif b < a:
                terr -= 1
            if a < 99:
                r1 += 1
            if b < 99:
                r2 += 1
    if op == 0:
        return _WIN + my
    return 8*terr + 2*(my - op) + (r1 - r2)

def _fmt(f, t, a):
    return "%d,%d:%d,%d:%d,%d" % (f//6, f%6, t//6, t%6, a//6, a%6)

def _any_legal(cells):
    for f in range(36):
        if cells[f] != 1:
            continue
        for line in RAY[f]:
            for t in line:
                if cells[t] != 0:
                    break
                c2 = cells[:]
                c2[f] = 0; c2[t] = 1
                for line2 in RAY[t]:
                    for a in line2:
                        if c2[a] != 0:
                            break
                        return _fmt(f, t, a)
    return None

def policy(board) -> str:
    start = time.perf_counter()
    cells = [int(v) for v in np.asarray(board).reshape(-1)]

    ft = []
    for f in range(36):
        if cells[f] != 1:
            continue
        for line in RAY[f]:
            for t in line:
                if cells[t] == 0:
                    ft.append((f, t))
                else:
                    break

    if not ft:
        s = _any_legal(cells)
        return s if s is not None else "0,0:0,0:0,0"

    ft.sort(key=lambda ft: -CENT[ft[1]])

    best = None
    best_sc = -10**18
    cnt = 0
    stop = False

    for f, t in ft:
        if stop:
            break
        c2 = cells[:]          # after amazon move
        c2[f] = 0
        c2[t] = 1
        arrows = []
        for line in RAY[t]:
            for a in line:
                if c2[a] != 0:
                    break
                arrows.append(a)
        if not arrows:
            continue
        arrows.sort(key=lambda a: -CENT[a])
        for a in arrows:
            c2[a] = -1
            sc = _evaluate(c2)
            c2[a] = 0
            cnt = getattr(policy, "_c", 0) + 1
            policy._c = cnt
            if sc > getattr(policy, "_b", -10**18):
                policy._b = sc
                best = (f, t, a)
            if cnt >= 24 and time.perf_counter() - start > 0.80:
                stop = True
                break
        if stop:
            break

    # use persistent best across the (single) call; reset for safety
    best = getattr(policy, "_best_move", None)
    # Recompute best properly in one pass to avoid stale state:
    # (The block above already tracked via policy attrs; do a clean single pass.)
    # Clean single authoritative pass:
    policy._b = -10**18
    policy._c = 0
    policy._best = None

    cnt = 0
    stop = False
    for f, t in ft_sorted(ft):
        if stop:
            break
        c2 = cells[:]
        c2[f] = 0
        c2[t] = 1
        arrows = []
        for line in RAY[t]:
            for a in line:
                if c2[a] != 0:
                    break
                arrows.append(a)
        if not arrows:
            continue
        arrows.sort(key=lambda a: -CENT[a])
        for a in arrows:
            c2[a] = -1
            sc = _evaluate(c2)
            c2[a] = 0
            cnt += 1
            if sc > policy._bb:
                policy._bb = sc
                policy._best = (f, t, a)
            if cnt >= 24 and time.perf_counter() - start > 0.80:
                stop = True
                break
        if stop:
            break

    best = policy._best
    policy._bb = -10**18
    policy._best = None
    if best is None:
        s = _any_legal(cells)
        return s if s is not None else "0,0:0,0:0,0"
    f, t, a = best
    return _fmt(f, t, a)

# initialize per-call state
policy._bb = -10**18
policy._best = None

def ft_sorted(ft):
    return sorted(ft, key=lambda ft: -CENT[ft[1]])
