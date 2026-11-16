
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines in a 3x3x3 grid
    lines = []
    
    # Straight lines along each axis
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    
    # Face diagonals
    for z in range(3):
        lines.append([(i, i, z) for i in range(3)])
        lines.append([(i, 2 - i, z) for i in range(3)])
    for y in range(3):
        lines.append([(i, y, i) for i in range(3)])
        lines.append([(i, y, 2 - i) for i in range(3)])
    for x in range(3):
        lines.append([(x, i, i) for i in range(3)])
        lines.append([(x, i, 2 - i) for i in range(3)])
    
    # Space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    # Find all empty cells
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    
    # Check for immediate winning moves
    winning_moves = []
    for line in lines:
        values = [board[i][j][k] for (i, j, k) in line]
        if values.count(1) == 2 and values.count(0) == 1:
            for (i, j, k) in line:
                if board[i][j][k] == 0:
                    winning_moves.append((i, j, k))
    if winning_moves:
        return winning_moves[0]
    
    # Check for opponent's winning moves to block
    blocking_moves = []
    for line in lines:
        values = [board[i][j][k] for (i, j, k) in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            for (i, j, k) in line:
                if board[i][j][k] == 0:
                    blocking_moves.append((i, j, k))
    if blocking_moves:
        return blocking_moves[0]
    
    # Precompute lines that each cell belongs to
    from collections import defaultdict
    cell_lines = defaultdict(list)
    for line in lines:
        for cell in line:
            cell_lines[cell].append(line)
    
    # Score cells based on strategic value
    max_score = -1
    best_cell = empty_cells[0]
    for cell in empty_cells:
        i, j, k = cell
        score = 0
        
        # Prioritize center
        if (i, j, k) == (1, 1, 1):
            score += 3
        # Prioritize corners
        elif all(c in {0, 2} for c in (i, j, k)):
            score += 1
        
        # Evaluate potential lines
        for line in cell_lines[cell]:
            values = [board[x][y][z] for (x, y, z) in line]
            if -1 in values:
                continue  # Opponent has already blocked this line
            ones = values.count(1)
            zeros = values.count(0)
            if ones == 1 and zeros == 2:
                score += 2
        
        # Update best cell
        if score > max_score or (score == max_score and cell == (1, 1, 1)):
            max_score = score
            best_cell = cell
    
    return best_cell
