
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
    
    # Evaluate and choose best move
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(state, move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else "H:P,P"


def generate_legal_moves(state):
    """Generate all legal moves for the current state."""
    my_pts = state['my_pts']
    my_bar = state['my_bar']
    opp_pts = state['opp_pts']
    dice = state['dice']
    
    if not dice:
        return ["H:P,P"]
    
    if len(dice) == 1:
        dice = dice + dice  # Doubles
    
    moves = []
    die1, die2 = sorted(dice, reverse=True)
    
    # Try both orderings
    for order in ['H', 'L']:
        if order == 'H':
            first_die, second_die = die1, die2
        else:
            first_die, second_die = die2, die1
        
        # Generate moves with this ordering
        first_moves = get_single_moves(my_pts, opp_pts, my_bar, first_die)
        
        for from1 in first_moves:
            # Apply first move
            new_my_pts, new_my_bar, new_opp_pts = apply_move(my_pts[:], opp_pts[:], my_bar, from1, first_die)
            
            # Get second moves
            second_moves = get_single_moves(new_my_pts, new_opp_pts, new_my_bar, second_die)
            
            for from2 in second_moves:
                moves.append(f"{order}:{from1},{from2}")
            
            # If no second move possible, try pass
            if not second_moves:
                moves.append(f"{order}:{from1},P")
    
    # If no two-move combinations, try single moves
    if not moves:
        for die in [die1, die2]:
            single_moves = get_single_moves(my_pts, opp_pts, my_bar, die)
            for from1 in single_moves:
                order = 'H' if die == die1 else 'L'
                moves.append(f"{order}:{from1},P")
    
    if not moves:
        moves.append("H:P,P")
    
    return moves


def get_single_moves(my_pts, opp_pts, my_bar, die):
    """Get all possible single moves for a given die."""
    moves = []
    
    # Must move from bar first
    if my_bar > 0:
        dest = 24 - die
        if dest >= 0 and opp_pts[dest] < 2:
            moves.append('B')
        return moves
    
    # Check if we can bear off
    can_bear_off = all(my_pts[i] == 0 for i in range(6, 24))
    
    for pos in range(24):
        if my_pts[pos] == 0:
            continue
        
        dest = pos - die
        
        if dest < 0:
            # Bearing off
            if can_bear_off:
                # Can bear off from this position if it's exact or highest
                if dest == -1 or (pos < die and all(my_pts[i] == 0 for i in range(pos + 1, 24))):
                    moves.append(f'A{pos}')
        elif opp_pts[dest] < 2:
            moves.append(f'A{pos}')
    
    if not moves:
        moves.append('P')
    
    return moves


def apply_move(my_pts, opp_pts, my_bar, from_loc, die):
    """Apply a single move and return new state."""
    new_my_pts = my_pts[:]
    new_opp_pts = opp_pts[:]
    new_my_bar = my_bar
    
    if from_loc == 'P':
        return new_my_pts, new_my_bar, new_opp_pts
    
    if from_loc == 'B':
        new_my_bar -= 1
        dest = 24 - die
        if dest >= 0:
            if new_opp_pts[dest] == 1:
                new_opp_pts[dest] = 0
            new_my_pts[dest] += 1
    else:
        pos = int(from_loc[1:])
        new_my_pts[pos] -= 1
        dest = pos - die
        if dest >= 0:
            if new_opp_pts[dest] == 1:
                new_opp_pts[dest] = 0
            new_my_pts[dest] += 1
    
    return new_my_pts, new_my_bar, new_opp_pts


def evaluate_move(state, move_str):
    """Evaluate a move and return a score."""
    # Simulate the move
    new_state = simulate_move(state, move_str)
    
    score = 0.0
    my_pts = new_state['my_pts']
    opp_pts = new_state['opp_pts']
    
    # Pip count (lower is better)
    my_pips = sum((23 - i + 1) * my_pts[i] for i in range(24)) + 25 * new_state['my_bar']
    opp_pips = sum((i + 1) * opp_pts[i] for i in range(24)) + 25 * new_state['opp_bar']
    score -= my_pips * 0.5
    
    # Bonus for bearing off
    score += new_state['my_off'] * 100
    
    # Penalty for blots (exposed checkers)
    for i in range(24):
        if my_pts[i] == 1:
            # Worse if in opponent's home or exposed to opponent
            exposure = min(6, 24 - i)
            score -= exposure * 15
    
    # Bonus for made points (2+ checkers)
    for i in range(24):
        if my_pts[i] >= 2:
            score += 10
            # Extra bonus for home board points
            if i < 6:
                score += 15
    
    # Penalty for checkers on bar
    score -= new_state['my_bar'] * 50
    
    # Bonus for hitting opponent
    score += new_state['opp_bar'] * 40
    
    return score


def simulate_move(state, move_str):
    """Simulate a move and return the resulting state."""
    parts = move_str.split(':')
    order = parts[0]
    froms = parts[1].split(',')
    
    dice = state['dice'][:]
    if len(dice) == 1:
        dice = dice + dice
    
    die1, die2 = sorted(dice, reverse=True)
    if order == 'H':
        dies = [die1, die2]
    else:
        dies = [die2, die1]
    
    new_my_pts = state['my_pts'][:]
    new_opp_pts = state['opp_pts'][:]
    new_my_bar = state['my_bar']
    new_opp_bar = state['opp_bar']
    new_my_off = state['my_off']
    
    for from_loc, die in zip(froms, dies):
        new_my_pts, new_my_bar, new_opp_pts = apply_move(new_my_pts, new_opp_pts, new_my_bar, from_loc, die)
        # Check for bearing off
        if from_loc != 'P' and from_loc != 'B':
            pos = int(from_loc[1:])
            if pos - die < 0:
                new_my_off += 1
    
    new_opp_bar = sum(1 for i in range(24) if state['opp_pts'][i] > new_opp_pts[i])
    
    return {
        'my_pts': new_my_pts,
        'opp_pts': new_opp_pts,
        'my_bar': new_my_bar,
        'opp_bar': new_opp_bar,
        'my_off': new_my_off,
        'opp_off': state['opp_off'],
        'dice': []
    }
