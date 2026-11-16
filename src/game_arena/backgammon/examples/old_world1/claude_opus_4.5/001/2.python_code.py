
import itertools

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    # Generate all possible moves and evaluate them
    moves = generate_legal_moves(state)
    
    if not moves:
        return "H:P,P"
    
    best_move = None
    best_score = float('-inf')
    
    for move in moves:
        new_state = apply_move(state, move)
        score = evaluate_position(new_state, state)
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move, dice)

def generate_legal_moves(state):
    dice = state['dice']
    if not dice:
        return [('P', 'P')]
    
    if len(dice) == 1:
        d = dice[0]
        moves = get_single_die_moves(state, d)
        if moves:
            return [(m, 'P') for m in moves]
        return [('P', 'P')]
    
    d1, d2 = dice[0], dice[1]
    high_die = max(d1, d2)
    low_die = min(d1, d2)
    
    all_moves = []
    
    # Try high die first, then low die
    for m1 in get_single_die_moves(state, high_die):
        new_state = apply_single_move(state, m1, high_die)
        for m2 in get_single_die_moves(new_state, low_die):
            all_moves.append((m1, m2, 'H'))
    
    # Try low die first, then high die
    for m1 in get_single_die_moves(state, low_die):
        new_state = apply_single_move(state, m1, low_die)
        for m2 in get_single_die_moves(new_state, high_die):
            all_moves.append((m1, m2, 'L'))
    
    if all_moves:
        return all_moves
    
    # Try single die moves (must use higher if possible)
    high_moves = get_single_die_moves(state, high_die)
    if high_moves:
        return [(m, 'P', 'H') for m in high_moves]
    
    low_moves = get_single_die_moves(state, low_die)
    if low_moves:
        return [(m, 'P', 'L') for m in low_moves]
    
    return [('P', 'P', 'H')]

def get_single_die_moves(state, die):
    my_pts = list(state['my_pts'])
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    moves = []
    
    # Must move from bar first
    if my_bar > 0:
        dest = die - 1  # Points 0-5 are opponent's home (my entry)
        if dest < 24 and opp_pts[dest] < 2:
            moves.append('B')
        return moves
    
    # Check if can bear off
    can_bear_off = all_in_home(my_pts)
    
    for i in range(24):
        if my_pts[i] > 0:
            dest = i + die
            if dest < 24:
                if opp_pts[dest] < 2:
                    moves.append(f'A{i}')
            elif can_bear_off:
                # Bearing off
                home_start = 18
                if i >= home_start:
                    if dest == 24:
                        moves.append(f'A{i}')
                    elif dest > 24:
                        # Can only bear off if no checkers on higher points
                        higher_exists = any(my_pts[j] > 0 for j in range(i+1, 24))
                        if not higher_exists:
                            moves.append(f'A{i}')
    
    return moves

def all_in_home(my_pts):
    # Home board is points 18-23
    for i in range(18):
        if my_pts[i] > 0:
            return False
    return True

def apply_single_move(state, move, die):
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    my_off = state['my_off']
    opp_bar = state['opp_bar']
    
    if move == 'P':
        pass
    elif move == 'B':
        my_bar -= 1
        dest = die - 1
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            opp_bar += 1
        my_pts[dest] += 1
    else:
        src = int(move[1:])
        my_pts[src] -= 1
        dest = src + die
        if dest < 24:
            if opp_pts[dest] == 1:
                opp_pts[dest] = 0
                opp_bar += 1
            my_pts[dest] += 1
        else:
            my_off += 1
    
    return {
        'my_pts': my_pts,
        'opp_pts': opp_pts,
        'my_bar': my_bar,
        'opp_bar': opp_bar,
        'my_off': my_off,
        'opp_off': state['opp_off'],
        'dice': state['dice']
    }

def apply_move(state, move):
    dice = state['dice']
    if len(dice) == 0:
        return state
    
    if len(move) == 2:
        m1, m2 = move
        d1 = dice[0] if len(dice) > 0 else 0
        d2 = dice[1] if len(dice) > 1 else 0
        high_die = max(d1, d2) if d1 and d2 else d1
        low_die = min(d1, d2) if d1 and d2 else 0
        new_state = apply_single_move(state, m1, high_die)
        if m2 != 'P' and low_die:
            new_state = apply_single_move(new_state, m2, low_die)
        return new_state
    else:
        m1, m2, order = move
        d1, d2 = dice[0], dice[1]
        high_die = max(d1, d2)
        low_die = min(d1, d2)
        if order == 'H':
            new_state = apply_single_move(state, m1, high_die)
            if m2 != 'P':
                new_state = apply_single_move(new_state, m2, low_die)
        else:
            new_state = apply_single_move(state, m1, low_die)
            if m2 != 'P':
                new_state = apply_single_move(new_state, m2, high_die)
        return new_state

def evaluate_position(new_state, old_state):
    my_pts = new_state['my_pts']
    opp_pts = new_state['opp_pts']
    my_bar = new_state['my_bar']
    my_off = new_state['my_off']
    opp_bar = new_state['opp_bar']
    
    score = 0
    
    # Bearing off is great
    score += my_off * 100
    
    # Being on bar is bad
    score -= my_bar * 50
    
    # Opponent on bar is good
    score += opp_bar * 30
    
    # Progress toward home
    for i in range(24):
        if my_pts[i] > 0:
            score += my_pts[i] * (i + 1) * 2  # Higher index = closer to bearing off
    
    # Blot penalty
    for i in range(24):
        if my_pts[i] == 1:
            # More dangerous if opponent can hit
            danger = 0
            for j in range(max(0, i-6), i):
                if opp_pts[j] > 0:
                    danger += 5
            if opp_bar > 0 and i < 6:
                danger += 10
            score -= danger
    
    # Made points are good
    for i in range(24):
        if my_pts[i] >= 2:
            score += 10
            if i >= 18:  # Home board points
                score += 5
    
    return score

def format_move(move, dice):
    if len(move) == 2:
        m1, m2 = move
        return f"H:{m1},{m2}"
    else:
        m1, m2, order = move
        return f"{order}:{m1},{m2}"
