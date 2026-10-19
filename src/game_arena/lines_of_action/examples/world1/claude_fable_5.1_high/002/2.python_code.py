
import time

INF = 10**9
WIN = 1000000
TIME_LIMIT = 0.8

PST_2D = [
    [-80, -25, -20, -20, -20, -20, -25, -80],
    [-25,  10,  10,  10,  10,  10,  10, -25],
    [-20,  10,  25,  25,  25,  25,  10, -20],
    [-20,  10,  25,  50,  50,  25,  10, -20],
    [-20,  10,  25,  50,  50,  25,  10, -20],
    [-20,  10,  25,  25,  25,  25,  10, -20],
    [-25,  10,  10,  10,  10,  10,  10, -25],
    [-80, -25, -20, -20, -20, -20, -25, -80],
]
PST = [PST_2D[i >> 3][i & 7] for i in range(64)]

AXES = [(0, 1), (1, 0), (1, 1), (1, -1)]

NBR = []
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
    NBR.append(tuple(_lst))


class Timeout(Exception):
    pass


def gen_moves(b, p):
    moves = []
    q = -p
    for idx in range(64):
        if b[idx] != p:
            continue
        r = idx >> 3
        c = idx & 7
        for dr, dc in AXES:
            cnt = 1
            rr = r + dr
            cc = c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                if b[rr * 8 + cc]:
                    cnt += 1
                rr += dr
                cc += dc
            rr = r - dr
            cc = c - dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                if b[rr * 8 + cc]:
                    cnt += 1
                rr -= dr
                cc -= dc
            for s in (1, -1):
                ddr = dr * s
                ddc = dc * s
                tr = r + ddr * cnt
                tc = c + ddc * cnt
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                ok = True
                for k in range(1, cnt):
                    if b[(r + ddr * k) * 8 + c + ddc * k] == q:
                        ok = False
                        break
                if ok:
                    t = tr * 8 + tc
                    if b[t] != p:
                        moves.append((idx, t))
    return moves


def connected(b, p):
    total = 0
    start = -1
    for i in range(64):
        if b[i] == p:
            total += 1
            if start < 0:
                start = i
    if total == 0:
        return False
    if total == 1:
        return True
    visited = bytearray(64)
    visited[start] = 1
    stack = [start]
    cnt = 0
    while stack:
        i = stack.pop()
        cnt += 1
        for j in NBR[i]:
            if b[j] == p and not visited[j]:
                visited[j] = 1
                stack.append(j)
    return cnt == total


def eval_side(b, p):
    pieces = [i for i in range(64) if b[i] == p]
    n = len(pieces)
    if n == 0:
        return -50000
    visited = bytearray(64)
    comps = 0
    largest = 0
    for i in pieces:
        if not visited[i]:
            comps += 1
            visited[i] = 1
            stack = [i]
            size = 0
            while stack:
                x = stack.pop()
                size += 1
                for j in NBR[x]:
                    if b[j] == p and not visited[j]:
                        visited[j] = 1
                        stack.append(j)
            if size > largest:
                largest = size
    pst = 0
    sr = 0
    sc = 0
    for i in pieces:
        pst += PST[i]
        sr += i >> 3
        sc += i & 7
    sr /= n
    sc /= n
    conc = 0.0
    for i in pieces:
        dr = abs((i >> 3) - sr)
        dc = abs((i & 7) - sc)
        conc += dr if dr > dc else dc
    score = -60 * (comps - 1) + pst - 10 * conc + 8 * largest
    return score


def evaluate(b):
    return eval_side(b, 1) - eval_side(b, -1)


def order_key(b, p, m):
    f, t = m
    k = PST[t] - PST[f]
    if b[t] == -p:
        k += 60
    nf = 0
    nt = 0
    for j in NBR[t]:
        if b[j] == p and j != f:
            nt += 1
    for j in NBR[f]:
        if b[j] == p:
            nf += 1
    k += 7 * (nt - nf)
    return -k


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 127) == 0:
            if time.perf_counter() > self.deadline:
                raise Timeout()

    def search(self, b, p, depth, alpha, beta):
        self.check_time()
        moves = gen_moves(b, p)
        if not moves:
            return p * evaluate(b)
        moves.sort(key=lambda m: order_key(b, p, m))
        best = -INF
        for f, t in moves:
            cap = b[t]
            b[t] = p
            b[f] = 0
            if connected(b, p):
                val = WIN + depth
            elif cap != 0 and connected(b, -p):
                val = -(WIN + depth)
            elif depth <= 1:
                val = p * evaluate(b)
            else:
                val = -self.search(b, -p, depth - 1, -beta, -alpha)
            b[f] = p
            b[t] = cap
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best


def fmt(m):
    f, t = m
    return "%d,%d:%d,%d" % (f >> 3, f & 7, t >> 3, t & 7)


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + TIME_LIMIT
    b = [0] * 64
    for r in range(8):
        for c in range(8):
            v = int(board[r][c])
            b[r * 8 + c] = 1 if v > 0 else (-1 if v < 0 else 0)
    p = 1
    moves = gen_moves(b, p)
    if not moves:
        # No legal moves; return something syntactically valid.
        for i in range(64):
            if b[i] == p:
                r, c = i >> 3, i & 7
                return "%d,%d:%d,%d" % (r, c, r, c)
        return "0,0:0,0"
    moves.sort(key=lambda m: order_key(b, p, m))
    # Immediate win check
    for f, t in moves:
        cap = b[t]
        b[t] = p
        b[f] = 0
        win = connected(b, p)
        b[f] = p
        b[t] = cap
        if win:
            return fmt((f, t))
    best_move = moves[0]
    try:
        searcher = Searcher(deadline)
        depth = 1
        while depth <= 8:
            ordered = [best_move] + [m for m in moves if m != best_move]
            cur_best = None
            cur_val = -INF
            alpha = -INF
            beta = INF
            for f, t in ordered:
                cap = b[t]
                b[t] = p
                b[f] = 0
                if connected(b, p):
                    val = WIN + depth
                elif cap != 0 and connected(b, -p):
                    val = -(WIN + depth)
                elif depth <= 1:
                    val = p * evaluate(b)
                else:
                    val = -searcher.search(b, -p, depth - 1, -beta, -alpha)
                b[f] = p
                b[t] = cap
                if val > cur_val:
                    cur_val = val
                    cur_best = (f, t)
                if val > alpha:
                    alpha = val
            if cur_best is not None:
                best_move = cur_best
            if cur_val >= WIN or cur_val <= -WIN:
                break
            depth += 1
            if time.perf_counter() - start > TIME_LIMIT * 0.45:
                break
    except Timeout:
        pass
    except Exception:
        pass
    return fmt(best_move)
