
import time

# Precompute adjacency for the 5x6 board to speed up move generation.
# Logic: Map flattened index 0..29 to neighbors [(neighbor_idx, direction_char), ...]
_ADJ = [[] for _ in range(30)]
for r in range(5):
    for c in range(6):
        idx = r * 6 + c
        # Up
        if r > 0: _ADJ[idx].append((idx - 6, 'U'))
        # Down
        if r < 4: _ADJ[idx].append((idx + 6, 'D'))
        # Left
        if c > 0: _ADJ[idx].append((idx - 1, 'L'))
        # Right
        if c < 5: _ADJ[idx].append((idx + 1, 'R'))

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Determines the next move for Clobber on a 5x6 grid.
    
    Args:
        you: 5x6 array (or flattened list) where 1 indicates current player's piece.
        opponent: 5x6 array (or flattened list) where 1 indicates opponent's piece.
        
    Returns:
        A formatted move string 'row,col,dir'.
    """
    start_time = time.time()
    # Leave a small buffer to ensure we return before the 1s hard limit
    time_limit = 0.95

    # --- Helper: Parse Input to Bitmasks ---
    def to_mask(grid):
        mask = 0
        # Handle different input formats:
        # 1. Numpy array (has .flatten())
        # 2. List of Lists
        # 3. Flat list
        flat = []
        try:
            if hasattr(grid, 'flatten'):
                flat = grid.flatten().tolist()
            elif isinstance(grid, list) and len(grid) == 5 and isinstance(grid[0], list):
                flat = [x for row in grid for x in row]
            else:
                flat = grid
        except:
            flat = grid
            
        for i, val in enumerate(flat):
            if val == 1:
                mask |= (1 << i)
        return mask

    my_mask = to_mask(you)
    op_mask = to_mask(opponent)

    # --- Helper: Move Generation ---
    def get_moves(m_mask, o_mask):
        """Generates list of (move_string, new_my_mask, new_op_mask)."""
        moves = []
        # Iterate over all pieces of current player
        temp = m_mask
        while temp:
            # Extract Lowest Set Bit Index
            p = temp & -temp
            from_idx = p.bit_length() - 1
            temp ^= p # Clear this bit to process next
            
            # Check neighbors
            for to_idx, d_char in _ADJ[from_idx]:
                # Check if destination has an opponent piece
                if (o_mask >> to_idx) & 1:
                    # Valid Capture:
                    # - Remove my piece from 'from_idx'
                    # - Add my piece to 'to_idx'
                    # - Remove opponent piece from 'to_idx'
                    nm = (m_mask ^ (1 << from_idx)) | (1 << to_idx)
                    no = o_mask ^ (1 << to_idx)
                    
                    r, c = divmod(from_idx, 6)
                    moves.append((f"{r},{c},{d_char}", nm, no))
        return moves

    # --- Helper: Heuristic ---
    def evaluate(m_mask, o_mask):
        """Scores position based on mobility difference."""
        # Count my moves
        m_mob = 0
        t = m_mask
        while t:
            p = t & -t
            idx = p.bit_length() - 1
            t ^= p
            for ni, _ in _ADJ[idx]:
                if (o_mask >> ni) & 1: m_mob += 1
        
        # Count opponent moves
        o_mob = 0
        t = o_mask
        while t:
            p = t & -t
            idx = p.bit_length() - 1
            t ^= p
            for ni, _ in _ADJ[idx]:
                if (m_mask >> ni) & 1: o_mob += 1
                
        return m_mob - o_mob

    # --- Transposition Table ---
    # Key: (my_mask, op_mask) -> Value: (depth, score, flag, best_move)
    # Flags: 0=Exact, 1=LowerBound, 2=UpperBound
    tt = {}

    # --- Search Algorithm: Negamax with Alpha-Beta ---
    def search(m, o, depth, alpha, beta):
        # Time Check
        if (time.time() - start_time) > time_limit:
            return None, None

        # TT Lookup
        tt_key = (m, o)
        if tt_key in tt:
            t_depth, t_val, t_flag, t_move = tt[tt_key]
            if t_depth >= depth:
                if t_flag == 0: return t_val, t_move
                if t_flag == 1 and t_val >= beta: return t_val, t_move
                if t_flag == 2 and t_val <= alpha: return t_val, t_move

        # Generate Moves
        moves = get_moves(m, o)
        
        # Terminal Node: No moves = Loss
        if not moves:
            # Score loss. Prefer losing later (add depth to negative score)
            return -10000 + (20 - depth), None

        # Leaf Node: Heuristic
        if depth == 0:
            return evaluate(m, o), moves[0][0]

        best_val = -float('inf')
        best_move = moves[0][0]
        alpha_orig = alpha

        # Iterate moves
        for m_str, nm, no in moves:
            # Recursive call:
            # Swap roles: (no, nm). Negate result.
            val, _ = search(no, nm, depth - 1, -beta, -alpha)
            
            if val is None: return None, None # Propagate timeout
            val = -val

            if val > best_val:
                best_val = val
                best_move = m_str
            
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break # Cutoff
        
        # Store in TT
        flag = 0
        if best_val <= alpha_orig: flag = 2 # Uppper bound
        elif best_val >= beta: flag = 1 # Lower bound
        
        tt[tt_key] = (depth, best_val, flag, best_move)
        return best_val, best_move

    # --- Iterative Deepening Loop ---
    
    # Get initial moves to ensure we have a fallback
    root_moves = get_moves(my_mask, op_mask)
    if not root_moves:
        return "0,0,U" # Should not happen if game is not already over
    
    best_move_found = root_moves[0][0]
    
    # Search from depth 1 upwards
    for d in range(1, 30):
        val, move = search(my_mask, op_mask, d, -float('inf'), float('inf'))
        
        if val is None:
            break # Timed out, use previous best move
            
        best_move_found = move
        
        # If we see a forced win (high positive score), we can stop early
        if val > 9000:
            break
            
    return best_move_found
