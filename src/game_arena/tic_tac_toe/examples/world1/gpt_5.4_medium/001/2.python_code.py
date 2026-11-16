
from functools import lru_cache

# Preferred move order for tie-breaking and search ordering:
# center, corners, then edges.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)

# All winning lines on a flattened 3x3 board.
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


def _flatten(board):
    return tuple(board[r][c] for r in range(3) for c in range(3))


def _terminal_result(state):
    """
    Returns:
        1   if player 1 has already won
        -1  if player -1 has already won
        0   if draw
        None if non-terminal
    """
    for a, b, c in _LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    if 0 not in state:
        return 0
    return None


def _step_adjust(score):
    """
    Prefer faster wins and slower losses.
    Terminal scores are +/-100 or 0.
    Each ply away from termination moves the score one point toward 0.
    """
    if score > 0:
        return score - 1
    if score < 0:
        return score + 1
    return 0


@lru_cache(maxsize=None)
def _solve(state, player):
    """
    Minimax value from the perspective of player 1 (us).
    'player' is whose turn it is in this state: 1 or -1.
    """
    result = _terminal_result(state)
    if result is not None:
        if result == 1:
            return 100
        if result == -1:
            return -100
        return 0

    legal_moves = [i for i in _MOVE_ORDER if state[i] == 0]

    if player == 1:
        best = -10**9
        for i in legal_moves:
            nxt = list(state)
            nxt[i] = 1
            score = _step_adjust(_solve(tuple(nxt), -1))
            if score > best:
                best = score
        return best
    else:
        best = 10**9
        for i in legal_moves:
            nxt = list(state)
            nxt[i] = -1
            score = _step_adjust(_solve(tuple(nxt), 1))
            if score < best:
                best = score
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return a legal move (row, col) for the current board.
    """
    state = _flatten(board)
    legal_moves = [i for i in _MOVE_ORDER if state[i] == 0]

    # Safety fallback: if no legal move exists, return a valid coordinate.
    # (Arena states should normally always have at least one empty cell.)
    if not legal_moves:
        return (0, 0)

    # If the board is already terminal but still has empty cells,
    # just return the preferred legal move to stay legal.
    if _terminal_result(state) is not None:
        i = legal_moves[0]
        return (i // 3, i % 3)

    best_move = legal_moves[0]
    best_score = -10**9

    # We are always choosing a move for player 1.
    for i in legal_moves:
        nxt = list(state)
        nxt[i] = 1
        score = _step_adjust(_solve(tuple(nxt), -1))
        if score > best_score:
            best_score = score
            best_move = i

    return (best_move // 3, best_move % 3)
