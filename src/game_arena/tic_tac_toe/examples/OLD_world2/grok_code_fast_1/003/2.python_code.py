
import math

def is_win(board, player):
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    # Check columns
    for c in range(4):
        if all(board[r][c] == player for r in range(4)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    return False

def get_empty(board):
    return [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

def evaluate(board):
    if is_win(board, 1):
        return 10
    elif is_win(board, -1):
        return -10
    return 0  # Neutral for non-terminal states

def minimax(board, depth, is_maximizing, alpha=float('-inf'), beta=float('inf')):
    empties = get_empty(board)
    if depth == 0 or not empties:
        return evaluate(board)
    
    if is_maximizing:
        max_eval = float('-inf')
        for r, c in empties:
            board[r][c] = 1
            eval_ = minimax(board, depth - 1, False, alpha, beta)
            board[r][c] = 0
            max_eval = max(max_eval, eval_)
            alpha = max(alpha, eval_)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in empties:
            board[r][c] = -1
            eval_ = minimax(board, depth - 1, True, alpha, beta)
            board[r][c] = 0
            min_eval = min(min_eval, eval_)
            beta = min(beta, eval_)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    empties = get_empty(board)
    # Check for immediate win
    for r, c in empties:
        board[r][c] = 1
        if is_win(board, 1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    # Check for block opponent's win
    for r, c in empties:
        board[r][c] = -1
        if is_win(board, -1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    # Evaluate remaining moves with shallow minimax (depth 2)
    best_val = float('-inf')
    best_move = None
    for r, c in empties:
        board[r][c] = 1
        val = minimax(board, 2, False)
        board[r][c] = 0
        if val > best_val:
            best_val = val
            best_move = (r, c)
    if best_move:
        return best_move
    # Fallback to first empty (shouldn't happen)
    return empties[0] if empties else (0, 0)
