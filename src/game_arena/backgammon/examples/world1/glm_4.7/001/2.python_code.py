
def policy(state: dict) -> str:
    """Backgammon policy using heuristic evaluation."""
    import random
    
    if not state or not state.get('dice'):
        return "H:P,P"
    
    my_pts = list(state['my_pts'])
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    low, high = min(dice), max(dice)
    is_double = len(dice) == 2 and dice[0] == dice[1]
    
    def can_bear_off(pts):
        return all(pts[i] == 0 for i in range(6, 24))
    
    def get_dest(from_point, die):
        if from_point == 'B':
            return 24 - die
        return int(from_point[1:]) - die
    
    def get_starts(pts, bar):
        if bar > 0:
            return ['B']
        return [f'A{i}' for i in range(24) if pts[i] > 0]
    
    def apply_move(pts, bar, from_point, die):
        new_pts = list(pts)
        new_bar = bar
        
        if from_point == 'B':
            new_bar -= 1
            dest = 24 - die
            if dest >= 0:
                new_pts[dest] += 1
        else:
            idx = int(from_point[1:])
            new_pts[idx] -= 1
            dest = idx - die
            if dest >= 0:
                new_pts[dest] += 1
        
        return new_pts, new_bar
    
    def would_hit(from_point, die, opp_pts):
        dest = get_dest(from_point, die)
        return 0 <= dest < 24 and opp_pts[dest] == 1
    
    def can_move(pts, bar, from_point, die, opp_pts):
        if from_point == 'B':
            if bar == 0:
                return False
        else:
            idx = int(from_point[1:])
            if pts[idx] == 0:
                return False
        
        if bar > 0 and from_point != 'B':
            return False
        
        dest = get_dest(from_point, die)
        
        if dest < 0:
            if not can_bear_off(pts):
                return False
            if from_point == 'B':
                return False
            idx = int(from_point[1:])
            if dest == -1:
                return True
            return all(pts[i] == 0 for i in range(idx))
        
        return opp_pts[dest] < 2
    
    def evaluate_move(from_point, die, pts, bar, opp_pts):
        score = 0
        dest = get_dest(from_point, die)
        
        if would_hit(from_point, die, opp_pts):
            score += 25
        
        if dest >= 0 and dest < 24:
            new_count = pts[dest] + (1 if from_point != 'B' else 0)
            if new_count == 2:
                score += 15
            elif new_count > 2:
                score += 5
        
        if dest < 0:
            score += 20
        
        if from_point != 'B':
            idx = int(from_point[1:])
            if pts[idx] == 2:
                score -= 8
            elif pts[idx] == 1:
                score -= 2
            score += (idx - max(0, dest)) * 0.1
        
        return score
    
    def evaluate_state(pts, bar, opp_pts):
        score = 0
        
        pip = sum(i * pts[i] for i in range(24))
        score -= pip * 0.05
        
        for i in range(24):
            if pts[i] >= 2:
                score += 4
                if i < 6:
                    score += 3
        
        for i in range(24):
            if pts[i] == 1:
                risk = sum(1 for d in range(1, 7) if i + d < 24 and opp_pts[i + d] > 0)
                score -= 3 + risk * 2
        
        score -= bar * 12
        
        prime_len = 0
        max_prime = 0
        for i in range(24):
            if pts[i] >= 2:
                prime_len += 1
                max_prime = max(max_prime, prime_len)
            else:
                prime_len = 0
        score += max_prime * 3
        
        return score
    
    best_move = "H:P,P"
    best_score = -float('inf')
    starts = get_starts(my_pts, my_bar)
    
    if is_double or len(dice) == 1:
        die = dice[0]
        for s in starts:
            if can_move(my_pts, my_bar, s, die, opp_pts):
                pts, bar = apply_move(my_pts, my_bar, s, die)
                total = evaluate_move(s, die, my_pts, my_bar, opp_pts) + evaluate_state(pts, bar, opp_pts)
                if total > best_score or (total == best_score and random.random() < 0.3):
                    best_score = total
                    best_move = f"H:{s},P"
    else:
        for order, d1, d2 in [('H', high, low), ('L', low, high)]:
            for s1 in starts:
                if can_move(my_pts, my_bar, s1, d1, opp_pts):
                    pts1, bar1 = apply_move(my_pts, my_bar, s1, d1)
                    starts2 = get_starts(pts1, bar1)
                    
                    two_played = False
                    for s2 in starts2:
                        if can_move(pts1, bar1, s2, d2, opp_pts):
                            two_played = True
                            pts2, bar2 = apply_move(pts1, bar1, s2, d2)
                            total = (evaluate_move(s1, d1, my_pts, my_bar, opp_pts) + 
                                   evaluate_move(s2, d2, pts1, bar1, opp_pts) +
                                   evaluate_state(pts2, bar2, opp_pts))
                            if total > best_score or (total == best_score and random.random() < 0.3):
                                best_score = total
                                best_move = f"{order}:{s1},{s2}"
                    
                    if not two_played and d1 == high:
                        total = evaluate_move(s1, d1, my_pts, my_bar, opp_pts) + evaluate_state(pts1, bar1, opp_pts)
                        if total > best_score or (total == best_score and random.random() < 0.3):
                            best_score = total
                            best_move = f"{order}:{s1},P"
    
    return best_move
