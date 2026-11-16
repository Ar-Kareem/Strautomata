
import itertools
import random

def policy(state: dict) -> str:
    """
    Backgammon AI policy that evaluates positions and selects optimal moves.
    Uses heuristics considering safety, progress, and board control.
    """
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # Generate all possible legal moves
    all_moves = generate_legal_moves(state, dice)
    
    if not all_moves:
        return "H:P,P"
    
    # Evaluate and select the best move
    best_move = select_best_move(state, dice, all_moves)
    
    return format_move(best_move, dice)

def generate_legal_moves(state: dict, dice: list) -> list:
    """Generate all legal move sequences for the current state."""
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice_sorted = sorted(dice, reverse=True)
    
    moves = []
    
    # If we have checkers on bar, we must move them first
    if my_bar > 0:
        for i, die in enumerate(dice_sorted):
            dest = die - 1  # Bar enters at point 0, so die value gives destination
            if is_legal_bar_move(dest, opp_pts):
                # After playing this die, recurse for remaining dice
                remaining_dice = dice_sorted[:i] + dice_sorted[i+1:]
                if not remaining_dice:
                    moves.append([('B', die)])
                else:
                    subsequent_moves = generate_bar_subsequent_moves(
                        state, die, remaining_dice, my_pts, opp_pts
                    )
                    for sub in subsequent_moves:
                        moves.append([('B', die)] + sub)
    else:
        # Normal move generation
        # Try all combinations of starting points and dice
        available_points = [i for i in range(24) if my_pts[i] > 0]
        
        if len(dice) == 1:
            die = dice_sorted[0]
            for point in available_points:
                dest = point - die
                if is_legal_move(point, dest, my_pts, opp_pts):
                    moves.append([(point, die)])
        else:
            # Try both orders of dice
            for order in ['H', 'L']:
                if order == 'H':
                    die1, die2 = dice_sorted[0], dice_sorted[1]
                else:
                    die1, die2 = dice_sorted[1], dice_sorted[0]
                
                # Try all combinations of two moves
                for i, pt1 in enumerate(available_points):
                    dest1 = pt1 - die1
                    if is_legal_move(pt1, dest1, my_pts, opp_pts):
                        # Simulate first move
                        pts_after_move1 = my_pts.copy()
                        pts_after_move1[pt1] -= 1
                        if 0 <= dest1 < 24:
                            pts_after_move1[dest1] += 1
                        
                        # Find available points after first move
                        available_after = available_points[:i] + available_points[i+1:]
                        if dest1 >= 0 and dest1 < 24 and my_pts[pt1] > 0:
                            # The point might still have checkers after move
                            pass
                        
                        for pt2 in available_after:
                            dest2 = pt2 - die2
                            if is_legal_move(pt2, dest2, pts_after_move1, opp_pts):
                                moves.append([(pt1, die1), (pt2, die2)])
            
            # Also try single move with higher die if double move not possible
            die = max(dice_sorted)
            for point in available_points:
                dest = point - die
                if is_legal_move(point, dest, my_pts, opp_pts):
                    moves.append([(point, die)])
    
    return moves

def is_legal_bar_move(dest: int, opp_pts: list) -> bool:
    """Check if entering from bar to dest is legal."""
    if dest < 0 or dest >= 24:
        return False
    return opp_pts[dest] <= 1  # Can only enter if 0 or 1 opponent checker

def is_legal_move(from_pt: int, dest: int, my_pts: list, opp_pts: list) -> bool:
    """Check if a move from from_pt to dest is legal."""
    if from_pt < 0 or from_pt >= 24:
        return False
    if my_pts[from_pt] <= 0:
        return False
    if dest < 0:
        # Bearing off
        return True
    if dest >= 24:
        return False
    return opp_pts[dest] <= 1  # Can't move onto 2+ opponent checkers

def generate_bar_subsequent_moves(state: dict, played_die: int, remaining_dice: list, 
                                 my_pts: list, opp_pts: list) -> list:
    """Generate subsequent moves after playing a bar move."""
    # Simulate the bar move
    pts_after_bar = my_pts.copy()
    dest = played_die - 1
    if 0 <= dest < 24:
        pts_after_bar[dest] += 1
    
    remaining_state = state.copy()
    remaining_state['my_pts'] = pts_after_bar
    remaining_state['my_bar'] = 0
    
    return generate_legal_moves(remaining_state, remaining_dice)

def select_best_move(state: dict, dice: list, moves: list) -> tuple:
    """Select the best move from the list of legal moves using evaluation."""
    if not moves:
        return None
    
    best_move = None
    best_score = float('-inf')
    
    for move_seq in moves:
        score = evaluate_move(state, move_seq, dice)
        if score > best_score:
            best_score = score
            best_move = move_seq
    
    # Add some randomness to break ties
    if best_move is None:
        best_move = moves[0]
    
    return best_move

def evaluate_move(state: dict, move_seq: list, dice: list) -> float:
    """Evaluate the quality of a move sequence."""
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    
    score = 0.0
    
    # Simulate the moves to get resulting position
    result_pts = my_pts.copy()
    result_bar = my_bar
    result_off = my_off
    
    for from_pt, die in move_seq:
        if from_pt == 'B':
            result_bar -= 1
            dest = die - 1
            if 0 <= dest < 24:
                result_pts[dest] += 1
        else:
            result_pts[from_pt] -= 1
            dest = from_pt - die
            if dest >= 0:
                if dest < 24:
                    result_pts[dest] += 1
                else:
                    result_off += 1
    
    # Evaluation criteria:
    
    # 1. Progress toward bearing off (most important)
    progress_score = calculate_progress_score(result_pts, result_bar, result_off, my_off)
    score += progress_score * 10
    
    # 2. Safety - avoid leaving exposed checkers
    safety_score = calculate_safety_score(result_pts, opp_pts)
    score += safety_score * 5
    
    # 3. Board control
    control_score = calculate_control_score(result_pts, opp_pts)
    score += control_score * 3
    
    # 4. Prime formation (blocking opponent)
    prime_score = calculate_prime_score(result_pts)
    score += prime_score * 2
    
    # 5. Prefer using both dice if possible
    dice_usage_score = len(move_seq) * 2
    score += dice_usage_score
    
    # 6. Bar completion bonus
    if result_bar == 0 and my_bar > 0:
        score += 10
    
    return score

def calculate_progress_score(pts: list, bar: int, off: int, my_off_initial: int) -> float:
    """Calculate how close we are to bearing off."""
    # Weight points closer to bear-off more heavily
    weights = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
               1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0,
               2.1, 2.2, 2.3, 2.4]
    
    score = 0.0
    for i, count in enumerate(pts):
        if count > 0:
            # Points 0-5 are in home board (closer to bear-off)
            if i <= 5:
                score += count * weights[i] * 2
            else:
                score += count * weights[i]
    
    # Bonus for checkers on bar (they need to re-enter)
    score -= bar * 3
    
    # Big bonus for borne-off checkers
    score += (off - my_off_initial) * 100
    
    return score

def calculate_safety_score(my_pts: list, opp_pts: list) -> float:
    """Calculate safety score - prefer safe positions."""
    score = 0.0
    
    for i, count in enumerate(my_pts.items()):
        if count > 0:
            # Check if checker is exposed to hit
            if i > 0:
                # Check opponent's ability to hit from behind
                if opp_pts[i-1] > 0:
                    if count == 1:
                        score -= 5  # Exposed single checker
                    elif count == 2:
                        score -= 2  # Partially exposed
    
    # Bonus for having made points (2+ checkers on same point)
    for i, count in enumerate(my_pts):
        if count >= 2:
            score += count * 2
    
    return score

def calculate_control_score(my_pts: list, opp_pts: list) -> float:
    """Calculate board control score."""
    score = 0.0
    
    for i in range(24):
        if my_pts[i] > opp_pts[i]:
            score += my_pts[i] - opp_pts[i]
        elif opp_pts[i] > my_pts[i]:
            score -= (opp_pts[i] - my_pts[i]) * 0.5
    
    # Control of home board (0-5) is more valuable
    for i in range(6):
        if my_pts[i] > 0:
            score += my_pts[i]
    
    return score

def calculate_prime_score(pts: list) -> float:
    """Calculate prime formation score - sequences of made points block opponent."""
    score = 0.0
    
    # Look for sequences of made points (2+ checkers)
    consecutive = 0
    for i in range(24):
        if pts[i] >= 2:
            consecutive += 1
            if consecutive >= 3:
                score += consecutive * 3  # Bonus for longer primes
        else:
            if consecutive >= 3:
                score += consecutive * 2  # Completed prime segment
            consecutive = 0
    
    if consecutive >= 3:
        score += consecutive * 2
    
    return score

def format_move(move_seq: list, dice: list) -> str:
    """Format the move sequence into the required string format."""
    if not move_seq:
        return "H:P,P"
    
    # Determine order based on dice values
    dice_values = [die for _, die in move_seq]
    
    if len(dice) == 1:
        order = 'H'
    else:
        # Compare with actual dice order
        dice_sorted = sorted(dice, reverse=True)
        if dice_values == dice_sorted:
            order = 'H'
        else:
            order = 'L'
    
    # Format FROM values
    from1 = format_from(move_seq[0][0])
    from2 = format_from(move_seq[1][0]) if len(move_seq) > 1 else 'P'
    
    return f"{order}:{from1},{from2}"

def format_from(from_value):
    """Format the starting point for the move string."""
    if from_value == 'B':
        return 'B'
    elif isinstance(from_value, int):
        return f"A{from_value}"
    else:
        return 'P'
