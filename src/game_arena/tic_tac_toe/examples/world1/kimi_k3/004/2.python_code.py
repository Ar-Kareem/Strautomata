
from functools import lru_cache

# Winning lines over a flattened 9-cell board (row-major).
LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
    (0, 4, 8), (2, 4, 6),              # diagonals
)

# Final tie-break preference: center, then corners, then edges.
PREF = (4, 0, 2, 6, 8, 1, 3, 5, 7)
PREF_RANK = {cell: rank for rank, cell in enumerate(PREF)}


def _winner(b):
    """Return 1 if player 1 won, -1 if player -1 won, 0 for a full-board draw, else None."""
    for a, c, d in LINES:
        s = b[a] + b[c] + b[d]
        if s == 3:
            return 1
        if s == -3:
            return -1
    if 0 not in b:
        return 0
    return None


def _player_to_move(b):
    """Infer whose turn it is from mark counts (legal positions only)."""
    return 1 if b.count(1) == b.count(-1) else -1


@lru_cache(maxsize=None)
def _minimax(b):
    """Exact game-theoretic value of position b from player 1's perspective: 1/0/-1."""
    w = _winner(b)
    if w is not None:
        return w
    p = _player_to_move(b)
    vals = []
    for i in range(9):
        if b[i] == 0:
            child = b[:i] + (p,) + b[i + 1:]
            vals.append(_minimax(child))
    return max(vals) if p == 1 else min(vals)


@lru_cache(maxsize=None)
def _expect(b):
    """
    Expected final score (win=1.0, draw=0.5, loss=0.0) of position b, assuming:
      - Player 1 always chooses among minimax-optimal moves the one maximizing this
        expectation (exactly the real policy's lexicographic behavior).
      - The opponent chooses uniformly at random among legal moves.
    Used only as a tie-breaker among equally-safe moves to maximize blunder chances.
    """
    w = _winner(b)
    if w is not None:
        return 1.0 if w == 1 else (0.5 if w == 0 else 0.0)
    p = _player_to_move(b)
    moves = [i for i in range(9) if b[i] == 0]
    if p == 1:
        best_val = max(_minimax(b[:i] + (1,) + b[i + 1:]) for i in moves)
        best_exp = -1.0
        for i in moves:
            child = b[:i] + (1,) + b[i + 1:]
            if _minimax(child) == best_val:
                e = _expect(child)
                if e > best_exp:
                    best_exp = e
        return best_exp
    else:
        total = 0.0
        for i in moves:
            total += _expect(b[:i] + (-1,) + b[i + 1:])
        return total / len(moves)


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        b = tuple(board[r][c] for r in range(3) for c in range(3))
        moves = [i for i in range(9) if b[i] == 0]
        if not moves:
            return (0, 0)  # No legal move exists; should never happen.

        best_move = moves[0]
        best_key = None
        for i in moves:
            child = b[:i] + (1,) + b[i + 1:]
            # Lexicographic: guaranteed result first, then trap potential, then cell preference.
            key = (_minimax(child), _expect(child), -PREF_RANK[i])
            if best_key is None or key > best_key:
                best_key = key
                best_move = i
        return (best_move // 3, best_move % 3)
    except Exception:
        # Absolute fallback: return the first empty cell to guarantee a legal move.
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)


if __name__ == "__main__":
    # Quick sanity checks.
    empty = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    mv = policy(empty)
    assert empty[mv[0]][mv[1]] == 0
    # Winning move available: take it.
    b1 = [[1, 1, 0], [-1, -1, 0], [0, 0, 0]]
    assert policy(b1) == (0, 2)
    # Opponent threat: must block.
    b2 = [[-1, -1, 0], [1, 0, 0], [0, 0, 1]]
    assert policy(b2) == (0, 2)
    print("All checks passed. Opening move:", policy(empty))
