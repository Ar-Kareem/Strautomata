
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
        s = sum(state[r][c] for r, c in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empty_cells(state):
    return [(r, c) for r, c in MOVE_ORDER if state[r][c] == 0]


def _to_tuple(board):
    return tuple(tuple(row) for row in board)


@lru_cache(maxsize=None)
def _minimax(state, player, depth):
    win = _winner(state)
    if win == 1:
        return 10 - depth
    if win == -1:
        return depth - 10

    moves = _empty_cells(state)
    if not moves:
        return 0

    if player == 1:
        best = -100
        for r, c in moves:
            new_state = [list(row) for row in state]
            new_state[r][c] = 1
            score = _minimax(tuple(tuple(row) for row in new_state), -1, depth + 1)
            if score > best:
                best = score
        return best
    else:
        best = 100
        for r, c in moves:
            new_state = [list(row) for row in state]
            new_state[r][c] = -1
            score = _minimax(tuple(tuple(row) for row in new_state), 1, depth + 1)
            if score < best:
                best = score
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = _to_tuple(board)
    legal_moves = _empty_cells(state)

    # If no legal move exists, this should not happen in a valid game.
    # Return a valid-shaped fallback to avoid crashing.
    if not legal_moves:
        return (0, 0)

    # If the board is already terminal but a move is requested anyway,
    # still return a legal empty square.
    if _winner(state) != 0:
        return legal_moves[0]

    # Immediate winning move.
    for r, c in legal_moves:
        test = [list(row) for row in state]
        test[r][c] = 1
        if _winner(tuple(tuple(row) for row in test)) == 1:
            return (r, c)

    # Immediate block against opponent win.
    for r, c in legal_moves:
        test = [list(row) for row in state]
        test[r][c] = -1
        if _winner(tuple(tuple(row) for row in test)) == -1:
            return (r, c)

    best_score = -100
    best_move = legal_moves[0]

    for r, c in legal_moves:
        new_state = [list(row) for row in state]
        new_state[r][c] = 1
        score = _minimax(tuple(tuple(row) for row in new_state), -1, 1)

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
