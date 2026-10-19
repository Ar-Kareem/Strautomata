
from functools import lru_cache

PREFERRED_MOVES = [
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
]


def _winner(board):
    for i in range(3):
        s = board[i][0] + board[i][1] + board[i][2]
        if s == 3:
            return 1
        if s == -3:
            return -1

        s = board[0][i] + board[1][i] + board[2][i]
        if s == 3:
            return 1
        if s == -3:
            return -1

    d1 = board[0][0] + board[1][1] + board[2][2]
    if d1 == 3:
        return 1
    if d1 == -3:
        return -1

    d2 = board[0][2] + board[1][1] + board[2][0]
    if d2 == 3:
        return 1
    if d2 == -3:
        return -1

    return 0


def _legal_moves(board):
    return [(r, c) for (r, c) in PREFERRED_MOVES if board[r][c] == 0]


def _to_tuple(board):
    return tuple(tuple(row) for row in board)


@lru_cache(maxsize=None)
def _solve(state, turn):
    board = [list(row) for row in state]
    w = _winner(board)
    if w != 0:
        return w * turn
    moves = _legal_moves(board)
    if not moves:
        return 0

    best = -2
    for r, c in moves:
        board[r][c] = turn
        child = _solve(_to_tuple(board), -turn)
        board[r][c] = 0
        score = -child
        if score > best:
            best = score
            if best == 1:
                break
    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    moves = _legal_moves(board)
    if not moves:
        return (0, 0)

    # Immediate win
    for r, c in moves:
        board[r][c] = 1
        if _winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Immediate block
    for r, c in moves:
        board[r][c] = -1
        if _winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Full minimax
    best_move = moves[0]
    best_score = -2
    for r, c in moves:
        board[r][c] = 1
        score = -_solve(_to_tuple(board), -1)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
