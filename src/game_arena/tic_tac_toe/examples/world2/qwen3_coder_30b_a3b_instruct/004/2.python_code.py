
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Check for winning moves or blocking moves
    empty_positions = []
    
    # Collect all empty positions
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_positions.append((i, j))
    
    # Check for winning moves (current player)
    for i, j in empty_positions:
        # Create a temporary board to test this move
        temp_board = [row[:] for row in board]  # Deep copy
        temp_board[i][j] = 1  # Assume current player's move
        
        # Check if this creates a win
        if check_win(temp_board, 1):
            return (i, j)
    
    # Check for blocking moves (opponent's winning move)
    for i, j in empty_positions:
        # Create a temporary board to test this move
        temp_board = [row[:] for row in board]  # Deep copy
        temp_board[i][j] = -1  # Assume opponent's move
        
        # Check if opponent would win
        if check_win(temp_board, -1):
            return (i, j)
    
    # If no immediate win/block, choose strategically
    # Prefer center positions and corners
    preferred_moves = []
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    corner_positions = [(0,0), (0,3), (3,0), (3,3)]
    
    # Add center positions first
    for pos in center_positions:
        if pos in empty_positions:
            preferred_moves.append(pos)
    
    # Then add corner positions
    for pos in corner_positions:
        if pos in empty_positions:
            preferred_moves.append(pos)
    
    # If we have preferred moves, return one
    if preferred_moves:
        return random.choice(preferred_moves)
    
    # Otherwise, return any valid move
    return random.choice(empty_positions)

def check_win(board: List[List[int]], player: int) -> bool:
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    
    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    
    # Check anti-diagonal
    if all(board[i][3-i] == player for i in range(4)):
        return True
    
    return False
