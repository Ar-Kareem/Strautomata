
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    def is_valid_move(col):
        return board_np[0][col] == 0
    
    def get_next_open_row(col):
        for row in range(5, -1, -1):
            if board_np[row][col] == 0:
                return row
        return -1
    
    def check_winner(board, player):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if all(board[r][c+i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for r in range(3):
            for c in range(7):
                if all(board[r+i][c] == player for i in range(4)):
                    return True
        
        # Check positive diagonal
        for r in range(3):
            for c in range(4):
                if all(board[r+i][c+i] == player for i in range(4)):
                    return True
        
        # Check negative diagonal
        for r in range(3, 6):
            for c in range(4):
                if all(board[r-i][c+i] == player for i in range(4)):
                    return True
        
        return False
    
    def evaluate_window(window, player):
        score = 0
        opponent = -player
        
        if window.count(player) == 4:
            score += 100
        elif window.count(player) == 3 and window.count(0) == 1:
            score += 10
        elif window.count(player) == 2 and window.count(0) == 2:
            score += 2
            
        if window.count(opponent) == 3 and window.count(0) == 1:
            score -= 80
            
        return score
    
    def score_position(board, player):
        score = 0
        
        # Score center column
        center_array = [board[r][3] for r in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        # Score horizontal
        for r in range(6):
            row_array = [int(board[r][c]) for c in range(7)]
            for c in range(4):
                window = row_array[c:c+4]
                score += evaluate_window(window, player)
        
        # Score vertical
        for c in range(7):
            col_array = [int(board[r][c]) for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(window, player)
        
        # Score positive diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score negative diagonal
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, player)
                
        return score
    
    # Check for immediate win
    for col in range(7):
        if is_valid_move(col):
            row = get_next_open_row(col)
            board_np[row][col] = 1
            if check_winner(board_np, 1):
                board_np[row][col] = 0
                return col
            board_np[row][col] = 0

    # Check for immediate block
    for col in range(7):
        if is_valid_move(col):
            row = get_next_open_row(col)
            board_np[row][col] = -1
            if check_winner(board_np, -1):
                board_np[row][col] = 0
                return col
            board_np[row][col] = 0
    
    # If no immediate win/block, use heuristic scoring
    best_score = -10000
    best_col = 3  # Default to center
    
    for col in range(7):
        if is_valid_move(col):
            row = get_next_open_row(col)
            board_np[row][col] = 1
            score = score_position(board_np, 1)
            board_np[row][col] = 0
            
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col
