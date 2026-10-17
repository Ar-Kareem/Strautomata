
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing our mark here
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0  # Reset the board
                    return (i, j)
                board[i][j] = 0  # Reset the board
    
    # Check for blocking opponent's winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing opponent's mark here
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0  # Reset the board
                    return (i, j)
                board[i][j] = 0  # Reset the board
    
    # Try to take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Try to take corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(i, j) for i, j in corners if board[i][j] == 0]
    if available_corners:
        return random.choice(available_corners)
    
    # Take any available side
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_sides = [(i, j) for i, j in sides if board[i][j] == 0]
    if available_sides:
        return random.choice(available_sides)
    
    # Fallback (should never happen in a valid game)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    
    # If no moves available (should never happen), return center
    return (1, 1)

def check_win(board: List[List[int]], player: int) -> bool:
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    
    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i] == player for i in range(3)):
        return True
    
    return False
