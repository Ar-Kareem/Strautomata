
import numpy as np
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Constants
    ROWS, COLS = 6, 7
    EMPTY = 0
    PLAYER = 1
    OPPONENT = -1
    
    # Check if a move leads to immediate win
    def check_win_move(col, player):
        temp_board = board_np.copy()
        for row in range(ROWS-1, -1, -1):
            if temp_board[row, col] == EMPTY:
                temp_board[row, col] = player
                # Check if this creates a win
                if check_win(temp_board, player, row, col):
                    return True
                break
        return False
    
    # Check if player has won starting from (row, col)
    def check_win(b, player, row, col):
        # Check horizontal
        count = 1
        # Check left
        c = col - 1
        while c >= 0 and b[row, c] == player:
            count += 1
            c -= 1
        # Check right
        c = col + 1
        while c < COLS and b[row, c] == player:
            count += 1
            c += 1
        if count >= 4:
            return True
            
        # Check vertical
        count = 1
        # Check down
        r = row + 1
        while r < ROWS and b[r, col] == player:
            count += 1
            r += 1
        if count >= 4:
            return True
            
        # Check diagonal /
        count = 1
        # Check up-right
        r, c = row - 1, col + 1
        while r >= 0 and c < COLS and b[r, c] == player:
            count += 1
            r -= 1
            c += 1
        # Check down-left
        r, c = row + 1, col - 1
        while r < ROWS and c >= 0 and b[r, c] == player:
            count += 1
            r += 1
            c -= 1
        if count >= 4:
            return True
            
        # Check diagonal \
        count = 1
        # Check up-left
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and b[r, c] == player:
            count += 1
            r -= 1
            c -= 1
        # Check down-right
        r, c = row + 1, col + 1
        while r < ROWS and c < COLS and b[r, c] == player:
            count += 1
            r += 1
            c += 1
        if count >= 4:
            return True
            
        return False
    
    # Get valid columns
    valid_cols = [col for col in range(COLS) if board_np[0, col] == EMPTY]
    
    # If no valid columns, return random (should not happen in normal play)
    if not valid_cols:
        return random.randint(0, COLS-1)
    
    # 1. Try to win immediately
    for col in valid_cols:
        if check_win_move(col, PLAYER):
            return col
    
    # 2. Block opponent's immediate win
    for col in valid_cols:
        if check_win_move(col, OPPONENT):
            return col
    
    # 3. Evaluate moves with a simple heuristic
    def evaluate_board(b):
        score = 0
        # Check all possible 4-in-a-row positions
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                window = [b[r, c+i] for i in range(4)]
                score += evaluate_window(window)
        
        # Vertical
        for r in range(ROWS-3):
            for c in range(COLS):
                window = [b[r+i, c] for i in range(4)]
                score += evaluate_window(window)
        
        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = [b[r-i, c+i] for i in range(4)]
                score += evaluate_window(window)
        
        # Diagonal \
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [b[r+i, c+i] for i in range(4)]
                score += evaluate_window(window)
        
        return score
    
    def evaluate_window(window):
        score = 0
        player_count = window.count(PLAYER)
        opponent_count = window.count(OPPONENT)
        empty_count = window.count(EMPTY)
        
        if player_count == 4:
            score += 1000
        elif player_count == 3 and empty_count == 1:
            score += 100
        elif player_count == 2 and empty_count == 2:
            score += 10
        elif opponent_count == 4:
            score -= 1000
        elif opponent_count == 3 and empty_count == 1:
            score -= 100
        elif opponent_count == 2 and empty_count == 2:
            score -= 10
        
        return score
    
    # Score each valid column
    best_col = valid_cols[0]
    best_score = -float('inf')
    
    # Center column preference
    center_col = COLS // 2
    center_array = list(range(center_col-1, center_col+2))  # Prefer middle columns
    
    for col in valid_cols:
        # Create a temporary board with the move
        temp_board = board_np.copy()
        for row in range(ROWS-1, -1, -1):
            if temp_board[row, col] == EMPTY:
                temp_board[row, col] = PLAYER
                break
        
        score = evaluate_board(temp_board)
        
        # Prefer center columns
        if col in center_array:
            score += 3
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
