
import time

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 targeting policy using Iterative Deepening Minimax with Bitboards.
    Target execution time: < 1.0s.
    """
    
    # -------------------------------------------------------------------------
    # Constants & Config
    # -------------------------------------------------------------------------
    ROWS = 6
    COLS = 7
    # Use ~85% of allowed time to ensure safety margin
    TIME_LIMIT = 0.85 
    start_time = time.time()
    
    # Preferred move order: Center columns first
    SEARCH_ORDER = [3, 2, 4, 1, 5, 0, 6]

    # -------------------------------------------------------------------------
    # Bitboard Helpers
    # -------------------------------------------------------------------------
    # The board is represented by two 64-bit integers (bitboards).
    # Layout: Each column uses 7 bits (6 for rows + 1 buffer bit at top).
    # Bit Index Formula: index = col * 7 + (5 - row) where row 5 is bottom.
    
    def parse_board(grid):
        my_b = 0
        opp_b = 0
        hts = [0] * COLS
        for c in range(COLS):
            h = 0
            # Scan from bottom (row 5) to top (row 0)
            for r in range(ROWS - 1, -1, -1):
                val = grid[r][c]
                if val == 0:
                    break
                
                # Calculate bit index
                idx = c * 7 + (ROWS - 1 - r)
                
                if val == 1:
                    my_b |= (1 << idx)
                else: # -1
                    opp_b |= (1 << idx)
                h += 1
            hts[c] = h
        return my_b, opp_b, hts

    def check_win(bb):
        """
        Bitwise check for 4 connected bits in any direction.
        Directions: Vertical (1), Horizontal (7), Diag \ (6), Diag / (8)
        """
        # Horizontal
        m = bb & (bb >> 7)
        if m & (m >> 14): return True
        # Vertical 
        m = bb & (bb >> 1)
        if m & (m >> 2): return True
        # Diagonal \
        m = bb & (bb >> 6)
        if m & (m >> 12): return True
        # Diagonal /
        m = bb & (bb >> 8)
        if m & (m >> 16): return True
        return False

    def count_set_bits(n):
        return bin(n).count('1')

    def evaluate(my, opp):
        """
        Static evaluation of the board position.
        Uses column weights to prioritize center control.
        """
        score = 0
        
        # Column Masks (6 bits per column shift)
        # Col 3 (Center)
        mask_3 = 0b111111 << 21
        # Cols 2, 4
        mask_24 = (0b111111 << 14) | (0b111111 << 28)
        # Cols 1, 5
        mask_15 = (0b111111 << 7) | (0b111111 << 35)
        # Cols 0, 6 have weight 0 usually
        
        # Weights
        # My pieces
        score += count_set_bits(my & mask_3) * 5
        score += count_set_bits(my & mask_24) * 3
        score += count_set_bits(my & mask_15) * 1
        
        # Opponent pieces - penalty
        score -= count_set_bits(opp & mask_3) * 5
        score -= count_set_bits(opp & mask_24) * 3
        score -= count_set_bits(opp & mask_15) * 1
        
        return score

    # -------------------------------------------------------------------------
    # Search Algorithm (IDDFS + Negamax)
    # -------------------------------------------------------------------------
    
    my_board, opp_board, heights = parse_board(board)
    
    # Identify valid moves (columns not full)
    valid_moves = [c for c in SEARCH_ORDER if heights[c] < ROWS]
    
    # Fallback if no moves possible (should not happen in valid game)
    if not valid_moves:
        return 0
    
    # 1. Immediate Win Check
    # Ensure we take a winning move instantly without search overhead
    for c in valid_moves:
        move_mask = 1 << (c * 7 + heights[c])
        if check_win(my_board | move_mask):
            return c

    # Search State
    best_move = valid_moves[0]
    nodes_visited = 0
    timeout_flag = False
    
    # Negamax with Alpha-Beta Pruning
    def negamax(my, opp, depth, alpha, beta):
        nonlocal nodes_visited, timeout_flag
        
        # Check time periodically
        nodes_visited += 1
        if nodes_visited & 1023 == 0:
            if time.time() - start_time > TIME_LIMIT:
                timeout_flag = True
        
        if timeout_flag:
            return 0
        
        # Base case
        if depth == 0:
            return evaluate(my, opp)
        
        # Generate candidate moves
        candidates = []
        for c in SEARCH_ORDER:
            if heights[c] < ROWS:
                candidates.append(c)
        
        if not candidates:
            return 0 # Draw
        
        max_val = -float('inf')
        
        for c in candidates:
            h = heights[c]
            move_mask = 1 << (c * 7 + h)
            new_my = my | move_mask
            
            if check_win(new_my):
                # Found a win. Score high, preferring shallower depth (faster win)
                # Max depth is around 42, so 100000 + depth ensures preference
                val = 100000 + depth
            else:
                # Recursion
                heights[c] += 1
                val = -negamax(opp, new_my, depth - 1, -beta, -alpha)
                heights[c] -= 1
            
            if timeout_flag:
                return 0
            
            if val > max_val:
                max_val = val
            alpha = max(alpha, max_val)
            if alpha >= beta:
                break
                
        return max_val

    # Iterative Deepening Loop
    # Start from depth 2 (depth 1 is trivial) and go deeper
    try:
        for depth in range(2, 43):
            if time.time() - start_time > TIME_LIMIT:
                break
            
            current_iter_best = -1
            current_iter_val = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            
            for c in valid_moves:
                h = heights[c]
                move_mask = 1 << (c * 7 + h)
                new_my = my_board | move_mask
                
                # Check immediate win again (redundant but safe for root consistency)
                if check_win(new_my):
                    val = 100000 + depth
                else:
                    heights[c] += 1
                    val = -negamax(opp_board, new_my, depth - 1, -beta, -alpha)
                    heights[c] -= 1
                
                if timeout_flag:
                    break
                
                if val > current_iter_val:
                    current_iter_val = val
                    current_iter_best = c
                
                alpha = max(alpha, val)
            
            if not timeout_flag:
                best_move = current_iter_best
                # If we found a proven win, no need to search deeper
                if current_iter_val > 90000:
                    break
    except Exception:
        pass # Return last best move on error

    return best_move
