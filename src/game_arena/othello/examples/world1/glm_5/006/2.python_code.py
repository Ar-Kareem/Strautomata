
import numpy as np
import time

# Constants for bitboard manipulation
MASK_A = 0xfefefefefefefefe  # Clears file 'a' (column 0)
MASK_H = 0x7f7f7f7f7f7f7f7f  # Clears file 'h' (column 7)

# High value for corners
CORNER_VAL = 500
# Penalty for X-squares (diagonal to corners) and C-squares (adjacent to corners)
# if the corner is empty.
X_VAL = -200
C_VAL = -50

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Main policy function to determine the next move.
    """
    start_time = time.time()
    time_limit = 0.95  # seconds

    # Convert numpy arrays to 64-bit integers (bitboards)
    my_b = arr_to_bits(you)
    opp_b = arr_to_bits(opponent)

    # Get all legal moves for the current player
    moves_b = get_moves(my_b, opp_b)
    
    if moves_b == 0:
        return "pass"

    # Extract move coordinates from the bitboard
    moves_list = list(bits_to_coords(moves_b))

    # If only one legal move, return it immediately
    if len(moves_list) == 1:
        return coord_to_str(moves_list[0])

    # Default to the first move found as a fallback
    best_move_coord = moves_list[0]
    
    # Iterative Deepening Search
    # We search to increasing depths until time runs out
    for depth in range(2, 64):
        current_time = time.time()
        if current_time - start_time > time_limit * 0.5: # Heuristic time check
            break

        # Order moves to improve alpha-beta pruning
        # Prioritize corners, then others
        moves_list.sort(key=lambda c: move_priority(c), reverse=True)
        
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        current_best_move = None
        
        for r, c in moves_list:
            # Check time within the loop
            if time.time() - start_time > time_limit:
                break
                
            move_bit = 1 << (r * 8 + c)
            
            # Apply the move to get the new state
            new_my, new_opp = apply_move(my_b, opp_b, move_bit)
            
            # Negamax recursive call
            # Note: roles are swapped for the next player
            score = -negamax(new_opp, new_my, depth - 1, -beta, -alpha, start_time, time_limit)
            
            if score > best_score:
                best_score = score
                current_best_move = (r, c)
            
            # Alpha update
            if score > alpha:
                alpha = score
                
            # Alpha-beta cutoff
            if alpha >= beta:
                break
        
        # Update the best move only if we completed the search for this depth
        # or at least found a valid move.
        if current_best_move:
            best_move_coord = current_best_move
            
        # If we found a winning line, stop searching
        if best_score >= 10000:
            break

    return coord_to_str(best_move_coord)

def negamax(my_b, opp_b, depth, alpha, beta, start_time, time_limit):
    """
    Negamax search with alpha-beta pruning.
    """
    # Time check
    if time.time() - start_time > time_limit:
        return 0 # Return neutral score on timeout to unwind

    # Move generation
    moves_b = get_moves(my_b, opp_b)
    
    if moves_b == 0:
        # If no moves, check if opponent can move
        opp_moves = get_moves(opp_b, my_b)
        if opp_moves == 0:
            # Game over: evaluate final disc difference
            return endgame_score(my_b, opp_b)
        else:
            # Pass: current player passes, opponent moves. Depth decrement is optional but safe.
            # We do not decrement depth here to avoid infinite loops if depth is high, 
            # but standard is depth-1. With finite depth, it's fine.
            return -negamax(opp_b, my_b, depth, -beta, -alpha, start_time, time_limit)

    if depth == 0:
        return evaluate(my_b, opp_b)

    # Basic move ordering: iterate bits.
    # Optimization: we can't easily sort bits without converting to list,
    # which is slow. We rely on shallow depth for speed or simple loop.
    
    best_score = -float('inf')
    
    # Iterate through all set bits in moves_b
    m = moves_b
    while m:
        move_bit = m & -m # Isolate lowest bit
        m ^= move_bit     # Remove it
        
        new_my, new_opp = apply_move(my_b, opp_b, move_bit)
        score = -negamax(new_opp, new_my, depth - 1, -beta, -alpha, start_time, time_limit)
        
        if score > best_score:
            best_score = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break # Prune
            
    return best_score

def arr_to_bits(arr):
    """Converts an 8x8 numpy array to a 64-bit integer bitboard."""
    b = 0
    for r in range(8):
        for c in range(8):
            if arr[r][c]:
                b |= 1 << (r * 8 + c)
    return b

def bits_to_coords(bits):
    """Yields (row, col) tuples from a bitboard."""
    while bits:
        b = bits & -bits
        idx = (b.bit_length() - 1)
        r, c = divmod(idx, 8)
        yield r, c
        bits ^= b

def coord_to_str(coord):
    """Converts (row, col) to algebraic notation string."""
    r, c = coord
    return chr(ord('a') + c) + str(r + 1)

def shift(bits, dr, dc):
    """Shifts a bitboard by (dr, dc). Returns 0 if bits fall off the board."""
    if dc == 1: # East
        bits = (bits << 1) & MASK_A
    elif dc == -1: # West
        bits = (bits >> 1) & MASK_H
    
    if dr == 1: # South
        bits = bits << 8
    elif dr == -1: # North
        bits = bits >> 8
        
    return bits & 0xFFFFFFFFFFFFFFFF

def get_moves(my_b, opp_b):
    """Generates all legal moves for the player."""
    empty = ~(my_b | opp_b) & 0xFFFFFFFFFFFFFFFF
    moves = 0
    
    # Directions: N, S, E, W, NE, NW, SE, SW
    dirs = [(-1, 0), (1, 0), (0, 1), (0, -1), (-1, 1), (-1, -1), (1, 1), (1, -1)]
    
    for dr, dc in dirs:
        # Candidate opponent discs adjacent to my discs in this direction
        # Step 1: Move my discs one step
        candidates = shift(my_b, dr, dc)
        # Step 2: Keep only opponent discs at those positions
        candidates = candidates & opp_b
        
        # Propagate along the direction
        while candidates:
            # The next step from these candidates
            next_step = shift(candidates, dr, dc)
            # Valid moves are empty squares reached after passing through opponent discs
            moves |= empty & next_step
            # New candidates are opponent discs adjacent to the previous ones
            candidates = opp_b & next_step
            
    return moves

def apply_move(my_b, opp_b, move_bit):
    """Applies a move and returns (new_my_b, new_opp_b)."""
    # Identify all discs to flip
    flips = 0
    dirs = [(-1, 0), (1, 0), (0, 1), (0, -1), (-1, 1), (-1, -1), (1, 1), (1, -1)]
    
    for dr, dc in dirs:
        line_flips = 0
        # Move one step in direction
        curr = shift(move_bit, dr, dc)
        
        # Continue while we hit opponent discs
        while curr & opp_b:
            line_flips |= curr
            curr = shift(curr, dr, dc)
            
        # If we eventually hit our own disc, the line is valid
        if curr & my_b:
            flips |= line_flips
            
    # Apply flips
    new_my_b = my_b | move_bit | flips
    new_opp_b = opp_b ^ flips # Remove flipped discs from opponent
    
    return new_my_b, new_opp_b

def evaluate(my_b, opp_b):
    """
    Heuristic evaluation of the board state.
    Higher score is better for the current player (my_b).
    """
    score = 0
    
    # 1. Mobility
    my_moves = popcount(get_moves(my_b, opp_b))
    opp_moves = popcount(get_moves(opp_b, my_b))
    score += (my_moves - opp_moves) * 10
    
    # 2. Corners and X/C squares
    # Corners
    corners = [0, 7, 56, 63]
    for c in corners:
        mask = 1 << c
        if my_b & mask:
            score += CORNER_VAL
        elif opp_b & mask:
            score -= CORNER_VAL
        else:
            # If corner empty, penalize/give points for adjacent X/C squares
            # X-squares (diagonals)
            x_sqs = [9, 14, 49, 54]
            c_sqs = [1, 6, 8, 15, 48, 55, 57, 62]
            
            # Check X squares
            if c == 0: x_mask = 1 << 9
            elif c == 7: x_mask = 1 << 14
            elif c == 56: x_mask = 1 << 49
            else: x_mask = 1 << 54
            
            if my_b & x_mask: score += X_VAL
            elif opp_b & x_mask: score -= X_VAL
            
            # Check C squares (simplified: just checks specific adjacency)
            # This is a bit manual but fast
            if c == 0:
                c_masks = [(1<<1), (1<<8)]
                for m in c_masks:
                    if my_b & m: score += C_VAL
                    elif opp_b & m: score -= C_VAL
            elif c == 7:
                c_masks = [(1<<6), (1<<15)]
                for m in c_masks:
                    if my_b & m: score += C_VAL
                    elif opp_b & m: score -= C_VAL
            elif c == 56:
                c_masks = [(1<<48), (1<<57)]
                for m in c_masks:
                    if my_b & m: score += C_VAL
                    elif opp_b & m: score -= C_VAL
            elif c == 63:
                c_masks = [(1<<55), (1<<62)]
                for m in c_masks:
                    if my_b & m: score += C_VAL
                    elif opp_b & m: score -= C_VAL

    # 3. Frontier Discs (Discs adjacent to empty squares)
    # Fewer frontier discs is better (implies more stable/discs with options)
    empty = ~(my_b | opp_b) & 0xFFFFFFFFFFFFFFFF
    
    # Check all 8 neighbors for empty squares
    neighbors = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0: continue
            neighbors |= shift(empty, dr, dc)
            
    my_frontier = popcount(my_b & neighbors)
    opp_frontier = popcount(opp_b & neighbors)
    score -= (my_frontier - opp_frontier) * 5
    
    return score

def endgame_score(my_b, opp_b):
    """Final score calculation based on disc count."""
    my_c = popcount(my_b)
    opp_c = popcount(opp_b)
    if my_c > opp_c:
        return 10000 + (my_c - opp_c)
    elif my_c < opp_c:
        return -10000 - (opp_c - my_c)
    else:
        return 0

def popcount(x):
    """Counts set bits."""
    return x.bit_count()

def move_priority(coord):
    """Simple value for move ordering. Higher is better."""
    r, c = coord
    if (r == 0 or r == 7) and (c == 0 or c == 7):
        return 100 # Corners
    if r == 0 or r == 7 or c == 0 or c == 7:
        return 10   # Edges
    return 0
