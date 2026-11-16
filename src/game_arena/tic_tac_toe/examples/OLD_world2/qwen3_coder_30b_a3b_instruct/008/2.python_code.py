
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game using a simple heuristic.
    
    The policy prioritizes:
    1. Winning moves
    2. Blocking opponent winning moves
    3. Taking the center if available
    4. Taking corners
    5. Taking any available position
    
    Args:
        board: 4x4 list of lists containing 0 (empty), 1 (you), -1 (opponent)
        
    Returns:
        Tuple of (row, col) for the next move (0-3 each)
    """
    # Convert to numpy array for easier manipulation
    np_board = np.array(board)
    
    # Check for winning moves (current player)
    for i in range(4):
        for j in range(4):
            if np_board[i, j] == 0:  # Empty position
                # Temporarily place our mark
                np_board[i, j] = 1
                if check_winner(np_board) == 1:
                    # Found winning move
                    np_board[i, j] = 0  # Reset
                    return (i, j)
                np_board[i, j] = 0  # Reset
    
    # Check for blocking moves (opponent winning)
    for i in range(4):
        for j in range(4):
            if np_board[i, j] == 0:  # Empty position
                # Temporarily place opponent's mark
                np_board[i, j] = -1
                if check_winner(np_board) == -1:
                    # Must block
                    np_board[i, j] = 0  # Reset
                    return (i, j)
                np_board[i, j] = 0  # Reset
    
    # Prefer center positions
    center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for i, j in center_positions:
        if np_board[i, j] == 0:
            return (i, j)
    
    # Prefer corner positions
    corner_positions = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for i, j in corner_positions:
        if np_board[i, j] == 0:
            return (i, j)
    
    # Take any available position
    for i in range(4):
        for j in range(4):
            if np_board[i, j] == 0:
                return (i, j)
    
    # This case should not happen in a valid game
    return (0, 0)

def check_winner(board: np.ndarray) -> int:
    """
    Check if there's a winner in a 4x4 board.
    
    Returns:
        1 if player 1 wins, -1 if player -1 wins, 0 if no winner
    """
    # Check rows
    for i in range(4):
        if np.all(board[i, :] == 1):
            return 1
        elif np.all(board[i, :] == -1):
            return -1
    
    # Check columns
    for j in range(4):
        if np.all(board[:, j] == 1):
            return 1
        elif np.all(board[:, j] == -1):
            return -1
    
    # Check main diagonal
    if np.all(np.diag(board) == 1):
        return 1
    elif np.all(np.diag(board) == -1):
        return -1
    
    # Check anti-diagonal
    if np.all(np.diag(np.fliplr(board)) == 1):
        return 1
    elif np.all(np.diag(np.fliplr(board)) == -1):
        return -1
    
    # No winner
    return 0
