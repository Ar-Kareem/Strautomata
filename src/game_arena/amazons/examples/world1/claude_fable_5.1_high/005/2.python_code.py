
import time
import numpy as np

DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
N = 6
TIME_BUDGET = 0.80


class Timeout(Exception):
    pass


def gen_moves(b, player):
    moves = []
    for r in range(N):
        row = b[r]
        for c in range(N):
            if row[c] == player:
                row[c] = 0
                for dr, dc in DIRS:
                    tr, tc = r + dr, c + dc
                    while 0 <= tr < N and 0 <= tc < N and b[tr][tc] == 0:
                        for ar, ac in DIRS:
                            xr, xc = tr + ar, tc + ac
                            while 0 <= xr < N and 0 <= xc < N and b[xr][xc] == 0:
                                moves.append((r, c, tr, tc, xr, xc))
                                xr += ar
                                xc += ac
                        tr += dr
                        tc += dc
                row[c] = player
    return moves


def has_move(b, player):
    for r in range(N):
        for c in range(N):
            if b[r][c] == player:
                for dr, dc in DIRS:
                    tr, tc = r + dr, c + dc
                    if 0 <= tr < N and 0 <= tc < N and b[tr][tc] == 0:
                        return True
    return False


def territory(b, player):
    dist = [[99] * N for _ in range(N)]
    frontier = []
    for r in range(N):
        for c in range(N):
            if b[r][c] == player:
                frontier.append((r, c))
    d = 0
    while frontier:
        d += 1
        nxt = []
        for r, c in frontier:
            for dr, dc in DIRS:
                tr, tc = r + dr, c + dc
                while 0 <= tr < N and 0 <= tc < N and b[tr][tc] == 0:
                    if dist[tr][tc] > d:
                        dist[tr][tc] = d
                        nxt.append((tr, tc))
                    tr += dr
                    tc += dc
        frontier = nxt
    return dist


def evaluate(b, to_move):
    # Score from perspective of player 1
    d1 = territory(b, 1)
    d2 = territory(b, 2)
    score = 0.0
    m1 = 0
    m2 = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == 0:
                a = d1[r][c]
                o = d2[r][c]
                if a == 1:
                    m1 += 1
                if o == 1:
                    m2 += 1
                if a < o:
                    score += 1.0
                elif o < a:
                    score -= 1.0
                elif a < 99:
                    score += 0.25 if to_move == 1 else -0.25
    score += 0.35 * (m1 - m2)
    return score


def order_key_factory(b, opp):
    opp_pos = []
    for r in range(N):
        for c in range(N):
            if b[r][c] == opp:
                opp_pos.append((r, c))

    def key(m):
        _, _, tr, tc, xr, xc = m
        s = 0
        for (pr, pc) in opp_pos:
            if abs(pr - xr) <= 1 and abs(pc - xc) <= 1:
                s += 2
            if abs(pr - tr) <= 1 and abs(pc - tc) <= 1:
                s += 1
        return -s

    return key


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0

    def negamax(self, b, depth, alpha, beta, player):
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.time() > self.deadline:
            raise Timeout()
        opp = 3 - player
        if depth <= 0:
            v = evaluate(b, player)
            return v if player == 1 else -v
        moves = gen_moves(b, player)
        if not moves:
            return -1000.0 - depth
        if depth > 1:
            moves.sort(key=order_key_factory(b, opp))
        best = -1e9
        for (r, c, tr, tc, xr, xc) in moves:
            b[r][c] = 0
            b[tr][tc] = player
            b[xr][xc] = -1
            v = -self.negamax(b, depth - 1, -beta, -alpha, opp)
            b[xr][xc] = 0
            b[tr][tc] = 0
            b[r][c] = player
            if v > best:
                best = v
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break
        return best


def fmt(m):
    r, c, tr, tc, xr, xc = m
    return "%d,%d:%d,%d:%d,%d" % (r, c, tr, tc, xr, xc)


def policy(board) -> str:
    start = time.time()
    deadline = start + TIME_BUDGET
    try:
        b = [[int(board[r][c]) for c in range(N)] for r in range(N)]
    except Exception:
        b = np.array(board).astype(int).tolist()

    moves = gen_moves(b, 1)
    if not moves:
        return "0,0:0,0:0,0"
    best_move = moves[0]

    try:
        searcher = Searcher(deadline)
        # initial ordering
        moves.sort(key=order_key_factory(b, 2))
        depth = 1
        while depth <= 12:
            scores = []
            alpha = -1e9
            beta = 1e9
            cur_best = None
            cur_best_val = -1e9
            for m in moves:
                r, c, tr, tc, xr, xc = m
                b[r][c] = 0
                b[tr][tc] = 1
                b[xr][xc] = -1
                try:
                    v = -searcher.negamax(b, depth - 1, -beta, -alpha, 2)
                finally:
                    b[xr][xc] = 0
                    b[tr][tc] = 0
                    b[r][c] = 1
                scores.append((v, m))
                if v > cur_best_val:
                    cur_best_val = v
                    cur_best = m
                if v > alpha:
                    alpha = v
            if cur_best is not None:
                best_move = cur_best
            scores.sort(key=lambda x: -x[0])
            moves = [m for _, m in scores]
            if cur_best_val > 900 or cur_best_val < -900:
                break
            if time.time() - start > TIME_BUDGET * 0.4:
                break
            depth += 1
    except Timeout:
        pass
    except Exception:
        pass

    return fmt(best_move)
