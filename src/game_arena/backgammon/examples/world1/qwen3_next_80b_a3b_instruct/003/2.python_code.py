
import numpy as np

def policy(state: dict) -> str:
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'])  # Sort to easily identify L and H
    if len(dice) == 0:
        return "H:P,P"  # No dice, must pass
    
    # Determine which is higher and lower die
    low_die, high_die = dice[0], dice[-1]
    
    # If checkers are on the bar, must re-enter first
    if my_bar > 0:
        # Try to re-enter on points accessible with either die
        legal_moves = []
        
        # Try with higher die first
        for die in [high_die, low_die]:
            point_to_enter = 24 - die  # Re-entry point from bar
            if point_to_enter >= 0 and point_to_enter <= 23:
                # Check if point is not blocked (opponent has < 2 checkers)
                if opp_pts[point_to_enter] < 2:
                    # Re-entering is possible
                    # We'll try to form a sequence of moves: re-enter with one die, then use the other if possible
                    # First, just plan a single re-entry move
                    if die == high_die:
                        move_str = f"H:B,P"
                    else:
                        move_str = f"L:B,P"
                    # But we need to see if we can use both dice
                    # After re-entering, can we make a second move?
                    temp_my_pts = my_pts.copy()
                    temp_my_pts[point_to_enter] += 1
                    remaining_die = low_die if die == high_die else high_die
                    second_moves = get_legal_second_moves(temp_my_pts, opp_pts, remaining_die, from_bar=False)
                    if len(second_moves) > 0:
                        # We can use both dice
                        move_str = f"H:B,{second_moves[0]}" if die == high_die else f"L:B,{second_moves[0]}"
                    else:
                        # Can't use both dice, but still must use one
                        if die == high_die:
                            move_str = f"H:B,P"
                        else:
                            move_str = f"L:B,P"
                    return move_str
        
        # If we can't re-enter with either die, must pass (should be impossible per rules)
        return "H:P,P"
    
    # No checkers on bar, now consider normal moves
    all_legal_moves = get_all_legal_moves(my_pts, opp_pts, dice)
    if len(all_legal_moves) == 0:
        return "H:P,P"
    
    # Evaluate all legal moves and choose best one
    best_move = None
    best_score = -float('inf')
    
    for move in all_legal_moves:
        score = evaluate_move(move, my_pts, opp_pts, dice)
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        return "H:P,P"
    
    return best_move

def get_all_legal_moves(my_pts, opp_pts, dice):
    """Generate all possible legal move sequences given dice"""
    moves = []
    low_die, high_die = min(dice), max(dice)
    dice_orderings = [(high_die, low_die), (low_die, high_die)]
    
    # For each ordered sequence of dice
    for die1, die2 in dice_orderings:
        # First move with die1
        first_moves = get_legal_moves_for_die(my_pts, opp_pts, die1)
        if len(first_moves) == 0:
            continue
        for move1 in first_moves:
            # Try second move with die2
            t_my_pts = my_pts.copy()
            if move1 != "P":
                point = int(move1[1:]) if move1.startswith("A") else 0
                if move1 == "B":
                    point = 24 - die1
                    if point < 0 or point > 23:
                        continue
                    t_my_pts[point] += 1
                else:
                    t_my_pts[point] -= 1
                    dest = point - die1  # Moving toward point 0
                    if 0 <= dest <= 23:
                        t_my_pts[dest] += 1
                
                # Calculate second move possibilities
                second_moves = get_legal_moves_for_die(t_my_pts, opp_pts, die2)
                if len(second_moves) == 0:
                    # Can't make second move - only use first
                    order = "H" if die1 == high_die else "L"
                    moves.append(f"{order}:{move1},P")
                else:
                    for move2 in second_moves:
                        order = "H" if die1 == high_die else "L"
                        moves.append(f"{order}:{move1},{move2}")
            else:
                # First move is pass - only possible if no other moves
                second_moves = get_legal_moves_for_die(my_pts, opp_pts, die2)
                for move2 in second_moves:
                    order = "H" if die1 == high_die else "L"
                    moves.append(f"{order}:{move1},{move2}")
    
    # Deduplicate and ensure we have at least the necessary
    # Return unique moves
    unique_moves = list(set(moves))
    return unique_moves

def get_legal_moves_for_die(my_pts, opp_pts, die):
    """Get all legal moves for a single die, return list of move strings"""
    moves = []
    
    # Check bearing off possibilities first
    total_checkers_in_home = sum(my_pts[0:6])
    all_in_home = total_checkers_in_home == sum(my_pts)
    
    if all_in_home:
        # Can bear off from home points
        for i in range(6):  # Points 0-5
            if my_pts[i] > 0:
                if i + 1 == die or i + 1 > die:  # Can bear off if die equals position or larger
                    moves.append(f"A{i}")
        # If we can't move any checker from home, try to use die to move within home
        if len(moves) == 0:
            # Just move within home
            for i in range(6):
                if my_pts[i] > 0:
                    dest = i - die
                    if dest >= 0:
                        if opp_pts[dest] < 2:  # Not blocked
                            moves.append(f"A{i}")
    
    # Normal moves (not bearing off, or can't bear off)
    if not all_in_home or len(moves) == 0:
        for i in range(24):
            if my_pts[i] > 0:
                dest = i - die  # Moving toward point 0
                if dest >= 0:
                    # Check if destination is not blocked by 2+ opponent checkers
                    if opp_pts[dest] < 2:
                        if i == 23 and die > 23:  # Can't move from 23 with die > 23, impossible
                            continue
                        moves.append(f"A{i}")
                elif dest < 0 and all_in_home:  # Bearing off
                    moves.append(f"A{i}")
    
    # If no moves from points, then we must have checkers on bar (handled elsewhere)
    # We also allow pass only if no other moves exist, but that behavior is handled in caller
    return moves

def get_legal_second_moves(my_pts, opp_pts, die, from_bar=False):
    """Helper to get valid second moves after first move has been made"""
    return get_legal_moves_for_die(my_pts, opp_pts, die)

def evaluate_move(move_str, my_pts, opp_pts, dice):
    """Score a move based on strategic factors"""
    if move_str.startswith("H:P,P") or move_str.startswith("L:P,P"):
        return 0  # Pass move, lowest priority unless forced
    
    # Parse move
    parts = move_str.split(":")
    order = parts[0]
    from_strs = parts[1].split(",")
    from1_str, from2_str = from_strs[0], from_strs[1]
    
    score = 0
    low_die, high_die = min(dice), max(dice)
    die1 = high_die if order == "H" else low_die
    die2 = low_die if order == "H" else high_die
    
    # Parse moves
    move1 = from1_str
    move2 = from2_str
    
    # Create temporary board state after move1
    t_my_pts = my_pts.copy()
    if move1 != "P":
        if move1 == "B":
            point_to_enter = 24 - die1
            t_my_pts[point_to_enter] += 1
        else:
            from_point = int(move1[1:])
            t_my_pts[from_point] -= 1
            dest = from_point - die1
            if dest >= 0:
                t_my_pts[dest] += 1
    
    # Then apply move2
    if move2 != "P":
        if move2 == "B":
            point_to_enter = 24 - die2
            t_my_pts[point_to_enter] += 1
        else:
            from_point = int(move2[1:])
            t_my_pts[from_point] -= 1
            dest = from_point - die2
            if dest >= 0:
                t_my_pts[dest] += 1
    
    # Scoring criteria:
    # 1. HITTING OPPONENT BLOTS (weight: +20 each)
    if move1 != "P" and move1 != "B":
        from_point = int(move1[1:])
        dest = from_point - die1
        if 0 <= dest <= 23 and opp_pts[dest] == 1:
            score += 20
    
    if move2 != "P" and move2 != "B":
        from_point = int(move2[1:])
        dest = from_point - die2
        if 0 <= dest <= 23 and opp_pts[dest] == 1:
            score += 20
    
    # 2. BEARING OFF (weight: +15 per checker borne off)
    total_in_home = sum(my_pts[0:6])
    if sum(my_pts) > 0 and total_in_home == sum(my_pts): # All in home
        # Check how many we can bear off with these dice
        new_my_pts = t_my_pts.copy()
        borne_off = sum(my_pts) - sum(new_my_pts)
        score += 15 * borne_off
    
    # 3. CREATING PRIMES (weight: +10 per point in a 2+ point prime)
    for i in range(18):  # Points 0-17 (can form primes down to 6)
        if t_my_pts[i] >= 2 and t_my_pts[i+1] >= 1:
            score += 10
    
    # 4. AVOIDING BLOTS (weight: -5 per blot on board)
    for i in range(24):
        if t_my_pts[i] == 1 and i > 5:  # Blot outside home
            score -= 5
    
    # 5. CONTROL OF MIDFIELD (weight: +3 per checker in points 6-17)
    for i in range(6, 18):
        score += 3 * t_my_pts[i]
    
    # 6. HIGH DICE USE (if higher die used for more distant move leading to better position)
    if move1 != "P" and move1 != "B":
        from_point = int(move1[1:])
        if die1 > die2 and from_point > 5:  # Higher die used on distant point
            score += 5
    
    # 7. SAFETY (avoid moving checker from safety)
    if move1 != "P" and move1 != "B":
        from_point = int(move1[1:])
        if my_pts[from_point] > 1:  # Was safe, now potentially risky
            dest = from_point - die1
            if dest >= 0 and t_my_pts[dest] == 1:  # Creating a blot
                score -= 10
    
    # 8. USE OF BOTH DICE
    if move1 != "P" and move2 != "P":
        score += 8  # Prefer using both dice
    
    # 9. RE-ENTERING FROM BAR (weight: +15)
    if move1 == "B" or move2 == "B":
        score += 15
    
    return score
