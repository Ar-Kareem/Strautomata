
import itertools

def policy(state: dict) -> str:
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = list(state['dice'])
    
    if len(dice) == 0:
        return "H:P,P"
    
    # Generate all legal moves and evaluate them
    # We need to simulate moves to find legal ones
    
    def can_move_to(point, my_p, opp_p):
        """Check if we can move a checker to this point"""
        if point < 0:
            return False  # bearing off handled separately
        # Opponent has 2+ checkers = blocked
        if opp_p[point] >= 2:
            return False
        return True
    
    def all_in_home(my_p, bar):
        """Check if all checkers are in home board (points 0-5)"""
        if bar > 0:
            return False
        for i in range(6, 24):
            if my_p[i] > 0:
                return False
        return True
    
    def can_bear_off(point, die, my_p):
        """Check if we can bear off from this point with this die"""
        if point == die - 1:
            return True  # exact
        if point < die - 1:
            # Can bear off if no checker on higher point in home
            for i in range(point + 1, 6):
                if my_p[i] > 0:
                    return False
            return True
        return False
    
    def apply_move(my_p, opp_p, bar, off, opp_b, src, die):
        """Apply a single die move. src='bar' or point index. Returns new state or None if illegal."""
        my_p = list(my_p)
        opp_p = list(opp_p)
        bar_new = bar
        off_new = off
        opp_b_new = opp_b
        
        if src == 'bar':
            if bar <= 0:
                return None
            dest = 24 - die  # entering from bar
            if dest < 0 or dest > 23:
                return None
            if opp_p[dest] >= 2:
                return None
            bar_new -= 1
            if opp_p[dest] == 1:
                opp_p[dest] = 0
                opp_b_new += 1
            my_p[dest] += 1
        else:
            pt = src
            if pt < 0 or pt > 23 or my_p[pt] <= 0:
                return None
            if bar > 0:
                return None  # must move from bar first
            dest = pt - die
            if dest < 0:
                # Bearing off
                if not all_in_home(my_p, bar_new):
                    return None
                if not can_bear_off(pt, die, my_p):
                    return None
                my_p[pt] -= 1
                off_new += 1
            else:
                if opp_p[dest] >= 2:
                    return None
                my_p[pt] -= 1
                if opp_p[dest] == 1:
                    opp_p[dest] = 0
                    opp_b_new += 1
                my_p[dest] += 1
        
        return (my_p, opp_p, bar_new, off_new, opp_b_new)
    
    def get_sources(my_p, bar):
        """Get possible source locations"""
        srcs = []
        if bar > 0:
            srcs.append('bar')
        else:
            for i in range(24):
                if my_p[i] > 0:
                    srcs.append(i)
        return srcs
    
    def evaluate(my_p, opp_p, bar, off, opp_b):
        score = 0.0
        
        # Bearing off progress (very important)
        score += off * 50
        
        # Opponent on bar
        score += opp_b * 15
        
        # My bar (bad)
        score -= bar * 40
        
        # Pip count (lower is better for us - we move from 23 to 0)
        pip = bar * 25
        for i in range(24):
            pip += my_p[i] * (i + 1)
        score -= pip * 0.5
        
        # Home board points made (points 0-5 with 2+ checkers)
        home_points_made = 0
        for i in range(6):
            if my_p[i] >= 2:
                home_points_made += 1
                score += (6 - i) * 5  # inner points worth more
        
        score += home_points_made * 8
        
        # Blocking points (any point with 2+ checkers)
        for i in range(24):
            if my_p[i] >= 2:
                score += 3
            if my_p[i] >= 4:
                score -= 2  # stacking too many is wasteful
        
        # Prime detection (consecutive points with 2+)
        consecutive = 0
        max_prime = 0
        for i in range(24):
            if my_p[i] >= 2:
                consecutive += 1
                max_prime = max(max_prime, consecutive)
            else:
                consecutive = 0
        if max_prime >= 3:
            score += max_prime * 10
        if max_prime >= 6:
            score += 50
        
        # Blot penalty
        for i in range(24):
            if my_p[i] == 1:
                # Penalty depends on how exposed it is
                # More exposed if further from home and opponent can hit
                exposure = 0
                for d in range(1, 7):
                    attack_from = i + d
                    if attack_from < 24 and opp_p[attack_from] > 0:
                        exposure += opp_p[attack_from]
                    if opp_b > 0 and (24 - d) == i:
                        exposure += opp_b
                # Also check bar entries
                penalty = 3 + exposure * 3
                if i >= 6:
                    penalty += 2  # blots outside home more dangerous
                score -= penalty
        
        # Anchor in opponent's home board (points 18-23 for us)
        for i in range(18, 24):
            if my_p[i] >= 2:
                score += 7
        
        return score
    
    # Generate moves
    best_score = float('-inf')
    best_move = "H:P,P"
    
    if len(dice) == 1:
        die = dice[0]
        found_move = False
        srcs = get_sources(my_pts, my_bar)
        for src in srcs:
            result = apply_move(my_pts, opp_pts, my_bar, my_off, opp_bar, src, die)
            if result is not None:
                found_move = True
                sc = evaluate(*result)
                if sc > best_score:
                    best_score = sc
                    src_str = 'B' if src == 'bar' else f'A{src}'
                    best_move = f"H:{src_str},P"
        if not found_move:
            best_move = "H:P,P"
    elif len(dice) == 2:
        d1, d2 = dice[0], dice[1]
        high = max(d1, d2)
        low = min(d1, d2)
        
        found_two = False
        found_one = False
        one_move_best = ("H:P,P", float('-inf'), False)  # move, score, is_high
        
        for order_char, first_die, second_die in [('H', high, low), ('L', low, high)]:
            srcs1 = get_sources(my_pts, my_bar)
            for s1 in srcs1:
                r1 = apply_move(my_pts, opp_pts, my_bar, my_off, opp_bar, s1, first_die)
                if r1 is None:
                    continue
                mp1, op1, b1, o1, ob1 = r1
                if not found_two:
                    found_one = True
                srcs2 = get_sources(mp1, b1)
                moved_second = False
                for s2 in srcs2:
                    r2 = apply_move(mp1, op1, b1, o1, ob1, s2, second_die)
                    if r2 is None:
                        continue
                    moved_second = True
                    found_two = True
                    sc = evaluate(*r2)
                    if sc > best_score:
                        best_score = sc
                        s1_str = 'B' if s1 == 'bar' else f'A{s1}'
                        s2_str = 'B' if s2 == 'bar' else f'A{s2}'
                        best_move = f"{order_char}:{s1_str},{s2_str}"
                
                if not moved_second and not found_two:
                    sc = evaluate(mp1, op1, b1, o1, ob1)
                    s1_str = 'B' if s1 == 'bar' else f'A{s1}'
                    if sc > one_move_best[1]:
                        is_high = (first_die == high)
                        one_move_best = (f"{order_char}:{s1_str},P", sc, is_high)
        
        if not found_two and found_one:
            # Must play higher die if only one can be played
            # Try both and see which die can actually be used
            can_high = False
            can_low = False
            best_high = ("H:P,P", float('-inf'))
            best_low = ("L:P,P", float('-inf'))
            
            srcs = get_sources(my_pts, my_bar)
            for s1 in srcs:
                rh = apply_move(my_pts, opp_pts, my_bar, my_off, opp_bar, s1, high)
                if rh is not None:
                    can_high = True
                    sc = evaluate(*rh)
                    s1_str = 'B' if s1 == 'bar' else f'A{s1}'
                    if sc > best_high[1]:
                        best_high = (f"H:{s1_str},P", sc)
                
                rl = apply_move(my_pts, opp_pts, my_bar, my_off, opp_bar, s1, low)
                if rl is not None:
                    can_low = True
                    sc = evaluate(*rl)
                    s1_str = 'B' if s1 == 'bar' else f'A{s1}'
                    if sc > best_low[1]:
                        best_low = (f"L:{s1_str},P", sc)
            
            if can_high:
                best_move = best_high[0]
            elif can_low:
                best_move = best_low[0]
        elif not found_two and not found_one:
            best_move = "H:P,P"
    
    return best_move
