
import numpy as np

def policy(state: dict) -> str:
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'])  # sorted as [low, high]
    low_die, high_die = dice[0], dice[1]
    
    # If no dice, pass (should not happen per rules, but safety)
    if len(dice) == 0:
        return "H:P,P"
    
    # If checkers on bar, must re-enter
    if my_bar > 0:
        # Try to re-enter using each die
        moves = []
        for die in dice:
            dest = 23 - die  # Re-enter from bar: destination is 23-die (absolute)
            if dest < 0 or dest > 23:
                continue
            # Check if can land on dest: opponent must have < 2 checkers
            if opp_pts[dest] <= 1:
                moves.append((die, 'B', dest))  # (die_value, from, to)
        
        if len(moves) == 0:
            # Cannot re-enter with either die => must pass die(s) but rules say must play if possible
            # But if both dice can't be played, then if one can be played, must play higher
            # But here neither can be played, so we return pass with higher first (convention)
            return "H:P,P"
        
        # If we can re-enter with both dice, we need to choose order
        # Try both orders: H then L, L then H
        possible_actions = []
        
        # Try using higher die first
        for die1, from1, to1 in moves:
            if die1 == high_die:
                # Use higher die first
                remaining_die = low_die
                remaining_dest = 23 - remaining_die
                if remaining_dest >= 0 and remaining_dest <= 23 and opp_pts[remaining_dest] <= 1:
                    # Can use both dice
                    possible_actions.append(f"H:B,A{remaining_dest}")
                else:
                    # Only higher die can be played
                    possible_actions.append(f"H:B,P")
        
        # Try using lower die first
        for die1, from1, to1 in moves:
            if die1 == low_die:
                remaining_die = high_die
                remaining_dest = 23 - remaining_die
                if remaining_dest >= 0 and remaining_dest <= 23 and opp_pts[remaining_dest] <= 1:
                    possible_actions.append(f"L:B,A{remaining_dest}")
                else:
                    possible_actions.append(f"L:B,P")
        
        # If only one die can be played, we must play the higher one if possible
        # So prefer action that plays the higher die first if we can't play both
        if any(action.endswith(",P") for action in possible_actions):
            # Only one die playable; choose the one that plays the higher die
            single_high = [a for a in possible_actions if a.startswith("H:B,P")]
            single_low = [a for a in possible_actions if a.startswith("L:B,P")]
            if single_high:
                return single_high[0]
            elif single_low:
                return single_low[0]
            else:
                # Can play both, choose the one that uses higher die first
                return [a for a in possible_actions if a.startswith("H:")][0] if any(a.startswith("H:") for a in possible_actions) else possible_actions[0]
        else:
            # Can play both, choose highest die first for safety
            return [a for a in possible_actions if a.startswith("H:")][0]
    
    # No checkers on bar — normal play
    # Find all legal moves for each die
    # We'll simulate possible moves for each die independently
    
    # Helper: check if a move from 'start' by 'die' is legal
    def is_legal_move(start, die):
        if start < 0 or start > 23:
            return False
        if my_pts[start] == 0:
            return False
        end = start - die  # moving toward 0 for player 1
        if end < 0:
            # Bearing off
            if not can_bear_off():
                return False
            return True
        if end > 23:  # shouldn't happen
            return False
        # Check if opponent has 2+ checkers on endpoint
        if opp_pts[end] >= 2:
            return False
        return True
    
    # Helper: check if all checkers are in home board (points 0-5 for player 1)
    def can_bear_off():
        # All my checkers must be in points 0 to 5
        return np.sum(my_pts[6:]) == 0
    
    # Find all legal single moves for each die
    legal_moves_high = []
    legal_moves_low = []
    
    for start in range(24):
        if is_legal_move(start, high_die):
            legal_moves_high.append(start)
        if is_legal_move(start, low_die):
            legal_moves_low.append(start)
    
    # Check bearing off options: both dice must be used if possible
    if can_bear_off():
        # Try bearing off with each die if possible
        bear_off_high = any(my_pts[i] > 0 and i + high_die >= 24 for i in range(6))
        bear_off_low = any(my_pts[i] > 0 and i + low_die >= 24 for i in range(6))
        
        # We can bear off checkers from points 0-5
        legal_bear_off_high = [i for i in range(6) if my_pts[i] > 0 and i + high_die >= 24]
        legal_bear_off_low = [i for i in range(6) if my_pts[i] > 0 and i + low_die >= 24]
        
        # Try to use both dice to bear off
        # Priority: bear off furthest checkers first to minimize total pips needed
        legal_bear_off_high.sort(reverse=True)
        legal_bear_off_low.sort(reverse=True)
        
        # Choose from the set of legal combinations
        if len(legal_bear_off_high) > 0 and len(legal_bear_off_low) > 0:
            # Try both orders
            # Option 1: High then Low
            # Pick the furthest checker that can be borne off with high die
            hv = legal_bear_off_high[0] if legal_bear_off_high else None
            lv = legal_bear_off_low[0] if legal_bear_off_low else None
            if hv is not None and lv is not None:
                # We can play both
                if hv == lv:  # same point
                    if my_pts[hv] >= 2:
                        return f"H:A{hv},A{hv}"
                return f"H:A{hv},A{lv}"
            elif len(legal_bear_off_high) > 0:
                return f"H:A{legal_bear_off_high[0]},P"
            elif len(legal_bear_off_low) > 0:
                return f"L:A{legal_bear_off_low[0]},P"
        
        # If we can only use one die, prioritize the higher one
        if len(legal_bear_off_high) > 0:
            return f"H:A{legal_bear_off_high[0]},P"
        elif len(legal_bear_off_low) > 0:
            return f"L:A{legal_bear_off_low[0]},P"
        
        # If neither dies can bear off a checker (because they don't get to 24), then we do normal play
        # (shouldn't happen if can_bear_off returns True and checkers are in 0-5)
    else:
        # Not in home board yet — normal play
        pass  # fall through to normal play logic
    
    # Normal play: not bearing off
    # Generate all possible move sequences
    # We try all pairs of legal moves with order H then L, and L then H
    # We'll score each sequence based on heuristics
    
    def score_move_sequence(moves_list):
        """Score a sequence of moves (list of [start, end])"""
        if not moves_list:
            return -1000  # bad
        score = 0
        # Heuristic weights
        HIT_BONUS = 50   # hitting opponent gives bonus
        PRIME_BONUS = 20 # building prime
        HOME_BONUS = 10  # moving toward home
        BLOT_PENALTY = -30 # leaving a blot
        SAFE_POINT_BONUS = 15 # landing on a point with own checkers
        
        for start, end in moves_list:
            # If we move checkers closer to home, reward
            if end >= 0:  # not bearing off
                if start > end:  # moving toward home
                    score += (start - end) * HOME_BONUS
            else:  # bearing off
                score += 100  # huge bonus for bearing off!
            
            # Check if we hit an opponent blot
            if end >= 0 and end <= 23 and opp_pts[end] == 1:
                score += HIT_BONUS
            
            # Check if we land on a point with our checkers (safe point)
            if end >= 0 and end <= 23 and my_pts[end] > 0:
                score += SAFE_POINT_BONUS
            
            # Check if we leave a blot behind (start becomes 1)
            if my_pts[start] == 1:  # we're leaving a blot
                score += BLOT_PENALTY
        
        return score
    
    # Collect all possible move sequences
    sequences = []  # list of (order, from1, from2)
    
    # Try H first then L
    for start1 in legal_moves_high:
        end1 = start1 - high_die
        if end1 < 0:
            # Check if bearing off is legal
            if can_bear_off():
                # We can bear off
                # Create a state after first move and check second move legality
                # We need to simulate the board after first move
                test_my_pts = my_pts.copy()
                test_my_pts[start1] -= 1
                if end1 >= 0:
                    test_my_pts[end1] += 1
                
                # Check second move with low die on new state
                for start2 in range(24):
                    if test_my_pts[start2] > 0:
                        end2 = start2 - low_die
                        if end2 < 0:
                            if can_bear_off():  # already true
                                sequences.append((f"H:A{start1},A{start2}"))
                        elif end2 >= 0 and end2 <= 23 and test_my_pts[end2] < 2 and opp_pts[end2] < 2:
                            sequences.append((f"H:A{start1},A{start2}"))
            else:
                continue
        else:
            # Normal point move
            if opp_pts[end1] < 2:
                # Update board state
                test_my_pts = my_pts.copy()
                test_my_pts[start1] -= 1
                test_my_pts[end1] += 1
                
                # Check second move
                for start2 in range(24):
                    if test_my_pts[start2] > 0:
                        end2 = start2 - low_die
                        if end2 < 0:
                            if can_bear_off():
                                sequences.append((f"H:A{start1},A{start2}"))
                        elif end2 >= 0 and end2 <= 23 and test_my_pts[end2] < 2 and opp_pts[end2] < 2:
                            sequences.append((f"H:A{start1},A{start2}"))
    
    # Try L first then H
    for start1 in legal_moves_low:
        end1 = start1 - low_die
        if end1 < 0:
            if can_bear_off():
                test_my_pts = my_pts.copy()
                test_my_pts[start1] -= 1
                if end1 >= 0:
                    test_my_pts[end1] += 1
                for start2 in range(24):
                    if test_my_pts[start2] > 0:
                        end2 = start2 - high_die
                        if end2 < 0:
                            if can_bear_off():
                                sequences.append((f"L:A{start1},A{start2}"))
                        elif end2 >= 0 and end2 <= 23 and test_my_pts[end2] < 2 and opp_pts[end2] < 2:
                            sequences.append((f"L:A{start1},A{start2}"))
            else:
                continue
        else:
            if opp_pts[end1] < 2:
                test_my_pts = my_pts.copy()
                test_my_pts[start1] -= 1
                test_my_pts[end1] += 1
                for start2 in range(24):
                    if test_my_pts[start2] > 0:
                        end2 = start2 - high_die
                        if end2 < 0:
                            if can_bear_off():
                                sequences.append((f"L:A{start1},A{start2}"))
                        elif end2 >= 0 and end2 <= 23 and test_my_pts[end2] < 2 and opp_pts[end2] < 2:
                            sequences.append((f"L:A{start1},A{start2}"))
    
    # Now handle single move cases
    # If only one die can be played, we must play the higher die if possible
    if len(sequences) == 0:
        # Try single moves: if only one die can be played
        if len(legal_moves_high) > 0:
            # Can play higher die
            return f"H:A{legal_moves_high[0]},P"
        elif len(legal_moves_low) > 0:
            # Can play lower die, but must play higher if possible => so we must use higher if available
            # But we just checked higher was unavailable
            return f" L:A{legal_moves_low[0]},P"
        else:
            # No legal moves at all
            return "H:P,P"
    
    # Choose the best sequence based on heuristic scoring
    best_score = -10000
    best_action = "H:P,P"
    
    for seq in sequences:
        # We need to compute a better score based on position after moves
        # For simplicity, assign a basic score based on die values and hits
        # Extract the from points
        parts = seq.split(":")[1].split(",")
        fi1 = parts[0][1:] if parts[0].startswith('A') else parts[0]
        fi2 = parts[1][1:] if parts[1].startswith('A') else parts[1]
        if fi1 == 'P':
            continue
        if fi2 == 'P':
            # Single move
            start1 = int(fi1)
            end1 = start1 - (high_die if seq.startswith("H") else low_die)
            score = 0
            # Calculate how much progress
            if end1 >= 0:
                # We moved toward home
                score += (start1 - end1) * 5
            else:
                # Bearing off!
                score += 100
            # Check if we hit
            if end1 >= 0 and end1 <= 23 and opp_pts[end1] == 1:
                score += 50
            if score > best_score:
                best_score = score
                best_action = seq
        else:
            start1 = int(fi1)
            start2 = int(fi2)
            die1 = high_die if seq.startswith("H") else low_die
            die2 = low_die if seq.startswith("H") else high_die
            end1 = start1 - die1
            end2 = start2 - die2
            score = 0
            if end1 >= 0:
                score += (start1 - end1) * 5
            else:
                score += 100
            if end2 >= 0:
                score += (start2 - end2) * 5
            else:
                score += 100
            # Hit bonuses
            if end1 >= 0 and end1 <= 23 and opp_pts[end1] == 1:
                score += 50
            if end2 >= 0 and end2 <= 23 and opp_pts[end2] == 1:
                score += 50
            # Add more if landing on own points
            if end1 >= 0 and end1 <= 23 and my_pts[end1] > 0:
                score += 5
            if end2 >= 0 and end2 <= 23 and my_pts[end2] > 0:
                score += 5
            if score > best_score:
                best_score = score
                best_action = seq
    
    if best_action == "H:P,P" and len(legal_moves_high) > 0:
        return f"H:A{legal_moves_high[0]},P"
    elif best_action == "H:P,P" and len(legal_moves_low) > 0:
        return f"L:A{legal_moves_low[0]},P"
    
    return best_action if best_action != "H:P,P" else "H:P,P"
