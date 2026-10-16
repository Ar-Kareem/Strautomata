
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    n_rows, n_cols = board.shape
    
    def is_winning_move(col, player):
        """Check if placing in column 'col' would win for 'player'"""
        # Find the first empty row in the column
        row = np.where(board[:, col] == 0)[0]
        if len(row) == 0:
            return False  # Column is full
        row = row[-1]  # Get the lowest empty row
        
        # Temporarily place the disc
        board[row, col] = player
        
        # Check all directions for 4 in a row
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # vertical, horizontal, diagonal down, diagonal up
        for dr, dc in directions:
            count = 1  # current disc
            # Search in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < n_rows and 0 <= c < n_cols and board[r, c] == player:
                count += 1
                r += dr
                c += dc
            # Search in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < n_rows and 0 <= c < n_cols and board[r, c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 4:
                board[row, col] = 0  # Undo temporary placement
                return True
        
        board[row, col] = 0  # Undo temporary placement
        return False
    
    def evaluate_move(col, player):
        """Evaluate the strategic value of a move for the given player"""
        if not is_valid_move(col):
            return -float('inf')
            
        # Find the first empty row in the column
        row = np.where(board[:, col] == 0)[0][-1]
        
        score = 0
        
        # Prefer center columns
        score += 2 - abs(col - 3)
        
        # Check if this move creates multiple threats
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            # Check for open-ended sequences
            length = 1
            open_ends = 0
            
            # Positive direction
            r, c = row + dr, col + dc
            if 0 <= r < n_rows and 0 <= c < n_cols:
                if board[r, c] == player:
                    length += 1
                    r += dr
                    c += dc
                    if 0 <= r < n_rows and 0 <= c < n_cols and board[r, c] == 0:
                        open_ends += 1
                elif board[r, c] == 0:
                    open_ends += 1
            
            # Negative direction
            r, c = row - dr, col - dc
            if 0 <= r < n_rows and 0 <= c < n_cols:
                if board[r, c] == player:
                    length += 1
                    r -= dr
                    c -= dc
                    if 0 <= r < n_rows and 0 <= c < n_cols and board[r, c] == 0:
                        open_ends += 1
                elif board[r, c] == 0:
                    open_ends += 1
            
            # Score based on sequence length and open ends
            if length >= 3 and open_ends >= 1:
                score += 100
            elif length == 2 and open_ends >= 1:
                score += 10 * open_ends
        
        return score
    
    def is_valid_move(col):
        """Check if a column is not full"""
        return board[0, col] == 0
    
    # 1. Check for immediate winning move
    for col in range(n_cols):
        if is_winning_move(col, 1):
            return col
    
    # 2. Check for opponent's immediate winning move and block it
    for col in range(n_cols):
        if is_winning_move(col, -1):
            return col
    
    # 3. Evaluate all possible moves and choose the best one
    best_score = -float('inf')
    best_col = 3  # Default to center column
    
    for col in range(n_cols):
        if not is_valid_move(col):
            continue
            
        # Evaluate move for current player
        score = evaluate_move(col, 1)
        
        # Check if this move would give opponent a win next turn
        # Temporarily make the move
        row = np.where(board[:, col] == 0)[0][-1]
        board[row, col] = 1
        
        opponent_has_win = False
        for opp_col in range(n_cols):
            if is_winning_move(opp_col, -1):
                opponent_has_win = True
                break
        
        # Undo temporary move
        board[row, col] = 0
        
        if opponent_has_win:
            score -= 1000  # Heavy penalty for moves that give opponent a win
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
