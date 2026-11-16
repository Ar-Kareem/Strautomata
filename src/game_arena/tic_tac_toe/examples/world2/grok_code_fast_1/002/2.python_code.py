
import numpy as np

WIN_LENGTH = 4

def is_terminal(board):
    # Check for win or draw
    for i in range(4):
        for j in range(4 - WIN_LENGTH + 1):
            # Row
            if all(board[i][j + k] == 1 for k in range(WIN_LENGTH)) or all(board[i][j + k] == -1 for k in range(WIN_LENGTH)):
                return board[i][j], True
            # Column
            if all(board[j + k][i] == 1 for k in range(WIN_LENGTH)) or all(board[j + k][i] == -1 for k in range(WIN_LENGTH)):
                return board[j][i], True
    # Diagonals
    for i in range(4 - WIN_LENGTH + 1):
        for j in range(4 - WIN_LENGTH + 1):
            if all(board[i + k][j + k] == 1 for k in range(WIN_LENGTH)):
                return 1, True
            if all(board[i + k][j + k] == -1 for k in range(WIN_LENGTH)):
                return -1, True
            if all(board[i + k][WIN_LENGTH - 1 - (j + k)] == 1 for k in range(WIN_LENGTH)):
                return 1, True
            if all(board[i + k][WIN_LENGTH - 1 - (j + k)] == -1 for k in range(WIN_LENGTH)):
                return -1, True
    # Check for draw (no empty cells)
    empty_cells = sum(row.count(0) for row in board)
    if empty_cells == 0:
        return 0, True
    return 0, False

def heuristic(board):
    # Simple heuristic: count threats
    score = 0
    for i in range(4):
        for j in range(4 - WIN_LENGTH + 1):
            # Row threats
            row_slice = [board[i][j + k] for k in range(WIN_LENGTH)]
            if row_slice.count(1) == WIN_LENGTH - 1 and row_slice.count(0) == 1:
                score += 10
            if row_slice.count(-1) == WIN_LENGTH - 1 and row_slice.count(0) == 1:
                score -= 10
            # Column threats
            col_slice = [board[j + k][i] for k in range(WIN_LENGTH)]
            if col_slice.count(1) == WIN_LENGTH - 1 and col_slice.count(0) == 1:
                score += 10
            if col_slice.count(-1) == WIN_LENGTH - 1 and col_slice.count(0) == 1:
                score -= 10
    # Diagonal threats
    for i in range(4 - WIN_LENGTH + 1):
        for j in range(4 - WIN_LENGTH + 1):
            diag_slice = [board[i + k][j + k] for k in range(WIN_LENGTH)]
            if diag_slice.count(1) == WIN_LENGTH - 1 and diag_slice.count(0) == 1:
                score += 10
            if diag_slice.count(-1) == WIN_LENGTH - 1 and diag_slice.count(0) == 1:
                score -= 10
            anti_diag_slice = [board[i + k][WIN_LENGTH - 1 - (j + k)] for k in range(WIN_LENGTH)]
            if anti_diag_slice.count(1) == WIN_LENGTH - 1 and anti_diag_slice.count(0) == 1:
                score += 10
            if anti_diag_slice.count(-1) == WIN_LENGTH - 1 and anti_diag_slice.count(0) == 1:
                score -= 10
    return score

def minimax(board, depth, is_max, alpha, beta, max_depth=6):
    winner, terminal = is_terminal(board)
    if terminal or depth >= max_depth:
        if terminal:
            return 1000 if winner == 1 else -1000 if winner == -1 else 0
        else:
            return heuristic(board)
    
    if is_max:
        max_eval = -float('inf')
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval = minimax(board, depth + 1, False, alpha, beta, max_depth)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval = minimax(board, depth + 1, True, alpha, beta, max_depth)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
        return min_eval

def policy(board):
    best_move = None
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                move_value = minimax(board, 1, False, alpha, beta)
                board[i][j] = 0
                if move_value > best_value:
                    best_value = move_value
                    best_move = (i, j)
    return best_move
