
from functools import lru_cache

_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _rank(result):
    # Guaranteed outcome, win probability, draw probability,
    # then shorter expected game length.
    outcome, win_probability, draw_probability, length = result
    return outcome, win_probability, draw_probability, -length


@lru_cache(maxsize=None)
def _solve(state, turn):
    """
    Return:
        guaranteed outcome,
        win probability against uniformly random opponent moves,
        draw probability under that model,
        expected remaining moves.

    Our future moves always prioritize the guaranteed outcome.
    """
    for a, b, c in _LINES:
        winner = state[a]
        if winner != 0 and winner == state[b] == state[c]:
            return winner, float(winner == 1), 0.0, 0.0

    moves = [i for i in _ORDER if state[i] == 0]
    if not moves:
        return 0, 0.0, 1.0, 0.0

    children = []
    for i in moves:
        next_state = state[:i] + (turn,) + state[i + 1:]
        children.append(_solve(next_state, -turn))

    if turn == 1:
        best = max(children, key=_rank)
        return best[0], best[1], best[2], best[3] + 1.0

    # Minimax assumes the opponent chooses its strongest response.
    # Secondary statistics separately model possible opponent mistakes.
    count = len(children)
    return (
        min(result[0] for result in children),
        sum(result[1] for result in children) / count,
        sum(result[2] for result in children) / count,
        1.0 + sum(result[3] for result in children) / count,
    )


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(board[r][c] for r in range(3) for c in range(3))
    legal_moves = [i for i in _ORDER if state[i] == 0]

    if not legal_moves:
        raise ValueError("A full board has no legal move.")

    best_move = legal_moves[0]
    best_rank = None

    for move in legal_moves:
        next_state = state[:move] + (1,) + state[move + 1:]
        move_rank = _rank(_solve(next_state, -1))

        if best_rank is None or move_rank > best_rank:
            best_rank = move_rank
            best_move = move

    return best_move // 3, best_move % 3
