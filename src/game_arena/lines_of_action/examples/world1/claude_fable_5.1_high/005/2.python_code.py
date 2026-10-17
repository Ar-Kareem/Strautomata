
import time

WIN = 1000000
TIME_BUDGET = 0.80

CENTER = [
 -80,-25,-20,-20,-20,-20,-25,-80,
 -25, 10, 10, 10, 10, 10, 10,-25,
 -20, 10, 25, 25, 25, 25, 10,-20,
 -20, 10, 25, 50, 50, 25, 10,-20,
 -20, 10, 25, 50, 50, 25, 10,-20,
 -20, 10, 25, 25, 25, 25, 10,-20,
 -25, 10, 10, 10, 10, 10, 10,-25,
 -80,-25,-20,-20,-20,-20,-25,-80]

AXES = [(0, 1), (1, 0), (1, 1), (1, -1)]

NEIGH = []
for _i in range(64):
    _r, _c = _i >> 3, _i & 7
    _lst = []
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr == 0 and _dc == 0:
                continue
            _rr, _cc = _r + _dr, _c + _dc
            if 0 <= _rr < 8 and 0 <= _cc < 8:
                _lst.append(_rr * 8 + _cc)
    NEIGH.append(_lst)


class Timeout(Exception):
    pass


def gen_moves(b, p):
    moves = []
    for idx in range(64):
        if b[idx] != p:
            continue
        r = idx >> 3
        c = idx & 7
        for dr, dc in AXES:
            n = 1
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                if b[rr * 8 + cc]:
                    n += 1
                rr += dr
                cc += dc
            rr, cc = r - dr, c - dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                if b[rr * 8 + cc]:
                    n += 1
                rr -= dr
                cc -= dc
            for sdr, sdc in ((dr, dc), (-dr, -dc)):
                tr = r + sdr * n
                tc = c + sdc * n
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                t = b[tr * 8 + tc]
                if t == p:
                    continue
                ok = True
                rr, cc = r + sdr, c + sdc
                for _ in range(n - 1):
                    if b[rr * 8 + cc] == -p:
                        ok = False
                        break
                    rr += sdr
                    cc += sdc
                if ok:
                    moves.append((idx, tr * 8 + tc, t))
    return moves


def connected(b, p):
    start = -1
    count = 0
    for i in range(64):
        if b[i] == p:
            count += 1
            if start < 0:
                start = i
    if count <= 1:
        return True
    seen = {start}
    stack = [start]
    while stack:
        i = stack.pop()
        for j in NEIGH[i]:
            if b[j] == p and j not in seen:
                seen.add(j)
                stack.append(j)
    return len(seen) == count


def side_score(b, p):
    pieces = [i for i in range(64) if b[i] == p]
    n = len(pieces)
    if n == 0:
        return 0.0
    seen = set()
    comps = 0
    adj = 0
    for i in pieces:
        for j in NEIGH[i]:
            if b[j] == p:
                adj += 1
        if i in seen:
            continue
        comps += 1
        seen.add(i)
        stack = [i]
        while stack:
            k = stack.pop()
            for j in NEIGH[k]:
                if b[j] == p and j not in seen:
                    seen.add(j)
                    stack.append(j)
    sr = 0
    sc = 0
    cent = 0
    for i in pieces:
        sr += i >> 3
        sc += i & 7
        cent += CENTER[i]
    cr = sr / n
    cc = sc / n
    dist = 0.0
    for i in pieces:
        dr = abs((i >> 3) - cr)
        dc = abs((i & 7) - cc)
        dist += dr if dr > dc else dc
    return -50.0 * (comps - 1) - 10.0 * dist + 0.6 * cent + 3.0 * adj


def evaluate(b, p):
    return side_score(b, p) - side_score(b, -p)


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.time() > self.deadline:
            raise Timeout()

    def search(self, b, p, depth, alpha, beta):
        self.check_time()
        # previous mover may have won
        if connected(b, -p):
            return -(WIN + depth)
        if connected(b, p):
            return WIN + depth
        if depth <= 0:
            return evaluate(b, p)
        moves = gen_moves(b, p)
        if not moves:
            return evaluate(b, p)
        moves.sort(key=lambda m: -((1000 if m[2] != 0 else 0) + CENTER[m[1]] - CENTER[m[0]]))
        best = -float('inf')
        for f, t, cap in moves:
            b[t] = p
            b[f] = 0
            score = -self.search(b, -p, depth - 1, -beta, -alpha)
            b[f] = p
            b[t] = cap
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best


def fmt(m):
    f, t, _ = m
    return "%d,%d:%d,%d" % (f >> 3, f & 7, t >> 3, t & 7)


def policy(board):
    start = time.time()
    deadline = start + TIME_BUDGET
    b = [int(board[r][c]) for r in range(8) for c in range(8)]
    moves = gen_moves(b, 1)
    if not moves:
        return "0,0:0,0"

    # Immediate win check
    for f, t, cap in moves:
        b[t] = 1
        b[f] = 0
        win = connected(b, 1)
        b[f] = 1
        b[t] = cap
        if win:
            return fmt((f, t, cap))

    # Initial ordering
    moves.sort(key=lambda m: -((1000 if m[2] != 0 else 0) + CENTER[m[1]] - CENTER[m[0]]))
    best_move = moves[0]
    searcher = Searcher(deadline)
    depth = 1
    try:
        while depth <= 20:
            alpha = -float('inf')
            beta = float('inf')
            scores = []
            iter_best = None
            iter_best_score = -float('inf')
            for f, t, cap in moves:
                b[t] = 1
                b[f] = 0
                score = -searcher.search(b, -1, depth - 1, -beta, -alpha)
                b[f] = 1
                b[t] = cap
                scores.append((score, (f, t, cap)))
                if score > iter_best_score:
                    iter_best_score = score
                    iter_best = (f, t, cap)
                    best_move = iter_best
                if score > alpha:
                    alpha = score
            scores.sort(key=lambda x: -x[0])
            moves = [m for _, m in scores]
            best_move = moves[0]
            if iter_best_score >= WIN or iter_best_score <= -WIN:
                break
            depth += 1
            if time.time() - start > TIME_BUDGET * 0.5:
                break
    except Timeout:
        pass
    return fmt(best_move)
