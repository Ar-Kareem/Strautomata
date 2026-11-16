
import numpy as np
from math import inf
from random import choice

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert the board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Find all empty positions
    empty_positions = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    # If there's a winning move, take it
    for move in empty_positions:
        temp_board = board_array.copy()
        temp_board[move] = 1
        if check_win(temp_board, 1):
            return move
    
    # If opponent has a winning move, block it
    for move in empty_positions:
        temp_board = board_array.copy()
        temp_board[move] = -1
        if check_win(temp_board, -1):
            return move
    
    # If center is available, consider taking it first
    center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    center_positions = [pos for pos in center_positions if pos in empty_positions]
    if center_positions:
        # Try to take the most centered position
        best_center = None
        min_distance = float('inf')
        center_point = (1.5, 1.5)  # Center of 4x4 board
        for pos in center_positions:
            distance = (pos[0] - center_point[0])**2 + (pos[1] - center_point[1])**2
            if distance < min_distance:
                min_distance = distance
                best_center = pos
        if best_center:
            return best_center
    
    # Use minimax with alpha-beta pruning for deeper search
    best_score = -inf
    best_move = None
    alpha = -inf
    beta = inf
    
    for move in empty_positions:
        temp_board = board_array.copy()
        temp_board[move] = 1
        score = minimax(temp_board, 0, False, alpha, beta)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)
    
    # If somehow best_move is None (shouldn't happen), pick randomly
    return best_move if best_move else choice(empty_positions)

def minimax(board, depth, is_maximizing, alpha, beta):
    winner = check_win(board, 1) or check_win(board, -1)
    
    if winner == 1:
        return 10 - depth
    elif winner == -1:
        return depth - 10
    elif np.count_nonzero(board == 0) == 0:
        return 0
    
    if is_maximizing:
        best_score = -inf
        empty_positions = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
        for move in empty_positions:
            temp_board = board.copy()
            temp_board[move] = 1
            score = minimax(temp_board, depth + 1, False, alpha, beta)
            best_score = max(score, best_score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = inf
        empty_positions = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
        for move in empty_positions:
            temp_board = board.copy()
            temp_board[move] = -1
            score = minimax(temp_board, depth + 1, True, alpha, beta)
            best_score = min(score, best_score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score

def check_win(board, player):
    # Check rows and columns
    for i in range(4):
        if np.all(board[i, :] == player) or np.all(board[:, i] == player):
            return True
    
    # Check diagonals
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    
    # Check 2x2 squares (for 4x4 board)
    for i in range(3):
        for j in range(3):
            if np.all(board[i:i+2, j:j+2] == player):
                return True
    
    return False
