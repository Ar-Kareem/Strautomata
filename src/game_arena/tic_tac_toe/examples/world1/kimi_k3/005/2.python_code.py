
import random
from functools import lru_cache

_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
)


def _winner(flat):
    """Return 1 if we won, -1 if the opponent won, else 0."""
    for a, b, c in _LINES:
        v = flat[a]
        if v and v == flat[b] == flat[c]:
            return v
    return 0


def _empty_cells(flat):
    return [i for i, v in enumerate(flat) if v == 0]


def _with_move(flat, idx, mark):
    return flat[:idx] + (mark,) + flat[idx + 1:]


@lru_cache(maxsize=None)
def _minimax(flat, turn):
    """Exact game-theoretic value from our (player 1) perspective.

    Win  -> 10 - depth  (prefer faster wins)
    Loss -> depth - 10  (prefer slower losses)
    Draw -> 0
    """
    w = _winner(flat)
    if w:
        depth = sum(1 for v in flat if v)
        return (10 - depth) if w == 1 else (depth - 10)
    cells = _empty_cells(flat)
    if not cells:
        return 0
    if turn == 1:
        return max(_minimax(_with_move(flat, i, 1), -1) for i in cells)
    return min(_minimax(_with_move(flat, i, -1), 1) for i in cells)


@lru_cache(maxsize=None)
def _expected_vs_random(flat, turn):
    """Expected result (win=1, draw=0, loss=-1) assuming the opponent moves
    uniformly at random while we keep playing minimax-optimal moves that
    maximize this expectation. Used only to rank equally-optimal moves."""
    w = _winner(flat)
    if w:
        return 1.0 if w == 1 else -1.0
    cells = _empty_cells(flat)
    if not cells:
        return 0.0
    if turn == 1:
        target = _minimax(flat, 1)
        return max(
            _expected_vs_random(_with_move(flat, i, 1), -1)
            for i in cells
            if _minimax(_with_move(flat, i, 1), -1) == target
        )
    return sum(
        _expected_vs_random(_with_move(flat, i, -1), 1) for i in cells
    ) / len(cells)


def policy(board):
    flat = tuple(board[r][c] for r in range(3) for c in range(3))
    cells = _empty_cells(flat)
    if not cells:
        return (0, 0)  # full board: no legal move exists; should never happen

    # 1) Keep only moves that preserve the perfect minimax result.
    target = _minimax(flat, 1)

    # 2) Among those, maximize the trap value against a random opponent.
    best_moves = []
    best_score = -2.0
    for i in cells:
        child = _with_move(flat, i, 1)
        if _minimax(child, -1) != target:
            continue  # this move would surrender the guaranteed result
        score = _expected_vs_random(child, -1)
        if score > best_score + 1e-9:
            best_score = score
            best_moves = [i]
        elif score >= best_score - 1e-9:
            best_moves.append(i)

    # 3) Random tie-break for unpredictability; always a legal empty cell.
    choice = random.choice(best_moves)
    return (choice // 3, choice % 3)
