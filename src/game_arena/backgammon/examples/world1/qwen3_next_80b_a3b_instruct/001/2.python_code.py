
import numpy as np

def policy(state: dict) -> str:
    # Extract state components
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'])  # Sort to get low and high
    
    # If no dice, pass
    if len(dice) == 0:
        return "H:P,P"
    
    low_die, high_die = dice[0], dice[1]
    
    # If checkers on bar, must re-enter first
    if my_bar > 0:
        legal_moves = []
        
        # Try re-entering with high die first
        for die_val, order in [(high_die, 'H'), (low_die, 'L')]:
            # Re-entry point: 24 - die_val (since points are 0-23, and opponent moves 0->23)
            re_entry_point = 24 - die_val - 1  # Convert to 0-indexed
            if re_entry_point < 0 or re_entry_point > 23:
                continue
                
            # Check if point is not blocked by opponent (>=2 checkers)
            if opp_pts[re_entry_point] < 2:
                # Legal re-entry
                # Simulate the move: remove one checker from bar, place on re_entry_point
                # Then try to play second die if possible
                remaining_dice = low_die if die_val == high_die else high_die
                
                # First move: from bar to re_entry_point
                first_move = "B"
                
                # Try second move within home board or other points
                second_moves = []
                
                # Check if we can use remaining die from any of our points
                for i in range(24):
                    if my_pts[i] > 0:
                        dest = i - remaining_dice
                        if dest >= 0:  # Moving toward 0
                            # Check if destination is not blocked by opponent
                            if opp_pts[dest] < 2:
                                second_moves.append(f"A{i}")
                
                # Also check for bearing off if possible
                home_board = my_pts[0:6]  # Points 0-5 are home board
                total_home = np.sum(home_board)
                if total_home == np.sum(my_pts):  # All checkers in home board
                    # Check if we can bear off from points when die can reach 0
                    for i in range(6):
                        if my_pts[i] > 0 and i + 1 >= remaining_dice:
                            # Can bear off from point i using die of value remaining_dice
                            second_moves.append(f"A{i}")
                
                # If we can make a second move, try both orders
                if second_moves:
                    for second in second_moves:
                        if option == 'H':
                            if die_val == high_die:
                                legal_moves.append(f"H:{first_move},{second}")
                            else:
                                legal_moves.append(f"L:{first_move},{second}")
                        elif option == 'L':
                            if die_val == low_die:
                                legal_moves.append(f"L:{first_move},{second}")
                            else:
                                legal_moves.append(f"H:{first_move},{second}")
                else:
                    # Only one move possible - must play the die we used for re-entry
                    # But we still must play the higher die when possible
                    if low_die == die_val:
                        legal_moves.append(f"L:{first_move},P")
                    else:
                        legal_moves.append(f"H:{first_move},P")
        
        # If no second move possible, we still need to return one move
        if len(legal_moves) == 0:
            # Shouldn't happen if bar exists and die is valid, but guard
            # Try re-entering with highest die if no second move (even if blind)
            if opp_pts[24 - high_die - 1] < 2:
                return f"H:B,P"
            elif opp_pts[24 - low_die - 1] < 2:
                return f"L:B,P"
            else:
                # No legal re-entry? Shouldn't be possible per rules, but pass
                return "H:P,P"
        
        # Select best move from legal_moves
        best_score = -float('inf')
        best_move = "H:P,P"
        
        for move in legal_moves:
            score = evaluate_move(move, state, dice)
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move

    # No checkers on bar - normal play
    # Generate all possible move combinations
    legal_moves = []
    
    # Try all possible orders: H then L, L then H
    for order in ['H', 'L']:
        die1 = high_die if order == 'H' else low_die
        die2 = low_die if order == 'H' else high_die
        
        # Find all possible first moves for die1
        first_moves = []
        
        # Check all points we have checkers on
        for start in range(24):
            if my_pts[start] > 0:
                dest = start - die1
                if dest >= 0:  # Moving toward 0
                    if opp_pts[dest] < 2:  # Not blocked
                        first_moves.append(f"A{start}")
                elif dest < 0:  # Bearing off
                    # Can only bear off if all checkers are in home board
                    home_board = np.sum(my_pts[0:6])
                    if home_board == np.sum(my_pts) and (24 - start) <= die1:
                        # This point is within home board and we can bear off
                        first_moves.append(f"A{start}")
        
        # Also check if we can move from the bar (shouldn't happen here, but guard)
        if my_bar > 0:
            re_entry_point = 24 - die1 - 1
            if opp_pts[re_entry_point] < 2:
                first_moves.append("B")
        
        for first in first_moves:
            # Create new state after first move (conceptually)
            # We don't modify actual state, just simulate
            remaining_checkers = my_pts.copy()
            if first == "B":
                # Remove one from bar and place on re-entry point
                if opp_pts[24 - die1 - 1] < 2:
                    remaining_checkers[24 - die1 - 1] += 1
                    # We don't track bar reduction as we're just evaluating
                else:
                    continue
            else:
                start_point = int(first[1:])
                remaining_checkers[start_point] -= 1
                dest_point = start_point - die1
                if dest_point >= 0:
                    remaining_checkers[dest_point] += 1
                else:
                    # Bear off - do nothing (checker removed)
                    pass
            
            # Now try second move with die2
            second_moves = []
            
            # Check all points with checkers
            for start in range(24):
                if remaining_checkers[start] > 0:
                    dest = start - die2
                    if dest >= 0:  # Moving toward 0
                        if opp_pts[dest] < 2:  # Not blocked by opponent (considering original opponent positions since hit is resolved)
                            second_moves.append(f"A{start}")
                    elif dest < 0:  # Bearing off
                        home_board = np.sum(remaining_checkers[0:6])
                        # Must have all checkers in home board to bear off
                        if home_board == np.sum(remaining_checkers) and (24 - start) <= die2:
                            second_moves.append(f"A{start}")
            
            # Also check for bar re-entry (if bar was used in first move, we don't have bar anymore)
            if my_bar > 0 and first != "B":  # bar still has checkers
                re_entry_point = 24 - die2 - 1
                if opp_pts[re_entry_point] < 2:
                    second_moves.append("B")
            
            if len(second_moves) == 0:
                # Must we play die? Only if it's mandatory - use the higher die first
                # But we already satisfied first move with higher die if H, so if second is impossible, pass
                # Still need to play if possible, else pass
                if first == "B" or (first.startswith("A") and int(first[1:]) >= die1):
                    # This move used a die, can't play second, so pass
                    second_moves.append("P")
                elif len(first_moves) == 0:
                    # This shouldn't happen
                    second_moves.append("P")
                
            for second in second_moves:
                if second == "P":
                    # We can pass only if we can't play the second die
                    legal_moves.append(f"{order}:{first},{second}")
                else:
                    legal_moves.append(f"{order}:{first},{second}")
    
    # Also check if we can play first die and not second die (if only one move possible)
    # But the engine requires both if possible, so we only include moves where both played if possible
    # We built legal_moves above with both possibilities
    
    if len(legal_moves) == 0:
        # Need to pass
        return "H:P,P"
    
    # Evaluate all legal moves and choose the best
    best_score = -float('inf')
    best_move = "H:P,P"
    
    for move in legal_moves:
        score = evaluate_move(move, state, dice)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def evaluate_move(move_str, state, dice):
    """
    Given a move string, compute a heuristic score for its quality
    """
    # Parse the move
    order, parts = move_str.split(':')
    first_src, second_src = parts.split(',')
    
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    my_bar = state['my_bar']
    my_off = state['my_off']
    
    score = 0.0
    
    # Add base score for borne off checkers
    score += my_off * 10.0
    
    # Adjust for home board consolidation
    home_board = my_pts[0:6]
    home_sum = np.sum(home_board)
    total_checkers = np.sum(my_pts)
    
    # Reward having checkers in home board
    if total_checkers > 0:
        score += (home_sum / total_checkers) * 15.0
    
    # Penalty for blots (single checkers vulnerable to hit)
    for i in range(24):
        if my_pts[i] == 1 and opp_pts[i] > 0:  # Blot
            score -= 20.0
    
    # Reward creating primes (6 consecutive points with >=2 checkers)
    for i in range(19):  # 24-6=18, so 19 is last possible start
        prime_check = True
        for j in range(i, i+6):
            if my_pts[j] < 2:
                prime_check = False
                break
        if prime_check:
            score += 15.0  # Reward for prime
    
    # Reward advancing checkers toward home
    for i in range(6, 24):  # Outer board
        if my_pts[i] > 0:
            # Distance from home: 6 - (23-i) = i - 17
            dist_from_home = i - 17  # For point 17, dist=0; point 18, dist=1... point 23, dist=6
            score += my_pts[i] * max(0, dist_from_home) * 0.5  # Prefer closer to home
    
    # Penalty for leaving checkers on outer board
    outer_board = my_pts[6:24]
    score -= np.sum(outer_board) * 0.2
    
    # Check if move leads to bearing off
    if first_src.startswith('A'):
        point = int(first_src[1:])
        if point < 6:  # In home board
            die = int(dice[1]) if order == 'H' else int(dice[0])  # First die used
            if point + 1 <= die:  # Can bear off
                score += 10.0  # Immediate bear off reward
            else:
                # Just moved within home board
                score += 2.0
    
    # Second move
    if second_src != "P":
        if second_src.startswith('A'):
            point = int(second_src[1:])
            if point < 6:
                die = int(dice[0]) if order == 'H' else int(dice[1])  # Second die
                if point + 1 <= die:
                    score += 10.0  # Second bear off
                else:
                    score += 2.0
    
    # If we used bar, reward re-entry
    if first_src == "B" or second_src == "B":
        score += 5.0
    
    return score
