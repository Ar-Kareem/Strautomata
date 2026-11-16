
import time

WIN = 100000
TIME_LIMIT = 0.72


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _gen_lines():
    dirs = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                d = (di, dj, dk)
                if d == (0, 0, 0):
                    continue
                for x in d:
                    if x != 0:
                        if x > 0:
                            dirs.append(d)
                        break
    lines = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for (di, dj, dk) in dirs:
                    a, b, c = i - di, j - dj, k - dk
                    if 0 <= a < 3 and 0 <= b < 3 and 0 <= c < 3:
                        continue
                    cells = []
                    ok = True
                    for t in range(3):
                        a, b, c = i + di * t, j + dj * t, k + dk * t
                        if not (0 <= a < 3 and 0 <= b < 3 and 0 <= c < 3):
                            ok = False
                            break
                        cells.append(_idx(a, b, c))
                    if ok:
                        lines.append(tuple(cells))
    return lines


LINES = _gen_lines()
CELL_LINES = [[] for _ in range(27)]
for ln in LINES:
    for c in ln:
        CELL_LINES[c].append(ln)
CELL_WEIGHT = [len(CELL_LINES[c]) for c in range(27)]
ORDER = sorted(range(27), key=lambda c: -CELL_WEIGHT[c])
CENTER = _idx(1, 1, 1)


class Timeout(Exception):
    pass


def _wins_at(b, m, p):
    for ln in CELL_LINES[m]:
        if b[ln[0]] == p and b[ln[1]] == p and b[ln[2]] == p:
            return True
    return False


def _winning_moves(b, p):
    res = []
    for ln in LINES:
        x, y, z = b[ln[0]], b[ln[1]], b[ln[2]]
        s = x + y + z
        if s == 2 * p:
            if x == 0:
                res.append(ln[0])
            elif y == 0:
                res.append(ln[1])
            else:
                res.append(ln[2])
    return res


def _evaluate(b, p):
    # evaluation from perspective of player p (to move)
    score = 0
    my_two = False
    opp_cells = set()
    for ln in LINES:
        x, y, z = b[ln[0]], b[ln[1]], b[ln[2]]
        cp = (x == p) + (y == p) + (z == p)
        co = (x == -p) + (y == -p) + (z == -p)
        if cp and co:
            continue
        if cp == 2:
            my_two = True
            score += 12
        elif cp == 1:
            score += 1
        elif co == 2:
            if x == 0:
                opp_cells.add(ln[0])
            elif y == 0:
                opp_cells.add(ln[1])
            else:
                opp_cells.add(ln[2])
            score -= 12
        elif co == 1:
            score -= 1
    if my_two:
        return 5000
    if len(opp_cells) >= 2:
        return -5000
    return score


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def search(self, b, p, depth, alpha, beta, empties):
        self.nodes += 1
        if (self.nodes & 511) == 0 and time.perf_counter() > self.deadline:
            raise Timeout()
        if empties == 0:
            return 0
        if depth <= 0:
            return _evaluate(b, p)
        key = (tuple(b), p)
        entry = self.tt.get(key)
        if entry is not None and entry[0] >= depth:
            val, flag = entry[1], entry[2]
            if flag == 0:
                return val
            elif flag == 1:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val
        alpha_orig = alpha
        moves = [c for c in ORDER if b[c] == 0]
        # order: winning moves first
        wins = []
        others = []
        for m in moves:
            b[m] = p
            if _wins_at(b, m, p):
                wins.append(m)
            else:
                others.append(m)
            b[m] = 0
        if wins:
            val = WIN + depth
            self.tt[key] = (depth, val, 0)
            return val
        best = -WIN * 10
        for m in others:
            b[m] = p
            val = -self.search(b, -p, depth - 1, -beta, -alpha, empties - 1)
            b[m] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        if best <= alpha_orig:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, best, flag)
        return best


def policy(board):
    start = time.perf_counter()
    b = [0] * 27
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                b[_idx(i, j, k)] = 1 if v == 1 else (-1 if v == -1 else 0)
    empties = [c for c in range(27) if b[c] == 0]
    if not empties:
        return (0, 0, 0)

    def to_tuple(c):
        return (c // 9, (c // 3) % 3, c % 3)

    # immediate win
    mw = _winning_moves(b, 1)
    if mw:
        return to_tuple(mw[0])
    # opening: center
    n_pieces = 27 - len(empties)
    if n_pieces <= 1 and b[CENTER] == 0:
        return to_tuple(CENTER)
    # immediate block if single threat
    ow = _winning_moves(b, -1)
    if ow:
        distinct = set(ow)
        if len(distinct) >= 1:
            fallback = ow[0]
    else:
        fallback = max(empties, key=lambda c: CELL_WEIGHT[c])

    deadline = start + TIME_LIMIT
    searcher = Searcher(deadline)
    best_move = fallback
    ordered = sorted(empties, key=lambda c: -CELL_WEIGHT[c])
    if ow:
        blocks = set(ow)
        ordered = [c for c in ordered if c in blocks] + [c for c in ordered if c not in blocks]
    try:
        for depth in range(1, len(empties) + 1):
            alpha = -WIN * 10
            beta = WIN * 10
            cur_best = None
            cur_val = -WIN * 10
            for m in ordered:
                b[m] = 1
                if _wins_at(b, m, 1):
                    val = WIN + depth
                else:
                    val = -searcher.search(b, -1, depth - 1, -beta, -alpha, len(empties) - 1)
                b[m] = 0
                if val > cur_val:
                    cur_val = val
                    cur_best = m
                if val > alpha:
                    alpha = val
            if cur_best is not None:
                best_move = cur_best
                # move best to front for next iteration
                ordered.remove(cur_best)
                ordered.insert(0, cur_best)
            if cur_val >= WIN or cur_val <= -WIN:
                break
    except Timeout:
        pass

    if b[best_move] != 0:
        best_move = empties[0]
    return to_tuple(best_move)
