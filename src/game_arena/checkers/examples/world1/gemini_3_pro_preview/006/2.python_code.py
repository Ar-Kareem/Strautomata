
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Checkers policy using Minimax with Alpha-Beta pruning.
    
    Args:
        my_men: List of (row, col) coordinates for my men.
        my_kings: List of (row, col) coordinates for my kings.
        opp_men: List of (row, col) coordinates for opponent men.
        opp_kings: List of (row, col) coordinates for opponent kings.
        color: 'b' or 'w'. 'b' moves down (row -1), 'w' moves up (row +1).
        
    Returns:
        tuple: ((from_row, from_col), (to_row, to_col))
    """
    
    # --- Configuration ---
    # Allowed time for calculation (seconds)
    TIME_LIMIT = 0.95
    start_time = time.time()
    
    # Search Depth (Ply)
    MAX_DEPTH = 4

    # --- Board Representation ---
    # 0: Empty
    # 1: My Man, 2: My King
    # -1: Opp Man, -2: Opp King
    board = [[0] * 8 for _ in range(8)]
    
    for r, c in my_men:
        board[r][c] = 1
    for r, c in my_kings:
        board[r][c] = 2
    for r, c in opp_men:
        board[r][c] = -1
    for r, c in opp_kings:
        board[r][c] = -2

    # Define forward direction based on color
    # 'w' (White) moves from 0 to 7 (Up, +1)
    # 'b' (Black) moves from 7 to 0 (Down, -1)
    forward = 1 if color == 'w' else -1
    promotion_row = 7 if color == 'w' else 0
    
    # --- Helper Functions ---

    def is_valid(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_legal_moves(board_state, player, active_piece=None):
        """
        Generates legal moves for 'player' (1 or -1).
        If 'active_piece' is set (r, c), only generates jumps for that piece (mid-chain).
        Returns: (moves_list, is_jump_flag)
        """
        jumps = []
        steps = []
        
        # Determine movement direction for the current player
        # If player is me (1), use 'forward'. If opp (-1), use '-forward'.
        p_forward = forward if player == 1 else -forward
        
        candidates = []
        if active_piece:
            candidates = [active_piece]
        else:
            for r in range(8):
                for c in range(8):
                    piece = board_state[r][c]
                    if piece * player > 0: # Checks if piece belongs to player
                        candidates.append((r, c))
        
        for r, c in candidates:
            piece = board_state[r][c]
            is_king = abs(piece) == 2
            
            # Directions: Kings move all 4 diagonals, Men move forward diagonals
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(p_forward, -1), (p_forward, 1)]
            
            for dr, dc in dirs:
                # Check Jump
                r_mid, c_mid = r + dr, c + dc
                r_end, c_end = r + 2*dr, c + 2*dc
                
                if is_valid(r_end, c_end):
                    mid_p = board_state[r_mid][c_mid]
                    end_p = board_state[r_end][c_end]
                    
                    # Valid Jump: Mid is enemy, End is empty
                    if (mid_p * player < 0) and (end_p == 0):
                        jumps.append(((r, c), (r_end, c_end)))
                
                # Check Step (only if not restricted by active_piece)
                if not active_piece:
                    r_step, c_step = r + dr, c + dc
                    if is_valid(r_step, c_step):
                        if board_state[r_step][c_step] == 0:
                            steps.append(((r, c), (r_step, c_step)))

        if jumps:
            return jumps, True  # Mandatory capture rule: if jumps exist, only jumps valid
        
        # If active_piece was set and no jumps found, it means chain ended. Return empty.
        if active_piece:
            return [], False
            
        return steps, False

    def evaluate(board_state):
        """Heuristic evaluation from the perspective of the bot (Player 1)."""
        score = 0
        for r in range(8):
            for c in range(8):
                p = board_state[r][c]
                if p == 0: continue
                
                # Base material
                val = 10 if abs(p) == 1 else 30
                
                # Central Control (Rows 3,4 Cols 2-5)
                if 2 <= c <= 5 and 3 <= r <= 4:
                    val += 2

                # Advancement for Men
                if abs(p) == 1:
                    # 'w' (1) wants r to be high, 'b' (-1) wants r to be low
                    # p > 0 is Me.
                    if p > 0:
                        advancement = r if color == 'w' else (7 - r)
                        val += advancement
                    else:
                        # Opponent logic (symmetric)
                        opp_adv = (7 - r) if color == 'w' else r
                        val += opp_adv
                
                # Back/King Rank Safety (Keep men on own baseline)
                # My baseline is 0 if 'w', 7 if 'b'.
                my_baseline = 0 if color == 'w' else 7
                if p == 1 and r == my_baseline:
                    val += 5
                
                if p > 0:
                    score += val
                else:
                    score -= val
        return score

    def minimax(board_state, depth, alpha, beta, is_max, active_piece=None):
        # Check time constraint slightly aggressively
        if (time.time() - start_time) > TIME_LIMIT:
            return evaluate(board_state)

        player = 1 if is_max else -1
        moves, is_jump = get_legal_moves(board_state, player, active_piece)
        
        # Terminal conditions
        if not moves:
            # If we were in a chain (active_piece) and no moves, the turn ends.
            # We must evaluate the board for the *next* player's turn start.
            if active_piece:
                return minimax(board_state, depth - 1, alpha, beta, not is_max, None)
            
            # If start of turn and no moves, game over (loss for current player)
            # Return big penalty/bonus
            return -1000 if is_max else 1000
        
        if depth <= 0 and not active_piece:
             return evaluate(board_state)

        best_val = -float('inf') if is_max else float('inf')

        for move in moves:
            (r1, c1), (r2, c2) = move
            
            # --- Emulate Move ---
            moving_p = board_state[r1][c1]
            captured_p = 0
            cap_r, cap_c = 0, 0
            
            board_state[r1][c1] = 0
            board_state[r2][c2] = moving_p
            
            # Handle Capture
            if is_jump:
                cap_r, cap_c = (r1 + r2) // 2, (c1 + c2) // 2
                captured_p = board_state[cap_r][cap_c]
                board_state[cap_r][cap_c] = 0
            
            # Handle Promotion
            promoted = False
            if abs(moving_p) == 1:
                # White promotes at 7, Black at 0
                target_r = 7 if (moving_p > 0 and color == 'w') or (moving_p < 0 and color == 'b') else 0
                # Use simplified logic based on 'forward'
                # My Pieces (1) promote at promotion_row. Opp (-1) at 7-promotion_row.
                my_prom = promotion_row
                opp_prom = 7 - promotion_row if promotion_row == 7 else 7 # 0 -> 7, 7 -> 0
                
                check_row = my_prom if moving_p > 0 else opp_prom
                
                if r2 == check_row:
                    board_state[r2][c2] = moving_p * 2 # Become +/- 2
                    promoted = True
            
            # --- Recursion ---
            val = 0
            
            # Logic: If jump and NOT promoted, check for multi-jump chain
            if is_jump and not promoted:
                # Check if this specific piece can jump again
                can_chain, _ = get_legal_moves(board_state, player, active_piece=(r2, c2))
                if can_chain:
                    # Must continue jumping (same player, same depth usually, or depth-0.5?)
                    # Pass active_piece to enforce continuity
                    val = minimax(board_state, depth, alpha, beta, is_max, active_piece=(r2, c2))
                else:
                    # Turn ends, switch player
                    val = minimax(board_state, depth - 1, alpha, beta, not is_max, None)
            else:
                # Step or Promoted (turn ends)
                val = minimax(board_state, depth - 1, alpha, beta, not is_max, None)
            
            # --- Backtrack (Undo Move) ---
            board_state[r1][c1] = moving_p
            board_state[r2][c2] = 0
            if is_jump:
                board_state[cap_r][cap_c] = captured_p
            
            # --- Alpha-Beta ---
            if is_max:
                best_val = max(best_val, val)
                alpha = max(alpha, best_val)
            else:
                best_val = min(best_val, val)
                beta = min(beta, best_val)
            
            if beta <= alpha:
                break
                
        return best_val

    # --- Root Search ---
    # We are player 1 (Maximizing)
    root_moves, is_jump = get_legal_moves(board, 1, None)
    
    if not root_moves:
        return ((0, 0), (0, 0)) # Should handle gracefully if no moves (loss)

    best_move = root_moves[0]
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    for move in root_moves:
        (r1, c1), (r2, c2) = move
        
        # Apply Move
        p = board[r1][c1]
        board[r1][c1] = 0
        board[r2][c2] = p
        
        captured = 0
        cap_r, cap_c = 0, 0
        if is_jump:
            cap_r, cap_c = (r1 + r2) // 2, (c1 + c2) // 2
            captured = board[cap_r][cap_c]
            board[cap_r][cap_c] = 0
            
        promoted = False
        if abs(p) == 1:
             if r2 == promotion_row:
                 board[r2][c2] = 2
                 promoted = True
        
        # Decide next state
        val = 0
        if is_jump and not promoted:
            # Check for chain
            chain_moves, _ = get_legal_moves(board, 1, active_piece=(r2, c2))
            if chain_moves:
                val = minimax(board, MAX_DEPTH, alpha, beta, True, active_piece=(r2, c2))
            else:
                val = minimax(board, MAX_DEPTH - 1, alpha, beta, False, None)
        else:
            val = minimax(board, MAX_DEPTH - 1, alpha, beta, False, None)
            
        # Backtrack
        board[r1][c1] = p
        board[r2][c2] = 0
        if is_jump:
            board[cap_r][cap_c] = captured
            
        if val > best_value:
            best_value = val
            best_move = move
            
        alpha = max(alpha, best_value)
        
        # Time safety break
        if (time.time() - start_time) > TIME_LIMIT:
            break

    return best_move
