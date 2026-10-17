
import time
import numpy as np

# --- PRECOMPUTED CONSTANTS & TABLES ---

# 6x6 board indices:
#  0  1  2 |  3  4  5
#  6  7  8 |  9 10 11
# 12 13 14 | 15 16 17
# -------------------
# 18 19 20 | 21 22 23
# 24 25 26 | 27 28 29
# 30 31 32 | 33 34 35

# Winning lines masks (rows, cols, diags of length >= 5)
WIN_MASKS = []

def _generate_win_masks():
    masks = []
    # Rows
    for r in range(6):
        row_bits = 0
        for c in range(6):
            row_bits |= (1 << (r * 6 + c))
        # 5 in a row in a 6-cell row: indices 0..4 and 1..5
        masks.append(row_bits & ~(1 << (r * 6 + 5))) # First 5
        masks.append(row_bits & ~(1 << (r * 6 + 0))) # Last 5
        
    # Cols
    for c in range(6):
        col_bits = 0
        for r in range(6):
            col_bits |= (1 << (r * 6 + c))
        # 5 in a col
        masks.append(col_bits & ~(1 << (5 * 6 + c))) # First 5
        masks.append(col_bits & ~(1 << (0 * 6 + c))) # Last 5
        
    # Diagonals
    # Main diag 1 (0,0 to 5,5): 0, 7, 14, 21, 28, 35
    d1 = sum(1 << (i*7) for i in range(6))
    masks.append(d1 & ~(1 << 35))
    masks.append(d1 & ~(1 << 0))
    
    # Anti diag 1 (0,5 to 5,0): 5, 10, 15, 20, 25, 30
    d2 = sum(1 << (5 + i*5) for i in range(6))
    masks.append(d2 & ~(1 << 30))
    masks.append(d2 & ~(1 << 5))
    
    # Offset diagonals (length 5)
    # (0,1) to (4,5): 1, 8, 15, 22, 29
    masks.append(sum(1 << (1 + i*7) for i in range(5)))
    # (1,0) to (5,4): 6, 13, 20, 27, 34
    masks.append(sum(1 << (6 + i*7) for i in range(5)))
    # (0,4) to (4,0): 4, 9, 14, 19, 24
    masks.append(sum(1 << (4 + i*5) for i in range(5)))
    # (1,5) to (5,1): 11, 16, 21, 26, 31
    masks.append(sum(1 << (11 + i*5) for i in range(5)))
    
    return masks

WIN_MASKS = _generate_win_masks()

# Quadrant masks and shifts
QUAD_INFO = [
    # (mask, list of bit indices in row-major order for 3x3)
    (0, [0, 1, 2, 6, 7, 8, 12, 13, 14]),       # Q0 top-left
    (1, [3, 4, 5, 9, 10, 11, 15, 16, 17]),     # Q1 top-right
    (2, [18, 19, 20, 24, 25, 26, 30, 31, 32]), # Q2 bot-left
    (3, [21, 22, 23, 27, 28, 29, 33, 34, 35])  # Q3 bot-right
]

# Precompute rotation lookup tables: Q_VAL (9 bits) -> ROT_VAL (9 bits)
# Although we work with full board integers, we can extract the 9 bits of a quad,
# perform lookup, and insert back.
# But it's actually faster to use bitwise permutation on the whole board 
# or specific mask logic if implemented efficiently. 
# Given pure Python, a lookup table for the 3x3 pattern is best. 
# There are 2^9 = 512 states per quad.

ROT_TABLES = {} # key: (quad_idx, direction 'L'/'R', 9_bit_int) -> 9_bit_int

def _init_rot_tables():
    # 3x3 indices relative 0..8
    # 0 1 2
    # 3 4 5
    # 6 7 8
    # L (CCW): 0->6, 1->3, 2->0, 3->7, 4->4, 5->1, 6->8, 7->5, 8->2
    map_L = {0:6, 1:3, 2:0, 3:7, 4:4, 5:1, 6:8, 7:5, 8:2}
    # R (CW): 0->2, 1->5, 2->8, 3->1, 4->4, 5->7, 6->0, 7->3, 8->6
    map_R = {0:2, 1:5, 2:8, 3:1, 4:4, 5:7, 6:0, 7:3, 8:6}
    
    for val in range(512):
        # bits of val correspond to indices 0..8
        res_L = 0
        res_R = 0
        for src, dst in map_L.items():
            if (val >> src) & 1:
                res_L |= (1 << dst)
        for src, dst in map_R.items():
            if (val >> src) & 1:
                res_R |= (1 << dst)
                
        ROT_TABLES[('L', val)] = res_L
        ROT_TABLES[('R', val)] = res_R

_init_rot_tables()

# Helper to check win
def check_win(board_int):
    for m in WIN_MASKS:
        if (board_int & m) == m:
            return True
    return False

# Function to rotate a board
# We need to extract bits for the quad, transform, and put back.
def get_rotated_board(board, quad_idx, direction):
    # Get quad definition
    q_mask = 0
    indices = QUAD_INFO[quad_idx][1]
    
    # Extract 9-bit pattern
    pattern = 0
    for i, pos in enumerate(indices):
        if (board >> pos) & 1:
            pattern |= (1 << i)
    
    # Lookup rotated pattern
    new_pattern = ROT_TABLES[(direction, pattern)]
    
    # Clear old quad bits
    # pre-calc mask for quad
    full_q_mask = 0
    for pos in indices:
        full_q_mask |= (1 << pos)
    
    new_board = board & ~full_q_mask
    
    # Set new bits
    for i, pos in enumerate(indices):
        if (new_pattern >> i) & 1:
            new_board |= (1 << pos)
            
    return new_board

def policy(you, opponent):
    """
    Main entry point.
    you, opponent: 6x6 numpy arrays or lists (0-indexed).
    Returns string "r,c,q,d" (1-indexed r,c).
    """
    start_time = time.time()
    
    # 1. Parse board to int
    you_int = 0
    opp_int = 0
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                you_int |= (1 << (r * 6 + c))
            if opponent[r][c]:
                opp_int |= (1 << (r * 6 + c))
                
    full_mask = you_int | opp_int
    
    # Identify empty cells
    empty_cells = []
    # Order empty cells: prefer center, then others
    # Center 16 block: rows 1-4, cols 1-4.
    # Inner 4: 14,15,20,21.
    centers = [14, 15, 20, 21]
    subcenters = [7, 8, 9, 10, 13, 16, 19, 22, 25, 26, 27, 28]
    # create full priority list
    all_indices = list(range(36))
    # sort by priority
    priority = []
    for x in all_indices:
        p = 0
        if x in centers: p = 2
        elif x in subcenters: p = 1
        priority.append((p, x))
    priority.sort(key=lambda x: x[0], reverse=True)
    sorted_indices = [x[1] for x in priority]
    
    for idx in sorted_indices:
        if not ((full_mask >> idx) & 1):
            empty_cells.append(idx)
            
    # Legal Moves: (cell_idx, quad, dir)
    # We won't generate full list to save memory/time, we iterate.
    
    best_move = None
    best_score = -float('inf')
    
    # Pre-calculate quadrants masks for quick rotation
    # (Done in helper)
    
    # STRATEGY: 
    # 1. Check for immediate win.
    # 2. If no immediate win, gather safe moves (where opp cannot win next).
    # 3. Score safe moves by heuristic.
    
    # Phase 1: Check my Immediate Wins
    for cell in empty_cells:
        # Place stone
        y_next = you_int | (1 << cell)
        o_next = opp_int
        
        # Check all 8 rotations
        for q in range(4):
            # Optimization: only rotate if quad is touched or has stones?
            # Pentago requires checking all because remote rotation can align lines.
            for d in ['L', 'R']:
                y_rot = get_rotated_board(y_next, q, d)
                o_rot = get_rotated_board(o_next, q, d)
                
                win_me = check_win(y_rot)
                win_opp = check_win(o_rot)
                
                if win_me and not win_opp:
                    # Found a winning move! Return immediately.
                    r = (cell // 6) + 1
                    c = (cell % 6) + 1
                    return f"{r},{c},{q},{d}"
                    
    # Phase 2: Search for best move preventing opponent win
    
    # To check if opponent can win, we need a fast function
    def can_opponent_win(y_state, o_state):
        # Opponent to move. Only need to find ONE move that wins for them.
        occ = y_state | o_state
        # Check empty cells for opponent
        # We can iterate all empty cells.
        # Micro-optimization: check if opponent has 4-in-a-row or 3-in-a-row already?
        # Just brute force, bitwise is fast.
        for c_idx in range(36):
            if not ((occ >> c_idx) & 1):
                o_test = o_state | (1 << c_idx)
                # Check rotations
                # We can stop early if win found
                for q_i in range(4):
                     # Try both dirs
                     # L
                     o_r = get_rotated_board(o_test, q_i, 'L')
                     if check_win(o_r):
                         y_r = get_rotated_board(y_state, q_i, 'L')
                         if not check_win(y_r): return True # Opp wins cleanly
                     # R
                     o_r = get_rotated_board(o_test, q_i, 'R')
                     if check_win(o_r):
                         y_r = get_rotated_board(y_state, q_i, 'R')
                         if not check_win(y_r): return True
        return False

    # Heuristic score
    def evaluate(y, o):
        score = 0
        # Check lines
        for m in WIN_MASKS:
            y_count = bin(y & m).count('1')
            o_count = bin(o & m).count('1')
            
            if y_count > 0 and o_count == 0:
                # Potential for me
                score += (10 ** y_count)
            elif o_count > 0 and y_count == 0:
                # Potential for opponent
                score -= (10 ** o_count) * 1.2 # slightly higher weight to defense
            # If both have stones, line is dead - 0 value (except for blocking purpose)
        
        # Center bonus
        center_mask = 0x000000
        # Indices 14,15,20,21
        for ci in [14, 15, 20, 21]:
            center_mask |= (1 << ci)
        
        c_y = bin(y & center_mask).count('1')
        c_o = bin(o & center_mask).count('1')
        score += (c_y * 10) - (c_o * 10)
        
        return score

    candidates = []
    
    # Check moves
    count = 0
    time_limit = 0.85
    
    # Fallback move
    default_r = (empty_cells[0] // 6) + 1
    default_c = (empty_cells[0] % 6) + 1
    best_move_str = f"{default_r},{default_c},0,L"
    
    for cell in empty_cells:
        # Check time
        if (count % 10 == 0) and (time.time() - start_time > time_limit):
            break
            
        y_next_base = you_int | (1 << cell)
        
        for q in range(4):
            for d in ['L', 'R']:
                count += 1
                
                # Apply move
                y_final = get_rotated_board(y_next_base, q, d)
                o_final = get_rotated_board(opp_int, q, d)
                
                # We already checked for Immediate Win in Phase 1, so here no move is an immediate win.
                # However, we must ensure we don't accidentally create a win for opponent (draw) or loss.
                
                if check_win(o_final):
                    # This move causes opponent to win (e.g. they had 4, we rotated them to 5).
                    # Since we didn't win (Phase 1 checked), this is a loss. Skip.
                    continue
                
                # Now check if opponent can win on their turn
                # This is the "Depth 2" lookahead
                # If time is critical, we might skip this for some branches, but it's crucial for defense.
                
                # Score this state immediately first
                # Optimization: if heuristic is terrible, maybe don't check deep defense? 
                # No, defense is priority.
                
                is_safe = True
                
                # Only run expensive 'can_opponent_win' if we have time
                if time.time() - start_time < time_limit:
                    if can_opponent_win(y_final, o_final):
                        is_safe = False
                
                heur_val = evaluate(y_final, o_final)
                
                # Penalize unsafe moves heavily
                if not is_safe:
                    heur_val -= 1000000
                
                # Update best
                if heur_val > best_score:
                    best_score = heur_val
                    r = (cell // 6) + 1
                    c = (cell % 6) + 1
                    best_move_str = f"{r},{c},{q},{d}"
    
    return best_move_str
