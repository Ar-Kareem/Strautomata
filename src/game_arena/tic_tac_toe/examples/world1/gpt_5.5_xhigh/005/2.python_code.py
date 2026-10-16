
from __future__ import annotations

from functools import lru_cache


_WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Tie-break preference: center > corners > edges.
_POSITIONAL_VALUE = (
    3, 2, 3,
    2, 4, 2,
    3, 2, 3,
)


def _to_state(board):
    """Convert the 3x3 board to a hashable flat tuple."""
    cells = []
    for r in range(3):
        for c in range(3):
            value = board[r][c]
            if value == 1:
                cells.append(1)
            elif value == -1:
                cells.append(-1)
            else:
                cells.append(0)
    return tuple(cells)


def _winner(state):
    """Return 1 if we have won, -1 if opponent has won, else 0."""
    for a, b, c in _WIN_LINES:
        total = state[a] + state[b] + state[c]
        if total == 3:
            return 1
        if total == -3:
            return -1
    return 0


def _legal_moves(state):
    return [i for i, value in enumerate(state) if value == 0]


def _place(state, move, mark):
    return state[:move] + (mark,) + state[move + 1:]


def _better_minimax_candidate(value, depth, best_value, best_depth, turn):
    """Comparison helper for exact minimax search."""
    if best_value is None:
        return True

    if turn == 1:
        # We maximize the result.
        if value != best_value:
            return value > best_value
        # Fast wins, slow losses.
        if value == 1:
            return depth < best_depth
        if value == -1:
            return depth > best_depth
        return depth < best_depth

    # Opponent minimizes the result.
    if value != best_value:
        return value < best_value
    # Opponent prefers fast opponent wins and delayed our wins.
    if value == -1:
        return depth < best_depth
    if value == 1:
        return depth > best_depth
    return depth < best_depth


@lru_cache(maxsize=None)
def _minimax(state, turn):
    """
    Return (game_theoretic_value, depth_to_terminal).

    game_theoretic_value:
        1  = forced win for us
        0  = forced draw
        -1 = forced loss
    """
    w = _winner(state)
    if w != 0:
        return w, 0

    moves = _legal_moves(state)
    if not moves:
        return 0, 0

    best_value = None
    best_depth = 0

    for move in moves:
        child = _place(state, move, turn)
        value, depth = _minimax(child, -turn)
        depth += 1

        if _better_minimax_candidate(value, depth, best_value, best_depth, turn):
            best_value = value
            best_depth = depth

    return best_value, best_depth


def _policy_score(value, depth, expectation, positional_value):
    """
    Scoring tuple for choosing among legal moves.

    Primary key is exact minimax value.
    Secondary keys exploit weaker opponents without sacrificing correctness.
    """
    if value > 0:
        # If winning is forced, win as quickly as possible.
        return value, -depth, expectation, positional_value
    if value < 0:
        # If already lost against perfect play, maximize swindle chances.
        return value, expectation, depth, positional_value
    # If drawable, pick the move with best expected payoff versus imperfect play.
    return value, expectation, positional_value, -depth


@lru_cache(maxsize=None)
def _expected_value(state, turn):
    """
    Expected utility against a random/imperfect opponent, assuming our future
    choices still obey the safe minimax-first policy.
    """
    w = _winner(state)
    if w != 0:
        return float(w)

    moves = _legal_moves(state)
    if not moves:
        return 0.0

    if turn == -1:
        # Opponent model for tie-breaking: average over legal replies.
        total = 0.0
        for move in moves:
            total += _expected_value(_place(state, move, -1), 1)
        return total / len(moves)

    # Our future turns use the same safe policy: minimax first, exploitation second.
    best_score = None
    best_expectation = -2.0

    for move in moves:
        child = _place(state, move, 1)
        value, depth = _minimax(child, -1)
        depth += 1
        expectation = _expected_value(child, -1)
        score = _policy_score(value, depth, expectation, _POSITIONAL_VALUE[move])

        if best_score is None or score > best_score:
            best_score = score
            best_expectation = expectation

    return best_expectation


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next move as (row, col). The returned cell is empty whenever
    at least one legal move exists.
    """
    state = _to_state(board)
    moves = _legal_moves(state)

    # No legal move exists on a full board; arena should not request a move then.
    if not moves:
        return (0, 0)

    # If called on an already-terminal board with empty cells, still return legal.
    if _winner(state) != 0:
        move = moves[0]
        return (move // 3, move % 3)

    best_move = moves[0]
    best_score = None

    for move in moves:
        child = _place(state, move, 1)
        value, depth = _minimax(child, -1)
        depth += 1
        expectation = _expected_value(child, -1)
        score = _policy_score(value, depth, expectation, _POSITIONAL_VALUE[move])

        if best_score is None or score > best_score:
            best_score = score
            best_move = move

    return (best_move // 3, best_move % 3)
