
from functools import lru_cache

# Board indices:
# 0 1 2
# 3 4 5
# 6 7 8

_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
)

# Prefer center, then corners, then edges when outcomes are equal.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _winner(state):
    """Return 1 if we won, -1 if opponent won, otherwise 0."""
    for a, b, c in _LINES:
        total = state[a] + state[b] + state[c]
        if total == 3:
            return 1
        if total == -3:
            return -1
    return 0


@lru_cache(maxsize=None)
def _minimax(state, turn):
    """
    Perfect-play minimax score from this state.
    Positive is good for us, negative is good for opponent.
    """
    winner = _winner(state)
    empty_count = state.count(0)

    if winner == 1:
        return 10 + empty_count  # prefer faster wins
    if winner == -1:
        return -10 - empty_count  # prefer slower losses
    if empty_count == 0:
        return 0

    if turn == 1:
        best = -1000
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                nxt = list(state)
                nxt[idx] = 1
                best = max(best, _minimax(tuple(nxt), -1))
        return best
    else:
        best = 1000
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                nxt = list(state)
                nxt[idx] = -1
                best = min(best, _minimax(tuple(nxt), 1))
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next legal move as (row, col).
    board[r][c] == 0 means empty.
    board[r][c] == 1 means our mark.
    board[r][c] == -1 means opponent mark.
    """
    state = tuple(int(board[r][c]) for r in range(3) for c in range(3))

    legal_moves = [idx for idx, value in enumerate(state) if value == 0]

    # This should not happen in a live game, but keeps the function total.
    if not legal_moves:
        return (0, 0)

    best_idx = legal_moves[0]
    best_score = -1000

    for idx in _MOVE_ORDER:
        if state[idx] == 0:
            nxt = list(state)
            nxt[idx] = 1
            score = _minimax(tuple(nxt), -1)

            if score > best_score:
                best_score = score
                best_idx = idx

    return best_idx // 3, best_idx % 3
