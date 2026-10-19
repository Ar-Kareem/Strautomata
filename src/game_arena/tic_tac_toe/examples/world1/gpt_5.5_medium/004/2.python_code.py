
from functools import lru_cache

# Winning line indices for a flattened 3x3 board.
_WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Prefer strategically strong squares when multiple moves are equally good.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _winner(state):
    """Return 1 if we won, -1 if opponent won, otherwise 0."""
    for a, b, c in _WIN_LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


@lru_cache(maxsize=None)
def _minimax(state, turn):
    """
    Return the value of a state assuming perfect play.
    Positive is good for us, negative is good for the opponent.
    """
    w = _winner(state)
    empty_count = state.count(0)

    if w != 0:
        # Earlier wins are better; later losses are better.
        return w * (100 + empty_count)

    if empty_count == 0:
        return 0

    if turn == 1:
        best = -10_000
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                child = list(state)
                child[idx] = 1
                score = _minimax(tuple(child), -1)
                if score > best:
                    best = score
        return best
    else:
        best = 10_000
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                child = list(state)
                child[idx] = -1
                score = _minimax(tuple(child), 1)
                if score < best:
                    best = score
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Choose the best legal move for the player represented by 1.

    Args:
        board: 3x3 list of lists, where:
               0 = empty
               1 = our move
              -1 = opponent move

    Returns:
        A legal move as (row, col).
    """
    state = tuple(int(board[r][c]) for r in range(3) for c in range(3))

    legal_moves = [idx for idx in _MOVE_ORDER if state[idx] == 0]

    # The game engine should not request a move on a full board, but this keeps
    # the function total and prevents crashes.
    if not legal_moves:
        return (0, 0)

    best_move = legal_moves[0]
    best_score = -10_000

    for idx in legal_moves:
        child = list(state)
        child[idx] = 1
        score = _minimax(tuple(child), -1)

        if score > best_score:
            best_score = score
            best_move = idx

    return divmod(best_move, 3)
