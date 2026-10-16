
import numpy as np
import time

def policy(board: list[list[int]]) -> int:
    """
    Connect-4 AI policy using minimax with alpha-beta pruning and iterative deepening.
    Prioritizes: 1) immediate wins, 2) blocking opponent wins, 3) best strategic move via search.
    """
    try:
        # Convert to numpy for faster operations
        board = np.array(board, dtype=np.int8)
        
        # Get valid moves (prioritize center for better alpha-beta pruning)
        valid_moves = get_valid_moves(board)
        if not valid_moves:
            return 0  # Should never happen in a legal game state
        
        # Sort moves by distance from center
        valid_moves.sort(key=lambda c: abs(c - 3))
        
        # 1. Check for immediate win
        for col in valid_moves:
            if is_winning_move(board, col, 1):
                return col
        
        # 2. Check for opponent's immediate win (block)
        for col in valid_moves:
            if is_winning_move(board, col, -1):
                return col
        
        # 3. Use minimax with iterative deepening
        best_move = valid_moves[0]
        
        # Time management - leave buffer for safety
        start_time = time.time()
        time_limit = 0.85  # seconds
        
        # Iterative deepening: try deeper searches until time runs out
        for depth in range(1, 10):
            if time.time() - start_time > time_limit:
                break
                
            move_scores = {}
            for col in valid_moves:
                # Simulate move
                row = get_next_open_row(board, col)
                board[row][col] = 1
                
                # Run minimax search
                score = minimax(board, depth-1, float('-inf'), float('inf'), False)
                move_scores[col] = score
                
                # Undo move
                board[row][col] = 0
                
                # Early exit if winning move found
                if score >= 10000:
                    return col
            
            # Choose best move from this depth
            if move_scores:
                current_best = max(move_scores.keys(), key=lambda x: move_scores[x])
                best_move = current_best
        
        return best_move
    
    except Exception:
        # Fallback: return first valid move to avoid disqualification
        board = np.array(board, dtype=np.int8)
        valid_moves = get_valid_moves(board)
        return valid_moves[0] if valid_moves else 0

def get_valid_moves(board):
    """Return list of columns that are not full"""
    valid = []
    for col in range(7):
        if board[0][col] == 0:  # Top row empty means column not full
            valid.append(col)
    return valid

def is_winning_move(board, col, player):
    """Check if dropping player's disc in col results in win"""
    row = get_next_open_row(board, col)
    if row is None:
        return False
    
    # Temporarily place the piece
    board[row][col] = player
    win = check_win(board, player, row, col)
    board[row][col] = 0  # Reset
    return win

def get_next_open_row(board, col):
    """Get the next open row in column (None if full)"""
    for row in range(5, -1, -1):  # Bottom to top
        if board[row][col] == 0:
            return row
    return None

def check_win(board, player, row, col):
    """Check if player has 4 in a row after move at (row, col)"""
    # Check all four directions
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        # Check both directions
        for sign in [1, -1]:
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r += sign * dr
                c += sign * dc
        if count >= 4:
            return True
    return False

def minimax(board, depth, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning"""
    
    valid_moves = get_valid_moves(board)
    
    # Terminal states
    if len(valid_moves) == 0:
        return 0
    
    # Depth limit reached - use heuristic
    if depth == 0:
        return evaluate_board(board)
    
    # Sort moves for better pruning
    valid_moves.sort(key=lambda c: abs(c - 3))
    
    if maximizing:
        max_eval = float('-inf')
        for col in valid_moves:
            row = get_next_open_row(board, col)
            board[row][col] = 1
            
            # Check if this move wins
            if check_win(board, 1, row, col):
                board[row][col] = 0
                return 10000
            
            eval_score = minimax(board, depth-1, alpha, beta, False)
            board[row][col] = 0
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in valid_moves:
            row = get_next_open_row(board, col)
            board[row][col] = -1
            
            # Check if opponent wins
            if check_win(board, -1, row, col):
                board[row][col] = 0
                return -10000
            
            eval_score = minimax(board, depth-1, alpha, beta, True)
            board[row][col] = 0
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate_board(board):
    """Heuristic evaluation of board position for maximizing player"""
    score = 0
    
    # Central column is most valuable (control the center)
    center_count = np.count_nonzero(board[:, 3] == 1) - np.count_nonzero(board[:, 3] == -1)
    score += center_count * 3
    
    # Evaluate all potential 4-in-a-row windows
    windows = get_all_windows(board)
    
    for window in windows:
        score += evaluate_window(window)
    
    return score

def get_all_windows(board):
    """Get all possible 4-cell windows for evaluation"""
    windows = []
    
    # Horizontal windows
    for r in range(6):
        for c in range(4):
            windows.append(board[r, c:c+4])
    
    # Vertical windows
    for r in range(3):
        for c in range(7):
            windows.append(board[r:r+4, c])
    
    # Positive diagonal windows
    for r in range(3):
        for c in range(4):
            window = [board[r+i][c+i] for i in range(4)]
            windows.append(window)
    
    # Negative diagonal windows
    for r in range(3, 6):
        for c in range(4):
            window = [board[r-i][c+i] for i in range(4)]
            windows.append(window)
    
    return windows

def evaluate_window(window):
    """Evaluate a single 4-cell window and return a score"""
    # Quick numpy sum check for efficiency
    if isinstance(window, np.ndarray):
        window_sum = np.sum(window)
        if window_sum == 4:
            return 1000
        if window_sum == -4:
            return -1000
    
    # Count pieces (for list windows or if sum check didn't trigger)
    player_count = window.count(1) if isinstance(window, list) else np.count_nonzero(window == 1)
    opponent_count = window.count(-1) if isinstance(window, list) else np.count_nonzero(window == -1)
    
    # Winning windows
    if player_count == 4:
        return 1000
    if opponent_count == 4:
        return -1000
    
    # Strong preference for 3 in a row (with empty space to complete)
    if player_count == 3 and opponent_count == 0:
        return 10
    if opponent_count == 3 and player_count == 0:
        return -10
    
    # Prefer 2 in a row
    if player_count == 2 and opponent_count == 0:
        return 2
    if opponent_count == 2 and player_count == 0:
        return -2
    
    return 0
