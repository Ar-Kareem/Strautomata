
import sys
sys.setrecursionlimit(10000)

# Precompute neighbor indices for all 30 cells (5 rows x 6 cols)
NEIGHBORS = [[] for _ in range(30)]
for r in range(5):
    for c in range(6):
        i = r * 6 + c
        if r > 0:
            NEIGHBORS[i].append(i - 6)  # Up
        if r < 4:
            NEIGHBORS[i].append(i + 6)  # Down
        if c > 0:
            NEIGHBORS[i].append(i - 1)  # Left
        if c < 5:
            NEIGHBORS[i].append(i + 1)  # Right


def policy(you, opponent):
    """Return the best move in format 'row,col,dir'."""
    
    # Convert input to bitmasks (handle both flat list and 2D array)
    my_mask = 0
    opp_mask = 0
    
    # Try to handle as flat list first (length 30)
    try:
        if len(you) == 30:
            for i in range(30):
                if you[i]:
                    my_mask |= (1 << i)
            for i in range(30):
                if opponent[i]:
                    opp_mask |= (1 << i)
        else:
            # Assume 5x6 grid
            for r in range(5):
                for c in range(6):
                    idx = r * 6 + c
                    if you[r][c]:
                        my_mask |= (1 << idx)
                    if opponent[r][c]:
                        opp_mask |= (1 << idx)
    except (TypeError, IndexError):
        # Fallback to 5x6 indexing
        for r in range(5):
            for c in range(6):
                idx = r * 6 + c
                if you[r][c]:
                    my_mask |= (1 << idx)
                if opponent[r][c]:
                    opp_mask |= (1 << idx)

    # Helper: check if a player has any legal moves
    def has_moves(p_mask, o_mask):
        m = p_mask
        while m:
            lsb = m & -m
            i = lsb.bit_length() - 1
            for nb in NEIGHBORS[i]:
                if o_mask & (1 << nb):
                    return True
            m ^= lsb
        return False

    # Generate all legal moves with metadata
    moves = []  # (from_idx, to_idx, row, col, d_row, d_col)
    m = my_mask
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        r = i // 6
        c = i % 6
        for nb in NEIGHBORS[i]:
            if opp_mask & (1 << nb):
                dr = (nb // 6) - r
                dc = (nb % 6) - c
                moves.append((i, nb, r, c, dr, dc))
        m ^= lsb

    if not moves:
        return "0,0,U"  # Should not happen in valid game

    # If only one move, play it immediately
    if len(moves) == 1:
        i, nb, r, c, dr, dc = moves[0]
        d = 'U' if dr == -1 else 'D' if dr == 1 else 'L' if dc == -1 else 'R'
        return f"{r},{c},{d}"

    # Check for immediate winning move (opponent has no moves after)
    for i, nb, r, c, dr, dc in moves:
        new_my = (my_mask & ~(1 << i)) | (1 << nb)
        new_opp = opp_mask & ~(1 << nb)
        if not has_moves(new_opp, new_my):
            d = 'U' if dr == -1 else 'D' if dr == 1 else 'L' if dc == -1 else 'R'
            return f"{r},{c},{d}"

    # Determine search depth based on game phase
    total_pieces = (my_mask | opp_mask).bit_count()
    if total_pieces <= 8:
        max_depth = 8
    elif total_pieces <= 14:
        max_depth = 6
    else:
        max_depth = 4

    # Evaluation function: mobility difference
    def evaluate(p_mask, o_mask):
        score = 0
        # Count moves for p_mask
        m = p_mask
        while m:
            lsb = m & -m
            i = lsb.bit_length() - 1
            for nb in NEIGHBORS[i]:
                if o_mask & (1 << nb):
                    score += 1
            m ^= lsb
        # Subtract moves for o_mask
        m = o_mask
        while m:
            lsb = m & -m
            i = lsb.bit_length() - 1
            for nb in NEIGHBORS[i]:
                if p_mask & (1 << nb):
                    score -= 1
            m ^= lsb
        return score

    # Negamax with Alpha-Beta pruning
    def negamax(p_mask, o_mask, depth, alpha, beta):
        if depth == 0:
            return evaluate(p_mask, o_mask)
        
        best_score = -9999
        has_move = False
        m = p_mask
        
        while m:
            lsb = m & -m
            i = lsb.bit_length() - 1
            for nb in NEIGHBORS[i]:
                if o_mask & (1 << nb):
                    has_move = True
                    new_p = (p_mask & ~(1 << i)) | (1 << nb)
                    new_o = o_mask & ~(1 << nb)
                    score = -negamax(new_o, new_p, depth - 1, -beta, -alpha)
                    if score >= beta:
                        return beta
                    if score > best_score:
                        best_score = score
                        if score > alpha:
                            alpha = score
            m ^= lsb
        
        if not has_move:
            # Loss - prefer longer losses (less negative)
            return -1000 + depth
        return best_score

    # Search for best move
    best_move = moves[0]
    best_score = -9999
    alpha = -9999
    beta = 9999
    
    for i, nb, r, c, dr, dc in moves:
        new_my = (my_mask & ~(1 << i)) | (1 << nb)
        new_opp = opp_mask & ~(1 << nb)
        score = -negamax(new_opp, new_my, max_depth - 1, -beta, -alpha)
        if score > best_score:
            best_score = score
            best_move = (i, nb, r, c, dr, dc)
            alpha = max(alpha, score)
    
    # Format output
    i, nb, r, c, dr, dc = best_move
    d = 'U' if dr == -1 else 'D' if dr == 1 else 'L' if dc == -1 else 'R'
    return f"{r},{c},{d}"
