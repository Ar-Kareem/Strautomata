
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier handling
    board_np = np.array(board)
    
    # Generate all possible winning lines in 3D tic-tac-toe
    winning_lines = []
    
    # Rows in each layer
    for z in range(3):
        for y in range(3):
            line = [(z, y, x) for x in range(3)]
            winning_lines.append(line)
    
    # Columns in each layer
    for z in range(3):
        for x in range(3):
            line = [(z, y, x) for y in range(3)]
            winning_lines.append(line)
    
    # Depths through layers
    for y in range(3):
        for x in range(3):
            line = [(z, y, x) for z in range(3)]
            winning_lines.append(line)
    
    # Diagonals within each layer (z constant)
    for z in range(3):
        # Main diagonal
        line = [(z, i, i) for i in range(3)]
        winning_lines.append(line)
        # Anti-diagonal
        line = [(z, i, 2-i) for i in range(3)]
        winning_lines.append(line)
    
    # Diagonals through layers (x or y constant)
    for fixed in range(3):
        # Diagonal through z, fixed x
        line = [(z, z, fixed) for z in range(3)]
        winning_lines.append(line)
        line = [(z, 2-z, fixed) for z in range(3)]
        winning_lines.append(line)
        # Diagonal through z, fixed y
        line = [(z, fixed, z) for z in range(3)]
        winning_lines.append(line)
        line = [(z, fixed, 2-z) for z in range(3)]
        winning_lines.append(line)
    
    # Diagonals through all three dimensions
    # Main space diagonal
    line = [(i, i, i) for i in range(3)]
    winning_lines.append(line)
    line = [(i, i, 2-i) for i in range(3)]
    winning_lines.append(line)
    line = [(i, 2-i, i) for i in range(3)]
    winning_lines.append(line)
    line = [(i, 2-i, 2-i) for i in range(3)]
    winning_lines.append(line)
    
    # Find all empty cells
    empty_cells = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board_np[z, y, x] == 0:
                    empty_cells.append((z, y, x))
    
    # If no empty cells, return invalid (shouldn't happen)
    if not empty_cells:
        return (0, 0, 0)
    
    # Check if we can win immediately
    for line in winning_lines:
        values = [board_np[z, y, x] for z, y, x in line]
        if values.count(1) == 2 and values.count(0) == 1:
            # We can win! Find the empty spot
            for z, y, x in line:
                if board_np[z, y, x] == 0:
                    return (z, y, x)
    
    # Check if we need to block opponent from winning
    for line in winning_lines:
        values = [board_np[z, y, x] for z, y, x in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            # Need to block! Find the empty spot
            for z, y, x in line:
                if board_np[z, y, x] == 0:
                    return (z, y, x)
    
    # No immediate win or block needed, use strategy
    # Prefer center
    if board_np[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Prefer corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    
    for corner in corners:
        z, y, x = corner
        if board_np[z, y, x] == 0:
            return corner
    
    # Otherwise, pick first available empty cell
    return empty_cells[0]
