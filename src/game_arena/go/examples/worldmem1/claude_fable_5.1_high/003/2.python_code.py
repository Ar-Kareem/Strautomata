
import time
import random

N = 19
K = 1.5

NBR = [[None] * N for _ in range(N)]
for _r in range(N):
    for _c in range(N):
        _l = []
        if _r > 0: _l.append((_r - 1, _c))
        if _r < N - 1: _l.append((_r + 1, _c))
        if _c > 0: _l.append((_r, _c - 1))
        if _c < N - 1: _l.append((_r, _c + 1))
        NBR[_r][_c] = _l

W_INF = [0.0, 1.0, 0.55, 0.3, 0.15]
INF_OFF = []
for _dr in range(-4, 5):
    for _dc in range(-4, 5):
        _d = abs(_dr) + abs(_dc)
        if 0 < _d <= 4:
            INF_OFF.append((_dr, _dc, W_INF[_d]))
W_GAIN = [1.0, 1.0, 0.55, 0.3]
GAIN_OFF = []
for _dr in range(-3, 4):
    for _dc in range(-3, 4):
        _d = abs(_dr) + abs(_dc)
        if _d <= 3:
            GAIN_OFF.append((_dr, _dc, W_GAIN[_d]))

LINE_BONUS = {1: -3.0, 2: -1.5, 3: 2.0, 4: 2.0, 5: 0.7, 6: 0.2}

CORNER_PTS = {
    (3, 3): (0, 7.0), (2, 3): (0, 6.0), (3, 2): (0, 6.0),
    (3, 15): (1, 7.0), (2, 15): (1, 6.0), (3, 16): (1, 6.0),
    (15, 3): (2, 7.0), (16, 3): (2, 6.0), (15, 2): (2, 6.0),
    (15, 15): (3, 7.0), (16, 15): (3, 6.0), (15, 16): (3, 6.0),
}
CORNER_REGION = [
    (range(0, 7), range(0, 7)),
    (range(0, 7), range(12, 19)),
    (range(12, 19), range(0, 7)),
    (range(12, 19), range(12, 19)),
]


def own(x):
    x = x / K
    if x > 1.0:
        return 1.0
    if x < -1.0:
        return -1.0
    return x


def board_key(board):
    return ''.join(''.join(str(v) for v in row) for row in board)


def flood(b, r, c):
    color = b[r][c]
    stones = [(r, c)]
    seen = {(r, c)}
    libs = set()
    i = 0
    while i < len(stones):
        a, bb = stones[i]
        i += 1
        for (x, y) in NBR[a][bb]:
            v = b[x][y]
            if v == 0:
                libs.add((x, y))
            elif v == color and (x, y) not in seen:
                seen.add((x, y))
                stones.append((x, y))
    return stones, libs


def place(board, r, c, color):
    if board[r][c] != 0:
        return None
    b = [row[:] for row in board]
    b[r][c] = color
    opp = 3 - color
    for (x, y) in NBR[r][c]:
        if b[x][y] == opp:
            st, lb = flood(b, x, y)
            if not lb:
                for (a, bb) in st:
                    b[a][bb] = 0
    st, lb = flood(b, r, c)
    if not lb:
        return None
    return b


def compute_groups(board):
    gid = [[-1] * N for _ in range(N)]
    groups = []
    for r in range(N):
        for c in range(N):
            if board[r][c] and gid[r][c] < 0:
                color = board[r][c]
                idx = len(groups)
                stack = [(r, c)]
                gid[r][c] = idx
                stones = []
                libs = set()
                while stack:
                    a, b = stack.pop()
                    stones.append((a, b))
                    for (x, y) in NBR[a][b]:
                        v = board[x][y]
                        if v == 0:
                            libs.add((x, y))
                        elif v == color and gid[x][y] < 0:
                            gid[x][y] = idx
                            stack.append((x, y))
                groups.append((color, stones, libs))
    return gid, groups


def influence(board, gid, groups):
    inf = [[0.0] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            v = board[r][c]
            if v:
                nl = len(groups[gid[r][c]][2])
                strength = 1.0 if nl >= 3 else (0.7 if nl == 2 else 0.3)
                sgn = strength if v == 1 else -strength
                for (dr, dc, w) in INF_OFF:
                    x = r + dr
                    y = c + dc
                    if 0 <= x < N and 0 <= y < N:
                        inf[x][y] += sgn * w
    return inf


def gain(board, inf, r, c):
    g = 0.0
    for (dr, dc, w) in GAIN_OFF:
        x = r + dr
        y = c + dc
        if 0 <= x < N and 0 <= y < N and board[x][y] == 0:
            v = inf[x][y]
            g += own(v + w) - own(v)
    return g


def can_escape(board, r, c, color, budget, deadline, depth=0):
    budget[0] -= 1
    if budget[0] <= 0 or depth > 40 or time.time() > deadline:
        return True
    stones, libs = flood(board, r, c)
    if len(libs) >= 2:
        return True
    if len(libs) == 0:
        return False
    opp = 3 - color
    seen = set()
    for (a, b) in stones:
        for (x, y) in NBR[a][b]:
            if board[x][y] == opp and (x, y) not in seen:
                est, elibs = flood(board, x, y)
                seen.update(est)
                if len(elibs) == 1:
                    (lr, lc) = next(iter(elibs))
                    nb = place(board, lr, lc, color)
                    if nb is not None:
                        s2, l2 = flood(nb, r, c)
                        if len(l2) >= 2:
                            return True
    (lr, lc) = next(iter(libs))
    nb = place(board, lr, lc, color)
    if nb is None:
        return False
    s2, l2 = flood(nb, lr, lc)
    if len(l2) >= 3:
        return True
    if len(l2) <= 1:
        return False
    for (ar, ac) in list(l2):
        b2 = place(nb, ar, ac, opp)
        if b2 is None:
            continue
        if b2[lr][lc] != color:
            return False
        ast, alibs = flood(b2, ar, ac)
        if len(alibs) <= 1:
            continue
        s3, l3 = flood(b2, lr, lc)
        if len(l3) >= 2:
            continue
        if not can_escape(b2, lr, lc, color, budget, deadline, depth + 1):
            return False
    return True


def ladder_vulnerable(board, r, c, color, deadline):
    stones, libs = flood(board, r, c)
    if len(libs) != 2:
        return False
    opp = 3 - color
    for (lr, lc) in libs:
        if time.time() > deadline:
            return False
        b2 = place(board, lr, lc, opp)
        if b2 is None:
            continue
        ast, alibs = flood(b2, lr, lc)
        if len(alibs) <= 1:
            continue
        if b2[r][c] != color:
            return True
        s2, l2 = flood(b2, r, c)
        if len(l2) == 1 and not can_escape(b2, r, c, color, [60], deadline):
            return True
    return False


def fallback_move(board):
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                for (x, y) in NBR[r][c]:
                    if board[x][y] == 0:
                        return (r + 1, c + 1)
    return (0, 0)


def policy(me, opponent, memory):
    t0 = time.time()
    deadline = t0 + 0.5
    board = [[0] * N for _ in range(N)]
    for p in me:
        r, c = int(p[0]), int(p[1])
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for p in opponent:
        r, c = int(p[0]), int(p[1])
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 2
    total = len(me) + len(opponent)
    hist = {}
    if isinstance(memory, dict) and total > 1:
        h = memory.get('hist')
        if isinstance(h, dict):
            hist = h
    try:
        hist[board_key(board)] = 1
        gid, groups = compute_groups(board)
        inf = influence(board, gid, groups)
        empties = N * N - total
        open_f = empties / float(N * N)

        corner_empty = []
        for (rr, cc) in CORNER_REGION:
            emp = True
            for r in rr:
                for c in cc:
                    if board[r][c]:
                        emp = False
                        break
                if not emp:
                    break
            corner_empty.append(emp)

        cands = []
        for r in range(N):
            for c in range(N):
                if board[r][c] != 0:
                    continue
                E = []
                Gm = set()
                Go = set()
                for (x, y) in NBR[r][c]:
                    v = board[x][y]
                    if v == 0:
                        E.append((x, y))
                    elif v == 1:
                        Gm.add(gid[x][y])
                    else:
                        Go.add(gid[x][y])
                captured = [g for g in Go if len(groups[g][2]) == 1]
                newlibs = set(E)
                for g in Gm:
                    newlibs |= groups[g][2]
                newlibs.discard((r, c))
                cap = 0
                if captured:
                    for g in captured:
                        for (a, b) in groups[g][1]:
                            cap += 1
                            for (x, y) in NBR[a][b]:
                                if (x == r and y == c) or (board[x][y] == 1 and gid[x][y] in Gm):
                                    newlibs.add((a, b))
                                    break
                L = len(newlibs)
                if L == 0:
                    continue
                if cap:
                    b2 = [row[:] for row in board]
                    b2[r][c] = 1
                    for g in captured:
                        for (a, b) in groups[g][1]:
                            b2[a][b] = 0
                    if board_key(b2) in hist:
                        continue
                size = 1
                for g in Gm:
                    size += len(groups[g][1])

                s = gain(board, inf, r, c)
                line = min(r, c, N - 1 - r, N - 1 - c) + 1
                s += LINE_BONUS.get(line, 0.0) * (0.2 + open_f)
                if open_f > 0.5 and (r, c) in CORNER_PTS:
                    k, val = CORNER_PTS[(r, c)]
                    if corner_empty[k]:
                        s += val
                if cap:
                    s += 10 + 6 * cap
                    seen_g = set()
                    for g in captured:
                        for (a, b) in groups[g][1]:
                            for (x, y) in NBR[a][b]:
                                if board[x][y] == 1:
                                    gg = gid[x][y]
                                    if gg not in seen_g and gg not in Gm and len(groups[gg][2]) == 1:
                                        seen_g.add(gg)
                                        s += 4 * len(groups[gg][1])
                weak_join = False
                for g in Gm:
                    ol = len(groups[g][2])
                    gs = len(groups[g][1])
                    if ol == 1:
                        weak_join = True
                        if L >= 2:
                            s += 5 + 4 * gs
                    elif ol == 2:
                        weak_join = True
                        if L >= 3:
                            s += 1 + 0.5 * gs
                if L == 1:
                    s -= 6 if cap else (25 + 5 * size)
                elif L == 2:
                    if not cap:
                        s -= 2 + 0.5 * size
                elif L == 3:
                    s -= 0.5
                s += min(L, 5) * 0.3
                att = []
                for g in Go:
                    ol = len(groups[g][2])
                    if ol == 1:
                        continue
                    gs = len(groups[g][1])
                    nl = ol - 1
                    if nl == 1:
                        s += 4 + 2 * gs
                        att.append((g, gs))
                    elif nl == 2:
                        s += 1.5 + 0.4 * gs
                    else:
                        s += 0.3
                    if ol > L and L <= 3 and not cap:
                        s -= 1
                if len(Gm) >= 2:
                    s += 2 + 0.5 * len(Gm) + (3 if weak_join else 0)
                if not E and not Go and Gm:
                    s -= 15
                v0 = inf[r][c]
                if v0 < -1.5:
                    s -= (-v0 - 1.5) * 2.5
                s += random.random() * 0.1
                cands.append([s, r, c, L, cap, size, Gm, att])

        if not cands:
            return (0, 0), {'hist': hist}

        cands.sort(key=lambda x: -x[0])
        top = cands[:18]
        vuln_cache = {}
        for cand in top:
            if time.time() > deadline:
                break
            s, r, c, L, cap, size, Gm, att = cand
            b2 = place(board, r, c, 1)
            if b2 is None:
                cand[0] = -1000.0
                continue
            safe_after = L >= 3
            if L == 2:
                if ladder_vulnerable(b2, r, c, 1, deadline):
                    s -= 6 * size + 8
                else:
                    s += 2 + 0.5 * size
                    safe_after = True
            for (g, gs) in att:
                (a, b) = groups[g][1][0]
                if b2[a][b] != 2:
                    continue
                if can_escape(b2, a, b, 2, [60], deadline):
                    s -= 3 + 1.5 * gs
                else:
                    s += 6 * gs + 6
            if safe_after:
                for g in Gm:
                    if len(groups[g][2]) == 2:
                        if g not in vuln_cache:
                            (a, b) = groups[g][1][0]
                            vuln_cache[g] = ladder_vulnerable(board, a, b, 1, deadline)
                        if vuln_cache[g]:
                            s += 4 * len(groups[g][1]) + 5
            cand[0] = s
        top.sort(key=lambda x: -x[0])

        for cand in top:
            s, r, c = cand[0], cand[1], cand[2]
            if s < 0.2:
                break
            b2 = place(board, r, c, 1)
            if b2 is None:
                continue
            nk = board_key(b2)
            if cand[4] and nk in hist:
                continue
            hist[nk] = 1
            return (r + 1, c + 1), {'hist': hist}
        return (0, 0), {'hist': hist}
    except Exception:
        mv = fallback_move(board)
        return mv, {'hist': hist}
