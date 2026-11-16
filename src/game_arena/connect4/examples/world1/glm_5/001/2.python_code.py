
import math
import random

# Constants
ROW_COUNT = 6
COLUMN_COUNT = 7
PLAYER = 1
OPPONENT = -1
EMPTY = 0
WIN_LENGTH = 4

def policy(board: list[list[int]]) -> int:
    """
    Determines the best move for the current player using Minimax with Alpha-Beta pruning.
    """
    valid_columns = get_valid_columns(board)
    if not valid_columns:
        return 0 # Should not happen in a valid game

    # 1. Check for immediate winning move
    for col in valid_columns:
        row = get_next_open_row(board, col)
        board[row][col] = PLAYER
        if winning_move(board, PLAYER):
            board[row][col] = EMPTY
            return col
        board[row][col] = EMPTY

    # 2. Check for immediate blocking move (opponent wins next)
    for col in valid_columns:
        row = get_next_open_row(board, col)
        board[row][col] = OPPONENT
        if winning_move(board, OPPONENT):
            board[row][col] = EMPTY
            return col
        board[row][col] = EMPTY

    # 3. Minimax with Alpha-Beta Pruning
    # Depth 5 offers a good balance between foresight and speed in Python
    depth = 5
    best_score = -math.inf
    best_cols = []
    
    # Order columns center-first to improve pruning
    col_order = [3, 2, 4, 1, 5, 0, 6]
    ordered_valid_columns = [c for c in col_order if c in valid_columns]

    for col in ordered_valid_columns:
        row = get_next_open_row(board, col)
        board[row][col] = PLAYER
        score = minimax(board, depth - 1, -math.inf, math.inf, False)
        board[row][col] = EMPTY
        
        if score > best_score:
            best_score = score
            best_cols = [col]
        elif score == best_score:
            best_cols.append(col)

    # Prefer center columns if multiple moves have same score
    if len(best_cols) > 1:
        center_pref = {3: 0, 2: 1, 4: 1, 1: 2, 5: 2, 0: 3, 6: 3}
        best_cols.sort(key=lambda x: center_pref.get(x, 4))
    
    return best_cols[0]

def minimax(board, depth, alpha, beta, maximizingPlayer):
    valid_columns = get_valid_columns(board)
    is_terminal = (winning_move(board, PLAYER) or winning_move(board, OPPONENT) or len(valid_columns) == 0)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, PLAYER):
                return 100000000000
            elif winning_move(board, OPPONENT):
                return -100000000000
            else:
                return 0 # Draw
        else:
            return score_position(board, PLAYER)

    col_order = [3, 2, 4, 1, 5, 0, 6]
    ordered_valid_columns = [c for c in col_order if c in valid_columns]

    if maximizingPlayer:
        value = -math.inf
        for col in ordered_valid_columns:
            row = get_next_open_row(board, col)
            board[row][col] = PLAYER
            new_score = minimax(board, depth - 1, alpha, beta, False)
            board[row][col] = EMPTY
            value = max(value, new_score)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = math.inf
        for col in ordered_valid_columns:
            row = get_next_open_row(board, col)
            board[row][col] = OPPONENT
            new_score = minimax(board, depth - 1, alpha, beta, True)
            board[row][col] = EMPTY
            value = min(value, new_score)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def score_position(board, player):
    score = 0

    # Score Center column
    center_array = [row[3] for row in board]
    center_count = center_array.count(player)
    score += center_count * 3

    # Score Horizontal
    for r in range(ROW_COUNT):
        row_array = board[r]
        for c in range(COLUMN_COUNT - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, player)

    # Score Vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            window = [board[r+i][c] for i in range(4)]
            score += evaluate_window(window, player)

    # Score Positive Diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, player)

    # Score Negative Diagonal
    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, player)

    return score

def evaluate_window(window, player):
    score = 0
    opp_piece = OPPONENT if player == PLAYER else PLAYER
    empty = EMPTY

    num_player = window.count(player)
    num_opp = window.count(opp_piece)
    num_empty = window.count(empty)

    if num_player == 4:
        score += 100
    elif num_player == 3 and num_empty == 1:
        score += 5
    elif num_player == 2 and num_empty == 2:
        score += 2

    if num_opp == 3 and num_empty == 1:
        score -= 4
        
    return score

def get_valid_columns(board):
    valid_columns = []
    for col in range(COLUMN_COUNT):
        if board[0][col] == EMPTY:
            valid_columns.append(col)
    return valid_columns

def get_next_open_row(board, col):
    for r in range(ROW_COUNT - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None

def winning_move(board, player):
    # Check horizontal
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT):
            if board[r][c] == player and board[r][c+1] == player and board[r][c+2] == player and board[r][c+3] == player:
                return True

    # Check vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == player and board[r+1][c] == player and board[r+2][c] == player and board[r+3][c] == player:
                return True

    # Check positively sloped diagonals
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == player and board[r+1][c+1] == player and board[r+2][c+2] == player and board[r+3][c+3] == player:
                return True

    # Check negatively sloped diagonals
    for c in range(COLUMN_COUNT - 3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == player and board[r-1][c+1] == player and board[r-2][c+2] == player and board[r-3][c+3] == player:
                return True
    return False
