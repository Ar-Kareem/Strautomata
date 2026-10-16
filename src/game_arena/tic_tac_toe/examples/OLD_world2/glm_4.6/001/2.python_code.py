
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game.
    
    Args:
        board: A 4x4 list of lists containing 0 (empty), 1 (you), and -1 (opponent).
    
    Returns:
        A tuple (row, col) indicating the chosen move (0-3 for both).
    """
    # First, check if we can win in the next move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    return (i, j)
                board[i][j] = 0
    
    # Then, check if we need to block the opponent from winning
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 1
                    return (i, j)
                board[i][j] = 0
    
    # Prioritize center and corners
    # Center is (1,1), (1,2), (2,1), (2,2)
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    available_centers = [(i,j) for (i,j) in center_positions if board[i][j] == 0]
    if available_centers:
        return random.choice(available_centers)
    
    # Then corners
    corners = [(0,0), (0,3), (3,0), (3,3)]
    available_corners = [(i,j) for (i,j) in corners if board[i][j] == 0]
    if available_corners:
        return random.choice(available_corners)
    
    # Finally, pick a random empty spot
    empty_spots = [(i,j) for i in range(4) for j in range(4) if board[i][j] == 0]
    if empty_spots:
        return random.choice(empty_spots)
    
    # No moves available (shouldn't happen in a valid game)
    return (0,0)

def check_win(board: List[List[int]], player: int) -> bool:
    """Check if the given player has won."""
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    
    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3-i] == player for i in range(4)):
        return True
    
    return False
