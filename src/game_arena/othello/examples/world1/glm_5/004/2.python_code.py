
import numpy as np
import sys

# Increase recursion depth just in case for deep endgames
sys.setrecursionlimit(2000)

# Piece-Square Table (PST) for evaluation
# Values are based on standard Othello strategy:
# Corners are highly valuable. Squares adjacent to corners are dangerous.
# Edges are generally good.
_WEIGHTS = [
    100, -20,  10,   5,   5,  10, -20, 100,
    -20, -50,  -2,  -2,  -2,  -2, -50, -20,
     10,  -2,   1,   1,   1,   1,  -2,  10,
      5,  -2,   1,   1,   1,   1,  -2,   5,
      5,  -2,   1,   1,   1,   1,  -2,   5,
     10,  -2,   1,   1,   1,   1,  -2,  10,
    -20, -50,  -2,  -2,  -2,  -2, -50, -20,
    100, -20,  10,   5,   5,  10, -20, 100
]

# Directions for checking valid moves (dr, dc)
_DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

def get_valid_moves(me, opp):
    """Returns a list of valid moves (index, flipped_bits) for the current player."""
    moves = []
    empty = ~(me | opp) & 0xFFFFFFFFFFFFFFFF
    
    # Iterate through each empty square
    # Using bit operations to find indices of empty squares
    e = empty
    while e:
        lsb = e & -e
        idx = (lsb.bit_length() - 1)
        e ^= lsb
        
        r, c = divmod(idx, 8)
        flipped = 0
        
        # Check all 8 directions
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            line = 0
            
            # Traverse while we see opponent pieces
            while 0 <= nr < 8 and 0 <= nc < 8:
                n_idx = nr * 8 + nc
                n_bit = 1 << n_idx
                
                if opp & n_bit:
                    line |= n_bit
                elif me & n_bit:
                    # Found our own piece, line is valid
                    flipped |= line
                    break
                else:
                    # Empty square, line invalid
                    break
                
                nr += dr
                nc += dc
            
        if flipped:
            moves.append((idx, flipped))
            
    return moves

def evaluate(me, opp):
    """Static evaluation function based on PST weights."""
    score = 0
    bits = me
    while bits:
        b = bits & -bits
        idx = b.bit_length() - 1
        score += _WEIGHTS[idx]
        bits -= b
        
    bits = opp
    while bits:
        b = bits & -bits
        idx = b.bit_length() - 1
        score -= _WEIGHTS[idx]
        bits -= b
        
    return score

def negamax(me, opp, depth, alpha, beta):
    """Negamax search with alpha-beta pruning."""
    moves = get_valid_moves(me, opp)
    
    # Game Over or Pass
    if not moves:
        if not get_valid_moves(opp, me):
            # Terminal state: return exact difference scaled
            me_c = bin(me).count('1')
            opp_c = bin(opp).count('1')
            if me_c > opp_c: return 10000
            if me_c < opp_c: return -10000
            return 0
        # Pass: switch players
        return -negamax(opp, me, depth, -beta, -alpha)
    
    if depth == 0:
        return evaluate(me, opp)
    
    # Move ordering: try promising moves first (corners, high weight)
    moves.sort(key=lambda x: _WEIGHTS[x[0]], reverse=True)
    
    for idx, flipped in moves:
        # Apply move
        new_me = me | (1 << idx) | flipped
        new_opp = opp & ~flipped
        
        val = -negamax(new_opp, new_me, depth - 1, -beta, -alpha)
        
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
            
    return alpha

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert numpy arrays to bitboards (uint64)
    me = 0
    opp = 0
    for r in range(8):
        for c in range(8):
            idx = r * 8 + c
            if you[r][c]:
                me |= (1 << idx)
            if opponent[r][c]:
                opp |= (1 << idx)
    
    # Determine search depth based on game progress
    empty_count = 64 - bin(me).count('1') - bin(opp).count('1')
    
    if empty_count <= 12:
        depth = 6
    elif empty_count <= 20:
        depth = 5
    else:
        depth = 4

    # Find the best move
    moves = get_valid_moves(me, opp)
    
    if not moves:
        return "pass"
    
    best_move_idx = -1
    best_score = -sys.maxsize
    alpha = -sys.maxsize
    beta = sys.maxsize
    
    # Order root moves as well
    moves.sort(key=lambda x: _WEIGHTS[x[0]], reverse=True)
    
    for idx, flipped in moves:
        new_me = me | (1 << idx) | flipped
        new_opp = opp & ~flipped
        
        # Recursion starts with opponent's perspective
        score = -negamax(new_opp, new_me, depth - 1, -beta, -alpha)
        
        if score > best_score:
            best_score = score
            best_move_idx = idx
        
        if score > alpha:
            alpha = score
            
    # Convert index to algebraic notation
    r, c = divmod(best_move_idx, 8)
    return f"{chr(ord('a') + c)}{r + 1}"

