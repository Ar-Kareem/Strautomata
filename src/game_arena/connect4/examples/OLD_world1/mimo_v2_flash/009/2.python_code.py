
import sys
import time

def policy(board: list[list[int]]) -> int:
    """
    Implements a Connect 4 AI using Minimax with Alpha-Beta pruning and Iterative Deepening.
    The AI prioritizes immediate wins, blocks immediate opponent wins, and then evaluates
    the board state based on positional advantage and potential threats.
    """
    start_time = time.time()
    TIMEOUT = 0.9  # Leave some buffer for overhead

    ROWS = 6
    COLS = 7
    
    # Create a transposed view of the board for easier column access
    # cols[col][row]
    cols = [[board[r][c] for r in range(ROWS)] for c in range(COLS)]

    # Pre-calculate valid moves to avoid redundant checks
    def get_valid_moves():
        valid = []
        for c in range(COLS):
            if cols[c][0] == 0: # Check top cell is empty
                valid.append(c)
        return valid

    # Check for a win for a specific player (1 or -1)
    def check_win(player):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if cols[c][r] == player and cols[c+1][r] == player and cols[c+2][r] == player and cols[c+3][r] == player:
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if cols[c][r] == player and cols[c][r+1] == player and cols[c][r+2] == player and cols[c][r+3] == player:
                    return True
        # Diagonals
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if cols[c][r] == player and cols[c+1][r+1] == player and cols[c+2][r+2] == player and cols[c+3][r+3] == player:
                    return True
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if cols[c][r] == player and cols[c+1][r-1] == player and cols[c+2][r-2] == player and cols[c+3][r-3] == player:
                    return True
        return False

    # Check if the current move creates a win for the player
    def check_win_at(col, player):
        # Find the row where the piece lands
        row = -1
        for r in range(ROWS - 1, -1, -1):
            if cols[col][r] == 0:
                row = r
                break
        if row == -1: return False # Should not happen if valid

        # Helper to check a sequence starting at (row, col) with delta (dr, dc)
        def count_in_dir(dr, dc):
            count = 1 # The piece we just placed
            # Check forward
            r, c = row + dr, col + dc
            while 0 <= r < ROWS and 0 <= c < COLS and cols[c][r] == player:
                count += 1
                r += dr
                c += dc
            # Check backward
            r, c = row - dr, col - dc
            while 0 <= r < ROWS and 0 <= c < COLS and cols[c][r] == player:
                count += 1
                r -= dr
                c -= dc
            return count >= 4

        # Horizontal
        if count_in_dir(0, 1): return True
        # Vertical
        if count_in_dir(1, 0): return True
        # Diagonal \
        if count_in_dir(1, 1): return True
        # Diagonal /
        if count_in_dir(1, -1): return True
        
        return False

    # Evaluation function
    def evaluate_window(window, player):
        opp = -player
        count_p = window.count(player)
        count_o = window.count(opp)
        count_e = window.count(0)

        if count_p == 4: return 100000 # Should be handled by win check, but safe to have
        if count_p == 3 and count_e == 1: return 5000 # Strong threat
        if count_p == 2 and count_e == 2: return 200 # Moderate potential
        if count_p == 1 and count_e == 3: return 10 # Setup
        
        # Opponent threats (we want to prevent these)
        if count_o == 3 and count_e == 1: return -8000 # Must block
        if count_o == 2 and count_e == 2: return -150
        
        return 0

    def score_position(player):
        score = 0
        
        # Center column preference
        center_col = cols[3]
        center_count = sum(1 for r in range(ROWS) if center_col[r] == player)
        score += center_count * 10
        
        # Horizontal
        for r in range(ROWS):
            row_array = [cols[c][r] for c in range(COLS)]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, player)

        # Vertical
        for c in range(COLS):
            col_array = [cols[c][r] for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, player)

        # Positive Diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [cols[c+i][r+i] for i in range(4)]
                score += evaluate_window(window, player)

        # Negative Diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [cols[c+i][r-i] for i in range(4)]
                score += evaluate_window(window, player)
                
        return score

    def minimax(alpha, beta, depth, is_maximizing, start_player):
        # Check timeout
        if time.time() - start_time > TIMEOUT:
            return 0 # Timeout indicator
        
        # Check terminal states or depth limit
        if depth == 0:
            return score_position(start_player)
        
        # Check win for the player who just moved (previous turn)
        # If is_maximizing is True, it means it's AI's turn now, so the previous move was Opponent's.
        # We check if Opponent won. If so, return -Infinity (bad for AI).
        # If is_maximizing is False, previous was AI. If AI won, return +Infinity.
        
        # Actually, it's safer to check based on who's turn it IS.
        # We are exploring the tree. 
        # If it's maximizing turn (AI), the previous move was Opponent. 
        # We need to see if Opponent created a win.
        # But wait, the board state passed to minimax represents the state BEFORE the move.
        # Let's handle board state modification outside.
        
        valid_moves = get_valid_moves()
        
        if not valid_moves:
            return 0 # Draw
        
        # Move ordering: Center first, then outwards
        valid_moves.sort(key=lambda x: abs(x - 3))
        
        if is_maximizing:
            max_eval = -float('inf')
            for col in valid_moves:
                # Apply move
                row = -1
                for r in range(ROWS - 1, -1, -1):
                    if cols[col][r] == 0:
                        cols[col][r] = start_player
                        row = r
                        break
                
                # Check immediate win
                if check_win_at(col, start_player):
                    eval_score = 1000000 + depth
                else:
                    eval_score = minimax(alpha, beta, depth - 1, False, start_player)
                
                # Undo move
                cols[col][row] = 0
                
                if eval_score > max_eval:
                    max_eval = eval_score
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            opp = -start_player
            for col in valid_moves:
                # Apply move
                row = -1
                for r in range(ROWS - 1, -1, -1):
                    if cols[col][r] == 0:
                        cols[col][r] = opp
                        row = r
                        break
                
                # Check immediate win
                if check_win_at(col, opp):
                    eval_score = -1000000 - depth
                else:
                    eval_score = minimax(alpha, beta, depth - 1, True, start_player)
                
                # Undo move
                cols[col][row] = 0
                
                if eval_score < min_eval:
                    min_eval = eval_score
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Logic ---

    # 1. Check for immediate win (pruning)
    valid_moves = get_valid_moves()
    # Sort by center preference
    valid_moves.sort(key=lambda x: abs(x - 3))
    
    for col in valid_moves:
        if check_win_at(col, 1):
            return col

    # 2. Check for immediate opponent threat next turn and block it
    # We must block if opponent has a winning move.
    # Optimization: Only check moves that could potentially win for opponent.
    # But standard check is fast enough (42 max states).
    for col in valid_moves:
        # Simulate opponent move
        row = -1
        for r in range(ROWS - 1, -1, -1):
            if cols[col][r] == 0:
                cols[col][r] = -1
                row = r
                break
        if check_win_at(col, -1):
            # Undo
            cols[col][row] = 0
            # If opponent wins here, we MUST play here to block
            # But wait, check if we can also win by playing here? 
            # If we play here, we occupy the spot. If opponent wins there, we can't block by playing elsewhere.
            # If this move blocks AND gives us a win, we already checked that in step 1.
            # So this is strictly a block.
            return col
        cols[col][row] = 0

    # 3. Lookahead
    # Iterative Deepening
    best_move = valid_moves[0] # Default to first valid
    best_score = -float('inf')
    
    max_depth = 1
    while True:
        if time.time() - start_time > TIMEOUT:
            break
        
        current_best_move = best_move
        current_best_score = -float('inf')
        
        for col in valid_moves:
            if time.time() - start_time > TIMEOUT:
                break
            
            # Apply move
            row = -1
            for r in range(ROWS - 1, -1, -1):
                if cols[col][r] == 0:
                    cols[col][r] = 1
                    row = r
                    break
            
            # Check win
            if check_win_at(col, 1):
                score = 1000000 + max_depth
            else:
                score = minimax(-float('inf'), float('inf'), max_depth - 1, False, 1)
            
            # Undo
            cols[col][row] = 0
            
            if score > current_best_score:
                current_best_score = score
                current_best_move = col
        
        if time.time() <= TIMEOUT:
            best_score = current_best_score
            best_move = current_best_move
            max_depth += 1
            if max_depth > 10: # Hard cap just in case
                break
        else:
            break

    return best_move
