
from functools import lru_cache

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

MOVE_ORDER = (
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
)


def _winner(state):
    for line in WIN_LINES:
        s = state[line[0][0]][line[0][1]] + state[line[1][0]][line[1][1]] + state[line[2][0]][line[2][1]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _full(state):
    for r in range(3):
        for c in range(3):
            if state[r][c] == 0:
                return False
    return True


def _to_tuple(board):
    return tuple(tuple(row) for row in board)


def _set_cell(state, r, c, value):
    rows = [list(row) for row in state]
    rows[r][c] = value
    return tuple(tuple(row) for row in rows)


@lru_cache(None)
def _minimax(state, player, depth):
    w = _winner(state)
    if w == 1:
        return 10 - depth
    if w == -1:
        return depth - 10
    if _full(state):
        return 0

    if player == 1:
        best = -100
        for r, c in MOVE_ORDER:
            if state[r][c] == 0:
                score = _minimax(_set_cell(state, r, c, 1), -1, depth + 1)
                if score > best:
                    best = score
        return best
    else:
        best = 100
        for r, c in MOVE_ORDER:
            if state[r][c] == 0:
                score = _minimax(_set_cell(state, r, c, -1), 1, depth + 1)
                if score < best:
                    best = score
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = _to_tuple(board)

    legal_moves = [(r, c) for r, c in MOVE_ORDER if state[r][c] == 0]

    if not legal_moves:
        return (0, 0)

    # Immediate win if available.
    for r, c in legal_moves:
        if _winner(_set_cell(state, r, c, 1)) == 1:
            return (r, c)

    # Immediate block if opponent can win next.
    for r, c in legal_moves:
        if _winner(_set_cell(state, r, c, -1)) == -1:
            return (r, c)

    best_move = legal_moves[0]
    best_score = -100

    for r, c in legal_moves:
        next_state = _set_cell(state, r, c, 1)
        score = _minimax(next_state, -1, 1)
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
