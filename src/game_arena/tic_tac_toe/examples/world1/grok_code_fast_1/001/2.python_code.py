
from math import inf

def is_winner(board, player):
    # Check rows, columns, and diagonals for a win
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):  # row i
            return True
        if all(board[j][i] == player for j in range(3)):  # column i
            return True
    # Diagonals
    if all(board[j][j] == player for j in range(3)):  # main diagonal
        return True
    if all(board[j][2 - j] == player for j in range(3)):  # anti-diagonal
        return True
    return False

def is_full(board):
    return all(board[i][j] != 0 for i in range(3) for j in range(3))

def minimax(board, depth, is_maximizing, alpha, beta):
    if is_winner(board, 1):
        return 1 - depth * 0.01  # Favor quicker wins
    if is_winner(board, -1):
        return -1 + depth * 0.01  # Favor delaying losses (but optimal anyway)
    if is_full(board):
        return 0
    
    if is_maximizing:
        max_eval = -inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval = minimax(board, depth + 1, False, alpha, beta)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
        return max_eval
    else:
        min_eval = inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval = minimax(board, depth + 1, True, alpha, beta)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
        return min_eval

def policy(board):
    best_eval = -inf
    best_move = None
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                eval = minimax(board, 0, False, -inf, inf)
                board[i][j] = 0
                if eval > best_eval:
                    best_eval = eval
                    best_move = (i, j)
    return best_move
