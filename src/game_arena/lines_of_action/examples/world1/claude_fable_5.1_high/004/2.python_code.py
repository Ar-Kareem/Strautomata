
import time

INF = 10 ** 9
WIN = 10 ** 6
TIME_BUDGET = 0.80

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
LT = []
for dr, dc in DIRS:
    if dr == 0:
        LT.append(0)
    elif dc == 0:
        LT.append(1)
    elif dr == dc:
        LT.append(2)
    else:
        LT.append(3)

RAY = []
NEIGH = []
for sq in range(64):
    r, c = divmod(sq, 8)
    rays = []
    for dr, dc in DIRS:
        ray = []
        rr, cc = r + dr, c + dc
        while 0 <= rr < 8 and 0 <= cc < 8:
            ray.append(rr * 8 + cc)
            rr += dr
            cc += dc
        rays.append(ray)
    RAY.append(rays)
    NEIGH.append([ray[0] for ray in rays if ray])

PST_2D = [
    [-20, -6, -5, -5, -5, -5, -6, -20],
    [-6, 3, 3, 3, 3, 3, 3, -6],
    [-5, 3, 6, 6, 6, 6, 3, -5],
    [-5, 3, 6, 12, 12, 6, 3, -5],
    [-5, 3, 6, 12, 12, 6, 3, -5],
    [-5, 3, 6, 6, 6, 6, 3, -5],
    [-6, 3, 3, 3, 3, 3, 3, -6],
    [-20, -6, -5, -5, -5, -5, -6, -20],
]
PST = [PST_2D[sq >> 3][sq & 7] for sq in range(64)]

W_G = 50
W_C = 6
W_L = 4


class Timeout(Exception):
    pass


def gen_moves(b, p):
    rc = [0] * 8
    cc = [0] * 8
    dc = [0] * 15
    ac = [0] * 15
    mine = []
    for sq in range(64):
        v = b[sq]
        if v:
            r = sq >> 3
            c = sq & 7
            rc[r] += 1
            cc[c] += 1
            dc[r - c + 7] += 1
            ac[r + c] += 1
            if v == p:
                mine.append(sq)
    moves = []
    q = -p
    for sq in mine:
        r = sq >> 3
        c = sq & 7
        lens = (rc[r], cc[c], dc[r - c + 7], ac[r + c])
        rays = RAY[sq]
        for di in range(8):
            n = lens[LT[di]]
            ray = rays[di]
            if len(ray) < n:
                continue
            ok = True
            for i in range(n - 1):
                if b[ray[i]] == q:
                    ok = False
                    break
            if ok:
                t = ray[n - 1]
                if b[t] != p:
                    moves.append((sq, t))
    return moves


def connected(b, p):
    start = -1
    total = 0
    for sq in range(64):
        if b[sq] == p:
            total += 1
            if start < 0:
                start = sq
    if total == 0:
        return False
    seen = {start}
    stack = [start]
    while stack:
        s = stack.pop()
        for nb in NEIGH[s]:
            if b[nb] == p and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return len(seen) == total


def side_score(b, p):
    pieces = [sq for sq in range(64) if b[sq] == p]
    n = len(pieces)
    if n == 0:
        return -WIN // 2
    sr = 0
    sc = 0
    pst = 0
    for sq in pieces:
        sr += sq >> 3
        sc += sq & 7
        pst += PST[sq]
    cr = sr / n
    ccm = sc / n
    conc = 0.0
    for sq in pieces:
        dr = abs((sq >> 3) - cr)
        dcol = abs((sq & 7) - ccm)
        conc += dr if dr > dcol else dcol
    seen = set()
    g = 0
    links = 0
    for sq in pieces:
        if sq in seen:
            continue
        g += 1
        seen.add(sq)
        stack = [sq]
        while stack:
            s = stack.pop()
            for nb in NEIGH[s]:
                if b[nb] == p:
                    links += 1
                    if nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
    return -g * W_G - conc * W_C + pst + (links // 2) * W_L


def evaluate(b, p):
    return side_score(b, p) - side_score(b, -p)


def order_moves(b, moves, p):
    def key(m):
        f, t = m
        s = PST[t] - PST[f]
        if b[t] == -p:
            s += 40
        return -s
    moves.sort(key=key)
    return moves


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.time() > self.deadline:
            raise Timeout()

    def negamax(self, b, p, depth, alpha, beta):
        self.check_time()
        if depth == 0:
            return evaluate(b, p)
        moves = gen_moves(b, p)
        if not moves:
            return evaluate(b, p)
        order_moves(b, moves, p)
        best = -INF
        for f, t in moves:
            cap = b[t]
            b[t] = p
            b[f] = 0
            if connected(b, p):
                val = WIN + depth
            elif cap != 0 and connected(b, -p):
                val = -WIN - depth
            elif cap != 0 and not any(x == -p for x in b):
                val = -WIN - depth
            else:
                val = -self.negamax(b, -p, depth - 1, -beta, -alpha)
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
    start = time.time()
    deadline = start + TIME_BUDGET
    b = [0] * 64
    for r in range(8):
        row = board[r]
        for c in range(8):
            b[r * 8 + c] = int(row[c])
    p = 1
    moves = gen_moves(b, p)
    if not moves:
        # No legal moves (should not happen); return something syntactically valid.
        for sq in range(64):
            if b[sq] == 1:
                return fmt((sq, sq))
        return "0,0:0,0"

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

    order_moves(b, moves, p)
    best_move = moves[0]
    searcher = Searcher(deadline)
    depth = 1
    try:
        while depth <= 12:
            # put previous best first
            if best_move in moves:
                moves.remove(best_move)
                moves.insert(0, best_move)
            alpha = -INF
            beta = INF
            cur_best = None
            cur_val = -INF
            completed = True
            for f, t in moves:
                cap = b[t]
                b[t] = p
                b[f] = 0
                try:
                    if connected(b, p):
                        val = WIN + depth
                    elif cap != 0 and connected(b, -p):
                        val = -WIN - depth
                    elif cap != 0 and not any(x == -p for x in b):
                        val = -WIN - depth
                    else:
                        val = -searcher.negamax(b, -p, depth - 1, -beta, -alpha)
                except Timeout:
                    b[f] = p
                    b[t] = cap
                    completed = False
                    break
                b[f] = p
                b[t] = cap
                if val > cur_val:
                    cur_val = val
                    cur_best = (f, t)
                if val > alpha:
                    alpha = val
            if cur_best is not None:
                best_move = cur_best
            if not completed:
                break
            if cur_val >= WIN or cur_val <= -WIN:
                break
            depth += 1
            if time.time() - start > TIME_BUDGET * 0.45:
                break
    except Timeout:
        pass
    except Exception:
        pass
    return fmt(best_move)
