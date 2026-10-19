
from typing import List

def check_winner(board: List[List[int]]) -> None:
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 for draw, None otherwise."""
    # rows
    for i in range(3):
        row_sum = sum(board[i])
        if row_sum == 3:
            return 1
        if row_sum == -3:
            return -1
    # columns
    for j in range(3):
        col_sum = sum(board[i][j] for i in range(3))
        if col_sum == 3:
            return 1
        if col_sum == -3:
            return -1
    # diagonals
    diag1 = board[0][0] + board[1][1] + board[2][2]
    if diag1 == 3:
        return 1
    if diag1 == -3:
        return -1
    diag2 = board[0][2] + board[1][1] + board[2][0]
    if diag2 == 3:
        return 1
    if diag2 == -3:
        return -1
    # draw?
    if all(board[i][j] != 0 for i in range(3) for j in range(3)):
        return 0
    return None

def minimax(board: List[List[int]], player: int) -> int:
    """
    Minimax algorithm returning the evaluation of the board from the perspective
    of player 1 (our AI). player is 1 for maximizing (AI), -1 for minimizing (opponent).
    Returns:
        1  - AI wins
        0  - draw
        -1 - opponent wins
    """
    result = check_winner(board)
    if result is not None:
        return result

    if player == 1:
        max_eval = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = player
                    eval = minimax(board, -player)
                    board[i][j] = 0
                    if eval > max_eval:
                        max_eval = eval
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = player
                    eval = minimax(board, -player)
                    board[i][j] = 0
                    if eval < min_eval:
                        min_eval = eval
        return min_eval

def policy(board: List[List[int]]) -> int:
    """
    Choose the next move for the AI (player 1) on a given Tic‑Tac‑Toe board.
    The board is a 3x3 list of lists with:
        0  – empty cell
        1  – AI's mark
        -1 – opponent's mark
    Returns an integer from 1 to 9 indicating the chosen cell,
    numbered row‑major:
        1 2 3
        4 5 6
        7 8 9
    """
    best_val = -float('inf')
    best_move = None

    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1  # simulate AI move
                move_val = minimax(board, -1)  # opponent's turn next
                board[i][j] = 0  # undo move

                if move_val > best_val:
                    best_val = move_val
                    best_move = (i, j)

    if best_move is None:
        import random
        empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
        if not empty_cells:
            raise ValueError("Board is full – no move possible.")
        best_move = random.choice(empty_cells)

    return best_move[0] * 3 + best_move[1] + 1

__all__ = ["policy"]
