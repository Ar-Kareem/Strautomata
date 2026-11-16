
import random

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy that tries to win, block opponent wins, and play strategically.
    """
    rows = 6
    cols = 7
    
    def get_valid_columns():
        """Return list of columns that are not full."""
        return [c for c in range(cols) if board[0][c] == 0]
    
    def get_next_open_row(col):
        """Get the lowest empty row in a column."""
        for r in range(rows - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return None
    
    def check_winning_move(col, player):
        """Check if dropping a disc in col wins for player."""
        row = get_next_open_row(col)
        if row is None:
            return False
        
        # Temporarily place the disc
        board[row][col] = player
        
        # Check for win
        win = is_winning_position(row, col, player)
        
        # Undo the move
        board[row][col] = 0
        
        return win
    
    def is_winning_position(row, col, player):
        """Check if position (row, col) creates a win for player."""
        # Check horizontal
        count = 1
        # Check left
        c = col - 1
        while c >= 0 and board[row][c] == player:
            count += 1
            c -= 1
        # Check right
        c = col + 1
        while c < cols and board[row][c] == player:
            count += 1
            c += 1
        if count >= 4:
            return True
        
        # Check vertical
        count = 1
        # Check down
        r = row + 1
        while r < rows and board[r][col] == player:
            count += 1
            r += 1
        # Check up
        r = row - 1
        while r >= 0 and board[r][col] == player:
            count += 1
            r -= 1
        if count >= 4:
            return True
        
        # Check diagonal (positive slope)
        count = 1
        # Check down-left
        r, c = row + 1, col - 1
        while r < rows and c >= 0 and board[r][c] == player:
            count += 1
            r += 1
            c -= 1
        # Check up-right
        r, c = row - 1, col + 1
        while r >= 0 and c < cols and board[r][c] == player:
            count += 1
            r -= 1
            c += 1
        if count >= 4:
            return True
        
        # Check diagonal (negative slope)
        count = 1
        # Check down-right
        r, c = row + 1, col + 1
        while r < rows and c < cols and board[r][c] == player:
            count += 1
            r += 1
            c += 1
        # Check up-left
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and board[r][c] == player:
            count += 1
            r -= 1
            c -= 1
        if count >= 4:
            return True
        
        return False
    
    def count_threats(col, player):
        """Count the number of 3-in-a-row threats created by this move."""
        row = get_next_open_row(col)
        if row is None:
            return 0
        
        board[row][col] = player
        threats = 0
        
        # Check all directions for 3-in-a-row with open ends
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            # Count in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # Count in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count == 3:
                threats += 1
        
        board[row][col] = 0
        return threats
    
    valid_cols = get_valid_columns()
    if not valid_cols:
        return 3  # Should never happen
    
    # 1. Check if we can win immediately
    for col in valid_cols:
        if check_winning_move(col, 1):
            return col
    
    # 2. Check if we need to block opponent from winning
    for col in valid_cols:
        if check_winning_move(col, -1):
            return col
    
    # 3. Prefer center columns for better position
    center_col = cols // 2
    if center_col in valid_cols:
        row = get_next_open_row(center_col)
        if row is not None:
            # Only take center if it doesn't set up opponent win
            board[row][center_col] = 1
            safe = True
            for c in valid_cols:
                if c != center_col and check_winning_move(c, -1):
                    safe = False
                    break
            board[row][center_col] = 0
            if safe and count_threats(center_col, 1) > 0:
                return center_col
    
    # 4. Look for moves that create threats
    best_col = None
    best_score = -1
    
    for col in valid_cols:
        score = count_threats(col, 1)
        # Penalize if it sets up opponent win
        row = get_next_open_row(col)
        if row is not None and row > 0:
            # Check if placing here allows opponent to win above
            board[row][col] = 1
            for c in valid_cols:
                if check_winning_move(c, -1):
                    score -= 10
            board[row][col] = 0
        
        if score > best_score:
            best_score = score
            best_col = col
    
    if best_col is not None and best_score >= 0:
        return best_col
    
    # 5. Default to center-biased random choice
    weights = [4 - abs(c - center_col) for c in valid_cols]
    return random.choices(valid_cols, weights=weights)[0]
