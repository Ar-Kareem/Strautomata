
#!/usr/bin/env python3
"""
Tic‑Tac‑Toe policy for player 1.

The board is a 3×3 list of lists containing:
    0 : empty square
    1 : our piece
   -1 : opponent's piece

The function `policy(board)` returns the optimal move (row, col)
using a minimax search with alpha‑beta pruning.
"""

from __future__ import annotations
from typing import List, Tuple, Optional

Board = List[List[int]]
Move = Tuple[int, int]

def _winner(board: Board) -> int:
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    lines = []

    # rows and columns
    for i in range(3):
        lines.append(board[i])                         # row i
        lines.append([board[0][i], board[1][i], board[2][i]])  # col i

    # diagonals
    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])

    for line in lines:
        s = sum(line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _is_full(board: Board) -> bool:
    return all(cell != 0 for row in board for cell in row)

def _available_moves(board: Board) -> List[Move]:
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

def _minimax(board: Board, player: int, alpha: int, beta: int) -> Tuple[int, Optional[Move]]:
    """
    Minimax search with alpha‑beta pruning.
    Returns (score, best_move) for the current player.
    Score is from the perspective of player 1:
        +1 = win for player 1,
        -1 = loss for player 1,
         0 = draw.
    """
    win = _winner(board)
    if win != 0:
        # terminal win/loss
        return (1 if win == 1 else -1, None)
    if _is_full(board):
        return (0, None)   # draw

    best_move: Optional[Move] = None

    if player == 1:   # maximizing player
        max_eval = -float('inf')
        for r, c in _available_moves(board):
            board[r][c] = 1
            eval_score, _ = _minimax(board, -1, alpha, beta)
            board[r][c] = 0
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (r, c)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break   # Beta cut‑off
        return (max_eval, best_move)
    else:             # minimizing player (opponent)
        min_eval = float('inf')
        for r, c in _available_moves(board):
            board[r][c] = -1
            eval_score, _ = _minimax(board, 1, alpha, beta)
            board[r][c] = 0
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (r, c)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break   # Alpha cut‑off
        return (min_eval, best_move)

def policy(board: Board) -> Move:
    """
    Choose the optimal move for player 1 on the given Tic‑Tac‑Toe board.

    Parameters
    ----------
    board : list[list[int]]
        3×3 board where 0 = empty, 1 = us, -1 = opponent.

    Returns
    -------
    tuple[int, int]
        Row and column (0‑based) of the selected move.
    """
    # Defensive programming – if board is already terminal, raise an error
    if _winner(board) != 0 or _is_full(board):
        raise ValueError("policy called on a finished board")

    _, best = _minimax(board, 1, -float('inf'), float('inf'))
    if best is None:
        # Should never happen because we already checked for terminal board
        raise RuntimeError("No legal moves available")
    return best

# Simple test when run as script
if __name__ == "__main__":
    # Example board: empty board → center is optimal
    empty_board = [[0, 0, 0],
                   [0, 0, 0],
                   [0, 0, 0]]
    print("Best move on empty board:", policy(empty_board))  # Expected (1, 1)
