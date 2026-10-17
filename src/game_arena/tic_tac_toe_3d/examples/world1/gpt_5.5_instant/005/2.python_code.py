
from functools import lru_cache

N = 3
CELLS = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]
IDX = {(i, j, k): i * 9 + j * 3 + k for i, j, k in CELLS}
POS = {v: k for k, v in IDX.items()}

def _generate_lines():
    dirs = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dy, dz) != (0, 0, 0):
                    # keep only one direction from each opposite pair
                    if (dx, dy, dz) > (0, 0, 0):
                        dirs.append((dx, dy, dz))

    lines = set()
    for x in range(3):
        for y in range(3):
            for z in range(3):
                for dx, dy, dz in dirs:
                    x2, y2, z2 = x + 2 * dx, y + 2 * dy, z + 2 * dz
                    if 0 <= x2 < 3 and 0 <= y2 < 3 and 0 <= z2 < 3:
                        line = tuple(sorted([
                            IDX[(x, y, z)],
                            IDX[(x + dx, y + dy, z + dz)],
                            IDX[(x2, y2, z2)]
                        ]))
                        lines.add(line)
    return tuple(sorted(lines))

LINES = _generate_lines()

CELL_LINES = [[] for _ in range(27)]
for line in LINES:
    for p in line:
        CELL_LINES[p].append(line)

LINE_COUNT = [len(CELL_LINES[p]) for p in range(27)]

# Good static ordering: center, high-line-count cells, then geometric closeness to center.
ORDER = sorted(
    range(27),
    key=lambda p: (
        p != IDX[(1, 1, 1)],
        -LINE_COUNT[p],
        abs(POS[p][0] - 1) + abs(POS[p][1] - 1) + abs(POS[p][2] - 1),
        p
    )
)

def _tuple_board(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))

def _winner(state):
    for a, b, c in LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _find_immediate(state, player):
    target = 2 * player
    for a, b, c in LINES:
        vals = state[a] + state[b] + state[c]
        if vals == target:
            if state[a] == 0:
                return a
            if state[b] == 0:
                return b
            if state[c] == 0:
                return c
    return None

def _heuristic(state):
    score = 0

    # Line-based evaluation.
    # Open two-in-a-row is very valuable; blocked lines have no value.
    for line in LINES:
        vals = [state[p] for p in line]
        mine = vals.count(1)
        opp = vals.count(-1)
        if mine and opp:
            continue
        if mine == 2:
            score += 120
        elif mine == 1:
            score += 8
        elif opp == 2:
            score -= 140
        elif opp == 1:
            score -= 9

    # Square quality bonus.
    for p, v in enumerate(state):
        if v == 1:
            score += LINE_COUNT[p] * 2
        elif v == -1:
            score -= LINE_COUNT[p] * 2

    return score

def _move_order(state, player):
    moves = [p for p in ORDER if state[p] == 0]

    def key(p):
        # Prefer immediate tactical/forcing moves and high-connectivity cells.
        st = list(state)
        st[p] = player
        st = tuple(st)

        val = LINE_COUNT[p] * 10
        if _winner(st) == player:
            val += 100000

        # Creating multiple threats is strong.
        threats = 0
        for line in CELL_LINES[p]:
            s = sum(st[x] for x in line)
            if s == 2 * player:
                threats += 1
            elif s == -2 * player:
                val += 100  # block opponent threat
        val += threats * 500
        return -val

    return sorted(moves, key=key)

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    state = _tuple_board(board)
    empties = [p for p in range(27) if state[p] == 0]

    # Absolute safety fallback.
    if not empties:
        return (0, 0, 0)

    # Opening: center is strongest in 3D tic-tac-toe.
    center = IDX[(1, 1, 1)]
    if state[center] == 0:
        return (1, 1, 1)

    # Win immediately.
    win = _find_immediate(state, 1)
    if win is not None:
        return POS[win]

    # Block immediate opponent win.
    block = _find_immediate(state, -1)
    if block is not None:
        return POS[block]

    remaining = len(empties)

    # Search depth chosen to remain fast under 1 second.
    # Endgames are solved exactly.
    if remaining <= 10:
        depth = remaining
    elif remaining <= 16:
        depth = 7
    else:
        depth = 5

    @lru_cache(None)
    def negamax(state, player, depth, alpha, beta):
        w = _winner(state)
        if w != 0:
            # From current player's perspective.
            return (100000 + depth) if w == player else (-100000 - depth)

        empty_count = state.count(0)
        if empty_count == 0:
            return 0

        if depth == 0:
            return _heuristic(state) * player

        # Tactical shortcuts inside search.
        immediate = _find_immediate(state, player)
        if immediate is not None:
            return 90000 + depth

        opp_immediate = _find_immediate(state, -player)
        moves = _move_order(state, player)

        # If opponent has an immediate win, strongly prioritize/legalize the block.
        if opp_immediate is not None and opp_immediate in moves:
            moves.remove(opp_immediate)
            moves.insert(0, opp_immediate)

        best = -10**9
        for p in moves:
            lst = list(state)
            lst[p] = player
            child = tuple(lst)
            val = -negamax(child, -player, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    best_move = None
    best_score = -10**18

    for p in _move_order(state, 1):
        lst = list(state)
        lst[p] = 1
        child = tuple(lst)

        if _winner(child) == 1:
            return POS[p]

        score = -negamax(child, -1, depth - 1, -10**9, 10**9)

        # Add small deterministic positional tie-break.
        score += LINE_COUNT[p] * 0.01
        if p == center:
            score += 0.1

        if score > best_score:
            best_score = score
            best_move = p

    if best_move is None or state[best_move] != 0:
        best_move = empties[0]

    return POS[best_move]
