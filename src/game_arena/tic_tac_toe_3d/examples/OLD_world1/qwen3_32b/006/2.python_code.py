
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible lines in a 3x3x3 cube
    lines = []

    # Orthogonal lines along the x-axis
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    # Orthogonal lines along the y-axis
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    # Orthogonal lines along the z-axis
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])

    # Face diagonals (x-y plane at each fixed z)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])

    # Face diagonals (x-z plane at each fixed y)
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])

    # Face diagonals (y-z plane at each fixed x)
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])

    # Space diagonals
    space_diagonals = [
        [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 0, 0)]
    ]
    for line in space_diagonals:
        lines.append(line)

    def is_winning_move(x, y, z, player):
        """Check if placing `player` at (x, y, z) wins the game."""
        for line in lines:
            if (x, y, z) in line:
                win = True
                for (xx, yy, zz) in line:
                    if (xx, yy, zz) == (x, y, z):
                        continue
                    if board[xx][yy][zz] != player:
                        win = False
                        break
                if win:
                    return True
        return False

    # --- Step 1: Win if possible
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0 and is_winning_move(x, y, z, 1):
                    return (x, y, z)

    # --- Step 2: Block opponent's winning move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0 and is_winning_move(x, y, z, -1):
                    return (x, y, z)

    # --- Step 3: Choose center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # --- Step 4: Prioritize corners if center is taken, or choose optimal lines
    empty_cells = [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0]

    def is_corner(x, y, z):
        """Determine if a cell is a corner."""
        return x in {0, 2} and y in {0, 2} and z in {0, 2}

    best_cell = None
    best_score = -1

    for cell in empty_cells:
        x, y, z = cell
        score = 0
        for line in lines:
            if cell in line:
                score += 1
        # Tie-breaker: prefer corners if other cells have same score
        if score > best_score or (score == best_score and is_corner(x, y, z) and not is_corner(best_cell[0], best_cell[1], best_cell[2])):
            best_score = score
            best_cell = cell

    return best_cell
