
# Precompute all possible lines in a 3x3x3 Tic Tac Toe board
lines = []
lines_by_cell = {}

# X-axis lines (fixed y and z)
for z in range(3):
    for y in range(3):
        line = [(z, 0, y), (z, 1, y), (z, 2, y)]
        lines.append(line)

# Y-axis lines (fixed x and z)
for z in range(3):
    for x in range(3):
        line = [(z, x, 0), (z, x, 1), (z, x, 2)]
        lines.append(line)

# Z-axis lines (fixed x and y)
for x in range(3):
    for y in range(3):
        line = [(0, x, y), (1, x, y), (2, x, y)]
        lines.append(line)

# Diagonals in fixed z planes
for z in range(3):
    line = [(z, 0, 0), (z, 1, 1), (z, 2, 2)]
    lines.append(line)
    line = [(z, 0, 2), (z, 1, 1), (z, 2, 0)]
    lines.append(line)

# Diagonals in fixed x planes (y-z planes)
for x in range(3):
    line = [(0, x, 0), (1, x, 1), (2, x, 2)]
    lines.append(line)
    line = [(0, x, 2), (1, x, 1), (2, x, 0)]
    lines.append(line)

# Diagonals in fixed y planes (x-z planes)
for y in range(3):
    line = [(0, 0, y), (1, 1, y), (2, 2, y)]
    lines.append(line)
    line = [(0, 2, y), (1, 1, y), (2, 0, y)]
    lines.append(line)

# Space diagonals
lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

# Build a dictionary mapping each cell to the lines that include it
for line in lines:
    for cell in line:
        if cell not in lines_by_cell:
            lines_by_cell[cell] = []
        lines_by_cell[cell].append(line)

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    empty_cells = []
    for z in range(3):
        for x in range(3):
            for y in range(3):
                if board[z][x][y] == 0:
                    empty_cells.append((z, x, y))
    
    if not empty_cells:
        return (0, 0, 0)
    
    # Check for winning moves
    for cell in empty_cells:
        z0, x0, y0 = cell
        if cell in lines_by_cell:
            for line in lines_by_cell[cell]:
                count_1 = 0
                for c in line:
                    if c == cell:
                        continue
                    z, x, y = c
                    if board[z][x][y] == 1:
                        count_1 += 1
                if count_1 == 2:
                    return cell
    
    # Check for blocking moves
    for cell in empty_cells:
        z0, x0, y0 = cell
        if cell in lines_by_cell:
            for line in lines_by_cell[cell]:
                count_neg1 = 0
                for c in line:
                    if c == cell:
                        continue
                    z, x, y = c
                    if board[z][x][y] == -1:
                        count_neg1 += 1
                if count_neg1 == 2:
                    return cell
    
    # Heuristic evaluation
    scores = {}
    for cell in empty_cells:
        z0, x0, y0 = cell
        score = 0
        if cell in lines_by_cell:
            for line in lines_by_cell[cell]:
                count_1 = 0
                count_neg1 = 0
                for c in line:
                    if c == cell:
                        continue
                    z, x, y = c
                    val = board[z][x][y]
                    if val == 1:
                        count_1 += 1
                    elif val == -1:
                        count_neg1 += 1
                if count_neg1 == 0:
                    score += count_1 * 10
        scores[cell] = score
    
    # Find best cell by score and priority
    best_cell = None
    best_score = -1
    best_priority = -1
    for cell, score in scores.items():
        z0, x0, y0 = cell
        if cell == (1, 1, 1):
            priority = 1000
        elif cell in [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]:
            priority = 100
        elif cell in [(0,1,1), (1,0,1), (1,1,0), (2,1,1), (1,2,1), (1,1,2)]:
            priority = 10
        else:
            priority = 1
        
        if score > best_score or (score == best_score and priority > best_priority):
            best_score = score
            best_priority = priority
            best_cell = cell
    
    if best_cell is not None:
        return best_cell
    else:
        return empty_cells[0]
