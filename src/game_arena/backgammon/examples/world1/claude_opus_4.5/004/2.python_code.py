
import copy

def policy(state: dict) -> str:
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    # Generate all legal moves and pick the best one
    legal_moves = generate_legal_moves(state)
    
    if not legal_moves:
        return "H:P,P"
    
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        new_state = apply_move(state, move)
        score = evaluate_position(new_state, state)
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move, dice)

def generate_legal_moves(state):
    dice = state['dice']
    if not dice:
        return [('H', 'P', 'P')]
    
    if len(dice) == 1:
        moves = generate_single_die_moves(state, dice[0])
        if moves:
            return [('H', m, 'P') for m in moves]
        return [('H', 'P', 'P')]
    
    d1, d2 = dice[0], dice[1]
    high_die = max(d1, d2)
    low_die = min(d1, d2)
    
    # Try using both dice
    all_moves = []
    
    # High first, then low
    first_moves_h = generate_single_die_moves(state, high_die)
    for m1 in first_moves_h:
        new_state = apply_single_move(state, m1, high_die)
        second_moves = generate_single_die_moves(new_state, low_die)
        for m2 in second_moves:
            all_moves.append(('H', m1, m2))
        if not second_moves:
            all_moves.append(('H', m1, 'P'))
    
    # Low first, then high
    first_moves_l = generate_single_die_moves(state, low_die)
    for m1 in first_moves_l:
        new_state = apply_single_move(state, m1, low_die)
        second_moves = generate_single_die_moves(new_state, high_die)
        for m2 in second_moves:
            all_moves.append(('L', m1, m2))
        if not second_moves:
            all_moves.append(('L', m1, 'P'))
    
    if not all_moves:
        return [('H', 'P', 'P')]
    
    # Prefer moves that use both dice
    two_dice_moves = [m for m in all_moves if m[2] != 'P']
    if two_dice_moves:
        return two_dice_moves
    
    # Must use higher die if only one can be played
    high_only = [m for m in all_moves if m[0] == 'H' and m[1] != 'P']
    low_only = [m for m in all_moves if m[0] == 'L' and m[1] != 'P']
    
    if high_only:
        return high_only
    if low_only:
        return low_only
    
    return [('H', 'P', 'P')]

def generate_single_die_moves(state, die):
    moves = []
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    
    if my_bar > 0:
        entry_point = 24 - die
        if opp_pts[entry_point] < 2:
            moves.append('B')
        return moves
    
    all_home = all(my_pts[i] == 0 for i in range(6, 24))
    
    for i in range(24):
        if my_pts[i] > 0:
            dest = i - die
            if dest >= 0:
                if opp_pts[dest] < 2:
                    moves.append(f'A{i}')
            elif all_home:
                # Bearing off
                if dest == -1 or (i == max(j for j in range(6) if my_pts[j] > 0) and dest < 0):
                    moves.append(f'A{i}')
    
    return moves

def apply_single_move(state, move, die):
    new_state = {
        'my_pts': state['my_pts'][:],
        'opp_pts': state['opp_pts'][:],
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off'],
        'dice': state['dice'][:]
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

def apply_move(state, move):
    order, m1, m2 = move
    dice = state['dice']
    if len(dice) < 2:
        d1 = dice[0] if dice else 0
        d2 = 0
    else:
        d1, d2 = dice[0], dice[1]
    
    high_die = max(d1, d2) if d2 else d1
    low_die = min(d1, d2) if d2 else 0
    
    if order == 'H':
        new_state = apply_single_move(state, m1, high_die)
        new_state = apply_single_move(new_state, m2, low_die)
    else:
        new_state = apply_single_move(state, m1, low_die)
        new_state = apply_single_move(new_state, m2, high_die)
    
    return new_state

def evaluate_position(state, old_state):
    score = 0
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    
    # Borne off checkers are great
    score += state['my_off'] * 100
    
    # Checkers on bar are bad
    score -= state['my_bar'] * 50
    
    # Opponent on bar is good
    score += state['opp_bar'] * 30
    
    # Evaluate positions
    for i in range(24):
        if my_pts[i] > 0:
            # Progress toward home (lower index is better)
            score -= i * my_pts[i] * 0.5
            
            # Blots are bad, especially far from home
            if my_pts[i] == 1:
                danger = sum(1 for j in range(i+1, min(i+7, 24)) if opp_pts[j] > 0)
                score -= danger * (24 - i) * 0.3
            
            # Made points are good
            if my_pts[i] >= 2:
                score += 5
                if i <= 5:  # Home board points
                    score += 8
                if i == 4 or i == 5:  # Key points
                    score += 5
    
    return score

def format_move(move, dice):
    order, m1, m2 = move
    return f"{order}:{m1},{m2}"
