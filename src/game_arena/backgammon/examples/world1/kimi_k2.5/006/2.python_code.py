
import copy

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    if len(dice) == 1:
        d = dice[0]
        moves = generate_single_moves(state, d)
        if moves:
            src = moves[0]
            return f"H:{src},P"
        else:
            return "H:P,P"
    
    d1, d2 = dice[0], dice[1]
    d_high = max(d1, d2)
    d_low = min(d1, d2)
    
    candidates = []
    
    # Try H order: high first, low second
    moves_h = generate_move_pairs(state, d_high, d_low)
    for src1, src2 in moves_h:
        candidates.append(("H", src1, src2))
    
    # Try L order: low first, high second (only if different)
    if d_high != d_low:
        moves_l = generate_move_pairs(state, d_low, d_high)
        for src1, src2 in moves_l:
            candidates.append(("L", src1, src2))
    
    # Try partial: only high die (if high is playable)
    single_high = generate_single_moves(state, d_high)
    for src in single_high:
        candidates.append(("H", src, "P"))
    
    # Try partial: only low die (only if high is not playable)
    if not single_high:
        single_low = generate_single_moves(state, d_low)
        for src in single_low:
            candidates.append(("H", "P", src))
    
    if not candidates:
        return "H:P,P"
    
    # Evaluate all candidates and pick the best
    best_move = None
    best_score = -float('inf')
    
    for order, src1, src2 in candidates:
        new_state = simulate_move(state, order, src1, src2, d_high, d_low)
        score = evaluate_state(new_state)
        if score > best_score:
            best_score = score
            best_move = (order, src1, src2)
    
    if best_move is None:
        return "H:P,P"
    
    return f"{best_move[0]}:{best_move[1]},{best_move[2]}"

def simulate_move(state, order, src1, src2, d_high, d_low):
    """Simulate the move and return new state"""
    s = copy.deepcopy(state)
    
    if order == "H":
        d1, d2 = d_high, d_low
    else:
        d1, d2 = d_low, d_high
    
    # First move
    if src1 != "P":
        s = apply_single_move(s, src1, d1)
    
    # Second move
    if src2 != "P":
        s = apply_single_move(s, src2, d2)
    
    return s

def apply_single_move(s, src, die):
    """Apply a single checker move to state copy"""
    if src == "B":
        # Enter from bar
        dest = 24 - die
        s['my_bar'] -= 1
        # Check for hit
        if s['opp_pts'][dest] == 1:
            s['opp_pts'][dest] = 0
            s['opp_bar'] += 1
        s['my_pts'][dest] += 1
    else:
        # From board
        idx = int(src[1:])
        s['my_pts'][idx] -= 1
        dest = idx - die
        
        if dest < 0:
            # Bearing off
            s['my_off'] += 1
        else:
            # Normal move
            if s['opp_pts'][dest] == 1:
                s['opp_pts'][dest] = 0
                s['opp_bar'] += 1
            s['my_pts'][dest] += 1
    
    return s

def generate_single_moves(state, die):
    """Generate all legal single moves for a die. Returns list of sources like 'A5' or 'B'"""
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    moves = []
    
    if my_bar > 0:
        dest = 24 - die
        if 18 <= dest <= 23 and opp_pts[dest] <= 1:
            moves.append("B")
    else:
        # Check if all in home board
        all_home = (sum(my_pts[6:]) == 0 and my_bar == 0)
        
        # Find furthest checker in home board for bearing off rules
        max_home = -1
        if all_home:
            for i in range(5, -1, -1):
                if my_pts[i] > 0:
                    max_home = i
                    break
        
        for i in range(24):
            if my_pts[i] == 0:
                continue
            dest = i - die
            if dest >= 0:
                if opp_pts[dest] <= 1:
                    moves.append(f"A{i}")
            else:
                # Bearing off
                if all_home and die >= i + 1:
                    # Can bear off if exact or if this is the furthest point
                    if i == max_home or die == i + 1:
                        moves.append(f"A{i}")
    
    return moves

def generate_move_pairs(state, d1, d2):
    """Generate pairs (src1, src2) for using d1 then d2"""
    pairs = []
    first_moves = generate_single_moves(state, d1)
    
    for src1 in first_moves:
        # Apply first move to get intermediate state
        temp_state = copy.deepcopy(state)
        temp_state = apply_single_move(temp_state, src1, d1)
        second_moves = generate_single_moves(temp_state, d2)
        
        if second_moves:
            for src2 in second_moves:
                pairs.append((src1, src2))
        else:
            # Only first move is valid (d2 blocked), still valid partial
            pairs.append((src1, "P"))
    
    # Also consider if first is blocked but wait, generate_single_moves returns empty if blocked
    return pairs

def evaluate_state(s):
    """Evaluate board state from perspective of player to move"""
    my_pts = s['my_pts']
    opp_pts = s['opp_pts']
    my_bar = s['my_bar']
    opp_bar = s['opp_bar']
    my_off = s['my_off']
    opp_off = s['opp_off']
    
    # Terminal evaluation
    if my_off >= 15:
        return 10000
    if opp_off >= 15:
        return -10000
    
    score = 0
    
    # Pip count (lower is better)
    my_pips = my_bar * 25
    opp_pips = opp_bar * 25
    
    for i in range(24):
        my_pips += my_pts[i] * (i + 1)
        opp_pips += opp_pts[i] * (24 - i)  # Opponent moves 0->23, so distance is 24-i
    
    score -= my_pips * 2
    score += opp_pips * 2
    
    # Checkers borne off
    score += my_off * 50
    score -= opp_off * 50
    
    # Home board strength (points 0-5)
    my_home_blocks = 0
    for i in range(6):
        if my_pts[i] >= 2:
            my_home_blocks += 1
            score += 3
        elif my_pts[i] == 1:
            score -= 1  # Single in home board is okay but not great
    score += my_home_blocks * 5
    
    # Anchors in opponent home (points 18-23)
    for i in range(18, 24):
        if my_pts[i] >= 2:
            score += 4  # Good anchor
    
    # Blots - penalize single checkers, especially exposed ones
    for i in range(24):
        if my_pts[i] == 1:
            # Higher penalty for blots further back
            penalty = 2
            if i >= 18:  # opponent home board
                penalty = 5
            elif i >= 6:  # outer board
                penalty = 3
            score -= penalty
        
        if opp_pts[i] == 1:
            # Opportunity to hit
            score += 2
    
    # Bar advantage
    score -= my_bar * 3
    score += opp_bar * 3
    
    # Race strategy adjustment: if ahead in pip count, bear off aggressively
    pip_diff = opp_pips - my_pips
    if pip_diff > 20:  # We're significantly ahead
        score += my_off * 10  # Extra weight on bearing off
    
    return score
