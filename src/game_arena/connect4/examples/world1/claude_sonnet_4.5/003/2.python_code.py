
def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy that chooses the best column to drop a disc.
    
    board: 6x7 grid where 1 = our disc, -1 = opponent's disc, 0 = empty
    Returns: column index (0-6) to drop disc
    """
    
    def get_valid_columns(board):
        """Return list of columns that aren't full."""
        return [col for col in range(7) if board[0][col] == 0]
    
    def drop_disc(board, col, player):
        """Simulate dropping a disc in a column. Returns row where it lands, or -1 if full."""
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                return row
        return -1
    
    def check_win(board, player):
        """Check if player has won."""
        # Horizontal
        for row in range(6):
            for col in range(4):
                if all(board[row][col + i] == player for i in range(4)):
                    return True
        
        # Vertical
        for row in range(3):
            for col in range(7):
                if all(board[row + i][col] == player for i in range(4)):
                    return True
        
        # Diagonal (down-right)
        for row in range(3):
            for col in range(4):
                if all(board[row + i][col + i] == player for i in range(4)):
                    return True
        
        # Diagonal (up-right)
        for row in range(3, 6):
            for col in range(4):
                if all(board[row - i][col + i] == player for i in range(4)):
                    return True
        
        return False
    
    def count_threats(board, player):
        """Count number of 3-in-a-row threats that can become 4-in-a-row."""
        threats = 0
        
        # Horizontal threats
        for row in range(6):
            for col in range(4):
                window = [board[row][col + i] for i in range(4)]
                if window.count(player) == 3 and window.count(0) == 1:
                    threats += 1
        
        # Vertical threats
        for row in range(3):
            for col in range(7):
                window = [board[row + i][col] for i in range(4)]
                if window.count(player) == 3 and window.count(0) == 1:
                    threats += 1
        
        # Diagonal threats
        for row in range(3):
            for col in range(4):
                window = [board[row + i][col + i] for i in range(4)]
                if window.count(player) == 3 and window.count(0) == 1:
                    threats += 1
        
        for row in range(3, 6):
            for col in range(4):
                window = [board[row - i][col + i] for i in range(4)]
                if window.count(player) == 3 and window.count(0) == 1:
                    threats += 1
        
        return threats
    
    def evaluate_move(board, col):
        """Evaluate the quality of a move."""
        # Simulate the move
        row = drop_disc(board, col, 1)
        if row == -1:
            return -1000000  # Invalid move
        
        board[row][col] = 1
        score = 0
        
        # Check if we win immediately
        if check_win(board, 1):
            board[row][col] = 0
            return 1000000
        
        # Check if opponent can win on their next move
        for opp_col in range(7):
            opp_row = drop_disc(board, opp_col, -1)
            if opp_row != -1:
                board[opp_row][opp_col] = -1
                if check_win(board, -1):
                    score -= 500000  # Avoid giving opponent a win
                board[opp_row][opp_col] = 0
        
        # Prefer center columns
        score += (3 - abs(col - 3)) * 10
        
        # Count our threats vs opponent threats
        our_threats = count_threats(board, 1)
        score += our_threats * 100
        
        board[row][col] = 0
        return score
    
    valid_cols = get_valid_columns(board)
    
    if not valid_cols:
        return 3  # Fallback, shouldn't happen
    
    # First check for immediate winning move
    for col in valid_cols:
        row = drop_disc(board, col, 1)
        if row != -1:
            board[row][col] = 1
            if check_win(board, 1):
                board[row][col] = 0
                return col
            board[row][col] = 0
    
    # Check for blocking opponent's immediate win
    for col in valid_cols:
        row = drop_disc(board, col, -1)
        if row != -1:
            board[row][col] = -1
            if check_win(board, -1):
                board[row][col] = 0
                return col
            board[row][col] = 0
    
    # Evaluate all valid moves and pick the best
    best_col = valid_cols[0]
    best_score = -float('inf')
    
    for col in valid_cols:
        score = evaluate_move(board, col)
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
