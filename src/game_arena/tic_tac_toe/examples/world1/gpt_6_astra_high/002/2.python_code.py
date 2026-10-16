
from functools import lru_cache

_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Deterministic preference when evaluated moves are otherwise identical.
_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _winner(state):
    for a, b, c in _LINES:
        if state[a] != 0 and state[a] == state[b] == state[c]:
            return state[a]
    return 0


def _place(state, index, player):
    return state[:index] + (player,) + state[index + 1:]


@lru_cache(maxsize=None)
def _solve(state, turn):
    """
    Return:
      guaranteed: minimax outcome from our perspective (-1, 0, 1)
      expected: expected outcome against uniformly random opponent moves,
                while we continue choosing minimax-optimal moves
    """
    winner = _winner(state)
    if winner:
        return winner, float(winner)

    moves = [i for i in _ORDER if state[i] == 0]
    if not moves:
        return 0, 0.0

    results = [
        _solve(_place(state, i, turn), -turn)
        for i in moves
    ]

    if turn == 1:
        # Guaranteed outcome takes precedence over the exploitation tie-break.
        return max(results)

    # The opponent is adversarial for the guarantee, but random for
    # the secondary estimate of how readily mistakes can be exploited.
    guaranteed = min(result[0] for result in results)
    expected = sum(result[1] for result in results) / len(results)
    return guaranteed, expected


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(board[r][c] for r in range(3) for c in range(3))
    legal = [i for i in _ORDER if state[i] == 0]

    # No legal action exists on a full board; a game must not request one.
    if not legal:
        raise ValueError("policy requires at least one empty cell")

    # Finish immediately whenever possible.
    for i in legal:
        if _winner(_place(state, i, 1)) == 1:
            return divmod(i, 3)

    best_move = legal[0]
    best_value = (-2, -2.0)

    for i in legal:
        value = _solve(_place(state, i, 1), -1)
        if value > best_value:
            best_value = value
            best_move = i

    return divmod(best_move, 3)
