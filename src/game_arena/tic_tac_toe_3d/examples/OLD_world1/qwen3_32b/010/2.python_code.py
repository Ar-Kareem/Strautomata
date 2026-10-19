
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all lines in the 3x3x3 cube
    lines = []
    
    # Lines along z-axis (fixed x, y)
    for x in range(3):
        for y in range(3):
            line = [(x, y, z) for z in range(3)]
            lines.append(line)
    
    # Lines along y-axis (fixed x, z)
    for x in range(3):
        for z in range(3):
            line = [(x, y, z) for y in range(3)]
            lines.append(line)
    
    # Lines along x-axis (fixed y, z)
    for y in range(3):
        for z in range(3):
            line = [(x, y, z) for x in range(3)]
            lines.append(line)
    
    # Diagonals on each z-layer face
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Diagonals on each x-layer face
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Diagonals on each y-layer face
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    
    # Space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    # Step 1: Check for immediate winning move
    for line in lines:
        cells = [board[x][y][z] for x, y, z in line]
        if cells.count(1) == 2 and cells.count(0) == 1:
            for i in range(3):
                if cells[i] == 0:
                    return line[i]
    
    # Step 2: Check for opponent's winning move and block
    for line in lines:
        cells = [board[x][y][z] for x, y, z in line]
        if cells.count(-1) == 2 and cells.count(0) == 1:
            for i in range(3):
                if cells[i] == 0:
                    return line[i]
    
    # Helper to get all empty cells
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append((x, y, z))
    
    # Step 3: Heuristic - pick center, then corners, then first available
    if (1, 1, 1) in empty_cells:
        return (1, 1, 1)
    
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        if corner in empty_cells:
            return corner
    
    return empty_cells[0]
