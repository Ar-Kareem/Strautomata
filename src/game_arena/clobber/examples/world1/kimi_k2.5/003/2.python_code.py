
# Precompute neighbor indices for each cell on the 5x6 board
NEIGHBORS = []
for r in range(5):
    for c in range(6):
        idx = r * 6 + c
        n = []
        if r > 0:
            n.append(idx - 6)  # Up
        if r < 4:
            n.append(idx + 6)  # Down
        if c > 0:
            n.append(idx - 1)  # Left
        if c < 5:
            n.append(idx + 1)  # Right
        NEIGHBORS.append(n)


def gen_moves(my_mask: int, opp_mask: int):
    """Generate all legal moves as (from_idx, to_idx) tuples."""
    moves = []
    mm = my_mask
    while mm:
        lsb = mm & -mm
        i = (lsb.bit_length() - 1)
        for j in NEIGHBORS[i]:
            if opp_mask & (1 << j):
                moves.append((i, j))
        mm ^= lsb
    return moves


def evaluate(my_mask: int, opp_mask: int) -> int:
    """Evaluate position from perspective of player to move.
    Returns mobility difference, or large negative if no moves (loss)."""
    my_moves = gen_moves(my_mask, opp_mask)
    if not my_moves:
        return -1000
    opp_moves = gen_moves(opp_mask, my_mask)
    return len(my_moves) - len(opp_moves)


def negamax(my_mask: int, opp_mask: int, depth: int, alpha: int, beta: int, tt: dict) -> int:
    """Negamax search with alpha-beta pruning and transposition table."""
    key = (my_mask, opp_mask, depth)
    if key in tt:
        return tt[key]
    
    if depth == 0:
        val = evaluate(my_mask, opp_mask)
        tt[key] = val
        return val
    
    moves = gen_moves(my_mask, opp_mask)
    if not moves:
        return -1000
    
    for i, j in moves:
        # Apply move: capture opponent piece at j, move from i to j
        new_my = (my_mask ^ (1 << i)) | (1 << j)
        new_opp = opp_mask ^ (1 << j)
        score = -negamax(new_opp, new_my, depth - 1, -beta, -alpha, tt)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    tt[key] = alpha
    return alpha


def policy(you: list[int], opponent: list[int]) -> str:
    # Convert input to bitmasks (handle both flat length-30 and 5x6 nested lists)
    my_mask = 0
    opp_mask = 0
    
    if len(you) == 30:
        for idx, val in enumerate(you):
            if val:
                my_mask |= (1 << idx)
    else:
        for r in range(5):
            for c in range(6):
                if you[r][c]:
                    my_mask |= (1 << (r * 6 + c))
    
    if len(opponent) == 30:
        for idx, val in enumerate(opponent):
            if val:
                opp_mask |= (1 << idx)
    else:
        for r in range(5):
            for c in range(6):
                if opponent[r][c]:
                    opp_mask |= (1 << (r * 6 + c))
    
    moves = gen_moves(my_mask, opp_mask)
    if not moves:
        # Should not happen in a valid game state, but return a dummy to prevent crash
        return "0,0,U"
    
    # Adaptive depth: use deeper search when branching factor is low
    if len(moves) > 40:
        max_depth = 3
    else:
        max_depth = 4
    
    # Order root moves by simple heuristic to improve alpha-beta pruning
    # Prefer moves that leave opponent with fewer mobility options
    scored_moves = []
    for i, j in moves:
        new_my = (my_mask ^ (1 << i)) | (1 << j)
        new_opp = opp_mask ^ (1 << j)
        opp_future = len(gen_moves(new_opp, new_my))
        scored_moves.append((opp_future, i, j))
    scored_moves.sort(key=lambda x: x[0])  # Sort by opponent mobility (ascending)
    ordered_moves = [(i, j) for _, i, j in scored_moves]
    
    tt = {}
    best_move = ordered_moves[0]
    best_score = -99999
    
    for i, j in ordered_moves:
        new_my = (my_mask ^ (1 << i)) | (1 << j)
        new_opp = opp_mask ^ (1 << j)
        score = -negamax(new_opp, new_my, max_depth - 1, -99999, 99999, tt)
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    # Convert best move to required string format
    i, j = best_move
    r = i // 6
    c = i % 6
    diff = j - i
    if diff == -6:
        d = 'U'
    elif diff == 6:
        d = 'D'
    elif diff == -1:
        d = 'L'
    else:
        d = 'R'
    
    return f"{r},{c},{d}"
