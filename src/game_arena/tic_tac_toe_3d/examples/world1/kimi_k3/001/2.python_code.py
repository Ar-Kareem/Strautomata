
import time


def _build_lines():
    """Generate all 49 winning lines of a 3x3x3 cube."""
    lines = []
    seen = set()
    dirs = [(di, dj, dk)
            for di in (-1, 0, 1)
            for dj in (-1, 0, 1)
            for dk in (-1, 0, 1)
            if (di, dj, dk) != (0, 0, 0)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for di, dj, dk in dirs:
                    a = (i + di, j + dj, k + dk)
                    b = (i + 2 * di, j + 2 * dj, k + 2 * dk)
                    if (0 <= a[0] < 3 and 0 <= a[1] < 3 and 0 <= a[2] < 3
                            and 0 <= b[0] < 3 and 0 <= b[1] < 3 and 0 <= b[2] < 3):
                        key = tuple(sorted(((i, j, k), a, b)))
                        if key not in seen:
                            seen.add(key)
                            lines.append(key)
    return lines


_LINES3 = _build_lines()                                   # 49 winning lines
_LINES = [tuple(i * 9 + j * 3 + k for (i, j, k) in line)   # flattened cells
          for line in _LINES3]
_NL = len(_LINES)

_CELL_LINES = [[] for _ in range(27)]
for _li, _ln in enumerate(_LINES):
    for _c in _ln:
        _CELL_LINES[_c].append(_li)
_CELL_LINES = [tuple(x) for x in _CELL_LINES]
_CELL_W = tuple(len(x) for x in _CELL_LINES)   # center=13, corner=7, face=5, edge=4

_WIN = 10 ** 7
_INF = 10 ** 9
_VAL = (0, 1, 100, 0)      # value of an open line with n of our pieces
_BUDGET = 0.9              # seconds of search per move


def _find_threat(empties, cnt):
    """Return an empty cell that completes a line for the given counters, else -1."""
    for c in empties:
        for li in _CELL_LINES[c]:
            if cnt[li] == 2:
                return c
    return -1


class _Solver:
    __slots__ = ('b', 'cnt', 'empties', 'nodes', 'deadline', 'abort', 'tt')

    def __init__(self, board):
        b = []
        for i in range(3):
            bi = board[i]
            for j in range(3):
                bij = bi[j]
                for k in range(3):
                    b.append(bij[k])
        self.b = b
        self.cnt = [[0] * _NL, [0] * _NL]      # [0]=us (player 1), [1]=opponent
        self.empties = []
        for c in range(27):
            v = b[c]
            if v == 0:
                self.empties.append(c)
            else:
                arr = self.cnt[0] if v == 1 else self.cnt[1]
                for li in _CELL_LINES[c]:
                    arr[li] += 1
        self.nodes = 0
        self.deadline = 0.0
        self.abort = False
        self.tt = {}

    def _make(self, c, pidx):
        self.b[c] = 1 if pidx == 0 else -1
        arr = self.cnt[pidx]
        for li in _CELL_LINES[c]:
            arr[li] += 1
        self.empties.remove(c)

    def _unmake(self, c, pidx):
        self.b[c] = 0
        arr = self.cnt[pidx]
        for li in _CELL_LINES[c]:
            arr[li] -= 1
        self.empties.append(c)

    def _won(self, c, pidx):
        arr = self.cnt[pidx]
        for li in _CELL_LINES[c]:
            if arr[li] == 3:
                return True
        return False

    def _evaluate(self, pidx):
        my = self.cnt[pidx]
        op = self.cnt[pidx ^ 1]
        s = 0
        for li in range(_NL):
            a = my[li]
            o = op[li]
            if a:
                if not o:
                    s += _VAL[a]
            elif o:
                s -= _VAL[o]
        return s

    def _ordered(self, pidx):
        my = self.cnt[pidx]
        op = self.cnt[pidx ^ 1]
        scored = []
        for c in self.empties:
            w = _CELL_W[c]
            block = False
            for li in _CELL_LINES[c]:
                if my[li] == 2:            # winning move
                    w += 1000000
                    block = False
                    break
                if op[li] == 2:            # must-block move
                    block = True
            if block:
                w += 500000
            scored.append((w, c))
        scored.sort(reverse=True)
        return [c for _, c in scored]

    def negamax(self, depth, alpha, beta, pidx, ply):
        self.nodes += 1
        if (self.nodes & 1023) == 0 and time.time() >= self.deadline:
            self.abort = True
            return 0
        if depth == 0:
            return self._evaluate(pidx)

        key = (tuple(self.b), pidx)
        ent = self.tt.get(key)
        if ent is not None and ent[0] >= depth:
            ev = ent[1]
            ef = ent[2]
            if ef == 0:                    # exact
                return ev
            if ef == 1:                    # lower bound
                if ev > alpha:
                    alpha = ev
            elif ev < beta:                # upper bound
                beta = ev
            if alpha >= beta:
                return ev

        alpha0 = alpha
        beta0 = beta
        best = -_INF
        for c in self._ordered(pidx):
            self._make(c, pidx)
            if self._won(c, pidx):
                score = _WIN - ply
            elif not self.empties:
                score = 0
            else:
                score = -self.negamax(depth - 1, -beta, -alpha, pidx ^ 1, ply + 1)
            self._unmake(c, pidx)
            if self.abort:
                return 0
            if score > best:
                best = score
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        break
        if best <= alpha0:
            flag = 2                       # upper bound
        elif best >= beta0:
            flag = 1                       # lower bound
        else:
            flag = 0                       # exact
        self.tt[key] = (depth, best, flag)
        return best

    def best_move(self, budget):
        self.deadline = time.time() + budget
        best = self._ordered(0)[0]
        max_depth = len(self.empties)
        depth = 1
        while depth <= max_depth:
            if time.time() >= self.deadline:
                break
            self.abort = False
            alpha = -_INF
            cur_best = None
            cur_score = -_INF
            root_moves = self._ordered(0)
            if best in root_moves:
                root_moves.remove(best)
                root_moves.insert(0, best)
            for c in root_moves:
                self._make(c, 0)
                if self._won(c, 0):
                    score = _WIN
                elif not self.empties:
                    score = 0
                else:
                    score = -self.negamax(depth - 1, -_INF, -alpha, 1, 1)
                self._unmake(c, 0)
                if self.abort:
                    cur_best = None
                    break
                if score > cur_score:
                    cur_score = score
                    cur_best = c
                if score > alpha:
                    alpha = score
            if cur_best is None:
                break
            best = cur_best
            if cur_score >= _WIN - 100:    # forced win found
                break
            depth += 1
        return best


def _to3(c):
    return (c // 9, (c // 3) % 3, c % 3)


def policy(board):
    try:
        empties = [(i, j, k)
                   for i in range(3) for j in range(3) for k in range(3)
                   if board[i][j][k] == 0]
        if not empties:
            return (0, 0, 0)
        if len(empties) == 27:
            return (1, 1, 1)               # strongest opening: the center

        solver = _Solver(board)
        em = solver.empties

        c = _find_threat(em, solver.cnt[0])    # win immediately
        if c >= 0:
            return _to3(c)
        c = _find_threat(em, solver.cnt[1])    # block opponent's immediate win
        if c >= 0:
            return _to3(c)
        if len(em) == 1:
            return _to3(em[0])

        c = solver.best_move(_BUDGET)
        if board[c // 9][(c // 3) % 3][c % 3] != 0:   # paranoid legality check
            c = em[0]
        return _to3(c)
    except Exception:
        # Last-resort fallback: first legal cell, so we always return a move.
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    try:
                        if board[i][j][k] == 0:
                            return (i, j, k)
                    except Exception:
                        pass
        return (1, 1, 1)
