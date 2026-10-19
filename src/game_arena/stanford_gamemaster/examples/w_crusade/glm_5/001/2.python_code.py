
def policy(state: list[list[object]], role: str) -> str:
    # Setup
    files = 'abcdefgh'
    file_to_idx = {f: i for i, f in enumerate(files)}
    knight_offsets = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    opponent = "black" if role == "white" else "white"
    
    # Parse cells from state
    cells = {}
    for prop in state:
        if prop[0] == "cell":
            cells[(prop[1], int(prop[2]))] = prop[3]
    
    # Find my pieces
    my_pieces = [(f, r) for (f, r), c in cells.items() if c == role]
    
    # Generate all legal moves
    def get_knight_destinations(f, r):
        f_idx = file_to_idx[f]
        dests = []
        for df, dr in knight_offsets:
            nf_idx = f_idx + df
            if 0 <= nf_idx < 8:
                nf = files[nf_idx]
                nr = r + dr
                if 1 <= nr <= 8:
                    dests.append((nf, nr))
        return dests
    
    legal_moves = []
    for pf, pr in my_pieces:
        for nf, nr in get_knight_destinations(pf, pr):
            np = (nf, nr)
            if np not in cells:
                legal_moves.append((pf, pr, nf, nr, False))
            elif cells[np] == opponent:
                legal_moves.append((pf, pr, nf, nr, True))
    
    if not legal_moves:
        return "move(a,1,b,3)"
    
    # Check if position is attacked by opponent
    def is_attacked(f, r):
        f_idx = file_to_idx[f]
        for df, dr in knight_offsets:
            af_idx = f_idx - df
            if 0 <= af_idx < 8:
                af = files[af_idx]
                ar = r - dr
                if 1 <= ar <= 8 and (af, ar) in cells and cells[(af, ar)] == opponent:
                    return True
        return False
    
    # Score each move
    def score_move(move):
        pf, pr, nf, nr, is_capture = move
        score = 0
        
        # Big bonus for captures
        if is_capture:
            score += 200
        
        # Safety considerations
        src_attacked = is_attacked(pf, pr)
        dest_attacked = is_attacked(nf, nr)
        
        if src_attacked and not dest_attacked:
            score += 60  # Escaping attack
        elif not src_attacked and dest_attacked:
            if is_capture:
                score -= 20  # Risky capture
            else:
                score -= 80  # Moving into attack
        
        # Advancement toward opponent
        if role == "white":
            score += (nr - pr) * 4
        else:
            score += (pr - nr) * 4
        
        # Center control
        f_idx = file_to_idx[nf]
        if nf in 'de':
            score += 4
        if nr in [4, 5]:
            score += 4
        
        # Threats created from new position
        threats = 0
        for df, dr in knight_offsets:
            tf_idx = f_idx + df
            if 0 <= tf_idx < 8:
                tf = files[tf_idx]
                tr = nr + dr
                if 1 <= tr <= 8:
                    tp = (tf, tr)
                    if tp in cells and cells[tp] == opponent:
                        threats += 1
        score += threats * 15
        
        # Mobility (squares reachable from destination)
        mobility = 0
        for df, dr in knight_offsets:
            mf_idx = f_idx + df
            if 0 <= mf_idx < 8:
                mf = files[mf_idx]
                mr = nr + dr
                if 1 <= mr <= 8:
                    mp = (mf, mr)
                    if mp not in cells or cells[mp] == opponent:
                        mobility += 1
        score += mobility * 2
        
        return score
    
    best_move = max(legal_moves, key=score_move)
    return f"move({best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]})"
