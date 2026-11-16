
import numpy as np
from collections import Counter

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier handling
    np_board = np.array(board)
    
    def is_column_full(col):
        return np_board[0][col] != 0
    
    def drop_disc(col, player):
        # Find the lowest available row in the column
        for row in range(5, -1, -1):
            if np_board[row][col] == 0:
                return row
        return -1  # Should not happen if column is not full
    
    def check_winner():
        # Check for winner in the current board state
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if (np_board[row][col] != 0 and 
                    np_board[row][col] == np_board[row][col+1] == np_board[row][col+2] == np_board[row][col+3]):
                    return np_board[row][col]
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if (np_board[row][col] != 0 and 
                    np_board[row][col] == np_board[row+1][col] == np_board[row+2][col] == np_board[row+3][col]):
                    return np_board[row][col]
        
        # Check diagonal (bottom-left to top-right)
        for row in range(3, 6):
            for col in range(4):
                if (np_board[row][col] != 0 and 
                    np_board[row][col] == np_board[row-1][col+1] == np_board[row-2][col+2] == np_board[row-3][col+3]):
                    return np_board[row][col]
        
        # Check diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                if (np_board[row][col] != 0 and 
                    np_board[row][col] == np_board[row+1][col+1] == np_board[row+2][col+2] == np_board[row+3][col+3]):
                    return np_board[row][col]
        
        return 0  # No winner
    
    def evaluate_board():
        # Simple evaluation function
        score = 0
        
        # Heuristics:
        # 1. 4-in-a-row = win (value of 10000)
        # 2. 3-in-a-row with empty space = 1000 (defensive)
        # 3. 2-in-a-row with empty space = 100
        # 4. Center column preference (value of 50 per disc there)
        
        # Check for my winning move (4-in-a-row)
        winner = check_winner()
        if winner == 1:
            return 100000
        elif winner == -1:
            return -100000
        
        # Evaluate all possible lines (horizontal, vertical, diagonal)
        for row in range(6):
            for col in range(7):
                # Check horizontal lines
                if col <= 3:
                    line = [np_board[row][col+i] for i in range(4)]
                    score += evaluate_line(line)
                
                # Check vertical lines  
                if row <= 2:
                    line = [np_board[row+i][col] for i in range(4)]
                    score += evaluate_line(line)
                
                # Check diagonal (top-left to bottom-right)
                if row <= 2 and col <= 3:
                    line = [np_board[row+i][col+i] for i in range(4)]
                    score += evaluate_line(line)
                
                # Check diagonal (bottom-left to top-right)
                if row >= 3 and col <= 3:
                    line = [np_board[row-i][col+i] for i in range(4)]
                    score += evaluate_line(line)
        
        return score
    
    def evaluate_line(line):
        # Evaluate a line of 4 cells
        count = Counter(line)
        my_discs = count[1]
        opp_discs = count[-1]
        empty_spaces = count[0]
        
        # If I have 4 in a row, huge score
        if my_discs == 4:
            return 10000
        # If opponent has 4 in a row, block immediately
        if opp_discs == 4:
            return -10000
        # If I have 3 in a row with one space, good
        if my_discs == 3 and empty_spaces == 1:
            return 1000
        # If opponent has 3 in a row with one space, block
        if opp_discs == 3 and empty_spaces == 1:
            return -1000
        # If I have 2 in a row with two spaces, decent
        if my_discs == 2 and empty_spaces == 2:
            return 100
        # If opponent has 2 in a row with two spaces, consider blocking
        if opp_discs == 2 and empty_spaces == 2:
            return -100
        return 0
    
    # Try to win immediately if possible
    for col in range(7):
        if is_column_full(col):
            continue
        # Try dropping a disc and see if it wins
        row = drop_disc(col, 1)
        if row != -1:
            # Temporarily place a disc to check for win
            np_board[row][col] = 1
            if check_winner() == 1:
                np_board[row][col] = 0  # Revert
                return col
            np_board[row][col] = 0  # Revert
    
    # Block opponent if they can win next move
    for col in range(7):
        if is_column_full(col):
            continue
        # Try dropping a disc and see if opponent wins 
        row = drop_disc(col, -1)
        if row != -1:
            # Temporarily place opponent's disc to check for win  
            np_board[row][col] = -1
            if check_winner() == -1:
                np_board[row][col] = 0  # Revert
                return col
            np_board[row][col] = 0  # Revert
    
    # Otherwise use minimax with simple depth of 4 for a good balance of performance and intelligence
    def minimax(depth, maximizing_player, alpha, beta):
        winner = check_winner()
        if winner == 1:
            return 10000 - depth
        elif winner == -1:
            return -10000 + depth
        elif depth == 0:
            return evaluate_board()
        elif all(is_column_full(col) for col in range(7)):
            return 0  # Draw
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in range(7):
                if is_column_full(col):
                    continue
                row = drop_disc(col, 1)
                if row != -1:
                    np_board[row][col] = 1
                    eval_score = minimax(depth-1, False, alpha, beta)
                    np_board[row][col] = 0
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            return max_eval
        else:  # Minimizing player (opponent)
            min_eval = float('inf')
            for col in range(7):
                if is_column_full(col):
                    continue
                row = drop_disc(col, -1)  
                if row != -1:
                    np_board[row][col] = -1
                    eval_score = minimax(depth-1, True, alpha, beta)
                    np_board[row][col] = 0
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            return min_eval
    
    # Get all valid moves
    valid_moves = [col for col in range(7) if not is_column_full(col)]
    
    if not valid_moves:  # Should not happen
        return 0
    
    # Try each move and score it using minimax
    best_score = float('-inf')
    best_col = valid_moves[0]
    
    for col in valid_moves:
        row = drop_disc(col, 1)
        if row != -1:
            np_board[row][col] = 1
            score = minimax(4, False, float('-inf'), float('inf'))  # Depth 4
            np_board[row][col] = 0
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col
