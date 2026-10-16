
import numpy as np
from collections import Counter

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    rows, cols = board.shape
    
    # Check for immediate winning moves
    for col in range(cols):
        if is_valid_move(board, col):
            board_copy = board.copy()
            drop_disc(board_copy, col, 1)
            if check_winner(board_copy) == 1:
                return col
    
    # Check for blocking moves (opponent's winning moves)
    for col in range(cols):
        if is_valid_move(board, col):
            board_copy = board.copy()
            drop_disc(board_copy, col, -1)
            if check_winner(board_copy) == -1:
                return col
    
    # Evaluate positions using a heuristic
    scores = []
    for col in range(cols):
        if is_valid_move(board, col):
            board_copy = board.copy()
            drop_disc(board_copy, col, 1)
            score = evaluate_position(board_copy, 1)
            scores.append((score, col))
        else:
            scores.append((-float('inf'), col))
    
    # Choose the column with the highest score
    best_score, best_col = max(scores, key=lambda x: x[0])
    return best_col

def is_valid_move(board, col):
    """Check if a move is valid (column not full)"""
    return board[0][col] == 0

def drop_disc(board, col, player):
    """Drop a disc in the specified column"""
    for row in reversed(range(board.shape[0])):
        if board[row][col] == 0:
            board[row][col] = player
            break

def check_winner(board):
    """Check if there's a winner on the board"""
    rows, cols = board.shape
    
    # Check horizontal
    for row in range(rows):
        for col in range(cols - 3):
            if all(board[row][col + i] == 1 for i in range(4)):
                return 1
            elif all(board[row][col + i] == -1 for i in range(4)):
                return -1
    
    # Check vertical
    for row in range(rows - 3):
        for col in range(cols):
            if all(board[row + i][col] == 1 for i in range(4)):
                return 1
            elif all(board[row + i][col] == -1 for i in range(4)):
                return -1
    
    # Check diagonal (top-left to bottom-right)
    for row in range(rows - 3):
        for col in range(cols - 3):
            if all(board[row + i][col + i] == 1 for i in range(4)):
                return 1
            elif all(board[row + i][col + i] == -1 for i in range(4)):
                return -1
    
    # Check diagonal (top-right to bottom-left)
    for row in range(rows - 3):
        for col in range(3, cols):
            if all(board[row + i][col - i] == 1 for i in range(4)):
                return 1
            elif all(board[row + i][col - i] == -1 for i in range(4)):
                return -1
    
    return 0

def evaluate_position(board, player):
    """Evaluate the position using a simple heuristic"""
    score = 0
    rows, cols = board.shape
    
    # Score patterns that could lead to four in a row
    # Center column preference
    center_counts = Counter(board[:, cols//2])
    score += center_counts[1] * 3
    
    # Horizontal patterns
    for row in range(rows):
        for col in range(cols - 3):
            window = board[row, col:col + 4]
            score += evaluate_window(window, player)
    
    # Vertical patterns
    for row in range(rows - 3):
        for col in range(cols):
            window = board[row:row + 4, col]
            score += evaluate_window(window, player)
    
    # Diagonal patterns (top-left to bottom-right)
    for row in range(rows - 3):
        for col in range(cols - 3):
            window = [board[row + i][col + i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Diagonal patterns (top-right to bottom-left)
    for row in range(rows - 3):
        for col in range(3, cols):
            window = [board[row + i][col - i] for i in range(4)]
            score += evaluate_window(window, player)
    
    return score

def evaluate_window(window, player):
    """Evaluate a window of 4 positions"""
    score = 0
    opponent = -player
    
    # Count discs in window
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(0)
    
    # Score based on pattern
    if player_count == 4:
        score += 100
    elif player_count == 3 and empty_count == 1:
        score += 10
    elif player_count == 2 and empty_count == 2:
        score += 2
    
    # Defensive scoring
    if opponent_count == 3 and empty_count == 1:
        score -= 80  # Block opponent's winning move
    
    return score
