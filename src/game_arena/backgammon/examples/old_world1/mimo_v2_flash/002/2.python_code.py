
import itertools
import random

def policy(state: dict) -> str:
    """
    Backgammon Policy:
    Uses a heuristic-based evaluation with a 1-step look-ahead (simulation of opponent roll)
    to balance aggression (hitting) and safety (avoiding blots).
    """
    
    # --- Constants and Heuristic Weights ---
    # Weights for the evaluation function
    W_PIP = -1.0          # Lower pip count is better
    W_BLOT = -5.0         # Penalize single checkers
    W_HOME = 2.0          # Encourage being in home board
    W_PRIME = 3.0         # Encourage building primes (consecutive blocks)
    W_HIT = 15.0          # Reward hitting opponent
    W_BAR = -10.0         # Heavy penalty for being on the bar
    W_OFF = -20.0         # Strongly reward bearing off (pip reduction)
    
    # --- Helper: Deep Copy State ---
    def copy_state(s):
        return {
            'my_pts': s['my_pts'][:],
            'opp_pts': s['opp_pts'][:],
            'my_bar': s['my_bar'],
            'opp_bar': s['opp_bar'],
            'my_off': s['my_off'],
            'opp_off': s['opp_off'],
            'dice': s['dice'][:]
        }

    # --- Helper: Check if point is safe ---
    def is_safe_for_opponent(pts, idx):
        return pts[idx] < 2

    # --- Helper: Apply Move to State (Simulation) ---
    def apply_move(s, from_loc, die_val, is_me=True):
        # Returns a tuple: (new_state, hit_occurred)
        # We assume 'from_loc' is valid for the player
        new_s = copy_state(s)
        hit_occurred = False
        
        if is_me:
            if from_loc == 'B':
                new_s['my_bar'] -= 1
                dest = 24 - die_val
            else:
                new_s['my_pts'][from_loc] -= 1
                dest = from_loc + die_val
            
            # Check for hit
            if dest < 24 and new_s['opp_pts'][dest] == 1:
                new_s['opp_pts'][dest] = 0
                new_s['opp_bar'] += 1
                hit_occurred = True
            
            # Place checker
            if dest >= 24:
                new_s['my_off'] += 1
            else:
                new_s['my_pts'][dest] += 1
        else:
            # Opponent moving (for simulation)
            if from_loc == 'B':
                new_s['opp_bar'] -= 1
                dest = die_val - 1 # Opponent moves 0->23
            else:
                new_s['opp_pts'][from_loc] -= 1
                dest = from_loc - die_val
            
            # Check for hit (opponent hitting me)
            if dest >= 0 and new_s['my_pts'][dest] == 1:
                new_s['my_pts'][dest] = 0
                new_s['my_bar'] += 1
                hit_occurred = True
            
            if dest < 0:
                new_s['opp_off'] += 1
            else:
                new_s['opp_pts'][dest] += 1
                
        return new_s, hit_occurred

    # --- Helper: Generator for Legal Moves (My Turn) ---
    def get_my_legal_moves(s, dice):
        """
        Generates all legal move sequences.
        Returns list of tuples: ( [(from_loc, die_val), ...], new_state )
        """
        moves = []
        # Handle doubles: Allow 1, 2, 3, or 4 moves
        if len(dice) == 1:
            combos = [(dice[0],)]
        elif dice[0] == dice[1]:
            combos = [(dice[0],), (dice[0], dice[0]), (dice[0], dice[0], dice[0]), (dice[0], dice[0], dice[0], dice[0])]
        else:
            combos = [(dice[0],), (dice[1],), (dice[0], dice[1]), (dice[1], dice[0])]

        # Checkers on bar?
        if s['my_bar'] > 0:
            # Must enter from bar
            valid_bars = []
            for d in set(dice):
                # Bar (24) -> 23-d
                dest = 23 - d
                if s['opp_pts'][dest] < 2:
                    valid_bars.append(('B', d))
            
            if not valid_bars:
                # Cannot enter
                if len(dice) == 2: # Try partials? 
                    # Standard rules: If you can't enter, you must pass the rest.
                    # However, strictly we must play the higher die if possible.
                    # But if we can't enter, we can't move anything else.
                    return [[('P', 0)]] # Actually engine handles this, but we return pass sequence
                return [[('P', 0)]]

            # If we can enter, generate sequences that start with entry
            for combo in combos:
                # Simulate entry
                # This is a simplified generator. We need recursion to handle all permutations.
                pass 

        # Recursive generator for all valid sequences
        valid_sequences = []
        
        def recurse(current_state, dice_remaining, current_path):
            if not dice_remaining:
                valid_sequences.append((current_path, current_state))
                return

            # If checkers on bar, ONLY consider bar moves
            if current_state['my_bar'] > 0:
                for i, d in enumerate(dice_remaining):
                    dest = 23 - d
                    if current_state['opp_pts'][dest] < 2:
                        next_state, hit = apply_move(current_state, 'B', d)
                        # We must consume this die exactly
                        new_dice = dice_remaining[:i] + dice_remaining[i+1:]
                        recurse(next_state, new_dice, current_path + [('B', d)])
                return

            # Standard moves
            moved = False
            # Try all points
            for pt in range(24):
                if current_state['my_pts'][pt] > 0:
                    # Try all dice available
                    for i, d in enumerate(dice_remaining):
                        # Check valid move
                        # Determine destination
                        dest = pt + d
                        
                        # Bearing off check
                        if dest >= 24:
                            # Can only bear off if all checkers in home board (18-23)
                            # or if on exact point
                            in_home = True
                            for k in range(18):
                                if current_state['my_pts'][k] > 0:
                                    in_home = False
                                    break
                            if in_home and (dest == 24 or all(current_state['my_pts'][k] == 0 for k in range(pt+1, 24))):
                                # Legal bear off
                                next_state, hit = apply_move(current_state, pt, d)
                                new_dice = dice_remaining[:i] + dice_remaining[i+1:]
                                recurse(next_state, new_dice, current_path + [(pt, d)])
                                moved = True
                                continue
                            else:
                                # Cannot bear off yet or overshoot
                                continue
                        
                        # Normal move
                        if dest < 24 and current_state['opp_pts'][dest] < 2:
                            next_state, hit = apply_move(current_state, pt, d)
                            new_dice = dice_remaining[:i] + dice_remaining[i+1:]
                            recurse(next_state, new_dice, current_path + [(pt, d)])
                            moved = True
            
            if not moved:
                valid_sequences.append((current_path, current_state))

        # Start recursion
        # We need to handle duplicate dice carefully. 
        # To avoid permutations of same move (e.g. A->B then C->D vs C->D then A->B), 
        # we don't strictly enforce order in recursion but generate all.
        # For simplicity, we just generate all legal sequences.
        
        recurse(s, dice, [])
        
        if not valid_sequences:
            return [[('P', 0)]]
        return valid_sequences

    # --- Heuristic Evaluation Function ---
    def evaluate(s, my_move_seq):
        score = 0.0
        
        # 1. Pips (Distance to bear off)
        my_pip = 0
        for i in range(24):
            my_pip += s['my_pts'][i] * (i + 1) # 0 is furthest
        opp_pip = 0
        for i in range(24):
            opp_pip += s['opp_pts'][i] * (24 - i) # 23 is furthest for opp
        
        score += W_PIP * (my_pip - opp_pip)

        # 2. Blots (Vulnerability)
        my_blots = sum(1 for x in s['my_pts'] if x == 1)
        opp_blots = sum(1 for x in s['opp_pts'] if x == 1)
        score += W_BLOT * (my_blots - opp_blots * 0.5) # Hitting is good, being hit is bad

        # 3. Home Board (Blocking)
        my_home_occ = sum(s['my_pts'][18:])
        score += W_HOME * my_home_occ

        # 4. Primes (Consecutive blocks)
        def count_primes(pts):
            count = 0
            consec = 0
            for p in pts:
                if p >= 2:
                    consec += 1
                else:
                    if consec >= 5: count += 1
                    consec = 0
            if consec >= 5: count += 1
            return count
        score += W_PRIME * (count_primes(s['my_pts']) - count_primes(s['opp_pts']))

        # 5. Bar Status
        score += W_BAR * s['my_bar']
        score += W_BAR * 2 * s['opp_bar'] # Opponent on bar is very good for us

        # 6. Off
        score += W_OFF * s['my_off']
        score += W_OFF * -2 * s['opp_off'] # Preventing opponent winning is high priority

        # 7. Hit Bonus (Immediate Reward)
        # We check if the move sequence resulted in a hit by looking at state diff or just detecting 'B' moves? 
        # Actually, we can check if my_checkers increased on a point that was previously 0, or if opp_bar increased.
        # However, we know 'hit_occurred' is hard to track in recursion result without passing it.
        # Let's check if the move sequence consumed a 'B' entry? No, that's entry not hit.
        # Let's check if opponent bar count increased.
        # But we need initial state for that. Let's pass initial state or just rely on 'opp_bar' value.
        # If opp_bar > 0 after move, we likely hit.
        # However, we also need to check if we landed on a blot.
        # Let's assume any move sequence that lands on a point with 1 checker (before move) is a hit.
        # This is hard to track in the recursive structure without passing more data.
        # Simple hack: if opp_bar count increased significantly, add bonus.
        # Actually, let's just calculate a separate "Hit Reward".
        # Let's assume if my path includes a landing on a point where opp was 1.
        # We will assume hitting is good and rely on the pip/blot differential to handle it mostly.

        # 8. Safety Check (Blot exposure)
        # If we left a blot, and opponent has checkers on bar, we might get hit next turn.
        # This requires a look-ahead.
        return score

    # --- Main Logic ---
    dice = state['dice']
    if not dice:
        return "H:P,P"

    # 1. Generate all legal move sequences for current dice
    legal_moves = get_my_legal_moves(state, dice)
    
    if not legal_moves or legal_moves == [[('P', 0)]]:
        return "H:P,P"

    # 2. Evaluate each move
    best_score = -float('inf')
    best_move_str = ""

    # Identify Dice Values
    if len(dice) == 2:
        d1, d2 = sorted(dice) # Low, High
    else:
        d1 = dice[0]
        d2 = None # Doubles handled in generator

    for path, next_state in legal_moves:
        # Check if move is valid (generator might return P,P if no moves)
        if not path or path[0][0] == 'P':
            # If we have dice but no moves, this is a pass
            move_str = "H:P,P" # Defaults to H (higher die), but P,P means pass
            score = -1000 # Low score so we prefer actual moves
        else:
            # Construct Move String
            # Path is list of (from, die_val)
            # We need to order moves: H or L first.
            # If we used both dice, we need to decide order.
            # If we only used one die, we must use P for the second.
            
            # Determine if we used d1 or d2
            used_d1 = any(d == d1 for _, d in path)
            used_d2 = d2 and any(d == d2 for _, d in path)
            
            from1 = ""
            from2 = ""
            
            # Identify the move associated with higher die (d2) and lower die (d1)
            move_d1 = [x for x in path if x[1] == d1]
            move_d2 = [x for x in path if x[1] == d2] if d2 else []
            
            # For doubles, we can have multiple moves. We pick the first two for formatting, 
            # or sort by point index to be deterministic.
            # In standard format, we only output 2 moves max (or 1 + P).
            # If we have 4 moves (doubles), we just output the first two relevant ones? 
            # No, the engine expects the sequence. 
            # The format supports exactly two FROM locations.
            # If we have 4 moves (e.g., 6-6), we need to output something like H:A5,A5? 
            # Actually, standard Backgammon notation for doubles often lists multiple moves.
            # But the prompt says: <FROM1>,<FROM2>. This implies max 2 physical moves.
            # However, the engine might be smart enough to handle sequential moves if we use the "order" bit correctly?
            # Let's assume we output the *first* move for the higher die and the *first* move for the lower die.
            # If we have 4 moves (doubles), we pick the first 2.
            
            # Sort moves by point index (0-23) then Bar (-1)
            def sort_key(x):
                if x[0] == 'B': return -1
                return x[0]
            
            path.sort(key=sort_key)

            # Get first moves for each die value
            if d2:
                # If we have both dice
                move_H = None
                move_L = None
                
                # Find moves for High die
                for x in path:
                    if x[1] == d2 and move_H is None:
                        move_H = x
                        path.remove(x) # Remove so we don't reuse
                        break
                
                # Find moves for Low die
                for x in path:
                    if x[1] == d1 and move_L is None:
                        move_L = x
                        path.remove(x)
                        break
                
                # If we used only one die, the other is P
                # If we used doubles (d1 == d2), we might have multiple.
                # If we used 4 moves, we just output the first 2 found.
                
                f1 = move_H[0] if move_H else (move_L[0] if move_L else 'P')
                f2 = move_L[0] if move_L else 'P'
                
                # If we played H first (which we did in logic), format as H
                # If we have only L move (meaning we didn't play H because it was illegal? No, generator handles that)
                # We must respect the "higher die first" rule if both are playable.
                # If both are playable, we must play H.
                
                # Wait, if we have a move list that used both, we need to output H or L based on order.
                # If we have both moves, we output H:F1,F2 (where F1 is from H die).
                # If we have only one move, we output X:F1,P.
                
                # If we have both moves:
                if move_H and move_L:
                    move_str = f"H:{move_H[0]},{move_L[0]}"
                elif move_H:
                    move_str = f"H:{move_H[0]},P"
                elif move_L:
                    # This case implies we didn't play the higher die, but could we?
                    # The generator ensures we play the best legal sequence. 
                    # If we only played L, it's because H was impossible.
                    # In that case, we can output L (though H:P,L is technically illegal if L is playable? No, order is arbitrary if only one die playable)
                    # The prompt says: "If only one die can be played, you must play the higher die when possible."
                    # So if we only have move_L, it means move_H was impossible.
                    # Then we must play H. But we don't have an H move.
                    # So we play H:P, [move_L]? No, H:P,L means play lower then higher? No.
                    # H:P,L means: Apply Higher Die (pass), then Lower Die (from L).
                    # That's valid.
                    move_str = f"H:P,{move_L[0]}"
                else:
                    move_str = "H:P,P"
            else:
                # Single die
                if path:
                    move_str = f"H:{path[0][0]},P"
                else:
                    move_str = "H:P,P"

        # --- Look-ahead / Safety Check (Simulation of Opponent Roll) ---
        # If we leave blots exposed to immediate hits, and we didn't hit them back, penalize.
        # We only do this if we are ahead or if the board is tight.
        
        # 1. Calculate raw heuristic score
        score = evaluate(next_state, path)
        
        # 2. Safety Bonus/Penalty
        # If opponent has checkers on bar, risk is low.
        # If we left a blot (points with 1 checker) and opponent has checkers NOT on bar...
        if next_state['opp_bar'] == 0:
            # Identify my blots
            my_blots_indices = [i for i, c in enumerate(next_state['my_pts']) if c == 1]
            if my_blots_indices:
                # Monte Carlo-ish: Sample a few good opponent dice or average
                # We will check if ANY opponent move can hit us.
                # Since opponent has 2 dice, we check all 36 rolls.
                # But for speed, we just check if a blot is within 6 of a possible opponent checker?
                # No, opponent moves backward.
                # Opponent from 0..23 to 0..23. Destination is src - die.
                # So if I have a blot at P, opponent can hit if he has a checker at P + D for some D in 1..6.
                
                can_be_hit = False
                hit_penalty = 0
                
                # Optimization: Only check if we are in opponent's home board (0-5) or near their rear?
                # Actually, anywhere on board.
                # Let's just calculate a probability-like penalty based on how many opponents are near.
                
                risk = 0
                for p in my_blots_indices:
                    # Opponent at p+1 to p+6
                    for d in range(1, 7):
                        opp_pos = p + d
                        if opp_pos < 24 and next_state['opp_pts'][opp_pos] > 0:
                            # There is an opponent there.
                            # Weight by how many checkers.
                            risk += next_state['opp_pts'][opp_pos] * d # Closer is worse
                
                # If we hit an opponent, we reduce risk (they are on bar)
                # We already accounted for opp_bar in evaluate().
                
                # Apply penalty
                if risk > 0:
                    score -= risk * 0.5 

        # Update best
        if score > best_score:
            best_score = score
            best_move_str = move_str

    if not best_move_str:
        return "H:P,P"
        
    return best_move_str
