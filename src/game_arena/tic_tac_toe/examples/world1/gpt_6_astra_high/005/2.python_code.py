
from functools import lru_cache

_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Deterministic preference when all evaluated scores are equal.
_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _winner(state):
    for a, b, c in _LINES:
        if state[a] != 0 and state[a] == state[b] == state[c]:
            return state[a]
    return 0


def _play(state, index, player):
    return state[:index] + (player,) + state[index + 1:]


@lru_cache(maxsize=None)
def _solve(state, turn):
    """Return (minimax outcome, expected result against random opposition)."""
    winner = _winner(state)
    if winner:
        return winner, float(winner)

    legal = [i for i in _ORDER if state[i] == 0]
    if not legal:
        return 0, 0.0

    results = [
        _solve(_play(state, i, turn), -turn)
        for i in legal
    ]

    if turn == 1:
        # Guaranteed outcome always takes priority over exploitation.
        return max(results)

    # An optimal opponent determines the guaranteed outcome.
    # A random opponent determines the secondary expected-result score.
    guaranteed = min(result[0] for result in results)
    expected = sum(result[1] for result in results) / len(results)
    return guaranteed, expected


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(board[r][c] for r in range(3) for c in range(3))
    legal = [i for i in _ORDER if state[i] == 0]

    if not legal:
        raise ValueError("No legal move exists on a full board.")

    best_index = legal[0]
    best_score = (-2, -2.0)

    for index in legal:
        child = _play(state, index, 1)

        if _winner(child) == 1:
            return divmod(index, 3)

        score = _solve(child, -1)
        if score > best_score:
            best_score = score
            best_index = index

    return divmod(best_index, 3)
