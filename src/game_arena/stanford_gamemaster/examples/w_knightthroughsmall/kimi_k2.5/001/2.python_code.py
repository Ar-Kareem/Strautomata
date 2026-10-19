
def policy(state: list[list[object]], role: str) -> str:
    # Parse board state
    board = {}  # (file, rank) -> color
    for fact in state:
        if fact[0] == "cell":
            f = fact[1]  # 'a'..'f'
            r = int(fact[2])  # 1..6
            color = fact[3]
            board[(f, r)] = color
    
    # Coordinate mapping
    files = ['a', 'b', 'c', 'd', 'e', 'f']
    f2i = {f: i for i, f in enumerate(files)}
    i2f = {i: f for i, f in enumerate(files)}
    
    opp = 'black' if role == 'white' else 'white'
    
    # Get my pieces
    my_pieces = [(f, r) for (f, r), c in board.items() if c == role]
    
    # Knight move offsets (forward only)
    if role == 'white':
        # Forward = increasing rank toward 6
        offsets = [(1, 2), (-1, 2), (2, 1), (-2, 1)]
        goal_rank = 6
    else:
        # Forward = decreasing rank toward 1
        offsets = [(1, -2), (-1, -2), (2, -1), (-2, -1)]
        goal_rank = 1
    
    def is_square_attacked(f, r, attacker_color):
        """Check if square (f,r) can be reached by attacker_color's next move"""
        f_idx = f2i[f]
        if attacker_color == 'white':
            att_offsets = [(1, 2), (-1, 2), (2, 1), (-2, 1)]
        else:
            att_offsets = [(1, -2), (-1, -2), (2, -1), (-2, -1)]
        
        for df, dr in att_offsets:
            af_idx = f_idx + df
            ar = r + dr
            if 0 <= af_idx < 6 and 1 <= ar <= 6:
                af = i2f[af_idx]
                if board.get((af, ar)) == attacker_color:
                    return True
        return False
    
    candidates = []
    
    for f, r in my_pieces:
        f_idx = f2i[f]
        for df, dr in offsets:
            nf_idx = f_idx + df
            nr = r + dr
            
            # Bounds check
            if not (0 <= nf_idx < 6 and 1 <= nr <= 6):
                continue
            
            nf = i2f[nf_idx]
            
            # Cannot capture own piece
            if board.get((nf, nr)) == role:
                continue
            
            is_capture = board.get((nf, nr)) == opp
            is_win = (nr == goal_rank)
            
            # Base scoring
            if is_win:
                score = 10000
            elif is_capture:
                # Captures are good, especially if they advance
                if role == 'white':
                    progress = nr - r
                else:
                    progress = r - nr
                score = 100 + progress * 5
            else:
                # Pure advancement
                if role == 'white':
                    score = (nr - r) * 10
                else:
                    score = (r - nr) * 10
            
            # Safety: penalize moving into opponent attack range (unless winning)
            if not is_win and is_square_attacked(nf, nr, opp):
                score -= 30
            
            move_str = f"move({f},{r},{nf},{nr})"
            candidates.append((score, move_str))
    
    # Sort by score descending
    candidates.sort(reverse=True, key=lambda x: x[0])
    
    if candidates:
        return candidates[0][1]
    else:
        # Fallback (should not happen in valid game states)
        # Return a syntactically valid dummy that will likely be illegal,
        # but prevents crash. In practice, legal moves always exist.
        return "move(a,1,b,3)"
