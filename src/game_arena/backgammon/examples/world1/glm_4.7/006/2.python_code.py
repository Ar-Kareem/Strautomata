
import random

def policy(state: dict) -> str:
    # Extract state information
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # Normalize dice to always have a low and high value for logic
    # If dice list is empty, no moves
    if not dice:
        return "H:P,P"
    
    # Handle case of 1 die by treating it as two identical dice for generation,
    # but standard rules usually limit moves to available checkers.
    # The engine handles specific "playability", we just provide candidates.
    d_vals = list(dice)
    if len(d_vals) == 1:
        d_vals.append(d_vals[0])
    
    d_low = min(d_vals)
    d_high = max(d_vals)
    
    # Helper: Check if bearing off is allowed
    def can_bear_off(pts, bar):
        if bar > 0:
            return False
        return sum(pts[6:]) == 0
    
    can_off = can_bear_off(my_pts, my_bar)

    # Helper: Validate a single move (from point 'p' with die 'd')
    def is_valid_move(pts, bar, opp_loc, d, p):
        if p == 'P':
            return True
        
        if p == 'B':
            if bar == 0:
                return False
            dest = 24 - d
            if not (0 <= dest < 24):
                return False
            if opp_loc[dest] >= 2:
                return False
            return True
            
        # p is an integer index 0..23
        if not (0 <= p < 24):
            return False
        if pts[p] == 0:
            return False
            
        dest = p - d
        
        if dest < 0:
            if can_off:
                if dest == -1:
                    return True
                # Check higher points
                if sum(pts[i] for i in range(p + 1, 6)) == 0:
                    return True
            return False
            
        if not (0 <= dest < 24):
            return False
        if opp_loc[dest] >= 2:
            return False
            
        return True

    candidates = []
    
    # We need to check both orders (H and L)
    orders = [
        ('H', d_high, d_low),
        ('L', d_low, d_high)
    ]
    
    for prefix, d1, d2 in orders:
        # Generate start points for Move 1
        starts1 = []
        if my_bar > 0:
            if is_valid_move(my_pts, my_bar, opp_pts, d1, 'B'):
                starts1.append('B')
        else:
            if is_valid_move(my_pts, my_bar, opp_pts, d1, 'P'):
                starts1.append('P')
            for p in range(24):
                if is_valid_move(my_pts, my_bar, opp_pts, d1, p):
                    starts1.append(p)
                    
        for s1 in starts1:
            # Simulate Move 1
            n_my_pts = list(my_pts)
            n_my_bar = my_bar
            n_opp_pts = list(opp_pts)
            n_opp_bar = opp_bar
            n_my_off = my_off
            
            move1_used = (s1 != 'P')
            
            if s1 != 'P':
                if s1 == 'B':
                    n_my_bar -= 1
                    dest = 24 - d1
                else:
                    n_my_pts[s1] -= 1
                    dest = s1 - d1
                
                if dest < 0:
                    n_my_off += 1
                else:
                    if n_opp_pts[dest] == 1:
                        n_opp_bar += 1
                        n_opp_pts[dest] = 0
                    n_my_pts[dest] += 1
            
            # Recalculate bearing off capability for Move 2
            n_can_off = can_bear_off(n_my_pts, n_my_bar)
            
            # Generate start points for Move 2
            starts2 = []
            if n_my_bar > 0:
                if is_valid_move(n_my_pts, n_my_bar, n_opp_pts, d2, 'B'):
                    starts2.append('B')
            else:
                if is_valid_move(n_my_pts, n_my_bar, n_opp_pts, d2, 'P'):
                    starts2.append('P')
                for p in range(24):
                    if is_valid_move(n_my_pts, n_my_bar, n_opp_pts, d2, p):
                        starts2.append(p)
            
            for s2 in starts2:
                move2_used = (s2 != 'P')
                
                # Format points to string
                def fmt(p):
                    if p == 'B': return 'B'
                    if p == 'P': return 'P'
                    return f"A{p}"
                
                candidates.append({
                    'prefix': prefix,
                    's1': fmt(s1),
                    's2': fmt(s2),
                    'state': (n_my_pts, n_opp_pts, n_my_bar, n_opp_bar, n_my_off, opp_off),
                    'moves_count': (1 if move1_used else 0) + (1 if move2_used else 0),
                    'd1': d1,
                    'd2': d2
                })

    # Filter candidates based on Backgammon rules
    
    play_both = [c for c in candidates if c['moves_count'] == 2]
    play_one = [c for c in candidates if c['moves_count'] == 1]
    play_none = [c for c in candidates if c['moves_count'] == 0]
    
    valid_candidates = []
    
    if play_both:
        valid_candidates = play_both
    elif play_one:
        # Must play higher die if only one move is possible
        for c in play_one:
            used_die = c['d1'] if c['s1'] != 'P' else c['d2']
            if used_die == d_high:
                valid_candidates.append(c)
            # If doubles (d_low == d_high), any single move is fine
            elif d_low == d_high:
                valid_candidates.append(c)
    elif play_none:
        valid_candidates = play_none
    
    if not valid_candidates:
        return "H:P,P"
    
    # Evaluation Function
    def evaluate_score(c):
        n_my_pts, n_opp_pts, n_my_bar, n_opp_bar, n_my_off, n_opp_off_loc = c['state']
        
        score = 0.0
        
        # 1. Bearing Off (Most important)
        score += n_my_off * 1000.0
        
        # 2. Hitting Opponent
        hits = n_opp_bar - opp_bar
        score += hits * 200.0
        
        # 3. Safety (Avoid blots)
        # Blots are single checkers
        my_blots = sum(1 for x in n_my_pts if x == 1)
        score -= my_blots * 15.0
        
        # Bonus for making points (anchors/blocks)
        my_points = sum(1 for x in n_my_pts if x >= 2)
        score += my_points * 10.0
        
        # 4. Pip Count (Race progress)
        my_pip = sum((i + 1) * cnt for i, cnt in enumerate(n_my_pts))
        opp_pip = sum((24 - i) * cnt for i, cnt in enumerate(n_opp_pts))
        opp_pip += n_opp_bar * 24
        score += (opp_pip - my_pip) * 0.5
        
        # 5. Home Board Control
        home_points = sum(1 for i in range(6) if n_my_pts[i] >= 2)
        score += home_points * 5.0
        
        # Add small random noise to break ties unpredictably
        score += random.random()
        
        return score

    best_move = max(valid_candidates, key=evaluate_score)
    return f"{best_move['prefix']}:{best_move['s1']},{best_move['s2']}"
