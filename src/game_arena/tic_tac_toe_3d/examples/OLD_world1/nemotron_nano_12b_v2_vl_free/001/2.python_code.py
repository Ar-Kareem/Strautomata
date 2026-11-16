
import copy

# Precompute all possible winning lines in 3D Tic-Tac-Toe (49 lines in total)
lines = []

# Axis-aligned lines (x, y, z directions)
# x-axis lines (fixed y and z)
for y in range(3):
    for z in range(3):
        lines.append([(0, y, z), (1, y, z), (2, y, z)])
# y-axis lines (fixed x and z)
for x in range(3):
    for z in range(3):
        lines.append([(x, y, z) for y in range(3)])
# z-axis lines (fixed x and y)
for x in range(3):
    for y in range(3):
        lines.append([(x, y, z) for z in range(3)])

# Diagonals in each plane (x-y, x-z, y-z)
# X-Y planes (fixed z)
for z in range(3):
    lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
    lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
# X-Z planes (fixed y)
for y in range(3):
    lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
    lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
# Y-Z planes (fixed x)
for x in range(3):
    lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
    lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])

# 3D space diagonals
lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

# Precompute line counts for each cell
line_counts = {}
for line in lines:
    for cell in line:
        line_counts[cell] = line_counts.get(cell, 0) + 1

def check_win(board):
    """Check if the current board state has a winner."""
    for line in lines:
        val = board[line[0][0]][line[0][1]][line[0][2]]
        if val == 0:
            continue
        if all(board[x][y][z] == val for (x, y, z) in line):
            return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Step 1: Check if AI can win by placing a move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    test_board = copy.deepcopy(board)
                    test_board[x][y][z] = 1
                    if check_win(test_board):
                        return (x, y, z)
    
    # Step 2: Check if opponent can win and block
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    test_board = copy.deepcopy(board)
                    test_board[x][y][z] = -1
                    if check_win(test_board):
                        return (x, y, z)
    
    # Step 3: Prioritize center, then use line count heuristic
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append((x, y, z))
    
    # Check if center cell is available
    center = (1, 1, 1)
    if center in empty_cells:
        return center
    
    # Build priority list based on line count
    cell_priority = []
    for cell in empty_cells:
        cnt = line_counts.get(cell, 0)
        cell_priority.append((-cnt, cell[0], cell[1], cell[2]))  # Negative for descending sort
    
    # Sort by priority (highest line count first), then by coordinates to break ties
    cell_priority.sort()
    
    # Return the highest priority cell
    return (cell_priority[0][1], cell_priority[0][2], cell_priority[0][3])
