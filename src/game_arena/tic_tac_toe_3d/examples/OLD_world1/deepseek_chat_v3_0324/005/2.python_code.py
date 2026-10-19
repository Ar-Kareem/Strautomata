
import numpy as np
from itertools import product
from collections import defaultdict

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determine the next move in 3D Tic Tac Toe.
    
    Strategy:
    1. First check for any immediate winning moves
    2. Then check for opponent's winning moves to block
    3. Then look for strategic positions (center, edges, etc.)
    4. Finally choose any available move if no strategy applies
    """
    board = np.array(board)
    size = 3
    
    # Generate all possible lines in 3D space
    def generate_lines():
        lines = []
        # Rows in each layer
        for z in range(size):
            for y in range(size):
                lines.append([(x, y, z) for x in range(size)])
        # Columns in each layer
        for z in range(size):
            for x in range(size):
                lines.append([(x, y, z) for y in range(size)])
        # Depth lines
        for x in range(size):
            for y in range(size):
                lines.append([(x, y, z) for z in range(size)])
        # Diagonals within layers
        for z in range(size):
            lines.append([(x, x, z) for x in range(size)])  # Main diagonal
            lines.append([(x, size-1-x, z) for x in range(size)])  # Anti-diagonal
        # Diagonals across layers
        lines.append([(x, x, x) for x in range(size)])  # Space diagonal
        lines.append([(x, size-1-x, x) for x in range(size)])  # Space anti-diagonal
        lines.append([(x, x, size-1-x) for x in range(size)])  # Another space diagonal
        lines.append([(x, size-1-x, size-1-x) for x in range(size)])  # Another space anti-diagonal
        return lines
    
    lines = generate_lines()
    
    # Check if a move completes a line for the given player
    def check_move(pos, player):
        x, y, z = pos
        if board[x, y, z] != 0:
            return False
        
        # Temporarily make the move
        board[x, y, z] = player
        
        # Check all lines that include this position
        for line in lines:
            if pos in line:
                line_values = [board[p] for p in line]
                if all(v == player for v in line_values):
                    # Undo the move
                    board[x, y, z] = 0
                    return True
        
        # Undo the move
        board[x, y, z] = 0
        return False
    
    # Priority 1: Check for winning moves
    for x, y, z in product(range(size), repeat=3):
        if board[x, y, z] == 0 and check_move((x, y, z), 1):
            return (x, y, z)
    
    # Priority 2: Block opponent's winning moves
    for x, y, z in product(range(size), repeat=3):
        if board[x, y, z] == 0 and check_move((x, y, z), -1):
            return (x, y, z)
    
    # Priority 3: Strategic positions
    # Center is most valuable in 3D Tic Tac Toe
    center = (1, 1, 1)
    if board[center] == 0:
        return center
    
    # Then corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board[corner] == 0:
            return corner
    
    # Then edges
    edges = [(0, 0, 1), (0, 1, 0), (0, 1, 2), (0, 2, 1),
             (1, 0, 0), (1, 0, 2), (1, 2, 0), (1, 2, 2),
             (2, 0, 1), (2, 1, 0), (2, 1, 2), (2, 2, 1),
             (1, 1, 0), (1, 1, 2), (1, 0, 1), (1, 2, 1),
             (0, 1, 1), (2, 1, 1)]
    for edge in edges:
        if board[edge] == 0:
            return edge
    
    # Priority 4: Any available move
    for x, y, z in product(range(size), repeat=3):
        if board[x, y, z] == 0:
            return (x, y, z)
    
    # Shouldn't reach here if board isn't full
    raise ValueError("No valid moves available")
