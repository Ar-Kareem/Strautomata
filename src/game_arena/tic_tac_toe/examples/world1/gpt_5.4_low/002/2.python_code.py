
from typing import List, Tuple

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

MOVE_PREFERENCE = [
    (1, 1),  # center
    (0, 0), (0, 2), (2, 0), (2, 2),  # corners
    (0, 1), (1, 0), (1, 2), (2, 1),  # edges
]


def _winner(board: List[List[int]]) -> int:
    for line in WIN_LINES:
        s = sum(board[r][c] for r, c in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empty_cells(board: List[List[int]]):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]


def _ordered_empty_cells(board: List[List[int]]):
    empties = set(_empty_cells(board))
    return [mv for mv in MOVE_PREFERENCE if mv in empties]


def _board_key(board: List[List[int]], turn: int):
    return tuple(tuple(row) for row in board), turn


def _minimax(board: List[List[int]], turn: int, memo) -> int:
    w = _winner(board)
    if w != 0:
        return w
    empties = _empty_cells(board)
    if not empties:
        return 0

    key = _board_key(board, turn)
    if key in memo:
        return memo[key]

    if turn == 1:
        best = -2
        for r, c in _ordered_empty_cells(board):
            board[r][c] = 1
            score = _minimax(board, -1, memo)
            board[r][c] = 0
            if score > best:
                best = score
            if best == 1:
                break
    else:
        best = 2
        for r, c in _ordered_empty_cells(board):
            board[r][c] = -1
            score = _minimax(board, 1, memo)
            board[r][c] = 0
            if score < best:
                best = score
            if best == -1:
                break

    memo[key] = best
    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Collect legal moves first to guarantee a legal return.
    legal_moves = _ordered_empty_cells(board)
    if not legal_moves:
        return (0, 0)  # Fallback for invalid/full boards; arena should normally avoid this.

    # 1) Immediate winning move.
    for r, c in legal_moves:
        board[r][c] = 1
        if _winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 2) Immediate block of opponent winning move.
    for r, c in legal_moves:
        board[r][c] = -1
        if _winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 3) Full minimax search for optimal move.
    memo = {}
    best_score = -2
    best_move = legal_moves[0]

    for r, c in legal_moves:
        board[r][c] = 1
        score = _minimax(board, -1, memo)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
