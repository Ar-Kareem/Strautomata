
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def generate_lines():
        lines = []
        # Axial lines along x
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        # Axial lines along y
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        # Axial lines along z
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        # Face diagonals perpendicular to x-axis
        for x in range(3):
            lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
            lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
        # Face diagonals perpendicular to y-axis
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        # Face diagonals perpendicular to z-axis
        for z in range(3):
            lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
            lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
        # Space diagonals
        space_diagonals = [
            [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
            [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
            [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
            [(0, 2, 2), (1, 1, 1), (2, 0, 0)],
        ]
        lines.extend(space_diagonals)
        return lines

    # Step 1: Generate all possible lines in the 3x3x3 cube
    lines = generate_lines()

    # Step 2: Attempt to win
    for line in lines:
        values = [board[x][y][z] for x, y, z in line]
        if sum(values) == 2 and 0 in values:
            for x, y, z in line:
                if board[x][y][z] == 0:
                    return (x, y, z)

    # Step 3: Block opponent's potential win
    for line in lines:
        values = [board[x][y][z] for x, y, z in line]
        if sum(values) == -2 and 0 in values:
            for x, y, z in line:
                if board[x][y][z] == 0:
                    return (x, y, z)

    # Step 4: Heuristic move selection

    # Precompute list of prioritized cells
    preference_order = []
    preference_order.append((1, 1, 1))

    # Add corners
    for x in [0, 2]:
        for y in [0, 2]:
            for z in [0, 2]:
                preference_order.append((x, y, z))

    # Add face centers
    face_centers = []
    for axis in range(3):
        for i in [0, 2]:
            for j in [0, 2]:
                if axis == 0:
                    face_centers.append((1, i, j))
                elif axis == 1:
                    face_centers.append((i, 1, j))
                else:
                    face_centers.append((i, j, 1))
    preference_order.extend(face_centers)

    # Generate all cells, excluding those already in preference_order
    all_cells = [(x, y, z) for x in range(3) for y in range(3) for z in range(3)]
    seen = set(preference_order)
    for cell in all_cells:
        if cell not in seen:
            preference_order.append(cell)

    # Find the first available empty cell in the prioritized order
    empty_cells = set((x, y, z) for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0)
    for cell in preference_order:
        if cell in empty_cells:
            return cell

    return (0, 0, 0)  # Should not be reached in valid game state
