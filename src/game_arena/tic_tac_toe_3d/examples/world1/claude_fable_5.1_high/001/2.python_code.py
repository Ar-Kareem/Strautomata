
import time

WIN = 1000000
TIME_LIMIT = 0.55


def _build_lines():
    dirs = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                if (di, dj, dk) > (0, 0, 0):
                    dirs.append((di, dj, dk))
    lines = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for di, dj, dk in dirs:
                    pi, pj, pk = i - di, j - dj, k - dk
                    if 0 <= pi < 3 and 0 <= pj < 3 and 0 <= pk < 3:
                        continue
                    ei, ej, ek = i + 2 * di, j + 2 * dj, k + 2 * dk
                    if 0 <= ei < 3 and 0 <= ej < 3 and 0 <= ek < 3:
                        lines.append((i * 9 + j * 3 + k,
                                      (i + di) * 9 + (j + dj) * 3 + (k + dk),
                                      ei * 9 + ej * 3 + ek))
    return lines


LINES = _build_lines()
CELL_LINES = [[] for _ in range(27)]
for _li, _l in enumerate(LINES):
    for _c in _l:
        CELL_LINES[_c].append(_li)

W = (0, 1, 8, 0)


class Timeout(Exception):
    pass


def wins_at(b, c, player):
    # b[c] is assumed empty
    for li in CELL_LINES[c]:
        a, d, e = LINES[li]
        if b[a] + b[d] + b[e] == 2 * player:
            return True
    return False


def evaluate(b, player):
    s = 0
    opp = -player
    for a, c, d in LINES:
        x, y, z = b[a], b[c], b[d]
        p = (x == player) + (y == player) + (z == player)
        n = (x == opp) + (y == opp) + (z == opp)
        if n == 0:
            s += W[p]
        elif p == 0:
            s -= W[n]
    return s


def order_moves(b, empties, player):
    opp = -player
    scored = []
    for c in empties:
        s = 0
        for li in CELL_LINES[c]:
            a, d, e = LINES[li]
            x, y, z = b[a], b[d], b[e]
            p = (x == player) + (y == player) + (z == player)
            n = (x == opp) + (y == opp) + (z == opp)
            if n == 0:
                s += (1, 6, 200)[p]
            elif p == 0:
                s += (0, 2, 100)[n]
        scored.append((s, c))
    scored.sort(reverse=True)
    return [c for _, c in scored]


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def negamax(self, b, player, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 511) == 0 and time.time() > self.deadline:
            raise Timeout
        empties = [c for c in range(27) if b[c] == 0]
        if not empties:
            return 0
        for c in empties:
            if wins_at(b, c, player):
                return WIN - ply
        threats = [c for c in empties if wins_at(b, c, -player)]
        if len(threats) >= 2:
            return -(WIN - ply - 1)
        if threats:
            c = threats[0]
            b[c] = player
            v = -self.negamax(b, -player, depth, -beta, -alpha, ply + 1)
            b[c] = 0
            return v
        if depth <= 0:
            return evaluate(b, player)
        key = (tuple(b), player)
        ent = self.tt.get(key)
        if ent is not None and ent[0] >= depth:
            flag, val = ent[1], ent[2]
            if flag == 0:
                return val
            if flag == 1 and val >= beta:
                return val
            if flag == 2 and val <= alpha:
                return val
        moves = order_moves(b, empties, player)
        best = -10 * WIN
        a0 = alpha
        for c in moves:
            b[c] = player
            v = -self.negamax(b, -player, depth - 1, -beta, -alpha, ply + 1)
            b[c] = 0
            if v > best:
                best = v
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break
        if best >= beta:
            flag = 1
        elif best <= a0:
            flag = 2
        else:
            flag = 0
        self.tt[key] = (depth, flag, best)
        return best

    def root(self, b, moves, depth, prev_best):
        if prev_best is not None and prev_best in moves:
            moves = [prev_best] + [m for m in moves if m != prev_best]
        alpha = -10 * WIN
        beta = 10 * WIN
        best_move = moves[0]
        best_val = -10 * WIN
        for c in moves:
            b[c] = 1
            v = -self.negamax(b, -1, depth - 1, -beta, -alpha, 1)
            b[c] = 0
            if v > best_val:
                best_val = v
                best_move = c
            if v > alpha:
                alpha = v
        return best_val, best_move


def _to_tuple(c):
    return (c // 9, (c // 3) % 3, c % 3)


def policy(board):
    start = time.time()
    try:
        b = [board[i][j][k] for i in range(3) for j in range(3) for k in range(3)]
        empties = [c for c in range(27) if b[c] == 0]
        if not empties:
            return (0, 0, 0)
        if len(empties) == 27 or (len(empties) == 26 and b[13] == 0):
            return (1, 1, 1)
        for c in empties:
            if wins_at(b, c, 1):
                return _to_tuple(c)
        threats = [c for c in empties if wins_at(b, c, -1)]
        if len(threats) == 1:
            return _to_tuple(threats[0])
        moves = threats if threats else empties
        moves = order_moves(b, moves, 1)
        best = moves[0]
        deadline = start + TIME_LIMIT
        searcher = Searcher(deadline)
        prev_best = None
        for depth in range(1, len(empties) + 1):
            try:
                val, mv = searcher.root(b, moves, depth, prev_best)
                best = mv
                prev_best = mv
                if val >= WIN - 100 or val <= -WIN + 100:
                    break
            except Timeout:
                break
            if time.time() > deadline:
                break
        if b[best] != 0:
            best = empties[0]
        return _to_tuple(best)
    except Exception:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i, j, k)
        return (0, 0, 0)
