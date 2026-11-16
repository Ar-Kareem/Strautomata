
import numpy as np

def is_win(board, player):
    # Check rows
    for r in range(4):
        if all(board[r][c] == player for c in range(4)):
            return True
    # Check columns
    for c in range(4):
        if all(board[r][c] == player for r in range(4)):
            return True
    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    # Check anti-diagonal
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    return False

def is_full(board):
    return all(board[r][c] != 0 for r in range(4) for c in range(4))

def heuristic(board):
    lines = []
    # Rows
    for r in range(4):
        lines.append([(r, c) for c in range(4)])
    # Columns
    for c in range(4):
        lines.append([(r, c) for r in range(4)])
    # Main diagonal
    lines.append([(i, i) for i in range(4)])
    # Anti-diagonal
    lines.append([(i, 3 - i) for i in range(4)])
    
    score = 0
    for line in lines:
        my_count = sum(1 for r, c in line if board[r][c] == 1)
        opp_count = sum(1 for r, c in line if board[r][c] == -1)
        empty_count = 4 - my_count - opp_count
        if opp_count == 0:
            score += my_count ** 2
        if my_count == 0:
            score -= opp_count ** 2
    return score

def minimax(board, depth, maximizing_player, alpha=-float('inf'), beta=float('inf')):
    if is_win(board, 1):
        return float('inf')
    if is_win(board, -1):
        return -float('inf')
    if is_full(board) or depth == 0:
        return heuristic(board)
    
    if maximizing_player:
        max_eval = -float('inf')
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
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
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    board[r][c] = -1
                    eval_ = minimax(board, depth - 1, True, alpha, beta)
                    board[r][c] = 0
                    min_eval = min(min_eval, eval_)
                    beta = min(beta, eval_)
                    if beta <= alpha:
                        break
        return min_eval

def policy(board):
    best_move = None
    best_value = -float('inf')
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                move_value = minimax(board, 4, False)
                board[r][c] = 0
                if move_value > best_value:
                    best_value = move_value
                    best_move = (r, c)
    return best_move
