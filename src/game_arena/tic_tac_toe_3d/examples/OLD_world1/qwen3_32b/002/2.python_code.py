
WIN_LINES = []

# Generate all lines for 3x3x3 Tic Tac Toe

# Lines along x-axis (varying x)
for y in range(3):
    for z in range(3):
        WIN_LINES.append([(x, y, z) for x in range(3)])

# Lines along y-axis (varying y)
for x in range(3):
    for z in range(3):
        WIN_LINES.append([(x, y, z) for y in range(3)])

# Lines along z-axis (varying z)
for x in range(3):
    for y in range(3):
        WIN_LINES.append([(x, y, z) for z in range(3)])

# Face diagonals - planes perpendicular to x-axis (fixed x)
for x in range(3):
    WIN_LINES.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
    WIN_LINES.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])

# Face diagonals - planes perpendicular to y-axis (fixed y)
for y in range(3):
    WIN_LINES.append([(0, y, 0), (1, y, 1), (2, y, 2)])
    WIN_LINES.append([(0, y, 2), (1, y, 1), (2, y, 0)])

# Face diagonals - planes perpendicular to z-axis (fixed z)
for z in range(3):
    WIN_LINES.append([(0, 0, z), (1, 1, z), (2, 2, z)])
    WIN_LINES.append([(0, 2, z), (1, 1, z), (2, 0, z)])

# Space diagonals
WIN_LINES.extend([
    [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
    [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
    [(0, 2, 0), (1, 1, 1), (2, 0, 0)],
    [(0, 2, 2), (1, 1, 1), (2, 0, 0)]
])

def is_win(board, player):
    for line in WIN_LINES:
        if all(board[x][y][z] == player for (x, y, z) in line):
            return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Find all empty cells
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append((x, y, z))

    # Step 1: Check if any move leads to a win
    for cell in empty_cells:
        x, y, z = cell
        original = board[x][y][z]
        board[x][y][z] = 1
        if is_win(board, 1):
            board[x][y][z] = 0
            return cell
        board[x][y][z] = original  # revert

    # Step 2: Check if opponent can win in their next move, block
    for cell in empty_cells:
        x, y, z = cell
        original = board[x][y][z]
        board[x][y][z] = -1
        if is_win(board, -1):
            board[x][y][z] = 0
            return cell
        board[x][y][z] = original  # revert

    # Step 3: take center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Step 4: take any corner
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for corner in corners:
        x, y, z = corner
        if board[x][y][z] == 0:
            return corner

    # Step 5: choose cell with most lines
    best_cell = None
    max_score = -1
    for cell in empty_cells:
        x, y, z = cell
        score = 0
        for line in WIN_LINES:
            if (x, y, z) in line:
                score += 1
        if score > max_score:
            max_score = score
            best_cell = cell
    if best_cell is not None:
        return best_cell
    else:
        # fallback to first empty cell
        return empty_cells[0]
