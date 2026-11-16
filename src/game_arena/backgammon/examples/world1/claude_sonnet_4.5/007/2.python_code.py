
def policy(state: dict) -> str:
    import random
    
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
    legal_moves = get_legal_moves(state)
    
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
    
    return best_move if best_move else legal_moves[0]


def get_legal_moves(state):
    """Generate all legal moves for current state"""
    dice = state['dice']
    if not dice:
        return ["H:P,P"]
    
    moves = []
    
    # Handle doubles
    if len(dice) == 1:
        dice_to_use = [dice[0]] * 2
    else:
        dice_to_use = sorted(dice, reverse=True)
    
    # Try all combinations
    if len(dice_to_use) == 2:
        # Try H order (higher first)
        for from1 in get_possible_starts(state):
            state1 = apply_single_move(state, from1, dice_to_use[0])
            if state1:
                for from2 in get_possible_starts(state1):
                    state2 = apply_single_move(state1, from2, dice_to_use[1])
                    if state2:
                        moves.append(f"H:{from1},{from2}")
                if not get_possible_starts(state1) or all(not apply_single_move(state1, f, dice_to_use[1]) for f in get_possible_starts(state1)):
                    moves.append(f"H:{from1},P")
        
        # Try L order (lower first)
        for from1 in get_possible_starts(state):
            state1 = apply_single_move(state, from1, dice_to_use[1])
            if state1:
                for from2 in get_possible_starts(state1):
                    state2 = apply_single_move(state1, from2, dice_to_use[0])
                    if state2:
                        moves.append(f"L:{from1},{from2}")
                if not get_possible_starts(state1) or all(not apply_single_move(state1, f, dice_to_use[0]) for f in get_possible_starts(state1)):
                    moves.append(f"L:{from1},P")
    
    if not moves:
        moves.append("H:P,P")
    
    return list(set(moves))


def get_possible_starts(state):
    """Get all possible starting positions"""
    starts = []
    
    if state['my_bar'] > 0:
        return ['B']
    
    for i in range(24):
        if state['my_pts'][i] > 0:
            starts.append(f'A{i}')
    
    return starts if starts else ['P']


def apply_single_move(state, from_pos, die):
    """Apply a single move and return new state, or None if illegal"""
    if from_pos == 'P':
        return None
    
    new_state = {
        'my_pts': state['my_pts'][:],
        'opp_pts': state['opp_pts'][:],
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off'],
        'dice': state['dice']
    }
    
    if from_pos == 'B':
        if new_state['my_bar'] == 0:
            return None
        dest = 24 - die
        if dest < 0 or dest >= 24:
            return None
        if new_state['opp_pts'][23 - dest] >= 2:
            return None
        new_state['my_bar'] -= 1
        new_state['my_pts'][dest] += 1
        return new_state
    
    # Regular move from point
    from_idx = int(from_pos[1:])
    if new_state['my_pts'][from_idx] == 0:
        return None
    
    dest = from_idx - die
    
    # Bearing off
    if dest < 0:
        all_home = all(new_state['my_pts'][i] == 0 for i in range(6, 24)) and new_state['my_bar'] == 0
        if not all_home:
            return None
        if dest == -1 or (dest < -1 and new_state['my_pts'][from_idx] > 0 and all(new_state['my_pts'][i] == 0 for i in range(from_idx + 1, 24))):
            new_state['my_pts'][from_idx] -= 1
            new_state['my_off'] += 1
            return new_state
        return None
    
    # Check if destination is blocked
    if new_state['opp_pts'][23 - dest] >= 2:
        return None
    
    new_state['my_pts'][from_idx] -= 1
    new_state['my_pts'][dest] += 1
    
    return new_state


def evaluate_move(state, move_str):
    """Evaluate the quality of a move"""
    # Simulate the move
    final_state = simulate_move(state, move_str)
    if not final_state:
        return -10000
    
    score = 0
    
    # Pip count (lower is better)
    my_pips = sum(i * final_state['my_pts'][i] for i in range(24)) + final_state['my_bar'] * 25
    score -= my_pips * 2
    
    # Penalize blots heavily
    for i in range(24):
        if final_state['my_pts'][i] == 1:
            exposure = min(6, 23 - i) if i > 5 else 12
            score -= exposure * 15
    
    # Reward made points
    for i in range(24):
        if final_state['my_pts'][i] >= 2:
            score += 10
            if i >= 18:  # Home board
                score += 15
    
    # Reward progress (bearing off)
    score += final_state['my_off'] * 50
    
    # Bonus for hitting opponent
    if final_state['opp_bar'] > state['opp_bar']:
        score += 100
    
    return score


def simulate_move(state, move_str):
    """Simulate a complete move"""
    parts = move_str.split(':')
    order = parts[0]
    froms = parts[1].split(',')
    
    dice = state['dice'] if state['dice'] else []
    if not dice:
        return state
    
    dice_sorted = sorted(dice, reverse=True) if len(dice) > 1 else [dice[0], dice[0]]
    
    if order == 'H':
        dice_order = dice_sorted
    else:
        dice_order = [dice_sorted[1], dice_sorted[0]]
    
    current_state = state
    for i, from_pos in enumerate(froms):
        if from_pos != 'P' and i < len(dice_order):
            current_state = apply_single_move(current_state, from_pos, dice_order[i])
            if not current_state:
                return None
    
    return current_state
