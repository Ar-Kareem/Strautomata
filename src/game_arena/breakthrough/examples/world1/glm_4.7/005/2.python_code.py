
import random

# Bitboard Constants
FILE_A = 0x0101010101010101  # Column 0 mask
FILE_H = 0x8080808080808080  # Column 7 mask
RANK_1 = 0x00000000000000FF  # Row 0 mask (White Home)
RANK_8 = 0xFF00000000000000  # Row 7 mask (Black Home)

# Precomputed array to map index to (row, col)
IDX_TO_RC = [(i >> 3, i & 7) for i in range(64)]

def tuple_to_bitboard(pieces):
    """Convert list of (r,c) tuples to a bitmask."""
    mask = 0
    for r, c in pieces:
        mask |= 1 << (r * 8 + c)
    return mask

def bitboard_to_list(mask):
    """Convert bitmask to list of (r,c) tuples."""
    pieces = []
    m = mask
    while m:
        lsb = m & -m
        idx = (lsb.bit_length() - 1)
        pieces.append(IDX_TO_RC[idx])
        m ^= lsb
    return pieces

def get_moves_bitboard(me_mask, opp_mask, color):
    """Generate all legal moves for 'color' given bitboards."""
    occupied = me_mask | opp_mask
    moves = []
    
    if color == 'w':
        # White moves Up (indices increase)
        # Forward: must be empty
        single_fwd = (me_mask << 8) & ~occupied & 0xFFFFFFFFFFFFFF00
        
        # Diagonals: can be empty or occupied by opponent
        # Left Diag (from player's view, visually left -> col-1)
        # Shift 7: 8 up, 1 left. Mask FILE_A to prevent wrap.
        left = (me_mask & ~FILE_A) << 7
        # Right Diag (col+1)
        # Shift 9: 8 up, 1 right. Mask FILE_H to prevent wrap.
        right = (me_mask & ~FILE_H) << 9
        
        # Valid diagonal targets are those not occupied by self
        valid_diag = ((left | right) & ~me_mask)
        
        # Iterate over pieces to reconstruct moves
        for r, c in bitboard_to_list(me_mask):
            idx = r * 8 + c
            fr, fc = r, c
            
            # Check Forward
            tr_fwd = idx + 8
            if tr_fwd < 64 and (single_fwd >> tr_fwd) & 1:
                moves.append(((fr, fc), IDX_TO_RC[tr_fwd]))
                
            # Check Diagonals
            tr_left = idx + 7
            if c > 0 and tr_left < 64 and (valid_diag >> tr_left) & 1:
                moves.append(((fr, fc), IDX_TO_RC[tr_left]))
                
            tr_right = idx + 9
            if c < 7 and tr_right < 64 and (valid_diag >> tr_right) & 1:
                moves.append(((fr, fc), IDX_TO_RC[tr_right]))
                
    else: # Black
        # Black moves Down (indices decrease)
        single_fwd = (me_mask >> 8) & ~occupied & 0x00FFFFFFFFFFFFFF
        
        # Left Diag (visually left -> col-1)
        # Shift 9: 8 down, 1 left. 
        # Wait, Black Down-Left: r-1, c-1. Index change: -8 - 1 = -9.
        # Check wrap: FILE_A (c=0) cannot move left.
        left = (me_mask & ~FILE_A) >> 9
        # Right Diag (visually right -> col+1)
        # Shift 7: 8 down, 1 right.
        # Check wrap: FILE_H (c=7) cannot move right.
        right = (me_mask & ~FILE_H) >> 7
        
        valid_diag = ((left | right) & ~me_mask)
        
        for r, c in bitboard_to_list(me_mask):
            idx = r * 8 + c
            fr, fc = r, c
            
            # Check Forward
            tr_fwd = idx - 8
            if tr_fwd >= 0 and (single_fwd >> tr_fwd) & 1:
                moves.append(((fr, fc), IDX_TO_RC[tr_fwd]))
                
            # Check Diagonals
            tr_left = idx - 9
            if c > 0 and tr_left >= 0 and (valid_diag >> tr_left) & 1:
                moves.append(((fr, fc), IDX_TO_RC[tr_left]))
                
            tr_right = idx - 7
            if c < 7 and tr_right >= 0 and (valid_diag >> tr_right) & 1:
                moves.append(((fr, fc), IDX_TO_RC[tr_right]))
                
    return moves

def apply_move(me_mask, opp_mask, move):
    """Applies a move tuple to the bitboards."""
    (fr, fc), (tr, tc) = move
    from_idx = fr * 8 + fc
    to_idx = tr * 8 + tc
    
    new_me = me_mask & ~(1 << from_idx)
    new_me |= (1 << to_idx)
    
    new_opp = opp_mask
    if (1 << to_idx) & opp_mask:
        new_opp &= ~(1 << to_idx)
        
    return new_me, new_opp

def evaluate(me_mask, opp_mask, color):
    """
    Returns a score relative to the player to move.
    Positive = Good for current player.
    """
    # Base scores
    me_count = me_mask.bit_count()
    opp_count = opp_mask.bit_count()
    
    if me_count == 0: return -100000
    if opp_count == 0: return 100000
    
    score = (me_count - opp_count) * 1000
    
    # Positional evaluation
    me_list = bitboard_to_list(me_mask)
    opp_list = bitboard_to_list(opp_mask)
    
    my_adv = 0
    opp_adv = 0
    
    if color == 'w':
        # White wants high rows
        for r, c in me_list: my_adv += r
        # Black (opponent) wants low rows (so 7-r is progress)
        for r, c in opp_list: opp_adv += (7 - r)
    else:
        # Black wants low rows
        for r, c in me_list: my_adv += (7 - r)
        # White (opponent) wants high rows
        for r, c in opp_list: opp_adv += r
        
    score += (my_adv - opp_adv) * 10
    
    return score

def minimax(me_mask, opp_mask, color, depth, alpha, beta):
    # Check win conditions related to board state
    if color == 'w' and (me_mask & RANK_8): return 100000 # White wins
    if color == 'b' and (me_mask & RANK_1): return 100000 # Black wins
    if color == 'w' and (opp_mask & RANK_1): return -100000 # Black reached end
    if color == 'b' and (opp_mask & RANK_8): return -100000 # White reached end
    
    if depth == 0:
        return evaluate(me_mask, opp_mask, color)

    moves = get_moves_bitboard(me_mask, opp_mask, color)
    if not moves:
        return -100000 # No moves = loss

    # Sort moves: Captures first
    opp_mask_ref = opp_mask
    moves.sort(key=lambda m: 1 if ((1 << (m[1][0]*8 + m[1][1])) & opp_mask_ref) else 0, reverse=True)

    if color == 'w':
        max_eval = -float('inf')
        for m in moves:
            new_me, new_opp = apply_move(me_mask, opp_mask, m)
            # Next turn is Black, perspective changes to Black
            # But minimax here returns score relative to the player to move in that call?
            # Let's stick to: score is always relative to CURRENT `color`.
            # No, standard minimax returns value of the state for the root player.
            # To avoid confusion, let's use the perspective flip:
            # If I am White (Max), and I move to state S.
            # In state S, it is Black's turn. Black will choose move that minimizes White's score (or maximizes theirs).
            # Let's rely on NegaMax-like logic but with explicit color check for simplicity.
            # Value = - minimax(new_opp, new_me, next_color, ...)
            
            val = minimax(new_opp, new_me, 'b', depth - 1, -beta, -alpha)
            # Invert val because if Black gets +10, it's -10 for White.
            max_eval = max(max_eval, -val)
            alpha = max(alpha, -val)
            if beta <= alpha: break
        return max_eval
    else:
        # Black wants to minimize White's score, or Maximize their own.
        # Let's treat the recursive value as "Score for the player to move".
        # Recursive call returns score for White.
        # Black wants to minimize White's score.
        
        # Actually, let's standardise: evaluate() returns score for 'color'.
        # So:
        # If White moves: val = - minimax(..., 'b', ...) (Maximize)
        # If Black moves: val = - minimax(..., 'w', ...) (Maximize self)
        
        # Let's restart the logic block for standard NegaMax:
        # v = -search(next_state, next_color)
        
        max_eval = -float('inf') # We always maximize for the *current* player
        next_color = 'w'
        
        for m in moves:
            new_me, new_opp = apply_move(me_mask, opp_mask, m)
            val = minimax(new_opp, new_me, next_color, depth - 1, -beta, -alpha)
            
            # val returned is score for next_color (White).
            # If I am Black, I want White's score to be low (or my score high).
            # NegaMax: best = max(best, -val)
            
            max_eval = max(max_eval, -val)
            alpha = max(alpha, -val)
            if beta <= alpha: break
        return max_eval

def policy(me, opp, color):
    me_mask = tuple_to_bitboard(me)
    opp_mask = tuple_to_bitboard(opp)
    
    # 1. Check for immediate winning move
    target_rank = RANK_8 if color == 'w' else RANK_1
    moves = get_moves_bitboard(me_mask, opp_mask, color)
    
    for m in moves:
        tr, tc = m[1]
        if (1 << (tr * 8 + tc)) & target_rank:
            return m
            
    # 2. Run Search
    best_move = None
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Dynamic Depth
    depth = 3
    if len(me) < 8 or len(opp) < 8: depth = 4
    
    moves.sort(key=lambda m: 1 if ((1 << (m[1][0]*8 + m[1][1])) & opp_mask) else 0, reverse=True)
    
    next_c = 'b' if color == 'w' else 'w'
    
    for m in moves:
        new_me, new_opp = apply_move(me_mask, opp_mask, m)
        val = minimax(new_opp, new_me, next_c, depth - 1, -beta, -alpha)
        
        # val is score for opponent. We want to minimize opponent's score (maximize -val).
        actual_val = -val
        
        if actual_val > best_val:
            best_val = actual_val
            best_move = m
            
        alpha = max(alpha, actual_val)
        
    if best_move is None:
        # Should not happen if moves exist, but fallback
        return moves[0]
        
    return best_move
