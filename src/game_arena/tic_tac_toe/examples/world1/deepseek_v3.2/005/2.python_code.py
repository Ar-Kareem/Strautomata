
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate win or block
    best_move = None
    
    # First, check if I can win in the next move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                if check_winner(board) == 1:
                    board[r][c] = 0  # reset
                    return (r, c)
                board[r][c] = 0
    
    # Then, check if opponent can win in the next move (block them)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = -1
                if check_winner(board) == -1:
                    board[r][c] = 0  # reset
                    best_move = (r, c)
                    # Don't return immediately, but this is the best block
                    # Actually we should block, so return now
                    return (r, c)
                board[r][c] = 0
    
    # If no immediate win/block, use minimax
    best_score = -math.inf
    best_move = None
    
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                score = minimax(board, 0, False, -math.inf, math.inf)
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    return best_move

def check_winner(board):
    # Check rows
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] and board[r][0] != 0:
            return board[r][0]
    # Check columns
    for c in range(3):
        if board[0][c] == board[1][c] == board[2][c] and board[0][c] != 0:
            return board[0][c]
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != 0:
        return board[0][2]
    # Check if game is still ongoing or draw
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return None  # Game not finished
    return 0  # Draw

def minimax(board, depth, is_maximizing, alpha, beta):
    result = check_winner(board)
    if result is not None:
        if result == 1:
            return 10 - depth
        elif result == -1:
            return depth - 10
        else:
            return 0
    
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
