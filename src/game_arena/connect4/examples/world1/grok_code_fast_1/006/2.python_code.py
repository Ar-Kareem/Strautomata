
import copy
import time

ROWS = 6
COLS = 7

def is_valid_move(board, col):
    return board[0][col] == 0

def get_next_open_row(board, col):
    for r in range(ROWS-1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def winning_move(board, piece):
    # Check horizontal locations for win
    for c in range(COLS-3):
        for r in range(ROWS):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True

    # Check vertical locations for win
    for c in range(COLS):
        for r in range(ROWS-3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True

    # Check positively sloped diaganols
    for c in range(COLS-3):
        for r in range(ROWS-3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True

    # Check negatively sloped diaganols
    for c in range(COLS-3):
        for r in range(3, ROWS):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True

    return False

def evaluate_window(window, piece):
    score = 0
    opp_piece = -piece

    if window.count(piece) == 4:
        score += 10000
    elif window.count(piece) == 3 and window.count(0) == 1:
        score += 100
    elif window.count(piece) == 2 and window.count(0) == 2:
        score += 10
    elif window.count(piece) == 1 and window.count(0) == 3:
        score += 1

    if window.count(opp_piece) == 3 and window.count(0) == 1:
        score -= 100

    return score

def score_position(board, piece):
    score = 0

    ## Score center column
    center_array = [board[i][COLS//2] for i in range(ROWS)]
    center_count = center_array.count(piece)
    score += center_count * 3

    ## Score Horizontal
    for r in range(ROWS):
        row_array = board[r]
        for c in range(COLS-3):
            window = row_array[c:c+4]
            score += evaluate_window(window, piece)

    ## Score Vertical
    for c in range(COLS):
        col_array = [board[i][c] for i in range(ROWS)]
        for r in range(ROWS-3):
            window = col_array[r:r+4]
            score += evaluate_window(window, piece)

    ## Score positive sloped diagonal
    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = [board[r+3-i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score

def is_terminal_node(board):
    return winning_move(board, 1) or winning_move(board, -1) or len(get_valid_moves(board)) == 0

def minimax(board, depth, alpha, beta, maximizingPlayer, piece):
    valid_moves = get_valid_moves(board)
    is_terminal = is_terminal_node(board)
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, piece):  # Maximizing player wins (you)
                return (None, 100000000000000)
            elif winning_move(board, -piece):
                return (None, -100000000000000)
            else: # Game is over, no more valid moves
                return (None, 0)
        else: # Depth is zero
            return (None, score_position(board, piece))
    if maximizingPlayer:
        value = -float('inf')
        best_col = valid_moves[0] if valid_moves else 0
        for col in valid_moves:
            row = get_next_open_row(board, col)
            temp_board = copy.deepcopy(board)
            drop_piece(temp_board, row, col, piece)
            new_score = minimax(temp_board, depth-1, alpha, beta, False, piece)[1]
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value

    else: # Minimizing player
        value = float('inf')
        best_col = valid_moves[0] if valid_moves else 0
        for col in valid_moves:
            row = get_next_open_row(board, col)
            temp_board = copy.deepcopy(board)
            drop_piece(temp_board, row, col, -piece)
            new_score = minimax(temp_board, depth-1, alpha, beta, True, piece)[1]
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value

def get_valid_moves(board):
    valid_moves = []
    for col in range(COLS):
        if is_valid_move(board, col):
            valid_moves.append(col)
    return valid_moves

def find_best_move(board, piece):
    valid_moves = get_valid_moves(board)
    best_col, _ = minimax(board, 3, -float('inf'), float('inf'), True, piece)
    if best_col in valid_moves:
        return best_col
    else:
        return valid_moves[0] if valid_moves else 0

def policy(board: list[list[int]]) -> int:
    return find_best_move(board, 1)
