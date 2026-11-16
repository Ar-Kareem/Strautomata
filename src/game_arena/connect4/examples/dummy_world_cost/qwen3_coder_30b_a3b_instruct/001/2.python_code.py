
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> int:
    # Convert to numpy for easier manipulation
    board = np.array(board)
    
    # Check for immediate win or block
    for col in range(7):
        if is_legal_move(board, col):
            # Try our move
            temp_board = make_move(board, col, 1)
            if check_winner(temp_board) == 1:
                return col
            # Try blocking opponent's win
            temp_board = make_move(board, col, -1)
            if check_winner(temp_board) == -1:
                # This is a blocking move, but we need to see if it actually wins
                return col
    
    # Use minimax with alpha-beta pruning
    best_score = float('-inf')
    best_col = 3  # Default to center if no better move found
    
    # Try each legal move with depth 5-6 for a good balance
    for col in range(7):
        if is_legal_move(board, col):
            new_board = make_move(board, col, 1)
            score = minimax(new_board, 5, False, float('-inf'), float('inf'))
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col

def is_legal_move(board, col):
    """Check if a move in the given column is legal"""
    return board[0][col] == 0

def make_move(board, col, player):
    """Make a move for the given player in the specified column"""
    new_board = board.copy()
    for row in range(5, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board

def check_winner(board):
    """Check if there's a winner on the board"""
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if board[row][col] != 0 and \
               board[row][col] == board[row][col+1] == board[row][col+2] == board[row][col+3]:
                return board[row][col]
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if board[row][col] != 0 and \
               board[row][col] == board[row+1][col] == board[row+2][col] == board[row+3][col]:
                return board[row][col]
    
    # Check positive diagonal
    for row in range(3):
        for col in range(4):
            if board[row][col] != 0 and \
               board[row][col] == board[row+1][col+1] == board[row+2][col+2] == board[row+3][col+3]:
                return board[row][col]
    
    # Check negative diagonal
    for row in range(3, 6):
        for col in range(4):
            if board[row][col] != 0 and \
               board[row][col] == board[row-1][col+1] == board[row-2][col+2] == board[row-3][col+3]:
                return board[row][col]
    
    return 0

def evaluate_board(board):
    """Evaluate the board state for the current player (1)"""
    score = 0
    
    # Center column preference
    center_count = np.sum(board[:, 3] == 1)
    score += center_count * 3
    
    # Check all possible lines of 4
    # Horizontal
    for row in range(6):
        for col in range(4):
            window = board[row, col:col+4]
            score += evaluate_window(window, 1)
    
    # Vertical
    for row in range(3):
        for col in range(7):
            window = board[row:row+4, col]
            score += evaluate_window(window, 1)
    
    # Positive diagonal
    for row in range(3):
        for col in range(4):
            window = [board[row+i][col+i] for i in range(4)]
            score += evaluate_window(window, 1)
    
    # Negative diagonal
    for row in range(3, 6):
        for col in range(4):
            window = [board[row-i][col+i] for i in range(4)]
            score += evaluate_window(window, 1)
    
    return score

def evaluate_window(window, player):
    """Evaluate a window of 4 cells for the specified player"""
    score = 0
    opponent = -player
    
    # Count number of player's discs in window
    player_count = np.sum(window == player)
    opponent_count = np.sum(window == opponent)
    empty_count = np.sum(window == 0)
    
    # Scoring for different scenarios
    if player_count == 4:
        score += 100
    elif player_count == 3 and empty_count == 1:
        score += 10
    elif player_count == 2 and empty_count == 2:
        score += 2
    elif player_count == 1 and empty_count == 3:
        score += 0.1
        
    # Defensive scoring for opponent threats
    if opponent_count == 3 and empty_count == 1:
        score -= 80
    elif opponent_count == 2 and empty_count == 2:
        score -= 5
    elif opponent_count == 1 and empty_count == 3:
        score -= 0.1
    
    return score

def minimax(board, depth, is_maximizing, alpha, beta):
    """Minimax algorithm with alpha-beta pruning"""
    winner = check_winner(board)
    
    # Terminal cases
    if winner == 1:
        return 100000
    elif winner == -1:
        return -100000
    elif depth == 0 or is_board_full(board):
        return evaluate_board(board)
    
    if is_maximizing:
        max_eval = float('-inf')
        for col in range(7):
            if is_legal_move(board, col):
                new_board = make_move(board, col, 1)
                eval_score = minimax(new_board, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
        return max_eval
    else:
        min_eval = float('inf')
        for col in range(7):
            if is_legal_move(board, col):
                new_board = make_move(board, col, -1)
                eval_score = minimax(new_board, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
        return min_eval

def is_board_full(board):
    """Check if the board is full"""
    return not np.any(board[0] == 0)
