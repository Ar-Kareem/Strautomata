
import numpy as np
from typing import Optional, Tuple

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Check for immediate winning moves or blocks
    move = find_winning_move(board_array, player=1)
    if move is not None:
        return move
    
    move = find_winning_move(board_array, player=-1)
    if move is not None:
        return move
    
    # Try to take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Try to take a corner if available
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for row, col in corners:
        if board[row][col] == 0:
            return (row, col)
    
    # Take any available edge
    edges = [(0,1), (1,0), (1,2), (2,1)]
    for row, col in edges:
        if board[row][col] == 0:
            return (row, col)
    
    # Fallback (shouldn't happen in a valid game)
    return next_empty_cell(board)

def find_winning_move(board: np.ndarray, player: int) -> Optional[Tuple[int, int]]:
    """Check if there's a winning move for the given player."""
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:
                # Simulate making this move
                board[i, j] = player
                if check_winner(board) == player:
                    board[i, j] = 0  # undo simulation
                    return (i, j)
                board[i, j] = 0  # undo simulation
    return None

def check_winner(board: np.ndarray) -> Optional[int]:
    """Check if the board has a winner. Returns the player number if won, None otherwise."""
    # Check rows
    for row in range(3):
        if board[row, 0] == board[row, 1] == board[row, 2] != 0:
            return board[row, 0]
    
    # Check columns
    for col in range(3):
        if board[0, col] == board[1, col] == board[2, col] != 0:
            return board[0, col]
    
    # Check diagonals
    if board[0, 0] == board[1, 1] == board[2, 2] != 0:
        return board[0, 0]
    if board[0, 2] == board[1, 1] == board[2, 0] != 0:
        return board[0, 2]
    
    return None

def next_empty_cell(board: list[list[int]]) -> Tuple[int, int]:
    """Returns the first empty cell found (fallback)."""
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)  # should never reach here in valid game
