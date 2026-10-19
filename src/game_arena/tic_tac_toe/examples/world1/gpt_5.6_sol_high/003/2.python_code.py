
from functools import lru_cache
from typing import List, Tuple


# Preferred order for equally optimal moves:
# center, corners, then edges.
_MOVE_ORDER = (
    (1, 1),
    (0, 0),
    (0, 2),
    (2, 0),
    (2, 2),
    (0, 1),
    (1, 0),
    (1, 2),
    (2, 1),
)

_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def _winner(state: Tuple[int, ...]) -> int:
    """Return 1 or -1 for a winner, or 0 if there is no winner."""
    for a, b, c in _LINES:
        value = state[a]
        if value != 0 and value == state[b] == state[c]:
            return value
    return 0


@lru_cache(maxsize=None)
def _minimax(state: Tuple[int, ...], turn: int) -> int:
    """
    Return the optimal score from this state.

    Positive scores favor us (1), negative scores favor the opponent (-1).
    Remaining empty cells reward quicker wins and delayed losses.
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
        best_score = -100
        for row, col in _MOVE_ORDER:
            index = row * 3 + col
            if state[index] == 0:
                next_state = list(state)
                next_state[index] = 1
                score = _minimax(tuple(next_state), -1)
                if score > best_score:
                    best_score = score
        return best_score

    best_score = 100
    for row, col in _MOVE_ORDER:
        index = row * 3 + col
        if state[index] == 0:
            next_state = list(state)
            next_state[index] = -1
            score = _minimax(tuple(next_state), 1)
            if score < best_score:
                best_score = score
    return best_score


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """Choose an optimal legal move for player 1."""
    state = tuple(board[row][col] for row in range(3) for col in range(3))

    best_move = None
    best_score = -100

    for row, col in _MOVE_ORDER:
        index = row * 3 + col
        if state[index] == 0:
            next_state = list(state)
            next_state[index] = 1
            score = _minimax(tuple(next_state), -1)

            if best_move is None or score > best_score:
                best_score = score
                best_move = (row, col)

    if best_move is None:
        raise ValueError("No legal moves are available")

    return best_move
