
from functools import lru_cache
from typing import List, Tuple

WIN_LINES = (
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
)

# Strong tie-break order for equally good moves.
MOVE_ORDER = (
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
)


def _to_state(board: List[List[int]]) -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(int(cell) for cell in row) for row in board)


def _winner(state: Tuple[Tuple[int, ...], ...]) -> int:
    for line in WIN_LINES:
        s = (
            state[line[0][0]][line[0][1]]
            + state[line[1][0]][line[1][1]]
            + state[line[2][0]][line[2][1]]
        )
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empty_count(state: Tuple[Tuple[int, ...], ...]) -> int:
    return sum(1 for row in state for cell in row if cell == 0)


def _legal_moves(state: Tuple[Tuple[int, ...], ...]):
    return [move for move in MOVE_ORDER if state[move[0]][move[1]] == 0]


def _play(state: Tuple[Tuple[int, ...], ...], move: Tuple[int, int], player: int):
    r, c = move
    rows = [list(row) for row in state]
    rows[r][c] = player
    return tuple(tuple(row) for row in rows)


@lru_cache(maxsize=None)
def _solve(state: Tuple[Tuple[int, ...], ...], player: int) -> int:
    """
    Returns a score from our perspective:
    positive = good for us, negative = good for opponent.
    Magnitude prefers faster wins and slower losses.
    """
    w = _winner(state)
    if w == 1:
        return 1 + _empty_count(state)
    if w == -1:
        return -1 - _empty_count(state)

    moves = _legal_moves(state)
    if not moves:
        return 0

    if player == 1:
        best = -10
        for move in moves:
            value = _solve(_play(state, move, 1), -1)
            if value > best:
                best = value
        return best
    else:
        best = 10
        for move in moves:
            value = _solve(_play(state, move, -1), 1)
            if value < best:
                best = value
        return best


def policy(board: List[List[int]]) -> Tuple[int, int]:
    try:
        state = _to_state(board)
        moves = _legal_moves(state)

        if not moves:
            # Should not happen in a normal non-terminal call.
            return (0, 0)

        best_move = moves[0]
        best_score = -10

        for move in moves:
            score = _solve(_play(state, move, 1), -1)
            if score > best_score:
                best_score = score
                best_move = move

        r, c = best_move
        if board[r][c] == 0:
            return (r, c)

    except Exception:
        pass

    # Safety fallback: always return a legal move if one exists.
    for r in range(3):
        for c in range(3):
            try:
                if board[r][c] == 0:
                    return (r, c)
            except Exception:
                continue

    # No legal move exists.
    return (0, 0)
