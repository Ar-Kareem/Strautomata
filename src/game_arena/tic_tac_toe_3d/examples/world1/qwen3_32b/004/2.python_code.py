
# Precompute all possible winning lines and line counts for each cell
lines = []
# Axis-aligned lines
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
for x in range(3):
    lines.append([(x, y, y) for y in range(3)])
    lines.append([(x, y, 2 - y) for y in range(3)])
for y in range(3):
    lines.append([(x, y, x) for x in range(3)])
    lines.append([(x, y, 2 - x) for x in range(3)])
for z in range(3):
    lines.append([(x, x, z) for x in range(3)])
    lines.append([(x, 2 - x, z) for x in range(3)])
# Space diagonals
lines.append([(i, i, i) for i in range(3)])
lines.append([(i, i, 2 - i) for i in range(3)])
lines.append([(i, 2 - i, i) for i in range(3)])
lines.append([(i, 2 - i, 2 - i) for i in range(3)])

# Compute line counts for each cell
line_counts = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(3)]
for line in lines:
    for (x, y, z) in line:
        line_counts[x][y][z] += 1

def is_winning(board, player):
    for line in lines:
        all_player = True
        for (x, y, z) in line:
            if board[x][y][z] != player:
                all_player = False
                break
        if all_player:
            return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    empty_cells = [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0]
    if not empty_cells:
        return (0, 0, 0)  # Shouldn't happen in valid game

    # Check for winning move
    for (x, y, z) in empty_cells:
        temp_board = [[[cell for cell in row] for row in layer] for layer in board]
        temp_board[x][y][z] = 1
        if is_winning(temp_board, 1):
            return (x, y, z)
    
    # Check for blocking opponent's win
    for (x, y, z) in empty_cells:
        temp_board = [[[cell for cell in row] for row in layer] for layer in board]
        temp_board[x][y][z] = -1
        if is_winning(temp_board, -1):
            return (x, y, z)
    
    # Choose cell with maximum line count heuristic
    best_move = max(empty_cells, key=lambda pos: line_counts[pos[0]][pos[1]][pos[2]])
    return best_move
