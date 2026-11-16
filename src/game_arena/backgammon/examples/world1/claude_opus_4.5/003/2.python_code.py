
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    def get_legal_moves():
        moves = []
        dice_list = list(dice)
        
        if len(dice_list) == 0:
            return [("H", "P", "P")]
        elif len(dice_list) == 1:
            d = dice_list[0]
            for m in get_single_moves(my_pts[:], my_bar, d):
                moves.append(("H", m, "P"))
            if not moves:
                moves.append(("H", "P", "P"))
            return moves
        
        d1, d2 = dice_list[0], dice_list[1]
        high_d, low_d = max(d1, d2), min(d1, d2)
        
        # Try H order: high die first, then low die
        for m1 in get_single_moves(my_pts[:], my_bar, high_d):
            pts1, bar1 = apply_move(my_pts[:], my_bar, m1, high_d)
            for m2 in get_single_moves(pts1, bar1, low_d):
                moves.append(("H", m1, m2))
        
        # Try L order: low die first, then high die
        for m1 in get_single_moves(my_pts[:], my_bar, low_d):
            pts1, bar1 = apply_move(my_pts[:], my_bar, m1, low_d)
            for m2 in get_single_moves(pts1, bar1, high_d):
                moves.append(("L", m1, m2))
        
        if not moves:
            # Try single moves with higher die first
            for m in get_single_moves(my_pts[:], my_bar, high_d):
                moves.append(("H", m, "P"))
            if not moves:
                for m in get_single_moves(my_pts[:], my_bar, low_d):
                    moves.append(("L", m, "P"))
            if not moves:
                moves.append(("H", "P", "P"))
        
        return moves
    
    def get_single_moves(pts, bar, die):
        moves = []
        if bar > 0:
            dest = 24 - die
            if dest >= 0 and opp_pts[dest] < 2:
                moves.append("B")
            return moves
        
        all_home = all(pts[i] == 0 for i in range(6, 24)) and bar == 0
        
        for i in range(24):
            if pts[i] > 0:
                dest = i - die
                if dest >= 0:
                    if opp_pts[dest] < 2:
                        moves.append(f"A{i}")
                elif all_home and i < 6:
                    if dest == -1 or (die > i and all(pts[j] == 0 for j in range(i+1, 6))):
                        moves.append(f"A{i}")
        return moves
    
    def apply_move(pts, bar, move, die):
        pts = pts[:]
        if move == "P":
            return pts, bar
        if move == "B":
            bar -= 1
            dest = 24 - die
            pts[dest] += 1
        else:
            src = int(move[1:])
            pts[src] -= 1
            dest = src - die
            if dest >= 0:
                pts[dest] += 1
        return pts, bar
    
    def evaluate(pts, bar):
        score = 0
        pip_count = sum(pts[i] * (i + 1) for i in range(24)) + bar * 25
        score -= pip_count * 1.0
        
        for i in range(6):
            if pts[i] >= 2:
                score += 5
        
        for i in range(24):
            if pts[i] == 1:
                penalty = 3 if i >= 18 else 2 if i >= 12 else 1
                score -= penalty
        
        off_count = 15 - sum(pts) - bar
        score += off_count * 10
        
        return score
    
    legal_moves = get_legal_moves()
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    dice_list = list(dice)
    if len(dice_list) == 2:
        high_d, low_d = max(dice_list), min(dice_list)
    elif len(dice_list) == 1:
        high_d, low_d = dice_list[0], 0
    else:
        high_d, low_d = 0, 0
    
    for move in legal_moves:
        order, m1, m2 = move
        pts, bar = my_pts[:], my_bar
        
        if order == "H":
            d1, d2 = high_d, low_d
        else:
            d1, d2 = low_d, high_d
        
        if m1 != "P":
            pts, bar = apply_move(pts, bar, m1, d1)
        if m2 != "P" and d2 > 0:
            pts, bar = apply_move(pts, bar, m2, d2)
        
        score = evaluate(pts, bar)
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]}:{best_move[1]},{best_move[2]}"
