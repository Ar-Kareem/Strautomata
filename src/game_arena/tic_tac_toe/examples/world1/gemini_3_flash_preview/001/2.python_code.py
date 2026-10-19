
import math

def check_winner(board):
    # Check rows and columns
    for i in range(3):
        if sum(board[i]) == 3: return 1
        if sum(board[i]) == -3: return -1
        if sum(board[j][i] for j in range(3)) == 3: return 1
        if sum(board[j][i] for j in range(3)) == -3: return -1
    
    # Check diagonals
    if board[0][0] + board[1][1] + board[2][2] == 3: return 1
    if board[0][2] + board[1][1] + board[2][0] == 3: return 1
    if board[0][0] + board[1][1] + board[2][2] == -3: return -1
    if board[0][2] + board[1][1] + board[2][0] == -3: return -1
    
    # Check for draw or ongoing
    if all(cell != 0 for row in board for cell in row):
        return 0
    return None

def minimax(board, depth, is_maximizing, alpha, beta):
    result = check_winner(board)
    if result is not None:
        return result

    if is_maximizing:
        best_score = -math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    score = minimax(board, depth + 1, False, alpha, beta)
                    board[r][c] = 0
                    best_score = max(score, best_score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break
        return best_score
    else:
        best_score = math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    score = minimax(board, depth + 1, True, alpha, beta)
                    board[r][c] = 0
                    best_score = min(score, best_score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
        return best_score

def policy(board: list[list[int]]) -> tuple[int, int]:
    best_val = -math.inf
    move = (-1, -1)
    
    # Optimization: if board is empty, take the center
    if all(cell == 0 for row in board for cell in row):
        return (1, 1)

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                move_val = minimax(board, 0, False, -math.inf, math.inf)
                board[r][c] = 0
                
                if move_val > best_val:
                    best_val = move_val
                    move = (r, c)
                    
    return move
