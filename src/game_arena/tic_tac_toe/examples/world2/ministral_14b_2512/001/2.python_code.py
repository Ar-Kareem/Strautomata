
import random

def has_four_in_a_row(board, player):
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True

    # Check columns
    for col in range(4):
        if all(board[row][col] == player for row in range(4)):
            return True

    # Check main diagonal (top-left to bottom-right)
    if all(board[i][i] == player for i in range(4)):
        return True

    # Check anti-diagonal (top-right to bottom-left)
    if all(board[i][3 - i] == player for i in range(4)):
        return True

    return False

def policy(board):
    empty_cells = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

    # Check for winning moves (4 in a row for me)
    for r, c in empty_cells:
        new_board = [row.copy() for row in board]
        new_board[r][c] = 1
        if has_four_in_a_row(new_board, 1):
            return (r, c)

    # Check for blocking moves (4 in a row for opponent if I don't block)
    for r, c in empty_cells:
        new_board = [row.copy() for row in board]
        new_board[r][c] = -1
        if has_four_in_a_row(new_board, -1):
            return (r, c)

    # If no immediate win or block, pick a random empty cell
    return random.choice(empty_cells)
