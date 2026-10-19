
import numpy as np
from typing import Tuple

def evaluate(board: list[list[int]], player: int) -> int:
    """
    Evaluate the board state for the given player.
    Returns:
        1 if player wins,
        -1 if opponent wins,
        0 if draw,
        None if game is not over.
    """
    opponent = -1 if player == 1 else 1

    # Check rows
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] == player:
            return 1
        if board[i][0] == board[i][1] == board[i][2] == opponent:
            return -1

    # Check columns
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] == player:
            return 1
        if board[0][j] == board[1][j] == board[2][j] == opponent:
            return -1

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return 1
    if board[0][2] == board[1][1] == board[2][0] == player:
        return 1
    if board[0][0] == board[1][1] == board[2][2] == opponent:
        return -1
    if board[0][2] == board[1][1] == board[2][0] == opponent:
        return -1

    # Check if the board is full (draw)
    if all(cell != 0 for row in board for cell in row):
        return 0

    return None

def get_possible_moves(board: list[list[int]]) -> list[Tuple[int, int]]:
    """
    Get all possible moves (empty cells) from the current board state.
    """
    return [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

def can_win(board: list[list[int]], player: int) -> bool:
    """
    Check if the given player can win in the next move.
    """
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                new_board = [row.copy() for row in board]
                new_board[i][j] = player
                if evaluate(new_board, player) == 1:
                    return True
    return False

def policy(board: list[list[int]]) -> Tuple[int, int]:
    """
    Choose the best move for the current board state.
    """
    possible_moves = get_possible_moves(board)
    player = 1
    opponent = -1

    # Check for immediate win
    for move in possible_moves:
        new_board = [row.copy() for row in board]
        new_board[move[0]][move[1]] = player
        if evaluate(new_board, player) == 1:
            return move

    # Check for immediate opponent win and block it
    for move in possible_moves:
        new_board = [row.copy() for row in board]
        new_board[move[0]][move[1]] = opponent
        if evaluate(new_board, opponent) == -1:
            return move

    # If no immediate win or block, choose a strategic move
    # Heuristic: prioritize center, then corners, then edges
    strategic_priority = {
        (1, 1): 3,  # Center
        (0, 0): 2, (0, 2): 2, (2, 0): 2, (2, 2): 2,  # Corners
        (0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1  # Edges
    }

    # Filter possible moves by strategic priority
    best_move = None
    best_priority = -1

    for move in possible_moves:
        priority = strategic_priority.get(move, 0)
        if priority > best_priority:
            best_priority = priority
            best_move = move

    return best_move
