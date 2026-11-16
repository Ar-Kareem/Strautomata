
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines (each line is a list of (z, y, x) tuples)
    lines = []
    
    # Planar lines (each layer)
    for z in range(3):
        # Rows
        for y in range(3):
            lines.append([(z, y, x) for x in range(3)])
        # Columns
        for x in range(3):
            lines.append([(z, y, x) for y in range(3)])
        # Diagonals
        lines.append([(z, i, i) for i in range(3)])
        lines.append([(z, i, 2 - i) for i in range(3)])
    
    # Vertical lines (through layers)
    for y in range(3):
        for x in range(3):
            lines.append([(z, y, x) for z in range(3)])
    
    # Space diagonals
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2 - i) for i in range(3)])
    lines.append([(i, 2 - i, i) for i in range(3)])
    lines.append([(i, 2 - i, 2 - i) for i in range(3)])
    
    # Check for winning move (two 1s and a 0)
    for line in lines:
        z1, y1, x1 = line[0]
        z2, y2, x2 = line[1]
        z3, y3, x3 = line[2]
        a, b, c = board[z1][y1][x1], board[z2][y2][x2], board[z3][y3][x3]
        if a + b + c == 2:
            for (z, y, x) in line:
                if board[z][y][x] == 0:
                    return (x, y, z)
    
    # Check for blocking move (two -1s and a 0)
    for line in lines:
        z1, y1, x1 = line[0]
        z2, y2, x2 = line[1]
        z3, y3, x3 = line[2]
        a, b, c = board[z1][y1][x1], board[z2][y2][x2], board[z3][y3][x3]
        if a + b + c == -2:
            for (z, y, x) in line:
                if board[z][y][x] == 0:
                    return (x, y, z)
    
    # Take center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Take a corner if available
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    random.shuffle(corners)  # Randomize to avoid predictability
    for (z, y, x) in corners:
        if board[z][y][x] == 0:
            return (x, y, z)
    
    # Take any available cell
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    return (x, y, z)
    
    # Fallback (shouldn't reach here)
    return (0, 0, 0)
