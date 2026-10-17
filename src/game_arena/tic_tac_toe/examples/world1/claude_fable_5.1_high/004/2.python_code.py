
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

# Positional preference for final tie-breaking (center, corners, edges)
POS_PREF = {
    (1, 1): 3,
    (0, 0): 2, (0, 2): 2, (2, 0): 2, (2, 2): 2,
    (0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1,
}


def winner(b):
    """Return 1, -1 if that player has three in a row, else 0."""
    for (a, bb, c) in LINES:
        v = b[a[0] * 3 + a[1]]
        if v != 0 and v == b[bb[0] * 3 + bb[1]] == b[c[0] * 3 + c[1]]:
            return v
    return 0


def empties(b):
    return [i for i in range(9) if b[i] == 0]


@lru_cache(maxsize=None)
def value(b, player):
    """
    Minimax value from the perspective of player 1 (me).
    b: tuple of 9 ints. player: whose turn it is (1 or -1).
    Positive = good for me. Larger magnitude = faster win / slower loss.
    """
    w = winner(b)
    if w != 0:
        # Remaining empties encodes speed: more empties -> faster result
        return w * (10 + b.count(0))
    moves = empties(b)
    if not moves:
        return 0
    if player == 1:
        best = -100
        for m in moves:
            nb = b[:m] + (1,) + b[m + 1:]
            v = value(nb, -1)
            if v > best:
                best = v
                if best >= 10 + b.count(0) - 1:
                    break
        return best
    else:
        best = 100
        for m in moves:
            nb = b[:m] + (-1,) + b[m + 1:]
            v = value(nb, 1)
            if v < best:
                best = v
                if best <= -(10 + b.count(0) - 1):
                    break
        return best


def trap_score(b):
    """
    Given a position where the opponent is to move, count how many of their
    replies lead to a forced win for me (blunder opportunities), and how many
    lead to an immediate loss for me (should be zero if we're safe).
    Higher is better.
    """
    moves = empties(b)
    if not moves or winner(b) != 0:
        return 0
    good = 0
    for m in moves:
        nb = b[:m] + (-1,) + b[m + 1:]
        v = value(nb, 1)
        if v > 0:
            good += 1
    return good


def policy(board):
    # Flatten board
    try:
        b = tuple(int(board[r][c]) for r in range(3) for c in range(3))
    except Exception:
        b = tuple([0] * 9)

    legal = empties(b)
    if not legal:
        # No legal move exists; return something (game should be over)
        return (0, 0)

    # Immediate win check (fast path)
    for m in legal:
        nb = b[:m] + (1,) + b[m + 1:]
        if winner(nb) == 1:
            return (m // 3, m % 3)

    # Immediate block check is handled by minimax, but keep fast path
    threats = []
    for m in legal:
        nb = b[:m] + (-1,) + b[m + 1:]
        if winner(nb) == -1:
            threats.append(m)
    if len(threats) == 1:
        m = threats[0]
        return (m // 3, m % 3)

    best_move = None
    best_key = None
    for m in legal:
        nb = b[:m] + (1,) + b[m + 1:]
        v = value(nb, -1)
        t = trap_score(nb)
        pos = POS_PREF.get((m // 3, m % 3), 0)
        key = (v, t, pos)
        if best_key is None or key > best_key:
            best_key = key
            best_move = m

    if best_move is None or b[best_move] != 0:
        best_move = legal[0]

    return (best_move // 3, best_move % 3)
