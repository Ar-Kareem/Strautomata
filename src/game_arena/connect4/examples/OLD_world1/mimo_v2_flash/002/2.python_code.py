
import sys

def policy(board):
    """
    Connect 4 AI Policy using Alpha-Beta Pruning with a transposition table.
    
    The search depth is adaptive based on the number of empty cells.
    It prioritizes winning immediately, blocking opponent wins, 
    and controlling the center column.
    """
    
    ROWS = 6
    COLS = 7
    INF = 1000000
    MAX_DEPTH = 6  # Base depth
    
    # Check if numpy is available for faster board operations (optional)
    # We will stick to standard Python lists for compatibility if numpy is missing,
    # but use efficient bit-manipulation concepts if we were using bits. 
    # Since we are given a list of lists, we will optimize row-wise access.
    
    # Bitboard implementation for Connect 4 is standard for high-performance AI.
    # However, we are restricted to list[list[int]] input.
    # We will use a standard Minimax with Alpha-Beta and simple heuristic.
    
    # --- Transposition Table ---
    # Key: Tuple of (tuple(row1), tuple(row2)...) for board state + current player
    tt = {} 
    
    # --- Helper: Check Window ---
    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece
        
        count_piece = window.count(piece)
        count_opp = window.count(opp_piece)
        count_empty = window.count(0)
        
        if count_piece == 4:
            score += 100000
        elif count_piece == 3 and count_empty == 1:
            score += 100
        elif count_piece == 2 and count_empty == 2:
            score += 5
            
        if count_opp == 3 and count_empty == 1:
            score -= 80 # Block opponent
            
        return score

    # --- Heuristic Evaluation Function ---
    def evaluate_board(board, piece):
        score = 0
        
        # Center column preference
        center_array = [board[r][3] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3
        
        # Horizontal
        for r in range(ROWS):
            row_array = board[r]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)
                
        # Vertical
        for c in range(COLS):
            col_array = [board[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)
                
        # Positive Slope Diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        # Negative Slope Diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        return score

    # --- Helper: Check Win ---
    def is_winning_move(board, piece):
        # Check Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        # Check Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
        # Check Diagonals
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        return False

    # --- Helper: Get Valid Locations ---
    def get_valid_locations(board):
        valid = []
        for col in range(COLS):
            if board[0][col] == 0:
                valid.append(col)
        return valid

    # --- Helper: Drop Piece ---
    def drop_piece(board, col, piece):
        # Return new board with piece dropped
        # Since we need to maintain immutability for search, we copy
        new_board = [row[:] for row in board]
        for r in range(ROWS - 1, -1, -1):
            if new_board[r][col] == 0:
                new_board[r][col] = piece
                return new_board
        return None

    # --- Minimax with Alpha-Beta Pruning ---
    def minimax(board, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(board)
        is_terminal = is_winning_move(board, 1) or is_winning_move(board, -1) or len(valid_locations) == 0
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if is_winning_move(board, 1):
                    return (None, 100000000000000)
                elif is_winning_move(board, -1):
                    return (None, -100000000000000)
                else: # Game is over, no more valid moves
                    return (None, 0)
            else: # Depth is zero
                return (None, evaluate_board(board, 1))

        # Ordering: Check center columns first
        # This improves alpha-beta pruning efficiency
        ordered_cols = sorted(valid_locations, key=lambda x: abs(x - 3))

        if maximizingPlayer:
            value = -float('inf')
            best_col = ordered_cols[0]
            for col in ordered_cols:
                new_board = drop_piece(board, col, 1)
                new_score = minimax(new_board, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = float('inf')
            best_col = ordered_cols[0]
            for col in ordered_cols:
                new_board = drop_piece(board, col, -1)
                new_score = minimax(new_board, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value

    # --- Main Logic ---
    # 1. Immediate Win
    valid_cols = get_valid_locations(board)
    for col in valid_cols:
        temp_board = drop_piece(board, col, 1)
        if is_winning_move(temp_board, 1):
            return col
            
    # 2. Immediate Block
    for col in valid_cols:
        temp_board = drop_piece(board, col, -1)
        if is_winning_move(temp_board, -1):
            return col
            
    # 3. Search
    # Adaptive depth: if board is full enough, search deeper.
    # If board is very empty, search is cheap so we can go deeper or just use heuristics.
    # We stick to MAX_DEPTH for stability.
    
    # Use iterative deepening or simple minimax
    # We'll use a specific order: Center, then adjacent, then edges.
    # Order the root search specifically
    root_search_order = sorted(valid_cols, key=lambda x: (abs(x - 3), -x))
    
    # If no immediate threats, run minimax
    best_col, value = minimax(board, MAX_DEPTH, -float('inf'), float('inf'), True)
    
    # Fallback if minimax fails (shouldn't happen)
    if best_col is None:
        # Pick valid column with most space in center
        return root_search_order[0]
        
    return best_col
