
import math

# Constants
ROW_COUNT = 6
COL_COUNT = 7
PLAYER = 1
OPPONENT = -1
EMPTY = 0

def get_valid_moves(board):
    """Returns a list of columns that are not full."""
    return [c for c in range(COL_COUNT) if board[0][c] == 0]

def get_next_open_row(board, col):
    """Finds the lowest empty row in the given column."""
    for r in range(ROW_COUNT - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1

def check_win(board, piece):
    """Checks if the specified player has won."""
    # Horizontal
    for r in range(ROW_COUNT):
        for c in range(COL_COUNT - 3):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True
    # Vertical
    for c in range(COL_COUNT):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True
    # Positive Diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COL_COUNT - 3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True
    # Negative Diagonal
    for r in range(3, ROW_COUNT):
        for c in range(COL_COUNT - 3):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True
    return False

def evaluate_window(window, piece):
    """Evaluates a window of 4 cells for scoring."""
    score = 0
    opp_piece = OPPONENT if piece == PLAYER else PLAYER

    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2

    if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
        score -= 4

    return score

def score_position(board, piece):
    """Scores the entire board state for the given piece."""
    score = 0

    # Score Center Column (preference for center control)
    center_array = [row[3] for row in board]
    center_count = center_array.count(piece)
    score += center_count * 3

    # Score Horizontal
    for r in range(ROW_COUNT):
        row_array = board[r]
        for c in range(COL_COUNT - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, piece)

    # Score Vertical
    for c in range(COL_COUNT):
        col_array = [board[r][c] for r in range(ROW_COUNT)]
        for r in range(ROW_COUNT - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, piece)

    # Score Positive Diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COL_COUNT - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    # Score Negative Diagonal
    for r in range(3, ROW_COUNT):
        for c in range(COL_COUNT - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score

def is_terminal_node(board):
    """Checks if the game has ended."""
    return check_win(board, PLAYER) or check_win(board, OPPONENT) or len(get_valid_moves(board)) == 0

def minimax(board, depth, alpha, beta, maximizingPlayer):
    """Minimax algorithm with Alpha-Beta pruning."""
    valid_moves = get_valid_moves(board)
    terminal = is_terminal_node(board)

    if depth == 0 or terminal:
        if terminal:
            if check_win(board, PLAYER):
                return (None, 100000000000000)
            elif check_win(board, OPPONENT):
                return (None, -100000000000000)
            else: # Game is over, no more valid moves
                return (None, 0)
        else: # Depth is 0
            return (None, score_position(board, PLAYER))

    # Move ordering: prioritize center columns to improve pruning
    valid_moves.sort(key=lambda x: -abs(x - 3))

    if maximizingPlayer:
        value = -math.inf
        column = valid_moves[0]
        for col in valid_moves:
            row = get_next_open_row(board, col)
            if row == -1: continue
            
            b_copy = [r[:] for r in board]
            b_copy[row][col] = PLAYER
            new_score = minimax(b_copy, depth - 1, alpha, beta, False)[1]
            
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value

    else: # Minimizing Player
        value = math.inf
        column = valid_moves[0]
        for col in valid_moves:
            row = get_next_open_row(board, col)
            if row == -1: continue

            b_copy = [r[:] for r in board]
            b_copy[row][col] = OPPONENT
            new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
            
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return column, value

def policy(board: list[list[int]]) -> int:
    """Main function to determine the next move."""
    valid_moves = get_valid_moves(board)
    
    # If no moves available (should not happen in a valid game state)
    if not valid_moves:
        return 0

    # 1. Check for immediate winning move
    for col in valid_moves:
        row = get_next_open_row(board, col)
        temp_board = [r[:] for r in board]
        temp_board[row][col] = PLAYER
        if check_win(temp_board, PLAYER):
            return col

    # 2. Check for immediate blocking move
    for col in valid_moves:
        row = get_next_open_row(board, col)
        temp_board = [r[:] for r in board]
        temp_board[row][col] = OPPONENT
        if check_win(temp_board, OPPONENT):
            return col

    # 3. Use Minimax for deeper strategy
    # Depth 5 is generally safe for 1 second time limit in Python
    col, _ = minimax(board, 5, -math.inf, math.inf, True)
    
    return col
