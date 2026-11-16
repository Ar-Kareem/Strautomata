
# No numpy needed for this solution as the board is a list of lists.

# Pre-calculate all possible winning lines on a 3x3x3 board.
# Each line is a list of 3 (z, y, x) coordinates that constitute a win.
ALL_WINNING_LINES = []

# 1. Lines parallel to axes (27 lines)
# Lines along the X-axis (rows: z, y fixed, x varies)
for z_coord in range(3):
    for y_coord in range(3):
        ALL_WINNING_LINES.append([(z_coord, y_coord, x_coord) for x_coord in range(3)])

# Lines along the Y-axis (columns: z, x fixed, y varies)
for z_coord in range(3):
    for x_coord in range(3):
        ALL_WINNING_LINES.append([(z_coord, y_coord, x_coord) for y_coord in range(3)])

# Lines along the Z-axis (pillars: y, x fixed, z varies)
for y_coord in range(3):
    for x_coord in range(3):
        ALL_WINNING_LINES.append([(z_coord, y_coord, x_coord) for z_coord in range(3)])

# 2. 2D diagonals within planes (18 lines)
# Diagonals on X-Y planes (z fixed, y and x vary)
for z_coord in range(3):
    ALL_WINNING_LINES.append([(z_coord, i, i) for i in range(3)])          # Diagonal: (z,0,0) -> (z,1,1) -> (z,2,2)
    ALL_WINNING_LINES.append([(z_coord, i, 2 - i) for i in range(3)])      # Anti-diagonal: (z,0,2) -> (z,1,1) -> (z,2,0)

# Diagonals on X-Z planes (y fixed, x and z vary)
for y_coord in range(3):
    ALL_WINNING_LINES.append([(i, y_coord, i) for i in range(3)])          # Diagonal: (0,y,0) -> (1,y,1) -> (2,y,2)
    ALL_WINNING_LINES.append([(i, y_coord, 2 - i) for i in range(3)])      # Anti-diagonal: (0,y,2) -> (1,y,1) -> (2,y,0)

# Diagonals on Y-Z planes (x fixed, y and z vary)
for x_coord in range(3):
    ALL_WINNING_LINES.append([(i, i, x_coord) for i in range(3)])          # Diagonal: (0,0,x) -> (1,1,x) -> (2,2,x)
    ALL_WINNING_LINES.append([(i, 2 - i, x_coord) for i in range(3)])      # Anti-diagonal: (0,2,x) -> (1,1,x) -> (2,0,x)

# 3. 3D diagonals (4 lines)
ALL_WINNING_LINES.append([(i, i, i) for i in range(3)])          # Main 3D diagonal: (0,0,0) -> (1,1,1) -> (2,2,2)
ALL_WINNING_LINES.append([(i, i, 2 - i) for i in range(3)])      # 3D diagonal: (0,0,2) -> (1,1,1) -> (2,2,0)
ALL_WINNING_LINES.append([(i, 2 - i, i) for i in range(3)])      # 3D diagonal: (0,2,0) -> (1,1,1) -> (2,0,2)
ALL_WINNING_LINES.append([(i, 2 - i, 2 - i) for i in range(3)])  # 3D diagonal: (0,2,2) -> (1,1,1) -> (2,0,0)

# Prioritized moves for non-win/block scenarios, ordered by strategic importance.
# This list is hand-ranked from most to least strategic.
PRIORITIZED_MOVES = [
    (1, 1, 1), # The absolute center, participates in the most winning lines.
    # Corners (8 positions), next most strategic, participate in many lines.
    (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
    (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),
    # Face Centers (6 positions).
    (0, 1, 1), (1, 0, 1), (1, 1, 0), (1, 1, 2), (1, 2, 1), (2, 1, 1),
    # Edge Centers (12 positions).
    (0, 0, 1), (0, 1, 0), (0, 1, 2), (0, 2, 1),
    (1, 0, 0), (1, 0, 2), (1, 2, 0), (1, 2, 2),
    (2, 0, 1), (2, 1, 0), (2, 1, 2), (2, 2, 1)
]

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for a 3x3x3 3D Tic Tac Toe game.

    The AI's strategy is as follows:
    1. Check for any immediate winning moves (place own piece to win).
    2. Check for any immediate blocking moves (prevent opponent from winning).
    3. If no immediate win/block, choose a move from a prioritized list of strategic positions
       (center, then corners, then face centers, then edge centers).
    4. As a last resort, pick the first available empty cell.

    Args:
        board: A 3x3x3 list of lists representing the game board.
               - `0`: empty cell
               - `1`: AI's piece
               - `-1`: opponent's piece

    Returns:
        A tuple of three integers (z, y, x) indicating the chosen empty cell to play.
    """

    # Helper function to check if a specific line on the board is fully occupied by 'player'
    # This means all three cells in the line belong to 'player' and are not empty or the opponent's.
    def check_line_for_player(current_board: list[list[list[int]]], player: int, line: list[tuple[int, int, int]]) -> bool:
        return all(current_board[z][y][x] == player for z, y, x in line)

    my_winning_moves = []
    blocking_moves = []
    available_empty_cells = []

    # Iterate through all cells on the board
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:  # If the cell is empty
                    current_move = (z, y, x)
                    available_empty_cells.append(current_move)

                    # --- Strategy Step 1: Check for immediate win for AI (player 1) ---
                    # Temporarily place AI's piece on the board
                    board[z][y][x] = 1
                    # Check if this move results in a win for AI
                    if any(check_line_for_player(board, 1, line) for line in ALL_WINNING_LINES):
                        my_winning_moves.append(current_move)
                    board[z][y][x] = 0  # Revert the board for the next check

                    # --- Strategy Step 2: Check for immediate win for opponent (player -1) ---
                    # Temporarily place opponent's piece on the board
                    board[z][y][x] = -1
                    # Check if this move would result in a win for the opponent
                    if any(check_line_for_player(board, -1, line) for line in ALL_WINNING_LINES):
                        blocking_moves.append(current_move)
                    board[z][y][x] = 0  # Revert the board for the next check

    # --- Execute prioritized moves ---
    # 1. If AI can win, take the first winning move found.
    if my_winning_moves:
        return my_winning_moves[0]

    # 2. If opponent can win, block their first winning move found.
    if blocking_moves:
        return blocking_moves[0]

    # 3. If no immediate wins or blocks, try strategic moves.
    #    Iterate through the pre-defined prioritized list of moves.
    for move in PRIORITIZED_MOVES:
        move_z, move_y, move_x = move
        if board[move_z][move_y][move_x] == 0:  # If the strategic position is empty
            return move

    # 4. Fallback: If no strategic moves are available (e.g., all prioritized spots are taken),
    #    choose the first available empty cell. This should only happen if the board is almost full
    #    or specific board states.
    if available_empty_cells:
        return available_empty_cells[0]

    # This case should ideally not be reached in a competitive game where a player is always
    # expected to make a valid move on a non-full board. Returning an arbitrary move as a safeguard.
    return (0, 0, 0)
