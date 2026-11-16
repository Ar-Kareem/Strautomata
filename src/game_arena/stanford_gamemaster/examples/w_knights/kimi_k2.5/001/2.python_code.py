
def policy(state: list[list[object]], role: str) -> str:
    """
    Knights game policy.
    - Win immediately if possible (reach rank 6 for white, rank 1 for black).
    - Prioritize captures (+1000 score).
    - Prioritize forward progress (+10 per rank closer to goal).
    - Avoid unsafe moves where opponent can capture immediately (-500).
    """
    my_pieces = set()
    opp_pieces = set()
    
    # Parse state propositions
    for prop in state:
        if isinstance(prop, list) and len(prop) >= 4 and prop[0] == "cell":
            file_char = prop[1]
            rank_str = prop[2]
            color = prop[3]
            try:
                f_idx = ord(file_char) - ord('a') + 1  # a=1, b=2, ..., f=6
                r_idx = int(rank_str)
                if 1 <= f_idx <= 6 and 1 <= r_idx <= 6:
                    if color == role:
                        my_pieces.add((f_idx, r_idx))
                    else:
                        opp_pieces.add((f_idx, r_idx))
            except (ValueError, TypeError):
                continue
    
    opp_role = "black" if role == "white" else "white"
    
    # Define knight offsets based on direction constraints
    if role == "white":
        # White moves upward (increasing rank)
        offsets = [(1, 2), (-1, 2), (2, 1), (-2, 1)]
        goal_rank = 6
    else:
        # Black moves downward (decreasing rank)
        offsets = [(1, -2), (-1, -2), (2, -1), (-2, -1)]
        goal_rank = 1
    
    legal_moves = []
    
    # Generate all legal moves
    for f, r in my_pieces:
        for df, dr in offsets:
            nf, nr = f + df, r + dr
            # Check board boundaries
            if 1 <= nf <= 6 and 1 <= nr <= 6:
                # Cannot capture own piece
                if (nf, nr) not in my_pieces:
                    is_capture = (nf, nr) in opp_pieces
                    is_win = (nr == goal_rank)
                    
                    # Format: move(a,2,b,4)
                    f_name = chr(ord('a') + f - 1)
                    nf_name = chr(ord('a') + nf - 1)
                    move_str = f"move({f_name},{r},{nf_name},{nr})"
                    legal_moves.append((move_str, is_win, is_capture, f, r, nf, nr))
    
    if not legal_moves:
        return "noop"  # Should not occur in valid game states
    
    # Immediate winning move: highest priority
    for move_str, is_win, is_capture, f, r, nf, nr in legal_moves:
        if is_win:
            return move_str
    
    # Evaluate non-winning moves
    best_move = legal_moves[0][0]
    best_score = -float('inf')
    
    # Opponent offsets for safety checking
    if opp_role == "white":
        opp_offsets = [(1, 2), (-1, 2), (2, 1), (-2, 1)]
    else:
        opp_offsets = [(1, -2), (-1, -2), (2, -1), (-2, -1)]
    
    for move_str, is_win, is_capture, f, r, nf, nr in legal_moves:
        score = 0
        
        # Capture bonus
        if is_capture:
            score += 1000
        
        # Progress bonus: closer to goal is better
        if role == "white":
            score += nr * 10
        else:
            score += (7 - nr) * 10  # nr=1 gives 60, nr=6 gives 10
        
        # Safety evaluation: simulate move and check if opponent can capture there
        sim_my = set(my_pieces)
        sim_my.remove((f, r))
        sim_my.add((nf, nr))
        
        sim_opp = set(opp_pieces)
        if is_capture:
            sim_opp.remove((nf, nr))
        
        unsafe = False
        for of, orank in sim_opp:
            for odf, odr in opp_offsets:
                o_nf, o_nr = of + odf, orank + odr
                if 1 <= o_nf <= 6 and 1 <= o_nr <= 6:
                    if o_nf == nf and o_nr == nr:
                        # Verify opponent doesn't land on their own piece
                        if (o_nf, o_nr) not in sim_opp:
                            unsafe = True
                            break
            if unsafe:
                break
        
        if unsafe:
            score -= 500
        
        if score > best_score:
            best_score = score
            best_move = move_str
    
    return best_move
