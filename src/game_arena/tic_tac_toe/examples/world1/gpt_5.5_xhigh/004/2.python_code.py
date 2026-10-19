
from __future__ import annotations

_WIN_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Prefer center, then corners, then edges when outcomes are equivalent.
_MOVE_ORDER: tuple[int, ...] = (4, 0, 2, 6, 8, 1, 3, 5, 7)

_CACHE: dict[tuple[tuple[int, ...], int], int] = {}


def _winner(state: tuple[int, ...]) -> int:
    for a, b, c in _WIN_LINES:
        total = state[a] + state[b] + state[c]
        if total == 3:
            return 1
        if total == -3:
            return -1
    return 0


def _minimax(state: tuple[int, ...], player: int) -> int:
    """
    Returns a score from our perspective:
      positive = good for us, negative = good for opponent.
    Larger positive scores prefer faster wins.
    More negative scores represent faster losses.
    """
    key = (state, player)
    if key in _CACHE:
        return _CACHE[key]

    win = _winner(state)
    if win == 1:
        score = 10 + state.count(0)
    elif win == -1:
        score = -10 - state.count(0)
    elif 0 not in state:
        score = 0
    elif player == 1:
        score = -100
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                child = list(state)
                child[idx] = 1
                score = max(score, _minimax(tuple(child), -1))
    else:
        score = 100
        for idx in _MOVE_ORDER:
            if state[idx] == 0:
                child = list(state)
                child[idx] = -1
                score = min(score, _minimax(tuple(child), 1))

    _CACHE[key] = score
    return score


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(int(board[r][c]) for r in range(3) for c in range(3))

    best_idx = None
    best_score = -100

    for idx in _MOVE_ORDER:
        if state[idx] == 0:
            child = list(state)
            child[idx] = 1
            score = _minimax(tuple(child), -1)

            if score > best_score:
                best_score = score
                best_idx = idx

    # A legal board with an unfinished game will always set best_idx.
    # This fallback prevents crashes if called on a full board.
    if best_idx is None:
        return (0, 0)

    return divmod(best_idx, 3)
