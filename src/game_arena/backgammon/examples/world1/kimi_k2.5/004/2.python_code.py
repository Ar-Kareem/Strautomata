
def policy(state):
    dice = state['dice']
    if not dice:
        return "H:P,P"
    
    def copy_state(s):
        return {
            'my_pts': s['my_pts'][:],
            'opp_pts': s['opp_pts'][:],
            'my_bar': s['my_bar'],
            'opp_bar': s['opp_bar'],
            'my_off': s['my_off'],
            'opp_off': s['opp_off'],
            'dice': s['dice']
        }
    
    def generate_sequences(s, dice_remaining, current_seq):
        """Generate all legal move sequences for the given ordered dice."""
        if not dice_remaining:
            yield current_seq, s
            return
        
        die = dice_remaining[0]
        rest = dice_remaining[1:]
        
        # Must enter from bar if checkers on bar
        if s['my_bar'] > 0:
            dest = 24 - die
            if 0 <= dest < 24 and s['opp_pts'][dest] < 2:
                ns = copy_state(s)
                ns['my_bar'] -= 1
                ns['my_pts'][dest] += 1
                # Hit opponent blot
                if ns['opp_pts'][dest] == 1:
                    ns['opp_pts'][dest] = 0
                    ns['opp_bar'] += 1
                yield from generate_sequences(ns, rest, current_seq + [('B', die)])
            # If cannot enter, this path is dead
            return
        
        # Check bearing off eligibility (all checkers in home board 0-5)
        all_in_home = all(s['my_pts'][i] == 0 for i in range(6, 24))
        
        found_move = False
        
        # Try all points
        for point in range(24):
            if s['my_pts'][point] == 0:
                continue
            
            dest = point - die
            
            if dest >= 0:
                # Normal move
                if s['opp_pts'][dest] < 2:
                    ns = copy_state(s)
                    ns['my_pts'][point] -= 1
                    ns['my_pts'][dest] += 1
                    # Hit opponent blot
                    if ns['opp_pts'][dest] == 1:
                        ns['opp_pts'][dest] = 0
                        ns['opp_bar'] += 1
                    yield from generate_sequences(ns, rest, current_seq + [(f'A{point}', die)])
                    found_move = True
            else:
                # Bear off attempt
                if all_in_home and point < 6:
                    # Check if any checkers on higher points in home board
                    can_bear = True
                    for p in range(point + 1, 6):
                        if s['my_pts'][p] > 0:
                            can_bear = False
                            break
                    if can_bear:
                        ns = copy_state(s)
                        ns['my_pts'][point] -= 1
                        ns['my_off'] += 1
                        yield from generate_sequences(ns, rest, current_seq + [(f'A{point}', die)])
                        found_move = True
        
        # If no move possible for this die
        if not found_move and not rest:
            # Cannot play this die, but no more dice to try
            yield current_seq, s
    
    def evaluate(s):
        """Evaluate board state from perspective of player to move."""
        my_pts = s['my_pts']
        opp_pts = s['opp_pts']
        my_bar = s['my_bar']
        opp_bar = s['opp_bar']
        my_off = s['my_off']
        opp_off = s['opp_off']
        
        # Pip count: sum of distances to bear off
        my_pip = sum(my_pts[i] * (i + 1) for i in range(24)) + my_bar * 25
        opp_pip = sum(opp_pts[i] * (24 - i) for i in range(24)) + opp_bar * 25
        
        # Blots (vulnerable single checkers)
        my_blots = sum(1 for i in range(24) if my_pts[i] == 1)
        opp_blots = sum(1 for i in range(24) if opp_pts[i] == 1)
        
        # Home board points made (0-5)
        my_home = sum(1 for i in range(6) if my_pts[i] >= 2)
        opp_home = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)
        
        # Anchors (points 18-23)
        my_anchors = sum(1 for i in range(18, 24) if my_pts[i] >= 2)
        
        # Weighted score
        score = 0.0
        score += 10.0 * my_off
        score -= 10.0 * opp_off
        score -= 0.2 * my_pip
        score += 0.2 * opp_pip
        score -= 5.0 * my_bar
        score += 5.0 * opp_bar
        score -= 2.0 * my_blots
        score += 1.5 * opp_blots
        score += 3.0 * my_home
        score -= 2.0 * opp_home
        score += 1.5 * my_anchors
        
        return score
    
    candidates = []
    
    if len(dice) == 1:
        d = dice[0]
        for seq, new_state in generate_sequences(state, [d], []):
            if len(seq) == 0:
                candidates.append(('H', 'P', 'P', new_state))
            else:
                candidates.append(('H', seq[0][0], 'P', new_state))
    else:
        d1, d2 = dice
        high, low = (d1, d2) if d1 > d2 else (d2, d1)
        
        # H order: higher die first
        for seq, new_state in generate_sequences(state, [high, low], []):
            if len(seq) == 0:
                candidates.append(('H', 'P', 'P', new_state))
            elif len(seq) == 1:
                candidates.append(('H', seq[0][0], 'P', new_state))
            else:
                candidates.append(('H', seq[0][0], seq[1][0], new_state))
        
        # L order: lower die first (only if dice differ)
        if d1 != d2:
            for seq, new_state in generate_sequences(state, [low, high], []):
                if len(seq) == 0:
                    candidates.append(('L', 'P', 'P', new_state))
                elif len(seq) == 1:
                    candidates.append(('L', seq[0][0], 'P', new_state))
                else:
                    candidates.append(('L', seq[0][0], seq[1][0], new_state))
    
    if not candidates:
        return "H:P,P"
    
    # Select best move by evaluation
    best_score = float('-inf')
    best_move = "H:P,P"
    
    for order, f1, f2, new_state in candidates:
        score = evaluate(new_state)
        if score > best_score:
            best_score = score
            best_move = f"{order}:{f1},{f2}"
    
    return best_move
