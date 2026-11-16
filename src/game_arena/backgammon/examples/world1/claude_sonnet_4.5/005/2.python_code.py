
def policy(state: dict) -> str:
    import itertools
    
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    # Generate all legal moves
    legal_moves = generate_legal_moves(state)
    
    if not legal_moves:
        return "H:P,P"
    
    # Evaluate and pick best move
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(state, move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def generate_legal_moves(state):
    my_pts = state['my_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    opp_pts = state['opp_pts']
    dice = state['dice']
    
    if not dice:
        return ["H:P,P"]
    
    moves = []
    
    # Handle doubles
    if len(dice) == 2 and dice[0] == dice[1]:
        die = dice[0]
        # Try to use die 4, 3, 2, 1 times
        for num_uses in [4, 3, 2, 1]:
            submoves = try_n_moves(my_pts[:], opp_pts, my_bar, my_off, die, num_uses)
            if submoves:
                moves.extend(submoves)
                break
        if not moves:
            moves.append("H:P,P")
        return moves
    
    # Regular dice
    if len(dice) == 1:
        die = dice[0]
        submoves = try_n_moves(my_pts[:], opp_pts, my_bar, my_off, die, 1)
        if submoves:
            return submoves
        return ["H:P,P"]
    
    # Two different dice
    d1, d2 = dice[0], dice[1]
    higher = max(d1, d2)
    lower = min(d1, d2)
    
    # Try both orders
    # H: higher first
    h_moves = try_two_dice(my_pts[:], opp_pts, my_bar, my_off, higher, lower, "H")
    # L: lower first
    l_moves = try_two_dice(my_pts[:], opp_pts, my_bar, my_off, lower, higher, "L")
    
    moves = h_moves + l_moves
    if not moves:
        moves.append("H:P,P")
    
    return moves

def try_two_dice(my_pts, opp_pts, my_bar, my_off, first_die, second_die, order):
    results = []
    
    # Get possible first moves
    first_froms = get_possible_moves(my_pts, opp_pts, my_bar, my_off, first_die)
    
    for from1 in first_froms:
        # Apply first move
        pts1, bar1, off1 = apply_move(my_pts[:], my_bar, my_off, from1, first_die)
        
        # Get possible second moves
        second_froms = get_possible_moves(pts1, opp_pts, bar1, off1, second_die)
        
        for from2 in second_froms:
            results.append(f"{order}:{from1},{from2}")
    
    # If no second move possible, try just first
    if not results and first_froms:
        for from1 in first_froms:
            results.append(f"{order}:{from1},P")
    
    return results

def try_n_moves(my_pts, opp_pts, my_bar, my_off, die, n):
    if n == 0:
        return []
    
    results = []
    froms = get_possible_moves(my_pts, opp_pts, my_bar, my_off, die)
    
    for from_pt in froms:
        pts1, bar1, off1 = apply_move(my_pts[:], my_bar, my_off, from_pt, die)
        
        if n == 1:
            results.append(f"H:{from_pt},P")
        else:
            # Recursively try remaining moves
            sub = try_n_moves_helper(pts1, opp_pts, bar1, off1, die, n-1, [from_pt])
            results.extend(sub)
    
    return results

def try_n_moves_helper(my_pts, opp_pts, my_bar, my_off, die, remaining, path):
    if remaining == 0:
        move_str = ",".join(path) + ",P" * (4 - len(path))
        return [f"H:{move_str}"[:move_str.index(',P,P')] if ',P,P' in move_str else f"H:{move_str}"]
    
    results = []
    froms = get_possible_moves(my_pts, opp_pts, my_bar, my_off, die)
    
    if not froms:
        move_str = ",".join(path + ["P"] * remaining)
        return [f"H:{move_str}"]
    
    for from_pt in froms:
        pts1, bar1, off1 = apply_move(my_pts[:], my_bar, my_off, from_pt, die)
        sub = try_n_moves_helper(pts1, opp_pts, bar1, off1, die, remaining-1, path + [from_pt])
        results.extend(sub)
    
    return results

def get_possible_moves(my_pts, opp_pts, my_bar, my_off, die):
    froms = []
    
    # Must move from bar first
    if my_bar > 0:
        target = 24 - die
        if target >= 0 and opp_pts[target] < 2:
            froms.append("B")
        return froms
    
    # Check if bearing off
    can_bear_off = all(my_pts[i] == 0 for i in range(6, 24))
    
    for i in range(24):
        if my_pts[i] == 0:
            continue
        
        target = i - die
        
        if target < 0:
            # Bearing off
            if can_bear_off:
                # Can bear off if exact or if no checkers behind
                if target == -1 or all(my_pts[j] == 0 for j in range(i+1, 24)):
                    froms.append(f"A{i}")
        else:
            # Regular move
            if opp_pts[target] < 2:
                froms.append(f"A{i}")
    
    if not froms:
        froms.append("P")
    
    return froms

def apply_move(my_pts, my_bar, my_off, from_str, die):
    pts = my_pts[:]
    bar = my_bar
    off = my_off
    
    if from_str == "P":
        return pts, bar, off
    
    if from_str == "B":
        bar -= 1
        target = 24 - die
        pts[target] += 1
    else:
        start = int(from_str[1:])
        pts[start] -= 1
        target = start - die
        if target < 0:
            off += 1
        else:
            pts[target] += 1
    
    return pts, bar, off

def evaluate_move(state, move_str):
    # Simulate the move and evaluate resulting position
    my_pts = state['my_pts'][:]
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    opp_bar = state['opp_bar']
    dice = state['dice']
    
    # Parse and apply move
    parts = move_str.split(':')
    order = parts[0]
    froms = parts[1].split(',')
    
    if len(dice) == 2 and dice[0] == dice[1]:
        die = dice[0]
        for from_str in froms:
            if from_str != 'P':
                my_pts, my_bar, my_off = apply_move(my_pts, my_bar, my_off, from_str, die)
    else:
        d1, d2 = (dice[0], dice[0]) if len(dice) == 1 else (max(dice), min(dice))
        dies = [d1, d2] if order == 'H' else [d2, d1]
        for i, from_str in enumerate(froms[:2]):
            if from_str != 'P' and i < len(dies):
                my_pts, my_bar, my_off = apply_move(my_pts, my_bar, my_off, from_str, dies[i])
    
    score = 0
    
    # Pip count (lower is better)
    my_pips = sum((23-i+1) * my_pts[i] for i in range(24)) + my_bar * 25
    opp_pips = sum((i+1) * opp_pts[i] for i in range(24)) + opp_bar * 25
    score -= my_pips * 2
    score += (opp_pips - my_pips) * 0.5
    
    # Blots (single checkers) are bad
    blots = sum(1 for i in range(24) if my_pts[i] == 1)
    score -= blots * 15
    
    # Points (2+ checkers) are good
    points = sum(1 for i in range(24) if my_pts[i] >= 2)
    score += points * 5
    
    # Home board strength when opponent on bar
    if opp_bar > 0:
        home_strength = sum(1 for i in range(6) if my_pts[i] >= 2)
        score += home_strength * 20
    
    # Progress toward bearing off
    score += my_off * 50
    
    return score
