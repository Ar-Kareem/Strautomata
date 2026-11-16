
import numpy as np
import random

def check_win_line(line):
    if line.count(1) == 2 and line.count(0) == 1:
        return line.index(0)
    return -1

def check_win(board):
    # Check rows, columns, and layers
    for i in range(3):
        # Layers
        for j in range(3):
            if check_win_line(board[i][j]) != -1:
                return (i, j, check_win_line(board[i][j]))
            if check_win_line([board[i][k][j] for k in range(3)]) != -1:
                return (i, check_win_line([board[i][k][j] for k in range(3)]), j)
        
        # Check vertical stacks
        if check_win_line([board[k][i][j] for k in range(3)]) != -1:
            return (check_win_line([board[k][i][j] for k in range(3)]), i, j)

    # Check every diagonal
    diagonals = [
        [board[i][i][i] for i in range(3)],  # (0,0,0), (1,1,1), (2,2,2)
        [board[i][i][2-i] for i in range(3)], # (0,0,2), (1,1,1), (2,2,0)
        [board[i][2-i][i] for i in range(3)], # (0,2,0), (1,1,1), (2,0,2)
        [board[2-i][i][i] for i in range(3)], # (0,0,0), (1,1,1), (2,2,2) for reverse
        [board[i][2-i][2-i] for i in range(3)],
        [board[2-i][i][2-i] for i in range(3)],
        [board[2-i][2-i][i] for i in range(3)],
        [board[i][2-i][i] for i in range(3)]
    ]

    for diag in diagonals:
        if check_win_line(diag) != -1:
            idx = check_win_line(diag)
            if diag is diagonals[0]:
                return (idx, idx, idx)  # main diagonal
            elif diag is diagonals[1]:
                return (idx, idx, 2 - idx)  # antidiagonal
            # Continue for the others

    return None

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Check if there's a winning move or a blocking move
    move = check_win(board)
    if move:
        return move

    # Collect all empty cells
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]

    if empty_cells:
        # Return a random empty cell
        return random.choice(empty_cells)

    # No move possible
    return (-1, -1, -1)
