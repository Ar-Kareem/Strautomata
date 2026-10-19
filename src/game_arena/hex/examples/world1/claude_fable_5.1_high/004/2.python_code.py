
import numpy as np
import math
import time

SIZE = 11
NC = SIZE * SIZE
TOPV = NC
BOTV = NC + 1
NEIGH = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
EPS = 0.01
BIG = 1e4
_DIAG = np.arange(NC + 2)


def _build_edges(color):
    ea = []
    eb = []
    for r in range(SIZE):
        for c in range(SIZE):
            i = r * SIZE + c
            for dr, dc in ((0, 1), (1, 0), (1, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < SIZE and 0 <= cc < SIZE:
                    ea.append(i)
                    eb.append(rr * SIZE + cc)
    if color == 'b':
        for c in range(SIZE):
            ea.append(TOPV); eb.append(c)
            ea.append(BOTV); eb.append((SIZE - 1) * SIZE + c)
    else:
        for r in range(SIZE):
            ea.append(TOPV); eb.append(r * SIZE)
            ea.append(BOTV); eb.append(r * SIZE + SIZE - 1)
    return np.array(ea), np.array(eb)


EDGES = {'b': _build_edges('b'), 'w': _build_edges('w')}

_NBRS = []
for _i in range(NC):
    _r, _c = divmod(_i, SIZE)
    _lst = []
    for _dr, _dc in NEIGH:
        _rr, _cc = _r + _dr, _c + _dc
        if 0 <= _rr < SIZE and 0 <= _cc < SIZE:
            _lst.append(_rr * SIZE + _cc)
    _NBRS.append(_lst)


def _resist(board, color):
    # board: np array, 1 = stones of player being measured, 2 = enemy, 0 = empty
    res = np.empty(NC + 2)
    res[:NC] = np.where(board == 1, EPS, np.where(board == 2, BIG, 1.0))
    res[NC:] = EPS
    ea, eb = EDGES[color]
    g = 2.0 / (res[ea] + res[eb])
    A = np.zeros((NC + 2, NC + 2))
    A[ea, eb] = g
    A[eb, ea] = g
    deg = A.sum(axis=1)
    L = -A
    L[_DIAG, _DIAG] += deg
    Lint = L[:NC, :NC]
    b = A[:NC, TOPV].copy()
    try:
        v = np.linalg.solve(Lint, b)
    except Exception:
        return 1e6
    I = float(np.dot(A[TOPV, :NC], 1.0 - v))
    if I <= 1e-12:
        return 1e12
    return 1.0 / I


def _evaluate(board, mycolor, oppcolor):
    rme = _resist(board, mycolor)
    oppboard = np.where(board == 1, 2, np.where(board == 2, 1, 0)).astype(np.int8)
    ropp = _resist(oppboard, oppcolor)
    return math.log(max(ropp, 1e-12)) - math.log(max(rme, 1e-12))


def _connected(board, val, color):
    bl = board.tolist()
    if color == 'b':
        starts = [c for c in range(SIZE) if bl[c] == val]
        goal_lo = (SIZE - 1) * SIZE
        is_goal = lambda i: i >= goal_lo
    else:
        starts = [r * SIZE for r in range(SIZE) if bl[r * SIZE] == val]
        is_goal = lambda i: (i % SIZE) == SIZE - 1
    seen = set(starts)
    stack = list(starts)
    while stack:
        i = stack.pop()
        if is_goal(i):
            return True
        for j in _NBRS[i]:
            if j not in seen and bl[j] == val:
                seen.add(j)
                stack.append(j)
    return False


def _center_dist(i):
    r, c = divmod(i, SIZE)
    return abs(r - 5) + abs(c - 5) + abs((r + c) - 10)


def policy(me, opp, color):
    t0 = time.time()
    board = np.zeros(NC, dtype=np.int8)
    for r, c in me:
        board[r * SIZE + c] = 1
    for r, c in opp:
        board[r * SIZE + c] = 2
    empties = [i for i in range(NC) if board[i] == 0]
    empties.sort(key=_center_dist)
    if not empties:
        return (0, 0)
    fallback = divmod(empties[0], SIZE)
    try:
        if not me and not opp:
            return (5, 5)
        oppcolor = 'w' if color == 'b' else 'b'

        # immediate win
        for i in empties:
            board[i] = 1
            if _connected(board, 1, color):
                board[i] = 0
                return divmod(i, SIZE)
            board[i] = 0
        # opponent threats
        threats = []
        for i in empties:
            board[i] = 2
            if _connected(board, 2, oppcolor):
                threats.append(i)
            board[i] = 0
        if len(threats) == 1:
            return divmod(threats[0], SIZE)
        cands = threats if threats else empties

        # 1-ply
        scores = {}
        for i in cands:
            board[i] = 1
            scores[i] = _evaluate(board, color, oppcolor)
            board[i] = 0
            if time.time() - t0 > 0.55:
                break
        if not scores:
            return fallback
        ranked = sorted(scores.keys(), key=lambda i: -scores[i])
        best1 = ranked[0]
        if threats or time.time() - t0 > 0.5:
            return divmod(best1, SIZE)

        # 2-ply on top candidates
        K = 9
        my_moves = ranked[:K]
        top_replies = ranked[:11]
        results = {}
        done_all = True
        for m in my_moves:
            reply_set = set(top_replies)
            for j in _NBRS[m]:
                if board[j] == 0:
                    reply_set.add(j)
            reply_set.discard(m)
            board[m] = 1
            worst = float('inf')
            aborted = False
            for o in reply_set:
                board[o] = 2
                if _connected(board, 2, oppcolor):
                    s = -1e9
                else:
                    s = _evaluate(board, color, oppcolor)
                board[o] = 0
                if s < worst:
                    worst = s
                if time.time() - t0 > 0.8:
                    aborted = True
                    break
            board[m] = 0
            if aborted:
                done_all = False
                break
            results[m] = worst
        if results:
            bestm = max(results.keys(), key=lambda i: (results[i], scores[i]))
            return divmod(bestm, SIZE)
        return divmod(best1, SIZE)
    except Exception:
        # ensure a legal move
        for i in range(NC):
            if board[i] == 0:
                return divmod(i, SIZE)
        return fallback
