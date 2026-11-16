
# Precompute all winning lines for 3D Tic Tac Toe
WINNING_LINES = []

# Lines parallel to x-axis (for each y and z)
for y in range(3):
    for z in range(3):
        line = [(z, y, 0), (z, y, 1), (z, y, 2)]
        WINNING_LINES.append(line)

# Lines parallel to y-axis (for each x and z)
for x in range(3):
    for z in range(3):
        line = [(z, 0, x), (z, 1, x), (z, 2, x)]
        WINNING_LINES.append(line)

# Lines parallel to z-axis (for each x and y)
for x in range(3):
    for y in range(3):
        line = [(0, y, x), (1, y, x), (2, y, x)]
        WINNING_LINES.append(line)

# Diagonals in xy-plane (for each z)
for z in range(3):
    line1 = [(z, 0, 0), (z, 1, 1), (z, 2, 2)]
    line2 = [(z, 0, 2), (z, 1, 1), (z, 2, 0)]
    WINNING_LINES.append(line1)
    WINNING_LINES.append(line2)

# Diagonals in xz-plane (for each y)
for y in range(3):
    line1 = [(0, y, 0), (1, y, 1), (2, y, 2)]
    line2 = [(0, y, 2), (1, y, 1), (2, y, 0)]
    WINNING_LINES.append(line1)
    WINNING_LINES.append(line2)

# Diagonals in yz-plane (for each x)
for x in range(3):
    line1 = [(0, 0, x), (1, 1, x), (2, 2, x)]
    line2 = [(0, 2, x), (1, 1, x), (2, 0, x)]
    WINNING_LINES.append(line1)
    WINNING_LINES.append(line2)

# Space diagonals
WINNING_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
WINNING_LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
WINNING_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
WINNING_LINES.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

# Precompute the score for each cell based on the number of winning lines it belongs to
CELL_SCORE = {}
for z in range(3):
    for y in range(3):
        for x in range(3):
            score = 0
            for line in WINNING_LINES:
                if (z, y, x) in line:
                    score += 1
            CELL_SCORE[(z, y, x)] = score

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Check for winning moves first
    for line in WINNING_LINES:
        count_my = 0
        count_empty = 0
        empty_cell = None
        for cell in line:
            z, y, x = cell
            if board[z][y][x] == 1:
                count_my += 1
            elif board[z][y][x] == 0:
                count_empty += 1
                empty_cell = cell
        if count_my == 2 and count_empty == 1:
            return empty_cell
    
    # If no winning move, check for blocking moves
    for line in WINNING_LINES:
        count_opponent = 0
        count_empty = 0
        empty_cell = None
        for cell in line:
            z, y, x = cell
            if board[z][y][x] == -1:
                count_opponent += 1
            elif board[z][y][x] == 0:
                count_empty += 1
                empty_cell = cell
        if count_opponent == 2 and count_empty == 1:
            return empty_cell
    
    # If no immediate win or block, choose the move with the highest score
    best_score = -1
    best_cells = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    score = CELL_SCORE[(z, y, x)]
                    if score > best_score:
                        best_score = score
                        best_cells = [(z, y, x)]
                    elif score == best_score:
                        best_cells.append((z, y, x))
    
    # If there are multiple cells with the same best score, choose randomly
    import random
    return random.choice(best_cells)
