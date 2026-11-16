
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines (49 total)
    all_lines = []
    # Layer rows
    for layer in range(3):
        for row in range(3):
            all_lines.append([(layer, row, col) for col in range(3)])
    # Layer columns
    for layer in range(3):
        for col in range(3):
            all_lines.append([(layer, row, col) for row in range(3)])
    # Layer diagonals
    for layer in range(3):
        all_lines.append([(layer, 0, 0), (layer, 1, 1), (layer, 2, 2)])
        all_lines.append([(layer, 0, 2), (layer, 1, 1), (layer, 2, 0)])
    # Vertical stacks
    for row in range(3):
        for col in range(3):
            all_lines.append([(i, row, col) for i in range(3)])
    # Diagonals in x-z planes
    for y in range(3):
        all_lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        all_lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    # Diagonals in y-z planes
    for x in range(3):
        all_lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        all_lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    # Space diagonals
    all_lines.extend([
        [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 0, 0)]
    ])
    
    # Map cells to their containing lines
    cell_lines = {}
    for i in range(3):
        for j in range(3):
            for k in range(3):
                cell_lines[(i, j, k)] = []
    for line in all_lines:
        for cell in line:
            cell_lines[cell].append(line)
    
    # Find all empty cells
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    if not empty_cells:
        return (0, 0, 0)  # Fallback
    
    best_score = -float('inf')
    best_cell = empty_cells[0]
    
    for cell in empty_cells:
        i, j, k = cell
        score = 0
        
        # Evaluate all lines containing this cell
        for line in cell_lines[cell]:
            values = [board[x][y][z] for (x, y, z) in line]
            count_1 = values.count(1)
            count_neg1 = values.count(-1)
            count_0 = values.count(0)
            
            if count_1 and count_neg1:
                continue  # Blocked line
            
            if count_1 == 2 and count_0 == 1:
                score += 1000  # Winning move
            elif count_neg1 == 2 and count_0 == 1:
                score += 100   # Block opponent win
            elif count_1 == 1 and count_0 == 2:
                score += 10    # Create opportunity
            elif count_neg1 == 1 and count_0 == 2:
                score += 5     # Disrupt opponent
            elif count_1 == 0 and count_neg1 == 0:
                score += 1     # Neutral potential
        
        # Strategic position bonus
        if (i, j, k) == (1, 1, 1):
            score += 20  # Center bonus
        elif all(x in {0, 2} for x in (i, j, k)):
            score += 3   # Corner bonus
        
        # Update best cell
        if score > best_score:
            best_score = score
            best_cell = cell
    
    return best_cell
