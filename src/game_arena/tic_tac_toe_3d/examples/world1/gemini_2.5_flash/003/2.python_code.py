
# All possible winning lines in a 3x3x3 Tic Tac Toe board.
# Each line is a list of 3 (x, y, z) coordinates.
# This variable is initialized once when the script is loaded, for efficiency.
WINNING_LINES = []

# --- 27 basic lines ---
# Rows (fixed y, z; vary x) - 3 layers * 3 rows/layer = 9 lines
for z in range(3):
    for y in range(3):
        WINNING_LINES.append([(x, y, z) for x in range(3)])

# Columns (fixed x, z; vary y) - 3 layers * 3 columns/layer = 9 lines
for z in range(3):
    for x in range(3):
        WINNING_LINES.append([(x, y, z) for y in range(3)])

# Pillars (fixed x, y; vary z) - 3 stacks * 3 rows/stack = 9 lines
for x in range(3):
    for y in range(3):
        WINNING_LINES.append([(x, y, z) for z in range(3)])

# --- 18 two-dimensional diagonal lines ---
# XY-plane diagonals (fixed z) - 3 layers * 2 diagonals/layer = 6 lines
for z in range(3):
    WINNING_LINES.append([(i, i, z) for i in range(3)])       # Main diagonal: (0,0,z), (1,1,z), (2,2,z)
    WINNING_LINES.append([(i, 2 - i, z) for i in range(3)])   # Anti-diagonal: (0,2,z), (1,1,z), (2,0,z)

# XZ-plane diagonals (fixed y) - 3 layers * 2 diagonals/layer = 6 lines
for y in range(3):
    WINNING_LINES.append([(i, y, i) for i in range(3)])       # Main diagonal
    WINNING_LINES.append([(i, y, 2 - i) for i in range(3)])   # Anti-diagonal

# YZ-plane diagonals (fixed x) - 3 layers * 2 diagonals/layer = 6 lines
for x in range(3):
    WINNING_LINES.append([(x, i, i) for i in range(3)])       # Main diagonal
    WINNING_LINES.append([(x, i, 2 - i) for i in range(3)])   # Anti-diagonal

# --- 4 three-dimensional diagonal lines ---
# 3D Diagonals
WINNING_LINES.append([(i, i, i) for i in range(3)])         # (0,0,0) to (2,2,2)
WINNING_LINES.append([(i, i, 2 - i) for i in range(3)])     # (0,0,2) to (2,2,0)
WINNING_LINES.append([(i, 2 - i, i) for i in range(3)])     # (0,2,0) to (2,0,2)
WINNING_LINES.append([(2 - i, i, i) for i in range(3)])     # (2,0,0) to (0,2,2)


def find_line_opportunity(player: int, board: list[list[list[int]]]) -> None:
    """
    Checks if a given player can win on their next move (by completing a line).
    If so, returns the coordinates of that winning move.
    """
    for line in WINNING_LINES:
        player_count = 0
        opponent_count = 0
        empty_slot = None

        # Iterate through the cells in the current winning line
        for (x, y, z) in line:
            cell_value = board[x][y][z]
            if cell_value == player:
                player_count += 1
            elif cell_value == -player:  # Check for opponent's pieces
                opponent_count += 1
            else:  # Cell is empty
                empty_slot = (x, y, z)

        # If the player has two pieces in this line, the opponent has none,
        # and there's one empty slot, this is a winning move for the player.
        if player_count == 2 and opponent_count == 0 and empty_slot is not None:
            return empty_slot
    return None


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for the AI in a 3x3x3 Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists representing the game board.
               0: empty, 1: AI (you), -1: Opponent.

    Returns:
        A tuple of three integers (x, y, z) indicating the chosen empty cell.
    """

    # 1. Check if the AI can win on this turn.
    my_winning_move = find_line_opportunity(1, board)
    if my_winning_move:
        return my_winning_move

    # 2. Check if the opponent can win on their next turn and block them.
    opponent_winning_move = find_line_opportunity(-1, board)
    if opponent_winning_move:
        return opponent_winning_move

    # 3. Try to take the center cell (most strategic position).
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # 4. Try to take any available corner. Corners are generally good positions.
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for x, y, z in corners:
        if board[x][y][z] == 0:
            return (x, y, z)

    # 5. As a fallback, take the first available empty cell found (arbitrary order).
    # This covers edge centers and face centers not explicitly prioritized.
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)

    # This case should theoretically not be reached in a valid game state
    # (there should always be an empty cell if a move is required).
    # However, it's good practice to have a fallback return.
    return (0, 0, 0) # Fallback, indicates an error state or full board without a clear move request.
