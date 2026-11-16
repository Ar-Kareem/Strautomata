
import time
import random

def policy(you: list, opponent: list) -> str:
    """
    Returns the best move for a Clobber game on a 5x6 grid using 
    Iterative Deepening Negamax with Alpha-Beta pruning and Bitboards.
    """
    
    # --- Constants & Precomputed Masks ---
    ROWS = 5
    COLS = 6
    SIZE = 30
    TIME_LIMIT = 0.95  # Seconds
    WIN_SCORE = 1_000_000

    # Bitmasks to prevent board wrapping logic errors
    # Indices are r * 6 + c
    MASK_ALL = (1 << SIZE) - 1
    MASK_COL_RIGHT = 0 # Valid source cols for Right move (cols 0-4)
    MASK_COL_LEFT = 0  # Valid source cols for Left move (cols 1-5)
    MASK_ROW_BOT = 0   # Valid source rows for Down move (rows 0-3)
    MASK_ROW_TOP = 0   # Valid source rows for Up move (rows 1-4)

    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            if c < COLS - 1: MASK_COL_RIGHT |= (1 << idx)
            if c > 0:        MASK_COL_LEFT  |= (1 << idx)
            if r < ROWS - 1: MASK_ROW_BOT   |= (1 << idx)
            if r > 0:        MASK_ROW_TOP   |= (1 << idx)

    # Move Definitions: (shift amount, direction char, validation source mask)
    # Right (+1), Left (-1), Down (+6), Up (-6)
    MOVES_DATA = [
        (1, 'R', MASK_COL_RIGHT),
        (-1, 'L', MASK_COL_LEFT),
        (6, 'D', MASK_ROW_BOT),
        (-6, 'U', MASK_ROW_TOP)
    ]

    # --- Helper Functions ---

    def count_set_bits(n):
        """Cross-version bit counting."""
        try:
            return n.bit_count()
        except AttributeError:
            return bin(n).count('1')

    def get_legal_moves(me, opp):
        """Generates list of (src_idx, dst_idx, direction_char)."""
        moves = []
        for shift, d_char, src_mask in MOVES_DATA:
            # We want 'me' pieces that have an 'opp' piece at the destination.
            # If moving Right (+1), destination is src+1.
            # We check: (me at src) AND (opp at src+shift).
            
            if shift > 0:
                # Align opp to me (shift opp right)
                candidates = me & (opp >> shift) & src_mask
            else:
                # Align opp to me (shift opp left by abs(shift))
                candidates = me & (opp << -shift) & src_mask
            
            while candidates:
                # Extract lowest set bit
                lowest = candidates & -candidates
                src_idx = count_set_bits(lowest - 1) # get index of bit
                moves.append((src_idx, src_idx + shift, d_char))
                candidates ^= lowest
        return moves

    def get_mobility_diff(me, opp):
        """Heuristic: My Move Count - Opp Move Count."""
        my_count = 0
        opp_count = 0
        
        # My moves
        for shift, _, src_mask in MOVES_DATA:
            if shift > 0: c = me & (opp >> shift) & src_mask
            else:         c = me & (opp << -shift) & src_mask
            if c: my_count += count_set_bits(c)
            
        # Opp moves (opp attacks me)
        for shift, _, src_mask in MOVES_DATA:
            if shift > 0: c = opp & (me >> shift) & src_mask
            else:         c = opp & (me << -shift) & src_mask
            if c: opp_count += count_set_bits(c)
            
        return my_count - opp_count

    # --- Search Engine ---

    class TimeoutError(Exception):
        pass

    transposition_table = {}

    def negamax(me, opp, depth, alpha, beta, start_time):
        if (time.time() - start_time) > TIME_LIMIT:
            raise TimeoutError

        state_key = (me, opp)
        
        # TT Lookup
        if state_key in transposition_table:
            entry = transposition_table[state_key]
            if entry['depth'] >= depth:
                if entry['flag'] == 0: # Exact
                    return entry['score']
                elif entry['flag'] == 1: # Lowerbound (cutoff low)
                    alpha = max(alpha, entry['score'])
                elif entry['flag'] == 2: # Upperbound (cutoff high)
                    beta = min(beta, entry['score'])
                
                if alpha >= beta:
                    return entry['score']

        moves = get_legal_moves(me, opp)

        # Terminal Node Check
        if not moves:
            # I have no moves -> I lose. 
            # Prefer losing later (lower depth remaining) -> larger negative score
            # Score formula: -(WIN_SCORE + depth)
            return -(WIN_SCORE + depth)

        # Depth Limit Check
        if depth == 0:
            return get_mobility_diff(me, opp)

        best_val = -float('inf')
        tt_flag = 2 # Default Upper bound
        
        # Move Ordering: Not strictly implemented, relying on random shuffle at root not here.
        
        for src, dst, _ in moves:
            # Apply move: Remove src from me, ADD dst to me, Remove dst from opp
            new_me = (me ^ (1 << src)) | (1 << dst)
            new_opp = (opp ^ (1 << dst))
            
            val = -negamax(new_opp, new_me, depth - 1, -beta, -alpha, start_time)
            
            if val > best_val:
                best_val = val
            
            alpha = max(alpha, best_val)
            if alpha >= beta:
                tt_flag = 1 # Lower bound
                break
        
        # Store in TT
        # If best_val fell between alpha/beta originally, it's exact.
        # But here we use standard simplification.
        if best_val > alpha and best_val < beta:
            tt_flag = 0 # Exact
            
        transposition_table[state_key] = {
            'depth': depth,
            'score': best_val,
            'flag': tt_flag
        }
        
        return best_val

    # --- Main Logic ---
    
    start_t = time.time()
    
    # 1. Input Parsing
    me_mask = 0
    opp_mask = 0
    
    # Flatten input if necessary
    flat_you = []
    flat_opp = []
    
    # Robustly handle different input types (1D list, 2D list, numpy)
    if hasattr(you, 'flatten'): 
        # Numpy array
        flat_you = you.flatten().tolist()
        flat_opp = opponent.flatten().tolist()
    elif isinstance(you[0], (list, tuple)):
        # List of lists
        flat_you = [c for r in you for c in r]
        flat_opp = [c for r in opponent for c in r]
    else:
        # Flat list
        flat_you = you
        flat_opp = opponent
        
    for i in range(SIZE):
        if flat_you[i]: me_mask |= (1 << i)
        if flat_opp[i]: opp_mask |= (1 << i)

    # 2. Get Legal Moves
    possible_moves = get_legal_moves(me_mask, opp_mask)
    
    if not possible_moves:
        return "0,0,R" # Should not happen unless game is already over
        
    # Default fallback move
    s, _, d = random.choice(possible_moves)
    best_move_str = f"{s//COLS},{s%COLS},{d}"

    # 3. Iterative Deepening Search
    # Randomize order to provide variety if values are equal
    random.shuffle(possible_moves)
    
    try:
        # Depth 1 to Max
        for depth in range(1, 50): 
            alpha = -float('inf')
            beta = float('inf')
            best_val = -float('inf')
            current_depth_best_move_str = None
            
            for src, dst, d_char in possible_moves:
                new_me = (me_mask ^ (1 << src)) | (1 << dst)
                new_opp = (opp_mask ^ (1 << dst))
                
                val = -negamax(new_opp, new_me, depth - 1, -beta, -alpha, start_t)
                
                if val > best_val:
                    best_val = val
                    current_depth_best_move_str = f"{src//COLS},{src%COLS},{d_char}"
                
                alpha = max(alpha, best_val)
            
            if current_depth_best_move_str:
                best_move_str = current_depth_best_move_str
            
            # If we found a guaranteed forced win, we don't strictly need to search deeper
            if best_val > WIN_SCORE / 2:
                break
                
    except TimeoutError:
        pass # Return best move found so far

    return best_move_str
