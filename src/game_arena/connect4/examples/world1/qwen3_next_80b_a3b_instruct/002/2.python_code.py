
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board = np.array(board, dtype=int)
    
    # Define constants
    ROWS, COLS = 6, 7
    MY_DISC = 1
    OPP_DISC = -1
    
    def get_valid_moves():
        return [c for c in range(COLS) if board[0][c] == 0]
    
    def is_winner(player):
        # Check horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(board[r][c+i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if all(board[r+i][c] == player for i in range(4)):
                    return True
        
        # Check diagonal (top-left to bottom-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(board[r+i][c+i] == player for i in range(4)):
                    return True
        
        # Check diagonal (bottom-left to top-right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(board[r-i][c+i] == player for i in range(4)):
                    return True
        
        return False
    
    def score_window(window, player):
        """Score a 4-cell window (for evaluation)"""
        opp_player = -player
        score = 0
        
        player_count = np.count_nonzero(window == player)
        opp_count = np.count_nonzero(window == opp_player)
        empty_count = np.count_nonzero(window == 0)
        
        if player_count == 4:
            score += 1000
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2
        elif opp_count == 3 and empty_count == 1:
            score -= 4  # Block opponent's 3-in-a-row is very important
        elif opp_count == 2 and empty_count == 2:
            score -= 1  # Block opponent's 2-in-a-row
        
        return score
    
    def evaluate_board():
        """Simple evaluation function"""
        score = 0
        
        # Center column preference
        center_col = board[:, COLS//2]
        center_count = np.count_nonzero(center_col == MY_DISC)
        score += center_count * 3
        
        # Check horizontal windows
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = board[r, c:c+4]
                score += score_window(window, MY_DISC)
        
        # Check vertical windows
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = board[r:r+4, c]
                score += score_window(window, MY_DISC)
        
        # Check diagonal (top-left to bottom-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += score_window(window, MY_DISC)
        
        # Check diagonal (bottom-left to top-right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += score_window(window, MY_DISC)
        
        return score
    
    def minimax(depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves()
        
        # Terminal conditions
        if depth == 0 or not valid_moves:
            return evaluate_board(), None
        
        if maximizing_player:
            max_eval = float('-inf')
            best_col = valid_moves[0] if valid_moves else 0
            
            for col in valid_moves:
                # Make move
                row = 0
                while row < ROWS - 1 and board[row+1][col] == 0:
                    row += 1
                board[row][col] = MY_DISC
                
                eval_val, _ = minimax(depth - 1, alpha, beta, False)
                
                # Undo move
                board[row][col] = 0
                
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_col = col
                
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            return max_eval, best_col
            
        else:  # Minimizing player (opponent)
            min_eval = float('inf')
            best_col = valid_moves[0] if valid_moves else 0
            
            for col in valid_moves:
                # Make move
                row = 0
                while row < ROWS - 1 and board[row+1][col] == 0:
                    row += 1
                board[row][col] = OPP_DISC
                
                eval_val, _ = minimax(depth - 1, alpha, beta, True)
                
                # Undo move
                board[row][col] = 0
                
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_col = col
                
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            return min_eval, best_col
    
    # Check for immediate win
    for col in range(COLS):
        if board[0][col] == 0:  # Column is not full
            # Find lowest empty row in column
            row = 0
            while row < ROWS - 1 and board[row + 1][col] == 0:
                row += 1
            
            # Try placing my disc
            board[row][col] = MY_DISC
            if is_winner(MY_DISC):
                # Revert the temporary move
                board[row][col] = 0
                return col
            # Revert the temporary move
            board[row][col] = 0
    
    # Check for immediate block (opponent's winning move)
    for col in range(COLS):
        if board[0][col] == 0:  # Column is not full
            # Find lowest empty row in column
            row = 0
            while row < ROWS - 1 and board[row + 1][col] == 0:
                row += 1
            
            # Try placing opponent's disc
            board[row][col] = OPP_DISC
            if is_winner(OPP_DISC):
                # Revert the temporary move
                board[row][col] = 0
                return col
            # Revert the temporary move
            board[row][col] = 0
    
    # Otherwise, use minimax with depth 4
    _, best_col = minimax(4, float('-inf'), float('inf'), True)
    
    # Fallback: if minimax failed (shouldn't happen), pick first valid column
    if best_col is None:
        valid_moves = get_valid_moves()
        if valid_moves:
            return valid_moves[0]
        else:
            return 3  # center as fallback
    
    return best_col
