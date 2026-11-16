
import numpy as np
from itertools import product

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = len(board)
    board_np = np.array(board)
    empty_cells = [(x, y, z) for x, y, z in product(range(n), repeat=3) if board[x][y][z] == 0]
    
    # Check all possible lines (rows, columns, depths, and diagonals)
    lines = []
    
    # Add all rows, columns, and depths
    for dim in range(3):
        for i in range(n):
            for j in range(n):
                lines.append([(i, j, k) if dim == 0 else 
                             (j, i, k) if dim == 1 else 
                             (j, k, i) for k in range(n)])
    
    # Add all face diagonals
    for dim in range(3):
        for i in range(n):
            lines.append([(i, j, j) for j in range(n)])
            lines.append([(i, j, n-1-j) for j in range(n)])
            lines.append([(j, i, j) for j in range(n)])
            lines.append([(j, i, n-1-j) for j in range(n)])
            lines.append([(j, j, i) for j in range(n)])
            lines.append([(j, n-1-j, i) for j in range(n)])
    
    # Add all space diagonals
    lines.append([(i, i, i) for i in range(n)])
    lines.append([(i, i, n-1-i) for i in range(n)])
    lines.append([(i, n-1-i, i) for i in range(n)])
    lines.append([(n-1-i, i, i) for i in range(n)])
    
    # First, check if we can win immediately
    for line in lines:
        values = [board[x][y][z] for (x, y, z) in line]
        if values.count(1) == n-1 and values.count(0) == 1:
            index = values.index(0)
            return line[index]
    
    # Second, block opponent from winning immediately
    for line in lines:
        values = [board[x][y][z] for (x, y, z) in line]
        if values.count(-1) == n-1 and values.count(0) == 1:
            index = values.index(0)
            return line[index]
    
    # Third, try to create a line with multiple possibilities
    best_score = -1
    best_move = empty_cells[0]
    
    for move in empty_cells:
        x, y, z = move
        score = 0
        
        # Check all lines through this cell
        for line in lines:
            if move not in line:
                continue
                
            values = [board[x][y][z] for (x, y, z) in line]
            if 1 not in values and -1 not in values:
                # Empty line
                score += 1
            elif -1 not in values:
                # Our line
                score += 2 * values.count(1)
        
        # Prefer center positions (strategic for 3D TTT)
        center_distance = abs(x - 1.5) + abs(y - 1.5) + abs(z - 1.5)
        score += (3 - center_distance)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
