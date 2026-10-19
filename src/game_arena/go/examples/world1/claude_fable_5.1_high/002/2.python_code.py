
import random
import time
import numpy as np

N = 19
W = N + 2
EMPTY, ME, OPP, BORDER = 0, 1, 2, 3
TL = 0.6

ALL_PTS = [r * W + c for r in range(1, N + 1) for c in range(1, N + 1)]
NB = [[] for _ in range(W * W)]
DG = [[] for _ in range(W * W)]
for _p in ALL_PTS:
    NB[_p] = [_p - 1, _p + 1, _p - W, _p + W]
    DG[_p] = [_p - W - 1, _p - W + 1, _p + W - 1, _p + W + 1]


def group_at(board, p):
    color = board[p]
    stones = {p}
    stack = [p]
    libs = set()
    while stack:
        q = stack.pop()
        for n in NB[q]:
            v = board[n]
            if v == EMPTY:
                libs.add(n)
            elif v == color and n not in stones:
                stones.add(n)
                stack.append(n)
    return stones, libs


def place(board, p, color):
    b = board[:]
    b[p] = color
    opp = 3 - color
    caps = []
    for n in NB[p]:
        if b[n] == opp:
            st, libs = group_at(b, n)
            if not libs:
                for s in st:
                    b[s] = EMPTY
                caps.extend(st)
    return b, caps


def defender_escapes(board, gp, depth, budget, t0):
    budget[0] -= 1
    if budget[0] < 0 or depth > 80 or time.time() - t0 > TL:
        return True
    color = board[gp]
    opp = 3 - color
    st, libs = group_at(board, gp)
    if len(libs) >= 2:
        return True
    if len(libs) == 0:
        return False
    checked = set()
    for s in st:
        for n in NB[s]:
            if board[n] == opp and n not in checked:
                ast, alibs = group_at(board, n)
                checked |= ast
                if len(alibs) == 1:
                    l = next(iter(alibs))
                    nb, caps = place(board, l, color)
                    st2, libs2 = group_at(nb, gp)
                    if len(libs2) >= 2:
                        return True
    lib = next(iter(libs))
    nb, caps = place(board, lib, color)
    st2, libs2 = group_at(nb, lib)
    if len(libs2) >= 3:
        return True
    if len(libs2) <= 1:
        return False
    return not attacker_captures(nb, lib, depth + 1, budget, t0)


def attacker_captures(board, gp, depth, budget, t0):
    budget[0] -= 1
    if budget[0] < 0 or depth > 80 or time.time() - t0 > TL:
        return False
    color = board[gp]
    att = 3 - color
    st, libs = group_at(board, gp)
    if len(libs) != 2:
        return len(libs) < 2
    for l in libs:
        nb, caps = place(board, l, att)
        ast, alibs = group_at(nb, l)
        if len(alibs) == 0:
            continue
        if len(alibs) == 1 and not caps:
            continue
        if not defender_escapes(nb, gp, depth + 1, budget, t0):
            return True
    return False


def is_eye(board, p, color):
    for n in NB[p]:
        v = board[n]
        if v != color and v != BORDER:
            return False
    opp = 3 - color
    cnt = 0
    edge = False
    for d in DG[p]:
        v = board[d]
        if v == BORDER:
            edge = True
        elif v == opp:
            cnt += 1
    if edge:
        return cnt == 0
    return cnt <= 1


def dist_map(board, color):
    INF = 99
    d = [INF] * (W * W)
    q = [p for p in ALL_PTS if board[p] == color]
    for p in q:
        d[p] = 0
    i = 0
    while i < len(q):
        p = q[i]
        i += 1
        nd = d[p] + 1
        for n in NB[p]:
            if board[n] != BORDER and d[n] > nd:
                d[n] = nd
                q.append(n)
    return d


def _fallback(me, opponent):
    board = [BORDER] * (W * W)
    for p in ALL_PTS:
        board[p] = EMPTY
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r * W + c] = ME
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r * W + c] = OPP
    cands = []
    for p in ALL_PTS:
        if board[p] != EMPTY:
            continue
        if any(board[n] == EMPTY for n in NB[p]) and not is_eye(board, p, ME):
            cands.append(p)
    if not cands:
        return (0, 0)
    p = random.choice(cands)
    r, c = divmod(p, W)
    return (r, c)


def _policy(me, opponent):
    t0 = time.time()
    board = [BORDER] * (W * W)
    for p in ALL_PTS:
        board[p] = EMPTY
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r * W + c] = ME
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r * W + c] = OPP
    stage = len(me) + len(opponent)

    gid = [-1] * (W * W)
    groups = []
    for p in ALL_PTS:
        v = board[p]
        if v in (ME, OPP) and gid[p] == -1:
            st, libs = group_at(board, p)
            g = len(groups)
            groups.append((st, libs, v))
            for s in st:
                gid[s] = g

    budget = [1000]
    own_laddered = {}
    for g, (st, libs, col) in enumerate(groups):
        if col == ME and len(libs) == 2 and budget[0] > 0:
            own_laddered[g] = attacker_captures(board, next(iter(st)), 0, budget, t0)
    budget = [2500]

    dist_own = dist_map(board, ME)
    dist_opp = dist_map(board, OPP)

    A = np.zeros((N + 8, N + 8))
    B = np.zeros((N + 8, N + 8))
    E = np.zeros((N + 8, N + 8))
    for p in ALL_PTS:
        r, c = divmod(p, W)
        v = board[p]
        if v == ME:
            A[r + 3, c + 3] = 1.0
        elif v == OPP:
            B[r + 3, c + 3] = 1.0
        else:
            E[r + 3, c + 3] = 1.0
    inf_me = np.zeros((N, N))
    inf_opp = np.zeros((N, N))
    empt3 = np.zeros((N, N))
    WT = {1: 1.0, 2: 0.55, 3: 0.3, 4: 0.15}
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            d = abs(dr) + abs(dc)
            if 1 <= d <= 4:
                w = WT[d]
                sl = (slice(4 + dr, 4 + dr + N), slice(4 + dc, 4 + dc + N))
                inf_me += w * A[sl]
                inf_opp += w * B[sl]
                if d <= 3:
                    empt3 += E[sl]

    def region_count(r0, r1, c0, c1):
        cnt = 0
        for r in range(r0, r1 + 1):
            base = r * W
            for c in range(c0, c1 + 1):
                if board[base + c] != EMPTY:
                    cnt += 1
        return cnt

    open_bonus = {}
    if stage < 40:
        for top in (True, False):
            for left in (True, False):
                r0, r1 = (1, 7) if top else (13, 19)
                c0, c1 = (1, 7) if left else (13, 19)
                if region_count(r0, r1, c0, c1) == 0:
                    def fr(x):
                        return x if top else 20 - x

                    def fc(x):
                        return x if left else 20 - x
                    for (rr, cc, bv) in [(4, 4, 14), (3, 4, 13), (4, 3, 13), (3, 3, 9), (3, 5, 8), (5, 3, 8)]:
                        open_bonus[(fr(rr), fc(cc))] = bv
    if 4 <= stage < 60:
        if region_count(1, 7, 8, 12) == 0:
            open_bonus[(4, 10)] = 7
            open_bonus[(3, 10)] = 6
        if region_count(13, 19, 8, 12) == 0:
            open_bonus[(16, 10)] = 7
            open_bonus[(17, 10)] = 6
        if region_count(8, 12, 1, 7) == 0:
            open_bonus[(10, 4)] = 7
            open_bonus[(10, 3)] = 6
        if region_count(8, 12, 13, 19) == 0:
            open_bonus[(10, 16)] = 7
            open_bonus[(10, 17)] = 6
        if stage >= 10 and region_count(8, 12, 8, 12) == 0:
            open_bonus[(10, 10)] = 3

    def evaluate(p):
        r, c = divmod(p, W)
        own_adj = set()
        opp_adj = set()
        empt = []
        for n in NB[p]:
            v = board[n]
            if v == EMPTY:
                empt.append(n)
            elif v == ME:
                own_adj.add(gid[n])
            elif v == OPP:
                opp_adj.add(gid[n])
        caps = [g for g in opp_adj if len(groups[g][1]) == 1]
        cap_count = 0
        nb = None
        capstones = []
        if caps:
            nb, capstones = place(board, p, ME)
            cap_count = len(capstones)
            st, libs = group_at(nb, p)
        else:
            libs = set(empt)
            for g in own_adj:
                libs |= groups[g][1]
            libs.discard(p)
        L = len(libs)
        if L == 0:
            return None
        if cap_count == 1 and L == 1 and not own_adj:
            return None
        size = 1 + sum(len(groups[g][0]) for g in own_adj)
        score = 10.0 * cap_count
        if caps:
            saved = set()
            for s in capstones:
                for n in NB[s]:
                    if board[n] == ME:
                        g = gid[n]
                        if g not in saved and g not in own_adj and len(groups[g][1]) == 1:
                            saved.add(g)
                            score += 6 * len(groups[g][0])
        capturable2 = False
        if L == 1:
            if cap_count == 0:
                score -= 40 + 12 * size
            else:
                score -= 8 * size
        elif L == 2 and cap_count == 0:
            if (opp_adj or dist_opp[p] <= 2) and budget[0] > 0:
                if nb is None:
                    nb = place(board, p, ME)[0]
                capturable2 = attacker_captures(nb, p, 0, budget, t0)
            if capturable2:
                score -= 15 + 8 * size
            else:
                score -= 1.5 + 1.0 * min(size, 10)
        for g in own_adj:
            gl = len(groups[g][1])
            gs = len(groups[g][0])
            if gl == 1:
                if L >= 3:
                    score += 7 * gs + 4
                elif L == 2 and not capturable2:
                    score += 6 * gs + 3
            elif gl == 2:
                if L >= 3:
                    if own_laddered.get(g):
                        score += 3 * gs + 3
                    else:
                        score += 0.8 * min(gs, 6) + 1
            elif gl == 3 and L >= 4:
                score += 0.3 * min(gs, 6)
        for g in opp_adj:
            if g in caps:
                continue
            gs = len(groups[g][0])
            nl = len(groups[g][1]) - 1
            if nl == 1:
                if L >= 2 or cap_count:
                    if nb is None:
                        nb = place(board, p, ME)[0]
                    esc = defender_escapes(nb, next(iter(groups[g][0])), 0, budget, t0)
                    if not esc:
                        score += 9 * gs + 5
                    else:
                        score += 1.0 * min(gs, 5) - (0 if L >= 3 else 2)
            elif nl == 2:
                if L >= 3:
                    score += 1.2 * min(gs, 8) + 1
                elif L == 2:
                    score += 0.3 * min(gs, 5)
            elif nl == 3 and L >= 3:
                score += 0.4 * min(gs, 8)
        if len(own_adj) >= 2:
            score += 2
            for g in own_adj:
                if len(groups[g][1]) <= 2:
                    score += 1.5 * len(groups[g][0])
        if len(opp_adj) >= 2 and L >= 2 and cap_count == 0:
            score += 2.5 + (1 if L >= 3 else 0)
        if not empt and not opp_adj and is_eye(board, p, ME):
            score -= 1000

        # positional
        e = min(r, c, N + 1 - r, N + 1 - c)
        if e == 1:
            score -= 8 if stage < 100 else 3
        elif e == 2:
            score -= 3 if stage < 60 else 0.5
        elif e in (3, 4):
            score += 2.5 if stage < 120 else 0.5
        else:
            score += 0.5 if stage < 40 else 0
        score += 0.12 * empt3[r - 1, c - 1]
        do = dist_own[p]
        dp = dist_opp[p]
        if do < 99:
            score += {1: 0.5, 2: 2.0, 3: 2.0, 4: 1.0, 5: 0.0}.get(do, -1.5)
        if dp < 99:
            score += {1: 0.5, 2: 1.5, 3: 1.5, 4: 0.8}.get(dp, 0.0)
            if dp in (2, 3) and e in (3, 4) and do >= 4 and stage < 80:
                score += 3
            if dp == 1 and stage < 20:
                score -= 2
        a = inf_me[r - 1, c - 1]
        b = inf_opp[r - 1, c - 1]
        if a > 1.2 and b < 0.15 * a and dp >= 3:
            score -= 6 + 4 * min(a, 4)
        elif b > 1.2 and a < 0.15 * b and do >= 3:
            score -= 3 + 2 * min(b, 4)
        elif a + b > 0.3:
            score += 4 * (2 * min(a, b) / (a + b))
        score += open_bonus.get((r, c), 0)
        return score

    best_score = -1e9
    best_move = None
    for p in ALL_PTS:
        if board[p] != EMPTY:
            continue
        s = evaluate(p)
        if s is None:
            continue
        s += random.random() * 0.3
        if s > best_score:
            best_score = s
            best_move = p
    if best_move is None or best_score < -15:
        return (0, 0)
    r, c = divmod(best_move, W)
    return (r, c)


def policy(me, opponent):
    try:
        mv = _policy(me, opponent)
        r, c = mv
        if mv == (0, 0) or (1 <= r <= N and 1 <= c <= N):
            return (int(r), int(c))
        return _fallback(me, opponent)
    except Exception:
        try:
            return _fallback(me, opponent)
        except Exception:
            return (0, 0)
