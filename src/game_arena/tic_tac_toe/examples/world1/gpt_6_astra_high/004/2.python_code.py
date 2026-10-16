
from functools import lru_cache

_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _winner(state):
    for a, b, c in _LINES:
        if state[a] != 0 and state[a] == state[b] == state[c]:
            return state[a]
    return 0


def _place(state, index, player):
    return state[:index] + (player,) + state[index + 1:]


@lru_cache(maxsize=None)
def _evaluate(state, turn):
    """
    Return:
      guaranteed outcome under optimal opposition,
      win probability against random opposition,
      draw probability against random opposition.
    Our future choices always prioritize the guaranteed outcome.
    """
    winner = _winner(state)
    if winner == 1:
        return (1, 1.0, 0.0)
    if winner == -1:
        return (-1, 0.0, 0.0)

    moves = [i for i in _ORDER if state[i] == 0]
    if not moves:
        return (0, 0.0, 1.0)

    values = [
        _evaluate(_place(state, i, turn), -turn)
        for i in moves
    ]

    if turn == 1:
        # Never sacrifice the minimax result for a speculative win.
        return max(values)

    # The opponent is adversarial for the safety calculation,
    # but random for the secondary opportunity calculation.
    count = len(values)
    return (
        min(value[0] for value in values),
        sum(value[1] for value in values) / count,
        sum(value[2] for value in values) / count,
    )


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(board[r][c] for r in range(3) for c in range(3))
    moves = [i for i in _ORDER if state[i] == 0]

    # A playable position necessarily contains an empty cell.
    if not moves:
        raise ValueError("No legal move exists on a full board.")

    candidates = [(i, _place(state, i, 1)) for i in moves]

    for index, next_state in candidates:
        if _winner(next_state) == 1:
            return divmod(index, 3)

    best_move = moves[0]
    best_value = (-2, -1.0, -1.0)

    for index, next_state in candidates:
        value = _evaluate(next_state, -1)
        if value > best_value:
            best_value = value
            best_move = index

    return divmod(best_move, 3)
