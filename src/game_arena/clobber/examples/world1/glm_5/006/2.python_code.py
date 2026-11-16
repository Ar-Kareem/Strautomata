
import time

# Constants
ROWS = 5
COLS = 6
TIME_LIMIT = 0.95

# Precompute masks for valid source squares for moves
# Right move: source col < 5
# Left move: source col > 0
# Down move: source row < 4
# Up move: source row > 0
MASK_R_SRC = 0
MASK_L_SRC = 0
MASK_D_SRC = 0
MASK_U_SRC = 0

for r in range(ROWS):
    for c in range(COLS):
        idx = r * COLS + c
        bit = 1 << idx
        if c < COLS - 1: MASK_R_SRC |= bit
        if c > 0:        MASK_L_SRC |= bit
        if r < ROWS - 1: MASK_D_SRC |= bit
        if r > 0:        MASK_U_SRC |= bit

def popcount(n):
    return bin(n).count('1')

def generate_moves_state(curr, other):
    """
    Generates a list of moves for the current player.
    Returns a list of tuples: (new_curr, new_other, from_idx, to_idx)
    """
    moves = []
    
    # Right moves: curr -> curr << 1 (check target in other, check source mask)
    # Target is at curr_idx + 1.
    targets_r = (curr << 1) & other & MASK_R_SRC
    t = targets_r
    while t:
        lsb = t & -t
        t_idx = (lsb.bit_length() - 1)
        s_idx = t_idx - 1
        # Apply move: clear source, set target, clear opponent target
        # new_curr = (curr ^ (1 << s_idx)) | (1 << t_idx) -> curr & ~src | tgt
        # new_other = other & ~(1 << t_idx)
        nc = (curr & ~(1 << s_idx)) | (1 << t_idx)
        no = other & ~(1 << t_idx)
        moves.append((nc, no, s_idx, t_idx))
        t ^= lsb

    # Left moves: curr -> curr >> 1
    targets_l = (curr >> 1) & other & MASK_L_SRC
    t = targets_l
    while t:
        lsb = t & -t
        t_idx = (lsb.bit_length() - 1)
        s_idx = t_idx + 1
        nc = (curr & ~(1 << s_idx)) | (1 << t_idx)
        no = other & ~(1 << t_idx)
        moves.append((nc, no, s_idx, t_idx))
        t ^= lsb

    # Down moves: curr -> curr << 6
    targets_d = (curr << COLS) & other & MASK_D_SRC
    t = targets_d
    while t:
        lsb = t & -t
        t_idx = (lsb.bit_length() - 1)
        s_idx = t_idx - COLS
        nc = (curr & ~(1 << s_idx)) | (1 << t_idx)
        no = other & ~(1 << t_idx)
        moves.append((nc, no, s_idx, t_idx))
        t ^= lsb

    # Up moves: curr -> curr >> 6
    targets_u = (curr >> COLS) & other & MASK_U_SRC
    t = targets_u
    while t:
        lsb = t & -t
        t_idx = (lsb.bit_length() - 1)
        s_idx = t_idx + COLS
        nc = (curr & ~(1 << s_idx)) | (1 << t_idx)
        no = other & ~(1 << t_idx)
        moves.append((nc, no, s_idx, t_idx))
        t ^= lsb

    return moves

def evaluate(curr, other):
    # Mobility heuristic: difference in available moves
    # My mobility
    m_r = (curr << 1) & other & MASK_R_SRC
    m_l = (curr >> 1) & other & MASK_L_SRC
    m_d = (curr << COLS) & other & MASK_D_SRC
    m_u = (curr >> COLS) & other & MASK_U_SRC
    my_mob = popcount(m_r | m_l | m_d | m_u)

    # Opponent mobility (moves 'other' can make on 'curr')
    o_r = (other << 1) & curr & MASK_R_SRC
    o_l = (other >> 1) & curr & MASK_L_SRC
    o_d = (other << COLS) & curr & MASK_D_SRC
    o_u = (other >> COLS) & curr & MASK_U_SRC
    opp_mob = popcount(o_r | o_l | o_d | o_u)

    return my_mob - opp_mob

def negamax(curr, other, depth, alpha, beta):
    # Check for loss (no moves)
    # We can integrate this into the loop check to save one generation
    # But checking mobility bits is fast
    moves_mask = ((curr << 1) & other & MASK_R_SRC) | \
                 ((curr >> 1) & other & MASK_L_SRC) | \
                 ((curr << COLS) & other & MASK_D_SRC) | \
                 ((curr >> COLS) & other & MASK_U_SRC)
    
    if moves_mask == 0:
        return -100000 + (10 - depth) # Loss penalty (sooner loss is worse)

    if depth == 0:
        return evaluate(curr, other)

    # Generate moves
    # We could optimize by using the masks directly, but let's use the generator
    # Since we already computed masks, we can pass them?
    # For simplicity and speed, just call the generator.
    moves = generate_moves_state(curr, other)
    
    best_score = -float('inf')
    
    for nc, no, s, t in moves:
        score = -negamax(no, nc, depth - 1, -beta, -alpha)
        
        if score > best_score:
            best_score = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
            
    return best_score

def policy(you, opponent):
    start_time = time.time()
    
    # Convert to bitboard
    me_b = 0
    opp_b = 0
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            if you[r][c] == 1:
                me_b |= (1 << idx)
            if opponent[r][c] == 1:
                opp_b |= (1 << idx)
    
    # Generate initial moves to check count and handle 1-move case
    initial_moves = generate_moves_state(me_b, opp_b)
    
    if not initial_moves:
        return "0,0,U" # Should not happen if game isn't over
    
    # If only 1 legal move, return it immediately
    if len(initial_moves) == 1:
        _, _, s_idx, t_idx = initial_moves[0]
        r, c = s_idx // COLS, s_idx % COLS
        tr, tc = t_idx // COLS, t_idx % COLS
        d = 'U'
        if tc > c: d = 'R'
        elif tc < c: d = 'L'
        elif tr > r: d = 'D'
        return f"{r},{c},{d}"
    
    best_move = initial_moves[0] # Default
    
    # Iterative Deepening
    for depth in range(1, 20):
        # Time check
        if time.time() - start_time > TIME_LIMIT:
            break
        
        best_score = -float('inf')
        current_best_move = best_move # Use previous best for ordering if needed, here just fallback
        
        # Basic move ordering: use previous best move?
        # Let's try the moves in the order generated for simplicity.
        # To improve, we could sort `initial_moves` based on previous scores if we stored them.
        # For now, simple loop.
        
        found_move_in_depth = False
        
        # Try previous best move first (simple optimization)
        # Move `best_move` to front of iteration
        ordered_moves = [best_move] + [m for m in initial_moves if m != best_move]
        
        for nc, no, s_idx, t_idx in ordered_moves:
            if time.time() - start_time > TIME_LIMIT:
                break
                
            score = -negamax(no, nc, depth - 1, -float('inf'), -best_score)
            
            if score > best_score:
                best_score = score
                current_best_move = (nc, no, s_idx, t_idx)
                found_move_in_depth = True
        
        if found_move_in_depth:
            best_move = current_best_move
        else:
            # Ran out of time or failed
            break
            
    s_idx, t_idx = best_move[2], best_move[3]
    r, c = s_idx // COLS, s_idx % COLS
    tr, tc = t_idx // COLS, t_idx % COLS
    
    d = 'U'
    if tc > c: d = 'R'
    elif tc < c: d = 'L'
    elif tr > r: d = 'D'
    
    return f"{r},{c},{d}"
