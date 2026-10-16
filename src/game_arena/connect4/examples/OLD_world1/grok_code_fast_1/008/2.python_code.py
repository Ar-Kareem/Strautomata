
import copy

ROWS = 6
COLS = 7

def get_possible_moves(board):
    moves = []
    for col in range(COLS):
        if board[0][col] == 0:
            moves.append(col)
    return moves

def drop_disc(board, col, player):
    new_board = [row[:] for row in board]
    for row in range(ROWS - 1, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            return new_board
    return None

def get_windows(board):
    windows = []
    # Horizontal
    for row in range(ROWS):
        for col in range(COLS - 3):
            windows.append([board[row][col + i] for i in range(4)])
    # Vertical
    for col in range(COLS):
        for row in range(ROWS - 3):
            windows.append([board[row + i][col] for i in range(4)])
    # Diagonal /
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            windows.append([board[row + i][col + i] for i in range(4)])
    # Diagonal \
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            windows.append([board[row + 3 - i][col + i] for i in range(4)])
    return windows

def is_win(board, player):
    for window in get_windows(board):
        if all(x == player for x in window):
            return True
    return False

def evaluate(board):
    score = 0
    for window in get_windows(board):
        count_me = sum(1 for x in window if x == 1)
        count_op = sum(1 for x in window if x == -1)
        blanks = 4 - count_me - count_op
        if count_op == 0 and blanks == 4 - count_me:
            score += 10 ** count_me
        if count_me == 0 and blanks == 4 - count_op:
            score -= 10 ** count_op
    return score

def minimax(board, depth, maximizing):
    if is_win(board, 1):
        return 10000
    if is_win(board, -1):
        return -10000
    if depth == 0:
        return evaluate(board)
    
    player = 1 if maximizing else -1
    moves = get_possible_moves(board)
    if maximizing:
        max_eval = -float('inf')
        for col in moves:
            new_board = drop_disc(board, col, player)
            eval = minimax(new_board, depth - 1, False)
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        for col in moves:
            new_board = drop_disc(board, col, player)
            eval = minimax(new_board, depth - 1, True)
            min_eval = min(min_eval, eval)
        return min_eval

def policy(board):
    best_score = -float('inf')
    best_col = 0
    for col in get_possible_moves(board):
        new_board = drop_disc(board, col, 1)
        score = minimax(new_board, 4, False)  # depth=4, opponent minimizes
        if score > best_score:
            best_score = score
            best_col = col
    return best_col
