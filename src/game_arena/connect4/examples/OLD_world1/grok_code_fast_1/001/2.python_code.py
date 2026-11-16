
import math
import copy

ROWS = 6
COLS = 7
DEPTH = 4  # Search depth for minimax

POSITION_SCORES = [
    [3, 4, 5, 7, 5, 4, 3],
    [4, 6, 8, 10, 8, 6, 4],
    [5, 8, 11, 13, 11, 8, 5],
    [5, 8, 11, 13, 11, 8, 5],
    [4, 6, 8, 10, 8, 6, 4],
    [3, 4, 5, 7, 5, 4, 3]
]

def is_valid_move(board, col):
    return board[0][col] == 0

def get_next_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1

def check_win(board, p):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == p for i in range(4)):
                return True
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == p for i in range(4)):
                return True
    # Diagonal /
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == p for i in range(4)):
                return True
    # Diagonal \
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            if all(board[r + i][c - i] == p for i in range(4)):
                return True
    return False

def is_terminal(board):
    return check_win(board, 1) or check_win(board, -1) or not any(is_valid_move(board, c) for c in range(COLS))

def evaluate_window(window, p):
    opp = -p
    empty = 0
    count_p = sum(1 for x in window if x == p)
    count_empty = sum(1 for x in window if x == empty)
    count_opp = sum(1 for x in window if x == opp)
    if count_opp == 0:
        if count_p == 4:
            return 100
        elif count_p == 3 and count_empty == 1:
            return 10
        elif count_p == 2 and count_empty == 2:
            return 2
    elif count_p == 0:
        if count_opp == 3 and count_empty == 1:
            return -80
        elif count_opp == 2 and count_empty == 2:
            return -2
    return 0

def evaluate_lines(board, p):
    score = 0
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += evaluate_window(window, p)
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r + i][c] for i in range(4)]
            score += evaluate_window(window, p)
    # Diagonal /
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window, p)
    # Diagonal \
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            window = [board[r + i][c - i] for i in range(4)]
            score += evaluate_window(window, p)
    return score

def evaluate(board):
    if check_win(board, 1):
        return 10000
    elif check_win(board, -1):
        return -10000
    score = 0
    # Position-based score
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 1:
                score += POSITION_SCORES[r][c]
            elif board[r][c] == -1:
                score -= POSITION_SCORES[r][c]
    # Window-based score
    score += evaluate_lines(board, 1)
    score -= evaluate_lines(board, -1)
    return score

def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or is_terminal(board):
        return evaluate(board)
    if maximizing:
        max_eval = -math.inf
        for col in range(COLS):
            if is_valid_move(board, col):
                row = get_next_row(board, col)
                board[row][col] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[row][col] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
        return max_eval
    else:
        min_eval = math.inf
        for col in range(COLS):
            if is_valid_move(board, col):
                row = get_next_row(board, col)
                board[row][col] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
        return min_eval

def policy(board: list[list[int]]) -> int:
    board_copy = copy.deepcopy(board)
    best_col = -1
    best_val = -math.inf
    for col in range(COLS):
        if is_valid_move(board_copy, col):
            row = get_next_row(board_copy, col)
            board_copy[row][col] = 1
            val = minimax(board_copy, DEPTH, -math.inf, math.inf, False)
            board_copy[row][col] = 0
            if val > best_val:
                best_val = val
                best_col = col
    return best_col
