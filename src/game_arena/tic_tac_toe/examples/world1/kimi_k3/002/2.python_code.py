
"""
Optimal 3x3 Tic-Tac-Toe policy.

Approach: exhaustive minimax over the entire game tree with memoization.
Score prefers faster wins and slower losses; ties are broken by
positional preference (center > corners > edges). Always returns a
legal move.
"""

from __future__ import annotations

from functools import lru_cache

# Winning lines over a flattened 9-cell board (index = row * 3 + col).
_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
)

# Tie-break preference: center, then corners, then edges.
_PREFERENCE = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _winner(flat: tuple) -> int:
    """Return 1 if player 1 has won, -1 if opponent has won, else 0."""
    for a, b, c in _LINES:
        v = flat[a]
        if v != 0 and v == flat[b] == flat[c]:
            return v
    return 0


@lru_cache(maxsize=None)
def _value(flat: tuple, my_turn: bool) -> int:
    """Game-theoretic value of a state from player 1's perspective.

    Positive  => forced win  (larger magnitude = happens sooner).
    Negative  => forced loss (larger magnitude = happens sooner).
    Zero      => draw with best play.
    """
    w = _winner(flat)
    empty_count = flat.count(0)
    if w == 1:
        return empty_count + 1
    if w == -1:
        return -(empty_count + 1)
    if empty_count == 0:
        return 0

    if my_turn:
        best = -100
        for i, v in enumerate(flat):
            if v == 0:
                child = flat[:i] + (1,) + flat[i + 1:]
                best = max(best, _value(child, False))
        return best

    best = 100
    for i, v in enumerate(flat):
        if v == 0:
            child = flat[:i] + (-1,) + flat[i + 1:]
            best = min(best, _value(child, True))
    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """Return the optimal legal move (row, col) for player 1."""
    flat = tuple(cell for row in board for cell in row)

    best_move = None
    best_val = -100

    # Scan empty cells in positional preference order; the strict '>'
    # keeps the most preferred cell among moves of equal value.
    for i in _PREFERENCE:
        if flat[i] != 0:
            continue
        if best_move is None:
            best_move = i  # guaranteed-legal fallback
        val = _value(flat[:i] + (1,) + flat[i + 1:], False)
        if val > best_val:
            best_val = val
            best_move = i

    if best_move is None:
        # Degenerate case: board is full. Should never occur, but we
        # must still return something.
        return (0, 0)

    return (best_move // 3, best_move % 3)
