
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Function to get the lowest empty row in a column
    def get_lowest_empty_row(col):
        for row in range(5, -1, -1):  # Start from bottom
            if board_np[row][col] == 0:
                return row
        return -1  # Column is full
    
    # Function to check if a move is valid
    def is_valid_move(col):
        return get_lowest_empty_row(col) != -1
    
    # Function to check if the board is full
    def is_board_full():
        return all(board_np[0][col] != 0 for col in range(7))
    
    # Function to check for a win
    def check_winner():
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if (board_np[row][col] != 0 and 
                    board_np[row][col] == board_np[row][col+1] == 
                    board_np[row][col+2] == board_np[row][col+3]):
                    return board_np[row][col]
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if (board_np[row][col] != 0 and 
                    board_np[row][col] == board_np[row+1][col] == 
                    board_np[row+2][col] == board_np[row+3][col]):
                    return board_np[row][col]
        
        # Check diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                if (board_np[row][col] != 0 and 
                    board_np[row][col] == board_np[row+1][col+1] == 
                    board_np[row+2][col+2] == board_np[row+3][col+3]):
                    return board_np[row][col]
        
        # Check diagonal (top-right to bottom-left)
        for row in range(3):
            for col in range(3, 7):
                if (board_np[row][col] != 0 and 
                    board_np[row][col] == board_np[row+1][col-1] == 
                    board_np[row+2][col-2] == board_np[row+3][col-3]):
                    return board_np[row][col]
        
        return 0
    
    # Heuristic evaluation function
    def evaluate_position():
        score = 0
        
        # Score horizontal lines
        for row in range(6):
            for col in range(4):
                window = [board_np[row][col+i] for i in range(4)]
                score += evaluate_window(window)
        
        # Score vertical lines
        for row in range(3):
            for col in range(7):
                window = [board_np[row+i][col] for i in range(4)]
                score += evaluate_window(window)
        
        # Score diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                window = [board_np[row+i][col+i] for i in range(4)]
                score += evaluate_window(window)
        
        # Score diagonal (top-right to bottom-left)
        for row in range(3):
            for col in range(3, 7):
                window = [board_np[row+i][col-i] for i in range(4)]
                score += evaluate_window(window)
        
        return score
    
    # Evaluate a window of 4 positions
    def evaluate_window(window):
        score = 0
        computer_pieces = window.count(1)
        opponent_pieces = window.count(-1)
        empty_spaces = window.count(0)
        
        # Score based on potential winning lines
        if computer_pieces == 4:
            score += 100
        elif computer_pieces == 3 and empty_spaces == 1:
            score += 10
        elif computer_pieces == 2 and empty_spaces == 2:
            score += 2
        
        if opponent_pieces == 3 and empty_spaces == 1:
            score -= 80  # Block opponent's winning move
        elif opponent_pieces == 2 and empty_spaces == 2:
            score -= 2
        
        # Prefer center columns
        for i in range(len(window)):
            if window[i] == 1 and i == 3:
                score += 3  # Bonus for center pieces
        
        return score
    
    # Minimax with alpha-beta pruning
    def minimax(depth, alpha, beta, maximizing_player):
        # Check if game is over or max depth reached
        winner = check_winner()
        if winner == 1:
            return 1000000 + depth
        elif winner == -1:
            return -1000000 - depth
        elif is_board_full() or depth == 0:
            return evaluate_position()
        
        if maximizing_player:
            max_eval = -float('inf')
            for col in range(7):
                if is_valid_move(col):
                    row = get_lowest_empty_row(col)
                    board_np[row][col] = 1  # Place my disc
                    eval_score = minimax(depth - 1, alpha, beta, False)
                    board_np[row][col] = 0  # Undo move
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for col in range(7):
                if is_valid_move(col):
                    row = get_lowest_empty_row(col)
                    board_np[row][col] = -1  # Place opponent's disc
                    eval_score = minimax(depth - 1, alpha, beta, True)
                    board_np[row][col] = 0  # Undo move
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            return min_eval
    
    # Try to win immediately if possible
    for col in range(7):
        if is_valid_move(col):
            row = get_lowest_empty_row(col)
            board_np[row][col] = 1
            if check_winner() == 1:
                board_np[row][col] = 0
                return col
            board_np[row][col] = 0
    
    # Try to block opponent's win if possible
    for col in range(7):
        if is_valid_move(col):
            row = get_lowest_empty_row(col)
            board_np[row][col] = -1
            if check_winner() == -1:
                board_np[row][col] = 0
                return col
            board_np[row][col] = 0
    
    # Default to depth-limited minimax search
    best_score = -float('inf')
    best_col = 3  # Default to center column
    
    # Try different search depths to balance speed and quality
    for depth in range(4, 6):  # Try depths 4 and 5
        for col in range(7):
            if is_valid_move(col):
                row = get_lowest_empty_row(col)
                board_np[row][col] = 1
                score = minimax(depth - 1, -float('inf'), float('inf'), False)
                board_np[row][col] = 0
                
                if score > best_score:
                    best_score = score
                    best_col = col
    
    return best_col
