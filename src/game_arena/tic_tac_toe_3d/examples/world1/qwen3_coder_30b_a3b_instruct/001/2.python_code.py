
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy for easier manipulation
    board_np = np.array(board)
    
    # Get all possible winning lines (3x3x3 board)
    lines = []
    
    # All rows (3 per layer, 3 layers)
    for z in range(3):
        for y in range(3):
            lines.append([(x, y, z) for x in range(3)])
    
    # All columns (3 per layer, 3 layers)  
    for z in range(3):
        for x in range(3):
            lines.append([(x, y, z) for y in range(3)])
            
    # All depth lines (3 per row/column, 3x3=9 combinations)
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    
    # All main diagonals through each layer
    for z in range(3):
        # Diagonal from (0,0,z) to (2,2,z)
        lines.append([(i, i, z) for i in range(3)])
        # Diagonal from (0,2,z) to (2,0,z)
        lines.append([(i, 2-i, z) for i in range(3)])
        
    # 4 main space diagonals
    lines.append([(i, i, i) for i in range(3)])  # From (0,0,0) to (2,2,2)
    lines.append([(i, i, 2-i) for i in range(3)])  # From (0,0,2) to (2,2,0)
    lines.append([(i, 2-i, i) for i in range(3)])  # From (0,2,0) to (2,0,2)
    lines.append([(2-i, i, i) for i in range(3)])  # From (2,0,0) to (0,2,2)
    
    # Look for immediate winning moves
    for line_coords in lines:
        values = [board_np[x][y][z] for x, y, z in line_coords]
        if values.count(1) == 2 and values.count(0) == 1:
            # I can win
            empty_idx = values.index(0)
            return line_coords[empty_idx]
    
    # Look for blocking moves
    for line_coords in lines:
        values = [board_np[x][y][z] for x, y, z in line_coords]
        if values.count(-1) == 2 and values.count(0) == 1:
            # Opponent can win, block
            empty_idx = values.index(0)
            return line_coords[empty_idx]
    
    # If center is available, take it
    if board_np[1][1][1] == 0:
        return (1, 1, 1)
    
    # Take corners if available  
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), 
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for x, y, z in corners:
        if board_np[x][y][z] == 0:
            return (x, y, z)
    
    # Take edges if available
    edges = [(0,0,1), (0,1,0), (0,1,2), (0,2,1),
             (1,0,0), (1,0,2), (1,2,0), (1,2,2),
             (2,0,1), (2,1,0), (2,1,2), (2,2,1)]
    for x, y, z in edges:
        if board_np[x][y][z] == 0:
            return (x, y, z)
    
    # Otherwise, take the first empty spot
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_np[x][y][z] == 0:
                    return (x, y, z)
    
    # This shouldn't happen in valid game state
    return (0, 0, 0)
