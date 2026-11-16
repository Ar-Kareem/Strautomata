
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI Policy.
    Uses a 1-ply lookahead with a sophisticated heuristic evaluation.
    The evaluation prioritizes threats (unblocked lines of 3 or 2).
    """
    # Convert to numpy array for easier slicing
    b = np.array(board)
    cols = 7
    
    # Helper: Get the lowest empty row index for a column (top is 0)
    def get_drop_row(board, col):
        rows = board.shape[0]
        col_vals = board[:, col]
        # Non-empty cells count from bottom
        non_empty = np.count_nonzero(col_vals)
        return rows - 1 - non_empty

    # Helper: Check if a move wins immediately
    def is_winning_move(board, col, player):
        row = get_drop_row(board, col)
        if row == -1: return False # Should not happen if validated
        
        # Temporarily place the piece
        temp_board = board.copy()
        temp_board[row, col] = player
        
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if np.all(temp_board[r, c:c+4] == player):
                    return True
        
        # Check vertical
        for c in range(7):
            for r in range(3):
                if np.all(temp_board[r:r+4, c] == player):
                    return True
        
        # Check diagonal (down-right)
        for r in range(3):
            for c in range(4):
                if temp_board[r, c] == player and temp_board[r+1, c+1] == player and temp_board[r+2, c+2] == player and temp_board[r+3, c+3] == player:
                    return True

        # Check diagonal (down-left)
        for r in range(3):
            for c in range(3, 7):
                if temp_board[r, c] == player and temp_board[r+1, c-1] == player and temp_board[r+2, c-2] == player and temp_board[r+3, c-3] == player:
                    return True
        
        return False

    # 1. Check for immediate win (find a move that makes 4)
    for col in range(cols):
        if b[0, col] == 0: # Check if column is not full
            if is_winning_move(b, col, 1):
                return col

    # 2. Check for immediate loss (block opponent's win)
    for col in range(cols):
        if b[0, col] == 0:
            if is_winning_move(b, col, -1):
                return col

    # 3. Heuristic Evaluation Function
    def evaluate_window(window):
        """
        Scores a sequence of 4 cells.
        Returns a score for the current player (1).
        """
        count_p = np.count_nonzero(window == 1)
        count_o = np.count_nonzero(window == -1)
        count_e = np.count_nonzero(window == 0)
        
        # If opponent has a piece in window, it's blocked for us (unless it's a threat we should have blocked)
        if count_o > 0:
            if count_o == 4: return -100000 # Should have been blocked earlier, but catastrophic
            if count_o == 3 and count_e == 1: return -90000 # Opponent threat (3-in-a-row)
            return 0 
        
        # No opponent pieces
        if count_p == 4: return 100000 # Win (should have been caught)
        if count_p == 3 and count_e == 1: return 1000 # High value threat (3-in-a-row)
        if count_p == 2 and count_e == 2: return 10 # Moderate value setup
        
        return 0

    def calculate_score(board, player):
        total_score = 0
        
        # Center column preference
        center_col = board[:, 3]
        total_score += np.count_nonzero(center_col == player) * 3

        # Horizontal
        for r in range(6):
            for c in range(4):
                window = board[r, c:c+4]
                total_score += evaluate_window(window)

        # Vertical
        for c in range(7):
            for r in range(3):
                window = board[r:r+4, c]
                total_score += evaluate_window(window)

        # Diagonal (Positive Slope)
        for r in range(3):
            for c in range(4):
                window = np.array([board[r+i, c+i] for i in range(4)])
                total_score += evaluate_window(window)

        # Diagonal (Negative Slope)
        for r in range(3):
            for c in range(3, 7):
                window = np.array([board[r+i, c-i] for i in range(4)])
                total_score += evaluate_window(window)
                
        return total_score

    # 4. Evaluate valid moves
    best_col = -1
    max_score = -float('inf')
    
    valid_moves = []
    for col in range(cols):
        if b[0, col] == 0:
            valid_moves.append(col)
            
    # Fallback: if somehow no valid moves (shouldn't happen in valid game)
    if not valid_moves:
        return 0 

    # Simple 1-ply lookahead (Greedy)
    for col in valid_moves:
        # Simulate move
        row = get_drop_row(b, col)
        b[row, col] = 1
        
        # Score the resulting board state
        # We want to maximize our score while minimizing opponent's potential score
        # A simple way is to look at the difference between our score and opponent's score
        my_score = calculate_score(b, 1)
        opp_score = calculate_score(b, -1)
        total_score = my_score - opp_score
        
        # Undo move
        b[row, col] = 0
        
        if total_score > max_score:
            max_score = total_score
            best_col = col
            
    return best_col
