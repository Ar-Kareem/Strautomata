
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determine the next move for 4x4 Tic Tac Toe.
    
    Strategy:
    1. Check for immediate win
    2. Block opponent's immediate win
    3. Check for potential forks (two winning threats)
    4. Take center positions
    5. Take corners
    6. Take any available position
    
    Returns: (row, col) tuple of the chosen move
    """
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Check for winning move
    move = find_winning_move(board_np, 1)
    if move:
        return move
    
    # Block opponent's winning move
    move = find_winning_move(board_np, -1)
    if move:
        return move
    
    # Look for fork opportunities
    move = find_fork_move(board_np, 1)
    if move:
        return move
    
    # Block opponent forks
    move = find_fork_move(board_np, -1)
    if move:
        return move
    
    # Take center positions (positions (1,1), (1,2), (2,1), (2,2))
    center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for pos in center_positions:
        if board_np[pos] == 0:
            return pos
    
    # Take corners
    corner_positions = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for pos in corner_positions:
        if board_np[pos] == 0:
            return pos
    
    # Take any available position
    for i in range(4):
        for j in range(4):
            if board_np[i, j] == 0:
                return (i, j)
    
    # Should never reach here in a valid game
    raise Exception("No valid moves available")

def find_winning_move(board: np.ndarray, player: int) -> Optional[Tuple[int, int]]:
    """Find a move that results in an immediate win for the player."""
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:  # Empty position
                # Temporarily make the move
                board[i, j] = player
                
                # Check if this creates a win
                if check_win(board, player):
                    # Undo the move
                    board[i, j] = 0
                    return (i, j)
                
                # Undo the move
                board[i, j] = 0
    return None

def find_fork_move(board: np.ndarray, player: int) -> Optional[Tuple[int, int]]:
    """Find a move that creates two winning threats (fork)."""
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:  # Empty position
                # Temporarily make the move
                board[i, j] = player
                
                # Count how many winning moves we have after this move
                win_count = 0
                for k in range(4):
                    for l in range(4):
                        if board[k, l] == 0:  # Another empty position
                            # Temporarily make a second move
                            board[k, l] = player
                            
                            # Check if this creates a win
                            if check_win(board, player):
                                win_count += 1
                                
                            # Undo the second move
                            board[k, l] = 0
                
                # Undo the first move
                board[i, j] = 0
                
                # If we have two or more winning moves after this move, it's a fork
                if win_count >= 2:
                    return (i, j)
    return None

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the player has won on the board."""
    # Check rows
    for i in range(4):
        if np.all(board[i, :] == player):
            return True
    
    # Check columns
    for j in range(4):
        if np.all(board[:, j] == player):
            return True
    
    # Check diagonals
    if np.all(np.diag(board) == player):
        return True
    
    if np.all(np.diag(np.fliplr(board)) == player):
        return True
    
    return False
