
import sys

# Precompute all 49 winning lines as bitmasks for a 3x3x3 board.
# Cells are indexed 0..26, corresponding to i*9 + j*3 + k.
LINES = []

def add_line(c1, c2, c3):
    """Helper to create a bitmask for a line of 3 cells."""
    mask = (1 << c1) | (1 << c2) | (1 << c3)
    LINES.append(mask)

# 1. Orthogonal lines (27)
# Rows (varying i, fixed j, k)
for j in range(3):
    for k in range(3):
        add_line(0*9 + j*3 + k, 1*9 + j*3 + k, 2*9 + j*3 + k)
# Cols (varying j, fixed i, k)
for i in range(3):
    for k in range(3):
        add_line(i*9 + 0*3 + k, i*9 + 1*3 + k, i*9 + 2*3 + k)
# Pillars (varying k, fixed i, j)
for i in range(3):
    for j in range(3):
        add_line(i*9 + j*3 + 0, i*9 + j*3 + 1, i*9 + j*3 + 2)

# 2. Face Diagonals (18)
# Diagonals on planes perpendicular to x (constant i)
for i in range(3):
    add_line(i*9 + 0*3 + 0, i*9 + 1*3 + 1, i*9 + 2*3 + 2)
    add_line(i*9 + 0*3 + 2, i*9 + 1*3 + 1, i*9 + 2*3 + 0)
# Diagonals on planes perpendicular to y (constant j)
for j in range(3):
    add_line(0*9 + j*3 + 0, 1*9 + j*3 + 1, 2*9 + j*3 + 2)
    add_line(0*9 + j*3 + 2, 1*9 + j*3 + 1, 2*9 + j*3 + 0)
# Diagonals on planes perpendicular to z (constant k)
for k in range(3):
    add_line(0*9 + 0*3 + k, 1*9 + 1*3 + k, 2*9 + 2*3 + k)
    add_line(0*9 + 2*3 + k, 1*9 + 1*3 + k, 2*9 + 0*3 + k)

# 3. Space Diagonals (4)
add_line(0, 13, 26)  # (0,0,0) to (2,2,2)
add_line(2, 13, 24)  # (0,0,2) to (2,2,0)
add_line(6, 13, 20)  # (0,2,0) to (2,0,2)
add_line(8, 13, 18)  # (0,2,2) to (2,0,0)

# Center index (1,1,1)
CENTER_IDX = 13

def evaluate(me_mask, opp_mask):
    """
    Evaluates the board state from the perspective of 'me'.
    Returns a score.
    """
    # Check for immediate wins
    for line in LINES:
        if (me_mask & line) == line:
            return 100000
        if (opp_mask & line) == line:
            return -100000
    
    score = 0
    # Heuristic evaluation based on open lines
    for line in LINES:
        # Check if line is contested (mixed pieces)
        if (me_mask & opp_mask) & line:
            continue
            
        count_me = (me_mask & line).bit_count()
        count_opp = (opp_mask & line).bit_count()
        
        # We only care about lines that are not blocked by opponent
        if count_opp == 0:
            if count_me == 1:
                score += 10
            elif count_me == 2:
                score += 100 # Threat
        
        # Lines where opponent has pieces but we don't (we need to block)
        if count_me == 0:
            if count_opp == 1:
                score -= 10
            elif count_opp == 2:
                score -= 100 # Opponent Threat
                
    return score

def minimax(me_mask, opp_mask, depth, alpha, beta, maximizing):
    """
    Minimax with Alpha-Beta pruning.
    """
    # Evaluate state to check for terminal wins/losses early
    current_eval = evaluate(me_mask, opp_mask)
    if abs(current_eval) > 1000:
        return current_eval
        
    if depth == 0:
        return current_eval

    # Generate empty cells
    occupied = me_mask | opp_mask
    empty_moves = []
    # Iterate 0..26
    # Unrolling loop slightly for speed or just range
    for i in range(27):
        if not (occupied & (1 << i)):
            empty_moves.append(i)
            
    if not empty_moves:
        return 0 # Draw

    if maximizing:
        max_eval = -float('inf')
        # Simple move ordering: center first improves pruning
        if CENTER_IDX in empty_moves:
            empty_moves.remove(CENTER_IDX)
            empty_moves.insert(0, CENTER_IDX)
            
        for move in empty_moves:
            new_me = me_mask | (1 << move)
            eval_score = minimax(new_me, opp_mask, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        if CENTER_IDX in empty_moves:
            empty_moves.remove(CENTER_IDX)
            empty_moves.insert(0, CENTER_IDX)
            
        for move in empty_moves:
            new_opp = opp_mask | (1 << move)
            eval_score = minimax(me_mask, new_opp, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to bitmasks
    me_mask = 0
    opp_mask = 0
    
    for i in range(3):
        for j in range(3):
            for k in range(3):
                val = board[i][j][k]
                idx = i * 9 + j * 3 + k
                if val == 1:
                    me_mask |= (1 << idx)
                elif val == -1:
                    opp_mask |= (1 << idx)
                    
    # Get available moves
    occupied = me_mask | opp_mask
    empty_moves = [i for i in range(27) if not (occupied & (1 << i))]
    
    if not empty_moves:
        return (0, 0, 0) # Should not happen if game is valid
        
    # Heuristic: If center is open and board is empty, take it (optimal opening)
    if me_mask == 0 and opp_mask == 0:
        return (1, 1, 1)
        
    # Search depth: 3 plies (Me -> Opp -> Me)
    # This is safe for Python time limits.
    DEPTH = 3
    
    best_move = -1
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Re-order root moves for efficiency
    if CENTER_IDX in empty_moves:
        empty_moves.remove(CENTER_IDX)
        empty_moves.insert(0, CENTER_IDX)
        
    for move in empty_moves:
        new_me_mask = me_mask | (1 << move)
        
        # Check for immediate win to save time
        is_win = False
        for line in LINES:
            if (new_me_mask & line) == line:
                is_win = True
                break
        if is_win:
            return (move // 9, (move % 9) // 3, move % 3)
            
        score = minimax(new_me_mask, opp_mask, DEPTH - 1, alpha, beta, False)
        
        if score > best_score:
            best_score = score
            best_move = move
            
        alpha = max(alpha, score)
        # Pruning at root
        if best_score >= 100000:
            break
            
    # Fallback if search fails or empty list (shouldn't)
    if best_move == -1 and empty_moves:
        best_move = empty_moves[0]
    elif best_move == -1:
        best_move = 0

    i = best_move // 9
    j = (best_move % 9) // 3
    k = best_move % 3
    
    return (i, j, k)
