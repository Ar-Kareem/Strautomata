
from __future__ import annotations

from functools import lru_cache

# Strong tie-breaking order for Tic Tac Toe:
# center first, then corners, then edges.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)

_WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
)


def _winner(state: tuple[int, ...]) -> int:
    """Return 1 if we have won, -1 if opponent has won, else 0."""
    for a, b, c in _WIN_LINES:
        total = state[a] + state[b] + state[c]
        if total == 3:
            return 1
        if total == -3:
            return -1
    return 0


@lru_cache(maxsize=None)
def _minimax(state: tuple[int, ...], turn: int) -> int:
    """
    Return a score from our perspective.
    Positive is good for us, negative is good for opponent.

    Scores include empty-count bonuses:
    - faster wins are better
    - slower losses are less bad
    """
    winner = _winner(state)
    empty_count = state.count(0)

    if winner == 1:
        return 10 + empty_count
    if winner == -1:
        return -10 - empty_count
    if empty_count == 0:
        return 0

    if turn == 1:
        best = -100
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                nxt = list(state)
                nxt[idx] = 1
                score = _minimax(tuple(nxt), -1)
                if score > best:
                    best = score
        return best

    best = 100
    for idx in _MOVE_ORDER:
        if state[idx] == 0:
            nxt = list(state)
            nxt[idx] = -1
            score = _minimax(tuple(nxt), 1)
            if score < best:
                best = score
    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Choose the next move for a 3x3 Tic Tac Toe board.

    board[r][c]:
      0  = empty
      1  = our mark
      -1 = opponent mark
    """
    state = tuple(int(board[r][c]) for r in range(3) for c in range(3))

    legal_moves = [idx for idx in _MOVE_ORDER if state[idx] == 0]

    # This should only occur if the game is already terminal/full.
    # If there is no legal move, no policy can return a truly legal move.
    if not legal_moves:
        return (0, 0)

    best_idx = legal_moves[0]
    best_score = -100

    for idx in legal_moves:
        nxt = list(state)
        nxt[idx] = 1
        score = _minimax(tuple(nxt), -1)

        if score > best_score:
            best_score = score
            best_idx = idx

    return (best_idx // 3, best_idx % 3)
