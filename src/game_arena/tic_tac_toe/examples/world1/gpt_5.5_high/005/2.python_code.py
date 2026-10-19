
from __future__ import annotations

from functools import lru_cache


_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
)

# Preferred order for deterministic tie-breaking: center, corners, then edges.
_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
_POSITIONAL = (3, 2, 3, 2, 5, 2, 3, 2, 3)
_LINE_SCORE = (0, 1, 6, 50)


@lru_cache(maxsize=None)
def _winner(state: tuple[int, ...]) -> int:
    """Return 1 if we have won, -1 if opponent has won, else 0."""
    for a, b, c in _LINES:
        total = state[a] + state[b] + state[c]
        if total == 3:
            return 1
        if total == -3:
            return -1
    return 0


@lru_cache(maxsize=None)
def _minimax(state: tuple[int, ...], turn: int) -> int:
    """
    Perfect-play minimax score from our perspective.

    Positive means forced win, zero means forced draw, negative means forced loss.
    Faster wins and slower losses are preferred.
    """
    w = _winner(state)
    if w == 1:
        return 100 + state.count(0)
    if w == -1:
        return -100 - state.count(0)
    if 0 not in state:
        return 0

    if turn == 1:
        best = -10_000
        for i in _ORDER:
            if state[i] == 0:
                new_state = state[:i] + (1,) + state[i + 1:]
                best = max(best, _minimax(new_state, -1))
        return best

    best = 10_000
    for i in _ORDER:
        if state[i] == 0:
            new_state = state[:i] + (-1,) + state[i + 1:]
            best = min(best, _minimax(new_state, 1))
    return best


@lru_cache(maxsize=None)
def _expected_vs_random(state: tuple[int, ...], turn: int) -> float:
    """
    Tie-breaker value assuming the opponent plays randomly while we still choose
    only moves that preserve the best minimax result.
    """
    w = _winner(state)
    if w == 1:
        return 1.0
    if w == -1:
        return -1.0
    if 0 not in state:
        return 0.0

    if turn == 1:
        best_key = None
        best_exp = -10.0
        for i in _ORDER:
            if state[i] == 0:
                new_state = state[:i] + (1,) + state[i + 1:]
                primary = _minimax(new_state, -1)
                exp = _expected_vs_random(new_state, -1)
                key = (primary, exp)
                if best_key is None or key > best_key:
                    best_key = key
                    best_exp = exp
        return best_exp

    total = 0.0
    count = 0
    for i in _ORDER:
        if state[i] == 0:
            new_state = state[:i] + (-1,) + state[i + 1:]
            total += _expected_vs_random(new_state, 1)
            count += 1
    return total / count if count else 0.0


def _winning_moves_count(state: tuple[int, ...], player: int) -> int:
    count = 0
    for i, value in enumerate(state):
        if value == 0:
            new_state = state[:i] + (player,) + state[i + 1:]
            if _winner(new_state) == player:
                count += 1
    return count


def _secondary_score(state: tuple[int, ...], move_index: int) -> int:
    """Small deterministic heuristic used only after minimax/expectation ties."""
    score = _POSITIONAL[move_index]

    for line in _LINES:
        vals = (state[line[0]], state[line[1]], state[line[2]])

        if -1 not in vals:
            score += _LINE_SCORE[vals.count(1)]
        if 1 not in vals:
            score -= _LINE_SCORE[vals.count(-1)]

    score += 8 * _winning_moves_count(state, 1)
    score -= 6 * _winning_moves_count(state, -1)
    return score


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next move as (row, col). The returned cell is always empty
    whenever at least one empty cell exists.
    """
    cells = []
    for r in range(3):
        for c in range(3):
            v = board[r][c]
            if v == 1:
                cells.append(1)
            elif v == -1:
                cells.append(-1)
            else:
                cells.append(0)

    state = tuple(cells)
    legal = [i for i, v in enumerate(state) if v == 0]

    # A full board should not be passed to the policy, but keep a safe fallback.
    if not legal:
        return (0, 0)

    best_index = legal[0]
    best_key = None

    for i in _ORDER:
        if state[i] != 0:
            continue

        new_state = state[:i] + (1,) + state[i + 1:]

        primary = _minimax(new_state, -1)
        expected = _expected_vs_random(new_state, -1)
        secondary = _secondary_score(new_state, i)

        key = (primary, expected, secondary)

        if best_key is None or key > best_key:
            best_key = key
            best_index = i

    return (best_index // 3, best_index % 3)
