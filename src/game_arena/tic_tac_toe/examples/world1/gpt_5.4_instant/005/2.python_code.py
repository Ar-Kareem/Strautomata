
from functools import lru_cache

PREFERRED_MOVES = [
    (1, 1),  # center
    (0, 0), (0, 2), (2, 0), (2, 2),  # corners
    (0, 1), (1, 0), (1, 2), (2, 1),  # edges
]

WIN_LINES = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]


def _winner(board):
    for line in WIN_LINES:
        s = sum(board[r][c] for r, c in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empty_cells(board):
    cells = []
    for r, c in PREFERRED_MOVES:
        if board[r][c] == 0:
            cells.append((r, c))
    return cells


def _to_tuple(board):
    return tuple(tuple(row) for row in board)


@lru_cache(maxsize=None)
def _solve(state, player):
    board = [list(row) for row in state]
    w = _winner(board)
    if w != 0:
        return w * player, None

    moves = _empty_cells(board)
    if not moves:
        return 0, None

    best_score = -2
    best_move = None

    for r, c in moves:
        board[r][c] = player
        child_score, _ = _solve(_to_tuple(board), -player)
        board[r][c] = 0
        score = -child_score

        if score > best_score:
            best_score = score
            best_move = (r, c)

        if best_score == 1:
            break

    return best_score, best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Defensive legality handling
    legal = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    if not legal:
        return (0, 0)

    # Immediate win
    for r, c in _empty_cells(board):
        board[r][c] = 1
        if _winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Immediate block
    for r, c in _empty_cells(board):
        board[r][c] = -1
        if _winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Full minimax
    _, move = _solve(_to_tuple(board), 1)
    if move is not None and board[move[0]][move[1]] == 0:
        return move

    # Guaranteed legal fallback
    for move in PREFERRED_MOVES:
        r, c = move
        if board[r][c] == 0:
            return move

    return legal[0]
