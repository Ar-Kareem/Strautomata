
from functools import lru_cache

# Winning line indices on a flattened 3x3 board.
_WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Prefer center, then corners, then edges.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _terminal_score(state):
    """
    Return a score if the state is terminal, otherwise None.

    Positive is good for us.
    Negative is good for the opponent.
    Earlier wins are preferred; later losses are preferred.
    """
    empty_count = state.count(0)

    for a, b, c in _WIN_LINES:
        line_sum = state[a] + state[b] + state[c]
        if line_sum == 3:
            return 10 + empty_count
        if line_sum == -3:
            return -10 - empty_count

    if empty_count == 0:
        return 0

    return None


@lru_cache(maxsize=None)
def _minimax(state, turn):
    """
    Minimax evaluation.

    state: tuple of 9 ints.
    turn: 1 for our move, -1 for opponent move.
    """
    terminal = _terminal_score(state)
    if terminal is not None:
        return terminal

    if turn == 1:
        best = -100
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                next_state = list(state)
                next_state[idx] = 1
                score = _minimax(tuple(next_state), -1)
                if score > best:
                    best = score
        return best

    else:
        best = 100
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                next_state = list(state)
                next_state[idx] = -1
                score = _minimax(tuple(next_state), 1)
                if score < best:
                    best = score
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the optimal legal move for the current player.

    board[r][c] meanings:
      0  = empty
      1  = our mark
      -1 = opponent mark
    """
    state = tuple(int(board[r][c]) for r in range(3) for c in range(3))

    best_score = -100
    best_idx = None

    for idx in _MOVE_ORDER:
        if state[idx] == 0:
            next_state = list(state)
            next_state[idx] = 1
            score = _minimax(tuple(next_state), -1)

            if score > best_score:
                best_score = score
                best_idx = idx

    # A full board should not be passed to policy because no legal move exists.
    # This fallback preserves the required return shape.
    if best_idx is None:
        return (0, 0)

    return divmod(best_idx, 3)
