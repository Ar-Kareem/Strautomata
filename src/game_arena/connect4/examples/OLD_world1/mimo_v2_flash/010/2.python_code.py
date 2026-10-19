
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI Policy.
    Implements a depth-limited minimax with alpha-beta pruning and 
    aggressive heuristics (center control, threat detection, threat blocking).
    """
    
    # Convert board to numpy array for easier manipulation
    # board is List[List[int]], usually shape (6, 7)
    board_np = np.array(board, dtype=int)
    ROWS, COLS = 6, 7
    PLAYER = 1
    OPPONENT = -1
    
    # Helper to get valid columns
    def get_valid_cols(b):
        valid = []
        for c in range(COLS):
            if b[0, c] == 0:
                valid.append(c)
        return valid

    # Helper to drop a piece and return the resulting board
    def drop_piece(b, col, player):
        # Make a copy to avoid modifying original
        new_b = b.copy()
        # Find the lowest empty row in the column
        # Iterate from bottom (ROWS-1) to top (0)
        for r in range(ROWS - 1, -1, -1):
            if new_b[r, col] == 0:
                new_b[r, col] = player
                return new_b, r
        return None, -1

    # Helper to check for a win for a specific player
    def check_win(b, player):
        # Check horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if b[r, c] == player and b[r, c+1] == player and b[r, c+2] == player and b[r, c+3] == player:
                    return True
        # Check vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if b[r, c] == player and b[r+1, c] == player and b[r+2, c] == player and b[r+3, c] == player:
                    return True
        # Check diagonal (down-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if b[r, c] == player and b[r+1, c+1] == player and b[r+2, c+2] == player and b[r+3, c+3] == player:
                    return True
        # Check diagonal (down-left)
        for r in range(ROWS - 3):
            for c in range(3, COLS):
                if b[r, c] == player and b[r+1, c-1] == player and b[r+2, c-2] == player and b[r+3, c-3] == player:
                    return True
        return False

    # Heuristic Evaluation Function
    def evaluate_window(window, player):
        opp = -player
        score = 0
        
        p_count = np.count_nonzero(window == player)
        o_count = np.count_nonzero(window == opp)
        empty_count = np.count_nonzero(window == 0)

        # 4 in a row (Win)
        if p_count == 4:
            return 100000 # Should be caught by check_win, but just in case
        
        # Threat: Opponent has 3 and 1 empty (Must block)
        if o_count == 3 and empty_count == 1:
            return -10000
        
        # Opportunity: Player has 3 and 1 empty
        if p_count == 3 and empty_count == 1:
            return 100
        
        # Opportunity: Player has 2 and 2 empty
        if p_count == 2 and empty_count == 2:
            return 10
            
        return score

    def score_position(b, player):
        score = 0
        
        # Center Control: Prefer columns 3, 2, 4
        center_array = b[:, 3]
        center_count = np.count_nonzero(center_array == player)
        score += center_count * 3
        
        # Horizontal windows
        for r in range(ROWS):
            row_array = b[r, :]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, player)

        # Vertical windows
        for c in range(COLS):
            col_array = b[:, c]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, player)

        # Diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = np.array([b[r, c], b[r+1, c+1], b[r+2, c+2], b[r+3, c+3]])
                score += evaluate_window(window, player)

        # Diagonal down-left
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = np.array([b[r, c+3], b[r+1, c+2], b[r+2, c+1], b[r+3, c]])
                score += evaluate_window(window, player)

        return score

    # Minimax with Alpha-Beta Pruning
    def minimax(b, depth, alpha, beta, maximizingPlayer):
        valid_moves = get_valid_cols(b)
        
        # Terminal node checks
        is_terminal = check_win(b, PLAYER) or check_win(b, OPPONENT) or len(valid_moves) == 0
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(b, PLAYER):
                    return (None, 1000000000)
                elif check_win(b, OPPONENT):
                    return (None, -1000000000)
                else:
                    return (None, 0)
            else:
                return (None, score_position(b, PLAYER))

        if maximizingPlayer:
            value = -float('inf')
            column = np.random.choice(valid_moves)
            
            # Optimization: Order moves (Center columns first)
            valid_moves.sort(key=lambda x: abs(x - 3))
            
            for col in valid_moves:
                new_b, _ = drop_piece(b, col, PLAYER)
                new_score = minimax(new_b, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = np.random.choice(valid_moves)
            
            valid_moves.sort(key=lambda x: abs(x - 3))

            for col in valid_moves:
                new_b, _ = drop_piece(b, col, OPPONENT)
                new_score = minimax(new_b, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # --- Main Logic ---
    
    # 1. Check if we can win immediately
    valid_cols = get_valid_cols(board_np)
    for col in valid_cols:
        new_b, _ = drop_piece(board_np, col, PLAYER)
        if check_win(new_b, PLAYER):
            return col
            
    # 2. Check if opponent can win next turn and block them
    for col in valid_cols:
        new_b, _ = drop_piece(board_np, col, OPPONENT)
        if check_win(new_b, OPPONENT):
            return col

    # 3. Run Minimax
    # Set depth based on board state. 
    # If board is nearly empty, we can search deeper.
    # If board is filling up, search gets faster.
    # To stay within 1 second, we usually cap at depth 5 or 6.
    # We count empty cells to adjust depth dynamically.
    empty_cells = np.count_nonzero(board_np == 0)
    
    if empty_cells > 35:
        depth = 4 # Early game: faster but broader
    elif empty_cells > 15:
        depth = 5 # Mid game
    else:
        depth = 6 # End game: precise
        
    best_col, _ = minimax(board_np, depth, -float('inf'), float('inf'), True)
    
    # Fallback (should not happen if board has valid moves)
    if best_col is None:
        # Pick center if possible, otherwise first valid
        if 3 in valid_cols: return 3
        return valid_cols[0]
        
    return best_col
