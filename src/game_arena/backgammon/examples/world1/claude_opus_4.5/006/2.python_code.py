
import itertools

def policy(state: dict) -> str:
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    legal_moves = generate_legal_moves(state, dice)
    
    if not legal_moves:
        return "H:P,P"
    
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        new_state = simulate_move(state, move, dice)
        score = evaluate(new_state)
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        return "H:P,P"
    
    return format_move(best_move, dice)

def generate_legal_moves(state, dice):
    if not dice:
        return [('H', 'P', 'P')]
    
    moves = []
    
    if len(dice) == 1:
        d = dice[0]
        single_moves = get_single_die_moves(state, d)
        for m in single_moves:
            moves.append(('H', m, 'P'))
        if not moves:
            moves.append(('H', 'P', 'P'))
    else:
        d1, d2 = dice[0], dice[1]
        high_die = max(d1, d2)
        low_die = min(d1, d2)
        
        # Try high die first, then low die
        for m1 in get_single_die_moves(state, high_die) or ['P']:
            state1 = apply_single_move(state, m1, high_die)
            for m2 in get_single_die_moves(state1, low_die) or ['P']:
                moves.append(('H', m1, m2))
        
        # Try low die first, then high die
        for m1 in get_single_die_moves(state, low_die) or ['P']:
            state1 = apply_single_move(state, m1, low_die)
            for m2 in get_single_die_moves(state1, high_die) or ['P']:
                moves.append(('L', m1, m2))
        
        # Filter: prefer moves that use both dice, then one die (prefer higher)
        two_die_moves = [m for m in moves if m[1] != 'P' and m[2] != 'P']
        if two_die_moves:
            moves = two_die_moves
        else:
            one_die_moves = [m for m in moves if m[1] != 'P' or m[2] != 'P']
            if one_die_moves:
                # Prefer higher die
                high_moves = [m for m in one_die_moves if (m[0] == 'H' and m[1] != 'P') or (m[0] == 'L' and m[2] != 'P')]
                moves = high_moves if high_moves else one_die_moves
    
    if not moves:
        moves = [('H', 'P', 'P')]
    
    return list(set(moves))

def get_single_die_moves(state, die):
    moves = []
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    
    if my_bar > 0:
        # Must enter from bar
        entry_point = 24 - die
        if entry_point >= 0 and opp_pts[entry_point] < 2:
            moves.append('B')
    else:
        # Check if can bear off
        all_home = all(my_pts[i] == 0 for i in range(6, 24)) and my_bar == 0
        
        for i in range(24):
            if my_pts[i] > 0:
                dest = i - die
                if dest >= 0:
                    if opp_pts[dest] < 2:
                        moves.append(f'A{i}')
                elif all_home and i < 6:
                    # Bearing off
                    if dest == -1 or (die > i and all(my_pts[j] == 0 for j in range(i+1, 6))):
                        moves.append(f'A{i}')
    
    return moves

def apply_single_move(state, move, die):
    new_state = {
        'my_pts': list(state['my_pts']),
        'opp_pts': list(state['opp_pts']),
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off'],
        'dice': state['dice']
    }
    
    if move == 'P':
        return new_state
    
    if move == 'B':
        new_state['my_bar'] -= 1
        dest = 24 - die
        if new_state['opp_pts'][dest] == 1:
            new_state['opp_pts'][dest] = 0
            new_state['opp_bar'] += 1
        new_state['my_pts'][dest] += 1
    else:
        src = int(move[1:])
        new_state['my_pts'][src] -= 1
        dest = src - die
        if dest >= 0:
            if new_state['opp_pts'][dest] == 1:
                new_state['opp_pts'][dest] = 0
                new_state['opp_bar'] += 1
            new_state['my_pts'][dest] += 1
        else:
            new_state['my_off'] += 1
    
    return new_state

def simulate_move(state, move, dice):
    order, m1, m2 = move
    if len(dice) == 0:
        return state
    elif len(dice) == 1:
        return apply_single_move(state, m1, dice[0])
    else:
        d1, d2 = dice[0], dice[1]
        high_die, low_die = max(d1, d2), min(d1, d2)
        if order == 'H':
            s1 = apply_single_move(state, m1, high_die)
            return apply_single_move(s1, m2, low_die)
        else:
            s1 = apply_single_move(state, m1, low_die)
            return apply_single_move(s1, m2, high_die)

def evaluate(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    
    score = 0
    
    # Pip count (lower is better)
    pip_count = sum((i + 1) * my_pts[i] for i in range(24)) + 25 * my_bar
    score -= pip_count * 0.5
    
    # Borne off checkers
    score += my_off * 20
    
    # Bar penalty
    score -= my_bar * 30
    
    # Blot penalty
    for i in range(24):
        if my_pts[i] == 1:
            danger = min(i + 1, 12)  # More dangerous closer to opponent
            score -= danger * 2
    
    # Made points bonus
    for i in range(24):
        if my_pts[i] >= 2:
            if i < 6:  # Home board
                score += 8
            elif i < 12:
                score += 5
            else:
                score += 3
    
    # Prime detection (consecutive made points)
    consecutive = 0
    for i in range(24):
        if my_pts[i] >= 2:
            consecutive += 1
            if consecutive >= 3:
                score += consecutive * 5
        else:
            consecutive = 0
    
    return score

def format_move(move, dice):
    order, m1, m2 = move
    return f"{order}:{m1},{m2}"
