
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # If no dice, return pass
    if len(dice) == 0:
        return "H:P,P"
    
    # Sort dice
    dice_sorted = sorted(dice)
    die1, die2 = dice_sorted[0], dice_sorted[1]  # lower, higher
    
    # Check if all my checkers are in home board (for bearing off)
    def all_in_home_board():
        return sum(my_pts[6:]) == 0
    
    # Function to check if a move from point `start` with `die` is legal
    def is_legal_move(start, die):
        # If checker is on bar, must move with die to enter
        if start == 'B':
            # Must enter on opponent's side: points 18-23 (for player) = absolute 18-23
            target = die - 1  # die is 1-6, so target 0-5 relative to opponent's board
            if target > 23:  # should not happen
                return False
            # Can't enter on point with >=2 opponent checkers
            if opp_pts[target] >= 2:
                return False
            return True
        else:  # start is absolute point 0-23
            target = start + die
            # Normal movement: if moving to or beyond point 24, then bearing off
            if target >= 24:
                if not all_in_home_board():
                    return False  # cannot bear off unless all checkers in home
                return True  # bearing off is always allowed if in home
            else:
                # Can't land on point with >=2 opponent checkers
                if opp_pts[target] >= 2:
                    return False
                return True
    
    # Get all possible moves
    possible_moves = []
    
    # Case 1: Have checkers on bar
    if my_bar > 0:
        # Must use dice to enter from bar first
        moves_from_bar = []
        for d in dice:
            if is_legal_move('B', d):
                # Can enter with this die
                moves_from_bar.append(d)
        
        if len(moves_from_bar) > 0:
            # We must use one die to enter from bar
            for d1 in moves_from_bar:
                # Then try to use the second die
                remaining_dice = [d for d in dice if d != d1] if len(dice) == 2 else []
                if len(remaining_dice) == 0:
                    # Only one die, use it to enter bar
                    move_str = 'H' if d1 == die2 else 'L'
                    move_str += f":B,P"
                    possible_moves.append((move_str, 1000))  # High score for bar entry
                else:
                    d2 = remaining_dice[0]
                    # Try to move with second die (from home or bar, but bar is now empty)
                    for start in range(24):
                        if my_pts[start] > 0 and is_legal_move(start, d2):
                            # Build move: use d1 first, then d2
                            order = 'H' if d1 == die2 else 'L'
                            move_str = f"{order}:B,A{start}"
                            possible_moves.append((move_str, evaluate_state_after_move(state, [('B', d1), (start, d2)])))
                    
                    # Also try using d2 first, then d1
                    if is_legal_move('B', d2):
                        for start in range(24):
                            if my_pts[start] > 0 and is_legal_move(start, d1):
                                order = 'H' if d2 == die2 else 'L'
                                move_str = f"{order}:B,A{start}"
                                possible_moves.append((move_str, evaluate_state_after_move(state, [('B', d2), (start, d1)])))
            
            # Handle single die case
            if len(dice) == 1:
                d = dice[0]
                if d in moves_from_bar:
                    move_str = "H:B,P" if d == die2 else "L:B,P"
                    possible_moves.append((move_str, 1000))
        
        # If no legal bar move, this is theoretically impossible per rules
        # But for safety, fall back to next case

    # Case 2: No checkers on bar — normal moves
    if my_bar == 0:
        # Try two-move sequences
        # Find all points where we have checkers
        movable_points = [i for i in range(24) if my_pts[i] > 0]
        
        # Generate all first and second move combinations for both orders
        for d1 in dice:
            for d2 in dice:
                if d1 == d2 and len(dice) == 1:
                    continue  # Skip if only one die
                for start1 in movable_points:
                    if not is_legal_move(start1, d1):
                        continue
                    # First move: start1 with d1
                    # For second move, we need updated state? But we simulate naively
                    # We'll evaluate the whole move sequence after
                    for start2 in movable_points:
                        if start1 == start2 and my_pts[start1] < 2:
                            continue  # Cannot move same point twice if only one checker
                        # Check if second move legal after first? 
                        # Since we don't simulate partial state, we'll allow it but check board state after
                        # and let evaluation catch illegalities
                        # But need to ensure start2 is valid with d2: 
                        if is_legal_move(start2, d2):
                            if d1 == die2:
                                order = 'H'
                                move_str = f"{order}:A{start1},A{start2}"
                            else:
                                order = 'L'
                                move_str = f"{order}:A{start1},A{start2}"
                            possible_moves.append((move_str, evaluate_state_after_move(state, [(start1, d1), (start2, d2)])))
        
        # Now try single die moves (if second die cannot be played)
        # We try both dice individually as first move, and second as P
        for d in dice:
            for start in movable_points:
                if is_legal_move(start, d):
                    # Use this die, and set second as P
                    order = 'H' if d == die2 else 'L'
                    move_str = f"{order}:A{start},P"
                    possible_moves.append((move_str, evaluate_state_after_move(state, [(start, d)])))

        # If no moves are available, return P,P
        if len(possible_moves) == 0:
            # Check if we can bear off optimally with one die
            if all_in_home_board():
                for d in dice:
                    for start in range(6):  # only home board
                        if my_pts[start] > 0:
                            if start + d >= 24:
                                # Can bear off
                                order = 'H' if d == die2 else 'L'
                                move_str = f"{order}:A{start},P"
                                possible_moves.append((move_str, evaluate_state_after_move(state, [(start, d)])))
                if len(possible_moves) == 0:
                    return "H:P,P"
            else:
                return "H:P,P"
    
    # If no moves found in all cases
    if len(possible_moves) == 0:
        return "H:P,P"
    
    # Choose the move with highest evaluation score
    best_move = max(possible_moves, key=lambda x: x[1])
    return best_move[0]

# Heuristic evaluation function
def evaluate_state_after_move(state, moves):
    # Simulate moves and evaluate resulting state
    my_pts = state['my_pts'][:]
    opp_pts = state['opp_pts'][:]
    my_bar = state['my_bar']
    my_off = state['my_off']
    
    # Apply each move
    for p, d in moves:
        if p == 'B':
            # Enter from bar
            my_bar -= 1
            target = d - 1  # bar entry -> points 18-23
            if opp_pts[target] == 1:
                # Hit! Send opponent checker to bar
                opp_pts[target] = 0
                opp_bar = state['opp_bar'] + 1  # not used in eval but correct logic
            opp_pts[target] = 0  # we don't track opp_bar in eval
            my_pts[target] += 1
        else:
            # Move from point p with distance d
            target = p + d
            if target >= 24:
                # Bear off
                my_pts[p] -= 1
                my_off += 1
            else:
                # Normal move
                my_pts[p] -= 1
                if opp_pts[target] == 1:
                    # Hit opponent
                    opp_pts[target] = 0
                    # opp_bar += 1 (not tracked)
                if my_pts[target] > 0:
                    my_pts[target] += 1
                else:
                    my_pts[target] = 1  # Assume nothing there, place one checker
    
    # Compute evaluation score
    score = 0
    
    # 1. Number of checkers borne off (high priority)
    score += my_off * 10
    
    # 2. Penalties for checkers on bar
    score -= my_bar * 20
    
    # 3. Checkers in home board (0-5) are good
    home_checkers = sum(my_pts[0:6])
    score += home_checkers * 5
    
    # 4. Checkers in opponent's home board (18-23) are good if they don't get hit
    opp_home_checkers = sum(my_pts[18:24])
    # But if they are singles, they are vulnerable
    for pt in range(18, 24):
        if my_pts[pt] == 1 and opp_pts[pt] == 0:
            score += 2
        elif my_pts[pt] == 1 and opp_pts[pt] >= 1:
            score -= 10  # exposed in enemy territory
    
    # 5. Build points (2+ checkers on same point = safe)
    for pt in range(24):
        if my_pts[pt] >= 2:
            score += 3
        if my_pts[pt] == 1:
            # Single checker: vulnerable to hit
            # Check if opponent can hit it
            for opp_pt in range(24):
                if opp_pts[opp_pt] >= 2:
                    # Opponent can hit if distance is right
                    distance = pt - opp_pt
                    if distance in [1,2,3,4,5,6]:
                        score -= 15  # exposed to hit
            # If no danger, just neutral
            if all(opp_pts[opp_pt] < 2 for opp_pt in range(24) if pt - opp_pt in range(1,7)):
                score += 2  # safe single
    
    # 6. Distance to bearing off
    total_distance = 0
    for pt in range(6, 24):
        total_distance += my_pts[pt] * (24 - pt)
    score -= total_distance / 10  # penalize checkers far from home
    
    # 7. Reward hitting opponent
    # In simulation we already did hit logic above, so we use the state
    # But we can also count how many opponent blots we threatened
    # (This is complex, so we leave at high level)
    
    return score
