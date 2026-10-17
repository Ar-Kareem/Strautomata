
import numpy as np

# Directions for bitwise operations (shift amounts)
# Board layout: bit 0 is a1, bit 7 is h1, bit 63 is h8.
# North: -8, South: +8, East: +1, West: -1
# NE: -7, NW: -9, SE: +9, SW: +7
DIRECTIONS = [-9, -8, -7, -1, 1, 7, 8, 9]

# Masks to prevent wrapping around edges during bitwise shifts
MASK_L = 0xfefefefefefefefe  # Clears column 0 (a-file)
MASK_R = 0x7f7f7f7f7f7f7f7f  # Clears column 7 (h-file)
MASK_FULL = 0xffffffffffffffff

# Precomputed masks for shifts
SHIFT_MASKS = {
    -9: MASK_L,  # NW
    -8: MASK_FULL, # N
    -7: MASK_R,  # NE
    -1: MASK_L,  # W
    1: MASK_R,   # E
    7: MASK_L,   # SW
    8: MASK_FULL, # S
    9: MASK_R    # SE
}

# Positional weights for heuristic evaluation
WEIGHTS = [
    100, -20,  10,   5,   5,  10, -20, 100,
    -20, -50,  -2,  -2,  -2,  -2, -50, -20,
     10,  -2,   1,   1,   1,   1,  -2,  10,
      5,  -2,   1,   1,   1,   1,  -2,   5,
      5,  -2,   1,   1,   1,   1,  -2,   5,
     10,  -2,   1,   1,   1,   1,  -2,  10,
    -20, -50,  -2,  -2,  -2,  -2, -50, -20,
    100, -20,  10,   5,   5,  10, -20, 100
]
# Convert to numpy array for fast operations
WEIGHTS_NP = np.array(WEIGHTS, dtype=np.int32)

def board_to_int(board_arr):
    """Converts an 8x8 numpy array (0/1) to a 64-bit integer."""
    return int(board_arr.flatten().dot(1 << np.arange(64, dtype=np.uint64)))

def get_valid_moves(my_board, opp_board):
    """Returns a list of valid move indices (0-63) for the current player."""
    empty = ~(my_board | opp_board) & MASK_FULL
    moves = 0
    
    for shift in DIRECTIONS:
        # Candidates are opponent pieces adjacent to my pieces in this direction
        # We shift 'my_board' in 'direction' to find neighbors
        if shift > 0:
            candidates = opp_board & ((my_board << shift) & SHIFT_MASKS[shift])
            # Propagate through opponent pieces
            while candidates:
                candidates = opp_board & ((candidates << shift) & SHIFT_MASKS[shift])
            # Valid moves are empty spots at the end of the chain
            valid = empty & ((candidates << shift) & SHIFT_MASKS[shift])
        else:
            s = -shift
            candidates = opp_board & ((my_board >> s) & SHIFT_MASKS[shift])
            while candidates:
                candidates = opp_board & ((candidates >> s) & SHIFT_MASKS[shift])
            valid = empty & ((candidates >> s) & SHIFT_MASKS[shift])
        
        moves |= valid
        
    # Convert bitboard of moves to list of indices
    move_indices = []
    m = moves
    while m:
        # Isolate lowest set bit
        lsb = m & -m
        idx = (lsb.bit_length() - 1)
        move_indices.append(idx)
        m &= m - 1
    return move_indices

def make_move(my_board, opp_board, move_idx):
    """Applies a move and returns the new (my_board, opp_board)."""
    move_bit = 1 << move_idx
    flipped = 0
    
    for shift in DIRECTIONS:
        line_flipped = 0
        # Check neighbor in direction 'shift'
        if shift > 0:
            current = (move_bit << shift) & SHIFT_MASKS[shift]
        else:
            current = (move_bit >> (-shift)) & SHIFT_MASKS[shift]
            
        # Traverse while we see opponent pieces
        while current & opp_board:
            line_flipped |= current
            if shift > 0:
                current = (current << shift) & SHIFT_MASKS[shift]
            else:
                current = (current >> (-shift)) & SHIFT_MASKS[shift]
        
        # If we end at our own piece, the line is valid
        if current & my_board:
            flipped |= line_flipped
            
    new_my_board = my_board | move_bit | flipped
    new_opp_board = opp_board & ~flipped
    return new_my_board, new_opp_board

def evaluate(my_board, opp_board):
    """Heuristic evaluation of the board state."""
    my_bits = np.array([(my_board >> i) & 1 for i in range(64)], dtype=np.int32)
    opp_bits = np.array([(opp_board >> i) & 1 for i in range(64)], dtype=np.int32)
    
    # 1. Positional Score
    pos_score = np.sum(WEIGHTS_NP * my_bits) - np.sum(WEIGHTS_NP * opp_bits)
    
    # 2. Mobility Score
    my_moves = len(get_valid_moves(my_board, opp_board))
    opp_moves = len(get_valid_moves(opp_board, my_board))
    mob_score = 0
    if my_moves + opp_moves > 0:
        mob_score = 10 * (my_moves - opp_moves)
        
    return pos_score + mob_score

def alphabeta(my_board, opp_board, depth, alpha, beta, maximizing):
    """Minimax with Alpha-Beta pruning."""
    my_moves = get_valid_moves(my_board, opp_board)
    opp_moves = get_valid_moves(opp_board, my_board) # Check if opponent can move later
    
    # Terminal state: game over
    if not my_moves and not opp_moves:
        my_count = bin(my_board).count('1')
        opp_count = bin(opp_board).count('1')
        if my_count > opp_count:
            return 10000
        elif my_count < opp_count:
            return -10000
        else:
            return 0
            
    # Depth limit reached
    if depth == 0:
        return evaluate(my_board, opp_board)
        
    # Current player must pass
    if not my_moves:
        return alphabeta(opp_board, my_board, depth, alpha, beta, not maximizing)
        
    # Move ordering: prioritize corners
    CORNERS = {0, 7, 56, 63}
    my_moves.sort(key=lambda x: -1000 if x in CORNERS else 0)
    
    if maximizing:
        max_eval = -float('inf')
        for move in my_moves:
            new_me, new_opp = make_move(my_board, opp_board, move)
            # Swap roles for next depth
            eval_val = alphabeta(new_opp, new_me, depth - 1, alpha, beta, False)
            if eval_val > max_eval:
                max_eval = eval_val
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in my_moves:
            new_me, new_opp = make_move(my_board, opp_board, move)
            eval_val = alphabeta(new_opp, new_me, depth - 1, alpha, beta, True)
            if eval_val < min_eval:
                min_eval = eval_val
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert numpy arrays to bitboards
    my_board = board_to_int(you)
    opp_board = board_to_int(opponent)
    
    # Determine search depth based on game progress
    empty_count = 64 - bin(my_board).count('1') - bin(opp_board).count('1')
    if empty_count <= 12:
        depth = 6 # Deeper search for endgame
    else:
        depth = 4 # Standard depth
        
    valid_moves = get_valid_moves(my_board, opp_board)
    
    if not valid_moves:
        return "pass"
    
    best_move = -1
    best_value = -float('inf')
    
    # Move ordering for root
    CORNERS = {0, 7, 56, 63}
    valid_moves.sort(key=lambda x: -1000 if x in CORNERS else 0)
    
    for move in valid_moves:
        new_me, new_opp = make_move(my_board, opp_board, move)
        # We are maximizing, next is minimizing (opponent's turn)
        # Note: alphabeta expects (current_player, opponent)
        # After make_move, our pieces are in new_me, opponent in new_opp.
        # Next turn is opponent's. So we call with (new_opp, new_me)
        val = alphabeta(new_opp, new_me, depth, -float('inf'), float('inf'), False)
        
        if val > best_value:
            best_value = val
            best_move = move
            
    # Convert index to "a1".."h8"
    col = best_move % 8
    row = best_move // 8
    return chr(ord('a') + col) + str(row + 1)

