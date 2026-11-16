
import random
from typing import List, Tuple

def policy(board: List[List[int]], legal_moves: List[int]) -> Tuple[int, int]:
    # Convert legal moves to (row, col) tuples
    legal_coords = [(m // 3, m % 3) for m in legal_moves]
    
    # Check for winning moves
    for row, col in legal_coords:
        if can_win(board, row, col, 1):
            return (row, col)
    
    # Check for blocking moves
    for row, col in legal_coords:
        if can_win(board, row, col, -1):  # -1 represents opponent
            return (row, col)
    
    # Prefer center, then corners, then edges
    priority_order = [
        (1, 1),  # center
        (0, 0), (0, 2), (2, 0), (2, 2),  # corners
        (0, 1), (1, 0), (1, 2), (2, 1)   # edges
    ]
    
    # Filter to legal moves
    priority_legal = [pos for pos in priority_order if pos in legal_coords]
    
    # If we have priority moves, return the first one
    if priority_legal:
        return priority_legal[0]
    
    # Fallback to any legal move
    return legal_coords[0]
    
def can_win(board, row, col, player):
    """Check if placing player at (row, col) creates a win"""
    # Create a temporary board to check for a potential win
    temp_board = [row[:] for row in board]  # deep copy
    temp_board[row][col] = player
    
    # Check rows
    for i in range(3):
        if temp_board[i][0] == temp_board[i][1] == temp_board[i][2] == player:
            return True
    
    # Check columns
    for j in range(3):
        if temp_board[0][j] == temp_board[1][j] == temp_board[2][j] == player:
            return True
    
    # Check diagonals
    if temp_board[0][0] == temp_board[1][1] == temp_board[2][2] == player:
        return True
    if temp_board[0][2] == temp_board[1][1] == temp_board[2][0] == player:
        return True
    
    return False
