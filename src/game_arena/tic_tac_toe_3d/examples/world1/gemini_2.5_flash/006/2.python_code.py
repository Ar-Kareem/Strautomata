
import numpy as np

# Pre-computed winning lines
# There are 49 winning lines in a 3x3x3 Tic Tac Toe game.
# Each line is a list of three (x, y, z) coordinates.
WINNING_LINES = []

# 1. Axis-parallel lines (27 lines)
# Iterate through all permutations of fixing two coordinates and varying one
for i in range(3):  # x-dimension
    for j in range(3):  # y-dimension
        # Lines parallel to Z-axis (varying z, fixed x, y)
        WINNING_LINES.append([(i, j, 0), (i, j, 1), (i, j, 2)])
        # Lines parallel to Y-axis (varying y, fixed x, z)
        WINNING_LINES.append([(i, 0, j), (i, 1, j), (i, 2, j)])
        # Lines parallel to X-axis (varying x, fixed y, z)
        WINNING_LINES.append([(0, i, j), (1, i, j), (2, i, j)])

# 2. Planar diagonals (18 lines)
# Diagonals within each 3x3 plane (XY, XZ, YZ)
for k in range(3): # Fixed coordinate (plane index)
    # XY-plane diagonals (z-fixed)
    WINNING_LINES.append([(0, 0, k), (1, 1, k), (2, 2, k)]) # Main diagonal
    WINNING_LINES.append([(0, 2, k), (1, 1, k), (2, 0, k)]) # Anti-diagonal
    # XZ-plane diagonals (y-fixed)
    WINNING_LINES.append([(0, k, 0), (1, k, 1), (2, k, 2)]) # Main diagonal
    WINNING_LINES.append([(0, k, 2), (1, k, 1), (2, k, 0)]) # Anti-diagonal
    # YZ-plane diagonals (x-fixed)
    WINNING_LINES.append([(k, 0, 0), (k, 1, 1), (k, 2, 2)]) # Main diagonal
    WINNING_LINES.append([(k, 0, 2), (k, 1, 1), (k, 2, 0)]) # Anti-diagonal

# 3. Space diagonals (4 lines)
# These pass through the center of the cube
WINNING_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
WINNING_LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
WINNING_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
WINNING_LINES.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])


def check_win(board_np: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won on the board.
    A player wins if they have 3 of their pieces in any of the WINNING_LINES.
    """
    for line in WINNING_LINES:
        # Get the values of the cells in the current line
        line_values = [board_np[x, y, z] for x, y, z in line]
        # Check if all values in the line belong to the current player
        if all(val == player for val in line_values):
            return True
    return False


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next optimal move for a 3x3x3 3D Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists representing the game board.
               0 for empty, 1 for the current player (you), -1 for the opponent.

    Returns:
        A tuple of three integers (x, y, z) indicating the chosen empty cell.
    """
    ME = 1  # Represents the current player
    OPPONENT = -1  # Represents the opponent

    # Convert the input board to a numpy array for efficient operations
    board_np = np.array(board)

    # Find all empty cells
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_np[x, y, z] == 0:
                    empty_cells.append((x, y, z))

    # If no empty cells, the game is over or board is full.
    # This state should ideally not be reached if called in a valid game context.
    if not empty_cells:
        # Return a dummy move or raise an error, depending on game rules.
        # Returning (0,0,0) is a fallback, but the game should handle this as a draw.
        return (0, 0, 0)

    # --- Strategy Priorities ---

    # 1. Check for immediate win: If I can win in one move, take it.
    for move in empty_cells:
        temp_board = board_np.copy()  # Create a temporary board
        temp_board[move[0], move[1], move[2]] = ME  # Simulate my move
        if check_win(temp_board, ME):
            return move

    # 2. Block opponent's immediate win: If the opponent can win in one move, block them.
    for move in empty_cells:
        temp_board = board_np.copy()
        temp_board[move[0], move[1], move[2]] = OPPONENT  # Simulate opponent's move
        if check_win(temp_board, OPPONENT):
            return move

    # 3. Evaluate other strategic moves (forks, threats, positional advantage)
    move_scores = {}
    for move in empty_cells:
        score = 0
        x, y, z = move

        my_two_in_a_row_count = 0  # To detect potential forks for me
        opp_two_in_a_row_count = 0  # To detect potential opponent forks to block

        for line in WINNING_LINES:
            # Check if the current 'move' is part of this winning line
            if move in line:
                # Get current state of the line *before* making the 'move'
                line_values_current = [board_np[cx, cy, cz] for cx, cy, cz in line]
                my_pieces_in_line = line_values_current.count(ME)
                opp_pieces_in_line = line_values_current.count(OPPONENT)
                empty_spots_in_line = line_values_current.count(0)

                # If placing ME at 'move' creates a 2-in-a-row with 1 empty spot (a "threat")
                # This makes a line like [ME, ME, 0] or [ME, 0, ME] or [0, ME, ME]
                if my_pieces_in_line == 1 and opp_pieces_in_line == 0 and empty_spots_in_line == 2:
                    my_two_in_a_row_count += 1

                # If placing ME at 'move' blocks an opponent's 2-in-a-row (a "threat")
                # This means the current line is [OPPONENT, OPPONENT, 0] and 'move' is '0'.
                if opp_pieces_in_line == 2 and my_pieces_in_line == 0 and empty_spots_in_line == 1:
                    opp_two_in_a_row_count += 1

        # Score for creating a fork (two simultaneous threats for me)
        if my_two_in_a_row_count >= 2:
            score += 200  # High score for creating my own fork
        elif my_two_in_a_row_count == 1:
            score += 20   # Medium score for creating a single threat

        # Score for blocking an opponent's fork (two simultaneous threats for opponent)
        if opp_two_in_a_row_count >= 2:
            score += 150  # Very good score for blocking an opponent's fork
        elif opp_two_in_a_row_count == 1:
            score += 30   # Good score for blocking a single opponent threat (defensive focus)

        # Positional preferences:
        # Prefer the center cell (1,1,1) as it is part of many winning lines.
        if move == (1, 1, 1):
            score += 50
        # Prefer corner cells (8 corners of the cube)
        elif move in [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
                      (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]:
            score += 25
        # Assign a minimal score to all other empty cells to ensure they are considered
        # if no other strategic advantage is found.
        else:
            score += 5

        move_scores[move] = score

    # Choose the move with the highest calculated score
    if move_scores:
        best_move = max(move_scores, key=move_scores.get)
        return best_move

    # Fallback: This part should logically not be reached if empty_cells is not empty
    # as all empty cells are given at least a default score of 5.
    return empty_cells[0]
