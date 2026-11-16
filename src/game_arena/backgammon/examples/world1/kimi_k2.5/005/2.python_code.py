
import copy

def policy(state: dict) -> str:
    dice = state['dice']
    
    # No dice to play
    if not dice:
        return "H:P,P"
    
    # Generate all legal moves respecting backgammon rules
    legal_moves = _generate_legal_moves(state)
    
    if not legal_moves:
        return "H:P,P"
    
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        new_state = _apply_move(state, move)
        score = _evaluate(new_state)
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        return "H:P,P"
    
    order, f1, f2 = best_move
    return f"{order}:{f1},{f2}"


def _generate_legal_moves(state):
    """Generate all legal moves respecting the constraint to play both dice if possible,
    otherwise play the higher die if possible, otherwise play the lower."""
    dice = state['dice']
    if not dice:
        return [("H", "P", "P")]
    
    d_sorted = sorted(dice, reverse=True)
    d_high = d_sorted[0]
    d_low = d_sorted[-1] if len(d_sorted) > 1 else d_high
    
    # Case: single die
    if len(dice) == 1:
        moves = []
        for from_pos, _ in _get_moves_for_die(d_high, state):
            moves.append(("H", from_pos, "P"))
        return moves if moves else [("H", "P", "P")]
    
    # Case: two dice (could be doubles)
    # First, try to play both dice
    both_moves = []
    
    # H order: high first, then low
    for f1, s1 in _get_moves_for_die(d_high, state):
        for f2, s2 in _get_moves_for_die(d_low, s1):
            both_moves.append(("H", f1, f2))
    
    # L order: low first, then high
    for f1, s1 in _get_moves_for_die(d_low, state):
        for f2, s2 in _get_moves_for_die(d_high, s1):
            both_moves.append(("L", f1, f2))
    
    if both_moves:
        return both_moves
    
    # Cannot play both. Try to play higher die only.
    high_only = []
    for f1, _ in _get_moves_for_die(d_high, state):
        high_only.append(("H", f1, "P"))
    
    if high_only:
        return high_only
    
    # Cannot play higher. Try to play lower die only.
    low_only = []
    for f1, _ in _get_moves_for_die(d_low, state):
        low_only.append(("L", f1, "P"))
    
    if low_only:
        return low_only
    
    return [("H", "P", "P")]


def _get_moves_for_die(d, st):
    """Get all legal moves for a single die value d from state st.
    Returns list of (from_str, new_state)."""
    results = []
    my_pts = list(st['my_pts'])
    opp_pts = list(st['opp_pts'])
    my_bar = st['my_bar']
    
    # Must move from bar first
    if my_bar > 0:
        # Entering: die d enters at point 24-d (d=1->23, d=6->18)
        dest = 24 - d
        if 0 <= dest <= 23 and opp_pts[dest] < 2:
            new_my_pts = list(my_pts)
            new_opp_pts = list(opp_pts)
            new_my_bar = my_bar - 1
            new_opp_bar = st['opp_bar']
            
            # Hit if opponent has blot
            if opp_pts[dest] == 1:
                new_opp_pts[dest] = 0
                new_opp_bar += 1
            else:
                new_opp_pts[dest] = opp_pts[dest]
            
            new_my_pts[dest] = my_pts[dest] + 1
            
            new_state = {
                'my_pts': new_my_pts,
                'opp_pts': new_opp_pts,
                'my_bar': new_my_bar,
                'opp_bar': new_opp_bar,
                'my_off': st['my_off'],
                'opp_off': st['opp_off'],
                'dice': st['dice']
            }
            results.append(("B", new_state))
        return results
    
    # Check if bearing off is allowed (all checkers in home board 0-5)
    can_bear_off = (st['my_bar'] == 0 and sum(my_pts[6:]) == 0)
    
    # Try moving from each point
    for p in range(24):
        if my_pts[p] == 0:
            continue
            
        dest = p - d
        
        if dest >= 0:
            # Regular move
            if opp_pts[dest] < 2:
                new_my_pts = list(my_pts)
                new_opp_pts = list(opp_pts)
                new_opp_bar = st['opp_bar']
                
                new_my_pts[p] -= 1
                new_my_pts[dest] += 1
                
                # Hit opponent blot
                if opp_pts[dest] == 1:
                    new_opp_pts[dest] = 0
                    new_opp_bar += 1
                else:
                    new_opp_pts[dest] = opp_pts[dest]
                
                new_state = {
                    'my_pts': new_my_pts,
                    'opp_pts': new_opp_pts,
                    'my_bar': 0,
                    'opp_bar': new_opp_bar,
                    'my_off': st['my_off'],
                    'opp_off': st['opp_off'],
                    'dice': st['dice']
                }
                results.append((f"A{p}", new_state))
        elif dest < 0 and can_bear_off and p <= 5:
            # Bearing off
            # Can only bear off from point p if no checkers on higher points in home board
            # or if p is the highest
            higher_occupied = False
            for hp in range(p+1, 6):
                if my_pts[hp] > 0:
                    higher_occupied = True
                    break
            
            if not higher_occupied:
                new_my_pts = list(my_pts)
                new_my_pts[p] -= 1
                
                new_state = {
                    'my_pts': new_my_pts,
                    'opp_pts': list(opp_pts),
                    'my_bar': 0,
                    'opp_bar': st['opp_bar'],
                    'my_off': st['my_off'] + 1,
                    'opp_off': st['opp_off'],
                    'dice': st['dice']
                }
                results.append((f"A{p}", new_state))
    
    return results


def _apply_move(state, move):
    """Apply a move to get the resulting state. Since _get_moves_for_die already
    returns the new state, we just need to extract it from the generation."""
    # Actually, in our generation, we already computed the state. 
    # But since we don't store it with the move string, we need to recompute or change structure.
    # For simplicity, we'll re-simulate.
    order, f1, f2 = move
    
    dice = state['dice']
    if not dice:
        return state
    
    d_sorted = sorted(dice, reverse=True)
    d_high = d_sorted[0]
    d_low = d_sorted[-1] if len(d_sorted) > 1 else d_high
    
    # Determine dice order
    if order == "H":
        first_die, second_die = d_high, d_low
    else:
        first_die, second_die = d_low, d_high
    
    current = state
    
    # Apply first move
    if f1 != "P":
        for from_pos, new_state in _get_moves_for_die(first_die, current):
            if from_pos == f1:
                current = new_state
                break
    
    # Apply second move
    if f2 != "P":
        for from_pos, new_state in _get_moves_for_die(second_die, current):
            if from_pos == f2:
                current = new_state
                break
    
    return current


def _evaluate(st):
    """Evaluate board state from perspective of player to move."""
    score = 0.0
    
    # Pip count (distance to bear off)
    # Point i has distance i+1. Bar has distance 24.
    my_pips = sum((i+1) * st['my_pts'][i] for i in range(24)) + st['my_bar'] * 24
    opp_pips = sum((i+1) * st['opp_pts'][i] for i in range(24)) + st['opp_bar'] * 24
    
    # Race advantage
    score += (opp_pips - my_pips) * 2.0
    
    # Checkers borne off
    score += st['my_off'] * 100.0
    score -= st['opp_off'] * 100.0
    
    # Bar checkers
    score -= st['my_bar'] * 50.0
    score += st['opp_bar'] * 50.0
    
    # Blots (single checkers) - penalty
    my_blots = sum(1 for i in range(24) if st['my_pts'][i] == 1)
    opp_blots = sum(1 for i in range(24) if st['opp_pts'][i] == 1)
    score -= my_blots * 10.0
    score += opp_blots * 10.0
    
    # Home board strength (points 0-5)
    my_home_points = sum(1 for i in range(6) if st['my_pts'][i] >= 2)
    score += my_home_points * 15.0
    
    # Opponent's home board strength (points 18-23 for us, where opp bears off)
    opp_home_points = sum(1 for i in range(18, 24) if st['opp_pts'][i] >= 2)
    score -= opp_home_points * 10.0
    
    # Anchors in opponent's home board (our points 18-23)
    my_anchors = sum(1 for i in range(18, 24) if st['my_pts'][i] >= 2)
    score += my_anchors * 8.0
    
    # Made points in outer board (6-17)
    my_outer = sum(1 for i in range(6, 18) if st['my_pts'][i] >= 2)
    score += my_outer * 3.0
    
    # Prime potential: consecutive made points
    made = [i for i in range(24) if st['my_pts'][i] >= 2]
    for i in range(len(made)-2):
        if made[i+1] == made[i] + 1 and made[i+2] == made[i] + 2:
            score += 10.0  # 3-prime
            if i+3 < len(made) and made[i+3] == made[i] + 3:
                score += 15.0  # 4-prime
                if i+4 < len(made) and made[i+4] == made[i] + 4:
                    score += 20.0  # 5-prime
    
    # Penalty for checkers trapped behind opponent's prime
    # (simplified: checkers on bar or deep in opponent's home)
    
    return score
