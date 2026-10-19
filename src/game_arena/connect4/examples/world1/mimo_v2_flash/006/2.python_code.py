
import sys
import time
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI using Iterative Deepening Minimax with Alpha-Beta pruning.
    """
    start_time = time.time()
    
    # Constants
    ROWS = 6
    COLS = 7
    INF = float('inf')
    MAX_DEPTH = 20  # Cap for safety
    TIME_LIMIT = 0.95 # seconds

    # Convert board to numpy array for easier slicing
    b = np.array(board)

    # Helper: Check if a column is not full
    def is_valid(col):
        return b[0][col] == 0

    # Helper: Get the first empty row in a column
    def get_next_open_row(col):
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                return r
        return -1

    # Helper: Check for a win
    def winning_move(piece, board_state=None):
        if board_state is None:
            board_state = b
        
        # Horizontal
        for c in range(COLS - 3):
            for r in range(ROWS):
                if board_state[r][c] == piece and board_state[r][c+1] == piece and board_state[r][c+2] == piece and board_state[r][c+3] == piece:
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if board_state[r][c] == piece and board_state[r+1][c] == piece and board_state[r+2][c] == piece and board_state[r+3][c] == piece:
                    return True
        # Positive Diagonal
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if board_state[r][c] == piece and board_state[r-1][c+1] == piece and board_state[r-2][c+2] == piece and board_state[r-3][c+3] == piece:
                    return True
        # Negative Diagonal
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if board_state[r][c] == piece and board_state[r+1][c+1] == piece and board_state[r+2][c+2] == piece and board_state[r+3][c+3] == piece:
                    return True
        return False

    # Heuristic Evaluation Function
    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece
        
        count_piece = np.count_nonzero(window == piece)
        count_opp = np.count_nonzero(window == opp_piece)
        count_empty = np.count_nonzero(window == 0)
        
        if count_piece == 4:
            score += 100000
        elif count_piece == 3 and count_empty == 1:
            score += 100
        elif count_piece == 2 and count_empty == 2:
            score += 10
        
        if count_opp == 3 and count_empty == 1:
            score -= 80 # Block opponent
            
        return score

    def score_position(board_state, piece):
        score = 0
        
        # Center column preference
        center_array = board_state[:, 3]
        center_count = np.count_nonzero(center_array == piece)
        score += center_count * 3

        # Horizontal
        for r in range(ROWS):
            row_array = board_state[r, :]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)

        # Vertical
        for c in range(COLS):
            col_array = board_state[:, c]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)

        # Positive Diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board_state[r-i][c+i] for i in range(4)]
                score += evaluate_window(np.array(window), piece)

        # Negative Diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board_state[r+i][c+i] for i in range(4)]
                score += evaluate_window(np.array(window), piece)

        return score

    # Order moves: Center columns first for better pruning
    def get_valid_locations():
        valid = [c for c in range(COLS) if is_valid(c)]
        # Sort by distance from center (abs(3-c))
        valid.sort(key=lambda x: abs(3 - x))
        return valid

    # Minimax with Alpha-Beta Pruning
    def minimax(alpha, beta, depth, maximizingPlayer):
        # Time check
        if time.time() - start_time > TIME_LIMIT:
            return None, 0 # Return None to signal timeout

        # Terminal node checks
        if winning_move(1, b): # AI wins
            return None, 1000000000
        if winning_move(-1, b): # Opponent wins
            return None, -1000000000
        
        if depth == 0:
            return None, score_position(b, 1)

        valid_locations = get_valid_locations()
        
        if not valid_locations: # Board full
            return None, 0

        if maximizingPlayer:
            value = -INF
            column = valid_locations[0]
            for col in valid_locations:
                # Make move
                r = get_next_open_row(col)
                b[r][col] = 1
                
                # Recurse
                _, new_score = minimax(alpha, beta, depth - 1, False)
                
                # Undo move
                b[r][col] = 0
                
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            
            return column, value
        else:
            value = INF
            column = valid_locations[0]
            for col in valid_locations:
                r = get_next_open_row(col)
                b[r][col] = -1
                
                _, new_score = minimax(alpha, beta, depth - 1, True)
                
                b[r][col] = 0
                
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            
            return column, value

    # --- Main Logic ---

    # 1. Immediate Win Check
    valid_cols = get_valid_locations()
    for col in valid_cols:
        r = get_next_open_row(col)
        b[r][col] = 1
        if winning_move(1, b):
            b[r][col] = 0
            return col
        b[r][col] = 0

    # 2. Immediate Block Check
    for col in valid_cols:
        r = get_next_open_row(col)
        b[r][col] = -1
        if winning_move(-1, b):
            b[r][col] = 0
            # We must play here, but return later to ensure move ordering logic respects this check if needed
            # However, in minimax this is naturally handled, but doing it explicitly for speed is good.
            # Since we return, we verify it's valid again.
            return col
        b[r][col] = 0

    # 3. Iterative Deepening
    best_move = valid_cols[0]
    depth = 1
    last_score = 0
    
    while depth <= MAX_DEPTH:
        if time.time() - start_time > TIME_LIMIT:
            break
            
        # Aspiration Window (narrow the alpha-beta range based on previous guess)
        alpha = last_score - 25
        beta = last_score + 25
        
        # Initial search
        move, score = minimax(alpha, beta, depth, True)
        
        # If score falls outside window, re-search with full bounds
        if score <= alpha or score >= beta:
            if time.time() - start_time > TIME_LIMIT:
                break
            move, score = minimax(-INF, INF, depth, True)
        
        if move is not None:
            best_move = move
            last_score = score
        
        depth += 1

    return best_move
