
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    np_board = np.array(board)
    lines = []
    
    # Generate all lines along each axis
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])  # x-axis lines
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])  # y-axis lines
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])  # z-axis lines
    
    # Add layer diagonals (2 per layer)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Add main cube diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    
    # Check for winning moves
    for line in lines:
        values = [np_board[x][y][z] for (x, y, z) in line]
        if values.count(1) == 2 and values.count(0) == 1:
            for (x, y, z) in line:
                if np_board[x][y][z] == 0:
                    return (x, y, z)
    
    # Check for blocking moves
    for line in lines:
        values = [np_board[x][y][z] for (x, y, z) in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            for (x, y, z) in line:
                if np_board[x][y][z] == 0:
                    return (x, y, z)
    
    # Find any empty cell if no threats
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if np_board[x][y][z] == 0:
                    return (x, y, z)
    
    # Fallback: return (0,0,0) if board is full (shouldn't happen)
    return (0, 0, 0)
