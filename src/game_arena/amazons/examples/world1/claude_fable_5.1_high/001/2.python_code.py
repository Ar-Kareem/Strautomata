
import time
import numpy as np

N = 6
DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
RAYS = []
NEIGH = []
for r in range(N):
    for c in range(N):
        rays = []
        for dr, dc in DIRS:
            ray = []
            rr, cc = r+dr, c+dc
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr*N+cc)
                rr += dr; cc += dc
            if ray:
                rays.append(ray)
        RAYS.append(rays)
        nb = []
        for dr, dc in DIRS:
            rr, cc = r+dr, c+dc
            if 0 <= rr < N and 0 <= cc < N:
                nb.append(rr*N+cc)
        NEIGH.append(nb)

class Timeout(Exception):
    pass

INF = float('inf')
WIN = 1000

def gen_moves(b, p):
    moves = []
    for frm in range(36):
        if b[frm] != p:
            continue
        b[frm] = 0
        for ray in RAYS[frm]:
            for to in ray:
                if b[to] != 0:
                    break
                for ray2 in RAYS[to]:
                    for ar in ray2:
                        if b[ar] != 0:
                            break
                        moves.append((frm, to, ar))
        b[frm] = p
    return moves

def dist_map(b, player):
    d = [99]*36
    frontier = []
    for i in range(36):
        if b[i] == player:
            d[i] = 0
            frontier.append(i)
    k = 0
    while frontier:
        nxt = []
        for i in frontier:
            for ray in RAYS[i]:
                for j in ray:
                    if b[j] != 0:
                        break
                    if d[j] > k+1:
                        d[j] = k+1
                        nxt.append(j)
        k += 1
        frontier = nxt
    return d

def evaluate(b):
    d1 = dist_map(b, 1)
    d2 = dist_map(b, 2)
    t = 0.0
    m1 = 0
    m2 = 0
    for i in range(36):
        if b[i] == 0:
            a = d1[i]; c = d2[i]
            if a == 1: m1 += 1
            if c == 1: m2 += 1
            if a < c: t += 1.0
            elif c < a: t -= 1.0
    return t, m1, m2

class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}
        self.nodes = 0

    def search(self, b, p, depth, alpha, beta):
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.perf_counter() > self.deadline:
            raise Timeout()
        if depth == 0:
            t, m1, m2 = evaluate(b)
            if p == 1:
                if m1 == 0:
                    return -WIN
                return t + 0.3*(m1-m2) + 0.1
            else:
                if m2 == 0:
                    return -WIN
                return -(t + 0.3*(m1-m2)) + 0.1
        key = (bytes(b), p)
        ent = self.tt.get(key)
        ttmove = None
        if ent is not None:
            edepth, eval_, eflag, emove = ent
            ttmove = emove
            if edepth >= depth:
                if eflag == 0:
                    return eval_
                elif eflag == 1:
                    if eval_ >= beta:
                        return eval_
                    if eval_ > alpha:
                        alpha = eval_
                else:
                    if eval_ <= alpha:
                        return eval_
                    if eval_ < beta:
                        beta = eval_
        moves = gen_moves(b, p)
        if not moves:
            return -(WIN + depth)
        opp = 3 - p
        near = [0]*36
        for i in range(36):
            if b[i] == opp:
                for j in NEIGH[i]:
                    near[j] += 1
        moves.sort(key=lambda m: -near[m[2]])
        if ttmove is not None and ttmove in moves:
            moves.remove(ttmove)
            moves.insert(0, ttmove)
        a0 = alpha
        best = -INF
        bestm = moves[0]
        for m in moves:
            f, t_, a = m
            b[f] = 0; b[t_] = p; b[a] = 3
            try:
                v = -self.search(b, opp, depth-1, -beta, -alpha)
            finally:
                b[a] = 0; b[t_] = 0; b[f] = p
            if v > best:
                best = v
                bestm = m
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        if best >= beta:
            flag = 1
        elif best <= a0:
            flag = 2
        else:
            flag = 0
        self.tt[key] = (depth, best, flag, bestm)
        return best

def fmt(m):
    f, t, a = m
    return "%d,%d:%d,%d:%d,%d" % (f//N, f%N, t//N, t%N, a//N, a%N)

def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.72
    arr = np.asarray(board).flatten()
    b = []
    for x in arr:
        v = int(x)
        b.append(3 if v == -1 else v)
    moves = gen_moves(b, 1)
    if not moves:
        return "0,0:0,0:0,0"
    best = moves[0]
    S = Searcher(deadline)
    ordered = moves
    depth = 1
    try:
        while depth <= 30:
            alpha = -INF
            scores = []
            cur_best = None
            for m in ordered:
                f, t_, a = m
                b[f] = 0; b[t_] = 1; b[a] = 3
                try:
                    v = -S.search(b, 2, depth-1, -INF, -alpha)
                finally:
                    b[a] = 0; b[t_] = 0; b[f] = 1
                scores.append((v, m))
                if v > alpha:
                    alpha = v
                    cur_best = m
            if cur_best is not None:
                best = cur_best
            scores.sort(key=lambda x: -x[0])
            ordered = [m for v, m in scores]
            if alpha >= WIN or alpha <= -WIN:
                break
            depth += 1
    except Timeout:
        pass
    return fmt(best)
