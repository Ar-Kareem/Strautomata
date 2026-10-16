
import numpy as np
import time

# --- Constants & Configuration ---
SEARCH_DEPTH = 8  # Base depth, adjusted dynamically in game logic
TIME_LIMIT = 0.95 # Seconds

# Directions: (shift amount, edge mask to prevent wrapping)
# Bitboard indexing: 0 = a8 (top-left), 63 = h1 (bottom-right)
# Shift +1 = East, +8 = South, etc.
DIRS = [
    (1, 0x7F7F7F7F7F7F7F7F),   # East
    (8, 0x00FFFFFFFFFFFFFF),   # South
    (-1, 0xFEFEFEFEFEFEFEFE),  # West
    (-8, 0xFFFFFFFFFFFFFF00),  # North
    (9, 0x007F7F7F7F7F7F7F),   # SE
    (7, 0x007F7F7F7F7F7F00),   # SW
    (-9, 0x7F7F7F7F7F7F7F00),  # NE
    (-7, 0x7F7F7F7F7F7F7F7F)   # NW
]

# Positional weights (Row 0 is Rank 8, Col 0 is File a)
# Corners are high value, adjacent squares are dangerous (negative).
W_MATRIX = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
], dtype=np.int32)

W_FLAT = W_MATRIX.flatten()

# Corner indices for move ordering prioritization
CORNERS = {0, 7, 56, 63}

# --- Bitboard Helper Functions ---

def to_bitboard(arr: np.ndarray) -> int:
    """Convert an 8x8 numpy array to a 64-bit integer."""
    bb = 0
    for r in range(8):
        for c in range(8):
            if arr[r][c]:
                bb |= 1 << ((7-r) * 8 + c) # Map (r,c) to bit index
    return bb

def get_moves(me: int, opp: int) -> int:
    """Return a bitmask of all legal moves for 'me' against 'opp'."""
    moves = 0
    empty = ~(me | opp) & 0xFFFFFFFFFFFFFFFF
    
    # Generate moves for each direction
    for shift, mask in DIRS:
        # Potential captures: opponent discs adjacent to my discs in this direction
        candidates = opp & ((me << shift) if shift > 0 else (me >> -shift))
        candidates &= mask # Wrap protection
        
        # Extend the line of opponent discs
        while candidates:
            # If we reach empty squares after a line of opponents, those are legal moves
            potential_moves = empty & ((candidates << shift) if shift > 0 else (candidates >> -shift))
            potential_moves &= mask
            moves |= potential_moves
            
            # Continue extending the line
            candidates = opp & ((candidates << shift) if shift > 0 else (candidates >> -shift))
            candidates &= mask
            
    return moves

def count_bits(x: int) -> int:
    return bin(x).count('1')

def do_move(me: int, opp: int, move_idx: int) -> tuple:
    """
    Execute a move. Returns (new_me, new_opp).
    Flips discs in all valid directions.
    """
    new_me = me | (1 << move_idx)
    flipped = 0
    move_bit = 1 << move_idx
    
    for shift, mask in DIRS:
        # Find potential bracket line in this direction
        candidate = opp
        if shift > 0:
            candidate = (candidate >> shift) & mask
        else:
            candidate = (candidate << -shift) & mask
            
        # Check if adjacent cell in this direction is opponent
        if not (candidate & (move_bit if shift == 0 else 
                             (move_bit >> shift) if shift > 0 else 
                             (move_bit << -shift))):
            continue
            
        # Accumulate opponent discs
        potential_flips = 0
        current = move_bit
        valid_line = False
        
        while True:
            if shift > 0:
                current = (current << shift) & mask
            else:
                current = (current >> -shift) & mask
            
            if current & me:
                valid_line = True
                break
            if not (current & opp):
                break
            potential_flips |= current
            
        if valid_line:
            flipped |= potential_flips

    return new_me | flipped, opp ^ flipped

def evaluate(me: int, opp: int) -> int:
    """
    Evaluate board state.
    Returns score from perspective of 'me'.
    """
    # 1. Positional Strategy
    me_score = 0
    opp_score = 0
    
    # Simple weighted sum (can be optimized with precomputed patterns, but loop is fine)
    # Vectorized approach using numpy on reconstructed array is slow, so we iterate bits
    # or use pre-computed masks. Given 64 bits, we just check set bits.
    
    # More efficient: Precompute value for each of the 64 squares
    # (This is implicit in the logic below)
    
    b_me = me
    b_opp = opp
    i = 0
    while b_me:
        lsb = b_me & -b_me
        idx = (lsb.bit_length() - 1)
        # idx 0 is h8 (bit 0 in standard int)?? 
        # Wait, to_bitboard maps (7,0) [a1] to bit 0? 
        # Let's verify to_bitboard:
        # r=7, c=0 -> (7-7)*8 + 0 = 0. So bit 0 is a1.
        # But W_MATRIX is defined [0][0] = a8.
        # We need to align W_FLAT indices with bit indices.
        # Bit 0 = a1 (r=7, c=0). W_MATRIX[7][0] is -20.
        # Bit 63 = h8 (r=0, c=7). W_MATRIX[0][7] is 100.
        
        # Mapping: Bit index i -> row r = 7 - i//8, col c = i % 8
        r = 7 - (idx // 8)
        c = idx % 8
        me_score += W_MATRIX[r][c]
        b_me ^= lsb

    while b_opp:
        lsb = b_opp & -b_opp
        idx = (lsb.bit_length() - 1)
        r = 7 - (idx // 8)
        c = idx % 8
        opp_score += W_MATRIX[r][c]
        b_opp ^= lsb
        
    score = me_score - opp_score
    
    # 2. Mobility (Number of legal moves)
    # Important to look ahead slightly, but pure mobility count is a good heuristic
    my_mobility = count_bits(get_moves(me, opp))
    opp_mobility = count_bits(get_moves(opp, me))
    
    score += (my_mobility - opp_mobility) * 5
    
    # 3. Parity / End game (simple disc count if board is full)
    # If empties are few, disc count matters more
    empty = 64 - count_bits(me | opp)
    if empty < 10:
        score += (count_bits(me) - count_bits(opp)) * 10
        
    return score

# --- Search Algorithm ---

_start_time = 0

def minimax(me: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    global _start_time
    if time.time() - _start_time > TIME_LIMIT:
        # Return heuristic if out of time (simplified handling)
        return evaluate(me, opp)

    moves_mask = get_moves(me, opp)
    
    if moves_mask == 0:
        if get_moves(opp, me) == 0:
            # Game over
            diff = count_bits(me) - count_bits(opp)
            return 1000000 if diff > 0 else -1000000 if diff < 0 else 0
        # Pass turn
        return -minimax(opp, me, depth, -beta, -alpha)

    if depth == 0:
        return evaluate(me, opp)

    # Move Ordering: Try corners first
    move_list = []
    # Extract corners
    corner_moves = moves_mask & 0x8100000000000081 # Mask for 0, 7, 56, 63
    
    if corner_moves:
        # If corner is available, take it! (Heuristic shortcut)
        # Or prioritize it heavily.
        m = corner_moves & -corner_moves
        idx = m.bit_length() - 1
        val = -minimax(*do_move(me, opp, idx), depth - 1, -beta, -alpha)
        return val

    # Generate list of moves
    m = moves_mask
    while m:
        lsb = m & -m
        move_list.append(lsb.bit_length() - 1)
        m ^= lsb

    # Sort by heuristic (simple mobility guess could be added here, but random is ok for non-corners)
    
    best_score = -float('inf')
    for idx in move_list:
        new_me, new_opp = do_move(me, opp, idx)
        score = -minimax(new_me, new_opp, depth - 1, -beta, -alpha)
        if score > best_score:
            best_score = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return best_score

# --- Main Policy ---

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _start_time
    _start_time = time.time()
    
    me = to_bitboard(you)
    opp = to_bitboard(opponent)
    
    # 1. Identify legal moves
    moves_mask = get_moves(me, opp)
    
    if moves_mask == 0:
        return "pass"
    
    # 2. Search for best move
    # Use iterative deepening or fixed depth based on empties
    empties = 64 - count_bits(me | opp)
    
    # Dynamic depth
    if empties > 40:
        depth = 6
    elif empties > 20:
        depth = 8
    else:
        depth = 12 # Deep search in endgame
        
    best_idx = -1
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Check corners immediately (highest priority)
    corners_available = [i for i in range(64) if (moves_mask & (1 << i)) and i in CORNERS]
    if corners_available:
        # Just take the first corner found
        best_idx = corners_available[0]
    else:
        move_list = []
        m = moves_mask
        while m:
            lsb = m & -m
            move_list.append(lsb.bit_length() - 1)
            m ^= lsb
            
        # Move Ordering: High value squares first?
        # Sort by weight descending to improve pruning
        move_list.sort(key=lambda i: W_FLAT[63-i], reverse=True) # 63-i mapping check:
        # Bit 0 is a1 (W_MATRIX[7][0]). W_FLAT index for (7,0) is 7*8+0 = 56.
        # Bit 63 is h8 (W_MATRIX[0][7]). W_FLAT index for (0,7) is 7.
        # There's a reverse relationship between Bit Index and Flat Index due to board orientation.
        # Bit 0 (a1) -> r=7,c=0. Flat=56.
        # Bit 63 (h8) -> r=0,c=7. Flat=7.
        # Formula: flat_idx = (7 - bit//8)*8 + bit%8 = 56 - (bit//8)*8 + bit%8 = 56 - bit + 2*(bit%8). 
        # This is getting complex. Let's just use the evaluate logic inline or simpler sort.
        # Let's just loop.
        
        for idx in move_list:
            new_me, new_opp = do_move(me, opp, idx)
            
            # Check time before each deep search
            if time.time() - _start_time > TIME_LIMIT:
                if best_idx != -1: break # Use best found so far
            
            score = -minimax(new_me, new_opp, depth - 1, -beta, -alpha)
            
            if score > best_score:
                best_score = score
                best_idx = idx
            
            if score > alpha:
                alpha = score
                
    # 3. Convert to Algebraic Notation
    # idx 0 = a1 (r=7, c=0)
    # file: a + (idx % 8)
    # rank: 8 - (idx // 8)
    r = 7 - (best_idx // 8)
    c = best_idx % 8
    
    return f"{chr(ord('a') + c)}{r + 1}"
