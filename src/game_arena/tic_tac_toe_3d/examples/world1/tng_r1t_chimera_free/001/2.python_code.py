
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines (rows, columns, depths, face and space diagonals)
    lines = []
    
    # Rows (for each z-layer and x-row, y varies)
    for z in range(3):
        for x in range(3):
            lines.append([(x, y, z) for y in range(3)])
    
    # Columns (for each z-layer and y-column, x varies)
    for z in range(3):
        for y in range(3):
            lines.append([(x, y, z) for x in range(3)])
    
    # Depth lines (for each x and y, z varies)
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    
    # Face diagonals (two per z-layer)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Space diagonals (four in total)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    # Find all winning and blocking moves
    winning_moves = []
    blocking_moves = []
    
    for line in lines:
        values = [board[z][x][y] for (x, y, z) in line]
        count_1 = sum(1 for v in values if v == 1)
        count_neg1 = sum(1 for v in values if v == -1)
        zeros = [(x, y, z) for (x, y, z) in line if board[z][x][y] == 0]
        
        if len(zeros) == 1:
            (x, y, z) = zeros[0]
            coord = (z, x, y)
            if count_1 == 2 and coord not in winning_moves:
                winning_moves.append(coord)
            elif count_neg1 == 2 and coord not in blocking_moves:
                blocking_moves.append(coord)
    
    # Return winning move if available
    if winning_moves:
        return winning_moves[0]
    
    # Return blocking move if available
    if blocking_moves:
        return blocking_moves[0]
    
    # Collect all empty cells and prioritize them
    empty_cells = []
    for z in range(3):
        for x in range(3):
            for y in range(3):
                if board[z][x][y] == 0:
                    empty_cells.append((z, x, y))
    
    # Define priority: center > corners > edges > face centers
    def cell_priority(cell):
        z, x, y = cell
        if (z, x, y) == (1, 1, 1):
            return 0  # Highest priority
        if all(c in {0, 2} for c in (z, x, y)):
            return 1  # Corner
        edge_count = sum(1 for c in (z, x, y) if c == 1)
        if edge_count == 1:
            return 2  # Edge
        if edge_count == 2:
            return 3  # Face center
        return 4
    
    # Sort empty cells by priority and return the best option
    empty_cells.sort(key=cell_priority)
    return empty_cells[0]
