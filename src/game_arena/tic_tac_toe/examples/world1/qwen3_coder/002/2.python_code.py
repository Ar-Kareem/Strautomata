
import copy
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to be more convenient (1 is me, -1 is opponent)
    # Board is already in the right format: 1 = me, -1 = opponent, 0 = empty
    
    # Check for immediate win
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing my piece here
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0  # Undo move
                    return (i, j)
                board[i][j] = 0  # Undo move
    
    # Check for immediate threat to block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing opponent's piece here
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0  # Undo move
                    return (i, j)
                board[i][j] = 0  # Undo move
    
    # If no immediate win or block, use minimax
    best_score = float('-inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, False)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move

def check_winner(board):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != 0:
            return row[0]
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != 0:
            return board[0][col]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    
    # Check for draw or ongoing game
    for row in board:
        if 0 in row:
            return 0  # Game ongoing
    
    return 0  # Draw

def is_board_full(board):
    for row in board:
        if 0 in row:
            return False
    return True

def minimax(board, depth, is_maximizing):
    winner = check_winner(board)
    
    # Terminal states
    if winner == 1:  # I win
        return 10 - depth
    elif winner == -1:  # Opponent wins
        return depth - 10
    elif is_board_full(board):  # Draw
        return 0
    
    if is_maximizing:
        max_eval = float('-inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval_score = minimax(board, depth + 1, False)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval_score)
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval_score = minimax(board, depth + 1, True)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval_score)
        return min_eval
