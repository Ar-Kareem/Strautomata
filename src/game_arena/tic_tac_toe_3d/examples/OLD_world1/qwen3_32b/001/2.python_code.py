
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Return the next move (x, y, z) for a 3x3x3 3D Tic Tac Toe game.
    
    Parameters:
    - board: A 3x3x3 3D array where:
        0 = empty,
        1 = player's move,
        -1 = opponent's move
    
    Returns:
    - tuple (x, y, z): Coordinates of the player's next move.
    """
    
    def generate_lines():
        lines = []
        
        # Axis-aligned lines (x, y, z)
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
            lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
            lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        for x in range(3):
            lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
            lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
        
        # Space diagonals
        lines.extend([
            [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
            [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
            [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
            [(0, 2, 2), (1, 1, 1), (2, 0, 0)],
        ])
        
        return lines

    lines = generate_lines()

    # 1. Check for own winning moves
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] != 0:
                    continue
                for line in lines:
                    if (x, y, z) not in line:
                        continue
                    if all((a, b, c) == (x, y, z) or board[a][b][c] == 1 for a, b, c in line):
                        return (x, y, z)

    # 2. Block opponent's winning moves
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] != 0:
                    continue
                for line in lines:
                    if (x, y, z) not in line:
                        continue
                    if all((a, b, c) == (x, y, z) or board[a][b][c] == -1 for a, b, c in line):
                        return (x, y, z)

    # 3. Choose the center
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # 4. Try corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),
    ]
    for x, y, z in corners:
        if board[x][y][z] == 0:
            return (x, y, z)

    # 5. Fallback: any empty cell
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)

    # Should not reach here in a valid game state
    return (0, 0, 0)
