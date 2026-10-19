
import time
import random

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI targeting policy using Iterative Deepening Negamax 
    with Alpha-Beta Pruning and Bitboard representation.
    """
    WIDTH = 7
    HEIGHT = 6
    TIME_LIMIT = 0.98
    MAX_SCORE = 1000000
    
    start_time = time.time()
    
    # -------------------------------------------------------------------------
    # 1. Parse Input Board to Bitboards
    # -------------------------------------------------------------------------
    # Layout: 7 columns. Each column uses 7 bits (6 rows + 1 sentinel at top).
    # Bit index = row_from_bottom + col_index * 7
    # Board Input: row 0 is top, row 5 is bottom.
    
    my_board = 0
    opp_board = 0
    heights = [0] * WIDTH
    
    for c in range(WIDTH):
        h = 0
        # Iterate from bottom (row 5) up to top (row 0)
        for r in range(HEIGHT - 1, -1, -1):
            val = board[r][c]
            if val == 0:
                break
            
            # Map to bitboard index
            idx = h + c * 7
            if val == 1:
                my_board |= (1 << idx)
            elif val == -1:
                opp_board |= (1 << idx)
            h += 1
        heights[c] = h

    # -------------------------------------------------------------------------
    # 2. Heuristics & Helpers
    # -------------------------------------------------------------------------
    # Center columns are strategically better
    col_order = [3, 2, 4, 1, 5, 0, 6]
    
    # Compatibility for bit counting
    if hasattr(int, "bit_count"):
        def count_set_bits(n): return n.bit_count()
    else:
        def count_set_bits(n): return bin(n).count("1")

    def check_win(pos):
        """Returns True if 'pos' bitboard has 4 connected bits."""
        # Vertical
        m = pos & (pos >> 1)
        if m & (m >> 2): return True
        # Horizontal
        m = pos & (pos >> 7)
        if m & (m >> 14): return True
        # Diagonal /
        m = pos & (pos >> 8)
        if m & (m >> 16): return True
        # Diagonal \
        m = pos & (pos >> 6)
        if m & (m >> 12): return True
        return False

    def evaluate(my, opp):
        """Static board evaluation based on piece centrality."""
        score = 0
        
        # Column 3 (Center)
        m = 0x3F << 21
        score += (count_set_bits(my & m) - count_set_bits(opp & m)) * 6
        
        # Columns 2 and 4
        m = (0x3F << 14) | (0x3F << 28)
        score += (count_set_bits(my & m) - count_set_bits(opp & m)) * 3
        
        # Columns 1 and 5
        m = (0x3F << 7) | (0x3F << 35)
        score += (count_set_bits(my & m) - count_set_bits(opp & m)) * 1
        
        return score

    # -------------------------------------------------------------------------
    # 3. Negamax Solver with Alpha-Beta Pruning
    # -------------------------------------------------------------------------
    nodes_visited = 0

    def solve(my, opp, depth, alpha, beta, h_list):
        nonlocal nodes_visited
        nodes_visited += 1
        
        # Check time periodically
        if (nodes_visited & 1023) == 0:
            if time.time() - start_time > TIME_LIMIT:
                return None
        
        # Base case
        if depth == 0:
            return evaluate(my, opp)
            
        # --- Move Generation with "Win/Block" Pruning ---
        
        # 1. Check for immediate win
        for c in col_order:
            if h_list[c] < HEIGHT:
                idx = h_list[c] + c * 7
                if check_win(my | (1 << idx)):
                    return MAX_SCORE + depth # Prefer faster win
        
        # 2. Check for forced block (if opponent wins next, we MUST block)
        blocking_col = -1
        block_mask = 0
        for c in col_order:
            if h_list[c] < HEIGHT:
                idx = h_list[c] + c * 7
                if check_win(opp | (1 << idx)):
                    blocking_col = c
                    block_mask = (1 << idx)
                    break
        
        possible_moves = []
        if blocking_col != -1:
            # Prune all other moves; we must block
            possible_moves = [(blocking_col, block_mask)]
        else:
            # Generate all valid moves
            for c in col_order:
                if h_list[c] < HEIGHT:
                    idx = h_list[c] + c * 7
                    possible_moves.append((c, 1 << idx))
        
        if not possible_moves:
            return 0 # Draw
            
        best = -float('inf')
        
        for col, mask in possible_moves:
            # Make move
            h_list[col] += 1
            new_my = my | mask
            
            # Recurse (swap roles: opp becomes my, new_my becomes opp)
            val = solve(opp, new_my, depth - 1, -beta, -alpha, h_list)
            
            # Undo move
            h_list[col] -= 1
            
            if val is None: return None # Propagate timeout
            
            val = -val
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break # Prune
                
        return best

    # -------------------------------------------------------------------------
    # 4. Main Search Loop (Iterative Deepening)
    # -------------------------------------------------------------------------
    valid_initial_moves = [c for c in col_order if heights[c] < HEIGHT]
    
    # If board full or no moves (should not happen based on rules)
    if not valid_initial_moves:
        return 0
    
    # 4a. Quick check for winning moves to return immediately
    for c in valid_initial_moves:
        idx = heights[c] + c * 7
        if check_win(my_board | (1 << idx)):
            return c
            
    # 4b. Initialize best_move. 
    # If a block is visible immediately, prefer it as baseline in case of timeout.
    best_move = valid_initial_moves[0]
    for c in valid_initial_moves:
         idx = heights[c] + c * 7
         if check_win(opp_board | (1 << idx)):
             best_move = c
             break

    # 4c. IDDFS
    # We unroll the first level of recursion to handle the return move index
    for d in range(1, 43):
        alpha = -float('inf')
        beta = float('inf')
        best_val_depth = -float('inf')
        best_move_depth = best_move # Keep previous best if this depth fails
        
        # Optimization: if forced block found at this depth, logic inside loop will find it.
        # However, we must iterate moves.
        
        moves_to_search = valid_initial_moves
        
        for c in moves_to_search:
            idx = heights[c] + c * 7
            mask = 1 << idx
            
            # Make move
            heights[c] += 1
            # Search children with depth d-1
            val = solve(opp_board, my_board | mask, d - 1, -beta, -alpha, heights)
            heights[c] -= 1
            
            if val is None:
                # Timeout: return the best move found in the previous fully completed depth
                return best_move
            
            val = -val
            
            if val > best_val_depth:
                best_val_depth = val
                best_move_depth = c
            
            if val > alpha:
                alpha = val
                
        best_move = best_move_depth
        
        # If we found a winning sequence, minimal calculation needed
        if best_val_depth > 90000:
            break
            
        if time.time() - start_time > TIME_LIMIT:
            break
            
    return best_move
