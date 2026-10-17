
import numpy as np

def check_winner(board):
    for line in board:
        if all(cell == 1 for cell in line):
            return 1
        elif all(cell == -1 for cell in line):
            return -1
    # Check columns
    for col in range(3):
        if all(board[row][col] == 1 for row in range(3)):
            return 1
        elif all(board[row][col] == -1 for row in range(3)):
            return -1
    # Check diagonals
    if all(board[i][i] == 1 for i in range(3)):
        return 1
    elif all(board[i][i] == -1 for i in range(3)):
        return -1
    return 0

def possible_moves(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

def policy(board: list[list[int]]) -> tuple[int, int]:
    for r, c in possible_moves(board):
        # Check if I can win in the next move
        board[r][c] = 1
        if check_winner(board) == 1:
            return (r, c)
        board[r][c] = 0  # Undo move

    for r, c in possible_moves(board):
        # Check if I need to block the opponent from winning
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0  # Undo move
            return (r, c)
        board[r][c] = 0  # Undo move

    # If no winning/blocking move, play in the first available empty spot
    if possible_moves(board):
        return possible_moves(board)[0]

    # In a completed game (unlikely), just return (0, 0)
    return (0, 0)
