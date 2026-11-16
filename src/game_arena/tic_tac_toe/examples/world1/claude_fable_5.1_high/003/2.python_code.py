
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

POSITION_PREF = {
    (1, 1): 3,
    (0, 0): 2, (0, 2): 2, (2, 0): 2, (2, 2): 2,
    (0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1,
}


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


def to_tuple(b):
    return tuple(tuple(int(x) for x in row) for row in b)


def place(bt, r, c, player):
    rows = [list(row) for row in bt]
    rows[r][c] = player
    return tuple(tuple(row) for row in rows)


@lru_cache(maxsize=None)
def minimax(bt, player):
    """Return value from the perspective of 'us' (player 1).
    Positive = we win (larger = faster), negative = we lose (smaller = faster)."""
    w = winner(bt)
    if w != 0:
        depth_bonus = sum(1 for r in range(3) for c in range(3) if bt[r][c] == 0)
        return w * (10 + depth_bonus)
    moves = empties(bt)
    if not moves:
        return 0
    if player == 1:
        best = -1000
        for r, c in moves:
            v = minimax(place(bt, r, c, 1), -1)
            if v > best:
                best = v
        return best
    else:
        best = 1000
        for r, c in moves:
            v = minimax(place(bt, r, c, -1), 1)
            if v < best:
                best = v
        return best


def trap_count(bt):
    """Number of opponent replies (from position bt, opponent to move) that lead to a forced win for us."""
    count = 0
    for r, c in empties(bt):
        nb = place(bt, r, c, -1)
        if minimax(nb, 1) > 0:
            count += 1
    return count


def policy(board):
    try:
        bt = to_tuple(board)
        moves = empties(bt)
        if not moves:
            return (0, 0)

        # Immediate win
        for r, c in moves:
            if winner(place(bt, r, c, 1)) == 1:
                return (r, c)

        # Evaluate all moves with minimax
        scored = []
        for r, c in moves:
            nb = place(bt, r, c, 1)
            v = minimax(nb, -1)
            scored.append((v, (r, c), nb))

        best_val = max(s[0] for s in scored)
        candidates = [s for s in scored if s[0] == best_val]

        if len(candidates) == 1:
            return candidates[0][1]

        # Tie-break: maximize traps for opponent, then positional preference
        best_move = None
        best_key = None
        for v, mv, nb in candidates:
            key = (trap_count(nb), POSITION_PREF.get(mv, 0))
            if best_key is None or key > best_key:
                best_key = key
                best_move = mv
        return best_move
    except Exception:
        # Safety fallback: always return a legal move
        for r in range(3):
            for c in range(3):
                try:
                    if board[r][c] == 0:
                        return (r, c)
                except Exception:
                    pass
        return (0, 0)
