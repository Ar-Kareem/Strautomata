
import numpy as np
import time

# Constants for bitboard logic
ROWS = 5
COLS = 6
FULL_MASK = (1 << (ROWS * COLS)) - 1

# Precompute masks for column boundaries to handle wrapping
# Column 0 indices: 0, 6, 12, 18, 24
COL_0_MASK = sum(1 << i for i in range(0, 30, 6))
# Column 5 indices: 5, 11, 17, 23, 29
COL_5_MASK = sum(1 << i for i in range(5, 30, 6))

# Directions for move generation: (shift_amount, boundary_mask_exclusion)
# Move Right: shift +1, cannot start at col 5
# Move Left: shift -1, cannot start at col 0
# Move Up: shift -6, valid if result is on board (handled by shifting 0s out)
# Move Down: shift +6, valid if result is on board

# Move Generation using Bitboards
# We compute possible destinations for each direction
# Destinations = (MyPieces SHIFT Dir) & OpponentPieces
# But we must ensure we don't shift across boundaries (horizontal) or off board (vertical)

def get_moves_bb(my_pieces, opp_pieces):
    """Returns a list of (start_bit, dest_bit) tuples."""
    moves = []
    
    # Up (Shift Right by 6 in bitboard terms where row 0 is LSB? No, let's define mapping.)
    # Let's use mapping: index = row * 6 + col.
    # Row 0 is bits 0-5. Row 4 is bits 24-29.
    # Up: row decreases. index decreases by 6. Shift Right by 6.
    up_dests = (my_pieces >> 6) & opp_pieces
    # Down: row increases. index increases by 6. Shift Left by 6.
    down_dests = ((my_pieces << 6) & FULL_MASK) & opp_pieces
    # Left: col decreases. index decreases by 1. Shift Right by 1.
    # Cannot move left from col 0.
    left_sources = my_pieces & ~COL_0_MASK
    left_dests = (left_sources >> 1) & opp_pieces
    # Right: col increases. index increases by 1. Shift Left by 1.
    # Cannot move right from col 5.
    right_sources = my_pieces & ~COL_5_MASK
    right_dests = (right_sources << 1) & opp_pieces

    # Extract moves from bitmasks
    # Helper to iterate set bits
    def iter_bits(n):
        while n:
            b = n & -n
            yield b
            n -= b

    # Up moves: dest is at bit b. start is at b << 6
    for dest in iter_bits(up_dests):
        moves.append((dest << 6, dest))
    # Down moves: dest is b. start is b >> 6
    for dest in iter_bits(down_dests):
        moves.append((dest >> 6, dest))
    # Left moves: dest is b. start is b << 1
    for dest in iter_bits(left_dests):
        moves.append((dest << 1, dest))
    # Right moves: dest is b. start is b >> 1
    for dest in iter_bits(right_dests):
        moves.append((dest >> 1, dest))
        
    return moves

def count_moves_bb(my_pieces, opp_pieces):
    """Efficiently counts legal moves."""
    cnt = 0
    # Up
    cnt += ((my_pieces >> 6) & opp_pieces).bit_count()
    # Down
    cnt += (((my_pieces << 6) & FULL_MASK) & opp_pieces).bit_count()
    # Left
    cnt += ((my_pieces & ~COL_0_MASK) >> 1 & opp_pieces).bit_count()
    # Right
    cnt += ((my_pieces & ~COL_5_MASK) << 1 & opp_pieces).bit_count()
    return cnt

def move_to_str(start_bit, dest_bit):
    """Converts bit positions to string 'row,col,dir'."""
    start_idx = (start_bit - 1).bit_length() if start_bit > 0 else -1
    dest_idx = (dest_bit - 1).bit_length() if dest_bit > 0 else -1
    
    r1, c1 = divmod(start_idx, 6)
    r2, c2 = divmod(dest_idx, 6)
    
    if r2 == r1 + 1: d = 'D'
    elif r2 == r1 - 1: d = 'U'
    elif c2 == c1 + 1: d = 'R'
    elif c2 == c1 - 1: d = 'L'
    else: d = '?' # Should not happen
    
    return f"{r1},{c1},{d}"

def negamax(my_pieces, opp_pieces, depth, alpha, beta):
    """Returns (score, best_move_tuple)."""
    # Terminal check: if I have no moves, I lose.
    my_moves = get_moves_bb(my_pieces, opp_pieces)
    if not my_moves:
        return -10000 - depth, None # Loss is bad, prefer later losses (depth)
    
    if depth == 0:
        # Evaluation: My Mobility - Opp Mobility
        score = count_moves_bb(my_pieces, opp_pieces) - count_moves_bb(opp_pieces, my_pieces)
        return score, None
    
    # Move ordering: heuristic to try 'forcing' moves first?
    # Simple heuristic: order by count of my moves after move? Too expensive.
    # Let's just process them. Order might be improved by checking if move captures a piece with many neighbors?
    
    best_score = -20000
    best_move = my_moves[0] # Default
    
    # To improve alpha-beta, we can sort moves by a simple heuristic.
    # Heuristic: prefer capturing pieces that have many of my neighbors?
    # Or just proceed. Clobber branching is low.
    
    for start, dest in my_moves:
        # Apply move
        # My piece at start moves to dest (which was opponent).
        # My pieces: remove start, add dest.
        # Opp pieces: remove dest.
        new_my = (my_pieces ^ start) | dest
        new_opp = opp_pieces ^ dest
        
        # Recursive call
        # Arguments swap: their turn, so they become 'my_pieces' in recursive call
        val, _ = negamax(new_opp, new_my, depth - 1, -beta, -alpha)
        current_score = -val
        
        if current_score > best_score:
            best_score = current_score
            best_move = (start, dest)
            
        alpha = max(alpha, current_score)
        if alpha >= beta:
            break # Beta cutoff
            
    return best_score, best_move

def policy(you: list, opponent: list) -> str:
    start_time = time.time()
    
    # Convert to bitboard
    my_bb = 0
    opp_bb = 0
    for r in range(5):
        for c in range(6):
            idx = r * 6 + c
            if you[r][c] == 1:
                my_bb |= (1 << idx)
            if opponent[r][c] == 1:
                opp_bb |= (1 << idx)
                
    # Iterative Deepening
    best_move = None
    # Time limit management
    # Clobber 5x6 is small. Depth 10-12 is reachable.
    
    # Check if only one move available
    moves = get_moves_bb(my_bb, opp_bb)
    if len(moves) == 1:
        return move_to_str(moves[0][0], moves[0][1])
        
    # We use a simplified iterative deepening to stay within time.
    # Since python is slow, we don't have much time for many depths.
    # 1 second allows roughly depth 6-8.
    
    for depth in range(1, 20):
        try:
            # simple time check wrapper logic could be here, 
            # but negamax is synchronous.
            # We estimate if we have time.
            if time.time() - start_time > 0.8: # Safety break
                break
            score, move = negamax(my_bb, opp_bb, depth, -30000, 30000)
            if move:
                best_move = move
            # If we found a winning line, break?
            if score > 9000: # Near certain win
                break
        except:
            break
            
    if best_move:
        return move_to_str(best_move[0], best_move[1])
    
    # Fallback (should not be reached if logic is correct)
    if moves:
        return move_to_str(moves[0][0], moves[0][1])
    return "0,0,U" # Should be impossible if game logic holds
