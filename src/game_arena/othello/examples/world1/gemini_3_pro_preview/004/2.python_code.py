
import numpy as np
import time

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello policy using Alpha-Beta pruning with Bitboards and Iterative Deepening.
    """
    
    # =========================================================================
    # Constants & Config
    # =========================================================================
    TIME_LIMIT = 0.95  # Seconds to search
    MAX_DEPTH = 64     # Ideally we stop by time, but this is a hard cap
    MIN_DEPTH = 1      # Ensure we do at least a shallow search
    
    # 8x8 Board Weights (Flattened)
    # Rewards corners, penalizes X-squares/C-squares near corners
    STATIC_WEIGHTS = np.array([
        100, -20,  10,   5,   5,  10, -20, 100,
        -20, -50,  -2,  -2,  -2,  -2, -50, -20,
         10,  -2,  -1,  -1,  -1,  -1,  -2,  10,
          5,  -2,  -1,  -1,  -1,  -1,  -2,   5,
          5,  -2,  -1,  -1,  -1,  -1,  -2,   5,
         10,  -2,  -1,  -1,  -1,  -1,  -2,  10,
        -20, -50,  -2,  -2,  -2,  -2, -50, -20,
        100, -20,  10,   5,   5,  10, -20, 100
    ], dtype=np.int32)
    
    # Corner indices and their neighbors (C-squares, X-squares)
    # Format: (Corner parameters), Neighbors: List of indices
    CORNERS = {
        0:  [1, 8, 9],       # Top-Left
        7:  [6, 15, 14],     # Top-Right
        56: [57, 48, 49],    # Bottom-Left
        63: [62, 55, 54]     # Bottom-Right
    }

    # Bitboard Masks
    MASK_FULL = 0xFFFFFFFFFFFFFFFF
    MASK_NOT_A = 0xFEFEFEFEFEFEFEFE # Mask out Col A (Left edge)
    MASK_NOT_H = 0x7F7F7F7F7F7F7F7F # Mask out Col H (Right edge)

    # Shift offsets for 8 directions
    # (Shift Amount, Mask to apply to source before shift)
    # N, S, E, W, NE, NW, SE, SW
    SHIFTS = [
        (8, None), (-8, None), 
        (1, MASK_NOT_H), (-1, MASK_NOT_A),
        (9, MASK_NOT_H), (-9, MASK_NOT_A),    # SE (+9), NW (-9)
        (-7, MASK_NOT_H), (7, MASK_NOT_A)     # NE (-7), SW (+7) 
    ]
    # Note: Positive shift is Left shift (<<), effectively increasing index.
    # Index 0 is a1 (top-left). Index 63 is h8.
    # Down is +8 (<<8). Right is +1 (<<1).
    # Be careful: Python << operates on value, increasing bit significance.
    # To move index 0 (bit 0) to index 8 (bit 8), we do 1 << 8. 
    # So "Down" is << 8. "Up" is >> 8.
    
    # Direction logic mapping for generator loop:
    # (shift_func, mask)
    # We define python lambdas for shifts to handle left/right directionality
    shift_ops = [
        (lambda x: x >> 8, MASK_FULL),            # North (-8)
        (lambda x: x << 8, MASK_FULL),            # South (+8)
        (lambda x: x << 1, MASK_NOT_H),           # East (+1)
        (lambda x: x >> 1, MASK_NOT_A),           # West (-1)
        (lambda x: x >> 7, MASK_NOT_H),           # NE (-7) -> actually +1 col, -1 row. +1-8 = -7. >>7.
        (lambda x: x >> 9, MASK_NOT_A),           # NW (-9) -> -1 col, -1 row. >>9.
        (lambda x: x << 9, MASK_NOT_H),           # SE (+9) -> +1 col, +1 row. <<9.
        (lambda x: x << 7, MASK_NOT_A)            # SW (+7) -> -1 col, +1 row. <<7.
    ]

    # =========================================================================
    # Helper Functions
    # =========================================================================

    def to_bitboard(arr):
        """Convert 8x8 numpy array to 64-bit integer."""
        # arr.flatten() is row-major: [r0c0, r0c1, ..., r7c7]
        # We map r0c0 to bit 0.
        flat = arr.flatten()
        # Create powers of 2 array
        powers = 1 << np.arange(64, dtype=object) # Use object for arbitrary prec if needed, though 64 fits
        return int(np.dot(flat, powers))

    def get_legal_moves(my_board, opp_board):
        """
        Generate legal moves mask using bitwise ops.
        Returns a single 64-bit integer where 1s are legal moves.
        """
        empty = ~(my_board | opp_board) & MASK_FULL
        legal = 0
        
        for shift_func, mask in shift_ops:
            # We want to find a string of opp discs bracketed by my disc.
            # Start: neighboring opp discs
            candidates = shift_func(my_board & mask) & opp_board
            
            # Propagate along the line while we see opp discs
            for _ in range(6):
                candidates |= shift_func(candidates & mask) & opp_board
            
            # The potential move is the empty square immediately following the line
            moves = shift_func(candidates & mask) & empty
            legal |= moves
            
        return legal

    def apply_move(my_board, opp_board, move_bit):
        """
        Apply a move and flip discs.
        Returns (new_my_board, new_opp_board).
        """
        if move_bit is None: # Pass
            return my_board, opp_board

        captured = 0
        for shift_func_fwd, mask_fwd in shift_ops:
            # Move_bit is the placement. Look 'backwards' to find bracket?
            # Actually easier to cast rays from the move_bit in all directions.
            
            # Determine reverse shift logic
            # If fwd is << k, rev is >> k.
            # We can re-use the shift_ops pairs if we identify pairs, 
            # or just run the propagation check.
            
            # Let's just probe outward from move_bit using the standard shifts
            mask = mask_fwd
            
            # Probing 'direction'
            line = 0
            current = shift_func_fwd(move_bit & mask)
            while current & opp_board:
                line |= current
                current = shift_func_fwd(current & mask)
            
            # Check if capped by my_board
            if current & my_board:
                captured |= line
                
        return (my_board | move_bit | captured), (opp_board & ~captured)

    def count_bits(n):
        return bin(n).count('1')

    def evaluate(my_board, opp_board, legal_moves_mask=None):
        """
        Heuristic evaluation.
        Positive value -> Good for 'my_board'.
        """
        # 1. Mobility
        if legal_moves_mask is None:
            legal_moves_mask = get_legal_moves(my_board, opp_board)
        my_mobility = count_bits(legal_moves_mask)
        opp_mobility = count_bits(get_legal_moves(opp_board, my_board))
        
        # Mobility score
        score = 10 * (my_mobility - opp_mobility)
        
        # 2. Disc Count (Only if game is ending, otherwise keep it light)
        # In early game, minimize discs (evaporation) is often good, but risky to code simply.
        # We stick to positional.
        
        # 3. Static Weights
        # Extract bits positions
        # This is the slow part in python, minimize iteration.
        # Approximation: Just check corners and raw count diff if needed.
        # A fully vectorized weight calc is too slow converting back to array.
        # Iterate set bits?
        
        # Optimized weight calculation:
        # We can't easily dot product a bitboard.
        # Iterate only non-zero parts?
        # For Python speed, let's focus on Corners and Key Squares manually,
        # and ignore the full 64-square sum if it's too slow.
        # But 64 iterations is fine.
        
        my_pos_score = 0
        opp_pos_score = 0
        
        # To optimize, we loop 0..63
        # But bit manipulation is faster: `while board: bit = board & -board; ...`
        
        # Simplified Eval for Speed:
        # Corners (High value)
        corners_my = my_board & 0x8100000000000081
        corners_opp = opp_board & 0x8100000000000081
        score += 80 * (count_bits(corners_my) - count_bits(corners_opp))
        
        # Penalize adjacent to empty corners
        # (This logic is crudely handled by static weights, but fast manual check is better)
        # Empty corners
        corners_all = 0x8100000000000081
        empty_corners = corners_all & ~(my_board | opp_board)
        
        if empty_corners:
            # Check bad spots
            if empty_corners & 1: # Top Left A1 empty
                if my_board & 0x0002020000000000: score -= 30 # C-squares: B1(2), A2(256), X: B2(512) -> wait bits
                # A1=0 (1<<0). B1=1 (1<<1). A2=8 (1<<8). B2=9 (1<<9).
                if my_board & ((1<<1)|(1<<8)|(1<<9)): score -= 20
                if opp_board & ((1<<1)|(1<<8)|(1<<9)): score += 20
            
            if empty_corners & (1<<7): # Top Right H1
                # H1=7. G1=6. H2=15. G2=14.
                mask = (1<<6)|(1<<15)|(1<<14)
                if my_board & mask: score -= 20
                if opp_board & mask: score += 20
                
            if empty_corners & (1<<56): # Bot Left A8
                # A8=56. B8=57. A7=48. B7=49.
                mask = (1<<57)|(1<<48)|(1<<49)
                if my_board & mask: score -= 20
                if opp_board & mask: score += 20
                
            if empty_corners & (1<<63): # Bot Right H8
                # H8=63. G8=62. H7=55. G7=54.
                mask = (1<<62)|(1<<55)|(1<<54)
                if my_board & mask: score -= 20
                if opp_board & mask: score += 20

        return score

    # =========================================================================
    # Search Algorithm
    # =========================================================================

    start_time = time.time()
    
    def negamax(my_bd, opp_bd, depth, alpha, beta, passed=False):
        # Time check
        if (time.time() - start_time) > TIME_LIMIT:
            raise TimeoutError
            
        # Leaf node
        if depth == 0:
            return evaluate(my_bd, opp_bd)
        
        legal = get_legal_moves(my_bd, opp_bd)
        
        # No moves
        if legal == 0:
            if passed: # Game over
                my_c = count_bits(my_bd)
                opp_c = count_bits(opp_bd)
                return 10000 * (my_c - opp_c) # Decisive score
            # Pass turn
            return -negamax(opp_bd, my_bd, depth, -beta, -alpha, passed=True)
        
        # Extract individual moves
        moves = []
        b = legal
        while b:
            lsb = b & -b # Isolate lowest bit
            moves.append(lsb)
            b ^= lsb
            
        # Move Ordering: Prioritize corners
        # Corner bits: 1, 128, 2^56, 2^63
        corners_mask = 0x8100000000000081
        moves.sort(key=lambda m: 1 if (m & corners_mask) else 0, reverse=True)

        best_score = -float('inf')
        
        for m in moves:
            new_my, new_opp = apply_move(my_bd, opp_bd, m)
            # Recursive call: swap players (negative score)
            try:
                score = -negamax(new_opp, new_my, depth - 1, -beta, -alpha, False)
            except TimeoutError:
                raise
            
            if score > best_score:
                best_score = score
            alpha = max(alpha, score)
            if alpha >= beta:
                break
                
        return best_score

    # =========================================================================
    # Main Execution
    # =========================================================================

    # 1. Parse Input
    my_bitboard = to_bitboard(you)
    opp_bitboard = to_bitboard(opponent)
    
    # 2. Initial Moves
    legal_mask = get_legal_moves(my_bitboard, opp_bitboard)
    if legal_mask == 0:
        return "pass"
        
    # Get move list
    legal_moves = []
    temp_mask = legal_mask
    while temp_mask:
        lsb = temp_mask & -temp_mask
        legal_moves.append(lsb)
        temp_mask ^= lsb
        
    # If forced move, take it (save time)
    if len(legal_moves) == 1:
        best_move_bit = legal_moves[0]
    else:
        # 3. Iterative Deepening
        best_move_bit = legal_moves[0] # Default
        
        try:
            for depth in range(MIN_DEPTH, MAX_DEPTH + 1):
                best_score_depth = -float('inf')
                best_move_depth = None
                
                # Sort moves for root based on previous heuristics or simple corner prioritization
                corners_mask = 0x8100000000000081
                legal_moves.sort(key=lambda m: 1 if (m & corners_mask) else 0, reverse=True)

                alpha = -float('inf')
                beta = float('inf')
                
                for m in legal_moves:
                    new_my, new_opp = apply_move(my_bitboard, opp_bitboard, m)
                    score = -negamax(new_opp, new_my, depth - 1, -beta, -alpha)
                    
                    if score > best_score_depth:
                        best_score_depth = score
                        best_move_depth = m
                    
                    alpha = max(alpha, score)
                
                # Update global best if completed depth
                best_move_bit = best_move_depth
                
                # Check soft time exit to avoid starting a depth we can't finish
                if (time.time() - start_time) > (TIME_LIMIT * 0.6):
                    break
                    
        except TimeoutError:
            pass # Return the best move found in previous completed depths

    # 4. Convert to String
    # Find bit index
    idx = 0
    while not (best_move_bit & (1 << idx)):
        idx += 1
        
    r, c = divmod(idx, 8)
    # Map c=0 -> 'a', c=7 -> 'h'
    # Map r=0 -> '1', r=7 -> '8'
    return f"{chr(ord('a') + c)}{r + 1}"
