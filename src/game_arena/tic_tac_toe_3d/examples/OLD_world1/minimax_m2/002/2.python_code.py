
# Precompute the winning lines for a 3x3x3 3D Tic Tac Toe game
lines = []
directions = [
    (1, 0, 0), (0, 1, 0), (0, 0, 1),
    (1, 1, 0), (1, -1, 0),
    (1, 0, 1), (1, 0, -1),
    (0, 1, 1), (0, 1, -1),
    (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1)
]

for dx, dy, dz in directions:
    for x in range(3):
        for y in range(3):
            for z in range(3):
                x_end = x + 2 * dx
                y_end = y + 2 * dy
                z_end = z + 2 * dz
                if 0 <= x_end < 3 and 0 <= y_end < 3 and 0 <= z_end < 3:
                    line = []
                    for i in range(3):
                        line.append((x + i * dx, y + i * dy, z + i * dz))
                    lines.append(line)

def policy(board):
    # Step 1: Check for our immediate win
    for line in lines:
        count_1 = 0
        for (x, y, z) in line:
            if board[x][y][z] == 1:
                count_1 += 1
        if count_1 == 2:
            for (x, y, z) in line:
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    # Step 2: Check for opponent's immediate win (to block)
    for line in lines:
        count_neg1 = 0
        for (x, y, z) in line:
            if board[x][y][z] == -1:
                count_neg1 += 1
        if count_neg1 == 2:
            for (x, y, z) in line:
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    # Step 3: Compute potential for each empty cell
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append((x, y, z))
    
    if not empty_cells:
        return (0, 0, 0)
    
    potential = {}
    for cell in empty_cells:
        x0, y0, z0 = cell
        count = 0
        for line in lines:
            if cell in line:
                has_one = False
                count_neg1 = 0
                for (x, y, z) in line:
                    if board[x][y][z] == 1:
                        has_one = True
                    elif board[x][y][z] == -1:
                        count_neg1 += 1
                if has_one and count_neg1 < 2:
                    count += 1
        potential[cell] = count
    
    max_potential = max(potential.values())
    candidate_cells = [cell for cell, p in potential.items() if p == max_potential]
    candidate_cells.sort(key=lambda cell: (abs(cell[0]-1) + abs(cell[1]-1) + abs(cell[2]-1), cell))
    return candidate_cells[0]
