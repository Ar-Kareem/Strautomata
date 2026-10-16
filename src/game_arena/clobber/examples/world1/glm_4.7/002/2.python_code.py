
import math
import random

# Board Constants
ROWS = 5
COLS = 6
SIZE = 30

# Bitmask Precomputation for boundaries
# Column 0 (bits: 0, 6, 12, 18, 24) - Cannot move Left from here
MASK_COL_0 = sum(1 << (r * COLS) for r in range(ROWS))
# Column 5 (bits: 5, 11, 17, 23, 29) - Cannot move Right from here
MASK_COL_5 = sum(1 << (r * COLS + COLS - 1) for r in range(ROWS))
# Row 0 (bits: 0-5) - Cannot move Up from here
MASK_ROW_0 = (1 << COLS) - 1
# Row 4 (bits: 24-29) - Cannot move Down from here
MASK_ROW_4 = sum(1 << ((ROWS - 1) * COLS + c) for c in range(COLS))

def get_mask(board):
    """
    Converts the input board (list of lists or flat list) to a 30-bit integer mask.
    """
    mask = 0
    if isinstance(board[0], list):
        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c]:
                    mask |= 1 << (r * COLS + c)
    else:
        for i, val in enumerate(board):
            if val:
                mask |= 1 << i
    return mask

def get_moves(p1_mask, p2_mask):
    """
    Generates all legal moves for player p1 against p2 using bitboard operations.
    Returns a list of (start_index, dest_index) tuples.
    """
    moves = []
    
    # Right moves: (p1 << 1) targets p2, ensure not wrapping from col 5
    targets = ((p1_mask & ~MASK_COL_5) << 1) & p2_mask
    t = targets
    while t:
        lsb = t & -t
        dest = lsb.bit_length() - 1
        start = dest - 1
        moves.append((start, dest))
        t -= lsb
        
    # Left moves: (p1 >> 1) targets p2, ensure not wrapping from col 0
    targets = ((p1_mask & ~MASK_COL_0) >> 1) & p2_mask
    t = targets
    while t:
        lsb = t & -t
        dest = lsb.bit_length() - 1
        start = dest + 1
        moves.append((start, dest))
        t -= lsb
        
    # Down moves: (p1 << 6) targets p2, ensure not wrapping from row 4
    targets = ((p1_mask & ~MASK_ROW_4) << COLS) & p2_mask
    t = targets
    while t:
        lsb = t & -t
        dest = lsb.bit_length() - 1
        start = dest - COLS
        moves.append((start, dest))
        t -= lsb
        
    # Up moves: (p1 >> 6) targets p2, ensure not wrapping from row 0
    targets = ((p1_mask & ~MASK_ROW_0) >> COLS) & p2_mask
    t = targets
    while t:
        lsb = t & -t
        dest = lsb.bit_length() - 1
        start = dest + COLS
        moves.append((start, dest))
        t -= lsb
        
    return moves

def apply_move(p1_mask, p2_mask, start, dest):
    """
    Applies a move to the bitboards.
    Returns (new_p1_mask, new_p2_mask).
    """
    # Remove piece from start, capture piece at dest, place piece at dest
    new_p1 = p1_mask & ~(1 << start)
    new_p2 = p2_mask & ~(1 << dest)
    new_p1 |= (1 << dest)
    return new_p1, new_p2

def get_mobility(p1, p2):
    """Counts the number of legal moves for p1 against p2."""
    return bin(((p1 & ~MASK_COL_5) << 1) & p2).count('1') + \
           bin(((p1 & ~MASK_COL_0) >> 1) & p2).count('1') + \
           bin(((p1 & ~MASK_ROW_4) << COLS) & p2).count('1') + \
           bin(((p1 & ~MASK_ROW_0) >> COLS) & p2).count('1')

def evaluate(p1, p2):
    """
    Evaluation function. 
    Positive score is good for the player associated with p1.
    Heuristic: Mobility Difference.
    """
    return get_mobility(p1, p2) - get_mobility(p2, p1)

def minimax(p1, p2, depth, alpha, beta, is_maximizing):
    if depth == 0:
        return evaluate(p1, p2)

    # Generate moves for the player whose turn it is
    current_player_mask = p1 if is_maximizing else p2
    opponent_mask = p2 if is_maximizing else p1
    moves = get_moves(current_player_mask, opponent_mask)
    
    if not moves:
        # If no moves, the current player loses
        return -100000 if is_maximizing else 100000

    if is_maximizing:
        max_eval = -math.inf
        for start, dest in moves:
            np1, np2 = apply_move(p1, p2, start, dest)
            eval_score = minimax(np1, np2, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for start, dest in moves:
            # Opponent moves: swap roles in apply_move
            np2, np1 = apply_move(p2, p1, start, dest)
            eval_score = minimax(np1, np2, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(you, opponent):
    # 1. Parse Input
    p1 = get_mask(you)
    p2 = get_mask(opponent)
    
    # 2. Generate Legal Moves
    moves = get_moves(p1, p2)
    
    # 3. Check for terminal state or single move
    if not moves:
        # This state implies we lost, but we must return a string to avoid disqualification error.
        # Return a dummy move if possible, though game should be over.
        return "0,0,R"
        
    if len(moves) == 1:
        s, d = moves[0]
        r, c = divmod(s, COLS)
        diff = d - s
        dr = 'R' if diff == 1 else 'L' if diff == -1 else 'D' if diff == COLS else 'U'
        return f"{r},{c},{dr}"
    
    # 4. Search for best move
    # Sort moves by a simple greedy heuristic to improve Alpha-Beta pruning
    def greedy_score(move):
        s, d = move
        n1, n2 = apply_move(p1, p2, s, d)
        return evaluate(n1, n2)
    
    moves.sort(key=greedy_score, reverse=True)
    
    best_move = moves[0]
    # Iterative Deepening up to depth 4 (3 is safer for 1s limit, 4 if fast)
    # Using a fixed reasonable depth is more consistent for 1s limit
    search_depth = 3 
    
    best_val = -math.inf
    alpha = -math.inf
    beta = math.inf
    
    for start, dest in moves:
        np1, np2 = apply_move(p1, p2, start, dest)
        val = minimax(np1, np2, search_depth, alpha, beta, False)
        
        if val > best_val:
            best_val = val
            best_move = (start, dest)
        
        alpha = max(alpha, val)
    
    # 5. Convert best move to string
    s, d = best_move
    r, c = divmod(s, COLS)
    diff = d - s
    if diff == 1: direction = 'R'
    elif diff == -1: direction = 'L'
    elif diff == COLS: direction = 'D'
    else: direction = 'U'
    
    return f"{r},{c},{direction}"
