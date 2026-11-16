
#!/usr/bin/env python3
"""
Policy for 3x3 Tic‑Tac‑Toe.

The function `policy(board)` receives a 3x3 list of lists with values:
    0 : empty square
    1 : our piece (the AI)
   -1 : opponent's piece

It returns a tuple (row, col) indicating the chosen move.
A minimax algorithm with alpha‑beta pruning is used to guarantee optimal play.
"""

from typing import List, Tuple

Board = List[List[int]]

def _winning_lines() -> List[List[Tuple[int, int]]]:
    """All possible winning line coordinates."""
    lines = []

    # rows
    for r in range(3):
        lines.append([(r, c) for c in range(3)])
    # columns
    for c in range(3):
        lines.append([(r, c) for r in range(3)])
    # diagonals
    lines.append([(i, i) for i in range(3)])
    lines.append([(i, 2 - i) for i in range(3)])

    return lines

_WIN_LINES = _winning_lines()

def _check_winner(board: Board) -> int:
    """
    Return 1 if player 1 has won,
           -1 if player -1 has won,
            0 otherwise (no winner yet).
    """
    for line in _WIN_LINES:
        total = sum(board[r][c] for r, c in line)
        if total == 3:
            return 1
        if total == -3:
            return -1
    return 0

def _is_full(board: Board) -> bool:
    return all(cell != 0 for row in board for cell in row)

def _minimax(board: Board, player: int, alpha: int, beta: int) -> Tuple[int, Tuple[int, int]]:
    """
    Minimax with alpha‑beta pruning.
    Returns (score, best_move) where score is evaluated from player 1's perspective.
    """
    winner = _check_winner(board)
    if winner != 0:
        # game over: return +1 for AI win, -1 for loss
        return (winner, (-1, -1))
    if _is_full(board):
        return (0, (-1, -1))  # draw

    best_move = (-1, -1)

    if player == 1:  # maximizing player (AI)
        max_eval = -float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    eval_score, _ = _minimax(board, -1, alpha, beta)
                    board[r][c] = 0
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = (r, c)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return (max_eval, best_move)
    else:  # minimizing player (opponent)
        min_eval = float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    eval_score, _ = _minimax(board, 1, alpha, beta)
                    board[r][c] = 0
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = (r, c)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return (min_eval, best_move)

def policy(board: Board) -> Tuple[int, int]:
    """
    Choose the optimal move for player 1 (the AI) on the given board.
    """
    # sanity check: ensure board shape
    if len(board) != 3 or any(len(row) != 3 for row in board):
        raise ValueError("Board must be a 3x3 list of lists.")

    # If there's a forced win or block, minimax will handle it.
    _, move = _minimax(board, 1, -float('inf'), float('inf'))

    # If minimax returns an invalid move (should not happen unless board full), pick first empty.
    if move == (-1, -1):
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
        # No moves left
        return (-1, -1)

    return move
