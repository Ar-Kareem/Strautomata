
import random
import math

# These constants define the game's parameters and piece encodings.
ROWS = 6
COLS = 7
WINDOW_LENGTH = 4
EMPTY = 0
MY_PIECE = 1
OPP_PIECE = -1

# --- Helper Functions ---

def is_valid_location(board: list[list[int]], col: int) -> bool:
    """Checks if a column is a valid location to drop a piece (i.e., not full)."""
    return board[0][col] == EMPTY

def get_next_open_row(board: list[list[int]], col: int) -> None:
    """Gets the next open row in a given column."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None

def get_valid_locations(board: list[list[int]]) -> list[int]:
    """Returns a list of all valid (non-full) columns."""
    return [c for c in range(COLS) if is_valid_location(board, c)]

def drop_piece(board: list[list[int]], row: int, col: int, piece: int):
    """Places a piece on the board at the specified location."""
    board[row][col] = piece

def winning_move(board: list[list[int]], piece: int) -> bool:
    """Checks if the given piece has a winning position on the board."""
    # Check horizontal locations for a win
    for c in range(COLS - 3):
        for r in range(ROWS):
            if all(board[r][c + i] == piece for i in range(WINDOW_LENGTH)):
                return True

    # Check vertical locations for a win
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == piece for i in range(WINDOW_LENGTH)):
                return True

    # Check positively sloped diagonals
    for c in range(COLS - 3):
        for r in range(ROWS - 3):
            if all(board[r + i][c + i] == piece for i in range(WINDOW_LENGTH)):
                return True

    # Check negatively sloped diagonals
    for c in range(COLS - 3):
        for r in range(3, ROWS):
            if all(board[r - i][c + i] == piece for i in range(WINDOW_LENGTH)):
                return True
                
    return False

def evaluate_window(window: list[int], piece: int) -> int:
    """Scores a 4-cell window from the perspective of the given piece."""
    score = 0
    opp_piece = -piece
    
    my_count = window.count(piece)
    opp_count = window.count(opp_piece)
    empty_count = window.count(EMPTY)

    if my_count == 4:
        score += 1000
    elif my_count == 3 and empty_count == 1:
        score += 10
    elif my_count == 2 and empty_count == 2:
        score += 3

    if opp_count == 3 and empty_count == 1:
        score -= 80
        
    return score

def score_position(board: list[list[int]], piece: int) -> int:
    """Calculates the overall heuristic score of the board for a given piece."""
    score = 0
    
    # --- Score center column ---
    center_array = [board[r][COLS // 2] for r in range(ROWS)]
    center_count = center_array.count(piece)
    score += center_count * 4

    # --- Score horizontal windows ---
    for r in range(ROWS):
        row_array = board[r]
        for c in range(COLS - 3):
            window = row_array[c:c + WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # --- Score vertical windows ---
    for c in range(COLS):
        col_array = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r:r + WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # --- Score diagonal windows ---
    # Positively sloped
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    # Negatively sloped
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    return score

# --- Main Policy Function ---

def policy(board: list[list[int]]) -> int:
    """
    Implements a Connect 4 targeting policy based on a heuristic evaluation.

    The policy follows a hierarchy of decision-making:
    1.  Play a winning move if available.
    2.  Block an opponent's winning move.
    3.  If neither of the above, choose the move that maximizes a heuristic score.
        The heuristic favors moves that:
        - Create 3-in-a-rows or 2-in-a-rows for the current player.
        - Avoid setting up the opponent for a win.
        - Prioritize control of the center columns as a tie-breaker.
    """
    valid_locations = get_valid_locations(board)
    
    # --- Priority 1: Check for an immediate winning move ---
    for col in valid_locations:
        row = get_next_open_row(board, col)
        temp_board = [r[:] for r in board]
        drop_piece(temp_board, row, col, MY_PIECE)
        if winning_move(temp_board, MY_PIECE):
            return col

    # --- Priority 2: Block the opponent's winning move ---
    for col in valid_locations:
        row = get_next_open_row(board, col)
        temp_board = [r[:] for r in board]
        drop_piece(temp_board, row, col, OPP_PIECE)
        if winning_move(temp_board, OPP_PIECE):
            return col
    
    # --- Priority 3: Use heuristic to find the best next move ---
    best_score = -float('inf')
    best_col = random.choice(valid_locations) # Default to a random valid move

    # To break ties, evaluate moves in a preferred order (center-out)
    preferred_col_order = [3, 4, 2, 5, 1, 6, 0]
    sorted_valid_locations = [c for c in preferred_col_order if c in valid_locations]

    for col in sorted_valid_locations:
        row = get_next_open_row(board, col)
        temp_board = [r[:] for r in board]
        drop_piece(temp_board, row, col, MY_PIECE)
        score = score_position(temp_board, MY_PIECE)
        
        if score > best_score:
            best_score = score
            best_col = col

    return best_col
