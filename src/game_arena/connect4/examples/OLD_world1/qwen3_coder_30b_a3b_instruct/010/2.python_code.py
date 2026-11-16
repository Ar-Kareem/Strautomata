
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    np_board = np.array(board)
    rows, cols = np_board.shape
    
    # Check for winning moves
    for col in range(cols):
        if is_valid_move(np_board, col):
            # Try dropping disc in this column
            temp_board = np_board.copy()
            drop_disc(temp_board, col, 1)
            if check_winner(temp_board, 1):
                return col
    
    # Check for blocking opponent wins
    for col in range(cols):
        if is_valid_move(np_board, col):
            temp_board = np_board.copy()
            drop_disc(temp_board, col, -1)
            if check_winner(temp_board, -1):
                return col
    
    # Evaluate positions using a simple scoring heuristic
    scores = []
    for col in range(cols):
        if not is_valid_move(np_board, col):
            scores.append(-1)  # Invalid move
            continue
            
        temp_board = np_board.copy()
        drop_disc(temp_board, col, 1)
        score = evaluate_position(temp_board, 1)
        scores.append(score)
    
    # Return column with highest score
    max_score = max(scores)
    best_cols = [i for i, score in enumerate(scores) if score == max_score]
    
    # Prefer center columns when scores are equal
    center = cols // 2
    best_cols = [col for col in best_cols if abs(col - center) <= 1]
    
    return best_cols[0] if best_cols else 3

def is_valid_move(board, col):
    """Check if a move in the given column is valid"""
    return board[0][col] == 0

def drop_disc(board, col, player):
    """Drop a disc in the given column for the specified player"""
    for row in range(len(board) - 1, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            break

def check_winner(board, player):
    """Check if the given player has won"""
    rows, cols = board.shape
    
    # Check horizontal
    for row in range(rows):
        for col in range(cols - 3):
            if all(board[row][col + i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(rows - 3):
        for col in range(cols):
            if all(board[row + i][col] == player for i in range(4)):
                return True
    
    # Check diagonal (positive slope)
    for row in range(rows - 3):
        for col in range(cols - 3):
            if all(board[row + i][col + i] == player for i in range(4)):
                return True
    
    # Check diagonal (negative slope)
    for row in range(3, rows):
        for col in range(cols - 3):
            if all(board[row - i][col + i] == player for i in range(4)):
                return True
    
    return False

def evaluate_position(board, player):
    """Simple heuristic to evaluate a board position"""
    score = 0
    rows, cols = board.shape
    
    # Evaluate all possible 4-in-a-row positions
    # Horizontal
    for row in range(rows):
        for col in range(cols - 3):
            window = [board[row][col + i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Vertical
    for row in range(rows - 3):
        for col in range(cols):
            window = [board[row + i][col] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Diagonal (positive slope)
    for row in range(rows - 3):
        for col in range(cols - 3):
            window = [board[row + i][col + i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Diagonal (negative slope)
    for row in range(3, rows):
        for col in range(cols - 3):
            window = [board[row - i][col + i] for i in range(4)]
            score += evaluate_window(window, player)
    
    return score

def evaluate_window(window, player):
    """Evaluate a window of 4 positions"""
    score = 0
    opponent = -player
    
    # Count discs of the player and opponent in this window
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(0)
    
    # Prefer positions that lead to winning conditions
    if player_count == 3 and empty_count == 1:
        score += 100
    elif player_count == 2 and empty_count == 2:
        score += 10
    elif player_count == 1 and empty_count == 3:
        score += 2
    
    # Prefer blocking opponent from winning
    if opponent_count == 3 and empty_count == 1:
        score -= 90
    elif opponent_count == 2 and empty_count == 2:
        score -= 5
    
    return score
