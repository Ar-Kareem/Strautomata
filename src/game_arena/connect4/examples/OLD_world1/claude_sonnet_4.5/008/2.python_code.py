
import random

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy that tries to win, block opponent, and play strategically.
    """
    rows = 6
    cols = 7
    
    def get_valid_columns():
        """Return list of columns that aren't full."""
        return [c for c in range(cols) if board[0][c] == 0]
    
    def get_next_open_row(col):
        """Get the next open row in a column (lowest available)."""
        for r in range(rows - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return None
    
    def check_window(window, player):
        """Count occurrences of player discs in a 4-cell window."""
        return window.count(player)
    
    def evaluate_window(window):
        """Evaluate a 4-cell window for scoring."""
        score = 0
        player = 1
        opponent = -1
        
        if check_window(window, player) == 4:
            score += 100
        elif check_window(window, player) == 3 and check_window(window, 0) == 1:
            score += 5
        elif check_window(window, player) == 2 and check_window(window, 0) == 2:
            score += 2
        
        if check_window(window, opponent) == 3 and check_window(window, 0) == 1:
            score -= 4
        
        return score
    
    def score_position(temp_board):
        """Score the entire board position."""
        score = 0
        
        # Score center column preference
        center_array = [temp_board[r][cols // 2] for r in range(rows)]
        center_count = center_array.count(1)
        score += center_count * 3
        
        # Score horizontal
        for r in range(rows):
            for c in range(cols - 3):
                window = [temp_board[r][c + i] for i in range(4)]
                score += evaluate_window(window)
        
        # Score vertical
        for c in range(cols):
            for r in range(rows - 3):
                window = [temp_board[r + i][c] for i in range(4)]
                score += evaluate_window(window)
        
        # Score positive diagonal
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = [temp_board[r + i][c + i] for i in range(4)]
                score += evaluate_window(window)
        
        # Score negative diagonal
        for r in range(3, rows):
            for c in range(cols - 3):
                window = [temp_board[r - i][c + i] for i in range(4)]
                score += evaluate_window(window)
        
        return score
    
    def is_winning_move(temp_board, col, player):
        """Check if dropping a disc in col creates a win for player."""
        row = get_next_open_row(col)
        if row is None:
            return False
        
        # Temporarily place the disc
        temp_board[row][col] = player
        
        # Check all directions for 4 in a row
        # Horizontal
        for c in range(max(0, col - 3), min(cols - 3, col) + 1):
            if all(temp_board[row][c + i] == player for i in range(4)):
                temp_board[row][col] = 0
                return True
        
        # Vertical
        for r in range(max(0, row - 3), min(rows - 3, row) + 1):
            if all(temp_board[r + i][col] == player for i in range(4)):
                temp_board[row][col] = 0
                return True
        
        # Positive diagonal
        for offset in range(-3, 1):
            r_start = row - offset
            c_start = col - offset
            if 0 <= r_start <= rows - 4 and 0 <= c_start <= cols - 4:
                if all(temp_board[r_start + i][c_start + i] == player for i in range(4)):
                    temp_board[row][col] = 0
                    return True
        
        # Negative diagonal
        for offset in range(-3, 1):
            r_start = row + offset
            c_start = col - offset
            if 3 <= r_start < rows and 0 <= c_start <= cols - 4:
                if all(temp_board[r_start - i][c_start + i] == player for i in range(4)):
                    temp_board[row][col] = 0
                    return True
        
        temp_board[row][col] = 0
        return False
    
    valid_columns = get_valid_columns()
    
    if not valid_columns:
        return 0
    
    # Make a copy of the board for testing moves
    temp_board = [row[:] for row in board]
    
    # Check if we can win immediately
    for col in valid_columns:
        if is_winning_move(temp_board, col, 1):
            return col
    
    # Check if we need to block opponent from winning
    for col in valid_columns:
        if is_winning_move(temp_board, col, -1):
            return col
    
    # Evaluate all valid moves and pick the best
    best_score = float('-inf')
    best_cols = []
    
    for col in valid_columns:
        row = get_next_open_row(col)
        temp_board[row][col] = 1
        score = score_position(temp_board)
        temp_board[row][col] = 0
        
        if score > best_score:
            best_score = score
            best_cols = [col]
        elif score == best_score:
            best_cols.append(col)
    
    return random.choice(best_cols)
