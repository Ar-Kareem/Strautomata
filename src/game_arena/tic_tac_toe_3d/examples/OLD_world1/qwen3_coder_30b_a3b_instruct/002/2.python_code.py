
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determine the next move for 3D Tic Tac Toe using a simple heuristic.
    
    The algorithm prioritizes:
    1. Winning moves
    2. Blocking opponent wins
    3. Center control
    4. Corner positions
    5. Random valid move
    
    Args:
        board: 3x3x3 list representing the game state
        
    Returns:
        Tuple of (x, y, z) coordinates for the next move
    """
    
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    n = 3
    
    # Helper function to check if a position is valid and empty
    def is_valid_and_empty(x, y, z):
        return (0 <= x < n and 0 <= y < n and 0 <= z < n and 
                board_array[x, y, z] == 0)
    
    # Helper function to check if a line sums to target (win condition)
    def check_line_sum(line, target):
        return sum(line) == target
    
    # Check for winning moves
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_array[x, y, z] == 0:  # Empty cell
                    # Temporarily make the move
                    board_array[x, y, z] = 1
                    
                    # Check if this creates a win
                    # Check rows, columns, and diagonals in each layer
                    if (check_line_sum(board_array[x, y, :], 3) or  # row
                        check_line_sum(board_array[x, :, z], 3) or  # column
                        check_line_sum(board_array[:, y, z], 3) or  # depth
                        # Check diagonals in each layer
                        (x == y == z and check_line_sum([board_array[i, i, i] for i in range(n)], 3)) or
                        (x == y and x == n-1-z and check_line_sum([board_array[i, i, n-1-i] for i in range(n)], 3)) or
                        (x == z and x == n-1-y and check_line_sum([board_array[i, n-1-i, i] for i in range(n)], 3)) or
                        (y == z and y == n-1-x and check_line_sum([board_array[n-1-i, i, i] for i in range(n)], 3))):
                        board_array[x, y, z] = 0  # Reset
                        return (x, y, z)
                    
                    board_array[x, y, z] = 0  # Reset
    
    # Check for blocking moves
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_array[x, y, z] == 0:  # Empty cell
                    # Temporarily make the opponent's move
                    board_array[x, y, z] = -1
                    
                    # Check if this creates an opponent win
                    # Check rows, columns, and diagonals in each layer
                    if (check_line_sum(board_array[x, y, :], -3) or  # row
                        check_line_sum(board_array[x, :, z], -3) or  # column
                        check_line_sum(board_array[:, y, z], -3) or  # depth
                        # Check diagonals in each layer
                        (x == y == z and check_line_sum([board_array[i, i, i] for i in range(n)], -3)) or
                        (x == y and x == n-1-z and check_line_sum([board_array[i, i, n-1-i] for i in range(n)], -3)) or
                        (x == z and x == n-1-y and check_line_sum([board_array[i, n-1-i, i] for i in range(n)], -3)) or
                        (y == z and y == n-1-x and check_line_sum([board_array[n-1-i, i, i] for i in range(n)], -3))):
                        board_array[x, y, z] = 0  # Reset
                        return (x, y, z)
                    
                    board_array[x, y, z] = 0  # Reset
    
    # If center is available, take it
    center = n // 2
    if is_valid_and_empty(center, center, center):
        return (center, center, center)
    
    # If corners are available, take them (prioritize corners with high value)
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for x, y, z in corners:
        if is_valid_and_empty(x, y, z):
            return (x, y, z)
    
    # If edge positions are available, take them
    edges = [(0,0,1), (0,1,0), (0,1,2), (0,2,1), (1,0,0), (1,0,2), (1,2,0), (1,2,2), (2,0,1), (2,1,0), (2,1,2), (2,2,1)]
    for x, y, z in edges:
        if is_valid_and_empty(x, y, z):
            return (x, y, z)
    
    # Fallback: Select any available position
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_array[x, y, z] == 0:
                    return (x, y, z)
    
    # Should never reach here in a valid game
    return (0, 0, 0)
