
#!/usr/bin/env python3
"""
Policy for 4x4 Tic‑Tac Toe (win = 4 in a line).

The board is a list of 4 lists, each containing 0 (empty), 1 (our piece) or -1 (opponent).
The function `policy` returns the (row, col) of the chosen move for player 1.
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict

# --------------------- Helper functions ---------------------

def _check_winner(board: List[List[int]]) -> Optional[int]:
    """Return 1 if player 1 wins, -1 if player -1 wins, else None."""
    # rows and columns
    for i in range(4):
        row_sum = sum(board[i])
        if row_sum == 4:
            return 1
        if row_sum == -4:
            return -1
        col_sum = sum(board[r][i] for r in range(4))
        if col_sum == 4:
            return 1
        if col_sum == -4:
            return -1

    # main diagonal
    diag1 = sum(board[i][i] for i in range(4))
    if diag1 == 4:
        return 1
    if diag1 == -4:
        return -1

    # anti‑diagonal
    diag2 = sum(board[i][3 - i] for i in range(4))
    if diag2 == 4:
        return 1
    if diag2 == -4:
        return -1

    return None


def _board_to_key(board: List[List[int]]) -> Tuple[int, ...]:
    """Flatten the board into an immutable tuple for caching."""
    return tuple(cell for row in board for cell in row)


# --------------------- Minimax with alpha‑beta ---------------------

# Simple transposition table
_cache: Dict[Tuple[int, ...], int] = {}

def _minimax(board: List[List[int]], player: int,
             alpha: int, beta: int) -> int:
    """
    Minimax evaluation for the current board.
    Returns +1 (player 1 wins), -1 (player -1 wins) or 0 (draw or undecided terminal).
    """
    key = _board_to_key(board)
    if key in _cache:
        return _cache[key]

    winner = _check_winner(board)
    if winner is not None:
        _cache[key] = winner
        return winner

    # Check for draw (full board)
    if all(cell != 0 for cell in key):
        _cache[key] = 0
        return 0

    # Not terminal: explore moves
    if player == 1:
        max_eval = -2  # lower than the worst possible score
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    board[r][c] = 1
                    eval_score = _minimax(board, -1, alpha, beta)
                    board[r][c] = 0
                    if eval_score > max_eval:
                        max_eval = eval_score
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        _cache[key] = max_eval
        return max_eval
    else:  # player == -1
        min_eval = 2
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    board[r][c] = -1
                    eval_score = _minimax(board, 1, alpha, beta)
                    board[r][c] = 0
                    if eval_score < min_eval:
                        min_eval = eval_score
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        _cache[key] = min_eval
        return min_eval


# --------------------- Public policy function ---------------------

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the best move for player 1 on a 4x4 Tic‑Tac Toe board.

    Parameters
    ----------
    board : list[list[int]]
        Current game state (0 = empty, 1 = us, -1 = opponent).

    Returns
    -------
    tuple[int, int]
        Row and column indices (0‑based) of the selected move.
    """
    best_score = -2
    best_move: Tuple[int, int] = (0, 0)  # default fallback

    # If board already terminal, just return first empty (should not happen)
    if _check_winner(board) is not None or all(cell != 0 for row in board for cell in row):
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)

    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                score = _minimax(board, -1, -2, 2)
                board[r][c] = 0

                if score > best_score:
                    best_score = score
                    best_move = (r, c)

                # Immediate win – no need to search further
                if best_score == 1:
                    return best_move

    return best_move

# The file can be imported and the `policy` function called directly.
