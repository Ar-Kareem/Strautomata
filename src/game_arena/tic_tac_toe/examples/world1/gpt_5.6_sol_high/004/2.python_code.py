
from functools import lru_cache


# Center, corners, then edges provide a strong deterministic tie-break order.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)

_WIN_LINES = (
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
    for a, b, c in _WIN_LINES:
        if state[a] != 0 and state[a] == state[b] == state[c]:
            return state[a]
    return 0


@lru_cache(maxsize=None)
def _search(state: tuple[int, ...], turn: int) -> tuple[int, float]:
    """
    Return:
      primary: adversarial minimax value
      secondary: performance against a mistake-prone/random opponent
    """
    winner = _winner(state)
    empty_count = state.count(0)

    if winner == 1:
        # More empty cells means the win happened sooner.
        return 100 + empty_count, 1.0 + empty_count * 0.01

    if winner == -1:
        # Earlier losses are worse than later losses.
        return -100 - empty_count, -1.0 - empty_count * 0.01

    if empty_count == 0:
        return 0, 0.0

    child_values = []

    for index in _MOVE_ORDER:
        if state[index] != 0:
            continue

        child = list(state)
        child[index] = turn
        child_values.append(_search(tuple(child), -turn))

    if turn == 1:
        # Our move: preserve the best minimax result, then maximize pressure.
        return max(child_values)

    # Opponent's minimax behavior determines the guaranteed result.
    guaranteed_value = min(value[0] for value in child_values)

    # The average measures how well the position performs if the opponent
    # does not always find the strongest response.
    expected_value = sum(value[1] for value in child_values) / len(child_values)

    return guaranteed_value, expected_value


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(int(board[row][col]) for row in range(3) for col in range(3))
    legal_moves = [index for index in _MOVE_ORDER if state[index] == 0]

    # A full board has no legal action; valid arena calls always have an empty
    # cell. This fallback keeps the function total for malformed calls.
    if not legal_moves:
        return 0, 0

    best_index = legal_moves[0]
    best_value = None

    for index in legal_moves:
        child = list(state)
        child[index] = 1
        value = _search(tuple(child), -1)

        if best_value is None or value > best_value:
            best_value = value
            best_index = index

    return divmod(best_index, 3)
