
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next best move in a 3D Tic Tac Toe game for the current player (1) 
    by favoring winning moves, blocking opponent's moves, and following a heuristic for
    selecting otherwise.
    """
    
    # Generate all possible lines in the 3x3x3 3D grid
    def generate_all_lines():
        lines = []
        # Lines aligned along X, Y, and Z axes
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Face diagonals: fixed z (x-y)
        for z in range(3):
            lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
            lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
        # Fixed x (y-z)
        for x in range(3):
            lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
            lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
        # Fixed y (x-z)
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        
        # Space diagonals crossing cube through the center
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        return lines

    # List of all lines that are considered for determining a win
    LINES = generate_all_lines()

    def is_win(current_board):
        for line in LINES:
            x0, y0, z0 = line[0]
            val0 = current_board[x0][y0][z0]
            if val0 == 0:
                continue  # Skip empty cells
            win = True
            for x, y, z in line[1:]:
                if current_board[x][y][z] != val0:
                    win = False
                    break
            if win:
                return True
        return False

    # Step 1: Immediate Win for Player (1)
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:  # Only if cell is empty
                    board[x][y][z] = 1
                    if is_win(board):
                        board[x][y][z] = 0
                        return (x, y, z)
                    board[x][y][z] = 0  # Restore the board

    # Step 2: Block Opponent's Win if possible (for -1)
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    board[x][y][z] = -1
                    if is_win(board):
                        board[x][y][z] = 0
                        return (x, y, z)
                    board[x][y][z] = 0  # Restore the board

    # Step 3: Choose move by heuristics

    # Center cell
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Corner cells
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for x, y, z in corners:
        if board[x][y][z] == 0:
            return (x, y, z)

    # Face centers
    face_centers = [
        (1, 0, 0), (1, 0, 2), (1, 2, 0), (1, 2, 2),
        (0, 1, 0), (2, 1, 0), (0, 1, 2), (2, 1, 2),
        (0, 0, 1), (0, 2, 1), (2, 0, 1), (2, 2, 1)
    ]
    for x, y, z in face_centers:
        if board[x][y][z] == 0:
            return (x, y, z)

    # Finally, return any empty cell
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
