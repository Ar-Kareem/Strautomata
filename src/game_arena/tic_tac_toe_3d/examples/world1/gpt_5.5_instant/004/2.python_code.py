
# 3x3x3 Tic Tac Toe policy
# Player: 1, Opponent: -1

from functools import lru_cache
import math

N = 3

def _generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(N):
        for k in range(N):
            lines.append(tuple((i, j, k) for i in range(N)))
    for i in range(N):
        for k in range(N):
            lines.append(tuple((i, j, k) for j in range(N)))
    for i in range(N):
        for j in range(N):
            lines.append(tuple((i, j, k) for k in range(N)))

    # Plane diagonals in ij planes for each k
    for k in range(N):
        lines.append(tuple((t, t, k) for t in range(N)))
        lines.append(tuple((t, N - 1 - t, k) for t in range(N)))

    # Plane diagonals in ik planes for each j
    for j in range(N):
        lines.append(tuple((t, j, t) for t in range(N)))
        lines.append(tuple((t, j, N - 1 - t) for t in range(N)))

    # Plane diagonals in jk planes for each i
    for i in range(N):
        lines.append(tuple((i, t, t) for t in range(N)))
        lines.append(tuple((i, t, N - 1 - t) for t in range(N)))

    # Space diagonals
    lines.append(tuple((t, t, t) for t in range(N)))
    lines.append(tuple((t, t, N - 1 - t) for t in range(N)))
    lines.append(tuple((t, N - 1 - t, t) for t in range(N)))
    lines.append(tuple((t, N - 1 - t, N - 1 - t) for t in range(N)))

    # Remove duplicates defensively
    seen = set()
    unique = []
    for line in lines:
        s = tuple(sorted(line))
        if s not in seen:
            seen.add(s)
            unique.append(line)
    return tuple(unique)

LINES = _generate_lines()

CELL_LINES = {(i, j, k): [] for i in range(N) for j in range(N) for k in range(N)}
for line in LINES:
    for cell in line:
        CELL_LINES[cell].append(line)

LINE_COUNT = {cell: len(CELL_LINES[cell]) for cell in CELL_LINES}

PREFERRED_CELLS = sorted(
    [(i, j, k) for i in range(N) for j in range(N) for k in range(N)],
    key=lambda c: (
        -LINE_COUNT[c],
        abs(c[0] - 1) + abs(c[1] - 1) + abs(c[2] - 1),
        c
    )
)

def _flatten(board):
    return tuple(board[i][j][k] for i in range(N) for j in range(N) for k in range(N))

def _idx(cell):
    i, j, k = cell
    return i * 9 + j * 3 + k

LINES_IDX = tuple(tuple(_idx(c) for c in line) for line in LINES)
PREFERRED_IDX = tuple(_idx(c) for c in PREFERRED_CELLS)

def _winner_flat(b):
    for line in LINES_IDX:
        s = b[line[0]] + b[line[1]] + b[line[2]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _empty_indices(b):
    return [i for i, v in enumerate(b) if v == 0]

def _to_cell(index):
    return (index // 9, (index % 9) // 3, index % 3)

def _first_empty(board):
    for i in range(N):
        for j in range(N):
            for k in range(N):
                if board[i][j][k] == 0:
                    return (i, j, k)
    return (0, 0, 0)

def _line_score(my_count, opp_count):
    if my_count and opp_count:
        return 0
    if my_count == 3:
        return 100000
    if opp_count == 3:
        return -100000
    if my_count == 2:
        return 800
    if opp_count == 2:
        return -950
    if my_count == 1:
        return 12
    if opp_count == 1:
        return -14
    return 1

def _heuristic(b):
    w = _winner_flat(b)
    if w == 1:
        return 1000000
    if w == -1:
        return -1000000

    score = 0

    # Positional bonus
    for idx, v in enumerate(b):
        if v:
            cell = _to_cell(idx)
            val = 4 * LINE_COUNT[cell]
            if cell == (1, 1, 1):
                val += 12
            elif 1 in cell:
                val += 2
            score += val if v == 1 else -val

    # Line potential
    my_twos = 0
    opp_twos = 0
    for line in LINES_IDX:
        vals = (b[line[0]], b[line[1]], b[line[2]])
        my = vals.count(1)
        opp = vals.count(-1)
        score += _line_score(my, opp)
        if my == 2 and opp == 0:
            my_twos += 1
        elif opp == 2 and my == 0:
            opp_twos += 1

    # Fork encouragement/prevention
    if my_twos >= 2:
        score += 1500 * (my_twos - 1)
    if opp_twos >= 2:
        score -= 1800 * (opp_twos - 1)

    return score

def _find_immediate(b, player):
    for idx0 in PREFERRED_IDX:
        if b[idx0] != 0:
            continue
        bb = list(b)
        bb[idx0] = player
        if _winner_flat(tuple(bb)) == player:
            return idx0
    return None

def _creates_threats(b, idx0, player):
    bb = list(b)
    bb[idx0] = player
    bb = tuple(bb)
    threats = 0
    for line in LINES_IDX:
        vals = (bb[line[0]], bb[line[1]], bb[line[2]])
        if vals.count(player) == 2 and vals.count(0) == 1:
            threats += 1
    return threats

def _ordered_moves(b, player):
    moves = [idx for idx in PREFERRED_IDX if b[idx] == 0]

    def key(idx0):
        bb = list(b)
        bb[idx0] = player
        tb = tuple(bb)
        if _winner_flat(tb) == player:
            return 10**9

        # Higher is better for side to move
        threats = _creates_threats(b, idx0, player)
        opp_threats_before = _creates_threats(b, idx0, -player)

        cell = _to_cell(idx0)
        positional = 10 * LINE_COUNT[cell]
        if cell == (1, 1, 1):
            positional += 30

        h = _heuristic(tb)
        return (h if player == 1 else -h) + 400 * threats - 80 * opp_threats_before + positional

    moves.sort(key=key, reverse=True)
    return moves

@lru_cache(maxsize=200000)
def _minimax(b, player, depth, alpha, beta):
    w = _winner_flat(b)
    if w == 1:
        return 1000000 + depth
    if w == -1:
        return -1000000 - depth

    empties = b.count(0)
    if empties == 0:
        return 0
    if depth <= 0:
        return _heuristic(b)

    # Tactical extensions: always examine immediate wins/blocks
    win = _find_immediate(b, player)
    if win is not None:
        return (1000000 + depth) if player == 1 else (-1000000 - depth)

    if player == 1:
        best = -10**9
        for m in _ordered_moves(b, player):
            bb = list(b)
            bb[m] = player
            val = _minimax(tuple(bb), -player, depth - 1, alpha, beta)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = 10**9
        for m in _ordered_moves(b, player):
            bb = list(b)
            bb[m] = player
            val = _minimax(tuple(bb), -player, depth - 1, alpha, beta)
            if val < best:
                best = val
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def _choose_by_search(b):
    empties = b.count(0)

    # Search deeper as the board fills. Branching is small in late game.
    if empties <= 8:
        depth = empties
    elif empties <= 13:
        depth = 5
    elif empties <= 18:
        depth = 4
    else:
        depth = 3

    best_move = None
    best_val = -10**10

    for m in _ordered_moves(b, 1):
        bb = list(b)
        bb[m] = 1
        val = _minimax(tuple(bb), -1, depth - 1, -10**9, 10**9)

        # Slight tie-break toward robust positional cells
        val += 0.001 * LINE_COUNT[_to_cell(m)]

        if val > best_val:
            best_val = val
            best_move = m

    return best_move

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Return a legal move (i, j, k) for 3x3x3 Tic Tac Toe.
    """
    try:
        b = _flatten(board)

        # If malformed or full, fall back safely.
        if len(b) != 27 or all(v != 0 for v in b):
            return _first_empty(board)

        # 1. Win immediately if possible.
        m = _find_immediate(b, 1)
        if m is not None:
            return _to_cell(m)

        # 2. Block opponent's immediate win.
        m = _find_immediate(b, -1)
        if m is not None:
            return _to_cell(m)

        # 3. Prefer center as opening if available.
        center = _idx((1, 1, 1))
        if b.count(0) >= 26 and b[center] == 0:
            return (1, 1, 1)

        # 4. Create unavoidable fork if available.
        fork_moves = []
        for idx0 in PREFERRED_IDX:
            if b[idx0] == 0:
                th = _creates_threats(b, idx0, 1)
                if th >= 2:
                    fork_moves.append((th, LINE_COUNT[_to_cell(idx0)], idx0))
        if fork_moves:
            fork_moves.sort(reverse=True)
            return _to_cell(fork_moves[0][2])

        # 5. Prevent opponent fork when urgent.
        opp_forks = []
        for idx0 in PREFERRED_IDX:
            if b[idx0] == 0:
                th = _creates_threats(b, idx0, -1)
                if th >= 2:
                    opp_forks.append((th, LINE_COUNT[_to_cell(idx0)], idx0))
        if len(opp_forks) == 1:
            return _to_cell(opp_forks[0][2])
        elif len(opp_forks) > 1:
            # Choose a move that best reduces opponent fork potential, via search/heuristic.
            m = _choose_by_search(b)
            if m is not None and b[m] == 0:
                return _to_cell(m)

        # 6. Alpha-beta search.
        m = _choose_by_search(b)
        if m is not None and b[m] == 0:
            return _to_cell(m)

        # 7. Heuristic fallback.
        best = None
        best_score = -10**18
        for idx0 in PREFERRED_IDX:
            if b[idx0] == 0:
                bb = list(b)
                bb[idx0] = 1
                score = _heuristic(tuple(bb))
                if score > best_score:
                    best_score = score
                    best = idx0
        if best is not None:
            return _to_cell(best)

        return _first_empty(board)

    except Exception:
        # Absolute safety: never fail to return a legal-looking move if possible.
        return _first_empty(board)
