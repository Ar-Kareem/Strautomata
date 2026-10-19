
def policy(you: list[int], opponent: list[int]) -> str:
    ROWS = 5
    COLS = 6
    N = ROWS * COLS
    
    # Precompute neighbors for each cell: list of (neighbor_idx, direction)
    neighbors = [[] for _ in range(N)]
    for r in range(ROWS):
        for c in range(COLS):
            i = r * COLS + c
            if r > 0:
                neighbors[i].append((i - COLS, 'U'))
            if r < ROWS - 1:
                neighbors[i].append((i + COLS, 'D'))
            if c > 0:
                neighbors[i].append((i - 1, 'L'))
            if c < COLS - 1:
                neighbors[i].append((i + 1, 'R'))
    
    def get_moves(me_mask: int, opp_mask: int):
        """Return list of (from_idx, to_idx) for all legal captures."""
        moves = []
        m = me_mask
        while m:
            lsb = m & -m
            idx = lsb.bit_length() - 1
            for nidx, _ in neighbors[idx]:
                if opp_mask & (1 << nidx):
                    moves.append((idx, nidx))
            m ^= lsb
        return moves
    
    def count_moves(me_mask: int, opp_mask: int) -> int:
        """Count number of legal moves."""
        count = 0
        m = me_mask
        while m:
            lsb = m & -m
            idx = lsb.bit_length() - 1
            for nidx, _ in neighbors[idx]:
                if opp_mask & (1 << nidx):
                    count += 1
            m ^= lsb
        return count
    
    def apply_move(me_mask: int, opp_mask: int, f: int, t: int):
        """Apply move from f to t (capturing opponent at t). Returns (new_me, new_opp)."""
        new_me = (me_mask & ~(1 << f)) | (1 << t)
        new_opp = opp_mask & ~(1 << t)
        return new_me, new_opp
    
    def evaluate(me_mask: int, opp_mask: int) -> int:
        """Evaluate position from perspective of player to move."""
        my_moves = count_moves(me_mask, opp_mask)
        if my_moves == 0:
            return -1000  # Loss
        opp_moves = count_moves(opp_mask, me_mask)
        return my_moves - opp_moves
    
    # Convert input lists to bit masks
    me_mask = 0
    opp_mask = 0
    for i in range(N):
        if you[i]:
            me_mask |= (1 << i)
        if opponent[i]:
            opp_mask |= (1 << i)
    
    moves = get_moves(me_mask, opp_mask)
    
    if not moves:
        # No legal moves (should not happen in valid game), return dummy
        return "0,0,U"
    
    if len(moves) == 1:
        f, t = moves[0]
        r, c = divmod(f, COLS)
        if t == f - COLS:
            return f"{r},{c},U"
        elif t == f + COLS:
            return f"{r},{c},D"
        elif t == f - 1:
            return f"{r},{c},L"
        else:
            return f"{r},{c},R"
    
    best_move = moves[0]
    best_score = -10000
    
    for f, t in moves:
        # Apply my move
        new_me, new_opp = apply_move(me_mask, opp_mask, f, t)
        
        # Check for immediate win (opponent has no moves)
        opp_moves = get_moves(new_opp, new_me)
        if not opp_moves:
            r, c = divmod(f, COLS)
            if t == f - COLS:
                return f"{r},{c},U"
            elif t == f + COLS:
                return f"{r},{c},D"
            elif t == f - 1:
                return f"{r},{c},L"
            else:
                return f"{r},{c},R"
        
        # Find opponent's best response (minimize my score)
        worst_score = 10000
        for of, ot in opp_moves:
            newer_opp, newer_me = apply_move(new_opp, new_me, of, ot)
            score = evaluate(newer_me, newer_opp)
            if score < worst_score:
                worst_score = score
                # Early break if we found a losing line for me
                if worst_score <= -1000:
                    break
        
        if worst_score > best_score:
            best_score = worst_score
            best_move = (f, t)
    
    f, t = best_move
    r, c = divmod(f, COLS)
    if t == f - COLS:
        return f"{r},{c},U"
    elif t == f + COLS:
        return f"{r},{c},D"
    elif t == f - 1:
        return f"{r},{c},L"
    else:
        return f"{r},{c},R"
