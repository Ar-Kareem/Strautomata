
import random
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Check all possible lines (rows, columns, depth, and diagonals)
    lines = []
    
    # Generate all possible winning lines
    # 1. Horizontal lines (3 per layer, 3 layers = 9 lines)
    for z in range(3):
        for y in range(3):
            lines.append([(x, y, z) for x in range(3)])
    
    # 2. Vertical lines (3 per layer, 3 layers = 9 lines)
    for z in range(3):
        for x in range(3):
            lines.append([(x, y, z) for y in range(3)])
    
    # 3. Depth lines (3 per column, 3 columns = 9 lines)
    for y in range(3):
        for x in range(3):
            lines.append([(x, y, z) for z in range(3)])
    
    # 4. Space diagonals
    # Main space diagonals
    lines.append([(i, i, i) for i in range(3)])  # x=y=z
    lines.append([(i, i, 2-i) for i in range(3)])  # x=y, z=2-i
    lines.append([(i, 2-i, i) for i in range(3)])  # x=z, y=2-i
    lines.append([(2-i, i, i) for i in range(3)])  # y=x, z=2-i
    
    # Check for immediate winning moves
    for line in lines:
        values = [board[x][y][z] for x, y, z in line]
        # If I have 2 in a line and can win
        if values.count(1) == 2 and values.count(0) == 1:
            for x, y, z in line:
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    # Check for blocking opponent winning moves
    for line in lines:
        values = [board[x][y][z] for x, y, z in line]
        # If opponent has 2 in a line, block
        if values.count(-1) == 2 and values.count(0) == 1:
            for x, y, z in line:
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    # If no immediate win/block, use pattern-based selection
    # Prefer center > corners > edges
    
    # Center position
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    
    # Try to pick an empty corner
    available_corners = [pos for pos in corners if board[pos[0]][pos[1]][pos[2]] == 0]
    if available_corners:
        return random.choice(available_corners)
    
    # If no corners, pick any empty position
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    # This shouldn't happen - board should have empty spots
    return (0, 0, 0)
