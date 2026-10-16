
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)

    # Check for immediate winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try this move
                board[i][j] = 1
                if is_winner(board, 1):
                    return (i, j)
                board[i][j] = 0  # Undo move

    # Check for immediate blocking move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try opponent's move
                board[i][j] = -1
                if is_winner(board, -1):
                    return (i, j)
                board[i][j] = 0  # Undo move

    # If no immediate win/block, use minimax
    best_score = -np.inf
    best_move = None

    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, False, -np.inf, np.inf)
                board[i][j] = 0

                if score > best_score:
                    best_score = score
                    best_move = (i, j)

    return best_move

def is_winner(board, player):
    # Check rows
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True

    # Check columns
    for j in range(3):
        if all(board[i][j] == player for i in range(3)):
            return True

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True

    return False

def is_draw(board):
    return np.all(board != 0)

def minimax(board, depth, is_maximizing, alpha, beta):
    # Check terminal states
    if is_winner(board, 1):
        return 10 - depth
    if is_winner(board, -1):
        return -10 + depth
    if is_draw(board):
        return 0

    if is_maximizing:
        best_score = -np.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    score = minimax(board, depth + 1, False, alpha, beta)
                    board[i][j] = 0
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
        return best_score
    else:
        best_score = np.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    score = minimax(board, depth + 1, True, alpha, beta)
                    board[i][j] = 0
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
        return best_score
