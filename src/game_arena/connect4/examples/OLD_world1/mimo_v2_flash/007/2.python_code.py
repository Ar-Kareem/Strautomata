
import numpy as np
import random

# Define constants for the board dimensions
ROWS = 6
COLS = 7
EMPTY = 0
ME = 1
OPP = -1

# Precompute center column mask for heuristic center control
# Center column is index 3
CENTER_MASK = np.array([1 if c == 3 else 0 for c in range(COLS)])

def is_valid_location(board, col):
    """Check if the top cell of the column is empty."""
    return board[0][col] == 0

def get_valid_locations(board):
    """Return a list of columns that are not full."""
    return [c for c in range(COLS) if is_valid_location(board, c)]

def get_next_open_row(board, col):
    """Find the lowest empty row in a given column."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1

def drop_piece(board, col, piece):
    """Simulate dropping a piece and return the new board state."""
    new_board = np.copy(board)
    row = get_next_open_row(board, col)
    if row != -1:
        new_board[row][col] = piece
    return new_board

def check_win(board, piece):
    """
    Check if the given piece has won.
    Returns True if there is a winning line of 4, False otherwise.
    """
    # Check horizontal locations
    for r in range(ROWS):
        for c in range(COLS - 3):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True

    # Check vertical locations
    for r in range(ROWS - 3):
        for c in range(COLS):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True

    # Check positively sloped diagonals
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True

    # Check negatively sloped diagonals
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True

    return False

def evaluate_window(window, piece):
    """
    Evaluate a window of 4 cells and return a score.
    Positive score favors 'piece', negative score favors opponent.
    """
    score = 0
    opp_piece = -piece
    
    count_piece = np.count_nonzero(window == piece)
    count_empty = np.count_nonzero(window == 0)
    count_opp = np.count_nonzero(window == opp_piece)

    if count_piece == 4:
        score += 100000  # Winning move
    elif count_piece == 3 and count_empty == 1:
        score += 100     # Threat
    elif count_piece == 2 and count_empty == 2:
        score += 10      # Potential
        
    # Penalize opponent's threats heavily
    if count_opp == 3 and count_empty == 1:
        score -= 150     # Block opponent's immediate win threat
        
    if count_opp == 2 and count_empty == 2:
        score -= 15      # Slow opponent development

    return score

def score_position(board, piece):
    """
    Heuristic evaluation of the board state.
    """
    score = 0
    
    # Preference for center column control
    center_array = np.copy(board[:, 3])
    center_count = np.count_nonzero(center_array == piece)
    score += center_count * 4

    # Horizontal
    for r in range(ROWS):
        row_array = board[r, :]
        for c in range(COLS - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, piece)

    # Vertical
    for c in range(COLS):
        col_array = board[:, c]
        for r in range(ROWS - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, piece)

    # Positive Sloped Diagonal
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(np.array(window), piece)

    # Negative Sloped Diagonal
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+3-i][c+i] for i in range(4)]
            score += evaluate_window(np.array(window), piece)

    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """
    Minimax with Alpha-Beta pruning.
    Returns (score, column).
    """
    valid_locations = get_valid_locations(board)
    is_terminal = check_win(board, ME) or check_win(board, OPP) or len(valid_locations) == 0
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if check_win(board, ME):
                return (1000000000, None)
            elif check_win(board, OPP):
                return (-1000000000, None)
            else: # Game is over, no more valid moves
                return (0, None)
        else: # Depth is zero
            return (score_position(board, ME), None)

    if maximizing_player:
        value = -float('inf')
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            temp_board = np.copy(board)
            temp_board[row][col] = ME
            new_score = minimax(temp_board, depth-1, alpha, beta, False)[0]
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, column
    else:
        value = float('inf')
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            temp_board = np.copy(board)
            temp_board[row][col] = OPP
            new_score = minimax(temp_board, depth-1, alpha, beta, True)[0]
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, column

def policy(board: list[list[int]]) -> int:
    """
    Main policy function called by the game engine.
    """
    # Convert list to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Determine depth based on remaining moves (rough heuristic to keep within 1s)
    # 42 total cells. If board is somewhat full, increase depth.
    # But standard depth of 5 is usually safe for 1s limit on standard C4.
    depth = 6
    
    # Check for immediate win
    valid_locations = get_valid_locations(board_array)
    for col in valid_locations:
        temp_board = np.copy(board_array)
        row = get_next_open_row(temp_board, col)
        temp_board[row][col] = ME
        if check_win(temp_board, ME):
            return col
            
    # Check for immediate block
    for col in valid_locations:
        temp_board = np.copy(board_array)
        row = get_next_open_row(temp_board, col)
        temp_board[row][col] = OPP
        if check_win(temp_board, OPP):
            return col
            
    # Run Minimax for strategic play
    _, best_col = minimax(board_array, depth, -float('inf'), float('inf'), True)
    
    # Fallback if minimax returns None (unlikely with valid moves)
    if best_col is None:
        if valid_locations:
            return random.choice(valid_locations)
        
    return best_col
