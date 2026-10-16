
import time

BIG = 1000000
INF = float("inf")


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _build_lines():
    lines = []
    for a in range(3):
        for b in range(3):
            lines.append((_idx(a, b, 0), _idx(a, b, 1), _idx(a, b, 2)))
            lines.append((_idx(a, 0, b), _idx(a, 1, b), _idx(a, 2, b)))
            lines.append((_idx(0, a, b), _idx(1, a, b), _idx(2, a, b)))
    for a in range(3):
        lines.append((_idx(a, 0, 0), _idx(a, 1, 1), _idx(a, 2, 2)))
        lines.append((_idx(a, 0, 2), _idx(a, 1, 1), _idx(a, 2, 0)))
        lines.append((_idx(0, a, 0), _idx(1, a, 1), _idx(2, a, 2)))
        lines.append((_idx(0, a, 2), _idx(1, a, 1), _idx(2, a, 0)))
        lines.append((_idx(0, 0, a), _idx(1, 1, a), _idx(2, 2, a)))
        lines.append((_idx(0, 2, a), _idx(1, 1, a), _idx(2, 0, a)))
    lines.append((_idx(0, 0, 0), _idx(1, 1, 1), _idx(2, 2, 2)))
    lines.append((_idx(0, 0, 2), _idx(1, 1, 1), _idx(2, 2, 0)))
    lines.append((_idx(0, 2, 0), _idx(1, 1, 1), _idx(2, 0, 2)))
    lines.append((_idx(2, 0, 0), _idx(1, 1, 1), _idx(0, 2, 2)))
    return lines


LINES = _build_lines()
NL = len(LINES)  # 49 winning lines
L0 = [t[0] for t in LINES]
L1 = [t[1] for t in LINES]
L2 = [t[2] for t in LINES]

CELL_LINES = [[] for _ in range(27)]
for _li in range(NL):
    CELL_LINES[L0[_li]].append(_li)
    CELL_LINES[L1[_li]].append(_li)
    CELL_LINES[L2[_li]].append(_li)
CELL_LINES = [tuple(x) for x in CELL_LINES]
CELL_W = [len(x) for x in CELL_LINES]
CELLS = tuple(range(27))


class _Timeout(Exception):
    pass


def _conv(c):
    return (c // 9, (c % 9) // 3, c % 3)


def _threat_cells(b, player):
    """Empty cells that immediately complete a line for `player`."""
    cells = []
    for li in range(NL):
        x = L0[li]; y = L1[li]; z = L2[li]
        vx = b[x]; vy = b[y]; vz = b[z]
        if (vx == player) + (vy == player) + (vz == player) == 2:
            if vx == 0:
                cells.append(x)
            elif vy == 0:
                cells.append(y)
            elif vz == 0:
                cells.append(z)
    return cells


class _Search:
    __slots__ = ("b", "ob", "xb", "our", "opp", "filled",
                 "deadline", "nodes", "tt", "max_nodes")

    def __init__(self, b, deadline):
        self.b = list(b)
        self.ob = 0
        self.xb = 0
        self.our = [0] * NL
        self.opp = [0] * NL
        filled = 0
        for idx in CELLS:
            v = b[idx]
            if v:
                filled += 1
                if v == 1:
                    self.ob |= (1 << idx)
                    for li in CELL_LINES[idx]:
                        self.our[li] += 1
                else:
                    self.xb |= (1 << idx)
                    for li in CELL_LINES[idx]:
                        self.opp[li] += 1
        self.filled = filled
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.max_nodes = 600000

    def make(self, idx, val):
        self.b[idx] = val
        self.filled += 1
        if val == 1:
            self.ob |= (1 << idx)
            our = self.our
            for li in CELL_LINES[idx]:
                our[li] += 1
        else:
            self.xb |= (1 << idx)
            opp = self.opp
            for li in CELL_LINES[idx]:
                opp[li] += 1

    def undo(self, idx, val):
        self.b[idx] = 0
        self.filled -= 1
        if val == 1:
            self.ob &= ~(1 << idx)
            our = self.our
            for li in CELL_LINES[idx]:
                our[li] -= 1
        else:
            self.xb &= ~(1 << idx)
            opp = self.opp
            for li in CELL_LINES[idx]:
                opp[li] -= 1

    def evaluate(self):
        our = self.our
        opp = self.opp
        s = 0
        ot = 0
        pt = 0
        for li in range(NL):
            a = our[li]
            o = opp[li]
            if a:
                if o:
                    continue
                if a == 2:
                    s += 40
                    ot += 1
                else:
                    s += 2
            elif o:
                if o == 2:
                    s -= 42
                    pt += 1
                else:
                    s -= 2
        if ot >= 2:
            s += 3000      # our fork = forced win
        if pt >= 2:
            s -= 3100      # opponent fork = forced loss
        return s

    def gen(self, maximizing):
        b = self.b
        if maximizing:
            m = self.our
            o = self.opp
        else:
            m = self.opp
            o = self.our
        scores = [0] * 27
        for li in range(NL):
            ml = m[li]
            if ml:
                if o[li]:
                    continue
                v = 10000 if ml == 2 else 6
            else:
                ol = o[li]
                if ol == 2:
                    v = 3000
                elif ol == 1:
                    v = 2
                else:
                    continue
            x = L0[li]; y = L1[li]; z = L2[li]
            if b[x] == 0:
                scores[x] += v
            if b[y] == 0:
                scores[y] += v
            if b[z] == 0:
                scores[z] += v
        cw = CELL_W
        paired = [(scores[c] + cw[c], c) for c in CELLS if b[c] == 0]
        paired.sort(reverse=True)
        return [c for _, c in paired]

    def search(self, depth, alpha, beta, maximizing, last_idx):
        self.nodes += 1
        if (self.nodes & 1023) == 0:
            if self.nodes > self.max_nodes or time.perf_counter() > self.deadline:
                raise _Timeout
        if last_idx >= 0:
            pm = self.opp if maximizing else self.our
            for li in CELL_LINES[last_idx]:
                if pm[li] == 3:
                    return (-(BIG + depth)) if maximizing else (BIG + depth)
        if self.filled == 27:
            return 0
        if depth <= 0:
            m = self.our if maximizing else self.opp
            o = self.opp if maximizing else self.our
            for li in range(NL):
                if m[li] == 2 and o[li] == 0:
                    return (BIG - 1) if maximizing else (-(BIG - 1))
            return self.evaluate()
        key = self.ob | (self.xb << 27)
        entry = self.tt.get(key)
        tt_best = -1
        if entry is not None:
            if entry[0] >= depth:
                ev = entry[1]
                ef = entry[2]
                if ef == 0 or (ef == 1 and ev >= beta) or (ef == 2 and ev <= alpha):
                    return ev
            tt_best = entry[3]
        moves = self.gen(maximizing)
        if tt_best >= 0 and tt_best in moves:
            moves.remove(tt_best)
            moves.insert(0, tt_best)
        alpha_orig = alpha
        beta_orig = beta
        best_idx = moves[0]
        if maximizing:
            value = -INF
            for idx in moves:
                self.make(idx, 1)
                v = self.search(depth - 1, alpha, beta, False, idx)
                self.undo(idx, 1)
                if v > value:
                    value = v
                    best_idx = idx
                if v > alpha:
                    alpha = v
                if alpha >= beta:
                    break
        else:
            value = INF
            for idx in moves:
                self.make(idx, -1)
                v = self.search(depth - 1, alpha, beta, True, idx)
                self.undo(idx, -1)
                if v < value:
                    value = v
                    best_idx = idx
                if v < beta:
                    beta = v
                if alpha >= beta:
                    break
        if value <= alpha_orig:
            flag = 2
        elif value >= beta_orig:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, value, flag, best_idx)
        return value

    def root(self, depth, moves):
        alpha = -INF
        best_val = -INF
        best_mv = moves[0]
        for idx in moves:
            self.make(idx, 1)
            v = self.search(depth - 1, alpha, INF, False, idx)
            self.undo(idx, 1)
            if v > best_val:
                best_val = v
                best_mv = idx
            if v > alpha:
                alpha = v
        return best_val, best_mv

    def best_move(self, max_depth):
        moves = self.gen(True)
        if not moves:
            return None
        best = moves[0]
        depth = 1
        while depth <= max_depth and time.perf_counter() < self.deadline - 0.02:
            try:
                val, mv = self.root(depth, moves)
            except _Timeout:
                break
            best = mv
            moves.remove(best)
            moves.insert(0, best)
            if val >= BIG // 2:
                break
            depth += 1
        return best


def policy(board):
    try:
        b = [0] * 27
        for i in range(3):
            bi = board[i]
            for j in range(3):
                row = bi[j]
                base = i * 9 + j * 3
                b[base] = row[0]
                b[base + 1] = row[1]
                b[base + 2] = row[2]
        empties = [c for c in CELLS if b[c] == 0]
        if not empties:
            return (0, 0, 0)
        if len(empties) == 1:
            return _conv(empties[0])
        # 1) Immediate win
        tw = _threat_cells(b, 1)
        if tw:
            return _conv(tw[0])
        # 2) Block opponent's immediate win(s)
        tb = _threat_cells(b, -1)
        if tb:
            counts = {}
            best_c = tb[0]
            best_n = 0
            for c in tb:
                n = counts.get(c, 0) + 1
                counts[c] = n
                if n > best_n:
                    best_n = n
                    best_c = c
            return _conv(best_c)
        # 3) Opening book: grab the center while it is safe
        filled = 27 - len(empties)
        if b[13] == 0 and filled <= 2:
            return (1, 1, 1)
        # 4) Iterative-deepening alpha-beta search
        deadline = time.perf_counter() + 0.8
        s = _Search(b, deadline)
        e = len(empties)
        if e > 20:
            max_depth = 5
        elif e > 14:
            max_depth = 6
        elif e > 9:
            max_depth = 8
        else:
            max_depth = e  # solve the endgame exactly
        mv = s.best_move(max_depth)
        if mv is None or b[mv] != 0:
            mv = empties[0]
        return _conv(mv)
    except Exception:
        try:
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if board[i][j][k] == 0:
                            return (i, j, k)
        except Exception:
            pass
    return (0, 0, 0)
