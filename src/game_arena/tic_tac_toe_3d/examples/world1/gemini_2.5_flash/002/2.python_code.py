
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next optimal move for a 3x3x3 3D Tic Tac Toe game.
    Priorities: Win -> Block -> Strategic (Center -> Face Centers -> Corners) -> Any Empty
    """

    # Global constant for all winning lines, computed once.
    # A winning line consists of 3 coordinates (x, y, z) that form a straight line.
    global WIN_LINES
    if 'WIN_LINES' not in globals() or not WIN_LINES:
        WIN_LINES = []

        # Lines parallel to X-axis (Varying x, fixed y, z)
        for y in range(3):
            for z in range(3):
                WIN_LINES.append([(x, y, z) for x in range(3)])

        # Lines parallel to Y-axis (Fixed x, varying y, fixed z)
        for x in range(3):
            for z in range(3):
                WIN_LINES.append([(x, y, z) for y in range(3)])

        # Lines parallel to Z-axis (Fixed x, fixed y, varying z)
        for x in range(3):
            for y in range(3):
                WIN_LINES.append([(x, y, z) for z in range(3)])

        # 2D Diagonals within each plane

        # XY-planes (fixed Z)
        for z in range(3):
            WIN_LINES.append([(0, 0, z), (1, 1, z), (2, 2, z)]) # Main diagonal
            WIN_LINES.append([(0, 2, z), (1, 1, z), (2, 0, z)]) # Anti-diagonal

        # XZ-planes (fixed Y)
        for y in range(3):
            WIN_LINES.append([(0, y, 0), (1, y, 1), (2, y, 2)]) # Main diagonal
            WIN_LINES.append([(0, y, 2), (1, y, 1), (2, y, 0)]) # Anti-diagonal

        # YZ-planes (fixed X)
        for x in range(3):
            WIN_LINES.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)]) # Main diagonal
            WIN_LINES.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)]) # Anti-diagonal

        # 3D Diagonals
        WIN_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        WIN_LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        WIN_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        WIN_LINES.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])

    # Strategic cell priorities
    CENTER = (1, 1, 1)
    FACE_CENTERS = [
        (0, 1, 1), (2, 1, 1),
        (1, 0, 1), (1, 2, 1),
        (1, 1, 0), (1, 1, 2)
    ]
    CORNERS = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    STRATEGIC_MOVES_PRIORITY = [CENTER] + FACE_CENTERS + CORNERS

    def find_empty_cells(current_board: list[list[list[int]]]) -> list[tuple[int, int, int]]:
        """
        Finds all empty cells on the board.
        """
        empty_cells = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if current_board[x][y][z] == 0:
                        empty_cells.append((x, y, z))
        return empty_cells

    def check_win(current_board: list[list[list[int]]], player: int) -> bool:
        """
        Checks if the given player has won the game.
        """
        for line in WIN_LINES:
            if all(current_board[x][y][z] == player for x, y, z in line):
                return True
        return False

    empty_cells = find_empty_cells(board)

    # 1. Check for a winning move for me (player 1)
    for x, y, z in empty_cells:
        board[x][y][z] = 1  # Temporarily make the move
        if check_win(board, 1):
            board[x][y][z] = 0  # Undo the move
            return (x, y, z)
        board[x][y][z] = 0  # Undo the move

    # 2. Check for a blocking move for the opponent (player -1)
    for x, y, z in empty_cells:
        board[x][y][z] = -1  # Temporarily place opponent's mark
        if check_win(board, -1):
            board[x][y][z] = 0  # Undo the move
            return (x, y, z)
        board[x][y][z] = 0  # Undo the move

    # 3. Check for strategic moves (center, then face centers, then corners)
    for sx, sy, sz in STRATEGIC_MOVES_PRIORITY:
        if board[sx][sy][sz] == 0:
            return (sx, sy, sz)

    # 4. If no strategic moves are available, pick the first available empty cell.
    # This acts as a fallback for edge positions or if strategic spots are already filled.
    if empty_cells:
        return empty_cells[0]

    # This case should ideally not be reached if the game is still active
    # and a move is required (i.e., board is not full and no winner yet).
    raise Exception("No available moves found. Board might be full or game over.")

