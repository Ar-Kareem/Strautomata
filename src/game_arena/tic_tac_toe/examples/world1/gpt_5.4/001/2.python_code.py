
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

PREFERRED_ORDER = [
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
]


def _winner(board_tuple):
    for line in WIN_LINES:
        s = sum(board_tuple[r][c] for r, c in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empty_cells(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]


@lru_cache(maxsize=None)
def _solve(board_tuple, player):
    w = _winner(board_tuple)
    if w != 0:
        return w * player, None

    empties = [(r, c) for r, c in PREFERRED_ORDER if board_tuple[r][c] == 0]
    if not empties:
        return 0, None

    best_score = -2
    best_move = None

    for r, c in empties:
        new_board = [list(row) for row in board_tuple]
        new_board[r][c] = player
        new_board = tuple(tuple(row) for row in new_board)

        score, _ = _solve(new_board, -player)
        score = -score

        if score > best_score:
            best_score = score
            best_move = (r, c)
            if best_score == 1:
                break

    return best_score, best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    empties = _empty_cells(board)
    if not empties:
        return (0, 0)

    # Immediate winning move
    for r, c in empties:
        board[r][c] = 1
        if _winner(tuple(tuple(row) for row in board)) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Immediate block of opponent win
    for r, c in empties:
        board[r][c] = -1
        if _winner(tuple(tuple(row) for row in board)) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    board_tuple = tuple(tuple(row) for row in board)
    _, move = _solve(board_tuple, 1)

    if move is not None and board[move[0]][move[1]] == 0:
        return move

    # Guaranteed legal fallback
    for move in PREFERRED_ORDER:
        r, c = move
        if board[r][c] == 0:
            return move

    return empties[0]
