
import numpy as np
from itertools import product
from typing import Optional

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """Returns the best move for the current player (1) on the 3D board."""
    n = len(board)
    if n != 3:
        raise ValueError("This AI only supports 3x3x3 boards")
    
    # Check if the board is empty (first move optimization)
    if is_board_empty(board):
        return (0, 0, 0)  # Optimal first move in corner
    
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    best_score = -float('inf')
    best_move = None
    
    # Get all empty positions
    empty_positions = [(x, y, z) for x, y, z in product(range(n), repeat=3) 
                      if board[x][y][z] == 0]
    
    # If only one move left, return it immediately
    if len(empty_positions) == 1:
        return empty_positions[0]
    
    for move in empty_positions:
        x, y, z = move
        # Make the move
        board_array[x][y][z] = 1
        # Calculate score for this move
        score = minimax(board_array, 0, False, -float('inf'), float('inf'))
        # Undo the move
        board_array[x][y][z] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float) -> float:
    """Minimax algorithm with alpha-beta pruning for 3D Tic Tac Toe."""
    result = check_winner(board)
    if result is not None:
        return result * (10 - depth)  # Favor faster wins
    
    n = board.shape[0]
    
    if is_maximizing:
        best_score = -float('inf')
        for x, y, z in product(range(n), repeat=3):
            if board[x][y][z] == 0:
                board[x][y][z] = 1
                score = minimax(board, depth+1, False, alpha, beta)
                board[x][y][z] = 0
                best_score = max(score, best_score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
        return best_score
    else:
        best_score = float('inf')
        for x, y, z in product(range(n), repeat=3):
            if board[x][y][z] == 0:
                board[x][y][z] = -1
                score = minimax(board, depth+1, True, alpha, beta)
                board[x][y][z] = 0
                best_score = min(score, best_score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
        return best_score

def check_winner(board: np.ndarray) -> Optional[int]:
    """Check if there's a winner in the 3D board. Returns 1 for player 1 win, -1 for player 2 win, 0 for draw, None if game continues."""
    n = board.shape[0]
    
    # Check all possible lines
    # 1. Check straight lines in x, y, z directions
    for i, j in product(range(n), repeat=2):
        # x-line (y and z fixed)
        if abs(sum(board[:, i, j])) == n:
            return np.sign(board[0, i, j])
        # y-line (x and z fixed)
        if abs(sum(board[i, :, j])) == n:
            return np.sign(board[i, 0, j])
        # z-line (x and y fixed)
        if abs(sum(board[i, j, :])) == n:
            return np.sign(board[i, j, 0])
    
    # 2. Check face diagonals (6 faces, 2 diagonals each)
    # Front and back face diagonals (z=0 and z=2)
    for z in [0, n-1]:
        # Main diagonal
        if abs(sum(board[i, i, z] for i in range(n))) == n:
            return np.sign(board[0, 0, z])
        # Anti-diagonal
        if abs(sum(board[i, n-1-i, z] for i in range(n))) == n:
            return np.sign(board[0, n-1, z])
    
    # Left and right face diagonals (x=0 and x=2)
    for x in [0, n-1]:
        # Main diagonal
        if abs(sum(board[x, i, i] for i in range(n))) == n:
            return np.sign(board[x, 0, 0])
        # Anti-diagonal
        if abs(sum(board[x, i, n-1-i] for i in range(n))) == n:
            return np.sign(board[x, 0, n-1])
    
    # Top and bottom face diagonals (y=0 and y=2)
    for y in [0, n-1]:
        # Main diagonal
        if abs(sum(board[i, y, i] for i in range(n))) == n:
            return np.sign(board[0, y, 0])
        # Anti-diagonal
        if abs(sum(board[i, y, n-1-i] for i in range(n))) == n:
            return np.sign(board[0, y, n-1])
    
    # 3. Check space diagonals (4 total)
    if abs(sum(board[i, i, i] for i in range(n))) == n:
        return np.sign(board[0, 0, 0])
    if abs(sum(board[i, i, n-1-i] for i in range(n))) == n:
        return np.sign(board[0, 0, n-1])
    if abs(sum(board[i, n-1-i, i] for i in range(n))) == n:
        return np.sign(board[0, n-1, 0])
    if abs(sum(board[n-1-i, i, i] for i in range(n))) == n:
        return np.sign(board[n-1, 0, 0])
    
    # Check if board is full (draw)
    if 0 not in board:
        return 0
    
    # Game continues
    return None

def is_board_empty(board: list[list[list[int]]]) -> bool:
    """Check if the entire board is empty."""
    return all(cell == 0 for layer in board for row in layer for cell in row)
