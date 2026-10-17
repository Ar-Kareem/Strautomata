
import sys
import time

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI Policy using Minimax with Alpha-Beta Pruning.
    Optimized for speed and standard 6x7 grid.
    """
    
    # Constants
    ROWS = 6
    COLS = 7
    EMPTY = 0
    ME = 1
    OPP = -1
    MAX_DEPTH = 9  # Initial max depth to aim for
    TIME_LIMIT = 0.85 # Seconds (leaving buffer for overhead)
    
    # Move ordering: Center columns first
    COLUMN_ORDER = [3, 2, 4, 1, 5, 0, 6]
    
    # Precompute winning lines for evaluation (caching coordinates)
    # Returns a list of lists, where each inner list contains 4 coordinates (r, c)
    def get_all_wins():
        lines = []
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                lines.append([(r, c), (r, c+1), (r, c+2), (r, c+3)])
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                lines.append([(r, c), (r+1, c), (r+2, c), (r+3, c)])
        # Diagonal Down-Right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                lines.append([(r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)])
        # Diagonal Up-Right
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                lines.append([(r, c), (r-1, c+1), (r-2, c+2), (r-3, c+3)])
        return lines

    WIN_LINES = get_all_wins()

    def get_valid_moves(b):
        """Returns list of valid column indices."""
        valid = []
        for c in COLUMN_ORDER:
            if b[0][c] == EMPTY:
                valid.append(c)
        return valid

    def drop_disc(b, col, player):
        """Returns new board with disc dropped, or None if invalid."""
        # Find lowest empty row
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == EMPTY:
                b[r][col] = player
                return b
        return None

    def undo_disc(b, col):
        """Removes the top disc from the column."""
        for r in range(ROWS):
            if b[r][col] != EMPTY:
                b[r][col] = EMPTY
                return

    def check_win(b):
        """Checks if the board is in a terminal state (win/loss/draw)."""
        # Optimization: We only need to check the last move, but checking whole board is safer for generic logic
        # Given time constraints, checking all lines is fine for terminal checks
        for line in WIN_LINES:
            vals = [b[r][c] for r, c in line]
            if vals.count(ME) == 4:
                return 100000 # Win
            if vals.count(OPP) == 4:
                return -100000 # Loss
        # Check for draw (no empty cells)
        if all(b[0][c] != EMPTY for c in range(COLS)):
            return 0 # Draw
        return None # Game not over

    def heuristic(b):
        """
        Evaluates the board heuristically.
        Scores are based on potential lines of 2 and 3.
        """
        score = 0
        
        # Center column preference
        center_array = [b[r][3] for r in range(ROWS)]
        score += center_array.count(ME) * 3
        score -= center_array.count(OPP) * 3

        for line in WIN_LINES:
            vals = [b[r][c] for r, c in line]
            my_count = vals.count(ME)
            opp_count = vals.count(OPP)
            empty = vals.count(EMPTY)
            
            # Scoring Logic
            if my_count == 3 and empty == 1: score += 100
            elif my_count == 2 and empty == 2: score += 10
            
            if opp_count == 3 and empty == 1: score -= 120 # Block threat is higher
            elif opp_count == 2 and empty == 2: score -= 5
            
        return score

    def minimax(b, depth, alpha, beta, maximizing, start_time, cache):
        """
        Minimax with Alpha-Beta pruning.
        Returns (score, best_col)
        """
        # Check time
        if time.time() - start_time > TIME_LIMIT:
            return None, None # Signal timeout

        # Check terminal state
        terminal_result = check_win(b)
        if terminal_result is not None:
            return terminal_result, None
        
        # Depth limit
        if depth == 0:
            return heuristic(b), None

        # Transposition Table Key (String representation of board)
        # Fast enough for 6x7
        board_key = "".join(str(cell) for row in b for cell in row)
        if board_key in cache:
            cached_depth, cached_score = cache[board_key]
            if cached_depth >= depth:
                return cached_score, None

        valid_moves = get_valid_moves(b)
        
        if not valid_moves:
            return 0, None # Draw

        best_col = valid_moves[0]

        if maximizing:
            max_eval = -float('inf')
            for col in valid_moves:
                # Apply move
                drop_disc(b, col, ME)
                
                eval_score, _ = minimax(b, depth - 1, alpha, beta, False, start_time, cache)
                
                # Undo move
                undo_disc(b, col)

                if eval_score is None: # Timeout occurred
                    return None, None

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            cache[board_key] = (depth, max_eval)
            return max_eval, best_col
        
        else: # Minimizing
            min_eval = float('inf')
            for col in valid_moves:
                # Apply move
                drop_disc(b, col, OPP)
                
                eval_score, _ = minimax(b, depth - 1, alpha, beta, True, start_time, cache)
                
                # Undo move
                undo_disc(b, col)

                if eval_score is None:
                    return None, None

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            cache[board_key] = (depth, min_eval)
            return min_eval, best_col

    # --- Main Execution ---
    
    # 1. Immediate Win Check (Look ahead 1 move)
    # If I can win now, do it.
    # If opponent can win next turn, block it.
    
    # Check if I can win
    for col in COLUMN_ORDER:
        if board[0][col] == EMPTY:
            # Simulate
            r = -1
            for i in range(ROWS - 1, -1, -1):
                if board[i][col] == EMPTY:
                    r = i
                    break
            board[r][col] = ME
            win = check_win(board)
            board[r][col] = EMPTY
            if win == 100000:
                return col

    # Check if opponent can win (Block)
    for col in COLUMN_ORDER:
        if board[0][col] == EMPTY:
            r = -1
            for i in range(ROWS - 1, -1, -1):
                if board[i][col] == EMPTY:
                    r = i
                    break
            board[r][col] = OPP
            win = check_win(board)
            board[r][col] = EMPTY
            if win == -100000:
                return col

    # 2. Minimax Search
    # We copy the board? No, we manipulate in place and undo. 
    # But the board passed in is a list reference. We must be careful not to modify it permanently
    # until we return the move. Actually, we don't modify the input board, we just simulate on it.
    # Wait, `drop_disc` modifies the board in place. Since `board` is passed to us, we should
    # strictly operate on a copy or ensure we undo perfectly. 
    # Given the constraints, let's create a shallow copy of rows to be safe, 
    # OR just rely on the fact that we undo every operation exactly.
    # "You are allowed to modify the board variable as long as you restore it before returning" -> usually not the case.
    # Safer to pass a copy to minimax.
    
    # Actually, Python lists are mutable. If we modify `board` inside `policy`, the caller sees it.
    # The instructions imply we just return an int. It's best practice NOT to modify input.
    # However, creating a deep copy of 42 cells is cheap.
    
    start_time = time.time()
    cache = {}
    
    # We will use a temporary board for calculations to be safe
    # But to save time/memory, let's just be very careful with undo.
    # Let's modify the passed board directly but undo immediately.
    # Wait, what if the caller expects `board` to remain unchanged?
    # The prompt says: "Your code is allowed 1 second... Output only the Python source code".
    # It doesn't explicitly forbid modifying the board reference, but it's dangerous.
    # Let's use a shallow copy of rows.
    
    temp_board = [row[:] for row in board]
    
    best_score = -float('inf')
    best_move = COLUMN_ORDER[0]
    
    # Iterative Deepening (Time-based)
    # We start depth small, increase. If time runs out, we use previous best.
    for depth in range(1, MAX_DEPTH + 1):
        score, move = minimax(temp_board, depth, -float('inf'), float('inf'), True, start_time, cache)
        
        # If timeout or error
        if score is None:
            break
        
        best_score = score
        best_move = move
        
        # If we found a forced win/loss, we might break early, but let's trust the search depth.
        if abs(score) > 50000: # Very high score indicates forced win
            break

    return best_move
