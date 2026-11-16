
# Predefined list of all 49 winning lines in 3D Tic Tac Toe
all_lines = [
    # X-axis lines (fixed y, z)
    [(0,0,0), (1,0,0), (2,0,0)],
    [(0,0,1), (1,0,1), (2,0,1)],
    [(0,0,2), (1,0,2), (2,0,2)],
    [(0,1,0), (1,1,0), (2,1,0)],
    [(0,1,1), (1,1,1), (2,1,1)],
    [(0,1,2), (1,1,2), (2,1,2)],
    [(0,2,0), (1,2,0), (2,2,0)],
    [(0,2,1), (1,2,1), (2,2,1)],
    [(0,2,2), (1,2,2), (2,2,2)],
    # Y-axis lines (fixed x, z)
    [(0,0,0), (0,1,0), (0,2,0)],
    [(0,0,1), (0,1,1), (0,2,1)],
    [(0,0,2), (0,1,2), (0,2,2)],
    [(1,0,0), (1,1,0), (1,2,0)],
    [(1,0,1), (1,1,1), (1,2,1)],
    [(1,0,2), (1,1,2), (1,2,2)],
    [(2,0,0), (2,1,0), (2,2,0)],
    [(2,0,1), (2,1,1), (2,2,1)],
    [(2,0,2), (2,1,2), (2,2,2)],
    # Z-axis lines (fixed x, y)
    [(0,0,0), (0,0,1), (0,0,2)],
    [(0,1,0), (0,1,1), (0,1,2)],
    [(0,2,0), (0,2,1), (0,2,2)],
    [(1,0,0), (1,0,1), (1,0,2)],
    [(1,1,0), (1,1,1), (1,0,2)],
    [(1,2,0), (1,2,1), (1,2,2)],
    [(2,0,0), (2,0,1), (2,0,2)],
    [(2,1,0), (2,1,1), (2,1,2)],
    [(2,2,0), (2,2,1), (2,2,2)],
    # Face diagonals (XY planes)
    [(0,0,0), (1,1,0), (2,2,0)],
    [(0,2,0), (1,1,0), (2,0,0)],
    [(0,0,1), (1,1,1), (2,2,1)],
    [(0,2,1), (1,1,1), (2,0,1)],
    [(0,0,2), (1,1,2), (2,2,2)],
    [(0,2,2), (1,1,2), (2,0,2)],
    # Face diagonals (YZ planes)
    [(0,0,0), (0,1,1), (0,2,2)],
    [(0,0,2), (0,1,1), (0,2,0)],
    [(1,0,0), (1,1,1), (1,2,2)],
    [(1,0,2), (1,1,1), (1,2,0)],
    [(2,0,0), (2,1,1), (2,2,2)],
    [(2,0,2), (2,1,1), (2,2,0)],
    # Face diagonals (XZ planes)
    [(0,0,0), (1,0,1), (2,0,2)],
    [(0,2,0), (1,0,1), (2,0,2)],
    [(0,0,2), (1,0,0), (2,0,2)],
    [(0,2,2), (1,0,1), (2,2,0)],
    # Space diagonals
    [(0,0,0), (1,1,1), (2,2,2)],
    [(0,0,2), (1,1,1), (2,2,0)],
    [(0,2,0), (1,1,1), (2,0,2)],
    [(0,2,2), (1,1,1), (2,0,0)]
]

def check_win(bd, player):
    """
    Checks if the given board has a winning line for the specified player.
    :param bd: 3x3x3 board (list of lists of lists)
    :param player: 1 or -1
    :return: True if player has a winning line, False otherwise
    """
    for line in all_lines:
        if all(bd[i][j][k] == player for i, j, k in line):
            return True
    return False

def policy(board):
    """
    Returns the next move as a tuple (i, j, k) for a 3x3x3 3D Tic Tac Toe game.
    :param board: 3x3x3 list of lists of lists
    :return: (i, j, k) where board[i][j][k] == 0
    """
    # Helper to make a deep copy of the board
    def copy_board(b):
        return [[[b[x][y][z] for z in range(3)] for y in range(3)] for x in range(3)]

    # Step 1: Try to find a winning move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    new = copy_board(board)
                    new[i][j][k] = 1
                    if check_win(new, 1):
                        return (i, j, k)

    # Step 2: Block opponent's winning move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    new = copy_board(board)
                    new[i][j][k] = -1
                    if check_win(new, -1):
                        return (i, j, k)

    # Step 3: Heuristic-based move selection (priority-based)
    priority = [
        (1,1,1),  # Center of cube
        (0,1,1), (2,1,1), (1,0,1), (1,2,1), (1,1,0), (1,1,2),  # Face centers
        (0,0,0), (0,0,2), (0,2,0), (0,2,2),  # Corners
        (2,0,0), (2,0,2), (2,2,0), (2,2,2),
    ]

    # Edge cells (middle of cube edges)
    edges = [
        (0,0,1), (0,2,1), (2,0,1), (2,2,1),
        (0,1,0), (0,1,2), (2,1,0), (2,1,2),
        (1,0,0), (1,2,0), (1,0,2), (1,2,2)
    ]
    priority.extend(edges)

    # Select first available move in priority order
    for i, j, k in priority:
        if board[i][j][k] == 0:
            return (i, j, k)

    # Fallback: return any empty cell (shouldn't happen if board isn't full)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)

    return None  # Should not reach here unless board is full
