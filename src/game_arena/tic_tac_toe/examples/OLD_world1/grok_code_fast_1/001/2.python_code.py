
import copy
import sys

INF = 1000

def check_winner(board):
    # Check all possible winning lines
    lines = [
        board[0], board[1], board[2],  # rows
        [board[i][0] for i in range(3)],  # col 0
        [board[i][1] for i in range(3)],  # col 1
        [board[i][2] for i in range(3)],  # col 2
        [board[i][i] for i in range(3)],  # diagonal
        [board[i][2-i] for i in range(3)]  # anti-diagonal
    ]
    for line in lines:
        if line[0] == line[1] == line[2] != 0:
            return line[0]
    return 0

def is_full(board):
    for row in board:
        if 0 in row:
            return False
    return True

def minimax(board, is_maximizer):
    winner = check_winner(board)
    if winner != 0:
        return winner if winner == 1 else -winner  # Normalize: +1 for maximizer win, -1 for minimizer win
    
    if is_full(board):
        return 0  # Draw
    
    if is_maximizer:  # My turn (1)
        max_eval = -INF
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval = minimax(board, False)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval)
        return max_eval
    else:  # Opponent's turn (-1)
        min_eval = INF
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval = minimax(board, True)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval)
        return min_eval

def policy(board: list[list[int]]) -> int:
    # Find the best move using minimax
    best_val = -INF
    best_move = -1
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                move_val = minimax(board, False)
                board[i][j] = 0
                if move_val > best_val:
                    best_val = move_val
                    best_move = i * 3 + j + 1
    return best_move
