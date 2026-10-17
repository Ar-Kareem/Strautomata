
import numpy as np
from collections import Counter

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    rows, cols = board.shape
    
    # Check for winning move
    for col in range(cols):
        if is_valid_move(board, col):
            drop_disc(board, col, 1)
            if check_winner(board, 1):
                undo_move(board, col)
                return col
            undo_move(board, col)
    
    # Check for blocking opponent's winning move
    for col in range(cols):
        if is_valid_move(board, col):
            drop_disc(board, col, -1)
            if check_winner(board, -1):
                undo_move(board, col)
                return col
            undo_move(board, col)
    
    # Evaluate positions using a heuristic
    best_score = -float('inf')
    best_cols = []
    
    for col in range(cols):
        if not is_valid_move(board, col):
            continue
            
        # Simulate dropping disc
        drop_disc(board, col, 1)
        score = evaluate_position(board, 1)
        undo_move(board, col)
        
        if score > best_score:
            best_score = score
            best_cols = [col]
        elif score == best_score:
            best_cols.append(col)
    
    # If multiple best moves, pick centermost
    if best_cols:
        center = cols // 2
        best_cols.sort(key=lambda c: abs(c - center))
        return best_cols[0]
    
    # Fallback: pick first valid column
    for col in range(cols):
        if is_valid_move(board, col):
            return col

def is_valid_move(board, col):
    """Check if a move is valid (column not full)"""
    return board[0, col] == 0

def drop_disc(board, col, player):
    """Drop a disc in the specified column"""
    for row in range(board.shape[0] - 1, -1, -1):
        if board[row, col] == 0:
            board[row, col] = player
            return row

def undo_move(board, col):
    """Undo the last move in a column"""
    for row in range(board.shape[0]):
        if board[row, col] != 0:
            board[row, col] = 0
            return

def check_winner(board, player):
    """Check if the specified player has won"""
    rows, cols = board.shape
    
    # Check horizontal
    for row in range(rows):
        for col in range(cols - 3):
            if all(board[row, col + i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(rows - 3):
        for col in range(cols):
            if all(board[row + i, col] == player for i in range(4)):
                return True
    
    # Check diagonal (top-left to bottom-right)
    for row in range(rows - 3):
        for col in range(cols - 3):
            if all(board[row + i, col + i] == player for i in range(4)):
                return True
    
    # Check diagonal (top-right to bottom-left)
    for row in range(rows - 3):
        for col in range(3, cols):
            if all(board[row + i, col - i] == player for i in range(4)):
                return True
    
    return False

def evaluate_position(board, player):
    """Simple heuristic evaluation function"""
    score = 0
    opponent = -player
    rows, cols = board.shape
    
    # Score for each possible 4-in-a-row
    for row in range(rows):
        for col in range(cols - 3):
            window = [board[row, col + i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Vertical windows
    for row in range(rows - 3):
        for col in range(cols):
            window = [board[row + i, col] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Positive diagonal windows
    for row in range(rows - 3):
        for col in range(cols - 3):
            window = [board[row + i, col + i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Negative diagonal windows
    for row in range(rows - 3):
        for col in range(3, cols):
            window = [board[row + i, col - i] for i in range(4)]
            score += evaluate_window(window, player)
    
    return score

def evaluate_window(window, player):
    """Evaluate a window of 4 positions"""
    score = 0
    opponent = -player
    
    count = Counter(window)
    player_count = count[player]
    opponent_count = count[opponent]
    empty_count = count[0]
    
    if player_count == 4:
        score += 100
    elif player_count == 3 and empty_count == 1:
        score += 10
    elif player_count == 2 and empty_count == 2:
        score += 2
    
    if opponent_count == 3 and empty_count == 1:
        score -= 80  # Block opponent's winning move
        
    return score
