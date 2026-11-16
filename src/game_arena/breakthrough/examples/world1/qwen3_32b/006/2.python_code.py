
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    me_set = set(me)
    opp_set = set(opp)
    moves = []
    direction = -1 if color == 'b' else 1

    for (r, c) in me:
        # Straight forward move
        new_r, new_c = r + direction, c
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            target_straight = (new_r, new_c)
            if target_straight not in me_set and target_straight not in opp_set:
                moves.append(((r, c), target_straight))
        
        # Diagonal left capture
        new_r, new_c = r + direction, c - 1
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            target_diag_left = (new_r, new_c)
            if target_diag_left in opp_set:
                moves.append(((r, c), target_diag_left))
        
        # Diagonal right capture
        new_r, new_c = r + direction, c + 1
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            target_diag_right = (new_r, new_c)
            if target_diag_right in opp_set:
                moves.append(((r, c), target_diag_right))
    
    best_score = -float('inf')
    best_moves = []

    for move in moves:
        (fr, fc), (tr, tc) = move
        is_promotion = (color == 'w' and tr == 7) or (color == 'b' and tr == 0)
        
        if is_promotion:
            score = float('inf')
        else:
            is_capture = (tr, tc) in opp_set
            delta = (tr - fr) * direction
            score = delta * 50
            if is_capture:
                score += 10
            
            # Center column bonus
            if tc in (3, 4):
                score += 2
        
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    return best_moves[0]
