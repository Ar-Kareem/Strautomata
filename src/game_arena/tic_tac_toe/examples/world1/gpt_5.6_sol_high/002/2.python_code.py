
from functools import lru_cache


# Preferred order for equally optimal moves: center, corners, then edges.
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


def _winner(state: tuple[int, ...]) -> int:
    """Return 1 or -1 if that player has won, otherwise return 0."""
    for a, b, c in _LINES:
        value = state[a]
        if value != 0 and value == state[b] and value == state[c]:
            return value
    return 0


def policy(board: list[list[int]]) -> tuple[int, int]:
    """Return an optimal legal move for player 1."""
    initial = tuple(board[row][col] for row in range(3) for col in range(3))

    legal_moves = [
        (row, col) for row, col in _MOVE_ORDER
        if initial[row * 3 + col] == 0
    ]

    # A legal next-move position necessarily has an empty cell.
    # This fallback preserves the required return type for malformed full boards.
    if not legal_moves:
        return (0, 0)

    @lru_cache(maxsize=None)
    def minimax(state: tuple[int, ...], turn: int, depth: int) -> int:
        winner = _winner(state)

        if winner == 1:
            return 100 - depth
        if winner == -1:
            return depth - 100
        if 0 not in state:
            return 0

        if turn == 1:
            best_score = -1000

            for row, col in _MOVE_ORDER:
                index = row * 3 + col
                if state[index] == 0:
                    next_state = list(state)
                    next_state[index] = 1
                    score = minimax(tuple(next_state), -1, depth + 1)
                    if score > best_score:
                        best_score = score

            return best_score

        best_score = 1000

        for row, col in _MOVE_ORDER:
            index = row * 3 + col
            if state[index] == 0:
                next_state = list(state)
                next_state[index] = -1
                score = minimax(tuple(next_state), 1, depth + 1)
                if score < best_score:
                    best_score = score

        return best_score

    best_move = legal_moves[0]
    best_score = -1000

    for row, col in legal_moves:
        index = row * 3 + col
        next_state = list(initial)
        next_state[index] = 1

        score = minimax(tuple(next_state), -1, 1)

        if score > best_score:
            best_score = score
            best_move = (row, col)

    return best_move
