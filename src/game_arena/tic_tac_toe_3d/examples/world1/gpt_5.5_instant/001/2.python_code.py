
from functools import lru_cache
import time

# Precompute all 49 winning lines in 3x3x3.
LINES = []
DIRS = []
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx == dy == dz == 0:
                continue
            # Keep only one orientation for each undirected direction.
            if (dx, dy, dz) > (0, 0, 0):
                DIRS.append((dx, dy, dz))

for x in range(3):
    for y in range(3):
        for z in range(3):
            for dx, dy, dz in DIRS:
                x2, y2, z2 = x + 2 * dx, y + 2 * dy, z + 2 * dz
                if 0 <= x2 < 3 and 0 <= y2 < 3 and 0 <= z2 < 3:
                    LINES.append(((x, y, z), (x + dx, y + dy, z + dz), (x2, y2, z2)))

# Remove duplicates defensively.
_tmp = []
_seen = set()
for line in LINES:
    key = tuple(sorted(line))
    if key not in _seen:
        _seen.add(key)
        _tmp.append(line)
LINES = _tmp

CELLS = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]

CELL_LINES = {c: [] for c in CELLS}
for idx, line in enumerate(LINES):
    for c in line:
        CELL_LINES[c].append(idx)

# Static positional value: number of winning lines through the cell, plus center bonus.
POS_VALUE = {}
for c in CELLS:
    v = len(CELL_LINES[c]) * 8
    if c == (1, 1, 1):
        v += 30
    elif sum(1 for t in c if t == 1) == 2:
        v += 6
    elif sum(1 for t in c if t == 1) == 1:
        v += 3
    POS_VALUE[c] = v

ORDERED_CELLS = sorted(CELLS, key=lambda c: POS_VALUE[c], reverse=True)


def _flat(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))


def _idx(c):
    return c[0] * 9 + c[1] * 3 + c[2]


def _cell(index):
    return (index // 9, (index // 3) % 3, index % 3)


LINE_IDXS = [tuple(_idx(c) for c in line) for line in LINES]
ORDERED_IDXS = [_idx(c) for c in ORDERED_CELLS]


def _winner(state):
    for a, b, c in LINE_IDXS:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empties(state):
    return [i for i, v in enumerate(state) if v == 0]


def _winning_moves(state, player):
    out = []
    for a, b, c in LINE_IDXS:
        vals = (state[a], state[b], state[c])
        if vals.count(player) == 2 and vals.count(0) == 1:
            if state[a] == 0:
                out.append(a)
            elif state[b] == 0:
                out.append(b)
            else:
                out.append(c)
    # unique, preserving order
    seen = set()
    res = []
    for m in out:
        if m not in seen:
            seen.add(m)
            res.append(m)
    return res


def _heuristic(state):
    win = _winner(state)
    if win:
        return win * 1000000

    score = 0

    # Line patterns.
    for a, b, c in LINE_IDXS:
        vals = (state[a], state[b], state[c])
        my = vals.count(1)
        op = vals.count(-1)
        if my and op:
            continue
        if my == 2:
            score += 900
        elif my == 1:
            score += 45
        elif op == 2:
            score -= 1050
        elif op == 1:
            score -= 50

    # Positional value.
    for i, v in enumerate(state):
        if v == 1:
            score += POS_VALUE[_cell(i)]
        elif v == -1:
            score -= POS_VALUE[_cell(i)]

    # Fork/threat count bonus.
    my_threats = len(_winning_moves(state, 1))
    op_threats = len(_winning_moves(state, -1))
    if my_threats >= 2:
        score += 2500 + 500 * my_threats
    if op_threats >= 2:
        score -= 3000 + 600 * op_threats
    score += 220 * my_threats
    score -= 260 * op_threats

    return score


def _move_order(state, player):
    empt = [i for i in ORDERED_IDXS if state[i] == 0]

    mywins = set(_winning_moves(state, player))
    blocks = set(_winning_moves(state, -player))

    def key(m):
        c = _cell(m)
        s = POS_VALUE[c]
        if m in mywins:
            s += 100000
        if m in blocks:
            s += 80000

        # Prefer moves that create multiple immediate threats.
        lst = list(state)
        lst[m] = player
        s += 300 * len(_winning_moves(tuple(lst), player))
        s -= 100 * len(_winning_moves(tuple(lst), -player))
        return s

    return sorted(empt, key=key, reverse=True)


@lru_cache(maxsize=200000)
def _negamax(state, player, depth, alpha, beta):
    w = _winner(state)
    if w:
        return (1000000 + depth) if w == player else (-1000000 - depth)

    if depth <= 0 or all(v != 0 for v in state):
        return player * _heuristic(state)

    # Tactical shortcuts.
    wins = _winning_moves(state, player)
    if wins:
        return 900000 + depth

    oppwins = _winning_moves(state, -player)
    # If opponent has two or more independent wins, usually losing unless we can win now.
    if len(oppwins) >= 2:
        return -850000 - depth

    best = -10**9
    for m in _move_order(state, player):
        ns = list(state)
        ns[m] = player
        val = -_negamax(tuple(ns), -player, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start = time.time()
    state = _flat(board)

    legal = [i for i, v in enumerate(state) if v == 0]
    if not legal:
        return (0, 0, 0)  # Should not occur in normal play.

    # 1. Win immediately.
    wins = _winning_moves(state, 1)
    if wins:
        return _cell(wins[0])

    # 2. Block immediate opponent win.
    blocks = _winning_moves(state, -1)
    if blocks:
        # If multiple blocks exist, choose the most valuable blocking square.
        b = max(blocks, key=lambda m: POS_VALUE[_cell(m)])
        return _cell(b)

    # 3. Opening preference: center is strongest in 3D.
    if state[_idx((1, 1, 1))] == 0:
        return (1, 1, 1)

    n_empty = len(legal)

    # Adaptive depth fits easily under 1 second for 27 cells with alpha-beta and cache.
    if n_empty >= 22:
        max_depth = 3
    elif n_empty >= 16:
        max_depth = 4
    elif n_empty >= 10:
        max_depth = 5
    else:
        max_depth = 8

    best_move = None
    best_val = -10**9

    # Iterative deepening gives a robust answer if time is tight.
    ordered = _move_order(state, 1)
    for depth in range(1, max_depth + 1):
        if time.time() - start > 0.85:
            break
        cur_best = best_move
        cur_val = -10**9

        for m in ordered:
            if time.time() - start > 0.92:
                break
            ns = list(state)
            ns[m] = 1
            val = -_negamax(tuple(ns), -1, depth - 1, -10**9, 10**9)

            # Small tie-breaker toward positional value.
            val += POS_VALUE[_cell(m)] * 0.01

            if val > cur_val:
                cur_val = val
                cur_best = m

        if cur_best is not None:
            best_move = cur_best
            best_val = cur_val

    if best_move is not None and state[best_move] == 0:
        return _cell(best_move)

    # 4. Absolute safe fallback: best legal positional move.
    fallback = max(legal, key=lambda m: POS_VALUE[_cell(m)])
    return _cell(fallback)
