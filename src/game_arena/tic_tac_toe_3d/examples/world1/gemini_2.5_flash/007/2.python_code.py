
import random

# Global variable to store all winning lines, computed once.
_ALL_WINNING_LINES = None

def _initialize_winning_lines():
    """
    Generates and stores all possible winning lines for a 3x3x3 board.
    A winning line consists of 3 coordinates (z, y, x).
    There are 49 such lines in 3D Tic-Tac-Toe.
    """
    global _ALL_WINNING_LINES
    if _ALL_WINNING_LINES is not None:
        return _ALL_WINNING_LINES

    lines = []

    # 1. Lines along Z, Y, X axes (27 lines)
    # Rows (fixed z, y, varying x)
    for z in range(3):
        for y in range(3):
            lines.append([(z, y, x) for x in range(3)])
    # Columns (fixed z, x, varying y)
    for z in range(3):
        for x in range(3):
            lines.append([(z, y, x) for y in range(3)])
    # Pillars (fixed y, x, varying z)
    for y in range(3):
        for x in range(3):
            lines.append([(z, y, x) for z in range(3)])

    # 2. 2D Diagonals on each face/slice (18 lines)
    for i in range(3):
        # Diagonals on Z-slices (where z=i is constant)
        lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)]) # Main diagonal
        lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)]) # Anti-diagonal

        # Diagonals on Y-slices (where y=i is constant)
        lines.append([(0, i, 0), (1, i, 1), (2, i, 2)]) # Main diagonal
        lines.append([(0, i, 2), (1, i, 1), (2, i, 0)]) # Anti-diagonal

        # Diagonals on X-slices (where x=i is constant)
        lines.append([(0, 0, i), (1, 1, i), (2, 2, i)]) # Main diagonal
        lines.append([(0, 2, i), (1, 1, i), (2, 0, i)]) # Anti-diagonal

    # 3. 3D Space Diagonals (4 main diagonals)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)]) # (0,0,0) to (2,2,2)
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)]) # (0,0,2) to (2,2,0)
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)]) # (0,2,0) to (2,0,2)
    lines.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)]) # (2,0,0) to (0,2,2)
    
    _ALL_WINNING_LINES = lines
    return _ALL_WINNING_LINES

def _find_critical_move(board, player_id: int):
    """
    Checks if 'player_id' can win in the next move, or if 'player_id' needs to block
    an opponent's win (when called with opponent's ID).
    Returns the coordinates (z, y, x) of the strategic move if found, otherwise None.
    """
    for line_coords in _initialize_winning_lines():
        player_pieces_count = 0
        empty_cell = None
        current_line_empty_count = 0
        
        for z, y, x in line_coords:
            cell_value = board[z][y][x]
            if cell_value == player_id:
                player_pieces_count += 1
            elif cell_value == 0:
                empty_cell = (z, y, x)
                current_line_empty_count += 1
            # If line contains opponent's piece, it cannot be won/blocked by this player
            elif cell_value == -player_id:
                player_pieces_count = -1 # Mark as invalid line for this player
                break
        
        # A move is critical if there are two of the player's pieces and exactly one empty cell.
        if player_pieces_count == 2 and current_line_empty_count == 1 and empty_cell is not None:
            return empty_cell
    return None

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for a 3x3x3 3D Tic Tac Toe game.
    
    Args:
        board: A 3x3x3 list of lists representing the game board.
               0: empty, 1: your piece, -1: opponent's piece.
               
    Returns:
        A tuple (z, y, x) indicating the chosen empty cell.
    """
    
    ME = 1
    OPPONENT = -1

    # 1. Check for a winning move for me
    my_winning_move = _find_critical_move(board, ME)
    if my_winning_move:
        return my_winning_move

    # 2. Check for a blocking move against the opponent
    opponent_winning_move = _find_critical_move(board, OPPONENT)
    if opponent_winning_move:
        return opponent_winning_move

    # 3. Try to take the center (1, 1, 1) if available, as it's highly strategic.
    center_cell = (1, 1, 1)
    if board[center_cell[0]][center_cell[1]][center_cell[2]] == 0:
        return center_cell

    # 4. Try to take corner cells if available. There are 8 corners.
    corners = [
        (0,0,0), (0,0,2), (0,2,0), (0,2,2),
        (2,0,0), (2,0,2), (2,2,0), (2,2,2)
    ]
    # Shuffle to add some variety if multiple corners are open and equally good
    shuffled_corners = random.sample(corners, len(corners)) # Use sample to avoid modifying original list
    for z, y, x in shuffled_corners:
        if board[z][y][x] == 0:
            return (z, y, x)
            
    # 5. Fallback: If no strategic moves, pick any available empty cell.
    # This covers face-centers, true-edge cells, and any other remaining empty cells.
    empty_cells = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empty_cells.append((z, y, x))
    
    if empty_cells:
        # Shuffle empty cells to add variety and avoid predictable patterns
        return random.choice(empty_cells)
    
    # This part should ideally not be reached in a live game as a move is always possible before game end,
    # unless the board is completely full and it's a draw, in which case no move is needed.
    # As a failsafe, return a default valid-looking cell, though it implies an error state.
    return (0,0,0) 
