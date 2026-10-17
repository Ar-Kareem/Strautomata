
import time

PST_ROWS = [
    [-80, -25, -20, -20, -20, -20, -25, -80],
    [-25,  10,  10,  10,  10,  10,  10, -25],
    [-20,  10,  25,  25,  25,  25,  10, -20],
    [-20,  10,  25,  50,  50,  25,  10, -20],
    [-20,  10,  25,  50,  50,  25,  10, -20],
    [-20,  10,  25,  25,  25,  25,  10, -20],
    [-25,  10,  10,  10,  10,  10,  10, -25],
    [-80, -25, -20, -20, -20, -20, -25, -80],
]
PST = [v for row in PST_ROWS for v in row]

NEIGH = []
for _i in range(64):
    _r, _c = divmod(_i, 8)
    _lst = []
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr == 0 and _dc == 0:
                continue
            _rr, _cc = _r + _dr, _c + _dc
            if 0 <= _rr < 8 and 0 <= _cc < 8:
                _lst.append(_rr * 8 + _cc)
    NEIGH.append(_lst)

# minimal sum of Chebyshev distances for n pieces packed around a center
MINDIST = [0] * 65
for _n in range(1, 65):
    rem = _n - 1
    k = 1
    tot = 0
    while rem > 0:
        take = min(rem, 8 * k)
        tot += take * k
        rem -= take
        k += 1
    MINDIST[_n] = tot

WIN = 100000


class _Timeout(Exception):
    pass


def gen_moves(b, p):
    rc = [0] * 8
    cc = [0] * 8
    d1 = [0] * 15
    d2 = [0] * 15
    mine = []
    for i in range(64):
        v = b[i]
        if v:
            r = i >> 3
            c = i & 7
            rc[r] += 1
            cc[c] += 1
            d1[r - c + 7] += 1
            d2[r + c] += 1
            if v == p:
                mine.append(i)
    opp = -p
    moves = []
    for i in mine:
        r = i >> 3
        c = i & 7
        nr = rc[r]
        nc = cc[c]
        n1 = d1[r - c + 7]
        n2 = d2[r + c]
        for dr, dc, n in ((0, 1, nr), (0, -1, nr), (1, 0, nc), (-1, 0, nc),
                          (1, 1, n1), (-1, -1, n1), (1, -1, n2), (-1, 1, n2)):
            tr = r + dr * n
            tc = c + dc * n
            if tr < 0 or tr > 7 or tc < 0 or tc > 7:
                continue
            t = tr * 8 + tc
            if b[t] == p:
                continue
            rr = r + dr
            c2 = c + dc
            ok = True
            for _ in range(n - 1):
                if b[rr * 8 + c2] == opp:
                    ok = False
                    break
                rr += dr
                c2 += dc
            if ok:
                moves.append((i, t))
    return moves


def connected(b, p):
    start = -1
    cnt = 0
    for i in range(64):
        if b[i] == p:
            cnt += 1
            if start < 0:
                start = i
    if cnt <= 1:
        return True
    seen = {start}
    stack = [start]
    n = 1
    while stack:
        i = stack.pop()
        for j in NEIGH[i]:
            if b[j] == p and j not in seen:
                seen.add(j)
                stack.append(j)
                n += 1
    return n == cnt


def side_eval(b, p):
    pieces = [i for i in range(64) if b[i] == p]
    n = len(pieces)
    if n == 0:
        return -50000
    seen = set()
    comps = 0
    links = 0
    for s in pieces:
        if s in seen:
            continue
        comps += 1
        seen.add(s)
        stack = [s]
        while stack:
            i = stack.pop()
            for j in NEIGH[i]:
                if b[j] == p:
                    links += 1
                    if j not in seen:
                        seen.add(j)
                        stack.append(j)
    links //= 2
    cen = 0
    sr = 0
    sc = 0
    for i in pieces:
        cen += PST[i]
        sr += i >> 3
        sc += i & 7
    cr = sr / n
    cc = sc / n
    dist = 0.0
    for i in pieces:
        dr = abs((i >> 3) - cr)
        dc = abs((i & 7) - cc)
        dist += dr if dr > dc else dc
    return -60 * (comps - 1) + cen * 0.5 - 8 * (dist - MINDIST[n]) + 4 * links


def evaluate(b, p):
    return side_eval(b, p) - side_eval(b, -p)


def order_moves(moves):
    moves.sort(key=lambda m: PST[m[1]] - PST[m[0]], reverse=True)
    return moves


def negamax(b, player, depth, alpha, beta, deadline):
    if time.time() > deadline:
        raise _Timeout()
    moves = gen_moves(b, player)
    if not moves:
        return evaluate(b, player)
    order_moves(moves)
    best = -10 ** 9
    for f, t in moves:
        captured = b[t]
        b[t] = player
        b[f] = 0
        if connected(b, player):
            val = WIN + depth
        elif captured and connected(b, -player):
            val = -WIN - depth
        elif depth <= 1:
            val = evaluate(b, player)
        else:
            val = -negamax(b, -player, depth - 1, -beta, -alpha, deadline)
        b[f] = player
        b[t] = captured
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best


def _fmt(m):
    f, t = m
    return "%d,%d:%d,%d" % (f >> 3, f & 7, t >> 3, t & 7)


def policy(board):
    start = time.time()
    deadline = start + 0.8
    b = [board[r][c] for r in range(8) for c in range(8)]
    moves = gen_moves(b, 1)
    if not moves:
        return "0,0:0,0"
    order_moves(moves)
    # immediate win check
    for f, t in moves:
        captured = b[t]
        b[t] = 1
        b[f] = 0
        w = connected(b, 1)
        b[f] = 1
        b[t] = captured
        if w:
            return _fmt((f, t))
    best_move = moves[0]
    ordered = list(moves)
    max_depth = 6
    for depth in range(1, max_depth + 1):
        scores = []
        alpha = -10 ** 9
        beta = 10 ** 9
        cur_best = None
        cur_best_val = -10 ** 9
        try:
            for f, t in ordered:
                captured = b[t]
                b[t] = 1
                b[f] = 0
                if connected(b, 1):
                    val = WIN + depth
                elif captured and connected(b, -1):
                    val = -WIN - depth
                elif depth <= 1:
                    val = evaluate(b, 1)
                else:
                    val = -negamax(b, -1, depth - 1, -beta, -alpha, deadline)
                b[f] = 1
                b[t] = captured
                scores.append((val, (f, t)))
                if val > cur_best_val:
                    cur_best_val = val
                    cur_best = (f, t)
                if val > alpha:
                    alpha = val
        except _Timeout:
            b[f] = 1
            b[t] = captured
            break
        if cur_best is not None:
            best_move = cur_best
            scores.sort(key=lambda x: x[0], reverse=True)
            ordered = [m for _, m in scores]
        if cur_best_val >= WIN - 100:
            break
        if time.time() - start > 0.35:
            break
    return _fmt(best_move)
