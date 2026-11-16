
def find_row(board, col):
    for r in reversed(range(6)):
        if board[r][col] == 0:
            return r
    return -1  # Indicates column is full (should not be called for valid_cols)

def check_win_at_pos(board, player, row, col):
    """Check if the player has a win that includes the disk at (row, col)."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Horizontal (right), Vertical (down), Diagonal (down-right), Diagonal (down-left)
    for dr, dc in directions:
        count = 1  # Start with the current disk
        # Check in positive direction
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r += dr
            c += dc
        # Check in negative direction
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        if count >= 4:
            return True
    return False

def evaluate_position(board, row, col, player):
    """Heuristic score for a move at (row, col) for player."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    score = 0
    for dr, dc in directions:
        count = 1  # Current disk
        # Positive direction
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r += dr
            c += dc
        # Negative direction
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        score += count * count  # Favor longer streaks quadratically
    return score

def policy(board):
    valid_cols = [col for col in range(7) if board[0][col] == 0]  # Find columns with at least one empty slot
    # Step 1: Check for immediate win
    for col in valid_cols:
        row = find_row(board, col)
        new_board = [list(r) for r in board]  # Make a copy
        new_board[row][col] = 1
        if check_win_at_pos(new_board, 1, row, col):
            return col
    # Step 2: Check to block opponent's immediate win
    opponent_win_cols = []
    for col in valid_cols:
        row = find_row(board, col)
        new_board = [list(r) for r in board]
        new_board[row][col] = -1  # Simulate opponent's move
        if check_win_at_pos(new_board, -1, row, col):
            opponent_win_cols.append(col)
    if opponent_win_cols:
        # Choose the blocking move that maximizes our own potential
        best_block_col = None
        best_block_score = -float('inf')
        for col in opponent_win_cols:
            row = find_row(board, col)
            new_board = [list(r) for r in board]
            new_board[row][col] = 1  # Simulate our blocking move
            score = evaluate_position(new_board, row, col, 1)
            center_score = 3 - abs(col - 3)  # Prefer center (3) with decreasing preference outward
            total_score = score + center_score
            if total_score > best_block_score:
                best_block_score = total_score
                best_block_col = col
        return best_block_col
    # Step 3: Choose the best heuristic-based move (no immediate win/block)
    best_col = valid_cols[0]
    best_score = -float('inf')
    for col in valid_cols:
        row = find_row(board, col)
        new_board = [list(r) for r in board]
        new_board[row][col] = 1
        score = evaluate_position(new_board, row, col, 1)
        center_score = 3 - abs(col - 3)
        total_score = score + center_score
        if total_score > best_score:
            best_score = total_score
            best_col = col
    return best_col
