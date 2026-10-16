
import copy

ROWS = 6
COLS = 7

def is_valid(board, col):
    return 0 <= col < COLS and board[0][col] == 0

def drop(board, col, player):
    new_board = copy.deepcopy(board)
    for r in range(ROWS - 1, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            return new_board
    return None  # Should not happen

def check_win(board, player):
    # Check horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # Check vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # Check diagonal /
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # Check diagonal \
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + 3 - i] == player for i in range(4)):
                return True
    return False

def evaluate(board):
    if check_win(board, 1):
        return 999999
    if check_win(board, -1):
        return -999999
    score = 0
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            piece = sum(board[r][c + i] for i in range(4))
            score += piece * 10
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            piece = sum(board[r + i][c] for i in range(4))
            score += piece * 10
    # Diagonal /
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            piece = sum(board[r + i][c + i] for i in range(4))
            score += piece * 10
    # Diagonal \
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            piece = sum(board[r + i][c + 3 - i] for i in range(4))
            score += piece * 10
    # Center column bonus
    for r in range(ROWS):
        score += board[r][3] * 1
    return score

def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or check_win(board, 1) or check_win(board, -1):
        return evaluate(board)
    if maximizing:
        max_eval = -float('inf')
        for col in range(COLS):
            if is_valid(board, col):
                new_board = drop(board, col, 1)
                if new_board is not None:
                    eval_val = minimax(new_board, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval_val)
                    alpha = max(alpha, eval_val)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for col in range(COLS):
            if is_valid(board, col):
                new_board = drop(board, col, -1)
                if new_board is not None:
                    eval_val = minimax(new_board, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval_val)
                    beta = min(beta, eval_val)
                    if beta <= alpha:
                        break
        return min_eval

def policy(board):
    column_order = [3, 2, 4, 1, 5, 0, 6]
    best_col = -1
    best_value = -float('inf')
    for col in column_order:
        if is_valid(board, col):
            new_board = drop(board, col, 1)
            if new_board is not None:
                value = minimax(new_board, 5, -float('inf'), float('inf'), False)
                if value > best_value:
                    best_value = value
                    best_col = col
    return best_col
