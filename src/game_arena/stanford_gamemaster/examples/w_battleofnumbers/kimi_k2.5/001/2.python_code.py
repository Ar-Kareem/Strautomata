
def policy(state: list[list[object]], role: str) -> str:
    # Parse state
    my_pieces = {}  # (r,c) -> number
    opp_pieces = {}  # (r,c) -> number
    opponent = "green" if role == "red" else "red"
    
    for fact in state:
        if fact[0] == "cell":
            r, c, num, color = int(fact[1]), int(fact[2]), int(fact[3]), fact[4]
            if color == role:
                my_pieces[(r, c)] = num
            else:
                opp_pieces[(r, c)] = num
    
    def can_capture(attacker: int, defender: int) -> bool:
        """Return True if attacker can capture defender"""
        if attacker == 1:
            return defender == 1 or defender == 5
        if attacker == 2:
            return defender <= 2
        if attacker == 3:
            return defender <= 3
        if attacker == 4:
            return defender <= 4
        if attacker == 5:
            return defender != 1 and defender <= 5  # 5 loses to 1
        return False
    
    def is_threatened(r: int, c: int, my_num: int, opp_dict: dict) -> bool:
        """Check if square (r,c) is threatened by any opponent piece"""
        for (orow, ocol), onum in opp_dict.items():
            if abs(orow - r) == 1 and abs(ocol - c) == 1:
                if can_capture(onum, my_num):
                    return True
        return False
    
    # Generate all legal moves: (r1, c1, r2, c2, is_capture, my_num, opp_num)
    moves = []
    dc_forward = 1 if role == "red" else -1
    
    for (r, c), num in my_pieces.items():
        # Forward orthogonal (must be empty)
        nr, nc = r, c + dc_forward
        if 1 <= nr <= 5 and 1 <= nc <= 5:
            if (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
                moves.append((r, c, nr, nc, False, num, 0))
        
        # Forward diagonals: move if empty, capture if opponent there
        for dr in (-1, 1):
            nr, nc = r + dr, c + dc_forward
            if 1 <= nr <= 5 and 1 <= nc <= 5:
                if (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
                    moves.append((r, c, nr, nc, False, num, 0))
                elif (nr, nc) in opp_pieces:
                    opp_num = opp_pieces[(nr, nc)]
                    if can_capture(num, opp_num):
                        moves.append((r, c, nr, nc, True, num, opp_num))
        
        # Backward diagonals: capture only
        for dr in (-1, 1):
            nr, nc = r + dr, c - dc_forward
            if 1 <= nr <= 5 and 1 <= nc <= 5:
                if (nr, nc) in opp_pieces:
                    opp_num = opp_pieces[(nr, nc)]
                    if can_capture(num, opp_num):
                        moves.append((r, c, nr, nc, True, num, opp_num))
    
    if not moves:
        # Fallback (should not happen in valid game)
        return "move(1,1,1,1)"
    
    # Evaluate moves
    best_move = None
    best_score = -100000
    
    for move in moves:
        r1, c1, r2, c2, is_cap, my_num, opp_num = move
        score = 0
        
        if is_cap:
            # Capturing is highly valuable
            score += 200 + opp_num * 10
            
            # Simulate capture: remove opponent piece, we move there
            temp_opp = dict(opp_pieces)
            del temp_opp[(r2, c2)]
            
            # Check if we get recaptured immediately
            if is_threatened(r2, c2, my_num, temp_opp):
                score -= my_num * 25  # Penalty for losing the piece
            else:
                score += 50  # Bonus for safe capture
        else:
            # Advancement bonus (prefer moving toward opponent)
            if role == "red":
                score += c2 * 3  # Higher column is better for red
            else:
                score += (6 - c2) * 3  # Lower column is better for green
            
            # Safety check: avoid moving into capture
            if is_threatened(r2, c2, my_num, opp_pieces):
                score -= my_num * 20
            
            # Escape bonus: moving away from current threat
            if is_threatened(r1, c1, my_num, opp_pieces):
                if not is_threatened(r2, c2, my_num, opp_pieces):
                    score += 60  # Good to escape
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        best_move = moves[0]
    
    r1, c1, r2, c2 = best_move[0], best_move[1], best_move[2], best_move[3]
    return f"move({r1},{c1},{r2},{c2})"
