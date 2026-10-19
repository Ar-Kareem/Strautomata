
import random

# Global list to store all 49 potential winning lines.
# This is computed once when the script is loaded to optimize performance.
ALL_LINES = []

def _generate_all_lines():
    """
    Generates all 49 winning lines in a 3x3x3 Tic-Tac-Toe board.
    Each line is a list of 3 coordinate tuples (x, y, z).
    """
    global ALL_LINES
    if ALL_LINES:  # Already generated
        return

    # 1. 27 lines parallel to axes (rows, columns, pillars)
    for i in range(3):  # Fixed z-plane for xy-axes, fixed y-plane for xz-axes, fixed x-plane for yz-axes
        for j in range(3):
            # Lines along x-axis (vary x, fixed y, z)
            ALL_LINES.append([(x, j, i) for x in range(3)])
            # Lines along y-axis (fixed x, vary y, fixed z)
            ALL_LINES.append([(j, y, i) for y in range(3)])
            # Lines along z-axis (fixed x, fixed y, vary z)
            ALL_LINES.append([(i, j, z) for z in range(3)])

    # 2. 18 lines along 2D plane diagonals
    for i in range(3):
        # Diagonals on xy-planes (fixed z)
        ALL_LINES.append([(0, 0, i), (1, 1, i), (2, 2, i)])
        ALL_LINES.append([(0, 2, i), (1, 1, i), (2, 0, i)])
        # Diagonals on xz-planes (fixed y)
        ALL_LINES.append([(0, i, 0), (1, i, 1), (2, i, 2)])
        ALL_LINES.append([(0, i, 2), (1, i, 1), (2, i, 0)])
        # Diagonals on yz-planes (fixed x)
        ALL_LINES.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
        ALL_LINES.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])

    # 3. 4 space diagonals
    ALL_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    ALL_LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    ALL_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    ALL_LINES.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])

# Global list for preferred move order (center, then corners, then others)
# This is computed once to provide a consistent strategic preference.
PREFERRED_MOVES_ORDER = []

def _generate_preferred_moves_order():
    """
    Generates a list of all 27 board coordinates, ordered by strategic preference:
    center, then corners, then other cells in a deterministic order.
    """
    global PREFERRED_MOVES_ORDER
    if PREFERRED_MOVES_ORDER: # Already generated
        return

    # 1. Center cell
    PREFERRED_MOVES_ORDER.append((1, 1, 1))

    # 2. Corner cells
    corners = [(x, y, z) for x in [0, 2] for y in [0, 2] for z in [0, 2] if (x, y, z) != (1, 1, 1)]
    PREFERRED_MOVES_ORDER.extend(corners)

    # 3. All other cells (edges and face centers)
    # Iterate through all possible coordinates and add those not already in the list.
    for z in range(3):
        for y in range(3):
            for x in range(3):
                cell = (x, y, z)
                if cell not in PREFERRED_MOVES_ORDER:
                    PREFERRED_MOVES_ORDER.append(cell)

# Initialize the global lists when the module is loaded
_generate_all_lines()
_generate_preferred_moves_order()


def check_potential_completion(board: list[list[list[int]]], player: int, line: list[tuple[int, int, int]]) -> None:
    """
    Checks if a given 'line' on the 'board' can be completed by 'player'
    to form a winning three-in-a-row in the next move.
    
    Args:
        board: The 3x3x3 Tic-Tac-Toe board.
        player: The player to check for (1 for AI, -1 for opponent).
        line: A list of 3 coordinate tuples representing a potential winning line.

    Returns:
        The coordinates of the empty cell that would complete the line for 'player',
        or None if the line cannot be completed (e.g., not 2 player-pieces and 1 empty,
        or opponent's piece blocks it).
    """
    player_count = 0
    empty_spot = None
    
    for x, y, z in line:
        cell_value = board[x][y][z]
        if cell_value == player:
            player_count += 1
        elif cell_value == 0:
            empty_spot = (x, y, z)
        else: # Opponent's piece is in this line, so player cannot win/block here
            return None
            
    if player_count == 2 and empty_spot is not None:
        return empty_spot
    return None


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next best move for the AI (player 1) in a 3x3x3 Tic-Tac-Toe game.

    Args:
        board: A 3x3x3 list of lists representing the game board.
               0: empty, 1: AI's piece, -1: Opponent's piece.

    Returns:
        A tuple of three integers (x, y, z) indicating the chosen empty cell.
    """

    # 1. Check for an immediate winning move for the AI (player 1)
    # If the AI can win, take that move without hesitation.
    for line in ALL_LINES:
        win_move = check_potential_completion(board, 1, line)
        if win_move:
            return win_move

    # 2. Check for an immediate winning move for the opponent (player -1) and block it
    # If the opponent can win on their next turn, the AI must block it.
    for line in ALL_LINES:
        block_move = check_potential_completion(board, -1, line)
        if block_move:
            return block_move
            
    # 3. Apply strategic moves based on preferred cell order
    # This prioritizes the center, then corners, then other cells.
    for move_coords in PREFERRED_MOVES_ORDER:
        x, y, z = move_coords
        if board[x][y][z] == 0: # If the preferred cell is empty, take it.
            return move_coords

    # Fallback option: If for some unexpected reason no strategic move was found
    # (e.g., board is full, or edge case not covered), pick any available empty cell.
    # In a correctly played game, this part should ideally not be reached before a win/draw.
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append((x,y,z))
    
    if empty_cells:
        return random.choice(empty_cells)
    
    # If no empty cells are found, the board is full. This implies the game should
    # have ended in a win or draw on the previous move, or the board state is invalid.
    # Returning a default (0,0,0) in this unlikely scenario, but it shouldn't be reached
    # if the game state is valid and it's truly the AI's turn to make a move.
    return (0,0,0) 
