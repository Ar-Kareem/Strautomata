
from functools import lru_cache

LINES = [
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
]


def winner(b):
    for (r1, c1), (r2, c2), (r3, c3) in LINES:
        s = b[r1][c1] + b[r2][c2] + b[r3][c3]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def empties(b):
    return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]


def place(b, r, c, p):
    rows = [list(row) for row in b]
    rows[r][c] = p
    return tuple(tuple(row) for row in rows)


@lru_cache(maxsize=None)
def value(b, player):
    """Minimax value from my (player 1) perspective. Faster wins are better,
    slower losses are better."""
    w = winner(b)
    if w != 0:
        n_empty = len(empties(b))
        return w * (10 + n_empty)
    moves = empties(b)
    if not moves:
        return 0
    if player == 1:
        best = -100
        for r, c in moves:
            v = value(place(b, r, c, 1), -1)
            if v > best:
                best = v
        return best
    else:
        best = 100
        for r, c in moves:
            v = value(place(b, r, c, -1), 1)
            if v < best:
                best = v
        return best


def trap_score(b):
    """Given it's the opponent's turn on board b, count how many of their
    replies hand me a forced win. More traps = better for us."""
    moves = empties(b)
    if not moves:
        return 0
    traps = 0
    for r, c in moves:
        nb = place(b, r, c, -1)
        if winner(nb) == -1:
            continue
        if value(nb, 1) > 0:
            traps += 1
    return traps


POSITION_PREF = {
    (1, 1): 3,
    (0, 0): 2, (0, 2): 2, (2, 0): 2, (2, 2): 2,
    (0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1,
}


def policy(board):
    try:
        b = tuple(tuple(int(board[r][c]) for c in range(3)) for r in range(3))
    except Exception:
        b = tuple(tuple(0 for _ in range(3)) for _ in range(3))

    moves = empties(b)
    if not moves:
        return (0, 0)

    # If the game is somehow already over, just return any legal move.
    if winner(b) != 0:
        return moves[0]

    # Immediate win check (fast path).
    for r, c in moves:
        if winner(place(b, r, c, 1)) == 1:
            return (r, c)

    best_move = moves[0]
    best_key = None
    for r, c in moves:
        nb = place(b, r, c, 1)
        v = value(nb, -1)
        t = trap_score(nb)
        key = (v, t, POSITION_PREF.get((r, c), 0))
        if best_key is None or key > best_key:
            best_key = key
            best_move = (r, c)

    r, c = best_move
    if b[r][c] != 0:
        return moves[0]
    return (int(r), int(c))
