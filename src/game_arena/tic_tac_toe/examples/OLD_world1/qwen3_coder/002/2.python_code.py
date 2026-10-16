
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to a more convenient format
    # 1 = me, -1 = opponent, 0 = empty
    
    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing my piece here
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0  # Reset
                    return (i, j)
                board[i][j] = 0  # Reset
    
    # Check for blocking opponent's winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing opponent's piece here
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0  # Reset
                    return (i, j)
                board[i][j] = 0  # Reset
    
    # Try to take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Try to take corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(r, c) for r, c in corners if board[r][c] == 0]
    if available_corners:
        return random.choice(available_corners)
    
    # Take any available side
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_sides = [(r, c) for r, c in sides if board[r][c] == 0]
    if available_sides:
        return random.choice(available_sides)
    
    # Fallback (should not happen in a valid game)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    
    # This should never happen
    return (0, 0)

def check_winner(board):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != 0:
            return row[0]
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != 0:
            return board[0][col]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    
    return 0  # No winner
