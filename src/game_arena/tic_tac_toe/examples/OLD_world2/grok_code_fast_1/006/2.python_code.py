
import numpy as np

def get_empty(board):
    return [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]

def check_win(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    return False

def evaluate_line(line):
    if 1 in line and -1 in line:
        return 0
    num_ones = sum(1 for x in line if x == 1)
    num_minus = sum(1 for x in line if x == -1)
    if num_ones > 0:
        return num_ones
    elif num_minus > 0:
        return -num_minus
    return 0

def heuristic(board):
    score = 0
    # Evaluate rows and columns
    for i in range(4):
        row = board[i]
        score += evaluate_line(row)
        col = [board[j][i] for j in range(4)]
        score += evaluate_line(col)
    # Evaluate diagonals
    diag1 = [board[i][i] for i in range(4)]
    score += evaluate_line(diag1)
    diag2 = [board[i][3 - i] for i in range(4)]
    score += evaluate_line(diag2)
    return score

def minimax(board, depth, maximizing, alpha=-np.inf, beta=np.inf):
    if check_win(board, 1):
        return 100 - depth
    if check_win(board, -1):
        return -100 + depth
    if len(get_empty(board)) == 0:
        return 0
    if depth > 4:  # Limit depth for performance
        return heuristic(board)
    if maximizing:
        max_eval = -np.inf
        for move in get_empty(board):
            board[move] = 1
            eval = minimax(board, depth + 1, False, alpha, beta)
            board[move] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = np.inf
        for move in get_empty(board):
            board[move] = -1
            eval = minimax(board, depth + 1, True, alpha, beta)
            board[move] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    empty_moves = get_empty(board)
    if not empty_moves:
        # This shouldn't happen, but default to (0,0)
        return (0, 0)
    best_score = -np.inf
    best_move = empty_moves[0]
    for move in empty_moves:
        board[move] = 1
        score = minimax(board, 0, False)
        board[move] = 0
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
