
import itertools

def policy(state: dict) -> str:
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = list(state['dice'])
    
    # Generate all possible move strings and pick the best one
    # We need to enumerate legal moves
    
    def is_opp_blocked(pt):
        """Check if point pt (0..23) is blocked by opponent (2+ checkers)"""
        return opp_pts[pt] >= 2
    
    def can_land(pt):
        """Check if we can land on absolute point pt"""
        if pt < 0:
            return False
        if pt > 23:
            return False
        return opp_pts[pt] < 2
    
    def all_in_home(mpts, mbar):
        """Check if all checkers are in home board (points 0-5)"""
        if mbar > 0:
            return False
        for i in range(6, 24):
            if mpts[i] > 0:
                return False
        return True
    
    def apply_single_move(mpts, opts, mbar, moff, src, die_val):
        """
        Apply a single die move. src is 'bar' or int 0..23.
        Returns (new_mpts, new_opts, new_mbar, new_moff, success)
        """
        mpts = list(mpts)
        opts = list(opts)
        
        if src == 'bar':
            # Enter from bar: destination is 24 - die_val
            dest = 24 - die_val
            if dest < 0 or dest > 23:
                return None
            if opts[dest] >= 2:
                return None
            new_mbar = mbar - 1
            hit = 0
            if opts[dest] == 1:
                opts[dest] = 0
                hit = 1
            mpts[dest] += 1
            return (mpts, opts, new_mbar, moff, hit)
        else:
            # Moving from point src
            if mpts[src] <= 0:
                return None
            dest = src - die_val
            if dest < 0:
                # Bearing off
                if not all_in_home(mpts, mbar):
                    return None
                # Can bear off if dest == -1 (exact) or if src is the highest occupied point
                if dest < -1:
                    # Check no checker on higher point
                    # This is bearing off with excess - only allowed if no checker on higher point
                    for i in range(src + 1, 6):
                        if mpts[i] > 0:
                            return None
                # dest < 0 means bearing off
                mpts[src] -= 1
                new_moff = moff + 1
                return (mpts, opts, mbar, new_moff, 0)
            else:
                if opts[dest] >= 2:
                    return None
                hit = 0
                if opts[dest] == 1:
                    opts[dest] = 0
                    hit = 1
                mpts[src] -= 1
                mpts[dest] += 1
                return (mpts, opts, mbar, moff, hit)
    
    def evaluate(mpts, opts, mbar, moff, obar, hits):
        """Evaluate position from my perspective. Higher is better."""
        score = 0.0
        
        # Bearing off is great
        score += moff * 50.0
        
        # Bar is terrible
        score -= mbar * 40.0
        
        # Opponent on bar is good
        score += obar * 20.0
        
        # Pip count (lower is better for me)
        pip = 0
        for i in range(24):
            pip += mpts[i] * (i + 1)
        pip += mbar * 25
        score -= pip * 0.5
        
        # Home board made points
        home_made = 0
        for i in range(6):
            if mpts[i] >= 2:
                home_made += 1
                score += 8.0
                # Inner points more valuable
                score += (6 - i) * 1.0
        
        # Primes (consecutive made points)
        consecutive = 0
        max_consecutive = 0
        for i in range(24):
            if mpts[i] >= 2:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0
        if max_consecutive >= 3:
            score += max_consecutive * 5.0
        if max_consecutive >= 6:
            score += 30.0
        
        # Blots (single checkers) - penalize based on danger
        for i in range(24):
            if mpts[i] == 1:
                # More dangerous if in opponent's home area or reachable
                if i >= 18:
                    score -= 12.0
                elif i >= 12:
                    score -= 8.0
                elif i >= 6:
                    score -= 5.0
                else:
                    score -= 3.0
        
        # Stacking penalty - too many checkers on one point
        for i in range(24):
            if mpts[i] > 3:
                score -= (mpts[i] - 3) * 2.0
        
        # Hitting bonus
        score += hits * 15.0
        
        # Anchors in opponent's home board (points 18-23 for us)
        for i in range(18, 24):
            if mpts[i] >= 2:
                score += 5.0
        
        # Distribution - reward spreading across key points
        # Being on the 7-point (index 6) and bar point (index 5)
        if mpts[5] >= 2:
            score += 3.0
        if mpts[6] >= 2:
            score += 3.0
        
        return score
    
    # Generate possible sources
    possible_sources = ['P']
    if my_bar > 0:
        possible_sources_with_bar = ['B']
    else:
        possible_sources_with_bar = []
        for i in range(24):
            if my_pts[i] > 0:
                possible_sources_with_bar.append(f'A{i}')
        possible_sources_with_bar.append('P')
    
    def src_to_internal(s):
        if s == 'B':
            return 'bar'
        elif s == 'P':
            return 'pass'
        else:
            return int(s[1:])
    
    def get_sources(mpts, mbar):
        srcs = []
        if mbar > 0:
            srcs.append('B')
        else:
            for i in range(24):
                if mpts[i] > 0:
                    srcs.append(f'A{i}')
        srcs.append('P')
        return srcs
    
    best_score = float('-inf')
    best_move = 'H:P,P'
    
    if len(dice) == 0:
        return 'H:P,P'
    
    if len(dice) == 1:
        die_val = dice[0]
        sources1 = get_sources(my_pts, my_bar)
        for s1 in sources1:
            si1 = src_to_internal(s1)
            if si1 == 'pass':
                move_str = f'H:{s1},P'
                score = evaluate(my_pts, opp_pts, my_bar, my_off, opp_bar, 0)
                if score > best_score:
                    best_score = score
                    best_move = move_str
                continue
            result = apply_single_move(my_pts, opp_pts, my_bar, my_off, si1, die_val)
            if result is None:
                continue
            nm, no, nb, noff, hit = result
            new_obar = opp_bar + hit
            score = evaluate(nm, no, nb, noff, new_obar, hit)
            move_str = f'H:{s1},P'
            if score > best_score:
                best_score = score
                best_move = move_str
        return best_move
    
    # Two dice
    d0, d1 = dice[0], dice[1]
    high_die = max(d0, d1)
    low_die = min(d0, d1)
    
    orders = ['H', 'L']
    
    found_two_move = False
    found_one_move = False
    best_one_move = None
    best_one_score = float('-inf')
    best_one_used_high = False
    
    for order in orders:
        if order == 'H':
            first_die = high_die
            second_die = low_die
        else:
            first_die = low_die
            second_die = high_die
        
        sources1 = get_sources(my_pts, my_bar)
        for s1 in sources1:
            si1 = src_to_internal(s1)
            if si1 == 'pass':
                # First move is pass - try second
                sources2 = get_sources(my_pts, my_bar)
                for s2 in sources2:
                    si2 = src_to_internal(s2)
                    if si2 == 'pass':
                        move_str = f'{order}:P,P'
                        score = evaluate(my_pts, opp_pts, my_bar, my_off, opp_bar, 0)
                        if not found_two_move and not found_one_move:
                            if score > best_score:
                                best_score = score
                                best_move = move_str
                        continue
                    result2 = apply_single_move(my_pts, opp_pts, my_bar, my_off, si2, second_die)
                    if result2 is None:
                        continue
                    nm2, no2, nb2, noff2, hit2 = result2
                    new_obar2 = opp_bar + hit2
                    score = evaluate(nm2, no2, nb2, noff2, new_obar2, hit2)
                    if not found_two_move:
                        used_high = (order == 'L')  # second move uses high die
                        if not found_one_move or score > best_one_score:
                            found_one_move = True
                            best_one_score = score
                            best_one_move = f'{order}:P,{s2}'
                            best_one_used_high = used_high
                continue
            
            result1 = apply_single_move(my_pts, opp_pts, my_bar, my_off, si1, first_die)
            if result1 is None:
                continue
            nm1, no1, nb1, noff1, hit1 = result1
            new_obar1 = opp_bar + hit1
            
            # Try second move
            sources2 = get_sources(nm1, nb1)
            for s2 in sources2:
                si2 = src_to_internal(s2)
                if si2 == 'pass':
                    # Only first move played
                    score = evaluate(nm1, no1, nb1, noff1, new_obar1, hit1)
                    used_high = (order == 'H')
                    if not found_two_move:
                        if not found_one_move or score > best_one_score or (used_high and not best_one_used_high and score >= best_one_score - 1):
                            found_one_move = True
                            best_one_score = score
                            best_one_move = f'{order}:{s1},P'
                            best_one_used_high = used_high
                    continue
                
                result2 = apply_single_move(nm1, no1, nb1, noff1, si2, second_die)
                if result2 is None:
                    continue
                nm2, no2, nb2, noff2, hit2 = result2
                total_hits = hit1 + hit2
                new_obar2 = opp_bar + total_hits
                score = evaluate(nm2, no2, nb2, noff2, new_obar2, total_hits)
                found_two_move = True
                if score > best_score:
                    best_score = score
                    best_move = f'{order}:{s1},{s2}'
    
    if not found_two_move and found_one_move:
        # Must play higher die if only one can be played and both are possible
        best_move = best_one_move
        best_score = best_one_score
    
    return best_move
