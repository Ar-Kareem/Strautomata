
import time
from collections import deque

N = 11
SIZE = N * N
HALF = N // 2
CENTER_IDX = HALF * N + HALF

EMPTY, SELF, OPPN = 0, 1, 2
INFV = 1000
WIN = 10 ** 6
OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1))
COLOR_OPP = {'b': 'w', 'w': 'b'}

ADJ = []
SRC = {'b': [], 'w': []}
DEST = {'b': [False] * SIZE, 'w': [False] * SIZE}
for r in range(N):
    for c in range(N):
        i = r * N + c
        nb = []
        for dr, dc in OFFSETS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                nb.append(rr * N + cc)
        ADJ.append(nb)
        if r == 0:
            SRC['b'].append(i)
        if c == 0:
            SRC['w'].append(i)
        if r == N - 1:
            DEST['b'][i] = True
        if c == N - 1:
            DEST['w'][i] = True


def two_path_cost(grid, player, color):
    """Best and second-disjoint connection costs (empty cells needed) for
    `player` across its two sides. 0-1 BFS; own=0, empty=1, opponent=blocked."""
    src = SRC[color]
    destm = DEST[color]
    dist = [INFV] * SIZE
    pred = [-1] * SIZE
    dq = deque()
    for i in src:
        g = grid[i]
        if g == player:
            dist[i] = 0
            dq.appendleft(i)
        elif g == EMPTY:
            dist[i] = 1
            dq.append(i)
    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in ADJ[u]:
            g = grid[v]
            if g == player:
                if du < dist[v]:
                    dist[v] = du
                    pred[v] = u
                    dq.appendleft(v)
            elif g == EMPTY:
                nd = du + 1
                if nd < dist[v]:
                    dist[v] = nd
                    pred[v] = u
                    dq.append(v)
    best = INFV
    bi = -1
    for i in range(SIZE):
        if destm[i] and dist[i] < best:
            best = dist[i]
            bi = i
    if best >= INFV:
        return INFV, INFV
    blocked = set()
    u = bi
    while u != -1:
        blocked.add(u)
        u = pred[u]
    dist2 = [INFV] * SIZE
    dq2 = deque()
    for i in src:
        if i in blocked:
            continue
        g = grid[i]
        if g == player:
            dist2[i] = 0
            dq2.appendleft(i)
        elif g == EMPTY:
            dist2[i] = 1
            dq2.append(i)
    while dq2:
        u = dq2.popleft()
        du = dist2[u]
        if destm[u]:
            return best, du
        for v in ADJ[u]:
            if v in blocked:
                continue
            g = grid[v]
            if g == player:
                if du < dist2[v]:
                    dist2[v] = du
                    dq2.appendleft(v)
            elif g == EMPTY:
                nd = du + 1
                if nd < dist2[v]:
                    dist2[v] = nd
                    dq2.append(v)
    return best, INFV


class _Abort(Exception):
    pass


class Solver:
    def __init__(self, grid, mycolor):
        self.grid = grid
        self.mycolor = mycolor
        self.oppcolor = COLOR_OPP[mycolor]
        self.nodes = 0
        self.deadline = 0.0
        self.ply = 0
        self.cap = 12
        self.root_cap = 20
        self.root_hint = None

    def won(self, marker):
        color = self.mycolor if marker == SELF else self.oppcolor
        destm = DEST[color]
        seen = [False] * SIZE
        stack = []
        for i in SRC[color]:
            if self.grid[i] == marker and not seen[i]:
                seen[i] = True
                if destm[i]:
                    return True
                stack.append(i)
        while stack:
            u = stack.pop()
            for v in ADJ[u]:
                if not seen[v] and self.grid[v] == marker:
                    seen[v] = True
                    if destm[v]:
                        return True
                    stack.append(v)
        return False

    def evaluate(self, turn):
        m1, m2 = two_path_cost(self.grid, SELF, self.mycolor)
        if m1 == 0:
            v = WIN
        else:
            o1, o2 = two_path_cost(self.grid, OPPN, self.oppcolor)
            if o1 == 0:
                v = -WIN
            else:
                v = (o1 + o2) - (m1 + m2)
        return v if turn == SELF else -v

    def gen_moves(self, turn, cap):
        grid = self.grid
        cands = set()
        saw_stone = False
        for i in range(SIZE):
            g = grid[i]
            if g != EMPTY:
                saw_stone = True
                for v in ADJ[i]:
                    if grid[v] == EMPTY:
                        cands.add(v)
        if not cands:
            if not saw_stone:
                return [CENTER_IDX]
            cands = [i for i in range(SIZE) if grid[i] == EMPTY]
            if not cands:
                return []
        other = OPPN if turn == SELF else SELF
        scored = []
        h = HALF
        for i in cands:
            s = 0.0
            for v in ADJ[i]:
                g = grid[v]
                if g == turn:
                    s += 3.0
                elif g == other:
                    s += 1.0
                else:
                    s += 0.25
            r = i // N
            c = i % N
            s += (N - abs(r - h) - abs(c - h)) * 0.05
            scored.append((s, i))
        scored.sort(key=lambda t: (t[0], -t[1]), reverse=True)
        if len(scored) > cap:
            scored = scored[:cap]
        return [i for _s, i in scored]

    def search(self, depth, alpha, beta, turn):
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.perf_counter() >= self.deadline:
            raise _Abort()
        if depth == 0:
            return self.evaluate(turn)
        other = OPPN if turn == SELF else SELF
        best = -WIN * 2
        moves = self.gen_moves(turn, self.cap)
        if not moves:
            return self.evaluate(turn)
        for m in moves:
            self.grid[m] = turn
            try:
                if self.won(turn):
                    val = WIN - (self.ply + 1)
                else:
                    self.ply += 1
                    val = -self.search(depth - 1, -beta, -alpha, other)
                    self.ply -= 1
            finally:
                self.grid[m] = EMPTY
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    def root(self, depth):
        moves = self.gen_moves(SELF, self.root_cap)
        if self.root_hint is not None and self.root_hint in moves:
            moves.remove(self.root_hint)
            moves.insert(0, self.root_hint)
        if not moves:
            return 0, None
        best = -WIN * 2
        best_move = moves[0]
        alpha = -WIN * 2
        beta = WIN * 2
        for m in moves:
            self.grid[m] = SELF
            try:
                if self.won(SELF):
                    val = WIN
                else:
                    self.ply += 1
                    val = -self.search(depth - 1, -beta, -alpha, OPPN)
                    self.ply -= 1
            finally:
                self.grid[m] = EMPTY
            if val > best:
                best = val
                best_move = m
            if best > alpha:
                alpha = best
        return best, best_move

    def choose(self, budget=0.88):
        self.deadline = time.perf_counter() + budget
        grid = self.grid
        empties = [i for i in range(SIZE) if grid[i] == EMPTY]
        if not empties:
            return None
        # immediate win for us
        for i in empties:
            grid[i] = SELF
            w = self.won(SELF)
            grid[i] = EMPTY
            if w:
                return i
        # mandatory blocks of opponent immediate wins
        threats = []
        for i in empties:
            grid[i] = OPPN
            w = self.won(OPPN)
            grid[i] = EMPTY
            if w:
                threats.append(i)
        if threats:
            return threats[0]
        best_move = None
        self.root_hint = None
        depth = 1
        while depth <= 30:
            if time.perf_counter() >= self.deadline:
                break
            try:
                _v, bm = self.root(depth)
            except _Abort:
                break
            if bm is not None:
                best_move = bm
                self.root_hint = bm
            depth += 1
        if best_move is None:
            best_move = empties[0]
        return best_move


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    try:
        grid = [EMPTY] * SIZE
        for r, c in me:
            grid[r * N + c] = SELF
        for r, c in opp:
            grid[r * N + c] = OPPN
        if color not in COLOR_OPP:
            color = 'b'
        solver = Solver(grid, color)
        idx = solver.choose(0.88)
        if idx is None:
            raise ValueError("no empty cell")
        return (idx // N, idx % N)
    except Exception:
        occupied = set()
        for r, c in me:
            occupied.add((r, c))
        for r, c in opp:
            occupied.add((r, c))
        for r in range(N):
            for c in range(N):
                if (r, c) not in occupied:
                    return (r, c)
        return (0, 0)
