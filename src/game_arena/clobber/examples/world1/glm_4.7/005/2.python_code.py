
import sys

# --- Bitboard Definitions for 5x6 Board ---
# Board indices: 0..29. Row = i // 6, Col = i % 6.
# 5 Rows (0-4), 6 Cols (0-5).

# Masks for columns to prevent invalid horizontal moves wrapping around rows
# Col 0: indices 0, 6, 12, 18, 24
_MASK_COL_0 = sum(1 << (r * 6) for r in range(5))
# Col 5: indices 5, 11, 17, 23, 29
_MASK_COL_5 = sum(1 << (r * 6 + 5) for r in range(5))

# Masks for rows to prevent invalid vertical moves
# Rows 0-4
_MASK_ROWS = [sum(1 << (r * 6 + c) for c in range(6)) for r in range(5)]

# Combine masks for vertical boundaries
# Valid Up moves: Player in Row 1-4 captures Opponent in Row 0-3
_MASK_NOT_ROW_0 = _MASK_ROWS[1] | _MASK_ROWS[2] | _MASK_ROWS[3] | _MASK_ROWS[4]
_MASK_NOT_ROW_4 = _MASK_ROWS[0] | _MASK_ROWS[1] | _MASK_ROWS[2] | _MASK_ROWS[3]

# Depth of search
_SEARCH_DEPTH = 4
_INF = 1000000

def _to_bitboard(board_list):
    """Converts a list of lists or flat list to a 30-bit integer."""
    bb = 0
    # Check if 2D
    if len(board_list) > 0 and isinstance(board_list[0], list):
        for r in range(5):
            for c in range(6):
                if board_list[r][c]:
                    bb |= 1 << (r * 6 + c)
    else:
        # Assume flat list of 30 or check length
        for i in range(min(len(board_list), 30)):
            if board_list[i]:
                bb |= 1 << i
    return bb

def _count_moves(me, opp):
    """
    Returns the number of legal moves for 'me' capturing 'opp'.
    Uses bitboard operations for speed.
    """
    moves = 0
    
    # Vertical Moves
    # Down: Me (r-1) captures Opp (r). Me rows 1-4, Opp rows 0-3.
    # (Me shifted right by 6) matches Opp
    moves += ((me & _MASK_NOT_ROW_0) >> 6 & opp).bit_count()
    
    # Up: Me (r) captures Opp (r-1). Me rows 0-3, Opp rows 1-4.
    # (Me shifted left by 6) matches Opp
    moves += ((me & _MASK_NOT_ROW_4) << 6 & opp).bit_count()
    
    # Horizontal Moves
    # Right: Me (c) captures Opp (c+1). Me cols 0-4, Opp cols 1-5.
    # (Me shifted left by 1) matches Opp (masked)
    # We must mask Opp to ignore col 0 (which shifts into col 1 of next row) ??
    # No, we mask ME to col 0-4.
    # If Me is at col 5, cannot move right.
    # Target (c+1) must exist. If Me is at col 4, target is 5.
    # Shift Me left by 1. 
    # Me & ~Col_5 (valid sources) << 1.
    # Result & Opp.
    moves += ((me & ~_MASK_COL_5) << 1 & opp).bit_count()
    
    # Left: Me (c) captures Opp (c-1). Me cols 1-5, Opp cols 0-4.
    # Shift Me right by 1.
    # Me & ~Col_0 (valid sources) >> 1.
    moves += ((me & ~_MASK_COL_0) >> 1 & opp).bit_count()
    
    return moves

def _evaluate(me, opp):
    """Heuristic evaluation: Mobility difference."""
    return _count_moves(me, opp) - _count_moves(opp, me)

def _minimax(me, opp, depth, alpha, beta):
    """
    Minimax with Alpha-Beta pruning.
    Returns the score of the position.
    """
    # Terminal node check (no moves for current player)
    # Note: We only check if current player has moves. If not, they lose.
    # A loss is -Inf.
    
    # Static evaluation or check terminal
    if depth == 0:
        return _evaluate(me, opp)
    
    # Check if me has any moves
    # We do a quick check of mobility. If 0, return -score
    my_mobility = _count_moves(me, opp)
    if my_mobility == 0:
        return -_INF + (_SEARCH_DEPTH - depth) # Prefer losing later

    best_val = -_INF
    
    # Generate moves
    # To avoid generating full list of objects, we iterate over bits
    # But for simplicity and speed in python, we iterate over 4 directions logic
    
    # 1. UP Moves (Me rows 0-3 -> Opp rows 1-4)
    # Sources: me & _MASK_NOT_ROW_4
    src_up = me & _MASK_NOT_ROW_4
    # Destinations: opp shifted right 6 (opp rows 1-4 become rows 0-3)
    # Actually, logic: Me at i. Target i+6. Opp has i+6.
    # So (me << 6) & opp indicates valid captures.
    up_captures = (src_up << 6) & opp
    
    while up_captures:
        dest_bit = up_captures & -up_captures # isolate lowest bit
        dest_idx = (dest_bit.bit_length() - 1)
        src_idx = dest_idx - 6
        # Move
        new_me = (me & ~(1 << src_idx)) | dest_bit
        new_opp = opp & ~dest_bit
        val = -_minimax(new_opp, new_me, depth - 1, -beta, -alpha)
        if val > best_val: best_val = val
        if val > alpha: alpha = val
        if beta <= alpha: return best_val
        up_captures ^= dest_bit

    # 2. DOWN Moves (Me rows 1-4 -> Opp rows 0-3)
    src_down = me & _MASK_NOT_ROW_0
    # (me >> 6) & opp
    down_captures = (src_down >> 6) & opp
    
    while down_captures:
        dest_bit = down_captures & -down_captures
        dest_idx = (dest_bit.bit_length() - 1)
        src_idx = dest_idx + 6
        new_me = (me & ~(1 << src_idx)) | dest_bit
        new_opp = opp & ~dest_bit
        val = -_minimax(new_opp, new_me, depth - 1, -beta, -alpha)
        if val > best_val: best_val = val
        if val > alpha: alpha = val
        if beta <= alpha: return best_val
        down_captures ^= dest_bit

    # 3. RIGHT Moves (Me cols 0-4 -> Opp cols 1-5)
    src_right = me & ~_MASK_COL_5
    # (me << 1) & opp
    right_captures = (src_right << 1) & opp
    
    while right_captures:
        dest_bit = right_captures & -right_captures
        dest_idx = (dest_bit.bit_length() - 1)
        src_idx = dest_idx - 1
        # Check boundary condition (row wrap around)
        # Already handled by masking src_right (~Col5) and implicit shifting
        # But we must ensure we didn't jump rows.
        # e.g. idx 5 -> None: best_val = val
        if val > alpha: alpha = val
        if beta <= alpha: return best_val
        right_captures ^= dest_bit

    # 4. LEFT Moves (Me cols 1-5 -> Opp cols 0-4)
    src_left = me & ~_MASK_COL_0
    # (me >> 1) & opp
    left_captures = (src_left >> 1) & opp
    
    while left_captures:
        dest_bit = left_captures & -left_captures
        dest_idx = (dest_bit.bit_length() - 1)
        src_idx = dest_idx + 1
        # Safe because src_left excludes col 0.
        new_me = (me & ~(1 << src_idx)) | dest_bit
        new_opp = opp & ~dest_bit
        val = -_minimax(new_opp, new_me, depth - 1, -beta, -alpha)
        if val > best_val: best_val = val
        if val > alpha: alpha = val
        if beta <= alpha: return best_val
        left_captures ^= dest_bit

    return best_val

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Main policy function.
    """
    # Convert to bitboards
    me_bb = _to_bitboard(you)
    opp_bb = _to_bitboard(opponent)

    best_move_str = ""
    best_val = -_INF - 1
    alpha = -_INF
    beta = _INF
    
    # Collect all legal moves as strings to return one later
    # We also need to iterate them for the search root
    
    # Helper to generate and search moves for a specific direction
    def search_dir(src_mask, shift, direction, is_positive_shift):
        nonlocal best_move_str, best_val, alpha
        
        # Valid captures: (src shifted) intersects opponent
        if is_positive_shift:
            captures = (src_mask << shift) & opp_bb
        else:
            captures = (src_mask >> shift) & opp_bb
            
        while captures:
            dest_bit = captures & -captures
            dest_idx = (dest_bit.bit_length() - 1)
            
            # Calculate source index
            if is_positive_shift:
                src_idx = dest_idx - shift
            else:
                src_idx = dest_idx + shift
                
            # Validate row boundary for vertical moves
            # We masked sources, so it should be safe, but just in case
            r_src, c_src = divmod(src_idx, 6)
            r_dest, c_dest = divmod(dest_idx, 6)
            
            # Create Move String
            move_str = f"{r_src},{c_src},{direction}"
            
            # Apply move
            new_me = (me_bb & ~(1 << src_idx)) | dest_bit
            new_opp = opp_bb & ~dest_bit
            
            # Search
            val = -_minimax(new_opp, new_me, _SEARCH_DEPTH - 1, -beta, -alpha)
            
            if val > best_val:
                best_val = val
                best_move_str = move_str
            
            if val > alpha:
                alpha = val
            
            if beta <= alpha:
                return # Prune remaining moves in this direction loop
                
            captures ^= dest_bit

    # 1. UP
    src_up = me_bb & _MASK_NOT_ROW_4
    search_dir(src_up, 6, 'U', True)
    
    # 2. DOWN
    src_down = me_bb & _MASK_NOT_ROW_0
    search_dir(src_down, 6, 'D', False)
    
    # 3. LEFT
    src_left = me_bb & ~_MASK_COL_0
    search_dir(src_left, 1, 'L', False)
    
    # 4. RIGHT
    src_right = me_bb & ~_MASK_COL_5
    search_dir(src_right, 1, 'R', True)

    # Fallback: Should not happen if legal moves exist
    if not best_move_str:
        # Find ANY legal move just to be safe (should be impossible if minimax works correctly or game not over)
        # Brute force scan
        for r in range(5):
            for c in range(6):
                if me_bb & (1 << (r*6 + c)):
                    if r > 0 and opp_bb & (1 << ((r-1)*6 + c)): return f"{r},{c},U"
                    if r < 4 and opp_bb & (1 << ((r+1)*6 + c)): return f"{r},{c},D"
                    if c > 0 and opp_bb & (1 << (r*6 + c - 1)): return f"{r},{c},L"
                    if c < 5 and opp_bb & (1 << (r*6 + c + 1)): return f"{r},{c},R"
    
    return best_move_str
