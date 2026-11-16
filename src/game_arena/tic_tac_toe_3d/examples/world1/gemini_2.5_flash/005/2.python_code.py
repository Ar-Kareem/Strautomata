
import random

# Precompute all 49 winning lines for a 3x3x3 Tic-Tac-Toe board.
# Each line is a list of (z, y, x) tuples representing cell coordinates.
WIN_LINES = []

# 1. Axis-aligned lines (27 lines)
# Lines parallel to X-axis (varying x, fixed z, y)
# Example: (0,0,0), (0,0,1), (0,0,2)
for z in range(3):
    for y in range(3):
        WIN_LINES.append([(z, y, x) for x in range(3)])

# Lines parallel to Y-axis (varying y, fixed z, x)
# Example: (0,0,0), (0,1,0), (0,2,0)
for z in range(3):
    for x in range(3):
        WIN_LINES.append([(z, y, x) for y in range(3)])

# Lines parallel to Z-axis (varying z, fixed y, x)
# Example: (0,0,0), (1,0,0), (2,0,0)
for y in range(3):
    for x in range(3):
        WIN_LINES.append([(z, y, x) for z in range(3)])

# 2. Planar Diagonals (18 lines)
# Diagonals on XY-planes (z fixed, y and x vary diagonally)
# Example (z=0): (0,0,0), (0,1,1), (0,2,2) and (0,0,2), (0,1,1), (0,2,0)
for z in range(3):
    WIN_LINES.append([(z, i, i) for i in range(3)])       # Main diagonal
    WIN_LINES.append([(z, i, 2 - i) for i in range(3)])   # Anti-diagonal

# Diagonals on XZ-planes (y fixed, z and x vary diagonally)
# Example (y=0): (0,0,0), (1,0,1), (2,0,2) and (0,0,2), (1,0,1), (2,0,0)
for y in range(3):
    WIN_LINES.append([(i, y, i) for i in range(3)])       # Main diagonal
    WIN_LINES.append([(i, y, 2 - i) for i in range(3)])   # Anti-diagonal

# Diagonals on YZ-planes (x fixed, z and y vary diagonally)
# Example (x=0): (0,0,0), (1,1,0), (2,2,0) and (0,2,0), (1,1,0), (2,0,0)
for x in range(3):
    WIN_LINES.append([(i, i, x) for i in range(3)])       # Main diagonal
    WIN_LINES.append([(i, 2 - i, x) for i in range(3)])   # Anti-diagonal

# 3. Space Diagonals (4 lines)
WIN_LINES.append([(i, i, i) for i in range(3)])            # (0,0,0) to (2,2,2)
WIN_LINES.append([(i, i, 2 - i) for i in range(3)])       # (0,0,2) to (2,2,0)
WIN_LINES.append([(i, 2 - i, i) for i in range(3)])       # (0,2,0) to (2,0,2)
WIN_LINES.append([(2 - i, i, i) for i in range(3)])       # (2,0,0) to (0,2,2)

def get_empty_cells(board: list[list[list[int]]]) -> list[tuple[int, int, int]]:
    """
    Helper function to get all empty cells (coordinates where value is 0).
    """
    empty_cells = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empty_cells.append((z, y, x))
    return empty_cells

def find_strategic_move(board: list[list[list[int]]], player: int) -> None:
    """
    Checks if 'player' can win (or block an opponent's win) in the next move.
    A strategic move exists if a line has two of 'player's pieces and one empty cell.
    Returns the coordinates of that empty cell, or None if no such move is found.
    """
    for line in WIN_LINES:
        player_count = 0
        empty_cell = None
        opponent_in_line = False

        for r, c, d in line:
            cell_value = board[r][c][d]
            if cell_value == player:
                player_count += 1
            elif cell_value == 0:
                empty_cell = (r, c, d)
            elif cell_value == -player: # Opponent piece blocks this line for 'player'
                opponent_in_line = True
                break # No need to check further in this line

        if not opponent_in_line and player_count == 2 and empty_cell:
            return empty_cell
    return None

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for a 3x3x3 3D Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists representing the game board.
               `0` (empty), `1` (you), and `-1` (opponent).

    Returns:
        A tuple (z, y, x) indicating the chosen empty cell where z, y, x are 0-2.
    """

    # 1. Check for an immediate winning move for AI (player 1)
    my_winning_move = find_strategic_move(board, 1)
    if my_winning_move:
        return my_winning_move

    # 2. Check for an immediate blocking move against the opponent (player -1)
    opponent_winning_move = find_strategic_move(board, -1)
    if opponent_winning_move:
        return opponent_winning_move

    # 3. Prioritize taking the center (1,1,1) if available
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # 4. Prioritize corners (8 cells)
    # Corners are cells with min/max coordinates (e.g., 0 or 2 for each dimension)
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    random.shuffle(corners) # Randomize choice among available corners for less predictable play
    for z, y, x in corners:
        if board[z][y][x] == 0:
            return (z, y, x)

    # 5. Prioritize (planar) face centers (6 cells)
    # These are cells like (0,1,1), (1,0,1), etc., where two coordinates are 1 and one is 0 or 2.
    face_centers = [
        (0,1,1), (1,0,1), (1,1,0),
        (2,1,1), (1,2,1), (1,1,2)
    ]
    random.shuffle(face_centers) # Randomize choice among available face centers
    for z, y, x in face_centers:
        if board[z][y][x] == 0:
            return (z, y, x)

    # 6. Prioritize edge centers (12 cells)
    # These are cells with exactly one coordinate as 1 and two as 0 or 2.
    edge_centers = [
        (0,0,1), (0,1,0), (0,1,2), (0,2,1), # Edges on z=0 layer
        (1,0,0), (1,0,2), (1,2,0), (1,2,2), # Edges bridging z=0 and z=2 (vertical edges for x=0,2 or y=0,2)
        (2,0,1), (2,1,0), (2,1,2), (2,2,1)  # Edges on z=2 layer
    ]
    random.shuffle(edge_centers) # Randomize choice among available edge centers
    for z, y, x in edge_centers:
        if board[z][y][x] == 0:
            return (z, y, x)

    # 7. Fallback: If no high-priority strategic move, pick any random empty cell.
    empty_cells = get_empty_cells(board)
    if empty_cells:
        return random.choice(empty_cells)
    
    # This point should theoretically not be reached in a valid game state
    # where a move is expected (i.e., the board is not full).
    # Returning (0,0,0) as a graceful failure state or if board is full.
    return (0, 0, 0)
