
import numpy as np
import time

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    grid = np.array(board, dtype=np.int8)
    global start_time
    start_time = time.time()
    
    # Get valid moves
    valid_cols = [c for c in range(7) if grid[0, c] == 0]
    
    if not valid_cols:
        return 0  # Should not happen in valid game
    
    # If only one move available, take it
    if len(valid_cols) == 1:
        return valid_cols[0]
    
    # Try to win immediately
    for col in valid_cols:
        if is_winning_move(grid, col, 1):
            return col
    
    # Prevent opponent from winning
    for col in valid_cols:
        if is_winning_move(grid, col, -1):
            return col
    
    # Use minimax with iterative deepening
    best_col = valid_cols[0]
    max_depth = 1
    
    # Try deeper searches within time limit
    while time.time() - start_time < 0.8:
        try:
            score, move = minimax(grid, max_depth, -float('inf'), float('inf'), True, valid_cols)
            if move is not None:
                best_col = move
            max_depth += 1
        except:
            break
    
    return best_col

def get_next_row(grid, col):
    """Get the row where a disc would land in the given column."""
    for row in range(5, -1, -1):
        if grid[row, col] == 0:
            return row
    return -1

def is_valid_move(grid, col):
    """Check if a move is valid (column not full)."""
    return grid[0, col] == 0

def make_move(grid, col, player):
    """Apply a move to the grid and return the row it was placed."""
    row = get_next_row(grid, col)
    if row == -1:
        return -1
    grid[row, col] = player
    return row

def undo_move(grid, col, row):
    """Undo a move."""
    grid[row, col] = 0

def is_winning_move(grid, col, player):
    """Check if placing a disc in col would win for player."""
    row = get_next_row(grid, col)
    if row == -1:
        return False
    
    # Temporarily make the move
    grid[row, col] = player
    result = check_win(grid, row, col, player)
    # Undo the move
    grid[row, col] = 0
    return result

def check_win(grid, row, col, player):
    """Check if the player has won with a move at (row, col)."""
    # Directions: horizontal, vertical, diagonal \, diagonal /
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for dr, dc in directions:
        count = 1  # The placed piece
        
        # Positive direction
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and grid[r, c] == player:
            count += 1
            r += dr
            c += dc
        
        # Negative direction
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and grid[r, c] == player:
            count += 1
            r -= dr
            c -= dc
        
        if count >= 4:
            return True
    
    return False

def evaluate_window(window, player):
    """Evaluate a window of 4 consecutive cells."""
    score = 0
    opp_player = -player
    
    player_count = np.sum(window == player)
    opp_count = np.sum(window == opp_player)
    empty_count = np.sum(window == 0)
    
    if player_count == 4:
        score += 1000
    elif player_count == 3 and empty_count == 1:
        score += 100
    elif player_count == 2 and empty_count == 2:
        score += 10
    
    if opp_count == 3 and empty_count == 1:
        score -= 90  # Slightly less than our own 3-in-a-row to prioritize defense
    
    return score

def score_position(grid, player):
    """Evaluate the board position for the given player."""
    score = 0
    
    # Center column preference
    center_array = grid[:, 3]
    center_count = np.sum(center_array == player)
    score += center_count * 6
    
    # Check all windows of 4
    # Horizontal
    for r in range(6):
        row_array = grid[r, :]
        for c in range(4):
            window = row_array[c:c+4]
            score += evaluate_window(window, player)
    
    # Vertical
    for c in range(7):
        col_array = grid[:, c]
        for r in range(3):
            window = col_array[r:r+4]
            score += evaluate_window(window, player)
    
    # Positive diagonal
    for r in range(3):
        for c in range(4):
            window = [grid[r+i, c+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Negative diagonal
    for r in range(3):
        for c in range(4):
            window = [grid[r+3-i, c+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    return score

def get_valid_moves(grid):
    """Get list of valid columns."""
    return [c for c in range(7) if grid[0, c] == 0]

def minimax(grid, depth, alpha, beta, maximizing, valid_cols=None):
    """Minimax with alpha-beta pruning."""
    global start_time
    if time.time() - start_time > 0.9:
        raise TimeoutError()
    
    if depth == 0:
        return score_position(grid, 1), None
    
    if valid_cols is None:
        valid_cols = get_valid_moves(grid)
    
    if not valid_cols:
        return 0, None  # Draw
    
    # Sort moves: center columns first for better pruning
    sorted_cols = sorted(valid_cols, key=lambda x: abs(x - 3))
    
    best_col = sorted_cols[0]
    
    if maximizing:
        max_eval = -float('inf')
        for col in sorted_cols:
            row = make_move(grid, col, 1)
            if row == -1:
                continue
            evaluation, _ = minimax(grid, depth - 1, alpha, beta, False)
            undo_move(grid, col, row)
            
            if evaluation > max_eval:
                max_eval = evaluation
                best_col = col
            
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return max_eval, best_col
    else:
        min_eval = float('inf')
        for col in sorted_cols:
            row = make_move(grid, col, -1)
            if row == -1:
                continue
            evaluation, _ = minimax(grid, depth - 1, alpha, beta, True)
            undo_move(grid, col, row)
            
            if evaluation < min_eval:
                min_eval = evaluation
                best_col = col
            
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return min_eval, best_col
