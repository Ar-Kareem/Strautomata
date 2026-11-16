
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible lines in a 3x3x3 3D Tic Tac Toe cube
    lines = []
    
    # Axis-aligned lines
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])  # z-axis
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])  # y-axis
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])  # x-axis
    
    # Face diagonals
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    # Collect all empty cells
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append((x, y, z))
    
    # Check if any cell is a winning move (for self)
    for cell in empty_cells:
        x, y, z = cell
        for line in lines:
            if cell not in line:
                continue
            win = True
            for (lx, ly, lz) in line:
                if (lx, ly, lz) == (x, y, z):
                    continue
                if board[lx][ly][lz] != 1:
                    win = False
                    break
            if win:
                return (x, y, z)
    
    # Check if any cell will prevent opponent from winning
    for cell in empty_cells:
        x, y, z = cell
        for line in lines:
            if cell not in line:
                continue
            block = True
            for (lx, ly, lz) in line:
                if (lx, ly, lz) == (x, y, z):
                    continue
                if board[lx][ly][lz] != -1:
                    block = False
                    break
            if block:
                return (x, y, z)
    
    # Fallback: choose the cell with the highest strategic importance
    scored_cells = []
    for cell in empty_cells:
        score = 0
        for line in lines:
            if cell in line:
                score += 1
        scored_cells.append((-score, cell))
    
    # Sort and return the best cell based on score
    scored_cells.sort()
    return scored_cells[0][1]
