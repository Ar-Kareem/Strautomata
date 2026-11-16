
import time
import random
import numpy as np

N = 19
NN = N * N

NEIGH = [[] for _ in range(NN)]
for _r in range(N):
    for _c in range(N):
        _i = _r * N + _c
        if _r > 0: NEIGH[_i].append(_i - N)
        if _r < N - 1: NEIGH[_i].append(_i + N)
        if _c > 0: NEIGH[_i].append(_i - 1)
        if _c < N - 1: NEIGH[_i].append(_i + 1)

W = [10.0, 5.0, 3.0, 2.0, 1.0]
T = 1.5
_KB = np.zeros((2 * N - 1, 2 * N - 1), dtype=np.float32)
for _dr in range(-4, 5):
    for _dc in range(-4, 5):
        _d = abs(_dr) + abs(_dc)
        if _d <= 4:
            _KB[N - 1 + _dr, N - 1 + _dc] = W[_d]
K3 = np.stack([_KB[N - 1 - r:2 * N - 1 - r, N - 1 - c:2 * N - 1 - c]
               for r in range(N) for c in range(N)]).astype(np.float32)


def flood(board, start):
    color = board[start]
    stones = {start}
    stack = [start]
    libs = set()
    while stack:
        i = stack.pop()
        for j in NEIGH[i]:
            v = board[j]
            if v == 0:
                libs.add(j)
            elif v == color and j not in stones:
                stones.add(j)
                stack.append(j)
    return stones, libs


def play(board, idx, color):
    b = board[:]
    b[idx] = color
    opp = 3 - color
    captured = []
    done = set()
    for j in NEIGH[idx]:
        if b[j] == opp and j not in done:
            st, li = flood(b, j)
            done |= st
            if not li:
                for s in st:
                    b[s] = 0
                captured.extend(st)
    return b, captured


def all_groups(board):
    gid = [-1] * NN
    groups = []
    for i in range(NN):
        if board[i] and gid[i] < 0:
            st, li = flood(board, i)
            g = len(groups)
            for s in st:
                gid[s] = g
            groups.append((board[i], st, li))
    return gid, groups


class Reader:
    def __init__(self, deadline, limit=400):
        self.nodes = 0
        self.deadline = deadline
        self.limit = limit


def defender_escapes(board, gstone, defender, depth, rd):
    rd.nodes += 1
    if depth > 40 or rd.nodes > rd.limit or time.time() > rd.deadline:
        return True
    stones, libs = flood(board, gstone)
    if not libs:
        return False
    if len(libs) >= 2:
        return True
    attacker = 3 - defender
    seen = set()
    for s in stones:
        for j in NEIGH[s]:
            if board[j] == attacker and j not in seen:
                ast, ali = flood(board, j)
                seen |= ast
                if len(ali) == 1:
                    return True
    lib = next(iter(libs))
    nb, cap = play(board, lib, defender)
    nst, nl = flood(nb, lib)
    L = len(nl)
    if L == 0:
        return False
    if L >= 3:
        return True
    if L == 1:
        return False
    return not attacker_captures(nb, lib, attacker, depth + 1, rd)


def attacker_captures(board, gstone, attacker, depth, rd):
    rd.nodes += 1
    if depth > 40 or rd.nodes > rd.limit or time.time() > rd.deadline:
        return False
    stones, libs = flood(board, gstone)
    if len(libs) == 1:
        return not defender_escapes(board, gstone, 3 - attacker, depth, rd)
    if len(libs) != 2:
        return False
    for lib in libs:
        nb, cap = play(board, lib, attacker)
        ast, al = flood(nb, lib)
        if len(al) == 0:
            continue
        if len(al) == 1 and not cap:
            continue
        if not defender_escapes(nb, gstone, 3 - attacker, depth + 1, rd):
            return True
    return False


def policy(me, opponent):
    t0 = time.time()
    deadline = t0 + 0.75
    board = [0] * NN
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + (c - 1)] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + (c - 1)] = 2
    nstones = sum(1 for v in board if v)
    gid, groups = all_groups(board)

    # influence / territory gain
    v = np.zeros(NN, dtype=np.float32)
    for i in range(NN):
        if board[i] == 1:
            v[i] = 1.0
        elif board[i] == 2:
            v[i] = -1.0
    I = np.tensordot(v, K3, axes=(0, 0))
    Inew = I[None, :, :] + K3
    own = (Inew > T).sum(axis=(1, 2))
    opp = (Inew < -T).sum(axis=(1, 2))
    base_own = int((I > T).sum())
    base_opp = int((I < -T).sum())
    gain = (own - base_own) + (base_opp - opp)
    gain = gain.astype(np.float64)
    Iflat = I.reshape(NN)

    # endangered own groups (2 libs, ladder-capturable)
    endangered = set()
    for g, (col, st, li) in enumerate(groups):
        if col == 1 and len(li) == 2 and time.time() < t0 + 0.2:
            rd = Reader(deadline, 250)
            if attacker_captures(board, next(iter(st)), 2, 0, rd):
                endangered.add(g)

    fline = max(0.0, 1.0 - nstones / 200.0)

    def corner_empty(r, c):
        r0 = 0 if r < N // 2 else N - 7
        c0 = 0 if c < N // 2 else N - 7
        for rr in range(r0, r0 + 7):
            base = rr * N
            for cc in range(c0, c0 + 7):
                if board[base + cc]:
                    return False
        return True

    cands = []
    for p in range(NN):
        if board[p]:
            continue
        fr_groups = set()
        op_groups = set()
        empties = []
        for j in NEIGH[p]:
            vv = board[j]
            if vv == 0:
                empties.append(j)
            elif vv == 1:
                fr_groups.add(gid[j])
            else:
                op_groups.add(gid[j])
        captures = [g for g in op_groups if len(groups[g][2]) == 1]
        nb = None
        if captures:
            nb, cap = play(board, p, 1)
            mystones, mylibs = flood(nb, p)
            ncap = len(cap)
        else:
            mylibs = set(empties)
            for g in fr_groups:
                mylibs |= groups[g][2]
            mylibs.discard(p)
            ncap = 0
            if not mylibs:
                continue
        nlibs = len(mylibs)
        size = 1 + sum(len(groups[g][1]) for g in fr_groups)
        if ncap == 1 and not fr_groups and nlibs == 1:
            continue  # possible ko recapture: avoid for legality safety

        score = float(gain[p])
        if ncap:
            score += 8.0 * ncap + 4.0
        if nlibs == 1:
            if ncap == 0:
                score -= 20.0 + 5.0 * size
            else:
                score -= 5.0
        elif nlibs == 2:
            score -= min(15.0, 2.0 + 1.0 * size)

        for g in fr_groups:
            gl = len(groups[g][2])
            gs = len(groups[g][1])
            if gl == 1:
                if nlibs >= 2:
                    score += 5.0 * gs + 4.0
                    if nlibs >= 3:
                        score += 2.0
            elif gl == 2:
                if nlibs >= 3 and g in endangered:
                    score += 4.0 * gs + 2.0
                elif nlibs >= 4:
                    score += 1.5 * gs
        if len(fr_groups) >= 2:
            score += 3.0

        for g in op_groups:
            if g in captures:
                continue
            ol = len(groups[g][2])
            os_ = len(groups[g][1])
            score += 1.5 + 0.3 * os_
            if ol == 2:
                if nlibs >= 2 or ncap:
                    if time.time() < deadline:
                        if nb is None:
                            nb, _ = play(board, p, 1)
                        rd = Reader(deadline, 400)
                        stone = next(iter(groups[g][1]))
                        if not defender_escapes(nb, stone, 2, 0, rd):
                            score += 6.0 * os_ + 5.0
                        else:
                            score += 0.7 * os_ + 1.0
                    else:
                        score += 0.7 * os_ + 1.0
            elif ol == 3:
                score += 0.4 * os_ + 0.5

        if not empties and not op_groups:
            score -= 15.0  # filling own eye

        r, c = divmod(p, N)
        line = min(r, c, N - 1 - r, N - 1 - c)
        if line == 0:
            score -= 5.0 * fline
        elif line == 1:
            score -= 2.5 * fline
        elif line in (2, 3):
            score += 1.5 * fline

        if nstones < 20 and r in (2, 3, 15, 16) and c in (2, 3, 15, 16) and corner_empty(r, c):
            score += 10.0

        ip = float(Iflat[p])
        if ip > 10:
            score -= min(5.0, 0.25 * (ip - 10))
        elif ip < -10:
            score -= min(8.0, 0.5 * (-10 - ip))

        score += random.random() * 0.3
        cands.append([score, p, nlibs, ncap, size, fr_groups])

    if not cands:
        return (0, 0)

    cands.sort(key=lambda x: -x[0])
    for cd in cands[:6]:
        if cd[2] == 2 and cd[3] == 0 and time.time() < deadline:
            nb, _ = play(board, cd[1], 1)
            rd = Reader(deadline, 400)
            if attacker_captures(nb, cd[1], 2, 0, rd):
                cd[0] -= 5.0 * cd[4] + 3.0
    cands.sort(key=lambda x: -x[0])

    for cd in cands:
        if cd[0] < 0.1:
            break
        p = cd[1]
        nb, cap = play(board, p, 1)
        st, li = flood(nb, p)
        if not li:
            continue
        if len(cap) == 1 and len(st) == 1 and len(li) == 1:
            continue
        r, c = divmod(p, N)
        return (r + 1, c + 1)
    return (0, 0)
