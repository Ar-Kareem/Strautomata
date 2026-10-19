
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Check if we can win in one move
    move = find_winning_move(board_array, 1)
    if move:
        return move
    
    # Check if we need to block opponent's winning move
    move = find_winning_move(board_array, -1)
    if move:
        return move
    
    # If center is available, take it
    if board_array[1, 1] == 0:
        return (1, 1)
    
    # Check corners (preferred positions)
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(r, c) for r, c in corners if board_array[r, c] == 0]
    if available_corners:
        return available_corners[0]
    
    # Take any available side position
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_sides = [(r, c) for r, c in sides if board_array[r, c] == 0]
    if available_sides:
        return available_sides[0]
    
    # This shouldn't happen in a valid game, but return first empty spot
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                return (i, j)
    
    # If no moves left (shouldn't happen), return center
    return (1, 1)

def find_winning_move(board: np.ndarray, player: int) -> None:
    """Find a winning move for the given player, or None if none exists."""
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:  # Empty spot
                # Try placing player's mark here
                board[i, j] = player
                
                # Check if this creates a win
                if check_win(board, player):
                    board[i, j] = 0  # Reset the board
                    return (i, j)
                
                # Reset the board
                board[i, j] = 0
    
    return None

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the given player has won."""
    # Check rows
    for i in range(3):
        if all(board[i, j] == player for j in range(3)):
            return True
    
    # Check columns
    for j in range(3):
        if all(board[i, j] == player for i in range(3)):
            return True
    
    # Check diagonals
    if all(board[i, i] == player for i in range(3)):
        return True
    
    if all(board[i, 2-i] == player for i in range(3)):
        return True
    
    return False
