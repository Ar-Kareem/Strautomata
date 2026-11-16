
import time
import random

# --- PRECOMPUTED CONSTANTS ---

# Masks for all 32 possible winning lines (5 consecutive bits)
# Represented as 1s in a 36-bit integer.
WIN_MASKS = []

def _init_win_masks():
    masks = []
    # Rows: 6 rows, 2 possible start positions (col 0 and col 1)
    for r in range(6):
        for c in range(2):
            m = 0
            for k in range(5): m |= (1 << (r * 6 + c + k))
            masks.append(m)
    # Cols: 6 cols, 2 possible start positions (row 0 and row 1)
    for c in range(6):
        for r in range(2):
            m = 0
            for k in range(5): m |= (1 << ((r + k) * 6 + c))
            masks.append(m)
    # Diagonals (Main direction: Top-Left to Bottom-Right)
    # Starts at (0,0), (0,1), (1,0), (1,1)
    # (0,0) length 6 -> 2 masks
    m1, m2 = 0, 0
    for k in range(5):
        m1 |= (1 << (k * 6 + k))
        m2 |= (1 << ((k + 1) * 6 + (k + 1)))
    masks.append(m1); masks.append(m2)
    
    # (0,1) length 5 -> 1 mask
    m = 0
    for k in range(5): m |= (1 << (k * 6 + (k + 1)))
    masks.append(m)
    
    # (1,0) length 5 -> 1 mask
    m = 0
    for k in range(5): m |= (1 << ((k + 1) * 6 + k))
    masks.append(m)
    
    # Anti-Diagonals (Top-Right to Bottom-Left)
    # Starts at (0,5), (0,4), (1,5), (1,4)
    # (0,5) length 6 -> 2 masks
    m1, m2 = 0, 0
    for k in range(5):
        m1 |= (1 << (k * 6 + (5 - k)))
        m2 |= (1 << ((k + 1) * 6 + (5 - (k + 1))))
    masks.append(m1); masks.append(m2)
    
    # (0,4) length 5
    m = 0
    for k in range(5): m |= (1 << (k * 6 + (4 - k)))
    masks.append(m)
    
    # (1,5) length 5
    m = 0
    for k in range(5): m |= (1 << ((k + 1) * 6 + (5 - k)))
    masks.append(m)
    
    return masks

WIN_MASKS = _init_win_masks()

# Quadrant masks and rotation mappings
# QUAD_MASK[q] gets bits for that quad
# ROT_MOVES[(q, dir)] = list of (src_bit, dst_bit)
QUAD_MASKS = [0, 0, 0, 0]
ROT_MOVES = {}

def _init_rotations():
    # Helper to get quadrant info
    # q0: global rows 0-2, cols 0-2
    q_ranges = [
        (0, 3, 0, 3), # q0
        (0, 3, 3, 6), # q1
        (3, 6, 0, 3), # q2
        (3, 6, 3, 6)  # q3
    ]
    
    for q in range(4):
        r_start, r_end, c_start, c_end = q_ranges[q]
        
        # Build Quad Mask
        mask = 0
        cells = [] # list of (r, c, global_idx)
        for r in range(r_start, r_end):
            for c in range(c_start, c_end):
                idx = r * 6 + c
                mask |= (1 << idx)
                cells.append((r, c, idx))
        QUAD_MASKS[q] = mask
        
        # Build Rotation Maps (L and R)
        # Relative coordinates (0..2, 0..2)
        # L: (rr, rc) -> (2-rc, rr)
        # R: (rr, rc) -> (rc, 2-rr)
        moves_L = []
        moves_R = []
        
        for r, c, idx in cells:
            rr = r - r_start
            rc = c - c_start
            
            # L
            nrr_L, nrc_L = 2 - rc, rr
            dst_r_L = r_start + nrr_L
            dst_c_L = c_start + nrc_L
            dst_idx_L = dst_r_L * 6 + dst_c_L
            moves_L.append((idx, dst_idx_L))
            
            # R
            nrr_R, nrc_R = rc, 2 - rr
            dst_r_R = r_start + nrr_R
            dst_c_R = c_start + nrc_R
            dst_idx_R = dst_r_R * 6 + dst_c_R
            moves_R.append((idx, dst_idx_R))
            
        ROT_MOVES[(q, 'L')] = moves_L
        ROT_MOVES[(q, 'R')] = moves_R

_init_rotations()

# --- BITBOARD HELPERS ---

def popcount(n):
    return bin(n).count('1')

def check_score(p1_board, p2_board):
    """
    Returns a heuristic score for p1_board against p2_board.
    Scan all WIN_MASKS. 
    If p1 has all 5 bits -> Win (Huge score).
    If mixed -> 0.
    Else count bits.
    """
    score = 0
    
    # Pre-calculated weights
    W5 = 10000000
    W4 = 10000
    W3 = 100
    W2 = 10
    
    p1_won = False
    p2_won = False

    for m in WIN_MASKS:
        # Intersect mask with boards
        i1 = p1_board & m
        i2 = p2_board & m
        
        # If mask matches fully
        if i1 == m: 
            p1_won = True
        if i2 == m:
            p2_won = True
            
        # Heuristic scoring for non-winning lines
        # Determine if line is 'open' (only one player has stones in this 5-window)
        if i1 and not i2:
            cnt = popcount(i1)
            if cnt == 4: score += W4
            elif cnt == 3: score += W3
            elif cnt == 2: score += W2
        elif i2 and not i1:
            cnt = popcount(i2)
            # Weight defense slightly higher to prevent traps
            if cnt == 4: score -= W4 * 1.2
            elif cnt == 3: score -= W3 * 1.2
            elif cnt == 2: score -= W2 * 1.2

    # Resolution of win states (PENTAGO rule: if both win, it's a draw)
    if p1_won and p2_won:
        return 0 # Draw
    if p1_won:
        return W5
    if p2_won:
        return -W5
        
    return score

def get_win_state(p1, p2):
    # 1: p1 win, -1: p2 win, 2: draw, 0: none
    w1 = False
    w2 = False
    for m in WIN_MASKS:
        if (p1 & m) == m: w1 = True
        if (p2 & m) == m: w2 = True
    if w1 and w2: return 2
    if w1: return 1
    if w2: return -1
    return 0

def apply_move_fast(p1, p2, move_idx, q, d_char):
    # Place stone
    new_p1 = p1 | (1 << move_idx)
    new_p2 = p2
    
    # Rotate
    # We need to rotate bits in quad q for both players
    # Mask out the old quadrant
    mask = QUAD_MASKS[q]
    
    # Extract static parts
    p1_static = new_p1 & ~mask
    p2_static = new_p2 & ~mask
    
    # Build rotated parts
    p1_rot = 0
    p2_rot = 0
    
    # Apply mapping
    mapping = ROT_MOVES[(q, d_char)]
    for src, dst in mapping:
        if (new_p1 >> src) & 1:
            p1_rot |= (1 << dst)
        if (new_p2 >> src) & 1:
            p2_rot |= (1 << dst)
            
    return p1_static | p1_rot, p2_static | p2_rot


# --- MAIN POLICY ---

def policy(you, opponent):
    start_time = time.time()
    
    # 1. Parse Input to Bitboards
    my_board = 0
    opp_board = 0
    empty_indices = []
    
    # Assuming standard array interface (list of lists or numpy)
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                my_board |= (1 << (r * 6 + c))
            elif opponent[r][c]:
                opp_board |= (1 << (r * 6 + c))
            else:
                empty_indices.append((r, c, r*6 + c))
                
    # 2. Heuristic Filter / Move Ordering
    # We generate all legal moves and score them at depth 0.
    # A legal move is (place_idx, quad, dir)
    candidates = []
    
    qs = [0, 1, 2, 3]
    ds = ['L', 'R']
    
    # Optimization: If very early game (few stones), limit branching?
    # No, fast Enough.
    
    # Loop all empty spots
    for r, c, idx in empty_indices:
        # Loop all rotations
        for q in qs:
            for d in ds:
                # Apply move
                p1_next, p2_next = apply_move_fast(my_board, opp_board, idx, q, d)
                
                # Immediate check for win
                # Optimization: check win inside apply loop avoids overhead later
                state = get_win_state(p1_next, p2_next)
                
                if state == 1:
                    # Found a winning move. Return immediately.
                    return f"{r+1},{c+1},{q},{d}"
                
                # Heuristic Score
                score = check_score(p1_next, p2_next)
                
                # Add randomness to break ties in openings
                sort_score = score + random.random()
                
                candidates.append({
                    'move_str': f"{r+1},{c+1},{q},{d}",
                    'p1': p1_next,
                    'p2': p2_next,
                    'score': sort_score,
                    'raw_score': score
                })
    
    # Sort candidates descending
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # If we found no moves (shouldn't happen), return dummy
    if not candidates:
        return "1,1,0,L"
        
    # If the best move is nearly a win (score > half win), take it.
    if candidates[0]['raw_score'] > 5000000:
        return candidates[0]['move_str']

    # 3. Alpha-Beta Search (Depth 2)
    # Search top K candidates to refine decision against opponent counter-play
    # Depth 2 means: I moved, now Opponent moves. I want to Maximize (Min(Opponent Score))
    
    best_final_move = candidates[0]['move_str']
    best_final_val = -float('inf')
    
    # Beam width: Check top 16 moves thoroughly. 
    # 16 * 288 (opp replies) ~= 4600 checks. Very easy for Python < 0.5s.
    beam_width = 20
    top_candidates = candidates[:beam_width]
    
    for cand in top_candidates:
        # Time Check
        if time.time() - start_time > 0.85:
            break
            
        p1_after_me = cand['p1']
        p2_after_me = cand['p2']
        
        # Now simulate opponent's best response (Minimizing my score)
        # Opponent places on remaining zeros.
        # Construct empty slots mask for fast iteration?
        # Faster: regenerate empty slots from bitboard? Or just track used?
        # We can detect empty slots by ~(p1 | p2).
        
        occupied = p1_after_me | p2_after_me
        
        # Opponent wants to minimize 'val'
        beta = float('inf') 
        
        # If I forced a Draw, value is 0. 
        # But if 'get_win_state' was 0, game continues.
        # My candidates loop already checked immediate Win/Draw.
        # So here state is 0.
        
        # Opponent move generation
        opp_best_reply_val = float('inf') # We want to minimize this
        
        # Identify empty spots
        # Iterating 36 bits is fast
        moves_checked = 0
        
        forced_break = False
        
        # Dynamic Move Generation for Opponent
        # We only need to find ONE move that kills us (Score < -huge) to prune this candidate
        
        for bit in range(36):
            if not ((occupied >> bit) & 1):
                # Opponent places at 'bit'
                # Opponent rotates q, d
                for q in qs:
                    for d in ds:
                        # Apply opponent move: p2 acts as p1 in function, p1 as p2
                        # apply_move_fast(moving_player, passive_player, ...)
                        # Returns (new_moving, new_passive)
                        op_next, my_next = apply_move_fast(p2_after_me, p1_after_me, bit, q, d)
                        
                        # Evaluate from MY perspective
                        val = check_score(my_next, op_next)
                        
                        if val < opp_best_reply_val:
                            opp_best_reply_val = val
                        
                        # Alpha-Beta-ish Cutoff
                        # If we found a move where I lose heavily, this candidate is bad.
                        # Assuming perfect opponent.
                        if opp_best_reply_val < -5000000:
                            forced_break = True
                            break
                    if forced_break: break
            if forced_break: break
            
        if opp_best_reply_val > best_final_val:
            best_final_val = opp_best_reply_val
            best_final_move = cand['move_str']
            
    return best_final_move
