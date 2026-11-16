
import numpy as np

def policy(state: dict) -> str:
    # Extract state
    my_pts = np.array(state['my_pts'])      # 24 points
    opp_pts = np.array(state['opp_pts'])    # 24 points
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'])  # sorted ascending: [low, high]
    low, high = dice[0], dice[1] if len(dice) > 1 else dice[0]
    
    # Define home board for player (points 18-23 are home board)
    HOME_BOARD_START = 18
    HOME_BOARD_END = 23
    
    # Check if all our checkers are in home board (for bearing off)
    def all_in_home_board():
        for i in range(0, HOME_BOARD_START):
            if my_pts[i] > 0:
                return False
        return True
    
    is_bearing_off_allowed = all_in_home_board()
    
    # Get all possible moves for a single die from a given point
    def get_legal_moves_from_point(point, die, bar_move=False):
        """Return list of legal destination points from `point` using `die`"""
        moves = []
        # If on bar, must re-enter
        if bar_move:
            dest = point + die  # But since we're on bar, we use die to re-enter
            # Re-entering: from bar to point `die` (in absolute: 0-23)
            # On bar: die value maps to point (die - 1) because point 0 is the 1st point
            dest = die - 1  # die 1 -> point 0, die 6 -> point 5
            if dest < 0 or dest > 23:
                return []
            # Can't move onto 2+ opponent checkers
            if opp_pts[dest] <= 1:
                moves.append(dest)
            return moves
        
        # Normal move: from point to point + die (toward 23)
        dest = point + die
        if dest > 23:
            # Bearing off
            if is_bearing_off_allowed:
                if point >= HOME_BOARD_START:
                    # Can bear off: check if die is large enough
                    if die >= (24 - point):  # die value >= distance to bear off
                        moves.append('off')
            return moves
        
        # Standard move within board
        if dest <= 23:
            if opp_pts[dest] <= 1:  # Safe to land
                moves.append(dest)
        return moves
    
    # Get all possible moves given dice and state
    def get_all_legal_moves():
        moves_list = []
        
        # If on bar, must use dice to re-enter first
        if my_bar > 0:
            possible_first_moves = []
            if len(dice) == 1:
                # Only one die to play
                reentry_dest = high - 1
                if opp_pts[reentry_dest] <= 1:
                    possible_first_moves.append((reentry_dest, high))
            else:
                # Two dice
                for d in dice:
                    reentry_dest = d - 1
                    if opp_pts[reentry_dest] <= 1:
                        possible_first_moves.append((reentry_dest, d))
            
            # For bar moves, we can use either die first
            for dest, die_used in possible_first_moves:
                # First move: from bar using die_used
                remaining_dice = dice[:]
                remaining_dice.remove(die_used)
                
                if len(remaining_dice) == 0:
                    # Only one die and we used it
                    moves_list.append(('B', 'P'))
                else:
                    # Second move: either from bar again (if possible) or from board
                    second_die = remaining_dice[0]
                    second_moves = []
                    
                    # Option 1: use second die on bar again (if possible)
                    reentry_dest2 = second_die - 1
                    if opp_pts[reentry_dest2] <= 1:
                        second_moves.append(('B', second_die))
                    
                    # Option 2: use second die from existing checkers on board
                    for i in range(24):
                        if my_pts[i] > 0:
                            dest2 = i + second_die
                            if dest2 > 23:
                                if is_bearing_off_allowed and i >= HOME_BOARD_START:
                                    if second_die >= (24 - i):
                                        second_moves.append((i, second_die))
                            else:
                                if opp_pts[dest2] <= 1:
                                    second_moves.append((i, second_die))
                    
                    # Generate combinations
                    for second_from, second_die_val in second_moves:
                        if second_from == 'B':
                            moves_list.append(('B', 'B'))
                        else:
                            moves_list.append(('B', second_from))
            
            # If no re-entry moves possible, return no moves
            if not possible_first_moves:
                # Must pass if we can't re-enter and have no other moves
                # But according to rules, if we have checkers on bar, we MUST move them
                # If no legal re-entry, then we cannot move at all? 
                # The engine should not let us have dice and checkers on bar with no legal re-entry
                # But in case all re-entries blocked, we pass (even though it's disallowed per rules? But constraint says we must return legal)
                # So if absolutely no move, we have to pass — but engine should prevent this.
                return [('P', 'P')]
            
            return moves_list
        
        # Not on bar — normal moves
        # Generate all possible pairs of moves for the two dice
        # Strategy: try both H and L orders, with all combinations of starting points
        
        moves_list = []
        # First, collect all points with checkers
        points_with_checkers = [i for i in range(24) if my_pts[i] > 0]
        
        # Try using higher die first (H)
        for from1 in points_with_checkers:
            dest1 = from1 + high
            if dest1 > 23:
                if is_bearing_off_allowed and from1 >= HOME_BOARD_START and high >= (24 - from1):
                    # Valid bearing off with high die
                    remaining_dice = [low]
                else:
                    continue
            else:
                if opp_pts[dest1] <= 1:
                    remaining_dice = [low]
                else:
                    continue
            
            # Now try to use low die
            if remaining_dice:
                d2 = remaining_dice[0]
                for from2 in points_with_checkers:
                    if from1 == from2 and my_pts[from1] < 2:
                        continue  # cannot use same point twice if only one checker
                    dest2 = from2 + d2
                    if dest2 > 23:
                        if is_bearing_off_allowed and from2 >= HOME_BOARD_START and d2 >= (24 - from2):
                            moves_list.append((from1, from2))
                    else:
                        if opp_pts[dest2] <= 1:
                            moves_list.append((from1, from2))
                
                # Also consider bearing off as second move, even if first is movement
                if is_bearing_off_allowed:
                    for from2 in points_with_checkers:
                        if from2 >= HOME_BOARD_START:
                            if d2 >= (24 - from2):
                                moves_list.append((from1, from2))
        
        # Try using lower die first (L)
        for from1 in points_with_checkers:
            dest1 = from1 + low
            if dest1 > 23:
                if is_bearing_off_allowed and from1 >= HOME_BOARD_START and low >= (24 - from1):
                    remaining_dice = [high]
                else:
                    continue
            else:
                if opp_pts[dest1] <= 1:
                    remaining_dice = [high]
                else:
                    continue
            
            # Now try to use high die
            if remaining_dice:
                d2 = remaining_dice[0]
                for from2 in points_with_checkers:
                    if from1 == from2 and my_pts[from1] < 2:
                        continue  # cannot use same point twice if only one checker
                    dest2 = from2 + d2
                    if dest2 > 23:
                        if is_bearing_off_allowed and from2 >= HOME_BOARD_START and d2 >= (24 - from2):
                            moves_list.append((from1, from2))
                    else:
                        if opp_pts[dest2] <= 1:
                            moves_list.append((from1, from2))
                
                # Also consider bearing off as second move
                if is_bearing_off_allowed:
                    for from2 in points_with_checkers:
                        if from2 >= HOME_BOARD_START:
                            if d2 >= (24 - from2):
                                moves_list.append((from1, from2))
        
        # If no moves found and we have dice, maybe we can bear off with one die? but we need both dice used if possible
        # Only if we can't play both, we play one? But rule: if both can be played, must play both
        # So if we didn't find any two-moves, we need to check if we can play one
        if len(dice) == 2 and not moves_list and my_bar == 0:
            # We might have only one die playable
            possible_single_moves = []
            for from_point in points_with_checkers:
                # Try using high die
                dest = from_point + high
                if dest > 23:
                    if is_bearing_off_allowed and from_point >= HOME_BOARD_START and high >= (24 - from_point):
                        possible_single_moves.append(('H', from_point))
                else:
                    if opp_pts[dest] <= 1:
                        possible_single_moves.append(('H', from_point))
            
            # Try using low die
            for from_point in points_with_checkers:
                dest = from_point + low
                if dest > 23:
                    if is_bearing_off_allowed and from_point >= HOME_BOARD_START and low >= (24 - from_point):
                        possible_single_moves.append(('L', from_point))
                else:
                    if opp_pts[dest] <= 1:
                        possible_single_moves.append(('L', from_point))
            
            # Choose one with highest die if available
            if possible_single_moves:
                # Prefer using the higher die
                highest_moves = [m for m in possible_single_moves if m[0] == 'H']
                if highest_moves:
                    moves_list.append((highest_moves[0][1], 'P'))
                else:
                    moves_list.append((possible_single_moves[0][1], 'P'))
        
        # Add one-die moves for single die case
        if len(dice) == 1 and not moves_list:
            for from_point in points_with_checkers:
                dest = from_point + low
                if dest > 23:
                    if is_bearing_off_allowed and from_point >= HOME_BOARD_START and low >= (24 - from_point):
                        moves_list.append((from_point, 'P'))
                else:
                    if opp_pts[dest] <= 1:
                        moves_list.append((from_point, 'P'))
        
        # If no moves and all expanded, we return pass
        if not moves_list:
            return [('P', 'P')]
        
        # Deduplicate moves_list (avoid same move twice)
        moves_list = list(set(tuple(sorted(move)) if isinstance(move, tuple) else move for move in moves_list))
        
        # Convert to correct format with H/L prefix
        final_moves = []
        for m in moves_list:
            if len(dice) == 1:
                # Must use the only die
                if m[0] == 'P' and m[1] == 'P':
                    final_moves.append(('H', m[0], m[1]))
                elif m[1] == 'P':
                    final_moves.append(('H', m[0], 'P'))
                else:
                    # Shouldn't get here since we have 1 die
                    final_moves.append(('H', m[0], m[1]))
            else:
                # Two dice: we need to determine H or L order
                # But we stored (from1, from2) assuming first move used first die in sequence
                # However, we generated both orders. But we only stored the from points.
                # We must now determine which die was used first.
                # We can infer from the move: if the first move used the high die, then it's H.
                # But we didn't store which die was used. So we must return both possibilities?
                
                # We didn't store die order. So we need to reconstruct possible orderings.
                from1, from2 = m[0], m[1]
                # Check if from1 can be moved with high die and from2 with low die
                can_use_high_first = False
                can_use_low_first = False
                
                if from1 != 'P':
                    dest1 = from1 + high
                    if dest1 > 23:
                        if is_bearing_off_allowed and from1 >= HOME_BOARD_START and high >= (24 - from1):
                            can_use_high_first = True
                    else:
                        if opp_pts[dest1] <= 1:
                            can_use_high_first = True
                
                if from2 != 'P' and from2 != 'B':
                    dest2 = from2 + low
                    if dest2 > 23:
                        if is_bearing_off_allowed and from2 >= HOME_BOARD_START and low >= (24 - from2):
                            # Only if first move didn't use a bar
                            if from1 != 'B' and can_use_high_first:
                                can_use_low_first = True
                    else:
                        if opp_pts[dest2] <= 1:
                            if from1 != 'B' and can_use_high_first:
                                can_use_low_first = True
                
                # For from1 to be high die, from2 must be low die
                if can_use_high_first and from2 == 'P':
                    final_moves.append(('H', from1, 'P'))
                elif can_use_high_first and from2 != 'P' and from2 != 'B':
                    # Check if from2 can be moved with low die
                    dest2 = from2 + low
                    valid_low = False
                    if dest2 > 23:
                        if is_bearing_off_allowed and from2 >= HOME_BOARD_START and low >= (24 - from2):
                            valid_low = True
                    else:
                        if opp_pts[dest2] <= 1:
                            valid_low = True
                    if valid_low:
                        final_moves.append(('H', from1, from2))
                
                # Now check low first
                if from1 != 'P':
                    dest1 = from1 + low
                    if dest1 > 23:
                        if is_bearing_off_allowed and from1 >= HOME_BOARD_START and low >= (24 - from1):
                            can_use_low_first = True
                    else:
                        if opp_pts[dest1] <= 1:
                            can_use_low_first = True
                
                if can_use_low_first and from2 == 'P':
                    final_moves.append(('L', from1, 'P'))
                elif can_use_low_first and from2 != 'P' and from2 != 'B':
                    dest2 = from2 + high
                    valid_high = False
                    if dest2 > 23:
                        if is_bearing_off_allowed and from2 >= HOME_BOARD_START and high >= (24 - from2):
                            valid_high = True
                    else:
                        if opp_pts[dest2] <= 1:
                            valid_high = True
                    if valid_high:
                        final_moves.append(('L', from1, from2))
        
        # Now, we have a list of moves with prepended H/L
        # Format: list of (order, from1, from2)
        if len(final_moves) == 0:
            return ['H:P,P']  # fallback
        
        # Now evaluate which move is best
        best_move = None
        best_score = float('-inf')
        
        for order, f1, f2 in final_moves:
            score = evaluate_move(state, order, f1, f2)
            if score > best_score:
                best_score = score
                best_move = (order, f1, f2)
        
        if best_move is None:
            best_move = ('H', 'P', 'P')
        
        from1_str = 'P' if best_move[1] == 'P' else 'B' if best_move[1] == 'B' else f"A{best_move[1]}"
        from2_str = 'P' if best_move[2] == 'P' else 'B' if best_move[2] == 'B' else f"A{best_move[2]}"
        return f"{best_move[0]}:{from1_str},{from2_str}"
    
    # Evaluation function for move quality
    def evaluate_move(state, order, from1, from2):
        # Create a simulated new state after this move
        # We don't simulate the whole game, just compute heuristic score
        score = 0
        my_pts_local = my_pts.copy()
        opp_pts_local = opp_pts.copy()
        my_bar_local = my_bar
        
        # Apply move
        dice_used = []
        if order == 'H':
            die1, die2 = high, low
        else:
            die1, die2 = low, high
        
        # Apply first move
        if from1 != 'P' and from1 != 'B':
            # Move from point 'from1'
            dest1 = from1 + die1
            if dest1 > 23 and is_bearing_off_allowed and from1 >= HOME_BOARD_START and die1 >= (24 - from1):
                # Bear off
                my_pts_local[from1] -= 1
            elif dest1 <= 23:
                # Move normally
                my_pts_local[from1] -= 1
                if opp_pts_local[dest1] == 1:
                    # Hit! Opponent blot hit
                    opp_pts_local[dest1] -= 1
                    opp_bar += 1
                my_pts_local[dest1] += 1
            dice_used.append(die1)
        
        elif from1 == 'B':
            # Re-enter from bar
            reentry_point = die1 - 1
            my_bar_local -= 1
            if opp_pts_local[reentry_point] == 1:
                opp_pts_local[reentry_point] -= 1
                opp_bar += 1
            my_pts_local[reentry_point] += 1
            dice_used.append(die1)
        
        # Apply second move
        if from2 != 'P' and from2 != 'B':
            dest2 = from2 + die2
            if dest2 > 23 and is_bearing_off_allowed and from2 >= HOME_BOARD_START and die2 >= (24 - from2):
                my_pts_local[from2] -= 1
            elif dest2 <= 23:
                my_pts_local[from2] -= 1
                if opp_pts_local[dest2] == 1:
                    opp_pts_local[dest2] -= 1
                    opp_bar += 1
                my_pts_local[dest2] += 1
            dice_used.append(die2)
        
        elif from2 == 'B':
            reentry_point2 = die2 - 1
            my_bar_local -= 1
            if opp_pts_local[reentry_point2] == 1:
                opp_pts_local[reentry_point2] -= 1
                opp_bar += 1
            my_pts_local[reentry_point2] += 1
            dice_used.append(die2)
        
        # Now compute heuristic
        # 1. Penalize blots
        blots = sum(1 for i in range(24) if my_pts_local[i] == 1)
        score -= blots * 3  # penalty for blots
        
        # 2. Reward home board control
        home_board_control = sum(my_pts_local[i] for i in range(HOME_BOARD_START, HOME_BOARD_END + 1))
        score += home_board_control * 1.2
        
        # 3. Reward points with 2 or more checkers
        safe_points = sum(1 for i in range(24) if my_pts_local[i] >= 2)
        score += safe_points * 0.8
        
        # 4. Opponent blots and vulnerabilities
        opp_blots = sum(1 for i in range(24) if opp_pts_local[i] == 1)
        score += opp_blots * 2  # we want opponent to have blots
        
        # 5. Number of checkers remaining
        remaining = sum(my_pts_local)
        score -= remaining * 0.5  # fewer checkers = better
        
        # 6. Block control (primes): 6 consecutive points with 2+ checkers
        # We'll just count consecutive 2+ points
        prime_score = 0
        consecutive = 0
        for i in range(24):
            if my_pts_local[i] >= 2:
                consecutive += 1
                if consecutive >= 2:
                    prime_score += 0.5
            else:
                consecutive = 0
        score += prime_score
        
        # 7. Distance to home
        distance_to_home = 0
        for i in range(0, HOME_BOARD_START):
            if my_pts_local[i] > 0:
                distance_to_home += my_pts_local[i] * (HOME_BOARD_START - i)
        score -= distance_to_home * 0.05  # smaller distance is better
        
        # 8. If we just bore off, jackpot!
        if from1 == 'P' and from2 == 'P':
            score -= 1000000  # penalty for pass, but we shouldn't get here if moves exist
        else:
            # Give bonus if we bear off one checker
            if (from1 != 'P' and from1 != 'B' and from1 + die1 > 23 and is_bearing_off_allowed) or \
               (from2 != 'P' and from2 != 'B' and from2 + die2 > 23 and is_bearing_off_allowed):
                score += 5

            # If we hit an opponent, give a big bonus
            if (from1 != 'P' and from1 != 'B' and from1 + die1 <= 23 and opp_pts[from1 + die1] == 1) or \
               (from2 != 'P' and from2 != 'B' and from2 + die2 <= 23 and opp_pts[from2 + die2] == 1):
                score += 10
            
            # If we re-entered from bar, bonus
            if from1 == 'B' or from2 == 'B':
                score += 5
        
        return score
    
    moves = get_all_legal_moves()
    if not moves:
        return "H:P,P"
    
    # We need to format the best move.
    # But our function get_all_legal_moves() returns list of tuples (from1, from2), but we need to assign H/L
    # We'll reuse the above logic for generating and scoring moves
    
    # Let's generate all valid move strings with their H/L prefixes
    best_move_str = "H:P,P"
    best_score = float('-inf')
    
    # Check if we have checkers on bar
    if my_bar > 0:
        # Must use one die to re-enter
        for d in dice:
            reentry_point = d - 1
            if opp_pts[reentry_point] <= 1:
                remaining_dice = dice.copy()
                remaining_dice.remove(d)
                if len(remaining_dice) == 0:
                    # Only one die
                    best_move_str = f"H:B,P" if d == high else f"L:B,P"
                    return best_move_str
                else:
                    # Try second die from bar or from board
                    second_die = remaining_dice[0]
                    # Try from bar again
                    reentry_point2 = second_die - 1
                    if opp_pts[reentry_point2] <= 1:
                        # Can re-enter on both dice
                        order = "H" if max(d, second_die) == d else "L"
                        if d == high and second_die == low:
                            best_move_str = f"H:B,B"
                        elif second_die == high and d == low:
                            best_move_str = f"L:B,B"
                        else:
                            best_move_str = f"H:B,B" if high in [d, second_die] and d == high else f"L:B,B"
                        return best_move_str
                    
                    # Try from board
                    found = False
                    for from_point in range(24):
                        if my_pts[from_point] > 0:
                            dest = from_point + second_die
                            if dest > 23:
                                if is_bearing_off_allowed and from_point >= HOME_BOARD_START and second_die >= (24 - from_point):
                                    # Valid bearing off
                                    order = "H" if d == high else "L"
                                    best_move_str = f"{order}:B,A{from_point}"
                                    return best_move_str
                            elif opp_pts[dest] <= 1:
                                # Valid normal move
                                order = "H" if d == high else "L"
                                best_move_str = f"{order}:B,A{from_point}"
                                return best_move_str
                    # If no board move possible, try second die from bar
                    if opp_pts[reentry_point2] <= 1:
                        order = "H" if d == high else "L"
                        best_move_str = f"{order}:B,B"
                        return best_move_str
        # If we get here, no legal re-entry, emergency
        return "H:P,P"
    
    # Otherwise, normal case (no bar)
    # We need to evaluate each possible move string with correct H/L
    # We'll try to mimic the logic above, but now with explicit H/L
    if len(dice) == 1:
        # Only one die
        d = dice[0]
        for spot in range(24):
            if my_pts[spot] > 0:
                dest = spot + d
                if dest > 23:
                    if is_bearing_off_allowed and spot >= HOME_BOARD_START and d >= (24 - spot):
                        return f"H:A{spot},P"
                elif opp_pts[dest] <= 1:
                    return f"H:A{spot},P"
        # If nothing, pass
        return "H:P,P"
    
    # Two dice
    moves_to_try = []
    
    # Try all pairs: check each starting point for first and second die
    for i in range(24):
        if my_pts[i] <= 0:
            continue
        dest_i = i + high
        if dest_i > 23:
            if not (is_bearing_off_allowed and i >= HOME_BOARD_START and high >= (24 - i)):
                continue
        else:
            if opp_pts[dest_i] > 1:
                continue
        # First move: i with high
        for j in range(24):
            if my_pts[j] <= 0:
                continue
            if i == j and my_pts[i] < 2:
                continue
            dest_j = j + low
            if dest_j > 23:
                if is_bearing_off_allowed and j >= HOME_BOARD_START and low >= (24 - j):
                    moves_to_try.append(('H', i, j))
            else:
                if opp_pts[dest_j] <= 1:
                    moves_to_try.append(('H', i, j))
    
    for i in range(24):
        if my_pts[i] <= 0:
            continue
        dest_i = i + low
        if dest_i > 23:
            if not (is_bearing_off_allowed and i >= HOME_BOARD_START and low >= (24 - i)):
                continue
        else:
            if opp_pts[dest_i] > 1:
                continue
        # First move: i with low
        for j in range(24):
            if my_pts[j] <= 0:
                continue
            if i == j and my_pts[i] < 2:
                continue
            dest_j = j + high
            if dest_j > 23:
                if is_bearing_off_allowed and j >= HOME_BOARD_START and high >= (24 - j):
                    moves_to_try.append(('L', i, j))
            else:
                if opp_pts[dest_j] <= 1:
                    moves_to_try.append(('L', i, j))
    
    # Also include one-move possibilities (if only one die playable)
    if len(moves_to_try) == 0:
        for i in range(24):
            if my_pts[i] <= 0:
                continue
            for die in [high, low]:
                dest = i + die
                if dest > 23:
                    if is_bearing_off_allowed and i >= HOME_BOARD_START and die >= (24 - i):
                        order = "H" if die == high else "L"
                        return f"{order}:A{i},P"
                else:
                    if opp_pts[dest] <= 1:
                        order = "H" if die == high else "L"
                        return f"{order}:A{i},P"
        return "H:P,P"
    
    # Now evaluate the moves
    best_score = float('-inf')
    best_move_str = "H:P,P"
    
    for order, from1, from2 in moves_to_try:
        score = evaluate_move(state, order, from1, from2)
        if score > best_score:
            best_score = score
            from1_str = f"A{from1}" if from1 != 'P' else 'P'
            from2_str = f"A{from2}" if from2 != 'P' else 'P'
            best_move_str = f"{order}:{from1_str},{from2_str}"
    
    return best_move_str
