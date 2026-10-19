
import time

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 targeting policy.
    Uses Iterative Deepening Negamax with Alpha-Beta pruning and Bitboards.
    """

    # --- Constants & Config ---
    ROWS = 6
    COLS = 7
    # Time limit: leave a small buffer (50ms)
    TIME_LIMIT = 0.95 
    
    # Column Weights for Heuristic Evaluation (Favor center)
    COL_WEIGHTS = [0, 2, 4, 6, 4, 2, 0]

    # Bitmasks for columns (row 0..5 in each column stride of 7)
    # Stride is 7 to allow a buffer bit between columns preventing wrap-around diagonals
    COL_MASKS = [(0b111111 << (c * 7)) for c in range(COLS)]

    # --- Bitboard Helpers ---
    
    def count_set_bits(n: int) -> int:
        return bin(n).count('1')

    def connected_four(pos: int) -> bool:
        """
        Check if 'pos' contains 4 connected bits.
        Directions: Horizontal, Vertical, Diagonal /, Diagonal \
        """
        # Horizontal (step 7)
        m = pos & (pos >> 7)
        if m & (m >> 14): return True
        
        # Diagonal \ (step 6)
        m = pos & (pos >> 6)
        if m & (m >> 12): return True
        
        # Diagonal / (step 8)
        m = pos & (pos >> 8)
        if m & (m >> 16): return True
        
        # Vertical (step 1)
        m = pos & (pos >> 1)
        if m & (m >> 2): return True

        return False

    def evaluate(pos: int, mask: int) -> int:
        """
        Static evaluation of the board state from perspective of 'pos'.
        """
        opp = pos ^ mask
        score = 0
        
        for c in range(COLS):
            # Extract column bits (bits 0-5 shifted to LSB)
            # (pos >> shift) & 63
            shift = c * 7
            my_col = (pos >> shift) & 0x3F
            opp_col = (opp >> shift) & 0x3F
            
            w = COL_WEIGHTS[c]
            if w > 0:
                # Material difference weighted by column importance
                score += (count_set_bits(my_col) - count_set_bits(opp_col)) * w
        
        return score

    # --- Search ---
    
    tt = {} # Transposition Table: {(pos, mask): (depth, flag, score)}
            # flag: 0=Exact, 1=LowerBound (alpha), 2=UpperBound (beta)
    
    nodes = 0
    start_time = time.time()

    def negamax(pos, mask, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        
        # 1. Transposition Table Lookup
        entry = tt.get((pos, mask))
        if entry and entry[0] >= depth:
            flag, val = entry[1], entry[2]
            if flag == 0: return val # Exact
            if flag == 1: alpha = max(alpha, val) # Lower Bound
            elif flag == 2: beta = min(beta, val) # Upper Bound
            if alpha >= beta: return val

        # 2. Check for Draw (Full Board)
        if count_set_bits(mask) == 42:
            return 0
        
        # 3. Base Case: Max Depth Reached
        if depth == 0:
            return evaluate(pos, mask)

        # 4. Generate Moves (Center columns first)
        # Order: 3 (Center), 2, 4, 1, 5, 0, 6
        valid_moves = []
        for c in [3, 2, 4, 1, 5, 0, 6]:
            # Check if column is not full (bit 5 of the column is not set in mask)
            # Column index c*7. Top row is c*7 + 5.
            if not (mask & (1 << (c * 7 + 5))):
                # Calculate move bit:
                # Isolate column bits from mask, add 1 (shifted to column start)
                # In binary, adding 1 to a stack of 1s flips them to 0 and sets the next bit to 1.
                move_bit = (mask & COL_MASKS[c]) + (1 << (c * 7))
                
                # Check Immediate Win (Optimization)
                if connected_four(pos | move_bit):
                    res = 10000 + depth # Prefer winning sooner
                    tt[(pos, mask)] = (depth, 0, res)
                    return res
                
                valid_moves.append(move_bit)
        
        if not valid_moves:
            return 0 # Should be caught by full board check

        # 5. Iterative Search
        best_val = -float('inf')
        flag = 2 # Default to UpperBound

        for move_bit in valid_moves:
            # Make move: Update mask, switch current player (pos)
            # New current player is opponent: (pos ^ mask)
            new_pos = pos ^ mask
            new_mask = mask | move_bit
            
            # Recurse with negated alpha/beta
            v = -negamax(new_pos, new_mask, depth - 1, -beta, -alpha)
            
            if v > best_val:
                best_val = v
            
            alpha = max(alpha, v)
            if alpha >= beta:
                flag = 1 # LowerBound (Cutoff)
                break
        
        tt[(pos, mask)] = (depth, flag, best_val)
        return best_val

    # --- Parse Input ---
    
    my_position = 0
    full_mask = 0
    
    # Input rows: 0 (top) -> 5 (bottom)
    # Bitboard rows: 0 (bottom) -> 5 (top)
    for r in range(ROWS):
        for c in range(COLS):
            val = board[r][c]
            if val != 0:
                idx = c * 7 + (5 - r)
                full_mask |= (1 << idx)
                if val == 1:
                    my_position |= (1 << idx)
    
    # --- Controller ---
    
    # Valid columns (using indices)
    valid_cols = [c for c in [3, 2, 4, 1, 5, 0, 6] if not (full_mask & (1 << (c * 7 + 5)))]
    if not valid_cols:
        return 0
        
    # Step 1: Check for Winning Move Immediately
    for c in valid_cols:
        move_bit = (full_mask & COL_MASKS[c]) + (1 << (c * 7))
        if connected_four(my_position | move_bit):
            return c
            
    # Step 2: Check for Forced Blocks (prevent opponent win)
    opp_position = my_position ^ full_mask
    block_col = -1
    for c in valid_cols:
        move_bit = (full_mask & COL_MASKS[c]) + (1 << (c * 7))
        if connected_four(opp_position | move_bit):
            block_col = c
            break # If multiple threats exist, strategy is likely lost anyway, pick first
            
    if block_col != -1:
        return block_col

    # Step 3: Iterative Deepening Search
    best_move = valid_cols[0]
    
    try:
        # Depth 1 to 42 (max moves)
        for depth in range(1, 43):
            # Time Check at depth start
            if time.time() - start_time > TIME_LIMIT: break
            
            alpha = -float('inf')
            beta = float('inf')
            max_val = -float('inf')
            current_best = best_move
            
            # Sort columns: try best_move from previous iteration first
            cols_to_search = [best_move] + [c for c in valid_cols if c != best_move]
            
            for c in cols_to_search:
                if time.time() - start_time > TIME_LIMIT: raise TimeoutError
                
                move_bit = (full_mask & COL_MASKS[c]) + (1 << (c * 7))
                # Next state: Opponent's turn
                new_pos = my_position ^ full_mask
                new_mask = full_mask | move_bit
                
                # Call Negamax (depth - 1 because we manually stepped once)
                val = -negamax(new_pos, new_mask, depth - 1, -beta, -alpha)
                
                if val > max_val:
                    max_val = val
                    current_best = c
                
                alpha = max(alpha, val)
            
            best_move = current_best
            
            # If we found a winning line, we can stop early
            if max_val > 9000:
                break
                
    except TimeoutError:
        pass # Return the best move found so far
        
    return best_move
