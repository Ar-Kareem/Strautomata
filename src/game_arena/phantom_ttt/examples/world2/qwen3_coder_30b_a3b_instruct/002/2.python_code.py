
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Find all possible moves (0 cells are potential moves)
    empty_cells = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                empty_cells.append((i, j))
    
    # If no empty cells, return invalid (shouldn't happen in game)
    if not empty_cells:
        return (0, 0)
    
    # Check if we can win immediately by completing a line
    # We check all possible winning lines in the board
    for i in range(3):
        # Check rows
        if board[i][0] == 1 and board[i][1] == 1 and board[i][2] == 0:
            return (i, 2)
        if board[i][0] == 1 and board[i][2] == 1 and board[i][1] == 0:
            return (i, 1)
        if board[i][1] == 1 and board[i][2] == 1 and board[i][0] == 0:
            return (i, 0)
        
        # Check columns
        if board[0][i] == 1 and board[1][i] == 1 and board[2][i] == 0:
            return (2, i)
        if board[0][i] == 1 and board[2][i] == 1 and board[1][i] == 0:
            return (1, i)
        if board[1][i] == 1 and board[2][i] == 1 and board[0][i] == 0:
            return (0, i)
    
    # Check diagonals
    if board[0][0] == 1 and board[1][1] == 1 and board[2][2] == 0:
        return (2, 2)
    if board[0][0] == 1 and board[2][2] == 1 and board[1][1] == 0:
        return (1, 1)
    if board[1][1] == 1 and board[2][2] == 1 and board[0][0] == 0:
        return (0, 0)
    
    if board[0][2] == 1 and board[1][1] == 1 and board[2][0] == 0:
        return (2, 0)
    if board[0][2] == 1 and board[2][0] == 1 and board[1][1] == 0:
        return (1, 1)
    if board[1][1] == 1 and board[2][0] == 1 and board[0][2] == 0:
        return (0, 2)
    
    # Check for blocking opponent's immediate win
    # But we can't easily know opponent's marks, so if a cell isn't confirmed ours,
    # we must be cautious
    
    # Prefer center if it's available
    if board[1][1] == 0:
        return (1, 1)
    
    # Prefer corners if available
    corners = [(0,0), (0,2), (2,0), (2,2)]
    available_corners = [c for c in corners if board[c[0]][c[1]] == 0]
    if available_corners:
        return random.choice(available_corners)
    
    # Otherwise choose randomly from empty cells
    return random.choice(empty_cells)
