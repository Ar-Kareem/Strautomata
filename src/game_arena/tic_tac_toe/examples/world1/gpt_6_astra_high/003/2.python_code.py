
from functools import lru_cache

_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Deterministic final tie-break: center, corners, then edges.
_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _place(state, index, player):
    return state[:index] + (player,) + state[index + 1:]


@lru_cache(maxsize=None)
def _evaluate(state, turn):
    """
    Return:
      guaranteed_score: minimax result, including win/loss timing
      practical_score: expected result against uniformly random opposition

    Practical score only breaks ties between minimax-optimal moves.
    """
    for a, b, c in _LINES:
        winner = state[a]
        if winner != 0 and winner == state[b] == state[c]:
            # Earlier wins score higher; earlier losses score lower.
            return winner * (10 + state.count(0)), float(winner)

    legal = [i for i in _ORDER if state[i] == 0]
    if not legal:
        return 0, 0.0

    results = [
        _evaluate(_place(state, i, turn), -turn)
        for i in legal
    ]

    if turn == 1:
        # Guaranteed outcome always takes precedence over exploitation.
        return max(results)

    # The guarantee assumes optimal opposition. The secondary estimate
    # averages all opponent moves to measure opportunities for mistakes.
    return (
        min(result[0] for result in results),
        sum(result[1] for result in results) / len(results),
    )


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(int(board[r][c]) for r in range(3) for c in range(3))
    legal = [i for i in _ORDER if state[i] == 0]

    if not legal:
        # No policy can return an empty cell on a full board.
        raise ValueError("policy requires a board with an empty cell")

    best_move = legal[0]
    best_value = None

    for move in legal:
        value = _evaluate(_place(state, move, 1), -1)
        if best_value is None or value > best_value:
            best_value = value
            best_move = move

    return best_move // 3, best_move % 3
