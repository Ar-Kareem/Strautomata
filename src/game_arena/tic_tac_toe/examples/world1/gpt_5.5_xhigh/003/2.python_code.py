
from __future__ import annotations

from functools import lru_cache


_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Prefer center, then corners, then edges when all deeper criteria tie.
_MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
_MOVE_RANK = {move: rank for rank, move in enumerate(_MOVE_ORDER)}
_LINE_WEIGHTS = (0, 1, 10, 100)


def _play(cells: tuple[int, ...], index: int, mark: int) -> tuple[int, ...]:
    return cells[:index] + (mark,) + cells[index + 1:]


@lru_cache(maxsize=None)
def _legal_moves(cells: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(i for i in _MOVE_ORDER if cells[i] == 0)


@lru_cache(maxsize=None)
def _winner(cells: tuple[int, ...]) -> int:
    for a, b, c in _LINES:
        mark = cells[a]
        if mark != 0 and mark == cells[b] and mark == cells[c]:
            return 1 if mark > 0 else -1
    return 0


@lru_cache(maxsize=None)
def _minimax(cells: tuple[int, ...], player: int) -> int:
    """
    Exact game-theoretic value from our perspective.
    Positive is good for us, negative is good for opponent.
    Magnitude includes depth preference: faster wins, slower losses.
    """
    winner = _winner(cells)
    empty_count = len(_legal_moves(cells))

    if winner == 1:
        return 10 + empty_count
    if winner == -1:
        return -10 - empty_count
    if empty_count == 0:
        return 0

    moves = _legal_moves(cells)

    if player == 1:
        best = -1000
        for move in moves:
            best = max(best, _minimax(_play(cells, move, 1), -1))
        return best

    best = 1000
    for move in moves:
        best = min(best, _minimax(_play(cells, move, -1), 1))
    return best


@lru_cache(maxsize=None)
def _expected_vs_random(cells: tuple[int, ...], player: int) -> float:
    """
    Tie-breaker value: assume the opponent chooses randomly, while we continue
    to make minimax-safe moves. This improves exploitation of weak opponents
    without sacrificing perfect-play guarantees.
    """
    winner = _winner(cells)
    moves = _legal_moves(cells)
    empty_count = len(moves)

    if winner == 1:
        return 1.0 + 0.01 * empty_count
    if winner == -1:
        return -1.0 - 0.01 * empty_count
    if empty_count == 0:
        return 0.0

    if player == -1:
        total = 0.0
        for move in moves:
            total += _expected_vs_random(_play(cells, move, -1), 1)
        return total / empty_count

    best_minimax = -1000
    best_expected = -1000.0

    for move in moves:
        child = _play(cells, move, 1)
        minimax_value = _minimax(child, -1)
        expected_value = _expected_vs_random(child, -1)

        if minimax_value > best_minimax or (
            minimax_value == best_minimax and expected_value > best_expected
        ):
            best_minimax = minimax_value
            best_expected = expected_value

    return best_expected


@lru_cache(maxsize=None)
def _static_score(cells: tuple[int, ...]) -> int:
    """Final deterministic tie-breaker based on line potential and position."""
    winner = _winner(cells)
    if winner:
        return 10000 * winner

    score = 0

    for a, b, c in _LINES:
        line = (cells[a], cells[b], cells[c])
        mine = line.count(1)
        opp = line.count(-1)

        if opp == 0:
            score += _LINE_WEIGHTS[mine]
        if mine == 0:
            score -= _LINE_WEIGHTS[opp]

    score += 3 * cells[4]
    score += cells[0] + cells[2] + cells[6] + cells[8]
    return score


def policy(board: list[list[int]]) -> tuple[int, int]:
    cells = tuple(int(board[r][c]) for r in range(3) for c in range(3))
    moves = _legal_moves(cells)

    # No legal move exists on a full board; normal arenas should not call here.
    if not moves:
        return (0, 0)

    if len(moves) == 1:
        return divmod(moves[0], 3)

    best_move = moves[0]
    best_key = None

    for move in moves:
        child = _play(cells, move, 1)

        key = (
            _minimax(child, -1),
            _expected_vs_random(child, -1),
            _static_score(child),
            -_MOVE_RANK[move],
        )

        if best_key is None or key > best_key:
            best_key = key
            best_move = move

    return best_move // 3, best_move % 3
