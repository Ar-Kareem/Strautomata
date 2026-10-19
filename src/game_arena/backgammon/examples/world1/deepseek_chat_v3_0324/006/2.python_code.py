
import numpy as np

def policy(state):
    # Pre-process state
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    dice = sorted(state['dice'], reverse=True)
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    
    # Check if we have checkers on bar
    if my_bar > 0:
        return handle_bar_reentry(state, my_bar, opp_pts, dice)
    
    # Check bearing off situation
    if can_bear_off(my_pts):
        return handle_bearing_off(state, my_pts, dice)
    
    # Calculate possible moves with evaluation
    best_score = -float('inf')
    best_move = "H:P,P"  # default pass if no legal moves found
    
    # Generate possible move orders (H vs L)
    for order in ['H', 'L']:
        # Generate possible moves for this order
        moves = generate_legal_moves(state, order)
        
        for move in moves:
            score = evaluate_move(move, state)
            if score > best_score:
                best_score = score
                best_move = move
    
    return best_move

def handle_bar_reentry(state, my_bar, opp_pts, dice):
    # Try to re-enter from bar
    entry_points = []
    for die in dice:
        entry = 23 - die + 1  # Convert to opponent's home board
        if entry < 0 or entry >= 24:
            continue  # invalid point
        if opp_pts[entry] < 2:  # Can enter
            entry_points.append(entry)
    
    if not entry_points:
        return "H:P,P"  # can't enter
    
    # Try to enter with highest die first (more flexible)
    attempt_order = ['H', 'L']
    for order in attempt_order:
        if order == 'H':
            die1, die2 = max(dice), min(dice)
        else:
            die1, die2 = min(dice), max(dice)
        
        entry1 = 23 - die1 + 1
        entry2 = 23 - die2 + 1
        
        # Check if we can enter with first die
        if (entry1 >= 0 and entry1 < 24) and opp_pts[entry1] < 2:
            # Try to enter with second die if possible
            if len(dice) == 2 and (entry2 >= 0 and entry2 < 24) and opp_pts[entry2] < 2 and my_bar > 1:
                return f"{order}:B,B"
            else:
                return f"{order}:B,P"
    
    # Shouldn't reach here if entry_points is not empty
    return "H:B,P"

def can_bear_off(my_pts):
    # Check if all checkers are in home board (A0-A5)
    home_points = my_pts[:6]
    outer_points = my_pts[6:]
    return np.sum(outer_points) == 0

def handle_bearing_off(state, my_pts, dice):
    # Simple bearing off strategy
    if not dice:
        return "H:P,P"
    
    home = my_pts[:6]
    available_points = [i for i in range(6) if home[i] > 0]
    
    if not available_points:
        return "H:P,P"
    
    dice = sorted(dice, reverse=True)
    
    # Try to bear off exact rolls first
    for die in dice:
        if die-1 < 6 and home[die-1] > 0:
            other_die = [d for d in dice if d != die][0] if len(dice) > 1 else None
            
            if other_die is not None and other_die-1 < 6 and home[other_die-1] > 0:
                return f"H:A{die-1},A{other_die-1}"
            else:
                return f"H:A{die-1},P"
    
    # If no exact rolls, bear off from highest point
    highest_point = max(available_points)
    if len(dice) == 2:
        return f"H:A{highest_point},A{highest_point}"
    else:
        return f"H:A{highest_point},P"

def generate_legal_moves(state, order):
    # Simplified move generator - returns a list of possible moves for evaluation
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    dice = sorted(state['dice'], reverse=True)
    moves = []
    
    if order == 'H':
        die1, die2 = dice[0], dice[1] if len(dice) > 1 else None
    else:
        die1, die2 = dice[-1], dice[0] if len(dice) > 1 else None
    
    # Generate first move options
    first_options = []
    for from_point in range(24):
        if my_pts[from_point] > 0:
            to_point = from_point - die1
            if to_point >= 0:
                if opp_pts[to_point] < 2:  # Legal move
                    first_options.append(f"A{from_point}")
            elif can_bear_off(state['my_pts']):
                first_options.append(f"A{from_point}")
    
    # Cases splitting
    if not first_options:
        return [f"{order}:P,P"]
    
    if die2 is None:
        for from1 in first_options:
            moves.append(f"{order}:{from1},P")
    else:
        for from1 in first_options:
            from1_idx = int(from1[1:]) if from1 != 'B' else None
            
            # Generate second move options
            second_options = []
            temp_pts = my_pts.copy()
            if from1.startswith('A'):
                temp_pts[int(from1[1:])] -= 1
            
            for from_point in range(24):
                if temp_pts[from_point] > 0:
                    to_point = from_point - die2
                    if to_point >= 0:
                        if opp_pts[to_point] < 2:
                            second_options.append(f"A{from_point}")
                    elif can_bear_off({'my_pts': temp_pts}):
                        second_options.append(f"A{from_point}")
            
            if not second_options:
                moves.append(f"{order}:{from1},P")
            else:
                for from2 in second_options:
                    moves.append(f"{order}:{from1},{from2}")
    
    if not moves:
        moves.append(f"{order}:P,P")
    
    return moves

def evaluate_move(move, state):
    # Basic evaluation function
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    score = 0
    
    # Parse the move
    parts = move.split(':')
    order = parts[0]
    actions = parts[1].split(',')
    
    # Simulate the move
    temp_my_pts = my_pts.copy()
    temp_opp_pts = opp_pts.copy()
    
    for action in actions:
        if action.startswith('A'):
            from_idx = int(action[1:])
            temp_my_pts[from_idx] -= 1
    
    # Score based on various factors
    # 1. Number of points with at least 2 checkers (make points)
    score += 5 * np.sum(temp_my_pts >= 2)
    
    # 2. Distance to bear off (lower is better)
    if can_bear_off({'my_pts': temp_my_pts}):
        score += 1000  # huge bonus for bearing off position
    else:
        distance = np.sum([i * temp_my_pts[i] for i in range(24)])
        score -= distance
    
    # 3. Hitting opponent's blots
    blot_hits = [i for i in range(24) if temp_opp_pts[i] == 1 and temp_my_pts[i] > 0]
    score += 10 * len(blot_hits)
    
    # 4. Avoid leaving blots
    my_blots = [i for i in range(24) if temp_my_pts[i] == 1]
    score -= 8 * len(my_blots)
    
    return score
