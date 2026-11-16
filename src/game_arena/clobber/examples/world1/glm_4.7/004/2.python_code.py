
import random
import time

# Board dimensions
ROWS = 5
COLS = 6

# Precompute neighbors for every cell index (0-29) for fast move generation
# NEIGHBORS[idx] = list of (neighbor_idx, direction_char)
NEIGHBORS = {}

def init_neighbors():
    dirs = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            adj = []
            for dr, dc, d in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    adj.append((nr * COLS + nc, d))
            NEIGHBORS[idx] = adj

init_neighbors()

def list_to_mask(board_list):
    """
    Converts the input board (list of lists or flat list) to a bitmask integer.
    Bit i is 1 if there is a piece at index i (row-major order).
    """
    if not board_list:
        return 0
    
    # Check if input is a 2D list (list of lists)
    if isinstance(board_list[0], list):
        mask = 0
        for r in range(len(board_list)):
            row = board_list[r]
            for c in range(len(row)):
                if row[c]:
                    mask |= 1 << (r * COLS + c)
        return mask
    else:
        # Assume flat list
        mask = 0
        for i, val in enumerate(board_list):
            if val:
                mask |= 1 << i
        return mask

def get_moves(my_mask, opp_mask):
    """
    Returns a list of legal moves (src_idx, dst_idx, direction_char).
    """
    moves = []
    m = my_mask
    while m:
        lsb = m & -m
        src = lsb.bit_length() - 1
        m ^= lsb
        
        for dst, d in NEIGHBORS[src]:
            if (opp_mask >> dst) & 1:
                moves.append((src, dst, d))
    return moves

def evaluate(my_mask, opp_mask):
    """
    Heuristic evaluation: Difference in mobility.
    Positive is good for the player whose turn it is.
    """
    my_moves = len(get_moves(my_mask, opp_mask))
    opp_moves = len(get_moves(opp_mask, my_mask))
    return my_moves - opp_moves

def search(my_mask, opp_mask, depth, alpha, beta):
    """
    Minimax with Alpha-Beta pruning.
    """
    moves = get_moves(my_mask, opp_mask)
    
    # Terminal state: no legal moves
    if not moves:
        return -100000 + depth # Prefer losing later
    
    if depth == 0:
        return evaluate(my_mask, opp_mask)
    
    # Heuristic sorting: prioritize moves that capture pieces with higher mobility
    # (pieces that are attacking many of our pieces)
    moves.sort(key=lambda mv: sum(1 for n, _ in NEIGHBORS[mv[1]] if (my_mask >> n) & 1), reverse=True)

    best_val = -float('inf')
    for src, dst, d in moves:
        src_bit = 1 << src
        dst_bit = 1 << dst
        
        # Apply move
        # Remove my piece from src, add to dst. Remove opp piece from dst.
        new_my = (my_mask ^ src_bit) | dst_bit
        new_opp = opp_mask ^ dst_bit
        
        val = -search(new_opp, new_my, depth - 1, -beta, -alpha)
        
        if val > best_val:
            best_val = val
        if val > alpha:
            alpha = val
        if val >= beta:
            break
            
    return best_val

def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.time()
    
    # Convert inputs to bitmasks
    my_mask = list_to_mask(you)
    opp_mask = list_to_mask(opponent)
    
    # Generate all legal moves
    moves = get_moves(my_mask, opp_mask)
    
    # Fallback if no moves (shouldn't happen in a playable game, but required for safety)
    if not moves:
        return "0,0,U"
    
    # Start with a random move as a baseline
    best_move = random.choice(moves)
    
    # Iterative deepening
    # Try depths 1 through 5, stopping if time runs out
    max_depth = 5
    for depth in range(1, max_depth + 1):
        # Check time limit (leave some buffer)
        if time.time() - start_time > 0.95:
            break
        
        current_best_val = -float('inf')
        current_best_move = best_move
        
        # Sort moves heuristically to improve pruning at root
        # We reuse the sorting logic from search or just shuffle/random
        # Using the same heuristic: capture active pieces
        sorted_moves = sorted(moves, key=lambda mv: sum(1 for n, _ in NEIGHBORS[mv[1]] if (my_mask >> n) & 1), reverse=True)
        
        for src, dst, d in sorted_moves:
            src_bit = 1 << src
            dst_bit = 1 << dst
            
            new_my = (my_mask ^ src_bit) | dst_bit
            new_opp = opp_mask ^ dst_bit
            
            val = -search(new_opp, new_my, depth - 1, -float('inf'), float('inf'))
            
            if val > current_best_val:
                current_best_val = val
                current_best_move = (src, dst, d)
                
                # If we found a winning move, stop searching
                if val > 10000:
                    best_move = current_best_move
                    return f"{best_move[0] // COLS},{best_move[0] % COLS},{best_move[2]}"
        
        if current_best_val > -float('inf'):
            best_move = current_best_move

    # Return the best move found in the format "row,col,dir"
    r = best_move[0] // COLS
    c = best_move[0] % COLS
    return f"{r},{c},{best_move[2]}"
