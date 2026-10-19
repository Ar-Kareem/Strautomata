
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing our mark here
                board[i][j] = 1
                if check_winner(board) == 1:
                    return (i, j)
                # Undo the move
                board[i][j] = 0
    
    # Block opponent's winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing opponent's mark here
                board[i][j] = -1
                if check_winner(board) == -1:
                    # Block this move
                    board[i][j] = 0
                    return (i, j)
                # Undo the move
                board[i][j] = 0
    
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
    
    # Fallback (shouldn't happen in normal play)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)

def check_winner(board: List[List[int]]) -> int:
    # Check rows
    for row in board:
        if abs(sum(row)) == 3:
            return row[0]
    
    # Check columns
    for col in range(3):
        if abs(sum(board[row][col] for row in range(3))) == 3:
            return board[0][col]
    
    # Check diagonals
    if abs(sum(board[i][i] for i in range(3))) == 3:
        return board[0][0]
    if abs(sum(board[i][2-i] for i in range(3))) == 3:
        return board[0][2]
    
    return 0
