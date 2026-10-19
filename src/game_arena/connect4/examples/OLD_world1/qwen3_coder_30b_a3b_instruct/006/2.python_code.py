
def policy(board: list[list[int]]) -> int:
    import numpy as np
    
    # Convert board to numpy array for easier manipulation
    np_board = np.array(board)
    rows, cols = np_board.shape
    
    def count_in_direction(r, c, dr, dc, player):
        """Count consecutive discs in a direction"""
        count = 0
        nr, nc = r + dr, c + dc
        while 0 <= nr < rows and 0 <= nc < cols and np_board[nr, nc] == player:
            count += 1
            nr += dr
            nc += dc
        return count
    
    def score_position(r, c, player):
        """Score a position based on potential lines"""
        if np_board[r, c] != 0:
            return 0
            
        score = 0
        # Check all 4 directions
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            # Count consecutive discs in both directions
            forward = count_in_direction(r, c, dr, dc, player)
            backward = count_in_direction(r, c, -dr, -dc, player)
            total = forward + backward + 1  # Include current position
            
            # Score based on line length
            if total >= 4:
                score += 10000  # Win
            elif total == 3 and (forward == 2 or backward == 2):
                score += 1000   # Three in a row with potential
            elif total == 2 and (forward == 1 or backward == 1):
                score += 100    # Two in a row with potential
            elif total == 1:
                score += 10     # Single disc
        
        return score
    
    # Check for immediate winning moves
    for c in range(cols):
        # Find the lowest empty row in column c
        if np_board[0, c] != 0:  # Column full
            continue
        for r in range(rows-1, -1, -1):
            if np_board[r, c] == 0:
                # Try placing here and check if it wins
                np_board[r, c] = 1  # Place our disc
                if score_position(r, c, 1) >= 10000:
                    # Reset board and return this column
                    np_board[r, c] = 0
                    return c
                np_board[r, c] = 0
                break
    
    # Check for blocking opponent wins
    for c in range(cols):
        if np_board[0, c] != 0:
            continue
        for r in range(rows-1, -1, -1):
            if np_board[r, c] == 0:
                np_board[r, c] = -1  # Place opponent's disc
                if score_position(r, c, -1) >= 10000:
                    # Reset board and block here
                    np_board[r, c] = 0
                    return c
                np_board[r, c] = 0
                break
    
    # Otherwise, score all positions and pick the best
    best_score = -1
    best_cols = []
    
    for c in range(cols):
        if np_board[0, c] != 0:  # Column full
            continue
            
        # Find the best row in this column
        best_row = -1
        for r in range(rows-1, -1, -1):
            if np_board[r, c] == 0:
                best_row = r
                break
        
        # Score this position for both players
        our_score = score_position(best_row, c, 1)
        their_score = score_position(best_row, c, -1)
        
        # Prefer positions that block opponent
        total_score = our_score + their_score * 0.8
        
        if total_score > best_score:
            best_score = total_score
            best_cols = [c]
        elif total_score == best_score:
            best_cols.append(c)
    
    # If there are multiple best columns, pick the center one
    if best_cols:
        if len(best_cols) > 1:
            center = cols // 2
            # Find the closest column to center
            return min(best_cols, key=lambda x: abs(x - center))
        else:
            return best_cols[0]
    else:
        # Fallback to any playable column
        for c in range(cols):
            if np_board[0, c] == 0:
                return c
