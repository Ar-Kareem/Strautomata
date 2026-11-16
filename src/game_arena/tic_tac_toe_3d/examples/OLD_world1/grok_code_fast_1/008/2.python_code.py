
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Define all winning lines for 3x3x3 Tic Tac Toe
    lines = []
    
    # XY planes (for each z)
    for z in range(3):
        # Rows (y constant)
        for y in range(3):
            lines.append([(z, y, 0), (z, y, 1), (z, y, 2)])
        # Columns (x constant)
        for x in range(3):
            lines.append([(z, 0, x), (z, 1, x), (z, 2, x)])
        # Diagonals in plane
        lines.append([(z, 0, 0), (z, 1, 1), (z, 2, 2)])
        lines.append([(z, 0, 2), (z, 1, 1), (z, 2, 0)])
    
    # XZ planes (for each y)
    for y in range(3):
        # Lines parallel to x (for each z)
        for z in range(3):
            lines.append([(0, y, z), (1, y, z), (2, y, z)])
        # Lines parallel to z (for each x)
        for x in range(3):
            lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])
        # Diagonals in plane
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    
    # YZ planes (for each x)
    for x in range(3):
        # Lines parallel to y (for each z)
        for z in range(3):
            lines.append([(x, 0, z), (x, 1, z), (x, 2, z)])
        # Lines parallel to z (for each y)
        for y in range(3):
            lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])
        # Diagonals in plane
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    # Get all empty cells
    empties = [
        (z, y, x)
        for z in range(3)
        for y in range(3)
        for x in range(3)
        if board[z][y][x] == 0
    ]
    
    # Check for winning move
    for move in empties:
        z, y, x = move
        for line in lines:
            if move in line:
                others = [p for p in line if p != move]
                if all(board[p[0]][p[1]][p[2]] == 1 for p in others):
                    return move
    
    # Check for blocking move
    for move in empties:
        z, y, x = move
        for line in lines:
            if move in line:
                others = [p for p in line if p != move]
                if all(board[p[0]][p[1]][p[2]] == -1 for p in others):
                    return move
    
    # Otherwise, choose random empty cell
    return random.choice(empties)
