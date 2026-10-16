
import time
import sys

# Constants for Bitboard layout (5 rows, 6 columns)
ROWS = 5
COLS = 6
SIZE = 30
FULL_MASK = (1 << SIZE) - 1

# Precomputed masks for column boundaries to prevent horizontal wrapping
MASK_COL_0 = sum(1 << (r * COLS + 0) for r in range(ROWS)) # Leftmost column
MASK_COL_5 = sum(1 << (r * COLS + 5) for r in range(ROWS)) # Rightmost column
NOT_COL_0 = ~MASK_COL_0 & FULL_MASK
NOT_COL_5 = ~MASK_COL_5 & FULL_MASK

# Transposition Table (Global to persist across calls if environment keeps the module loaded)
# Key: (you_bb, opp_bb), Value: (score, depth, flag, best_move_str)
TT = {}

# Constants for TT flags
FLAG_EXACT = 0
FLAG_LOWER = 1
FLAG_UPPER = 2

# Helper for popcount (Python 3.10+ has int.bit_count)
if hasattr(int, "bit_count"):
    def popcount(n):
        return n.bit_count()
else:
    def popcount(n):
        return bin(n).count('1')

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Determines the best move for Clobber on a 5x6 board.
    """
    start_time = time.time()
    time_limit = start_time + 0.90  # Allow 0.9s max execution time
    
    # --- 1. Parsing Input ---
    you_bb = 0
    opp_bb = 0
    
    # Auto-detect input format (List[List], Numpy, or Flat List)
    # We iterate coordinates (r, c) -> index i
    try:
        # Check if numpy-like or list-of-lists
        is_numpy = hasattr(you, 'shape')
        is_list_of_lists = isinstance(you, list) and len(you) > 0 and isinstance(you[0], list)
        
        for r in range(ROWS):
            for c in range(COLS):
                idx = r * COLS + c
                val_y = 0
                val_o = 0
                
                if is_numpy:
                    val_y = you[r, c]
                    val_o = opponent[r, c]
                elif is_list_of_lists:
                    val_y = you[r][c]
                    val_o = opponent[r][c]
                else:
                    # Assume flat list
                    val_y = you[idx]
                    val_o = opponent[idx]
                
                if val_y:
                    you_bb |= (1 << idx)
                elif val_o:
                    opp_bb |= (1 << idx)
    except Exception:
        # Fallback if structure is unexpected, though unlikely given specs
        return ""

    # --- 2. Iterative Deepening Search ---
    best_move = None
    depth = 1
    
    # Generate initial moves to ensure we have a fallback
    initial_moves = generate_moves(you_bb, opp_bb)
    if not initial_moves:
        return "" # No legal moves, loss condition
        
    best_move = initial_moves[0][2] # Default fallback
    
    while True:
        try:
            # Check timeout before starting a new depth
            if time.time() > time_limit:
                break
                
            # Perform Negamax Search
            score, move_str = negamax(you_bb, opp_bb, depth, -999999, 999999, time_limit)
            
            if move_str:
                best_move = move_str
            
            # Check for proving a win or inevitable loss (values > 90000)
            if score > 90000 or score < -90000:
                break
            
            depth += 1
            # 5x6 board max depth isn't infinite, but 30 is theoretical max.
            # In 1s, we likely hit depth 8-12.
            if depth > 40: 
                break
                
        except TimeoutError:
            break
            
    return best_move

def negamax(my_bb, opp_bb, depth, alpha, beta, deadline):
    """
    Negamax with Alpha-Beta Pruning.
    Returns (score, best_move_string)
    """
    # Time check (every few nodes implicit by depth or just perform at start)
    if time.time() > deadline:
        raise TimeoutError

    # TT Lookup
    tt_key = (my_bb, opp_bb)
    tt_move = None
    if tt_key in TT:
        s, d, f, m = TT[tt_key]
        if d >= depth:
            if f == FLAG_EXACT:
                return s, m
            elif f == FLAG_LOWER:
                alpha = max(alpha, s)
            elif f == FLAG_UPPER:
                beta = min(beta, s)
            if alpha >= beta:
                return s, m
        # Use TT move for ordering even if depth is insufficient
        tt_move = m

    # Leaf Evaluation
    if depth == 0:
        val = evaluate(my_bb, opp_bb)
        # Store in TT as exact for depth 0
        TT[tt_key] = (val, 0, FLAG_EXACT, None)
        return val, None

    move_list = generate_moves(my_bb, opp_bb)
    
    # Terminal State check
    if not move_list:
        # I have no moves -> I lose. 
        # Score should be very low, adjusted by depth to prefer losing later over sooner.
        # Max score approx 100000.
        return -100000 + (100 - depth), None

    # Move Ordering
    # If we have a best move from TT, try it first
    if tt_move:
        # Find tuple matching string
        for i in range(len(move_list)):
            if move_list[i][2] == tt_move:
                # Move to front
                move_list.insert(0, move_list.pop(i))
                break

    best_val = -float('inf')
    best_str = None
    
    orig_alpha = alpha
    
    for src, dst, m_str in move_list:
        # Apply Move
        # Remove MY piece from src, Add MY piece to dst
        # Remove OPP piece from dst (covered by XORing/Setting)
        
        # New MY: bit @src becomes 0, bit @dst becomes 1.
        # Since src was 1 and dst was 0 in my_bb:
        new_my = (my_bb ^ (1 << src)) | (1 << dst)
        
        # New OPP: bit @dst becomes 0 (it was 1).
        new_opp = opp_bb ^ (1 << dst)
        
        # Recursive call (Swap roles: opp becomes 'you')
        val, _ = negamax(new_opp, new_my, depth - 1, -beta, -alpha, deadline)
        val = -val
        
        if val > best_val:
            best_val = val
            best_str = m_str
        
        alpha = max(alpha, val)
        if alpha >= beta:
            break # Beta Cutoff

    # Update TT
    flag = FLAG_EXACT
    if best_val <= orig_alpha:
        flag = FLAG_UPPER # Fail low
    elif best_val >= beta:
        flag = FLAG_LOWER # Fail high
        
    TT[tt_key] = (best_val, depth, flag, best_str)
    
    return best_val, best_str

def generate_moves(my_bb, opp_bb):
    """
    Generates all legal moves for 'my_bb'.
    Returns list of (src_index, dst_index, move_string)
    """
    moves = []
    
    # 1. UP: src - 6. DEST = SRC - 6.
    # Logic: To find valid sources, we check destinations.
    # Destination must be OPP. Source needs to be MY.
    # Pattern: (MY >> 6) & OPP identifies valid DESTINATIONS for 'UP' moves from MY.
    dest_map = (my_bb >> 6) & opp_bb
    while dest_map:
        d_bit = dest_map & -dest_map
        dst = d_bit.bit_length() - 1
        src = dst + 6
        r, c = src // COLS, src % COLS
        moves.append((src, dst, f"{r},{c},U"))
        dest_map ^= d_bit
        
    # 2. DOWN: src + 6. DEST = SRC + 6.
    # Pattern: (MY << 6) & OPP
    dest_map = (my_bb << 6) & opp_bb & FULL_MASK
    while dest_map:
        d_bit = dest_map & -dest_map
        dst = d_bit.bit_length() - 1
        src = dst - 6
        r, c = src // COLS, src % COLS
        moves.append((src, dst, f"{r},{c},D"))
        dest_map ^= d_bit
        
    # 3. LEFT: src - 1. DEST = SRC - 1.
    # Pattern: ((MY & NOT_COL_0) >> 1) & OPP
    # Mask src to ensure we don't wrap 'left' from column 0
    dest_map = ((my_bb & NOT_COL_0) >> 1) & opp_bb
    while dest_map:
        d_bit = dest_map & -dest_map
        dst = d_bit.bit_length() - 1
        src = dst + 1
        r, c = src // COLS, src % COLS
        moves.append((src, dst, f"{r},{c},L"))
        dest_map ^= d_bit
        
    # 4. RIGHT: src + 1. DEST = SRC + 1.
    # Pattern: ((MY & NOT_COL_5) << 1) & OPP
    dest_map = ((my_bb & NOT_COL_5) << 1) & opp_bb & FULL_MASK
    while dest_map:
        d_bit = dest_map & -dest_map
        dst = d_bit.bit_length() - 1
        src = dst - 1
        r, c = src // COLS, src % COLS
        moves.append((src, dst, f"{r},{c},R"))
        dest_map ^= d_bit
        
    return moves

def evaluate(my_bb, opp_bb):
    """
    Heuristic Evaluation: Mobility Difference.
    (My Moves) - (Opponent Moves).
    """
    return count_liberties(my_bb, opp_bb) - count_liberties(opp_bb, my_bb)

def count_liberties(p1, p2):
    """Counts possible captures p1 can make on p2."""
    c = 0
    # UP capture
    c += popcount((p1 >> 6) & p2)
    # DOWN capture
    c += popcount((p1 << 6) & p2 & FULL_MASK)
    # LEFT capture
    c += popcount(((p1 & NOT_COL_0) >> 1) & p2)
    # RIGHT capture
    c += popcount(((p1 & NOT_COL_5) << 1) & p2 & FULL_MASK)
    return c
