
def policy(board: list[list[int]]) -> int:
    def get_next_row(board, col):
        """Get the next available row in a column (lowest empty spot)."""
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                return row
        return -1
    
    def check_win(board, row, col, player):
        """Check if placing player's disc at (row, col) creates a win."""
        if row == -1:
            return False
        
        # Temporarily place the disc
        original = board[row][col]
        board[row][col] = player
        
        # Check horizontal
        count = 1
        # Check left
        c = col - 1
        while c >= 0 and board[row][c] == player:
            count += 1
            c -= 1
        # Check right
        c = col + 1
        while c < 7 and board[row][c] == player:
            count += 1
            c += 1
        if count >= 4:
            board[row][col] = original
            return True
        
        # Check vertical
        count = 1
        # Check down
        r = row + 1
        while r < 6 and board[r][col] == player:
            count += 1
            r += 1
        # Check up
        r = row - 1
        while r >= 0 and board[r][col] == player:
            count += 1
            r -= 1
        if count >= 4:
            board[row][col] = original
            return True
        
        # Check diagonal (down-right)
        count = 1
        r, c = row + 1, col + 1
        while r < 6 and c < 7 and board[r][c] == player:
            count += 1
            r += 1
            c += 1
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and board[r][c] == player:
            count += 1
            r -= 1
            c -= 1
        if count >= 4:
            board[row][col] = original
            return True
        
        # Check diagonal (down-left)
        count = 1
        r, c = row + 1, col - 1
        while r < 6 and c >= 0 and board[r][c] == player:
            count += 1
            r += 1
            c -= 1
        r, c = row - 1, col + 1
        while r >= 0 and c < 7 and board[r][c] == player:
            count += 1
            r -= 1
            c += 1
        if count >= 4:
            board[row][col] = original
            return True
        
        board[row][col] = original
        return False
    
    def evaluate_move(board, col):
        """Evaluate how good a move is using heuristics."""
        row = get_next_row(board, col)
        if row == -1:
            return -1000
        
        score = 0
        
        # Prefer center columns
        score += (3 - abs(col - 3)) * 10
        
        # Count threats (3 in a row with potential for 4)
        board[row][col] = 1
        
        # Check for creating threats
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # diagonal down-right
            (1, -1)   # diagonal down-left
        ]
        
        for dr, dc in directions:
            count = 1
            # Count in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == 1:
                count += 1
                r += dr
                c += dc
            # Count in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == 1:
                count += 1
                r -= dr
                c -= dc
            
            if count == 3:
                score += 50
            elif count == 2:
                score += 10
        
        board[row][col] = 0
        return score
    
    # Get valid columns
    valid_cols = [col for col in range(7) if board[0][col] == 0]
    
    if not valid_cols:
        return 3  # Fallback (shouldn't happen)
    
    # 1. Check for immediate win
    for col in valid_cols:
        row = get_next_row(board, col)
        if check_win(board, row, col, 1):
            return col
    
    # 2. Block opponent's immediate win
    for col in valid_cols:
        row = get_next_row(board, col)
        if check_win(board, row, col, -1):
            return col
    
    # 3. Choose best move based on heuristic
    best_score = -float('inf')
    best_col = valid_cols[0]
    
    for col in valid_cols:
        score = evaluate_move(board, col)
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
